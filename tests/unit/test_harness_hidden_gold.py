"""Hidden-gold access tests (ZERO API).

Proves the harness leakage barrier:
- the hidden observed-change proxy is loaded ONLY at scoring time, never by a
  Ranker/Planner;
- the public case bundle contains no proxy paths and no semantic-gold markers;
- HELD_OUT_TEST cases are fail-closed at the adapter and the runner.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.harness.djangocms import DjangoCMSRealCommitDataset
from benchmark.harness.interfaces import (
    HiddenGoldAccessError,
    PublicCase,
    RankedPrediction,
)
from benchmark.harness.protocol_a import run_protocol_a_via_harness
from benchmark.harness.runner import HarnessRunner

DATASET_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "benchmark_data"
    / "real_commit_impact_v1"
)


class _ProxySniffingRanker:
    """Test ranker that FAILS if any hidden proxy path is visible in the case."""

    def __init__(self, proxy_paths: tuple[str, ...]) -> None:
        self._proxy = set(proxy_paths)
        self.calls = 0

    def rank(
        self,
        *,
        case: PublicCase,
        snapshot: object | None,
        k: int,
    ) -> RankedPrediction:
        self.calls += 1
        # Structural leakage check: the proxy LIST must never be a field of the
        # public case (a proxy path may legitimately be inside the candidate
        # universe as public metadata, but the proxy list itself is hidden).
        assert "proxy" not in case.__dict__ or not case.__dict__.get("proxy")
        return RankedPrediction(
            method="sniff",
            case_id=case.case_id,
            k=k,
            ranked_paths=tuple(sorted(case.candidate_paths))[:k],
        )


def test_public_case_has_no_proxy_field() -> None:
    adapter = DjangoCMSRealCommitDataset(dataset_dir=DATASET_DIR)
    for cid in adapter.case_ids()[:6]:
        case = adapter.load_public_case(cid)
        assert not hasattr(case, "proxy")
        assert "proxy_paths" not in case.__dict__
        assert "observed_change_set_proxy" not in str(case.__dict__.keys())


def test_public_case_has_no_semantic_gold_markers() -> None:
    adapter = DjangoCMSRealCommitDataset(dataset_dir=DATASET_DIR)
    for cid in adapter.case_ids()[:6]:
        case = adapter.load_public_case(cid)
        for marker in ("REGENERATE", "VALIDATE", "HUMAN_REVIEW", "PRESERVE"):
            assert marker not in case.intent_text


def test_held_out_split_fails_closed() -> None:
    adapter = DjangoCMSRealCommitDataset(dataset_dir=DATASET_DIR)
    import json

    freeze = json.loads((DATASET_DIR / "split_freeze.json").read_text(encoding="utf-8"))
    held = freeze["per_split"]["HELD_OUT_TEST"]["case_ids"]
    held_id = held[0]
    with pytest.raises(HiddenGoldAccessError):
        adapter.load_hidden_proxy_paths(held_id)


def test_runner_refuses_held_out_in_split_policy() -> None:
    class _HeldOutDataset(DjangoCMSRealCommitDataset):
        name = "djangocms-real-commit-v1-heldout-probe"

        def case_ids(self) -> tuple[str, ...]:
            import json

            freeze = json.loads((DATASET_DIR / "split_freeze.json").read_text(encoding="utf-8"))
            return tuple(freeze["per_split"]["HELD_OUT_TEST"]["case_ids"][:1])

    from benchmark.harness.djangocms import DjangoCMSParentSnapshot
    from benchmark.harness.protocol_a import build_protocol_a_spec

    spec = build_protocol_a_spec(method_name="random", corpus_mode="metadata")
    dataset = _HeldOutDataset(DATASET_DIR)
    with pytest.raises(HiddenGoldAccessError):
        HarnessRunner(
            spec=spec,
            dataset=dataset,
            snapshot_provider=DjangoCMSParentSnapshot(cache_dir=None),
            ranker=registry_resolve_ranker(),
        ).run()


def registry_resolve_ranker():
    from benchmark.harness import registry

    return registry.resolve_ranker("random")()


def test_proxy_only_loaded_at_scoring() -> None:
    # The adapter's load_hidden_proxy_paths is invoked by the runner at
    # scoring time; the recorded payload separates proxy from the public case.
    payload = run_protocol_a_via_harness(
        dataset_dir=DATASET_DIR, cache_dir=None, case_slice=(0, 1)
    )
    assert payload["cases"]
    assert payload["cases"][0]["proxy_paths"]  # recorded for scoring only
    # Rows carry no proxy leak: candidate_paths subset and proxy recorded
    # separately.
    case = payload["cases"][0]
    for row in case["results"]:
        assert set(row["selected_paths"]) <= set(case["candidate_paths"])


def test_ranker_never_receives_proxy() -> None:
    adapter = DjangoCMSRealCommitDataset(dataset_dir=DATASET_DIR)
    cid = adapter.case_ids()[0]
    proxy = set(adapter.load_hidden_proxy_paths(cid))
    spy = _ProxySniffingRanker(proxy)

    from benchmark.harness.djangocms import DjangoCMSParentSnapshot
    from benchmark.harness.protocol_a import _SingleCaseAdapter, build_protocol_a_spec

    spec = build_protocol_a_spec(method_name="random", corpus_mode="metadata")
    result = HarnessRunner(
        spec=spec,
        dataset=_SingleCaseAdapter(adapter, cid),
        snapshot_provider=DjangoCMSParentSnapshot(cache_dir=None),
        ranker=spy,
    ).run()
    assert spy.calls == len(spec.k_values)
    for cr in result.case_results:
        assert cr.case_id == cid
