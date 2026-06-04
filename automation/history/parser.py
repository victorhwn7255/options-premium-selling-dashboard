"""Read helpers for the history markdown files: find the last-logged date, parse a prior
NP table for day-over-day deltas, and slice the latest N entries for Claude context.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

# Same pattern as backend/import_metrics_log.py:33
DATE_HEADING = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\b")


def _headings(text: str) -> list[tuple[int, str]]:
    """Return [(line_index, iso_date)] for every dated entry heading, top to bottom."""
    out = []
    for i, line in enumerate(text.splitlines()):
        m = DATE_HEADING.match(line)
        if m:
            out.append((i, m.group(1)))
    return out


def last_logged_date(path: str | Path) -> date | None:
    text = Path(path).read_text()
    hs = _headings(text)
    return date.fromisoformat(hs[0][1]) if hs else None


def has_entry(path: str | Path, iso_date: str) -> bool:
    pat = re.compile(rf"^##\s+{re.escape(iso_date)}\b", re.M)
    return bool(pat.search(Path(path).read_text()))


def latest_entries(path: str | Path, n: int = 7) -> str:
    """Raw text of the top-N dated entries (from the 1st heading up to just before the (n+1)th)."""
    text = Path(path).read_text()
    lines = text.splitlines()
    hs = _headings(text)
    if not hs:
        return ""
    start = hs[0][0]
    end = hs[n][0] if len(hs) > n else len(lines)
    return "\n".join(lines[start:end]).rstrip("\n")


def _num(cell: str):
    cell = cell.strip()
    if cell in ("", "N/A", "—", "TBD"):
        return None
    try:
        return float(cell)
    except ValueError:
        return None


def entry_text(path: str | Path, iso_date: str) -> str | None:
    """Return the full text of one dated entry (heading through just before its closing ---)."""
    text = Path(path).read_text()
    lines = text.splitlines()
    hs = _headings(text)
    idx = next((i for i, (_, d) in enumerate(hs) if d == iso_date), None)
    if idx is None:
        return None
    start = hs[idx][0]
    end = hs[idx + 1][0] if idx + 1 < len(hs) else len(lines)
    return "\n".join(lines[start:end]).rstrip("\n")


def parse_np_table(path: str | Path, iso_date: str) -> dict[str, dict] | None:
    """Parse the NP metrics table for a given date into {ticker: {score, iv, rv30, vrp,
    term_slope, rv_accel, skew}}. Returns None if that date's entry isn't present."""
    text = Path(path).read_text()
    lines = text.splitlines()
    hs = _headings(text)
    idx = next((i for i, (_, d) in enumerate(hs) if d == iso_date), None)
    if idx is None:
        return None
    start = hs[idx][0]
    end = hs[idx + 1][0] if idx + 1 < len(hs) else len(lines)
    out: dict[str, dict] = {}
    for line in lines[start:end]:
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 12 or cells[0] in ("Ticker",) or cells[0].startswith("--"):
            continue
        out[cells[0]] = {
            "score": int(_num(cells[1])) if _num(cells[1]) is not None else None,
            "iv": _num(cells[2]),
            "iv_pct": _num(cells[3]),
            "rv30": _num(cells[4]),
            "vrp": _num(cells[5]),
            "term_slope": _num(cells[6]),
            "rv_accel": _num(cells[7]),
            "skew": _num(cells[8]),
        }
    return out or None
