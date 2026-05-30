'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import type {
  CreditPutSpreadsResponse, CreditPutSpreadCandidate,
  RegimeOverlay, CPSRejectionSummary,
} from '@/lib/types';
import { fetchCreditPutSpreads } from '@/lib/api';
import CreditPutSpreadTable from './CreditPutSpreadTable';
import CreditPutSpreadDetailPanel from './CreditPutSpreadDetailPanel';

function buildScanMarkdown(data: CreditPutSpreadsResponse): string {
  const s = data.rejectionSummary;
  const o = data.regimeOverlay;
  const scanLine = s
    ? `**Scan summary:** Checked ${s.checked} / ${s.actionable} actionable / ${s.rejectedByBaseGate} base_gate / ${s.rejectedByConstruction} construction / ${s.rejectedByExecution} execution / ${s.rejectedByOverlay} overlay / ${s.rejectedByConfirmation} confirmation`
    : `**Scan summary:** (unavailable)`;
  const termWord = o.vixBackwardation == null ? '—' : o.vixBackwardation ? 'Backwardation' : 'Contango';
  const overlayLine = `**Overlay:** VIX ${o.vix != null ? o.vix.toFixed(2) : '—'} / VIX3M ${o.vix3m != null ? o.vix3m.toFixed(2) : '—'} / VVIX ${o.vvix != null ? o.vvix.toFixed(1) : '—'} — ${o.status}, ${termWord}`;
  const lines: string[] = [scanLine, overlayLine];
  if (data.candidates.length > 0) {
    lines.push('');
    lines.push('| # | Ticker | Action | Days | Score | C/W | Credit | Width | Max Loss | RV Status | Notes |');
    lines.push('|---|--------|--------|------|-------|------|--------|-------|----------|-----------|-------|');
    data.candidates.forEach((c, i) => {
      const action = c.action.replace('_CPS', '');
      const days = `${c.consecutiveSellDays}d`;
      const score = String(Math.round(c.baseScore));
      const cw = `${(c.creditToWidth * 100).toFixed(1)}%`;
      const credit = `$${c.netCredit.toFixed(2)}`;
      const width = `$${c.width % 1 === 0 ? c.width.toFixed(0) : c.width.toFixed(2)}`;
      const maxLoss = `$${c.maxLoss.toFixed(2)}`;
      const rv = c.rvAccelStatus ?? '—';
      const note = (c.warnings[0] ?? '').split('—')[0].trim().slice(0, 18) || '—';
      lines.push(`| ${i + 1} | ${c.ticker} | ${action} | ${days} | ${score} | ${cw} | ${credit} | ${width} | ${maxLoss} | ${rv} | ${note} |`);
    });
  }
  return lines.join('\n');
}

function CopyScanButton({ data }: { data: CreditPutSpreadsResponse }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = useCallback(() => {
    const md = buildScanMarkdown(data);
    navigator.clipboard.writeText(md).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [data]);

  return (
    <span className="relative group">
      <button
        onClick={handleCopy}
        className="p-1 rounded hover:bg-surface-alt transition-colors"
        aria-label="Copy scan to clipboard"
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
      <span
        className="pointer-events-none absolute right-0 top-full mt-2 opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-150 origin-top-right z-50"
        style={{ background: 'var(--color-tooltip-bg)', color: 'var(--color-tooltip-text)' }}
      >
        <span className="flex items-center rounded-lg px-3.5 py-2.5 shadow-lg whitespace-nowrap" style={{ boxShadow: '0 8px 24px rgba(0,0,0,0.18)' }}>
          <span className="text-2xs font-medium" style={{ color: 'var(--color-tooltip-text)' }}>
            {copied ? 'Copied!' : 'Copy scan to clipboard'}
          </span>
        </span>
      </span>
    </span>
  );
}

function statusColor(status: string): { fg: string; bg: string; border: string } {
  switch (status) {
    case 'NORMAL':
      return { fg: 'var(--color-secondary)', bg: 'var(--color-secondary-subtle)', border: 'var(--color-secondary-30)' };
    case 'CAUTION':
      return { fg: 'var(--color-warning)', bg: 'var(--color-warning-subtle)', border: 'var(--color-warning-30)' };
    case 'DANGER':
      return { fg: 'var(--color-error)', bg: 'var(--color-error-subtle)', border: 'var(--color-error-30)' };
    default:  // UNKNOWN
      return { fg: 'var(--color-txt-tertiary)', bg: 'var(--color-surface-alt)', border: 'var(--color-border-subtle)' };
  }
}

function RegimeOverlayRow({ overlay }: { overlay: RegimeOverlay }) {
  const colors = statusColor(overlay.status);
  const isUnknown = overlay.status === 'UNKNOWN';

  const fields: Array<{ label: string; value: string; muted?: boolean }> = [
    { label: 'Overlay', value: overlay.status, muted: false },
    { label: 'VIX',     value: overlay.vix    != null ? overlay.vix.toFixed(2)   : '—', muted: isUnknown },
    { label: 'VIX3M',   value: overlay.vix3m  != null ? overlay.vix3m.toFixed(2) : '—', muted: isUnknown },
    { label: 'VVIX',    value: overlay.vvix   != null ? overlay.vvix.toFixed(1)  : '—', muted: isUnknown },
    {
      label: 'Term',
      value: overlay.vixBackwardation == null
        ? '—'
        : overlay.vixBackwardation ? 'Backwardation' : 'Contango',
      muted: isUnknown,
    },
  ];

  return (
    <div
      className="rounded-lg border px-4 sm:px-5 py-3 flex flex-wrap items-center gap-x-5 gap-y-2"
      style={{ background: colors.bg, borderColor: colors.border }}
    >
      <span className="font-primary text-[10px] font-semibold uppercase tracking-widest" style={{ color: colors.fg }}>
        Regime Overlay
      </span>
      {fields.map((f, i) => (
        <span key={f.label} className="flex items-baseline gap-1.5">
          <span className="font-primary text-[10px] font-semibold uppercase tracking-wider text-txt-tertiary">
            {f.label}
          </span>
          <span
            className="font-mono text-xs sm:text-sm font-semibold"
            style={{
              color: i === 0 ? colors.fg : (f.muted ? 'var(--color-txt-tertiary)' : 'var(--color-txt-secondary)'),
            }}
          >
            {f.value}
          </span>
        </span>
      ))}
      {overlay.warnings.length > 0 && (
        <div className="basis-full text-[11px] leading-relaxed" style={{ color: colors.fg }}>
          {isUnknown ? (
            <span className="italic">Regime overlay unavailable — candidates not blocked.</span>
          ) : (
            <ul className="list-disc pl-4 marker:text-txt-tertiary">
              {overlay.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function RejectionSummaryChips({ summary }: { summary: CPSRejectionSummary }) {
  const chips: Array<{ label: string; count: number; tone: 'good' | 'bad' | 'neutral' }> = [
    { label: 'Checked',         count: summary.checked,                 tone: 'neutral' },
    { label: 'Actionable',      count: summary.actionable,              tone: summary.actionable > 0 ? 'good' : 'neutral' },
    { label: 'Base gate',       count: summary.rejectedByBaseGate,      tone: summary.rejectedByBaseGate > 0 ? 'bad' : 'neutral' },
    { label: 'Construction',    count: summary.rejectedByConstruction,  tone: summary.rejectedByConstruction > 0 ? 'bad' : 'neutral' },
    { label: 'Execution',       count: summary.rejectedByExecution,     tone: summary.rejectedByExecution > 0 ? 'bad' : 'neutral' },
    { label: 'Overlay',         count: summary.rejectedByOverlay,       tone: summary.rejectedByOverlay > 0 ? 'bad' : 'neutral' },
    { label: 'Confirmation',    count: summary.rejectedByConfirmation,  tone: summary.rejectedByConfirmation > 0 ? 'bad' : 'neutral' },
  ];

  const colorFor = (tone: 'good' | 'bad' | 'neutral') =>
    tone === 'good' ? 'var(--color-secondary)'
      : tone === 'bad' ? 'var(--color-warning)'
        : 'var(--color-txt-secondary)';

  return (
    <div className="flex flex-wrap gap-2">
      {chips.map(c => (
        <span
          key={c.label}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-border-subtle bg-surface-alt"
        >
          <span className="font-primary text-[10px] uppercase tracking-wider text-txt-tertiary">
            {c.label}
          </span>
          <span className="font-mono text-xs font-semibold" style={{ color: colorFor(c.tone) }}>
            {c.count}
          </span>
        </span>
      ))}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="text-center">
        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-sm text-txt-tertiary">Loading Credit Put Spreads...</p>
      </div>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-lg border border-error-20 bg-error-subtle px-5 py-5">
      <p className="text-sm font-semibold text-error mb-1">Could not load Credit Put Spreads</p>
      <p className="text-xs text-txt-secondary mb-3">{message}</p>
      <button
        onClick={onRetry}
        className="px-3 py-1.5 text-xs font-medium rounded-md bg-primary text-white hover:bg-primary-hover transition-colors"
      >
        Retry
      </button>
    </div>
  );
}

interface EmptyStateProps {
  message?: string | null;
  summary?: CPSRejectionSummary | null;
  universe: string[];
  data: CreditPutSpreadsResponse;
}

function EmptyState({ message, summary, universe, data }: EmptyStateProps) {
  return (
    <div className="bg-surface rounded-lg border border-border px-5 sm:px-6 py-6">
      <p className="text-sm font-medium text-txt mb-1">
        No current Credit Put Spread candidates passed the filters.
      </p>
      <p className="text-xs text-txt-secondary mb-4 leading-relaxed">
        {message ||
          'The universe ' +
          `(${universe.join(', ')}) was evaluated, but no spread cleared every binary gate today.`}
      </p>
      {summary && (
        <>
          <div className="flex items-center justify-between mb-2">
            <div className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase">
              Rejection summary
            </div>
            <CopyScanButton data={data} />
          </div>
          <RejectionSummaryChips summary={summary} />
          <p className="text-[11px] text-txt-tertiary mt-3 leading-relaxed">
            <strong className="text-txt-secondary">How to read this:</strong>{' '}
            <em>Base gate</em> — earnings / DANGER regime / VRP. <em>Construction</em> — no clean
            DTE / short delta / long leg. <em>Execution</em> — bid/ask too wide, low OI / volume.
            <em> Overlay</em> — market-wide VIX / VVIX blocked SELL_CPS. <em>Confirmation</em> —
            cleared everything except the 2-day ticker-level streak.
          </p>
        </>
      )}
    </div>
  );
}

export default function CreditPutSpreadsTab() {
  const [data, setData] = useState<CreditPutSpreadsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchCreditPutSpreads()
      .then(r => {
        if (cancelled) return;
        setData(r);
        // Auto-select the top candidate (if any) for instant detail visibility.
        if (r.candidates.length > 0) {
          setSelectedTicker(prev => prev ?? r.candidates[0].ticker);
        }
      })
      .catch(e => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Unknown error');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [refreshKey]);

  const selectedCandidate = useMemo<CreditPutSpreadCandidate | null>(() => {
    if (!data || !selectedTicker) return null;
    return data.candidates.find(c => c.ticker === selectedTicker) ?? null;
  }, [data, selectedTicker]);

  if (loading) return <LoadingState />;
  if (error) {
    return (
      <ErrorState
        message={error}
        onRetry={() => setRefreshKey(k => k + 1)}
      />
    );
  }
  if (!data) {
    return (
      <ErrorState
        message="No response from server"
        onRetry={() => setRefreshKey(k => k + 1)}
      />
    );
  }

  return (
    <div className="space-y-5">
      {/* Regime overlay row — always visible so UNKNOWN state still surfaces clearly. */}
      <RegimeOverlayRow overlay={data.regimeOverlay} />

      {/* Candidate states */}
      {data.candidates.length === 0 ? (
        <EmptyState
          message={data.message}
          summary={data.rejectionSummary}
          universe={data.cpsUniverse}
          data={data}
        />
      ) : (
        <>
          {/* Compact rejection summary (always show when present, even with candidates) */}
          {data.rejectionSummary && (
            <div className="rounded-lg border border-border-subtle bg-surface-alt px-4 py-3">
              <div className="flex items-center justify-between mb-2">
                <div className="font-primary text-[10px] font-semibold text-txt-tertiary tracking-widest uppercase">
                  Scan summary
                </div>
                <CopyScanButton data={data} />
              </div>
              <RejectionSummaryChips summary={data.rejectionSummary} />
            </div>
          )}

          <CreditPutSpreadTable
            candidates={data.candidates}
            selectedTicker={selectedTicker}
            onSelect={setSelectedTicker}
          />

          {selectedCandidate && (
            <CreditPutSpreadDetailPanel candidate={selectedCandidate} />
          )}
        </>
      )}

      {/* Methodology footer — mirrors the Naked Puts footer convention */}
      <div className="px-4 sm:px-5 py-4 bg-surface-alt rounded-lg border border-border-subtle">
        <div className="text-xs text-txt-tertiary leading-loose">
          <strong className="text-txt-secondary">Construction:</strong>{' '}
          30–45 DTE, target 0.20 short delta, ATR-aware width (0.75–1.5× ATR).{' '}
          <strong className="text-txt-secondary">Gates:</strong>{' '}
          credit/width ≥ 25% for SELL_CPS (≥ 20% for WATCH_CPS), bid/ask &lt; 20%, OI ≥ 100, volume ≥ 25, ticker-level 2-day confirmation.{' '}
          <strong className="text-txt-secondary">Ranking:</strong>{' '}
          Base Edge Score after binary filters (no separate CPS score).{' '}
          <strong className="text-txt-secondary">Position size:</strong>{' '}
          trader-controlled — record contract count in your trade journal.{' '}
          <span className="text-secondary">Live data — not financial advice.</span>
        </div>
      </div>
    </div>
  );
}
