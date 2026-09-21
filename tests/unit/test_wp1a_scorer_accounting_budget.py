"""WP-1a shared scorer + accounting + budget tests (AC-1A.7/8/9)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
if str(PROJECT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.wp1a.accounting import (  # noqa: E402
    ArmEfficiency,
    rmcss_marginal_view,
    rmcss_setup_view,
)
from benchmark.wp1a.budget import ABORT_LABEL, project_agent_cost  # noqa: E402
from benchmark.wp1a.scorer import (  # noqa: E402
    ArmConfusion,
    assert_identical_task_ids,
    paired_bootstrap_delta_f1,
    per_task_confusion,
    score_arm,
)

WP1A = PROJECT_DIR / "research" / "wp1a"


class TestScorer:
    def test_confusion_components(self) -> None:
        c = per_task_confusion({"a", "b"}, {"a", "c"})
        assert (c.tp, c.fp, c.fn) == (1, 1, 1)
        assert abs(c.f1 - 0.5) < 1e-12
        assert abs(c.precision - 0.5) < 1e-12
        assert abs(c.recall - 0.5) < 1e-12

    def test_score_arm_metrics(self) -> None:
        pred = {"t1": {"a", "b"}, "t2": set()}
        labels = {"t1": {"a", "c"}, "t2": {"d"}}
        m = score_arm(pred, labels, ["t1", "t2"])
        assert m["tp"] == 1 and m["fp"] == 1 and m["fn"] == 2
        assert m["empty_set_rate"] == 0.5
        assert m["mean_predicted_set_size"] == 1.0

    def test_identical_task_ids(self) -> None:
        ids = assert_identical_task_ids({"a", "b"}, {"b", "a"}, {"a", "b"})
        assert ids == ["a", "b"]

    def test_paired_bootstrap_reproducible(self) -> None:
        a = [ArmConfusion(1, 0, 0), ArmConfusion(1, 1, 1), ArmConfusion(0, 1, 1)]
        b = [ArmConfusion(1, 1, 0), ArmConfusion(0, 0, 2), ArmConfusion(1, 0, 1)]
        r1 = paired_bootstrap_delta_f1(a, b, n_resamples=500)
        r2 = paired_bootstrap_delta_f1(a, b, n_resamples=500)
        assert r1["delta_f1_point"] == r2["delta_f1_point"]
        assert r1["n_resamples"] == 500
        assert r1["seed"] == 20260920


class TestAccounting:
    def test_arm_effciency_record(self) -> None:
        arm = ArmEfficiency(arm="sip", prompt_tokens=1000, completion_tokens=100,
                            total_tokens=1100, model_calls=1, wall_seconds=3.0,
                            usd_cost=0.01)
        rec = arm.record(n_tasks=50)
        assert rec["total_tokens"] == 1100
        assert rec["mean_per_task_tokens"] == 22.0
        assert rec["mean_per_task_usd"] == 0.0002

    def test_marginal_view_no_double_count(self) -> None:
        v = rmcss_marginal_view(sip_inference_cost_usd=1.0,
                                query_embedding_incremental_cost_usd=0.02,
                                dense_incremental_cost_usd=0.0,
                                memory_lookup_incremental_cost_usd=0.0,
                                classifier_incremental_cost_usd=0.0,
                                n_tasks=300)
        assert v["total_marginal_usd"] == 1.02
        assert "NOT re-charged" in v["note_no_double_counting"]

    def test_setup_view_amortized(self) -> None:
        v = rmcss_setup_view(embedding_corpus_index_build_usd=0.20,
                             repository_memory_index_build_usd=0.0,
                             setup_wall_seconds=3600.0,
                             setup_compute_provenance="local")
        assert abs(v["amortized_at_n50_usd_per_task"] - 0.004) < 1e-9
        assert abs(v["amortized_at_n300_usd_per_task"] - 0.0006666666666) < 1e-6


class TestBudget:
    def test_budget_model_inputs(self) -> None:
        b = project_agent_cost()
        assert b["main_n"] == 50
        assert b["calibration_n"] == 3
        assert b["max_calls_per_task"] == 8
        assert b["completion_cap"] == 512
        assert b["calibration_cannot_prove_worst_case"] is True
        assert ABORT_LABEL in b["abort_rule"]

    def test_budget_ceiling_recommended_not_auto_accepted(self) -> None:
        b = project_agent_cost()
        assert "RECOMMENDED_FOR_AHMED_REVIEW" in b["ceiling_status"]

    def test_budget_model_json(self) -> None:
        b = json.loads((WP1A / "wp1a_budget_model.json").read_text(encoding="utf-8"))
        assert b["wp1a"] == "wp1a_budget_model"
        assert b["main_n"] == 50
        assert b["recommended_ceiling_usd"] > 0


class TestAccountingSchemaJson:
    def test_schema_json(self) -> None:
        s = json.loads((WP1A / "wp1a_accounting_schema.json").read_text(encoding="utf-8"))
        assert "total_tokens" in s["per_arm_fields"]
        assert "rmcss_two_views_rule" in s
        assert "latency_provenance_rule" in s
