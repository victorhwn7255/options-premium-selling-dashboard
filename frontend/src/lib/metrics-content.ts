// Glossary content for the "How to use" guide. Regrouped by role (signals → vetoes → decisions →
// context → v2). Every threshold pill is a FUNCTION of the backend's GET /api/thresholds payload, so
// the pills cannot drift from the code (2026-09-03). Analogies / formulas / case studies render
// behind a "more" toggle.

import type { Thresholds } from './types';

export interface MetricReading {
  label: string;
  color: 'good' | 'ok' | 'bad' | 'neutral';
}

export interface MetricDefinition {
  id: string;
  emoji: string;
  name: string;
  tag: string;
  section: 'signals' | 'vetoes' | 'decisions' | 'context' | 'v2';
  explain: string;                                              // HTML
  whatToDo?: string;                                            // plain
  readings: MetricReading[] | ((t: Thresholds) => MetricReading[]);
  analogy?: string;                                             // HTML
  formulaLabel?: string;
  formulas: string[] | ((t: Thresholds) => string[]);
  example?: { tag: string; body: string };
}

const pct = (x: number, d = 0) => `${(x * 100).toFixed(d)}%`;

export const METRICS: MetricDefinition[] = [
  // ── Signals (the five score components) ─────────────────────────────────
  {
    id: 'rv', emoji: '🎢', name: 'Realized Volatility (RV)', tag: 'RV10 · RV20 · RV30', section: 'signals',
    explain: 'How much the stock has <strong>actually</strong> been moving, annualized, over the last 10 / 20 / 30 trading days. RV30 is the denominator of v1’s VRP; RV10 / RV30 is RV acceleration.',
    readings: [{ label: 'An input, not a signal on its own — it only matters against IV', color: 'neutral' }],
    analogy: 'A player’s shooting stats: RV10 is the last two games (streaky), RV30 the last month (reliable).',
    formulas: ['log_returns = ln(close[t] / close[t−1])', 'RV_N = stdev(log_returns, N days, ddof=1) × √252 × 100'],
  },
  {
    id: 'iv', emoji: '🔮', name: 'Implied Volatility (IV)', tag: '30-day ATM', section: 'signals',
    explain: 'How much the options market <strong>expects</strong> the stock to move over the next 30 days — the price of fear, baked into the option premium.',
    whatToDo: 'Never trade on the level. Compare it to realized (VRP) or to the forecast (FVRP); and if IV just jumped, assume a spike is starting, not that a bargain appeared.',
    readings: [
      { label: 'IV only matters relative to realized / forecast vol — the level alone predicts nothing', color: 'neutral' },
      { label: 'A sudden IV jump often marks the START of a vol spike — check the IV-vs-RV chart', color: 'ok' },
    ],
    analogy: 'The Vegas line before a game — a prediction that is usually a little too high. The strategy bets on that "little".',
    formulaLabel: 'How we calculate it',
    formulas: t => [
      `1. Take the two expirations nearest 30 days`, `2. Strikes within 3% of spot (ATM), ≥ ${t.data_quality.min_atm_contracts} liquid contracts or NO DATA`,
      '3. Average put + call IV at the nearest strike', '4. Interpolate to exactly 30 days',
    ],
  },
  {
    id: 'vrp', emoji: '💰', name: 'Volatility Risk Premium (VRP)', tag: 'Core signal', section: 'signals',
    explain: '<strong>The whole reason the strategy works.</strong> The gap between what options charge (IV) and what the stock then does (RV). Positive most of the time — people overpay for protection — and that overpayment is what a premium seller harvests. The scorer gates on the <em>ratio</em>; the absolute points shape structure and delta.',
    whatToDo: 'Ratio inside the sweet spot, plus a few absolute points of cushion. Treat very high ratios as a warning, not a bonus.',
    readings: t => [
      { label: `Ratio ≥ ${t.v1_scorer.vrp_ratio_dead_zone} = tradeable premium (below → WATCHLIST)`, color: 'good' },
      { label: `Ratio ${t.v1_scorer.vrp_ratio_dead_zone}–1.45 = the sweet spot`, color: 'good' },
      { label: `Ratio ≥ ${t.v1_scorer.vrp_ratio_cap} = suspicious — often the start of a vol spike, not extra edge`, color: 'ok' },
      { label: `VRP < 0 = no edge (score capped at ${t.v1_scorer.negative_vrp_cap}, never SELL)`, color: 'bad' },
    ],
    analogy: 'The weather app says 80% chance of a storm, so everyone buys a $20 umbrella. It drizzles. The umbrella sellers made money because people <em>overpaid for protection</em>.',
    formulas: t => [
      'VRP = IV(30d) − RV(30d)                (vol points)',
      'VRP ratio = IV(30d) / RV(30d)          (what the scorer gates on)',
      `VRP Quality points = clamp(0, ${t.v1_scorer.vrp_points}, (ratio − ${t.v1_scorer.vrp_ratio_dead_zone}) × ${(t.v1_scorer.vrp_points / (t.v1_scorer.vrp_ratio_cap - t.v1_scorer.vrp_ratio_dead_zone)).toFixed(2)})`,
    ],
    example: { tag: 'Jun 4, 2026', body: 'XLF printed a VRP of <strong>7.3</strong> — the widest clean premium on the board — with deep contango (slope 0.86) and a score of 74. The scanner called SELL and the briefing sized it: “Quarter on Day-1, 30–45 DTE.” A real, measured gap between what options charged and what the stock then moved.' },
  },
  {
    id: 'iv-pctl', emoji: '📏', name: 'IV Percentile & IV Rank', tag: '1-year lookback', section: 'signals',
    explain: 'Where today’s IV sits against the last year. Percentile = share of days with lower IV (robust to outliers — the scorer uses it). Rank = min-max position (used for the construction hint, not the score).',
    whatToDo: 'Do not chase it. It is a modest score component and has no timing power on its own.',
    readings: t => [
      { label: `≥ ${t.v1_scorer.iv_pct_floor} = earns IV-percentile points (0–${t.v1_scorer.iv_pct_points}, modest weight)`, color: 'ok' },
      { label: `< ${t.v1_scorer.iv_pct_floor} = no IV-percentile points`, color: 'bad' },
      { label: 'IV Rank ≥ 80 changes the construction hint (closer delta, shorter DTE) — not the edge', color: 'neutral' },
    ],
    analogy: 'Height percentile at school: 80th means taller than 80% of the class. Useful context; it does not tell you who wins the game.',
    formulas: t => [
      'IV Percentile = (# days with IV < today) / total days × 100',
      'IV Rank = (today − 1y min) / (1y max − 1y min) × 100',
      `Points = clamp(0, ${t.v1_scorer.iv_pct_points}, (percentile − ${t.v1_scorer.iv_pct_floor}) × ${(t.v1_scorer.iv_pct_points / (100 - t.v1_scorer.iv_pct_floor)).toFixed(3)})`,
    ],
  },
  {
    id: 'term-structure', emoji: '⛰️', name: 'Term Structure (Slope)', tag: 'Front IV / Back IV', section: 'signals',
    explain: 'Near-term IV divided by far-term IV. Below 1.0 = <em>contango</em> (normal: more time, more uncertainty). Above 1.0 = <em>backwardation</em> — the market is pricing trouble <strong>right now</strong>. It scores points below 1.0 and becomes a veto above it.',
    whatToDo: 'Prefer ≤ 0.95. Above the CAUTION line you are defined-risk only; above DANGER you do not sell.',
    readings: t => [
      { label: `≤ ${t.v1_scorer.term_hinges[0]} = deep contango (max ${t.v1_scorer.term_points[0]} pts)`, color: 'good' },
      { label: `${t.v1_scorer.term_hinges[0]}–${t.v1_scorer.term_hinges[1]} = contango (favourable)`, color: 'good' },
      { label: `${t.v1_scorer.term_hinges[1]}–${t.regime_per_ticker.caution_slope} = flat / mild backwardation — few points, no veto yet`, color: 'ok' },
      { label: `> ${t.regime_per_ticker.caution_slope} = CAUTION (defined risk only) · > ${t.regime_per_ticker.danger_slope} = DANGER → AVOID`, color: 'bad' },
    ],
    analogy: 'Renting an umbrella: a week normally costs more than a day. If <em>today</em> suddenly costs more than the week, a storm is expected now. That is backwardation.',
    formulas: t => [
      'slope = shortest-tenor IV / longest-tenor IV (8 tenors, 1W … 1Y)',
      `points: ${t.v1_scorer.term_points[0]} at ≤ ${t.v1_scorer.term_hinges[0]} → ${t.v1_scorer.term_points[1]} at ${t.v1_scorer.term_hinges[1]} → 0 at ≥ ${t.v1_scorer.term_hinges[2]}`,
    ],
    example: { tag: 'Jun 10, 2026', body: 'The universe’s average slope crossed 1.0 for the first time in the logged record (<strong>1.013</strong>), with QQQ at 1.17 and flagged DANGER; average VRP was just +1.1. The briefing: <em>“this is the event, not the harvest — stay flat.”</em>' },
  },
  {
    id: 'rv-accel', emoji: '🚀', name: 'RV Acceleration & RV Accel Status', tag: 'RV10 / RV30 · five-tier chip', section: 'signals',
    explain: 'Is realized vol speeding up or slowing down? Recent (10-day) vs longer (30-day) realized vol. It scores the <strong>RV Stability</strong> points, drives the five-tier <strong>RV Accel Status</strong> chip, and — since July 2026 — is a veto on its own: above the CAUTION line a name cannot print SELL. Rising realized vol is exactly what closes the premium gap you are selling.',
    whatToDo: 'Sell into Good or Excellent. In the backtest, entries at 0.85–1.10 ran PF 4.3; above 1.10 they lost (PF 0.8).',
    readings: t => [
      ...t.rv_accel_status.map((tier, i, arr) => ({
        label: `${i === 0 ? '≤ ' + tier.max : tier.max === null ? '> ' + arr[i - 1].max : `${arr[i - 1].max}–${tier.max}`} = ${tier.label} — ${tier.meaning}`,
        color: (tier.label === 'Excellent' || tier.label === 'Good' ? 'good' : tier.label === 'Acceptable' ? 'ok' : 'bad') as MetricReading['color'],
      })),
      { label: `> ${t.regime_per_ticker.caution_accel} = CAUTION regime on its own (no SELL, defined risk only)`, color: 'bad' },
    ],
    analogy: 'Speedometer vs trip average: doing 90 on a 60 average means the road just got bumpier. The chip reports the road; you decide whether to drive.',
    formulas: t => [
      'RV acceleration = RV10 / RV30',
      `RV Stability points: ${t.v1_scorer.accel_points[0]} at ≤ ${t.v1_scorer.accel_hinges[0]} → ${t.v1_scorer.accel_points[1]} at ${t.v1_scorer.accel_hinges[1]} → 0 at ≥ ${t.v1_scorer.accel_hinges[2]}`,
    ],
    example: { tag: 'Jul 6, 2026', body: 'Average acceleration re-heated to <strong>1.062</strong> and 14 names flipped to CAUTION in one session while the term structure stayed in contango. Realized vol waking up before the options market repriced — exactly what this metric catches and the curve misses.' },
  },
  {
    id: 'skew', emoji: '⚖️', name: '25-Delta Skew', tag: 'Put protection demand', section: 'signals',
    explain: 'How much more expensive downside puts are than at-the-money options. Some skew is healthy — steady insurance demand is premium to sell. Extreme skew means the smart money is paying up for protection, which is a warning, not an opportunity.',
    readings: t => [
      { label: `${t.v1_scorer.skew_nodes[0]}–${t.v1_scorer.skew_nodes[1]} = demand building (points ramp up)`, color: 'ok' },
      { label: `${t.v1_scorer.skew_nodes[1]}–${t.v1_scorer.skew_nodes[2]} = the sweet spot (max ${t.v1_scorer.skew_points} pts)`, color: 'good' },
      { label: `${t.v1_scorer.skew_nodes[2]}–${t.v1_scorer.skew_nodes[3]} = tapering — protection may be informed`, color: 'ok' },
      { label: `> ${t.cps.inherited_gates.extreme_skew} = extreme → AVOID (a hard gate for credit spreads)`, color: 'bad' },
    ],
    analogy: 'If insurers suddenly charge 3× for flood cover in your street, they may know something you don’t.',
    formulas: ['skew = IV(25Δ put) − IV(ATM), at the expiration nearest 30 DTE', 'points: trapezoid 0 → 7 → 12 → 20'],
  },

  // ── Vetoes ───────────────────────────────────────────────────────────────
  {
    id: 'ticker-regime', emoji: '🚦', name: 'Per-ticker regime (NORMAL / CAUTION / DANGER)', tag: 'Veto layer', section: 'vetoes',
    explain: 'Computed beside the score, never inside it. DANGER makes the recommendation <strong>AVOID</strong> regardless of score; CAUTION allows only REDUCE SIZE (defined risk) or NO EDGE. In every backtest DANGER was the one losing cohort and the gates added about half the portfolio’s return — this layer is the part of the system that has earned trust.',
    whatToDo: 'Read the regime before the score. A 90 in DANGER is still AVOID.',
    readings: t => [
      { label: `DANGER: term slope > ${t.regime_per_ticker.danger_slope} → AVOID`, color: 'bad' },
      { label: `CAUTION: slope > ${t.regime_per_ticker.caution_slope}, or RV accel > ${t.regime_per_ticker.caution_accel}, or IV Rank > ${t.regime_per_ticker.caution_ivr} with accel > ${t.regime_per_ticker.caution_ivr_accel}`, color: 'ok' },
      { label: `CAUTION + score ≥ ${t.v1_scorer.reduce_size} → REDUCE SIZE (defined risk); below → NO EDGE`, color: 'ok' },
    ],
    formulas: [],
    example: { tag: 'Ten-year replay, Sept 2026', body: 'Across 2018-02, 2018-Q4, 2020-03, 2022, 2024-08 and 2025-04 the state-machine vetoes alone avoided <strong>64%</strong> of the index sleeve’s tail loss while clearing 70% of clean days; the downside-accel gate alone 57% / 78%. The design catches the tail.' },
  },
  {
    id: 'earnings-gate', emoji: '🚧', name: 'Earnings Gate', tag: 'Hard veto', section: 'vetoes',
    explain: 'If a single name reports within the gate window the score is forced to 0 and the action is <strong>SKIP</strong>, whatever the other metrics say. An earnings gap is binary risk that no premium pays for. ETFs are exempt (no earnings).',
    whatToDo: 'For a naked put, want earnings clear of the whole hold (+5 sessions), not just the gate window; 15–21 days out is small-size territory.',
    readings: t => [
      { label: `≤ ${t.earnings_gate_days} days = gated out, score forced to 0`, color: 'bad' },
      { label: `> ${t.earnings_gate_days} days = score computed normally`, color: 'good' },
    ],
    analogy: 'Benching the star before the playoffs — one game is not worth losing the season.',
    formulas: t => [`if not ETF and days_to_earnings ≤ ${t.earnings_gate_days}: score = 0, action = SKIP`],
  },
  {
    id: 'watchlist', emoji: '👀', name: 'WATCHLIST (premium too thin)', tag: 'Actionability gate', section: 'vetoes',
    explain: 'A SELL or CONDITIONAL score whose VRP <em>ratio</em> sits below the dead zone is demoted to <strong>WATCHLIST</strong>: the structure is clean but the premium is not enough cushion to trade. The score is preserved so you can see the name coming; no position construction is offered.',
    readings: t => [
      { label: `ratio < ${t.v1_scorer.vrp_ratio_dead_zone} on a SELL / CONDITIONAL score → WATCHLIST, no position`, color: 'ok' },
      { label: `negative VRP → score capped at ${t.v1_scorer.negative_vrp_cap}`, color: 'bad' },
    ],
    formulas: [],
  },

  // ── Decisions ────────────────────────────────────────────────────────────
  {
    id: 'composite-score', emoji: '🏆', name: 'Composite Score', tag: '0 – 100', section: 'decisions',
    explain: 'A single 0–100 answer to <em>“how much premium-selling edge is present right now?”</em>, built additively from the five signals. <strong>What it is not:</strong> a ranking. In every test so far (two backtests and the live forward-capture record) it has shown no power to rank one candidate above another — a 72 and a 65 are the same thing. Treat SELL / CONDITIONAL as a <em>candidate list</em>; the vetoes, the environment and the caps decide the trade.',
    whatToDo: 'Use the tier as a gate (is edge present?), never the number as a sort key.',
    readings: t => [
      { label: `≥ ${t.v1_scorer.sell} = SELL PREMIUM — a candidate (NORMAL regime, ratio ≥ ${t.v1_scorer.vrp_ratio_dead_zone})`, color: 'good' },
      { label: `≥ ${t.v1_scorer.conditional} = CONDITIONAL — a weaker candidate`, color: 'ok' },
      { label: `< ${t.v1_scorer.conditional} = NO EDGE — skip`, color: 'bad' },
      { label: `CAUTION → REDUCE SIZE (≥ ${t.v1_scorer.reduce_size}) · DANGER → AVOID, regardless of score`, color: 'neutral' },
    ],
    analogy: 'A pre-flight checklist, not a player rating: it says the plane is airworthy, not which of two airworthy planes flies better. Pick by the weather (regime, RV Accel), not by the checklist score.',
    formulaLabel: 'Formula (backend scoring)',
    formulas: t => [
      `VRP Quality   (0–${t.v1_scorer.vrp_points})  ratio ${t.v1_scorer.vrp_ratio_dead_zone} → 0, ${t.v1_scorer.vrp_ratio_cap} → ${t.v1_scorer.vrp_points}`,
      `IV Percentile (0–${t.v1_scorer.iv_pct_points})  pctl ${t.v1_scorer.iv_pct_floor} → 0, 100 → ${t.v1_scorer.iv_pct_points}`,
      `Term Structure(0–${t.v1_scorer.term_points[0]})  slope ${t.v1_scorer.term_hinges[0]} → ${t.v1_scorer.term_points[0]}, ${t.v1_scorer.term_hinges[1]} → ${t.v1_scorer.term_points[1]}, ${t.v1_scorer.term_hinges[2]} → 0`,
      `RV Stability  (0–${t.v1_scorer.accel_points[0]})  accel ${t.v1_scorer.accel_hinges[0]} → ${t.v1_scorer.accel_points[0]}, ${t.v1_scorer.accel_hinges[1]} → ${t.v1_scorer.accel_points[1]}, ${t.v1_scorer.accel_hinges[2]} → 0`,
      `Skew          (0–${t.v1_scorer.skew_points})  ${t.v1_scorer.skew_nodes.join(' → ')} (trapezoid)`,
      'Total = sum, clamped 0–100; then the negative-VRP cap and the WATCHLIST gate',
    ],
    example: { tag: 'Jun 4, 2026 — why you still read the vetoes', body: 'NKE printed <strong>65 (SELL)</strong> with a “monster” VRP of 27.3 — and the briefing flagged it <em>“SCORE ARTIFACT — ignore”</em>: RV accel 1.36 (Avoid/Wait) and earnings 21 days out. A high score with a screaming accel status is a trap, not a trade.' },
  },
  {
    id: 'position-hints', emoji: '🧭', name: 'Position construction hints', tag: 'Drawer', section: 'decisions',
    explain: 'When a name qualifies, the drawer suggests a delta band, a structure, a DTE window and a notional band, keyed on regime first, then IV Rank and VRP. Suggestions, not orders — and the sizing card’s caps, not the notional band, decide size.',
    whatToDo: 'Within the default band, prefer 25–30Δ in NORMAL regimes (friction amortizes better); enter at 45 DTE.',
    readings: [],
    formulaLabel: 'The table the backend uses',
    formulas: t => t.position_hints.map(h => `${h.condition.padEnd(34)} ${h.delta.padEnd(7)} ${h.dte.padEnd(6)} ${h.notional.padEnd(5)} ${h.structure}`),
  },
  {
    id: 'cps-rules', emoji: '🧱', name: 'Credit Put Spreads — the rules', tag: 'CPS tab', section: 'decisions',
    explain: 'The same volatility edge, expressed with defined risk on the index ETFs. No separate score: the base hard gates are inherited, then construction and execution filters, then the VIX / VIX3M / VVIX overlay, then a <strong>two-day confirmation</strong>. Defined risk does not rescue a hostile regime.',
    whatToDo: 'In REGULAR SEASON this is the only tab you trade from. “Thin premium” means what it says.',
    readings: t => [
      { label: `SELL_CPS: credit/width ≥ ${pct(t.cps.sell_credit_to_width)} and ${t.cps.confirmation_days} consecutive days`, color: 'good' },
      { label: `WATCH_CPS: ≥ ${pct(t.cps.watch_credit_to_width)} or unconfirmed · "Thin premium" < ${pct(t.cps.thin_premium_threshold)}`, color: 'ok' },
      { label: `Overlay DANGER: VIX > VIX3M or VVIX > ${t.cps.vvix_danger} → no SELL_CPS`, color: 'bad' },
      { label: `Legs: bid/ask ≤ ${pct(t.cps.max_bid_ask_ratio)}, OI ≥ ${t.cps.min_open_interest}, volume ≥ ${t.cps.min_volume}`, color: 'neutral' },
    ],
    formulas: t => [
      `Universe: ${t.cps.universe.join(', ')} · DTE ${t.cps.min_dte}–${t.cps.max_dte} (target ${t.cps.target_dte}) · short delta ${t.cps.min_short_delta}–${t.cps.max_short_delta}`,
      `Exits: profit target ${pct(t.cps.profit_target_frac)} · time ${t.cps.time_exit_dte} DTE · defensive ${t.cps.defensive_mark_multiple}× credit · pin risk ≤ ${t.cps.pin_risk_dte} DTE · event ≤ ${t.cps.event_risk_dte} DTE`,
      `High credit/width warning > ${pct(t.cps.high_credit_to_width_warning)} (verify regime, skew, accel)`,
    ],
  },
  {
    id: 'sizing-caps', emoji: '🧮', name: 'Sizing card & the five caps', tag: 'Portfolio / Risk', section: 'decisions',
    explain: 'The sizing card shows the full arithmetic — quarter-Kelly base × risk dial × opportunity dial ÷ margin — and the <strong>binding cap</strong>. Caps reject, never trim: the card returns the largest compliant size and names the cap that binds. The stress panel reprices the whole book at a crash scenario every night.',
    whatToDo: 'f* = 0 means the Kelly seed sees no growth-optimal size — take the smallest cap-compliant size, not the largest.',
    readings: t => [
      { label: `Book stressed loss ≤ ${pct(t.sizing.cap_book_stress_frac)} at spot × ${t.sizing.stress_spot_mult}, IV × ${t.sizing.stress_iv_mult}`, color: 'bad' },
      { label: `Total margin ≤ ${pct(t.sizing.cap_margin_frac)} · notional ≤ ${pct(t.sizing.cap_notional_frac)}`, color: 'ok' },
      { label: `Per name: margin ≤ ${pct(t.sizing.cap_name_margin_frac)} · stressed loss ≤ ${pct(t.sizing.cap_name_stress_frac, 1)}`, color: 'ok' },
      { label: `φ = ${t.sizing.kelly_fraction} (quarter-Kelly) · f* seed = ${t.sizing.f_star_seed ?? '—'}`, color: 'neutral' },
    ],
    formulas: t => [
      'contracts = floor(equity × φ × f* × R × O ÷ margin per contract), then caps',
      `R (risk dial) ∈ [${t.sizing.dial_R_bounds.join(', ')}] = median forecast downside vol ÷ current · O (opportunity) ∈ [${t.sizing.dial_O_bounds.join(', ')}] from the FVRP z-score`,
      'The stress scenario is a convention, not a worst case — priced per name, no cross-name correlation.',
    ],
  },
  {
    id: 'exit-flags', emoji: '🚪', name: 'Journal exit flags', tag: 'Portfolio / Risk', section: 'decisions',
    explain: 'Every open position is marked after the 18:30 ET scan and the strategy’s own exit rules are re-evaluated. The flags are the rules — there is deliberately <strong>no stop-loss</strong>; the caps make the implicit stop unreachable.',
    whatToDo: 'Two flags saying leave is a decision already made. Write the exit plan at entry so the flags can hold you to it.',
    readings: t => [
      { label: `PROFIT_TARGET: capture ≥ ${pct(t.exits.profit_target)} (${pct(t.exits.profit_target_rv_rising)} when RV accel > ${t.exits.rv_rising_accel} or CAUTION)`, color: 'good' },
      { label: `TIME_EXIT: DTE ≤ ${t.exits.time_exit_dte}`, color: 'good' },
      { label: `DANGER_UNDERWATER: DANGER and mark ≥ ${t.exits.danger_underwater_mult}× credit → the only forced loss exit`, color: 'bad' },
      { label: `SPREAD_AWARE_DECAY: premium < ${t.exits.spread_aware_premium_mult}× spread, > ${t.exits.spread_aware_sigma_mult}σ OTM, no gate → decay to ~${t.exits.spread_aware_decay_to_dte} DTE`, color: 'ok' },
      { label: `TESTED: spot at/below the short strike or |Δ| ≥ ${t.exits.tested_delta}`, color: 'ok' },
    ],
    formulas: [],
    example: { tag: 'GLD 345P, Aug–Sep 2026', body: 'Ninety-five percent captured, the plan date four days past, PROFIT_TARGET and TIME_EXIT both raised for nineteen straight sessions — and the position was still open. The flags were right on day one; the narrative kept finding reasons. That is what this card exists to prevent.' },
  },

  // ── Context (display-only trade metrics) ─────────────────────────────────
  {
    id: 'greeks', emoji: '⌛', name: 'ATM Greeks: Theta & Vega', tag: 'θ per day · ν per 1% IV', section: 'context',
    explain: '<strong>Theta</strong> is the premium that decays into your pocket each day; <strong>vega</strong> is how much the option moves per 1-point IV change — your risk. The drawer shows θ/ν: more decay per unit of vol exposure is better.',
    readings: [{ label: 'Display only — not scored', color: 'neutral' }],
    formulas: ['θ = daily time decay of the ATM option', 'ν = price change per 1% IV move', 'θ/ν = |theta| / |vega|'],
  },
  {
    id: 'atr', emoji: '📐', name: 'ATR-14', tag: 'Dollar movement', section: 'context',
    explain: 'The average daily range in dollars over 14 days. The CPS builder uses it to size spread widths (0.75–1.5× ATR).',
    readings: [{ label: 'Display / construction input — not scored', color: 'neutral' }],
    formulas: ['True range = max(high − low, |high − prev close|, |low − prev close|)', 'ATR-14 = mean of the last 14'],
  },

  // ── v2 · advisory ────────────────────────────────────────────────────────
  {
    id: 'sigma-fwd', emoji: '🔭', name: 'Forward Volatility Forecast (σ_fwd)', tag: 'v2 · advisory', section: 'v2',
    explain: 'v1 measures edge against what volatility <strong>was</strong>; v2 against what it <strong>will likely be</strong>: a pooled forecast of the next 21 sessions trained on 10 years across all 33 names, with a downside-only twin (σ_fwd_dn). <strong>Honesty note (Sept 2026):</strong> a ten-year replay found σ_fwd running roughly 10–25% <em>above</em> what was later realized on the index names — a bias that makes v2 say “no forward premium” far too often. It is being recalibrated (Test T1) before it can gate anything.',
    readings: [
      { label: 'The denominator of everything v2 does', color: 'neutral' },
      { label: 'Currently biased high — under recalibration (T1)', color: 'ok' },
    ],
    analogy: 'Windshield instead of rear-view mirror — once the windshield is cleaned.',
    formulas: ['σ_fwd = pooled ridge forecast of realized vol over the next 21 sessions', 'inputs: Garman-Klass + overnight variance at 1/5/25/125-day memories, downside share, market factor'],
    example: { tag: 'Jul 7, 2026', body: 'SBUX: v1’s rear-view RV said premium looked fine; σ_fwd read <strong>0.343</strong> — more turbulence ahead than behind. Same option prices, different denominator, opposite conclusion.' },
  },
  {
    id: 'fvrp', emoji: '🧭', name: 'Forward VRP (FVRP) + z-score', tag: 'v2 · advisory', section: 'v2',
    explain: 'VRP with the forecast as denominator, plus a z-score asking “is this rich for <em>this</em> name against its own year?”. Read it as context, never as permission.',
    whatToDo: 'A rich FVRP on an index is often the first day of a vol spike — IV jumps, the forecast lags. Check the IV chart before believing it.',
    readings: t => [
      { label: 'z ≥ +1 = rich vs its own history — first check that IV is not spiking', color: 'ok' },
      { label: `FVRP < 1.0 = v2 rules it out (over-fires today — forecaster bias) · dead zones ${t.v2.dead_zone_index} index / ${t.v2.dead_zone_single} single [PROVISIONAL]`, color: 'bad' },
      { label: 'A second opinion on danger, not a buy signal', color: 'neutral' },
    ],
    formulas: t => [
      'FVRP = IV(30d) / σ_fwd  ·  z = z-score of ln(FVRP) over a trailing year (≥ 60 obs)',
      `abs premium floor: IV − σ_fwd ≥ ${t.v2.abs_premium_floor_volpts} vol pts · veto denominator today: "${t.v2.veto_denominator}" (T1 owns the switch)`,
    ],
    example: { tag: 'Jul 7, 2026 — and what a ten-year replay made of it', body: 'MSFT printed FVRP <strong>1.33 / z +1.62</strong> — the richest premium on the board — while v1 had it at NO EDGE. From Jul 8 v2’s own gate painted MSFT DANGER. The Sept-2026 replay explained the pattern: days v2 cleared earned <strong>less</strong> than days it vetoed on all four index names.' },
  },
  {
    id: 'slope-1m3m', emoji: '🌡️', name: '1M/3M Term Slope (v2)', tag: 'v2 · advisory', section: 'v2',
    explain: 'v2’s earlier-warning term check: 1-month vs 3-month IV, with two-sided thresholds (raise fast, lower carefully) so one noisy day cannot flip the state.',
    readings: t => [
      { label: `< ${t.v2.g2_caution_out} = healthy near-term contango`, color: 'good' },
      { label: `≥ ${t.v2.g2_caution_in} = CAUTION (exits ≤ ${t.v2.g2_caution_out})`, color: 'ok' },
      { label: `≥ ${t.v2.g2_danger_in} = DANGER (exits ≤ ${t.v2.g2_danger_out}) — fires on ~53% of single-name days; per-sleeve re-baseline pending`, color: 'bad' },
    ],
    formulas: ['slope_1m3m = IV(1M) / IV(3M)'],
  },
  {
    id: 'accel-dn', emoji: '📉', name: 'Downside Acceleration (accel_dn)', tag: 'v2 · advisory', section: 'v2',
    explain: 'Only down-moves count: last week’s downside energy vs last month’s. A single-day crash gets a <em>transient</em> tag (a short time-out) instead of a full regime change.',
    readings: t => [
      { label: '< 1.0 = downside quieting', color: 'good' },
      { label: `≥ ${t.v2.g3_in} = CAUTION (exits ≤ ${t.v2.g3_out}) · transient blackout ${t.v2.transient_blackout_days} sessions`, color: 'bad' },
    ],
    formulas: ['accel_dn = √( EWMA₅(downside var) / EWMA₂₅(downside var) )'],
    example: { tag: 'Jul 9–10, 2026', body: 'JNJ: rich premium (FVRP 1.17 / z +0.99) on a name v1 called AVOID; v2 briefly cleared it, then accel_dn climbed <strong>1.118 → 1.216</strong> and v2 re-gated it — the insurance was expensive because the house was starting to shake.' },
  },
  {
    id: 'gate-state', emoji: '🚦', name: 'v2 Gate State & Hysteresis', tag: 'v2 · advisory', section: 'v2',
    explain: 'A small state machine per name (NORMAL / CAUTION / DANGER) fed by four live gates — earnings, 1M/3M slope, downside accel, negative forward VRP — with a book-wide freeze designed but not yet live. Every transition needs two confirming sessions. <strong>The gate state and the transient tag are the trustworthy part of the badge</strong>; the FVRP reasons currently over-fire.',
    readings: t => [
      { label: `Any transition: ${t.v2.confirm_days} consecutive confirming sessions; exit bars tighter than entry`, color: 'neutral' },
      { label: 'CAUTION / DANGER / transient = v2 stands down — the part to trust', color: 'bad' },
      { label: 'NORMAL + eligible = v2 sees no veto — a second opinion, not a buy signal', color: 'ok' },
    ],
    analogy: 'A thermostat, not a light switch.',
    formulas: [],
    example: { tag: 'Jul 7–13, 2026', body: 'The SBUX veto held for <strong>six consecutive sessions</strong> without a flip while v1’s label bounced between CONDITIONAL and SELL. That stability is the hysteresis working.' },
  },
];

export const SECTIONS: { key: MetricDefinition['section']; label: string; desc?: string }[] = [
  { key: 'signals', label: '📊 Signals — the five score components', desc: 'What the score is built from. Each is an input; none is a decision on its own.' },
  { key: 'vetoes', label: '🛑 Vetoes — what stops a trade', desc: 'The layer that has earned trust in every test. Read these before the score.' },
  { key: 'decisions', label: '🎯 Decisions — score tier, structure, size, exit', desc: 'What you actually act on.' },
  { key: 'context', label: '🔬 Context — display-only trade metrics' },
  { key: 'v2', label: '🔭 v2 · advisory (forward-looking engine)', desc: 'Runs beside v1 since July 2026 — the gate badge and the drawer’s v2 section. Changes no live decision; its forecaster is being recalibrated (Test T1). A second opinion on danger, not a buy signal.' },
];
