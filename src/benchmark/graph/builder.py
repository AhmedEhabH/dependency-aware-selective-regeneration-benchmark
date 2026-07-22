from __future__ import annotations

import re
from collections import deque

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
