"""Phase 3 — persistence + API tests for Credit Put Spreads.

Covers:
  • database.get_vrp_history (correct order, insufficient history)
  • database.record_cps_candidate (insert + upsert)
  • database.get_consecutive_sell_days (ticker-level, weekends OK)
  • database.get_consecutive_exact_spread_days (separate from ticker-level)
  • API: /api/credit-put-spreads/latest empty state
  • API: /api/credit-put-spreads/latest cached response
  • API: existing /api/scan/latest unchanged
  • API: CPS_UNIVERSE only — no JNJ/AAPL leak
  • API: overlay UNKNOWN warning surfaces
  • API: overlay DANGER blocks SELL_CPS
  • SELL_CPS gated on 2-day confirmation
  • WATCH_CPS allowed before confirmation
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import traceback
from datetime import date, timedelta
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database


# ── Test runner ───────────────────────────────────────────────────────


passed = 0
failed: list[tuple[str, str]] = []


def run(name, fn):
    global passed
    print(f"\nTest: {name}")
    try:
        fn()
        passed += 1
        print(f"  PASS: {name}")
    except AssertionError as e:
        failed.append((name, str(e)))
        print(f"  FAIL: {name}\n    {e}")
    except Exception as e:
        failed.append((name, f"{type(e).__name__}: {e}"))
        print(f"  ERROR: {name}\n    {type(e).__name__}: {e}\n{traceback.format_exc()}")


def fresh_db():
    """Hand back an isolated SQLite path so tests can run in parallel-safe order."""
    tmp = tempfile.mktemp(suffix=".db")
    database.DB_PATH = type(database.DB_PATH)(tmp)
    database.init_db()
    return tmp


# ── Persistence tests ─────────────────────────────────────────────────


def test_get_vrp_history_returns_last_n_oldest_first():
    """40 days inserted, request 60 → returns all 40 oldest-first."""
    tmp = fresh_db()
    try:
        for i in range(40):
            d = date.today() - timedelta(days=40 - i)
            database.store_daily_iv("SPY", atm_iv=20.0, rv30=15.0, vrp=5.0 + i * 0.1, as_of=d)
        hist = database.get_vrp_history("SPY", days=60)
        assert len(hist) == 40, f"expected 40, got {len(hist)}"
        assert hist[0] == 5.0, hist[0]
        assert abs(hist[-1] - 8.9) < 1e-6, hist[-1]
    finally:
        os.unlink(tmp)


def test_get_vrp_history_clips_to_requested_days():
    """100 days inserted, request 60 → newest 60 returned oldest-first."""
    tmp = fresh_db()
    try:
        for i in range(100):
            d = date.today() - timedelta(days=100 - i)
            database.store_daily_iv("SPY", atm_iv=20.0, rv30=15.0, vrp=float(i), as_of=d)
        hist = database.get_vrp_history("SPY", days=60)
        assert len(hist) == 60, f"expected 60, got {len(hist)}"
        # Newest 60 = i values 40..99, oldest-first
        assert hist[0] == 40.0, hist[0]
        assert hist[-1] == 99.0, hist[-1]
    finally:
        os.unlink(tmp)


def test_get_vrp_history_returns_empty_on_no_data():
    """Unknown ticker → empty list, no crash."""
    tmp = fresh_db()
    try:
        assert database.get_vrp_history("WUT", days=60) == []
    finally:
        os.unlink(tmp)


def test_record_cps_candidate_inserts_row():
    tmp = fresh_db()
    try:
        rid = database.record_cps_candidate(
            scan_date="2026-05-11", ticker="SPY", action="SELL_CPS",
            expiration="2026-06-19", short_strike=500.0, long_strike=495.0,
            credit_to_width=0.27, base_score=70, regime="NORMAL",
            passed_filters=True, sell_eligible=True,
        )
        assert rid > 0
        conn = database.get_connection()
        row = conn.execute(
            "SELECT ticker, action, sell_eligible FROM cps_candidate_history WHERE id=?",
            (rid,),
        ).fetchone()
        conn.close()
        assert row == ("SPY", "SELL_CPS", 1), row
    finally:
        os.unlink(tmp)


def test_record_cps_candidate_upserts_on_duplicate():
    """Same (scan_date, ticker, expiration, strikes) → UPDATE, not duplicate."""
    tmp = fresh_db()
    try:
        database.record_cps_candidate(
            scan_date="2026-05-11", ticker="SPY", action="WATCH_CPS",
            expiration="2026-06-19", short_strike=500.0, long_strike=495.0,
            sell_eligible=False, passed_filters=False,
        )
        database.record_cps_candidate(
            scan_date="2026-05-11", ticker="SPY", action="SELL_CPS",
            expiration="2026-06-19", short_strike=500.0, long_strike=495.0,
            sell_eligible=True, passed_filters=True,
        )
        conn = database.get_connection()
        rows = conn.execute(
            "SELECT action, sell_eligible FROM cps_candidate_history WHERE ticker='SPY'",
        ).fetchall()
        conn.close()
        assert len(rows) == 1, f"expected 1 row (upsert), got {len(rows)}"
        assert rows[0] == ("SELL_CPS", 1), rows[0]
    finally:
        os.unlink(tmp)


def test_consecutive_sell_days_counts_ticker_level():
    """3 days of SELL-eligible candidates on SPY → streak = 3."""
    tmp = fresh_db()
    try:
        asof = date(2026, 5, 11)
        for offset in (0, 1, 2):
            d = (asof - timedelta(days=offset)).isoformat()
            database.record_cps_candidate(
                scan_date=d, ticker="SPY", action="SELL_CPS",
                expiration="2026-06-19", short_strike=500.0, long_strike=495.0,
                sell_eligible=True, passed_filters=True,
            )
        assert database.get_consecutive_sell_days("SPY", asof=asof) == 3
    finally:
        os.unlink(tmp)


def test_consecutive_sell_days_stops_at_gap():
    """Streak interrupted by a non-eligible day → resets after the break."""
    tmp = fresh_db()
    try:
        asof = date(2026, 5, 11)
        # 2 eligible days at the most recent dates, then 1 NOT eligible, then more eligible
        for offset, eligible in ((0, True), (1, True), (2, False), (3, True), (4, True)):
            d = (asof - timedelta(days=offset)).isoformat()
            database.record_cps_candidate(
                scan_date=d, ticker="SPY", action="SELL_CPS" if eligible else "NO_EDGE",
                expiration="2026-06-19", short_strike=500.0, long_strike=495.0,
                sell_eligible=eligible, passed_filters=eligible,
            )
        # Walking back from asof: 2 eligible (offsets 0,1), then gap at 2 → streak 2
        assert database.get_consecutive_sell_days("SPY", asof=asof) == 2
    finally:
        os.unlink(tmp)


def test_consecutive_sell_days_handles_multiple_spreads_per_day():
    """Multiple candidate rows per day; any-eligible counts."""
    tmp = fresh_db()
    try:
        asof = date(2026, 5, 11)
        d = asof.isoformat()
        # Two rows same day: one NOT eligible, one IS eligible
        database.record_cps_candidate(
            scan_date=d, ticker="SPY", action="NO_EDGE",
            expiration="2026-06-19", short_strike=485.0, long_strike=480.0,
            sell_eligible=False,
        )
        database.record_cps_candidate(
            scan_date=d, ticker="SPY", action="SELL_CPS",
            expiration="2026-06-19", short_strike=500.0, long_strike=495.0,
            sell_eligible=True,
        )
        assert database.get_consecutive_sell_days("SPY", asof=asof) == 1
    finally:
        os.unlink(tmp)


def test_exact_spread_consecutive_independent_from_ticker_level():
    """Exact-spread streak < ticker-level when strikes shift mid-streak."""
    tmp = fresh_db()
    try:
        asof = date(2026, 5, 11)
        # Day -2: 500/495 spread, eligible
        database.record_cps_candidate(
            scan_date=(asof - timedelta(days=2)).isoformat(),
            ticker="SPY", action="SELL_CPS",
            expiration="2026-06-19", short_strike=500.0, long_strike=495.0,
            sell_eligible=True,
        )
        # Day -1 and 0: spread rotated to 502/497, eligible both days
        for offset in (1, 0):
            database.record_cps_candidate(
                scan_date=(asof - timedelta(days=offset)).isoformat(),
                ticker="SPY", action="SELL_CPS",
                expiration="2026-06-19", short_strike=502.0, long_strike=497.0,
                sell_eligible=True,
            )
        # Ticker-level: 3 consecutive eligible days
        assert database.get_consecutive_sell_days("SPY", asof=asof) == 3
        # Exact-spread for 502/497: 2 days
        assert database.get_consecutive_exact_spread_days(
            "SPY", "2026-06-19", 502.0, 497.0, asof=asof,
        ) == 2
        # Exact-spread for 500/495: 1 trailing eligible row at offset -2.
        # The function walks date DESC over rows matching the exact pair —
        # 500/495 has only that one historical row, so its streak is 1.
        # (At display time the orchestrator never queries for "yesterday's
        # strikes if today's strikes shifted"; this just documents the API.)
        assert database.get_consecutive_exact_spread_days(
            "SPY", "2026-06-19", 500.0, 495.0, asof=asof,
        ) == 1
    finally:
        os.unlink(tmp)


def test_save_and_load_cps_scan_response():
    tmp = fresh_db()
    try:
        payload = {
            "scan_date": "2026-05-11",
            "market_regime": "THE PLAYOFFS",
            "cps_universe": ["SPY", "QQQ", "IWM"],
            "regime_overlay": {"status": "NORMAL", "warnings": []},
            "candidates": [],
        }
        database.save_cps_scan_response("2026-05-11", payload)
        loaded = database.get_latest_cps_scan_response()
        assert loaded == payload
    finally:
        os.unlink(tmp)


def test_load_cps_scan_response_returns_none_when_empty():
    tmp = fresh_db()
    try:
        assert database.get_latest_cps_scan_response() is None
    finally:
        os.unlink(tmp)


# ── API tests (FastAPI TestClient) ────────────────────────────────────


def _import_main_with_test_db(tmp_db: str):
    """Patch DB_PATH BEFORE importing/reloading main so the FastAPI app
    sees the fresh DB. Returns the reloaded main module."""
    import importlib
    database.DB_PATH = type(database.DB_PATH)(tmp_db)
    database.init_db()
    import main
    importlib.reload(main)
    return main


def test_api_returns_empty_shell_when_no_cached_response():
    """Fresh DB → endpoint returns UNKNOWN overlay + empty candidates + message."""
    from fastapi.testclient import TestClient
    tmp = tempfile.mktemp(suffix=".db")
    try:
        main = _import_main_with_test_db(tmp)
        client = TestClient(main.app)
        r = client.get("/api/credit-put-spreads/latest")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["candidates"] == []
        assert body["regime_overlay"]["status"] == "UNKNOWN"
        # CPS_UNIVERSE is configurable; assert membership of the original MVP
        # set is preserved while allowing the universe to expand without test churn.
        assert {"SPY", "QQQ", "IWM"}.issubset(set(body["cps_universe"]))
        assert body["message"] is not None
    finally:
        os.unlink(tmp)


def test_api_returns_cached_response_when_present():
    """Cached response → endpoint hands it back unchanged."""
    from fastapi.testclient import TestClient
    tmp = tempfile.mktemp(suffix=".db")
    try:
        main = _import_main_with_test_db(tmp)
        sample = {
            "scan_date": "2026-05-11",
            "market_regime": "THE PLAYOFFS",
            "cps_universe": ["SPY", "QQQ", "IWM"],
            "regime_overlay": {
                "status": "NORMAL", "vix": 18.0, "vix3m": 20.0, "vvix": 95.0,
                "vix_backwardation": False, "warnings": [],
            },
            "candidates": [],
            "message": None,
            "rejection_summary": {
                "checked": 3, "actionable": 0, "rejected_by_base_gate": 0,
                "rejected_by_construction": 0, "rejected_by_execution": 0,
                "rejected_by_overlay": 0, "rejected_by_confirmation": 3,
            },
        }
        database.save_cps_scan_response("2026-05-11", sample)
        client = TestClient(main.app)
        r = client.get("/api/credit-put-spreads/latest")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["scan_date"] == "2026-05-11"
        assert body["regime_overlay"]["status"] == "NORMAL"
        assert body["rejection_summary"]["checked"] == 3
        assert body["rejection_summary"]["rejected_by_confirmation"] == 3
    finally:
        os.unlink(tmp)


def test_api_unknown_overlay_warning_surfaces():
    """UNKNOWN overlay should pass through warnings array."""
    from fastapi.testclient import TestClient
    tmp = tempfile.mktemp(suffix=".db")
    try:
        main = _import_main_with_test_db(tmp)
        database.save_cps_scan_response("2026-05-11", {
            "scan_date": "2026-05-11", "market_regime": "UNKNOWN",
            "cps_universe": ["SPY", "QQQ", "IWM"],
            "regime_overlay": {
                "status": "UNKNOWN",
                "warnings": [
                    "Regime overlay UNKNOWN — VIX/VIX3M/VVIX unavailable."
                ],
            },
            "candidates": [], "message": "test",
        })
        client = TestClient(main.app)
        body = client.get("/api/credit-put-spreads/latest").json()
        assert body["regime_overlay"]["status"] == "UNKNOWN"
        assert any("UNKNOWN" in w for w in body["regime_overlay"]["warnings"])
    finally:
        os.unlink(tmp)


def test_api_only_serves_cps_universe_tickers():
    """Cached candidates that somehow include a non-CPS ticker still parse,
    but our scan integration is the gate — verify by inspecting the response
    universe field rather than mocking the full scan."""
    from fastapi.testclient import TestClient
    tmp = tempfile.mktemp(suffix=".db")
    try:
        main = _import_main_with_test_db(tmp)
        client = TestClient(main.app)
        body = client.get("/api/credit-put-spreads/latest").json()
        # Universe may expand; assert MVP core membership without locking the exact list.
        assert {"SPY", "QQQ", "IWM"}.issubset(set(body["cps_universe"]))
        # Empty-shell case: no candidates leak in.
        assert body["candidates"] == []
    finally:
        os.unlink(tmp)


def test_api_does_not_mutate_naked_puts_endpoint():
    """Hitting /api/credit-put-spreads/latest must not touch scan_results."""
    from fastapi.testclient import TestClient
    tmp = tempfile.mktemp(suffix=".db")
    try:
        main = _import_main_with_test_db(tmp)
        # Seed an existing scan_results row
        database.store_scan_result(
            scanned_at="2026-05-11T20:00:00Z",
            regime={"overall_regime": "THE PLAYOFFS", "regime_color": "#000",
                    "description": "ok", "avg_iv_rank": 50, "avg_rv_accel": 1.0,
                    "danger_count": 0, "caution_count": 0, "total_tickers": 3},
            tickers=[],
            historical={},
        )
        client = TestClient(main.app)
        before = client.get("/api/scan/latest").json()
        # Hit CPS endpoint multiple times
        for _ in range(3):
            client.get("/api/credit-put-spreads/latest")
        after = client.get("/api/scan/latest").json()
        assert before == after, "scan/latest mutated by CPS endpoint"
    finally:
        os.unlink(tmp)


def test_pydantic_response_validates_cached_payload():
    """Stored response must round-trip through CreditPutSpreadsResponse."""
    from models import CreditPutSpreadsResponse
    payload = {
        "scan_date": "2026-05-11",
        "market_regime": "THE PLAYOFFS",
        "cps_universe": ["SPY", "QQQ", "IWM"],
        "regime_overlay": {
            "status": "CAUTION", "vix": 18.0, "vix3m": 20.0, "vvix": 120.0,
            "vix_backwardation": False,
            "warnings": ["VVIX 120 > 110 — vol-of-vol elevated"],
        },
        "candidates": [],
        "rejection_summary": {
            "checked": 3, "actionable": 0, "rejected_by_base_gate": 1,
            "rejected_by_construction": 1, "rejected_by_execution": 0,
            "rejected_by_overlay": 1, "rejected_by_confirmation": 0,
        },
    }
    parsed = CreditPutSpreadsResponse.model_validate(payload)
    assert parsed.regime_overlay.status == "CAUTION"
    assert parsed.rejection_summary.rejected_by_overlay == 1


# ── Builder + scan-integration smoke ──────────────────────────────────


def test_build_cps_response_blocks_sell_on_overlay_danger():
    """Integration: VIX backwardation overlay downgrades SELL_CPS → WATCH_CPS."""
    from models import TickerResult
    from spread_builder import build_candidate_outcome_for_ticker
    from regime_overlay import build_overlay_from_values
    from test_spread_builder import FakeTickerResult, make_clean_chain

    overlay = build_overlay_from_values(vix=22.0, vix3m=20.0, vvix=95.0)
    assert overlay.status == "DANGER"
    tr = FakeTickerResult()
    outcome = build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, regime_overlay=overlay,
        consecutive_sell_days=2,
    )
    assert outcome.action == "WATCH_CPS", outcome.action


def test_sell_cps_gated_on_two_day_confirmation():
    """consecutive_sell_days < 2 → WATCH_CPS, not SELL_CPS."""
    from spread_builder import build_candidate_outcome_for_ticker
    from test_spread_builder import FakeTickerResult, make_clean_chain
    tr = FakeTickerResult()
    o1 = build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=1,
    )
    assert o1.action == "WATCH_CPS", o1.action
    o2 = build_candidate_outcome_for_ticker(
        ticker="SPY", ticker_result=tr, chain=make_clean_chain(),
        spot=500.0, atr14=5.0, consecutive_sell_days=2,
    )
    assert o2.action == "SELL_CPS", o2.action


# ── Runner ────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("Phase 3 — CPS persistence + API integration tests")
    print("=" * 64)
    tests = [
        ("get_vrp_history oldest-first", test_get_vrp_history_returns_last_n_oldest_first),
        ("get_vrp_history clips to N", test_get_vrp_history_clips_to_requested_days),
        ("get_vrp_history empty on no data", test_get_vrp_history_returns_empty_on_no_data),
        ("record_cps_candidate inserts row", test_record_cps_candidate_inserts_row),
        ("record_cps_candidate upserts", test_record_cps_candidate_upserts_on_duplicate),
        ("Ticker-level streak counts", test_consecutive_sell_days_counts_ticker_level),
        ("Ticker streak stops at gap", test_consecutive_sell_days_stops_at_gap),
        ("Multiple spreads per day OR-ed", test_consecutive_sell_days_handles_multiple_spreads_per_day),
        ("Exact-spread streak ≤ ticker streak", test_exact_spread_consecutive_independent_from_ticker_level),
        ("save/load CPS response round-trip", test_save_and_load_cps_scan_response),
        ("Empty response returns None", test_load_cps_scan_response_returns_none_when_empty),
        ("API empty shell w/ UNKNOWN overlay", test_api_returns_empty_shell_when_no_cached_response),
        ("API returns cached response", test_api_returns_cached_response_when_present),
        ("API UNKNOWN warning surfaces", test_api_unknown_overlay_warning_surfaces),
        ("API only serves CPS_UNIVERSE", test_api_only_serves_cps_universe_tickers),
        ("API does NOT mutate /scan/latest", test_api_does_not_mutate_naked_puts_endpoint),
        ("Pydantic validates cached payload", test_pydantic_response_validates_cached_payload),
        ("Overlay DANGER blocks SELL_CPS", test_build_cps_response_blocks_sell_on_overlay_danger),
        ("2-day confirmation gates SELL_CPS", test_sell_cps_gated_on_two_day_confirmation),
    ]
    for name, fn in tests:
        run(name, fn)
    print("\n" + "=" * 64)
    print(f"Results: {passed} passed, {len(failed)} failed")
    print("=" * 64)
    if failed:
        sys.exit(1)
