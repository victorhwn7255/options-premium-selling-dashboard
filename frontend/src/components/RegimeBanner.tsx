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
      regime: 'THE PLAYOFFS', colorClass: 'text-black', borderClass: 'border border-black',
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
    colorClass = 'text-black';
    borderClass = 'border-l-0';
    desc = "Game's out of reach — sit on the bench, protect your capital";
    detail = `${dangerPctStr}% of tickers in DANGER regime — systemic stress across the universe. No premium selling today.`;
  } else if (stressPct > 0.25) {
    regime = 'REGULAR SEASON';
    colorClass = 'text-black';
    borderClass = 'border-l-8 border-black';
    desc = 'Every possession counts — play tight, no turnovers';
    detail = `${stressPctStr}% of tickers are stressed (${dangerCount} DANGER, ${stressCount - dangerCount} CAUTION). Play tight — defined-risk structures only, reduced sizing.`;
  } else if (avgVRP > 8 && avgTermSlope < 0.90) {
    regime = 'THE FINALS';
    colorClass = 'text-black';
    borderClass = 'border-2 border-black';
    desc = "You're on fire — wide VRP in contango, keep shooting";
    detail = `Avg VRP at ${avgVRP.toFixed(1)} with deep contango — the options market is significantly overpricing volatility. Statistical edge is at its widest.`;
  } else {
    regime = 'THE PLAYOFFS';
    colorClass = 'text-black';
    borderClass = 'border border-black';
    desc = 'Running your sets — nothing weird, execute the playbook';
    detail = `Most tickers in normal regime with stable vol. Run your standard playbook on high-scoring tickers.`;
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
    { label: 'Avg Term Slope', value: r.avgTermSlope.toFixed(2), good: r.avgTermSlope < 0.95 },
    { label: 'RV Accel', value: r.avgRVAccel.toFixed(2), good: r.avgRVAccel < 1.08 },
    { label: 'Tradeable', value: `${r.tradeableCount}/${r.eligibleCount}`, good: r.tradeableCount > 3 },
  ];

  // Determine container classes based on regime
  const isHostile = r.regime === 'OFF SEASON';
  const containerClass = isHostile
    ? 'bg-black text-white p-4 sm:p-5 sm:px-6'
    : r.regime === 'REGULAR SEASON'
      ? 'bg-white border-l-8 border-black p-4 sm:p-5 sm:px-6'
      : r.regime === 'THE FINALS'
        ? 'bg-white border-2 border-black p-4 sm:p-5 sm:px-6'
        : 'bg-white border border-black p-4 sm:p-5 sm:px-6';

  // Regime name extra classes
  const regimeNameExtra = isHostile
    ? 'uppercase tracking-tight'
    : r.regime === 'REGULAR SEASON'
      ? 'italic'
      : '';

  return (
    <div className={containerClass}>
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        {/* Left: regime info */}
        <div>
          <span className={`font-mono text-xs font-semibold ${isHostile ? 'text-white/60' : 'text-[#525252]'} tracking-widest uppercase`}>
            Market Regime
          </span>
          <div className={`font-display text-4xl font-bold ${isHostile ? 'text-white' : 'text-black'} leading-tight mt-1.5 ${regimeNameExtra}`}>
            {r.regime}
          </div>
          {r.desc && (
            <p className={`font-body text-lg text-[#525252] italic mt-5 ${isHostile ? '!text-white/80' : ''}`}>
              {r.desc}
            </p>
          )}
          <p className={`font-body text-lg text-[#525252] italic max-w-[480px] leading-relaxed mt-1 ${isHostile ? '!text-white/70' : ''}`}>
            {r.detail}
          </p>
        </div>

        {/* Right: aggregate metrics */}
        <div className="grid grid-cols-2 gap-x-6 gap-y-2 sm:flex sm:gap-7 sm:items-start">
          {metrics.map(m => (
            <div key={m.label} className="text-left sm:text-right">
              <span className={`font-mono text-xs font-semibold ${isHostile ? 'text-white/60' : 'text-[#525252]'} tracking-widest uppercase`}>
                {m.label}
              </span>
              <div className="mt-0.5">
                <span className={m.good
                  ? `font-mono text-xl font-semibold ${isHostile ? 'text-white' : 'text-black'}`
                  : `font-mono text-xl font-bold italic ${isHostile ? 'text-white' : 'text-black'}`
                }>
                  {m.value}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Hostile alert */}
      {r.isHostile && (
        <div className="bg-white text-black border-l-4 border-white px-4 py-3 mt-6 font-mono text-sm">
          No premium selling today. Let&apos;s be disciplined and wait for better days.
        </div>
      )}

    </div>
  );
}
