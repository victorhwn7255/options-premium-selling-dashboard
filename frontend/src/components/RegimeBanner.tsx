'use client';

import type { DashboardTicker } from '@/lib/types';

interface RegimeBannerProps {
  data: DashboardTicker[];
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

export default function RegimeBanner({ data }: RegimeBannerProps) {
  const r = computeRegime(data);

  const metrics = [
    { label: 'Avg VRP', value: r.avgVRP.toFixed(1), good: r.avgVRP > 5 },
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
          {metrics.map(m => (
            <div key={m.label} className="text-center sm:text-center">
              <span className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase block">
                {m.label}
              </span>
              <span className={`font-mono text-lg sm:text-xl font-semibold block mt-0.5 ${m.good ? 'text-txt' : 'text-warning'}`}>
                {m.value}
              </span>
            </div>
          ))}
        </div>
      </div>

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
