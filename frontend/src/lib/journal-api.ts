/**
 * Trade Journal (J1) — types + fetchers.
 *
 * Every endpoint here sits behind the backend's owner gate (Cloudflare Access
 * JWT / bearer / dev-open) and fails closed with 403. The frontend NEVER holds
 * a credential: in prod the Cloudflare Access cookie rides along on same-origin
 * fetches; locally the backend runs dev-open. A 403 simply means "not the
 * owner" and the UI renders the locked state — the public demo is unaffected.
 *
 * Responses are served snake_case and kept snake_case here (same convention as
 * the MACHINE-view fetchers): what the API says is what you see.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export interface PositionFlag {
  code: string;
  detail: string;
  rule: string;
}

export interface PositionMark {
  position_id: number;
  date: string;
  underlying_close: number | null;
  option_bid: number | null;
  option_ask: number | null;
  option_mid: number | null;
  short_delta: number | null;
  unrealized_pnl: number | null;
  capture_pct: number | null;
  dte: number | null;
  earnings_dte: number | null;
  mark_source: string;
  mark_iv?: number | null;          // per-contract IV (Phase C S3)
}

export interface Position {
  id: number;
  ticker: string;
  structure: 'naked_put' | 'put_spread';
  status: string;
  short_strike: number | null;
  long_strike: number | null;
  expiry: string | null;
  contracts: number | null;
  entry_date: string | null;
  entry_credit: number | null;
  entry_commissions: number | null;
  close_date: string | null;
  close_debit: number | null;
  close_commissions: number | null;
  realized_pnl: number | null;
  entry_spot: number | null;
  entry_iv: number | null;
  entry_sigma_fwd: number | null;
  entry_fvrp: number | null;
  scan_ref: string | null;
  thesis: string | null;
  target_capture: number | null;
  exit_dte_plan: number | null;
  max_loss_plan: number | null;
  checklist_json?: string | null;
  exit_reason: string | null;
  followed_plan: number | null;
  roll_group_id: number | null;
  latest_mark?: PositionMark | null;
  flags?: PositionFlag[];
  marks?: PositionMark[];
  // Phase C sizing snapshot at entry — what v2 recommended vs `contracts` entered
  // (the "size followed?" audit pair). All null for pre-Phase-C entries.
  rec_contracts?: number | null;
  f_star?: number | null;
  dial_R?: number | null;
  dial_O?: number | null;
  margin_per_contract?: number | null;
  binding_cap?: string | null;
}

export interface JournalSettings {
  nav: number | null;
  equity_updated_at?: string | null;
  equity_stale_sessions?: number | null;
  equity_stale?: boolean | null;    // NAV older than the freshness bar -> sizing suspect
  default_target_capture: number;
  default_exit_dte: number;
  default_commission_per_contract: number | null;
}

export interface PositionCreateBody {
  ticker: string;
  structure: 'naked_put' | 'put_spread';
  short_strike: number;
  long_strike?: number | null;
  expiry: string;
  contracts: number;
  entry_date?: string;
  entry_credit: number;
  entry_commissions?: number;
  thesis?: string;
  target_capture?: number;
  exit_dte_plan?: number;
  max_loss_plan?: number;
  deviation_reason?: string;
}

export interface PositionCloseBody {
  close_date?: string;
  close_debit: number;
  close_commissions?: number;
  exit_reason: string;
  followed_plan?: boolean;
  notes?: string;
}

export const EXIT_REASONS = [
  'profit_target', 'time_exit', 'earnings_wall', 'danger_underwater',
  'stop', 'rolled', 'assigned', 'expired', 'discretionary',
] as const;

/** Thrown for non-OK responses; carries status so callers can branch on 403/422. */
export class JournalApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function jfetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch { /* keep statusText */ }
    throw new JournalApiError(res.status, detail);
  }
  return res.json();
}

/** Access probe: true = owner (or dev-open), false = locked (403). */
export async function probeJournalAccess(): Promise<boolean> {
  try {
    await jfetch('/api/positions/open');
    return true;
  } catch (e) {
    if (e instanceof JournalApiError && e.status === 403) return false;
    throw e;
  }
}

export const fetchOpenBook = () =>
  jfetch<{ positions: Position[]; count: number }>('/api/positions/open');

export const fetchPosition = (id: number) => jfetch<Position>(`/api/positions/${id}`);

export const createPosition = (body: PositionCreateBody) =>
  jfetch<Position>('/api/positions', { method: 'POST', body: JSON.stringify(body) });

export const closePosition = (id: number, body: PositionCloseBody) =>
  jfetch<Position>(`/api/positions/${id}/close`, { method: 'POST', body: JSON.stringify(body) });

export const patchPosition = (id: number, body: Partial<PositionCreateBody>) =>
  jfetch<Position>(`/api/positions/${id}`, { method: 'PATCH', body: JSON.stringify(body) });

export const fetchJournal = () =>
  jfetch<{ trades: Position[]; count: number }>('/api/journal');

export const fetchJournalSettings = () => jfetch<JournalSettings>('/api/settings');

export const saveJournalSettings = (body: Partial<JournalSettings>) =>
  jfetch<JournalSettings>('/api/settings', { method: 'PUT', body: JSON.stringify(body) });


/* ── Phase C3: advisory sizing + portfolio stress (owner-gated; server-computed —
      this client renders the arithmetic, it never computes it) ─────────────── */

export interface SizingResult {
  ticker: string; strike: number; premium: number; dte: number;
  spot: number; iv: number;
  equity: number; phi: number;
  kelly: { f_star: number; source: string; n_seed_trades?: number | null;
           n_live_closed?: number | null; seed_generated?: string | null;
           live_path?: string; note?: string };
  dial_R: number; dial_R_driver: string;
  dial_O: number; dial_O_driver: string;
  margin_per_contract: number;
  rec_contracts_raw: number;
  rec_contracts: number;
  binding_cap: string;
  f_star_zero: boolean;
  arithmetic: string;
  incremental_book_stress: number;
  book_notes: string[];
  advisory: string;
}

export interface CapRow {
  cap: string; value: number; limit: number;
  pct_of_limit: number | null; headroom: number; breached: boolean;
}

export interface StressReport {
  equity: number;
  scenarios: {
    severe: { label: string; loss: number; pct_equity: number };
    mild: { label: string; loss: number; pct_equity: number };
  };
  caps: CapRow[];
  per_name: { ticker: string; margin: CapRow; stress: CapRow }[];
  headroom: { ticker: string; more_contracts: number; binding_cap: string }[];
  positions_stressed: number;
  book_notes: string[];
  caveat: string;
}

export const fetchSizing = (ticker: string, strike: number, premium: number, dte: number) =>
  jfetch<SizingResult>(
    `/api/sizing/${encodeURIComponent(ticker)}?strike=${strike}&premium=${premium}&dte=${dte}`);

export const fetchPortfolioStress = () => jfetch<StressReport>('/api/portfolio/stress');

/* Cached owner probe for surfaces OUTSIDE the journal tab (the sizing card on
   candidate rows): probe once per page load, share the promise. */
let _ownerProbe: Promise<boolean> | null = null;
export function ownerAccessCached(): Promise<boolean> {
  if (!_ownerProbe) _ownerProbe = probeJournalAccess().catch(() => false);
  return _ownerProbe;
}
