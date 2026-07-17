'use client';

/**
 * Trade Journal (J1) — live positions + closed-trade history.
 *
 * Owner-gated: on mount we probe the API; a 403 renders the locked card and
 * nothing else (the public demo never sees the book). All flags, checklists and
 * P&L numbers are computed by the backend (P1) — this component only renders.
 */

import React, { useCallback, useEffect, useState } from 'react';
import {
  EXIT_REASONS, JournalApiError, JournalSettings, Position, PositionCloseBody,
  PositionCreateBody, closePosition, createPosition, fetchJournal,
  fetchJournalSettings, fetchOpenBook, probeJournalAccess, saveJournalSettings,
} from '@/lib/journal-api';

// ── formatting helpers ──────────────────────────────────────────────────────
const fmtMoney = (v: number | null | undefined, dp = 0) =>
  v == null ? '—' : `${v < 0 ? '-' : ''}$${Math.abs(v).toFixed(dp)}`;
const fmtPct = (v: number | null | undefined) => (v == null ? '—' : `${(v * 100).toFixed(0)}%`);
const pnlClass = (v: number | null | undefined) =>
  v == null ? 'text-txt-tertiary' : v >= 0 ? 'text-secondary' : 'text-error';

const FLAG_STYLE: Record<string, string> = {
  PROFIT_TARGET: 'text-secondary border-secondary/40',
  TIME_EXIT: 'text-warning border-warning/40',
  EARNINGS_WALL: 'text-warning border-warning/40',
  DANGER_UNDERWATER: 'text-error border-error/40',
  TESTED: 'text-error border-error/40',
  PENDING_SETTLEMENT: 'text-error border-error/40',
};

function FlagChips({ position }: { position: Position }) {
  if (!position.flags?.length) {
    return <span className="text-[11px] text-txt-tertiary">—</span>;
  }
  return (
    <span className="inline-flex flex-wrap gap-1">
      {position.flags.map(f => (
        <span
          key={f.code}
          title={`${f.detail}\n\nRule: ${f.rule}`}
          className={`inline-block px-1.5 py-0.5 rounded border text-[10px] font-mono font-semibold cursor-help ${FLAG_STYLE[f.code] || 'text-txt-secondary border-border'}`}
        >
          {f.code.replace(/_/g, ' ')}
        </span>
      ))}
    </span>
  );
}

// ── locked (public) state ───────────────────────────────────────────────────
function LockedCard() {
  return (
    <div className="bg-surface rounded-lg border border-border overflow-hidden">
      <div className="px-6 py-12 sm:py-16 text-center max-w-2xl mx-auto">
        {/* Lock mark — quiet, in the app's line-icon style */}
        <div className="mx-auto mb-5 w-11 h-11 rounded-full border border-border-subtle bg-surface-alt flex items-center justify-center">
          <svg className="w-5 h-5 text-txt-tertiary" fill="none" viewBox="0 0 24 24"
            stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
            <rect x="5" y="11" width="14" height="9" rx="2" />
            <path strokeLinecap="round" d="M8 11V8a4 4 0 1 1 8 0v3" />
          </svg>
        </div>
        <div className="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-semibold uppercase tracking-widest border border-border-subtle bg-surface-alt text-txt-tertiary mb-4">
          Operator only
        </div>
        <h2 className="font-secondary text-xl sm:text-2xl font-medium text-txt mb-3">
          The book is private
        </h2>
        <p className="text-sm text-txt-secondary leading-relaxed max-w-md mx-auto">
          Live positions and the trade journal belong to the operator&apos;s account.
          Everything else here — the scanner, the regime read, the spreads tab — is
          open and stays open.
        </p>
        <div className="mt-8 pt-6 border-t border-border-subtle max-w-md mx-auto">
          <a
            href="/api/positions/open"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded border border-border text-txt-secondary hover:border-primary hover:text-txt transition-colors"
          >
            Owner sign-in
            <span aria-hidden="true">→</span>
          </a>
          <p className="mt-3 text-[11px] text-txt-tertiary leading-relaxed">
            Opens the verification flow in a new tab — a one-time PIN goes to the
            operator&apos;s email. Finish it, come back, and this page unlocks itself.
          </p>
        </div>
      </div>
    </div>
  );
}

// ── modal shell ─────────────────────────────────────────────────────────────
function Modal({ title, onClose, children }: {
  title: string; onClose: () => void; children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 sm:p-8" onClick={onClose}>
      <div
        className="bg-surface rounded-lg border border-border w-full max-w-lg my-8"
        onClick={e => e.stopPropagation()}
      >
        <div className="px-5 py-3.5 border-b border-border-subtle flex items-center justify-between">
          <h3 className="font-secondary text-lg font-medium text-txt">{title}</h3>
          <button onClick={onClose} aria-label="Close"
            className="text-txt-tertiary hover:text-txt text-xl leading-none">×</button>
        </div>
        <div className="px-5 py-4">{children}</div>
      </div>
    </div>
  );
}

const inputCls = 'w-full bg-surface-alt border border-border rounded px-2.5 py-1.5 text-sm ' +
  'text-txt font-mono focus:outline-none focus:border-primary';
const labelCls = 'block text-[10px] font-semibold uppercase tracking-widest text-txt-tertiary mb-1';

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <span className={labelCls}>{label}</span>
      {children}
    </div>
  );
}

// ── entry form ──────────────────────────────────────────────────────────────
function EntryModal({ onDone, onClose }: { onDone: () => void; onClose: () => void }) {
  const [form, setForm] = useState({
    ticker: '', structure: 'naked_put' as 'naked_put' | 'put_spread',
    short_strike: '', long_strike: '', expiry: '', contracts: '1',
    entry_credit: '', entry_commissions: '', entry_date: '', thesis: '',
  });
  const [deviationReason, setDeviationReason] = useState('');
  const [checklistError, setChecklistError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const submit = async () => {
    setError(null);
    setBusy(true);
    try {
      const body: PositionCreateBody = {
        ticker: form.ticker.trim().toUpperCase(),
        structure: form.structure,
        short_strike: parseFloat(form.short_strike),
        long_strike: form.structure === 'put_spread' ? parseFloat(form.long_strike) : undefined,
        expiry: form.expiry,
        contracts: parseInt(form.contracts, 10),
        entry_credit: parseFloat(form.entry_credit),
        entry_commissions: form.entry_commissions ? parseFloat(form.entry_commissions) : 0,
        entry_date: form.entry_date || undefined,
        thesis: form.thesis || undefined,
        deviation_reason: deviationReason || undefined,
      };
      await createPosition(body);
      onDone();
    } catch (e) {
      if (e instanceof JournalApiError && e.status === 422 && e.message.includes('checklist')) {
        setChecklistError(e.message);
      } else {
        setError(e instanceof Error ? e.message : String(e));
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="New Position" onClose={onClose}>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Ticker"><input className={inputCls} value={form.ticker} onChange={set('ticker')} placeholder="AMZN" /></Field>
        <Field label="Structure">
          <select className={inputCls} value={form.structure} onChange={set('structure')}>
            <option value="naked_put">Naked put</option>
            <option value="put_spread">Put credit spread</option>
          </select>
        </Field>
        <Field label="Short strike"><input className={inputCls} type="number" step="0.5" value={form.short_strike} onChange={set('short_strike')} /></Field>
        {form.structure === 'put_spread' && (
          <Field label="Long strike"><input className={inputCls} type="number" step="0.5" value={form.long_strike} onChange={set('long_strike')} /></Field>
        )}
        <Field label="Expiry"><input className={inputCls} type="date" value={form.expiry} onChange={set('expiry')} /></Field>
        <Field label="Contracts"><input className={inputCls} type="number" min="1" value={form.contracts} onChange={set('contracts')} /></Field>
        <Field label="Net credit / share"><input className={inputCls} type="number" step="0.01" value={form.entry_credit} onChange={set('entry_credit')} placeholder="2.00" /></Field>
        <Field label="Commissions ($)"><input className={inputCls} type="number" step="0.01" value={form.entry_commissions} onChange={set('entry_commissions')} placeholder="0" /></Field>
        <Field label="Entry date (default today)"><input className={inputCls} type="date" value={form.entry_date} onChange={set('entry_date')} /></Field>
      </div>
      <div className="mt-3">
        <Field label="Thesis (why this trade)">
          <textarea className={`${inputCls} font-primary`} rows={2} value={form.thesis} onChange={set('thesis')} />
        </Field>
      </div>

      {checklistError && (
        <div className="mt-3 rounded border border-warning/40 bg-surface-alt px-3 py-2.5">
          <p className="text-xs text-warning font-semibold mb-1.5">Entry checklist failed</p>
          <p className="text-[11px] text-txt-secondary mb-2 font-mono">{checklistError}</p>
          <Field label="Deviation reason (journaled with the trade)">
            <input className={inputCls} value={deviationReason} onChange={e => setDeviationReason(e.target.value)}
              placeholder="why you're overriding the checklist" />
          </Field>
        </div>
      )}
      {error && <p className="mt-3 text-xs text-error">{error}</p>}

      <div className="mt-4 flex justify-end gap-2">
        <button onClick={onClose} className="px-3 py-1.5 text-sm text-txt-secondary hover:text-txt">Cancel</button>
        <button onClick={submit} disabled={busy}
          className="px-4 py-1.5 text-sm font-semibold rounded bg-primary text-white hover:opacity-90 disabled:opacity-50">
          {busy ? 'Saving…' : checklistError ? 'Save with deviation' : 'Open position'}
        </button>
      </div>
    </Modal>
  );
}

// ── close form ──────────────────────────────────────────────────────────────
function CloseModal({ position, onDone, onClose }: {
  position: Position; onDone: () => void; onClose: () => void;
}) {
  const [form, setForm] = useState({
    close_debit: '', close_commissions: '', close_date: '',
    exit_reason: 'profit_target', notes: '',
  });
  const [followedPlan, setFollowedPlan] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const submit = async () => {
    setError(null);
    setBusy(true);
    try {
      const body: PositionCloseBody = {
        close_debit: parseFloat(form.close_debit),
        close_commissions: form.close_commissions ? parseFloat(form.close_commissions) : 0,
        close_date: form.close_date || undefined,
        exit_reason: form.exit_reason,
        followed_plan: followedPlan,
        notes: form.notes || undefined,
      };
      await closePosition(position.id, body);
      onDone();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title={`Close ${position.ticker} ${position.short_strike}P`} onClose={onClose}>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Net debit to close / share">
          <input className={inputCls} type="number" step="0.01" value={form.close_debit}
            onChange={set('close_debit')} placeholder="0 = expired worthless" />
        </Field>
        <Field label="Commissions ($)"><input className={inputCls} type="number" step="0.01" value={form.close_commissions} onChange={set('close_commissions')} /></Field>
        <Field label="Close date (default today)"><input className={inputCls} type="date" value={form.close_date} onChange={set('close_date')} /></Field>
        <Field label="Exit reason">
          <select className={inputCls} value={form.exit_reason} onChange={set('exit_reason')}>
            {EXIT_REASONS.map(r => <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>)}
          </select>
        </Field>
      </div>
      <label className="mt-3 flex items-center gap-2 text-sm text-txt-secondary cursor-pointer">
        <input type="checkbox" checked={followedPlan} onChange={e => setFollowedPlan(e.target.checked)} />
        This exit followed the plan-at-entry
      </label>
      <div className="mt-3">
        <Field label="Notes"><textarea className={`${inputCls} font-primary`} rows={2} value={form.notes} onChange={set('notes')} /></Field>
      </div>
      {error && <p className="mt-3 text-xs text-error">{error}</p>}
      <div className="mt-4 flex justify-end gap-2">
        <button onClick={onClose} className="px-3 py-1.5 text-sm text-txt-secondary hover:text-txt">Cancel</button>
        <button onClick={submit} disabled={busy}
          className="px-4 py-1.5 text-sm font-semibold rounded bg-primary text-white hover:opacity-90 disabled:opacity-50">
          {busy ? 'Closing…' : 'Close position'}
        </button>
      </div>
    </Modal>
  );
}

// ── settings card ───────────────────────────────────────────────────────────
function SettingsCard({ settings, onSaved }: { settings: JournalSettings; onSaved: () => void }) {
  const [nav, setNav] = useState(settings.nav?.toString() ?? '');
  const [saved, setSaved] = useState(false);
  const save = async () => {
    await saveJournalSettings({ nav: nav ? parseFloat(nav) : null });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
    onSaved();
  };
  return (
    <div className="flex items-center gap-2 text-xs text-txt-tertiary">
      <span className="font-semibold uppercase tracking-widest text-[10px]">NAV</span>
      <input className={`${inputCls} !w-28 !py-1`} type="number" value={nav}
        onChange={e => setNav(e.target.value)} placeholder="account $" />
      <button onClick={save} className="px-2 py-1 rounded border border-border hover:border-primary text-txt-secondary">
        {saved ? 'Saved ✓' : 'Save'}
      </button>
    </div>
  );
}

// ── main tab ────────────────────────────────────────────────────────────────
export default function JournalTab() {
  const [access, setAccess] = useState<'checking' | 'locked' | 'open'>('checking');
  const [book, setBook] = useState<Position[]>([]);
  const [closed, setClosed] = useState<Position[]>([]);
  const [settings, setSettings] = useState<JournalSettings | null>(null);
  const [entryOpen, setEntryOpen] = useState(false);
  const [closing, setClosing] = useState<Position | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const [b, j, s] = await Promise.all([fetchOpenBook(), fetchJournal(), fetchJournalSettings()]);
      setBook(b.positions);
      setClosed(j.trades);
      setSettings(s);
      setLoadError(null);
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    let alive = true;
    probeJournalAccess()
      .then(ok => {
        if (!alive) return;
        setAccess(ok ? 'open' : 'locked');
        if (ok) reload();
      })
      .catch(() => alive && setAccess('locked'));
    return () => { alive = false; };
  }, [reload]);

  // While locked, re-probe on window focus — so finishing the owner sign-in
  // (a PIN flow in another tab) unlocks this page the moment you come back.
  useEffect(() => {
    if (access !== 'locked') return;
    const recheck = () => {
      probeJournalAccess()
        .then(ok => { if (ok) { setAccess('open'); reload(); } })
        .catch(() => {});
    };
    window.addEventListener('focus', recheck);
    return () => window.removeEventListener('focus', recheck);
  }, [access, reload]);

  if (access === 'checking') {
    return <div className="text-center py-12 text-sm text-txt-tertiary">Checking access…</div>;
  }
  if (access === 'locked') return <LockedCard />;

  const th = 'px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-widest text-txt-tertiary whitespace-nowrap';
  const td = 'px-3 py-2.5 text-sm font-mono whitespace-nowrap';

  return (
    <div className="space-y-5">
      {/* Open book */}
      <div className="bg-surface rounded-lg border border-border overflow-hidden">
        <div className="px-4 sm:px-5 py-3 border-b border-border-subtle flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h2 className="font-secondary text-lg font-medium text-txt">Live Positions</h2>
            <p className="text-[11px] text-txt-tertiary">
              Marked nightly after the 18:30 ET scan · flags cite the strategy rule they come from (hover)
            </p>
          </div>
          <div className="flex items-center gap-3">
            {settings && <SettingsCard settings={settings} onSaved={reload} />}
            <button onClick={() => setEntryOpen(true)}
              className="px-3 py-1.5 text-sm font-semibold rounded bg-primary text-white hover:opacity-90">
              + New position
            </button>
          </div>
        </div>
        {loadError && <p className="px-5 py-3 text-xs text-error">{loadError}</p>}
        {book.length === 0 ? (
          <p className="px-5 py-8 text-sm text-txt-tertiary text-center">
            No open positions — the book is flat.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-border-subtle">
                <tr>
                  <th className={th}>Ticker</th><th className={th}>Structure</th>
                  <th className={th}>Strikes</th><th className={th}>Expiry (DTE)</th>
                  <th className={th}>Qty</th><th className={th}>Credit</th>
                  <th className={th}>Mark</th><th className={th}>Unrl P&L</th>
                  <th className={th}>Capture</th><th className={th}>Flags</th><th className={th}></th>
                </tr>
              </thead>
              <tbody>
                {book.map(p => {
                  const m = p.latest_mark;
                  return (
                    <tr key={p.id} className="border-b border-border-subtle last:border-0">
                      <td className={`${td} font-semibold text-txt`}>{p.ticker}</td>
                      <td className={`${td} text-txt-secondary`}>{p.structure === 'naked_put' ? 'naked put' : 'put spread'}</td>
                      <td className={`${td} text-txt-secondary`}>
                        {p.short_strike}{p.long_strike ? `/${p.long_strike}` : ''}P
                      </td>
                      <td className={`${td} text-txt-secondary`}>
                        {p.expiry} {m?.dte != null && <span className="text-txt-tertiary">({m.dte}d)</span>}
                      </td>
                      <td className={`${td} text-txt-secondary`}>{p.contracts}</td>
                      <td className={`${td} text-txt-secondary`}>{p.entry_credit?.toFixed(2)}</td>
                      <td className={`${td} text-txt-secondary`}>
                        {m?.option_mid != null ? m.option_mid.toFixed(2) : '—'}
                        {m?.mark_source === 'carried' && (
                          <span className="text-warning text-[10px] ml-1" title="carried mark — no fresh quote today">*</span>
                        )}
                      </td>
                      <td className={`${td} font-semibold ${pnlClass(m?.unrealized_pnl)}`}>{fmtMoney(m?.unrealized_pnl)}</td>
                      <td className={`${td} text-txt-secondary`}>{fmtPct(m?.capture_pct)}</td>
                      <td className="px-3 py-2.5">{<FlagChips position={p} />}</td>
                      <td className={td}>
                        <button onClick={() => setClosing(p)}
                          className="px-2 py-1 text-xs rounded border border-border text-txt-secondary hover:border-primary hover:text-txt">
                          Close
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Closed trades */}
      <div className="bg-surface rounded-lg border border-border overflow-hidden">
        <div className="px-4 sm:px-5 py-3 border-b border-border-subtle">
          <h2 className="font-secondary text-lg font-medium text-txt">Trade History</h2>
          <p className="text-[11px] text-txt-tertiary">
            Every trade carries its entry-day signal snapshot (v1 + v2) — analytics land in J2
          </p>
        </div>
        {closed.length === 0 ? (
          <p className="px-5 py-8 text-sm text-txt-tertiary text-center">No closed trades yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-border-subtle">
                <tr>
                  <th className={th}>Ticker</th><th className={th}>Structure</th>
                  <th className={th}>Entry → Close</th><th className={th}>Credit → Debit</th>
                  <th className={th}>Realized P&L</th><th className={th}>Exit</th>
                  <th className={th}>Plan</th>
                </tr>
              </thead>
              <tbody>
                {closed.map(p => (
                  <tr key={p.id} className="border-b border-border-subtle last:border-0">
                    <td className={`${td} font-semibold text-txt`}>{p.ticker}</td>
                    <td className={`${td} text-txt-secondary`}>
                      {p.structure === 'naked_put' ? 'naked put' : 'put spread'} {p.short_strike}{p.long_strike ? `/${p.long_strike}` : ''}P
                    </td>
                    <td className={`${td} text-txt-secondary`}>{p.entry_date} → {p.close_date}</td>
                    <td className={`${td} text-txt-secondary`}>
                      {p.entry_credit?.toFixed(2)} → {p.close_debit?.toFixed(2)}
                    </td>
                    <td className={`${td} font-semibold ${pnlClass(p.realized_pnl)}`}>{fmtMoney(p.realized_pnl, 2)}</td>
                    <td className={`${td} text-txt-secondary`}>{p.exit_reason?.replace(/_/g, ' ') ?? '—'}</td>
                    <td className={td}>
                      {p.followed_plan == null ? <span className="text-txt-tertiary">—</span>
                        : p.followed_plan ? <span className="text-secondary">✓</span>
                        : <span className="text-warning" title="deviated from plan">✗</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {entryOpen && <EntryModal onClose={() => setEntryOpen(false)} onDone={() => { setEntryOpen(false); reload(); }} />}
      {closing && <CloseModal position={closing} onClose={() => setClosing(null)} onDone={() => { setClosing(null); reload(); }} />}
    </div>
  );
}
