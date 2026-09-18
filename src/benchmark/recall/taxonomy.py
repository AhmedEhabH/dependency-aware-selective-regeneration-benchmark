"""Deterministic FN taxonomy (DEVELOPMENT only; parent-visible features only).

Classifies every Sparse false-negative file using ONLY evidence available at
inference time (intent text, candidate universe metadata, dependency graph,
djangoCMS ancestors-of-parent co-change). The hidden proxy is used ONLY to
identify the file as an FN after the fact (``is_missed_positive``); it never
enters a feature or the classifier.

Categories (mission-defined, multi-label allowed; one primary_reason):
  A DIRECT_LEXICAL            : filename/path/symbol overlaps the change intent
  B DIRECT_DEPENDENCY         : 1-hop undirected graph edge to/from a seed
  C INDIRECT_DEPENDENCY_2HOP  : reachable in 2 undirected hops, not 1
  D DOWNSTREAM_CONSUMER       : imports a seed (consumer) AND lexically distant
  E UPSTREAM_PROVIDER         : imported by a seed (provider) AND lexically distant
  F CROSS_LAYER               : shares a non-generic concern term with a seed in
                                a different directory, no 1/2-hop edge
  G HISTORY_COCHANGE          : co-changed with the write set in ancestors of
                                parent (djangoCMS only; Saleor UNAVAILABLE)
  H STRUCTURAL_NEIGHBOR       : same parent dir / module as a seed, no stronger
                                evidence
  I NO_OBSERVABLE_SIGNAL      : none of the cheap evidence exposes the file

primary_reason priority (deterministic, documented in the report):
  direct-1-hop directional-distant (D/E) > DIRECT_DEPENDENCY (B) >
  INDIRECT_DEPENDENCY_2HOP (C) > HISTORY_COCHANGE (G) > DIRECT_LEXICAL (A) >
  CROSS_LAYER (F) > STRUCTURAL_NEIGHBOR (H) > NO_OBSERVABLE_SIGNAL (I).
"""
from __future__ import annotations

from pathlib import Path

from .data import RecallTask
from .tokenization import path_tokens, token_set_text

# Generic / structural-only tokens that never qualify as a "concern" term for
# CROSS_LAYER (deterministic, frozen).
_LAYER_OR_GENERIC = frozenset(
    {
        "admin", "models", "utils", "util", "api", "views", "view", "forms",
        "form", "signals", "signal", "templatetags", "templates", "template",
        "management", "tests", "test", "migrations", "migration", "static",
        "context_processors", "plugin_pool", "plugins", "plugin", "toolbar",
        "cms_toolbar", "menu", "permissions", "permission", "sitemap",
        "middleware", "checks", "apps", "conf", "constants", "constant",
        "compat", "exceptions", "exception", "fields", "field", "base",
        "decorators", "extensions", "publisher", "cache", "urls", "url",
        "helpers", "helper", "setup", "wsgi", "asgi", "settings", "setting",
        "core", "lib", "common", "default", "defaults", "init", "py",
        "saleor", "django", "cms", "shop", "order", "checkout", "payment",
        "product", "graphql", "attribute", "channel",
    }
)

PRIMARY_ORDER = (
    "DOWNSTREAM_CONSUMER",
    "UPSTREAM_PROVIDER",
    "DIRECT_DEPENDENCY",
    "INDIRECT_DEPENDENCY_2HOP",
    "HISTORY_COCHANGE",
    "DIRECT_LEXICAL",
    "CROSS_LAYER",
    "STRUCTURAL_NEIGHBOR",
    "NO_OBSERVABLE_SIGNAL",
)

ALL_CATEGORIES = PRIMARY_ORDER


def _lexical(c: dict) -> bool:
    return bool(c["intent_overlap"] == 1 or c["bm25"] > 0.0)


def _cross_layer(c: dict, seeds: dict[str, dict]) -> bool:
    """Shares a non-generic concern term with a seed in a different directory."""
    c_tokens = set(path_tokens(c["path"])) | set(token_set_text(c.get("module", "")))
    c_dir = c["parent_dir"]
    if not c_tokens:
        return False
    for s, s_rec in seeds.items():
        s_tokens = set(path_tokens(s)) | set(token_set_text(s_rec.get("module", "")))
        s_dir = str(Path(s).parent)
        if s_dir == c_dir:
            continue
        shared = (c_tokens & s_tokens) - _LAYER_OR_GENERIC
        if shared:
            return True
    return False


def _structural_neighbor(c: dict, seeds: dict[str, dict]) -> bool:
    """Same parent directory or same module as a seed (sibling/package family)."""
    for s, s_rec in seeds.items():
        if c["parent_dir"] == str(Path(s).parent):
            return True
        if c.get("module") and c["module"] == str(s_rec.get("module", "")):
            return True
    return False


def classify_candidate(c: dict, seeds: dict[str, dict]) -> dict:
    """Deterministic taxonomy labels for one candidate (FN or not).

    Returns {"labels": [...], "primary": str}. ``seeds`` maps seed path ->
    universe record (parent-visible). ``c`` must carry the observable features
    produced by :mod:`benchmark.recall.data`.
    """
    lexical = _lexical(c)
    dist = int(c["dist"])
    labels: list[str] = []

    if lexical:
        labels.append("DIRECT_LEXICAL")
    if dist == 1:
        labels.append("DIRECT_DEPENDENCY")
        if c["consumer"] and not lexical:
            labels.append("DOWNSTREAM_CONSUMER")
        if c["provider"] and not lexical:
            labels.append("UPSTREAM_PROVIDER")
    elif dist == 2:
        labels.append("INDIRECT_DEPENDENCY_2HOP")
    if c["co_change"] > 0 and c["history_available"]:
        labels.append("HISTORY_COCHANGE")
    if _cross_layer(c, seeds):
        labels.append("CROSS_LAYER")
    if _structural_neighbor(c, seeds):
        labels.append("STRUCTURAL_NEIGHBOR")

    if not labels:
        labels = ["NO_OBSERVABLE_SIGNAL"]

    # deterministic primary by priority order
    primary = "NO_OBSERVABLE_SIGNAL"
    for cat in PRIMARY_ORDER:
        if cat in labels:
            primary = cat
            break
    labels.sort()
    return {"labels": labels, "primary": primary}


def seed_records(task: RecallTask) -> dict[str, dict]:
    """Seed path -> universe record map (parent-visible; path, module)."""
    return {
        p: task.universe_records.get(p, {"path": p, "module": ""})
        for p in task.seeds
    }


def classify_task(task: RecallTask) -> list[dict]:
    """Classify every FN file of a task."""
    seeds = seed_records(task)
    rows: list[dict] = []
    for c in task.candidates:
        if not c["is_missed_positive"]:
            continue
        lab = classify_candidate(c, seeds)
        rows.append(
            {
                "case_id": task.case_id,
                "repository": task.repository,
                "role": task.role,
                "path": c["path"],
                "labels": lab["labels"],
                "primary": lab["primary"],
                "bm25": c["bm25"],
                "bm25_rank_pct": c["bm25_rank_pct"],
                "pt_rank_pct": c["pt_rank_pct"],
                "intent_overlap": c["intent_overlap"],
                "graph_neighbor": c["graph_neighbor"],
                "dist": c["dist"],
                "consumer": c["consumer"],
                "provider": c["provider"],
                "co_change": c["co_change"],
                "history_available": c["history_available"],
                "module": c["module"],
                "parent_dir": c["parent_dir"],
            }
        )
    rows.sort(key=lambda r: (r["path"],))
    return rows


def classify_tasks(tasks: list[RecallTask]) -> list[dict]:
    out: list[dict] = []
    for t in tasks:
        out.extend(classify_task(t))
    out.sort(key=lambda r: (r["repository"], r["case_id"], r["path"]))
    return out
