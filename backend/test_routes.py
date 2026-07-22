"""Route-wiring regression guards.

Born from a real production incident (2026-07-22): the `_cached_scan_response` dedup
refactor left the `@app.get("/api/scan/latest")` decorator on the extracted HELPER instead
of the route handler, so FastAPI treated the helper's `cached: dict` param as a required
request body and every GET returned 422. It passed py_compile + import + all unit tests
because there was no HTTP-level test on the route. These guards close that gap.

Run: python -m pytest test_routes.py -v
"""
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _routes():
    return [(r.path, r.endpoint.__name__) for r in main.app.routes if hasattr(r, "endpoint")]


def test_scan_latest_binds_to_the_handler_not_a_helper():
    """The exact 2026-07-22 bug: the route must resolve to get_latest_cached_scan, not the
    _cached_scan_response builder."""
    bound = [n for p, n in _routes() if p == "/api/scan/latest"]
    assert bound == ["get_latest_cached_scan"], f"/api/scan/latest bound to {bound}"


def test_no_route_is_bound_to_a_private_helper():
    """Generalises the bug class: an @app decorator on a `_`-prefixed helper is almost
    certainly a misplaced decorator, and FastAPI will demand the helper's args as a body."""
    suspicious = [(p, n) for p, n in _routes() if n.startswith("_")]
    assert not suspicious, f"routes bound to private helpers (misplaced decorator?): {suspicious}"


def test_scan_latest_get_is_not_422():
    """A bare GET must succeed (empty ScanResponse when no cache), never 422 'body required'."""
    r = client.get("/api/scan/latest")
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:200]}"
    body = r.json()
    for key in ("tickers", "cached", "regime", "historical"):
        assert key in body, f"ScanResponse missing '{key}'"
    assert isinstance(body["tickers"], list)


def test_health_ok():
    """Smoke: the health route is wired and returns the expected shape."""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json().get("status") in ("ok", "degraded")
