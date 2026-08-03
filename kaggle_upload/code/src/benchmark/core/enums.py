from enum import StrEnum


class ActionKind(StrEnum):
    regenerate = "regenerate"
    preserve = "preserve"
    validate_only = "validate_only"
    human_review = "human_review"


class ArtifactType(StrEnum):
    requirement = "requirement"
    source = "source"
    test = "test"
    migration = "migration"
    api_schema = "api_schema"
    documentation = "documentation"
    configuration = "configuration"
    architecture = "architecture"
    deployment = "deployment"


class BlastRadius(StrEnum):
    localized = "localized"
    moderate = "moderate"
    cross_cutting = "cross_cutting"


class RunStatus(StrEnum):
    prepared = "prepared"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    timed_out = "timed_out"
    cancelled = "cancelled"


class FailureKind(StrEnum):
    infrastructure = "infrastructure"
    infrastructure_nonrepairable = "infrastructure_nonrepairable"
    model_output = "model_output"
    build = "build"
    changed_requirement = "changed_requirement"
    regression = "regression"
    architecture = "architecture"
    timeout = "timeout"
    scientific_budget_exhausted = "scientific_budget_exhausted"
    harness_defect = "harness_defect"


class EvidenceTier(StrEnum):
    engineering_validation = "engineering_validation"
    smoke = "smoke"
    pilot = "pilot"
    confirmatory = "confirmatory"
    exploratory = "exploratory"
    legacy_pilot = "legacy_pilot"
