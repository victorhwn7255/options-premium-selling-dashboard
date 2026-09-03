'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { fetchThresholds } from '@/lib/api';
import { THRESHOLDS_FALLBACK } from '@/lib/thresholds-fallback';
import type { Thresholds } from '@/lib/types';
import { decisionCards, GUIDE_FOOTER, type DecisionCard } from '@/lib/guide-content';
import { REGIMES, FINALS_FOOTNOTE } from '@/lib/regime-content';
import { METRICS, SECTIONS } from '@/lib/metrics-content';
import RegimeSection from './RegimeSection';
import MetricCard from './MetricCard';

export type GuideTab = 'playbook' | 'regimes' | 'glossary';

interface Props {
  open: boolean;
  initialTab?: GuideTab;
  currentRegime: string;
  onClose: () => void;
}

const TABS: { key: GuideTab; label: string }[] = [
  { key: 'playbook', label: 'Playbook' },
  { key: 'regimes', label: 'Regimes' },
  { key: 'glossary', label: 'Glossary' },
];

/* ── Playbook: one decision card ─────────────────────── */

function DecisionCardView({ card, onJump }: { card: DecisionCard; onJump: (id: string) => void }) {
  return (
    <section id={`decision-${card.id}`} className="bg-surface rounded-lg border border-border p-5">
      <div className="flex items-baseline gap-3">
        <span className="font-mono text-xs font-semibold text-txt-tertiary">STEP {card.step}</span>
        <h3 className="font-secondary text-xl font-medium text-txt">{card.title}</h3>
      </div>
      <p
        className="mt-2 text-sm text-txt-secondary leading-relaxed [&_strong]:text-txt [&_strong]:font-medium [&_code]:font-mono [&_code]:text-xs"
        dangerouslySetInnerHTML={{ __html: card.lead }}
      />
      {card.table && (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-[10px] font-primary font-semibold tracking-widest uppercase text-txt-tertiary">
                {card.table.cols.map(c => <th key={c} className="py-1.5 pr-3">{c}</th>)}
              </tr>
            </thead>
            <tbody>
              {card.table.rows.map((r, i) => (
                <tr key={i} className="border-t border-border-subtle align-top">
                  {r.cells.map((cell, j) => (
                    <td key={j} className={`py-2 pr-3 leading-relaxed ${j === 0 ? 'font-mono font-medium text-txt whitespace-nowrap' : 'text-txt-secondary'}`}>
                      {cell}
                      {j === r.cells.length - 1 && r.kind === 'guidance' && (
                        <span className="ml-1.5 font-mono text-[9px] uppercase tracking-wider text-txt-tertiary bg-surface-alt px-1.5 py-0.5 rounded-full">guidance</span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="mt-3 text-xs text-txt leading-relaxed">
        <span className="font-primary text-[10px] font-semibold tracking-widest uppercase text-txt-tertiary mr-2">What to do</span>
        {card.whatToDo}
      </p>
      {card.seeAlso.length > 0 && (
        <p className="mt-2 text-[11px] text-txt-tertiary">
          See also:{' '}
          {card.seeAlso.map((s, i) => (
            <span key={s.metricId}>
              {i > 0 && ' · '}
              <button type="button" onClick={() => onJump(s.metricId)} className="underline decoration-dotted hover:text-txt">{s.label}</button>
            </span>
          ))}
        </p>
      )}
    </section>
  );
}

/* ── Modal ──────────────────────────────────────────── */

export default function HowToGuideModal({ open, initialTab = 'playbook', currentRegime, onClose }: Props) {
  const [tab, setTab] = useState<GuideTab>(initialTab);
  const [t, setT] = useState<Thresholds>(THRESHOLDS_FALLBACK);
  const [source, setSource] = useState<'live' | 'cached'>('cached');
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => { if (open) setTab(initialTab); }, [open, initialTab]);

  // Thresholds: live endpoint wins; the generated fallback keeps the guide readable offline.
  useEffect(() => {
    if (!open) return;
    let alive = true;
    fetchThresholds().then(live => {
      if (!alive) return;
      if (live) { setT(live); setSource('live'); } else { setT(THRESHOLDS_FALLBACK); setSource('cached'); }
    });
    return () => { alive = false; };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', handler); document.body.style.overflow = prev; };
  }, [open, onClose]);

  // Regimes tab: scroll to the current regime once rendered.
  useEffect(() => {
    if (!open || tab !== 'regimes') return;
    const timer = setTimeout(() => {
      const panel = bodyRef.current;
      const el = panel?.querySelector<HTMLElement>(`[data-regime="${currentRegime}"]`);
      if (panel && el) panel.scrollTop = el.offsetTop - panel.offsetTop - 16;
    }, 120);
    return () => clearTimeout(timer);
  }, [open, tab, currentRegime]);

  const jumpTo = useCallback((metricId: string) => {
    setTab('glossary');
    setTimeout(() => {
      const el = bodyRef.current?.querySelector<HTMLElement>(`[data-metric-id="${metricId}"]`);
      el?.scrollIntoView({ block: 'start', behavior: 'smooth' });
    }, 80);
  }, []);

  if (!open || typeof window === 'undefined') return null;

  const cards = decisionCards(t);

  return createPortal(
    <div className="fixed inset-0 z-[10000] flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-sm animate-fade-in" onClick={onClose}>
      <div
        role="dialog" aria-modal="true" aria-label="How to use Theta Harvest"
        className="relative w-full max-w-[800px] max-h-[88vh] bg-bg rounded-xl border border-border shadow-xl flex flex-col animate-slide-in"
        onClick={e => e.stopPropagation()}
      >
        {/* Header + tabs */}
        <div className="sticky top-0 z-10 bg-bg rounded-t-xl border-b border-border-subtle px-5 sm:px-8 pt-5 pb-0">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="font-secondary text-[26px] font-semibold text-txt leading-tight">How to use Theta Harvest</h2>
              <p className="font-secondary italic text-sm text-txt-tertiary mt-1">Four decisions, in the order you make them — then the glossary.</p>
            </div>
            <button onClick={onClose} aria-label="Close" className="shrink-0 w-8 h-8 flex items-center justify-center rounded-md text-txt-tertiary hover:text-txt hover:bg-surface-alt transition-colors">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
          <div className="mt-4 flex items-end justify-between">
            <div className="flex gap-1" role="tablist">
              {TABS.map(x => (
                <button
                  key={x.key} role="tab" aria-selected={tab === x.key} onClick={() => setTab(x.key)}
                  className={`px-3.5 py-2 text-sm font-primary font-medium rounded-t-md border-b-2 transition-colors ${
                    tab === x.key ? 'border-primary text-txt' : 'border-transparent text-txt-tertiary hover:text-txt'
                  }`}
                >
                  {x.label}
                </button>
              ))}
            </div>
            <span className="font-mono text-[10px] text-txt-tertiary pb-2" title="Every number in this guide is read from the backend (GET /api/thresholds)">
              thresholds: {source}
            </span>
          </div>
        </div>

        {/* Body */}
        <div ref={bodyRef} className="overflow-y-auto flex-1 px-4 sm:px-8 py-5">
          {tab === 'playbook' && (
            <div className="space-y-4">
              {cards.map(c => <DecisionCardView key={c.id} card={c} onJump={jumpTo} />)}
              <p className="text-xs text-txt-tertiary italic leading-relaxed pt-2">
                Everything updates after the 18:30 ET scan. In the current tape (avg VRP negative since late July 2026) the honest answer to step 2 has been “nothing” for most sessions — that is the app making a decision, not failing to.
              </p>
            </div>
          )}

          {tab === 'regimes' && (
            <div className="space-y-5">
              {REGIMES.map(rd => (
                <div key={rd.regime} data-regime={rd.regime}>
                  <RegimeSection
                    regime={rd.regime} tagline={rd.tagline} colorToken={rd.colorToken}
                    triggers={rd.triggers(t)} triggerLogic={rd.triggerLogic}
                    explanation={rd.explanation} dos={rd.dos} donts={rd.donts}
                    example={rd.example} isCurrent={currentRegime === rd.regime}
                  />
                </div>
              ))}
              <div data-regime="THE FINALS" className="rounded-lg border border-border-subtle bg-surface-alt px-5 py-4 text-xs text-txt-secondary leading-relaxed">
                <span className="font-mono font-semibold text-accent mr-2">THE FINALS</span>{FINALS_FOOTNOTE(t)}
              </div>
              <p className="text-xs text-txt-tertiary leading-relaxed">
                <strong className="text-txt">The v2 engine</strong> runs beside v1 (the 🔭 badge on each row): a forward-vol forecast instead of the trailing 30 days, and a hysteretic gate state per name. It changes no live decision; its forecaster is being recalibrated (Test T1). Read its gate state and transient tag as a second opinion on danger — never its “eligible” flag as a buy signal.
              </p>
            </div>
          )}

          {tab === 'glossary' && (
            <div className="space-y-6">
              {SECTIONS.map(section => {
                const items = METRICS.filter(m => m.section === section.key);
                if (!items.length) return null;
                return (
                  <div key={section.key}>
                    <div className="font-primary text-[10px] font-semibold tracking-widest uppercase text-txt-tertiary mb-1 px-1">{section.label}</div>
                    {section.desc && <p className="text-xs text-txt-tertiary leading-relaxed mb-3 px-1">{section.desc}</p>}
                    <div className="space-y-3">
                      {items.map(m => <MetricCard key={m.id} metric={m} t={t} />)}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-border-subtle px-5 sm:px-8 py-3.5">
          <p className="text-xs italic text-txt-tertiary leading-relaxed">{GUIDE_FOOTER}</p>
        </div>
      </div>
    </div>,
    document.body,
  );
}
