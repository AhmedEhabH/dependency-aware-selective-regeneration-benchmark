"""Deterministic parent-revision code-unit extraction (T3, ZERO API).

Mirrors the official SweRank repository-structure parsing
(https://github.com/gangiswag/SweRank src/get_repo_structure/
get_repo_structure.py): a Python file is decomposed into code units by
`ast.parse` line spans:

  - top-level functions (ast.FunctionDef, not AsyncFunctionDef)
  - classes (ast.ClassDef) — the class body INCLUDING its methods, as the
    official parser stores the class source text with methods inline
  - methods of classes (ast.FunctionDef nodes inside a ClassDef body)

Fallback (deterministic): if `ast.parse` raises OR the file yields no units,
the WHOLE file text becomes a single unit.

The hidden proxy never enters extraction; only parent-revision source text is
used. All functions are pure and deterministic.
"""
from __future__ import annotations

import ast
import hashlib


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def extract_code_units(source: str) -> list[str]:
    """Return the deterministic ordered list of code-unit source texts."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return [source]

    lines = source.splitlines()

    def _span(node) -> str:
        lo = (node.lineno or 1) - 1
        hi = node.end_lineno or (lo + 1)
        return "\n".join(lines[lo:hi])

    units: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            units.append(_span(node))
            for n in node.body:
                # Official SweRank parser indexes sync methods only.
                if isinstance(n, ast.FunctionDef) and not isinstance(n, ast.AsyncFunctionDef):
                    units.append(_span(n))
        # Official SweRank parser indexes top-level SYNC functions only
        # (function_names excludes AsyncFunctionDef).
        elif isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef):
            units.append(_span(node))

    # Deterministic dedupe of identical unit texts while preserving first order.
    seen: set[str] = set()
    out: list[str] = []
    for u in units:
        key = sha256_text(u)
        if key in seen:
            continue
        seen.add(key)
        out.append(u)

    if not out:
        return [source]
    return out


def unit_kind_and_name(source: str) -> str:
    """Best-effort human-readable unit label (for the report, not the model)."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return "module"
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.lineno == 1:
            return f"class {node.name}"
        if isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef) and node.lineno == 1:
            return f"function {node.name}"
    return "module"
