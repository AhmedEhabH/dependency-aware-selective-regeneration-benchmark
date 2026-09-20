"""PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 — Channel A structural co-change.

Deterministic historical co-change statistics (frozen, mission §9-§10):

  C(f)    = number of parent-visible production-changing commits touching f.
  C(s)    = number touching s.
  C(f, s) = number touching both.
  Jaccard(f, s) = C(f,s) / (C(f) + C(s) - C(f,s))
  If C(f,s) < 2 -> pair score = 0.   (frozen support threshold = 2, NO sweep)

Inference-time seeds (frozen, mission §10) — inference-available ONLY:
  A. ALL Sparse-selected files;
  B. the Qwen dense rank-1 file.
  Do NOT seed from target labels.

For candidate f:
  cochange_sparse(f) = max Jaccard(f, s) over s in Sparse; 0 if Sparse empty.
  cochange_top1(f)   = Jaccard(f, dense-rank1-file).
  cochange_memory_score(f) = max(cochange_sparse(f), cochange_top1(f)).

All functions are pure and deterministic.
"""
from __future__ import annotations

from .history import TaskHistory

SUPPORT_FREEZE = 2


def jaccard(c_f: int, c_s: int, c_fs: int) -> float:
    """Jaccard(f, s); 0 if the pair support is below the frozen threshold.

    Frozen support threshold = 2 (mission §9: if C(f,s) < 2 pair score = 0).
    """
    if c_fs < SUPPORT_FREEZE:
        return 0.0
    denom = c_f + c_s - c_fs
    if denom <= 0:
        return 0.0
    return c_fs / denom


def cochange_sparse_map(task_history: TaskHistory, sparse: set[str]) -> dict[str, float]:
    """{f: max Jaccard(f, s) over Sparse seeds}; all-zero if Sparse empty.

    For f == s (a Sparse file with history) the self-pair Jaccard is 1.0;
    the frozen formula max over s in Sparse includes the self pair.
    """
    if not sparse:
        return {}
    c_f = task_history.history_change_count
    best: dict[str, float] = {}
    for s in sparse:
        c_s = c_f.get(s, 0)
        cto = task_history.cochange_counts_to(s)
        for f, c_fs in cto.items():
            val = jaccard(c_f.get(f, 0), c_s, c_fs)
            if val > best.get(f, 0.0):
                best[f] = val
        if c_s > 0:
            best[s] = 1.0
    return best


def cochange_top1_map(task_history: TaskHistory, rank1_file: str | None) -> dict[str, float]:
    """{f: Jaccard(f, dense-rank1-file)}; {} if there is no rank-1 file."""
    if rank1_file is None:
        return {}
    c_f = task_history.history_change_count
    c_s = c_f.get(rank1_file, 0)
    out: dict[str, float] = {}
    for f, c_fs in task_history.cochange_counts_to(rank1_file).items():
        out[f] = jaccard(c_f.get(f, 0), c_s, c_fs)
    if c_s > 0:
        out[rank1_file] = 1.0
    return out


def cochange_memory_score_map(cochange_sparse: dict[str, float],
                              cochange_top1: dict[str, float]) -> dict[str, float]:
    """{f: max(cochange_sparse(f), cochange_top1(f))} (frozen, mission §10)."""
    keys = set(cochange_sparse) | set(cochange_top1)
    return {f: max(cochange_sparse.get(f, 0.0), cochange_top1.get(f, 0.0))
            for f in keys}


def structural_candidates(scores: dict[str, float], support: dict[str, int],
                          non_sparse: list[str], k: int = 10) -> list[str]:
    """Top-k NON-SPARSE files by cochange_memory_score > 0 (frozen §12).

    Tie-break (frozen): (1) higher score; (2) higher historical support
    (C(f)); (3) normalized path ascending.
    """
    scored: list[tuple[float, int, str]] = []
    for f in non_sparse:
        score = scores.get(f, 0.0)
        if score <= 0.0:
            continue
        scored.append((score, support.get(f, 0), f))
    scored.sort(key=lambda t: (-t[0], -t[1], t[2]))
    return [f for _, _, f in scored[:k]]
