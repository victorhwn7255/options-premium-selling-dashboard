"""Trial registry — the P2 mechanism, made real (spec Module E2 / Module F).

Append-only JSONL at ``database.TRIAL_REGISTRY_PATH`` (created empty by ``init_db``; never
truncated). Every backtest / research run in the Signal-Quality Program is *registered here
before it runs* (``registered_before_run: true``) and records its result afterwards. The
deflated-Sharpe hurdle rises with the count of trials that have run, adopted or not.

Row = spec E2 verbatim ``{id, date, hypothesis, config_hash, data_window,
registered_before_run, result_summary, adopted}`` plus additive fields:
``acceptance`` (the pre-registered pass rule), ``run_dates`` (list), ``notes``, ``event``
(``register`` | ``result``). Results are appended as NEW rows carrying the same ``id`` — the
latest row for an id is its current state; nothing is ever rewritten.

``config_hash`` ties a registration/result to the exact ``[PROVISIONAL]`` set it ran under
(sha256 of the golden-master CONFIG). Adoption (``adopted: true``) is only ever written after the
user's sign-off in ``references/change-logs.md`` — this module never decides it.

CLI (run on the box so the hash is prod's CONFIG):
    python trial_registry.py register-program        # the four Signal-Quality Program trials
    python trial_registry.py register --id X --hypothesis "..." --window "..." --acceptance "..."
    python trial_registry.py result --id X --summary "..." [--adopted] [--run-date YYYY-MM-DD]
    python trial_registry.py list
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

import database as db
import theta_core as tc

E2_FIELDS = ("id", "date", "hypothesis", "config_hash", "data_window",
             "registered_before_run", "result_summary", "adopted")

# The Signal-Quality Program's pre-registrations (text is the contract — see
# tasks/signal-quality/ws0-trial-registry.md and the P1–P5 table in 00-index.md).
PROGRAM_TRIALS: list[dict] = [
    {
        "id": "T1-2026-09-fvrp-denominator",
        "hypothesis": ("Confirmatory (Module F T1). On ticker-days where IV/sigma_fwd and IV/RV30 "
                       "disagree on eligibility, the forecast denominator has >= 0 net expectancy "
                       "difference on a standardized 20-delta put with current exit rules, and a "
                       "lower false-block rate in post-spike windows."),
        "data_window": "2025-02-11 -> run date; sigma_fwd recomputed walk-forward (monthly refits)",
        "acceptance": ("Adopt the forecast denominator iff point estimate >= 0 AND post-spike "
                       "false-block rate falls (spec Module F verbatim). Secondary, signal-level: "
                       "E[capture_30d] on each side of the disagreement set, block-bootstrap by month."),
    },
    {
        "id": "X1-2026-09-index-sleeve-replay",
        "hypothesis": ("Exploratory (scenario CV). The v2 veto layer (G3/G4/G5 + market-term proxy "
                       "VIX/VIX3M + VVIX overlay + G6 macro window) would have avoided >= 80% of the "
                       "index-sleeve tail loss (loss-weighted recall) across 2018-02, 2018-Q4, 2020-03, "
                       "2022, 2024-08 and 2025-04, while clearing >= 50% of win days outside events "
                       "and releasing after each trough."),
        "data_window": "2016-07-07 -> run date; SPY/QQQ/IWM (+GLD) on VIX/VXN/RVX (+GVZ) IV proxies",
        "acceptance": ("P1 pooled loss-weighted recall >= 0.80 with one-sided 90% block-bootstrap "
                       "(by month) lower bound >= 0.70. P2 per-event >= 0.50 in >= 5 of 6 AND >= 0.70 "
                       "in both 2020-03 and 2022. P3 outside-event win-day clearance >= 0.50; any single "
                       "gate vetoing > 40% of outside-event win days is a calibration flag, not a design "
                       "fail. P4 post-trough 30-session win-day clearance >= 0.50 in >= 4 of 6. P5 v2 "
                       "any-veto pooled recall >= v1 live index vetoes (rv-accel > 1.10, VIX > VIX3M, "
                       "VVIX > 130, negative trailing VRP) on the same days. Confirmed by user 2026-09-03."),
    },
    {
        "id": "X2-2026-09-single-name-screens",
        "hypothesis": ("Exploratory. Top-quintile iv_hv1y_rank and capture_mom_rank ticker-days carry "
                       "higher capture_30d than bottom-quintile, concentrated in high-IV regimes "
                       "(iv_percentile >= 70)."),
        "data_window": "2025-02-11 -> run date (resolved capture rows); rerun monthly as the sample grows",
        "acceptance": ("Quintile spread (top - bottom) > 0 with block-bootstrap (by month) p < 0.10 "
                       "over >= 60 resolved sessions, per sleeve. Telemetry-only until then."),
    },
    {
        "id": "X3-2026-09-g6-macro-window",
        "hypothesis": ("Exploratory. Index-sleeve |return| and negative-jump incidence are elevated "
                       "inside the G6 window (FOMC/CPI/NFP, g6_pre_days before through the event day) "
                       "versus outside, 2016 -> 2026."),
        "data_window": "2016-07-07 -> run date; FOMC full history, CPI/NFP where the calendar covers",
        "acceptance": ("Ratio of mean s_neg inside/outside the window > 1 with p < 0.10 -> evidence for "
                       "keeping G6 advisory-on; otherwise G6 stays in CONFIG but is reported as unsupported."),
    },
]


def _path() -> Path:
    # Read at call time so tests can monkeypatch database.TRIAL_REGISTRY_PATH.
    return Path(db.TRIAL_REGISTRY_PATH)


def config_hash() -> str:
    """sha256 (first 16 hex) of the golden-master CONFIG — the [PROVISIONAL] set a trial ran under."""
    blob = json.dumps(tc.CONFIG, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def _read_rows() -> list[dict]:
    p = _path()
    if not p.exists():
        return []
    rows = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _append(row: dict) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def latest(trial_id: str) -> dict | None:
    """Current state of a trial (its most recent row), or None if never registered."""
    cur = None
    for r in _read_rows():
        if r.get("id") == trial_id:
            cur = r
    return cur


def list_trials() -> list[dict]:
    """One entry per id (latest row), in first-registration order."""
    order: list[str] = []
    state: dict[str, dict] = {}
    for r in _read_rows():
        i = r.get("id")
        if i not in state:
            order.append(i)
        state[i] = r
    return [state[i] for i in order]


def dsr_hurdle_n() -> int:
    """Number of trials that have run at least once — the deflated-Sharpe trial count N."""
    return sum(1 for t in list_trials() if t.get("run_dates"))


def register(trial_id: str, hypothesis: str, data_window: str, acceptance: str,
             notes: str = "", today: str | None = None) -> dict:
    """Pre-register a trial. Idempotent for an identical payload; a *different* payload under an
    existing id is refused (registrations are immutable — use a new id)."""
    cur = latest(trial_id)
    if cur is not None:
        same = (cur.get("hypothesis"), cur.get("data_window"), cur.get("acceptance")) == \
               (hypothesis, data_window, acceptance)
        if same:
            return cur
        raise ValueError(f"trial {trial_id!r} is already registered with a different payload; "
                         f"registrations are immutable — register a new id")
    row = {
        "id": trial_id,
        "date": today or date.today().isoformat(),
        "hypothesis": hypothesis,
        "config_hash": config_hash(),
        "data_window": data_window,
        "registered_before_run": True,
        "result_summary": None,
        "adopted": False,
        "acceptance": acceptance,
        "run_dates": [],
        "notes": notes,
        "event": "register",
    }
    _append(row)
    return row


def record_result(trial_id: str, result_summary: str, adopted: bool = False,
                  run_date: str | None = None, notes: str | None = None,
                  today: str | None = None) -> dict:
    """Append a result row for a registered trial (refused if the id was never registered)."""
    cur = latest(trial_id)
    if cur is None:
        raise KeyError(f"trial {trial_id!r} is not registered — register before running (P2)")
    today = today or date.today().isoformat()
    row = dict(cur)
    row.update({
        "date": today,
        "config_hash": config_hash(),
        "result_summary": result_summary,
        "adopted": bool(adopted),
        "run_dates": list(cur.get("run_dates") or []) + [run_date or today],
        "event": "result",
    })
    if notes is not None:
        row["notes"] = notes
    _append(row)
    return row


def register_program() -> list[dict]:
    """Register the Signal-Quality Program's four trials (idempotent)."""
    return [register(t["id"], t["hypothesis"], t["data_window"], t["acceptance"])
            for t in PROGRAM_TRIALS]


def _main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Append-only trial registry (spec E2).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("register-program", help="register the four Signal-Quality Program trials")
    r = sub.add_parser("register")
    r.add_argument("--id", required=True); r.add_argument("--hypothesis", required=True)
    r.add_argument("--window", required=True); r.add_argument("--acceptance", required=True)
    r.add_argument("--notes", default="")
    s = sub.add_parser("result")
    s.add_argument("--id", required=True); s.add_argument("--summary", required=True)
    s.add_argument("--adopted", action="store_true"); s.add_argument("--run-date", default=None)
    s.add_argument("--notes", default=None)
    sub.add_parser("list")
    a = ap.parse_args(argv)

    if a.cmd == "register-program":
        for row in register_program():
            print(f"registered {row['id']}  hash={row['config_hash']}  runs={len(row['run_dates'])}")
    elif a.cmd == "register":
        row = register(a.id, a.hypothesis, a.window, a.acceptance, notes=a.notes)
        print(json.dumps(row, indent=2, sort_keys=True))
    elif a.cmd == "result":
        row = record_result(a.id, a.summary, adopted=a.adopted, run_date=a.run_date, notes=a.notes)
        print(json.dumps(row, indent=2, sort_keys=True))
    elif a.cmd == "list":
        for t in list_trials():
            print(f"{t['id']:<40} runs={len(t.get('run_dates') or []):<2} adopted={t.get('adopted')!s:<5} "
                  f"hash={t.get('config_hash')}  {t.get('date')}")
        print(f"DSR hurdle N = {dsr_hurdle_n()}  (path: {_path()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
