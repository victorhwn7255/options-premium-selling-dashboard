'use client';

import React, { useCallback, useRef, useEffect, useState } from 'react';
import DetailPanel from '@/components/DetailPanel';
import type { DashboardTicker } from '@/lib/types';

interface LeaderboardProps {
  data: DashboardTicker[];
  selected: string | null;
  onSelect: (sym: string) => void;
  selectedData: DashboardTicker | null;
}

/* ── Inline sub-components ────────────────────────── */

function VRPBar({ value, max = 20 }: { value: number; max?: number }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const colorClass = value >= 10 ? 'text-secondary' : value >= 5 ? 'text-primary' : 'text-txt-tertiary';
  const barColor = value >= 10 ? 'bg-secondary' : value >= 5 ? 'bg-primary' : 'bg-txt-tertiary';

  return (
    <div className="flex items-center gap-2 min-w-[100px]">
      <div className="flex-1 h-1 bg-border-subtle rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} rounded-full transition-all duration-normal`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`font-mono text-sm font-semibold ${colorClass}`}>
        {value.toFixed(1)}
      </span>
    </div>
  );
}

function ScorePill({ score }: { score: number }) {
  let bgClass: string, colorStyle: string;
  if (score >= 65) {
    bgClass = 'bg-success-subtle';
    colorStyle = 'var(--color-badge-sell)';
  } else if (score >= 45) {
    bgClass = 'bg-warning-subtle';
    colorStyle = 'var(--color-badge-reduce)';
  } else if (score > 0) {
    bgClass = 'bg-surface-alt';
    colorStyle = 'var(--color-txt-tertiary)';
  } else {
    bgClass = 'bg-error-subtle';
    colorStyle = 'var(--color-badge-avoid)';
  }

  return (
    <div
      className={`inline-flex items-center justify-center w-9 h-9 rounded-full font-mono text-sm font-bold ${bgClass}`}
      style={{ color: colorStyle }}
    >
      {score}
    </div>
  );
}

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
    AVOID: {
      bgClass: 'bg-error-subtle', colorStyle: 'var(--color-badge-avoid)',
      borderClass: 'border-error-20', label: 'AVOID',
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

/* ── Mobile card (shown < sm) ────────────────────── */

function MobileTickerCard({
  row, isSelected, onSelect, selectedData,
}: {
  row: DashboardTicker; isSelected: boolean; onSelect: (sym: string) => void; selectedData: DashboardTicker | null;
}) {
  const isSkipped = row.action === 'SKIP';

  return (
    <div>
      <div
        onClick={() => onSelect(row.sym)}
        className={`rounded-lg px-3.5 py-3 cursor-pointer transition-colors ${
          isSelected ? 'bg-primary-subtle border-l-[3px] border-l-primary' : 'bg-surface hover:bg-surface-alt'
        }`}
        style={{ opacity: isSkipped ? 0.5 : 1 }}
      >
        {/* Line 1: Ticker + name + score */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-baseline gap-2 min-w-0">
            <span className="font-primary text-sm font-semibold text-txt">{row.sym}</span>
            <span className="font-primary text-2xs text-txt-tertiary truncate flex items-center gap-1">
              {row.name || row.sector}
              {row.regime === 'DANGER' && <span className="inline-block w-1.5 h-1.5 rounded-full bg-error shrink-0" />}
              {row.regime === 'CAUTION' && <span className="inline-block w-1.5 h-1.5 rounded-full bg-warning shrink-0" />}
            </span>
          </div>
          <ScorePill score={row.score} />
        </div>
        {/* Line 2: Key metrics */}
        <div className="font-mono text-sm text-txt-secondary mt-1.5">
          VRP {row.vrp.toFixed(1)} · Term {row.termSlope.toFixed(2)} · RV {row.rvAccel.toFixed(2)}
        </div>
        {/* Line 3: Action chips */}
        <div className="flex items-center justify-end gap-1.5 mt-2">
          <SizingChip sizing={row.sizing} />
          <ActionChip action={row.action} reason={row.actionReason} />
        </div>
      </div>
      {/* Expandable detail */}
      <ExpandableDetail ticker={isSelected ? selectedData : null} isOpen={isSelected} />
    </div>
  );
}

/* ── Main component ───────────────────────────────── */

const HEADERS = [
  { key: 'ticker', label: 'Ticker', align: 'text-left' },
  { key: 'vrp', label: 'VRP', align: 'text-left', hideOnMobile: true },
  { key: 'termSlope', label: 'Term', align: 'text-right' },
  { key: 'rvAccel', label: 'RV Accel', align: 'text-right' },
  { key: 'earnings', label: 'Earnings', align: 'text-right', hideOnTablet: true },
  { key: 'score', label: 'Score', align: 'text-center' },
  { key: 'action', label: 'Signal', align: 'text-right' },
] as const;

/* ── Expandable detail row ────────────────────────── */

function ExpandableDetail({ ticker, isOpen }: { ticker: DashboardTicker | null; isOpen: boolean }) {
  const contentRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(0);

  useEffect(() => {
    if (isOpen && contentRef.current) {
      setHeight(contentRef.current.scrollHeight);
    } else {
      setHeight(0);
    }
  }, [isOpen, ticker]);

  // Re-measure when charts load (they render async)
  useEffect(() => {
    if (!isOpen || !contentRef.current) return;
    const observer = new ResizeObserver(() => {
      if (contentRef.current) setHeight(contentRef.current.scrollHeight);
    });
    observer.observe(contentRef.current);
    return () => observer.disconnect();
  }, [isOpen, ticker]);

  return (
    <div
      style={{
        maxHeight: isOpen ? `${height}px` : '0px',
        transition: 'max-height 0.3s ease-in-out',
        overflow: 'hidden',
      }}
    >
      <div ref={contentRef} className="pt-2 pb-6">
        {ticker && <DetailPanel ticker={ticker} />}
      </div>
    </div>
  );
}

export default function Leaderboard({ data, selected, onSelect, selectedData }: LeaderboardProps) {
  const sellCount = data.filter(d => d.action === 'SELL').length;
  const conditionalCount = data.filter(d => d.action === 'CONDITIONAL').length;
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    const header = '| Ticker | Score | IV | IV Pct | RV30 | VRP | Term Slope | RV Accel | 25Δ Skew | θ/V | Earnings | Regime |';
    const sep    = '|--------|-------|----|--------|------|-----|------------|----------|----------|-----|----------|--------|';
    const rows = data.map(row => {
      const earnings = row.earningsDTE ? `${row.earningsDTE}d` : row.isEtf ? 'ETF' : 'TBD';
      const regime = row.action === 'SKIP' ? (row.actionReason || 'SKIP') : `${row.action} (${row.regime})`;
      const tv = row.thetaVega != null ? row.thetaVega.toFixed(2) : '—';
      return `| ${row.sym} | ${row.score} | ${row.iv.toFixed(1)} | ${row.ivPct.toFixed(0)} | ${row.rv30.toFixed(1)} | ${row.vrp.toFixed(1)} | ${row.termSlope.toFixed(2)} | ${row.rvAccel.toFixed(2)} | ${row.skew25d.toFixed(1)} | ${tv} | ${earnings} | ${regime} |`;
    });
    const md = [header, sep, ...rows].join('\n');
    navigator.clipboard.writeText(md).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [data]);

  const handleRowHover = useCallback((e: React.MouseEvent<HTMLTableRowElement>, isSelected: boolean, enter: boolean) => {
    if (!isSelected) {
      const cells = e.currentTarget.querySelectorAll<HTMLTableCellElement>('td');
      const bg = enter ? 'var(--color-row-hover)' : 'transparent';
      cells.forEach((td, i) => {
        td.style.background = bg;
        if (i === 0) td.style.borderRadius = enter ? '8px 0 0 8px' : '0';
        if (i === cells.length - 1) td.style.borderRadius = enter ? '0 8px 8px 0' : '0';
      });
    }
  }, []);

  return (
    <div className="bg-surface rounded-lg border border-border overflow-hidden">
      {/* Header */}
      <div className="px-4 sm:px-6 pt-4 sm:pt-5">
        <div className="flex justify-between items-baseline">
          <div>
            <h2 className="font-secondary text-xl font-medium text-txt">
              Opportunity Leaderboard
            </h2>
            <p className="text-2xs sm:text-xs md:text-sm text-txt-tertiary mt-0.5">
              Ranked by composite score — select a row for trade construction
            </p>
          </div>
          <span className="flex items-center gap-2">
            <span className="font-mono text-2xs sm:text-xs md:text-sm text-txt-tertiary">
              {sellCount} actionable &middot; {conditionalCount} conditional
            </span>
            <span className="relative group">
              <button
                onClick={handleCopy}
                className="p-1 rounded hover:bg-surface-alt transition-colors"
                aria-label="Copy metrics to clipboard"
              >
                {copied ? (
                  <svg className="w-4 h-4 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-txt-tertiary hover:text-txt transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9.75a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
                  </svg>
                )}
              </button>
              {/* Tooltip */}
              <span
                className="pointer-events-none absolute right-0 top-full mt-2 opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 origin-top-right z-50"
                style={{ background: 'var(--color-tooltip-bg)', color: 'var(--color-tooltip-text)' }}
              >
                <span className="flex items-center rounded-lg px-3.5 py-2.5 shadow-lg whitespace-nowrap" style={{ boxShadow: '0 8px 24px rgba(0,0,0,0.18)' }}>
                  <span className="text-2xs font-medium" style={{ color: 'var(--color-tooltip-text)' }}>
                    {copied ? 'Copied!' : 'Copy metrics to clipboard'}
                  </span>
                </span>
              </span>
            </span>
          </span>
        </div>
      </div>

      {/* Mobile card list (< sm) */}
      <div className="sm:hidden px-3 pt-3 pb-2 space-y-2">
        {data.map(row => (
          <MobileTickerCard
            key={row.sym}
            row={row}
            isSelected={selected === row.sym}
            onSelect={onSelect}
            selectedData={selectedData}
          />
        ))}
      </div>

      {/* Desktop table (>= sm) */}
      <div className="hidden sm:block px-2 pt-3 pb-2 overflow-x-auto">
        <table className="w-full border-separate border-spacing-0">
          <thead>
            <tr>
              {HEADERS.map(h => (
                <th
                  key={h.key}
                  className={`
                    font-primary text-[10px] font-semibold text-txt-tertiary tracking-wider uppercase
                    px-4 py-2 whitespace-nowrap border-b-2 border-b-primary
                    ${h.align}
                    ${'hideOnMobile' in h && h.hideOnMobile ? 'hidden sm:table-cell' : ''}
                    ${'hideOnTablet' in h && h.hideOnTablet ? 'hidden md:table-cell' : ''}
                  `}
                >
                  {h.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Spacer below header border */}
            <tr><td colSpan={7} className="h-2 p-0" /></tr>
            {data.map(row => {
              const isSelected = selected === row.sym;
              const isSkipped = row.action === 'SKIP';
              const isAvoided = row.action === 'AVOID';

              return (
                <React.Fragment key={row.sym}>
                  <tr
                    onClick={() => onSelect(row.sym)}
                    onMouseEnter={e => handleRowHover(e, isSelected, true)}
                    onMouseLeave={e => handleRowHover(e, isSelected, false)}
                    className="cursor-pointer"
                    style={{ opacity: isSkipped ? 0.5 : isAvoided ? 0.65 : 1 }}
                  >
                    {/* Ticker */}
                    <td
                      className="px-4 py-3.5 transition-colors"
                      style={{
                        background: isSelected ? 'var(--color-primary-subtle)' : 'transparent',
                        borderRadius: isSelected ? '8px 0 0 8px' : '0',
                      }}
                    >
                      <div className="font-primary text-sm font-semibold text-txt">{row.sym}</div>
                      <div className="font-primary text-2xs text-txt-tertiary flex items-center gap-1.5">
                        {row.sector}
                        {row.regime === 'DANGER' && (
                          <span className="inline-block w-1.5 h-1.5 rounded-full bg-error shrink-0" title="Danger regime" />
                        )}
                        {row.regime === 'CAUTION' && (
                          <span className="inline-block w-1.5 h-1.5 rounded-full bg-warning shrink-0" title="Caution regime" />
                        )}
                      </div>
                    </td>

                    {/* VRP bar */}
                    <td
                      className="px-4 py-3.5 hidden sm:table-cell transition-colors"
                      style={{ background: isSelected ? 'var(--color-primary-subtle)' : 'transparent' }}
                    >
                      <VRPBar value={row.vrp} />
                    </td>

                    {/* Term Slope */}
                    <td
                      className="px-4 py-3.5 text-right transition-colors"
                      style={{ background: isSelected ? 'var(--color-primary-subtle)' : 'transparent' }}
                    >
                      <span className={`font-mono text-sm ${row.termSlope > 1 ? 'text-error' : 'text-txt-secondary'}`}>
                        {row.termSlope.toFixed(2)}
                      </span>
                    </td>

                    {/* RV Accel + sizing */}
                    <td
                      className="px-4 py-3.5 text-right transition-colors"
                      style={{ background: isSelected ? 'var(--color-primary-subtle)' : 'transparent' }}
                    >
                      <span className={`font-mono text-sm ${row.rvAccel > 1.10 ? 'text-error' : 'text-txt-secondary'}`}>
                        {row.rvAccel.toFixed(2)}
                      </span>
                    </td>

                    {/* Earnings */}
                    <td
                      className="px-4 py-3.5 text-right hidden md:table-cell transition-colors"
                      style={{ background: isSelected ? 'var(--color-primary-subtle)' : 'transparent' }}
                    >
                      {row.earningsDTE ? (
                        <span className={`font-mono text-sm ${row.earningsWarning ? 'text-error' : 'text-txt'}`}>
                          {row.earningsDTE}d {row.earningsWarning && '\u26A0'}
                        </span>
                      ) : (
                        <span className="font-mono text-sm text-txt-tertiary">
                          {row.isEtf ? 'ETF' : 'TBD'}
                        </span>
                      )}
                    </td>

                    {/* Score pill */}
                    <td
                      className="px-4 py-3.5 text-center transition-colors"
                      style={{ background: isSelected ? 'var(--color-primary-subtle)' : 'transparent' }}
                    >
                      <div className="relative inline-block">
                        <ScorePill score={row.score} />
                        {row.preGateScore != null && (
                          <span className="absolute left-full top-1/2 -translate-y-1/2 ml-1.5 font-mono text-sm text-txt-tertiary whitespace-nowrap">({row.preGateScore})</span>
                        )}
                      </div>
                    </td>

                    {/* Signal */}
                    <td
                      className="px-4 py-3.5 text-right transition-colors"
                      style={{
                        background: isSelected ? 'var(--color-primary-subtle)' : 'transparent',
                        borderRadius: isSelected ? '0 8px 8px 0' : '0',
                      }}
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        <SizingChip sizing={row.sizing} />
                        <ActionChip action={row.action} reason={row.actionReason} />
                      </div>
                    </td>
                  </tr>

                  {/* Expandable detail row */}
                  <tr>
                    <td colSpan={7} className="p-0 border-0">
                      <ExpandableDetail
                        ticker={isSelected ? selectedData : null}
                        isOpen={isSelected}
                      />
                    </td>
                  </tr>
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
