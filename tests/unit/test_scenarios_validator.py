import pytest

from benchmark.core.enums import ActionKind, ArtifactType, BlastRadius
from benchmark.core.exceptions import ScenarioError
from benchmark.core.models import ArtifactRef, Scenario
from benchmark.scenarios.validator import ScenarioValidator


def _make_any_scenario(**overrides: object) -> Scenario:
    defaults: dict[str, object] = {
        "scenario_id": "test-001",
        "repository": "todo",
        "change_type": "Schema change",
        "blast_radius": BlastRadius.localized,
        "requirement_before": "old behavior",
        "requirement_after": "new behavior",
        "rationale": "test rationale",
    }
    defaults.update(overrides)
    s = object.__new__(Scenario)
    for k, v in defaults.items():
        object.__setattr__(s, k, v)
    if "expected_actions" not in overrides:
        object.__setattr__(s, "expected_actions", ())
    if "expected_affected_artifacts" not in overrides:
        object.__setattr__(s, "expected_affected_artifacts", ())
    if "acceptance_criteria" not in overrides:
        object.__setattr__(s, "acceptance_criteria", ())
    if "architecture_constraints" not in overrides:
        object.__setattr__(s, "architecture_constraints", ())
    if "hidden_tests" not in overrides:
        object.__setattr__(s, "hidden_tests", ())
    return s


class TestScenarioValidator:
    def test_valid_scenario_passes(self) -> None:
        validator = ScenarioValidator()
        scenario = _make_any_scenario()
        errors = validator.validate(scenario)
        assert errors == []

    def test_empty_scenario_id_fails(self) -> None:
        validator = ScenarioValidator()
        scenario = _make_any_scenario(scenario_id="")
        with pytest.raises(ScenarioError, match="validation failed"):
            validator.validate(scenario)

    def test_empty_repository_fails(self) -> None:
        validator = ScenarioValidator()
        scenario = _make_any_scenario(repository="")
        with pytest.raises(ScenarioError) as exc:
            validator.validate(scenario)
        errors = (exc.value.context or {}).get("errors", [])
        assert any("repository" in e for e in errors)

    def test_empty_requirement_before_fails(self) -> None:
        validator = ScenarioValidator()
        scenario = _make_any_scenario(requirement_before="")
        with pytest.raises(ScenarioError) as exc:
            validator.validate(scenario)
        errors = (exc.value.context or {}).get("errors", [])
        assert any("requirement_before" in e for e in errors)

    def test_empty_requirement_after_fails(self) -> None:
        validator = ScenarioValidator()
        scenario = _make_any_scenario(requirement_after="")
        with pytest.raises(ScenarioError) as exc:
            validator.validate(scenario)
        errors = (exc.value.context or {}).get("errors", [])
        assert any("requirement_after" in e for e in errors)

    def test_duplicate_expected_actions_fails(self) -> None:
        validator = ScenarioValidator()
        ref = ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source)
        scenario = _make_any_scenario(
            expected_actions=(
                (ref, ActionKind.regenerate),
                (ref, ActionKind.regenerate),
            ),
        )
        with pytest.raises(ScenarioError) as exc:
            validator.validate(scenario)
        errors = (exc.value.context or {}).get("errors", [])
        assert any("Duplicate" in e for e in errors)

    def test_validate_all_returns_errors(self) -> None:
        validator = ScenarioValidator()
        valid = _make_any_scenario()
        invalid = _make_any_scenario(scenario_id="")
        results = validator.validate_all([valid, invalid])
        assert len(results) == 1
        assert results[0][0] == ""
        assert "scenario_id" in str(results[0][1])
