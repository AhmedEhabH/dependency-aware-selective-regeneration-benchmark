"""Integration tests: frozen djangoCMS 5.0.0 candidate universe + graph regression (M4A-1).

Proves the frozen M3/M1 identities remain unchanged after the backwards-compatible
parameterization of ``source_graph.py``:
- candidate universe count: 144
- candidate universe canonical hash: 43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410
- graph edge count: 562
- graph canonical hash: 0a6bf0f758c9cd7de79adb72138c549a2b0aee3cfd62841496cb455d1ce7cd58
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmark.real_commits import validation
from benchmark.real_commits.miner import PRODUCTION_ROOTS

FROZEN_UNIVERSE_COUNT = 144
FROZEN_UNIVERSE_HASH = "43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410"
FROZEN_GRAPH_EDGE_COUNT = 562
FROZEN_GRAPH_HASH = "0a6bf0f758c9cd7de79adb72138c549a2b0aee3cfd62841496cb455d1ce7cd58"


def test_frozen_candidate_universe_identity_unchanged() -> None:
    result = validation.frozen_universe_regression()
    assert result["count_ok"] is True
    assert result["hash_ok"] is True
    assert result["count"] == FROZEN_UNIVERSE_COUNT
    assert result["hash"] == FROZEN_UNIVERSE_HASH


def test_frozen_graph_identity_unchanged() -> None:
    result = validation.frozen_graph_regression()
    assert result["edge_count_ok"] is True
    assert result["hash_ok"] is True
    assert result["edge_count"] == FROZEN_GRAPH_EDGE_COUNT
    assert result["hash"] == FROZEN_GRAPH_HASH
    assert result["node_count"] == FROZEN_UNIVERSE_COUNT


def test_production_roots_match_frozen_extraction() -> None:
    """M4A-1 package_roots default must equal the frozen djangoCMS roots."""
    assert PRODUCTION_ROOTS == ("cms", "menus")


@pytest.mark.skipif(
    not (Path("dist/real-commit-cache/djangocms/.git")).is_dir(),
    reason="full django-cms cache not available; frozen artifact identity still verified",
)
def test_frozen_identities_reproducible_from_cached_anchor_source() -> None:
    """Re-extract from the cached anchor source with DEFAULT parameters.

    Proves the parameterization kept default behavior semantically equivalent:
    universe hash and graph edge-set must be identical to the frozen artifacts.
    The graph canonical hash may differ ONLY by the recorded extractor-source hash
    (the extractor module changed since the freeze; edges/nodes/counts identical).
    """
    import io
    import subprocess
    import tarfile
    import tempfile
    from datetime import UTC, datetime

    from benchmark.external_validity.source_graph import (
        build_candidate_universe,
        build_dependency_graph,
        canonical_universe_hash,
    )

    cache = Path("dist/real-commit-cache/djangocms")
    anchor = "0f633fc9fa213357f4202482aab2b0edad680f95"
    res = subprocess.run(
        ["git", "-C", str(cache), "archive", "--format=tar", anchor],
        capture_output=True,
        check=True,
    )
    with tempfile.TemporaryDirectory(prefix="rc-regress-") as tmp:
        root = Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(res.stdout), mode="r|") as tf:
            tf.extractall(root)
        records = build_candidate_universe(root, package_roots=("cms", "menus"))
        assert len(records) == FROZEN_UNIVERSE_COUNT
        assert canonical_universe_hash(records) == FROZEN_UNIVERSE_HASH

        graph = build_dependency_graph(
            repo_root=root,
            records=records,
            pinned_commit=anchor,
            candidate_universe_hash=FROZEN_UNIVERSE_HASH,
            extractor_hash="regression-check",
            generated_utc=datetime.now(UTC).isoformat(),
        )
        assert graph["node_count"] == FROZEN_UNIVERSE_COUNT
        assert graph["edge_count"] == FROZEN_GRAPH_EDGE_COUNT
        frozen_graph = json.loads(
            validation.FROZEN_GRAPH_PATH.read_text(encoding="utf-8")
        )
        assert set(map(tuple, graph["edges"])) == set(map(tuple, frozen_graph["edges"]))
