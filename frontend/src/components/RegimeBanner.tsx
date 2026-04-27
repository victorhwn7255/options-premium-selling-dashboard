'use client';

import type { DashboardTicker, VrpHistoryPoint } from '@/lib/types';
import VrpActivityGrid from './VrpActivityGrid';

interface RegimeBannerProps {
  data: DashboardTicker[];
  vrpHistory?: VrpHistoryPoint[];
  vrpYear?: number;
}

export function computeRegime(data: DashboardTicker[]) {
  // Exclude earnings-gated and no-data tickers — they contaminate regime metrics
  const eligible = data.filter(d => d.action !== 'SKIP' && d.action !== 'NO DATA');
  if (eligible.length === 0) {
    return {
      regime: 'THE PLAYOFFS', colorClass: 'text-secondary', borderClass: 'border-l-secondary',
      desc: '', detail: 'All tickers near earnings — insufficient data for regime.',
      avgVRP: 0, avgTermSlope: 0, avgRVAccel: 0,
      tradeableCount: 0, eligibleCount: 0, total: data.length, isHostile: false,
    };
  }
  const tradeable = eligible.filter(d => d.action === 'SELL' || d.action === 'CONDITIONAL');
  const avgVRP = eligible.reduce((s, d) => s + (d.vrp ?? 0), 0) / eligible.length;
  const avgTermSlope = eligible.reduce((s, d) => s + d.termSlope, 0) / eligible.length;
  const avgRVAccel = eligible.reduce((s, d) => s + d.rvAccel, 0) / eligible.length;

  // Use backend per-ticker regime (NORMAL/CAUTION/DANGER) for market-wide assessment
  const dangerCount = eligible.filter(d => d.regime === 'DANGER').length;
  const stressCount = eligible.filter(d => d.regime === 'DANGER' || d.regime === 'CAUTION').length;
  const dangerPct = dangerCount / eligible.length;
  const stressPct = stressCount / eligible.length;

  let regime: string, colorClass: string, borderClass: string, desc: string, detail: string;

  const dangerPctStr = Math.round(dangerPct * 100);
  const stressPctStr = Math.round(stressPct * 100);

  if (dangerPct > 0.40) {
    regime = 'OFF SEASON';
    colorClass = 'text-error';
    borderClass = 'border-l-error';
    desc = "Game's out of reach — sit on the bench, protect your capital";
    detail = `${dangerPctStr}% of tickers in DANGER regime — systemic stress across the universe. No premium selling today.`;
  } else if (stressPct > 0.25) {
    regime = 'REGULAR SEASON';
    colorClass = 'text-warning';
    borderClass = 'border-l-warning';
    desc = 'Every possession counts — play tight, no turnovers';
    detail = `${stressPctStr}% stressed (${dangerCount} DANGER, ${stressCount - dangerCount} CAUTION). Defined-risk only, reduced sizing.`;
  } else if (avgVRP > 8 && avgTermSlope < 0.90) {
    regime = 'THE FINALS';
    colorClass = 'text-accent';
    borderClass = 'border-l-accent';
    desc = "You're on fire — wide VRP in contango, keep shooting";
    detail = `Avg VRP at ${avgVRP.toFixed(1)} with deep contango — statistical edge is at its widest.`;
  } else {
    regime = 'THE PLAYOFFS';
    colorClass = 'text-secondary';
    borderClass = 'border-l-secondary';
    desc = 'Running your sets — nothing weird, execute the playbook';
    detail = `Most tickers in normal regime with stable vol. Run your standard playbook.`;
  }

  return {
    regime, colorClass, borderClass, desc, detail,
    avgVRP, avgTermSlope, avgRVAccel,
    tradeableCount: tradeable.length,
    eligibleCount: eligible.length,
    total: data.length,
    isHostile: regime === 'OFF SEASON',
  };
}

export default function RegimeBanner({ data, vrpHistory, vrpYear }: RegimeBannerProps) {
  const r = computeRegime(data);

  const metrics: Array<{
    label: string;
    value: string;
    good: boolean;
    tooltip?: { title: string; body: string };
  }> = [
    {
      label: 'Avg VRP',
      value: r.avgVRP.toFixed(1),
      good: r.avgVRP > 5,
      tooltip: {
        title: 'Eligible-set mean',
        body: `Averaged over the ${r.eligibleCount} tickers that aren't earnings-gated (DTE ≤ 14) or NO DATA. The heatmap below uses the full 33-ticker universe, so the two values can differ.`,
      },
    },
    { label: 'Term Slope', value: r.avgTermSlope.toFixed(2), good: r.avgTermSlope < 0.95 },
    { label: 'RV Accel', value: r.avgRVAccel.toFixed(2), good: r.avgRVAccel < 1.08 },
    { label: 'Tradeable', value: `${r.tradeableCount}/${r.eligibleCount}`, good: r.tradeableCount > 3 },
  ];

  return (
    <div className="bg-surface rounded-lg border border-border overflow-hidden">
      {/* Top row: Regime name + metrics in one line */}
      <div className="px-4 sm:px-6 py-4 sm:py-5 flex flex-col sm:flex-row sm:items-center gap-4">
        {/* Regime name — compact, left-aligned */}
        <div className="flex items-center gap-3 sm:min-w-[200px]">
          <div>
            <span className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase block">
              Market Regime
            </span>
            <div className={`font-secondary text-xl sm:text-2xl font-medium ${r.colorClass} leading-tight mt-0.5`}>
              {r.regime}
            </div>
          </div>
        </div>

        {/* Metrics — inline row, grows to fill */}
        <div className="flex-1 grid grid-cols-4 gap-3 sm:gap-4">
          {metrics.map(m => {
            const labelEl = (
              <span className="inline-flex items-center gap-1 font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase">
                {m.label}
                {m.tooltip && (
                  <svg
                    className="w-2.5 h-2.5 opacity-60"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                    aria-hidden="true"
                  >
                    <circle cx="12" cy="12" r="9" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 16v-4M12 8h.01" />
                  </svg>
                )}
              </span>
            );
            const valueEl = (
              <span
                className={`font-mono text-lg sm:text-xl font-semibold block mt-0.5 ${m.good ? 'text-txt' : 'text-warning'}`}
              >
                {m.value}
              </span>
            );

            if (!m.tooltip) {
              return (
                <div key={m.label} className="text-center">
                  <span className="block">{labelEl}</span>
                  {valueEl}
                </div>
              );
            }

            return (
              <div key={m.label} className="text-center relative group cursor-help">
                <span className="block">{labelEl}</span>
                {valueEl}
                <span className="pointer-events-none absolute left-1/2 -translate-x-1/2 top-full mt-2 z-50 opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 origin-top">
                  <span
                    className="block rounded-lg px-4 py-3 text-left"
                    style={{
                      background: 'var(--color-tooltip-bg)',
                      color: 'var(--color-tooltip-text)',
                      boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
                      width: 360,
                    }}
                  >
                    <span
                      className="block text-[9px] font-semibold uppercase tracking-widest mb-1.5"
                      style={{ color: 'var(--color-tooltip-label)' }}
                    >
                      {m.tooltip.title}
                    </span>
                    <span className="block text-[11px] leading-relaxed">{m.tooltip.body}</span>
                  </span>
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Activity grid: daily Avg VRP heatmap */}
      {vrpHistory && vrpHistory.length > 0 && (
        <div className="px-4 sm:px-6 py-6 sm:py-7 border-t border-border-subtle">
          <VrpActivityGrid year={vrpYear ?? new Date().getFullYear()} points={vrpHistory} />
        </div>
      )}

      {/* Bottom strip: description */}
      <div className="px-4 sm:px-6 py-2.5 border-t border-border-subtle bg-surface-alt">
        <p className="text-xs text-txt-secondary leading-relaxed">
          <span className={`font-semibold ${r.colorClass}`}>{r.desc}</span>
          {r.detail && <span className="text-txt-tertiary"> — {r.detail}</span>}
        </p>
      </div>

      {/* Hostile alert */}
      {r.isHostile && (
        <div className="px-4 sm:px-6 py-2.5 bg-error-subtle border-t border-error-20 text-xs leading-normal"
          style={{ color: 'var(--color-error)' }}>
          No premium selling today. Let&apos;s be disciplined and wait for better days.
        </div>
      )}
    </div>
  );
}
