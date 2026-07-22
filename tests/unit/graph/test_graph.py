from benchmark.graph.builder import ImpactPropagator, PythonImportExtractor, ScopeReducer
from benchmark.graph.models import DependencyEdge, DependencyGraphModel, DependencyNode


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
