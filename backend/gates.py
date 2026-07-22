"""Phase B — v2 eligibility orchestration.

App-level glue between the theta_core gate/eligibility primitives and the scan.
Extracted from ``main._compute_v2_shadow`` (Phase B, 2026-07-22) so the seven-condition
eligibility decision (strategy §3) and its human-readable reasons are unit-testable in
isolation instead of buried in the scan loop.

Advisory only: v1 remains authoritative until Phase E. **No thresholds live here** — they
all come from ``theta_core.CONFIG`` (P3). The ``theta_core.GateState`` state machine
(golden-master-guarded) is untouched; this module only orchestrates around it and owns no
I/O (the caller seeds/persists gate state).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import theta_core as tc


@dataclass
class Eligibility:
    """The v2 eligibility verdict for one ticker-day (pure result, no I/O)."""
    gate_state: str
    transient: bool
    pending: str | None
    pending_days: int
    eligible: bool
    ineligibility_reasons: list[str] = field(default_factory=list)
    # live-v1 earnings parity — feeds shadow divergence classification so that a name
    # both engines gate on earnings reads AGREE, not a false V2_STRICTER.
    v1_earnings_gated: bool = False


def resolve_earnings_gate(is_etf: bool, earnings_dte: int | None) -> tuple[bool, bool, bool]:
    """G1 earnings (ETF-exempt) → ``(v1_gated, v2_gated, unverified)``.

    v1 gates a DATED non-ETF within ``g1_earnings_gate_days`` (mirrors the live
    ``scoring.ts`` SKIP). v2 hardens with the D4 fallback: a single name with **no
    verified date** is gated too (live-v1 only warns) — that difference is a genuine
    V2_STRICTER, not a shadow artifact.
    """
    if is_etf:
        return False, False, False
    if earnings_dte is None:
        return False, True, True                       # D4: unverified → v2 gates, v1 warns
    if earnings_dte <= tc.CONFIG["g1_earnings_gate_days"]:
        return True, True, False                       # dated in-window → both gate
    return False, False, False


def evaluate_eligibility(gs: "tc.GateState", *, is_etf: bool,
                         fvrp_ratio: float | None, abs_premium_volpts: float | None,
                         earnings_dte: int | None, accel_dn: float,
                         slope_1m3m: float | None, book_frozen: bool = False) -> Eligibility:
    """Seven-condition entry eligibility (strategy §3) + reasons for one ticker-day.

    ``gs`` is a POST-update ``theta_core.GateState`` — the caller applies the transition
    (it owns the DB seed/persist); this function is otherwise pure.

    ``book_frozen`` is the G5 portfolio-regime freeze. The seam is threaded here (G5 is one
    of the seven conditions) but the caller currently passes ``False``; its computation
    (index FVRP < 1.0, or global-vol-factor 20-session z > 2 — spec §4 G5) is wired in a
    follow-up. The default keeps behavior identical to the pre-extraction inline path.
    """
    dead_zone = tc.CONFIG["dead_zone_index"] if is_etf else tc.CONFIG["dead_zone_single"]
    v1_gated, v2_gated, unverified = resolve_earnings_gate(is_etf, earnings_dte)

    reasons: list[str] = []
    if book_frozen:
        reasons.append("book freeze (G5 — portfolio regime)")
    if unverified:
        reasons.append("earnings_unverified (no date — G1/D4 gated)")
    elif v2_gated:
        reasons.append(f"gate G1 earnings (in {earnings_dte}d)")

    eligible = False
    if fvrp_ratio is None:
        reasons.append("no FVRP (chain/forecast unavailable)")
    else:
        eligible = (not book_frozen) and gs.entry_eligible(
            fvrp_ratio, dead_zone,
            abs_premium_volpts if abs_premium_volpts is not None else 0.0,
            earnings_clear=not v2_gated)
        if fvrp_ratio < 1.0:
            reasons.append(f"FVRP {fvrp_ratio:.2f} < 1.0 (neg fwd-VRP)")
        elif fvrp_ratio < dead_zone:
            reasons.append(f"FVRP {fvrp_ratio:.2f} < {dead_zone:.2f} dead zone")
        if abs_premium_volpts is not None and abs_premium_volpts < tc.CONFIG["abs_premium_floor_volpts"]:
            reasons.append(f"abs premium {abs_premium_volpts:.1f} < {tc.CONFIG['abs_premium_floor_volpts']} vol pts")
        if gs.state != "NORMAL":
            reasons.append(f"gate {gs.state} (accel_dn {accel_dn:.2f}"
                           + (f", slope {slope_1m3m:.2f})" if slope_1m3m is not None else ")"))
        if gs.transient or gs._blackout > 0:
            reasons.append("transient blackout")

    return Eligibility(
        gate_state=gs.state, transient=gs.transient, pending=gs._pending,
        pending_days=gs._pending_days, eligible=eligible,
        ineligibility_reasons=reasons, v1_earnings_gated=v1_gated)
