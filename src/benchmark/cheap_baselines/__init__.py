"""Cheap non-LLM impact-selection baselines (Protocol A, post-ICCI block).

Zero-LLM-cost baseline family over RealCommitImpactDataset-v1
TRAIN 24 / VALIDATION 6:

- B0 Random@K          deterministic seeded random ranking, matched K
- B1 BM25@K            lexical BM25 over parent-commit candidate file text
- B2 Path/token@K      path/identifier token similarity (BM25-independent)
- B3 Graph@K           frozen per-case parent-only dependency graph, seeded by
                       intent-term hits against candidate metadata
- B4 Hybrid@K          frozen pre-validation combination of BM25 + graph signal

Evaluation uses the SAME frozen binary evaluator semantics as P1/P5
(``p1_selection_metrics``): predicted positive file = a selected file;
reference = the case's observed changed-production-Python proxy within U_t.

STRICT DATA RULE: TRAIN + VALIDATION only. HELD_OUT_TEST (10) is permanently
exposed and never used for tuning / threshold / K / feature selection.
T3 classification per docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md.
"""

from __future__ import annotations

from .corpus import (
    CandidateCorpus,
    GitParentCorpus,
    MetadataCorpus,
)
from .evaluation import (
    aggregate_macro_metrics,
    aggregate_micro_metrics,
    per_task_eval,
)
from .rankers import (
    BaselineResult,
    rank_bm25,
    rank_graph,
    rank_hybrid,
    rank_path_token,
    rank_random,
)

__all__ = [
    "BaselineResult",
    "CandidateCorpus",
    "GitParentCorpus",
    "MetadataCorpus",
    "aggregate_macro_metrics",
    "aggregate_micro_metrics",
    "per_task_eval",
    "rank_bm25",
    "rank_graph",
    "rank_hybrid",
    "rank_path_token",
    "rank_random",
]
