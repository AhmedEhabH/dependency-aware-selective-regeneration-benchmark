"""PILOT-READY-01 addendum: multi-repository selective input contract.

RED tests for the three latent production-path blockers found by the
independent audit:

  A. one dependency graph built from the first repository and reused for
     every Pilot run;
  B. django CMS / Saleor ``llm_editable`` directories are rejected by the real
     file-granular ``resolve_allowed_artifacts`` runtime;
  C. non-todo ``artifact_catalog`` shapes do not produce a usable descriptor
     set (Saleor currently produces zero).

Ground Truth is evaluation-only: none of these tests encode expected Ground
Truth matches. They prove the input contract (graph identity, editable
universe, descriptors) is repository-specific, deterministic, and executable.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.core.enums import BlastRadius
from benchmark.core.exceptions import RepositoryError
from benchmark.core.models import Scenario
from benchmark.repositories.loader import RepositoryLoader
from benchmark.repositories.snapshot import resolve_allowed_artifacts

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_DIR / "benchmark_data"

PILOT_REPOS = ("todo", "djangocms", "saleor")
PILOT_SCENARIO_IDS = [
    "todo-loc-001",
    "todo-loc-002",
    "todo-mod-004",
    "todo-cross-007",
    "djangocms-mod-005",
    "djangocms-loc-002",
    "djangocms-mod-004",
    "djangocms-cross-007",
    "saleor-loc-001",
    "saleor-loc-002",
    "saleor-mod-004",
    "saleor-cross-007",
]


def _pilot_scenario(scenario_id: str) -> Scenario:
    repo = scenario_id.split("-")[0]
    return Scenario(
        scenario_id=scenario_id,
        repository=repo,
        change_type="modify",
        blast_radius=BlastRadius.localized,
        requirement_before="before",
        requirement_after="after",
        rationale="pilot readiness input contract",
    )


def _pilot_scenarios() -> list[Scenario]:
    return [_pilot_scenario(sid) for sid in PILOT_SCENARIO_IDS]


def _mirror_llm_editable(root: Path, profile: object) -> None:
    """Deterministically mirror a profile's llm_editable policy as real files.

    Directory entries become a representative editable module. This mirrors
    profile semantics without requiring the upstream repository checkout.
    """
    au = profile.artifact_universe
    assert isinstance(au, dict)
    llm_editable = au["llm_editable"]
    assert isinstance(llm_editable, list)
    for entry in llm_editable:
        target = root / entry.rstrip("/") / "mod.py" if entry.endswith("/") else root / entry
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")


def _editable_for_repo(
    tmp_path: Path, repo: str
) -> tuple[object, tuple[str, ...]]:
    loader = RepositoryLoader(DATA_DIR)
    collection = loader.load_manifest()
    profile = collection.get_profile(repo)
    assert profile is not None
    root = tmp_path / f"snap-{repo}"
    root.mkdir()
    _mirror_llm_editable(root, profile)
    from benchmark.repositories.snapshot import expand_editable_paths

    llm_editable = tuple(profile.artifact_universe["llm_editable"])
    expanded = expand_editable_paths(root, llm_editable)
    return profile, expanded


class TestT1MixedRepositoryGraphFailsClosed:
    """T1 — build_dependency_graph must not silently use the first repository."""

    def test_mixed_repository_scenarios_fail_closed(self) -> None:
        from seven_arm_benchmark import build_dependency_graph

        mixed = [
            _pilot_scenario("todo-loc-001"),
            _pilot_scenario("djangocms-mod-005"),
        ]
        with pytest.raises(ValueError, match="single repository"):
            build_dependency_graph(DATA_DIR, mixed)


class TestT2PerRepositoryPilotGraphMap:
    """T2 — main() graph path produces exactly the per-repository Pilot map."""

    def test_exact_keys_todo_djangocms_saleor(self) -> None:
        from seven_arm_benchmark import build_repository_dependency_graphs

        graphs = build_repository_dependency_graphs(DATA_DIR, _pilot_scenarios())
        assert set(graphs) == set(PILOT_REPOS)

    def test_repository_specific_graph_evidence(self) -> None:
        from seven_arm_benchmark import build_repository_dependency_graphs

        graphs = build_repository_dependency_graphs(DATA_DIR, _pilot_scenarios())
        assert graphs["todo"] is not graphs["djangocms"]
        assert graphs["djangocms"] is not graphs["saleor"]

        todo_graph = graphs["todo"]
        assert len(todo_graph.nodes) == 5
        assert len(todo_graph.edges) == 6

        djangocms_graph = graphs["djangocms"]
        assert djangocms_graph.metadata.get("source") == "neutral_edgeless_fallback"
        assert djangocms_graph.metadata.get("repo_id") == "djangocms"

        saleor_graph = graphs["saleor"]
        assert saleor_graph.metadata.get("source") == "architecture_fallback"
        assert saleor_graph.metadata.get("repo_id") == "saleor"


class TestT3EditableUniverseExecutable:
    """T3 — real llm_editable policy resolves without directory rejection."""

    def test_directory_policy_expands_to_concrete_files(self, tmp_path: Path) -> None:
        from benchmark.repositories.snapshot import expand_editable_paths

        snap = tmp_path / "snap"
        (snap / "cms" / "middleware").mkdir(parents=True)
        (snap / "cms" / "middleware" / "toolbar.py").write_text("", encoding="utf-8")
        (snap / "cms" / "middleware" / "page.py").write_text("", encoding="utf-8")
        (snap / "cms" / "middleware" / "tests").mkdir()
        (snap / "cms" / "middleware" / "tests" / "test_toolbar.py").write_text("", encoding="utf-8")
        (snap / "cms" / "middleware" / "migrations").mkdir()
        (snap / "cms" / "middleware" / "migrations" / "0001.py").write_text("", encoding="utf-8")
        (snap / "menus").mkdir()
        (snap / "menus" / "menu.py").write_text("", encoding="utf-8")

        expanded = expand_editable_paths(snap, ("cms/middleware/", "menus/"))
        assert expanded == (
            "cms/middleware/page.py",
            "cms/middleware/toolbar.py",
            "menus/menu.py",
        )
        assert all(not p.endswith("/") for p in expanded)
        assert "cms/middleware/tests/test_toolbar.py" not in expanded
        assert "cms/middleware/migrations/0001.py" not in expanded

    def test_expanded_universe_resolves_without_directory_rejection(
        self, tmp_path: Path
    ) -> None:
        from benchmark.repositories.snapshot import expand_editable_paths

        snap = tmp_path / "snap"
        (snap / "cms" / "middleware").mkdir(parents=True)
        (snap / "cms" / "middleware" / "toolbar.py").write_text("", encoding="utf-8")
        (snap / "menus").mkdir()
        (snap / "menus" / "menu.py").write_text("", encoding="utf-8")

        expanded = expand_editable_paths(snap, ("cms/middleware/", "menus/"))
        resolved = resolve_allowed_artifacts(snap, expanded)
        assert [r.path for r in resolved] == list(expanded)
        assert all(r.path.endswith(".py") for r in resolved)

    def test_empty_directory_fails_closed(self, tmp_path: Path) -> None:
        from benchmark.repositories.snapshot import expand_editable_paths

        snap = tmp_path / "snap"
        (snap / "empty").mkdir(parents=True)
        with pytest.raises(RepositoryError, match="no eligible source files"):
            expand_editable_paths(snap, ("empty/",))

    def test_duplicate_normalized_paths_rejected(self, tmp_path: Path) -> None:
        from benchmark.repositories.snapshot import expand_editable_paths

        snap = tmp_path / "snap"
        (snap / "cms").mkdir(parents=True)
        (snap / "cms" / "models.py").write_text("", encoding="utf-8")
        with pytest.raises(RepositoryError, match="Duplicate path"):
            expand_editable_paths(snap, ("cms/models.py", "cms/models.py"))

    def test_policy_guards_remain_green(self, tmp_path: Path) -> None:
        from benchmark.repositories.snapshot import expand_editable_paths

        snap = tmp_path / "snap"
        snap.mkdir()
        for bad in ("/abs.py", "../outside/foo.py", "a\\b.py"):
            with pytest.raises(RepositoryError):
                expand_editable_paths(snap, (bad,))

    def test_all_three_pilot_profiles_expand(self, tmp_path: Path) -> None:
        for repo in PILOT_REPOS:
            _profile, expanded = _editable_for_repo(tmp_path, repo)
            assert expanded, f"{repo} llm_editable expanded to nothing"


class TestT4ArtifactDescriptorsExecutable:
    """T4 — all three Pilot repositories produce canonical usable descriptors."""

    def test_todo_descriptors_nonempty_and_semantically_unchanged(
        self, tmp_path: Path
    ) -> None:
        from benchmark.selection.dependency_scope import descriptors_from_profile

        profile, editable = _editable_for_repo(tmp_path, "todo")
        descs = descriptors_from_profile(profile.artifact_catalog, editable)
        assert [d.path for d in descs] == [
            "todo/models.py",
            "todo/permissions.py",
            "todo/serializers.py",
            "todo/urls.py",
            "todo/views.py",
        ]

    def test_djangocms_descriptors_nonempty_and_concrete(self, tmp_path: Path) -> None:
        from benchmark.selection.dependency_scope import descriptors_from_profile

        profile, editable = _editable_for_repo(tmp_path, "djangocms")
        descs = descriptors_from_profile(profile.artifact_catalog, editable)
        paths = {d.path for d in descs}
        assert paths, "djangocms descriptors must be non-empty"
        assert "cms/api.py" in paths
        assert "cms/admin/pageadmin.py" in paths
        assert any(p.startswith("cms/models/") for p in paths)

    def test_saleor_descriptors_path_based_not_category_keys(
        self, tmp_path: Path
    ) -> None:
        from benchmark.selection.dependency_scope import descriptors_from_profile

        profile, editable = _editable_for_repo(tmp_path, "saleor")
        descs = descriptors_from_profile(profile.artifact_catalog, editable)
        paths = {d.path for d in descs}
        assert paths, "saleor descriptors must be non-empty"
        assert "saleor/graphql/api.py" in paths
        assert "graphql_schema" not in paths
        assert all("/" in p for p in paths)

    def test_descriptors_stay_within_profile_editable_universe(
        self, tmp_path: Path
    ) -> None:
        from benchmark.selection.dependency_scope import descriptors_from_profile

        for repo in PILOT_REPOS:
            profile, editable = _editable_for_repo(tmp_path, repo)
            descs = descriptors_from_profile(profile.artifact_catalog, editable)
            dpaths = {d.path for d in descs}
            assert dpaths, f"{repo} descriptors must be non-empty"
            assert dpaths <= set(editable), (
                f"{repo} descriptors must come from the profile editable universe"
            )


class TestT5PilotMultiRepoWiring:
    """T5 — each selected Pilot scenario receives ITS repository's inputs."""

    def test_no_cross_repository_input_reuse(self, tmp_path: Path) -> None:
        from benchmark.repositories.snapshot import expand_editable_paths
        from benchmark.selection.dependency_scope import descriptors_from_profile
        from seven_arm_benchmark import build_repository_dependency_graphs

        scenarios = _pilot_scenarios()
        graphs = build_repository_dependency_graphs(DATA_DIR, scenarios)
        assert set(graphs) == set(PILOT_REPOS)

        loader = RepositoryLoader(DATA_DIR)
        collection = loader.load_manifest()
        editable: dict[str, tuple[str, ...]] = {}
        descriptors: dict[str, tuple[object, ...]] = {}
        for repo in PILOT_REPOS:
            profile = collection.get_profile(repo)
            assert profile is not None
            root = tmp_path / f"w-{repo}"
            root.mkdir()
            _mirror_llm_editable(root, profile)
            llm_editable = tuple(profile.artifact_universe["llm_editable"])
            editable[repo] = expand_editable_paths(root, llm_editable)
            descriptors[repo] = descriptors_from_profile(
                profile.artifact_catalog, editable[repo]
            )

        # main()'s per-run lookup: dep_graph=_dep_graphs[repository_id],
        # editable_artifact_paths=_editable_paths.get(repository_id),
        # artifact_descriptors=_artifact_descriptors.get(repository_id).
        for scenario in scenarios:
            repo = scenario.repository
            assert graphs[repo] is graphs[repo]
            assert editable[repo], f"{repo} editable universe empty"
            assert descriptors[repo], f"{repo} descriptors empty"

        # A single graph / descriptor set must never be reused across repos.
        assert graphs["todo"] is not graphs["djangocms"]
        assert graphs["djangocms"] is not graphs["saleor"]
        assert editable["todo"] != editable["djangocms"]
        assert descriptors["djangocms"] != descriptors["saleor"]
