import type { RvAccelStatus, V2Eligibility } from '@/lib/types';

/**
 * Shared status badges used by both Leaderboard and DetailPanel — they were
 * duplicated verbatim across the two files (simplify-2026-07-22). Display-only
 * chips, no logic. Phase B's GateBadge lives HERE (built once, imported by both views).
 */

const STATE_ORDER: Record<string, number> = { NORMAL: 0, CAUTION: 1, DANGER: 2 };

/**
 * v2 shadow gate-state chip (Phase B, advisory). MONOCHROME by design — state is
 * conveyed by weight/fill, not hue, so it never competes with v1's colored action
 * chips (v1 stays authoritative until Phase E). Display-only: the gate state + reasons
 * come straight from the API's `eligibility` object; nothing is computed client-side (P1).
 * The tooltip carries the exact ineligibility reasons.
 */
export function GateBadge({ eligibility }: { eligibility?: V2Eligibility | null }) {
  if (!eligibility || !eligibility.gate_state) return null;
  const { gate_state, pending, pending_days, transient, eligible, ineligibility_reasons } = eligibility;

  const stateCls =
    gate_state === 'CAUTION' ? 'bg-surface-alt text-txt border-border-strong'
    : gate_state === 'DANGER' ? 'border-transparent'
    : 'text-txt-tertiary border-border-subtle';           // NORMAL — quiet outline
  const stateStyle = gate_state === 'DANGER'
    ? { background: 'var(--color-txt)', color: 'var(--color-bg)' }   // strongest, monochrome
    : undefined;

  const arrow = pending && pending !== gate_state
    ? ((STATE_ORDER[pending] ?? 0) > (STATE_ORDER[gate_state] ?? 0) ? '↑' : '↓')
    : null;

  const title = eligible
    ? 'v2 shadow gate — ELIGIBLE (advisory; v1 decides)'
    : `v2 shadow gate — ineligible: ${(ineligibility_reasons ?? []).join('; ') || 'gated'}`;

  return (
    <span className="inline-flex items-center gap-1 whitespace-nowrap" title={title}>
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded-full font-primary text-[10px] font-semibold tracking-wide border ${stateCls}`}
        style={stateStyle}
      >
        v2 {gate_state}
      </span>
      {arrow && (
        <span className="font-mono text-[9px] text-txt-tertiary" title={`confirming ${pending} (${pending_days}/2)`}>
          {arrow}{pending_days}/2
        </span>
      )}
      {transient && (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded-full font-primary text-[9px] font-medium border border-border-subtle text-txt-tertiary">
          transient
        </span>
      )}
    </span>
  );
}

export function ThinPremiumBadge({ visible }: { visible: boolean }) {
  if (!visible) return null;
  return (
    <span
      title="VRP ratio just above 1.15 dead zone — premium is thin"
      className="inline-flex items-center px-2 py-0.5 rounded-full font-primary text-[10px] font-semibold tracking-wide border border-warning-30 bg-warning-subtle text-warning whitespace-nowrap"
    >
      Thin Premium
    </span>
  );
}

export function EarningsWarningBadge({
  warning, label, detail,
}: { warning?: string | null; label?: string; detail?: string }) {
  if (!warning || !label) return null;
  return (
    <span
      title={detail || label}
      className="inline-flex items-center px-2 py-0.5 rounded-full font-primary text-[10px] font-semibold tracking-wide border border-warning-30 bg-warning-subtle text-warning whitespace-nowrap"
    >
      {label}
    </span>
  );
}

export function RvAccelStatusChip({ status }: { status?: RvAccelStatus }) {
  // Hide on Excellent / Good / Acceptable; show only on Caution / Avoid-Wait so
  // the signal column stays quiet on clean rows. Display-only; no sizing.
  if (!status) return null;
  if (status.label !== 'Caution' && status.label !== 'Avoid / Wait') return null;
  const isCaution = status.label === 'Caution';
  return (
    <span
      title={`RV Accel — ${status.label}: ${status.description}`}
      className={`inline-flex items-center px-2 py-0.5 rounded-full font-primary text-[10px] font-semibold tracking-wide border ${
        isCaution
          ? 'text-warning bg-warning-subtle border-warning-30'
          : 'text-error bg-error-subtle border-error-20'
      }`}
    >
      RV {status.label}
    </span>
  );
}
