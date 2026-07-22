from benchmark.core.enums import BlastRadius
from benchmark.core.models import Scenario, ScenarioSequence
from benchmark.scenarios.sequencing import ScenarioSequencer


def _make_scenario(scenario_id: str, blast_radius: BlastRadius, repo: str = "todo") -> Scenario:
    return Scenario(
        scenario_id=scenario_id,
        repository=repo,
        change_type="test",
        blast_radius=blast_radius,
        requirement_before="old",
        requirement_after="new",
        rationale="test",
    )


class TestScenarioSequencer:
    def test_sequence_orders_by_blast_radius(self) -> None:
        cross = _make_scenario("s3", BlastRadius.cross_cutting)
        loc = _make_scenario("s1", BlastRadius.localized)
        mod = _make_scenario("s2", BlastRadius.moderate)

        seq = ScenarioSequencer().sequence([cross, loc, mod])
        assert isinstance(seq, ScenarioSequence)
        assert seq.scenarios[0].blast_radius == BlastRadius.localized
        assert seq.scenarios[1].blast_radius == BlastRadius.moderate
        assert seq.scenarios[2].blast_radius == BlastRadius.cross_cutting

    def test_sequence_ties_broken_by_id(self) -> None:
        s1 = _make_scenario("b", BlastRadius.localized)
        s2 = _make_scenario("a", BlastRadius.localized)
        seq = ScenarioSequencer().sequence([s1, s2])
        assert seq.scenarios[0].scenario_id == "a"
        assert seq.scenarios[1].scenario_id == "b"

    def test_sequence_empty_list(self) -> None:
        seq = ScenarioSequencer().sequence([])
        assert len(seq.scenarios) == 0

    def test_sequence_by_repository(self) -> None:
        s1 = _make_scenario("s1", BlastRadius.localized, "todo")
        s2 = _make_scenario("s2", BlastRadius.moderate, "djangocms")

        result = ScenarioSequencer().sequence_by_repository([s1, s2])
        assert "todo" in result
        assert "djangocms" in result
        assert len(result["todo"].scenarios) == 1
        assert len(result["djangocms"].scenarios) == 1

    def test_sequence_by_repository_maintains_order(self) -> None:
        s1 = _make_scenario("s1", BlastRadius.moderate, "todo")
        s2 = _make_scenario("s2", BlastRadius.localized, "todo")

        result = ScenarioSequencer().sequence_by_repository([s1, s2])
        todo_seq = result["todo"]
        assert todo_seq.scenarios[0].blast_radius == BlastRadius.localized
        assert todo_seq.scenarios[1].blast_radius == BlastRadius.moderate
