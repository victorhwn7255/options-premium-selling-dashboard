/* ── Dashboard Types ──────────────────────────────────── */

export type RvAccelStatusLabel =
  | 'Excellent'
  | 'Good'
  | 'Acceptable'
  | 'Caution'
  | 'Avoid / Wait';

export interface RvAccelStatus {
  label: RvAccelStatusLabel;
  description: string;
}

export interface DashboardTicker {
  sym: string;
  name: string;
  sector: string;
  price: number;
  iv: number | null;
  rv30: number;
  rv10: number;
  termSlope: number;
  skew25d: number;
  theta?: number;
  vega?: number;
  atr14?: number;
  earningsDTE?: number | null;
  isEtf: boolean;
  // Derived
  vrp: number | null;
  rvAccel: number;
  ivPct: number;
  thetaVega?: number;
  earningsGateActive?: boolean;
  // Scored
  score: number;
  action: 'SELL' | 'CONDITIONAL' | 'WATCHLIST' | 'NO EDGE' | 'AVOID' | 'SKIP' | 'NO DATA';
  actionReason: string | null;
  preGateScore?: number;  // Score computed before earnings gate (display-only, present only when gated and > 0)
  // RV Acceleration Status — display-only environment-cleanliness label.
  // Replaces the pre-Phase-2C `sizing` (Full/Half/Quarter) prescription.
  // Position size is a trader-controlled decision, not dashboard output.
  rvAccelStatus?: RvAccelStatus;
  regime: 'NORMAL' | 'CAUTION' | 'DANGER';
  // QA Phase 1 additions (see references/dashboard-behavior-qa-report.md)
  vrpRatio: number | null;
  thinPremium: boolean;  // 1.15 ≤ vrp_ratio < 1.25 AND action === 'CONDITIONAL'
  // QA Phase 1 — scan-quality suppression diagnostics. When the scan is DEGRADED,
  // SELL / CONDITIONAL / WATCHLIST rows are downgraded to NO EDGE for trading safety
  // but the original signal context is preserved here for the DetailPanel audit note.
  suppressedByScanQuality: boolean;
  preSuppressionRecommendation?: string;  // raw backend rec ("SELL PREMIUM" / "CONDITIONAL" / "WATCHLIST")
  preSuppressionAction?: 'SELL' | 'CONDITIONAL' | 'WATCHLIST';  // frontend-derived from above
  preSuppressionScore?: number;
  scanQualitySuppressionReason?: string;
  // Phase 2B — decision-clarity metadata. Display-only; never affects filters/counts.
  // Earnings warning: TBD/null for non-ETF, or FMP/Yahoo drift > 5d.
  // Renamed to *Kind to avoid clashing with the Phase-1 boolean `earningsGateActive`
  // (used for the ⚠ DTE chevron when DTE ≤ 14).
  earningsWarningKind?: 'DATE_UNVERIFIED' | 'DATE_CONFLICT' | null;
  earningsWarningLabel?: string;
  earningsWarningDetail?: string;
  // Display-only action label so Leaderboard can show CAUTION+REDUCE SIZE distinctly
  // from DANGER+AVOID without changing the canonical `action` field used by counts.
  displayAction?: string;
  cautionReason?: string;
  // API data (attached for detail panel)
  termStructurePoints?: TermStructurePoint[];
  recommendation?: string;
  flags?: string[];
  suggestedDelta?: string;
  suggestedStructure?: string;
  suggestedDte?: string;
  suggestedMaxNotional?: string;
}

export interface VolHistoryPoint {
  date: string;
  iv: number;
  rv: number;
  vrp: number;
}

export interface TermStructurePoint2 {
  label: string;
  dte: number;
  iv: number;
}

/* ── API Response Types ──────────────────────────────── */

export interface TermStructurePoint {
  tenor_label: string;
  tenor_days: number;
  iv: number;
}

export interface SkewPoint {
  delta: number;
  iv: number;
  type: string;
}

export interface TickerResult {
  ticker: string;
  name: string;
  sector: string;
  price: number;
  iv_current: number | null;
  iv_rank: number;
  iv_percentile: number;
  rv10: number;
  rv20: number;
  rv30: number;
  vrp: number | null;
  vrp_ratio: number | null;
  rv_acceleration: number;
  term_slope: number;
  is_contango: boolean;
  skew_25d: number;
  signal_score: number;
  regime: 'NORMAL' | 'CAUTION' | 'DANGER';
  recommendation: string;
  flags: string[];
  suggested_delta: string;
  suggested_structure: string;
  suggested_dte: string;
  suggested_max_notional: string;
  earnings_dte: number | null;
  is_etf: boolean;
  theta: number | null;
  vega: number | null;
  atr14: number | null;
  term_structure_points: TermStructurePoint[];
  skew_points: SkewPoint[];
  // Scan-quality suppression diagnostics (optional for old cached scans)
  suppressed_by_scan_quality?: boolean;
  pre_suppression_recommendation?: string | null;
  pre_suppression_score?: number | null;
  scan_quality_suppression_reason?: string | null;
  // v2 shadow-pipeline telemetry (Phase A, advisory-only; optional for old cached scans).
  // Display-only in the MACHINE view — never used for gating client-side (P1).
  sigma_fwd?: number | null;
  sigma_fwd_dn?: number | null;
  fvrp_ratio?: number | null;
  fvrp_z?: number | null;
  slope_1m3m?: number | null;
  accel_dn?: number | null;
  v2_gate_state?: string | null;
  v2_eligible?: boolean | null;
  v2_warm?: boolean | null;
  v2_ineligibility_reasons?: string[] | null;
  // Structured Phase-B surface (canonical; the flat v2_* above mirror it). The frontend
  // only RENDERS this — gate state comes from the API, never computed client-side (P1).
  eligibility?: V2Eligibility | null;
}

// v2 gate/eligibility surface (Phase B). Advisory — v1 authoritative until Phase E.
export interface V2Eligibility {
  gate_state: 'NORMAL' | 'CAUTION' | 'DANGER' | string;
  transient: boolean;
  pending: string | null;      // proposed state under 2-day confirmation, if any
  pending_days: number;
  eligible: boolean;
  ineligibility_reasons: string[];
}

export interface RegimeSummary {
  overall_regime: string;
  regime_color: string;
  description: string;
  avg_iv_rank: number;
  avg_rv_accel: number;
  danger_count: number;
  caution_count: number;
  total_tickers: number;
  vix_term_slope: number | null;
}

export interface HistoricalPoint {
  date: string;
  iv: number | null;
  rv: number | null;
  vrp: number | null;
  term_slope: number | null;
}

export interface ScanResponse {
  timestamp: string;
  regime: RegimeSummary | null;
  tickers: TickerResult[];
  historical: Record<string, HistoricalPoint[]>;
  scanned_at: string | null;
  cached: boolean;
  message?: string;
  // QA Phase 1: surfaces "OK" or "DEGRADED" with reason for the banner
  scan_quality?: string;
  scan_quality_reason?: string | null;
}

export interface HealthResponse {
  status: string;
  marketdata_connected: boolean;
  db_initialized: boolean;
  tickers_configured: number;
  historical_data_points: number;
}

// ── v2 shadow endpoints (MACHINE view only) ─────────────────────────────────

export interface ShadowSummaryResponse {
  n_ticker_days: number;
  n_warm: number;
  dates: string[];
  agreement_rate: number | null;
  divergence_counts: Record<string, number>;
  index_gating_rate_v1: number | null;
  index_gating_rate_v2: number | null;
  single_gating_rate_v1: number | null;
  single_gating_rate_v2: number | null;
  oscillation_v1: number | null;
  oscillation_v2: number | null;
  warm_coverage: number | null;
  // WS2a forward realized capture (spec E3) — resolves with a 21-session lag; all optional.
  capture_n_resolved?: number | null;
  capture_window_resolved?: number | null;
  capture_window_dates?: string[] | null;
  capture_mean_all?: number | null;
  capture_mean_v1_actionable?: number | null;
  capture_mean_v2_eligible?: number | null;
  capture_mean_v2_eligible_warm?: number | null;
  capture_neg_rate_v1_gated?: number | null;
  capture_neg_rate_v1_cleared?: number | null;
  capture_neg_rate_v2_vetoed?: number | null;
  capture_neg_rate_v2_cleared?: number | null;
  capture_neg_rate_v2_vetoed_warm?: number | null;
  capture_neg_rate_v2_cleared_warm?: number | null;
  sigma_fwd_log_mae?: number | null;
  rv30_log_mae?: number | null;
  sigma_fwd_log_mae_gk?: number | null;
  // WS4 veto-denominator instrumentation
  veto_denominator?: string | null;
  veto_disagree_rate?: number | null;
  veto_disagree_n?: number | null;
}

export interface ShadowDiffRow {
  date: string;
  ticker: string;
  is_etf: boolean | null;
  v1_action: string | null;
  v1_regime: string | null;
  v2_eligible: boolean | null;
  v2_gate_state: string | null;
  v2_transient: boolean | null;
  divergence_class: string | null;
  divergence_reason: string | null;
  v2_warm: boolean | null;
  v1_vrp_ratio: number | null;
  v1_term_slope: number | null;
  v1_rv_accel: number | null;
  fvrp_ratio: number | null;
  fvrp_z: number | null;
  slope_1m3m: number | null;
  accel_dn: number | null;
  sigma_fwd: number | null;
}

export interface ShadowDiffResponse {
  count: number;
  rows: ShadowDiffRow[];
}

export interface VerificationResult {
  id: number;
  scanned_at: string;
  verified_at: string;
  total_checks: number;
  pass_count: number;
  warn_count: number;
  fail_count: number;
  failures: { ticker: string; name: string; status: string; ours?: string; ref?: string; diff?: string; note?: string }[];
  warnings: { ticker: string; name: string; status: string; ours?: string; ref?: string; diff?: string; note?: string }[];
}

export interface EarningsCheck {
  ticker: string;
  status: string;
  our_dte: number | null;
  our_date: string | null;
  yahoo_dte: number | null;
  yahoo_date: string | null;
  diff_days: number | null;
  note: string | null;
}

export interface EarningsVerificationResult {
  id: number;
  scanned_at: string;
  verified_at: string;
  total_checks: number;
  pass_count: number;
  fail_count: number;
  skip_count: number;
  checks: EarningsCheck[];
}

/* ── Day-over-Day Comparison Types ──────────────────── */

export interface TickerDelta {
  score: number | null;
  iv: number | null;
  iv_percentile: number | null;
  rv30: number | null;
  vrp: number | null;
  term_slope: number | null;
  rv_acceleration: number | null;
  skew_25d: number | null;
  regime_changed: boolean;
  previous_regime: string | null;
}

export interface TickerComparison {
  ticker: string;
  current: TickerResult;
  previous: TickerResult | null;
  deltas: TickerDelta | null;
}

export interface ComparisonResponse {
  current_scanned_at: string;
  previous_scanned_at: string | null;
  tickers: TickerComparison[];
}

export interface VrpHistoryPoint {
  date: string;
  avg_vrp: number;
  ticker_count: number;
}

export interface VrpHistoryResponse {
  year: number;
  points: VrpHistoryPoint[];
}


/* ── Credit Put Spreads ───────────────────────────────────
 * Phase 1 — additive, no impact on existing types.
 * CPS is a defined-risk expression of the SAME volatility edge used by the
 * Naked Puts tab; candidates are ranked by Base Edge Score after binary
 * construction + execution filters. See references/credit-put-spreads.md.
 */

export type CreditPutSpreadAction =
  | 'SELL_CPS'
  | 'WATCH_CPS'
  | 'WAIT'
  | 'AVOID'
  | 'NO_EDGE'
  | 'NO_DATA';

// UNKNOWN — yfinance feed unavailable, overlay surfaces a warning but
// candidates are NOT blocked (per Phase-1 clarification §1).
export type RegimeOverlayStatus = 'NORMAL' | 'CAUTION' | 'DANGER' | 'UNKNOWN';

export interface CreditPutSpreadLeg {
  strike: number;
  expiration: string;
  dte: number;
  delta?: number;
  bid: number;
  ask: number;
  mid: number;
  iv?: number;
  theta?: number;
  vega?: number;
  openInterest?: number;
  volume?: number;
  // bid_ask_ratio = (ask - bid) / mid. Never `spreadRatio` — see build plan §1.2.
  bidAskRatio?: number;
}

export interface RegimeOverlay {
  status: RegimeOverlayStatus;
  vix?: number;
  vix3m?: number;
  vvix?: number;
  vixBackwardation?: boolean;
  warnings: string[];
}

export interface CreditPutSpreadCandidate {
  ticker: string;
  spot: number;

  action: CreditPutSpreadAction;
  baseScore: number;
  rankScore: number;
  regime: string;

  expiration: string;
  dte: number;

  shortPut: CreditPutSpreadLeg;
  longPut: CreditPutSpreadLeg;

  // Per-share economics (multiply by 100 for per-contract dollars).
  width: number;
  netCredit: number;
  maxLoss: number;
  creditToWidth: number;
  breakeven: number;

  atr14?: number;
  expectedMove?: number;
  expectedMoveLower?: number;
  widthToAtr?: number;
  widthToExpectedMove?: number;

  vrp?: number;
  vrpRatio?: number;
  vrpZscore60d?: number;
  ivPercentile?: number;
  termSlope?: number;
  rvAccel?: number;
  rvAccelStatus?: string;
  skew?: number;
  earningsDte?: number;

  // Ticker-level streak gates SELL_CPS. Exact-spread streak is display-only.
  consecutiveSellDays: number;
  exactSpreadConsecutiveDays: number;

  vix?: number;
  vix3m?: number;
  vvix?: number;
  regimeOverlayStatus?: RegimeOverlayStatus;

  notes: string[];
  warnings: string[];
  rejectionReasons: string[];
}

export interface CPSRejectionSummary {
  checked: number;
  actionable: number;
  rejectedByBaseGate: number;
  rejectedByConstruction: number;
  rejectedByExecution: number;
  rejectedByOverlay: number;
  rejectedByConfirmation: number;
}

export interface CreditPutSpreadsResponse {
  scanDate: string;
  marketRegime: string;
  cpsUniverse: string[];
  regimeOverlay: RegimeOverlay;
  candidates: CreditPutSpreadCandidate[];
  message?: string;
  rejectionSummary?: CPSRejectionSummary;
}

// Mirror of backend SpreadExitAction enum. Used by frontend exit-badge.
export type SpreadExitAction =
  | 'HOLD'
  | 'CLOSE_PROFIT_TARGET'
  | 'CLOSE_DEFENSIVE'
  | 'CLOSE_TIME'
  | 'CLOSE_PIN_RISK'
  | 'CLOSE_EVENT_RISK';

export interface SpreadExitDecision {
  action: SpreadExitAction;
  reason: string;
  notes: string[];
}


// ── "How to use" guide — display thresholds (GET /api/thresholds; backend/thresholds.py) ──
export interface RvAccelTier { max: number | null; label: string; meaning: string }
export interface PositionHint { condition: string; delta: string; structure: string; dte: string; notional: string }
export interface Thresholds {
  provenance: Record<string, string>;
  v1_scorer: {
    vrp_ratio_dead_zone: number; vrp_ratio_cap: number; vrp_points: number;
    iv_pct_floor: number; iv_pct_points: number;
    term_hinges: number[]; term_points: number[];
    accel_hinges: number[]; accel_points: number[];
    skew_nodes: number[]; skew_points: number;
    sell: number; conditional: number; reduce_size: number; negative_vrp_cap: number;
  };
  regime_per_ticker: { danger_slope: number; caution_slope: number; caution_accel: number; caution_ivr: number; caution_ivr_accel: number };
  dashboard_regime: { off_season_danger_pct: number; regular_season_stress_pct: number; finals_avg_vrp: number; finals_avg_slope: number; finals_ever_triggered: boolean };
  earnings_gate_days: number;
  rv_accel_status: RvAccelTier[];
  position_hints: PositionHint[];
  cps: {
    universe: string[]; target_dte: number; min_dte: number; max_dte: number;
    target_short_delta: number; min_short_delta: number; max_short_delta: number;
    sell_credit_to_width: number; watch_credit_to_width: number; thin_premium_threshold: number;
    high_credit_to_width_warning: number; max_bid_ask_ratio: number; min_open_interest: number;
    min_volume: number; confirmation_days: number; vvix_caution: number; vvix_danger: number;
    vrp_zscore_60d_min: number; time_exit_dte: number; profit_target_frac: number;
    defensive_mark_multiple: number; event_risk_dte: number; pin_risk_dte: number;
    inherited_gates: { earnings_dte: number; danger_slope: number; min_vrp_ratio: number; rv_accel_wait: number; extreme_skew: number };
  };
  exits: {
    profit_target: number; profit_target_rv_rising: number; rv_rising_accel: number; time_exit_dte: number;
    tested_delta: number; spread_aware_premium_mult: number; spread_aware_sigma_mult: number;
    spread_aware_decay_to_dte: number; stop_loss: null; danger_underwater_mult: number;
  };
  sizing: {
    kelly_fraction: number; kelly_min_trades: number; f_star_seed: number | null;
    dial_R_bounds: number[]; dial_O_bounds: number[];
    cap_notional_frac: number; cap_margin_frac: number; cap_name_margin_frac: number;
    cap_name_stress_frac: number; cap_book_stress_frac: number;
    stress_spot_mult: number; stress_iv_mult: number; stress_days_elapsed: number; margin_alpha: number;
  };
  v2: {
    dead_zone_index: number; dead_zone_single: number; abs_premium_floor_volpts: number;
    g1_earnings_gate_days: number; g2_caution_in: number; g2_caution_out: number;
    g2_danger_in: number; g2_danger_out: number; g3_in: number; g3_out: number; g3_concentration: number;
    confirm_days: number; transient_blackout_days: number; veto_denominator: string;
    max_spread_over_mid: number; max_rtc_over_capture: number;
  };
  data_quality: { min_atm_contracts: number; max_spread_ratio: number; max_iv: number };
}
