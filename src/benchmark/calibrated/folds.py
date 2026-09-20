"""CALIBRATED_SET_SELECTION_V1 — deterministic task-grouped folds (T3, ZERO API).

Frozen (docs/CALIBRATED_SET_SELECTION_V1_IMPACT_DECLARATION_2026-09-20.md §7):

- Deterministic 5-fold OUTER task-grouped CV; all candidate files of the same
  task always stay together.
- Folds approximately stratified by repository: within each repository the
  sorted case IDs are shuffled with a fixed seed and assigned
  `fold = index % k`, so every fold contains ~1/k of each repository's tasks.

Assignment depends ONLY on case IDs (repository + case_id), never on scores or
labels, so the SAME fold assignment is used for realization A and realization B.
All functions are pure and deterministic.
"""
from __future__ import annotations

import random
from collections.abc import Callable, Iterable


def grouped_stratified_folds(
    case_ids: Iterable[str],
    repo_of: Callable[[str], str],
    k: int = 5,
    seed: int = 20260920,
) -> dict[str, int]:
    """Map case_id -> fold index (0..k-1), task-grouped and repo-stratified.

    - task grouping: assignment is per task (never per file);
    - repository stratification: each repository's tasks are deterministically
      shuffled and split evenly across the k folds;
    - determinism: fixed seed + sorted inputs => identical assignment on every
      rerun, independent of realization A/B.
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    out: dict[str, int] = {}
    repos = sorted({repo_of(c) for c in case_ids})
    for repo in repos:
        ids = sorted(c for c in case_ids if repo_of(c) == repo)
        rng = random.Random(seed)
        rng.shuffle(ids)
        for i, cid in enumerate(ids):
            out[cid] = i % k
    return out


def split_by_fold(fold_map: dict[str, int], fold: int) -> tuple[set[str], set[str]]:
    """Return (train_case_ids, held_out_case_ids) for a given outer fold."""
    train: set[str] = set()
    held: set[str] = set()
    for cid, f in fold_map.items():
        (held if f == fold else train).add(cid)
    return train, held
