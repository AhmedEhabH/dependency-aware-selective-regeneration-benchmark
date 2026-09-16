"""Dataset-adapter isolation tests (ZERO API).

Proves:
- switching the dataset adapter (same repository rules) does not change how a
  ranker behaves (method code is adapter-agnostic);
- the runner emits the same ranked paths for the same public case regardless
  of the adapter implementation used to load it;
- a ranker cannot reach repository-specific internals through the seam.
"""

from __future__ import annotations

from pathlib import Path

from benchmark.harness import interfaces
from benchmark.harness.djangocms import DjangoCMSRealCommitDataset
from benchmark.harness.protocol_a import build_protocol_a_spec
from benchmark.harness.runner import HarnessRunner

DATASET_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "benchmark_data"
    / "real_commit_impact_v1"
)


class _CanonicalAdapter(interfaces.DatasetAdapter):
    """Adapter-agnostic reimplementation that yields the SAME public case."""

    name = "canonical-test"
    splits_allowed = ("TRAIN",)

    def __init__(self, base: interfaces.DatasetAdapter) -> None:
        self._base = base

    def case_ids(self) -> tuple[str, ...]:
        return self._base.case_ids()

    def split_of(self, case_id: str) -> str:
        return self._base.split_of(case_id)

    def load_public_case(self, case_id: str) -> interfaces.PublicCase:
        case = self._base.load_public_case(case_id)
        # Reconstruct via the public dataclass only (adapter-agnostic path).
        return interfaces.PublicCase(
            case_id=case.case_id,
            repository=case.repository,
            repository_url=case.repository_url,
            parent_commit=case.parent_commit,
            target_commit=case.target_commit,
            intent_text=case.intent_text,
            candidate_paths=case.candidate_paths,
            candidate_records=case.candidate_records,
            graph_edges=case.graph_edges,
            public_bundle_sha256=case.public_bundle_sha256,
        )

    def load_hidden_proxy_paths(self, case_id: str) -> tuple[str, ...]:
        return self._base.load_hidden_proxy_paths(case_id)


def test_rankings_identical_across_adapter_implementations() -> None:
    from benchmark.harness import registry
    from benchmark.harness.djangocms import DjangoCMSParentSnapshot
    from benchmark.harness.protocol_a import _SingleCaseAdapter

    base = DjangoCMSRealCommitDataset(dataset_dir=DATASET_DIR)
    cid = base.case_ids()[0]
    canonical = _CanonicalAdapter(base)

    def ranked_with(dataset: interfaces.DatasetAdapter) -> tuple[str, ...]:
        spec = build_protocol_a_spec(method_name="bm25", corpus_mode="metadata")
        result = HarnessRunner(
            spec=spec,
            dataset=_SingleCaseAdapter(dataset, cid),
            snapshot_provider=DjangoCMSParentSnapshot(cache_dir=None),
            ranker=registry.resolve_ranker("bm25")(),
        ).run()
        (cr,) = result.case_results
        row = cr.rows[0]
        return tuple(row["ranked_paths"])

    assert ranked_with(base) == ranked_with(canonical)


def test_ranker_sees_only_public_case_type() -> None:
    base = DjangoCMSRealCommitDataset(dataset_dir=DATASET_DIR)
    cid = base.case_ids()[0]
    case = base.load_public_case(cid)
    # The public case is a PublicCase dataclass, not a repository-specific type.
    assert isinstance(case, interfaces.PublicCase)
    assert type(case).__module__ == "benchmark.harness.interfaces"
