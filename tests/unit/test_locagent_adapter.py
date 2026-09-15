"""Unit tests for P5-A LocAgent shared-protocol adapter + common evaluator."""

from __future__ import annotations

from pathlib import Path

from benchmark.locagent import evaluator
from benchmark.locagent.adapter import (
    LOCAGENT_PINNED_COMMIT,
    LOCAGENT_REPOSITORY_URL,
    LocAgentAdapter,
    LocAgentInput,
    upstream_pin_check,
)

DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "benchmark_data" / "real_commit_impact_v1"


def test_upstream_pin_frozen() -> None:
    pin = upstream_pin_check()
    assert LOCAGENT_REPOSITORY_URL == "https://github.com/gersteinlab/LocAgent"
    assert len(LOCAGENT_PINNED_COMMIT) == 40
    assert pin["pinned_commit"] == LOCAGENT_PINNED_COMMIT
    assert pin["no_vendoring"] is True
    assert pin["input_fields"] == [
        "instance_id", "repo", "base_commit", "problem_statement", "patch",
    ]


def test_adapter_miner_dev_case_no_leakage() -> None:
    adapter = LocAgentAdapter(DATASET_DIR)
    instance = adapter.build_input("djangocms-rc-47040a2887ca")
    assert instance.split == "MINER_DEV"
    assert instance.patch == ""
    assert instance.base_commit
    assert instance.problem_statement.strip()
    assert adapter.leakage_errors(instance) == []


def test_adapter_input_never_contains_hidden_proxy() -> None:
    adapter = LocAgentAdapter(DATASET_DIR)
    for cid in ("djangocms-rc-47040a2887ca", "djangocms-rc-e008ff4b5c21"):
        instance = adapter.build_input(cid)
        adapter.assert_no_leakage(instance)
        payload = instance.to_swebench_dict()
        blob = " ".join(payload.values())
        for marker in ("observed_change_set_proxy", "target_diff", "hidden/", "gold_patch"):
            assert marker not in blob


def test_patch_is_empty_non_informative() -> None:
    adapter = LocAgentAdapter(DATASET_DIR)
    instance = adapter.build_input("djangocms-rc-47040a2887ca")
    assert instance.patch == ""
    # upstream LocAgent reads 'patch'; a non-empty value would be a leak vector
    assert instance.to_swebench_dict()["patch"] == ""


def test_leakage_errors_detects_non_empty_patch() -> None:
    inst = LocAgentInput(
        instance_id="x", repo="r", base_commit="b" * 40,
        problem_statement="fix", patch="diff --git a/cms/models/pagemodel.py b/cms/models/pagemodel.py",
    )
    errors = LocAgentAdapter(DATASET_DIR).leakage_errors(inst)
    assert any("patch must be EMPTY" in e for e in errors)


def test_parse_locagent_found_files_valid() -> None:
    valid = {"cms/admin/forms.py", "cms/models/pagemodel.py", "cms/api.py"}
    raw = """- cms/admin/forms.py\n- cms/models/pagemodel.py\n- cms/api.py\n"""
    found = evaluator.parse_locagent_found_files(raw, valid)
    assert list(found) == ["cms/admin/forms.py", "cms/models/pagemodel.py", "cms/api.py"]


def test_parse_locagent_found_files_json() -> None:
    valid = {"cms/a.py", "cms/b.py"}
    raw = '{"found_files": ["cms/a.py", "cms/b.py", "invented.py"]}'
    found = evaluator.parse_locagent_found_files(raw, valid)
    assert list(found) == ["cms/a.py", "cms/b.py"]


def test_parse_locagent_found_files_rejects_out_of_universe() -> None:
    valid = {"cms/a.py"}
    found = evaluator.parse_locagent_found_files("cms/nonexistent.py\n", valid)
    assert found == ()


def test_common_evaluator_perfect_and_imperfect() -> None:
    perfect = evaluator.common_evaluator(
        predicted_file_set={"a.py", "b.py"}, proxy_paths={"a.py", "b.py"},
        model_calls=1, prompt_tokens=100, completion_tokens=50,
    )
    assert perfect["precision"] == 1.0 and perfect["recall"] == 1.0 and perfect["fnr"] == 0.0
    assert perfect["total_tokens"] == 150
    assert perfect["policy"] == "exact_emitted_file_set"

    imperfect = evaluator.common_evaluator(
        predicted_file_set={"a.py", "c.py"}, proxy_paths={"a.py", "b.py"},
    )
    assert imperfect["tp"] == 1 and imperfect["fn"] == 1 and imperfect["fp"] == 1


def test_common_evaluator_never_mixes_native_acc() -> None:
    res = evaluator.common_evaluator(
        predicted_file_set={"a.py"}, proxy_paths={"a.py"},
        native_ranked_files=("a.py", "b.py"),
    )
    assert "note" in res and "Acc" in res["note"]


def test_pair_common_results_aggregation() -> None:
    rows = [
        evaluator.common_evaluator(predicted_file_set={"a"}, proxy_paths={"a"}),
        evaluator.common_evaluator(predicted_file_set={"a", "b"}, proxy_paths={"a"}),
    ]
    agg = evaluator.pair_common_results(rows)
    assert agg["task_count"] == 2
    assert agg["valid_output_rate"] == 1.0
    assert 0.0 <= agg["mean_f1"] <= 1.0


def test_cost_audit_paid_qwen_run_not_zero() -> None:
    """A Qwen/OpenRouter LocAgent run with token usage must NOT be free.

    Guards against upstream util/cost_analysis.py returning 0 for any model
    name containing 'qwen' (upstream native cost is diagnostic-only).
    """
    res = evaluator.common_evaluator(
        predicted_file_set={"cms/a.py"}, proxy_paths={"cms/a.py"},
        prompt_tokens=5000, completion_tokens=800,
    )
    assert res["total_tokens"] > 0
    assert res["cost_usd"] > 0.0
    assert res["cost_source"] == "estimated:frozen-p1-pricing"

    # Explicit audit assertion is fail-closed on zero cost with usage.
    import pytest

    with pytest.raises(AssertionError):
        evaluator.assert_cost_not_zero_for_paid_usage(
            prompt_tokens=100, completion_tokens=100, cost_usd=0.0,
        )
    # Zero tokens with zero cost is fine (no usage -> no claim).
    evaluator.assert_cost_not_zero_for_paid_usage(
        prompt_tokens=0, completion_tokens=0, cost_usd=0.0,
    )


def test_estimate_cost_uses_frozen_p1_pricing() -> None:
    est = evaluator.estimate_cost_usd(1_000_000, 0)
    assert abs(est - 0.30) < 1e-6
    est2 = evaluator.estimate_cost_usd(0, 1_000_000)
    assert abs(est2 - 1.00) < 1e-6
