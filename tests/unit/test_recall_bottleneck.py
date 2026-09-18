"""First-pass recall bottleneck — unit tests (T3, ZERO API).

Covers:
- FN taxonomy determinism + category invariants
- graph direction correctness (consumer/provider direction)
- no hidden-proxy feature generation (features are parent-visible only)
- duplicate candidate handling
- tasks with zero FN
- tiny universes
- queue budget clipping
- tie-breaking determinism
- repository portability
- Route-B composite reproduction (frozen numbers)
"""
# ruff: noqa: N806
from __future__ import annotations

from collections import Counter

from benchmark.recall.data import load_dev_tasks
from benchmark.recall.queues import (
    QUEUE_RANKERS,
    _top_added,
    naive_union_metrics,
    oracle_reviewer_metrics,
)
from benchmark.recall.rankers import rank_composite, recovery
from benchmark.recall.taxonomy import (
    ALL_CATEGORIES,
    classify_candidate,
    classify_task,
)


def _load():
    return load_dev_tasks()


def test_dev_counts_and_sealed():
    tasks = _load()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]
    assert len(dc) == 174
    assert len(sc) == 149
    assert len(tasks) == 174 + 149
    for t in tasks:
        assert "internal-test" not in t.role.lower()
        assert "reserve" not in t.role.lower()


def test_fn_universe_matches_known():
    tasks = _load()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]
    assert sum(t.n_missed for t in dc) == 382
    assert sum(t.n_missed for t in sc) == 369


def test_route_b_composite_reproduction():
    """Composite macro ORR must equal the frozen route_b_v2 numbers exactly."""
    tasks = _load()
    dc = [t for t in tasks if t.repository == "djangocms"]
    frozen = {1: 0.0464, 3: 0.1177, 5: 0.1633, 10: 0.2512}
    for B, expected in frozen.items():
        rs = [recovery(t, rank_composite(t), B) for t in dc]
        macro = sum(r["orr"] for r in rs) / len(rs)
        assert abs(macro - expected) < 1e-4, (B, macro, expected)


def test_taxonomy_determinism():
    tasks = _load()[:10]
    r1 = [classify_task(t) for t in tasks]
    r2 = [classify_task(t) for t in tasks]
    assert r1 == r2


def test_taxonomy_primary_in_categories():
    tasks = _load()[:20]
    for t in tasks:
        rows = classify_task(t)
        for r in rows:
            assert r["primary"] in ALL_CATEGORIES
            assert r["primary"] in r["labels"] or r["primary"] == "NO_OBSERVABLE_SIGNAL"


def test_taxonomy_labels_nonempty():
    tasks = _load()[:30]
    for t in tasks:
        for r in classify_task(t):
            assert r["labels"]


def test_no_observable_signal_only_when_no_labels():
    """A file with any cheap signal must not be primary NO_OBSERVABLE_SIGNAL."""
    from benchmark.recall.taxonomy import seed_records

    tasks = _load()[:30]
    for t in tasks:
        seeds = seed_records(t)
        for c in t.candidates:
            if not c["is_missed_positive"]:
                continue
            lab = classify_candidate(c, seeds)
            has_signal = bool(
                c["bm25"] > 0 or c["intent_overlap"] == 1 or c["dist"] in (1, 2)
                or (c["co_change"] > 0 and c["history_available"])
                or c["consumer"] or c["provider"]
            )
            if has_signal:
                assert "NO_OBSERVABLE_SIGNAL" not in lab["labels"], (t.case_id, c["path"], lab)


def test_graph_direction_consistency():
    """consumer edge (f->s) and provider edge (s->f) must be consistent with
    graph proximity (dist 0 = the file is itself a seed; dist 1 = adjacent)."""
    tasks = _load()[:40]
    for t in tasks:
        for c in t.candidates:
            if c["consumer"] or c["provider"]:
                assert c["dist"] in (0, 1), (t.case_id, c["path"], c["dist"], c["consumer"], c["provider"])


def test_zero_fn_tasks():
    tasks = _load()
    zero = [t for t in tasks if t.n_missed == 0]
    assert len(zero) >= 20
    for t in zero:
        assert classify_task(t) == []
        for B in (1, 3, 5):
            r = recovery(t, rank_composite(t), B)
            assert r["orr"] == 0.0


def test_tiny_universe_tasks():
    tasks = _load()
    tiny = [t for t in tasks if t.universe_size <= 40]
    for t in tiny:
        for q in QUEUE_RANKERS:
            added = _top_added(t, q, 10)
            assert len(set(added)) == len(added)
            assert len(added) <= t.omitted_size


def test_queue_budget_clipping():
    tasks = _load()[:20]
    for t in tasks:
        for q in QUEUE_RANKERS:
            a5 = _top_added(t, q, 5)
            a10 = _top_added(t, q, 10)
            assert len(a5) <= 5
            assert len(a10) <= 10
            assert set(a5) <= set(a10)


def test_tie_breaking_deterministic():
    tasks = _load()[:20]
    for t in tasks:
        for q in QUEUE_RANKERS:
            r1 = QUEUE_RANKERS[q](t)
            r2 = QUEUE_RANKERS[q](t)
            assert r1 == r2


def test_duplicate_candidate_handling():
    tasks = _load()[:20]
    for t in tasks:
        paths = [c["path"] for c in t.candidates]
        assert len(paths) == len(set(paths))


def test_repository_portability():
    """Both repos must produce taxonomy rows and finite queue metrics."""
    tasks = _load()
    for repo in ("djangocms", "saleor"):
        ts = [t for t in tasks if t.repository == repo]
        rows = []
        for t in ts:
            rows.extend(classify_task(t))
        assert len(rows) > 0
        for q in QUEUE_RANKERS:
            for t in ts[:5]:
                m = naive_union_metrics(t, q, 5)
                assert m["tp"] + m["fn"] == len(t.proxy)
                o = oracle_reviewer_metrics(t, q, 5)
                assert o["n_accepted"] <= o["n_fns_in_top"]


def test_naive_union_conserves_proxy():
    tasks = _load()[:20]
    for t in tasks:
        for q in QUEUE_RANKERS:
            m = naive_union_metrics(t, q, 5)
            assert m["tp"] + m["fn"] == len(t.proxy)


def test_oracle_reviewer_never_worse_on_recall():
    tasks = _load()[:20]
    for t in tasks:
        for q in QUEUE_RANKERS:
            naive = naive_union_metrics(t, q, 5)
            rev = oracle_reviewer_metrics(t, q, 5)
            assert rev["recall"] >= naive["recall"]


def test_no_proxy_in_features():
    """Feature set of every candidate must not contain proxy-derived fields."""
    tasks = _load()[:20]
    allowed = {"path", "module", "parent_dir", "bm25", "bm25_rank_pct", "pt_rank_pct",
               "graph_neighbor", "intent_overlap", "composite", "dist", "consumer",
               "provider", "sibling", "co_change", "history_available",
               "is_missed_positive"}
    for t in tasks:
        for c in t.candidates:
            extra = set(c.keys()) - allowed
            assert not extra, (t.case_id, c["path"], extra)


def test_recovery_zero_for_zero_budget():
    tasks = _load()[:10]
    for t in tasks:
        r = recovery(t, rank_composite(t), 0)
        assert r["recovered"] == 0
        assert r["queue_size"] == 0


def test_primary_distribution_stable_across_reload():
    t1 = _load()
    t2 = _load()
    c1 = Counter(r["primary"] for t in t1 for r in classify_task(t))
    c2 = Counter(r["primary"] for t in t2 for r in classify_task(t))
    assert c1 == c2
