from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DependencyNode:
    path: str
    node_type: str = "source"

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("DependencyNode.path must not be empty")


@dataclass(frozen=True)
class DependencyEdge:
    source: str
    target: str
    edge_type: str = "import"

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("DependencyEdge.source must not be empty")
        if not self.target:
            raise ValueError("DependencyEdge.target must not be empty")


@dataclass(frozen=True)
class DependencyGraphModel:
    nodes: tuple[DependencyNode, ...] = ()
    edges: tuple[DependencyEdge, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for node in self.nodes:
            if node.path in seen:
                raise ValueError(f"Duplicate node path: {node.path}")
            seen.add(node.path)

    @property
    def node_paths(self) -> tuple[str, ...]:
        return tuple(n.path for n in self.nodes)

    def adjacent(self, path: str) -> set[str]:
        result: set[str] = set()
        for edge in self.edges:
            if edge.source == path:
                result.add(edge.target)
            elif edge.target == path:
                result.add(edge.source)
        return result
