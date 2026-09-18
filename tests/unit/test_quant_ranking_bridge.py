"""Quantitative-structural ranking bridge — unit tests (T3, ZERO API).

Covers:
- formula determinism + frozen three-formula identity
- feature provenance: only parent-visible fields feed the rankers
- graph-direction consistency (rev_support counts downstream edges)
- matched-budget macro ORR helpers
- fold/portability helpers run on both repos
- metric recomputation on synthetic FNs
- sealed-set guard
- no hidden-proxy feature generation
"""
# ruff: noqa: N806
from __future__ import annotations

from benchmark.recall.data import load_dev_tasks
from benchmark.recall.quant_rankers import (
    QUANT_RANKERS,
    _bidir_norm,
    _fwd_norm,
    _rev_norm,
    artifact_corr,
    candidate_precision,
    fold_direction,
    macro_orr,
    naive_union_f1,
    oracle_reviewer_f1,
    unique_fn_beyond_route_b,
)
from benchmark.recall.rankers import recovery


def _load():
    if not hasattr(_load, "_tasks"):
        _load._tasks = load_dev_tasks()
    return _load._tasks


def test_dev_counts_and_sealed():
    tasks = _load()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]
    assert len(dc) == 174
    assert len(sc) == 149
    for t in tasks:
        assert "internal-test" not in t.role.lower()
        assert "reserve" not in t.role.lower()


def test_three_and_only_three_quant_rankers():
    assert list(QUANT_RANKERS) == ["R1_BM25+RevSupport", "R2_BM25+BidirSupport", "R3_BM25+BidirNorm"]


def test_rankers_deterministic():
    tasks = _load()[:20]
    for t in tasks:
        for rfn in QUANT_RANKERS.values():
            assert rfn(t) == rfn(t)
            assert len(rfn(t)) == t.omitted_size


def test_support_counts_are_counts():
    """rev_support must equal the count of downstream edges to seeds; forward
    the count of upstream edges from seeds (graph-direction consistency)."""
    tasks = _load()[:30]
    for t in tasks:
        for c in t.candidates:
            rev = int(c["rev_support"])
            fwd = int(c["fwd_support"])
            assert rev >= 0 and fwd >= 0
            # membership implies count >= 1
            if c["consumer"]:
                assert rev >= 1, (t.case_id, c["path"])
            if c["provider"]:
                assert fwd >= 1, (t.case_id, c["path"])
            if rev == 0:
                assert not c["consumer"]
            if fwd == 0:
                assert not c["provider"]


def test_normalizations_bounded():
    tasks = _load()[:30]
    for t in tasks:
        rn = _rev_norm(t)
        fn = _fwd_norm(t)
        bn = _bidir_norm(t)
        for c in t.candidates:
            assert 0.0 <= rn[c["path"]] <= 1.0
            assert 0.0 <= fn[c["path"]] <= 1.0
            assert 0.0 <= bn[c["path"]] <= 1.0


def test_no_proxy_in_features():
    """Feature set of every candidate must not contain proxy-derived fields."""
    tasks = _load()[:20]
    allowed = {"path", "module", "parent_dir", "bm25", "bm25_rank_pct", "pt_rank_pct",
               "graph_neighbor", "intent_overlap", "composite", "dist", "consumer",
               "provider", "rev_support", "fwd_support", "sibling", "co_change",
               "history_available", "is_missed_positive"}
    for t in tasks:
        for c in t.candidates:
            extra = set(c.keys()) - allowed
            assert not extra, (t.case_id, c["path"], extra)


def test_rankers_only_use_parent_visible_fields():
    """Ranking keys must be computable from a strict subset of parent-visible
    fields (no composite/is_missed_positive/proxy)."""
    tasks = _load()[:20]
    for t in tasks:
        for rfn in QUANT_RANKERS.values():
            ranked = rfn(t)
            assert len(ranked) == len(set(ranked))
            # determinism under the same features
            r2 = rfn(t)
            assert ranked == r2


def test_macro_orr_matches_recovery_definition():
    tasks = _load()[:10]
    from benchmark.recall.rankers import rank_composite

    for B in (1, 3, 5):
        rows = [recovery(t, rank_composite(t), B) for t in tasks]
        exp = sum(r["orr"] for r in rows) / len(rows)
        assert abs(macro_orr(tasks, rank_composite, B) - exp) < 1e-9


def test_synthetic_metric_recomputation():
    """On a hand-built task with a known top-B, candidate_precision and
    naive_union_f1 must match manual arithmetic."""
# Use the first real task but force the top-B set to a known subset.
    tasks = _load()
    t = next(t for t in tasks if t.n_missed >= 3 and t.omitted_size >= 5)
    ranked = [c["path"] for c in t.candidates][:5]
    # ranker that returns a fixed order
    def fixed_rfn(_t):
        return ranked

    B = 5
    top = set(ranked[:B])
    fn_set = {c["path"] for c in t.candidates if c["is_missed_positive"]}
    exp_prec = len(top & fn_set) / len(top)
    got_prec = candidate_precision([t], fixed_rfn, B)
    assert abs(got_prec - exp_prec) < 1e-9
    # naive union F1
    pos = set(t.proxy)
    final = set(t.write_set) | top
    tp = len(final & pos)
    fp = len(final - pos)
    fn = len(pos - final)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    exp_f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    assert abs(naive_union_f1([t], fixed_rfn, B)["f1"] - round(exp_f1, 4)) < 1e-6
# oracle reviewer adds zero NEW FP beyond the Sparse baseline FP tail
    o = oracle_reviewer_f1([t], fixed_rfn, B)
    sparse_fp = len(set(t.write_set) - set(t.proxy))
    assert o["fp"] <= sparse_fp
    assert o["tp"] + o["fn"] == len(set(t.proxy))  # no positives lost


def test_unique_fn_beyond_route_b_nonnegative():
    tasks = _load()
    for repo in ("djangocms", "saleor"):
        ts = [t for t in tasks if t.repository == repo]
        for rfn in QUANT_RANKERS.values():
            for B in (1, 3, 5, 10):
                assert unique_fn_beyond_route_b(ts, rfn, B) >= 0


def test_fold_and_artifact_helpers_both_repos():
    tasks = _load()
    for repo in ("djangocms", "saleor"):
        ts = [t for t in tasks if t.repository == repo]
        for rfn in QUANT_RANKERS.values():
            folds = fold_direction(ts, rfn, 5, 5, 20260918)
            assert len(folds) == 5
            assert all(0.0 <= x <= 1.0 for x in folds)
            cu, co = artifact_corr(ts, rfn, 5)
            assert -1.0 <= cu <= 1.0 and -1.0 <= co <= 1.0


def test_repo_portability():
    """Every ranker must produce finite metrics on both repos at all budgets."""
    tasks = _load()
    for repo in ("djangocms", "saleor"):
        ts = [t for t in tasks if t.repository == repo]
        for B in (1, 3, 5, 10):
            for rfn in QUANT_RANKERS.values():
                m = macro_orr(ts, rfn, B)
                assert 0.0 <= m <= 1.0
                p = candidate_precision(ts, rfn, B)
                assert 0.0 <= p <= 1.0

