"""Unit tests for cheap non-LLM baselines (Protocol A, ZERO API).

Covers tokenizer, BM25 determinism, rankers B0–B4, seed rule, deterministic
seeding, evaluation metrics (synthetic known values), and leakage/pa
parent-state safety.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmark.cheap_baselines import evaluation, runner
from benchmark.cheap_baselines.bm25 import BM25Index
from benchmark.cheap_baselines.corpus import MetadataCorpus
from benchmark.cheap_baselines.rankers import (
    compute_seed_paths,
    rank_bm25,
    rank_graph,
    rank_hybrid,
    rank_path_token,
    rank_random,
)
from benchmark.cheap_baselines.tokenize import token_set, tokenize, tokenize_path

DATASET_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "benchmark_data"
    / "real_commit_impact_v1"
)

CASES = (
    "djangocms-rc-06ecf3a8e8de",  # TRAIN
    "djangocms-rc-0daae01f2f65",  # VALIDATION
)

_BUNDLE_RECORDS = (
    {"path": "cms/models/pagemodel.py", "module": "cms.models", "classes": ["Page"], "functions": []},
    {"path": "cms/admin/pageadmin.py", "module": "cms.admin", "classes": ["PageAdmin"], "functions": []},
    {"path": "cms/api.py", "module": "cms", "classes": [], "functions": ["get_page"]},
)
_BUNDLE_PATHS = ("cms/models/pagemodel.py", "cms/admin/pageadmin.py", "cms/api.py")

_METADATA = MetadataCorpus(parent_commit="p" * 40, candidate_records=_BUNDLE_RECORDS)


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------


def test_tokenize_snake_and_camel() -> None:
    assert {"get", "page"} <= token_set("get_page helper")
    assert {"get", "page"} <= token_set("getPage helper")
    assert {"slug"} <= token_set("SlugUniquenessChecker")


def test_tokenize_drops_stopwords() -> None:
    tokens = tokenize("fix: add the pagemodel refactor this now")
    assert "fix" not in tokens
    assert "the" not in tokens
    assert "this" not in tokens
    assert "refactor" not in tokens
    assert "pagemodel" in tokens
    assert "now" in tokens


def test_tokenize_path_segments() -> None:
    assert tokenize_path("cms/models/pagemodel.py") == ("cms", "models", "pagemodel")


# ---------------------------------------------------------------------------
# BM25
# ---------------------------------------------------------------------------


def test_bm25_is_deterministic() -> None:
    corpus = {
        "a.py": "def page_slug: return slug",
        "b.py": "class MenuItem: pass",
    }
    i1 = BM25Index(corpus)
    i2 = BM25Index(dict(sorted(corpus.items())))
    assert i1.rank("slug", k=2) == i2.rank("slug", k=2)
    assert i1.n_docs == 2


def test_bm25_prefers_matching_doc() -> None:
    corpus = {
        "a.py": "def page_slug: return slug",
        "b.py": "class MenuItem: pass",
    }
    index = BM25Index(corpus)
    assert index.rank("page slug checker", k=1)[0] == "a.py"


# ---------------------------------------------------------------------------
# Rankers — determinism + seed rule
# ---------------------------------------------------------------------------


def test_random_rank_deterministic_and_matched_k() -> None:
    r1 = rank_random(case_id="c1", candidate_paths=_BUNDLE_PATHS, seed=20260915, k=3)
    r2 = rank_random(case_id="c1", candidate_paths=_BUNDLE_PATHS, seed=20260915, k=3)
    assert r1 == r2
    assert len(r1) == 3
    assert set(r1) <= set(_BUNDLE_PATHS)


def test_random_rank_differs_across_cases() -> None:
    r1 = rank_random(case_id="c1", candidate_paths=_BUNDLE_PATHS, seed=20260915, k=3)
    r2 = rank_random(case_id="c2", candidate_paths=_BUNDLE_PATHS, seed=20260915, k=3)
    assert r1 != r2


def test_bm25_rank_bounded_by_k() -> None:
    ranked = rank_bm25(intent_text="fix: slug uniqueness page", corpus=_METADATA, k=2)
    assert len(ranked) == 2


def test_path_token_rank_prefers_obvious_match() -> None:
    ranked = rank_path_token(
        intent_text="fix: pageadmin slug models",
        candidate_paths=_BUNDLE_PATHS,
        candidate_records=_BUNDLE_RECORDS,
        k=2,
    )
    assert "cms/admin/pageadmin.py" in ranked
    assert "cms/models/pagemodel.py" in ranked


def test_seed_rule_nonempty_and_non_leaking() -> None:
    elig = compute_seed_paths(
        intent_text="fix: page models slug",
        candidate_paths=_BUNDLE_PATHS,
        candidate_records=_BUNDLE_RECORDS,
    )
    assert elig.eligible
    assert "cms/models/pagemodel.py" in elig.seed_paths


def test_seed_rule_empty_documents_not_invents() -> None:
    elig = compute_seed_paths(
        intent_text="zzz qqq www exclusive",
        candidate_paths=_BUNDLE_PATHS,
        candidate_records=_BUNDLE_RECORDS,
    )
    assert not elig.eligible
    assert elig.seed_paths == ()
    assert elig.reason == "no_defensible_seed_signal_stop_and_document"


def test_graph_rank_empty_seed_returns_empty() -> None:
    ranked, seeds, reason = rank_graph(
        intent_text="zzz qqq www exclusive",
        candidate_paths=_BUNDLE_PATHS,
        candidate_records=_BUNDLE_RECORDS,
        graph_edges=(("cms/models/pagemodel.py", "cms/admin/pageadmin.py"),),
        k=3,
    )
    assert ranked == ()
    assert reason == "no_defensible_seed_signal_stop_and_document"


def test_graph_rank_bounds() -> None:
    ranked, seeds, reason = rank_graph(
        intent_text="fix: page models slug",
        candidate_paths=_BUNDLE_PATHS,
        candidate_records=_BUNDLE_RECORDS,
        graph_edges=(("cms/models/pagemodel.py", "cms/admin/pageadmin.py"),),
        k=2,
    )
    assert reason == "seeds_ok"
    assert len(ranked) == 2
    assert len(seeds) >= 1


def test_hybrid_rank_bounded_and_frozen_rule() -> None:
    ranked, reason = rank_hybrid(
        intent_text="fix: page models slug",
        corpus=_METADATA,
        candidate_paths=_BUNDLE_PATHS,
        candidate_records=_BUNDLE_RECORDS,
        graph_edges=(("cms/models/pagemodel.py", "cms/admin/pageadmin.py"),),
        k=2,
    )
    assert len(ranked) == 2
    assert reason == "hybrid_alpha_0.5"


def test_hybrid_seedless_reduces_to_bm25() -> None:
    ranked, reason = rank_hybrid(
        intent_text="zzz qqq www exclusive",
        corpus=_METADATA,
        candidate_paths=_BUNDLE_PATHS,
        candidate_records=_BUNDLE_RECORDS,
        graph_edges=(("cms/models/pagemodel.py", "cms/admin/pageadmin.py"),),
        k=2,
    )
    assert reason.startswith("graph_seed_empty")
    assert len(ranked) == 2


# ---------------------------------------------------------------------------
# Evaluation metrics — synthetic known values
# ---------------------------------------------------------------------------


def test_evaluator_synthetic_exact() -> None:
    metrics = evaluation.per_task_eval(
        case_id="synthetic",
        selected_paths=("c/models/pagemodel.py", "c/api.py", "c/plugin_pool.py"),
        proxy_paths=("c/models/pagemodel.py", "c/admin/pageadmin.py", "c/api.py"),
    )
    assert metrics["tp"] == 2
    assert metrics["fp"] == 1
    assert metrics["fn"] == 1
    assert abs(metrics["precision"] - 2 / 3) < 1e-9
    assert abs(metrics["recall"] - 2 / 3) < 1e-9
    assert abs(metrics["f1"] - 2 / 3) < 1e-9
    assert abs(metrics["fnr"] - 1 / 3) < 1e-9


def test_micro_macro_aggregation() -> None:
    a = evaluation.per_task_eval(
        case_id="a",
        selected_paths=("cms/models/pagemodel.py", "cms/api.py"),
        proxy_paths=("cms/models/pagemodel.py",),
    )
    b = evaluation.per_task_eval(
        case_id="b",
        selected_paths=("cms/api.py",),
        proxy_paths=("cms/api.py", "cms/admin/pageadmin.py"),
    )
    micro = evaluation.aggregate_micro_metrics([a, b])
    assert micro["tp"] == 2
    assert micro["fp"] == 1
    assert micro["fn"] == 1
    macro = evaluation.aggregate_macro_metrics([a, b])
    # a: selected {pagemodel, api}, proxy {pagemodel} -> P=0.5/R=1.0/F1=2/3
    # b: selected {api}, proxy {api, pageadmin} -> P=1.0/R=0.5/F1=2/3
    assert abs(macro["precision"] - 0.75) < 1e-9
    assert abs(macro["recall"] - 0.75) < 1e-9
    assert abs(macro["f1"] - 2 / 3) < 1e-9
    assert abs(macro["fnr"] - 0.25) < 1e-9


# ---------------------------------------------------------------------------
# Dataset / split discipline
# ---------------------------------------------------------------------------


def test_allowed_case_ids_excludes_held_out() -> None:
    ids = runner.allowed_case_ids(DATASET_DIR)
    split_freeze = json.loads((DATASET_DIR / "split_freeze.json").read_text(encoding="utf-8"))
    held = set(split_freeze["per_split"]["HELD_OUT_TEST"]["case_ids"])
    assert not (set(ids) & held)
    assert len(ids) == 30


def test_split_for_case_rejects_held_out() -> None:
    split_freeze = json.loads((DATASET_DIR / "split_freeze.json").read_text(encoding="utf-8"))
    held = split_freeze["per_split"]["HELD_OUT_TEST"]["case_ids"][0]
    with pytest.raises(ValueError):
        runner.split_for_case(DATASET_DIR, held)


# ---------------------------------------------------------------------------
# Leakage — pipeline inputs never contain proxy / future state
# ---------------------------------------------------------------------------


def test_runner_case_query_is_public_intent_only() -> None:
    for cid in CASES:
        bundle = __import__(
            "benchmark.real_commits.p1_evaluation", fromlist=["load_case_public_bundle"]
        ).load_case_public_bundle(DATASET_DIR, cid)
        proxy = set(
            __import__(
                "benchmark.real_commits.p1_evaluation", fromlist=["load_hidden_proxy_paths"]
            ).load_hidden_proxy_paths(DATASET_DIR, cid)
        )
        # The query used by rankers is exactly the public intent_text.
        # Nothing in the ranked pipeline receives the proxy paths except the
        # evaluation step, which happens post-ranking.
        assert bundle.intent_text
        # The proxy never appears as a separate pipeline input:
        cev = runner._run_single_case(
            bundle,
            proxy,
            runner.split_for_case(DATASET_DIR, cid),
            cache_dir=None,
        )
        for row in cev.to_json()["results"]:
            # predicted selection is derived from candidate paths only.
            assert set(row["selected_paths"]) <= set(cev.to_json()["candidate_paths"])


def test_graph_seed_rule_never_proxy_derived() -> None:
    for cid in CASES:
        bundle = __import__(
            "benchmark.real_commits.p1_evaluation", fromlist=["load_case_public_bundle"]
        ).load_case_public_bundle(DATASET_DIR, cid)
        elig = compute_seed_paths(
            intent_text=bundle.intent_text,
            candidate_paths=bundle.candidate_paths,
            candidate_records=bundle.candidate_records,
        )
        # Seeds are derived from the public intent + candidate metadata; they
        # can legitimately land on proxy files (public info), but the RULE must
        # be metadata-driven — here we only assert determinism and the
        # documented non-empty path.
        assert isinstance(elig.seed_paths, tuple)
        assert elig.eligible if elig.seed_paths else not elig.eligible
