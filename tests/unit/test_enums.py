from benchmark.core.enums import ActionKind, ArtifactType, BlastRadius, EvidenceTier, FailureKind, RunStatus


class TestEnumStringStability:
    def test_action_kind_values(self) -> None:
        assert ActionKind.regenerate == "regenerate"
        assert ActionKind.preserve == "preserve"
        assert ActionKind.validate_only == "validate_only"
        assert ActionKind.human_review == "human_review"

    def test_artifact_type_values(self) -> None:
        assert ArtifactType.requirement == "requirement"
        assert ArtifactType.source == "source"
        assert ArtifactType.test == "test"
        assert ArtifactType.migration == "migration"
        assert ArtifactType.api_schema == "api_schema"
        assert ArtifactType.documentation == "documentation"
        assert ArtifactType.configuration == "configuration"
        assert ArtifactType.architecture == "architecture"
        assert ArtifactType.deployment == "deployment"

    def test_blast_radius_values(self) -> None:
        assert BlastRadius.localized == "localized"
        assert BlastRadius.moderate == "moderate"
        assert BlastRadius.cross_cutting == "cross_cutting"

    def test_run_status_values(self) -> None:
        assert RunStatus.prepared == "prepared"
        assert RunStatus.running == "running"
        assert RunStatus.succeeded == "succeeded"
        assert RunStatus.failed == "failed"
        assert RunStatus.timed_out == "timed_out"
        assert RunStatus.cancelled == "cancelled"

    def test_failure_kind_values(self) -> None:
        assert FailureKind.infrastructure == "infrastructure"
        assert FailureKind.model_output == "model_output"
        assert FailureKind.build == "build"
        assert FailureKind.changed_requirement == "changed_requirement"
        assert FailureKind.regression == "regression"
        assert FailureKind.architecture == "architecture"
        assert FailureKind.timeout == "timeout"
        assert FailureKind.harness_defect == "harness_defect"

    def test_evidence_tier_values(self) -> None:
        assert EvidenceTier.engineering_validation == "engineering_validation"
        assert EvidenceTier.smoke == "smoke"
        assert EvidenceTier.pilot == "pilot"
        assert EvidenceTier.confirmatory == "confirmatory"
        assert EvidenceTier.exploratory == "exploratory"
        assert EvidenceTier.legacy_pilot == "legacy_pilot"

    def test_enum_json_serializable(self) -> None:
        import json

        data = {
            "action": ActionKind.regenerate,
            "blast": BlastRadius.cross_cutting,
            "status": RunStatus.succeeded,
        }
        serialized = json.dumps(data, default=str)
        assert "regenerate" in serialized
        assert "cross_cutting" in serialized
        assert "succeeded" in serialized

    def test_enum_yaml_serializable(self) -> None:
        import yaml

        data = {"action": ActionKind.preserve, "tier": EvidenceTier.confirmatory}
        serialized = yaml.dump(data)
        assert "preserve" in serialized
        assert "confirmatory" in serialized
