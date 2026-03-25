'use client';

import React, { useCallback, useRef, useEffect, useState } from 'react';
import DetailPanel from '@/components/DetailPanel';
import type { DashboardTicker, TickerDelta } from '@/lib/types';

interface LeaderboardProps {
  data: DashboardTicker[];
  selected: string | null;
  onSelect: (sym: string) => void;
  selectedData: DashboardTicker | null;
  deltaMap: Record<string, TickerDelta>;
}

/* ── Inline sub-components ────────────────────────── */

function VRPBar({ value, max = 20 }: { value: number | null; max?: number }) {
  if (value == null) {
    return <span className="font-mono text-sm text-[#525252]">N/A</span>;
  }
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className="flex items-center gap-2 min-w-[100px]">
      <div className="flex-1 bg-[#E5E5E5] h-[6px] overflow-hidden">
        <div
          className="bg-black h-[6px] transition-all duration-normal"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="font-mono text-sm font-semibold text-black">
        {value.toFixed(1)}
      </span>
    </div>
  );
}

function ScorePill({ score }: { score: number }) {
  if (score >= 65) {
    return (
      <div className="inline-flex items-center justify-center w-10 h-10 bg-black text-white font-display text-xl font-bold">
        {score}
      </div>
    );
  } else if (score >= 45) {
    return (
      <div className="inline-flex items-center justify-center w-10 h-10 border-2 border-black font-display text-xl font-bold">
        {score}
      </div>
    );
  } else if (score > 0) {
    return (
      <span className="font-mono text-lg text-[#525252]">
        {score}
      </span>
    );
  } else {
    return (
      <span className="font-mono text-lg text-[#525252] line-through">
        {score}
      </span>
    );
  }
}

function ActionChip({ action, reason }: { action: string; reason: string | null }) {
  const baseClasses = 'font-mono text-xs font-medium uppercase tracking-widest';

  switch (action) {
    case 'SELL':
      return (
        <span className={`inline-flex items-center bg-black text-white ${baseClasses} px-3 py-1 whitespace-nowrap`}>
          SELL PREMIUM
        </span>
      );
    case 'CONDITIONAL':
      return (
        <span className={`inline-flex items-center border border-black text-black ${baseClasses} px-3 py-1 whitespace-nowrap`}>
          CONDITIONAL
        </span>
      );
    case 'NO EDGE':
      return (
        <span className={`text-[#525252] ${baseClasses} whitespace-nowrap`}>
          NO EDGE
        </span>
      );
    case 'SKIP':
      return (
        <span className={`text-[#525252] ${baseClasses} line-through whitespace-nowrap`}>
          {reason || 'SKIP'}
        </span>
      );
    case 'AVOID':
      return (
        <span className={`inline-flex items-center bg-black text-white ${baseClasses} px-3 py-1 border-l-4 border-white whitespace-nowrap`}>
          AVOID
        </span>
      );
    case 'NO DATA':
      return (
        <span className={`text-[#525252] ${baseClasses} whitespace-nowrap`}>
          NO DATA
        </span>
      );
    default:
      return (
        <span className={`text-[#525252] ${baseClasses} whitespace-nowrap`}>
          NO EDGE
        </span>
      );
  }
}

function DeltaChip({ value, precision = 1 }: { value: number | null | undefined; precision?: number }) {
  if (value == null) return null;
  const sign = value > 0 ? '+' : '';
  return (
    <span className="font-mono text-[10px] text-[#525252] ml-1 hidden lg:inline">
      {sign}{value.toFixed(precision)}
    </span>
  );
}

function SizingChip({ sizing }: { sizing?: string }) {
  if (!sizing || sizing === 'Full') return null;
  const isHalf = sizing === 'Half';

  if (isHalf) {
    return (
      <span className="font-mono text-xs font-medium uppercase text-[#525252]">
        &darr; Half
      </span>
    );
  }

  return (
    <span className="font-mono text-xs font-medium uppercase text-[#525252] italic">
      &darr; Quarter
    </span>
  );
}

/* ── Mobile card (shown < sm) ────────────────────── */

function MobileTickerCard({
  row, isSelected, onSelect, selectedData, delta,
}: {
  row: DashboardTicker; isSelected: boolean; onSelect: (sym: string) => void; selectedData: DashboardTicker | null; delta?: TickerDelta | null;
}) {
  const isSkipped = row.action === 'SKIP';

  return (
    <div>
      <div
        onClick={() => onSelect(row.sym)}
        className={`px-3.5 py-3 cursor-pointer transition-colors ${
          isSelected ? 'bg-black text-white border-l-4 border-white' : 'bg-white border border-[#E5E5E5] hover:bg-[#F5F5F5]'
        }`}
        style={{ opacity: isSkipped ? 0.5 : 1 }}
      >
        {/* Line 1: Ticker + name + score */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-baseline gap-2 min-w-0">
            <span className="font-primary text-sm font-semibold">{row.sym}</span>
            <span className="font-primary text-2xs truncate flex items-center gap-1">
              {row.name || row.sector}
              {row.regime === 'DANGER' && <span className="font-mono text-[9px] uppercase font-bold shrink-0">DANGER</span>}
              {row.regime === 'CAUTION' && <span className="font-mono text-[9px] uppercase text-[#525252] shrink-0">CAUTION</span>}
            </span>
          </div>
          <ScorePill score={row.score} />
        </div>
        {/* Line 2: Key metrics */}
        <div className="font-mono text-sm mt-1.5">
          VRP {row.vrp != null ? row.vrp.toFixed(1) : 'N/A'} · Term {row.termSlope.toFixed(2)} · RV {row.rvAccel.toFixed(2)}
        </div>
        {/* Line 3: Action chips */}
        <div className="flex items-center justify-end gap-1.5 mt-2">
          <SizingChip sizing={row.sizing} />
          <ActionChip action={row.action} reason={row.actionReason} />
        </div>
      </div>
      {/* Expandable detail */}
      <ExpandableDetail ticker={isSelected ? selectedData : null} isOpen={isSelected} delta={isSelected ? delta : null} />
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

function ExpandableDetail({ ticker, isOpen, delta }: { ticker: DashboardTicker | null; isOpen: boolean; delta?: TickerDelta | null }) {
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
        {ticker && <DetailPanel ticker={ticker} delta={delta} />}
      </div>
    </div>
  );
}

export default function Leaderboard({ data, selected, onSelect, selectedData, deltaMap }: LeaderboardProps) {
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
      return `| ${row.sym} | ${row.score} | ${row.iv != null ? row.iv.toFixed(1) : 'N/A'} | ${row.ivPct.toFixed(0)} | ${row.rv30.toFixed(1)} | ${row.vrp != null ? row.vrp.toFixed(1) : 'N/A'} | ${row.termSlope.toFixed(2)} | ${row.rvAccel.toFixed(2)} | ${row.skew25d.toFixed(1)} | ${tv} | ${earnings} | ${regime} |`;
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
      const bg = enter ? '#F5F5F5' : 'transparent';
      cells.forEach((td) => {
        td.style.background = bg;
        td.style.borderRadius = '0';
      });
    }
  }, []);

  return (
    <div className="bg-white border border-black overflow-hidden">
      {/* Header */}
      <div className="px-4 sm:px-6 pt-4 sm:pt-5">
        <div className="flex justify-between items-baseline">
          <div>
            <h2 className="font-display text-xl font-medium text-black">
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
                className="p-1 hover:bg-[#F5F5F5] transition-colors"
                aria-label="Copy metrics to clipboard"
              >
                {copied ? (
                  <svg className="w-4 h-4 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-[#525252] hover:text-black transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9.75a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
                  </svg>
                )}
              </button>
              {/* Tooltip */}
              <span
                className="pointer-events-none absolute right-0 top-full mt-2 opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 origin-top-right z-50"
                style={{ background: 'var(--color-tooltip-bg)', color: 'var(--color-tooltip-text)' }}
              >
                <span className="flex items-center px-3.5 py-2.5 whitespace-nowrap">
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
            delta={deltaMap[row.sym] ?? null}
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
                    font-mono text-xs font-semibold text-[#525252] tracking-widest uppercase
                    px-4 py-2 whitespace-nowrap border-b-2 border-black
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
              const delta = deltaMap[row.sym];

              return (
                <React.Fragment key={row.sym}>
                  <tr
                    onClick={() => onSelect(row.sym)}
                    onMouseEnter={e => handleRowHover(e, isSelected, true)}
                    onMouseLeave={e => handleRowHover(e, isSelected, false)}
                    className={`cursor-pointer ${isSelected ? '' : 'border-b border-[#E5E5E5]'}`}
                    style={{ opacity: isSkipped ? 0.5 : isAvoided ? 0.65 : 1 }}
                  >
                    {/* Ticker */}
                    <td
                      className={`px-4 py-3.5 transition-colors ${isSelected ? 'bg-black text-white' : ''}`}
                      style={{
                        borderRadius: '0',
                      }}
                    >
                      <div className={`font-primary text-sm font-semibold ${isSelected ? 'text-white' : 'text-txt'}`}>{row.sym}</div>
                      <div className={`font-primary text-2xs flex items-center gap-1.5 ${isSelected ? 'text-white/70' : 'text-txt-tertiary'}`}>
                        {row.sector}
                        {row.regime === 'DANGER' && (
                          <span className="font-mono text-[9px] font-bold uppercase" title="Danger regime">DANGER</span>
                        )}
                        {row.regime === 'CAUTION' && (
                          <span className={`font-mono text-[9px] uppercase ${isSelected ? 'text-white/70' : 'text-[#525252]'}`} title="Caution regime">CAUTION</span>
                        )}
                        {delta?.regime_changed && delta?.previous_regime && (
                          <span className={`text-[9px] hidden lg:inline ${isSelected ? 'text-white/50' : 'text-txt-tertiary'}`}>
                            was {delta.previous_regime}
                          </span>
                        )}
                      </div>
                    </td>

                    {/* VRP bar */}
                    <td
                      className={`px-4 py-3.5 hidden sm:table-cell transition-colors ${isSelected ? 'bg-black' : ''}`}
                    >
                      {isSelected ? (
                        <div className="flex items-center gap-2 min-w-[100px]">
                          <div className="flex-1 bg-white/20 h-[6px] overflow-hidden">
                            <div className="bg-white h-[6px] transition-all duration-normal" style={{ width: `${Math.min(100, Math.max(0, ((row.vrp ?? 0) / 20) * 100))}%` }} />
                          </div>
                          <span className="font-mono text-sm font-semibold text-white">{row.vrp != null ? row.vrp.toFixed(1) : 'N/A'}</span>
                        </div>
                      ) : (
                        <VRPBar value={row.vrp} />
                      )}
                      <DeltaChip value={delta?.vrp} />
                    </td>

                    {/* Term Slope */}
                    <td
                      className={`px-4 py-3.5 text-right transition-colors ${isSelected ? 'bg-black' : ''}`}
                    >
                      <span className={`font-mono text-sm ${isSelected ? 'text-white' : 'text-black'}`}>
                        {row.termSlope.toFixed(2)}
                      </span>
                      <DeltaChip value={delta?.term_slope} precision={2} />
                    </td>

                    {/* RV Accel + sizing */}
                    <td
                      className={`px-4 py-3.5 text-right transition-colors ${isSelected ? 'bg-black' : ''}`}
                    >
                      <span className={`font-mono text-sm ${isSelected ? 'text-white' : 'text-black'}`}>
                        {row.rvAccel.toFixed(2)}
                      </span>
                    </td>

                    {/* Earnings */}
                    <td
                      className={`px-4 py-3.5 text-right hidden md:table-cell transition-colors ${isSelected ? 'bg-black' : ''}`}
                    >
                      {row.earningsDTE ? (
                        <span className={`font-mono text-sm ${isSelected ? 'text-white' : 'text-black'}`}>
                          {row.earningsDTE}d {row.earningsWarning && '\u26A0'}
                        </span>
                      ) : (
                        <span className={`font-mono text-sm ${isSelected ? 'text-white/50' : 'text-[#525252]'}`}>
                          {row.isEtf ? 'ETF' : 'TBD'}
                        </span>
                      )}
                    </td>

                    {/* Score pill */}
                    <td
                      className={`px-4 py-3.5 text-center transition-colors ${isSelected ? 'bg-black' : ''}`}
                    >
                      <div className="relative inline-block">
                        {isSelected ? (
                          <span className="font-display text-xl font-bold text-white">{row.score}</span>
                        ) : (
                          <ScorePill score={row.score} />
                        )}
                        <DeltaChip value={delta?.score} precision={0} />
                        {row.preGateScore != null && (
                          <span className={`absolute left-full top-1/2 -translate-y-1/2 ml-1.5 font-mono text-sm whitespace-nowrap ${isSelected ? 'text-white/50' : 'text-txt-tertiary'}`}>({row.preGateScore})</span>
                        )}
                      </div>
                    </td>

                    {/* Signal */}
                    <td
                      className={`px-4 py-3.5 text-right transition-colors ${isSelected ? 'bg-black' : ''}`}
                      style={{
                        borderRadius: '0',
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
                        delta={isSelected ? (deltaMap[row.sym] ?? null) : null}
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
