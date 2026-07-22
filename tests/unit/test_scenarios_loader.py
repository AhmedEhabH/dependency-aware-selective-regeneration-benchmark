from pathlib import Path

import pytest
import yaml

from benchmark.core.exceptions import ScenarioError
from benchmark.scenarios.loader import ScenarioLoader

SAMPLE_SCENARIO_YAML = {
    "scenario_id": "todo-loc-001",
    "repository": "todo",
    "change_type": "Schema and field changes",
    "blast_radius": "localized",
    "requirement_before": "Old behavior description",
    "requirement_after": "New behavior description",
    "rationale": "Test rationale",
    "acceptance_criteria": [
        "Task model has a priority field",
        "TaskSerializer.priority is a read-write ChoiceField",
    ],
    "expected_affected_artifacts": [
        "todo/models.py:Task (add priority field)",
        "todo/serializers.py:TaskSerializer (add priority field)",
    ],
    "expected_actions": {
        "todo/models.py:Task": "modify",
        "todo/serializers.py:TaskSerializer": "modify",
    },
    "regression_obligations": [
        "todo/tests/test_models.py",
        "todo/tests/test_serializers.py",
    ],
    "architecture_constraints": [
        "No changes to views.py, urls.py, permissions.py",
    ],
    "hidden_tests": [
        {"description": "Regression test", "type": "regression"},
    ],
}


class TestScenarioLoader:
    def test_init(self, tmp_path: Path) -> None:
        loader = ScenarioLoader(tmp_path)
        assert loader is not None

    def test_load_scenario(self, tmp_path: Path) -> None:
        scenario_file = tmp_path / "test_scenario.yaml"
        scenario_file.write_text(yaml.dump(SAMPLE_SCENARIO_YAML), encoding="utf-8")

        loader = ScenarioLoader(tmp_path)
        scenario = loader.load_scenario(scenario_file)
        assert scenario.scenario_id == "todo-loc-001"
        assert scenario.repository == "todo"
        assert len(scenario.acceptance_criteria) == 2
        assert len(scenario.expected_affected_artifacts) == 2
        assert len(scenario.expected_actions) == 2

    def test_load_nonexistent_file_raises(self, tmp_path: Path) -> None:
        loader = ScenarioLoader(tmp_path)
        with pytest.raises(ScenarioError, match="not found"):
            loader.load_scenario(tmp_path / "nonexistent.yaml")

    def test_load_invalid_yaml_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.yaml"
        f.write_text(": broken yaml [", encoding="utf-8")
        loader = ScenarioLoader(tmp_path)
        with pytest.raises(ScenarioError, match="Failed to parse"):
            loader.load_scenario(f)

    def test_load_scalar_yaml_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "scalar.yaml"
        f.write_text("just a string", encoding="utf-8")
        loader = ScenarioLoader(tmp_path)
        with pytest.raises(ScenarioError, match="must be a mapping"):
            loader.load_scenario(f)

    def test_load_all(self, tmp_path: Path) -> None:
        for i in range(3):
            data = dict(SAMPLE_SCENARIO_YAML)
            data["scenario_id"] = f"test-{i:03d}"
            if i == 1:
                data["repository"] = "other"
            (tmp_path / f"scenario_{i:03d}.yaml").write_text(
                yaml.dump(data), encoding="utf-8"
            )

        loader = ScenarioLoader(tmp_path)
        scenarios = loader.load_all()
        assert len(scenarios) == 3
        ids = [s.scenario_id for s in scenarios]
        assert "test-000" in ids
        assert "test-001" in ids
        assert "test-002" in ids

    def test_load_all_no_scenarios_raises(self, tmp_path: Path) -> None:
        loader = ScenarioLoader(tmp_path)
        with pytest.raises(ScenarioError, match="No scenario files found"):
            loader.load_all()

    def test_load_by_repository(self, tmp_path: Path) -> None:
        for i in range(4):
            data = dict(SAMPLE_SCENARIO_YAML)
            data["scenario_id"] = f"test-{i:03d}"
            data["repository"] = "todo" if i < 2 else "djangocms"
            (tmp_path / f"scenario_{i:03d}.yaml").write_text(
                yaml.dump(data), encoding="utf-8"
            )

        loader = ScenarioLoader(tmp_path)
        todo_scenarios = loader.load_by_repository("todo")
        assert len(todo_scenarios) == 2
        djangocms_scenarios = loader.load_by_repository("djangocms")
        assert len(djangocms_scenarios) == 2
