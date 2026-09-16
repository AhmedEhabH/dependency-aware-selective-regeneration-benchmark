"""Omission-Risk Feature Study V1 — task-level labels (PRE-REGISTERED).

Primary label (defined BEFORE any feature performance was observed):

    has_fn(t; K_ref) = 1  iff  |proxy(t) \\ P(t; K_ref)| >= 1
                       (the first-pass BM25@K_ref selection omits >= 1
                        reference-positive file)

where P(t; K_ref) is the deterministic metadata-corpus BM25@K_ref selection.

Reference depth PRE-REGISTERED: K_ref = 10 (the recall/FNR-oriented operating
point with the highest VALIDATION F1 in Protocol A). K in {3, 5} are registered
label-sensitivity depths.

Statistical unit = task (n=30: TRAIN 24 / VALIDATION 6). Deterministic rankers
have no nested repetitions; P1-style nested LLM repetitions are not present on
TRAIN/VALIDATION (deferred with the sparse-plan features).

Secondary outcomes (pre-registered buckets):
    fn_count   = |proxy \\ first_pass|
    fn_rate    = fn_count / |proxy|
    severity   = 'none' | 'partial' | 'complete'   (fn_rate == 0 / <0.5 / >=0.5)

The proxy is loaded ONLY here (evaluation time). It is never a feature input.
"""

from __future__ import annotations

from typing import Any

from benchmark.harness.interfaces import PublicCase

K_REF_PRIMARY: int = 10
K_REF_SENSITIVITY: tuple[int, ...] = (3, 5)
SEVERITY_THRESHOLDS: tuple[tuple[str, float], ...] = (
    ("none", 0.0),
    ("partial", 0.5),
    ("complete", 1.0),
)


def severity_bucket(fn_rate: float) -> str:
    """Pre-registered bucket by fn_rate: none / partial / complete."""
    if fn_rate <= 0.0:
        return "none"
    if fn_rate < 0.5:
        return "partial"
    return "complete"


def task_labels(
    *,
    case: PublicCase,
    first_pass_by_k: dict[int, set[str]],
    proxy_paths: tuple[str, ...],
) -> dict[str, Any]:
    """Compute the pre-registered task-level labels for every reference K.

    ``first_pass_by_k`` maps K -> selected path set (must already be computed
    without the proxy). Returns a dict with has_fn / fn_count / fn_rate /
    severity for each K and the proxy size.
    """
    del case  # labels are a pure function of (first_pass, proxy); case kept in the
    # signature to document the input contract (public case -> labels).
    proxy = set(proxy_paths)
    proxy_size = len(proxy)
    out: dict[str, Any] = {"proxy_size": proxy_size}
    for k, selected in first_pass_by_k.items():
        fn_count = len(proxy - selected)
        fn_rate = (fn_count / proxy_size) if proxy_size else 0.0
        out[f"has_fn_k{k}"] = 1 if fn_count >= 1 else 0
        out[f"fn_count_k{k}"] = fn_count
        out[f"fn_rate_k{k}"] = fn_rate
        out[f"severity_k{k}"] = severity_bucket(fn_rate)
    return out
