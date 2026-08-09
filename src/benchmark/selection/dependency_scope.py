from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
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


LOW_INFORMATION_SOFTWARE_TERMS: frozenset[str] = frozenset({
    "add", "addition", "change", "changes", "code", "current", "existing",
    "file", "files", "implementation", "modify", "modified", "modification",
    "new", "required", "requirement", "support", "py",
})


@dataclass(frozen=True)
class RequirementSignals:
    positive_terms: frozenset[str]
    negative_descriptor_paths: frozenset[str]


MIN_REVERSE_CONSUMER_OVERLAP = 3


NEGATIVE_PHRASE_PATTERNS: tuple[str, ...] = (
    r"no changes to ([\w./]+)",
    r"([\w./]+) must not be modified",
    r"([\w./]+) is not required",
    r"([\w./]+) changes are not required",
    r"without changing ([\w./]+)",
)


def _extract_negative_paths(text: str) -> frozenset[str]:
    paths: set[str] = set()
    lower_text = text.lower()
    for pattern in NEGATIVE_PHRASE_PATTERNS:
        for match in re.finditer(pattern, lower_text):
            path = match.group(1).strip().rstrip(".,;:!?")
            if path:
                paths.add(path)
    return frozenset(paths)


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    return [p.strip() for p in parts if p.strip()]


def derive_requirement_signals(
    change: RequirementChange,
    descriptors: tuple[ArtifactDescriptor, ...],
) -> RequirementSignals:
    positive_terms: set[str] = set()
    negative_paths: set[str] = set()

    for source in (change.before, change.after, *change.acceptance_criteria):
        negative_paths |= _extract_negative_paths(source)
        for sentence in _split_sentences(source):
            if _extract_negative_paths(sentence):
                continue
            pos_tokens = _normalize(sentence)
            pos_filtered = [
                t for t in pos_tokens
                if t not in STOP_WORDS and t not in LOW_INFORMATION_SOFTWARE_TERMS and len(t) > 1
            ]
            positive_terms.update(_singular(t) for t in pos_filtered)

    matched_negative_descriptor_paths: set[str] = set()
    for desc in descriptors:
        desc_lower = desc.path.lower()
        stem = Path(desc_lower).stem
        cat_lower = desc.category.lower()
        for neg_path in negative_paths:
            if neg_path in (desc_lower, stem, cat_lower):
                matched_negative_descriptor_paths.add(desc.path)
                break
        for sym in desc.provides_symbols:
            if sym.lower() in negative_paths:
                matched_negative_descriptor_paths.add(desc.path)
                break

    return RequirementSignals(
        positive_terms=frozenset(positive_terms),
        negative_descriptor_paths=frozenset(matched_negative_descriptor_paths),
    )


def _normalize(text: str) -> list[str]:
    parts: list[str] = []
    for token in text.split():
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

    def _make_descriptor(
        path: str,
        entry: dict[str, Any] | str | None,
    ) -> ArtifactDescriptor:
        meta = entry if isinstance(entry, dict) else None
        return ArtifactDescriptor(
            path=path,
            category=str(meta.get("category", "")) if meta else "",
            description=str(meta.get("description", "")) if meta else "",
            provides_symbols=tuple(str(s) for s in meta.get("provides_symbols", [])) if meta else (),
            typical_change_triggers=tuple(str(s) for s in meta.get("typical_change_triggers", [])) if meta else (),
        )

    for entry in artifact_catalog:
        if isinstance(entry, dict):
            path: str = entry.get("id", "")
        else:
            path = str(entry)
        if not path:
            continue
        if path.endswith("/"):
            # Directory policy entry: valid descendant semantics against the
            # file-granular editable universe (repository/profile derived).
            for editable_path in sorted(editable_set):
                if editable_path.startswith(path):
                    result.append(_make_descriptor(editable_path, entry))
            continue
        if path not in editable_set:
            continue
        result.append(_make_descriptor(path, entry))

    seen: set[str] = set()
    unique: list[ArtifactDescriptor] = []
    for descriptor in result:
        if descriptor.path not in seen:
            seen.add(descriptor.path)
            unique.append(descriptor)
    unique.sort(key=lambda d: d.path)
    return tuple(unique)


def derive_requirement_terms(change: RequirementChange) -> frozenset[str]:
    raw = f"{change.before} {change.after} {' '.join(change.acceptance_criteria)}"
    tokens = _normalize(raw)
    filtered = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]
    singulars = [_singular(t) for t in filtered]
    return frozenset(singulars)


def _desc_meaningful_terms(desc: ArtifactDescriptor) -> set[str]:
    terms: set[str] = set()
    for trig in desc.typical_change_triggers:
        trig_tokens = _normalize(trig)
        terms.update(
            _singular(t) for t in trig_tokens
            if t not in STOP_WORDS and t not in LOW_INFORMATION_SOFTWARE_TERMS and len(t) > 1
        )
    terms.update(
        _singular(t) for t in _normalize(desc.description)
        if t not in STOP_WORDS and t not in LOW_INFORMATION_SOFTWARE_TERMS and len(t) > 1
    )
    return terms


def _trigger_meaningful_terms(desc: ArtifactDescriptor) -> set[str]:
    terms: set[str] = set()
    for trig in desc.typical_change_triggers:
        trig_tokens = _normalize(trig)
        terms.update(
            _singular(t) for t in trig_tokens
            if t not in STOP_WORDS and t not in LOW_INFORMATION_SOFTWARE_TERMS and len(t) > 1
        )
    return terms


def _seed_descriptors(
    descriptors: tuple[ArtifactDescriptor, ...],
    pos: frozenset[str],
) -> list[str]:
    seeds: list[str] = []
    for desc in descriptors:
        desc_path_stem = Path(desc.path.lower()).stem
        desc_cat_lower = desc.category.lower()
        desc_meaningful = _desc_meaningful_terms(desc)

        # Rule 1: complete provided-symbol phrase occurs in positive public text
        for sym in desc.provides_symbols:
            sym_terms = frozenset(_singular(t) for t in _normalize(sym))
            if sym_terms and sym_terms <= pos:
                seeds.append(desc.path)
                break
        if desc.path in seeds:
            continue

        # Rule 2: path stem or category occurs in positive terms
        # and at least one additional meaningful descriptor term matches
        stem_and_cat_tokens = set(_normalize(desc_path_stem)) | set(_normalize(desc_cat_lower))
        stem_or_cat_in_pos = bool(stem_and_cat_tokens & pos)
        if stem_or_cat_in_pos:
            additional_match = pos & desc_meaningful
            if additional_match:
                seeds.append(desc.path)
                continue

        # Rule 3: trigger phrase match
        for trig in desc.typical_change_triggers:
            trig_tokens = _normalize(trig)
            meaningful = [
                t for t in trig_tokens
                if t not in STOP_WORDS and t not in LOW_INFORMATION_SOFTWARE_TERMS and len(t) > 1
            ]
            if len(meaningful) < 2:
                continue
            matched = [t for t in meaningful if _singular(t) in pos]
            if len(matched) >= 2 and len(matched) / len(meaningful) >= 2 / 3:
                seeds.append(desc.path)
                break
    return seeds


def _build_graph_adjacency(graph: DependencyGraph) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    forward: dict[str, set[str]] = {}
    reverse: dict[str, set[str]] = {}
    for src, dst in graph.edges:
        forward.setdefault(src, set()).add(dst)
        reverse.setdefault(dst, set()).add(src)
    return forward, reverse


def select_dependency_scope(
    change: RequirementChange,
    artifact_universe: ArtifactUniverse,
    descriptors: tuple[ArtifactDescriptor, ...],
    graph: DependencyGraph,
) -> tuple[str, ...]:
    signals = derive_requirement_signals(change, descriptors)
    pos = signals.positive_terms
    neg_paths = signals.negative_descriptor_paths

    forward, reverse = _build_graph_adjacency(graph)

    seeds = _seed_descriptors(descriptors, pos)

    if not seeds:
        return ()

    universe_set = {a.path for a in artifact_universe.artifacts}

    descriptors_by_path = {d.path: d for d in descriptors}

    selected: set[str] = set()
    for seed in seeds:
        selected.add(seed)
        for consumer in reverse.get(seed, set()):
            consumer_desc = descriptors_by_path.get(consumer)
            if consumer_desc:
                consumer_meaningful = _trigger_meaningful_terms(consumer_desc)
                overlap = pos & consumer_meaningful
                if len(overlap) >= MIN_REVERSE_CONSUMER_OVERLAP:
                    selected.add(consumer)

    result_set = (selected & universe_set) - neg_paths

    if not result_set:
        return ()

    return tuple(sorted(result_set))
