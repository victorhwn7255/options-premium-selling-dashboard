# Theta Harvest

Volatility premium scanner for options sellers. Identifies high-probability premium selling opportunities using IV rank, volatility risk premium (VRP), term structure analysis, and regime detection.

**Data powered by [MarketData.app](https://www.marketdata.app)**. Earnings dates from [FMP](https://financialmodelingprep.com).

## Architecture

```
theta-harvest/
├── backend/          # FastAPI — data fetching, vol calculations, scoring
│   ├── main.py       # FastAPI app, endpoints, ticker universe, daily scan gate, cron scheduler
│   ├── marketdata_client.py  # MarketData.app API client (options + stocks)
│   ├── fmp_client.py # FMP API client for earnings dates (SQLite-cached)
│   ├── calculator.py # RV, IV, term structure, skew, ATM Greeks, ATR14
│   ├── scorer.py     # Opportunity scoring engine (0–100)
│   ├── csv_store.py  # CSV persistence for daily metrics + option quotes
│   ├── models.py     # Pydantic response models
│   ├── database.py   # SQLite for historical IV, scan results, earnings cache
│   └── data/         # SQLite database + CSVs (auto-created, gitignored)
├── frontend/         # Next.js 14 + Tailwind CSS
│   ├── src/app/      # App Router pages
│   ├── src/components/  # React components
│   ├── src/hooks/    # useTheme, useKeyboard, useCssColors
│   └── src/lib/      # API client, types, scoring
└── assets/           # Favicon (θ symbol)
```

## Subscription Requirements

| Service | Tier | Cost | Used For |
|---------|------|------|----------|
| MarketData.app | **Starter** | $12/mo | Options chains (IV, Greeks), stock candles, stock quotes |
| FMP | **Free** | $0 | Earnings dates |

**Total: $12/month**

## Quick Start

### Option A: Docker (recommended)

```bash
cp .env.example .env
# Edit .env with your API tokens

docker compose up --build
```

Backend at `http://localhost:8030`, frontend at `http://localhost:3000`.

The bind mount (`./backend/data:/app/data`) persists your IV history database and CSVs across restarts.

### Option B: Local development

**Backend:**

```bash
cd backend
pip install -r requirements.txt
export MARKETDATA_TOKEN=your_token_here
export FMP_API_KEY=your_key_here    # Optional
python main.py
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | System status check |
| GET | `/api/scan/latest` | Most recent cached scan result |
| POST | `/api/scan` | Trigger full scan (once per day) |
| GET | `/api/scan/history` | Metadata for recent scans |
| GET | `/api/ticker/{ticker}/history` | Historical IV/RV series |
| GET | `/api/universe` | List configured tickers |
| GET | `/api/earnings/remaining` | Earnings refresh remaining count today |
| POST | `/api/earnings/refresh` | Re-fetch earnings dates from FMP (3x/day) |

## Rate Limiting

- **Full scan**: Once per day (ET timezone). Subsequent requests return cached results.
- **Earnings refresh**: 3 times per day. UI shows remaining count.
- **Automated scan**: Cron runs at 6:30 PM ET, Mon–Fri.

## Design System

The frontend uses the **Anthropic Warm Humanist** design system:

- **Typography**: Source Serif 4 (headings), General Sans (UI), JetBrains Mono (data)
- **Palette**: Terracotta primary (#C47B5A), sage secondary (#7D8C6E), warm earth tones
- **Texture**: Risograph-style grain overlay
- **Dark mode**: Full dark theme via CSS custom properties
- **Favicon**: Theta (θ) symbol on terracotta rounded square

## Customization

### Adding/removing tickers

Edit the `UNIVERSE` dict in `backend/main.py`. Each ticker needs a display name and sector:

```python
"TICKER": {"name": "Display Name", "sector": "Sector"},
```

Works identically with individual stocks and ETFs.

### Adjusting scoring thresholds

Default filter thresholds are in `frontend/src/lib/types.ts` (`DEFAULT_FILTERS`) and can be adjusted live in the dashboard UI.

## Important Notes

- **Paper trade first**: Run 2–3 months of paper trades before committing capital
- **Not a signal generator**: This tool's primary value is preventing bad trades
- **Earnings awareness**: Earnings dates are fetched from FMP and displayed as DTE — always verify independently
- **IV Rank bootstrapping**: On first run, IV Rank defaults to 50%. After ~20 trading days of daily scans, it becomes meaningful. Full calibration takes ~252 trading days.
