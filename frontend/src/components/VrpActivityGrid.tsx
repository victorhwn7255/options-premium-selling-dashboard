'use client';

import { useCallback, useMemo, useRef, useState } from 'react';
import type { VrpHistoryPoint } from '@/lib/types';

interface VrpActivityGridProps {
  year: number;
  points: VrpHistoryPoint[];
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const DAY_ROW_LABELS: Array<string | null> = [null, 'Mon', null, 'Wed', null, 'Fri', null];

function bucket(vrp: number): 1 | 2 | 3 | 4 {
  if (vrp <= 2) return 1;
  if (vrp <= 4) return 2;
  if (vrp <= 7) return 3;
  return 4;
}

interface Cell {
  iso: string;
  inYear: boolean;
}

type TipStatus = 'data' | 'no-scan' | 'upcoming';

interface Tooltip {
  x: number;
  y: number;
  dateLabel: string;
  status: TipStatus;
  vrp?: number;
}

function buildWeeks(year: number): { weeks: Cell[][]; weekStart: Date } {
  const yearStart = new Date(Date.UTC(year, 0, 1));
  const yearEnd = new Date(Date.UTC(year, 11, 31));
  const weekStart = new Date(yearStart);
  weekStart.setUTCDate(weekStart.getUTCDate() - yearStart.getUTCDay());
  const weekEnd = new Date(yearEnd);
  weekEnd.setUTCDate(weekEnd.getUTCDate() + (6 - yearEnd.getUTCDay()));

  const weeks: Cell[][] = [];
  const cursor = new Date(weekStart);
  while (cursor <= weekEnd) {
    const week: Cell[] = [];
    for (let i = 0; i < 7; i++) {
      week.push({
        iso: cursor.toISOString().slice(0, 10),
        inYear: cursor.getUTCFullYear() === year,
      });
      cursor.setUTCDate(cursor.getUTCDate() + 1);
    }
    weeks.push(week);
  }
  return { weeks, weekStart };
}

function formatDateLong(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  const month = dt.toLocaleString('en-US', { month: 'short', timeZone: 'UTC' });
  const weekday = dt.toLocaleString('en-US', { weekday: 'short', timeZone: 'UTC' });
  return `${weekday} · ${month} ${d}, ${y}`;
}

export default function VrpActivityGrid({ year, points }: VrpActivityGridProps) {
  const { weeks, weekStart } = useMemo(() => buildWeeks(year), [year]);
  const numWeeks = weeks.length;

  const vrpMap = useMemo(() => {
    const m = new Map<string, number>();
    for (const p of points) m.set(p.date, p.avg_vrp);
    return m;
  }, [points]);

  const monthLabels = useMemo(() => {
    const startMs = weekStart.getTime();
    return MONTHS.map((label, monthIdx) => {
      const firstOfMonth = Date.UTC(year, monthIdx, 1);
      const daysSinceStart = Math.floor((firstOfMonth - startMs) / 86_400_000);
      const weekIdx = Math.floor(daysSinceStart / 7);
      return { label, weekIdx };
    }).filter(m => m.weekIdx >= 0 && m.weekIdx < numWeeks);
  }, [year, numWeeks, weekStart]);

  const todayIso = new Date().toISOString().slice(0, 10);
  const validPoints = points.filter(p => p.date <= todayIso);
  const totalScans = validPoints.length;
  const yearAvg = totalScans > 0 ? validPoints.reduce((s, p) => s + p.avg_vrp, 0) / totalScans : 0;

  const cellsAspectRatio = `${numWeeks * 1.05} / 7`;

  const wrapperRef = useRef<HTMLDivElement>(null);
  const [tip, setTip] = useState<Tooltip | null>(null);

  const showTip = useCallback(
    (e: React.MouseEvent<HTMLDivElement>, cell: Cell, vrp: number | undefined) => {
      if (!cell.inYear) return;
      const wrapperRect = wrapperRef.current?.getBoundingClientRect();
      if (!wrapperRect) return;
      const cellRect = e.currentTarget.getBoundingClientRect();
      let status: TipStatus = 'no-scan';
      if (vrp !== undefined) status = 'data';
      else if (cell.iso > todayIso) status = 'upcoming';
      setTip({
        x: cellRect.left - wrapperRect.left + cellRect.width / 2,
        y: cellRect.top - wrapperRect.top,
        dateLabel: formatDateLong(cell.iso),
        status,
        vrp,
      });
    },
    [todayIso]
  );

  const hideTip = useCallback(() => setTip(null), []);

  return (
    <div ref={wrapperRef} className="w-full relative">
      {/* Header: title + legend */}
      <div className="flex items-center justify-between mb-5 flex-wrap gap-2">
        <div className="flex items-baseline gap-2">
          <span className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase">
            Daily Avg VRP
          </span>
          <span className="font-mono text-[11px] text-txt-secondary">{year}</span>
          {totalScans > 0 && (
            <span className="text-[11px] text-txt-tertiary">
              · {totalScans} scans · YTD mean {yearAvg.toFixed(1)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-txt-tertiary">
          <span>Less</span>
          {[0, 1, 2, 3, 4].map(level => (
            <div
              key={level}
              className="rounded-[2px]"
              style={{ width: 11, height: 11, backgroundColor: `var(--grid-l${level})` }}
            />
          ))}
          <span>More</span>
        </div>
      </div>

      {/* Grid: [day labels] [month labels above cells] */}
      <div
        className="grid items-stretch"
        style={{ gridTemplateColumns: '28px 1fr', gridTemplateRows: 'auto 1fr', columnGap: 6 }}
      >
        <div />

        {/* Month labels — pinned to row 1, single-column placement, overflow rightward */}
        <div
          className="grid text-[10px] text-txt-tertiary mb-1"
          style={{ gridTemplateColumns: `repeat(${numWeeks}, 1fr)`, height: 14 }}
        >
          {monthLabels.map(({ label, weekIdx }) => (
            <span
              key={label}
              className="whitespace-nowrap leading-none"
              style={{ gridColumnStart: weekIdx + 1, gridRowStart: 1 }}
            >
              {label}
            </span>
          ))}
        </div>

        {/* Day-of-week labels */}
        <div
          className="grid text-[10px] text-txt-tertiary"
          style={{ gridTemplateRows: 'repeat(7, 1fr)' }}
        >
          {DAY_ROW_LABELS.map((label, i) => (
            <div key={i} className="flex items-center leading-none">
              {label ?? ''}
            </div>
          ))}
        </div>

        {/* Cells grid */}
        <div
          className="grid"
          style={{
            gridTemplateColumns: `repeat(${numWeeks}, 1fr)`,
            gridTemplateRows: 'repeat(7, 1fr)',
            gridAutoFlow: 'column',
            gap: 3,
            aspectRatio: cellsAspectRatio,
          }}
          onMouseLeave={hideTip}
        >
          {weeks.flatMap((week, weekIdx) =>
            week.map((cell, dayIdx) => {
              const vrp = cell.inYear ? vrpMap.get(cell.iso) : undefined;
              let level: 0 | 1 | 2 | 3 | 4 = 0;
              if (cell.inYear && vrp !== undefined) level = bucket(vrp);
              const interactive = cell.inYear;

              return (
                <div
                  key={`${weekIdx}-${dayIdx}`}
                  className={
                    'rounded-[2px] transition-[filter,transform] duration-75' +
                    (interactive ? ' hover:brightness-125 cursor-default' : '')
                  }
                  style={{
                    backgroundColor: `var(--grid-l${level})`,
                    opacity: cell.inYear ? 1 : 0.35,
                  }}
                  onMouseEnter={interactive ? e => showTip(e, cell, vrp) : undefined}
                />
              );
            })
          )}
        </div>
      </div>

      {/* Caption — left-aligned to the heatmap cells (offset by day-labels column 28px + 6px gap) */}
      <p
        className="mt-5 text-[10px] text-txt-tertiary leading-relaxed"
        style={{ paddingLeft: 34 }}
      >
        <span className="text-txt-secondary font-medium">Full-universe measure</span>
        {' — '}
        mean VRP across all 33 tickers per scan day, including earnings-gated and NO DATA names.
        Distinct from the banner&apos;s <span className="font-mono">Avg VRP</span> tile, which uses
        only the eligible set (excludes earnings-gated and NO DATA), so the two values can disagree
        — when they do, earnings-gated mega-caps are typically carrying inflated pre-event premium.
        Brighter = wider edge · buckets ≤2 / 2–4 / 4–7 / &gt;7.
      </p>

      {/* Tooltip */}
      {tip && (
        <div
          className="pointer-events-none absolute z-10 rounded-lg px-3 py-2 whitespace-nowrap"
          style={{
            left: tip.x,
            top: tip.y,
            transform: 'translate(-50%, calc(-100% - 10px))',
            background: 'var(--color-tooltip-bg)',
            color: 'var(--color-tooltip-text)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
          }}
        >
          <div
            className="text-[9px] font-semibold uppercase tracking-widest mb-1"
            style={{ color: 'var(--color-tooltip-label)' }}
          >
            {tip.dateLabel}
          </div>
          <div className="font-mono text-xs font-semibold leading-none">
            {tip.status === 'data' && (
              <>
                <span style={{ color: 'var(--color-tooltip-label)' }}>Avg VRP </span>
                <span>{tip.vrp!.toFixed(2)}</span>
              </>
            )}
            {tip.status === 'upcoming' && <span>Upcoming</span>}
            {tip.status === 'no-scan' && <span>No scan</span>}
          </div>
          {/* Tail pointing down */}
          <div
            className="absolute left-1/2 -translate-x-1/2 -bottom-[5px] w-0 h-0"
            style={{
              borderLeft: '6px solid transparent',
              borderRight: '6px solid transparent',
              borderTop: '6px solid var(--color-tooltip-bg)',
            }}
          />
        </div>
      )}
    </div>
  );
}
