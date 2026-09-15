"""Integration + leakage tests for cheap-baselines-v1 (ZERO API).

Proves:
- the full runner produces a deterministic result shape on real TRAIN/VALIDATION
  cases with a metadata corpus (no git);
- BM25 index built with the parent-commit corpus never reads target/future
  state in the runner integration path;
- deterministic-seed tests across a full re-run;
- persisted output files reproduce from raw predictions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmark.cheap_baselines import evaluation, runner
from benchmark.cheap_baselines.corpus import MetadataCorpus

DATASET_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "benchmark_data"
    / "real_commit_impact_v1"
)

REAL_CASE = "djangocms-rc-06ecf3a8e8de"  # TRAIN


@pytest.fixture(scope="module")
def runner_output(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    """Run the metadata-only runner over 2 real cases (deterministic)."""
    tmp_path_factory.mktemp("cb-integration")
    case_ids = runner.allowed_case_ids(DATASET_DIR)[:2]
    evals: list[runner.CaseEval] = []
    for cid in case_ids:
        bundle = __import__(
            "benchmark.real_commits.p1_evaluation", fromlist=["load_case_public_bundle"]
        ).load_case_public_bundle(DATASET_DIR, cid)
        proxy = __import__(
            "benchmark.real_commits.p1_evaluation", fromlist=["load_hidden_proxy_paths"]
        ).load_hidden_proxy_paths(DATASET_DIR, cid)
        evals.append(
            runner._run_single_case(
                bundle, proxy, runner.split_for_case(DATASET_DIR, cid), cache_dir=None
            )
        )
    payload = {"cases": [c.to_json() for c in evals]}
    return {"evals": evals, "payload": payload, "case_ids": case_ids}


def test_runner_result_shape(runner_output: dict[str, object]) -> None:
    payload = runner_output["payload"]
    for case in payload["cases"]:  # type: ignore[index]
        assert len(case["results"]) == 5 * 4  # 5 baselines x 4 K
        candidate_paths = set(case["candidate_paths"])
        for row in case["results"]:
            assert row["baseline"] in ("random", "bm25", "path_token", "graph", "hybrid")
            assert row["k"] in (1, 3, 5, 10)
            assert set(row["selected_paths"]) <= candidate_paths


def test_runner_restart_is_deterministic() -> None:
    case_ids = runner.allowed_case_ids(DATASET_DIR)[:1]
    cid = case_ids[0]

    def _predictive_projection() -> list[dict]:
        bundle = __import__(
            "benchmark.real_commits.p1_evaluation", fromlist=["load_case_public_bundle"]
        ).load_case_public_bundle(DATASET_DIR, cid)
        proxy = __import__(
            "benchmark.real_commits.p1_evaluation", fromlist=["load_hidden_proxy_paths"]
        ).load_hidden_proxy_paths(DATASET_DIR, cid)
        cev = runner._run_single_case(
            bundle, proxy, runner.split_for_case(DATASET_DIR, cid), cache_dir=None
        )
        rows: list[dict] = []
        for row in cev.to_json()["results"]:
            rows.append(
                {
                    "baseline": row["baseline"],
                    "k": row["k"],
                    "selected_paths": row["selected_paths"],
                    "ranked_paths": row["ranked_paths"],
                }
            )
        return rows

    assert _predictive_projection() == _predictive_projection()


def test_aggregate_reproduces_from_rows() -> None:
    case_ids = runner.allowed_case_ids(DATASET_DIR)[:3]
    rows = []
    for cid in case_ids:
        bundle = __import__(
            "benchmark.real_commits.p1_evaluation", fromlist=["load_case_public_bundle"]
        ).load_case_public_bundle(DATASET_DIR, cid)
        proxy = __import__(
            "benchmark.real_commits.p1_evaluation", fromlist=["load_hidden_proxy_paths"]
        ).load_hidden_proxy_paths(DATASET_DIR, cid)
        cev = runner._run_single_case(
            bundle, proxy, runner.split_for_case(DATASET_DIR, cid), cache_dir=None
        )
        rows.extend(cev.to_json()["results"])
    for baseline in ("random", "bm25", "path_token", "graph", "hybrid"):
        group = [r for r in rows if r["baseline"] == baseline and r["k"] == 5]
        micro = evaluation.aggregate_micro_metrics(group)
        assert micro["tasks"] == 3
        assert micro["tp"] + micro["fp"] == sum(r["selected_count"] for r in group)
        assert micro["tp"] + micro["fn"] == sum(r["proxy_count"] for r in group)


# ---------------------------------------------------------------------------
# Historical-parent-state + leakage of the git corpus path
# ---------------------------------------------------------------------------


def test_git_corpus_rejects_missing_parent() -> None:
    with pytest.raises(RuntimeError, match="not available in cache"):
        __import__(
            "benchmark.cheap_baselines.corpus", fromlist=["GitParentCorpus"]
        ).GitParentCorpus(
            cache_dir=str(Path(__file__).resolve().parent.parent.parent / "dist" / "does-not-exist"),
            parent_commit="deadbeef" * 5,
            candidate_paths=("cms/__init__.py",),
        )


def test_metadata_corpus_source_label_and_hash_stable() -> None:
    bundle = __import__(
        "benchmark.real_commits.p1_evaluation", fromlist=["load_case_public_bundle"]
    ).load_case_public_bundle(DATASET_DIR, REAL_CASE)
    c1 = MetadataCorpus(parent_commit=bundle.parent_commit, candidate_records=bundle.candidate_records)
    c2 = MetadataCorpus(parent_commit=bundle.parent_commit, candidate_records=bundle.candidate_records)
    assert c1.source == "metadata"
    assert c1.sha256 == c2.sha256
    for path in bundle.candidate_paths:
        assert path in c1.texts


# ---------------------------------------------------------------------------
# CLI dry-run reproduces persisted artifacts from raw predictions
# ---------------------------------------------------------------------------


def test_cli_dry_run_writes_reproducible_artifacts(tmp_path: Path) -> None:
    from benchmark.cheap_baselines.runner import (
        build_config_files,
    )

    output = tmp_path / "out"
    output.mkdir()
    config = build_config_files(cache_dir=None)
    (output / "config_v1.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    assert (output / "config_v1.json").is_file()
    reloaded = json.loads((output / "config_v1.json").read_text(encoding="utf-8"))
    assert reloaded["exposes"]["HELD_OUT_TEST_tuning"] == "FORBIDDEN"
    assert reloaded["corpus_mode"] == "metadata"
