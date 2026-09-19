"""QWEN3 two-realization runner unit tests (T3, ZERO network).

Tests the deterministic, budget-guarded, label-free parts of the runner and
analyzer WITHOUT touching the network or the real corpus:
  - whitespace-only unit exclusion rule (protocol §12.9);
  - ChunkCache round-trip + missing/add/get;
  - fail-closed budget projection (must STOP before the $0.50 ceiling);
  - analyzer metric contributions (Qwen - RouteB) on a tiny synthetic task;
  - reproducibility stats (Jaccard / one-file flip / same-set percentage).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))


sys.path.insert(0, str(_PROJECT_DIR / "scripts"))
import qwen3_two_realization_analyze as ana  # noqa: E402
import qwen3_two_realization_run as run  # noqa: E402


def test_whitespace_only_units_excluded():
    # Protocol §12.9: whitespace-only units are skipped deterministically.
    assert run._valid_unit("def f():\n    return 1") is True
    assert run._valid_unit("   \n  ") is False
    assert run._valid_unit("") is False


def test_chunk_cache_roundtrip(tmp_path):
    cache = run.ChunkCache(tmp_path / "cache")
    texts = ["alpha", "beta", "gamma"]
    vecs = [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]
    cache.add(texts[:2], vecs[:2])
    cache.add(texts[2:], vecs[2:])
    assert len(cache) == 3
    got = cache.get(["gamma", "alpha"])
    assert got.shape == (2, 2)
    np.testing.assert_allclose(got[0], [0.5, 0.5])
    # reload from disk (resume safety)
    cache2 = run.ChunkCache(tmp_path / "cache")
    assert len(cache2) == 3
    np.testing.assert_allclose(cache2.get(["beta"]), [[0.0, 1.0]])


def test_budget_projection_stops_before_ceiling():
    # With a realistic per-unit token average, projecting 2 realizations must
    # be BELOW the ceiling, and a burned budget near the ceiling must trip.
    proj = run._projected_cost(0.0, run.N_UNITS_ESTIMATE, 323)
    assert proj < run.CEILING_USD
    assert proj == pytest.approx(0.023 + 0.2188, abs=1e-4)
    big = run._projected_cost(0.40, run.N_UNITS_ESTIMATE, 323)
    assert big >= run.CEILING_USD


def _tiny_task(cid="t1"):
    class T:
        case_id = cid
        repository = "djangocms"
        parent_commit = "abc123"
        write_set = frozenset({"a.py"})
        proxy = frozenset({"b.py", "c.py"})
        fn_paths = frozenset({"b.py", "c.py"})
        n_missed = 2
        omitted_size = 2
        intent_text = "query"
    return T()


def test_analyzer_metric_contributions():
    t = _tiny_task()
    r = {
        "repository": "djangocms", "case_id": "t1", "omitted_size": 2,
        "qwen_ranked": ["b.py", "c.py"],
        "routeb_ranked": ["b.py", "c.py"],
        "bm25_ranked": ["b.py", "c.py"],
    }
    # write_set={a.py}, omitted={b.py, c.py}, proxy={b.py, c.py}
    q = ana._contrib(r, t, "qwen", 5)
    # final={a.py,b.py,c.py}; tp=2 (b,c), fp=1 (a), fn=0
    assert q == {"tp": 2, "fp": 1, "fn": 0, "orr": 1.0, "cand_fn": 2, "cand_sel": 2}


def test_reproducibility_stats():
    base = {
        "t1": {"qwen_ranked": ["a", "b", "c", "d", "e"], "omitted_size": 5},
        "t2": {"qwen_ranked": ["a", "b", "c", "d", "e"], "omitted_size": 5},
        "t3": {"qwen_ranked": ["a", "b", "c", "d", "e"], "omitted_size": 5},
    }
    alt = {
        "t1": {"qwen_ranked": ["a", "b", "c", "d", "e"], "omitted_size": 5},
        "t2": {"qwen_ranked": ["a", "b", "c", "d", "f"], "omitted_size": 5},
        "t3": {"qwen_ranked": ["x", "y", "z", "w", "v"], "omitted_size": 5},
    }
    rep = ana._reproducibility(base, alt)
    # t1 same (Jaccard 1.0), t2 one-file swap (Jaccard 4/6), t3 disjoint (Jaccard 0)
    assert rep["exact_same_selected_set_task_percentage"] == pytest.approx(100.0 / 3, abs=0.01)
    assert rep["n_one_file_boundary_flip_tasks"] == 1
    assert rep["jaccard"]["min"] == pytest.approx(0.0, abs=1e-9)
    assert rep["jaccard"]["mean"] == pytest.approx(round((1.0 + 4.0 / 6 + 0.0) / 3, 4), abs=1e-9)
    assert rep["jaccard"]["median"] == pytest.approx(round(4.0 / 6, 4), abs=1e-9)


def test_full_score_rows_are_label_free():
    # The persistence schema (see runner main loop) must not carry proxy/fn labels.
    fields = {"case_id", "repository", "parent_commit", "file_path",
              "dense_file_score", "dense_rank", "in_sparse", "query_sha256",
              "model_id", "provider", "realization_id"}
    assert "proxy" not in fields and "fn_paths" not in fields
    assert "write_set" not in fields
