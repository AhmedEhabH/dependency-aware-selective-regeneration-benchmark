from __future__ import annotations

import re
from collections import deque
from typing import Any

from benchmark.core.models import DependencyGraph
from benchmark.graph.models import DependencyEdge, DependencyGraphModel


class PythonImportExtractor:
    """Extracts import-level dependency edges from Python source files."""

    _IMPORT_RE = re.compile(
        r"^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))",
        re.MULTILINE,
    )

    def extract(self, file_path: str, content: str) -> list[DependencyEdge]:
        edges: list[DependencyEdge] = []
        for match in self._IMPORT_RE.finditer(content):
            module = match.group(1) or match.group(2)
            if not module:
                continue
            target = module.replace(".", "/") + ".py"
            edges.append(
                DependencyEdge(source=file_path, target=target, edge_type="import")
            )
        return edges


class ImpactPropagator:
    """BFS propagation from seed nodes through a dependency graph."""

    def propagate(
        self,
        seeds: set[str],
        graph: DependencyGraphModel,
    ) -> set[str]:
        visited: set[str] = set(seeds)
        queue: deque[str] = deque(seeds)
        while queue:
            node = queue.popleft()
            for neighbour in graph.adjacent(node):
                if neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(neighbour)
        return visited


class ScopeReducer:
    """Filters an impact set by blast-radius scope."""

    def reduce(
        self,
        impacted: set[str],
        seeds: set[str],
        blast_radius: str,
    ) -> set[str]:
        if blast_radius == "localized":
            return seeds
        if blast_radius == "moderate":
            direct_neighbours: set[str] = set()
            for seed in seeds:
                for path in impacted:
                    if path != seed:
                        direct_neighbours.add(path)
            return seeds | set(list(direct_neighbours)[:5])
        return impacted


class ProfileGraphBuilder:
    """Builds a DependencyGraph from a repository profile's architecture data."""

    def build_from_architecture(self, architecture: dict[str, Any]) -> DependencyGraph | None:
        dep_graph = architecture.get("dependency_graph", {})
        if not isinstance(dep_graph, dict):
            return None
        edges_raw = dep_graph.get("edges", [])
        if not isinstance(edges_raw, list) or not edges_raw:
            return None
        nodes: set[str] = set()
        edges: list[tuple[str, str]] = []
        for entry in edges_raw:
            if not isinstance(entry, dict):
                continue
            from_node = entry.get("from", "")
            to_node = entry.get("to", "")
            if from_node and to_node:
                nodes.add(from_node)
                nodes.add(to_node)
                edges.append((from_node, to_node))
        if not edges:
            return None
        return DependencyGraph(
            nodes=tuple(sorted(nodes)),
            edges=tuple(edges),
            metadata={"edge_count": str(len(edges))},
        )

    def build_from_profile(self, profile: object) -> DependencyGraph | None:
        arch: dict[str, Any] = {}
        if hasattr(profile, "architecture"):
            arch = profile.architecture
        if not isinstance(arch, dict):
            return None
        return self.build_from_architecture(arch)
