// Regime guide content — trimmed to 3 dos / 3 don'ts + one dated example per regime (2026-09-03).
// THE FINALS has never triggered (0 of 284 logged days) and is rendered as a footnote, not a section.
// Thresholds in the trigger lines are rendered from GET /api/thresholds by the modal.

import type { Thresholds } from './types';

export interface RegimeContent {
  regime: string;
  tagline: string;
  colorToken: 'error' | 'warning' | 'secondary' | 'accent';
  triggerLogic: string;
  triggers: (t: Thresholds) => { metric: string; value: string }[];
  explanation: string[];
  dos: string[];
  donts: string[];
  example: { tag: string; metrics: { label: string; value: string }[]; narrative: string };
}

const pct = (x: number) => `${Math.round(x * 100)}%`;

export const REGIMES: RegimeContent[] = [
  {
    regime: 'OFF SEASON',
    tagline: 'Too dangerous to sell — sit out and protect your capital',
    colorToken: 'error',
    triggerLogic: 'threshold',
    triggers: t => [{ metric: 'DANGER ratio', value: `> ${pct(t.dashboard_regime.off_season_danger_pct)} of eligible tickers` }],
    explanation: [
      'More than 40% of tickers have flipped to DANGER — deep backwardation or extreme IV with rising realized vol. This is systemic stress, not a single-name event. Premium selling in backwardation is picking up pennies in front of a bulldozer that is already moving: the options market is saying realized vol will likely exceed implied.',
      'Since daily logging began (Mar 24, 2026) no session has reached OFF SEASON — the worst logged stress day (Jun 10, 2026) still rated REGULAR SEASON. That rarity is the point: when it fires, it is unambiguous.',
    ],
    dos: [
      'Open nothing new — go to cash or stay fully hedged',
      "Manage what you hold by the strategy's own exit rules (75% target, 21 DTE, close only if DANGER and underwater ≥ 1.25× credit) — there are no stop-losses",
      'Use the time to study post-regime candidates — high pre-gate scores are the names to watch',
    ],
    donts: [
      'Open any new short-premium position, however "cheap" the puts look — they are cheap for a reason',
      'Try to catch the bottom by selling into the spike',
      'Assume it is temporary — regimes can persist for weeks',
    ],
    example: {
      tag: 'Feb 13, 2026',
      metrics: [
        { label: 'Avg VRP', value: '1.1' }, { label: 'Term Slope', value: '1.09' },
        { label: 'RV Accel', value: '1.17' }, { label: 'Tradeable', value: '1 / 25' },
      ],
      narrative: 'Broad market in backwardation with near-zero VRP; gold surging (GLD slope 1.20); multiple tech names with negative VRP after a selloff. Only 1 of 25 tickers passed any scoring threshold. The correct action was no action.',
    },
  },
  {
    regime: 'REGULAR SEASON',
    tagline: 'Stressed market — defined risk only, or skip the day',
    colorToken: 'warning',
    triggerLogic: 'threshold',
    triggers: t => [{ metric: 'Stress ratio', value: `> ${pct(t.dashboard_regime.regular_season_stress_pct)} of tickers in DANGER or CAUTION` }],
    explanation: [
      'Playable but stressed: more than a quarter of the universe is showing caution or danger — backwardation, extreme IV with rising RV, or both. This is where defined-risk structures earn their keep; they cap the downside if the regime deteriorates.',
    ],
    dos: [
      'Use defined risk only — the Credit Put Spreads tab is built for this regime',
      'Demand a clean RV Accel status (Excellent / Good) and a print that survives two consecutive scans',
      'Keep the 45-DTE entry / 21-DTE exit cadence — shorter entries tested worse (30-DTE entries ran PF 0.90 vs 1.81 at 45 DTE)',
    ],
    donts: [
      'Sell naked options — undefined risk in accelerating vol is how accounts blow up',
      'Sell a ticker that is individually in backwardation because the market-level label is only REGULAR SEASON',
      'Add to losing positions — the only forced exit is DANGER plus underwater (mark ≥ 1.25× credit); otherwise the 21-DTE rule governs',
    ],
    example: {
      tag: 'Jul 6, 2026',
      metrics: [
        { label: 'Stress', value: '48.3%' }, { label: 'CAUTION', value: '14 names' },
        { label: 'Avg VRP', value: '−1.4' }, { label: 'RV Accel', value: '1.062' },
      ],
      narrative: 'Stress exploded from 6.9% to 48.3% in one session — 14 tickers flipped to CAUTION while the term structure stayed in contango (0.844): realized vol waking up before options repriced, with no premium cushion (avg VRP −1.4). The lone clean SELL (SBUX, 68) was carried; every CAUTION name was avoided. REGULAR SEASON in practice: the playbook shrinks to protecting what you hold.',
    },
  },
  {
    regime: 'THE PLAYOFFS',
    tagline: 'Normal market — run the Playbook, index first',
    colorToken: 'secondary',
    triggerLogic: 'default (no other regime triggers)',
    triggers: t => [
      { metric: 'DANGER ratio', value: `≤ ${pct(t.dashboard_regime.off_season_danger_pct)}` },
      { metric: 'Stress ratio', value: `≤ ${pct(t.dashboard_regime.regular_season_stress_pct)}` },
    ],
    explanation: [
      'Normal conditions — most tickers NORMAL, term structures in contango, realized vol stable. This is 60–70% of trading days. Run the Playbook tab: index-first, on prints that clear every veto, sized by the caps.',
    ],
    dos: [
      'Execute on SELL (≥ 65) or CONDITIONAL (≥ 45) prints that clear every veto — the score measures how much edge is present; it does not rank one name above another',
      'Index first (SPY / QQQ / IWM, deep-chain sector ETFs); RV Accel Good or Excellent; enter at 45 DTE, exit by 21 DTE',
      'Manage winners at 75% of max profit (50% when RV is rising or the name is CAUTION)',
    ],
    donts: [
      'Get complacent — THE PLAYOFFS can turn into REGULAR SEASON in one session',
      'Over-concentrate — spread across 3–4 sectors',
      "Size on conviction — the sizing card's binding cap rules; record every entry's contract count in the journal",
    ],
    example: {
      tag: 'Jun 4, 2026',
      metrics: [
        { label: 'Avg VRP', value: '+2.4' }, { label: 'Term Slope', value: '0.93' },
        { label: 'RV Accel', value: '0.96' }, { label: 'Tradeable', value: '3S / 4C' },
      ],
      narrative: 'Zero DANGER tickers, stress 6.1%, average accel below 1.0 — a clean board. XLF crossed to SELL at 74 (VRP 7.3, contango 0.86, accel 1.00) and QQQ held as the core SELL at 70. The same day NKE printed SELL at 65 with a "monster" VRP of 27.3 — and the briefing flagged it "SCORE ARTIFACT — ignore" (accel 1.36, earnings 21 days out). Playoffs means run the playbook — and still read the vetoes.',
    },
  },
];

export const FINALS_FOOTNOTE = (t: Thresholds) =>
  `THE FINALS (avg VRP > ${t.dashboard_regime.finals_avg_vrp} AND avg slope < ${t.dashboard_regime.finals_avg_slope}) has never triggered — 0 of 284 logged days. If it ever does, run the Playbook as for PLAYOFFS: the only difference is that more names may qualify. It is not a regime to wait for.`;
