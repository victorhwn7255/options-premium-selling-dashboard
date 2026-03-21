import type { DashboardTicker, ScanResponse, TickerResult } from './types';

/**
 * Map backend recommendation string to frontend action type.
 * Backend values: SELL PREMIUM, CONDITIONAL, REDUCE SIZE, AVOID, NO EDGE
 * Frontend action: SELL, CONDITIONAL, NO EDGE, AVOID, SKIP (earnings gate)
 */
function mapRecommendation(rec: string): DashboardTicker['action'] {
  switch (rec) {
    case 'SELL PREMIUM': return 'SELL';
    case 'CONDITIONAL': return 'CONDITIONAL';
    case 'AVOID': return 'AVOID';
    case 'REDUCE SIZE': return 'AVOID';
    case 'NO DATA': return 'NO DATA';
    default: return 'NO EDGE';
  }
}

export function convertApiTicker(t: TickerResult): DashboardTicker {
  const rvAccel = t.rv_acceleration;
  const earningsDTE = t.earnings_dte ?? undefined;
  const earningsWarning = t.earnings_dte != null && t.earnings_dte <= 14;

  const thetaVega = (t.theta != null && t.vega != null && t.vega !== 0)
    ? Math.abs(t.theta / t.vega) : undefined;

  // Use backend-computed score and recommendation
  let score = t.signal_score;
  let action = mapRecommendation(t.recommendation);
  let actionReason: string | null = null;
  let preGateScore: number | undefined;

  // Earnings gate — override score/action but preserve pre-gate score for display
  if (t.earnings_dte != null && t.earnings_dte <= 14) {
    preGateScore = score > 0 ? score : undefined;
    score = 0;
    action = 'SKIP';
    actionReason = `Earnings in ${t.earnings_dte}d`;
  }

  let sizing = 'Full';
  if (rvAccel > 1.10) sizing = 'Half';
  if (rvAccel > 1.20) sizing = 'Quarter';

  return {
    sym: t.ticker,
    name: t.name,
    sector: t.sector,
    price: t.price,
    iv: t.iv_current ?? null,
    rv30: t.rv30,
    rv10: t.rv10,
    termSlope: t.term_slope,
    skew25d: t.skew_25d,
    theta: t.theta ?? undefined,
    vega: t.vega ?? undefined,
    atr14: t.atr14 ?? undefined,
    earningsDTE,
    isEtf: t.is_etf ?? false,
    vrp: t.vrp ?? null,
    rvAccel,
    ivPct: t.iv_percentile,
    thetaVega,
    earningsWarning,
    score,
    action,
    actionReason,
    preGateScore,
    sizing,
    regime: t.regime as DashboardTicker['regime'],
    termStructurePoints: t.term_structure_points,
    recommendation: t.recommendation,
    flags: t.flags,
    suggestedDelta: t.suggested_delta,
    suggestedStructure: t.suggested_structure,
    suggestedDte: t.suggested_dte,
    suggestedMaxNotional: t.suggested_max_notional,
  };
}

export function buildScoredData(apiData?: ScanResponse | null): DashboardTicker[] {
  if (!apiData?.tickers?.length) return [];
  return apiData.tickers.map(convertApiTicker).sort((a, b) => b.score - a.score);
}
