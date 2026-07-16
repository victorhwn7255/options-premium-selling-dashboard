"""Trade Journal (J1) tests — migration, lifecycle math, auth fail-closed, flags.

Run from backend/:  python3 test_journal.py   (also works under pytest)
Uses a temp DB (database.DB_PATH patched) — never touches the dev/prod DB.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault("JOURNAL_DEV_OPEN", "1")  # HTTP tests run dev-open; auth unit tests flip it

import database  # noqa: E402
import auth  # noqa: E402
import positions_api as papi  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def _ok(label, cond):
    assert cond, f"FAIL {label}"
    print(f"  PASS  {label}")


def _fresh_db(tmpdir: str):
    database.DB_PATH = Path(tmpdir) / "test.db"
    database.TRIAL_REGISTRY_PATH = Path(tmpdir) / "trial_registry.jsonl"
    database.init_db()


def test_migration_idempotent():
    with tempfile.TemporaryDirectory() as td:
        _fresh_db(td)
        database.init_db()  # second run must be a no-op
        conn = database.get_connection()
        pos_cols = {r[1] for r in conn.execute("PRAGMA table_info(positions)")}
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()
        _ok("journal columns on positions",
            {"scan_ref", "thesis", "target_capture", "exit_dte_plan", "checklist_json",
             "exit_reason", "followed_plan", "roll_group_id", "user_id"} <= pos_cols)
        _ok("position_marks + app_settings tables exist",
            {"position_marks", "app_settings"} <= tables)


def test_pure_math():
    _ok("occ symbol format",
        papi.occ_symbol("AMZN", "2026-03-20", "put", 200) == "AMZN260320P00200000")
    _ok("occ fractional strike",
        papi.occ_symbol("SPY", "2026-03-20", "put", 512.5) == "SPY260320P00512500")
    _ok("naked net debit", papi.net_close_debit(1.20, None, "naked_put") == 1.20)
    _ok("spread net debit", papi.net_close_debit(1.20, 0.35, "put_spread") == 0.85)
    _ok("spread needs both mids", papi.net_close_debit(1.20, None, "put_spread") is None)
    _ok("pnl math", papi.position_pnl(2.00, 0.50, 2, commissions=4.0) == 296.0)
    _ok("capture math", papi.capture_pct(2.00, 0.50) == 0.75)


def test_auth_fail_closed():
    class FakeRequest:
        def __init__(self, headers):
            self.headers = headers

    saved = (auth._DEV_OPEN, auth._JOURNAL_TOKEN)
    try:
        auth._DEV_OPEN, auth._JOURNAL_TOKEN = False, ""
        try:
            asyncio.run(auth.require_owner(FakeRequest({})))
            raise AssertionError("expected 403 with no creds configured")
        except HTTPException as e:
            _ok("no creds configured -> 403 (fail closed)", e.status_code == 403)

        auth._JOURNAL_TOKEN = "s3cret"
        try:
            asyncio.run(auth.require_owner(FakeRequest({"Authorization": "Bearer wrong"})))
            raise AssertionError("expected 403 on wrong bearer")
        except HTTPException as e:
            _ok("wrong bearer -> 403", e.status_code == 403)
        asyncio.run(auth.require_owner(FakeRequest({"Authorization": "Bearer s3cret"})))
        _ok("correct bearer -> allowed", True)

        auth._DEV_OPEN = True
        asyncio.run(auth.require_owner(FakeRequest({})))
        _ok("dev-open -> allowed", True)
    finally:
        auth._DEV_OPEN, auth._JOURNAL_TOKEN = saved


def _fake_scan(score=70, regime="NORMAL", ratio=1.3, earn=30):
    return {"scanned_at": "2026-07-16T22:45:00Z", "tickers": [{
        "ticker": "AMZN", "price": 226.0, "iv_current": 44.0, "signal_score": score,
        "recommendation": "SELL PREMIUM" if score >= 65 else "NO EDGE",
        "regime": regime, "vrp": 9.8, "vrp_ratio": ratio, "term_slope": 0.85,
        "rv_acceleration": 0.6, "skew_25d": 0.4, "iv_percentile": 91,
        "earnings_dte": earn, "is_etf": False, "sigma_fwd": 0.34, "fvrp_ratio": 1.28,
        "fvrp_z": 1.4, "slope_1m3m": 1.13, "accel_dn": 0.63,
        "v2_gate_state": "DANGER", "v2_eligible": False,
    }]}


def _client():
    app = FastAPI()
    app.include_router(papi.router)
    return TestClient(app)


def test_lifecycle_http():
    with tempfile.TemporaryDirectory() as td:
        _fresh_db(td)
        auth._DEV_OPEN = True
        papi.get_latest_scan = _fake_scan  # patch module-local symbol
        c = _client()

        body = {"ticker": "AMZN", "structure": "naked_put", "short_strike": 210,
                "expiry": "2026-08-21", "contracts": 2, "entry_credit": 2.00,
                "entry_commissions": 2.6, "entry_date": "2026-07-16"}
        r = c.post("/api/positions", json=body)
        _ok("open position 200", r.status_code == 200)
        pos = r.json()
        _ok("scan_ref attached", pos["scan_ref"] == "2026-07-16T22:45:00Z")
        _ok("entry snapshot fields", pos["entry_iv"] == 44.0 and pos["entry_fvrp"] == 1.28)
        checklist = json.loads(pos["checklist_json"])
        _ok("checklist passes", all(checklist["checks"].values()))
        _ok("v2 opinion captured", checklist["values"]["v2_gate_state"] == "DANGER")

        # marks: store one then verify open-book math and flags
        database.store_position_mark(pos["id"], "2026-07-17", underlying_close=225.0,
                                     option_mid=0.40, unrealized_pnl=320.0,
                                     capture_pct=0.80, dte=35, earnings_dte=30,
                                     mark_source="scan_chain")
        r = c.get("/api/positions/open")
        book = r.json()
        _ok("open book lists it", book["count"] == 1)
        codes = {f["code"] for f in book["positions"][0]["flags"]}
        _ok("PROFIT_TARGET flag at 80% capture", "PROFIT_TARGET" in codes)
        _ok("no TIME_EXIT at 35 dte", "TIME_EXIT" not in codes)

        r = c.post(f"/api/positions/{pos['id']}/close",
                   json={"close_debit": 0.40, "close_commissions": 2.6,
                         "exit_reason": "profit_target", "followed_plan": True,
                         "close_date": "2026-07-17"})
        _ok("close 200", r.status_code == 200)
        closed = r.json()
        # (2.00-0.40)*100*2 - 5.2 = 314.8
        _ok("realized pnl", abs(closed["realized_pnl"] - 314.8) < 1e-6)
        _ok("status closed", closed["status"] == "closed")
        conn = database.get_connection()
        n_tel = conn.execute("SELECT COUNT(*) FROM trades WHERE position_id = ?",
                             (pos["id"],)).fetchone()[0]
        cap = conn.execute("SELECT capture FROM trades WHERE position_id = ?",
                           (pos["id"],)).fetchone()[0]
        conn.close()
        _ok("Module-G telemetry row written", n_tel == 1)
        _ok("telemetry capture", abs(cap - 0.80) < 1e-6)

        r = c.post(f"/api/positions/{pos['id']}/close",
                   json={"close_debit": 0.4, "exit_reason": "profit_target"})
        _ok("double close -> 409", r.status_code == 409)

        r = c.get("/api/journal/analytics")
        a = r.json()
        _ok("analytics overall n=1 win", a["overall"]["n"] == 1 and a["overall"]["win_rate"] == 1.0)
        _ok("analytics regime bucket", a["breakdown"]["by_regime"]["NORMAL"]["n"] == 1)


def test_checklist_gate():
    with tempfile.TemporaryDirectory() as td:
        _fresh_db(td)
        auth._DEV_OPEN = True
        papi.get_latest_scan = lambda: _fake_scan(score=40, regime="CAUTION", ratio=1.0)
        c = _client()
        body = {"ticker": "AMZN", "structure": "naked_put", "short_strike": 210,
                "expiry": "2026-08-21", "contracts": 1, "entry_credit": 1.0}
        r = c.post("/api/positions", json=body)
        _ok("checklist failure without reason -> 422", r.status_code == 422)
        body["deviation_reason"] = "testing a thesis about CAUTION entries"
        r = c.post("/api/positions", json=body)
        _ok("deviation_reason unlocks entry", r.status_code == 200)
        checklist = json.loads(r.json()["checklist_json"])
        _ok("deviation recorded", "CAUTION" in checklist["deviation_reason"])


def test_flags_edges():
    today = date.today()
    pos = {"expiry": (today + timedelta(days=10)).isoformat(), "short_strike": 210,
           "target_capture": 0.75, "exit_dte_plan": 21, "entry_credit": 2.0}
    mark = {"capture_pct": 0.55, "dte": 10, "earnings_dte": 5,
            "underlying_close": 205.0, "short_delta": -0.42, "unrealized_pnl": -100}
    trow = {"regime": "DANGER", "rv_acceleration": 1.2}
    codes = {f["code"] for f in papi.compute_flags(pos, mark, trow)}
    _ok("50% target variant fires under hot accel", "PROFIT_TARGET" in codes)
    _ok("TIME_EXIT at 10 dte", "TIME_EXIT" in codes)
    _ok("EARNINGS_WALL inside hold", "EARNINGS_WALL" in codes)
    _ok("DANGER_UNDERWATER", "DANGER_UNDERWATER" in codes)
    _ok("TESTED via spot<=strike", "TESTED" in codes)

    expired = {"expiry": (today - timedelta(days=1)).isoformat(), "short_strike": 210}
    codes = {f["code"] for f in papi.compute_flags(expired, None, None)}
    _ok("PENDING_SETTLEMENT after expiry", codes == {"PENDING_SETTLEMENT"})


if __name__ == "__main__":
    print("Trade Journal (J1) tests:")
    test_migration_idempotent()
    test_pure_math()
    test_auth_fail_closed()
    test_lifecycle_http()
    test_checklist_gate()
    test_flags_edges()
    print("All journal tests passed.")
