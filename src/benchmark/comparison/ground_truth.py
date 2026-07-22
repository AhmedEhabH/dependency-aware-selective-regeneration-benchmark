from __future__ import annotations

from dataclasses import dataclass

from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import ArtifactRef, ImpactDecision, ImpactPrediction, Scenario


@dataclass(frozen=True)
class GroundTruthEntry:
    scenario_id: str
    artifact: ArtifactRef
    expected_action: ActionKind
    justification: str = ""
    confidence: int = 5
    adjudicated: bool = False


@dataclass(frozen=True)
class GroundTruthCollection:
    entries: tuple[GroundTruthEntry, ...] = ()

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for entry in self.entries:
            key = f"{entry.scenario_id}:{entry.artifact.path}"
            if key in seen:
                raise ValueError(f"Duplicate ground truth entry: {key}")
            seen.add(key)

    def get_for_scenario(self, scenario_id: str) -> tuple[GroundTruthEntry, ...]:
        return tuple(e for e in self.entries if e.scenario_id == scenario_id)

    def get_expected_actions(self, scenario_id: str) -> dict[str, ActionKind]:
        return {e.artifact.path: e.expected_action for e in self.entries if e.scenario_id == scenario_id}


class GroundTruthComparator:
    def __init__(self, ground_truth: GroundTruthCollection | None = None) -> None:
        self._ground_truth = ground_truth or GroundTruthCollection()

    def compare(
        self,
        prediction: ImpactPrediction,
        scenario: Scenario,
    ) -> ImpactPrediction:
        expected_actions = scenario.expected_actions

        decisions: list[ImpactDecision] = []
        for artifact, expected_action in expected_actions:
            pred_action = None
            for d in prediction.decisions:
                if d.artifact.path == artifact.path:
                    pred_action = d.action
                    break

            if pred_action is None:
                pred_action = ActionKind.preserve

            decisions.append(
                ImpactDecision(
                    artifact=artifact,
                    action=pred_action,
                    rationale=f"Expected: {expected_action}, Predicted: {pred_action}",
                )
            )

        return ImpactPrediction(decisions=tuple(decisions))

    def compute_match_rate(
        self,
        prediction: ImpactPrediction,
        scenario: Scenario,
    ) -> float:
        expected = scenario.expected_actions
        if not expected:
            return 1.0

        matches = 0
        for artifact, expected_action in expected:
            for d in prediction.decisions:
                if d.artifact.path == artifact.path:
                    if d.action == expected_action:
                        matches += 1
                    break

        return matches / len(expected)

    def build_from_scenario(self, scenario: Scenario) -> ImpactPrediction:
        decisions: list[ImpactDecision] = []
        for artifact, action in scenario.expected_actions:
            decisions.append(
                ImpactDecision(
                    artifact=artifact,
                    action=action,
                    rationale="Ground truth from scenario definition",
                )
            )
        return ImpactPrediction(decisions=tuple(decisions))

    def load_from_yaml(self, yaml_content: str) -> GroundTruthCollection:
        import yaml

        data = yaml.safe_load(yaml_content)
        entries: list[GroundTruthEntry] = []

        for item in data.get("ground_truth", []):
            scenario_id = item["scenario_id"]
            artifact_path = item["artifact_path"]
            artifact_type = item.get("artifact_type", "source")

            entry = GroundTruthEntry(
                scenario_id=scenario_id,
                artifact=ArtifactRef(path=artifact_path, artifact_type=ArtifactType(artifact_type)),
                expected_action=ActionKind(item["expected_action"]),
                justification=item.get("justification", ""),
                confidence=item.get("confidence", 5),
                adjudicated=item.get("adjudicated", False),
            )
            entries.append(entry)

        return GroundTruthCollection(entries=tuple(entries))
