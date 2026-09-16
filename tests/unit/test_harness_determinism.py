"""Deterministic ranking tests (ZERO API).

The same inputs + frozen seed must produce the same ranked output across
repeated constructions (restart determinism) for every frozen ranker.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.harness import interfaces, registry
from benchmark.harness.djangocms import DjangoCMSParentSnapshot

DATASET_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "benchmark_data"
    / "real_commit_impact_v1"
)

SYNTHETIC = interfaces.PublicCase(
    case_id="synth",
    repository="djangocms",
    repository_url="https://github.com/django-cms/django-cms",
    parent_commit="p" * 40,
    target_commit="t" * 40,
    intent_text="fix: page slug uniqueness check on menu model",
    candidate_paths=("cms/models/pagemodel.py", "cms/admin/pageadmin.py", "cms/menu.py", "cms/api.py"),
    candidate_records=(
        {"path": "cms/models/pagemodel.py", "module": "cms.models", "classes": ["Page"], "functions": []},
        {"path": "cms/admin/pageadmin.py", "module": "cms.admin", "classes": ["PageAdmin"], "functions": []},
        {"path": "cms/menu.py", "module": "cms.menu", "classes": ["Menu"], "functions": ["get_menu"]},
        {"path": "cms/api.py", "module": "cms", "classes": [], "functions": ["get_page"]},
    ),
    graph_edges=(("cms/models/pagemodel.py", "cms/admin/pageadmin.py"),),
    public_bundle_sha256="x",
)


@pytest.mark.parametrize("method", ["random", "bm25", "path_token", "graph", "hybrid"])
def test_restart_determinism(method: str) -> None:
    snapshot = DjangoCMSParentSnapshot(cache_dir=None).snapshot(SYNTHETIC)
    r1 = registry.resolve_ranker(method)().rank(case=SYNTHETIC, snapshot=snapshot, k=3)
    r2 = registry.resolve_ranker(method)().rank(case=SYNTHETIC, snapshot=snapshot, k=3)
    assert r1.ranked_paths == r2.ranked_paths
    assert r1.selected_paths == r2.selected_paths


def test_random_differs_across_case_ids() -> None:
    snapshot = DjangoCMSParentSnapshot(cache_dir=None).snapshot(SYNTHETIC)
    ranker = registry.resolve_ranker("random")()
    a = ranker.rank(case=SYNTHETIC, snapshot=snapshot, k=3)
    other = interfaces.PublicCase(
        **{**SYNTHETIC.__dict__, "case_id": "synth-other"}
    )
    b = ranker.rank(case=other, snapshot=snapshot, k=3)
    assert a.ranked_paths != b.ranked_paths or len(set(a.ranked_paths)) == len(a.ranked_paths)


def test_selected_is_topk_of_ranked() -> None:
    snapshot = DjangoCMSParentSnapshot(cache_dir=None).snapshot(SYNTHETIC)
    for method in ("random", "bm25", "path_token", "graph", "hybrid"):
        pred = registry.resolve_ranker(method)().rank(case=SYNTHETIC, snapshot=snapshot, k=2)
        assert pred.selected_paths == pred.ranked_paths[:2]
        assert len(pred.selected_paths) == 2
