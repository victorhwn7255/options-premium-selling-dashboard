'use client';

import { useState } from 'react';
import type { MetricDefinition, MetricReading } from '@/lib/metrics-content';
import type { Thresholds } from '@/lib/types';

/* ── Reading pill ────────────────────────────────────── */

const READING_COLORS: Record<MetricReading['color'], { dot: string; text: string; bg: string }> = {
  good:    { dot: 'bg-success',  text: 'text-success',  bg: 'bg-success-subtle' },
  ok:      { dot: 'bg-warning',  text: 'text-warning',  bg: 'bg-warning-subtle' },
  bad:     { dot: 'bg-error',    text: 'text-error',    bg: 'bg-error-subtle' },
  neutral: { dot: 'bg-accent',   text: 'text-accent',   bg: 'bg-accent-subtle' },
};

export function ReadingPill({ reading }: { reading: MetricReading }) {
  const c = READING_COLORS[reading.color];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-2xs font-medium ${c.text} ${c.bg}`}>
      <span className={`w-2 h-2 rounded-full shrink-0 ${c.dot}`} />
      {reading.label}
    </span>
  );
}

/* ── Metric card: one sentence + threshold pills + "what to do"; analogy/formula/case study behind "more" ── */

export default function MetricCard({ metric, t, defaultOpen = false }: { metric: MetricDefinition; t: Thresholds; defaultOpen?: boolean }) {
  const [more, setMore] = useState(defaultOpen);
  const readings = typeof metric.readings === 'function' ? metric.readings(t) : metric.readings;
  const formulas = typeof metric.formulas === 'function' ? metric.formulas(t) : metric.formulas;
  const hasMore = Boolean(metric.analogy || formulas.length || metric.example);

  return (
    <div id={`metric-${metric.id}`} data-metric-id={metric.id} className="relative bg-surface rounded-lg border border-border overflow-hidden pl-2 scroll-mt-4">
      <div className="absolute left-0 top-0 bottom-0 w-1 rounded-l-lg" style={{ backgroundColor: 'var(--color-primary)' }} />
      <div className="px-5 py-4">
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className="text-[22px] leading-none">{metric.emoji}</span>
          <span className="font-secondary text-[18px] font-semibold text-txt">{metric.name}</span>
          <span className="font-mono text-[10px] font-semibold uppercase tracking-wider text-txt-tertiary bg-surface-alt px-2 py-0.5 rounded-full">
            {metric.tag}
          </span>
        </div>

        <div
          className="mt-2.5 text-sm text-txt-secondary leading-relaxed [&_strong]:text-txt [&_strong]:font-medium [&_em]:font-secondary [&_em]:italic [&_em]:text-primary"
          dangerouslySetInnerHTML={{ __html: metric.explain }}
        />

        {readings.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {readings.map((r, i) => <ReadingPill key={i} reading={r} />)}
          </div>
        )}

        {metric.whatToDo && (
          <p className="mt-3 text-xs text-txt leading-relaxed">
            <span className="font-primary text-[10px] font-semibold tracking-widest uppercase text-txt-tertiary mr-2">What to do</span>
            {metric.whatToDo}
          </p>
        )}

        {hasMore && (
          <button
            type="button"
            onClick={() => setMore(v => !v)}
            className="mt-3 font-mono text-[11px] text-txt-tertiary hover:text-txt transition-colors"
            aria-expanded={more}
          >
            {more ? '[−] less' : '[+] more — analogy · formula · case study'}
          </button>
        )}

        {more && (
          <div className="mt-3 space-y-3">
            {metric.analogy && (
              <div className="bg-surface-alt rounded-md px-4 py-3" style={{ borderLeft: '3px solid var(--color-accent)' }}>
                <div className="font-primary text-[10px] font-semibold tracking-widest uppercase mb-1.5" style={{ color: 'var(--color-accent)' }}>Think of it like</div>
                <div className="text-xs text-txt-secondary leading-relaxed [&_em]:font-secondary [&_em]:italic [&_em]:text-primary" dangerouslySetInnerHTML={{ __html: metric.analogy }} />
              </div>
            )}
            {formulas.length > 0 && (
              <div>
                <div className="font-primary text-[10px] font-semibold tracking-widest uppercase text-txt-tertiary mb-1.5">{metric.formulaLabel ?? 'Formula'}</div>
                <div className="bg-bg-alt rounded-md border border-border px-4 py-3 space-y-1 overflow-x-auto">
                  {formulas.map((f, i) => (
                    <div key={i} className="font-mono text-xs whitespace-pre" style={{ color: 'var(--color-primary)' }}>{f}</div>
                  ))}
                </div>
              </div>
            )}
            {metric.example && (
              <div className="bg-surface-alt rounded-md px-4 py-3" style={{ borderLeft: '3px solid var(--color-secondary)' }}>
                <div className="font-primary text-[10px] font-semibold tracking-widest uppercase mb-1.5" style={{ color: 'var(--color-secondary)' }}>Real case study · {metric.example.tag}</div>
                <div className="text-xs text-txt-secondary leading-relaxed [&_strong]:text-txt [&_strong]:font-medium [&_em]:font-secondary [&_em]:italic [&_em]:text-primary" dangerouslySetInnerHTML={{ __html: metric.example.body }} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
