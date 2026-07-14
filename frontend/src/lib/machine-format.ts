/**
 * machine-format.ts — MACHINE view section descriptors + serializer.
 *
 * The anti-drift core: MachineView builds `MachineSection[]` once; the React
 * renderer walks it AND the COPY_ALL serializer walks it, so what's on screen
 * and what lands on the clipboard can never diverge.
 *
 * Values are rendered VERBATIM from the wire (full precision, snake_case keys,
 * no rounding, no derived logic). P1: this module must never import scoring.ts
 * or compute any gate/eligibility state — it only reshapes API responses.
 */

import type {
  ScanResponse, HealthResponse, VerificationResult, EarningsVerificationResult,
  TickerDelta, ShadowSummaryResponse, ShadowDiffResponse,
} from './types';

// ── Section descriptors ─────────────────────────────────────────────────────

export interface KVSection {
  kind: 'kv';
  id: string;                                  // e.g. 'SCAN.META'
  note?: string;                               // e.g. 'window=20' | 'FETCH_ERROR: …'
  rows: [label: string, value: unknown][];
}

export interface TableSection {
  kind: 'table';
  id: string;
  note?: string;                               // e.g. 'rows=33'
  columns: string[];                           // raw wire field names, verbatim
  rows: unknown[][];                           // positional, matching columns
}

export type MachineSection = KVSection | TableSection;

// ── The one value stringifier (render cells AND serializer call this) ──────

export function fmtValue(v: unknown): string {
  if (v === null || v === undefined) return '∅';
  if (typeof v === 'number' || typeof v === 'boolean') return String(v);
  if (typeof v === 'string') return v === '' ? '""' : v;
  return JSON.stringify(v);                    // arrays + nested objects, compact
}

// ── COPY_ALL serializer ─────────────────────────────────────────────────────

const cell = (s: string) => s.replace(/\|/g, '\\|').replace(/\r?\n/g, ' ');

export function serializeSections(sections: MachineSection[], header: string): string {
  const out: string[] = [header];
  for (const s of sections) {
    out.push('', `== ${s.id} ==${s.note ? ` ${s.note}` : ''}`);
    if (s.kind === 'kv') {
      for (const [k, v] of s.rows) out.push(`${k}: ${cell(fmtValue(v))}`);
    } else {
      out.push(s.columns.join(' | '));
      for (const r of s.rows) out.push(r.map(v => cell(fmtValue(v))).join(' | '));
    }
  }
  return out.join('\n');
}

// ── Column groupings (explicit, so TICKERS.OTHER can catch the rest) ───────

const V1_CORE_KEYS = [
  'ticker', 'price', 'iv_current', 'iv_rank', 'iv_percentile', 'rv10', 'rv20',
  'rv30', 'vrp', 'vrp_ratio', 'rv_acceleration', 'term_slope', 'is_contango',
  'skew_25d', 'signal_score', 'regime', 'recommendation',
];

const V1_META_KEYS = [
  'ticker', 'name', 'sector', 'is_etf', 'earnings_dte', 'flags',
  'suggested_delta', 'suggested_structure', 'suggested_dte',
  'suggested_max_notional', 'theta', 'vega', 'atr14',
  'suppressed_by_scan_quality', 'pre_suppression_recommendation',
  'pre_suppression_score', 'scan_quality_suppression_reason',
];

const V2_SHADOW_KEYS = [
  'ticker', 'sigma_fwd', 'sigma_fwd_dn', 'fvrp_ratio', 'fvrp_z', 'slope_1m3m',
  'accel_dn', 'v2_gate_state', 'v2_eligible', 'v2_warm', 'v2_ineligibility_reasons',
];

// Array-valued ticker keys flattened into their own sections below.
const TICKER_ARRAY_KEYS = ['term_structure_points', 'skew_points'];

const SHADOW_DIFF_COLS = [
  'date', 'ticker', 'is_etf', 'v1_action', 'v1_regime', 'v2_eligible',
  'v2_gate_state', 'v2_transient', 'divergence_class', 'divergence_reason',
  'v2_warm', 'v1_vrp_ratio', 'v1_term_slope', 'v1_rv_accel', 'fvrp_ratio',
  'fvrp_z', 'slope_1m3m', 'accel_dn', 'sigma_fwd',
];

const DELTA_COLS = [
  'score', 'iv', 'iv_percentile', 'rv30', 'vrp', 'term_slope',
  'rv_acceleration', 'skew_25d', 'regime_changed', 'previous_regime',
];

const VERIFY_CHECK_COLS = ['ticker', 'name', 'status', 'ours', 'ref', 'diff', 'note'];
const EARNINGS_CHECK_COLS = ['ticker', 'status', 'our_dte', 'our_date', 'yahoo_dte', 'yahoo_date', 'diff_days', 'note'];

// ── Builder helpers ─────────────────────────────────────────────────────────

type Raw = Record<string, unknown>;

const pick = (row: Raw, keys: string[]): unknown[] => keys.map(k => row[k]);

/** KV rows from an object, wire key order preserved. */
const kvOf = (obj: Raw, prefix = ''): [string, unknown][] =>
  Object.entries(obj).map(([k, v]) => [`${prefix}${k}`, v]);

const noteFor = (data: unknown, err: string | undefined, note: string): string =>
  err ? `FETCH_ERROR: ${err}` : data === null ? 'loading' : note;

// ── Input bundle ────────────────────────────────────────────────────────────

export interface MachineData {
  scan: ScanResponse | null;
  scanStatus: string;                          // 'scanning' | 'idle'
  scanProgress: string | null;
  health: HealthResponse | null;
  verification: VerificationResult | null;
  earningsVerification: EarningsVerificationResult | null;
  deltaMap: Record<string, TickerDelta>;
  shadowSummary: ShadowSummaryResponse | null;
  shadowDiff: ShadowDiffResponse | null;
  cpsRaw: Raw | null;
  errors: Record<string, string>;              // fetchKey -> message
}

// ── The builder ─────────────────────────────────────────────────────────────

export function buildMachineSections(d: MachineData): MachineSection[] {
  const sections: MachineSection[] = [];
  // Tickers as raw records so v2 (and any future) fields flow through verbatim.
  const tickers = (d.scan?.tickers ?? []) as unknown as Raw[];
  const rowsNote = `rows=${tickers.length}`;

  // OPS.CONSOLE — the data rows under the ops buttons (buttons are controls,
  // rendered by MachineView, never serialized).
  sections.push({
    kind: 'kv', id: 'OPS.CONSOLE',
    rows: [
      ['scan.status', d.scanStatus],
      ['scan.progress', d.scanProgress],
      ...(d.health
        ? kvOf(d.health as unknown as Raw, 'health.')
        : [['health', d.errors.health ? `FETCH_ERROR: ${d.errors.health}` : null] as [string, unknown]]),
    ],
  });

  // SCAN.META + REGIME
  if (d.scan) {
    const s = d.scan as unknown as Raw;
    sections.push({
      kind: 'kv', id: 'SCAN.META',
      rows: [
        ['timestamp', s.timestamp], ['scanned_at', s.scanned_at],
        ['cached', s.cached], ['message', s.message],
        ['scan_quality', s.scan_quality], ['scan_quality_reason', s.scan_quality_reason],
      ],
    });
    sections.push({
      kind: 'kv', id: 'REGIME',
      note: d.scan.regime ? undefined : 'null',
      rows: d.scan.regime ? kvOf(d.scan.regime as unknown as Raw) : [],
    });

    // Ticker tables (explicit groups + a catch-all so nothing is ever dropped)
    sections.push({ kind: 'table', id: 'TICKERS.V1.CORE', note: rowsNote, columns: V1_CORE_KEYS, rows: tickers.map(t => pick(t, V1_CORE_KEYS)) });
    sections.push({ kind: 'table', id: 'TICKERS.V1.META', note: rowsNote, columns: V1_META_KEYS, rows: tickers.map(t => pick(t, V1_META_KEYS)) });
    sections.push({ kind: 'table', id: 'TICKERS.V2.SHADOW', note: rowsNote, columns: V2_SHADOW_KEYS, rows: tickers.map(t => pick(t, V2_SHADOW_KEYS)) });

    const claimed = new Set([...V1_CORE_KEYS, ...V1_META_KEYS, ...V2_SHADOW_KEYS, ...TICKER_ARRAY_KEYS]);
    const other = [...new Set(tickers.flatMap(t => Object.keys(t)))].filter(k => !claimed.has(k));
    if (other.length) {
      const cols = ['ticker', ...other];
      sections.push({ kind: 'table', id: 'TICKERS.OTHER', note: rowsNote, columns: cols, rows: tickers.map(t => pick(t, cols)) });
    }

    // Flattened per-ticker arrays
    const ts = tickers.flatMap(t =>
      ((t.term_structure_points as Raw[] | undefined) ?? []).map(p => [t.ticker, p.tenor_label, p.tenor_days, p.iv]));
    sections.push({ kind: 'table', id: 'TICKERS.TERM_STRUCTURE', note: `rows=${ts.length}`, columns: ['ticker', 'tenor_label', 'tenor_days', 'iv'], rows: ts });

    const sk = tickers.flatMap(t =>
      ((t.skew_points as Raw[] | undefined) ?? []).map(p => [t.ticker, p.delta, p.iv, p.type]));
    sections.push({ kind: 'table', id: 'TICKERS.SKEW', note: `rows=${sk.length}`, columns: ['ticker', 'delta', 'iv', 'type'], rows: sk });
  } else {
    sections.push({ kind: 'kv', id: 'SCAN.META', note: 'no scan data', rows: [] });
  }

  // DELTAS.DAY_OVER_DAY
  const deltaTickers = Object.keys(d.deltaMap).sort();
  sections.push({
    kind: 'table', id: 'DELTAS.DAY_OVER_DAY', note: `rows=${deltaTickers.length}`,
    columns: ['ticker', ...DELTA_COLS],
    rows: deltaTickers.map(t => [t, ...pick(d.deltaMap[t] as unknown as Raw, DELTA_COLS)]),
  });

  // VERIFY.METRICS (summary KV + failures/warnings in one table)
  if (d.verification) {
    const v = d.verification;
    sections.push({
      kind: 'kv', id: 'VERIFY.METRICS',
      rows: [
        ['scanned_at', v.scanned_at], ['verified_at', v.verified_at],
        ['total_checks', v.total_checks], ['pass_count', v.pass_count],
        ['warn_count', v.warn_count], ['fail_count', v.fail_count],
      ],
    });
    const checks = [...v.failures, ...v.warnings] as unknown as Raw[];
    sections.push({ kind: 'table', id: 'VERIFY.METRICS.CHECKS', note: `rows=${checks.length}`, columns: VERIFY_CHECK_COLS, rows: checks.map(c => pick(c, VERIFY_CHECK_COLS)) });
  } else {
    sections.push({ kind: 'kv', id: 'VERIFY.METRICS', note: 'no verification data', rows: [] });
  }

  // VERIFY.EARNINGS
  if (d.earningsVerification) {
    const e = d.earningsVerification;
    sections.push({
      kind: 'kv', id: 'VERIFY.EARNINGS',
      rows: [
        ['scanned_at', e.scanned_at], ['verified_at', e.verified_at],
        ['total_checks', e.total_checks], ['pass_count', e.pass_count],
        ['fail_count', e.fail_count], ['skip_count', e.skip_count],
      ],
    });
    const checks = e.checks as unknown as Raw[];
    sections.push({ kind: 'table', id: 'VERIFY.EARNINGS.CHECKS', note: `rows=${checks.length}`, columns: EARNINGS_CHECK_COLS, rows: checks.map(c => pick(c, EARNINGS_CHECK_COLS)) });
  } else {
    sections.push({ kind: 'kv', id: 'VERIFY.EARNINGS', note: 'no verification data', rows: [] });
  }

  // SHADOW.SUMMARY + SHADOW.DIFF (v2 shadow substrate — verbatim telemetry)
  sections.push({
    kind: 'kv', id: 'SHADOW.SUMMARY',
    note: noteFor(d.shadowSummary, d.errors.shadow_summary, 'window=20'),
    rows: d.shadowSummary ? kvOf(d.shadowSummary as unknown as Raw) : [],
  });
  sections.push({
    kind: 'table', id: 'SHADOW.DIFF',
    note: noteFor(d.shadowDiff, d.errors.shadow_diff, `count=${d.shadowDiff?.count ?? 0} limit=500`),
    columns: SHADOW_DIFF_COLS,
    rows: (d.shadowDiff?.rows ?? []).map(r => pick(r as unknown as Raw, SHADOW_DIFF_COLS)),
  });

  // CPS.RAW.* — wire-format snake_case, no camelization
  if (d.cpsRaw) {
    const c = d.cpsRaw;
    sections.push({
      kind: 'kv', id: 'CPS.RAW.META',
      rows: [
        ['scan_date', c.scan_date], ['market_regime', c.market_regime],
        ['message', c.message], ['cps_universe', c.cps_universe],
      ],
    });
    sections.push({
      kind: 'kv', id: 'CPS.RAW.OVERLAY',
      rows: c.regime_overlay ? kvOf(c.regime_overlay as Raw) : [],
    });
    const cands = (c.candidates as Raw[] | undefined) ?? [];
    const candCols = [...new Set(cands.flatMap(x => Object.keys(x)))];
    sections.push({ kind: 'table', id: 'CPS.RAW.CANDIDATES', note: `rows=${cands.length}`, columns: candCols, rows: cands.map(x => pick(x, candCols)) });
    sections.push({
      kind: 'kv', id: 'CPS.RAW.REJECTIONS',
      rows: c.rejection_summary ? kvOf(c.rejection_summary as Raw) : [],
    });
  } else {
    sections.push({ kind: 'kv', id: 'CPS.RAW', note: noteFor(d.cpsRaw, d.errors.cps, 'loading'), rows: [] });
  }

  return sections;
}

export function exportHeader(scannedAt: string | null | undefined): string {
  return `THETA_HARVEST MACHINE EXPORT scanned_at=${scannedAt ?? '∅'} generated_at=${new Date().toISOString()}`;
}
