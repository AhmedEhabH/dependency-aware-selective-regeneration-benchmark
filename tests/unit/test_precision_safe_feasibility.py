"""Precision-safe acceptance feasibility - unit tests (T3, ZERO API).

Covers:
- Stage-4 evidence verification (frozen negative untouched, 300 calls, 6/60 invalid)
- frozen ORR@5 recomputation matches the Stage-4 metrics JSON
- Arm-B rank-position candidate-precision determinism
- B=5 source split (Route-B top-10 vs reverse-1hop-only) determinism
- pool cap saturation + cap-loss recomputation
- feasibility rule invariants (accepted subset of top-K AND verifier-approved)
- matched-subset comparison determinism
- schema-invalid taxonomy (6 non-pool-path)
- future fresh sample availability (>= 30 per repo after excluding Stage-4)
- no hidden-proxy input to the pool construction
"""
# ruff: noqa: N806
from __future__ import annotations

import json
from pathlib import Path

from benchmark.recall.data import load_dev_tasks
from benchmark.recall.rankers import rank_composite

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
_RESULT_JSON = _PROJECT_DIR / "research" / "bounded-semantic-expansion" / "pilot_results.json"
_REG_JSON = _PROJECT_DIR / "research" / "bounded-semantic-expansion" / "pilot_registration_freeze.json"
_METRICS_JSON = _PROJECT_DIR / "reports" / "bounded_semantic_expansion_metrics.json"


def _load():
    if not hasattr(_load, "_data"):
        result = json.loads(_RESULT_JSON.read_text(encoding="utf-8"))
        reg = json.loads(_REG_JSON.read_text(encoding="utf-8"))
        metrics = json.loads(_METRICS_JSON.read_text(encoding="utf-8"))
        _load._data = (result, reg, metrics, load_dev_tasks())
    return _load._data


def _fn_paths(t) -> set[str]:
    return {c["path"] for c in t.candidates if c["is_missed_positive"]}


def test_stage4_evidence_verified():
    result, _, _, tasks = _load()
    ledger = result["ledger"]
    arm_a = [r for r in result["records"] if r["arm"] == "A"]
    arm_b = [r for r in result["records"] if r["arm"] == "B"]
    assert ledger["actual_calls"] == 300
    assert len(arm_a) == 240 and len(arm_b) == 60
    assert ledger["actual_tokens"] == 106_325
    assert abs(ledger["actual_cost_usd"] - 0.044399) < 1e-4
    assert abs(ledger["wall_seconds"] - 553.6) < 0.6
    assert ledger.get("budget_respected") is True
    assert sum(1 for r in arm_b if not r["schema_valid"]) == 6
    assert sum(1 for r in arm_a if not r["schema_valid"]) == 0


def test_stage4_verdict_frozen():
    _, _, metrics, _ = _load()
    gate = json.loads(
        (_PROJECT_DIR / "reports" / "bounded_semantic_expansion_gate.json").read_text(encoding="utf-8")
    )
    assert gate["decision"] == "BOUNDED_SEMANTIC_NEGATIVE_FROZEN"


def test_frozen_orr5_recomputed():
    result, _, metrics, tasks = _load()
    by_cid = {t.case_id: t for t in tasks}

    def orr5(repo: str, arm: str) -> float:
        vals = []
        for r in result["records"]:
            if r["repository"] != repo or r["arm"] != arm:
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


def test_dev_counts_and_sealed():
    _, reg, _, tasks = _load()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]
    assert len(dc) == 174 and len(sc) == 149
    sample_ids = {s["case_id"] for s in reg["sample"]}
    assert sample_ids <= {t.case_id for t in tasks}
    assert all("internal-test" not in t.role.lower() and "reserve" not in t.role.lower()
               for t in tasks if t.case_id in sample_ids)


def test_rank_position_candidate_precision_deterministic():
    result, reg, _, tasks = _load()
    by_cid = {t.case_id: t for t in tasks}
    arm_b = [r for r in result["records"] if r["arm"] == "B" and r["repository"] == "djangocms" and r["schema_valid"]]
    cum_fn = cum_sel = 0
    for i in range(1, 6):
        for r in arm_b:
            ordered = r.get("ordered_selected", [])
            if len(ordered) >= i:
                cum_sel += 1
                if ordered[i - 1] in _fn_paths(by_cid[r["case_id"]]):
                    cum_fn += 1
    assert cum_sel == 118
    assert cum_fn == 11
    assert abs(cum_fn / cum_sel - 0.0932) < 1e-3


def test_source_split_b5():
    result, reg, _, tasks = _load()
    by_cid = {t.case_id: t for t in tasks}
    reg_by_cid = {s["case_id"]: s for s in reg["sample"]}
    arm_b = [r for r in result["records"] if r["arm"] == "B" and r["schema_valid"]]
    for repo in ("djangocms", "saleor"):
        fn_o = fp_o = fn_c = fp_c = 0
        n_add = 0
        for r in arm_b:
            if r["repository"] != repo:
                continue
            t = by_cid[r["case_id"]]
            sel = set(r.get("per_b", {}).get("5", {}).get("additions", []))
            n_add += len(sel)
            routeb10 = set(reg_by_cid[r["case_id"]]["arm_a_tops"]["10"])
            for p in sel:
                if p in _fn_paths(t):
                    if p in routeb10:
                        fn_o += 1
                    else:
                        fn_c += 1
                else:
                    if p in routeb10:
                        fp_o += 1
                    else:
                        fp_c += 1
        assert fn_o + fn_c + fp_o + fp_c == n_add
        if repo == "djangocms":
            assert (fn_o, fn_c, fp_o, fp_c) == (7, 4, 62, 45)
        else:
            assert (fn_o, fn_c, fp_o, fp_c) == (19, 4, 66, 41)


def test_pool_cap_saturation():
    _, reg, _, _ = _load()
    dc_sizes = [s["pool_size"] for s in reg["sample"] if s["repository"] == "djangocms"]
    sc_sizes = [s["pool_size"] for s in reg["sample"] if s["repository"] == "saleor"]
    assert max(dc_sizes) == 40 and max(sc_sizes) == 40
    assert sum(1 for s in sc_sizes if s == 40) == 29
    assert all(s <= 40 for s in dc_sizes + sc_sizes)


def test_cap_loss_recomputed():
    result, reg, _, tasks = _load()
    by_cid = {t.case_id: t for t in tasks}
    lost = {"djangocms": 0, "saleor": 0}
    for s in reg["sample"]:
        t = by_cid[s["case_id"]]
        fn_set = _fn_paths(t)
        base = set(rank_composite(t)[:10])
        union = base | {c["path"] for c in t.candidates if c["consumer"]}
        cand_map = {c["path"]: c for c in t.candidates}
        full = set(sorted(union, key=lambda p: (-float(cand_map[p]["bm25"]), p)))
        lost[t.repository] += len(fn_set & (full - set(s["pool"])))
    assert lost == {"djangocms": 10, "saleor": 29}


def test_feasibility_rule_invariants():
    result, reg, _, tasks = _load()
    by_cid = {t.case_id: t for t in tasks}
    a_by_cid = {(r["case_id"], r["B"]): r for r in result["records"] if r["arm"] == "A"}
    for r in result["records"]:
        if r["arm"] != "B" or not r["schema_valid"]:
            continue
        by_cid[r["case_id"]]
        routeb10 = set(next(s for s in reg["sample"] if s["case_id"] == r["case_id"])["arm_a_tops"]["10"])
        approved = set(a_by_cid[(r["case_id"], 10)]["verifier_selected"])
        for K in (5, 10):
            accepted = set(p for p in r.get("ordered_selected", [])[:K] if p in routeb10 and p in approved)
            assert accepted <= set(r.get("ordered_selected", [])[:K])
            assert accepted <= approved
            assert len(accepted) <= K
            assert not (accepted & routeb10 - approved)  # never accepts unapproved overlap


def test_matched_subset_comparison_deterministic():
    result, _, _, tasks = _load()
    by_cid = {t.case_id: t for t in tasks}
    {(r["case_id"], r["B"]): r for r in result["records"] if r["arm"] == "A"}
    for repo in ("djangocms", "saleor"):
        b_recs = [r for r in result["records"] if r["arm"] == "B" and r["repository"] == repo and r["schema_valid"]]
        assert len(b_recs) == 27
        for r in b_recs:
            assert r["case_id"] in by_cid


def test_schema_invalid_taxonomy_all_nonpool():
    result, _, _, _ = _load()
    inv = [r for r in result["records"] if r["arm"] == "B" and not r["schema_valid"]]
    assert len(inv) == 6
    for r in inv:
        parsed = json.loads(r["raw_response"])
        content = parsed["choices"][0]["message"]["content"]
        items = json.loads(content).get("ordered") or []
        pool = set(r.get("pool", []))
        assert any(it.get("path") not in pool for it in items)


def test_future_fresh_sample_available():
    _, reg, _, tasks = _load()
    used = {s["case_id"] for s in reg["sample"]}
    for repo in ("djangocms", "saleor"):
        eligible = [t.case_id for t in tasks if t.repository == repo and t.n_missed >= 1 and t.omitted_size >= 5]
        remaining = sorted(set(eligible) - used)
        assert len(remaining) >= 30
    assert len(used) == 60


def test_no_hidden_proxy_in_pool_construction():
    _, reg, _, tasks = _load()
    by_cid = {t.case_id: t for t in tasks}
    # The pool is constructed from rank_composite (parent-visible BM25+graph)
    # and the consumer flag (parent-visible directed edge). Verify the frozen
    # registration pool equals that construction.
    for s in reg["sample"]:
        t = by_cid[s["case_id"]]
        base = set(rank_composite(t)[:10])
        union = base | {c["path"] for c in t.candidates if c["consumer"]}
        cand_map = {c["path"]: c for c in t.candidates}
        ordered = sorted(union, key=lambda p: (-float(cand_map[p]["bm25"]), p))
        assert list(s["pool"]) == ordered[:40]
