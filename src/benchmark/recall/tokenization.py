"""Deterministic path/module token helpers for the recall taxonomy (T3)."""
from __future__ import annotations

from benchmark.cheap_baselines.tokenize import tokenize


def path_tokens(path: str) -> tuple[str, ...]:
    """Path-segment tokens of a repo-relative path (e.g. cms/models/page.py)."""
    cleaned = path
    if cleaned.endswith(".py"):
        cleaned = cleaned[: -len(".py")]
    return tokenize(cleaned.replace("/", " "))


def token_set_text(text: str) -> frozenset[str]:
    from benchmark.cheap_baselines.tokenize import token_set

    return token_set(text or "")
