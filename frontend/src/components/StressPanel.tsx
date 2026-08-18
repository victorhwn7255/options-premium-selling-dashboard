'use client';

/**
 * Phase C3 — portfolio stress panel (the Portfolio / Risk tab's highest-value
 * element). Each row is a cap: current value, limit, headroom — the bar fills
 * toward the limit and turns red ONLY on breach (monochrome otherwise).
 * All numbers computed server-side (/api/portfolio/stress); rendered verbatim.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { CapRow, StressReport, fetchPortfolioStress } from '@/lib/journal-api';

const CAP_LABELS: Record<string, string> = {
  book_stress: 'Book stressed loss',
  margin_util: 'Margin utilization',
  notional: 'Notional / equity',
  name_margin: 'Name margin',
  name_stress: 'Name stressed loss',
};

function usd(v: number): string {
  return '$' + Math.round(v).toLocaleString();
}

function CapBar({ row, label }: { row: CapRow; label?: string }) {
  const pct = Math.min((row.pct_of_limit ?? 0) * 100, 100);
  return (
    <div className="space-y-1">
      <div className="flex items-baseline justify-between gap-2 text-[11px]">
        <span className="text-txt-secondary">{label ?? CAP_LABELS[row.cap] ?? row.cap}</span>
        <span className="font-mono text-txt-tertiary">
          {usd(row.value)} / {usd(row.limit)}
          {row.breached
            ? <span className="text-error font-semibold"> · BREACH</span>
            : <span> · {usd(row.headroom)} headroom</span>}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-border-subtle overflow-hidden">
        <div
          className={`h-full rounded-full ${row.breached ? 'bg-error' : 'bg-txt-tertiary'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function StressPanel() {
  const [report, setReport] = useState<StressReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    fetchPortfolioStress()
      .then(r => { setReport(r); setError(null); })
      .catch(e => setError(e instanceof Error ? e.message : String(e)));
  }, []);
  useEffect(() => { reload(); }, [reload]);

  if (error) {
    return (
      <div className="bg-surface rounded-lg border border-border px-5 py-4">
        <h2 className="font-secondary text-lg font-medium text-txt">Book Risk</h2>
        <p className="text-xs text-txt-tertiary mt-1">{error}</p>
      </div>
    );
  }
  if (!report) return null;

  const { scenarios } = report;
  return (
    <div className="bg-surface rounded-lg border border-border overflow-hidden">
      <div className="px-4 sm:px-5 py-3 border-b border-border-subtle">
        <h2 className="font-secondary text-lg font-medium text-txt">Book Risk</h2>
        <p className="text-[11px] text-txt-tertiary">
          {report.positions_stressed === 0
            ? 'Book is flat — caps shown against a zero book'
            : `${report.positions_stressed} position${report.positions_stressed > 1 ? 's' : ''} stressed · equity $${report.equity.toLocaleString()}`}
        </p>
      </div>

      <div className="px-4 sm:px-5 py-4 space-y-4">
        {/* Stress scenarios */}
        <div className="grid sm:grid-cols-2 gap-3">
          {([['severe', scenarios.severe], ['mild', scenarios.mild]] as const).map(([key, s]) => (
            <div key={key} className="rounded border border-border-subtle bg-surface-alt px-3 py-2.5">
              <div className="text-[10px] uppercase tracking-widest text-txt-tertiary">{s.label}</div>
              <div className="font-mono text-lg text-txt mt-0.5">
                −{usd(s.loss)}
                <span className="text-xs text-txt-tertiary ml-2">
                  {(s.pct_equity * 100).toFixed(1)}% of equity
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Book-level caps */}
        <div className="space-y-2.5">
          {report.caps.map(c => <CapBar key={c.cap} row={c} />)}
        </div>

        {/* Per-name caps */}
        {report.per_name.length > 0 && (
          <div className="space-y-2.5 pt-1 border-t border-border-subtle">
            {report.per_name.map(n => (
              <React.Fragment key={n.ticker}>
                <CapBar row={n.margin} label={`${n.ticker} margin`} />
                <CapBar row={n.stress} label={`${n.ticker} stressed loss`} />
              </React.Fragment>
            ))}
          </div>
        )}

        {/* Headroom readout — the actionable line */}
        {report.headroom.length > 0 && (
          <div className="text-[11px] text-txt-secondary space-y-0.5">
            {report.headroom.map(h => (
              <div key={h.ticker}>
                ≈ <span className="font-mono">{h.more_contracts}</span> more {h.ticker} contracts
                before {h.binding_cap === 'none' ? 'any cap binds (50+ headroom)' : `the ${h.binding_cap.replace(/_/g, ' ')} binds`}
              </div>
            ))}
          </div>
        )}

        {report.book_notes.length > 0 && (
          <p className="text-[10px] text-txt-tertiary">{report.book_notes.join(' · ')}</p>
        )}
        <p className="text-[10px] text-txt-tertiary italic">{report.caveat}</p>
      </div>
    </div>
  );
}
