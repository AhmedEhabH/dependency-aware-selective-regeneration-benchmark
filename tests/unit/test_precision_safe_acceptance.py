"""Precision-safe acceptance pilot - unit tests (T3, real DEVELOPMENT pilot).

Covers:
- budget ledger within ceilings (357 calls / 176,060 tokens / $0.0648 / 655.7 s)
- record structure (240 Arm A + 60 rank + 60 verify; 3 fail-closed abstentions)
- ORR@5 recomputation matches the metrics JSON
- preregistered gate decision == PRECISION_SAFE_ACCEPTANCE_FAIL with djangocms
  c1/c2 fail points and saleor c1 pass
- F1 and candidate-precision protection (Arm B >= Arm A - 0.05 / >= Arm A)
- schema validity (100% of 357 dispatched calls; zero partial credit)
- sealed + disjoint sample (60 fresh tasks, Stage-4 excluded)
- no hidden proxy in prompt construction
- regression: the frozen Stage-4 verdict remains BOUNDED_SEMANTIC_NEGATIVE_FROZEN
"""
from __future__ import annotations

import json
from pathlib import Path

from benchmark.recall.data import load_dev_tasks

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
_RESULT_JSON = _PROJECT_DIR / "research" / "precision-safe-acceptance-pilot" / "pilot_results.json"
_REG_JSON = _PROJECT_DIR / "research" / "precision-safe-acceptance-pilot" / "pilot_registration_freeze.json"
_METRICS_JSON = _PROJECT_DIR / "reports" / "precision_safe_acceptance_metrics.json"
_GATE_JSON = _PROJECT_DIR / "reports" / "precision_safe_acceptance_gate.json"
_STAGE4_REG = _PROJECT_DIR / "research" / "bounded-semantic-expansion" / "pilot_registration_freeze.json"


def _load():
    if not hasattr(_load, "_data"):
        result = json.loads(_RESULT_JSON.read_text(encoding="utf-8"))
        reg = json.loads(_REG_JSON.read_text(encoding="utf-8"))
        metrics = json.loads(_METRICS_JSON.read_text(encoding="utf-8"))
        gate = json.loads(_GATE_JSON.read_text(encoding="utf-8"))
        stage4 = json.loads(_STAGE4_REG.read_text(encoding="utf-8"))
        _load._data = (result, reg, metrics, gate, stage4, load_dev_tasks())
    return _load._data


def test_ledger_within_ceilings():
    result, _, _, _, _, _ = _load()
    led = result["ledger"]
    assert led["actual_calls"] == 357 <= 400
    assert led["actual_tokens"] == 176_060 <= 300_000
    assert led["actual_cost_usd"] <= 0.15
    assert led["wall_seconds"] <= 3600
    assert led["budget_respected"] is True
    assert led["resumed_from_disk"] == 357


def test_record_structure():
    result, _, _, _, _, _ = _load()
    recs = result["records"]
    arm_a = [r for r in recs if r["stage"] == "arm_a_verifier"]
    rank = [r for r in recs if r["stage"] == "rank"]
    verify = [r for r in recs if r["stage"] == "verify"]
    assert len(arm_a) == 240 and len(rank) == 60 and len(verify) == 60
    assert all(r["schema_valid"] for r in arm_a)
    assert all(r["schema_valid"] for r in rank)
    skipped = [r for r in verify if r.get("skipped")]
    assert len(skipped) == 3
    assert sum(1 for r in verify if r["schema_valid"]) == 57
    assert all(r["total_tokens"] == 0 and r["api_cost"] == 0 for r in skipped)
    for r in rank:
        per_b = r["per_b"]
        assert set(per_b) == {"1", "3", "5", "10"}
        assert all(len(per_b[k]["additions"]) <= 10 for k in per_b)


def test_orr5_recomputed_matches():
    result, _, metrics, _, _, tasks = _load()
    by_cid = {t.case_id: t for t in tasks}
    arm_a = [r for r in result["records"] if r["stage"] == "arm_a_verifier"]
    rank = [r for r in result["records"] if r["stage"] == "rank"]

    def orr5(repo: str, arm: str) -> float:
        recs = arm_a if arm == "A" else rank
        vals = []
        for r in recs:
            if r["repository"] != repo:
                continue
            if arm == "A" and r["B"] != 5:
                continue
            t = by_cid[r["case_id"]]
            if t.n_missed == 0:
                vals.append(0.0)
                continue
            if arm == "A":
                vals.append(len(r["verifier_recovered"]) / t.n_missed)
            else:
                vals.append(len(r.get("per_b", {}).get("5", {}).get("recovered", [])) / t.n_missed)
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    for repo in ("djangocms", "saleor"):
        assert orr5(repo, "A") == metrics["repos"][repo]["B"]["5"]["arm_a"]["macro_orr"]
        assert orr5(repo, "B") == metrics["repos"][repo]["B"]["5"]["arm_b"]["macro_orr"]


def test_gate_decision_and_fail_points():
    _, _, _, gate, _, _ = _load()
    assert gate["decision"] == "PRECISION_SAFE_ACCEPTANCE_FAIL"
    assert gate["pass"] is False
    dc = gate["repos"]["djangocms"]
    sc = gate["repos"]["saleor"]
    assert dc["c1_orr_materially_above_armA"] is False
    assert dc["c2_fold_majority_positive"] is False
    assert sc["c1_orr_materially_above_armA"] is True
    assert sc["c2_fold_majority_positive"] is True
    assert dc["c3_naive_f1_not_materially_worse"] is True
    assert dc["c4_candidate_precision_not_below_armA"] is True
    assert sc["c3_naive_f1_not_materially_worse"] is True
    assert sc["c4_candidate_precision_not_below_armA"] is True
    assert gate["schema_rate_all_dispatched_calls"] == 1.0
    assert gate["zero_partial_credit"] is True
    assert gate["arm_b_calls_per_task"] == 2.0


def test_f1_and_precision_protected_both_repos():
    _, _, metrics, _, _, _ = _load()
    for repo in ("djangocms", "saleor"):
        b5 = metrics["repos"][repo]["B"]["5"]
        a, b = b5["arm_a"], b5["arm_b"]
        assert b["naive_union_f1"] >= a["naive_union_f1"] - 0.05
        assert b["candidate_precision"] >= a["candidate_precision"]
        assert b["final_precision"] >= a["final_precision"]


def test_schema_validity_and_no_partial_credit():
    result, _, _, gate, _, _ = _load()
    dispatched = [r for r in result["records"] if r.get("total_tokens", 0) > 0 or r.get("api_cost", 0) > 0]
    assert len(dispatched) == 357
    assert all(r["schema_valid"] for r in dispatched)
    assert not any(
        not r["schema_valid"] and r.get("per_b", {}).get("5", {}).get("additions", [])
        for r in result["records"]
    )


def test_sealed_and_disjoint_sample():
    _, reg, _, _, stage4, tasks = _load()
    sample_ids = {s["case_id"] for s in reg["sample"]}
    stage4_ids = {s["case_id"] for s in stage4["sample"]}
    assert len(sample_ids) == 60
    assert len(sample_ids & stage4_ids) == 0
    assert sample_ids <= {t.case_id for t in tasks}
    assert all("internal-test" not in t.role.lower() and "reserve" not in t.role.lower()
               for t in tasks if t.case_id in sample_ids)
    assert all(s["pool_size"] <= 80 for s in reg["sample"])


def test_stage4_verdict_still_frozen():
    _, _, _, _, _, _ = _load()
    gate4 = json.loads(
        (_PROJECT_DIR / "reports" / "bounded_semantic_expansion_gate.json").read_text(encoding="utf-8")
    )
    assert gate4["decision"] == "BOUNDED_SEMANTIC_NEGATIVE_FROZEN"


def test_no_hidden_proxy_in_pool():
    _, reg, _, _, _, tasks = _load()
    by_cid = {t.case_id: t for t in tasks}
    from benchmark.recall.rankers import rank_composite

    for s in reg["sample"]:
        t = by_cid[s["case_id"]]
        base = set(rank_composite(t)[:10])
        union = base | {c["path"] for c in t.candidates if c["consumer"]}
        cand_map = {c["path"]: c for c in t.candidates}
        ordered = sorted(union, key=lambda p: (-float(cand_map[p]["bm25"]), p))
        assert list(s["pool"]) == ordered[:80]
        assert list(s["pool_id_map"].values()) == [f"C{i:02d}" for i in range(1, len(s["pool"]) + 1)]
        assert set(s["pool_id_map"]) == set(s["pool"])
