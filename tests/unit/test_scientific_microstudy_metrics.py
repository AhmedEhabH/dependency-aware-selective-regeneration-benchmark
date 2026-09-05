from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"

# Ad-hoc in-process import (tests do not rely on the package being installed).
_SPEC = importlib.util.spec_from_file_location(
    "build_todo_microstudy_results", SCRIPTS_DIR / "build_todo_microstudy_results.py"
)
_MOD = importlib.util.module_from_spec(_SPEC)
sys.modules["build_todo_microstudy_results"] = _MOD
_spec = _SPEC
assert _spec.loader is not None
_spec.loader.exec_module(_MOD)

FIVE_FILE_UNIVERSE = _MOD.FIVE_FILE_UNIVERSE


def _gold(scenario_id: str) -> tuple[set[str], set[str]]:
    return _MOD.gold_sets_for_scenario(scenario_id)


GOLD_001 = {
    "gold_regen": {"todo/models.py", "todo/serializers.py", "todo/views.py"},
    "gold_preserve": {"todo/permissions.py", "todo/urls.py"},
}


class TestGoldSets:
    def test_five_file_universe_exact(self) -> None:
        assert {
            "todo/models.py",
            "todo/serializers.py",
            "todo/views.py",
            "todo/permissions.py",
            "todo/urls.py",
        } == FIVE_FILE_UNIVERSE

    def test_smoke_001_gold_sets(self) -> None:
        regen, preserve = _MOD.gold_sets_for_scenario("todo-smoke-001")
        assert regen == GOLD_001["gold_regen"]
        assert preserve == GOLD_001["gold_preserve"]

    def test_smoke_002_gold_sets(self) -> None:
        regen, preserve = _MOD.gold_sets_for_scenario("todo-smoke-002")
        assert regen == {"todo/models.py", "todo/views.py"}
        assert preserve == {"todo/serializers.py", "todo/permissions.py", "todo/urls.py"}

    def test_smoke_003_gold_sets(self) -> None:
        regen, preserve = _MOD.gold_sets_for_scenario("todo-smoke-003")
        assert regen == {"todo/models.py", "todo/serializers.py", "todo/permissions.py", "todo/views.py"}
        assert preserve == {"todo/urls.py"}


def _record(
    scenario_id: str,
    strategy: str,
    rep: int,
    *,
    evaluator_passed: bool | None,
    baseline_passed: bool | None,
    predicted: dict[str, str],
    changed: list[str],
    mig_pass: bool | None = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    model_calls: int = 0,
    selected: int = 0,
    regenerated: int = 0,
) -> _MOD.RunRecordData:
    return _MOD.RunRecordData(
        run_id=f"{scenario_id}_{strategy}_rep{rep}_x",
        profile="scientific-microstudy-01",
        repository_id="todo",
        scenario_id=scenario_id,
        strategy_id=strategy,
        repetition=rep,
        seed=42,
        status="succeeded",
        scenario_evaluator_passed=evaluator_passed,
        baseline_validation_passed=baseline_passed,
        migration_generation_passed=mig_pass,
        predicted_actions=dict(predicted),
        changed_artifact_paths=list(changed),
        selection_prompt_tokens=prompt_tokens,
        selection_completion_tokens=0,
        regeneration_prompt_tokens=0,
        regeneration_completion_tokens=completion_tokens,
        repair_prompt_tokens=0,
        repair_completion_tokens=0,
        total_workflow_tokens=prompt_tokens + completion_tokens,
        total_workflow_model_calls=model_calls,
        selected_artifact_count=selected,
        regenerated_artifact_count=regenerated,
    )


class TestRunMetrics:
    def test_perfect_selective_run(self) -> None:
        r = _record(
            "todo-smoke-001", "selective", 1,
            evaluator_passed=True, baseline_passed=True,
            predicted={
                "todo/models.py": "regenerate",
                "todo/serializers.py": "regenerate",
                "todo/views.py": "regenerate",
                "todo/permissions.py": "preserve",
                "todo/urls.py": "preserve",
            },
            changed=["todo/models.py", "todo/serializers.py", "todo/views.py"],
            mig_pass=True,
        )
        m = _MOD.compute_run_metrics(r, "todo-smoke-001")
        assert m["changed_requirement_pass"] is True
        assert m["baseline_pass"] is True
        assert m["impact_recall"] == 1.0
        assert m["unintended_preserve_changes"] == []
        assert m["preservation_pass"] is True
        assert m["migration_generation_passed"] is True

    def test_missing_regenerate_lowers_recall(self) -> None:
        r = _record(
            "todo-smoke-001", "selective", 1,
            evaluator_passed=True, baseline_passed=True,
            predicted={
                "todo/models.py": "regenerate",
                "todo/serializers.py": "regenerate",
                "todo/permissions.py": "preserve",
                "todo/urls.py": "preserve",
            },
            changed=["todo/models.py", "todo/serializers.py"],
        )
        m = _MOD.compute_run_metrics(r, "todo-smoke-001")
        # missing todo/views.py in predicted regenerate-set -> recall < 1.0
        assert m["impact_recall"] == 2 / 3

    def test_unintended_preserve_change_fails_preservation(self) -> None:
        r = _record(
            "todo-smoke-001", "selective", 1,
            evaluator_passed=True, baseline_passed=True,
            predicted={
                "todo/models.py": "regenerate",
                "todo/serializers.py": "regenerate",
                "todo/views.py": "regenerate",
                "todo/urls.py": "preserve",
            },
            changed=["todo/models.py", "todo/permissions.py"],
        )
        m = _MOD.compute_run_metrics(r, "todo-smoke-001")
        assert m["unintended_preserve_changes"] == ["todo/permissions.py"]
        assert m["preservation_pass"] is False

    def test_migration_excluded_from_strategy_recall_denominator(self) -> None:
        # Migration path appears in predicted_actions? (should not normally) but is excluded.
        r = _record(
            "todo-smoke-001", "selective", 1,
            evaluator_passed=True, baseline_passed=True,
            predicted={
                "todo/models.py": "regenerate",
                "todo/serializers.py": "regenerate",
                "todo/views.py": "regenerate",
                "todo/migrations/": "regenerate",
            },
            changed=["todo/models.py"],
            mig_pass=True,
        )
        m = _MOD.compute_run_metrics(r, "todo-smoke-001")
        assert "todo/migrations/" not in [p for p in m["predicted_regenerate_source_paths"]]
        assert set(m["gold_regenerate_source_paths"]) == GOLD_001["gold_regen"]


class TestScenarioStragglers:
    def _selective_5(self, passes: int) -> list:
        return [
            _record(
                "todo-smoke-001", "selective", i + 1,
                evaluator_passed=(i < passes), baseline_passed=True,
                predicted=_MOD.PERFECT_001_PREDICTED,
                changed=list(GOLD_001["gold_regen"]),
                mig_pass=True,
            )
            for i in range(5)
        ]

    def test_4_of_5_passes_for_scenario(self) -> None:
        ev = _MOD.evaluate_scenario(
            scenario_id="todo-smoke-001",
            agent_records=self._selective_5(5),
            selective_records=self._selective_5(4),
        )
        assert ev["G1"]["selective"] is True
        assert ev["G1"]["agent"] is True
        assert ev["G1"]["selective_ge_4_5"] is True
        assert ev["G1"]["agent_not_worse_by_more_than_1"] is True
        assert ev["G2"]["preservation_4_5"] is True
        assert ev["G3"]["recall_4_5"] is True

    def test_agent_lead_by_more_than_1_fails_g1(self) -> None:
        ev = _MOD.evaluate_scenario(
            scenario_id="todo-smoke-001",
            agent_records=self._selective_5(5),
            selective_records=self._selective_5(3),
        )
        assert ev["G1"]["selective"] is False
        assert ev["G1"]["selective_ge_4_5"] is False
        assert ev["G1"]["agent_not_worse_by_more_than_1"] is False

    def test_agent_lead_by_exactly_1_passes_g1(self) -> None:
        ev = _MOD.evaluate_scenario(
            scenario_id="todo-smoke-001",
            agent_records=self._selective_5(5),
            selective_records=self._selective_5(4),
        )
        assert ev["G1"]["selective"] is True

    def test_g3_recall_below_threshold(self) -> None:
        records = []
        for i in range(5):
            predicted = dict(_MOD.PERFECT_001_PREDICTED)
            if i == 0:
                del predicted["todo/views.py"]
            records.append(
                _record(
                    "todo-smoke-001", "selective", i + 1,
                    evaluator_passed=True, baseline_passed=True,
                    predicted=predicted,
                    changed=list(GOLD_001["gold_regen"]) if i > 0 else ["todo/models.py"],
                    mig_pass=True,
                )
            )
        ev = _MOD.evaluate_scenario(
            scenario_id="todo-smoke-001",
            agent_records=self._selective_5(5),
            selective_records=records,
        )
        # recall 1.0 in 4/5, missing in 1/5 -> passes 4/5
        assert ev["G3"]["recall_4_5"] is True


class TestStudyDecision:
    def test_study_go_all_gates_clear(self) -> None:
        scenario_results = {
            "todo-smoke-001": {"G1": {"selective": True}, "G2": True, "G3": True},
            "todo-smoke-002": {"G1": {"selective": True}, "G2": True, "G3": True},
            "todo-smoke-003": {"G1": {"selective": True}, "G2": True, "G3": True},
        }
        decision = _MOD.compute_study_decision(scenario_results)
        assert decision["go"] is True
        assert decision["requirement"] == "all 3 clear G1 AND G2 AND at least 2/3 clear G3"

    def test_study_no_go_missing_one_scenario_g3(self) -> None:
        scenario_results = {
            "todo-smoke-001": {"G1": {"selective": True}, "G2": True, "G3": True},
            "todo-smoke-002": {"G1": {"selective": True}, "G2": True, "G3": False},
            "todo-smoke-003": {"G1": {"selective": True}, "G2": True, "G3": True},
        }
        decision = _MOD.compute_study_decision(scenario_results)
        # 2/3 clear G3 -> GO qualifies on G3 branch but all G1/G2 must clear.
        assert decision["go"] is True

    def test_study_no_go_two_scenarios_missing_g3(self) -> None:
        scenario_results = {
            "todo-smoke-001": {"G1": {"selective": True}, "G2": True, "G3": True},
            "todo-smoke-002": {"G1": {"selective": True}, "G2": True, "G3": False},
            "todo-smoke-003": {"G1": {"selective": True}, "G2": True, "G3": False},
        }
        decision = _MOD.compute_study_decision(scenario_results)
        assert decision["go"] is False
        assert decision["reason"] == "impact recall cleared in fewer than 2/3 scenarios; study NO-GO"

    def test_study_no_go_one_scenario_g1_fails(self) -> None:
        scenario_results = {
            "todo-smoke-001": {"G1": {"selective": True}, "G2": True, "G3": True},
            "todo-smoke-002": {"G1": {"selective": False}, "G2": True, "G3": True},
            "todo-smoke-003": {"G1": {"selective": True}, "G2": True, "G3": True},
        }
        decision = _MOD.compute_study_decision(scenario_results)
        assert decision["go"] is False

    def test_study_no_go_one_scenario_g2_fails(self) -> None:
        scenario_results = {
            "todo-smoke-001": {"G1": {"selective": True}, "G2": True, "G3": True},
            "todo-smoke-002": {"G1": {"selective": True}, "G2": False, "G3": True},
            "todo-smoke-003": {"G1": {"selective": True}, "G2": True, "G3": True},
        }
        decision = _MOD.compute_study_decision(scenario_results)
        assert decision["go"] is False
