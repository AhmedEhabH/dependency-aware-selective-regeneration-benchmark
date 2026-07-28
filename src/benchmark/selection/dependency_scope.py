from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from benchmark.core.models import (
    ArtifactUniverse,
    DependencyGraph,
    RequirementChange,
)


@dataclass(frozen=True)
class ArtifactDescriptor:
    path: str
    category: str
    description: str
    provides_symbols: tuple[str, ...]
    typical_change_triggers: tuple[str, ...]


STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "by", "with", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "not",
    "no", "nor", "so", "if", "then", "than", "that", "this", "these",
    "those", "it", "its", "they", "them", "their", "we", "our", "you",
    "your", "he", "she", "him", "her", "his", "my", "all",
    "each", "every", "both", "few", "more", "most", "other", "some",
    "such", "only", "own", "same", "too", "very", "just", "about",
    "above", "after", "again", "against", "below", "between", "during",
    "before", "behind", "down", "up", "out", "off", "over", "under",
    "into", "through", "until", "upon", "within", "without",
})


def _normalize(text: str) -> list[str]:
    parts: list[str] = []
    for token in text.lower().split():
        token = token.strip("(),.;:\"'!?[]{}")
        if not token:
            continue
        snake_parts = token.split("_")
        for sp in snake_parts:
            camel_parts = re.findall(r"[a-z]+|[A-Z][a-z]*|[A-Z]+(?=[A-Z]|$)", sp)
            parts.extend(p.lower() for p in camel_parts)
    return parts


def _singular(word: str) -> str:
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("es") and len(word) > 4:
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def descriptors_from_profile(
    artifact_catalog: tuple[dict[str, Any] | str, ...],
    editable_paths: tuple[str, ...],
) -> tuple[ArtifactDescriptor, ...]:
    editable_set = set(editable_paths)
    result: list[ArtifactDescriptor] = []
    for entry in artifact_catalog:
        if isinstance(entry, dict):
            path: str = entry.get("id", "")
        else:
            path = str(entry)
        if path not in editable_set:
            continue
        if isinstance(entry, dict):
            result.append(ArtifactDescriptor(
                path=path,
                category=str(entry.get("category", "")),
                description=str(entry.get("description", "")),
                provides_symbols=tuple(str(s) for s in entry.get("provides_symbols", [])),
                typical_change_triggers=tuple(str(s) for s in entry.get("typical_change_triggers", [])),
            ))
        else:
            result.append(ArtifactDescriptor(
                path=path,
                category="",
                description="",
                provides_symbols=(),
                typical_change_triggers=(),
            ))
    result.sort(key=lambda d: d.path)
    return tuple(result)


def derive_requirement_terms(change: RequirementChange) -> frozenset[str]:
    raw = f"{change.before} {change.after} {' '.join(change.acceptance_criteria)}"
    tokens = _normalize(raw)
    filtered = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]
    singulars = [_singular(t) for t in filtered]
    return frozenset(singulars)


def select_dependency_scope(
    change: RequirementChange,
    artifact_universe: ArtifactUniverse,
    descriptors: tuple[ArtifactDescriptor, ...],
    graph: DependencyGraph,
) -> tuple[str, ...]:
    req_terms = derive_requirement_terms(change)

    adj: dict[str, set[str]] = {}
    for src, dst in graph.edges:
        adj.setdefault(src, set()).add(dst)

    seeds: list[str] = []
    for desc in descriptors:
        desc_terms: set[str] = set()
        desc_terms.update(_normalize(desc.path))
        desc_terms.update(_normalize(desc.category))
        desc_terms.update(_normalize(desc.description))
        for sym in desc.provides_symbols:
            desc_terms.update(_normalize(sym))
        for trig in desc.typical_change_triggers:
            desc_terms.update(_normalize(trig))

        # Rule a: normalized provided symbol appears in requirement terms
        for sym in desc.provides_symbols:
            sym_terms = frozenset(_singular(t) for t in _normalize(sym))
            if sym_terms and sym_terms <= req_terms:
                seeds.append(desc.path)
                break
        if desc.path in seeds:
            continue

        # Rule b: at least two non-stop requirement terms in descriptor terms
        intersection = req_terms & {_singular(t) for t in desc_terms if t not in STOP_WORDS and len(t) > 1}
        if len(intersection) >= 2:
            seeds.append(desc.path)
            continue

        # Rule c: complete normalized trigger phrase has at least two matching content words
        for trig in desc.typical_change_triggers:
            trig_terms = _normalize(trig)
            trig_non_stop = [t for t in trig_terms if t not in STOP_WORDS and len(t) > 1]
            match_count = sum(1 for t in trig_non_stop if _singular(t) in req_terms)
            if match_count >= 2:
                seeds.append(desc.path)
                break

    if not seeds:
        return ()

    # Collect seeds and their direct dependencies via outgoing edges
    universe_set = {a.path for a in artifact_universe.artifacts}
    selected: set[str] = set()
    for seed in seeds:
        selected.add(seed)
        for dep in adj.get(seed, set()):
            selected.add(dep)

    # Intersect with ArtifactUniverse
    result = sorted(selected & universe_set)
    return tuple(result)
