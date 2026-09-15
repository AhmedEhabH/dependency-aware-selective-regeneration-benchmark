"""Runner for the cheap non-LLM baseline protocol (TRAIN/VALIDATION only).

Deterministic, zero-LLM, zero-API. For each case:

1. Loads the frozen PUBLIC per-case bundle (intent, candidate universe,
   dependency graph) and the hidden proxy (evaluation-only).
2. Builds the parent-only corpus: metadata representation always; also
   parent-commit file content when ``cache_dir`` is provided.
3. Runs B0–B4 × K {1,3,5,10}, records per-task metrics and timings.

Only TRAIN and VALIDATION case ids are ever processed. HELD_OUT_TEST is
refused fail-closed. All outputs persist under ``research/cheap-baselines-v1/``.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from benchmark.real_commits import p1_evaluation as p1

from . import evaluation
from .bm25 import BM25Index
from .corpus import GitParentCorpus, MetadataCorpus
from .rankers import (
    BASELINES,
    K_VALUES,
    BaselineResult,
    bm25_scores,
    rank_bm25_from_index,
    rank_graph,
    rank_hybrid,
    rank_path_token,
    rank_random,
)

PROTOCOL_VERSION: str = "cheap-nonllm-baselines-v1"
PROTOCOL_SEED: int = 20260915

SPLITS_ALLOWED: tuple[str, ...] = ("TRAIN", "VALIDATION")


def _sha256_json(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class CaseEval:
    case_id: str
    split: str
    intent_text: str
    candidate_paths: tuple[str, ...]
    proxy_paths: tuple[str, ...]
    corpus_source: str
    config_hash: str
    by_baseline_k: dict[str, dict[int, BaselineResult]] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for baseline in BASELINES:
            for k in K_VALUES:
                result = self.by_baseline_k.get(baseline, {}).get(k)
                if result is None:
                    continue
                metrics = evaluation.per_task_eval(
                    case_id=self.case_id,
                    selected_paths=result.selected,
                    proxy_paths=self.proxy_paths,
                )
                rows.append(
                    {
                        "case_id": self.case_id,
                        "split": self.split,
                        "baseline": baseline,
                        "k": k,
                        "ranked_paths": list(result.ranked_paths),
                        "selected_paths": list(result.selected),
                        "seed_reason": result.metadata.get("seed_reason", ""),
                        "build_seconds": result.metadata.get("build_seconds", 0.0),
                        "query_seconds": result.metadata.get("query_seconds", 0.0),
                        "corpus_build_seconds": result.metadata.get(
                            "corpus_build_seconds", 0.0
                        ),
                        "corpus_source": result.metadata.get("corpus_source", self.corpus_source),
                        **metrics,
                    }
                )
        return {
            "case_id": self.case_id,
            "split": self.split,
            "intent_text": self.intent_text,
            "candidate_paths": list(self.candidate_paths),
            "proxy_paths": list(self.proxy_paths),
            "corpus_source": self.corpus_source,
            "config_hash": self.config_hash,
            "results": rows,
        }


def split_for_case(dataset_dir: Path, case_id: str) -> str:
    split_freeze = json.loads(
        (dataset_dir / "split_freeze.json").read_text(encoding="utf-8")
    )
    split = split_freeze.get("assignment", {}).get(case_id)
    if split not in SPLITS_ALLOWED:
        raise ValueError(
            f"case {case_id} is split {split!r}; only {SPLITS_ALLOWED} are allowed"
        )
    return str(split)


def allowed_case_ids(dataset_dir: Path) -> tuple[str, ...]:
    split_freeze = json.loads(
        (dataset_dir / "split_freeze.json").read_text(encoding="utf-8")
    )
    case_ids = sorted(
        cid
        for cid, split in split_freeze.get("assignment", {}).items()
        if split in SPLITS_ALLOWED
    )
    return tuple(case_ids)


def _run_single_case(
    bundle: p1.P1CaseBundle,
    proxy_paths: tuple[str, ...],
    split: str,
    cache_dir: Path | None,
) -> CaseEval:
    mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
    candidate_paths = mapping.paths()
    config_payload = {
        "protocol_version": PROTOCOL_VERSION,
        "seed": PROTOCOL_SEED,
        "case_id": bundle.case_id,
        "candidate_count": len(candidate_paths),
        "corpus_mode": "parent_commit" if cache_dir else "metadata",
    }
    config_hash = _sha256_json(config_payload)

    corpus_source = "metadata"
    corpus_build_seconds = 0.0
    if cache_dir is not None:
        build_start = time.perf_counter()
        corpus = GitParentCorpus(
            cache_dir=str(cache_dir),
            parent_commit=bundle.parent_commit,
            candidate_paths=candidate_paths,
        )
        corpus_source = corpus.source
        corpus_build_seconds = time.perf_counter() - build_start
    else:
        corpus = MetadataCorpus(
            parent_commit=bundle.parent_commit,
            candidate_records=bundle.candidate_records,
        )

    # Build the BM25 index ONCE per case; share across B1 and B4.
    index_build_t0 = time.perf_counter()
    index = BM25Index(corpus.texts)
    index_build_seconds = time.perf_counter() - index_build_t0
    bm25_scores_by_doc = bm25_scores(corpus, bundle.intent_text)

    case_eval = CaseEval(
        case_id=bundle.case_id,
        split=split,
        intent_text=bundle.intent_text,
        candidate_paths=candidate_paths,
        proxy_paths=proxy_paths,
        corpus_source=corpus_source,
        config_hash=config_hash,
    )

    for k in K_VALUES:
        # B0 Random@K
        t0 = time.perf_counter()
        ranked = rank_random(
            case_id=bundle.case_id,
            candidate_paths=candidate_paths,
            seed=PROTOCOL_SEED,
            k=k,
        )
        case_eval.by_baseline_k.setdefault("random", {})[k] = BaselineResult(
            baseline="random",
            case_id=bundle.case_id,
            k=k,
            ranked_paths=ranked,
            selected=ranked,
            metadata={
                "build_seconds": 0.0,
                "query_seconds": time.perf_counter() - t0,
                "corpus_source": "seed",
            },
        )

        # B1 BM25@K (build already done once per case; only query timing here)
        t0 = time.perf_counter()
        ranked = rank_bm25_from_index(index, intent_text=bundle.intent_text, k=k)
        query_seconds = time.perf_counter() - t0
        case_eval.by_baseline_k.setdefault("bm25", {})[k] = BaselineResult(
            baseline="bm25",
            case_id=bundle.case_id,
            k=k,
            ranked_paths=ranked,
            selected=ranked,
            metadata={
                "build_seconds": index_build_seconds,
                "query_seconds": query_seconds,
                "index_docs": index.n_docs,
                "corpus_source": corpus_source,
                "corpus_build_seconds": corpus_build_seconds,
            },
        )

        # B2 Path/identifier token@K
        t0 = time.perf_counter()
        ranked = rank_path_token(
            intent_text=bundle.intent_text,
            candidate_paths=candidate_paths,
            candidate_records=bundle.candidate_records,
            k=k,
        )
        case_eval.by_baseline_k.setdefault("path_token", {})[k] = BaselineResult(
            baseline="path_token",
            case_id=bundle.case_id,
            k=k,
            ranked_paths=ranked,
            selected=ranked,
            metadata={
                "build_seconds": 0.0,
                "query_seconds": time.perf_counter() - t0,
                "corpus_source": "metadata",
            },
        )

        # B3 Graph@K
        t0 = time.perf_counter()
        ranked, seeds, reason = rank_graph(
            intent_text=bundle.intent_text,
            candidate_paths=candidate_paths,
            candidate_records=bundle.candidate_records,
            graph_edges=bundle.graph_edges,
            k=k,
        )
        case_eval.by_baseline_k.setdefault("graph", {})[k] = BaselineResult(
            baseline="graph",
            case_id=bundle.case_id,
            k=k,
            ranked_paths=ranked,
            selected=ranked,
            metadata={
                "build_seconds": 0.0,
                "query_seconds": time.perf_counter() - t0,
                "corpus_source": "graph",
                "seed_paths": list(seeds),
                "seed_reason": reason,
            },
        )

        # B4 Hybrid@K
        t0 = time.perf_counter()
        ranked, reason = rank_hybrid(
            intent_text=bundle.intent_text,
            corpus=corpus,
            candidate_paths=candidate_paths,
            candidate_records=bundle.candidate_records,
            graph_edges=bundle.graph_edges,
            k=k,
            bm25_scores_by_doc=bm25_scores_by_doc,
        )
        case_eval.by_baseline_k.setdefault("hybrid", {})[k] = BaselineResult(
            baseline="hybrid",
            case_id=bundle.case_id,
            k=k,
            ranked_paths=ranked,
            selected=ranked,
            metadata={
                "build_seconds": index_build_seconds,
                "query_seconds": time.perf_counter() - t0,
                "corpus_source": corpus_source,
                "seed_reason": reason,
                "corpus_build_seconds": corpus_build_seconds,
            },
        )

    return case_eval


def run_baselines(
    *,
    dataset_dir: Path,
    cache_dir: Path | None,
) -> tuple[list[CaseEval], dict[str, Any]]:
    """Run B0–B4 × K over all TRAIN + VALIDATION cases.

    Returns (case_evals, protocol_manifest). Deterministic. Zero API.
    """
    case_ids = allowed_case_ids(dataset_dir)
    case_evals: list[CaseEval] = []
    for cid in case_ids:
        bundle = p1.load_case_public_bundle(dataset_dir, cid)
        proxy = p1.load_hidden_proxy_paths(dataset_dir, cid)
        split = split_for_case(dataset_dir, cid)
        print(f"  case {cid} split={split} candidates={len(bundle.candidate_paths)} proxy={len(proxy)}")
        case_evals.append(_run_single_case(bundle, proxy, split, cache_dir))

    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "seed": PROTOCOL_SEED,
        "splits_used": list(SPLITS_ALLOWED),
        "k_values": list(K_VALUES),
        "baselines": list(BASELINES),
        "corpus_mode": "parent_commit" if cache_dir else "metadata",
        "case_ids": list(case_ids),
        "case_count": len(case_ids),
        "evalutor_evaluator_version": evaluation.EVALUATOR_VERSION,
        "reference": "observed changed-production-Python proxy within U_t",
        "predicted_positive": "selected file (top-K ranked)",
        "zero_llm_calls": True,
        "zero_llm_tokens": True,
        "manifest_sha256": "",
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    manifest["manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return case_evals, manifest


def build_config_files(cache_dir: Path | None) -> dict[str, Any]:
    """Config file describing the frozen baseline configuration bundle."""
    return {
        "protocol_version": PROTOCOL_VERSION,
        "seed": PROTOCOL_SEED,
        "k_values": list(K_VALUES),
        "baselines": list(BASELINES),
        "baseline_definitions": {
            "B0_random": "deterministic seeded random ranking, matched K, seed=case_id-derived",
            "B1_bm25": "BM25(Okapi) over parent-commit candidate file text vs visible intent",
            "B2_path_token": "path/identifier/module/class/function token overlap vs intent",
            "B3_graph": "frozen parent-only dependency graph, seed=intent-token x candidate-token hits",
            "B4_hybrid": "alpha=0.5 frozen combination of normalized BM25 + normalized graph signal",
        },
        "seed_rule": "seed = candidate with intent-token ∩ candidate-token != empty (non-leaking); "
        "empty seed => document, no invented signal",
        "hybrid_rule": "score = 0.5*Nm(BM25) + 0.5*Ng(graph); Ng=(1+maxd-d)/(1+maxd) reachable else 0",
        "corpus_mode": "parent_commit" if cache_dir else "metadata",
        "reference": "observed changed-production-Python proxy within U_t (evaluation-only)",
        "evaluator_version": evaluation.EVALUATOR_VERSION,
        "efficiency_metrics": [
            "wall-clock_index_build_seconds",
            "wall-clock_query_seconds",
            "zero_llm_calls",
            "zero_llm_tokens",
        ],
        "exposes": {
            "HELD_OUT_TEST_tuning": "FORBIDDEN",
            "proxy_in_pipeline_input": "FORBIDDEN",
            "future_commit_state": "FORBIDDEN",
        },
    }
