from dataclasses import replace
from pathlib import Path

import yaml

from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import (
    ArtifactRef,
    ArtifactUniverse,
    DependencyGraph,
    RequirementChange,
)
from benchmark.scenarios.loader import ScenarioLoader
from benchmark.selection.dependency_scope import (
    LOW_INFORMATION_SOFTWARE_TERMS,
    MIN_REVERSE_CONSUMER_OVERLAP,
    NEGATIVE_PHRASE_PATTERNS,
    ArtifactDescriptor,
    _normalize,
    derive_requirement_signals,
    descriptors_from_profile,
    select_dependency_scope,
)

FIVE_UNIVERSE = ArtifactUniverse(
    artifacts=(
        ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source),
        ArtifactRef(path="todo/serializers.py", artifact_type=ArtifactType.source),
        ArtifactRef(path="todo/views.py", artifact_type=ArtifactType.source),
        ArtifactRef(path="todo/permissions.py", artifact_type=ArtifactType.source),
        ArtifactRef(path="todo/urls.py", artifact_type=ArtifactType.source),
    )
)

FIVE_PATHS = frozenset({
    "todo/models.py", "todo/serializers.py", "todo/views.py",
    "todo/permissions.py", "todo/urls.py",
})

TODO_GRAPH = DependencyGraph(
    nodes=("todo/models.py", "todo/serializers.py", "todo/views.py", "todo/urls.py", "todo/permissions.py"),
    edges=(
        ("todo/urls.py", "todo/views.py"),
        ("todo/views.py", "todo/serializers.py"),
        ("todo/views.py", "todo/models.py"),
        ("todo/views.py", "todo/permissions.py"),
        ("todo/serializers.py", "todo/models.py"),
        ("todo/permissions.py", "todo/models.py"),
    ),
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TODO_PROFILE_PATH = _PROJECT_ROOT / "benchmark_data" / "repository_profiles" / "todo.yaml"


def _load_profile_catalog() -> tuple[dict, ...]:
    raw = yaml.safe_load(TODO_PROFILE_PATH.read_text())
    return tuple(raw["artifact_catalog"])


def _build_descriptors() -> tuple[ArtifactDescriptor, ...]:
    catalog = _load_profile_catalog()
    editable = ("todo/models.py", "todo/serializers.py", "todo/views.py", "todo/permissions.py", "todo/urls.py")
    return descriptors_from_profile(catalog, editable)


DESCRIPTORS = _build_descriptors()


# --- Scenario definitions (public text only) ---

SCENARIO_001 = RequirementChange(
    before=(
        "The Task model already has owner (nullable ForeignKey), project (ForeignKey to Project), "
        "and tags (ManyToManyField to Tag). The Task model does not have a priority field. "
        "The TaskSerializer does not expose priority. The TaskViewSet currently has no priority "
        "filter parameter. There is no priority concept anywhere in the codebase."
    ),
    after=(
        "The Task model must gain a Priority enum implemented with Django TextChoices. "
        "The allowed stored values are HIGH, MEDIUM, LOW. The default priority is MEDIUM. "
        "The TaskSerializer must expose priority as a writable field. The list endpoint must "
        "support filtering by priority via GET /api/tasks/?priority=HIGH. Requests without "
        "the priority query parameter must retain the current unfiltered listing behaviour. "
        "Existing Task.owner, Task.tags, Project and Tag behaviour must be preserved."
    ),
    acceptance_criteria=(
        "Task model has priority field with choices HIGH, MEDIUM, LOW and default MEDIUM",
        "TaskSerializer exposes priority field as a read-write ChoiceField",
        "Task list endpoint supports ?priority=HIGH filtering",
        "Unfiltered listing behaviour is unchanged",
        "All existing tests pass without modification",
    ),
)

SCENARIO_002 = RequirementChange(
    before=(
        "Tasks are permanently deleted when a DELETE request is sent to the API. "
        "There is no mechanism to recover deleted tasks. The Task model has no concept "
        "of soft deletion, archived status, or deleted_at timestamp. The default Task "
        "queryset returns all tasks including deleted ones."
    ),
    after=(
        "The Task model must gain soft deletion: a deleted_at DateTimeField that is null "
        "by default. When a DELETE request is received, the task's deleted_at field is set "
        "to the current timestamp instead of being removed from the database. Normal API "
        "listing endpoints (GET /api/tasks/) must exclude soft-deleted tasks by default. "
        "A detail=False DRF @action named deleted must list only soft-deleted tasks. "
        "A detail=True DRF @action named restore must set deleted_at back to null, "
        "restoring the task. Soft-deleted tasks retain all their existing data (title, "
        "description, status, project, tags). Attempting to access a soft-deleted task "
        "by ID returns 404. Serializer changes are not required. DefaultRouter exposes "
        "both actions automatically so todo/urls.py must not be modified."
    ),
    acceptance_criteria=(
        "DELETE /api/tasks/{id}/ sets deleted_at instead of removing the row",
        "GET /api/tasks/ excludes soft-deleted tasks by default",
        "GET /api/tasks/{id}/ returns 404 for soft-deleted tasks",
        "GET /api/tasks/deleted/ lists only soft-deleted tasks",
        "POST /api/tasks/{id}/restore/ sets deleted_at=null and returns the restored task",
        "Soft-deleted tasks retain all original data after restore",
    ),
)

SCENARIO_003 = RequirementChange(
    before=(
        "The Project model has name and description only; it has no owner field. "
        "The Task model has a nullable owner ForeignKey. The TaskViewSet uses "
        "IsOwnerOrReadOnly. IsOwnerOrReadOnly.has_permission allows any authenticated "
        "user through at the view level. IsOwnerOrReadOnly.has_object_permission allows "
        "safe methods and checks obj.owner == request.user for object write operations. "
        "The ProjectViewSet and TagViewSet use IsProjectMember. "
        "IsProjectMember.has_permission allows any authenticated user through, so "
        "authenticated users may currently create Projects and Tags. "
        "IsProjectMember.has_object_permission allows safe methods and requires "
        "request.user.is_staff for object update and delete. No existing authorization "
        "rule derives authority from Project ownership."
    ),
    after=(
        "The Project model must gain an owner ForeignKey to the authenticated user model. "
        "Any authenticated user may continue creating a Project; the creator is automatically "
        "stored as Project.owner. The Project owner is exposed read-only by "
        "ProjectSerializer. All authenticated users may read Projects, Tasks and Tags. "
        "Only the Project.owner may update or delete that Project. Only the user who owns "
        "the Task's project may create, update or delete Tasks within that Project. "
        "The Task.owner field remains in the model for backward compatibility but is not "
        "the authority for this new policy. TagViewSet authorization behaviour must remain "
        "exactly as it was before. Unauthorized write operations must return 403. "
        "Exactly one new migration must be generated."
    ),
    acceptance_criteria=(
        "POST /api/tasks/ in a project owned by another user returns 403",
        "PATCH /api/tasks/{id}/ in a project owned by another user returns 403",
        "DELETE /api/tasks/{id}/ in a project owned by another user returns 403",
        "GET /api/tasks/ returns all tasks (read access is unrestricted)",
        "A user can create, update, and delete tasks in their own project",
        "Only the project owner can update or delete the project itself",
        "Any authenticated user can create a new project",
        "Project owner is read-only in the API and is set automatically on creation",
    ),
)


class TestNormalize:
    def test_taskviewset_splits_correctly(self):
        result = _normalize("TaskViewSet")
        assert result == ["task", "view", "set"], f"Got {result}"

    def test_projectserializer_splits_correctly(self):
        result = _normalize("ProjectSerializer")
        assert result == ["project", "serializer"], f"Got {result}"

    def test_snake_case_splits_correctly(self):
        result = _normalize("deleted_at")
        assert "deleted" in result
        assert "at" in result

    def test_mixed_case_and_snake(self):
        result = _normalize("TaskViewSet priority_field")
        assert "task" in result
        assert "view" in result
        assert "set" in result
        assert "priority" in result
        assert "field" in result


class TestReverseConsumerConstant:
    def test_threshold_is_three(self):
        assert MIN_REVERSE_CONSUMER_OVERLAP == 3


class TestReverseConsumerOverlap:
    def test_three_overlaps_includes_consumer(self):
        desc_consumer = ArtifactDescriptor(
            path="todo/views.py", category="view",
            description="TaskViewSet with priority filter and delete handler and restore action",
            provides_symbols=("TaskViewSet",),
            typical_change_triggers=("API changes",),
        )
        pos = frozenset({"priority", "filter", "delete", "handler", "restore", "action"})
        from benchmark.selection.dependency_scope import _desc_meaningful_terms
        consumer_meaningful = _desc_meaningful_terms(desc_consumer)
        overlap = pos & consumer_meaningful
        assert len(overlap) >= MIN_REVERSE_CONSUMER_OVERLAP, (
            f"Expected >=3 overlap for consumer inclusion, got {len(overlap)}: {overlap}"
        )

    def test_two_overlaps_excludes_consumer(self):
        desc_consumer = ArtifactDescriptor(
            path="todo/permissions.py", category="permission",
            description="Permission classes",
            provides_symbols=("IsOwnerOrReadOnly",),
            typical_change_triggers=("authorization changes",),
        )
        pos = frozenset({"model", "field"})
        from benchmark.selection.dependency_scope import _desc_meaningful_terms
        consumer_meaningful = _desc_meaningful_terms(desc_consumer)
        overlap = pos & consumer_meaningful
        assert len(overlap) < MIN_REVERSE_CONSUMER_OVERLAP, (
            f"Expected <3 overlap for consumer exclusion, got {len(overlap)}: {overlap}"
        )

    def test_explicit_negative_exclusion_wins(self):
        change = RequirementChange(
            before="The current system has no soft deletion.",
            after="Serializer changes are not required. todo/serializers.py must not be modified.",
            acceptance_criteria=("Soft deletion is implemented",),
        )
        descriptor = ArtifactDescriptor(
            path="todo/serializers.py", category="serializer",
            description="DRF serializers",
            provides_symbols=("TaskSerializer",),
            typical_change_triggers=("field changes",),
        )
        signals = derive_requirement_signals(change, (descriptor,))
        assert "todo/serializers.py" in signals.negative_descriptor_paths, (
            "Explicit negative exclusion must be recognized"
        )
        assert "serializer" not in signals.positive_terms, (
            "Negative sentence must not contribute positive terms"
        )


class TestLowInformationTerms:
    def test_contains_no_domain_terms(self):
        domain = {"priority", "deleted", "owner", "project", "task", "serializer", "view", "permission"}
        overlap = LOW_INFORMATION_SOFTWARE_TERMS & domain
        assert not overlap, f"LOW_INFORMATION_SOFTWARE_TERMS contains domain terms: {overlap}"

    def test_contains_expected_generic_terms(self):
        assert "add" in LOW_INFORMATION_SOFTWARE_TERMS
        assert "change" in LOW_INFORMATION_SOFTWARE_TERMS
        assert "new" in LOW_INFORMATION_SOFTWARE_TERMS


class TestNegativePhrasePatterns:
    def test_positive_patterns_defined(self):
        assert len(NEGATIVE_PHRASE_PATTERNS) >= 4

    def test_extract_negative_paths_basic(self):
        from benchmark.selection.dependency_scope import _extract_negative_paths
        text = "Serializer changes are not required. No changes to todo/urls.py."
        result = _extract_negative_paths(text)
        assert "todo/urls.py" in result

    def test_extract_no_matches(self):
        from benchmark.selection.dependency_scope import _extract_negative_paths
        result = _extract_negative_paths("Everything is fine and needs changes.")
        assert len(result) == 0


class TestRequirementSignals:
    def test_scenario_002_excludes_serializer_and_urls(self):
        signals = derive_requirement_signals(SCENARIO_002, DESCRIPTORS)
        assert "todo/serializers.py" in signals.negative_descriptor_paths
        assert "todo/urls.py" in signals.negative_descriptor_paths

    def test_scenario_003_has_positive_terms(self):
        signals = derive_requirement_signals(SCENARIO_003, DESCRIPTORS)
        assert len(signals.positive_terms) > 0

    def test_smoke_001_no_negatives(self):
        signals = derive_requirement_signals(SCENARIO_001, DESCRIPTORS)
        # scenario 1 has no explicit "no changes to X" statements for editable files
        # "without modification" in "Existing tests pass without modification" refers to tests
        # and "Project and Tag behaviour must be preserved" is not a path exclusion
        assert "todo/urls.py" not in signals.negative_descriptor_paths
        assert "todo/permissions.py" not in signals.negative_descriptor_paths


class TestSelectDependencyScopeSmoke:
    def test_real_production_construction_without_ground_truth(self):
        """Load a Smoke scenario via ScenarioLoader, create two Scenario variants
        with different expected_affected_artifacts and expected_actions using
        dataclasses.replace, build the strategy via make_strategy, and prove
        identical predictions."""
        from seven_arm_benchmark import make_strategy
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        scenarios_dir = project_root / "benchmark_data" / "scenarios"
        loader = ScenarioLoader(scenarios_dir)
        scenario = loader.load_scenario(scenarios_dir / "todo-smoke-001.yaml")

        altered_artifacts = (
            ArtifactRef(path="todo/nonexistent.py", artifact_type=ArtifactType.source),
        )
        altered_actions = (
            (ArtifactRef(path="todo/nonexistent.py", artifact_type=ArtifactType.source), ActionKind.preserve),
        )
        sc_a = replace(scenario, expected_affected_artifacts=altered_artifacts, expected_actions=altered_actions)
        sc_b = replace(scenario, expected_affected_artifacts=(), expected_actions=())

        change_a = RequirementChange(
            before=sc_a.requirement_before,
            after=sc_a.requirement_after,
            acceptance_criteria=tuple(c.description for c in sc_a.acceptance_criteria),
        )
        change_b = RequirementChange(
            before=sc_b.requirement_before,
            after=sc_b.requirement_after,
            acceptance_criteria=tuple(c.description for c in sc_b.acceptance_criteria),
        )

        strategy = make_strategy("selective", graph=TODO_GRAPH, artifact_descriptors=DESCRIPTORS)
        import inspect
        src = inspect.getsource(type(strategy).analyze_impact)
        assert "expected_affected_artifacts" not in src
        assert "expected_actions" not in src

        result_a = select_dependency_scope(change_a, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
        result_b = select_dependency_scope(change_b, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
        assert result_a == result_b, (
            f"Different expected_affected_artifacts must not change selection: "
            f"a={result_a} b={result_b}"
        )

    def test_fails_closed_on_empty_meaningful_text(self):
        empty = RequirementChange(before="old", after="new", acceptance_criteria=("x",))
        result = select_dependency_scope(empty, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
        assert len(result) == 0, f"Should fail closed with empty text, got: {result}"

    def test_all_scenarios_no_scenario_id_in_code(self):
        import inspect
        source = inspect.getsource(select_dependency_scope)
        assert "todo-smoke-" not in source, (
            "Production code must not contain scenario ID strings"
        )


class TestSelectiveDeterminism:
    def test_three_scenarios_all_deterministic(self):
        for sc in (SCENARIO_001, SCENARIO_002, SCENARIO_003):
            r1 = select_dependency_scope(sc, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
            r2 = select_dependency_scope(sc, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
            assert r1 == r2, f"Non-deterministic result for {sc.acceptance_criteria[0][:40]}..."


class TestBroadMatchingPrevented:
    def test_low_info_terms_do_not_cause_seeds(self):
        descriptor_with_only_generic_triggers = ArtifactDescriptor(
            path="todo/generic.py",
            category="source",
            description="A generic file with no specific domain terms",
            provides_symbols=("GeneralHelper",),
            typical_change_triggers=("API additions or modifications",),
        )
        change = RequirementChange(
            before="The system has basic functionality.",
            after="Add new API endpoint for listing.",
            acceptance_criteria=("API must support new modification",),
        )
        result = select_dependency_scope(
            change,
            ArtifactUniverse(artifacts=(ArtifactRef(path="todo/generic.py", artifact_type=ArtifactType.source),)),
            (descriptor_with_only_generic_triggers,),
            DependencyGraph(),
        )
        assert len(result) == 0, (
            f"Generic-only triggers must not seed artifacts. Got: {result}"
        )


class TestUniverseBoundary:
    def test_selected_paths_all_in_five_file_universe(self):
        for sc in (SCENARIO_001, SCENARIO_002, SCENARIO_003):
            result = select_dependency_scope(sc, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
            for p in result:
                assert p in FIVE_PATHS, f"{p} not in 5-file universe for {sc.acceptance_criteria[0][:40]}..."


def _categories_for_result(result: tuple[str, ...]) -> set[str]:
    path_to_cat = {
        "todo/models.py": "model",
        "todo/serializers.py": "serializer",
        "todo/views.py": "view",
        "todo/permissions.py": "permission",
        "todo/urls.py": "config",
    }
    return {path_to_cat[p] for p in result if p in path_to_cat}


class TestPublicLayerCoverage:
    """Engineering Smoke gates: every selected scope must cover all explicitly
    required public layers for that change request."""

    def test_priority_covers_model_serializer_view(self):
        result = select_dependency_scope(SCENARIO_001, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
        cats = _categories_for_result(result)
        assert "model" in cats, f"Priority must cover model. Got: {result}"
        assert "serializer" in cats, f"Priority must cover serializer. Got: {result}"
        assert "view" in cats, f"Priority must cover view. Got: {result}"

    def test_priority_does_not_select_urls(self):
        result = select_dependency_scope(SCENARIO_001, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
        assert "todo/urls.py" not in result, (
            f"Priority must not select urls.py. Got: {result}"
        )

    def test_soft_deletion_covers_model_view(self):
        result = select_dependency_scope(SCENARIO_002, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
        cats = _categories_for_result(result)
        assert "model" in cats, f"Soft deletion must cover model. Got: {result}"
        assert "view" in cats, f"Soft deletion must cover view. Got: {result}"

    def test_soft_deletion_does_not_select_urls(self):
        result = select_dependency_scope(SCENARIO_002, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
        assert "todo/urls.py" not in result, (
            f"Soft deletion must not select urls.py. Got: {result}"
        )

    def test_soft_deletion_does_not_select_serializer(self):
        result = select_dependency_scope(SCENARIO_002, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
        assert "todo/serializers.py" not in result, (
            f"Soft deletion must not select serializers.py. Got: {result}"
        )

    def test_ownership_covers_model_serializer_permission_view(self):
        result = select_dependency_scope(SCENARIO_003, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
        cats = _categories_for_result(result)
        assert "model" in cats, f"Ownership must cover model. Got: {result}"
        assert "serializer" in cats, f"Ownership must cover serializer. Got: {result}"
        assert "permission" in cats, f"Ownership must cover permission. Got: {result}"
        assert "view" in cats, f"Ownership must cover view. Got: {result}"

    def test_ownership_does_not_select_urls(self):
        result = select_dependency_scope(SCENARIO_003, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
        assert "todo/urls.py" not in result, (
            f"Ownership must not select urls.py. Got: {result}"
        )

    def test_every_result_is_strict_subset_of_five(self):
        for name, sc in [("001", SCENARIO_001), ("002", SCENARIO_002), ("003", SCENARIO_003)]:
            result = select_dependency_scope(sc, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)
            assert len(result) > 0, f"Scenario {name} must select at least one path"
            assert len(result) < 5, f"Scenario {name} must select fewer than all 5 paths, got {result}"
            for p in result:
                assert p in FIVE_PATHS, f"{p} not in five-file universe for scenario {name}"
