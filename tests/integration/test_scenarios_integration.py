from pathlib import Path

import pytest
import yaml

from benchmark.scenarios.loader import ScenarioLoader

SCENARIOS_DIR = Path("benchmark_data/scenarios")
PROFILES_DIR = Path("benchmark_data/repository_profiles")
REPO_TODO_DIR = Path("benchmark_data/repositories/todo")

SMOKE_IDS = ("todo-smoke-001", "todo-smoke-002", "todo-smoke-003")

# Ground Truth paths per scenario (real normalized paths, no parentheses)
GT_001 = {"todo/models.py", "todo/serializers.py", "todo/views.py", "todo/migrations/"}
GT_002 = {"todo/models.py", "todo/views.py", "todo/migrations/"}
GT_003 = {
    "todo/models.py",
    "todo/serializers.py",
    "todo/permissions.py",
    "todo/views.py",
    "todo/migrations/",
}

LLM_EDITABLE_EXPECTED = {
    "todo/models.py",
    "todo/serializers.py",
    "todo/views.py",
    "todo/permissions.py",
    "todo/urls.py",
}


def _path_in_repo(repo_root: Path, path_str: str) -> bool:
    """Check if a relative path exists under a repository root."""
    full = (repo_root / path_str).resolve()
    return full.exists() and str(full).startswith(str(repo_root.resolve()))


@pytest.fixture(scope="module")
def smoke_scenarios() -> dict[str, "Scenario"]:
    loader = ScenarioLoader(SCENARIOS_DIR)
    all_scenarios = loader.load_all()
    return {s.scenario_id: s for s in all_scenarios if s.scenario_id in SMOKE_IDS}


@pytest.fixture(scope="module")
def smoke_yamls() -> dict[str, dict]:
    result = {}
    for sid in SMOKE_IDS:
        path = SCENARIOS_DIR / f"{sid}.yaml"
        if path.is_file():
            result[sid] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return result


class TestSmokeScenariosV2:
    """V2-01B: scenario contract correctness."""

    def test_all_smoke_load_successfully(self, smoke_scenarios: dict) -> None:
        assert len(smoke_scenarios) == 3
        for sid in SMOKE_IDS:
            assert sid in smoke_scenarios, f"Missing scenario: {sid}"

    def test_artifact_paths_no_parentheses(self, smoke_scenarios: dict) -> None:
        for sid, scenario in smoke_scenarios.items():
            for ref in scenario.expected_affected_artifacts:
                assert "(" not in ref.path, f"{sid}: path contains '(' in {ref.path}"
                assert ")" not in ref.path, f"{sid}: path contains ')' in {ref.path}"

    def test_artifact_paths_no_test_prefix(self, smoke_scenarios: dict) -> None:
        for sid, scenario in smoke_scenarios.items():
            for ref in scenario.expected_affected_artifacts:
                assert not ref.path.startswith("todo/tests/"), (
                    f"{sid}: path starts with todo/tests/: {ref.path}"
                )

    def test_001_ground_truth_paths(self, smoke_scenarios: dict) -> None:
        scenario = smoke_scenarios["todo-smoke-001"]
        paths = {ref.path for ref in scenario.expected_affected_artifacts}
        assert paths == GT_001, f"001 paths mismatch: {paths}"

    def test_002_ground_truth_paths(self, smoke_scenarios: dict) -> None:
        scenario = smoke_scenarios["todo-smoke-002"]
        paths = {ref.path for ref in scenario.expected_affected_artifacts}
        assert paths == GT_002, f"002 paths mismatch: {paths}"

    def test_003_ground_truth_paths(self, smoke_scenarios: dict) -> None:
        scenario = smoke_scenarios["todo-smoke-003"]
        paths = {ref.path for ref in scenario.expected_affected_artifacts}
        assert paths == GT_003, f"003 paths mismatch: {paths}"

    def test_002_excludes_urls_py(self, smoke_scenarios: dict) -> None:
        scenario = smoke_scenarios["todo-smoke-002"]
        paths = {ref.path for ref in scenario.expected_affected_artifacts}
        assert "todo/urls.py" not in paths, "002 must not include todo/urls.py"

    def test_001_requirement_before_matches_baseline(self, smoke_scenarios: dict) -> None:
        rb = smoke_scenarios["todo-smoke-001"].requirement_before
        assert "owner" in rb, "001 before must mention owner"
        assert "project" in rb, "001 before must mention project"
        assert "tags" in rb, "001 before must mention tags"
        assert "does not have a priority" in rb or "no priority" in rb, (
            "001 before must state no priority"
        )
        assert "TaskSerializer does not expose" in rb, (
            "001 before must state serializer does not expose priority"
        )
        assert "no priority filter" in rb, (
            "001 before must state no priority filter in view"
        )

    def test_002_requirement_before_matches_baseline(self, smoke_scenarios: dict) -> None:
        rb = smoke_scenarios["todo-smoke-002"].requirement_before
        assert "permanently deleted" in rb, "002 before must mention permanent deletion"
        assert "no mechanism to recover" in rb, "002 before must state no recovery"
        assert "no concept of soft deletion" in rb, "002 before must state no soft deletion"

    def test_003_requirement_before_matches_baseline(self, smoke_scenarios: dict) -> None:
        rb = smoke_scenarios["todo-smoke-003"].requirement_before
        assert "name and description" in rb, "003 before must mention Project fields"
        assert "no owner field" in rb, "003 before must state Project has no owner"
        assert "IsOwnerOrReadOnly" in rb, "003 before must mention IsOwnerOrReadOnly"
        assert "IsProjectMember" in rb, "003 before must mention IsProjectMember"
        assert "derives authority from Project ownership" in rb or "not based on Project ownership" in rb, (
            "003 before must state authorization not based on Project ownership"
        )

    def test_003_before_authenticated_creation_allowed(self, smoke_yamls: dict) -> None:
        rb = smoke_yamls["todo-smoke-003"]["requirement_before"]
        assert "authenticated users may currently create" in rb, (
            "003 before must state authenticated creation is allowed"
        )

    def test_003_before_not_all_writes_require_staff(self, smoke_yamls: dict) -> None:
        rb = smoke_yamls["todo-smoke-003"]["requirement_before"]
        assert "all writes require staff" not in rb.lower(), (
            "003 before must not claim all writes require staff"
        )

    def test_003_constraints_no_old_tag_constraint(self, smoke_yamls: dict) -> None:
        cons = smoke_yamls["todo-smoke-003"].get("architecture_constraints", [])
        combined = " ".join(cons)
        assert "Tag-level IsOwnerOrReadOnly" not in combined, (
            "003 constraints must not contain old Tag-level IsOwnerOrReadOnly"
        )

    def test_003_constraints_preserve_tag_viewset(self, smoke_yamls: dict) -> None:
        cons = smoke_yamls["todo-smoke-003"].get("architecture_constraints", [])
        combined = " ".join(cons)
        assert "TagViewSet must continue using IsProjectMember" in combined, (
            "003 constraints must explicitly preserve TagViewSet + IsProjectMember"
        )

    def test_003_expected_artifact_views_description(self, smoke_yamls: dict) -> None:
        affected = smoke_yamls["todo-smoke-003"].get("expected_affected_artifacts", [])
        views_entry = [a for a in affected if "todo/views.py" in a]
        assert len(views_entry) == 1
        assert "wire Project-owner permission classes" in views_entry[0], (
            "003 views.py artifact description must mention wiring permission classes"
        )


_ARTIFACT_CATALOG_PROFILE: dict | None = None


def _load_artifact_catalog_profile() -> dict:
    global _ARTIFACT_CATALOG_PROFILE
    if _ARTIFACT_CATALOG_PROFILE is None:
        path = PROFILES_DIR / "todo.yaml"
        assert path.is_file(), f"Profile not found: {path}"
        _ARTIFACT_CATALOG_PROFILE = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _ARTIFACT_CATALOG_PROFILE


class TestRepositoryArtifactCatalog:
    """V2-01B: artifact catalog and included paths exist on disk."""

    def test_all_catalog_ids_exist_on_disk(self) -> None:
        profile = _load_artifact_catalog_profile()
        catalog = profile.get("artifact_catalog", [])
        for entry in catalog:
            aid = entry["id"]
            assert _path_in_repo(REPO_TODO_DIR, aid), (
                f"Catalog ID does not exist: {aid}"
            )

    def test_all_included_entries_exist_on_disk(self) -> None:
        profile = _load_artifact_catalog_profile()
        au = profile.get("artifact_universe", {})
        included = au.get("included", [])
        for path_str in included:
            assert _path_in_repo(REPO_TODO_DIR, path_str), (
                f"Included path does not exist: {path_str}"
            )

    def test_no_todo_project_in_catalog(self) -> None:
        profile = _load_artifact_catalog_profile()
        catalog = profile.get("artifact_catalog", [])
        for entry in catalog:
            assert "todo_project/" not in entry["id"], (
                f"Catalog ID contains todo_project/: {entry['id']}"
            )

    def test_no_todo_project_in_included(self) -> None:
        profile = _load_artifact_catalog_profile()
        au = profile.get("artifact_universe", {})
        included = au.get("included", [])
        for path_str in included:
            assert "todo_project/" not in path_str, (
                f"Included path contains todo_project/: {path_str}"
            )

    def test_no_admin_py_in_included(self) -> None:
        profile = _load_artifact_catalog_profile()
        au = profile.get("artifact_universe", {})
        included = au.get("included", [])
        assert "todo/admin.py" not in included, (
            "todo/admin.py must not be in included"
        )

    def test_llm_editable_remains_frozen(self) -> None:
        profile = _load_artifact_catalog_profile()
        au = profile.get("artifact_universe", {})
        editable = set(au.get("llm_editable", []))
        assert editable == LLM_EDITABLE_EXPECTED, (
            f"llm_editable changed: {editable}"
        )

    def test_llm_editable_is_subset_of_repo(self) -> None:
        profile = _load_artifact_catalog_profile()
        au = profile.get("artifact_universe", {})
        editable = au.get("llm_editable", [])
        for path_str in editable:
            assert _path_in_repo(REPO_TODO_DIR, path_str), (
                f"llm_editable path does not exist in repo: {path_str}"
            )

    def test_all_catalog_ids_exist_on_disk(self) -> None:
        profile = _load_artifact_catalog_profile()
        catalog = profile.get("artifact_catalog", [])
        for entry in catalog:
            aid = entry["id"]
            assert _path_in_repo(REPO_TODO_DIR, aid), (
                f"Catalog ID does not exist: {aid}"
            )

    def test_all_included_entries_exist_on_disk(self) -> None:
        profile = _load_artifact_catalog_profile()
        au = profile.get("artifact_universe", {})
        included = au.get("included", [])
        for path_str in included:
            assert _path_in_repo(REPO_TODO_DIR, path_str), (
                f"Included path does not exist: {path_str}"
            )

    def test_no_todo_project_in_catalog(self) -> None:
        profile = _load_artifact_catalog_profile()
        catalog = profile.get("artifact_catalog", [])
        for entry in catalog:
            assert "todo_project/" not in entry["id"], (
                f"Catalog ID contains todo_project/: {entry['id']}"
            )

    def test_no_todo_project_in_included(self) -> None:
        profile = _load_artifact_catalog_profile()
        au = profile.get("artifact_universe", {})
        included = au.get("included", [])
        for path_str in included:
            assert "todo_project/" not in path_str, (
                f"Included path contains todo_project/: {path_str}"
            )

    def test_no_admin_py_in_included(self) -> None:
        profile = _load_artifact_catalog_profile()
        au = profile.get("artifact_universe", {})
        included = au.get("included", [])
        assert "todo/admin.py" not in included, (
            "todo/admin.py must not be in included"
        )

    def test_llm_editable_remains_frozen(self) -> None:
        profile = _load_artifact_catalog_profile()
        au = profile.get("artifact_universe", {})
        editable = set(au.get("llm_editable", []))
        assert editable == LLM_EDITABLE_EXPECTED, (
            f"llm_editable changed: {editable}"
        )

    def test_llm_editable_is_subset_of_repo(self) -> None:
        profile = _load_artifact_catalog_profile()
        au = profile.get("artifact_universe", {})
        editable = au.get("llm_editable", [])
        for path_str in editable:
            assert _path_in_repo(REPO_TODO_DIR, path_str), (
                f"llm_editable path does not exist in repo: {path_str}"
            )


_TODO_PROFILE: dict | None = None


def _load_todo_profile() -> dict:
    global _TODO_PROFILE
    if _TODO_PROFILE is None:
        path = PROFILES_DIR / "todo.yaml"
        assert path.is_file(), f"Profile not found: {path}"
        _TODO_PROFILE = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _TODO_PROFILE


class TestRepositoryProfileV2:
    """V2-01: repository profile llm_editable policy."""

    def test_llm_editable_exists(self) -> None:
        profile = _load_todo_profile()
        au = profile.get("artifact_universe", {})
        assert "llm_editable" in au, "artifact_universe must contain llm_editable"

    def test_llm_editable_exact_paths(self) -> None:
        profile = _load_todo_profile()
        au = profile.get("artifact_universe", {})
        editable = au.get("llm_editable", [])
        expected = {
            "todo/models.py",
            "todo/serializers.py",
            "todo/views.py",
            "todo/permissions.py",
            "todo/urls.py",
        }
        assert set(editable) == expected, f"llm_editable mismatch: {set(editable)}"

    def test_included_entries_preserved(self) -> None:
        profile = _load_todo_profile()
        au = profile.get("artifact_universe", {})
        included = au.get("included", [])
        assert "todo/models.py" in included
        assert "todo/views.py" in included
        assert "manage.py" in included

    def test_excluded_entries_preserved(self) -> None:
        profile = _load_todo_profile()
        au = profile.get("artifact_universe", {})
        excluded = au.get("excluded", [])
        excluded_paths = {e["path"] for e in excluded}
        assert "todo/migrations/" in excluded_paths


class TestRealScenarioLoading:
    def test_load_all_real_scenarios(self) -> None:
        loader = ScenarioLoader(SCENARIOS_DIR)
        scenarios = loader.load_all()
        assert len(scenarios) >= 1
        scenario_ids = [s.scenario_id for s in scenarios]
        assert "todo-loc-001" in scenario_ids

    def test_all_scenarios_valid(self) -> None:
        loader = ScenarioLoader(SCENARIOS_DIR)
        scenarios = loader.load_all()

        from benchmark.scenarios.validator import ScenarioValidator
        validator = ScenarioValidator()
        errors = validator.validate_all(scenarios)
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_scenarios_have_required_fields(self) -> None:
        loader = ScenarioLoader(SCENARIOS_DIR)
        scenarios = loader.load_all()
        for s in scenarios:
            assert s.scenario_id, f"Missing scenario_id in {s}"
            assert s.repository, f"Missing repository in {s.scenario_id}"
            assert s.requirement_before, f"Missing requirement_before in {s.scenario_id}"
            assert s.requirement_after, f"Missing requirement_after in {s.scenario_id}"
            assert s.rationale, f"Missing rationale in {s.scenario_id}"

    def test_scenario_ids_match_pattern(self) -> None:
        loader = ScenarioLoader(SCENARIOS_DIR)
        scenarios = loader.load_all()
        for s in scenarios:
            parts = s.scenario_id.split("-")
            assert len(parts) == 3, f"Unexpected scenario_id format: {s.scenario_id}"
            assert parts[0] in ("todo", "djangocms", "saleor")
            assert parts[1] in ("loc", "mod", "cross", "smoke")
            assert parts[2].isdigit()

    def test_blast_radius_distribution(self) -> None:
        loader = ScenarioLoader(SCENARIOS_DIR)
        scenarios = loader.load_all()
        from benchmark.core.enums import BlastRadius
        counts = {br: 0 for br in BlastRadius}
        for s in scenarios:
            counts[s.blast_radius] += 1
        assert counts[BlastRadius.localized] >= 1
        assert counts[BlastRadius.moderate] >= 1
        assert counts[BlastRadius.cross_cutting] >= 1
