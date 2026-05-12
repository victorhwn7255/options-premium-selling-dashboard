'use client';

import React from 'react';
import type { CreditPutSpreadCandidate, CreditPutSpreadLeg } from '@/lib/types';
import CreditPutSpreadActionBadge from './CreditPutSpreadActionBadge';
import CreditPutSpreadEconomicsCard from './CreditPutSpreadEconomicsCard';

interface CreditPutSpreadDetailPanelProps {
  candidate: CreditPutSpreadCandidate;
}

function dollars(v: number | undefined | null, digits = 2): string {
  if (v == null) return '—';
  return `$${v.toFixed(digits)}`;
}

function pct(v: number | undefined | null, digits = 1): string {
  if (v == null) return '—';
  return `${v.toFixed(digits)}%`;
}

function num(v: number | undefined | null, digits = 2): string {
  if (v == null) return '—';
  return v.toFixed(digits);
}

function LegRow({ label, leg }: { label: string; leg: CreditPutSpreadLeg }) {
  const fields: Array<[string, string]> = [
    ['Strike', dollars(leg.strike, 0)],
    ['Δ', leg.delta != null ? leg.delta.toFixed(3) : '—'],
    ['Bid', dollars(leg.bid)],
    ['Ask', dollars(leg.ask)],
    ['Mid', dollars(leg.mid)],
    ['IV', leg.iv != null ? `${leg.iv.toFixed(1)}%` : '—'],
    ['Vol', leg.volume?.toString() ?? '—'],
    ['OI', leg.openInterest?.toString() ?? '—'],
    ['bid_ask_ratio', leg.bidAskRatio != null ? `${(leg.bidAskRatio * 100).toFixed(1)}%` : '—'],
  ];
  return (
    <div className="border border-border-subtle rounded-md bg-bg-alt px-3 py-2.5">
      <div className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-wider uppercase mb-2">
        {label}
      </div>
      <div className="grid grid-cols-3 gap-x-3 gap-y-1.5">
        {fields.map(([k, v]) => (
          <div key={k} className="flex flex-col">
            <span className="text-[10px] text-txt-tertiary uppercase tracking-wider">{k}</span>
            <span className="font-mono text-xs text-txt">{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function CreditPutSpreadDetailPanel({
  candidate,
}: CreditPutSpreadDetailPanelProps) {
  // Base edge context — six tiles
  const baseEdge: Array<{ label: string; value: string; sub?: string }> = [
    {
      label: 'VRP',
      value: num(candidate.vrp, 1),
      sub: candidate.vrpRatio != null ? `ratio ${candidate.vrpRatio.toFixed(2)}` : undefined,
    },
    {
      label: 'IV Pct',
      value: pct(candidate.ivPercentile, 0),
      sub: '252-day window',
    },
    {
      label: 'Term Slope',
      value: num(candidate.termSlope, 2),
      sub: candidate.termSlope != null && candidate.termSlope < 1 ? 'contango ✓' : 'backwardation ⚠',
    },
    {
      label: 'RV Accel',
      value: num(candidate.rvAccel, 2),
      sub: candidate.rvAccelStatus ?? undefined,
    },
    {
      label: '25Δ Skew',
      value: num(candidate.skew, 1),
      sub: candidate.vrpZscore60d != null ? `60d z ${candidate.vrpZscore60d.toFixed(2)}` : '60d z unknown',
    },
    {
      label: 'Confirmation',
      value: `${candidate.consecutiveSellDays}d`,
      sub: `exact-spread ${candidate.exactSpreadConsecutiveDays}d`,
    },
  ];

  const headerBorderColor =
    candidate.action === 'SELL_CPS' ? 'var(--color-secondary)'
      : candidate.action === 'WATCH_CPS' ? 'var(--color-accent)'
        : candidate.action === 'WAIT' ? 'var(--color-warning)'
          : candidate.action === 'AVOID' ? 'var(--color-error)'
            : 'var(--color-txt-tertiary)';

  return (
    <div
      className="bg-surface rounded-lg border border-border overflow-hidden"
      style={{ borderTop: `3px solid ${headerBorderColor}` }}
    >
      {/* Header */}
      <div className="px-4 sm:px-6 py-4 border-b border-border-subtle flex flex-wrap items-start gap-3 justify-between">
        <div>
          <div className="flex items-baseline gap-2.5">
            <span className="font-secondary text-lg sm:text-[22px] font-medium text-txt">
              {candidate.ticker}
            </span>
            <span className="text-sm text-txt-tertiary">
              ${candidate.spot.toFixed(2)} spot
            </span>
          </div>
          <div className="flex gap-2 mt-2 flex-wrap items-center">
            <CreditPutSpreadActionBadge action={candidate.action} />
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-2xs border border-border-subtle bg-bg-alt text-txt-secondary">
              Base {Math.round(candidate.baseScore)}
            </span>
            <span
              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-2xs border"
              style={{
                color: candidate.regime === 'DANGER' ? 'var(--color-error)'
                  : candidate.regime === 'CAUTION' ? 'var(--color-warning)'
                    : 'var(--color-txt-secondary)',
                borderColor:
                  candidate.regime === 'DANGER' ? 'var(--color-error-30)'
                    : candidate.regime === 'CAUTION' ? 'var(--color-warning-30)'
                      : 'var(--color-border-subtle)',
                background:
                  candidate.regime === 'DANGER' ? 'var(--color-error-subtle)'
                    : candidate.regime === 'CAUTION' ? 'var(--color-warning-subtle)'
                      : 'transparent',
              }}
            >
              {candidate.regime}
            </span>
            {candidate.regimeOverlayStatus && (
              <span
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-2xs border border-border-subtle bg-surface-alt text-txt-secondary"
                title="Market-wide regime overlay (VIX/VIX3M/VVIX)"
              >
                Overlay: {candidate.regimeOverlayStatus}
              </span>
            )}
          </div>
        </div>
        <div className="text-right">
          <div className="font-mono text-base font-semibold text-txt">
            {candidate.expiration}
          </div>
          <div className="font-mono text-2xs text-txt-tertiary">{candidate.dte} DTE</div>
        </div>
      </div>

      {/* Base edge metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 border-b border-border-subtle">
        {baseEdge.map((m, i) => (
          <div
            key={m.label}
            className={[
              'px-3 sm:px-4 py-3 border-border-subtle',
              i % 2 === 0 ? 'border-r' : '',
              i % 3 !== 2 ? 'md:border-r' : '',
              i % 6 !== 5 ? 'lg:border-r' : '',
              i < baseEdge.length - 1 ? 'border-b' : '',
              'md:border-b-0',
            ].join(' ')}
          >
            <div className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase">
              {m.label}
            </div>
            <div className="mt-1 font-mono text-base font-semibold text-txt">{m.value}</div>
            {m.sub && (
              <div className="font-primary text-[10px] text-txt-tertiary mt-0.5 leading-tight">
                {m.sub}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Spread economics card */}
      <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-border-subtle">
        <div className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase mb-3">
          Spread Economics
        </div>
        <CreditPutSpreadEconomicsCard candidate={candidate} />
        <div className="mt-3 text-[10px] text-txt-tertiary italic leading-relaxed">
          Per-share values shown by default. Per-contract dollars in tooltips. Position size is a
          trader-controlled decision — record contracts in your trade journal.
        </div>
      </div>

      {/* Per-leg detail */}
      <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-border-subtle">
        <div className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase mb-3">
          Leg Detail
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <LegRow label={`Short Put (${candidate.shortPut.strike})`} leg={candidate.shortPut} />
          <LegRow label={`Long Put  (${candidate.longPut.strike})`} leg={candidate.longPut} />
        </div>
        {candidate.expectedMove != null && (
          <div className="mt-3 text-[10px] text-txt-tertiary">
            Expected-move (1σ) ±{dollars(candidate.expectedMove)} ·
            {' '}lower bound {dollars(candidate.expectedMoveLower)} ·
            {' '}width / ATR {num(candidate.widthToAtr, 2)} ·
            {' '}width / EM {num(candidate.widthToExpectedMove, 2)}
          </div>
        )}
      </div>

      {/* Notes */}
      {candidate.notes.length > 0 && (
        <div className="px-4 sm:px-6 py-3 border-b border-border-subtle">
          <div className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase mb-2">
            Notes
          </div>
          <ul className="text-xs text-txt-secondary space-y-0.5 list-disc pl-4">
            {candidate.notes.map((n, i) => <li key={i}>{n}</li>)}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {candidate.warnings.length > 0 && (
        <div className="px-4 sm:px-6 py-3 border-b border-border-subtle">
          <div className="font-primary text-[10px] font-semibold text-warning tracking-widest uppercase mb-2">
            Warnings
          </div>
          <ul className="text-xs text-txt-secondary space-y-0.5 list-disc pl-4">
            {candidate.warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}

      {/* Rejection reasons (rare for actionable candidates, but surface when present) */}
      {candidate.rejectionReasons.length > 0 && (
        <div className="px-4 sm:px-6 py-3">
          <div className="font-primary text-[10px] font-semibold text-error tracking-widest uppercase mb-2">
            Reasons signal is held back
          </div>
          <ul className="text-xs text-txt-secondary space-y-0.5 list-disc pl-4">
            {candidate.rejectionReasons.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
