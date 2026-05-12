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

