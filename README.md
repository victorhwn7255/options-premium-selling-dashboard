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

There's one edge a retail trader actually has, and it's the same one the casino has: **stop buying the ticket — start selling it.** Be the house. Options are systematically *overpriced* — implied volatility overstates the moves that actually happen **~70% of the time** (measured on this exact 33-name universe, not folklore), because people overpay for protection they rarely need. Sell that overpriced insurance and the fear premium decays into your account every single day as **theta** (time value). Sell **puts** specifically and you get paid a second time, for the downside **skew** the market bids up out of habit. That gap between fear and reality has a name — the **Volatility Risk Premium** — and it's a real, repeatable edge.

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

**The discipline that keeps you alive.** A high score is only half the system. Hard gates and a market-wide regime read can veto any trade, no matter how juicy the premium looks:

- 🚫 **Earnings within 14 days → `SKIP`.** Binary gap risk no premium pays for. *(Single names only — ETFs don't have earnings.)*
- 🚫 **Deep backwardation (DANGER regime) → `AVOID`.** The market is pricing a real event — don't fight it.
- 🚫 **Realized vol accelerating (> 1.10) → forced `CAUTION`.** A storm that's still building doesn't care how rich the premium looks.
- 🚫 **Negative VRP → score capped at 54.** If realized vol is beating implied, there's no insurance to sell.
- 🚫 **Premium too thin (VRP ratio < 1.15) → `WATCHLIST`.** Clean structure, not enough pay — no position offered until the premium expands.
- 🏀 **Market Regime** sets the whole-table posture with an at-a-glance, NBA-themed read: **THE FINALS** (widest edge — be aggressive) · **THE PLAYOFFS** (normal) · **REGULAR SEASON** (defined-risk only) · **OFF SEASON** (go to cash).

**Two ways to express the edge:** **Naked Puts** — the full 33-name scan where the edge lives — and **Credit Put Spreads**, a defined-risk version of the *same* edge scoped to SPY / QQQ / IWM, with construction filters and a 2-day confirmation before it ever says sell.

**What you act on:** **`SELL` ≥ 65** · **`CONDITIONAL` ≥ 45** · **`WATCHLIST`** (setup clean, premium too thin — wait) · **`AVOID` / `SKIP`** when the structure turns hostile.

**What's next.** A **forward-looking v2 engine** already runs silently beside all of this — a volatility *forecaster* (σ_fwd, trained on 10 years × 33 tickers) that measures the premium against where vol is *going* instead of where it's been, with hysteresis-damped risk gates. It's compared against v1 every trading day and changes **no live decision** until it earns cutover with evidence (see the [Roadmap](#-roadmap)).

> Go deeper: the full scoring engine in [`context/1-domain/scoring-and-strategy.md`](context/1-domain/scoring-and-strategy.md) · the strategy thesis in [`references/strategy_v1.md`](references/strategy_v1.md) · the v2 upgrade thesis in [`references/strategy_v2.md`](references/strategy_v2.md) · defined-risk spreads in [`references/credit-put-spreads.md`](references/credit-put-spreads.md).

## ⚙️ How — how it's built & how to use it

**How it works.** A **FastAPI** backend is the single source of truth — it fetches the data, computes every metric, runs the composite score, and executes the daily scan after the close (6:30 PM ET). A **Next.js** frontend renders the dashboard and passes the backend's scores through *unchanged* — one brain, no double math. Persistence is **SQLite (WAL) + per-ticker CSVs**; the production app runs on **AWS Lightsail** behind a **Cloudflare Tunnel**, and a self-healing job writes five daily history logs — the metrics table, an AI-written market briefing, the spreads snapshot, and the two v2 shadow-divergence records — without anyone touching it.

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
python test_theta_core.py      # v2 golden master (1e-9 vs the reference implementation)
python test_estimators.py      # v2 estimators
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
- **Automated daily scan** of 33 tickers across 10 sectors, every trading day after the close.
- **A forward-looking v2 engine currently runs in shadow** — it changes no live decision until it earns cutover with evidence.
- **`[HUMAN | MACHINE]` toggle** — one click flips the dashboard into a monospace, full-precision, copy-paste-ready render of everything the API returns. Built for scripts, scrapers, and AI agents.
- **Credit Put Spreads tab** — defined-risk expression of the same edge with construction + execution filters and 2-day confirmation.
- **Trend at a glance** — day-over-day deltas plus a GitHub-style **VRP activity grid**.
- **Self-healing history automation** — five daily logs (metrics, AI-written briefing, spreads, v2 shadow divergence) with no babysitting.
- **Dark / light theme**, responsive dashboard.

## 🛠 Built With

| Layer | Stack |
|---|---|
| **Backend** | Python 3.12 · FastAPI · NumPy · Pydantic · APScheduler · SQLite (WAL) |
| **Frontend** | Next.js 14 · React 18 · TypeScript · Recharts · Tailwind CSS |
| **Infra** | Docker Compose · Cloudflare Tunnel · AWS Lightsail |
| **Data** | [MarketData.app](https://www.marketdata.app) (options/stocks) · [FMP](https://financialmodelingprep.com) (earnings) · [yfinance](https://github.com/ranaroussi/yfinance) (VIX family + 10-year OHLC history seed) |

## 🗺 Roadmap

The active work is a staged **v1 → v2 engine upgrade**. The core idea: v1 measures the premium against where volatility *has been* (trailing RV); v2 measures it against where volatility is *going* — a forward forecast (σ_fwd) trained on 10 years × 33 tickers, with hysteresis-damped risk gates that don't flip-flop day to day. v1 keeps making every live decision the whole way; each phase has to earn the next with evidence, not vibes:

- [x] **Phase A — silent** *(live now)*: v2 runs in shadow beside every scan; a daily divergence log records where the two engines disagree and which one was right to.
- [ ] **Phase B — visible, but advisory**: calibrate v2's thresholds against v1's track record; show v2's read in the UI. v1 still decides.
- [ ] **Phase C — position-aware**: positions, sizing caps, portfolio-level gates.
- [ ] **Phase D — self-measuring**: track what each engine *would have* traded, head to head.
- [ ] **Phase E — cutover**: one flag flips authority to v2, with a 30-session dual-run rollback window.
- [ ] **Phase F — self-improving**: pre-registered trials become the only path to changing a threshold.

Still queued behind the arc: **Journal tab** (trade entry, exits, P/L, score-at-entry) · **Credit Put Spreads** universe expansion (EEM / TLT / XLE) · **portfolio-level Greeks** aggregation.

## 🙏 Acknowledgments

- [MarketData.app](https://www.marketdata.app) — options & stock market data
- [Financial Modeling Prep](https://financialmodelingprep.com) — earnings dates
- [yfinance](https://github.com/ranaroussi/yfinance) — VIX / VIX3M / VVIX overlay

---

<div align="center">

Released under the **MIT License**.

<sub><a href="#readme-top">↑ Back to top</a></sub>

</div>
