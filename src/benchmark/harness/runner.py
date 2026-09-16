"""Generic harness runner (V1).

Drives one :class:`~benchmark.harness.spec.ExperimentSpec` through the seams:

    DatasetAdapter.load_public_case(case)
        -> SnapshotProvider.snapshot(case)          (optional)
        -> Ranker.rank(case, snapshot, k)           (or Planner.plan)
        -> common evaluator vs hidden proxy         (evaluation-only)

Enforced invariants:

- Split policy: only the spec's ``splits_allowed`` are processed; anything else
  (e.g. HELD_OUT_TEST) fails closed.
- Hidden gold barrier: the proxy is loaded by the adapter and passed ONLY to
  the evaluator, never to method code.
- Budget: the spec budget is checked before/after each case; zero-LLM specs
  fail on any model call.
- Determinism: rankers are deterministic given the frozen seed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from . import interfaces, registry
from .evaluator import COMMON_EVALUATOR_VERSION, evaluate_prediction
from .spec import ExperimentSpec


@dataclass
class HarnessCaseResult:
    """Per-case harness result (all K values for one method)."""

    case_id: str
    split: str
    intent_text: str
    candidate_paths: tuple[str, ...]
    proxy_paths: tuple[str, ...]
    corpus_source: str
    spec_sha256: str
    rows: list[dict[str, Any]] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "split": self.split,
            "intent_text": self.intent_text,
            "candidate_paths": list(self.candidate_paths),
            "proxy_paths": list(self.proxy_paths),
            "corpus_source": self.corpus_source,
            "spec_sha256": self.spec_sha256,
            "results": self.rows,
        }


@dataclass
class HarnessRunResult:
    """Aggregate harness run output."""

    spec: ExperimentSpec
    case_results: list[HarnessCaseResult]
    manifest: dict[str, Any] = field(default_factory=dict)


class HarnessRunner:
    """Runs one experiment spec through the registered implementations."""

    def __init__(
        self,
        *,
        spec: ExperimentSpec,
        dataset: interfaces.DatasetAdapter,
        snapshot_provider: interfaces.SnapshotProvider | None = None,
        ranker: interfaces.Ranker | None = None,
        planner: interfaces.Planner | None = None,
        backend: interfaces.ModelBackend | None = None,
    ) -> None:
        if ranker is None and planner is None:
            raise ValueError("harness runner requires a ranker or a planner")
        if ranker is not None and planner is not None:
            raise ValueError("harness runner accepts one of ranker/planner, not both")
        if backend is None:
            backend = registry.resolve_backend("none")()
        self.spec = spec
        self.dataset = dataset
        self.snapshot_provider = snapshot_provider
        self.ranker = ranker
        self.planner = planner
        self.backend = backend

    def run(self) -> HarnessRunResult:
        """Run the spec over all allowed cases. Zero scientific API calls."""
        case_ids = self.dataset.case_ids()
        spec_budget = self.spec.budget
        case_results: list[HarnessCaseResult] = []
        total_rows = 0
        t_start = time.perf_counter()

        for cid in case_ids:
            split = self.dataset.split_of(cid)
            if split not in self.spec.splits_allowed:
                raise interfaces.HiddenGoldAccessError(
                    f"split policy: case {cid} is {split!r}; spec allows only "
                    f"{self.spec.splits_allowed}"
                )
            case = self.dataset.load_public_case(cid)
            snapshot = (
                self.snapshot_provider.snapshot(case)
                if self.snapshot_provider is not None
                else None
            )

            rows: list[dict[str, Any]] = []
            for k in self.spec.k_values:
                if self.ranker is not None:
                    prediction = self.ranker.rank(
                        case=case, snapshot=snapshot, k=k
                    )
                else:
                    assert self.planner is not None
                    plan = self.planner.plan(case=case, snapshot=snapshot)
                    prediction = interfaces.RankedPrediction(
                        method=plan.method,
                        case_id=plan.case_id,
                        k=k,
                        ranked_paths=plan.selected_paths,
                        metadata=plan.metadata,
                    )
                # Budget check happens BEFORE scoring (LLM usage, if any).
                spec_budget.check_llm(
                    calls=self.backend.llm_calls,
                    tokens=self.backend.llm_tokens,
                )
                # Hidden proxy is loaded ONLY here, for scoring.
                proxy = self.dataset.load_hidden_proxy_paths(cid)
                row = evaluate_prediction(
                    prediction=prediction, proxy_paths=proxy
                )
                row["ranked_paths"] = list(prediction.ranked_paths)
                row["selected_paths"] = list(prediction.selected_paths)
                row["metadata"] = dict(prediction.metadata)
                rows.append(row)
                total_rows += 1

            case_results.append(
                HarnessCaseResult(
                    case_id=cid,
                    split=split,
                    intent_text=case.intent_text,
                    candidate_paths=case.candidate_paths,
                    proxy_paths=tuple(
                        sorted(set(self.dataset.load_hidden_proxy_paths(cid)))
                    ),
                    corpus_source=snapshot.source if snapshot is not None else "none",
                    spec_sha256=self.spec.sha256,
                    rows=rows,
                )
            )

        elapsed = time.perf_counter() - t_start
        spec_budget.check_llm(
            calls=self.backend.llm_calls,
            tokens=self.backend.llm_tokens,
        )
        if (
            spec_budget.max_wallclock_seconds is not None
            and elapsed > spec_budget.max_wallclock_seconds
        ):
            raise interfaces.BudgetExceededError(
                f"wallclock budget exceeded: {elapsed:.1f}s > "
                f"{spec_budget.max_wallclock_seconds}s"
            )

        manifest = {
            "spec_id": self.spec.spec_id,
            "spec_sha256": self.spec.sha256,
            "protocol_version": self.spec.protocol_version,
            "dataset_name": self.spec.dataset_name,
            "repository": self.spec.repository,
            "method_name": self.spec.method_name,
            "model_name": self.spec.model_name,
            "provider": self.spec.provider,
            "splits_allowed": list(self.spec.splits_allowed),
            "k_values": list(self.spec.k_values),
            "case_ids": case_ids,
            "case_count": len(case_ids),
            "row_count": total_rows,
            "evaluator_version": COMMON_EVALUATOR_VERSION,
            "zero_llm_calls": True if self.spec.budget.zero_llm else self.backend.llm_calls == 0,
            "llm_calls": self.backend.llm_calls,
            "llm_tokens": self.backend.llm_tokens,
            "wallclock_seconds": round(elapsed, 6),
        }
        return HarnessRunResult(spec=self.spec, case_results=case_results, manifest=manifest)
