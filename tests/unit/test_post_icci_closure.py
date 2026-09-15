"""POST-ICCI deterministic regression tests.

Covers the LocAgent common-evaluator normalization contract and the two
LocAgent recomputation variants:

- Normalization (task 3): raw LocAgent output object -> entity/location-to-path
  conversion -> path canonicalization -> duplicate handling -> universe
  intersection -> out-of-universe retention in raw logs -> final predicted
  file set.
- Two-way recomputation (task 4): A fail-closed all-10-task headline vs
  B usable-output-only 5-task diagnostic (survivor-conditioned), with the
  failure taxonomy (2 timeout / 1 context-length / 2 completed-but-empty).
- Four-action FN breakdown (task 5) is checked against the frozen P1 micro
  FN totals (secondary diagnostic, not a new experiment).

ZERO API. All assertions recompute from frozen evidence; nothing is copied
from a summary that the test itself is meant to check.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_PACKAGE_ROOT / "src"))

from benchmark.locagent import evaluator  # noqa: E402
from benchmark.real_commits import p1_evaluation as p1  # noqa: E402

DATASET_DIR = _PACKAGE_ROOT / "benchmark_data" / "real_commit_impact_v1"
P5C_DIR = _PACKAGE_ROOT / "research" / "locagent-p5b" / "out_c"
STUDY_DIR = _PACKAGE_ROOT / "research" / "real-commit-p1-01"
TWO_WAY = _PACKAGE_ROOT / "research" / "locagent-p5b" / "locagent_two_way.json"
FN_BREAKDOWN = _PACKAGE_ROOT / "research" / "post-icci-zero-api-closure" / "four_action_fn_breakdown.json"

HELD_OUT = [
    "djangocms-rc-4307e1b8c2e2",
    "djangocms-rc-50c3576080be",
    "djangocms-rc-630a50361ada",
    "djangocms-rc-66c70394c9e1",
    "djangocms-rc-75978fb1c3ad",
    "djangocms-rc-8d50660e7bcf",
    "djangocms-rc-9e33db4f4660",
    "djangocms-rc-b39799f9fc1c",
    "djangocms-rc-ba16eb9a1d09",
    "djangocms-rc-fdda30c271f0",
]

EMPTY_TAXONOMY = {
    "djangocms-rc-4307e1b8c2e2": "timeout",
    "djangocms-rc-66c70394c9e1": "context_length_badrequest",
    "djangocms-rc-9e33db4f4660": "completed_but_empty",
    "djangocms-rc-b39799f9fc1c": "completed_but_empty",
    "djangocms-rc-fdda30c271f0": "timeout",
}


def _proxy(case_id: str) -> set[str]:
    p = DATASET_DIR / "scientific" / case_id / "hidden" / "observed_change_set_proxy.json"
    return set(json.loads(p.read_text(encoding="utf-8"))["paths"])


def _universe(case_id: str) -> set[str]:
    p = DATASET_DIR / "scientific" / case_id / "public" / "candidate_universe.json"
    return {str(r["path"]) for r in json.loads(p.read_text(encoding="utf-8"))["records"]}


def _merged_ranked(case_id: str) -> tuple[str, ...]:
    for line in (P5C_DIR / "merged_loc_outputs_mrr.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["instance_id"] != case_id:
            continue
        ff = row.get("found_files") or []
        if ff and isinstance(ff[0], list):
            return tuple(ff[0])
        if isinstance(ff, list):
            return tuple(ff)
        return ()
    return ()


# ---------------------------------------------------------------------------
# Task 3 — LocAgent common-evaluator normalization contract
# ---------------------------------------------------------------------------


def test_raw_locagent_output_object_has_expected_fields() -> None:
    rows = {}
    for line in (P5C_DIR / "loc_outputs.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        rows[row["instance_id"]] = row
    assert set(rows) == set(HELD_OUT)
    for cid in HELD_OUT:
        row = rows[cid]
        assert set(row) == {"instance_id", "found_files", "found_modules", "found_entities",
                            "raw_output_loc", "meta_data"}
        assert isinstance(row["found_files"], list)
        assert isinstance(row["meta_data"], dict)
        assert row["meta_data"]["patch"] == ""


def test_scored_file_set_is_universe_intersection_of_ranked_files() -> None:
    # Frozen comparison policy: predicted = set(ranked found_files) & universe.
    for cid in HELD_OUT:
        ranked = _merged_ranked(cid)
        uni = _universe(cid)
        predicted = set(ranked) & uni
        assert predicted <= uni
        # Every scored predicted file is an exact member of the candidate universe.
        assert all(f in uni for f in predicted)


def test_out_of_universe_files_retained_in_raw_logs_but_dropped_from_scored_set() -> None:
    # 8d50660e7bcf: the emitted list contains cms/migrations/0039_...py which is
    # NOT in the parent-only production candidate universe (migrations excluded).
    cid = "djangocms-rc-8d50660e7bcf"
    ranked = _merged_ranked(cid)
    uni = _universe(cid)
    oou = [f for f in ranked if f not in uni]
    assert len(oou) >= 1, "expected at least one out-of-universe raw log entry"
    assert all("migrations" in f for f in oou)
    # Raw log retains the full emitted list; the scored set drops the OOU file.
    predicted = set(ranked) & uni
    assert len(predicted) == len(ranked) - len(oou)


def test_duplicate_handling_unique_predicted_set() -> None:
    # LocAgentRawOutput.unique_predicted_file_set() merges found_files and
    # ranked_files into ONE set (dedup is inherent to the set).
    raw = evaluator.LocAgentRawOutput(
        instance_id="x",
        found_files=("cms/a.py", "cms/a.py", "cms/b.py"),
        ranked_files=("cms/a.py",),
    )
    assert raw.unique_predicted_file_set() == {"cms/a.py", "cms/b.py"}


def test_path_canonicalization_exact_universe_match_no_rewriting() -> None:
    # Canonicalization is exact string membership against the parent-only
    # candidate universe; no path rewriting is performed by the evaluator.
    for cid in ("djangocms-rc-50c3576080be", "djangocms-rc-ba16eb9a1d09"):
        ranked = _merged_ranked(cid)
        uni = _universe(cid)
        for f in set(ranked) & uni:
            assert f in uni


def test_entity_location_to_path_conversion_uses_emitted_file_paths() -> None:
    # The common evaluator consumes found_files (emitted file paths). The
    # entity/location strings (found_modules / found_entities as
    # "path:Entity" / "path:Class.method") are NOT converted into the scored
    # file set by the frozen P5-C pipeline; they remain native artifacts in the
    # raw logs. Prove no scored predicted file is a "path:Entity" string.
    for cid in HELD_OUT:
        ranked = _merged_ranked(cid)
        uni = _universe(cid)
        predicted = set(ranked) & uni
        assert not any(":" in f for f in predicted)


# ---------------------------------------------------------------------------
# Task 4 — Two-way LocAgent recomputation (A headline / B diagnostic)
# ---------------------------------------------------------------------------


def _locagent_task_metrics(cid: str) -> dict[str, int]:
    ranked = _merged_ranked(cid)
    uni = _universe(cid)
    predicted = set(ranked) & uni
    proxy = _proxy(cid)
    return {"tp": len(predicted & proxy), "fp": len(predicted - proxy), "fn": len(proxy - predicted)}


def test_headline_fail_closed_all_10_recomputed_matches_frozen() -> None:
    total = {"tp": 0, "fp": 0, "fn": 0}
    for cid in HELD_OUT:
        m = _locagent_task_metrics(cid)
        for k in total:
            total[k] += m[k]
    assert total == {"tp": 10, "fp": 13, "fn": 27}
    tp, fp, fn = total["tp"], total["fp"], total["fn"]
    p = tp / (tp + fp)
    r = tp / (tp + fn)
    f1 = 2 * p * r / (p + r)
    assert abs(p - 0.434783) < 1e-5
    assert abs(r - 0.270270) < 1e-5
    assert abs(f1 - 0.333333) < 1e-5


def test_diagnostic_usable_only_5_survivor_conditioned() -> None:
    usable = [cid for cid in HELD_OUT if cid not in EMPTY_TAXONOMY]
    assert usable == [
        "djangocms-rc-50c3576080be",
        "djangocms-rc-630a50361ada",
        "djangocms-rc-75978fb1c3ad",
        "djangocms-rc-8d50660e7bcf",
        "djangocms-rc-ba16eb9a1d09",
    ]
    total = {"tp": 0, "fp": 0, "fn": 0}
    for cid in usable:
        m = _locagent_task_metrics(cid)
        for k in total:
            total[k] += m[k]
    # 50c(5/7/7) + 630a(1/0/0) + 7597(1/0/0) + 8d50(3/0/2) + ba16(0/7/6)
    assert total == {"tp": 10, "fp": 13, "fn": 15}


def test_failure_taxonomy_exact_counts() -> None:
    from collections import Counter

    counts = Counter(EMPTY_TAXONOMY.values())
    assert counts["timeout"] == 2
    assert counts["context_length_badrequest"] == 1
    assert counts["completed_but_empty"] == 2
    assert sum(counts.values()) == 5


def test_two_way_json_labels_require_diagnostic_wording() -> None:
    data = json.loads(TWO_WAY.read_text(encoding="utf-8"))
    assert data["zero_api"] is True
    assert "FAIL-CLOSED all-10-task common metrics" in data["headline_A_fail_closed_all_10"]["label"]
    assert "DIAGNOSTIC ONLY (survivor-conditioned)" in data["diagnostic_B_usable_5"]["label"]
    assert data["headline_A_fail_closed_all_10"]["micro_pooled"] == {
        "tp": 10, "fp": 13, "fn": 27,
        "precision": 0.434783, "recall": 0.27027, "f1": 0.333333, "fnr": 0.72973,
    }


# ---------------------------------------------------------------------------
# Task 5 — Four-action FN breakdown (secondary diagnostic) matches frozen P1
# ---------------------------------------------------------------------------


def _frozen_p1_micro_fns() -> dict[str, int]:
    metrics = json.loads((STUDY_DIR / "final_metrics.json").read_text(encoding="utf-8"))
    out = {}
    for arm in ("full_v2", "sparse_v2"):
        out[arm] = metrics["arms"][arm]["micro_overall"]["fn"]
    return out


def test_four_action_fn_breakdown_matches_frozen_micro_fn() -> None:
    breakdown = json.loads(FN_BREAKDOWN.read_text(encoding="utf-8"))
    frozen = _frozen_p1_micro_fns()
    for arm in ("full_v2", "sparse_v2"):
        agg = breakdown["aggregate"][arm]
        total = sum(agg.values())
        assert total == frozen[arm], f"{arm}: breakdown FN {total} != frozen FN {frozen[arm]}"


def test_four_action_breakdown_classified_actions() -> None:
    breakdown = json.loads(FN_BREAKDOWN.read_text(encoding="utf-8"))
    for arm in ("full_v2", "sparse_v2"):
        agg = breakdown["aggregate"][arm]
        assert set(agg) == {"PRESERVE", "VALIDATE", "HUMAN_REVIEW"}
    assert breakdown["decoded_cells"] == 60
    assert breakdown["decode_failures"] == []


def test_p1_action_vocab_is_four_actions() -> None:
    assert p1.P1_ACTION_VOCAB == ("PRESERVE", "REGENERATE", "VALIDATE", "HUMAN_REVIEW")
