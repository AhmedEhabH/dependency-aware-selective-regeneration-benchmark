# ruff: noqa: N803, N806
"""Quantitative-structural ranking bridge (T3, ZERO API, DEVELOPMENT).

Section 2 of the ranking-bridge mission: can quantitative structural support
order the high-coverage reverse-1hop pool better than the current binary graph
flag, without learned models or LLMs?

EXACTLY THREE transparent formulas are frozen BEFORE outcome inspection. All
features are parent-visible at inference time (normalized BM25 + directed
seed-support counts over the frozen graph). The hidden proxy is never a
ranking input.

Feature provenance:
- bm25          : existing normalized BM25 (frozen tokenizer/index).
- rev_support   : count of distinct seeds s with an edge (candidate -> s),
                  i.e. the candidate consumes/depends on that Sparse-selected
                  seed (downstream-consumer support). Seeds = intent-seed
                  paths UNION Sparse write set, identical to the seed set used
                  by the frozen consumer/provider binary flags.
- fwd_support   : count of distinct seeds s with an edge (s -> candidate),
                  i.e. the candidate is a provider/upstream dependency of that
                  seed.
- typed-edge support counts are NOT used: the frozen dependency graph exposes
  only untyped [source, dest] edges (schema version in dependency_graph.json),
  so import/call/inheritance/reference types are not validly available.

Formulas (score, tie-break desc score then asc path):
  R1 BM25+RevSupport   : bm25 + rev_norm
  R2 BM25+BidirSupport : bm25 + rev_norm + fwd_norm
  R3 BM25+BidirNorm    : bm25 + bidir_norm   (single combined bidirectional term)

Normalization is deterministic WITHIN the task (parent-visible):
  rev_norm(p)   = rev_support(p)   / max(1, max_rev_support_over_candidates)
  fwd_norm(p)   = fwd_support(p)   / max(1, max_fwd_support_over_candidates)
  bidir_norm(p) = (rev_support(p)+fwd_support(p)) / max(1, max_bidir_over_candidates)
"""
from __future__ import annotations

import time
from collections.abc import Callable, Sequence

from .data import RecallTask
from .rankers import recovery

RankFn = Callable[[RecallTask], list[str]]


def _rank(task: RecallTask, key_fn: object) -> list[str]:
    cands = list(task.candidates)
    key = key_fn if callable(key_fn) else (lambda _c: 0.0)
    cands.sort(key=lambda c: (-float(key(c)), c["path"]))
    return [c["path"] for c in cands]


def _task_max(task: RecallTask, field: str) -> int:
    return max((int(c[field]) for c in task.candidates), default=0)


def _rev_norm(task: RecallTask) -> dict[str, float]:
    mx = max(1, _task_max(task, "rev_support"))
    return {c["path"]: int(c["rev_support"]) / mx for c in task.candidates}


def _fwd_norm(task: RecallTask) -> dict[str, float]:
    mx = max(1, _task_max(task, "fwd_support"))
    return {c["path"]: int(c["fwd_support"]) / mx for c in task.candidates}


def _bidir_norm(task: RecallTask) -> dict[str, float]:
    mx = max(1, max((int(c["rev_support"]) + int(c["fwd_support"]) for c in task.candidates), default=0))
    return {c["path"]: (int(c["rev_support"]) + int(c["fwd_support"])) / mx for c in task.candidates}


def rank_bm25_rev_support(task: RecallTask) -> list[str]:
    """R1 BM25+RevSupport: bm25 + normalized reverse-seed-support count."""
    rev = _rev_norm(task)
    return _rank(task, lambda c: c["bm25"] + rev[c["path"]])


def rank_bm25_bidir_support(task: RecallTask) -> list[str]:
    """R2 BM25+BidirSupport: bm25 + rev_norm + fwd_norm (both directions)."""
    rev = _rev_norm(task)
    fwd = _fwd_norm(task)
    return _rank(task, lambda c: c["bm25"] + rev[c["path"]] + fwd[c["path"]])


def rank_bm25_bidir_norm(task: RecallTask) -> list[str]:
    """R3 BM25+BidirNorm: bm25 + single combined bidirectional normalized term."""
    bid = _bidir_norm(task)
    return _rank(task, lambda c: c["bm25"] + bid[c["path"]])


QUANT_RANKERS = {
    "R1_BM25+RevSupport": rank_bm25_rev_support,
    "R2_BM25+BidirSupport": rank_bm25_bidir_support,
    "R3_BM25+BidirNorm": rank_bm25_bidir_norm,
}


def _fn_set(task: RecallTask) -> set[str]:
    return {c["path"] for c in task.candidates if c["is_missed_positive"]}


def macro_orr(tasks: list[RecallTask], rfn: RankFn, B: int) -> float:
    rows = [recovery(t, rfn(t), B) for t in tasks]
    return sum(r["orr"] for r in rows) / len(rows) if rows else 0.0


def candidate_precision(tasks: list[RecallTask], rfn: RankFn, B: int) -> float:
    """Fraction of FN among the top-B candidates (precision of the ranking)."""
    tot_top = 0
    tot_fn = 0
    for t in tasks:
        B_eff = min(B, t.omitted_size)
        top = set(rfn(t)[:B_eff])
        if not top:
            continue
        tot_top += len(top)
        tot_fn += len(top & _fn_set(t))
    return (tot_fn / tot_top) if tot_top else 0.0


def unique_fn_beyond_route_b(tasks: list[RecallTask], rfn: RankFn, B: int) -> int:
    from .rankers import rank_composite

    uniq = 0
    for t in tasks:
        B_eff = min(B, t.omitted_size)
        rt = set(rank_composite(t)[:B_eff]) & _fn_set(t)
        qt = set(rfn(t)[:B_eff]) & _fn_set(t)
        uniq += len(qt - rt)
    return uniq


def naive_union_f1(tasks: list[RecallTask], rfn: RankFn, B: int) -> dict:
    tp = fp = fn = 0
    for t in tasks:
        B_eff = min(B, t.omitted_size)
        added = set(rfn(t)[:B_eff])
        final = set(t.write_set) | added
        pos = set(t.proxy)
        tp += len(final & pos)
        fp += len(final - pos)
        fn += len(pos - final)
    return _f1(tp, fp, fn)


def oracle_reviewer_f1(tasks: list[RecallTask], rfn: RankFn, B: int) -> dict:
    """Perfect reviewer: only true FNs among top-B are accepted (zero FP add)."""
    tp = fp = fn = 0
    for t in tasks:
        B_eff = min(B, t.omitted_size)
        fn_set = set(t.proxy) - set(t.write_set)
        accepted = {p for p in rfn(t)[:B_eff] if p in fn_set}
        final = set(t.write_set) | accepted
        pos = set(t.proxy)
        tp += len(final & pos)
        fp += len(final - pos)
        fn += len(pos - final)
    return _f1(tp, fp, fn)


def _f1(tp: int, fp: int, fn: int) -> dict[str, int | float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4),
            "recall": round(r, 4), "f1": round(f1, 4)}


def _corr(a: Sequence[float], b: Sequence[float]) -> float:
    n = len(a)
    if n < 2:
        return 0.0
    ma = sum(a) / n
    mb = sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True))
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    return (cov / (va * vb) ** 0.5) if (va * vb) else 0.0


def artifact_corr(tasks: list[RecallTask], rfn: RankFn, B: int) -> tuple[float, float]:
    """corr between (ranker ORR - Route-B ORR) and universe/omitted size."""
    from .rankers import rank_composite

    deltas, uni, omi = [], [], []
    for t in tasks:
        M = t.n_missed
        N = t.omitted_size
        if M == 0 or N == 0:
            continue
        rb = recovery(t, rank_composite(t), B)["orr"]
        q = recovery(t, rfn(t), B)["orr"]
        deltas.append(q - rb)
        uni.append(t.universe_size)
        omi.append(t.omitted_size)
    return _corr(deltas, uni), _corr(deltas, omi)


def fold_direction(tasks: list[RecallTask], rfn: RankFn, B: int, folds: int = 5, seed: int = 20260918) -> list[float]:
    """Seeded task-grouped fold fractions where ranker ORR >= Route-B ORR.

    Returns one fraction per fold in [0, 1] (ties count as 0.5).
"""
    import random

    from .rankers import rank_composite

    rng = random.Random(seed)
    order = list(tasks)
    rng.shuffle(order)
    out: list[float] = []
    for k in range(folds):
        fold = order[k::folds]
        pos = 0.0
        for t in fold:
            M = t.n_missed
            if M == 0:
                continue
            rb = recovery(t, rank_composite(t), B)["orr"]
            q = recovery(t, rfn(t), B)["orr"]
            if q > rb:
                pos += 1
            elif q == rb:
                pos += 0.5
        out.append(pos / len(fold) if fold else 0.0)
    return out


def deterministic_rank_time_ms(tasks: list[RecallTask], rfn: RankFn) -> float:
    """Wall-clock cost of ranking all tasks (deterministic, no IO)."""
    t0 = time.perf_counter()
    for t in tasks:
        rfn(t)
    return round((time.perf_counter() - t0) * 1000.0, 3)

