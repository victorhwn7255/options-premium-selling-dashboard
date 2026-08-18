'use client';

/**
 * Phase C3 — advisory entry-sizing card, attached to candidate rows (Naked Puts
 * drawer + CPS detail panel). Renders ONLY for the authenticated owner (cached
 * probe — the public demo never sees equity-derived numbers).
 *
 * Everything shown is computed SERVER-side (/api/sizing/{ticker}); this card
 * renders the returned arithmetic verbatim — it computes nothing (P1 pattern).
 * The full chain (equity·φ·f*·R·O/M), each dial's driver, and the binding cap
 * are always visible so a mis-sized recommendation is visible on its face.
 * Advisory only: the human enters the trade; there is no order path.
 */

import React, { useEffect, useState } from 'react';
import { JournalApiError, SizingResult, fetchSizing, ownerAccessCached } from '@/lib/journal-api';

interface SizingCardProps {
  ticker: string;
  /** Prefills — CPS passes its short leg; the NP drawer passes heuristics. */
  defaultStrike?: number;
  defaultPremium?: number;
  defaultDte?: number;
  /** Compute immediately with the prefills (CPS rows — a concrete candidate). */
  autoCompute?: boolean;
  /** Context note, e.g. the CPS "sizes the short-put leg" caveat. */
  note?: string;
}

export default function SizingCard({ ticker, defaultStrike, defaultPremium,
                                     defaultDte = 35, autoCompute = false,
                                     note }: SizingCardProps) {
  const [owner, setOwner] = useState(false);
  const [strike, setStrike] = useState(defaultStrike?.toString() ?? '');
  const [premium, setPremium] = useState(defaultPremium?.toString() ?? '');
  const [dte, setDte] = useState(defaultDte.toString());
  const [result, setResult] = useState<SizingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { ownerAccessCached().then(setOwner); }, []);
  // Re-prefill when the selected candidate changes.
  useEffect(() => {
    setStrike(defaultStrike?.toString() ?? '');
    setPremium(defaultPremium?.toString() ?? '');
    setDte(defaultDte.toString());
    setResult(null);
    setError(null);
  }, [ticker, defaultStrike, defaultPremium, defaultDte]);

  const compute = React.useCallback(async (s: number, p: number, d: number) => {
    setBusy(true);
    setError(null);
    try {
      setResult(await fetchSizing(ticker, s, p, d));
    } catch (e) {
      setResult(null);
      setError(e instanceof JournalApiError && e.status === 409
        ? `${e.message} — set NAV in the Portfolio / Risk tab first`
        : e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [ticker]);

  useEffect(() => {
    if (owner && autoCompute && defaultStrike && defaultPremium) {
      compute(defaultStrike, defaultPremium, defaultDte);
    }
  }, [owner, autoCompute, defaultStrike, defaultPremium, defaultDte, compute]);

  if (!owner) return null;

  const num = (v: string) => { const n = parseFloat(v); return isNaN(n) ? null : n; };
  const canCompute = num(strike) !== null && num(premium) !== null && num(dte) !== null;
  const input = 'w-20 px-2 py-1 text-xs font-mono bg-surface border border-border rounded text-txt';
  const lbl = 'text-[10px] uppercase tracking-widest text-txt-tertiary';

  return (
    <div className="rounded-lg border border-border bg-surface-alt p-4 space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-txt-secondary">
          Entry Sizing <span className="normal-case font-normal text-txt-tertiary">· advisory — you enter the trade</span>
        </h3>
        {result && (
          <span className="text-[10px] text-txt-tertiary font-mono">
            f* {result.kelly.f_star.toFixed(3)} ({result.kelly.source})
          </span>
        )}
      </div>

      <div className="flex items-end gap-3 flex-wrap">
        <label className="space-y-0.5"><div className={lbl}>Strike</div>
          <input className={input} value={strike} onChange={e => setStrike(e.target.value)} inputMode="decimal" /></label>
        <label className="space-y-0.5"><div className={lbl}>Premium</div>
          <input className={input} value={premium} onChange={e => setPremium(e.target.value)} inputMode="decimal" /></label>
        <label className="space-y-0.5"><div className={lbl}>DTE</div>
          <input className={input} value={dte} onChange={e => setDte(e.target.value)} inputMode="numeric" /></label>
        <button disabled={!canCompute || busy}
          onClick={() => compute(num(strike)!, num(premium)!, num(dte)!)}
          className="px-3 py-1.5 text-xs font-semibold rounded bg-primary text-white disabled:opacity-40 hover:opacity-90">
          {busy ? 'Computing…' : 'Size it'}
        </button>
      </div>

      {note && <p className="text-[11px] text-txt-tertiary">{note}</p>}
      {error && <p className="text-xs text-error">{error}</p>}

      {result && (
        <div className="space-y-2.5">
          {result.f_star_zero && (
            <div className="px-3 py-2 rounded border border-warning-30 bg-warning-subtle text-xs text-txt">
              <strong>f* = 0 — no positive-growth size.</strong> The Kelly engine (backtest seed
              + disaster injection) finds no size with positive expected growth; the
              recommendation is 0 by construction, not by a cap. Log immature / disaster
              injection dominates — recalibration belongs to Phase-F trials.
            </div>
          )}

          <div className="flex items-baseline gap-3 flex-wrap">
            <span className="font-mono text-2xl font-semibold text-txt">
              {result.rec_contracts}
            </span>
            <span className="text-xs text-txt-secondary">recommended contracts</span>
            {result.binding_cap !== 'none' && (
              <span className="text-[11px] font-mono px-2 py-0.5 rounded border border-warning-30 bg-warning-subtle text-warning">
                {result.binding_cap} binds (raw {result.rec_contracts_raw})
              </span>
            )}
          </div>

          <p className="font-mono text-[11px] text-txt-secondary break-all">{result.arithmetic}</p>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-1.5 text-[11px]">
            <div><span className={lbl}>Equity·φ </span>
              <span className="font-mono text-txt-secondary">${result.equity.toLocaleString()} × {result.phi}</span></div>
            <div><span className={lbl}>Margin / contract </span>
              <span className="font-mono text-txt-secondary">${result.margin_per_contract.toLocaleString()}</span></div>
            <div><span className={lbl}>Incr. book stress </span>
              <span className="font-mono text-txt-secondary">${result.incremental_book_stress.toLocaleString()}</span></div>
            <div className="col-span-2 sm:col-span-3 text-txt-tertiary">
              R {result.dial_R} — {result.dial_R_driver}</div>
            <div className="col-span-2 sm:col-span-3 text-txt-tertiary">
              O {result.dial_O} — {result.dial_O_driver}</div>
          </div>

          {result.book_notes.length > 0 && (
            <p className="text-[10px] text-txt-tertiary">{result.book_notes.join(' · ')}</p>
          )}
        </div>
      )}
    </div>
  );
}
