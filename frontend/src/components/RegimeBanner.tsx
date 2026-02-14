'use client';

import type { DashboardTicker } from '@/lib/types';

interface RegimeBannerProps {
  data: DashboardTicker[];
}

function computeRegime(data: DashboardTicker[]) {
  // Exclude earnings-gated tickers — their event-driven IV contaminates regime metrics
  const eligible = data.filter(d => d.action !== 'SKIP');
  if (eligible.length === 0) {
    return {
      regime: 'SHOOTAROUND', colorClass: 'text-secondary', borderClass: 'border-l-secondary',
      desc: 'All tickers near earnings — insufficient data for regime',
      avgVRP: 0, avgTermSlope: 0, avgRVAccel: 0,
      tradeableCount: 0, eligibleCount: 0, total: data.length, isHostile: false,
    };
  }
  const tradeable = eligible.filter(d => d.action === 'SELL' || d.action === 'CONDITIONAL');
  const avgVRP = eligible.reduce((s, d) => s + d.vrp, 0) / eligible.length;
  const avgTermSlope = eligible.reduce((s, d) => s + d.termSlope, 0) / eligible.length;
  const avgRVAccel = eligible.reduce((s, d) => s + d.rvAccel, 0) / eligible.length;
  const backwardation = eligible.filter(d => d.termSlope > 1.0).length;

  let regime: string, colorClass: string, borderClass: string, desc: string;

  if (backwardation >= 3 || avgTermSlope > 1.02) {
    regime = 'GARBAGE TIME';
    colorClass = 'text-error';
    borderClass = 'border-l-error';
    desc = "";
  } else if (avgRVAccel > 1.12 || backwardation >= 1) {
    regime = 'CLUTCH Q4';
    colorClass = 'text-warning';
    borderClass = 'border-l-warning';
    desc = 'Be cautious! Small positions, defined risk, no turnovers';
  } else if (avgVRP > 8 && avgTermSlope < 0.90) {
    regime = 'HEAT CHECK';
    colorClass = 'text-accent';
    borderClass = 'border-l-accent';
    desc = "Wide VRP in contango, keep shooting";
  } else {
    regime = 'SHOOTAROUND';
    colorClass = 'text-secondary';
    borderClass = 'border-l-secondary';
    desc = 'Standard conditions, execute the playbook';
  }

  return {
    regime, colorClass, borderClass, desc,
    avgVRP, avgTermSlope, avgRVAccel,
    tradeableCount: tradeable.length,
    eligibleCount: eligible.length,
    total: data.length,
    isHostile: regime === 'GARBAGE TIME',
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

  return (
    <div className={`bg-surface rounded-lg border border-border border-l-4 ${r.borderClass} p-5 px-6`}>
      <div className="flex justify-between items-center flex-wrap gap-4">
        {/* Left: regime info */}
        <div className="flex items-baseline gap-4">
          <div>
            <span className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase">
              Market Regime
            </span>
            <div className={`font-secondary text-[26px] font-medium ${r.colorClass} leading-tight mt-1.5`}>
              {r.regime}
            </div>
          </div>
          <p className="text-xs text-txt-secondary max-w-[420px] leading-normal pt-1">
            
            {r.desc}
          </p>
        </div>

        {/* Right: aggregate metrics */}
        <div className="flex gap-7 items-start">
          {metrics.map(m => (
            <div key={m.label} className="text-right">
              <span className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase">
                {m.label}
              </span>
              <div className="mt-0.5">
                <span className={`font-mono text-xl font-semibold ${m.good ? 'text-txt' : 'text-warning'}`}>
                  {m.value}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Hostile alert */}
      {r.isHostile && (
        <div className="mt-6 px-3.5 py-2.5 bg-error-subtle rounded-md border border-error-20 text-xs leading-normal"
          style={{ color: 'var(--color-error)' }}>
          No premium selling today. Let&apos;s be disciplined and wait for better days.
        </div>
      )}
    </div>
  );
}
