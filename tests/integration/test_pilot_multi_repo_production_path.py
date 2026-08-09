"""PILOT-READY-01: multi-repository selective production-path integration contract.

Proves the three repository-specific input contracts — dependency graph,
file-granular editable universe, and artifact descriptors — work together
through the real ``HybridSelectiveStrategy`` impact-analysis path for all 12
frozen Pilot scenarios across todo / djangocms / saleor.

- Uses real config / scenario / repository-profile loaders.
- Uses deterministic temporary mirrored snapshots (no network cloning).
- Ground Truth is evaluation-only: ``expected_affected_artifacts`` are never
  used to build the graph, the editable universe, or the descriptors. Those
  inputs come exclusively from the repository profiles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from benchmark.config.loader import load_config
from benchmark.core.enums import ActionKind
from benchmark.core.models import ArtifactUniverse, RequirementChange
from benchmark.repositories.loader import RepositoryLoader
from benchmark.repositories.snapshot import expand_editable_paths, resolve_allowed_artifacts
from benchmark.scenarios.loader import ScenarioLoader
from benchmark.selection.dependency_scope import descriptors_from_profile
from benchmark.strategies import HybridSelectiveStrategy

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_DIR / "benchmark_data"
PILOT_CONFIG_PATH = PROJECT_DIR / "configs" / "pilot.yaml"

PILOT_REPOS = ("todo", "djangocms", "saleor")


def _mirror_llm_editable(root: Path, profile: Any) -> None:
    """Deterministically mirror a profile's llm_editable policy as real files.

    Directory entries become a representative editable module. This mirrors
    profile semantics without requiring the upstream repository checkout.
    """
    au = profile.artifact_universe
    assert isinstance(au, dict)
    for entry in au["llm_editable"]:
        target = root / entry.rstrip("/") / "mod.py" if entry.endswith("/") else root / entry
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")


@pytest.fixture(scope="module")
def pilot_inputs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """Load real Pilot config/scenarios/profiles once for the whole module."""
    from seven_arm_benchmark import build_repository_dependency_graphs

    config = load_config(PILOT_CONFIG_PATH)
    scenario_ids = tuple(config.scenario_selection.scenario_ids)

    scenario_loader = ScenarioLoader(DATA_DIR / "scenarios")
    loaded = {s.scenario_id: s for s in scenario_loader.load_all()}
    scenarios = [loaded[sid] for sid in scenario_ids]

    graphs = build_repository_dependency_graphs(DATA_DIR, scenarios)

    loader = RepositoryLoader(DATA_DIR)
    collection = loader.load_manifest()
    snapshot_root = tmp_path_factory.mktemp("pilot-snapshots")

    repos: dict[str, dict[str, Any]] = {}
    for repo in PILOT_REPOS:
        profile = collection.get_profile(repo)
        assert profile is not None
        root = snapshot_root / f"snap-{repo}"
        _mirror_llm_editable(root, profile)
        editable = expand_editable_paths(
            root, tuple(profile.artifact_universe["llm_editable"])
        )
        descriptors = descriptors_from_profile(profile.artifact_catalog, editable)
        refs = resolve_allowed_artifacts(root, editable)
        repos[repo] = {
            "editable": editable,
            "descriptors": descriptors,
            "universe": ArtifactUniverse(artifacts=refs),
            "snapshot": loader.resolve_snapshot(repo),
        }

    return {
        "config": config,
        "scenario_ids": scenario_ids,
        "scenarios": scenarios,
        "graphs": graphs,
        "repos": repos,
    }


class TestPilotScenarioContract:
    """Pilot scenario IDs come from configs/pilot.yaml, all loadable, 4 per repo."""

    def test_exact_twelve_scenario_ids_from_pilot_config(
        self, pilot_inputs: dict[str, Any]
    ) -> None:
        config = pilot_inputs["config"]
        expected = tuple(config.scenario_selection.scenario_ids)
        assert len(expected) == 12
        assert pilot_inputs["scenario_ids"] == expected

    def test_four_scenarios_per_repository(self, pilot_inputs: dict[str, Any]) -> None:
        counts = {"todo": 0, "djangocms": 0, "saleor": 0}
        for sid in pilot_inputs["scenario_ids"]:
            repo = sid.split("-")[0]
            assert repo in counts
            counts[repo] += 1
        assert counts == {"todo": 4, "djangocms": 4, "saleor": 4}


class TestPerRepositoryGraphContract:
    """One graph per repository; repository-appropriate source/metadata."""

    def test_graph_map_has_exactly_the_three_repositories(
        self, pilot_inputs: dict[str, Any]
    ) -> None:
        graphs = pilot_inputs["graphs"]
        assert set(graphs) == set(PILOT_REPOS)

    def test_graph_identity_and_metadata_are_repository_appropriate(
        self, pilot_inputs: dict[str, Any]
    ) -> None:
        graphs = pilot_inputs["graphs"]

        todo_graph = graphs["todo"]
        assert len(todo_graph.nodes) == 5
        assert len(todo_graph.edges) == 6

        djangocms_graph = graphs["djangocms"]
        assert djangocms_graph.metadata.get("source") == "neutral_edgeless_fallback"
        assert djangocms_graph.metadata.get("repo_id") == "djangocms"

        saleor_graph = graphs["saleor"]
        assert saleor_graph.metadata.get("source") == "architecture_fallback"
        assert saleor_graph.metadata.get("repo_id") == "saleor"

    def test_no_graph_shared_across_repositories(self, pilot_inputs: dict[str, Any]) -> None:
        graphs = pilot_inputs["graphs"]
        assert graphs["todo"] is not graphs["djangocms"]
        assert graphs["djangocms"] is not graphs["saleor"]
        assert graphs["todo"] is not graphs["saleor"]


class TestPerRepositoryUniverseContract:
    """Editable universe and descriptors are concrete, non-empty, and consistent."""

    def test_editable_paths_concrete_non_empty(self, pilot_inputs: dict[str, Any]) -> None:
        for repo in PILOT_REPOS:
            editable = pilot_inputs["repos"][repo]["editable"]
            assert editable
            assert all(not p.endswith("/") for p in editable)
            assert all(p.endswith(".py") for p in editable)

    def test_descriptors_non_empty(self, pilot_inputs: dict[str, Any]) -> None:
        for repo in PILOT_REPOS:
            descriptors = pilot_inputs["repos"][repo]["descriptors"]
            assert descriptors, f"{repo} descriptors must be non-empty"

    def test_descriptors_within_editable_universe(self, pilot_inputs: dict[str, Any]) -> None:
        for repo in PILOT_REPOS:
            descriptors = pilot_inputs["repos"][repo]["descriptors"]
            editable = set(pilot_inputs["repos"][repo]["editable"])
            assert {d.path for d in descriptors} <= editable

    def test_universe_resolves_to_concrete_files(self, pilot_inputs: dict[str, Any]) -> None:
        for repo in PILOT_REPOS:
            universe = pilot_inputs["repos"][repo]["universe"]
            assert len(universe.artifacts) == len(pilot_inputs["repos"][repo]["editable"])

    def test_no_cross_repository_universe_reuse(self, pilot_inputs: dict[str, Any]) -> None:
        todo_editable = pilot_inputs["repos"]["todo"]["editable"]
        djangocms_editable = pilot_inputs["repos"]["djangocms"]["editable"]
        saleor_editable = pilot_inputs["repos"]["saleor"]["editable"]
        assert todo_editable != djangocms_editable
        assert djangocms_editable != saleor_editable

        todo_descs = {d.path for d in pilot_inputs["repos"]["todo"]["descriptors"]}
        saleor_descs = {d.path for d in pilot_inputs["repos"]["saleor"]["descriptors"]}
        assert todo_descs != saleor_descs


class TestSelectiveImpactAnalysisAllPilotScenarios:
    """HybridSelectiveStrategy runs for all 12 Pilot deltas without exceptions."""

    def test_all_twelve_scenarios_analyze_without_exception(
        self, pilot_inputs: dict[str, Any]
    ) -> None:
        graphs = pilot_inputs["graphs"]
        repos = pilot_inputs["repos"]
        for scenario in pilot_inputs["scenarios"]:
            repo = scenario.repository
            strategy = HybridSelectiveStrategy(
                graph=graphs[repo],
                artifact_descriptors=repos[repo]["descriptors"],
            )
            change = RequirementChange(
                before=scenario.requirement_before,
                after=scenario.requirement_after,
                acceptance_criteria=tuple(c.description for c in scenario.acceptance_criteria),
            )
            prediction = strategy.analyze_impact(
                repository=repos[repo]["snapshot"],
                requirement_change=change,
                artifact_universe=repos[repo]["universe"],
            )
            assert len(prediction.decisions) == len(repos[repo]["universe"].artifacts)
            universe_paths = {a.path for a in repos[repo]["universe"].artifacts}
            for decision in prediction.decisions:
                assert decision.artifact.path in universe_paths

    def test_regenerate_paths_never_escape_repository_universe(
        self, pilot_inputs: dict[str, Any]
    ) -> None:
        from benchmark.core.models import RequirementChange

        graphs = pilot_inputs["graphs"]
        repos = pilot_inputs["repos"]
        for scenario in pilot_inputs["scenarios"]:
            repo = scenario.repository
            strategy = HybridSelectiveStrategy(
                graph=graphs[repo],
                artifact_descriptors=repos[repo]["descriptors"],
            )
            change = RequirementChange(
                before=scenario.requirement_before,
                after=scenario.requirement_after,
                acceptance_criteria=tuple(c.description for c in scenario.acceptance_criteria),
            )
            prediction = strategy.analyze_impact(
                repository=repos[repo]["snapshot"],
                requirement_change=change,
                artifact_universe=repos[repo]["universe"],
            )
            editable = set(repos[repo]["editable"])
            for decision in prediction.decisions:
                if decision.action == ActionKind.regenerate:
                    assert decision.artifact.path in editable, (
                        f"{scenario.scenario_id}: regenerate path {decision.artifact.path} "
                        "escapes the repository editable universe"
                    )
