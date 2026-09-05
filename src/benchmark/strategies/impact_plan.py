"""Stage-C ImpactPlan Selective strategy (D047 / scientific-wip-impactplan-v1).

This is the proposed arm's treatment:
- collect strategy-visible evidence;
- produce a first-class persisted ImpactPlan (R/P/V/H over the candidate
  universe) via the configured Impact Planner;
- apply the fail-closed invariant + uncertainty gate;
- expose planner cost (calls/tokens/latency) so the runner adds it to the
  proposed-arm total.

NO scenario gold, NO hidden evaluator, NO result tables enter the planner.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from benchmark.core.models import (
    ArtifactUniverse,
    DependencyGraph,
    EvidenceItem,
    ImpactPlan,
    ImpactPrediction,
    RepositorySnapshot,
    RequirementChange,
    TokenUsage,
)
from benchmark.selection.dependency_scope import ArtifactDescriptor
from benchmark.selection.impact_evidence import collect_impact_evidence
from benchmark.selection.impact_planner import (
    ImpactPlanError,
    ImpactPlanner,
    MockImpactPlanner,
    PlannerInput,
    gate_plan,
)

logger = logging.getLogger(__name__)


class ImpactPlanSelectiveStrategy:
    """Proposed-arm Selective strategy driven by an explicit ImpactPlan."""

    def __init__(
        self,
        planner: ImpactPlanner | None = None,
        graph: DependencyGraph | None = None,
        artifact_descriptors: tuple[ArtifactDescriptor, ...] = (),
        extra_architecture_constraints: tuple[str, ...] = (),
    ) -> None:
        self._planner = planner or MockImpactPlanner()
        self._graph = graph or DependencyGraph()
        self._artifact_descriptors = artifact_descriptors
        self._extra_architecture_constraints = extra_architecture_constraints
        self._last_plan: ImpactPlan | None = None
        self._model_call_guard: Callable[[], bool] | None = None
        self._planner_guard_bound = False

    @property
    def last_plan(self) -> ImpactPlan | None:
        return self._last_plan

    def set_model_call_guard(self, guard: Callable[[], bool] | None) -> None:
        """Install cooperative deadline guard for the planner (real runs)."""
        self._model_call_guard = guard
        setter = getattr(self._planner, "set_model_call_guard", None)
        if callable(setter):
            setter(guard)

    def _evidence(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> tuple[EvidenceItem, ...]:
        return collect_impact_evidence(
            requirement_change,
            artifact_universe,
            self._artifact_descriptors,
            self._graph,
            workspace_root=repository.path,
            extra_architecture_constraints=self._extra_architecture_constraints,
        )

    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
        **kwargs: object,
    ) -> ImpactPrediction:
        evidence = self._evidence(repository, requirement_change, artifact_universe)
        inp = PlannerInput(
            requirement_change=requirement_change,
            artifact_universe=artifact_universe,
            evidence=evidence,
            run_id=f"{requirement_change.after[:32]}_{repository.commit_sha[:8]}",
            scenario_id=requirement_change.after[:64],
            source_commit=repository.commit_sha,
            extra_architecture_constraints=self._extra_architecture_constraints,
            plan_version="v1",
        )
        try:
            plan = self._planner.plan(inp)
        except ImpactPlanError as exc:
            logger.error("impact planner failed: %s", exc)
            return ImpactPrediction(
                decisions=(),
                errors=(f"impact_plan_planner_error: {exc}",),
                token_usage=self._planner_token_usage(),
                impact_plan=None,
            )

        gated = gate_plan(plan, tuple(a.path for a in artifact_universe.artifacts))
        if not gated.passed:
            logger.error("impact plan gate failed: %s", gated.violations)
            return ImpactPrediction(
                decisions=(),
                errors=(
                    "impact_plan_invariant_failure: " + "; ".join(gated.violations),
                ),
                token_usage=self._planner_token_usage(),
                impact_plan=gated.plan,
            )

        self._last_plan = gated.plan
        return ImpactPrediction(
            decisions=gated.plan.decisions,
            token_usage=self._planner_token_usage(),
            impact_plan=gated.plan,
        )

    def _planner_token_usage(self) -> TokenUsage:
        tu = getattr(self._planner, "token_usage", None)
        if isinstance(tu, TokenUsage):
            return tu
        return TokenUsage(0, 0, 0)

    def expand_plan(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
        *,
        failure_summary: str,
        parent_plan: ImpactPlan,
    ) -> ImpactPrediction:
        """One bounded evidence-driven expansion (v2)."""
        evidence = self._evidence(repository, requirement_change, artifact_universe)
        inp = PlannerInput(
            requirement_change=requirement_change,
            artifact_universe=artifact_universe,
            evidence=evidence,
            run_id=f"{requirement_change.after[:32]}_{repository.commit_sha[:8]}",
            scenario_id=requirement_change.after[:64],
            source_commit=repository.commit_sha,
            extra_architecture_constraints=self._extra_architecture_constraints,
            prior_plan_summary=failure_summary,
            parent_plan_hash=parent_plan.plan_hash,
            plan_version="v2",
        )
        try:
            plan = self._planner.plan(inp)
        except ImpactPlanError as exc:
            return ImpactPrediction(
                decisions=(),
                errors=(f"impact_plan_expansion_planner_error: {exc}",),
                token_usage=self._planner_token_usage(),
                impact_plan=None,
            )
        gated = gate_plan(plan, tuple(a.path for a in artifact_universe.artifacts))
        if not gated.passed:
            return ImpactPrediction(
                decisions=(),
                errors=("impact_plan_expansion_invariant_failure: " + "; ".join(gated.violations),),
                token_usage=self._planner_token_usage(),
                impact_plan=gated.plan,
            )
        self._last_plan = gated.plan
        return ImpactPrediction(
            decisions=gated.plan.decisions,
            token_usage=self._planner_token_usage(),
            impact_plan=gated.plan,
        )

    @property
    def model_call_count(self) -> int:
        return int(getattr(self._planner, "model_calls", 0))

    @property
    def prompt_tokens(self) -> int:
        return getattr(self._planner, "token_usage", TokenUsage()).prompt_tokens

    @property
    def completion_tokens(self) -> int:
        return getattr(self._planner, "token_usage", TokenUsage()).completion_tokens

    @property
    def total_tokens(self) -> int:
        tu = getattr(self._planner, "token_usage", TokenUsage())
        return tu.total_tokens
