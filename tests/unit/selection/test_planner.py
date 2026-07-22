from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import (
    ArtifactRef,
    ArtifactUniverse,
    ImpactDecision,
    ImpactPrediction,
)
from benchmark.selection.planner import ArtifactSelection, ArtifactSelector, RegenerationPlan, RegenerationPlanner


def _make_prediction_with_regenerate_and_preserve() -> ImpactPrediction:
    return ImpactPrediction(
        decisions=(
            ImpactDecision(
                artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                action=ActionKind.regenerate,
                rationale="needs update",
            ),
            ImpactDecision(
                artifact=ArtifactRef(path="src/views.py", artifact_type=ArtifactType.source),
                action=ActionKind.preserve,
                rationale="no change needed",
            ),
            ImpactDecision(
                artifact=ArtifactRef(path="tests/test_models.py", artifact_type=ArtifactType.test),
                action=ActionKind.human_review,
                rationale="uncertain",
            ),
        )
    )


def _make_universe() -> ArtifactUniverse:
    return ArtifactUniverse(
        artifacts=(
            ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/views.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="tests/test_models.py", artifact_type=ArtifactType.test),
        )
    )


class TestArtifactSelector:
    def test_selects_regenerate_and_review(self) -> None:
        selector = ArtifactSelector()
        prediction = _make_prediction_with_regenerate_and_preserve()
        selection = selector.select(prediction, _make_universe())
        assert len(selection.artifacts) == 2
        paths = {a.path for a in selection.artifacts}
        assert "src/models.py" in paths
        assert "tests/test_models.py" in paths
        assert "src/views.py" not in paths

    def test_empty_prediction_returns_all(self) -> None:
        selector = ArtifactSelector()
        selection = selector.select(ImpactPrediction(), _make_universe())
        assert len(selection.artifacts) == 3

    def test_selection_is_frozen(self) -> None:
        selector = ArtifactSelector()
        selection = selector.select(_make_prediction_with_regenerate_and_preserve(), _make_universe())
        assert isinstance(selection, ArtifactSelection)


class TestRegenerationPlanner:
    def test_regenerate_before_review(self) -> None:
        selector = ArtifactSelector()
        planner = RegenerationPlanner()
        prediction = _make_prediction_with_regenerate_and_preserve()
        selection = selector.select(prediction, _make_universe())
        plan = planner.plan(selection, prediction)
        assert isinstance(plan, RegenerationPlan)
        paths = [a.path for a in plan.ordered_artifacts]
        assert paths[0] == "src/models.py"
        assert "tests/test_models.py" in paths

    def test_plan_actions_match_decisions(self) -> None:
        selector = ArtifactSelector()
        planner = RegenerationPlanner()
        prediction = _make_prediction_with_regenerate_and_preserve()
        selection = selector.select(prediction, _make_universe())
        plan = planner.plan(selection, prediction)
        assert plan.actions["src/models.py"] == ActionKind.regenerate
        assert plan.actions["tests/test_models.py"] == ActionKind.human_review

    def test_plan_is_frozen(self) -> None:
        selector = ArtifactSelector()
        planner = RegenerationPlanner()
        prediction = _make_prediction_with_regenerate_and_preserve()
        selection = selector.select(prediction, _make_universe())
        plan = planner.plan(selection, prediction)
        assert isinstance(plan, RegenerationPlan)
