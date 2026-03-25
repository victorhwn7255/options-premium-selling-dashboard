'use client';

import React, { useMemo, useState, useEffect } from 'react';
import {
  AreaChart, Area, ComposedChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { DashboardTicker, VolHistoryPoint, TermStructurePoint2, TickerDelta } from '@/lib/types';
import { fetchTickerHistory } from '@/lib/api';

interface DetailPanelProps {
  ticker: DashboardTicker | null;
  delta?: TickerDelta | null;
}

/* -- Chart tooltip ---------------------------------------- */

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) {
  if (!active || !payload?.length) return null;

  return (
    <div
      className="px-3 py-2 font-mono text-xs bg-black text-white"
      style={{ lineHeight: 1.6 }}
    >
      <div className="font-semibold mb-0.5">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-1.5">
          <div className="w-[7px] h-[7px] shrink-0" style={{ background: p.color }} />
          <span style={{ opacity: 0.7 }}>{p.name}:</span>
          <span className="font-mono text-xs text-white">
            {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
          </span>
        </div>
      ))}
    </div>
  );
}

/* -- Action chip ------------------------------------------ */

function ActionChip({ action, reason }: { action: string; reason: string | null }) {
  const configs: Record<string, { className: string; label: string }> = {
    SELL: {
      className: 'bg-black text-white font-mono text-xs font-medium uppercase tracking-widest px-3 py-1',
      label: 'SELL PREMIUM',
    },
    CONDITIONAL: {
      className: 'border border-black text-black font-mono text-xs font-medium uppercase tracking-widest px-3 py-1',
      label: 'CONDITIONAL',
    },
    'NO EDGE': {
      className: 'text-[#525252] font-mono text-xs font-medium uppercase tracking-widest',
      label: 'NO EDGE',
    },
    AVOID: {
      className: 'bg-black text-white font-mono text-xs font-medium uppercase tracking-widest px-3 py-1 border-l-4 border-white',
      label: 'AVOID',
    },
    SKIP: {
      className: 'text-[#525252] font-mono text-xs font-medium uppercase tracking-widest line-through',
      label: reason || 'SKIP',
    },
    'NO DATA': {
      className: 'text-[#525252] font-mono text-xs font-medium uppercase tracking-widest',
      label: 'NO DATA',
    },
  };
  const c = configs[action] || configs['NO EDGE'];

  return (
    <span className={`inline-flex items-center whitespace-nowrap ${c.className}`}>
      {c.label}
    </span>
  );
}

function SizingChip({ sizing }: { sizing?: string }) {
  if (!sizing || sizing === 'Full') return null;
  const isHalf = sizing === 'Half';

  return (
    <span className={`inline-flex items-center font-mono text-xs font-medium uppercase ${isHalf ? 'text-[#525252]' : 'text-[#525252] italic'}`}>
      &darr; {sizing}
    </span>
  );
}

/* -- Main component --------------------------------------- */

export default function DetailPanel({ ticker, delta }: DetailPanelProps) {

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
      <div className="bg-white border border-dashed border-black px-6 py-12 text-center">
        <p className="text-sm text-[#525252] font-body">
          Select a ticker to view trade construction
        </p>
      </div>
    );
  }

  const isSkipped = ticker.action === 'SKIP';
  const isAvoided = ticker.action === 'AVOID';
  const isNoData = ticker.action === 'NO DATA';

  // Trade construction from API
  const suggestDelta = ticker.suggestedDelta
    ?? (ticker.ivPct >= 80 ? '16\u0394' : ticker.ivPct >= 60 ? '20\u0394' : '25\u0394');
  const suggestStructure = ticker.suggestedStructure
    ?? ((ticker.vrp ?? 0) > 10
      ? 'Short strangle or jade lizard'
      : (ticker.vrp ?? 0) > 6
        ? 'Put credit spread or iron condor'
        : 'Narrow put spread (defined risk)');
  const suggestDTE = ticker.suggestedDte
    ?? (ticker.ivPct >= 80 ? '30-38 DTE' : '38-45 DTE');
  const suggestSize = ticker.sizing === 'Half' ? '\u00BD standard' :
    ticker.sizing === 'Quarter' ? '\u00BC standard' : 'Standard';

  const metricsGrid = [
    { label: 'VRP', value: ticker.vrp != null ? ticker.vrp.toFixed(1) : 'N/A', sub: ticker.iv != null ? `IV ${ticker.iv.toFixed(1)} \u2212 RV ${ticker.rv30.toFixed(1)}` : 'No reliable IV', highlight: ticker.vrp != null && ticker.vrp >= 8, warn: false },
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

  const chartAxisStyle = { fontSize: 11, fontFamily: "'JetBrains Mono', monospace", fill: '#525252' };

  return (
    <div
      className="bg-white border border-black overflow-hidden"
      style={{ borderTop: '4px solid #000000' }}
    >
      {/* Header */}
      <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-[#E5E5E5]">
        <div className="flex justify-between items-start flex-wrap gap-3">
          <div>
            <div className="flex items-baseline gap-2.5">
              <span className="font-display text-3xl sm:text-4xl font-bold text-black tracking-tight">{ticker.sym}</span>
              <span className="text-lg text-[#525252] font-body">{ticker.name}</span>
            </div>
            <div className="flex gap-2 mt-2 flex-wrap items-center">
              <ActionChip action={ticker.action} reason={ticker.actionReason} />
              <SizingChip sizing={ticker.sizing} />
              {ticker.regime !== 'NORMAL' && (
                <span className="bg-black text-white font-mono text-[10px] font-medium uppercase tracking-widest px-2 py-0.5">
                  {ticker.regime}
                </span>
              )}
              <span className="font-mono text-[10px] text-[#525252] uppercase tracking-widest px-2.5 py-0.5 border border-[#E5E5E5]">
                {ticker.sector}
              </span>
            </div>
          </div>
          <span className="font-mono text-xl sm:text-[26px] font-semibold text-black">
            ${ticker.price.toFixed(2)}
          </span>
        </div>
      </div>

      {/* 2x4 metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 border-b border-[#E5E5E5]">
        {metricsGrid.map((m, i) => {
          const borderCls = [
            i % 2 === 0 ? 'border-r' : '',
            i % 2 !== 0 && i % 4 !== 3 ? 'md:border-r' : '',
            i < 6 ? 'border-b' : '',
            i >= 4 && i < 6 ? 'md:border-b-0' : '',
          ].filter(Boolean).join(' ');
          return (
          <div
            key={m.label}
            className={`px-3 sm:px-5 py-3 sm:py-4 border-[#E5E5E5] ${borderCls} hover:border-black transition-colors duration-100`}
          >
            <span className="font-mono text-[10px] font-semibold text-[#525252] tracking-widest uppercase">
              {m.label}
            </span>
            <div className="mt-1">
              <span
                className={`font-mono text-lg font-semibold text-black ${m.warn ? 'font-bold italic underline decoration-2 decoration-black' : m.highlight ? 'font-bold' : ''}`}
              >
                {m.value}
              </span>
            </div>
            <div
              className={`text-2xs mt-0.5 font-mono ${m.warn ? 'font-bold italic text-black' : 'text-[#525252]'}`}
            >
              {m.sub}
            </div>
          </div>
          );
        })}
      </div>

      {/* Day-over-Day Comparison */}
      {delta ? (
        <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-[#E5E5E5]">
          <span className="font-mono text-[10px] font-semibold text-[#525252] tracking-widest uppercase block mb-3">
            Day-over-Day
          </span>
          <div className="grid grid-cols-[auto_1fr_1fr] gap-x-4 gap-y-1.5 font-mono text-sm">
            <span className="text-2xs text-[#525252] font-mono font-semibold uppercase tracking-wider">Metric</span>
            <span className="text-2xs text-[#525252] font-mono font-semibold uppercase tracking-wider text-right">Today</span>
            <span className="text-2xs text-[#525252] font-mono font-semibold uppercase tracking-wider text-right">Change</span>
            {[
              { label: 'Score', today: String(ticker.score), change: delta.score, precision: 0, invertColor: false },
              { label: 'VRP', today: ticker.vrp != null ? ticker.vrp.toFixed(1) : 'N/A', change: delta.vrp, precision: 1, invertColor: false },
              { label: 'Term Slope', today: ticker.termSlope.toFixed(2), change: delta.term_slope, precision: 3, invertColor: true },
              { label: 'RV Accel', today: ticker.rvAccel.toFixed(2), change: delta.rv_acceleration, precision: 3, invertColor: true },
              { label: 'IV', today: ticker.iv != null ? ticker.iv.toFixed(1) : 'N/A', change: delta.iv, precision: 1, invertColor: false },
              { label: 'IV Pct', today: `${ticker.ivPct}%`, change: delta.iv_percentile, precision: 1, invertColor: false },
              { label: 'Skew', today: ticker.skew25d.toFixed(1), change: delta.skew_25d, precision: 1, invertColor: false },
            ].map(row => {
              const changeStr = row.change != null
                ? `${row.change > 0 ? '+' : ''}${row.change.toFixed(row.precision)}`
                : '--';
              // Monochrome emphasis: favorable = normal, unfavorable = bold, neutral = muted
              const changeClass = row.change == null ? 'text-[#525252]'
                : row.change === 0 ? 'text-[#525252]'
                : (row.invertColor ? row.change < 0 : row.change > 0) ? 'text-black'
                : 'text-black font-bold';
              return (
                <React.Fragment key={row.label}>
                  <span className="text-[#525252] text-xs">{row.label}</span>
                  <span className="text-black text-right">{row.today}</span>
                  <span className={`text-right ${changeClass}`}>{changeStr}</span>
                </React.Fragment>
              );
            })}
            <span className="text-[#525252] text-xs">Regime</span>
            <span className="text-black text-right">{ticker.regime}</span>
            <span className={`text-right ${delta.regime_changed ? 'text-black font-bold' : 'text-[#525252]'}`}>
              {delta.regime_changed && delta.previous_regime ? `was ${delta.previous_regime}` : '--'}
            </span>
          </div>
        </div>
      ) : (
        <div className="px-4 sm:px-6 py-3 border-b border-[#E5E5E5]">
          <span className="text-2xs text-[#525252] font-mono">First scan &mdash; no prior day comparison available</span>
        </div>
      )}

      {/* Position Construction -- only if actionable */}
      {!isSkipped && !isAvoided && !isNoData && ticker.action !== 'NO EDGE' && (
        <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-[#E5E5E5]">
          <span className="font-mono text-[10px] font-semibold text-[#525252] tracking-widest uppercase block mb-3">
            Position Construction
          </span>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
            {[
              { label: 'Target Delta', value: suggestDelta },
              { label: 'Structure', value: suggestStructure },
              { label: 'DTE', value: suggestDTE },
              { label: 'Sizing', value: suggestSize },
            ].map(item => (
              <div key={item.label} className="bg-[#F5F5F5] px-3.5 py-3 border border-[#E5E5E5]">
                <div className="font-mono text-[10px] font-semibold text-[#525252] tracking-wider uppercase mb-1">
                  {item.label}
                </div>
                <div className="font-body text-xs font-medium text-black leading-snug">
                  {item.value}
                </div>
              </div>
            ))}
          </div>
          {/* Flags from API */}
          {ticker.flags && ticker.flags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {ticker.flags.map((flag, i) => (
                <span key={i} className="text-2xs px-2 py-0.5 border-l-4 border-black bg-[#F5F5F5] font-mono text-black">
                  {flag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Skip reason */}
      {isSkipped && (
        <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-[#E5E5E5]">
          <div className="px-4 py-3.5 border-l-4 border-black bg-[#F5F5F5] text-xs leading-normal font-mono text-black">
            <p><strong>Skipped:</strong> {ticker.actionReason}. No premium selling recommended for this ticker.</p>
            {ticker.preGateScore != null && (
              <p className="mt-1.5 text-[#525252]">
                Score without earnings gate: <span className="font-mono font-semibold text-black">{ticker.preGateScore}</span> — monitor post-earnings
              </p>
            )}
          </div>
        </div>
      )}

      {/* Avoid warning */}
      {isAvoided && (
        <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-[#E5E5E5]">
          <div className="px-4 py-3.5 bg-black text-white text-xs leading-normal font-mono">
            <p><strong>{ticker.regime === 'DANGER' ? 'Danger regime' : 'Caution regime'}:</strong> Do not sell premium on this ticker. {ticker.regime === 'DANGER' ? 'Deep backwardation or acute stress detected.' : 'Elevated risk — reduce exposure, defined risk only.'}</p>
          </div>
          {ticker.flags && ticker.flags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {ticker.flags.map((flag, i) => (
                <span key={i} className="text-2xs px-2 py-0.5 bg-black text-white font-mono">
                  {flag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* No data warning */}
      {isNoData && (
        <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-[#E5E5E5]">
          <div className="px-4 py-3.5 bg-[#F5F5F5] border border-[#E5E5E5] text-xs leading-normal text-[#525252] font-mono">
            <p><strong className="text-black">Insufficient data:</strong> Not enough liquid contracts to compute reliable IV. Metrics shown may be incomplete or unavailable.</p>
          </div>
          {ticker.flags && ticker.flags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {ticker.flags.map((flag, i) => (
                <span key={i} className="text-2xs px-2 py-0.5 bg-[#F5F5F5] border border-[#E5E5E5] text-[#525252] font-mono">
                  {flag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Charts -- IV/RV + Term Structure side by side */}
      <div className="grid grid-cols-1 md:grid-cols-2 border-t border-[#E5E5E5]">
        {/* IV/RV Chart */}
        <div className="px-5 pt-5 pb-4 md:border-r md:border-[#E5E5E5]">
          <div className="mb-3 flex items-baseline gap-3">
            <span className="font-display text-sm font-bold text-black">IV vs RV — 120 Day</span>
            <span className="font-mono text-[10px] text-[#525252]">— solid &middot; --- dashed</span>
          </div>
          {volHistory.length > 0 ? (
            <div className="w-full h-[150px] sm:h-[180px]">
              <ResponsiveContainer>
                <ComposedChart data={volHistory} margin={{ top: 5, right: 8, left: -15, bottom: 0 }}>
                  <CartesianGrid stroke="#E5E5E5" strokeDasharray="1 4" vertical={false} />
                  <XAxis dataKey="date" tick={chartAxisStyle} interval={20} axisLine={{ stroke: '#000000', strokeWidth: 1 }} tickLine={{ stroke: '#E5E5E5' }} />
                  <YAxis tick={chartAxisStyle} domain={['auto', 'auto']} axisLine={{ stroke: '#000000', strokeWidth: 1 }} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Area type="monotone" dataKey="iv" fill="#000000" fillOpacity={0.05} stroke="none" />
                  <Line type="monotone" dataKey="iv" stroke="#000000" strokeWidth={2} dot={false} name="IV" />
                  <Line type="monotone" dataKey="rv" stroke="#000000" strokeWidth={1} dot={false} name="RV30" strokeDasharray="6 4" />
                  <ReferenceLine y={0} stroke="#000000" strokeDasharray="4 4" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="w-full h-[150px] sm:h-[180px] flex items-center justify-center">
              <p className="text-xs text-[#525252] font-mono">Collecting history — chart available after first scan</p>
            </div>
          )}
        </div>

        {/* Term Structure */}
        <div className="px-5 pt-5 pb-4">
          <div className="mb-3 flex justify-between items-baseline">
            <span className="font-display text-sm font-bold text-black">Term Structure</span>
            <span
              className={`font-mono text-xs font-medium px-2 py-0.5 ${
                ticker.termSlope < 1
                  ? 'border border-black text-black'
                  : 'bg-black text-white'
              }`}
            >
              {ticker.termSlope < 1 ? 'Contango' : 'Backwardation'}
            </span>
          </div>
          {termStructure.length > 0 ? (
            <div className="w-full h-[150px] sm:h-[180px]">
              <ResponsiveContainer>
                <AreaChart data={termStructure} margin={{ top: 5, right: 8, left: -15, bottom: 0 }}>
                  <CartesianGrid stroke="#E5E5E5" strokeDasharray="1 4" vertical={false} />
                  <XAxis dataKey="label" tick={chartAxisStyle} axisLine={{ stroke: '#000000', strokeWidth: 1 }} tickLine={{ stroke: '#E5E5E5' }} />
                  <YAxis tick={chartAxisStyle} domain={['auto', 'auto']} axisLine={{ stroke: '#000000', strokeWidth: 1 }} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="iv"
                    fill="#000000"
                    fillOpacity={0.05}
                    stroke="#000000"
                    strokeWidth={2}
                    name="IV %"
                    dot={{ fill: '#000000', r: 3 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="w-full h-[150px] sm:h-[180px] flex items-center justify-center">
              <p className="text-xs text-[#525252] font-mono">No term structure data available</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
