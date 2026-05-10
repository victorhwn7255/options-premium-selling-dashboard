#!/usr/bin/env python3
"""
Phase 1 Historical Replay
=========================
Parses history/metrics-logs.md and applies Phase 1 transformations
(VRP-ratio gate, scan-quality detection, suppression) across all scan days
to verify the fixes against expected outcomes documented in the QA report.

Usage:  python scripts/phase1_historical_replay.py
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
from collections import defaultdict


ROOT = Path(__file__).resolve().parents[1]
METRICS_LOG = ROOT / "history" / "metrics-logs.md"

# Import scan-quality thresholds from production code so the replay can never
# silently drift from the live detection rules.
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
from scan_quality import (  # noqa: E402  -- import after sys.path tweak
    SLOPE_WALL_TOLERANCE,
    SLOPE_WALL_THRESHOLD,
    NO_DATA_THRESHOLD,
)

# VRP gate (1.15) is hardcoded in backend/scorer.py and Thin Premium bounds
# (1.15, 1.25) in frontend/src/lib/scoring.ts. They aren't exposed as named
# constants in production today.
# TODO: promote these to shared backend constants if thresholds become configurable.
VRP_GATE = 1.15
THIN_LO, THIN_HI = 1.15, 1.25


def parse_metrics_log(path):
    text = path.read_text()
    day_re = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s+\(\w+\)", re.M)
    matches = list(day_re.finditer(text))
    days = []
    for i, m in enumerate(matches):
        date = m.group(1)
        s, e = m.end(), matches[i + 1].start() if i + 1 < len(matches) else len(text)
        days.append((date, parse_table(text[s:e])))
    return days


def parse_table(section):
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if not cells or cells[0] == "Ticker":
            continue
        if len(cells) < 12:
            continue
        try:
            rows.append({
                "ticker": cells[0],
                "score": int(cells[1]),
                "iv": pf(cells[2]),
                "iv_pct": float(cells[3]) if cells[3] != "N/A" else None,
                "rv30": float(cells[4]),
                "vrp": pf(cells[5]),
                "term_slope": float(cells[6]),
                "rv_accel": float(cells[7]),
                "skew": float(cells[8]),
                "earnings": cells[10],
                "regime_col": cells[11],
            })
        except (ValueError, IndexError):
            pass
    return rows


def pf(s):
    if s in {"N/A", "—", "-"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def vrp_ratio(iv, rv30):
    if iv is None or rv30 is None or rv30 == 0:
        return None
    return iv / rv30


def parse_action(regime_col):
    """Returns (action, regime, is_gated)."""
    if regime_col.startswith("Earnings in"):
        return "SKIP", None, True
    m = re.match(r"(.*?)\s*\((\w+)\)", regime_col)
    if not m:
        return "NO EDGE", "NORMAL", False
    label, regime = m.group(1).strip(), m.group(2).strip()
    return label, regime, False


def replay(rows):
    """Apply Phase 1 to a list of parsed rows. Returns (scan_quality, reason, replayed_rows)."""
    n = len(rows)
    no_data = sum(1 for r in rows if r["iv"] is None or "NO DATA" in r["regime_col"])
    if no_data > NO_DATA_THRESHOLD:
        quality = "DEGRADED"
        reason = f"{no_data} of {n} tickers returned NO DATA"
    else:
        wall = sum(
            1 for r in rows
            if r["term_slope"] is not None
            and abs(r["term_slope"] - 1.0) < SLOPE_WALL_TOLERANCE
        )
        if n and wall / n > SLOPE_WALL_THRESHOLD:
            quality = "DEGRADED"
            reason = f"{wall} of {n} tickers show term slope ≈ 1.00 ({wall/n:.0%})"
        else:
            quality = "OK"
            reason = None

    out = []
    for r in rows:
        old_action, regime, gated = parse_action(r["regime_col"])
        new_action = old_action
        # VRP-ratio gate
        ratio = vrp_ratio(r["iv"], r["rv30"])
        gate_fired = False
        if not gated and old_action in ("SELL", "CONDITIONAL") and ratio is not None and ratio < VRP_GATE:
            new_action = "WATCHLIST"
            gate_fired = True
        # Scan-quality suppression
        suppressed = False
        if quality == "DEGRADED" and new_action in ("SELL", "CONDITIONAL", "WATCHLIST"):
            new_action = "NO EDGE"
            suppressed = True
        # Thin Premium
        thin = (
            new_action == "CONDITIONAL"
            and ratio is not None
            and THIN_LO <= ratio < THIN_HI
        )
        out.append({
            **r,
            "vrp_ratio": ratio,
            "old_action": old_action,
            "new_action": new_action,
            "regime": regime,
            "gated": gated,
            "gate_fired": gate_fired,
            "suppressed": suppressed,
            "thin_premium": thin,
        })
    return quality, reason, out


def main():
    days = parse_metrics_log(METRICS_LOG)
    replayed = [(d, *replay(rows)) for d, rows in days]

    # Section A: VRP gate transitions
    print("\n## Section A: VRP gate transitions (SELL/CONDITIONAL → WATCHLIST)")
    print(f"{'Date':<12} {'Ticker':<6} {'Old':<11} {'New':<10} {'Score':>5} {'IV':>6} {'RV30':>6} {'Ratio':>6}")
    for date, q, reason, rows in replayed:
        for r in rows:
            if r["gate_fired"]:
                print(f"{date:<12} {r['ticker']:<6} {r['old_action']:<11} {r['new_action']:<10} "
                      f"{r['score']:>5} {r['iv']:>6.2f} {r['rv30']:>6.2f} {r['vrp_ratio']:>6.3f}")
    transitions = sum(1 for d, q, _, rs in replayed for r in rs if r["gate_fired"])
    print(f"Total VRP-gate transitions: {transitions}")

    # Section B: Preserved expectations
    print("\n## Section B: Preserved candidates")
    expectations = [
        ("2026-05-08", "JNJ", "CONDITIONAL"),
        ("2026-05-08", "WMT", "SKIP"),
        ("2026-05-04", "WMT", "SELL"),
        ("2026-04-27", "WMT", "SELL"),
    ]
    for date_t, ticker_t, expected in expectations:
        for date, q, _, rows in replayed:
            if date != date_t:
                continue
            for r in rows:
                if r["ticker"] == ticker_t:
                    ratio_str = f"{r['vrp_ratio']:.3f}" if r["vrp_ratio"] else "N/A"
                    ok = r["new_action"] == expected
                    flag = "OK" if ok else "MISMATCH"
                    print(f"  [{flag:>8}] {date} {ticker_t:<5} expected={expected} got={r['new_action']} "
                          f"(score={r['score']} ratio={ratio_str})")

    # Section C: Thin Premium rows
    print("\n## Section C: Thin Premium rows")
    print(f"{'Date':<12} {'Ticker':<6} {'Score':>5} {'Ratio':>6} {'Action':<12} ThinPremium")
    thin_count = 0
    for date, q, _, rows in replayed:
        for r in rows:
            if r["thin_premium"]:
                thin_count += 1
                print(f"{date:<12} {r['ticker']:<6} {r['score']:>5} {r['vrp_ratio']:>6.3f} "
                      f"{r['new_action']:<12} YES")
    print(f"Total Thin Premium rows: {thin_count}")

    # Section D: Degraded scans
    print("\n## Section D: Degraded scan days")
    print(f"{'Date':<12} {'Quality':<9} {'NO DATA':>8} {'Wall':>5} {'Total':>5}  Reason")
    for date, q, reason, rows in replayed:
        no_data = sum(1 for r in rows if r["iv"] is None or "NO DATA" in r["regime_col"])
        wall = sum(
            1 for r in rows
            if r["term_slope"] is not None
            and abs(r["term_slope"] - 1.0) < SLOPE_WALL_TOLERANCE
        )
        if q == "DEGRADED":
            print(f"{date:<12} {q:<9} {no_data:>8} {wall:>5} {len(rows):>5}  {reason}")
    deg_days = sum(1 for d, q, _, _ in replayed if q == "DEGRADED")
    print(f"Total degraded days: {deg_days}")

    # Section E: Suppression impact
    print("\n## Section E: Suppression impact (degraded scans)")
    for date, q, _, rows in replayed:
        if q != "DEGRADED":
            continue
        suppressed_rows = [r for r in rows if r["suppressed"]]
        avoid_preserved = [r for r in rows if r["new_action"] == "AVOID"]
        no_data_preserved = [r for r in rows if r["new_action"] == "NO DATA"]
        print(f"\n{date}: {len(suppressed_rows)} suppressed, "
              f"{len(avoid_preserved)} AVOID preserved, "
              f"{len(no_data_preserved)} NO DATA preserved")
        for r in suppressed_rows:
            print(f"  {r['ticker']:<5} was {r['old_action']:<11} → NO EDGE  (score {r['score']} preserved)")

    # Section F: Daily action counts
    print("\n## Section F: Daily action counts (after Phase 1)")
    print(f"{'Date':<12} {'Quality':<9} {'SELL':>4} {'COND':>4} {'WATCH':>5} {'SKIP':>4} {'AVOID':>5} {'NOEDG':>5} {'NODAT':>5}")
    for date, q, _, rows in replayed:
        c = defaultdict(int)
        for r in rows:
            c[r["new_action"]] += 1
        print(f"{date:<12} {q:<9} {c['SELL']:>4} {c['CONDITIONAL']:>4} {c['WATCHLIST']:>5} "
              f"{c['SKIP']:>4} {c['AVOID']:>5} {c['NO EDGE']:>5} {c['NO DATA']:>5}")

    # Section G: Unexpected changes
    print("\n## Section G: Unexpected SELL/CONDITIONAL downgrades")
    bad = []
    for date, q, _, rows in replayed:
        if q == "DEGRADED":
            continue
        for r in rows:
            if (r["old_action"] in ("SELL", "CONDITIONAL")
                    and r["new_action"] not in ("SELL", "CONDITIONAL")
                    and r["vrp_ratio"] is not None
                    and r["vrp_ratio"] >= VRP_GATE):
                bad.append((date, r))
    if bad:
        for date, r in bad:
            print(f"  {date} {r['ticker']}: {r['old_action']} → {r['new_action']} ratio={r['vrp_ratio']:.3f}")
    else:
        print("  (none — all SELL/CONDITIONAL with vrp_ratio≥1.15 preserved)")


if __name__ == "__main__":
    main()
