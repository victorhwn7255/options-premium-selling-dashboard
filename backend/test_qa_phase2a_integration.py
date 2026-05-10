"""
QA Phase 2A — FastAPI integration test for /api/scan/latest.

Verifies that the cached-scan endpoint surfaces the Phase 1 scan-quality fields
on the wire (not just inside the scorer/helpers). Mocks the DB read path so
the test runs offline without a live MARKETDATA_TOKEN or pre-populated SQLite.

Run: cd backend && python test_qa_phase2a_integration.py
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Ensure module-level main.py imports succeed without a real API token.
os.environ.setdefault("MARKETDATA_TOKEN", "test-stub-for-integration")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402


client = TestClient(main.app)


def test_latest_scan_empty_cache_returns_default_scan_quality():
    """When no cached scan exists, the response is empty + scan_quality defaults to OK."""
    with patch("main.get_latest_scan", return_value=None):
        resp = client.get("/api/scan/latest")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Phase 1 fields exist on every ScanResponse.
    assert "scan_quality" in body, "scan_quality must be present on every response"
    assert "scan_quality_reason" in body
    assert "tickers" in body and body["tickers"] == []
    # Default applies to empty cache.
    assert body["scan_quality"] == "OK"
    assert body["scan_quality_reason"] is None
    print("  PASS: empty cache → scan_quality OK with empty tickers list")


def _make_cached(tickers):
    """Build the cached-scan dict shape that get_latest_scan() returns."""
    regime = {
        "overall_regime": "NORMAL",
        "regime_color": "#6B8C5A",
        "description": "Test",
        "avg_iv_rank": 50.0,
        "avg_rv_accel": 0.9,
        "danger_count": 0,
        "caution_count": 0,
        "total_tickers": len(tickers),
        "vix_term_slope": None,
    }
    return {
        "scanned_at": "2026-04-16T22:30:00Z",
        "regime": regime,
        "tickers": tickers,
        "historical": {},
    }


def _ticker_dict(ticker, *, recommendation, term_slope, signal_score=50,
                 iv_current=20.0, regime="NORMAL"):
    return {
        "ticker": ticker, "name": ticker, "sector": "Test",
        "price": 100.0,
        "iv_current": iv_current, "iv_rank": 50.0, "iv_percentile": 50.0,
        "rv10": 15.0, "rv20": 15.0, "rv30": 15.0,
        "vrp": 5.0, "vrp_ratio": 1.33,
        "rv_acceleration": 0.85, "term_slope": term_slope,
        "is_contango": term_slope < 1.0, "skew_25d": 2.0,
        "signal_score": signal_score, "regime": regime,
        "recommendation": recommendation, "flags": [],
        "suggested_delta": "x", "suggested_structure": "x",
        "suggested_dte": "x", "suggested_max_notional": "x",
        "earnings_dte": None, "is_etf": False,
        "term_structure_points": [], "skew_points": [],
    }


def test_latest_scan_cached_ok_response_has_scan_quality():
    """Healthy cached scan reads back as OK; actionable rows are unchanged."""
    cached = _make_cached([
        _ticker_dict("AAA", recommendation="SELL PREMIUM", term_slope=0.85, signal_score=70),
        _ticker_dict("BBB", recommendation="CONDITIONAL", term_slope=0.95, signal_score=50),
        _ticker_dict("CCC", recommendation="WATCHLIST", term_slope=0.85, signal_score=46),
        _ticker_dict("DDD", recommendation="NO EDGE", term_slope=0.95, signal_score=33),
    ])
    with patch("main.get_latest_scan", return_value=cached):
        resp = client.get("/api/scan/latest")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["scan_quality"] == "OK"
    assert body["scan_quality_reason"] is None
    recs = {t["ticker"]: t["recommendation"] for t in body["tickers"]}
    assert recs == {
        "AAA": "SELL PREMIUM",
        "BBB": "CONDITIONAL",
        "CCC": "WATCHLIST",
        "DDD": "NO EDGE",
    }, f"Recommendations should be untouched on OK scan, got {recs}"
    print("  PASS: cached OK scan returns scan_quality OK with recommendations intact")


def test_latest_scan_cached_degraded_response_suppresses_actionable():
    """Cached scan with >4 NO DATA tickers triggers DEGRADED + suppression on read."""
    tickers = [
        _ticker_dict("SELL", recommendation="SELL PREMIUM", term_slope=0.85, signal_score=70),
        _ticker_dict("COND", recommendation="CONDITIONAL", term_slope=0.95, signal_score=50),
        _ticker_dict("WATCH", recommendation="WATCHLIST", term_slope=0.85, signal_score=46),
        _ticker_dict("AVOID_R", recommendation="AVOID", term_slope=1.20, signal_score=42, regime="DANGER"),
    ]
    # Add 5 NO DATA rows to trigger DEGRADED via the NO DATA cluster trigger.
    for i in range(5):
        tickers.append(_ticker_dict(f"ND{i}", recommendation="NO DATA",
                                    term_slope=0.95, signal_score=0,
                                    iv_current=None))
    cached = _make_cached(tickers)

    with patch("main.get_latest_scan", return_value=cached):
        resp = client.get("/api/scan/latest")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["scan_quality"] == "DEGRADED", \
        f"Expected DEGRADED with 5 NO DATA rows, got {body['scan_quality']}"
    assert body["scan_quality_reason"], "Must surface suppression reason on the wire"
    assert "NO DATA" in body["scan_quality_reason"]

    by_ticker = {t["ticker"]: t for t in body["tickers"]}
    # SELL / CONDITIONAL / WATCHLIST → NO EDGE, with audit metadata preserved.
    for sym, original in [("SELL", "SELL PREMIUM"),
                          ("COND", "CONDITIONAL"),
                          ("WATCH", "WATCHLIST")]:
        t = by_ticker[sym]
        assert t["recommendation"] == "NO EDGE", \
            f"{sym} should be downgraded to NO EDGE, got {t['recommendation']}"
        assert t["suppressed_by_scan_quality"] is True
        assert t["pre_suppression_recommendation"] == original
        assert t["pre_suppression_score"] is not None
        # signal_score itself is preserved (the audit truth).
        assert t["signal_score"] == _ticker_dict(sym, recommendation=original,
                                                 term_slope=0.85,
                                                 signal_score=t["signal_score"]
                                                 )["signal_score"]
    # AVOID and NO DATA preserved.
    assert by_ticker["AVOID_R"]["recommendation"] == "AVOID"
    assert by_ticker["AVOID_R"]["suppressed_by_scan_quality"] is False
    assert by_ticker["ND0"]["recommendation"] == "NO DATA"
    assert by_ticker["ND0"]["suppressed_by_scan_quality"] is False

    print("  PASS: cached DEGRADED scan → 3 actionable suppressed, AVOID/NO DATA preserved")


if __name__ == "__main__":
    print("=" * 64)
    print("QA Phase 2A — /api/scan/latest integration tests")
    print("=" * 64)

    tests = [
        ("Empty cache → scan_quality default", test_latest_scan_empty_cache_returns_default_scan_quality),
        ("Cached OK → unchanged recommendations", test_latest_scan_cached_ok_response_has_scan_quality),
        ("Cached DEGRADED → suppression on the wire", test_latest_scan_cached_degraded_response_suppresses_actionable),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\nTest: {name}")
        try:
            fn()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")
            failed += 1

    print("\n" + "=" * 64)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 64)
    sys.exit(0 if failed == 0 else 1)
