import type { RvAccelStatus } from '@/lib/types';

/**
 * Shared status badges used by both Leaderboard and DetailPanel — they were
 * duplicated verbatim across the two files (simplify-2026-07-22). Display-only
 * chips, no logic. Phase B's GateBadge should join THIS module rather than be
 * copied into each view again.
 */

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
