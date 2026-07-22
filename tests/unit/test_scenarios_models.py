import pytest

from benchmark.core.enums import ActionKind, ArtifactType, BlastRadius
from benchmark.scenarios.models import ScenarioModel, _parse_action_kind, _parse_artifact_ref, _parse_blast_radius


class TestParseHelpers:
    def test_parse_blast_radius_valid(self) -> None:
        assert _parse_blast_radius("localized") == BlastRadius.localized
        assert _parse_blast_radius("moderate") == BlastRadius.moderate
        assert _parse_blast_radius("cross_cutting") == BlastRadius.cross_cutting

    def test_parse_blast_radius_invalid(self) -> None:
        with pytest.raises(ValueError, match="Invalid blast_radius"):
            _parse_blast_radius("unknown")

    def test_parse_artifact_ref_with_description(self) -> None:
        ref = _parse_artifact_ref("todo/models.py:Task (add priority field)")
        assert ref.path == "todo/models.py"
        assert ref.artifact_type == ArtifactType.source

    def test_parse_artifact_ref_config(self) -> None:
        ref = _parse_artifact_ref("config/settings.yaml")
        assert ref.path == "config/settings.yaml"
        assert ref.artifact_type == ArtifactType.configuration

    def test_parse_artifact_ref_doc(self) -> None:
        ref = _parse_artifact_ref("README.md")
        assert ref.path == "README.md"
        assert ref.artifact_type == ArtifactType.documentation

    def test_parse_artifact_ref_no_extension(self) -> None:
        ref = _parse_artifact_ref("manage.py")
        assert ref.path == "manage.py"
        assert ref.artifact_type == ArtifactType.source

    def test_parse_action_kind_valid(self) -> None:
        assert _parse_action_kind("modify") == ActionKind.regenerate
        assert _parse_action_kind("create") == ActionKind.regenerate
        with pytest.raises(ValueError):
            _parse_action_kind("")

    def test_parse_action_kind_standard(self) -> None:
        assert _parse_action_kind("regenerate") == ActionKind.regenerate
        assert _parse_action_kind("preserve") == ActionKind.preserve


class TestScenarioModel:
    def test_valid_creation(self) -> None:
        model = ScenarioModel(
            scenario_id="todo-loc-001",
            repository="todo",
            change_type="Schema and field changes",
            blast_radius="localized",
            requirement_before="The Task model has only basic fields",
            requirement_after="The Task model must gain a priority field",
            rationale="This is the simplest schema change",
            acceptance_criteria=("criterion 1",),
            expected_affected_artifacts=("todo/models.py:Task",),
            expected_actions={"todo/models.py:Task": "modify"},
            regression_obligations=("todo/tests/test_models.py",),
            architecture_constraints=("No changes to views.py",),
            hidden_tests=({"description": "Test 1", "type": "regression"},),
        )
        assert model.scenario_id == "todo-loc-001"
        assert model.repository == "todo"
        assert model.blast_radius == "localized"
        assert len(model.acceptance_criteria) == 1

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="ScenarioModel.scenario_id"):
            ScenarioModel(
                scenario_id="",
                repository="r",
                change_type="t",
                blast_radius="localized",
                requirement_before="b",
                requirement_after="a",
                rationale="x",
            )

    def test_empty_repository_raises(self) -> None:
        with pytest.raises(ValueError, match="ScenarioModel.repository"):
            ScenarioModel(
                scenario_id="s",
                repository="",
                change_type="t",
                blast_radius="localized",
                requirement_before="b",
                requirement_after="a",
                rationale="x",
            )

    def test_to_core_scenario(self) -> None:
        model = ScenarioModel(
            scenario_id="todo-loc-001",
            repository="todo",
            change_type="Schema and field changes",
            blast_radius="localized",
            requirement_before="old behavior",
            requirement_after="new behavior",
            rationale="test rationale",
            acceptance_criteria=("Must work",),
            expected_affected_artifacts=("todo/models.py",),
            expected_actions={"todo/models.py:Task": "modify"},
            architecture_constraints=("No view changes",),
        )
        core = model.to_core_scenario()
        assert core.scenario_id == "todo-loc-001"
        assert core.repository == "todo"
        assert core.blast_radius == BlastRadius.localized
        assert len(core.acceptance_criteria) == 1
        assert core.acceptance_criteria[0].description == "Must work"
        assert len(core.expected_affected_artifacts) == 1
        assert core.expected_affected_artifacts[0].path == "todo/models.py"
        assert len(core.expected_actions) == 1
        assert core.expected_actions[0][0].path == "todo/models.py"
        assert core.expected_actions[0][1] == ActionKind.regenerate

    def test_from_yaml_mapping(self) -> None:
        data = {
            "scenario_id": "test-001",
            "repository": "todo",
            "change_type": "Schema change",
            "blast_radius": "moderate",
            "requirement_before": "old",
            "requirement_after": "new",
            "rationale": "test",
            "acceptance_criteria": ["Criterion 1"],
            "expected_affected_artifacts": ["todo/models.py"],
            "expected_actions": {"todo/models.py": "modify"},
            "architecture_constraints": ["No view changes"],
            "hidden_tests": [
                {"description": "Hidden test 1", "type": "regression"},
            ],
        }
        model = ScenarioModel.from_yaml_mapping(data)
        assert model.scenario_id == "test-001"
        assert model.blast_radius == "moderate"
        assert model.hidden_tests[0]["description"] == "Hidden test 1"

    def test_from_yaml_mapping_missing_fields(self) -> None:
        data: dict[str, object] = {}
        with pytest.raises(ValueError, match="scenario_id"):
            ScenarioModel.from_yaml_mapping(data)
