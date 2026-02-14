import type { DashboardTicker, ScanResponse, TickerResult } from './types';

function computeScore(ticker: {
  iv: number;
  rv30: number;
  rv10: number;
  termSlope: number;
  ivPct: number;
  earningsDTE?: number | null;
}): { score: number; action: DashboardTicker['action']; actionReason: string | null; preGateScore?: number } {
  const vrp = ticker.iv - ticker.rv30;
  const rvAccel = ticker.rv10 / ticker.rv30;

  // Always compute full score first
  const vrpScore = Math.min(40, vrp * 2.5);
  const termScore =
    ticker.termSlope < 0.85 ? 25 :
    ticker.termSlope < 0.90 ? 18 :
    ticker.termSlope < 0.95 ? 12 : 5;
  const ivPctScore =
    ticker.ivPct >= 80 ? 20 :
    ticker.ivPct >= 60 ? 14 :
    ticker.ivPct >= 40 ? 8 : 3;
  const rvPenalty =
    rvAccel > 1.15 ? -15 :
    rvAccel > 1.05 ? -6 : 0;

  const raw = vrpScore + termScore + ivPctScore + rvPenalty;
  const computed = Math.round(Math.max(0, Math.min(100, raw)));

  // Earnings gate — override score/action but preserve pre-gate score
  if (ticker.earningsDTE != null && ticker.earningsDTE <= 14) {
    return {
      score: 0, action: 'SKIP',
      actionReason: `Earnings in ${ticker.earningsDTE}d`,
      preGateScore: computed > 0 ? computed : undefined,
    };
  }

  const action: DashboardTicker['action'] =
    computed >= 70 ? 'SELL' :
    computed >= 50 ? 'CONDITIONAL' : 'NO EDGE';

  return { score: computed, action, actionReason: null };
}

export function convertApiTicker(t: TickerResult): DashboardTicker {
  const rvAccel = t.rv_acceleration;

  // Build raw ticker data first
  const earningsDTE = t.earnings_dte ?? undefined;
  const earningsWarning = t.earnings_dte != null && t.earnings_dte <= 14;

  const thetaVega = (t.theta != null && t.vega != null && t.vega !== 0)
    ? Math.abs(t.theta / t.vega) : undefined;

  // Compute score client-side (replaces backend signal_score)
  const { score, action, actionReason, preGateScore } = computeScore({
    iv: t.iv_current,
    rv30: t.rv30,
    rv10: t.rv10,
    termSlope: t.term_slope,
    ivPct: t.iv_percentile,
    earningsDTE: t.earnings_dte,
  });

  let sizing = 'Full';
  if (rvAccel > 1.10) sizing = 'Half';
  if (rvAccel > 1.20) sizing = 'Quarter';

  return {
    sym: t.ticker,
    name: t.name,
    sector: t.sector,
    price: t.price,
    iv: t.iv_current,
    rv30: t.rv30,
    rv10: t.rv10,
    termSlope: t.term_slope,
    skew25d: t.skew_25d,
    theta: t.theta ?? undefined,
    vega: t.vega ?? undefined,
    atr14: t.atr14 ?? undefined,
    earningsDTE,
    isEtf: t.is_etf ?? false,
    vrp: t.vrp,
    rvAccel,
    ivPct: t.iv_percentile,
    thetaVega,
    earningsWarning,
    score,
    action,
    actionReason,
    preGateScore,
    sizing,
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
