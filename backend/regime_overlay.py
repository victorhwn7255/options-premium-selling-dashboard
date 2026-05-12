"""
Market-wide volatility regime overlay (VIX / VIX3M / VVIX).

Data source: yfinance (`^VIX`, `^VIX3M`, `^VVIX`). When the feed fails
(weekend, network outage, library missing), the overlay returns
`status="UNKNOWN"` with a warning entry. **UNKNOWN does not block CPS
candidates** — but the warning surfaces so the trader can apply their
own judgement.

Status semantics (see references/credit-put-spreads.md §9):

  • DANGER  — VIX > VIX3M  (front backwardation) OR VVIX > VVIX_DANGER
  • CAUTION — VVIX > VVIX_CAUTION but no DANGER trigger
  • NORMAL  — all values present and within bounds
  • UNKNOWN — data unavailable; candidates not blocked

Decoupled from `spread_builder.py` so the same overlay can later be
surfaced by the Naked Puts banner. yfinance is imported lazily inside
the fetcher so unit tests can run without the dependency.
"""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass
from typing import Callable, Optional

import config as cfg
from models import RegimeOverlay

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────
# Pure logic: build an overlay from raw VIX / VIX3M / VVIX values.
# Tests inject values directly; production passes fetched values.
# ────────────────────────────────────────────────────────────────────────

def build_overlay_from_values(
    vix: Optional[float],
    vix3m: Optional[float],
    vvix: Optional[float],
) -> RegimeOverlay:
    """Pure overlay computation. No I/O, fully deterministic.

    Any None input forces `status="UNKNOWN"` with an explicit warning.
    """
    warnings: list[str] = []

    if vix is None or vix3m is None or vvix is None:
        missing = []
        if vix is None: missing.append("^VIX")
        if vix3m is None: missing.append("^VIX3M")
        if vvix is None: missing.append("^VVIX")
        warnings.append(
            f"Regime overlay UNKNOWN — missing {', '.join(missing)}. "
            "Candidates not blocked, but verify manually."
        )
        return RegimeOverlay(
            status="UNKNOWN",
            vix=vix,
            vix3m=vix3m,
            vvix=vvix,
            vix_backwardation=None,
            warnings=warnings,
        )

    vix_backwardation = vix > vix3m

    # DANGER triggers (most restrictive)
    if vix_backwardation:
        warnings.append(
            f"VIX/VIX3M backwardation ({vix:.2f} > {vix3m:.2f}) — "
            "front-end vol fear elevated; new SELL_CPS entries blocked."
        )
    if vvix > cfg.VVIX_DANGER:
        warnings.append(
            f"VVIX {vvix:.1f} > {cfg.VVIX_DANGER:.0f} — vol-of-vol extreme; "
            "new SELL_CPS entries blocked."
        )

    if vix_backwardation or vvix > cfg.VVIX_DANGER:
        status = "DANGER"
    elif vvix > cfg.VVIX_CAUTION:
        status = "CAUTION"
        warnings.append(
            f"VVIX {vvix:.1f} > {cfg.VVIX_CAUTION:.0f} — vol-of-vol elevated; "
            "require stronger setup confirmation."
        )
    else:
        status = "NORMAL"

    return RegimeOverlay(
        status=status,  # type: ignore[arg-type]
        vix=vix,
        vix3m=vix3m,
        vvix=vvix,
        vix_backwardation=vix_backwardation,
        warnings=warnings,
    )


# ────────────────────────────────────────────────────────────────────────
# yfinance fetch — lazy import so tests don't need yfinance installed
# ────────────────────────────────────────────────────────────────────────

@dataclass
class _RawOverlayValues:
    vix: Optional[float]
    vix3m: Optional[float]
    vvix: Optional[float]


def _fetch_last_close(symbol: str) -> Optional[float]:
    """Fetch the most recent close price for a Yahoo ticker. None on failure."""
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        logger.warning("yfinance not installed; regime overlay will return UNKNOWN")
        return None
    try:
        # 5d window covers weekends + thin holiday days
        hist = yf.Ticker(symbol).history(period="5d", auto_adjust=False)
        if hist is None or hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception as e:  # network / parse / unknown
        logger.warning("yfinance fetch failed for %s: %s", symbol, e)
        return None


def fetch_regime_overlay(
    fetcher: Optional[Callable[[str], Optional[float]]] = None,
) -> RegimeOverlay:
    """Fetch the live overlay from yfinance.

    `fetcher` is injectable for testing — defaults to `_fetch_last_close`.
    If any of the three feeds returns None, the overlay falls into UNKNOWN
    and explicitly does NOT pretend the missing data is NORMAL.
    """
    if fetcher is None:
        fetcher = _fetch_last_close

    vix = fetcher("^VIX")
    vix3m = fetcher("^VIX3M")
    vvix = fetcher("^VVIX")

    return build_overlay_from_values(vix=vix, vix3m=vix3m, vvix=vvix)


# ────────────────────────────────────────────────────────────────────────
# VRP z-score helper — pure function, no DB
# (DB-backed variant lives in spread_builder orchestration in Phase 3.)
# ────────────────────────────────────────────────────────────────────────

def compute_vrp_zscore_60d(
    history: list[float],
    current: float,
    min_points: int = 20,
) -> Optional[float]:
    """Rolling 60-day VRP z-score. None when too few points or zero variance.

    Caller is expected to slice the last ~60 trading days of VRP from the
    `daily_iv` table before passing in. We accept any length ≥ min_points
    so partial history doesn't crash on a fresh universe ticker.
    """
    series = [v for v in history if v is not None]
    if len(series) < min_points:
        return None
    if len(series) > 60:
        series = series[-60:]
    try:
        std = statistics.pstdev(series)
    except statistics.StatisticsError:
        return None
    if std == 0:
        return None
    mean = sum(series) / len(series)
    return (current - mean) / std
