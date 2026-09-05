"""Stage-C automatic evidence collector for the ImpactPlan treatment (D047).

The collector builds the strategy-visible evidence items that the Impact
Planner may cite. It deliberately reuses existing plumbing (the Todo static
dependency graph, artifact descriptors / seed matching) and adds only the
minimal new pieces required by the Stage-C contract:

- static graph evidence (dependency edges inside/around the candidate universe);
- semantic seed evidence from descriptors / requirement signals;
- automatic repository-native test-link evidence (Todo ``todo/tests/test_*.py``
  modules mapped to the source module they exercise);
- architectural evidence: visible architecture constraints normalized into
  non-gold planner constraints.

NO scenario gold (expected_actions), NO hidden evaluator content, and NO final
result tables ever enter this collector.
"""

from __future__ import annotations

import re
from pathlib import Path

from benchmark.core.models import (
    ArtifactUniverse,
    DependencyGraph,
    EvidenceItem,
    RequirementChange,
)
from benchmark.selection.dependency_scope import (
    ArtifactDescriptor,
    derive_requirement_terms,
)


def collect_impact_evidence(
    requirement_change: RequirementChange,
    artifact_universe: ArtifactUniverse,
    descriptors: tuple[ArtifactDescriptor, ...],
    graph: DependencyGraph,
    *,
    workspace_root: str | Path | None = None,
    extra_architecture_constraints: tuple[str, ...] = (),
) -> tuple[EvidenceItem, ...]:
    """Collect deterministic strategy-visible evidence for the candidate universe."""
    items: list[EvidenceItem] = []
    universe = {a.path for a in artifact_universe.artifacts}

    # 1. Static graph evidence: edges whose endpoints overlap the universe.
    for index, (src, dst) in enumerate(graph.edges):
        if src in universe or dst in universe:
            items.append(
                EvidenceItem(
                    evidence_id=f"static-graph-edge-{index}",
                    artifact_path=dst if dst in universe else src,
                    evidence_type="static",
                    source="todo_dependency_graph",
                    direction="dependency_edge",
                    description=f"static dependency edge {src} -> {dst}",
                )
            )

    # 2. Semantic seed evidence from descriptors (reuse existing term matching).
    req_terms = derive_requirement_terms(requirement_change)
    for index, desc in enumerate(descriptors):
        trigger_terms: set[str] = set()
        for trig in desc.typical_change_triggers:
            trigger_terms.update(
                t.lower() for t in re.findall(r"[a-z]+", trig.lower()) if len(t) > 2
            )
        for sym in desc.provides_symbols:
            trigger_terms.update(
                t.lower() for t in re.findall(r"[a-z]+", sym.lower()) if len(t) > 2
            )
        overlap = req_terms & trigger_terms
        if overlap:
            items.append(
                EvidenceItem(
                    evidence_id=f"semantic-seed-{index}",
                    artifact_path=desc.path,
                    evidence_type="semantic",
                    source="artifact_descriptors_and_requirement",
                    direction="semantic_seed",
                    description=(
                        f"artifact descriptor matches requirement terms: "
                        f"{sorted(overlap)[:6]}"
                    ),
                    score=float(len(overlap)),
                )
            )

    # 3. Repository-native test-link evidence (automatic, Todo scope).
    if workspace_root is not None:
        items.extend(
            _discover_test_links(
                Path(workspace_root),
                universe=universe,
            )
        )

    # 4. Architecture evidence: visible constraints normalized as planner inputs.
    for index, constraint in enumerate(extra_architecture_constraints):
        if constraint.strip():
            items.append(
                EvidenceItem(
                    evidence_id=f"architecture-constraint-{index}",
                    artifact_path="",
                    evidence_type="architecture",
                    source="visible_architecture_constraints",
                    direction="architecture_obligation",
                    description=constraint.strip(),
                )
            )

    return tuple(items)


def _discover_test_links(
    root: Path,
    *,
    universe: set[str],
) -> list[EvidenceItem]:
    """Automatically map repository-native test modules to candidate sources.

    Todo layout: ``todo/tests/test_<module>.py`` exercises ``todo/<module>.py``.
    A test module is evidence (test_link) for the source it names.
    """
    items: list[EvidenceItem] = []
    tests_dir = root / "todo" / "tests"
    if not tests_dir.is_dir():
        return items

    candidate_basenames = {
        Path(p).name for p in universe
    }
    index = 0
    for path in sorted(tests_dir.iterdir()):
        if path.suffix != ".py" or path.name == "__init__.py":
            continue
        stem = path.stem
        source_name = stem.removeprefix("test_") + ".py"
        if source_name not in candidate_basenames:
            continue
        source_path = f"todo/{source_name}"
        evidence = _test_link_evidence(
            source_path=source_path,
            test_path=f"todo/tests/{path.name}",
            index=index,
        )
        index += 1
        items.append(evidence)
    return items


def _test_link_evidence(
    *,
    source_path: str,
    test_path: str,
    index: int,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=f"test-link-{index}",
        artifact_path=source_path,
        evidence_type="test_link",
        source="repository_native_tests",
        direction="test_to_source",
        description=(
            f"repository-native test module {test_path} exercises {source_path}"
        ),
        score=1.0,
    )
