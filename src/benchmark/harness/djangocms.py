"""djangoCMS adapter — dataset + parent snapshot + frozen B0–B4 ranker adapters.

This is the ONLY place django-specific rules live (repo identity, split policy
for the frozen RealCommitImpactDataset-v1, candidate universe semantics). It
delegates to the FROZEN loaders:

- ``benchmark.real_commits.p1_evaluation`` (public bundle / hidden proxy)
- ``benchmark.cheap_baselines.corpus`` (parent snapshot)
- ``benchmark.cheap_baselines.rankers`` (frozen B0–B4 rules)

Nothing in these frozen modules is rewritten; this adapter only presents them
through the harness seams.
"""

from __future__ import annotations

from dataclasses import field
from pathlib import Path
from typing import Any, ClassVar

from benchmark.cheap_baselines.bm25 import BM25Index
from benchmark.cheap_baselines.corpus import (
    CandidateCorpus,
    GitParentCorpus,
    MetadataCorpus,
)
from benchmark.cheap_baselines.rankers import (
    bm25_scores,
    rank_bm25_from_index,
    rank_graph,
    rank_hybrid,
    rank_path_token,
    rank_random,
)
from benchmark.real_commits import p1_evaluation as p1

from . import interfaces
from .registry import register_dataset, register_ranker, register_snapshot

DJANGOCMS_REPOSITORY: str = "djangocms"
DJANGOCMS_REPOSITORY_URL: str = "https://github.com/django-cms/django-cms"

FROZEN_SPLITS_ALLOWED: tuple[str, ...] = ("TRAIN", "VALIDATION")
FROZEN_HELD_OUT_SPLIT: str = "HELD_OUT_TEST"
FROZEN_SEED: int = 20260915


@register_dataset
class DjangoCMSRealCommitDataset(interfaces.DatasetAdapter):
    """RealCommitImpactDataset-v1 (djangoCMS) through the DatasetAdapter seam.

    STRICT DATA RULE: only TRAIN + VALIDATION may be processed. Any case
    assigned to HELD_OUT_TEST fails closed (split policy enforced twice: here
    and in :class:`~benchmark.harness.runner.HarnessRunner`).
    """

    name: ClassVar[str] = "djangocms-real-commit-v1"
    splits_allowed: ClassVar[tuple[str, ...]] = FROZEN_SPLITS_ALLOWED

    def __init__(self, dataset_dir: Path) -> None:
        self.dataset_dir = Path(dataset_dir)
        self._split_freeze: dict[str, Any] = {}
        self._case_ids: tuple[str, ...] | None = None

    def _load_split_freeze(self) -> dict[str, Any]:
        if not self._split_freeze:
            self._split_freeze = _json_load(self.dataset_dir / "split_freeze.json")
        return self._split_freeze

    def case_ids(self) -> tuple[str, ...]:
        if self._case_ids is None:
            freeze = self._load_split_freeze()
            self._case_ids = tuple(
                sorted(
                    cid
                    for cid, split in freeze.get("assignment", {}).items()
                    if split in self.splits_allowed
                )
            )
        return self._case_ids

    def split_of(self, case_id: str) -> str:
        freeze = self._load_split_freeze()
        split = freeze.get("assignment", {}).get(case_id)
        if split is None:
            raise KeyError(f"case {case_id} not in split_freeze.json")
        return str(split)

    def load_public_case(self, case_id: str) -> interfaces.PublicCase:
        bundle = p1.load_case_public_bundle(self.dataset_dir, case_id)
        return interfaces.PublicCase(
            case_id=bundle.case_id,
            repository=bundle.repository,
            repository_url=bundle.repository_url,
            parent_commit=bundle.parent_commit,
            target_commit=bundle.target_commit,
            intent_text=bundle.intent_text,
            candidate_paths=bundle.candidate_paths,
            candidate_records=bundle.candidate_records,
            graph_edges=bundle.graph_edges,
            public_bundle_sha256=bundle.public_bundle_sha256,
        )

    def load_hidden_proxy_paths(self, case_id: str) -> tuple[str, ...]:
        split = self.split_of(case_id)
        if split == FROZEN_HELD_OUT_SPLIT:
            raise interfaces.HiddenGoldAccessError(
                f"split policy: {case_id} is HELD_OUT_TEST and must never be "
                "processed by a method"
            )
        return p1.load_hidden_proxy_paths(self.dataset_dir, case_id)


@register_snapshot
class DjangoCMSParentSnapshot(interfaces.SnapshotProvider):
    """RepositoryView for djangoCMS: parent-commit snapshot for one case.

    ``mode="metadata"`` uses candidate metadata only (no git). ``mode="git"``
    materializes the parent tree from the frozen cache repo via
    :class:`~benchmark.cheap_baselines.corpus.GitParentCorpus`.
    """

    name: ClassVar[str] = "djangocms-parent-snapshot"

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None

    def snapshot(self, case: interfaces.PublicCase) -> interfaces.CandidateSnapshot:
        if self.cache_dir is None:
            corpus = MetadataCorpus(
                parent_commit=case.parent_commit,
                candidate_records=case.candidate_records,
            )
        else:
            corpus = GitParentCorpus(
                cache_dir=str(self.cache_dir),
                parent_commit=case.parent_commit,
                candidate_paths=case.candidate_paths,
            )
        return interfaces.CandidateSnapshot(
            source=corpus.source,
            parent_commit=corpus.parent_commit,
            texts=corpus.texts,
            sha256=corpus.sha256,
        )


# ---------------------------------------------------------------------------
# Frozen B0–B4 ranker adapters (delegate to frozen cheap_baselines rankers)
# ---------------------------------------------------------------------------


class _FrozenRankerBase(interfaces.Ranker):
    """Common machinery for frozen-baseline ranker adapters."""

    case_records: tuple[dict[str, Any], ...] = ()
    seed: int = FROZEN_SEED
    metadata: dict[str, Any] = field(default_factory=dict)

    def rank(
        self,
        *,
        case: interfaces.PublicCase,
        snapshot: interfaces.CandidateSnapshot | None,
        k: int,
    ) -> interfaces.RankedPrediction:
        return self._rank(case=case, snapshot=snapshot, k=k)

    def _rank(
        self,
        *,
        case: interfaces.PublicCase,
        snapshot: interfaces.CandidateSnapshot | None,
        k: int,
    ) -> interfaces.RankedPrediction:
        raise NotImplementedError


@register_ranker
class FrozenRandomRanker(_FrozenRankerBase):
    """B0 — deterministic seeded random ranking (frozen seed)."""

    name: ClassVar[str] = "random"

    def _rank(
        self,
        *,
        case: interfaces.PublicCase,
        snapshot: interfaces.CandidateSnapshot | None,
        k: int,
    ) -> interfaces.RankedPrediction:
        ranked = rank_random(
            case_id=case.case_id,
            candidate_paths=case.candidate_paths,
            seed=FROZEN_SEED,
            k=k,
        )
        return interfaces.RankedPrediction(
            method=self.name, case_id=case.case_id, k=k, ranked_paths=ranked
        )


@register_ranker
class FrozenBM25Ranker(_FrozenRankerBase):
    """B1 — BM25 over the parent-commit corpus (frozen k1/b/stopwords)."""

    name: ClassVar[str] = "bm25"

    def _rank(
        self,
        *,
        case: interfaces.PublicCase,
        snapshot: interfaces.CandidateSnapshot | None,
        k: int,
    ) -> interfaces.RankedPrediction:
        if snapshot is None:
            raise ValueError("bm25 ranker requires a parent snapshot")
        index = BM25Index(snapshot.texts)
        ranked = rank_bm25_from_index(index, intent_text=case.intent_text, k=k)
        return interfaces.RankedPrediction(
            method=self.name,
            case_id=case.case_id,
            k=k,
            ranked_paths=ranked,
            metadata={"index_docs": index.n_docs},
        )


@register_ranker
class FrozenPathTokenRanker(_FrozenRankerBase):
    """B2 — path/identifier token overlap (frozen)."""

    name: ClassVar[str] = "path_token"

    def _rank(
        self,
        *,
        case: interfaces.PublicCase,
        snapshot: interfaces.CandidateSnapshot | None,
        k: int,
    ) -> interfaces.RankedPrediction:
        ranked = rank_path_token(
            intent_text=case.intent_text,
            candidate_paths=case.candidate_paths,
            candidate_records=case.candidate_records,
            k=k,
        )
        return interfaces.RankedPrediction(
            method=self.name, case_id=case.case_id, k=k, ranked_paths=ranked
        )


@register_ranker
class FrozenGraphRanker(_FrozenRankerBase):
    """B3 — Graph@K from the frozen parent-only graph, seeded by intent hits."""

    name: ClassVar[str] = "graph"

    def _rank(
        self,
        *,
        case: interfaces.PublicCase,
        snapshot: interfaces.CandidateSnapshot | None,
        k: int,
    ) -> interfaces.RankedPrediction:
        ranked, seeds, reason = rank_graph(
            intent_text=case.intent_text,
            candidate_paths=case.candidate_paths,
            candidate_records=case.candidate_records,
            graph_edges=case.graph_edges,
            k=k,
        )
        return interfaces.RankedPrediction(
            method=self.name,
            case_id=case.case_id,
            k=k,
            ranked_paths=ranked,
            metadata={"seed_paths": list(seeds), "seed_reason": reason},
        )


@register_ranker
class FrozenHybridRanker(_FrozenRankerBase):
    """B4 — frozen alpha=0.5 Hybrid of normalized BM25 + graph signal."""

    name: ClassVar[str] = "hybrid"

    def _rank(
        self,
        *,
        case: interfaces.PublicCase,
        snapshot: interfaces.CandidateSnapshot | None,
        k: int,
    ) -> interfaces.RankedPrediction:
        if snapshot is None:
            raise ValueError("hybrid ranker requires a parent snapshot")
        corpus = CandidateCorpus(
            source=snapshot.source,
            parent_commit=snapshot.parent_commit,
            texts=snapshot.texts,
        )
        scores = bm25_scores(corpus, case.intent_text)
        ranked, reason = rank_hybrid(
            intent_text=case.intent_text,
            corpus=corpus,
            candidate_paths=case.candidate_paths,
            candidate_records=case.candidate_records,
            graph_edges=case.graph_edges,
            k=k,
            bm25_scores_by_doc=scores,
        )
        return interfaces.RankedPrediction(
            method=self.name,
            case_id=case.case_id,
            k=k,
            ranked_paths=ranked,
            metadata={"seed_reason": reason},
        )


def _json_load(path: Path) -> dict[str, Any]:
    import json

    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    assert isinstance(payload, dict)
    return payload
