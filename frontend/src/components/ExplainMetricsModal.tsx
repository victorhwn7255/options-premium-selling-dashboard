'use client';

import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { METRICS, SECTIONS } from '@/lib/metrics-content';
import type { MetricDefinition, MetricReading } from '@/lib/metrics-content';

interface ExplainMetricsModalProps {
  open: boolean;
  onClose: () => void;
}

/* ── Reading pill ────────────────────────────────────── */

const READING_COLORS: Record<MetricReading['color'], { dot: string; text: string; bg: string }> = {
  good:    { dot: 'bg-black',      text: 'text-black',      bg: 'border border-black' },
  ok:      { dot: 'bg-[#525252]',  text: 'text-[#525252]',  bg: 'border border-[#E5E5E5]' },
  bad:     { dot: 'bg-black',      text: 'text-white',      bg: 'bg-black' },
  neutral: { dot: 'bg-[#525252]',  text: 'text-[#525252]',  bg: 'border border-[#E5E5E5]' },
};

function ReadingPill({ reading }: { reading: MetricReading }) {
  const c = READING_COLORS[reading.color];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-2xs font-medium ${c.text} ${c.bg}`}>
      <span className={`w-2 h-2 shrink-0 ${c.dot}`} />
      {reading.label}
    </span>
  );
}

/* ── Metric card ─────────────────────────────────────── */

function MetricCard({ metric }: { metric: MetricDefinition }) {
  return (
    <div className="relative bg-white border border-black overflow-hidden pl-2">
      {/* Left accent bar */}
      <div className="absolute left-0 top-0 bottom-0 w-1 bg-black" />

      <div className="px-5 py-5">
        {/* Header */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className="text-[24px] leading-none">{metric.emoji}</span>
          <span className="font-display text-[19px] font-semibold text-black">{metric.name}</span>
          <span className="font-mono text-[10px] font-semibold uppercase tracking-wider text-[#525252] bg-[#F5F5F5] px-2 py-0.5">
            {metric.tag}
          </span>
        </div>

        {/* Explanation */}
        <div
          className="mt-3 text-sm text-[#525252] leading-relaxed font-body [&_strong]:text-black [&_strong]:font-medium [&_em]:font-display [&_em]:italic [&_em]:text-black"
          dangerouslySetInnerHTML={{ __html: metric.explain }}
        />

        {/* Analogy box */}
        <div className="mt-4 bg-[#F5F5F5] px-4 py-3 border-l-4 border-black">
          <div className="font-mono text-[10px] font-semibold tracking-widest uppercase mb-1.5 text-black">
            Think of it like
          </div>
          <div
            className="text-xs text-[#525252] leading-relaxed font-body [&_em]:font-display [&_em]:italic [&_em]:text-black"
            dangerouslySetInnerHTML={{ __html: metric.analogy }}
          />
        </div>

        {/* Formula block */}
        <div className="mt-4">
          <div className="font-mono text-[10px] font-semibold tracking-widest uppercase text-[#525252] mb-1.5">
            {metric.formulaLabel}
          </div>
          <div className="bg-[#F5F5F5] border border-[#E5E5E5] px-4 py-3 space-y-1">
            {metric.formulas.map((f, i) => (
              <div key={i} className="font-mono text-xs text-black">
                {f}
              </div>
            ))}
          </div>
        </div>

        {/* Reading pills */}
        {metric.readings.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {metric.readings.map((r, i) => (
              <ReadingPill key={i} reading={r} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Main modal ──────────────────────────────────────── */

export default function ExplainMetricsModal({ open, onClose }: ExplainMetricsModalProps) {
  // Escape key
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, onClose]);

  // Body scroll lock
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = prev; };
  }, [open]);

  if (!open || typeof window === 'undefined') return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-[720px] max-h-[85vh] bg-white border border-black flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 bg-white border-b-2 border-black px-6 sm:px-8 py-5 flex items-start justify-between gap-4">
          <div>
            <h2 className="font-display text-3xl font-bold text-black leading-tight tracking-tight">
              Key Metrics for Premium Selling
            </h2>
            <p className="font-body italic text-sm text-[#525252] mt-1">
              Explain the key metrics like I&apos;m 12.
            </p>
          </div>
          <button
            onClick={onClose}
            className="shrink-0 w-8 h-8 flex items-center justify-center text-[#525252] hover:text-black hover:bg-[#F5F5F5] transition-colors duration-100"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 px-4 sm:px-8 py-5">
          {SECTIONS.map(section => {
            const sectionMetrics = METRICS.filter(m => m.section === section.key);
            return (
              <div key={section.key} className="mb-6 last:mb-0">
                {/* Section label */}
                <div className="font-mono text-[10px] font-semibold tracking-widest uppercase text-[#525252] mb-3 px-1">
                  {section.label}
                </div>
                <div className="space-y-3">
                  {sectionMetrics.map(metric => (
                    <MetricCard key={metric.id} metric={metric} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="border-t border-[#E5E5E5] px-6 sm:px-8 py-4">
          <p className="text-xs italic text-[#525252] leading-relaxed font-body">
            All metrics update daily after market close (~6:30 PM ET). The scoring engine combines these metrics into a single 0&ndash;100 score per ticker, filtered by the earnings gate and adjusted by the market regime. When in doubt, trust the score &mdash; it&apos;s doing the math so you don&apos;t have to.
          </p>
        </div>
      </div>
    </div>,
    document.body,
  );
}
