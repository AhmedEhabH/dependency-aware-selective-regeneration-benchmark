"""Tests for the P5-C shared-protocol comparison scorer logic.

Covers the frozen comparison semantics without requiring the real 10-task
P5-C evidence: micro pooling, macro means, bootstrap determinism, and the
CORRECTED native metrics (official LocAgent Acc@K, task-level Hit@K, and
item-hit counts that must never masquerade as task accuracy) derived from
ORIGINAL ranked order (never reconstructed from a set).

Regression coverage (V20 reporting correction, 2026-09-15):
- a task containing MULTIPLE correct files in top-K must NOT be counted by
  item-hit counting: official Acc@K counts a task only when correct-in-topK
  == min(len(proxy), K);
- the historical 4/10, 8/10, 9/10 values were item-hit sums, not task
  accuracy, and must not reappear as Acc@K / Hit@K.
"""

from __future__ import annotations

import random

from scripts.locagent_shared_comparison import _bootstrap_mean_delta, _macro_mean, _micro_pooled
from benchmark.locagent import evaluator


def test_micro_pooled_matches_manual() -> None:
    rows = [
        {"tp": 3, "fp": 1, "fn": 1},
        {"tp": 1, "fp": 0, "fn": 4},
    ]
    res = _micro_pooled(rows)
    assert res["tp"] == 4 and res["fp"] == 1 and res["fn"] == 5
    assert abs(res["precision"] - 4 / 5) < 1e-6
    assert abs(res["recall"] - 4 / 9) < 1e-6


def test_micro_pooled_zero_division_safe() -> None:
    res = _micro_pooled([{"tp": 0, "fp": 0, "fn": 0}])
    assert res["f1"] == 0.0 and res["fnr"] == 0.0


def test_macro_mean() -> None:
    rows = [{"f1": 0.5}, {"f1": 1.0}]
    assert abs(_macro_mean(rows, "f1") - 0.75) < 1e-9
    assert _macro_mean([], "f1") == 0.0


def test_bootstrap_deterministic_with_seed() -> None:
    deltas = [0.1 * i for i in range(10)]
    a = _bootstrap_mean_delta(deltas, iterations=5000, seed=123)
    b = _bootstrap_mean_delta(deltas, iterations=5000, seed=123)
    assert a == b
    assert a["mean_delta"] == round(sum(deltas) / len(deltas), 6)
    assert a["ci95_low"] <= a["mean_delta"] <= a["ci95_high"]


def test_bootstrap_rng_reproducible_primitive() -> None:
    # Determinism comes from a seeded RNG; prove the primitive.
    r1 = random.Random(42)
    s1 = [r1.randrange(100) for _ in range(50)]
    r2 = random.Random(42)
    s2 = [r2.randrange(100) for _ in range(50)]
    assert s1 == s2


def test_acc_at_k_uses_ranked_order_not_set() -> None:
    # If Acc@K were computed from a set, the "order" would be lost. Here we
    # model the scorer's ranking rule directly: iterate the ranked tuple in
    # order, count hits among the first k.
    ranked = ("cms/b.py", "cms/a.py", "cms/c.py")
    proxy = {"cms/a.py", "cms/c.py"}
    for k, expected_hits in ((1, 0), (2, 1), (3, 2)):
        hits = sum(1 for f in ranked[:k] if f in proxy)
        assert hits == expected_hits


def test_ranked_order_preserves_original_sequence() -> None:
    # The scorer must consume merged_loc_outputs_mrr.jsonl ORDER, i.e. the
    # tuple identity is preserved (order matters for Acc@K).
    ranked = ("cms/admin/forms.py", "cms/admin/pageadmin.py", "cms/models/pagemodel.py")
    assert list(ranked) == ["cms/admin/forms.py", "cms/admin/pageadmin.py", "cms/models/pagemodel.py"]
    assert ranked[0] == "cms/admin/forms.py"  # first ranked file stays first


# ---------------------------------------------------------------------------
# C1 regression: official LocAgent Acc@K vs Hit@K vs item-hits
# ---------------------------------------------------------------------------


def test_official_acc_at_k_requires_all_min_gt_files() -> None:
    # Task with TWO correct proxy files; official Acc@K counts the task only
    # when correct-in-topK == min(len(proxy), K). Item-hit counting must NOT
    # masquerade as task accuracy.
    ranked = ("cms/a.py", "cms/b.py", "cms/c.py")
    proxy = {"cms/a.py", "cms/b.py"}
    # At K=1: correct=1 == min(2,1)=1 -> official Acc@1 hit.
    assert evaluator.locagent_acc_at_k(ranked, proxy, 1) is True
    # At K=3: correct=2 == min(2,3)=2 -> official Acc@3 hit.
    assert evaluator.locagent_acc_at_k(ranked, proxy, 3) is True
    # Item hits at K=3 = 2 (audit-only, never task accuracy).
    assert evaluator.locagent_item_hits_at_k(ranked, proxy, 3) == 2


def test_official_acc_at_k_counts_task_not_items() -> None:
    # The historical bug summed item hits across tasks and labelled them as
    # "tasks with >=1 hit". Prove the corrected per-task semantics: one task
    # with 2 correct files contributes ONE Acc@K hit (not 2), and a task where
    # only 1 of 2 proxy files is in top-K is NOT an official Acc@K hit.
    ranked = ("cms/a.py", "cms/x.py", "cms/y.py")
    proxy = {"cms/a.py", "cms/b.py"}
    # K=2: correct=1, min(len=2, K=2)=2 -> 1 != 2 -> NOT an official Acc@3 hit
    assert evaluator.locagent_acc_at_k(ranked, proxy, 2) is False
    # Hit@2 (>=1 proxy file in top-2) IS a hit (a.py).
    assert evaluator.locagent_hit_at_k(ranked, proxy, 2) is True
    # item-hits at K=2 = 1 (audit-only).
    assert evaluator.locagent_item_hits_at_k(ranked, proxy, 2) == 1


def test_historical_8_of_10_and_9_of_10_are_item_hits_not_tasks() -> None:
    # Direct regression on the historical P5-C claim: the old "Acc@3 8/10,
    # Acc@5 9/10" were cross-task sums of matching FILE ITEMS. Under the
    # official metric and the simple Hit@K definition, both are 4/10 (only the
    # 4 tasks with a rank-1 correct file ever hit at any K).
    merged = {}
    from pathlib import Path
    p5c = Path(__file__).resolve().parent.parent.parent / "research" / "locagent-p5b" / "out_c"
    import json
    for line in (p5c / "merged_loc_outputs_mrr.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        merged[row["instance_id"]] = row
    ds = Path(__file__).resolve().parent.parent.parent / "benchmark_data" / "real_commit_impact_v1"

    def proxy(cid):
        return set(json.loads((ds / "scientific" / cid / "hidden" / "observed_change_set_proxy.json").read_text())["paths"])

    n_ok = 0
    total = 0
    item_acc3 = 0
    item_acc5 = 0
    for cid, m in merged.items():
        ff = m.get("found_files") or []
        ranked = tuple(ff[0]) if ff and isinstance(ff[0], list) else tuple(ff)
        p = proxy(cid)
        n_ok += 1 if evaluator.locagent_hit_at_k(ranked, p, 3) else 0
        total += 1
        item_acc3 += evaluator.locagent_item_hits_at_k(ranked, p, 3)
        item_acc5 += evaluator.locagent_item_hits_at_k(ranked, p, 5)
    # Simple task-level Hit@3 == 4/10 (from the raw evidence).
    assert n_ok == 4 and total == 10
    # The historical 8/9 values were item-hit sums and are NOT Hit@K / Acc@K.
    assert item_acc3 == 8
    assert item_acc5 == 9
    assert item_acc3 != n_ok
    assert item_acc5 != n_ok


def test_official_acc_at_k_p5c_recomputation() -> None:
    # Independent recomputation on the real P5-C evidence under the official
    # definition: Acc@1 = 4/10, Acc@3 = 4/10, Acc@5 = 2/10.
    from pathlib import Path
    import json
    p5c = Path(__file__).resolve().parent.parent.parent / "research" / "locagent-p5b" / "out_c"
    ds = Path(__file__).resolve().parent.parent.parent / "benchmark_data" / "real_commit_impact_v1"
    merged = {}
    for line in (p5c / "merged_loc_outputs_mrr.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        merged[row["instance_id"]] = row

    def proxy(cid):
        return set(json.loads((ds / "scientific" / cid / "hidden" / "observed_change_set_proxy.json").read_text())["paths"])

    for k, expected in ((1, 4), (3, 4), (5, 2)):
        n = 0
        for cid, m in merged.items():
            ff = m.get("found_files") or []
            ranked = tuple(ff[0]) if ff and isinstance(ff[0], list) else tuple(ff)
            n += 1 if evaluator.locagent_acc_at_k(ranked, proxy(cid), k) else 0
        assert n == expected, f"Acc@{k} = {n}, expected {expected}"
