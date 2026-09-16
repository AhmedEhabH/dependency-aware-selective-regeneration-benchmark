"""Budget enforcement tests for the harness (ZERO API).

Proves:
- a zero-LLM spec fails closed if any model call happens;
- a MockBackend with non-zero usage violates a zero-LLM budget;
- explicit call/token/cost/wallclock bounds raise BudgetExceededError;
- the budget is persisted in the ExperimentSpec.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.harness import interfaces
from benchmark.harness.backends import MockBackend, NoneBackend
from benchmark.harness.protocol_a import build_protocol_a_spec
from benchmark.harness.runner import HarnessRunner
from benchmark.harness.spec import ExperimentSpec

DATASET_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "benchmark_data"
    / "real_commit_impact_v1"
)


def test_none_backend_fails_closed_on_complete() -> None:
    backend = NoneBackend()
    with pytest.raises(interfaces.BudgetExceededError):
        backend.complete(prompt="x")


def test_mock_backend_records_usage() -> None:
    backend = MockBackend()
    backend.complete(prompt="x", estimated_tokens=10)
    assert backend.llm_calls == 1
    assert backend.llm_tokens == 10


def test_zero_llm_spec_rejects_mock_usage() -> None:
    spec = build_protocol_a_spec(method_name="random", corpus_mode="metadata")
    assert spec.budget.zero_llm is True
    backend = MockBackend()
    backend.complete(prompt="x")
    with pytest.raises(interfaces.BudgetExceededError):
        spec.budget.check_llm(calls=backend.llm_calls, tokens=backend.llm_tokens)


def test_spec_persists_budget() -> None:
    spec = build_protocol_a_spec(method_name="bm25", corpus_mode="metadata")
    restored = ExperimentSpec.from_dict(spec.to_dict())
    assert restored.budget == spec.budget
    assert restored.budget.zero_llm is True


def test_wallclock_budget_enforced() -> None:
    from benchmark.harness import registry
    from benchmark.harness.djangocms import DjangoCMSParentSnapshot

    class _TinyDataset(interfaces.DatasetAdapter):
        name = "tiny"
        splits_allowed = ("TRAIN",)

        def case_ids(self) -> tuple[str, ...]:
            return ("tiny-case",)

        def split_of(self, case_id: str) -> str:
            return "TRAIN"

        def load_public_case(self, case_id: str) -> interfaces.PublicCase:
            return interfaces.PublicCase(
                case_id="tiny-case",
                repository="tiny",
                repository_url="",
                parent_commit="p" * 40,
                target_commit="t" * 40,
                intent_text="fix: page slug",
                candidate_paths=("a.py", "b.py", "c.py"),
                candidate_records=(),
                graph_edges=(),
                public_bundle_sha256="x",
            )

        def load_hidden_proxy_paths(self, case_id: str) -> tuple[str, ...]:
            return ("a.py",)

    spec = ExperimentSpec(
        spec_id="tiny",
        protocol_version="tiny-v1",
        dataset_name="tiny",
        repository="tiny",
        method_name="random",
        model_name="",
        provider="none",
        k_values=(1,),
        splits_allowed=("TRAIN",),
        seed=1,
        budget=interfaces.BudgetPolicy(
            zero_llm=True, max_wallclock_seconds=-1.0
        ),
    )
    runner = HarnessRunner(
        spec=spec,
        dataset=_TinyDataset(),
        snapshot_provider=DjangoCMSParentSnapshot(cache_dir=None),
        ranker=registry.resolve_ranker("random")(),
    )
    with pytest.raises(interfaces.BudgetExceededError):
        runner.run()
