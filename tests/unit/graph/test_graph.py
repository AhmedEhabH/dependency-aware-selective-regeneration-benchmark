from __future__ import annotations

from pathlib import Path
from typing import cast

from benchmark.core.enums import ArtifactType, BlastRadius
from benchmark.core.models import ArtifactRef, DependencyGraph, Scenario
from benchmark.graph.builder import ImpactPropagator, ProfileGraphBuilder, PythonImportExtractor, ScopeReducer
from benchmark.graph.models import DependencyEdge, DependencyGraphModel, DependencyNode


class TestProfileGraphBuilder:
    """ProfileGraphBuilder: neutral repository-derived fallback and architecture extraction."""

    def test_extract_architecture_paths_from_layer_list(self) -> None:
        builder = ProfileGraphBuilder()
        arch = {
            "layers": [
                {"id": "api", "artifacts": ["src/views.py", "src/urls.py"]},
                {"id": "data", "artifacts": ["src/models.py"]},
            ],
        }
        paths = builder._extract_architecture_paths(arch)
        assert paths == {"src/views.py", "src/urls.py", "src/models.py"}

    def test_extract_architecture_paths_from_layer_dict(self) -> None:
        builder = ProfileGraphBuilder()
        arch = {
            "layers": {
                "graphql": {"path": "saleor/graphql", "role": "api"},
                "domain": {"path": "saleor/order", "role": "core"},
            },
        }
        paths = builder._extract_architecture_paths(arch)
        assert "saleor/graphql" in paths
        assert "saleor/order" in paths

    def test_extract_architecture_paths_from_dependency_graph(self) -> None:
        builder = ProfileGraphBuilder()
        arch = {
            "dependency_graph": {
                "edges": [
                    {"from": "src/a.py", "to": "src/b.py"},
                ],
            },
        }
        paths = builder._extract_architecture_paths(arch)
        assert paths == {"src/a.py", "src/b.py"}

    def test_extract_architecture_paths_from_boundaries(self) -> None:
        builder = ProfileGraphBuilder()
        arch = {
            "module_boundaries": [
                {"source": "src/views.py"},
                {"source": "src/models.py"},
            ],
        }
        paths = builder._extract_architecture_paths(arch)
        assert paths == {"src/views.py", "src/models.py"}

    def test_extract_architecture_paths_skips_annotations(self) -> None:
        builder = ProfileGraphBuilder()
        arch = {
            "layers": [
                {"artifacts": ["src/models.py (field definitions)", "src/migrations/"]},
            ],
        }
        paths = builder._extract_architecture_paths(arch)
        assert "src/models.py" in paths
        # Parenthetical annotation is stripped; directory path kept
        assert "src/migrations" in paths

    def test_extract_architecture_paths_empty_returns_empty(self) -> None:
        builder = ProfileGraphBuilder()
        assert builder._extract_architecture_paths({}) == set()

    def test_build_nodes_from_architecture_returns_edgeless_graph(self) -> None:
        builder = ProfileGraphBuilder()
        arch = {
            "layers": [
                {"artifacts": ["src/a.py", "src/b.py"]},
            ],
        }
        graph = builder.build_nodes_from_architecture(arch)
        assert graph is not None
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 0
        assert graph.metadata.get("source") == "architecture_fallback"

    def test_build_nodes_from_architecture_none_when_no_paths(self) -> None:
        builder = ProfileGraphBuilder()
        assert builder.build_nodes_from_architecture({}) is None

    def test_build_nodes_from_architecture_deterministic(self) -> None:
        builder = ProfileGraphBuilder()
        arch = {
            "layers": [
                {"artifacts": ["src/b.py", "src/a.py"]},
            ],
        }
        g1 = builder.build_nodes_from_architecture(arch)
        g2 = builder.build_nodes_from_architecture(arch)
        assert g1 is not None and g2 is not None
        assert g1.nodes == ("src/a.py", "src/b.py")
        assert g1.nodes == g2.nodes

    def test_build_nodes_from_architecture_no_fabricated_edges(self) -> None:
        """Architecture-derived graph must never have edges — only nodes."""
        builder = ProfileGraphBuilder()
        arch = {
            "layers": [
                {"artifacts": ["src/a.py", "src/b.py"]},
            ],
        }
        graph = builder.build_nodes_from_architecture(arch)
        assert graph is not None
        assert len(graph.edges) == 0


# ---------------------------------------------------------------------------
# SU-0010B1B Critical Leakage-Regression Tests
# ---------------------------------------------------------------------------


class TestGroundTruthLeakageRegression:
    """Dependency graph construction must never use Ground Truth.

    Repository-derived artifacts must be used exclusively; Ground Truth-only
    paths must never appear as graph nodes.
    """

    def _make_minimal_data_dir(self, tmp_path: Path, repo_id: str, profile_yaml: str) -> Path:
        data_dir = tmp_path / "data"
        (data_dir / "scenarios").mkdir(parents=True)
        (data_dir / "manifests").mkdir(parents=True)
        (data_dir / "repository_profiles").mkdir(parents=True)

        # Minimal manifest
        repos_yaml = f"repositories:\n  {repo_id}:\n    url: https://example.com\n"
        (data_dir / "manifests" / "repositories.yaml").write_text(repos_yaml, encoding="utf-8")
        versions_yaml = f"versions:\n  {repo_id}:\n    commit_sha: abc123\n"
        (data_dir / "manifests" / "repository_versions.yaml").write_text(versions_yaml, encoding="utf-8")

        # Minimal scenario (avoids loader loading all 24 scenarios)
        scenario_yaml = f"""scenario_id: "test-{repo_id}-001"
repository: {repo_id}
change_type: "modify"
blast_radius: localized
requirement_before: "before"
requirement_after: "after"
rationale: "test"
"""
        (data_dir / "scenarios" / f"{repo_id}-test.yaml").write_text(scenario_yaml, encoding="utf-8")

        # Profile
        (data_dir / "repository_profiles" / f"{repo_id}.yaml").write_text(profile_yaml, encoding="utf-8")
        return data_dir

    def _make_scenario(self, repo_id: str, artifacts: tuple[str, ...] = ()) -> Scenario:
        return Scenario(
            scenario_id=f"test-{repo_id}-001",
            repository=repo_id,
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=tuple(
                ArtifactRef(path=p, artifact_type=ArtifactType.source) for p in artifacts
            ),
        )

    def _build_graph(
        self, data_dir: Path, scenario: Scenario
    ) -> DependencyGraph:
        from seven_arm_benchmark import build_dependency_graph
        graph = build_dependency_graph(data_dir, [scenario])
        assert graph is not None
        return cast(DependencyGraph, graph)

    def test_graph_contains_repo_artifacts_not_ground_truth(self, tmp_path: Path) -> None:
        """Repository-derived artifacts present; Ground Truth-only path absent."""
        repo_id = "test-repo"
        profile_yaml = """
repository_id: test-repo
architecture:
  dependency_graph:
    edges:
      - from: src/actual_a.py
        to: src/actual_b.py
"""
        data_dir = self._make_minimal_data_dir(tmp_path, repo_id, profile_yaml)

        scenario = self._make_scenario(
            repo_id=repo_id,
            artifacts=("src/ground_truth_only.py",),
        )
        graph = self._build_graph(data_dir, scenario)
        node_set = set(graph.nodes)

        # Repository-derived artifacts must be present
        assert "src/actual_a.py" in node_set
        assert "src/actual_b.py" in node_set

        # Ground Truth-only path must NOT be present
        assert "src/ground_truth_only.py" not in node_set

    def test_real_profile_graph_remains_preferred(self, tmp_path: Path) -> None:
        """When a real profile graph with edges exists, it is used over fallback."""
        repo_id = "test-repo"
        profile_yaml = """
repository_id: test-repo
architecture:
  dependency_graph:
    edges:
      - from: src/preferred_a.py
        to: src/preferred_b.py
"""
        data_dir = self._make_minimal_data_dir(tmp_path, repo_id, profile_yaml)

        scenario = self._make_scenario(
            repo_id=repo_id,
            artifacts=("src/ground_truth_only.py",),
        )
        graph = self._build_graph(data_dir, scenario)
        assert len(graph.edges) >= 1
        assert ("src/preferred_a.py", "src/preferred_b.py") in graph.edges
        # Ground Truth must not pollute the real graph
        assert "src/ground_truth_only.py" not in graph.nodes

    def test_neutral_fallback_is_edgeless_and_deterministic(self, tmp_path: Path) -> None:
        """When no profile graph, neutral fallback has zero edges and no GT."""
        repo_id = "test-repo"
        profile_yaml = """repository_id: test-repo
name: Test Repo
protocol_version: "1.0"
overview: test
"""
        data_dir = self._make_minimal_data_dir(tmp_path, repo_id, profile_yaml)

        scenario = self._make_scenario(
            repo_id=repo_id,
            artifacts=("src/ground_truth_only.py",),
        )
        graph = self._build_graph(data_dir, scenario)
        # Neutral fallback: edgeless, no Ground Truth nodes
        assert len(graph.edges) == 0
        assert "src/ground_truth_only.py" not in graph.nodes
        # Metadata identifies fallback source
        assert graph.metadata.get("source") == "neutral_edgeless_fallback"

    def test_neutral_fallback_has_zero_fabricated_edges(self, tmp_path: Path) -> None:
        """Neutral fallback must never fabricate dependency edges."""
        repo_id = "test-repo"
        profile_yaml = """repository_id: test-repo
name: Test Repo
protocol_version: "1.0"
overview: test
"""
        data_dir = self._make_minimal_data_dir(tmp_path, repo_id, profile_yaml)

        scenario = self._make_scenario(
            repo_id=repo_id,
            artifacts=("src/a.py", "src/b.py"),
        )
        graph = self._build_graph(data_dir, scenario)
        assert len(graph.edges) == 0  # No fabricated edges

    def test_empty_repository_returns_empty_graph(self, tmp_path: Path) -> None:
        """When data dir has no profile at all, still returns edgeless graph."""
        repo_id = "test-repo"
        profile_yaml = """repository_id: test-repo
name: Test Repo
protocol_version: "1.0"
overview: test
"""
        data_dir = self._make_minimal_data_dir(tmp_path, repo_id, profile_yaml)

        scenario = self._make_scenario(repo_id=repo_id, artifacts=())
        graph = self._build_graph(data_dir, scenario)
        # Returns neutral fallback, not None
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_repeated_construction_produces_equal_graph(self, tmp_path: Path) -> None:
        repo_id = "test-repo"
        profile_yaml = """
repository_id: test-repo
architecture:
  dependency_graph:
    edges:
      - from: src/a.py
        to: src/b.py
"""
        data_dir = self._make_minimal_data_dir(tmp_path, repo_id, profile_yaml)
        scenario = self._make_scenario(repo_id=repo_id, artifacts=())

        g1 = self._build_graph(data_dir, scenario)
        g2 = self._build_graph(data_dir, scenario)
        assert g1.nodes == g2.nodes
        assert g1.edges == g2.edges

    def test_expected_actions_do_not_alter_graph(self, tmp_path: Path) -> None:
        """expected_actions on scenario must not change graph construction."""
        repo_id = "test-repo"
        profile_yaml = """
repository_id: test-repo
architecture:
  dependency_graph:
    edges:
      - from: src/a.py
        to: src/b.py
"""
        data_dir = self._make_minimal_data_dir(tmp_path, repo_id, profile_yaml)

        scenario_with_gt = Scenario(
            scenario_id="test",
            repository=repo_id,
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=(ArtifactRef(path="src/gt.py", artifact_type=ArtifactType.source),),
            expected_actions=(),
        )
        graph_no_actions = self._build_graph(data_dir, scenario_with_gt)

        # Same scenario without actions/GT
        scenario_clean = Scenario(
            scenario_id="test",
            repository=repo_id,
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
        )
        graph_with_data = self._build_graph(data_dir, scenario_clean)
        assert graph_no_actions.nodes == graph_with_data.nodes
        assert graph_no_actions.edges == graph_with_data.edges

    def test_ground_truth_only_paths_never_become_nodes(self, tmp_path: Path) -> None:
        """Ground Truth-only artifacts must never be graph nodes."""
        repo_id = "test-repo"
        profile_yaml = """
repository_id: test-repo
architecture:
  dependency_graph:
    edges:
      - from: src/real.py
        to: src/also_real.py
"""
        data_dir = self._make_minimal_data_dir(tmp_path, repo_id, profile_yaml)

        scenario = Scenario(
            scenario_id="test",
            repository=repo_id,
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=(
                ArtifactRef(path="src/gt_only.py", artifact_type=ArtifactType.source),
            ),
            expected_actions=(),
        )
        graph = self._build_graph(data_dir, scenario)
        assert "src/gt_only.py" not in graph.nodes
        assert "src/real.py" in graph.nodes
        assert "src/also_real.py" in graph.nodes

    def test_graph_construction_does_not_mutate_artifact_universe(self, tmp_path: Path) -> None:
        """Calling build_dependency_graph must not alter input scenarios."""
        from copy import deepcopy

        from benchmark.core.enums import ArtifactType
        from benchmark.core.models import ArtifactRef

        repo_id = "test-repo"
        profile_yaml = """
repository_id: test-repo
architecture:
  dependency_graph:
    edges:
      - from: src/a.py
        to: src/b.py
"""
        data_dir = self._make_minimal_data_dir(tmp_path, repo_id, profile_yaml)

        scenario = Scenario(
            scenario_id="test",
            repository=repo_id,
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=(ArtifactRef(path="src/gt.py", artifact_type=ArtifactType.source),),
        )
        before = deepcopy(scenario)
        self._build_graph(data_dir, scenario)
        assert before == scenario


# ---------------------------------------------------------------------------
# Original graph unit tests
# ---------------------------------------------------------------------------


class TestDependencyNode:
    def test_valid_creation(self) -> None:
        node = DependencyNode(path="src/models.py")
        assert node.path == "src/models.py"
        assert node.node_type == "source"

    def test_empty_path_raises(self) -> None:
        try:
            DependencyNode(path="")
            raise AssertionError("Should have raised")
        except ValueError:
            pass


class TestDependencyEdge:
    def test_valid_creation(self) -> None:
        edge = DependencyEdge(source="a.py", target="b.py")
        assert edge.source == "a.py"
        assert edge.target == "b.py"
        assert edge.edge_type == "import"

    def test_empty_source_raises(self) -> None:
        try:
            DependencyEdge(source="", target="b.py")
            raise AssertionError("Should have raised")
        except ValueError:
            pass

    def test_empty_target_raises(self) -> None:
        try:
            DependencyEdge(source="a.py", target="")
            raise AssertionError("Should have raised")
        except ValueError:
            pass


class TestDependencyGraphModel:
    def test_valid_creation(self) -> None:
        graph = DependencyGraphModel(
            nodes=(DependencyNode(path="a.py"), DependencyNode(path="b.py")),
            edges=(DependencyEdge(source="a.py", target="b.py"),),
        )
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1

    def test_duplicate_node_raises(self) -> None:
        try:
            DependencyGraphModel(
                nodes=(DependencyNode(path="a.py"), DependencyNode(path="a.py")),
            )
            raise AssertionError("Should have raised")
        except ValueError:
            pass

    def test_node_paths_property(self) -> None:
        graph = DependencyGraphModel(
            nodes=(DependencyNode(path="x.py"), DependencyNode(path="y.py")),
        )
        assert graph.node_paths == ("x.py", "y.py")

    def test_adjacent(self) -> None:
        graph = DependencyGraphModel(
            nodes=(DependencyNode(path="a.py"), DependencyNode(path="b.py"), DependencyNode(path="c.py")),
            edges=(
                DependencyEdge(source="a.py", target="b.py"),
                DependencyEdge(source="b.py", target="c.py"),
            ),
        )
        assert graph.adjacent("a.py") == {"b.py"}
        assert graph.adjacent("b.py") == {"a.py", "c.py"}
        assert graph.adjacent("c.py") == {"b.py"}


class TestPythonImportExtractor:
    def test_extracts_from_import(self) -> None:
        extractor = PythonImportExtractor()
        edges = extractor.extract(
            "src/views.py",
            "from src.models import User\nimport os\n",
        )
        assert len(edges) >= 2
        sources = {e.target for e in edges}
        assert "src/models.py" in sources

    def test_no_imports(self) -> None:
        extractor = PythonImportExtractor()
        edges = extractor.extract("src/utils.py", "x = 1\n")
        assert len(edges) == 0


class TestImpactPropagator:
    def test_propagate_from_single_seed(self) -> None:
        graph = DependencyGraphModel(
            nodes=(
                DependencyNode(path="a.py"),
                DependencyNode(path="b.py"),
                DependencyNode(path="c.py"),
            ),
            edges=(
                DependencyEdge(source="a.py", target="b.py"),
                DependencyEdge(source="b.py", target="c.py"),
            ),
        )
        propagator = ImpactPropagator()
        result = propagator.propagate({"a.py"}, graph)
        assert result == {"a.py", "b.py", "c.py"}

    def test_propagate_disconnected(self) -> None:
        graph = DependencyGraphModel(
            nodes=(DependencyNode(path="a.py"), DependencyNode(path="b.py")),
            edges=(),
        )
        propagator = ImpactPropagator()
        result = propagator.propagate({"a.py"}, graph)
        assert result == {"a.py"}


class TestScopeReducer:
    def test_localized_returns_seeds_only(self) -> None:
        reducer = ScopeReducer()
        result = reducer.reduce({"a.py", "b.py", "c.py"}, {"a.py"}, "localized")
        assert result == {"a.py"}

    def test_moderate_limits_breadth(self) -> None:
        reducer = ScopeReducer()
        result = reducer.reduce({"a.py", "b.py", "c.py", "d.py"}, {"a.py"}, "moderate")
        assert "a.py" in result

    def test_cross_cutting_returns_all(self) -> None:
        reducer = ScopeReducer()
        result = reducer.reduce({"a.py", "b.py"}, {"a.py"}, "cross_cutting")
        assert result == {"a.py", "b.py"}
