'use client';

import React from 'react';
import type { CreditPutSpreadCandidate } from '@/lib/types';
import CreditPutSpreadActionBadge from './CreditPutSpreadActionBadge';

interface CreditPutSpreadTableProps {
  candidates: CreditPutSpreadCandidate[];
  selectedTicker: string | null;
  onSelect: (ticker: string | null) => void;
}

function formatSpread(c: CreditPutSpreadCandidate): string {
  const short = Number.isInteger(c.shortPut.strike)
    ? c.shortPut.strike.toString()
    : c.shortPut.strike.toFixed(1);
  const long = Number.isInteger(c.longPut.strike)
    ? c.longPut.strike.toString()
    : c.longPut.strike.toFixed(1);
  return `${short}/${long}P`;
}

function dollars(v: number, digits = 2): string {
  return `$${v.toFixed(digits)}`;
}

const HEADERS = [
  { key: 'rank',       label: '#',           align: 'text-right',  hideOnMobile: false },
  { key: 'ticker',     label: 'Ticker',      align: 'text-left',   hideOnMobile: false },
  { key: 'action',     label: 'Action',      align: 'text-left',   hideOnMobile: false },
  { key: 'baseScore',  label: 'Base',        align: 'text-right',  hideOnMobile: false },
  { key: 'consecutive',label: 'Days',        align: 'text-right',  hideOnMobile: true  },
  { key: 'regime',     label: 'Regime',      align: 'text-left',   hideOnTablet: true  },
  { key: 'rvStatus',   label: 'RV Status',   align: 'text-left',   hideOnTablet: true  },
  { key: 'spread',     label: 'Spread',      align: 'text-left',   hideOnMobile: false },
  { key: 'dte',        label: 'DTE',         align: 'text-right',  hideOnMobile: true  },
  { key: 'credit',     label: 'Credit',      align: 'text-right',  hideOnMobile: false },
  { key: 'width',      label: 'Width',       align: 'text-right',  hideOnMobile: true  },
  { key: 'cw',         label: 'C/W',         align: 'text-right',  hideOnMobile: false },
  { key: 'maxLoss',    label: 'Max Loss',    align: 'text-right',  hideOnTablet: true  },
  { key: 'breakeven',  label: 'Breakeven',   align: 'text-right',  hideOnTablet: true  },
  { key: 'warnings',   label: 'Notes',       align: 'text-left',   hideOnMobile: true  },
] as const;

export default function CreditPutSpreadTable({
  candidates, selectedTicker, onSelect,
}: CreditPutSpreadTableProps) {
  if (candidates.length === 0) {
    return null;
  }

  return (
    <div className="bg-surface rounded-lg border border-border overflow-hidden">
      <div className="px-4 sm:px-6 pt-4 sm:pt-5">
        <div className="flex justify-between items-baseline">
          <div>
            <h2 className="font-secondary text-xl font-medium text-txt">
              Credit Put Spread Candidates
            </h2>
            <p className="text-2xs sm:text-xs md:text-sm text-txt-tertiary mt-0.5">
              Ranked by Base Edge Score after binary construction / execution filters
            </p>
          </div>
          <span className="font-mono text-2xs sm:text-xs md:text-sm text-txt-tertiary">
            {candidates.filter(c => c.action === 'SELL_CPS').length} actionable
            {' · '}
            {candidates.filter(c => c.action === 'WATCH_CPS').length} watch
          </span>
        </div>
      </div>

      <div className="px-2 pt-3 pb-2 overflow-x-auto">
        <table className="w-full border-separate border-spacing-0 min-w-[760px]">
          <thead>
            <tr>
              {HEADERS.map(h => (
                <th
                  key={h.key}
                  className={[
                    'font-primary text-[10px] font-semibold text-txt-tertiary',
                    'tracking-wider uppercase px-3 py-2 whitespace-nowrap',
                    'border-b-2 border-b-primary',
                    h.align,
                    'hideOnMobile' in h && h.hideOnMobile ? 'hidden sm:table-cell' : '',
                    'hideOnTablet' in h && h.hideOnTablet ? 'hidden md:table-cell' : '',
                  ].filter(Boolean).join(' ')}
                >
                  {h.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr><td colSpan={HEADERS.length} className="h-2 p-0" /></tr>
            {candidates.map((c, idx) => {
              const isSelected = selectedTicker === c.ticker;
              const rowBg = isSelected
                ? 'var(--color-primary-subtle)'
                : 'transparent';

              return (
                <tr
                  key={`${c.ticker}-${c.shortPut.strike}-${c.longPut.strike}`}
                  onClick={() => onSelect(isSelected ? null : c.ticker)}
                  className="cursor-pointer transition-colors hover:bg-surface-alt"
                >
                  {/* Rank */}
                  <td
                    className="px-3 py-3 text-right transition-colors"
                    style={{
                      background: rowBg,
                      borderRadius: isSelected ? '8px 0 0 8px' : '0',
                    }}
                  >
                    <span className="font-mono text-sm text-txt-tertiary">{idx + 1}</span>
                  </td>

                  {/* Ticker */}
                  <td className="px-3 py-3 transition-colors" style={{ background: rowBg }}>
                    <div className="font-primary text-sm font-semibold text-txt">{c.ticker}</div>
                    <div className="font-mono text-[10px] text-txt-tertiary">
                      {dollars(c.spot)} spot
                    </div>
                  </td>

                  {/* Action */}
                  <td className="px-3 py-3 transition-colors" style={{ background: rowBg }}>
                    <CreditPutSpreadActionBadge action={c.action} size="sm" />
                  </td>

                  {/* Base Score */}
                  <td className="px-3 py-3 text-right transition-colors" style={{ background: rowBg }}>
                    <span className="font-mono text-sm font-semibold text-txt">{Math.round(c.baseScore)}</span>
                  </td>

                  {/* Consecutive Days */}
                  <td
                    className="px-3 py-3 text-right transition-colors hidden sm:table-cell"
                    style={{ background: rowBg }}
                    title={`Exact-spread streak: ${c.exactSpreadConsecutiveDays} day(s)`}
                  >
                    <span className="font-mono text-sm text-txt-secondary">
                      {c.consecutiveSellDays}d
                    </span>
                  </td>

                  {/* Regime */}
                  <td className="px-3 py-3 transition-colors hidden md:table-cell" style={{ background: rowBg }}>
                    <span
                      className="font-mono text-2xs"
                      style={{
                        color:
                          c.regime === 'DANGER' ? 'var(--color-error)'
                            : c.regime === 'CAUTION' ? 'var(--color-warning)'
                              : 'var(--color-txt-secondary)',
                      }}
                    >
                      {c.regime}
                    </span>
                  </td>

                  {/* RV Status */}
                  <td className="px-3 py-3 transition-colors hidden md:table-cell" style={{ background: rowBg }}>
                    <span className="font-mono text-2xs text-txt-secondary">
                      {c.rvAccelStatus ?? '—'}
                    </span>
                  </td>

                  {/* Spread */}
                  <td className="px-3 py-3 transition-colors" style={{ background: rowBg }}>
                    <span className="font-mono text-sm text-txt">{formatSpread(c)}</span>
                  </td>

                  {/* DTE */}
                  <td
                    className="px-3 py-3 text-right transition-colors hidden sm:table-cell"
                    style={{ background: rowBg }}
                  >
                    <span className="font-mono text-sm text-txt-secondary">{c.dte}d</span>
                  </td>

                  {/* Credit */}
                  <td className="px-3 py-3 text-right transition-colors" style={{ background: rowBg }}>
                    <span className="font-mono text-sm font-semibold text-secondary">
                      {dollars(c.netCredit)}
                    </span>
                  </td>

                  {/* Width */}
                  <td
                    className="px-3 py-3 text-right transition-colors hidden sm:table-cell"
                    style={{ background: rowBg }}
                  >
                    <span className="font-mono text-sm text-txt-secondary">{dollars(c.width, 0)}</span>
                  </td>

                  {/* C/W */}
                  <td className="px-3 py-3 text-right transition-colors" style={{ background: rowBg }}>
                    <span
                      className="font-mono text-sm font-semibold"
                      style={{
                        color: c.creditToWidth >= 0.25
                          ? 'var(--color-secondary)'
                          : 'var(--color-warning)',
                      }}
                    >
                      {(c.creditToWidth * 100).toFixed(1)}%
                    </span>
                  </td>

                  {/* Max Loss */}
                  <td
                    className="px-3 py-3 text-right transition-colors hidden md:table-cell"
                    style={{ background: rowBg }}
                  >
                    <span className="font-mono text-sm text-error">
                      {dollars(c.maxLoss)}
                    </span>
                  </td>

                  {/* Breakeven */}
                  <td
                    className="px-3 py-3 text-right transition-colors hidden md:table-cell"
                    style={{ background: rowBg }}
                  >
                    <span className="font-mono text-sm text-txt-secondary">
                      {dollars(c.breakeven)}
                    </span>
                  </td>

                  {/* Notes */}
                  <td
                    className="px-3 py-3 transition-colors hidden sm:table-cell"
                    style={{
                      background: rowBg,
                      borderRadius: isSelected ? '0 8px 8px 0' : '0',
                    }}
                  >
                    {c.warnings.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {c.warnings.slice(0, 2).map((w, i) => (
                          <span
                            key={i}
                            title={w}
                            className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[9px] bg-warning-subtle border border-warning-30 text-warning whitespace-nowrap max-w-[120px] truncate"
                          >
                            {w.split('—')[0].trim().slice(0, 18)}
                          </span>
                        ))}
                        {c.warnings.length > 2 && (
                          <span className="text-[9px] text-txt-tertiary">
                            +{c.warnings.length - 2}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-2xs text-txt-tertiary">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
