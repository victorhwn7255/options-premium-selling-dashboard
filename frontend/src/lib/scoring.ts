import type { DashboardTicker, ScanResponse, TickerResult, EarningsCheck } from './types';

/**
 * Map backend recommendation string to frontend action type.
 * Backend values: SELL PREMIUM, CONDITIONAL, WATCHLIST, REDUCE SIZE, AVOID, NO EDGE, NO DATA
 * Frontend action: SELL, CONDITIONAL, WATCHLIST, NO EDGE, AVOID, SKIP (earnings gate), NO DATA
 */
function mapRecommendation(rec: string): DashboardTicker['action'] {
  switch (rec) {
    case 'SELL PREMIUM': return 'SELL';
    case 'CONDITIONAL': return 'CONDITIONAL';
    case 'WATCHLIST': return 'WATCHLIST';
    case 'AVOID': return 'AVOID';
    case 'REDUCE SIZE': return 'AVOID';
    case 'NO DATA': return 'NO DATA';
    default: return 'NO EDGE';
  }
}

export function convertApiTicker(t: TickerResult): DashboardTicker {
  const rvAccel = t.rv_acceleration;
  const earningsDTE = t.earnings_dte ?? undefined;
  // ETFs exempt — keep `earningsGateActive` consistent with the gate below.
  const earningsGateActive = t.earnings_dte != null && t.earnings_dte <= 14 && !t.is_etf;

  const thetaVega = (t.theta != null && t.vega != null && t.vega !== 0)
    ? Math.abs(t.theta / t.vega) : undefined;

  // Use backend-computed score and recommendation
  let score = t.signal_score;
  let action = mapRecommendation(t.recommendation);
  let actionReason: string | null = null;
  let preGateScore: number | undefined;

  // Earnings gate — override score/action but preserve pre-gate score for display.
  // ETFs are exempt per the documented contract (metrics.md / strategy.md / ADR-003).
  // The backend never sets earnings_dte for ETFs, but the !is_etf guard is
  // defense-in-depth in case a future data path violates that invariant.
  // See backend/test_qa_phase1_regression.py::test_etf_never_earnings_gated.
  if (t.earnings_dte != null && t.earnings_dte <= 14 && !t.is_etf) {
    preGateScore = score > 0 ? score : undefined;
    score = 0;
    action = 'SKIP';
    actionReason = `Earnings in ${t.earnings_dte}d`;
  }

  let sizing = 'Full';
  if (rvAccel > 1.10) sizing = 'Half';
  if (rvAccel > 1.20) sizing = 'Quarter';

  // Thin Premium badge: CONDITIONAL with VRP ratio just above the dead zone.
  // Range 1.15–1.25 = "made it past the gate but premium isn't fat" — warn, don't block.
  // See references/dashboard-behavior-qa-report.md §6 P1 / §7.2.
  const vrpRatio = t.vrp_ratio ?? null;
  const thinPremium = (
    action === 'CONDITIONAL' &&
    vrpRatio !== null &&
    vrpRatio >= 1.15 &&
    vrpRatio < 1.25
  );

  // Scan-quality suppression diagnostics — derive frontend-side action from
  // the preserved backend recommendation. Only the three actionable states
  // can ever appear here, so the union is narrowed accordingly.
  const suppressedByScanQuality = t.suppressed_by_scan_quality === true;
  const preSuppressionRecommendation = t.pre_suppression_recommendation ?? undefined;
  const preSuppressionScore = t.pre_suppression_score ?? undefined;
  const scanQualitySuppressionReason = t.scan_quality_suppression_reason ?? undefined;
  let preSuppressionAction: DashboardTicker['preSuppressionAction'];
  if (preSuppressionRecommendation === 'SELL PREMIUM') preSuppressionAction = 'SELL';
  else if (preSuppressionRecommendation === 'CONDITIONAL') preSuppressionAction = 'CONDITIONAL';
  else if (preSuppressionRecommendation === 'WATCHLIST') preSuppressionAction = 'WATCHLIST';

  // Phase 2B — Earnings TBD warning. Single-ticker derivable: non-ETF with null
  // earnings_dte means the FMP/Yahoo earnings pipeline could not produce a date.
  // DATE_CONFLICT (drift > 5 days) is added by enrichWithEarningsWarnings() since
  // it requires the separate earnings-verification feed.
  // Note: this is *Kind to avoid colliding with the Phase-1 boolean
  // `earningsGateActive` (used for the DTE ≤ 14 chevron, declared at line 24 above).
  const isEtf = t.is_etf ?? false;
  let earningsWarningKind: DashboardTicker['earningsWarningKind'] = null;
  let earningsWarningLabel: string | undefined;
  let earningsWarningDetail: string | undefined;
  if (!isEtf && t.earnings_dte == null) {
    earningsWarningKind = 'DATE_UNVERIFIED';
    earningsWarningLabel = 'Date unverified';
    earningsWarningDetail = 'Earnings date is missing or unverified. Confirm manually before trading.';
  }

  // Phase 2B — Display-only action label that distinguishes DANGER+AVOID from
  // CAUTION+REDUCE SIZE on the Leaderboard. The canonical `action` field is
  // unchanged so all filters/counts (tradeable count, regime banner, etc.)
  // behave identically to Phase 1.
  let displayAction: string | undefined;
  let cautionReason: string | undefined;
  if (action === 'AVOID') {
    if (t.regime === 'CAUTION' || t.recommendation === 'REDUCE SIZE') {
      displayAction = 'REDUCE SIZE';
      cautionReason = 'Defined-risk only';
    }
    // DANGER stays as 'AVOID' — already red, already correct.
  } else if (action === 'NO EDGE' && t.regime === 'CAUTION') {
    cautionReason = 'Caution regime';
    // displayAction stays undefined; Leaderboard renders 'NO EDGE' chip
    // plus a small CAUTION sub-pill (see ActionChip caller).
  }

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
    earningsGateActive,
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
    vrpRatio,
    thinPremium,
    suppressedByScanQuality,
    preSuppressionRecommendation,
    preSuppressionAction,
    preSuppressionScore,
    scanQualitySuppressionReason,
    earningsWarningKind: earningsWarningKind ?? undefined,
    earningsWarningLabel,
    earningsWarningDetail,
    displayAction,
    cautionReason,
  };
}

export function buildScoredData(apiData?: ScanResponse | null): DashboardTicker[] {
  if (!apiData?.tickers?.length) return [];
  return apiData.tickers.map(convertApiTicker).sort((a, b) => b.score - a.score);
}

/**
 * Phase 2B — overlay DATE_CONFLICT warnings using the earnings-verification feed.
 * If the FMP and Yahoo earnings dates disagree by > 5 days, the row is flagged.
 * ETFs and rows already flagged DATE_UNVERIFIED are not overwritten.
 *
 * Call after `buildScoredData()` once `earningsVerification.checks` is loaded.
 */
export function enrichWithEarningsWarnings(
  tickers: DashboardTicker[],
  checks: EarningsCheck[] | undefined,
): DashboardTicker[] {
  if (!checks || checks.length === 0) return tickers;
  const map = new Map<string, EarningsCheck>();
  for (const c of checks) map.set(c.ticker, c);
  return tickers.map(t => {
    if (t.isEtf) return t;
    if (t.earningsWarningKind === 'DATE_UNVERIFIED') return t; // TBD takes precedence
    const c = map.get(t.sym);
    if (!c || c.diff_days == null) return t;
    if (Math.abs(c.diff_days) <= 5) return t;
    return {
      ...t,
      earningsWarningKind: 'DATE_CONFLICT',
      earningsWarningLabel: 'Date conflict',
      earningsWarningDetail: `FMP and Yahoo earnings dates differ by ${Math.abs(c.diff_days)}d. Confirm manually before trading.`,
    };
  });
}
