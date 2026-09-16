"""Config reproducibility tests for the harness (ZERO API).

Identical config must produce an identical ExperimentSpec SHA-256. The frozen
Protocol-A spec must be reproducible across fresh constructions and across
JSON round-trips.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.harness.protocol_a import (
    FROZEN_K_VALUES,
    build_protocol_a_spec,
)
from benchmark.harness.spec import ExperimentSpec


def test_frozen_spec_hash_is_stable_across_instances() -> None:
    hashes = {build_protocol_a_spec(method_name="bm25", corpus_mode="metadata").sha256 for _ in range(3)}
    assert len(hashes) == 1


@pytest.mark.parametrize("method", ["random", "bm25", "path_token", "graph", "hybrid"])
def test_every_method_spec_reproducible(method: str) -> None:
    a = build_protocol_a_spec(method_name=method, corpus_mode="metadata")
    b = build_protocol_a_spec(method_name=method, corpus_mode="metadata")
    assert a.sha256 == b.sha256
    assert a.method_name == method


def test_corpus_mode_changes_hash() -> None:
    a = build_protocol_a_spec(method_name="bm25", corpus_mode="metadata")
    b = build_protocol_a_spec(method_name="bm25", corpus_mode="parent_commit")
    assert a.sha256 != b.sha256


def test_method_change_changes_hash() -> None:
    a = build_protocol_a_spec(method_name="bm25", corpus_mode="metadata")
    b = build_protocol_a_spec(method_name="graph", corpus_mode="metadata")
    assert a.sha256 != b.sha256


def test_spec_dict_roundtrip_preserves_hash(tmp_path: Path) -> None:
    spec = build_protocol_a_spec(method_name="hybrid", corpus_mode="metadata")
    path = tmp_path / "spec.json"
    import json

    path.write_text(json.dumps(spec.to_dict(), indent=2), encoding="utf-8")
    restored = ExperimentSpec.from_dict(json.loads(path.read_text(encoding="utf-8")))
    assert restored.sha256 == spec.sha256
    assert restored.k_values == FROZEN_K_VALUES
