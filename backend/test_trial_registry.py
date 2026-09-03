"""Trial registry (WS0) — append-only JSONL, fold-by-id, refusals, hash stability.

Run:  cd backend && python -m pytest test_trial_registry.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import database
import trial_registry as tr


@pytest.fixture()
def registry(tmp_path, monkeypatch):
    p = tmp_path / "trial_registry.jsonl"
    monkeypatch.setattr(database, "TRIAL_REGISTRY_PATH", p)
    return p


def _lines(p: Path) -> list[str]:
    return [l for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def test_register_writes_e2_row(registry):
    row = tr.register("T-test", "h", "w", "acc", notes="n", today="2026-09-03")
    assert set(tr.E2_FIELDS) <= set(row)
    assert row["registered_before_run"] is True and row["adopted"] is False
    assert row["result_summary"] is None and row["run_dates"] == [] and row["event"] == "register"
    assert row["config_hash"] == tr.config_hash() and len(row["config_hash"]) == 16
    assert len(_lines(registry)) == 1 and json.loads(_lines(registry)[0])["id"] == "T-test"


def test_register_is_idempotent_and_immutable(registry):
    tr.register("T-test", "h", "w", "acc")
    tr.register("T-test", "h", "w", "acc")                 # identical payload → no-op
    assert len(_lines(registry)) == 1
    with pytest.raises(ValueError):
        tr.register("T-test", "h CHANGED", "w", "acc")     # different payload → refused
    assert len(_lines(registry)) == 1


def test_result_requires_registration_and_appends(registry):
    with pytest.raises(KeyError):
        tr.record_result("never", "x")
    tr.register("T-test", "h", "w", "acc", today="2026-09-03")
    r1 = tr.record_result("T-test", "ran once", run_date="2026-09-10", today="2026-09-10")
    r2 = tr.record_result("T-test", "ran twice", adopted=False, run_date="2026-09-20", today="2026-09-20")
    assert len(_lines(registry)) == 3                        # append-only: 1 register + 2 results
    assert r1["run_dates"] == ["2026-09-10"] and r2["run_dates"] == ["2026-09-10", "2026-09-20"]
    assert r2["event"] == "result" and r2["registered_before_run"] is True
    assert tr.latest("T-test")["result_summary"] == "ran twice"


def test_list_folds_by_id_in_registration_order(registry):
    tr.register("B", "h", "w", "acc"); tr.register("A", "h", "w", "acc")
    tr.record_result("B", "done", run_date="2026-09-10")
    ids = [t["id"] for t in tr.list_trials()]
    assert ids == ["B", "A"]
    assert tr.dsr_hurdle_n() == 1                            # only B has run


def test_file_never_shrinks(registry):
    sizes = []
    tr.register("A", "h", "w", "acc"); sizes.append(registry.stat().st_size)
    tr.register("A", "h", "w", "acc"); sizes.append(registry.stat().st_size)
    tr.record_result("A", "r"); sizes.append(registry.stat().st_size)
    assert sizes == sorted(sizes)


def test_program_trials_register_idempotently(registry):
    rows = tr.register_program()
    assert [r["id"] for r in rows] == [t["id"] for t in tr.PROGRAM_TRIALS]
    assert len(_lines(registry)) == 4
    tr.register_program()
    assert len(_lines(registry)) == 4
    x1 = tr.latest("X1-2026-09-index-sleeve-replay")
    assert "loss-weighted recall >= 0.80" in x1["acceptance"] and "Confirmed by user 2026-09-03" in x1["acceptance"]


def test_config_hash_stable_and_config_sensitive(monkeypatch):
    h0 = tr.config_hash()
    assert h0 == tr.config_hash()
    import theta_core as tc
    monkeypatch.setitem(tc.CONFIG, "g5_global_z", 9.9)
    assert tr.config_hash() != h0
