"""Number formatting helpers that match JavaScript's Number.prototype.toFixed /
Math.round semantics (round-half-away-from-zero), so Python output byte-matches
the dashboard's clipboard strings.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def fixed(x, n: int) -> str | None:
    """Equivalent of JS `x.toFixed(n)` (half-away-from-zero). Returns None if x is None."""
    if x is None:
        return None
    q = Decimal(1).scaleb(-n)  # 10**-n  (Decimal('1'), '0.1', '0.01', ...)
    # Decimal(x) (not str(x)) uses the exact IEEE-754 binary value, matching how JS
    # toFixed rounds the underlying double (e.g. 27.65 is really 27.6499… → "27.6").
    return str(Decimal(x).quantize(q, rounding=ROUND_HALF_UP))


def round_half_up(x) -> int:
    """Equivalent of JS `Math.round(x)` for the values we use (non-negative scores)."""
    return int(Decimal(x).quantize(Decimal(1), rounding=ROUND_HALF_UP))
