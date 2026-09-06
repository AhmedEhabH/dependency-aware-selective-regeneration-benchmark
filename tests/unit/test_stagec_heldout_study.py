"""Focused tests for STAGE-C-HELDOUT-CHALLENGE-01 (D053) held-out selection study.

Covers the 12 focused test items from ``04_TESTS_SIX_GATES_AND_AUDIT.md``:

  1. profile topology = 6 x 2 x 5 = 60
  2. exact six scenario IDs frozen in the pack
  3. selection_only=true for new profile (CLI dry-run uses selection-only path)
  4. scientific_gold_isolation=true for new profile (runner flag wired)
  5. gold expected_actions absent from Agent prompt
  6. gold expected_actions absent from ImpactPlan prompt/evidence
  7. no scenario visible requirement contains todo/, .py, models.py,
     serializers.py, views.py, permissions.py, urls.py
  8. each hidden gold set is non-empty and within the five-file universe
  9. all six scenarios have architecture_constraints: []
 10. result builder known synthetic metrics exact
 11. result builder reports both arm aggregates correctly
 12. historical Stage-C and v1.1 reports remain untouched

These tests reuse the selection-only runner semantics already covered in
``test_stagec_selection_study.py``; this module focuses on the held-out profile
wiring and the frozen held-out dataset.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from seven_arm_benchmark import PROFILES, resolve_profile_protocol

ROOT = Path(__file__).resolve().parent.parent.parent
SCENARIOS_DIR = ROOT / "benchmark_data" / "scenarios"
REPORTS_DIR = ROOT / "reports"

HELDOUT_IDS = [f"todo-heldout-{i:03d}" for i in range(1, 7)]

FIVE_FILE_UNIVERSE = {
    "todo/models.py",
    "todo/serializers.py",
    "todo/views.py",
    "todo/permissions.py",
    "todo/urls.py",
}

FORBIDDEN_TOKENS = (
    "todo/",
    ".py",
    "models.py",
    "serializers.py",
    "views.py",
    "permissions.py",
    "urls.py",
)

EXPECTED_GOLD = {
    "todo-heldout-001": {"todo/models.py", "todo/serializers.py"},
    "todo-heldout-002": {"todo/views.py"},
    "todo-heldout-003": {"todo/models.py", "todo/serializers.py", "todo/views.py"},
    "todo-heldout-004": {"todo/models.py"},
    "todo-heldout-005": {"todo/permissions.py", "todo/views.py"},
    "todo-heldout-006": {"todo/models.py", "todo/serializers.py", "todo/permissions.py"},
}


def _load_heldout_yamls() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for sid in HELDOUT_IDS:
        raw = (SCENARIOS_DIR / f"{sid}.yaml").read_text(encoding="utf-8")
        out[sid] = yaml.safe_load(raw)
    return out


class TestTopology:
    def test_60_cell_topology(self) -> None:
        profile = PROFILES["scientific-stagec-heldout-01"]
        assert profile.scenario_count == 6
        assert set(profile.strategies) == {"iterative_repository_agent", "impact_plan"}
        assert profile.repetitions == 5
        total = profile.scenario_count * len(profile.strategies) * profile.repetitions
        assert total == 60
        assert profile.repository_names == ["todo"]

    def test_exact_six_heldout_ids(self) -> None:
        profile = PROFILES["scientific-stagec-heldout-01"]
        assert profile.scenario_ids == HELDOUT_IDS

    def test_profile_protocol_resolution(self) -> None:
        assert resolve_profile_protocol("scientific-stagec-heldout-01") == "scientific-stagec-heldout-01"

    def test_profile_is_not_publication(self) -> None:
        assert PROFILES["scientific-stagec-heldout-01"].is_publication is False

    def test_profile_timeout_900(self) -> None:
        assert PROFILES["scientific-stagec-heldout-01"].timeout_seconds == 900


class TestSelectionOnlyWiring:
    def test_cli_dryrun_agent_record_is_selection_only(self, tmp_path: Path) -> None:
        out = tmp_path / "agent"
        cmd = [
            sys.executable, str(ROOT / "seven_arm_benchmark.py"),
            "--profile", "scientific-stagec-heldout-01",
            "--strategy", "iterative_repository_agent",
            "--dry-run", "--output-dir", str(out), "--max-runs", "1",
        ]
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900)
        assert proc.returncode == 0, proc.stderr[-2000:]
        records = _read_jsonl(out / "run_records.jsonl")
        assert len(records) == 1
        rec = records[0]
        assert rec["status"] == "succeeded"
        assert rec["profile"] == "scientific-stagec-heldout-01"
        assert rec["protocol_version"] == "scientific-stagec-heldout-01"
        # Selection-only: no regeneration/repair path ever contributes.
        assert int(rec.get("regeneration_model_calls", 0)) == 0
        assert int(rec.get("repair_model_calls", 0)) == 0
        assert int(rec.get("total_workflow_model_calls", 0)) == 0  # mock: no calls
        # Selection-only record shape: selection counters exist on the record.
        assert "selection_model_calls" in rec
        assert "selection_total_tokens" in rec
        sid = json.loads((out / "source_identity.json").read_text(encoding="utf-8"))
        assert sid["profile"] == "scientific-stagec-heldout-01"
        assert str(sid["agent_control_max_completion_tokens"]) == "1024"

    def test_cli_dryrun_impactplan_record_is_selection_only(self, tmp_path: Path) -> None:
        out = tmp_path / "impact"
        cmd = [
            sys.executable, str(ROOT / "seven_arm_benchmark.py"),
            "--profile", "scientific-stagec-heldout-01",
            "--strategy", "impact_plan",
            "--dry-run", "--output-dir", str(out), "--max-runs", "1",
        ]
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900)
        assert proc.returncode == 0, proc.stderr[-2000:]
        records = _read_jsonl(out / "run_records.jsonl")
        assert len(records) == 1
        rec = records[0]
        assert rec["status"] == "succeeded"
        assert rec["profile"] == "scientific-stagec-heldout-01"
        assert rec["protocol_version"] == "scientific-stagec-heldout-01"
        assert int(rec.get("regeneration_model_calls", 0)) == 0
        assert int(rec.get("repair_model_calls", 0)) == 0
        # No evaluator/migration stage in selection-only.
        assert int(rec.get("migration_duration_seconds") or 0) == 0
        assert "selection_model_calls" in rec

    def test_runner_config_selection_only_available(self) -> None:
        from benchmark.execution.runner import RunnerConfig

        cfg = RunnerConfig(
            strategy_name="iterative_repository_agent",
            backend_name="openrouter",
            protocol_version="scientific-stagec-heldout-01",
            selection_only=True,
            scientific_gold_isolation=True,
            editable_artifact_paths=tuple(sorted(FIVE_FILE_UNIVERSE)),
        )
        assert cfg.selection_only is True
        assert cfg.scientific_gold_isolation is True


def _read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


class TestNoGoldLeakage:
    def test_agent_prompt_has_no_gold(self) -> None:
        from benchmark.strategies.iterative_agent import INITIAL_SYSTEM_PROMPT

        assert "expected_actions" not in INITIAL_SYSTEM_PROMPT
        assert "GOLD_SENTINEL" not in INITIAL_SYSTEM_PROMPT
        assert "todo-heldout" not in INITIAL_SYSTEM_PROMPT

    def test_planner_prompt_has_no_gold(self) -> None:
        from benchmark.selection.impact_planner import PLANNER_PROMPT_TEMPLATE

        assert "expected_actions" not in PLANNER_PROMPT_TEMPLATE
        assert "GOLD_SENTINEL" not in PLANNER_PROMPT_TEMPLATE
        assert "todo-heldout" not in PLANNER_PROMPT_TEMPLATE


class TestHeldOutDataset:
    def test_no_visible_source_file_names(self) -> None:
        data = _load_heldout_yamls()
        for sid, sc in data.items():
            visible = "\n".join(
                (str(sc["requirement_before"]),
                 str(sc["requirement_after"]),
                 str(sc["rationale"]),
                 str(sc["acceptance_criteria"]))
            )
            hits = [t for t in FORBIDDEN_TOKENS if t in visible]
            assert not hits, f"{sid} leaks source-file tokens {hits}"

    def test_gold_nonempty_within_universe(self) -> None:
        data = _load_heldout_yamls()
        for sid in HELDOUT_IDS:
            actions = data[sid].get("expected_actions") or {}
            gold = set(actions.keys())
            assert gold, f"{sid} empty gold"
            assert gold <= FIVE_FILE_UNIVERSE, f"{sid} gold outside universe"

    def test_all_architecture_constraints_empty(self) -> None:
        data = _load_heldout_yamls()
        for sid in HELDOUT_IDS:
            assert data[sid].get("architecture_constraints") == [], sid

    def test_normalized_gold_matches_frozen_expected(self) -> None:
        from scripts.build_stagec_heldout_results import gold_for_scenario

        for sid in HELDOUT_IDS:
            assert gold_for_scenario(sid, SCENARIOS_DIR) == EXPECTED_GOLD[sid], sid


class TestResultBuilder:
    def _synthetic_records(self, tmp_path: Path) -> Path:
        import dataclasses

        from benchmark.checkpoint.persistence import RunRecordData
        from scripts.build_stagec_heldout_results import PROTOCOL

        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        arm_sets = {
            "iterative_repository_agent": {
                "todo/models.py": "regenerate",
                "todo/serializers.py": "regenerate",
                "todo/views.py": "preserve",
                "todo/urls.py": "preserve",
                "todo/permissions.py": "preserve",
            },
            "impact_plan": {
                "todo/models.py": "regenerate",
                "todo/serializers.py": "regenerate",
                "todo/views.py": "regenerate",
                "todo/urls.py": "preserve",
                "todo/permissions.py": "preserve",
            },
        }
        for arm, actions in arm_sets.items():
            impact_plan = None
            if arm == "impact_plan":
                impact_plan = {
                    "plan": {
                        "decisions": [
                            {"path": p, "action": a}
                            for p, a in actions.items()
                        ],
                        "context_set": ["todo/serializers.py"],
                        "write_set": [p for p, a in actions.items() if a == "regenerate"],
                    },
                    "final_after_expansion": False,
                }
            rec = RunRecordData(
                run_id=f"todo-heldout-003_{arm}_rep1_holdout",
                profile=PROTOCOL,
                repository_id="todo",
                scenario_id="todo-heldout-003",
                strategy_id=arm,
                repetition=1,
                seed=42,
                status="succeeded",
                protocol_version=PROTOCOL,
                config_hash="heldouthash",
                model_metadata={"model": "dry-run:mock"},
                token_usage={"prompt": 100, "completion": 20, "total": 120},
                selection_total_tokens=120,
                total_workflow_tokens=120,
                total_workflow_model_calls=1,
                total_workflow_duration_seconds=5.0,
                predicted_actions=actions,
                impact_plan=impact_plan,
                selection_study={
                    "initial_predicted_actions": actions,
                    "initial_regenerate_source_paths": [
                        p for p, a in actions.items() if a == "regenerate"
                    ],
                    "impact_plan_actions": actions if arm == "impact_plan" else {},
                    "context_set": ["todo/serializers.py"] if arm == "impact_plan" else [],
                    "validation_obligations": [],
                    "finish_reason": "stop",
                    "truncation": False,
                    "raw_response_sha256": [],
                    "failure_evidence": "",
                },
            )
            with open(runs_dir / "run_records.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(dataclasses.asdict(rec), sort_keys=True) + "\n")
        return runs_dir

    def test_builder_synthetic_metrics_exact(self, tmp_path: Path) -> None:
        from scripts.build_stagec_heldout_results import build

        runs_dir = self._synthetic_records(tmp_path)
        out = build(runs_dir, SCENARIOS_DIR, tmp_path / "reports")
        row = next(r for r in out["rows"] if r["strategy_id"] == "iterative_repository_agent")
        # heldout-003 gold = models + serializers + views.
        assert row["precision_mean"] == pytest.approx(1.0)
        assert row["recall_mean"] == pytest.approx(2 / 3)
        assert row["f1_mean"] == pytest.approx(0.8)
        assert row["fnr_mean"] == pytest.approx(1 / 3)
        assert row["valid_finals"] == 1
        assert row["tokens"] == 120
        assert row["model_calls"] == 1

    def test_builder_reports_both_arm_aggregates(self, tmp_path: Path) -> None:
        from scripts.build_stagec_heldout_results import build

        runs_dir = self._synthetic_records(tmp_path)
        out = build(runs_dir, SCENARIOS_DIR, tmp_path / "reports")
        assert len(out["agents"]) == 1
        assert len(out["impact_plans"]) == 1
        agent = out["agents"][0]
        plan = out["impact_plans"][0]
        assert agent["strategy_id"] == "iterative_repository_agent"
        assert plan["strategy_id"] == "impact_plan"
        assert agent["full_recall_count"] == 0
        assert plan["full_recall_count"] == 1
        assert plan["R"] == 3
        assert "impactplan_token_delta_pct" in out["deltas"]


class TestHistoricalUntouched:
    @pytest.mark.parametrize(
        "path",
        [
            "reports/STAGEC_SELECTION_01_RESULTS.csv",
            "reports/SCIENTIFIC_MICROSTUDY_V11_DECISION.md",
            "reports/scientific_stagec_selection_01/run_records.jsonl",
            "reports/scientific_microstudy_v11/run_records.jsonl",
        ],
    )
    def test_historical_files_unchanged(self, path: str) -> None:
        proc = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", path],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert proc.returncode == 0, f"{path} modified vs HEAD"
