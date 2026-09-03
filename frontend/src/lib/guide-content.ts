// "Playbook" tab — four decision cards, in the order a trader asks them. Every number is rendered from
// GET /api/thresholds (backend/thresholds.py); rows marked "guidance" come from the strategy docs /
// evidence and are NOT code gates — the table says which is which.

import type { Thresholds } from './types';

export interface GuideRow { cells: string[]; kind?: 'gate' | 'guidance' }
export interface GuideTable { cols: string[]; rows: GuideRow[] }
export interface DecisionCard {
  id: string;
  step: number;
  title: string;
  lead: string;              // HTML
  table?: GuideTable;
  whatToDo: string;          // plain
  seeAlso: { label: string; metricId: string }[];
}

const pct = (x: number, d = 0) => `${(x * 100).toFixed(d)}%`;

export function decisionCards(t: Thresholds): DecisionCard[] {
  const v = t.v1_scorer, r = t.regime_per_ticker, d = t.dashboard_regime, e = t.exits, s = t.sizing, c = t.cps;
  const tier = (label: string) => t.rv_accel_status.find(x => x.label === label);
  const good = tier('Good'), exc = tier('Excellent');
  return [
    {
      id: 'today', step: 1, title: 'Should I trade today?',
      lead: 'Start with the <strong>regime banner</strong>. It is the first decision layer and the score never overrides it.',
      table: {
        cols: ['Regime', 'Trigger', 'Posture'],
        rows: [
          { cells: ['OFF SEASON', `> ${pct(d.off_season_danger_pct)} of eligible tickers in DANGER`, 'No new positions. Manage what you hold by the exit rules.'], kind: 'gate' },
          { cells: ['REGULAR SEASON', `> ${pct(d.regular_season_stress_pct)} in DANGER or CAUTION`, 'Defined risk only (Credit Put Spreads tab), smaller, index first — or skip the day.'], kind: 'gate' },
          { cells: ['THE PLAYOFFS', 'neither of the above', 'Run steps 2–4 on prints that clear every veto.'], kind: 'gate' },
          { cells: ['THE FINALS', `avg VRP > ${d.finals_avg_vrp} and avg slope < ${d.finals_avg_slope}`, 'Never triggered (0 of 284 days). If it fires, treat it as PLAYOFFS.'], kind: 'guidance' },
        ],
      },
      whatToDo: 'OFF SEASON → close the app. REGULAR SEASON → CPS tab only. PLAYOFFS → step 2.',
      seeAlso: [{ label: 'per-ticker regime', metricId: 'ticker-regime' }, { label: 'term structure', metricId: 'term-structure' }],
    },
    {
      id: 'tradeable', step: 2, title: "What's tradeable?",
      lead: `Read the <strong>vetoes first</strong>, then treat what survives as a <strong>candidate list, not a ranking</strong> — in every test so far a ${v.sell} and a 72 have been the same thing. The vetoes, the environment and the caps decide the trade.`,
      table: {
        cols: ['Check', 'Rule', 'Source'],
        rows: [
          { cells: ['Per-ticker regime', `AVOID if slope > ${r.danger_slope} · CAUTION (defined risk / no SELL) if slope > ${r.caution_slope} or RV accel > ${r.caution_accel}`, 'gate'], kind: 'gate' },
          { cells: ['Earnings', `SKIP if earnings ≤ ${t.earnings_gate_days} days (single names)`, 'gate'], kind: 'gate' },
          { cells: ['Premium cushion', `WATCHLIST (no position) if VRP ratio < ${v.vrp_ratio_dead_zone}; negative VRP caps the score at ${v.negative_vrp_cap}`, 'gate'], kind: 'gate' },
          { cells: ['RV Accel status', `Require ${exc?.label ?? 'Excellent'} (≤ ${exc?.max}) or ${good?.label ?? 'Good'} (≤ ${good?.max}); never Caution / Avoid`, 'gate + guidance'], kind: 'gate' },
          { cells: ['VRP ratio', `${v.vrp_ratio_dead_zone}–1.45 is the sweet spot; be suspicious above ${v.vrp_ratio_cap} — often the start of a vol spike`, 'guidance (evidence)'], kind: 'guidance' },
          { cells: ['IV not spiking', 'IV roughly flat-to-down over the last week (IV-vs-RV chart) — a jump often precedes a realized-vol explosion', 'guidance (evidence)'], kind: 'guidance' },
          { cells: ['Term structure', `≤ 0.95 preferred; ${v.term_hinges[1]}–${r.caution_slope} earns few points and is CAUTION-adjacent`, 'guidance'], kind: 'guidance' },
          { cells: ['Skew', `${v.skew_nodes[1]}–${v.skew_nodes[2]} is the sweet spot; > ${v.skew_nodes[3]} is an AVOID for spreads`, 'gate + guidance'], kind: 'guidance' },
          { cells: ['Earnings vs hold', 'Clear of the whole hold (+5 sessions) for a naked put — 15–21 days is small-size territory', 'guidance (strategy §3.4)'], kind: 'guidance' },
          { cells: ['Persistence', `The print survives ${c.confirmation_days} consecutive scans (the CPS rule; one-day prints burned twice in Aug 2026)`, 'gate (CPS) / guidance'], kind: 'guidance' },
          { cells: ['Friction', `Quoted spread ≤ ${pct(t.v2.max_spread_over_mid)} of mid; CPS legs bid/ask ≤ ${pct(c.max_bid_ask_ratio)}, OI ≥ ${c.min_open_interest}; "Thin premium" (< ${pct(c.thin_premium_threshold)} credit/width) is a quote, not a trade`, 'gate'], kind: 'gate' },
          { cells: ['Sleeve', `Index first (${c.universe.join(' / ')}, deep-chain sector ETFs); single names need everything above plus a cleaner read`, 'guidance (evidence)'], kind: 'guidance' },
          { cells: ['v2 badge 🔭', 'Trust the gate state (CAUTION / DANGER) and the transient tag as a second opinion on danger; do not read "eligible" as a buy signal (forecaster under recalibration)', 'advisory'], kind: 'guidance' },
        ],
      },
      whatToDo: 'Strip out every vetoed row. If nothing survives, the correct output is no trade — that has been the right answer for most of Aug–Sep 2026.',
      seeAlso: [{ label: 'composite score', metricId: 'composite-score' }, { label: 'WATCHLIST', metricId: 'watchlist' }, { label: 'RV acceleration', metricId: 'rv-accel' }, { label: 'CPS rules', metricId: 'cps-rules' }],
    },
    {
      id: 'size', step: 3, title: 'How much?',
      lead: `Open the ticker drawer → <strong>Sizing card</strong>. It shows the whole arithmetic — <code>floor(equity × φ × f* × R × O ÷ margin)</code>, φ = ${s.kelly_fraction} (quarter-Kelly) — and the <strong>binding cap</strong>. ${s.f_star_seed === 0 ? `Today the Kelly seed says <strong>f* = 0</strong>: no growth-optimal size once a disaster is injected — so size by the caps, not by conviction.` : ''}`,
      table: {
        cols: ['Cap', 'Limit', 'Meaning'],
        rows: [
          { cells: ['Book stressed loss', pct(s.cap_book_stress_frac), `Full-book reprice at spot × ${s.stress_spot_mult}, IV × ${s.stress_iv_mult}, +${s.stress_days_elapsed} sessions — the number that makes "no stop-loss" coherent`], kind: 'gate' },
          { cells: ['Total margin', pct(s.cap_margin_frac), 'Σ initial margin ÷ equity'], kind: 'gate' },
          { cells: ['Short-put notional', pct(s.cap_notional_frac), 'Cash-secured standard'], kind: 'gate' },
          { cells: ['Per-name margin', pct(s.cap_name_margin_frac), 'One name cannot dominate the book'], kind: 'gate' },
          { cells: ['Per-name stressed loss', pct(s.cap_name_stress_frac, 1), 'The cap the live GLD position breached at 206% on the console’s first day'], kind: 'gate' },
        ],
      },
      whatToDo: 'Caps reject, never trim: take the largest cap-compliant size the card names. The stress scenario is a convention, not a worst case — a correlated gap can exceed it.',
      seeAlso: [{ label: 'sizing caps', metricId: 'sizing-caps' }, { label: 'position hints', metricId: 'position-hints' }],
    },
    {
      id: 'exit', step: 4, title: 'When do I leave?',
      lead: 'Enter the fill in the <strong>Journal</strong> with its exit plan; the <strong>Portfolio / Risk</strong> tab then raises these flags nightly. They are the strategy’s own rules — obey them, not the narrative.',
      table: {
        cols: ['Flag', 'Rule', 'Action'],
        rows: [
          { cells: ['PROFIT_TARGET', `capture ≥ ${pct(e.profit_target)} (${pct(e.profit_target_rv_rising)} when RV accel > ${e.rv_rising_accel} or the name is CAUTION)`, 'Close — the backtest showed 75% beat 50% once friction is counted'], kind: 'gate' },
          { cells: ['TIME_EXIT', `DTE ≤ ${e.time_exit_dte}`, 'Close — gamma outgrows theta from here'], kind: 'gate' },
          { cells: ['SPREAD_AWARE_DECAY', `premium < ${e.spread_aware_premium_mult}× the quoted spread, strike > ${e.spread_aware_sigma_mult}σ OTM, no active v2 gate`, `The 21-DTE exception: let it decay to ~${e.spread_aware_decay_to_dte} DTE rather than pay to close`], kind: 'gate' },
          { cells: ['DANGER_UNDERWATER', `regime DANGER and mark ≥ ${e.danger_underwater_mult}× entry credit`, 'Close — the only forced loss exit'], kind: 'gate' },
          { cells: ['TESTED', `spot at/below the short strike or |Δ| ≥ ${e.tested_delta}`, 'Defend / roll decision point'], kind: 'gate' },
          { cells: ['Stop-loss', 'none', 'Deliberate: stops tested PF 0.97–1.31; the caps make the implicit stop unreachable'], kind: 'guidance' },
        ],
      },
      whatToDo: 'Two flags saying leave is a decision already made. The current GLD trade — 95% captured, plan date passed, nineteen sessions of "leave" — is the cautionary tale.',
      seeAlso: [{ label: 'exit flags', metricId: 'exit-flags' }],
    },
  ];
}

export const GUIDE_FOOTER =
  'The score measures edge; the vetoes decide whether you may trade; the caps decide how much; the flags decide when to leave.';
