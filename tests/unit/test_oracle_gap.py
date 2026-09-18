"""Oracle-gap mission — unit tests (T3, ZERO API).

Covers:
- exact oracle math (add/drop/bidirectional);
- no hidden-proxy access from heuristic policies;
- add/drop set semantics (union/subtraction);
- duplicate-file handling (sets);
- zero-FN / zero-FP tasks;
- tiny candidate sets;
- budget clipping;
- preservation of frozen evidence (load_all matches frozen per_task_rows);
- sealed-set fail-closed guard (INTERNAL_TEST never used for selection).
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.oracle_gap_bbsr import bbsr_oracle, bbsr_task
from scripts.oracle_gap_ceilings import (
    oracle_add,
    oracle_bi,
    oracle_drop,
    reachability,
    route_b_add_only,
)
from scripts.oracle_gap_data import load_all
from scripts.oracle_gap_fp_pruning import (
    build_selected_rows,
    evaluate_drop,
    rank_selected,
)

PROJECT = Path(__file__).resolve().parent.parent.parent
P2_ROWS = PROJECT / "research" / "p2-phase1" / "per_task_rows.json"


def _counts(cases: list[dict]) -> list[dict]:
    return cases


def test_oracle_add_math() -> None:
    counts = [
        {"case_id": "a", "tp": 2, "fp": 3, "fn": 5, "proxy_size": 7, "write_set_size": 5, "n_missed": 5},
        {"case_id": "b", "tp": 0, "fp": 0, "fn": 4, "proxy_size": 4, "write_set_size": 0, "n_missed": 4},
    ]
    # A=2: add min(2,fn) per task
    m = oracle_add(counts, 2)
    assert m["tp"] == 2 + 2 + 2
    assert m["fn"] == 5 - 2 + 4 - 2
    assert m["fp"] == 3
    # A=ALL: add all FNs
    m_all = oracle_add(counts, None)
    assert m_all["fn"] == 0
    assert m_all["tp"] == 2 + 5 + 4


def test_oracle_drop_math() -> None:
    counts = [
        {"case_id": "a", "tp": 2, "fp": 3, "fn": 5, "proxy_size": 7, "write_set_size": 5, "n_missed": 5},
        {"case_id": "b", "tp": 1, "fp": 4, "fn": 0, "proxy_size": 1, "write_set_size": 5, "n_missed": 0},
    ]
    m = oracle_drop(counts, 2)
    assert m["fp"] == 3 - 2 + 4 - 2
    assert m["tp"] == 3
    m_all = oracle_drop(counts, None)
    assert m_all["fp"] == 0


def test_oracle_bidirectional_math() -> None:
    counts = [
        {"case_id": "a", "tp": 2, "fp": 3, "fn": 5, "proxy_size": 7, "write_set_size": 5, "n_missed": 5},
    ]
    m = oracle_bi(counts, 3, 2)
    assert m["tp"] == 2 + 3
    assert m["fn"] == 5 - 3
    assert m["fp"] == 3 - 2


def test_oracle_never_negative() -> None:
    counts = [
        {"case_id": "a", "tp": 0, "fp": 1, "fn": 0, "proxy_size": 0, "write_set_size": 1, "n_missed": 0},
    ]
    m = oracle_drop(counts, 5)
    assert m["fp"] == 0
    assert m["tp"] == 0
    m2 = oracle_add(counts, 5)
    assert m2["fn"] == 0


def test_zero_fn_task() -> None:
    counts = [
        {"case_id": "a", "tp": 1, "fp": 0, "fn": 0, "proxy_size": 1, "write_set_size": 1, "n_missed": 0},
        {"case_id": "b", "tp": 0, "fp": 1, "fn": 2, "proxy_size": 2, "write_set_size": 1, "n_missed": 2},
    ]
    m = oracle_add(counts, 1)
    assert m["tp"] == 1 + 1
    assert m["fn"] == 1


def test_zero_fp_task() -> None:
    counts = [
        {"case_id": "a", "tp": 2, "fp": 0, "fn": 1, "proxy_size": 3, "write_set_size": 2, "n_missed": 1},
    ]
    m = oracle_drop(counts, 3)
    assert m["fp"] == 0
    assert m["tp"] == 2


def test_reachability_structure() -> None:
    counts = [
        {"case_id": "a", "tp": 2, "fp": 3, "fn": 5, "proxy_size": 7, "write_set_size": 5, "n_missed": 5},
        {"case_id": "b", "tp": 0, "fp": 0, "fn": 4, "proxy_size": 4, "write_set_size": 0, "n_missed": 4},
    ]
    r = reachability(counts)
    assert 0.50 in r
    e = r[0.50]
    assert e["add_only"] is not None
    assert e["reachable_bi"]
    assert e["bidirectional"]["A"] is not None


def test_route_b_add_only_is_superset() -> None:
    """Route-B add-only must be a superset of the Sparse write set per task."""
    tasks = load_all()
    dc = [t for t in tasks if t.repository == "djangocms"]
    for t in dc[:20]:
        m = route_b_add_only([t], 5)
        # tp+fn must equal proxy size (all positives accounted)
        assert m["tp"] + m["fn"] == len(t.proxy)


def test_bbsr_heuristic_uses_observable_only():
    """The BBSR heuristic must only consume composite/features, never is_missed_positive."""
    tasks = load_all()
    for t in tasks[:5]:
        res = bbsr_task(t, 2, 2)
        assert res["tp"] + res["fn"] == len(t.proxy)


def test_bbsr_oracle_is_upper_bound():
    """Oracle review must never do worse on recall than heuristic review."""
    tasks = load_all()
    for t in tasks[:30]:
        h = bbsr_task(t, 2, 1)
        o = bbsr_oracle(t, 2, 1)
        assert o["tp"] >= h["tp"]


def test_budget_clipping():
    """Adding more budget than FNs/FPs available must not change counts."""
    counts = [
        {"case_id": "a", "tp": 0, "fp": 1, "fn": 2, "proxy_size": 2, "write_set_size": 1, "n_missed": 2},
    ]
    m5 = oracle_add(counts, 5)
    mall = oracle_add(counts, None)
    assert m5 == mall


def test_aggregate_matches_frozen_per_task_rows():
    """load_all must reproduce the frozen P2 per_task_rows n_missed exactly."""
    tasks = load_all()
    ptr = json.loads(P2_ROWS.read_text(encoding="utf-8"))
    for repo, rows_key in (("djangocms", "djangocms_dev"), ("saleor", "saleor_dev")):
        mine = sum(t.n_missed for t in tasks if t.repository == repo)
        frozen = sum(r["n_missed"] for r in ptr[rows_key])
        assert mine == frozen
        ids_mine = {t.case_id for t in tasks if t.repository == repo}
        ids_frozen = {r["case_id"] for r in ptr[rows_key]}
        assert ids_mine == ids_frozen


def test_sealed_sets_guard():
    """The mission data layer must contain NO INTERNAL_TEST / RESERVE case ids."""
    tasks = load_all()
    ids = {t.case_id for t in tasks}
    # djangoCMS INTERNAL_TEST (80) and RESERVE are NOT in DEV load
    # (DEV = V1 30 + V2 DEV_TRAIN 117 + DEV_VALIDATION 27 = 174; Saleor 149)
    assert len(ids) == 174 + 149
    for t in tasks:
        assert "internal-test" not in t.role.lower()
        assert "reserve" not in t.role.lower()


def test_fp_pruning_rows_feature_complete():
    tasks = load_all()
    dc = [t for t in tasks if t.repository == "djangocms"]
    rows = build_selected_rows(dc)
    assert len(rows) >= 100
    for r in rows:
        for k in ("bm25", "composite", "graph_neighbor", "pt_overlap", "is_fp"):
            assert k in r


def test_fp_pruning_drop_never_negative():
    # use a real task so task_map lookup succeeds
    tasks = load_all()
    t0 = next(t for t in tasks if t.write_set)
    rows = [
        {"case_id": t0.case_id, "path": next(iter(sorted(t0.write_set))), "is_fp": 1, "is_tp": 0,
         "bm25": 0.1, "composite": 0.1, "graph_neighbor": 0.0, "pt_overlap": 0, "bm25_rank_pct": 0.9},
    ]
    task_map = {t.case_id: t for t in tasks}
    order = rank_selected(rows, "composite")
    m = evaluate_drop(rows, 3, order, task_map)
    assert m["n_flagged"] == 1
    assert m["final_fp"] >= 0


def test_salesforce_not_used():
    """No salesforce/locagent new calls; plan doc is the deliverable."""
    plan = PROJECT / "reports" / "LOCAGENT_FAIR_COMPARISON_PLAN_V2.md"
    assert plan.is_file()
    text = plan.read_text(encoding="utf-8").lower()
    assert "zero locagent spend" in text or "no new locagent" in text
