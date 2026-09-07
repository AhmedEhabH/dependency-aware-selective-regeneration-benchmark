"""Real source-derived deterministic Python AST import graph for external-validity preparation.

This module builds:
- a file-granular candidate universe (production Python under ``cms/**/*.py`` and
  ``menus/**/*.py`` of a pinned upstream repository);
- a deterministic dependency graph whose edges are ``source file -> imported local file``
  resolved exclusively from real ``ast`` import statements inside the candidate universe.

CONTRACT (pack file 02):
  - graph source MUST be ``python_ast_source_extractor``, never fallback;
  - no scenario expected_actions / hidden tests / evaluator gold / hand-authored edges;
  - no fallback/empty/synthetic graph;
  - deterministic canonical rebuild/hash (ignoring timestamp-only metadata);
  - module-to-file resolution only inside the candidate universe; external imports ignored.

This module deliberately does NOT import any benchmark LLM / strategy / execution code,
so the preparation pipeline cannot accidentally issue a scientific model call.
"""

from __future__ import annotations

import ast
import hashlib
import json
import random
import re
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

EXTRACTOR_VERSION: str = "1.0.0"
GRAPH_SOURCE_NAME: str = "python_ast_source_extractor"

EXCLUDED_DIR_SEGMENTS: frozenset[str] = frozenset(
    {"tests", "test_utils", "migrations", "__pycache__"}
)
EXCLUDED_FILE_SUFFIXES: tuple[str, ...] = (".pyc", ".pyo")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_excluded(rel_path: Path) -> bool:
    """True when the repository-relative path is excluded from the candidate universe."""
    if rel_path.suffix in EXCLUDED_FILE_SUFFIXES:
        return True
    for part in rel_path.parts:
        if part in EXCLUDED_DIR_SEGMENTS:
            return True
    return False


def _module_name(rel_path: Path) -> str:
    """Convert a repo-relative ``.py`` path to its dotted module name."""
    stem = rel_path.with_suffix("")
    if stem.name == "__init__":
        parts = list(stem.parts[:-1])
    else:
        parts = list(stem.parts)
    return ".".join(parts)


def _loc(text: str) -> int:
    return len(text.splitlines())


def _split_symbols(tree: ast.Module) -> tuple[tuple[str, ...], tuple[str, ...]]:
    classes: list[str] = []
    functions: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
    return tuple(sorted(classes)), tuple(sorted(functions))


def _import_edges_from_file(content: str, package: str, resolve: Any) -> list[str]:
    """Return the set of universe-relative target paths imported by one source file.

    Resolution semantics (AST only):
      - ``import a.b.c`` -> ``resolve_module("a.b.c")``
      - ``import a.b as x`` -> ``resolve_module("a.b")``
      - ``from a.b import c`` -> ``resolve_module("a.b")`` and ``resolve_module("a.b.c")``
        (submodule import) if either maps inside the universe;
      - ``from a.b import c as x`` -> same as ``from a.b import c``;
      - ``from . import x`` / ``from .mod import x`` / ``from ..mod import x`` -> resolved
        relative to the importing file's package.

    External third-party imports resolve to None and are ignored (no local edge).
    """
    targets: set[str] = set()
    try:
        tree = ast.parse(content)
    except (SyntaxError, ValueError, UnicodeDecodeError):
        return []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = resolve(alias.name)
                if target is not None:
                    targets.add(target)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                base = package
                if node.level >= 2:
                    for _ in range(node.level - 1):
                        base = base.rsplit(".", 1)[0] if base else ""
                if node.module:
                    root = f"{base}.{node.module}" if base else node.module
                else:
                    root = base
            else:
                root = node.module or ""
            candidates = {root}
            for alias in node.names:
                if alias.name != "*":
                    candidates.add(f"{root}.{alias.name}" if root else alias.name)
            for candidate in candidates:
                if not candidate:
                    continue
                target = resolve(candidate)
                if target is not None:
                    targets.add(target)
    return sorted(targets)


def build_candidate_universe(repo_root: Path) -> list[dict[str, Any]]:
    """Build the file-granular deterministic candidate universe.

    Records are sorted by repository-relative path so the artifact is canonical.
    Each record: ``path``, ``sha256``, ``loc``, ``module``, ``classes``, ``functions``,
    ``import_count``. ``import_count`` counts AST import statements; symbols are top-level.
    """
    records: list[dict[str, Any]] = []
    for root_dir in ("cms", "menus"):
        base = repo_root / root_dir
        if not base.is_dir():
            continue
        for file in sorted(base.rglob("*.py")):
            rel = file.relative_to(repo_root)
            if _is_excluded(rel):
                continue
            text = file.read_text(encoding="utf-8", errors="replace")
            try:
                tree = ast.parse(text, filename=str(file))
                parse_ok = True
            except (SyntaxError, ValueError):
                tree = None
                parse_ok = False
            if parse_ok and tree is not None:
                imports = [
                    node for node in ast.walk(tree)
                    if isinstance(node, (ast.Import, ast.ImportFrom))
                ]
                import_count = len(imports)
                classes, functions = _split_symbols(tree)
            else:
                import_count = 0
                classes = ()
                functions = ()
            records.append(
                {
                    "path": rel.as_posix(),
                    "sha256": sha256_hex(text.encode("utf-8")),
                    "loc": _loc(text),
                    "module": _module_name(rel),
                    "classes": list(classes),
                    "functions": list(functions),
                    "import_count": import_count,
                }
            )
    return records


def _build_module_map(records: list[dict[str, Any]]) -> dict[str, str]:
    return {str(rec["module"]): str(rec["path"]) for rec in records}


def _make_resolver(module_map: dict[str, str]) -> Any:
    def resolve(module_name: str) -> str | None:
        parts = module_name.split(".")
        for i in range(len(parts), 0, -1):
            prefix = ".".join(parts[:i])
            hit = module_map.get(prefix)
            if hit is not None:
                return hit
        return None
    return resolve


def build_dependency_graph(
    repo_root: Path,
    records: list[dict[str, Any]],
    *,
    pinned_commit: str,
    candidate_universe_hash: str,
    extractor_hash: str,
    generated_utc: str,
) -> dict[str, Any]:
    """Build the deterministic AST dependency graph over the candidate universe.

    Edge direction: ``source file -> imported local file`` (matching the Todo graph.
    ``graph_source`` is always ``python_ast_source_extractor``; there is no fallback path.
    The graph is derived ONLY from real AST import statements inside candidate files;
    scenario expected_actions / hidden gold / hand-authored edges never enter here.

    Metadata: repo_id, version, pinned_commit, candidate_universe_hash, extractor
    version/hash, node/edge counts, parse success/fail counts, isolated node count,
    weakly-connected component count, graph_source, generated_utc. The generated_utc
    field is the ONLY timestamp-like field (stripped for the canonical hash).
    """
    module_map = _build_module_map(records)
    resolve = _make_resolver(module_map)
    node_set: set[str] = {str(rec["path"]) for rec in records}
    edges: set[tuple[str, str]] = set()
    parse_ok = 0
    parse_fail = 0
    
    for rec in records:
        path = str(rec["path"])
        file = repo_root / path
        try:
            text = file.read_text(encoding="utf-8", errors="replace")
            ast.parse(text, filename=str(file))
            parse_ok += 1
        except (SyntaxError, ValueError, UnicodeDecodeError):
            parse_fail += 1
            continue
        
        package = str(rec["module"])
        for target in _import_edges_from_file(text, package, resolve):
            if target in node_set:
                edges.add((path, target))
    
    node_count = len(node_set)
    edge_count = len(edges)
    
    # Build adjacency for connectivity analysis
    adjacency: dict[str, set[str]] = {node: set() for node in node_set}
    for src, dst in edges:
        adjacency[src].add(dst)
        adjacency[dst].add(src)
    
    non_isolated = {node for node, neighs in adjacency.items() if neighs}
    wcc_count = _weakly_connected_component_count(adjacency, node_set)
    
    return {
        "schema": "djangocms-external-validity-dependency-graph/1",
        "repo_id": "djangocms",
        "version": "5.0.0",
        "pinned_commit": pinned_commit,
        "candidate_universe_hash": candidate_universe_hash,
        "extractor_version": EXTRACTOR_VERSION,
        "extractor_hash": extractor_hash,
        "graph_source": GRAPH_SOURCE_NAME,
        "generated_utc": generated_utc,
        "node_count": node_count,
        "edge_count": edge_count,
        "parse_success_count": parse_ok,
        "parse_failure_count": parse_fail,
        "isolated_node_count": node_count - len(non_isolated),
        "non_isolated_node_count": len(non_isolated),
        "weakly_connected_component_count": wcc_count,
        "edges": sorted(edges),
    }


def _weakly_connected_component_count(
    adjacency: dict[str, set[str]], node_set: set[str]
) -> int:
    visited: set[str] = set()
    count = 0
    for node in sorted(node_set):
        if node in visited:
            continue
        count += 1
        queue: deque[str] = deque([node])
        visited.add(node)
        while queue:
            current = queue.popleft()
            for neighbour in adjacency.get(current, set()):
                if neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(neighbour)
    return count


def canonical_graph_hash(graph: dict[str, Any]) -> str:
    """Deterministic SHA-256 of the graph, ignoring timestamp-only metadata fields."""
    stripped = {key: value for key, value in graph.items() if key not in {"generated_utc"}}
    canonical = json.dumps(stripped, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256_hex(canonical.encode("utf-8"))


def canonical_universe_hash(records: list[dict[str, Any]]) -> str:
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256_hex(canonical.encode("utf-8"))


def extractor_source_hash() -> str:
    """Deterministic hash of this extractor module's own source at build time."""
    here = Path(__file__).resolve()
    return sha256_hex(here.read_bytes())


def eligibility(
    *,
    pinned_commit_matches: bool,
    candidate_files: int,
    parse_success_rate: float,
    edge_count: int,
    non_isolated_node_count: int,
    graph_source: str,
) -> dict[str, Any]:
    """Compute the operational graph-readiness eligibility gate (file 02)."""
    criteria = {
        "pinned_source_commit_exact": pinned_commit_matches,
        "candidate_files_ge_25": candidate_files >= 25,
        "ast_parse_success_ge_95pct": parse_success_rate >= 95.0,
        "internal_import_edges_ge_20": edge_count >= 20,
        "non_isolated_nodes_ge_10": non_isolated_node_count >= 10,
        "graph_source_is_python_ast_extractor": graph_source == GRAPH_SOURCE_NAME,
    }
    return {
        "pinned_commit_matches": pinned_commit_matches,
        "candidate_files": candidate_files,
        "parse_success_rate_pct": round(parse_success_rate, 2),
        "edge_count": edge_count,
        "non_isolated_node_count": non_isolated_node_count,
        "graph_source": graph_source,
        "criteria": criteria,
        "eligible": all(criteria.values()),
    }


def sample_edges(
    graph: dict[str, Any], *, count: int = 10, seed: int = 42
) -> list[tuple[str, str]]:
    """Deterministically sample edges for the independent 10-edge traceability gate."""
    edges = list(graph["edges"])
    if not edges:
        return []
    rng = random.Random(seed)
    indices = sorted(rng.sample(range(len(edges)), min(count, len(edges))))
    return [edges[i] for i in indices]


def edge_import_evidence(
    repo_root: Path, src_path: str, dst_path: str, module_map: dict[str, str]
) -> list[str]:
    """Return the exact AST import statement source lines in ``src`` that resolve to ``dst``."""
    resolve = _make_resolver(module_map)
    file = repo_root / src_path
    try:
        text = file.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text, filename=str(file))
    except (SyntaxError, ValueError, UnicodeDecodeError):
        return []
    
    package = _module_name(Path(src_path))
    targets = set(_import_edges_from_file(text, package, resolve))
    if dst_path not in targets:
        return []
    
    lines = text.splitlines()
    evidence: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if resolve(alias.name) == dst_path:
                    evidence.append(lines[node.lineno - 1].strip())
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                root = f"{node.module}.{alias.name}" if node.module else alias.name
                candidates = {root, node.module or ""}
                if any(resolve(c) == dst_path for c in candidates):
                    evidence.append(lines[node.lineno - 1].strip())
    return sorted(set(evidence))


def normalize_source_gold(paths: Iterable[str]) -> tuple[str, ...]:
    """Source-gold normalization: keep existing production ``.py`` paths only.

    Excludes migrations/test files (never selection targets) and any non-.py paths.
    """
    cleaned: list[str] = []
    for raw in paths:
        path = raw.strip().strip('"').strip("'")
        if not path.endswith(".py"):
            continue
        rel = Path(path)
        if any(part in EXCLUDED_DIR_SEGMENTS for part in rel.parts):
            continue
        cleaned.append(rel.as_posix())
    return tuple(sorted(set(cleaned)))


_LEAK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bcms/[A-Za-z0-9_./-]+\.py\b"),
    re.compile(r"\bmenus/[A-Za-z0-9_./-]+\.py\b"),
)
_DOT_PY_LEAK: re.Pattern[str] = re.compile(r"\b[A-Za-z0-9_/-]+\.py\b")
_MODULE_HINT_LEAK: re.Pattern[str] = re.compile(r"\b(?:cms|menus)\.[a-zA-Z0-9_.]+")


def scan_visible_leaks(visible_text: str) -> dict[str, Any]:
    """Scan visible requirement/acceptance text for forbidden repository-path leakage.

    Flags: exact_path_leaks (``cms/...py`` / ``menus/...py``), dot_py_leaks (any
    ``.py`` file-name mention), module_hints (``cms.`` / ``menus.`` dotted module mentions.
    Product/domain terms (PageContent, plugin, toolbar, permission, page, API) are
    allowed and are NOT flagged.
    """
    exact_path_leaks: list[str] = []
    dot_py_leaks: list[str] = []
    module_hints: list[str] = []
    for pattern in _LEAK_PATTERNS:
        exact_path_leaks.extend(pattern.findall(visible_text))
    dot_py_leaks.extend(_DOT_PY_LEAK.findall(visible_text))
    module_hints.extend(_MODULE_HINT_LEAK.findall(visible_text))
    return {
        "exact_path_leak_count": len(exact_path_leaks),
        "dot_py_leak_count": len(dot_py_leaks),
        "module_hint_count": len(module_hints),
        "exact_path_leaks": sorted(set(exact_path_leaks)),
        "dot_py_leaks": sorted(set(dot_py_leaks)),
        "module_hints": sorted(set(module_hints)),
    }