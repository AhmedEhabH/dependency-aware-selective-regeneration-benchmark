from datetime import UTC, datetime

import pytest

from benchmark.core.enums import ActionKind, ArtifactType, BlastRadius, FailureKind, RunStatus
from benchmark.core.models import (
    AnalysisReport,
    ArtifactRef,
    ArtifactUniverse,
    Budget,
    FailureRecord,
    ImpactDecision,
    ImpactPrediction,
    MetricValue,
    ProvenanceEvent,
    RequirementChange,
    RunIdentity,
    RunRecord,
    Scenario,
    ScenarioSequence,
)


class TestFrozenImmutability:
    def test_requirement_change_is_frozen(self) -> None:
        rc = RequirementChange(before="old", after="new")
        with pytest.raises(AttributeError):
            rc.before = "changed"  # type: ignore[misc]

    def test_artifact_ref_is_frozen(self) -> None:
        ref = ArtifactRef(path="foo.py", artifact_type=ArtifactType.source)
        with pytest.raises(AttributeError):
            ref.path = "bar.py"  # type: ignore[misc]

    def test_impact_decision_is_frozen(self) -> None:
        ref = ArtifactRef(path="x.py", artifact_type=ArtifactType.source)
        d = ImpactDecision(artifact=ref, action=ActionKind.regenerate, rationale="test")
        with pytest.raises(AttributeError):
            d.action = ActionKind.preserve  # type: ignore[misc]

    def test_run_record_is_frozen(self) -> None:
        identity = RunIdentity(
            run_id="r1",
            protocol_version="1.0",
            repository_commit_sha="abc123",
            scenario_id="s1",
            strategy_name="strat",
        )
        record = RunRecord(identity=identity, status=RunStatus.succeeded)
        with pytest.raises(AttributeError):
            record.status = RunStatus.failed  # type: ignore[misc]


class TestRequirementChange:
    def test_empty_before_raises(self) -> None:
        with pytest.raises(ValueError, match="RequirementChange.before"):
            RequirementChange(before="", after="new")

    def test_empty_after_raises(self) -> None:
        with pytest.raises(ValueError, match="RequirementChange.after"):
            RequirementChange(before="old", after="")

    def test_valid_creation(self) -> None:
        rc = RequirementChange(before="old behavior", after="new behavior")
        assert rc.before == "old behavior"
        assert rc.after == "new behavior"

    def test_with_acceptance_criteria(self) -> None:
        rc = RequirementChange(
            before="old",
            after="new",
            acceptance_criteria=("criterion 1", "criterion 2"),
        )
        assert len(rc.acceptance_criteria) == 2


class TestArtifactRef:
    def test_empty_path_raises(self) -> None:
        with pytest.raises(ValueError, match="ArtifactRef.path"):
            ArtifactRef(path="", artifact_type=ArtifactType.source)

    def test_valid_creation(self) -> None:
        ref = ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source)
        assert ref.path == "src/main.py"
        assert ref.artifact_type == ArtifactType.source


class TestArtifactUniverse:
    def test_duplicate_path_raises(self) -> None:
        ref1 = ArtifactRef(path="a.py", artifact_type=ArtifactType.source)
        ref2 = ArtifactRef(path="a.py", artifact_type=ArtifactType.test)
        with pytest.raises(ValueError, match="Duplicate artifact path"):
            ArtifactUniverse(artifacts=(ref1, ref2))

    def test_contains(self) -> None:
        ref = ArtifactRef(path="a.py", artifact_type=ArtifactType.source)
        universe = ArtifactUniverse(artifacts=(ref,))
        assert universe.contains("a.py")
        assert not universe.contains("b.py")

    def test_empty_universe(self) -> None:
        universe = ArtifactUniverse()
        assert len(universe.artifacts) == 0


class TestArtifactUniverseValidation:
    def test_reject_duplicate_ids(self) -> None:
        ref1 = ArtifactRef(path="dup.py", artifact_type=ArtifactType.source)
        ref2 = ArtifactRef(path="dup.py", artifact_type=ArtifactType.test)
        with pytest.raises(ValueError, match="Duplicate artifact path"):
            ArtifactUniverse(artifacts=(ref1, ref2))


class TestImpactDecision:
    def test_valid_creation(self) -> None:
        ref = ArtifactRef(path="a.py", artifact_type=ArtifactType.source)
        d = ImpactDecision(artifact=ref, action=ActionKind.regenerate, rationale="needs update")
        assert d.artifact is ref
        assert d.action == ActionKind.regenerate
        assert d.rationale == "needs update"

    def test_default_rationale(self) -> None:
        ref = ArtifactRef(path="a.py", artifact_type=ArtifactType.source)
        d = ImpactDecision(artifact=ref, action=ActionKind.preserve)
        assert d.rationale == ""


class TestUndefinedMetric:
    def test_none_value(self) -> None:
        m = MetricValue(name="precision", value=None)
        assert m.value is None

    def test_zero_is_not_none(self) -> None:
        m = MetricValue(name="recall", value=0.0)
        assert m.value == 0.0
        assert m.value is not None


class TestFailureRecord:
    def test_valid_creation(self) -> None:
        f = FailureRecord(failure_kind=FailureKind.build, message="Build failed")
        assert f.failure_kind == FailureKind.build
        assert f.message == "Build failed"

    def test_empty_message_raises(self) -> None:
        with pytest.raises(ValueError, match="FailureRecord.message"):
            FailureRecord(failure_kind=FailureKind.timeout, message="")


class TestBudget:
    def test_default_values(self) -> None:
        b = Budget()
        assert b.max_iterations == 3
        assert b.max_tokens == 0
        assert b.timeout_seconds == 0

    def test_negative_iterations_raises(self) -> None:
        with pytest.raises(ValueError, match="Budget.max_iterations"):
            Budget(max_iterations=0)

    def test_negative_tokens_raises(self) -> None:
        with pytest.raises(ValueError, match="Budget.max_tokens"):
            Budget(max_tokens=-1)

    def test_max_iterations_semantics(self) -> None:
        b = Budget(max_iterations=3)
        assert b.max_iterations == 3


class TestRunIdentity:
    def test_valid_creation(self) -> None:
        identity = RunIdentity(
            run_id="run-001",
            protocol_version="1.0",
            repository_commit_sha="abc123",
            scenario_id="scenario-1",
            strategy_name="hybrid",
        )
        assert identity.run_id == "run-001"
        assert identity.protocol_version == "1.0"
        assert identity.repository_commit_sha == "abc123"

    def test_empty_run_id_raises(self) -> None:
        with pytest.raises(ValueError, match="RunIdentity.run_id"):
            RunIdentity(
                run_id="", protocol_version="1.0", repository_commit_sha="a",
                scenario_id="s", strategy_name="st",
            )

    def test_empty_protocol_version_raises(self) -> None:
        with pytest.raises(ValueError, match="RunIdentity.protocol_version"):
            RunIdentity(run_id="r", protocol_version="", repository_commit_sha="a", scenario_id="s", strategy_name="st")

    def test_empty_commit_sha_raises(self) -> None:
        with pytest.raises(ValueError, match="RunIdentity.repository_commit_sha"):
            RunIdentity(
                run_id="r", protocol_version="1.0", repository_commit_sha="",
                scenario_id="s", strategy_name="st",
            )


class TestScenario:
    def test_valid_creation(self) -> None:
        s = Scenario(
            scenario_id="test-001",
            repository="todo",
            change_type="schema",
            blast_radius=BlastRadius.localized,
            requirement_before="old",
            requirement_after="new",
            rationale="test",
        )
        assert s.scenario_id == "test-001"
        assert s.blast_radius == BlastRadius.localized

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="Scenario.scenario_id"):
            Scenario(scenario_id="", repository="r", change_type="t", blast_radius=BlastRadius.localized,
                     requirement_before="b", requirement_after="a", rationale="x")


class TestScenarioSequence:
    def test_duplicate_scenario_ids_raises(self) -> None:
        s1 = Scenario(scenario_id="s1", repository="r", change_type="t", blast_radius=BlastRadius.localized,
                      requirement_before="b", requirement_after="a", rationale="x")
        s2 = Scenario(scenario_id="s1", repository="r", change_type="t", blast_radius=BlastRadius.moderate,
                      requirement_before="b", requirement_after="a", rationale="x")
        with pytest.raises(ValueError, match="Duplicate scenario_id"):
            ScenarioSequence(scenarios=(s1, s2))

    def test_valid_sequence(self) -> None:
        s1 = Scenario(scenario_id="s1", repository="r", change_type="t", blast_radius=BlastRadius.localized,
                      requirement_before="b", requirement_after="a", rationale="x")
        s2 = Scenario(scenario_id="s2", repository="r", change_type="t", blast_radius=BlastRadius.moderate,
                      requirement_before="b", requirement_after="a", rationale="x")
        seq = ScenarioSequence(scenarios=(s1, s2))
        assert len(seq.scenarios) == 2


class TestUtcTimestamp:
    def test_run_identity_timestamp_is_utc(self) -> None:
        identity = RunIdentity(
            run_id="r1",
            protocol_version="1.0",
            repository_commit_sha="abc",
            scenario_id="s1",
            strategy_name="strat",
        )
        assert identity.timestamp.tzinfo is not None
        assert identity.timestamp.tzinfo.utcoffset(identity.timestamp) == UTC.utcoffset(identity.timestamp)

    def test_provenance_event_timestamp(self) -> None:

        event = ProvenanceEvent(
            timestamp=datetime.now(UTC),
            layer="core",
            action="test",
            input_hash="abc",
            output_hash="def",
        )
        assert event.timestamp.tzinfo is not None


class TestDeterministicEquality:
    def test_artifact_ref_equality(self) -> None:
        ref1 = ArtifactRef(path="a.py", artifact_type=ArtifactType.source)
        ref2 = ArtifactRef(path="a.py", artifact_type=ArtifactType.source)
        assert ref1 == ref2
        assert hash(ref1) == hash(ref2)

    def test_impact_prediction_equality(self) -> None:
        p1 = ImpactPrediction(decisions=())
        p2 = ImpactPrediction(decisions=())
        assert p1 == p2


class TestSerialization:
    def test_yaml_roundtrip_artifact_ref(self) -> None:
        import yaml

        ref = ArtifactRef(path="a.py", artifact_type=ArtifactType.source)
        data = {"path": ref.path, "type": str(ref.artifact_type)}
        yaml_str = yaml.dump(data)
        loaded = yaml.safe_load(yaml_str)
        assert loaded["path"] == "a.py"
        assert loaded["type"] == "source"

    def test_json_roundtrip_run_identity(self) -> None:
        import json

        identity = RunIdentity(
            run_id="r1",
            protocol_version="1.0",
            repository_commit_sha="abc",
            scenario_id="s1",
            strategy_name="strat",
        )
        data = {
            "run_id": identity.run_id,
            "protocol_version": identity.protocol_version,
            "repo_sha": identity.repository_commit_sha,
            "timestamp": identity.timestamp.isoformat(),
        }
        json_str = json.dumps(data)
        loaded = json.loads(json_str)
        assert loaded["run_id"] == "r1"
        assert loaded["protocol_version"] == "1.0"


class TestAnalysisReport:
    def test_empty_title_raises(self) -> None:
        with pytest.raises(ValueError, match="AnalysisReport.title"):
            AnalysisReport(title="")

    def test_valid_creation(self) -> None:
        report = AnalysisReport(title="Test Report", metrics=(MetricValue(name="acc", value=0.95),), summary="All good")
        assert report.title == "Test Report"
        assert report.metrics[0].name == "acc"
        assert report.metrics[0].value == 0.95
