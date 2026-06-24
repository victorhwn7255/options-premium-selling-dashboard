<a id="readme-top"></a>

<div align="center">

<img src="assets/banner-1.png" alt="Theta Harvest" width="100%">

<p><em>Most retail traders buy options and lose. <b>Theta Harvest</b> helps you sell them — scoring where the premium-selling edge is real (and where it'll get you killed) <b>0–100</b>, every trading day.</em></p>

<p>
<img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12">
<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
<img src="https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" alt="Next.js 14">
<img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript">
<img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
<img src="https://img.shields.io/badge/License-MIT-C47B5A?style=for-the-badge" alt="MIT License">
</p>

<p>
<a href="https://theta.thevixguy.com"><b>🌐 Live Demo</b></a> &nbsp;·&nbsp;
<a href="#-why--the-problem-were-solving">🎯 Why</a> &nbsp;·&nbsp;
<a href="#-what--the-edge--the-framework">🧠 What</a> &nbsp;·&nbsp;
<a href="#-how--how-its-built--how-to-use-it">🚀 Run it</a>
</p>

<!-- 🎬 Demo GIF coming soon — drop a screen recording of a scan → ticker drill-down at assets/demo.gif and uncomment:
<img src="assets/demo.gif" alt="Theta Harvest demo" width="100%">
-->
<sub>🎬 Live walkthrough GIF coming soon — until then, see it running at <a href="https://theta.thevixguy.com">theta.thevixguy.com</a>.</sub>

</div>

---

## Contents

[🎯 Why](#-why--the-problem-were-solving) ·
[🧠 What](#-what--the-edge--the-framework) ·
[⚙️ How](#-how--how-its-built--how-to-use-it) ·
[✨ Highlights](#-highlights) ·
[🛠 Built With](#-built-with) ·
[🗺 Roadmap](#-roadmap) ·
[🙏 Acknowledgments](#-acknowledgments)

---

## 🎯 Why — the problem we're solving

Retail traders lose at options because they're playing the hardest game on the board. Buy a call or a put and you have to be right about **three things at once** — direction, timing, *and* magnitude — against market makers who price all three for a living. Most of those bets expire out of the money. It's a lottery ticket dressed up as a strategy.

There's one edge a retail trader actually has, and it's the same one the casino has: **stop buying the ticket — start selling it.** Be the house. Options are systematically *overpriced* — implied volatility overstates the moves that actually happen **~80% of the time**, because people overpay for protection they rarely need. Sell that overpriced insurance and the fear premium decays into your account every single day as **theta** (time value). Sell **puts** specifically and you get paid a second time, for the downside **skew** the market bids up out of habit. That gap between fear and reality has a name — the **Volatility Risk Premium** — and it's a real, repeatable edge.

So why doesn't everyone do it? Because selling premium *blind* is how accounts blow up. Sell into a falling knife — backwardation, an earnings event, a volatility spike — and a single trade erases months of patient income. **The hard part was never placing the trade. It's knowing *when* the edge is real and when to sit on your hands.** That is the entire job Theta Harvest does for you: it scans the market every day, scores the edge, and is just as disciplined about telling you **NO** as it is about telling you **GO**.

> Built for quant-minded options sellers who want a systematic read on premium-selling conditions — and as a working, end-to-end example of a **data → scoring → dashboard** product.

## 🧠 What — the edge & the framework

Theta Harvest scans a curated universe of **33 liquid US stocks and ETFs** after every market close, fuses **five volatility signals** into a single **0–100 edge score**, and surfaces the names where the premium is fattest *and* the market structure actually supports harvesting it. It doesn't predict direction — it measures *how favorable* selling conditions are right now, and steps aside when they aren't.

**The five signals — one score:**

| Signal | Max | What it answers |
|---|--:|---|
| **VRP Quality** | 30 | Is implied vol genuinely rich vs. what's actually realized? *(the core edge)* |
| **IV Percentile** | 25 | Are these options expensive vs. their own 1-year history? |
| **Term Structure** | 20 | Is the curve calm (contango = good) or inverted (backwardation = danger)? |
| **RV Stability** | 15 | Is realized vol settling down, or accelerating into a storm? |
| **Skew** | 10 | Is there real 25-delta put demand to get paid for? |

Purely additive, no penalties — the number reads cleanly as *"how much edge is present?"*

**The discipline that keeps you alive.** A high score is only half the system. Three hard gates and a market-wide regime read can veto any trade, no matter how juicy the premium looks:

- 🚫 **Earnings within 14 days → `SKIP`.** Binary gap risk no premium pays for.
- 🚫 **Deep backwardation (DANGER regime) → `AVOID`.** The market is pricing a real event — don't fight it.
- 🚫 **Negative VRP → score capped at 44.** If realized vol is beating implied, there's no insurance to sell.
- 🏀 **Market Regime** sets the whole-table posture with an at-a-glance, NBA-themed read: **THE FINALS** (widest edge — be aggressive) · **THE PLAYOFFS** (normal) · **REGULAR SEASON** (defined-risk only) · **OFF SEASON** (go to cash).

**Two ways to express the edge:** **Naked Puts** — the full 33-name scan where the edge lives — and **Credit Put Spreads**, a defined-risk version of the *same* edge scoped to SPY / QQQ / IWM, with construction filters and a 2-day confirmation before it ever says sell.

**What you act on:** **`SELL` ≥ 65** · **`CONDITIONAL` ≥ 45** · **`AVOID` / `SKIP`** when the structure turns hostile.

> Go deeper: the full scoring engine in [`context/1-domain/scoring-and-strategy.md`](context/1-domain/scoring-and-strategy.md) · the strategy thesis in [`references/strategy.md`](references/strategy.md) · defined-risk spreads in [`references/credit-put-spreads.md`](references/credit-put-spreads.md).

## ⚙️ How — how it's built & how to use it

**How it works.** A **FastAPI** backend is the single source of truth — it fetches the data, computes every metric, runs the composite score, and executes the daily scan after the close (6:30 PM ET). A **Next.js** frontend renders the dashboard and passes the backend's scores through *unchanged* — one brain, no double math. Persistence is **SQLite (WAL) + per-ticker CSVs**; the production app runs on **AWS Lightsail** behind a **Cloudflare Tunnel**, and a self-healing job logs each day's metrics plus an AI-written market briefing without anyone touching it.

> Architecture deep-dive: [`context/2-system/architecture.md`](context/2-system/architecture.md).

**How to use it — run the whole thing in one command:**

```bash
git clone https://github.com/victorhwn7255/options-premium-selling-dashboard.git
cd options-premium-selling-dashboard

export MARKETDATA_TOKEN=your_token_here   # required
export FMP_API_KEY=your_key_here          # optional (earnings dates)

docker compose up --build
```

- **Dashboard** → http://localhost:3000 — read the leaderboard, check the regime banner, click any ticker to see its score breakdown and suggested structure (delta · DTE · spread width).
- **Backend API** → http://localhost:8030

<details>
<summary><b>Local dev (without Docker) &amp; tests</b></summary>

```bash
# backend
cd backend && pip install -r requirements.txt
export MARKETDATA_TOKEN=your_token_here
python main.py                                # uvicorn on :8000

# frontend
cd frontend && npm install && npm run dev     # :3000

# tests
cd backend
python test_calculator.py
python -m pytest test_liquidity_filter.py -v
```
</details>

<!-- 📸 Screenshots — drop dashboard captures into assets/ and uncomment:
<p align="center">
  <img src="assets/screenshot-leaderboard.png" alt="Leaderboard" width="49%">
  <img src="assets/screenshot-detail.png" alt="Ticker detail" width="49%">
</p>
-->

## ✨ Highlights

- **0–100 edge score** from five additive signals — one number, no black box.
- **Two-layer risk control** — per-ticker regime (`NORMAL` / `CAUTION` / `DANGER`) under an NBA-themed market regime.
- **Automated daily scan** of 33 tickers across 7 sectors, every trading day after the close.
- **Credit Put Spreads tab** — defined-risk expression of the same edge with construction + execution filters and 2-day confirmation.
- **Trend at a glance** — day-over-day deltas plus a GitHub-style **VRP activity grid**.
- **Self-healing history automation** that logs daily metrics and an AI-written briefing — no babysitting.
- **Dark / light theme**, responsive dashboard.

## 🛠 Built With

| Layer | Stack |
|---|---|
| **Backend** | Python 3.12 · FastAPI · NumPy · Pydantic · APScheduler · SQLite (WAL) |
| **Frontend** | Next.js 14 · React 18 · TypeScript · Recharts · Tailwind CSS |
| **Infra** | Docker Compose · Cloudflare Tunnel · AWS Lightsail |
| **Data** | [MarketData.app](https://www.marketdata.app) (options/stocks) · [FMP](https://financialmodelingprep.com) (earnings) · [yfinance](https://github.com/ranaroussi/yfinance) (VIX / VIX3M / VVIX) |

## 🗺 Roadmap

- [ ] **Journal tab** — trade entry, exits, P/L, score-at-entry (Phase 6)
- [ ] **Credit Put Spreads** universe expansion (EEM / TLT / XLE)
- [ ] **Portfolio-level Greeks** aggregation

## 🙏 Acknowledgments

- [MarketData.app](https://www.marketdata.app) — options & stock market data
- [Financial Modeling Prep](https://financialmodelingprep.com) — earnings dates
- [yfinance](https://github.com/ranaroussi/yfinance) — VIX / VIX3M / VVIX overlay

---

<div align="center">

Released under the **MIT License**.

<sub><a href="#readme-top">↑ Back to top</a></sub>

</div>
