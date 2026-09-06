"""Focused tests for the STAGE-C consolidation analysis scripts.

Covers:
- v1.1 root-cause classifier deterministic rules (frozen classes A-I)
- v1.1 reproduced frozen counts (overall / by-arm / by-scenario)
- latency aggregation (mean/median/p90/max, call-equivalent, outliers)
- Truth Matrix source-data consistency

No model calls. Raw evidence files are read-only.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_stagec_latency import aggregate  # noqa: E402
from analyze_v11_root_causes import CLASS_LABELS, classify_run  # noqa: E402


def _detail(stage: str, kind: str, msg: str) -> dict:
    return {"stage": stage, "kind": kind, "message": msg, "details": ""}


class TestClassifierRules:
    def test_selection_control(self) -> None:
        rec = {"failure_details": [_detail("analyze_impact", "model_output", "planner error")]}
        cls, stage, _ = classify_run(rec)
        assert cls == "A"
        assert stage == "analyze_impact"

    def test_generation_structured_output(self) -> None:
        rec = {"failure_details": [_detail("generation_guard", "build", "no generated source")]}
        cls, stage, _ = classify_run(rec)
        assert cls == "B"
        assert stage == "generation_guard"

    def test_exact_patch_application(self) -> None:
        rec = {"failure_details": [
            _detail("regeneration", "model_output",
                    "exact_patch_failed: todo/models.py: block 2: SEARCH content not found")
        ]}
        cls, _, _ = classify_run(rec)
        assert cls == "C"

    def test_syntax_static_validation(self) -> None:
        rec = {"failure_details": [
            _detail("regeneration", "model_output",
                    "artifact_contract_violation: todo/models.py: python_syntax_error: line 34")
        ]}
        cls, _, _ = classify_run(rec)
        assert cls == "D"

    def test_migration_runtime(self) -> None:
        rec = {"failure_details": [
            _detail("migration_generation", "build",
                    "Migration failed: exit=3; stdout: cannot add non-nullable field")
        ]}
        cls, _, _ = classify_run(rec)
        assert cls == "E"

    def test_functional_evaluator(self) -> None:
        rec = {"failure_details": [
            _detail("scenario_evaluator", "build", "Scenario evaluator failed; checks: a, b")
        ]}
        cls, _, _ = classify_run(rec)
        assert cls == "F"

    def test_human_review_without_earlier_cause_is_g(self) -> None:
        rec = {
            "failure_details": [
                _detail("human_review", "build", "ImpactPlan bounded expansion exhausted")
            ],
            "migration_generation_passed": None,
            "scenario_evaluator_passed": None,
            "scenario_evaluator_checks": [],
        }
        cls, _, _ = classify_run(rec)
        assert cls == "G"

    def test_human_review_with_migration_failure_is_e(self) -> None:
        rec = {
            "failure_details": [
                _detail("human_review", "build", "ImpactPlan bounded expansion exhausted")
            ],
            "migration_generation_passed": False,
            "scenario_evaluator_passed": None,
            "scenario_evaluator_checks": [],
        }
        cls, _, _ = classify_run(rec)
        assert cls == "E"

    def test_human_review_with_evaluator_failure_is_f(self) -> None:
        rec = {
            "failure_details": [
                _detail("human_review", "build", "ImpactPlan bounded expansion exhausted")
            ],
            "migration_generation_passed": True,
            "scenario_evaluator_passed": False,
            "scenario_evaluator_checks": ["a", "b"],
        }
        cls, _, _ = classify_run(rec)
        assert cls == "F"

    def test_earliest_causal_failure_wins(self) -> None:
        # Later exact-patch + human_review must not override the first migration failure.
        rec = {"failure_details": [
            _detail("migration_generation", "build", "Migration failed"),
            _detail("regeneration", "model_output", "exact_patch_failed"),
            _detail("human_review", "build", "bounded expansion exhausted"),
        ]}
        cls, _, _ = classify_run(rec)
        assert cls == "E"

    def test_frozen_class_labels_exact(self) -> None:
        assert list(CLASS_LABELS) == ["A", "B", "C", "D", "E", "F", "G", "H", "I"]


class TestReproducedV11Counts:
    @pytest.fixture(scope="class")
    @classmethod
    def rows_and_summary(cls):
        from analyze_v11_root_causes import build

        runs_path = ROOT / "reports" / "scientific_microstudy_v11" / "run_records.jsonl"
        return build(runs_path)

    def test_overall_counts_match_frozen(self, rows_and_summary) -> None:
        _, summary = rows_and_summary
        overall = summary["overall"]
        assert overall == {
            "A": 1, "B": 0, "C": 10, "D": 8, "E": 4, "F": 7, "G": 0, "H": 0, "I": 0,
        }

    def test_arm_counts_match_frozen(self, rows_and_summary) -> None:
        _, summary = rows_and_summary
        agent = {k.split("::")[1]: v for k, v in summary["arm"].items()
                 if k.startswith("iterative")}
        ip = {k.split("::")[1]: v for k, v in summary["arm"].items()
              if k.startswith("impact")}
        assert agent == {"C": 5, "D": 4, "E": 3, "F": 3}
        assert ip == {"A": 1, "C": 5, "D": 4, "E": 1, "F": 4}

    def test_scenario_counts_match_frozen(self, rows_and_summary) -> None:
        _, summary = rows_and_summary
        s001 = {k.split("::")[1]: v for k, v in summary["scenario"].items()
                if k.startswith("todo-smoke-001")}
        s002 = {k.split("::")[1]: v for k, v in summary["scenario"].items()
                if k.startswith("todo-smoke-002")}
        s003 = {k.split("::")[1]: v for k, v in summary["scenario"].items()
                if k.startswith("todo-smoke-003")}
        assert s001 == {"C": 3, "D": 7}
        assert s002 == {"A": 1, "C": 2, "F": 7}
        assert s003 == {"C": 5, "D": 1, "E": 4}

    def test_30_rows_exactly_one_class_each(self, rows_and_summary) -> None:
        rows, _ = rows_and_summary
        assert len(rows) == 30
        assert all(r["first_failure_class"] in CLASS_LABELS for r in rows)


class TestLatencyAggregation:
    def test_aggregate_known_synthetic(self) -> None:
        recs = [
            {"run_id": f"r{i}", "total_workflow_duration_seconds": d,
             "total_workflow_model_calls": c, "selection_tool_calls": t,
             "selection_tool_duration_seconds": 0.0,
             "token_usage": {"prompt": 10, "completion": 5, "total": 15}}
            for i, (d, c, t) in enumerate(
                [(10.0, 1, 3), (20.0, 2, 4), (30.0, 3, 5), (40.0, 4, 6)], start=1
            )
        ]
        agg = aggregate(recs)
        assert agg["n"] == 4
        assert agg["total_selection_duration"] == pytest.approx(100.0)
        assert agg["mean_run_duration"] == pytest.approx(25.0)
        assert agg["median_run_duration"] == pytest.approx(25.0)
        assert agg["p90_run_duration"] == pytest.approx(40.0)
        assert agg["max_run_duration"] == pytest.approx(40.0)
        assert agg["total_model_calls"] == 10
        assert agg["total_tool_calls"] == 18
        assert agg["total_prompt_tokens"] == 40
        assert agg["total_completion_tokens"] == 20
        assert agg["total_tokens"] == 60
        assert agg["call_equivalent_duration"] == pytest.approx(10.0)
        assert agg["top3_outlier_run_ids"][0]["run_id"] == "r4"

    def test_empty_records(self) -> None:
        agg = aggregate([])
        assert agg["n"] == 0
        assert agg["total_selection_duration"] == 0.0
        assert agg["median_run_duration"] == 0.0
        assert agg["call_equivalent_duration"] == 0.0
        assert agg["top3_outlier_run_ids"] == []


class TestTruthMatrixConsistency:
    def test_truth_matrix_embeds_frozen_numbers(self) -> None:
        text = (ROOT / "reports" / "RESEARCH_TRUTH_MATRIX.md").read_text(encoding="utf-8")
        for token in ("0.8778", "0.7694", "0.9200", "0.8540", "-72.98%", "-86.36%",
                      "-47.51%", "60/60", "30/30", "C=10", "D=8", "E=4", "F=7",
                      "236.162", "490.108", "149.468", "111.406"):
            assert token in text, token

    def test_raw_evidence_untouched_by_git(self) -> None:
        for path in (
            "reports/scientific_microstudy_v11/run_records.jsonl",
            "reports/scientific_stagec_selection_01/run_records.jsonl",
            "reports/scientific_stagec_heldout_01/run_records.jsonl",
            "reports/STAGEC_SELECTION_01_RESULTS.csv",
            "reports/STAGEC_HELDOUT_01_RESULTS.csv",
        ):
            proc = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", path],
                                  cwd=ROOT, capture_output=True, text=True)
            assert proc.returncode == 0, f"{path} modified vs HEAD"


class TestScriptsRunEndToEnd:
    def test_v11_script_emits_reports(self, tmp_path: Path) -> None:
        runs = ROOT / "reports" / "scientific_microstudy_v11" / "run_records.jsonl"
        csv_p = tmp_path / "t.csv"
        md_p = tmp_path / "t.md"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "analyze_v11_root_causes.py"),
             str(runs), str(csv_p), str(md_p)],
            cwd=ROOT, capture_output=True, text=True, timeout=300,
        )
        assert proc.returncode == 0, proc.stderr[-1000:]
        assert csv_p.is_file() and md_p.is_file()
        assert "V11_ROOT_CAUSE_TAXONOMY_READY" in proc.stdout

    def test_latency_script_emits_reports(self, tmp_path: Path) -> None:
        smoke = ROOT / "reports" / "scientific_stagec_selection_01" / "run_records.jsonl"
        held = ROOT / "reports" / "scientific_stagec_heldout_01" / "run_records.jsonl"
        csv_p = tmp_path / "l.csv"
        md_p = tmp_path / "l.md"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "analyze_stagec_latency.py"),
             str(smoke), str(held), str(csv_p), str(md_p)],
            cwd=ROOT, capture_output=True, text=True, timeout=300,
        )
        assert proc.returncode == 0, proc.stderr[-1000:]
        assert csv_p.is_file() and md_p.is_file()
        assert "STAGEC_LATENCY_DECOMPOSITION_READY" in proc.stdout
