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

    def _extract_architecture_paths(self, architecture: dict[str, Any]) -> set[str]:
        """Extract eligible repository-relative file paths from architecture data.

        Scans layers, module_boundaries, and dependency_graph sections for
        artifact paths mentioned in the repository profile.  Returns a set
        of normalised, deduplicated paths.  No Ground Truth enters here.
        """
        paths: set[str] = set()

        # 1. dependency_graph edges (from / to)
        dep_graph = architecture.get("dependency_graph", {})
        if isinstance(dep_graph, dict):
            for entry in dep_graph.get("edges", []):
                if isinstance(entry, dict):
                    for key in ("from", "to"):
                        val = entry.get(key, "")
                        if isinstance(val, str) and val:
                            paths.add(val)

        # 2. layer artifacts
        layers = architecture.get("layers")
        if isinstance(layers, list):
            for layer in layers:
                if isinstance(layer, dict):
                    for a in layer.get("artifacts", []):
                        if isinstance(a, str):
                            clean = a.split("(")[0].strip().rstrip("/")
                            if clean and "/" in clean:
                                paths.add(clean)
        elif isinstance(layers, dict):
            for _key, layer in layers.items():
                if isinstance(layer, dict):
                    for candidate in ("path", "artifacts"):
                        val = layer.get(candidate)
                        if isinstance(val, str):
                            if val and "/" in val:
                                paths.add(val)
                        elif isinstance(val, list):
                            for item in val:
                                if isinstance(item, str):
                                    clean = item.split("(")[0].strip().rstrip("/")
                                    if clean and "/" in clean:
                                        paths.add(clean)

        # 3. module_boundaries (source / allowed_dependencies / forbidden)
        boundaries = architecture.get("module_boundaries", [])
        if isinstance(boundaries, list):
            for b in boundaries:
                if isinstance(b, dict):
                    src = b.get("source", "")
                    if isinstance(src, str) and src:
                        paths.add(src)

        return paths

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

    def build_nodes_from_architecture(self, architecture: dict[str, Any]) -> DependencyGraph | None:
        """Build an edgeless DependencyGraph whose nodes are extracted from
        the profile's architecture data (layers, module boundaries, graph
        sources).  Returns None when no paths can be resolved.

        This is the neutral repository-derived fallback — intentionally
        conservative, no Ground Truth, no fabricated edges.
        """
        paths = self._extract_architecture_paths(architecture)
        if not paths:
            return None
        return DependencyGraph(
            nodes=tuple(sorted(paths)),
            edges=(),
            metadata={"source": "architecture_fallback"},
        )
