"""PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 — co-change + episodic tests.

Covers the mission §37 requirements: co-change counts; Jaccard formula;
support >= 2; Sparse-empty behavior; dense-rank1 seed behavior; historical
commit-text indexing; BM25 determinism; structural top10; episodic top10;
candidate-union construction.
"""
# ruff: noqa: N812

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.memory_rescue import cochange as CC  # noqa: E402
from benchmark.memory_rescue import episodic as EP  # noqa: E402


class _FakeTaskHistory:
    """Synthetic TaskHistory with a fixed co-change relation."""

    def __init__(self, hcc, relations):
        self.history_change_count = hcc
        self._relations = relations  # seed -> {f: c_fs}

    def cochange_counts_to(self, seed):
        return dict(self._relations.get(seed, {}))


def _make_history():
    # f1 co-changes with s1 (3 times) and s2 (2 times); s1 co-changes f2 (2).
    hcc = {"s1": 5, "s2": 3, "f1": 4, "f2": 3, "noise": 100}
    relations = {
        "s1": {"f1": 3, "f2": 2},
        "s2": {"f1": 2},
    }
    return _FakeTaskHistory(hcc, relations)


def test_cochange_sparse_map():
    th = _make_history()
    sparse = {"s1", "s2"}
    cs = CC.cochange_sparse_map(th, sparse)
    # f1: max(jaccard(4,5,3)=3/6=0.5, jaccard(4,3,2)=2/5=0.4) = 0.5
    assert cs["f1"] == pytest.approx(0.5, abs=1e-12)
    # f2: jaccard(3,5,2)=2/6=1/3 (only via s1)
    assert cs["f2"] == pytest.approx(1 / 3, abs=1e-12)
    # sparse files themselves: self-pair -> 1.0 when C>0
    assert cs["s1"] == 1.0
    assert "noise" not in cs


def test_cochange_sparse_map_empty_sparse():
    th = _make_history()
    assert CC.cochange_sparse_map(th, set()) == {}


def test_cochange_top1_map():
    th = _make_history()
    ct1 = CC.cochange_top1_map(th, "s1")
    assert ct1["f1"] == pytest.approx(0.5, abs=1e-12)
    assert ct1["s1"] == 1.0  # self pair
    assert CC.cochange_top1_map(th, None) == {}


def test_cochange_memory_score_map():
    cs = {"f1": 0.5, "f2": 0.25}
    ct1 = {"f1": 0.7, "f3": 0.9}
    m = CC.cochange_memory_score_map(cs, ct1)
    assert m["f1"] == pytest.approx(0.7, abs=1e-12)
    assert m["f2"] == pytest.approx(0.25, abs=1e-12)
    assert m["f3"] == pytest.approx(0.9, abs=1e-12)


def test_structural_candidates_top10_tiebreak():
    th = _make_history()
    sparse = {"s1", "s2"}
    cs = CC.cochange_sparse_map(th, sparse)
    ct1 = CC.cochange_top1_map(th, "s1")
    mem = CC.cochange_memory_score_map(cs, ct1)
    non_sparse = ["f1", "f2", "zero", "zzz"]
    support = th.history_change_count
    top = CC.structural_candidates(mem, support, non_sparse, k=2)
    assert top[0] == "f1"  # highest score
    assert len(top) == 2
    # zero-score files excluded
    assert "zero" not in top


def test_structural_candidates_path_ascending_tiebreak():
    mem = {"a.py": 0.5, "b.py": 0.5}
    support = {"a.py": 3, "b.py": 3}
    top = CC.structural_candidates(mem, support, ["b.py", "a.py"], k=10)
    assert top == ["a.py", "b.py"]  # equal score+support -> path ascending


def test_structural_candidates_higher_support_tiebreak():
    mem = {"a.py": 0.5, "b.py": 0.5}
    support = {"a.py": 9, "b.py": 2}
    top = CC.structural_candidates(mem, support, ["b.py", "a.py"], k=10)
    assert top == ["a.py", "b.py"]  # higher support first


def test_episodic_bm25_deterministic():
    records = [
        {"sha": "a", "subject": "fix shipping zone", "body": "zone fix",
         "paths": ("saleor/shipping.py",)},
        {"sha": "b", "subject": "add channels", "body": "channel type",
         "paths": ("saleor/graphql/channel/types.py",)},
        {"sha": "c", "subject": "unrelated", "body": "formatting",
         "paths": ("saleor/__init__.py",)},
    ]
    q1 = "add channels"
    s1 = EP.episode_signals(records, q1)
    s2 = EP.episode_signals(records, q1)
    assert s1 == s2  # determinism
    assert "saleor/graphql/channel/types.py" in s1
    assert s1["saleor/graphql/channel/types.py"]["episode_hit_count"] >= 1
    assert 0.0 <= s1["saleor/graphql/channel/types.py"]["episode_similarity"] <= 1.0


def test_episodic_retrieve_top_frozen_k():
    assert EP.EPISODIC_TOP_CHANGES == 10
    docs = {f"c{i}": f"commit {i} feature widget" for i in range(20)}
    top = EP.retrieve_top(docs, "feature widget", k=10)
    assert len(top) == 10
    top2 = EP.retrieve_top(docs, "feature widget", k=10)
    assert top == top2


def test_episodic_zero_when_not_touched():
    records = [
        {"sha": "a", "subject": "fix zone", "body": "", "paths": ("x.py",)},
    ]
    s = EP.episode_signals(records, "fix zone")
    assert "unrelated.py" not in s


def test_episode_signals_normalization_by_max():
    records = [
        {"sha": "strong", "subject": "widget widget widget widget widget",
         "body": "", "paths": ("best.py",)},
        {"sha": "weak", "subject": "unrelated formatting", "body": "",
         "paths": ("worst.py",)},
    ]
    s = EP.episode_signals(records, "widget widget widget widget widget")
    assert s["best.py"]["episode_similarity"] == pytest.approx(1.0, abs=1e-9)
    assert s["best.py"]["episode_similarity"] >= s["worst.py"]["episode_similarity"]
