"""Deterministic tokenization for cheap non-LLM baselines.

Tokenization is a pure, deterministic function of text: identifiers are split
on snake_case / camelCase boundaries and non-alphanumerics, lowercased, and
filtered against a small frozen stopword set. No NLP libraries are used.
"""

from __future__ import annotations

import re

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_SEPARATOR = re.compile(r"[^a-zA-Z0-9]+")
_ALNUM = re.compile(r"^[a-z0-9]+$")

# Frozen minimal stopword set (deterministic, tiny). Kept deliberately small so
# rare code identifiers are not accidentally dropped.
STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "have",
        "in",
        "into",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "were",
        "with",
        "will",
        "not",
        "no",
        "yes",
        "do",
        "does",
        "did",
        "fix",
        "fixes",
        "fixed",
        "feat",
        "feature",
        "add",
        "added",
        "adding",
        "update",
        "updated",
        "updating",
        "change",
        "changes",
        "changed",
        "changing",
        "remove",
        "removed",
        "removing",
        "improve",
        "improved",
        "fixing",
        "new",
        "refactor",
        "refactored",
        "revert",
        "reverted",
        "merge",
        "merged",
        "minor",
        "major",
    }
)


def tokenize(text: str) -> tuple[str, ...]:
    """Deterministically tokenize text into a tuple of lowercased tokens.

    Splits on snake/camel boundaries and non-alphanumeric separators, keeps
    alphanumeric tokens, drops frozen stopwords, and always returns a
    deterministic order (document order, de-duplicated not required here; use
    :func:`token_set` for set semantics).
    """
    tokens: list[str] = []
    for piece in _SEPARATOR.split(_CAMEL_BOUNDARY.sub(" ", text)):
        for token in piece.lower().replace("_", " ").split():
            if _ALNUM.match(token) and token not in STOPWORDS:
                tokens.append(token)
    return tuple(tokens)


def token_set(text: str) -> frozenset[str]:
    return frozenset(tokenize(text))


def tokenize_path(path: str) -> tuple[str, ...]:
    """Tokenize a repository-relative path into path-segment tokens.

    Example: ``cms/models/pagemodel.py`` -> ``("cms", "models", "pagemodel")``.
    The ``.py`` suffix is stripped because it carries no signal among
    candidates. Deterministic.
    """
    cleaned = path
    if cleaned.endswith(".py"):
        cleaned = cleaned[: -len(".py")]
    return tokenize(cleaned.replace("/", " "))
