/* ── Dashboard Types ──────────────────────────────────── */

export interface DashboardTicker {
  sym: string;
  name: string;
  sector: string;
  price: number;
  iv: number;
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
  vrp: number;
  rvAccel: number;
  ivPct: number;
  thetaVega?: number;
  earningsWarning?: boolean;
  // Scored
  score: number;
  action: 'SELL' | 'CONDITIONAL' | 'NO EDGE' | 'SKIP';
  actionReason: string | null;
  preGateScore?: number;  // Score computed before earnings gate (display-only, present only when gated and > 0)
  sizing?: string;
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
  iv_current: number;
  iv_rank: number;
  iv_percentile: number;
  rv10: number;
  rv20: number;
  rv30: number;
  vrp: number;
  vrp_ratio: number;
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
}

export interface HealthResponse {
  status: string;
  marketdata_connected: boolean;
  db_initialized: boolean;
  tickers_configured: number;
  historical_data_points: number;
}

