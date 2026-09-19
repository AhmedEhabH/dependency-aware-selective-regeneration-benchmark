"""Frozen SweRank file-level adapter tests (T3, ZERO API).

Covers: code-unit extraction determinism and fallback; the ONE MAX aggregation
rule; deterministic ranking with path tie-break; omitted-candidate pool
semantics; no target-label usage in ranking inputs.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from benchmark.signal.code_units import extract_code_units
from benchmark.signal.swrank_adapter import (
    aggregate_file_score,
    cosine,
    rank_files,
    score_units,
)


def test_extract_code_units_functions_classes_methods():
    src = (
        "import os\n\n"
        "def top(a):\n    return a\n\n"
        "class K:\n"
        "    def m(self):\n        return 1\n"
        "    def n(self):\n        return 2\n"
        "\n"
        "async def atask():\n    pass\n"
    )
    units = extract_code_units(src)
    joined = "\n".join(units)
    assert "def top(a):" in joined
    assert "class K:" in joined
    assert "def m(self):" in joined
    assert "def n(self):" in joined
    # Official SweRank parser does NOT index top-level async functions.
    assert "async def atask():" not in joined


def test_extract_code_units_async_only_file_falls_back_to_module():
    src = "async def atask():\n    pass\n"
    units = extract_code_units(src)
    assert len(units) == 1 and units[0] == src


def test_extract_code_units_fallback_on_syntax_error():
    src = "def broken(:\n    pass\n  ???"
    units = extract_code_units(src)
    assert len(units) == 1 and units[0] == src


def test_extract_code_units_module_only_fallback():
    src = "VALUE = 1\nOTHER = 2\n"
    units = extract_code_units(src)
    assert len(units) == 1 and units[0] == src


def test_extract_code_units_deterministic():
    src = "def f():\n    return 1\n\ndef g():\n    return 2\n"
    assert extract_code_units(src) == extract_code_units(src)


def test_cosine_unit_vectors():
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.0, 1.0, 0.0])
    c = np.array([1.0, 0.0, 0.0])
    assert cosine(a, b) == pytest.approx(0.0)
    assert cosine(a, c) == pytest.approx(1.0)
    assert cosine(a, -a) == pytest.approx(-1.0)


def test_cosine_zero_vector():
    z = np.zeros(3)
    a = np.array([1.0, 0.0, 0.0])
    assert cosine(z, a) == 0.0
    assert cosine(a, z) == 0.0


def test_aggregate_file_score_is_max_only():
    assert aggregate_file_score([("a", 0.1), ("b", 0.9)]) == pytest.approx(0.9)
    assert aggregate_file_score([("a", 0.1), ("b", 0.9), ("c", 0.55)]) == pytest.approx(0.9)
    assert aggregate_file_score([]) == -math.inf


def test_score_units_uses_cosine():
    embs = {"u1": np.array([1.0, 0.0, 0.0]), "u2": np.array([0.0, 1.0, 0.0])}
    q = np.array([1.0, 0.0, 0.0])
    s = score_units(embs, q)
    assert s["u1"] == pytest.approx(1.0)
    assert s["u2"] == pytest.approx(0.0)


def test_rank_files_omits_write_set_and_ties_by_path():
    scores = {"c/b.py": 0.5, "a/a.py": 0.5, "b/z.py": 0.9, "a/w.py": 0.2}
    universe = ["c/b.py", "a/a.py", "b/z.py", "a/w.py"]
    ranked = rank_files(scores, universe, frozenset({"c/b.py"}))
    # write set = {c/b.py}; b/z.py highest; then path tie a/a.py before others.
    assert ranked[0] == "b/z.py"
    # the two 0.5 files tie -> ascending path
    tail = ranked[1:]
    assert tail == sorted(tail)
    assert "c/b.py" not in ranked  # in write set -> not a candidate
    assert set(ranked) == {"a/a.py", "b/z.py", "a/w.py"}


def test_rank_files_tiebreak_ascending_path():
    scores = {"m/zz.py": 0.7, "a/aa.py": 0.7, "a/ab.py": 0.7}
    ranked = rank_files(scores, list(scores), frozenset())
    assert ranked == sorted(scores)


def test_rank_files_deterministic():
    scores = {"c.py": 0.1, "a.py": 0.9, "b.py": 0.5}
    universe = ["c.py", "a.py", "b.py"]
    assert rank_files(scores, universe, frozenset()) == rank_files(scores, universe, frozenset())


def test_rank_files_unrepresented_file_never_wins_tie():
    # file with -inf score (no units) must sort last regardless of path
    scores = {"b.py": -math.inf}
    universe = ["a.py", "b.py"]
    ranked = rank_files(scores, universe, frozenset())
    assert ranked[-1] == "b.py"
