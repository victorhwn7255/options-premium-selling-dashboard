'use client';

import { useMemo, useState, useEffect } from 'react';
import {
  AreaChart, Area, ComposedChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { DashboardTicker, VolHistoryPoint, TermStructurePoint2 } from '@/lib/types';
import { fetchTickerHistory } from '@/lib/api';
import { useCssColors } from '@/hooks/useCssColors';

interface DetailPanelProps {
  ticker: DashboardTicker | null;
}

/* -- Chart tooltip ---------------------------------------- */

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) {
  const colors = useCssColors();
  if (!active || !payload?.length) return null;

  return (
    <div
      className="rounded-md px-3 py-2 font-primary text-xs shadow-lg"
      style={{ background: colors.text, color: colors.textInverse, lineHeight: 1.6 }}
    >
      <div className="font-semibold mb-0.5">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-1.5">
          <div className="w-[7px] h-[7px] rounded-full shrink-0" style={{ background: p.color }} />
          <span style={{ opacity: 0.7 }}>{p.name}:</span>
          <span className="font-mono text-xs" style={{ color: 'var(--color-txt-inverse)' }}>
            {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
          </span>
        </div>
      ))}
    </div>
  );
}

/* -- Action chip ------------------------------------------ */

function ActionChip({ action, reason }: { action: string; reason: string | null }) {
  const configs: Record<string, { bgClass: string; colorStyle: string; borderClass: string; label: string }> = {
    SELL: {
      bgClass: 'bg-success-subtle', colorStyle: 'var(--color-badge-sell)',
      borderClass: 'border-success-30', label: 'SELL PREMIUM',
    },
    CONDITIONAL: {
      bgClass: 'bg-warning-subtle', colorStyle: 'var(--color-badge-reduce)',
      borderClass: 'border-warning-30', label: 'CONDITIONAL',
    },
    'NO EDGE': {
      bgClass: 'bg-surface-alt', colorStyle: 'var(--color-txt-tertiary)',
      borderClass: 'border-border-subtle', label: 'NO EDGE',
    },
    SKIP: {
      bgClass: 'bg-error-subtle', colorStyle: 'var(--color-badge-avoid)',
      borderClass: 'border-error-20', label: reason || 'SKIP',
    },
  };
  const c = configs[action] || configs['NO EDGE'];

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full font-primary text-2xs font-semibold tracking-wide border ${c.bgClass} ${c.borderClass} whitespace-nowrap`}
      style={{ color: c.colorStyle }}
    >
      {c.label}
    </span>
  );
}

function SizingChip({ sizing }: { sizing?: string }) {
  if (!sizing || sizing === 'Full') return null;
  const isHalf = sizing === 'Half';

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full font-mono text-[10px] font-semibold border ${
        isHalf
          ? 'text-warning bg-warning-subtle border-warning-30'
          : 'text-error bg-error-subtle border-error-20'
      }`}
    >
      &darr; {sizing}
    </span>
  );
}

/* -- Main component --------------------------------------- */

export default function DetailPanel({ ticker }: DetailPanelProps) {
  const colors = useCssColors();

  // Fetch vol history from API
  const [volHistory, setVolHistory] = useState<VolHistoryPoint[]>([]);
  useEffect(() => {
    if (!ticker) {
      setVolHistory([]);
      return;
    }
    let cancelled = false;
    fetchTickerHistory(ticker.sym, 120)
      .then(data => {
        if (cancelled || !data.history?.length) return;
        setVolHistory(
          data.history.map((p: { date: string; iv: number | null; rv: number | null; vrp: number | null }) => ({
            date: new Date(p.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            iv: p.iv ?? 0,
            rv: p.rv ?? 0,
            vrp: p.vrp ?? 0,
          }))
        );
      })
      .catch(() => setVolHistory([]));
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticker?.sym]);

  // Convert term structure points from API
  const termStructure: TermStructurePoint2[] = useMemo(() => {
    if (!ticker?.termStructurePoints?.length) return [];
    return ticker.termStructurePoints.map(p => ({
      label: p.tenor_label,
      dte: p.tenor_days,
      iv: p.iv,
    }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticker?.sym]);

  // Empty state
  if (!ticker) {
    return (
      <div className="bg-surface rounded-lg border border-dashed border-border-strong px-6 py-12 text-center">
        <p className="text-sm text-txt-tertiary">
          Select a ticker to view trade construction
        </p>
      </div>
    );
  }

  const isSkipped = ticker.action === 'SKIP';

  // Trade construction from API
  const suggestDelta = ticker.suggestedDelta
    ?? (ticker.ivPct >= 80 ? '16\u0394' : ticker.ivPct >= 60 ? '20\u0394' : '25\u0394');
  const suggestStructure = ticker.suggestedStructure
    ?? (ticker.vrp > 10
      ? 'Short strangle or jade lizard'
      : ticker.vrp > 6
        ? 'Put credit spread or iron condor'
        : 'Narrow put spread (defined risk)');
  const suggestDTE = ticker.suggestedDte
    ?? (ticker.ivPct >= 80 ? '30-38 DTE' : '38-45 DTE');
  const suggestSize = ticker.sizing === 'Half' ? '\u00BD standard' :
    ticker.sizing === 'Quarter' ? '\u00BC standard' : 'Standard';

  const metricsGrid = [
    { label: 'VRP', value: ticker.vrp.toFixed(1), sub: `IV ${ticker.iv.toFixed(1)} \u2212 RV ${ticker.rv30.toFixed(1)}`, highlight: ticker.vrp >= 8, warn: false },
    { label: 'Term Slope', value: ticker.termSlope.toFixed(2), sub: ticker.termSlope < 1 ? 'Contango \u2713' : 'Backwardation \u26A0', highlight: false, warn: ticker.termSlope > 1 },
    { label: 'RV Accel', value: ticker.rvAccel.toFixed(2), sub: `RV10 ${ticker.rv10.toFixed(1)} / RV30 ${ticker.rv30.toFixed(1)}`, highlight: false, warn: ticker.rvAccel > 1.10 },
    { label: 'IV Percentile', value: `${ticker.ivPct}%`, sub: '252-day window', highlight: false, warn: false },
    { label: '25\u0394 Put Skew', value: ticker.skew25d.toFixed(1), sub: 'vol points above ATM', highlight: false, warn: false },
    {
      label: '\u03B8/\u03BD Ratio',
      value: ticker.thetaVega != null ? ticker.thetaVega.toFixed(2) : 'N/A',
      sub: ticker.theta != null && ticker.vega != null
        ? `\u03B8 ${ticker.theta.toFixed(2)} / \u03BD ${ticker.vega.toFixed(2)}`
        : 'Not available',
      highlight: false, warn: false,
    },
    {
      label: 'ATR 14',
      value: ticker.atr14 != null ? `$${ticker.atr14.toFixed(2)}` : 'N/A',
      sub: ticker.atr14 != null
        ? `${(ticker.atr14 / ticker.price * 100).toFixed(2)}% of spot`
        : 'Not available',
      highlight: false, warn: false,
    },
    {
      label: 'Earnings',
      value: ticker.earningsDTE != null ? `${ticker.earningsDTE}d` : (ticker.isEtf ? 'ETF' : '\u2014'),
      sub: ticker.earningsWarning ? '\u26A0 Within DTE window' : ticker.earningsDTE != null ? 'Clear' : (ticker.isEtf ? 'No earnings risk' : 'Not available'),
      highlight: false, warn: ticker.earningsWarning ?? false,
    },
  ];

  const chartAxisStyle = { fontSize: 9, fontFamily: "'JetBrains Mono', monospace", fill: colors.textTertiary };

  return (
    <div
      className="bg-surface rounded-lg border border-border overflow-hidden"
      style={{ borderTop: `3px solid ${isSkipped ? colors.error : colors.primary}` }}
    >
      {/* Header */}
      <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-border-subtle">
        <div className="flex justify-between items-start flex-wrap gap-3">
          <div>
            <div className="flex items-baseline gap-2.5">
              <span className="font-secondary text-lg sm:text-[22px] font-medium text-txt">{ticker.sym}</span>
              <span className="text-sm text-txt-tertiary">{ticker.name}</span>
            </div>
            <div className="flex gap-2 mt-2 flex-wrap items-center">
              <ActionChip action={ticker.action} reason={ticker.actionReason} />
              <SizingChip sizing={ticker.sizing} />
              <span className="text-2xs text-txt-tertiary px-2.5 py-0.5 rounded-full bg-bg-alt border border-border-subtle">
                {ticker.sector}
              </span>
            </div>
          </div>
          <span className="font-mono text-xl sm:text-[26px] font-semibold text-txt">
            ${ticker.price.toFixed(2)}
          </span>
        </div>
      </div>

      {/* 2x4 metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 border-b border-border-subtle">
        {metricsGrid.map((m, i) => {
          // Mobile (2-col): right border on left column, bottom border except last row
          // Desktop (4-col): right border except every 4th, bottom border first row only
          const borderCls = [
            i % 2 === 0 ? 'border-r' : '',
            i % 2 !== 0 && i % 4 !== 3 ? 'md:border-r' : '',
            i < 6 ? 'border-b' : '',
            i >= 4 && i < 6 ? 'md:border-b-0' : '',
          ].filter(Boolean).join(' ');
          return (
          <div
            key={m.label}
            className={`px-3 sm:px-5 py-3 sm:py-4 border-border-subtle ${borderCls}`}
          >
            <span className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase">
              {m.label}
            </span>
            <div className="mt-1">
              <span
                className="font-mono text-lg font-semibold"
                style={{ color: m.warn ? colors.error : m.highlight ? colors.secondary : colors.text }}
              >
                {m.value}
              </span>
            </div>
            <div
              className="text-2xs mt-0.5"
              style={{ color: m.warn ? colors.error : colors.textTertiary }}
            >
              {m.sub}
            </div>
          </div>
          );
        })}
      </div>

      {/* Position Construction -- only if actionable */}
      {!isSkipped && ticker.action !== 'NO EDGE' && (
        <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-border-subtle">
          <span className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase block mb-3">
            Position Construction
          </span>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
            {[
              { label: 'Target Delta', value: suggestDelta },
              { label: 'Structure', value: suggestStructure },
              { label: 'DTE', value: suggestDTE },
              { label: 'Sizing', value: suggestSize },
            ].map(item => (
              <div key={item.label} className="bg-bg-alt rounded-md px-3.5 py-3 border border-border-subtle">
                <div className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-wider uppercase mb-1">
                  {item.label}
                </div>
                <div className="font-primary text-xs font-medium text-txt leading-snug">
                  {item.value}
                </div>
              </div>
            ))}
          </div>
          {/* Flags from API */}
          {ticker.flags && ticker.flags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {ticker.flags.map((flag, i) => (
                <span key={i} className="text-2xs px-2 py-0.5 rounded-full bg-warning-subtle text-warning border border-warning-30">
                  {flag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Skip reason */}
      {isSkipped && (
        <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-border-subtle">
          <div className="px-4 py-3.5 bg-error-subtle rounded-md border border-error-20 text-xs leading-normal"
            style={{ color: 'var(--color-error)' }}>
            <p><strong>Skipped:</strong> {ticker.actionReason}. No premium selling recommended for this ticker.</p>
            {ticker.preGateScore != null && (
              <p className="mt-1.5 text-txt-secondary">
                Score without earnings gate: <span className="font-mono font-semibold">{ticker.preGateScore}</span> — monitor post-earnings
              </p>
            )}
          </div>
        </div>
      )}

      {/* Charts -- IV/RV + Term Structure side by side */}
      <div className="grid grid-cols-1 md:grid-cols-2 border-t border-border-subtle">
        {/* IV/RV Chart */}
        <div className="px-5 pt-5 pb-4 md:border-r md:border-border-subtle">
          <div className="mb-3">
            <span className="font-secondary text-sm font-medium text-txt">IV vs RV — 120 Day</span>
          </div>
          {volHistory.length > 0 ? (
            <div className="w-full h-[150px] sm:h-[180px]">
              <ResponsiveContainer>
                <ComposedChart data={volHistory} margin={{ top: 5, right: 8, left: -15, bottom: 0 }}>
                  <defs>
                    <linearGradient id={`vrpFill-${ticker.sym}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={colors.primary} stopOpacity={0.15} />
                      <stop offset="100%" stopColor={colors.primary} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.08)" />
                  <XAxis dataKey="date" tick={chartAxisStyle} interval={20} axisLine={false} tickLine={false} />
                  <YAxis tick={chartAxisStyle} domain={['auto', 'auto']} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Area type="monotone" dataKey="iv" fill={`url(#vrpFill-${ticker.sym})`} stroke="none" />
                  <Line type="monotone" dataKey="iv" stroke={colors.primary} strokeWidth={2} dot={false} name="IV" />
                  <Line type="monotone" dataKey="rv" stroke={colors.secondary} strokeWidth={1.5} dot={false} name="RV30" strokeDasharray="4 3" />
                  <ReferenceLine y={0} stroke={colors.borderStrong} strokeDasharray="3 3" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="w-full h-[150px] sm:h-[180px] flex items-center justify-center">
              <p className="text-xs text-txt-tertiary">Collecting history — chart available after first scan</p>
            </div>
          )}
        </div>

        {/* Term Structure */}
        <div className="px-5 pt-5 pb-4">
          <div className="mb-3 flex justify-between items-baseline">
            <span className="font-secondary text-sm font-medium text-txt">Term Structure</span>
            <span
              className={`font-mono text-2xs font-medium px-2 py-0.5 rounded-full ${
                ticker.termSlope < 1
                  ? 'text-secondary bg-secondary-subtle'
                  : 'text-error bg-error-subtle'
              }`}
            >
              {ticker.termSlope < 1 ? 'Contango' : 'Backwardation'}
            </span>
          </div>
          {termStructure.length > 0 ? (
            <div className="w-full h-[150px] sm:h-[180px]">
              <ResponsiveContainer>
                <AreaChart data={termStructure} margin={{ top: 5, right: 8, left: -15, bottom: 0 }}>
                  <defs>
                    <linearGradient id={`termFill-${ticker.sym}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={colors.accent} stopOpacity={0.15} />
                      <stop offset="100%" stopColor={colors.accent} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.08)" />
                  <XAxis dataKey="label" tick={chartAxisStyle} axisLine={false} tickLine={false} />
                  <YAxis tick={chartAxisStyle} domain={['auto', 'auto']} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="iv"
                    fill={`url(#termFill-${ticker.sym})`}
                    stroke={colors.accent}
                    strokeWidth={2}
                    name="IV %"
                    dot={{ fill: colors.accent, r: 3 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="w-full h-[150px] sm:h-[180px] flex items-center justify-center">
              <p className="text-xs text-txt-tertiary">No term structure data available</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
