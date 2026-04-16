---
last_verified: 2026-04-16
verified_against: dc030c3
rot_risk: medium
rot_triggers:
  - docker-compose.yml
  - backend/Dockerfile
  - frontend/Dockerfile
  - frontend/next.config.js
  - backend/backfill.py
  - backend/repair_rv.py
  - utils/verify_metrics.py
audience: both
---

# Deployment

## Purpose

How to run, build, and deploy the system. Lookup reference for commands, environment variables, and operational gotchas.

## Scope

**This file covers:** Docker stack, env vars, local dev, rebuild workflow, volumes, Cloudflare tunnel, CLI scripts (backfill, repair, verify), tests, operational gotchas.

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

### Backfill (`backend/backfill.py`)

Populates historical IV for IV Rank/Percentile calculations. Requires `MARKETDATA_TOKEN`.

**How it works:** Two-step API approach per ticker per date — fetches option chain for contract symbols, then fetches quotes for nearest-ATM contracts and solves Black-Scholes for IV. Stores results in `daily_iv` table and daily CSVs.

```bash
cd backend
python backfill.py --days 252 --verbose              # Full year for all tickers
python backfill.py --days 5 --tickers SPY --dry-run  # Preview without API calls
python backfill.py --resume --verbose                 # Skip dates already in DB
python backfill.py --batch-size 30 --credit-limit 1000  # Controlled run
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--days` | 252 | Trading days to backfill (~1 year) |
| `--tickers` | all | Comma-separated subset (e.g., `SPY,QQQ`) |
| `--resume` | off | Skip (ticker, date) pairs already in `daily_iv` |
| `--dry-run` | off | Show plan without making API calls |
| `--batch-size` | unlimited | Max trading days per run |
| `--credit-limit` | 1000 | Stop when API credits drop below this |
| `--verbose` | off | Per-ticker per-date debug logs |

**Cost:** ~11 API calls per ticker per date. Rate-limited to 15 calls/min internally. A full 252-day × 33-ticker run is ~90k calls — use `--batch-size` and `--resume` to spread across sessions.

**Safe to interrupt:** Commits to SQLite and appends CSVs per-item. Re-run with `--resume` to pick up where you left off.

### Repair (`backend/repair_rv.py`)

Fixes stock-split-corrupted RV30/VRP values in both SQLite and CSVs. Run this when you see absurd RV30 spikes (e.g., 657% instead of ~30%) after a stock split.

**How it works:** Fetches fresh adjusted bars, detects splits via single-day |log-return| > 0.5 (~65% move), recomputes RV30 and VRP for affected dates, updates both `daily_iv` rows and `data/daily/{TICKER}.csv`.

```bash
cd backend
python repair_rv.py --tickers NFLX --dry-run     # Preview changes
python repair_rv.py --tickers NFLX               # Apply fix
python repair_rv.py --tickers NFLX,AMZN          # Multiple tickers
python repair_rv.py --all                         # Entire universe
```

**When to run:** After a stock split, if RV30 or VRP values look nonsensical for that ticker. The scan pipeline now fetches adjusted bars, so new data is fine — this fixes historical rows computed from unadjusted bars.

### Verify (`utils/verify_metrics.py`)

Independent cross-check of dashboard metrics against Yahoo Finance. Runs 14 checks per ticker (price ±1%, RV ±3 vol points, VRP formula consistency, IV range, ATR ±5%, SPY IV vs VIX ±5 pts) plus earnings date verification (±3-7 days tolerance).

```bash
python utils/verify_metrics.py --verbose                              # All tickers
python utils/verify_metrics.py --tickers SPY,GOOG --api-url http://localhost:8030
```

**Automatic vs. manual:** Post-scan, `main.py` runs earnings verification automatically (Yahoo override on >5-day FMP discrepancy). The full metrics verification is manual — run it after data fixes or when metrics look suspicious.

**Output:** Colored PASS/WARN/FAIL per check. Results stored in `verification_results` and `earnings_verification_results` tables.

---

## Tests

Manual test suite, no CI. Run after modifying `calculator.py`, `scorer.py`, or `filter_liquid_contracts()`.

```bash
cd backend
python test_calculator.py                         # 5 tests
python -m pytest test_liquidity_filter.py -v      # 9 tests
```

| Test file | Tests | What it covers |
|-----------|-------|----------------|
| `test_calculator.py` | 5 | RV computation (10/20/30/60-day), ATM IV interpolation, IV rank edge cases, scoring (SELL + DANGER scenarios), database round-trip |
| `test_liquidity_filter.py` | 9 | Bid/ask spread filter (50% threshold), zero-bid rejection, boundary cases, integration impact on skew and ATM IV |

---

## Operational Gotchas

**SGT timezone host.** The production host is in UTC+8. All trading logic uses ET explicitly via `zoneinfo.ZoneInfo("America/New_York")`. Any new time-sensitive code must pass the timezone — `datetime.now()` without `tz=` returns SGT. See [fragile-seams.md § Timezone Seams](../3-guardrails/fragile-seams.md#host-timezone-vs-trading-timezone).

**Earnings counter resets on restart.** The daily limit for `POST /api/earnings/refresh` is in-memory (`_earnings_refresh_tracker`). Container restart, Docker rebuild, or uvicorn reload resets it to zero.

**Frontend build-time BACKEND_URL.** The API proxy destination is baked into the Next.js build via `BACKEND_URL` arg. Changing the backend address requires rebuilding the frontend container.

**Rate limit is 10/min.** The MarketData.app token bucket is set to 10 calls/min (API supports 50). Scans take ~13 minutes. See [ADR-005](../3-guardrails/decisions/005-rate-limit-10-per-minute.md) for why.
