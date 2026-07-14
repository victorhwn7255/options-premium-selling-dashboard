'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import type {
  ScanResponse, HealthResponse, VerificationResult, EarningsVerificationResult,
  TickerDelta, ShadowSummaryResponse, ShadowDiffResponse,
} from '@/lib/types';
import { fetchHealth, fetchShadowSummary, fetchShadowDiff, fetchCreditPutSpreadsRaw } from '@/lib/api';
import { buildMachineSections, serializeSections, exportHeader } from '@/lib/machine-format';
import MachineSectionView from './MachineSectionView';

/**
 * MACHINE mode — a verbatim, full-precision render of everything the API
 * returns, plus the ops console (relocated earnings-refresh + scan trigger).
 *
 * P1: display-only. No scoring.ts import, no derived gate/eligibility logic —
 * v2 fields are rendered exactly as the backend sent them.
 */
interface MachineViewProps {
  apiData: ScanResponse | null;
  loading: boolean;
  refreshing: boolean;
  scanProgress: string | null;
  verification: VerificationResult | null;
  earningsVerification: EarningsVerificationResult | null;
  deltaMap: Record<string, TickerDelta>;
}

const opsBtn =
  'font-mono text-2xs px-2.5 py-1 border border-border rounded-sm text-txt ' +
  'hover:bg-surface-alt transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-pre';

export default function MachineView(props: MachineViewProps) {
  const { apiData, loading } = props;
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [shadowSummary, setShadowSummary] = useState<ShadowSummaryResponse | null>(null);
  const [shadowDiff, setShadowDiff] = useState<ShadowDiffResponse | null>(null);
  const [cpsRaw, setCpsRaw] = useState<Record<string, unknown> | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle');

  // Self-fetch the MACHINE-only surfaces; each fails independently into an
  // errors note (failures are data too). Re-fetch when a new scan lands.
  useEffect(() => {
    let cancelled = false;
    const grab = <T,>(key: string, fn: () => Promise<T>, set: (v: T) => void) =>
      fn().then(v => { if (!cancelled) set(v); })
        .catch(e => { if (!cancelled) setErrors(prev => ({ ...prev, [key]: String(e?.message ?? e) })); });
    grab('health', fetchHealth, setHealth);
    grab('shadow_summary', () => fetchShadowSummary(20), setShadowSummary);
    grab('shadow_diff', () => fetchShadowDiff(500), setShadowDiff);
    grab('cps', fetchCreditPutSpreadsRaw, setCpsRaw);
    return () => { cancelled = true; };
  }, [apiData?.scanned_at]); // eslint-disable-line react-hooks/exhaustive-deps

  const sections = useMemo(() => buildMachineSections({
    scan: apiData,
    scanStatus: props.refreshing ? 'scanning' : 'idle',
    scanProgress: props.scanProgress,
    health,
    verification: props.verification,
    earningsVerification: props.earningsVerification,
    deltaMap: props.deltaMap,
    shadowSummary,
    shadowDiff,
    cpsRaw,
    errors,
  }), [apiData, props.refreshing, props.scanProgress, health,
       props.verification, props.earningsVerification, props.deltaMap,
       shadowSummary, shadowDiff, cpsRaw, errors]);

  const handleCopyAll = useCallback(() => {
    navigator.clipboard.writeText(serializeSections(sections, exportHeader(apiData?.scanned_at)))
      .then(() => setCopyState('copied'))
      .catch(() => setCopyState('failed'));
    setTimeout(() => setCopyState('idle'), 2000);
  }, [sections, apiData?.scanned_at]);

  if (loading && !apiData) {
    return <p className="font-mono text-xs text-txt-tertiary py-20 text-center">loading…</p>;
  }

  return (
    <div className="font-mono">
      {/* Page banner */}
      <p className="text-2xs text-txt-tertiary tracking-wider mb-4 whitespace-nowrap overflow-hidden">
        MACHINE // theta-harvest // verbatim=true precision=full
      </p>

      {/* Ops controls — controls, not data: never serialized by COPY_ALL.
          Deliberately NO scan trigger and NO earnings refresh: scans run on the
          18:30 ET cron, and earnings dates self-heal nightly (FMP cache expires
          once a date passes + post-scan Yahoo backfill/override). */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <button className={opsBtn} onClick={handleCopyAll}>
          {copyState === 'copied' ? '[COPIED]' : copyState === 'failed' ? '[COPY_FAILED]' : '[COPY_ALL]'}
        </button>
      </div>

      {sections.map(s => <MachineSectionView key={s.id} section={s} />)}
    </div>
  );
}
