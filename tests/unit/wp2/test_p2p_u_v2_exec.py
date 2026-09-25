"""WP-2 P2P-U V2 ENG execution runner (Mission-09) - unit tests (ZERO API).

Covers deterministic chunking (identical membership/order across states and
repetitions), which is the only pure-logic surface of the exec runner; the
execution itself is substrate-bound and validated by the real ENG runs.
"""

from __future__ import annotations

from scripts.wp2_p2p_u_v2_exec import deterministic_chunks


def test_deterministic_chunks_single() -> None:
    nodes = [f"saleor/a/tests/test_a.py::t{i}" for i in range(10)]
    chunks = deterministic_chunks(nodes, max_chars=10**6)
    assert chunks == [nodes]
    assert sum(len(c) for c in chunks) == len(nodes)


def test_deterministic_chunks_small_limit() -> None:
    nodes = [f"saleor/a/tests/test_a.py::t{i}" for i in range(10)]
    chunks = deterministic_chunks(nodes, max_chars=50)
    assert len(chunks) > 1
    # membership preserved exactly, order preserved within chunk sequence
    assert [n for c in chunks for n in c] == nodes
    # identical on repeated calls
    assert chunks == deterministic_chunks(nodes, max_chars=50)


def test_deterministic_chunks_empty() -> None:
    assert deterministic_chunks([]) == []


def test_deterministic_chunks_stable_across_runs() -> None:
    nodes = [f"saleor/x/tests/test_x.py::n{i:04d}" for i in range(500)]
    a = deterministic_chunks(nodes)
    b = deterministic_chunks(nodes)
    assert a == b
    assert sum(len(c) for c in a) == 500
