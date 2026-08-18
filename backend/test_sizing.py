"""Phase C3 sizing-engine tests — Kelly provenance, wiring math, BSM stress hand-calc,
caps reject-not-trim, f*=0 pathway, snapshot round-trip, equity freshness.

Run from backend/:  python3 test_sizing.py   (also works under pytest)
Uses a temp DB (database.DB_PATH patched) — never touches the dev/prod DB.
The `claude`/network layer is never involved; everything here is hermetic.
"""
from __future__ import annotations

import json
import math
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault("JOURNAL_DEV_OPEN", "1")

import database  # noqa: E402
import positions_api as papi  # noqa: E402
import sizing  # noqa: E402
import theta_core as tc  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from scipy.stats import norm  # noqa: E402


def _ok(label, cond):
    assert cond, f"FAIL {label}"
    print(f"  PASS  {label}")


def _fresh_db(tmpdir: str):
    database.DB_PATH = Path(tmpdir) / "test.db"
    database.TRIAL_REGISTRY_PATH = Path(tmpdir) / "trial_registry.jsonl"
    database.init_db()


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(papi.router)
    return TestClient(app)


def _seed_file(td: str, f_star: float, n: int = 100) -> Path:
    p = Path(td) / "kelly_seed.json"
    p.write_text(json.dumps({
        "generated": "2026-08-18", "source": "test", "cohorts": ["SELL"],
        "n_trades": n, "n_months": 12, "f_star_seed": f_star,
        "pnl_per_margin": [0.01] * n, "months": ["2025-01"] * n,
    }))
    return p


def _use_seed(path):
    """Point sizing at a seed file (or None for missing) and drop the cache."""
    sizing.SEED_PATH = Path(path) if path else Path("/nonexistent/kelly_seed.json")
    sizing._seed_cache = None


def _daily_iv_row(ticker="SPY", spot=500.0, atm_iv=20.0, sigma_fwd=0.19,
                  sigma_fwd_dn=0.15, fvrp_z=0.0, iso=None):
    conn = database.get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO daily_iv (ticker, date, atm_iv, spot, sigma_fwd,"
        " sigma_fwd_dn, fvrp_z) VALUES (?,?,?,?,?,?,?)",
        (ticker, iso or date.today().isoformat(), atm_iv, spot, sigma_fwd,
         sigma_fwd_dn, fvrp_z))
    conn.commit()
    conn.close()


def _set_nav(client, nav=100_000):
    r = client.put("/api/settings", json={"nav": nav})
    assert r.status_code == 200, r.text


# ── 1. Kelly provenance ─────────────────────────────────────────────────────
def test_kelly_sources():
    with tempfile.TemporaryDirectory() as td:
        _fresh_db(td)
        _use_seed(_seed_file(td, 0.42))
        k = sizing.kelly_f_star()
        _ok("seed present -> source=seed, f* from artifact",
            k["source"] == "seed" and k["f_star"] == 0.42)
        _use_seed(None)
        k = sizing.kelly_f_star()
        _ok("seed missing -> cold-start floor",
            k["source"] == "floor" and k["f_star"] == tc.CONFIG["kelly_cold_start_floor"])


# ── 2. Wiring math: margin + contracts formula reproduced by hand ──────────
def test_sizing_arithmetic_hand_calc():
    with tempfile.TemporaryDirectory() as td:
        _fresh_db(td)
        # equity 1M + f* 0.10 sized so NO cap binds (name_stress at 2.5% of 1M = $25k
        # comfortably clears 3 contracts' ~$18.7k stressed loss) — the uncapped path.
        _use_seed(_seed_file(td, 0.10))
        _daily_iv_row()  # single row: median sigma_dn == now -> R = 1; fvrp_z 0 -> O = 1
        client = _client()
        _set_nav(client, 1_000_000)
        r = client.get("/api/sizing/SPY", params={"strike": 460, "premium": 5.0, "dte": 35})
        assert r.status_code == 200, r.text
        d = r.json()
        M = tc.margin_short_put(5.0, 500.0, 460.0)   # hand: 100*max(5+0.2*500-40, 5+46)
        _ok("margin matches hand-calc", abs(d["margin_per_contract"] - round(M, 2)) < 1e-9)
        _ok("R and O neutral on flat context", d["dial_R"] == 1.0 and d["dial_O"] == 1.0)
        expect = int(1_000_000 * 0.25 * 0.10 * 1.0 * 1.0 / M)
        _ok(f"rec_contracts == floor(eq*phi*f*R*O/M) == {expect}",
            d["rec_contracts_raw"] == expect and d["rec_contracts"] == expect)
        _ok("no cap binds at this size/equity", d["binding_cap"] == "none")
        _ok("advisory label present", "advisory" in d and "never places" in d["advisory"])
        _ok("arithmetic string shows every factor", "0.25" in d["arithmetic"])


# ── 3. BSM stress vs independent hand-calc ──────────────────────────────────
def _bsm_put_ref(S, K, sigma, t):
    if t <= 0 or sigma <= 0:
        return max(K - S, 0.0)
    sq = sigma * math.sqrt(t)
    d1 = (math.log(S / K) + 0.5 * sigma * sigma * t) / sq
    d2 = d1 - sq
    return K * norm.cdf(-d2) - S * norm.cdf(-d1)


def test_book_stress_hand_calc():
    with tempfile.TemporaryDirectory() as td:
        _fresh_db(td)
        _use_seed(_seed_file(td, 0.5))
        _daily_iv_row(ticker="GLD", spot=380.0, atm_iv=22.0)
        client = _client()
        _set_nav(client, 100_000)
        pid = client.post("/api/positions", json={
            "ticker": "GLD", "structure": "naked_put", "short_strike": 345,
            "expiry": (date.today() + timedelta(days=60)).isoformat(),
            "contracts": 3, "entry_credit": 2.83,
            "deviation_reason": "test fixture"}).json()["id"]
        database.store_position_mark(pid, date.today().isoformat(),
                                     underlying_close=380.0, option_bid=2.0,
                                     option_ask=2.2, option_mid=2.1, short_delta=-0.15,
                                     unrealized_pnl=219.0, capture_pct=0.258, dte=60,
                                     earnings_dte=None, mark_source="scan_chain")
        r = client.get("/api/portfolio/stress")
        assert r.status_code == 200, r.text
        d = r.json()
        # independent reprice: iv from daily_iv (0.22), spot from the mark (380)
        c = tc.CONFIG
        t_now, t_str = 60 / 252, (60 - c["stress_days_elapsed"]) / 252
        px_now = _bsm_put_ref(380.0, 345.0, 0.22, t_now)
        px_str = _bsm_put_ref(380.0 * c["stress_spot_mult"], 345.0,
                              0.22 * c["stress_iv_mult"], t_str)
        expect_loss = (px_str - px_now) * 100 * 3
        got = d["scenarios"]["severe"]["loss"]
        _ok(f"severe stress loss matches independent BSM ({expect_loss:,.0f})",
            abs(got - expect_loss) < 0.05)
        _ok("mild scenario present and smaller",
            0 < d["scenarios"]["mild"]["loss"] < got)
        _ok("five cap surfaces present",
            {c2["cap"] for c2 in d["caps"]} == {"book_stress", "margin_util", "notional"}
            and d["per_name"][0]["margin"]["cap"] == "name_margin"
            and d["per_name"][0]["stress"]["cap"] == "name_stress")
        _ok("verbatim caveat rendered", d["caveat"].startswith("convention, not a worst case"))
        _ok("headroom names a binding cap or none",
            d["headroom"][0]["binding_cap"] in
            {"none", "book_stress_cap", "margin_cap", "name_margin_cap",
             "name_stress_cap", "notional_cap"})


# ── 4. Caps reject, never trim ──────────────────────────────────────────────
def test_caps_reject_not_trim():
    with tempfile.TemporaryDirectory() as td:
        _fresh_db(td)
        _use_seed(_seed_file(td, 0.80))
        _daily_iv_row()  # SPY 500, R=O=1
        client = _client()
        _set_nav(client, 100_000)
        # premium 5, strike 460 -> M = $10,500; raw rec = floor(20000/10500) = 1... make raw
        # bigger: f=0.8 -> floor(100000*0.25*0.8/M). Choose strike 490 (otm 10):
        # M = 100*max(5+100-10, 5+49) = 9500 -> raw = 2. name_margin cap 8% = 8000 -> even
        # n=1 (9500) breaches name_margin_cap -> largest compliant 0, cap named.
        r = client.get("/api/sizing/SPY", params={"strike": 490, "premium": 5.0, "dte": 35})
        d = r.json()
        _ok("raw recommendation computed before caps", d["rec_contracts_raw"] >= 1)
        _ok("cap rejected to the largest compliant size (0 here), cap NAMED",
            d["rec_contracts"] == 0 and d["binding_cap"] == "name_margin_cap")
        _ok("arithmetic string names the binding cap", "name_margin_cap" in d["arithmetic"])
        # now a compliant-at-lower-n case: equity 1M, M=$9,500 -> raw 21. Walking down,
        # the name-STRESS cap (2.5% of 1M = $25k) binds first: a 490-strike put stressed
        # {-20%, IVx2, +5d} loses ~$8.16k/contract -> 3 pass ($24.5k), 4 breach.
        _set_nav(client, 1_000_000)
        d = client.get("/api/sizing/SPY",
                       params={"strike": 490, "premium": 5.0, "dte": 35}).json()
        _ok("walks down to largest compliant (3), not silent 0 / not raw 21",
            d["rec_contracts_raw"] == 21 and d["rec_contracts"] == 3
            and d["binding_cap"] == "name_stress_cap")


# ── 5. f*=0 is a surfaced signal, not a silent zero ─────────────────────────
def test_f_star_zero_pathway():
    with tempfile.TemporaryDirectory() as td:
        _fresh_db(td)
        _use_seed(_seed_file(td, 0.0))
        _daily_iv_row()
        client = _client()
        _set_nav(client, 100_000)
        d = client.get("/api/sizing/SPY",
                       params={"strike": 460, "premium": 5.0, "dte": 35}).json()
        _ok("f*=0 -> rec 0 with explicit flag",
            d["rec_contracts"] == 0 and d["f_star_zero"] is True)
        _ok("kelly provenance says seed", d["kelly"]["source"] == "seed")


# ── 6. Snapshot round-trip + equity freshness + gating ──────────────────────
def test_snapshot_and_equity_freshness():
    with tempfile.TemporaryDirectory() as td:
        _fresh_db(td)
        _use_seed(_seed_file(td, 0.5))
        client = _client()
        # sizing before NAV -> 409, not a silent default
        _daily_iv_row()
        r = client.get("/api/sizing/SPY", params={"strike": 460, "premium": 5, "dte": 35})
        _ok("sizing without NAV -> 409", r.status_code == 409)
        _set_nav(client, 250_000)
        s = client.get("/api/settings").json()
        _ok("nav PUT stamps equity_updated_at (today, fresh)",
            s["equity_updated_at"] == date.today().isoformat()
            and s["equity_stale_sessions"] == 0 and s["equity_stale"] is False)
        database.set_setting("equity_updated_at",
                             (date.today() - timedelta(days=14)).isoformat())
        s = client.get("/api/settings").json()
        _ok("2-week-old equity flagged stale",
            s["equity_stale"] is True and s["equity_stale_sessions"] >= 8)
        # snapshot round-trip
        pid = client.post("/api/positions", json={
            "ticker": "SPY", "structure": "naked_put", "short_strike": 460,
            "expiry": (date.today() + timedelta(days=45)).isoformat(),
            "contracts": 3, "entry_credit": 5.0, "deviation_reason": "test",
            "rec_contracts": 2, "f_star": 0.5, "dial_R": 1.0, "dial_O": 1.1,
            "margin_per_contract": 10500.0, "binding_cap": "none"}).json()["id"]
        row = client.get(f"/api/positions/{pid}").json()
        _ok("sizing snapshot persisted (size-followed audit source)",
            row["rec_contracts"] == 2 and row["f_star"] == 0.5
            and row["binding_cap"] == "none" and row["contracts"] == 3)


# ── 7. The real shipped seed artifact ───────────────────────────────────────
def test_real_seed_artifact():
    p = Path(__file__).parent / "kelly_seed.json"
    _ok("kelly_seed.json shipped next to sizing.py", p.exists())
    seed = json.loads(p.read_text())
    _ok("seed carries >= 1000 SELL+COND trades",
        seed["n_trades"] >= 1000 and seed["cohorts"] == ["SELL", "COND"])
    _ok("f_star_seed pinned at 0.0 (the honest 2026-08 verdict: disaster injection "
        "dominates the thin backtest mean — revisit via Phase-F trials, not by editing)",
        seed["f_star_seed"] == 0.0)
    _ok("arrays consistent", len(seed["pnl_per_margin"]) == seed["n_trades"]
        and len(seed["months"]) == seed["n_trades"])


if __name__ == "__main__":
    print("Sizing tests:")
    test_kelly_sources()
    test_sizing_arithmetic_hand_calc()
    test_book_stress_hand_calc()
    test_caps_reject_not_trim()
    test_f_star_zero_pathway()
    test_snapshot_and_equity_freshness()
    test_real_seed_artifact()
    print("All sizing tests passed.")
