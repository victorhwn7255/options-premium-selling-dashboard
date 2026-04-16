---
last_verified: 2026-04-16
verified_against: 2134cff
rot_risk: medium
rot_triggers:
  - docker-compose.yml
  - backend/Dockerfile
  - frontend/Dockerfile
  - frontend/next.config.js
audience: both
---

# Deployment

## Purpose

How to run, build, and deploy the system. Lookup reference for commands, environment variables, and operational gotchas.

## Scope

**This file covers:** Docker stack, env vars, local dev, rebuild workflow, volumes, Cloudflare tunnel, CLI scripts, operational gotchas.

**This file does NOT cover:**
- Architecture and data flow — see `2-system/architecture.md`
- Database schema — see `2-system/data-model.md`

---

## Docker Compose (Production)

Three services in `docker-compose.yml`:

| Service | Image | Ports | Notes |
|---------|-------|-------|-------|
| `backend` | `./backend` (python:3.12-slim) | 8030 → 8000 | Bind mounts: `./backend/data:/app/data`, `./utils:/app/utils` |
| `frontend` | `./frontend` (node:20-alpine) | 3000 → 3000 | Build arg: `BACKEND_URL=http://backend:8000` |
| `cloudflared` | `cloudflare/cloudflared:latest` | — | Tunnel to theta.thevixguy.com |

```bash
docker compose up --build              # Start full stack
docker compose down                    # Stop
docker compose up -d --build backend   # Rebuild backend only
docker compose logs -f backend         # Tail backend logs
```

**Backend source is baked into the Docker image.** Any `.py` edit requires `docker compose up -d --build backend`. The `data/` directory is bind-mounted, so SQLite and CSVs survive rebuilds. The `utils/` directory is also bind-mounted for the post-scan verification import.

**Healthcheck:** `python -c "import httpx; httpx.get('http://localhost:8000/api/health')"` every 60s, 3 retries, 10s start period.

---

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `MARKETDATA_TOKEN` | **Yes** | — | Bearer token for api.marketdata.app (Starter plan, $12/mo) |
| `FMP_API_KEY` | No | — | Financial Modeling Prep earnings dates. Without it, falls back to MarketData's earnings endpoint. |
| `CORS_ORIGINS` | No | — | Extra CORS origins, comma-separated (appended to default localhost list) |
| `CLOUDFLARE_TUNNEL_TOKEN` | No | — | Cloudflare tunnel for public access |
| `RISK_FREE_RATE` | No | `0.043` | BSM IV solver discount rate for `backfill.py` |

Set via `.env` file in the project root (gitignored) or passed directly to Docker.

---

## Local Development (Without Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
export MARKETDATA_TOKEN=your_token
export FMP_API_KEY=your_key          # optional
python main.py                       # uvicorn on :8000, hot reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev                          # Next.js dev server on :3000
```

Frontend proxies `/api/*` to `http://localhost:8030` by default (see `next.config.js`). For local dev without Docker, the backend runs on :8000 — either change the proxy target or run Docker for the backend only.

---

## CLI Scripts

**Backfill** — populate historical IV for IV Rank/Percentile (requires `MARKETDATA_TOKEN`):

```bash
cd backend
python backfill.py --days 252 --verbose          # Full year
python backfill.py --days 5 --tickers SPY --dry-run  # Preview
python backfill.py --resume --verbose              # Skip existing dates
python backfill.py --batch-size 30 --credit-limit 1000  # Controlled run
```

**Repair** — fix stock-split-corrupted RV30/VRP:

```bash
cd backend
python repair_rv.py --tickers NFLX --dry-run     # Preview
python repair_rv.py --tickers NFLX               # Apply fix
python repair_rv.py --all                         # Fix entire universe
```

**Tests** (manual, no CI):

```bash
cd backend
python test_calculator.py                         # 5 tests
python -m pytest test_liquidity_filter.py -v      # 6 tests
```

---

## Operational Gotchas

**SGT timezone host.** The production host is in UTC+8. All trading logic uses ET explicitly via `zoneinfo.ZoneInfo("America/New_York")`. Any new time-sensitive code must pass the timezone — `datetime.now()` without `tz=` returns SGT. See [fragile-seams.md § Timezone Seams](../3-guardrails/fragile-seams.md#host-timezone-vs-trading-timezone).

**Earnings counter resets on restart.** The daily limit for `POST /api/earnings/refresh` is in-memory (`_earnings_refresh_tracker`). Container restart, Docker rebuild, or uvicorn reload resets it to zero.

**Frontend build-time BACKEND_URL.** The API proxy destination is baked into the Next.js build via `BACKEND_URL` arg. Changing the backend address requires rebuilding the frontend container.

**Rate limit is 10/min.** The MarketData.app token bucket is set to 10 calls/min (API supports 50). Scans take ~13 minutes. See [ADR-005](../3-guardrails/decisions/005-rate-limit-10-per-minute.md) for why.
