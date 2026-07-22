'use client';

/**
 * v2 Shadow Review panel (Phase B, operator-only, transitional — removed at Phase E).
 * Renders the v1-vs-v2 comparison from the public /api/shadow/summary + /diff endpoints:
 * the summary strip (agreement, divergence counts, per-sleeve gating, oscillation), the
 * B0.5 health metrics (V2_LOOSER trend + per-sleeve gate rates), and filterable drill rows.
 * Display-only — nothing here computes gate state (P1); it reads what the API classified.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { fetchShadowSummary, fetchShadowDiff } from '@/lib/api';
import type { ShadowSummaryResponse, ShadowDiffRow } from '@/lib/types';

const CLASS_FILTERS = ['ALL', 'V2_STRICTER', 'V2_LOOSER', 'STATE_MISMATCH', 'AGREE', 'NODATA_SKEW'] as const;

function pct(x: number | null | undefined, digits = 0): string {
  return x == null ? '—' : `${(x * 100).toFixed(digits)}%`;
}
function num(x: number | null | undefined, digits = 2): string {
  return x == null ? '—' : x.toFixed(digits);
}

function Stat({ label, value, sub }: { label: string; value: React.ReactNode; sub?: string }) {
  return (
    <div className="bg-surface rounded-md px-3 py-2.5 border border-border-subtle">
      <div className="font-primary text-[9px] font-semibold text-txt-tertiary tracking-wider uppercase">{label}</div>
      <div className="font-mono text-base font-semibold text-txt mt-0.5">{value}</div>
      {sub && <div className="font-primary text-[9px] text-txt-tertiary mt-0.5">{sub}</div>}
    </div>
  );
}

/** Divergence chip — subtle tones (STRICTER = v2 vetoes what v1 trades; LOOSER = inverse). */
function DivergenceChip({ cls }: { cls: string | null }) {
  if (!cls) return <span className="text-txt-tertiary">—</span>;
  const style: Record<string, string> = {
    AGREE: 'text-txt-tertiary border-border-subtle',
    V2_STRICTER: 'text-txt border-border-strong bg-surface-alt',
    V2_LOOSER: 'text-secondary border-secondary-30 bg-secondary-subtle',
    STATE_MISMATCH: 'text-accent border-accent-30 bg-accent-subtle',
    NODATA_SKEW: 'text-txt-tertiary border-border-subtle',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full font-primary text-[9px] font-semibold tracking-wide border whitespace-nowrap ${style[cls] ?? style.AGREE}`}>
      {cls.replace('V2_', '').replace('_', ' ')}
    </span>
  );
}

export default function ShadowPanel() {
  const [summary, setSummary] = useState<ShadowSummaryResponse | null>(null);
  const [rows, setRows] = useState<ShadowDiffRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [clsFilter, setClsFilter] = useState<string>('ALL');
  const [sleeveFilter, setSleeveFilter] = useState<'ALL' | 'INDEX' | 'SINGLE'>('ALL');
  const [warmOnly, setWarmOnly] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchShadowSummary(20), fetchShadowDiff(500)])
      .then(([s, d]) => { if (!cancelled) { setSummary(s); setRows(d.rows); } })
      .catch(e => { if (!cancelled) setError(e?.message ? String(e.message) : 'Failed to load shadow data'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const dc = summary?.divergence_counts ?? {};
  const latestDate = rows.length ? rows.reduce((a, r) => (r.date > a ? r.date : a), rows[0].date) : null;

  const filtered = useMemo(() => rows.filter(r => {
    if (clsFilter !== 'ALL' && r.divergence_class !== clsFilter) return false;
    if (sleeveFilter === 'INDEX' && !r.is_etf) return false;
    if (sleeveFilter === 'SINGLE' && r.is_etf) return false;
    if (warmOnly && !r.v2_warm) return false;
    return true;
  }), [rows, clsFilter, sleeveFilter, warmOnly]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  if (error) {
    return (
      <div className="bg-surface rounded-lg border border-border px-5 py-8 text-center">
        <p className="text-sm text-txt-secondary">Could not load shadow data.</p>
        <p className="text-xs text-txt-tertiary mt-1">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="bg-surface rounded-lg border border-border px-4 sm:px-6 py-4">
        <div className="flex items-baseline justify-between flex-wrap gap-2">
          <h2 className="font-secondary text-xl font-medium text-txt">🔭 v2 Shadow Review</h2>
          <span className="font-mono text-2xs text-txt-tertiary">
            {summary?.n_ticker_days ?? 0} ticker-days · {summary?.dates?.length ?? 0} sessions
            {latestDate ? ` · latest ${latestDate}` : ''}
          </span>
        </div>
        <p className="text-xs text-txt-tertiary mt-1 leading-relaxed">
          The forward-looking engine running silently beside v1. Advisory only — it changes no live
          decision until it earns cutover with evidence. This panel is the operator&apos;s calibration view.
        </p>
      </div>

      {/* Summary strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5">
        <Stat label="Agreement" value={pct(summary?.agreement_rate)} sub="v1 = v2 actionability" />
        <Stat label="V2 Stricter" value={dc.V2_STRICTER ?? 0} sub="v1 trades, v2 gates" />
        <Stat label="V2 Looser" value={dc.V2_LOOSER ?? 0} sub="v2 allows, v1 gates" />
        <Stat label="State mismatch" value={dc.STATE_MISMATCH ?? 0} sub="regime differs" />
        <Stat label="Warm coverage" value={pct(summary?.warm_coverage)} sub="forecaster fitted" />
        <Stat label="No-data skew" value={dc.NODATA_SKEW ?? 0} sub="one side blind" />
      </div>

      {/* B0.5 health strip — per-sleeve gating + oscillation (hysteresis payoff) */}
      <div className="bg-bg-alt rounded-lg border border-border-subtle px-4 sm:px-5 py-4">
        <div className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase mb-3">
          Gate health · per sleeve
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
          <Stat label="Index gate · v1 / v2" value={`${pct(summary?.index_gating_rate_v1)} / ${pct(summary?.index_gating_rate_v2)}`} sub="ETF sleeve non-actionable" />
          <Stat label="Single gate · v1 / v2" value={`${pct(summary?.single_gating_rate_v1)} / ${pct(summary?.single_gating_rate_v2)}`} sub="single-name non-actionable" />
          <Stat label="Oscillation · v1 / v2" value={`${num(summary?.oscillation_v1)} / ${num(summary?.oscillation_v2)}`} sub="gate flips / ticker (↓ = steadier)" />
          <Stat label="V2 Looser" value={dc.V2_LOOSER ?? 0} sub="strictness-health (0 ⇒ watch)" />
        </div>
        <p className="text-[10px] text-txt-tertiary mt-2.5 leading-relaxed italic">
          Watch the single-name v2 gate rate (G2 term-slope over-fires on backwardated single names) and
          keep V2 Looser above zero — a gate that clears nothing is stuck, not calibrated.
        </p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center gap-1 flex-wrap">
          {CLASS_FILTERS.map(c => (
            <button
              key={c}
              onClick={() => setClsFilter(c)}
              className={`px-2.5 py-1 rounded-full text-[10px] font-primary font-semibold tracking-wide border transition-colors ${
                clsFilter === c ? 'bg-txt text-bg border-transparent' : 'text-txt-tertiary border-border-subtle hover:text-txt-secondary'
              }`}
            >
              {c === 'ALL' ? 'All' : c.replace('V2_', '').replace('_', ' ')}
            </button>
          ))}
        </div>
        <span className="w-px h-4 bg-border-subtle mx-1 hidden sm:inline-block" />
        {(['ALL', 'INDEX', 'SINGLE'] as const).map(s => (
          <button
            key={s}
            onClick={() => setSleeveFilter(s)}
            className={`px-2.5 py-1 rounded-full text-[10px] font-primary font-semibold tracking-wide border transition-colors ${
              sleeveFilter === s ? 'bg-txt text-bg border-transparent' : 'text-txt-tertiary border-border-subtle hover:text-txt-secondary'
            }`}
          >
            {s === 'ALL' ? 'All sleeves' : s === 'INDEX' ? 'Index/ETF' : 'Single-name'}
          </button>
        ))}
        <label className="flex items-center gap-1.5 text-[10px] text-txt-secondary cursor-pointer ml-1">
          <input type="checkbox" checked={warmOnly} onChange={e => setWarmOnly(e.target.checked)} className="accent-primary" />
          Warm only
        </label>
        <span className="font-mono text-2xs text-txt-tertiary ml-auto">{filtered.length} rows</span>
      </div>

      {/* Drill table */}
      <div className="bg-surface rounded-lg border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-separate border-spacing-0 text-xs">
            <thead>
              <tr>
                {['Date', 'Ticker', 'v1 Action', 'v1 Regime', 'v2 Gate', 'Elig', 'Divergence', 'FVRP', 'z', '1M/3M', 'accel↓', 'Reason'].map(h => (
                  <th key={h} className="font-primary text-[9px] font-semibold text-txt-tertiary tracking-wider uppercase px-3 py-2 text-left whitespace-nowrap border-b border-border-subtle">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((r, i) => (
                <tr key={`${r.date}-${r.ticker}-${i}`} className="hover:bg-surface-alt" style={{ opacity: r.v2_warm ? 1 : 0.55 }}>
                  <td className="px-3 py-2 font-mono text-2xs text-txt-tertiary whitespace-nowrap border-b border-border-subtle">{r.date}</td>
                  <td className="px-3 py-2 font-primary font-semibold text-txt whitespace-nowrap border-b border-border-subtle">
                    {r.ticker}
                    {r.is_etf && <span className="ml-1 text-[8px] text-txt-tertiary align-top">ETF</span>}
                  </td>
                  <td className="px-3 py-2 text-txt-secondary whitespace-nowrap border-b border-border-subtle">{r.v1_action ?? '—'}</td>
                  <td className="px-3 py-2 text-txt-tertiary whitespace-nowrap border-b border-border-subtle">{r.v1_regime ?? '—'}</td>
                  <td className="px-3 py-2 font-mono text-txt whitespace-nowrap border-b border-border-subtle">
                    {r.v2_gate_state ?? '—'}{r.v2_transient ? ' ·t' : ''}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap border-b border-border-subtle">
                    {r.v2_eligible == null ? <span className="text-txt-tertiary">—</span>
                      : r.v2_eligible ? <span className="text-secondary font-semibold">yes</span>
                      : <span className="text-txt-tertiary">no</span>}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap border-b border-border-subtle"><DivergenceChip cls={r.divergence_class} /></td>
                  <td className="px-3 py-2 font-mono text-txt-secondary text-right whitespace-nowrap border-b border-border-subtle">{num(r.fvrp_ratio)}</td>
                  <td className="px-3 py-2 font-mono text-txt-tertiary text-right whitespace-nowrap border-b border-border-subtle">{r.fvrp_z == null ? '—' : `${r.fvrp_z > 0 ? '+' : ''}${r.fvrp_z.toFixed(2)}`}</td>
                  <td className="px-3 py-2 font-mono text-txt-tertiary text-right whitespace-nowrap border-b border-border-subtle">{num(r.slope_1m3m)}</td>
                  <td className="px-3 py-2 font-mono text-txt-tertiary text-right whitespace-nowrap border-b border-border-subtle">{num(r.accel_dn)}</td>
                  <td className="px-3 py-2 text-txt-tertiary border-b border-border-subtle max-w-[240px] truncate" title={r.divergence_reason ?? ''}>
                    {r.divergence_reason || '—'}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={12} className="px-3 py-8 text-center text-xs text-txt-tertiary">No rows match these filters.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
