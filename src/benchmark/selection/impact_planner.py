"""Stage-C structured Impact Planner + fail-closed safety gate (D047).

The planner turns visible requirements/acceptance/architecture constraints +
candidate artifacts + automatic evidence into an ``ImpactPlan`` with R/P/V/H
actions. It is deliberately hybrid:

- deterministic ``MockImpactPlanner`` for tests (no model calls);
- ``OpenRouterImpactPlanner`` for real acceptance/study runs (structured JSON
  through the existing OpenRouterBackend, same frozen scientific model as the
  executor).

The plan gate is fail-closed: it enforces every Stage-C invariant and applies
the frozen uncertainty rule (missing evidence or conflicting evidence for an R
proposal -> H; confidence < 0.60 -> H; never auto-promote P/V/H to R).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Protocol

from benchmark.core.enums import ActionKind
from benchmark.core.models import (
    ArtifactRef,
    ArtifactUniverse,
    EvidenceItem,
    ImpactDecision,
    ImpactPlan,
    LLMResponse,
    RequirementChange,
    SupportingEvidence,
    TokenUsage,
    ValidationObligation,
)

# Frozen uncertainty rule (Stage-C contract / D047)
MIN_CONFIDENCE: float = 0.60
PLANNER_VERSION: str = "scientific-wip-impactplan-v1-planner-1"


class ImpactPlanError(RuntimeError):
    """Raised when a planner output cannot be turned into a valid ImpactPlan."""


@dataclass(frozen=True)
class PlannerInput:
    requirement_change: RequirementChange
    artifact_universe: ArtifactUniverse
    evidence: tuple[EvidenceItem, ...]
    run_id: str
    scenario_id: str
    source_commit: str
    extra_architecture_constraints: tuple[str, ...] = ()
    prior_plan_summary: str | None = None
    parent_plan_hash: str | None = None
    plan_version: str = "v1"


@dataclass(frozen=True)
class PlanGateResult:
    plan: ImpactPlan
    violations: tuple[str, ...] = ()
    passed: bool = False

    def __post_init__(self) -> None:
        if self.passed and self.violations:
            raise ValueError("passed=True with non-empty violations")


# ---------------------------------------------------------------------------
# Invariant gate (fail-closed)
# ---------------------------------------------------------------------------

def _decision_action_map(plan: ImpactPlan) -> dict[str, ActionKind]:
    return {d.artifact.path: d.action for d in plan.decisions}


def compute_plan_hash(plan: ImpactPlan) -> str:
    payload = {
        "run_id": plan.run_id,
        "scenario_id": plan.scenario_id,
        "planner_version": plan.planner_version,
        "plan_version": plan.plan_version,
        "parent_plan_hash": plan.parent_plan_hash,
        "decisions": [
            {"path": d.artifact.path, "action": d.action.value}
            for d in plan.decisions
        ],
        "context_set": sorted(plan.context_set),
        "validation_obligations": [
            {"id": o.obligation_id, "kind": o.kind, "target": o.target}
            for o in plan.validation_obligations
        ],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def validate_impact_plan_invariants(
    plan: ImpactPlan,
    candidate_paths: tuple[str, ...],
) -> tuple[str, ...]:
    """Return every Stage-C invariant violation (empty == pass).

    Invariants (03_STAGE_C_IMPACTPLAN_CONTRACT.md):
    1. every candidate artifact classified exactly once;
    2. write_set == {action R};
    3. P/V/H are not writable (enforced structurally: write_set is R only);
    4. action sets pairwise disjoint;
    5. context_set independent of action sets;
    6. every R cites at least one strategy-visible evidence item;
    7. every V cites a validation/architecture reason;
    8. unknown paths rejected;
    9. hidden evaluator/gold cannot appear (checked by leakage tests, not here);
    10. plan persisted before first write (enforced by the runner);
    11. prohibited write attempts blocked (enforced by executor);
    12. planner cost counted (enforced by runner/strategy).
    """
    violations: list[str] = []
    candidate = set(candidate_paths)
    paths = {d.artifact.path for d in plan.decisions}

    # Invariant 8: unknown paths rejected
    unknown = sorted(paths - candidate)
    if unknown:
        violations.append(f"unknown_paths_in_plan: {unknown}")

    # Invariant 1: every candidate classified exactly once
    missing = sorted(candidate - paths)
    if missing:
        violations.append(f"candidate_not_classified: {missing}")
    duplicate = [p for p in candidate if list(paths).count(p) > 1]
    if duplicate:
        violations.append(f"candidate_duplicated: {sorted(set(duplicate))}")

    action_map = _decision_action_map(plan)

    # Invariant 2/4: write_set correctness + disjointness
    expected_write = {p for p, a in action_map.items() if a == ActionKind.regenerate}
    if set(plan.write_set) != expected_write:
        violations.append("write_set_mismatch: write_set != {R}")
    actual_sets = [
        set(plan.preserve_set),
        set(plan.validate_set),
        set(plan.human_review_set),
        expected_write,
    ]
    union: set[str] = set()
    for s in actual_sets:
        if union & s:
            violations.append("action_sets_not_disjoint")
        union |= s

    # Invariant 3: P/V/H are not writable
    for d in plan.decisions:
        if (
            d.action
            in (ActionKind.preserve, ActionKind.validate_only, ActionKind.human_review)
            and d.artifact.path in set(plan.write_set)
        ):
            violations.append(f"non_r_in_write_set: {d.artifact.path}")

    # Invariant 6: every R cites visible evidence
    for d in plan.decisions:
        if d.action == ActionKind.regenerate:
            cited = {s.source for s in d.supporting_evidence}
            if not cited:
                violations.append(f"r_missing_evidence: {d.artifact.path}")

    # Invariant 7: every V cites a validation/architecture reason
    for d in plan.decisions:
        if d.action == ActionKind.validate_only:
            cited = {s.source for s in d.supporting_evidence}
            if not cited:
                violations.append(f"v_missing_validation_reason: {d.artifact.path}")

    # Invariant 5: context_set need not equal any action set (orthogonality is
    # allowed by construction; we only reject context paths that are unknown).
    unknown_context = sorted(set(plan.context_set) - candidate)
    if unknown_context:
        violations.append(f"unknown_context_path: {unknown_context}")

    return tuple(dict.fromkeys(violations))


def apply_uncertainty_rule(plan: ImpactPlan) -> ImpactPlan:
    """Frozen WIP uncertainty rule.

    - R proposal with no cited evidence -> H;
    - R proposal with confidence < MIN_CONFIDENCE -> H;
    - any decision with confidence < MIN_CONFIDENCE -> H;
    - never auto-promote P/V/H to R.
    """
    new_decisions: list[ImpactDecision] = []
    for d in plan.decisions:
        action = d.action
        confident = d.confidence >= MIN_CONFIDENCE
        has_evidence = bool(d.supporting_evidence)
        if d.action == ActionKind.regenerate and (not confident or not has_evidence):
            action = ActionKind.human_review
            d = ImpactDecision(
                artifact=d.artifact,
                action=action,
                rationale=(
                    f"converted to H under frozen uncertainty rule "
                    f"(confidence={d.confidence}, evidence={has_evidence})"
                ),
                supporting_evidence=d.supporting_evidence,
                confidence=d.confidence,
                reason_codes=(*d.reason_codes, "uncertainty_rule"),
            )
        if action != ActionKind.human_review and not confident:
            action = ActionKind.human_review
            d = ImpactDecision(
                artifact=d.artifact,
                action=action,
                rationale=f"converted to H under frozen uncertainty rule (confidence={d.confidence})",
                supporting_evidence=d.supporting_evidence,
                confidence=d.confidence,
                reason_codes=(*d.reason_codes, "uncertainty_rule"),
            )
        new_decisions.append(d)
    return ImpactPlan(
        run_id=plan.run_id,
        scenario_id=plan.scenario_id,
        source_commit=plan.source_commit,
        planner_version=plan.planner_version,
        plan_version=plan.plan_version,
        parent_plan_hash=plan.parent_plan_hash,
        decisions=tuple(new_decisions),
        context_set=plan.context_set,
        validation_obligations=plan.validation_obligations,
        architecture_checks=plan.architecture_checks,
        escalation_reason=plan.escalation_reason,
        planner_token_usage=None if plan.planner_token_usage is None else plan.planner_token_usage,
        planner_model_calls=plan.planner_model_calls,
        planner_latency_seconds=plan.planner_latency_seconds,
        plan_hash=compute_plan_hash(plan),
    )


def gate_plan(
    plan: ImpactPlan, candidate_paths: tuple[str, ...],
) -> PlanGateResult:
    """Apply uncertainty rule then validate invariants; return fail-closed result."""
    safe = apply_uncertainty_rule(plan)
    if not safe.plan_hash:
        safe = replace(safe, plan_hash=compute_plan_hash(safe))
    violations = validate_impact_plan_invariants(safe, candidate_paths)
    return PlanGateResult(plan=safe, violations=violations, passed=not violations)


# ---------------------------------------------------------------------------
# Planner Protocol
# ---------------------------------------------------------------------------

class ImpactPlanner(Protocol):
    def plan(self, inp: PlannerInput) -> ImpactPlan: ...


    @property
    def token_usage(self) -> TokenUsage: ...


    @property
    def model_calls(self) -> int: ...

    @property
    def latency_seconds(self) -> float: ...


# ---------------------------------------------------------------------------
# Mock deterministic planner (tests + dry-run)
# ---------------------------------------------------------------------------

class MockImpactPlanner:
    """Deterministic planner for tests/dry-runs (no model calls).

    ``r_paths`` / ``v_paths`` behave like injected visible candidate evidence
    (never scenario gold). Everything else defaults to P. Used only in tests,
    dry-runs, and pipeline smoke.
    """

    def __init__(
        self,
        r_paths: frozenset[str] = frozenset(),
        v_paths: frozenset[str] = frozenset(),
    ) -> None:
        if not r_paths.isdisjoint(v_paths):
            raise ValueError("r_paths and v_paths must be disjoint")
        self._r_paths = frozenset(r_paths)
        self._v_paths = frozenset(v_paths)
        self._token_usage = TokenUsage(0, 0, 0)
        self._model_calls = 0
        self._latency = 0.0

    @property
    def token_usage(self) -> TokenUsage:
        return self._token_usage

    @property
    def model_calls(self) -> int:
        return self._model_calls

    @property
    def latency_seconds(self) -> float:
        return self._latency

    def plan(self, inp: PlannerInput) -> ImpactPlan:
        decisions: list[ImpactDecision] = []
        obligations: list[ValidationObligation] = []
        for idx, artifact in enumerate(inp.artifact_universe.artifacts):
            path = artifact.path
            evidence: tuple[SupportingEvidence, ...]
            if path in self._r_paths:
                action = ActionKind.regenerate
                evidence = (
                    SupportingEvidence(
                        description=f"mock-selected regenerate for {path}",
                        source="mock_planner_deterministic",
                    ),
                )
            elif path in self._v_paths:
                action = ActionKind.validate_only
                evidence = (
                    SupportingEvidence(
                        description="mock validate-only (linked to repository tests)",
                        source="mock_planner_validation",
                    ),
                )
                obligations.append(
                    ValidationObligation(
                        obligation_id=f"mock-obligation-{idx}",
                        kind="regression",
                        target=f"todo/tests/test_{Path(path).stem}.py",
                        reason="mock planner validation obligation",
                    )
                )
            else:
                action = ActionKind.preserve
                evidence = ()
            decisions.append(
                ImpactDecision(
                    artifact=artifact,
                    action=action,
                    rationale=f"mock planner: {action.value}",
                    supporting_evidence=evidence,
                    confidence=0.9,
                    reason_codes=("mock",),
                )
            )
        plan = ImpactPlan(
            run_id=inp.run_id,
            scenario_id=inp.scenario_id,
            source_commit=inp.source_commit,
            planner_version=PLANNER_VERSION,
            plan_version=inp.plan_version,
            parent_plan_hash=inp.parent_plan_hash,
            decisions=tuple(decisions),
            context_set=tuple(a.path for a in inp.artifact_universe.artifacts),
            validation_obligations=tuple(obligations),
            architecture_checks=tuple(inp.extra_architecture_constraints),
            escalation_reason="",
        )
        return replace(plan, plan_hash=compute_plan_hash(plan))


# ---------------------------------------------------------------------------
# Generic plan builder from a parsed JSON plan (both mock-free and real use)
# ---------------------------------------------------------------------------

def impact_plan_from_json(
    parsed: dict[str, Any],
    *,
    run_id: str,
    scenario_id: str,
    source_commit: str,
    planner_version: str,
    plan_version: str,
    parent_plan_hash: str | None,
    candidate_paths: tuple[str, ...],
    token_usage: TokenUsage | None = None,
    model_calls: int = 0,
    latency_seconds: float = 0.0,
) -> ImpactPlan:
    """Turn a planner's JSON representation into an ImpactPlan (structural only;
    invariants are enforced by :func:`gate_plan`)."""
    raw_decisions = parsed.get("decisions")
    if not isinstance(raw_decisions, list):
        raise ImpactPlanError("planner output missing 'decisions' list")
    action_map: dict[str, ActionKind] = {}
    try:
        for item in raw_decisions:
            if not isinstance(item, dict):
                raise ImpactPlanError("decision item is not an object")
            path = str(item.get("path") or "").strip()
            action_str = str(item.get("action") or "").strip().lower()
            action = ActionKind(action_str)
            if action not in (ActionKind.regenerate, ActionKind.preserve,
                              ActionKind.validate_only, ActionKind.human_review):
                raise ImpactPlanError(f"unknown action {action_str!r} for {path}")
            if not path:
                raise ImpactPlanError("decision has empty path")
            action_map[path] = action
    except (KeyError, TypeError, ValueError) as exc:
        raise ImpactPlanError(f"malformed decision: {exc}") from exc

    for path in candidate_paths:
        if path not in action_map:
            action_map[path] = ActionKind.preserve

    unknowns = [p for p in action_map if p not in set(candidate_paths)]
    if unknowns:
        raise ImpactPlanError(f"planner produced unknown paths: {sorted(unknowns)}")

    from benchmark.core.enums import ArtifactType
    from benchmark.core.models import ArtifactRef

    refs: dict[str, ArtifactRef] = {}
    for path in candidate_paths:
        refs[path] = ArtifactRef(path=path, artifact_type=ArtifactType.source)

    decisions = [
        ImpactDecision(
            artifact=refs[path],
            action=action_map[path],
            rationale=(
                _decision_rationale(parsed, path)
            ),
            supporting_evidence=_decision_evidence(parsed, path),
            confidence=_decision_confidence(parsed, path),
            reason_codes=tuple(_decision_reason_codes(parsed, path)),
        )
        for path in candidate_paths
    ]

    raw_obligations = parsed.get("validation_obligations", [])
    obligations: list[ValidationObligation] = []
    if isinstance(raw_obligations, list):
        for idx, ob in enumerate(raw_obligations):
            if isinstance(ob, dict):
                obligations.append(
                    ValidationObligation(
                        obligation_id=str(ob.get("obligation_id") or f"obligation-{idx}"),
                        kind=str(ob.get("kind") or "regression"),
                        target=str(ob.get("target") or ""),
                        reason=str(ob.get("reason") or ""),
                        evidence_refs=tuple(str(x) for x in (ob.get("evidence_refs") or [])),
                    )
                )

    plan = ImpactPlan(
        run_id=run_id,
        scenario_id=scenario_id,
        source_commit=source_commit,
        planner_version=planner_version,
        plan_version=plan_version,
        parent_plan_hash=parent_plan_hash,
        decisions=tuple(decisions),
        context_set=tuple(str(x) for x in (parsed.get("context_set") or [])),
        validation_obligations=tuple(obligations),
        architecture_checks=tuple(str(x) for x in (parsed.get("architecture_checks") or [])),
        escalation_reason=str(parsed.get("escalation_reason") or ""),
        planner_token_usage=token_usage,
        planner_model_calls=model_calls,
        planner_latency_seconds=latency_seconds,
    )
    return replace(plan, plan_hash=compute_plan_hash(plan))


def _decision_rationale(parsed: dict[str, Any], path: str) -> str:
    for item in parsed.get("decisions", []):
        if isinstance(item, dict) and item.get("path") == path:
            return str(item.get("rationale") or "planner decision")
    return "planner decision"


def _decision_evidence(parsed: dict[str, Any], path: str) -> tuple[SupportingEvidence, ...]:
    evidence: list[SupportingEvidence] = []
    for item in parsed.get("decisions", []):
        if isinstance(item, dict) and item.get("path") == path:
            raw = item.get("evidence") or []
            if isinstance(raw, list):
                for ev in raw:
                    if isinstance(ev, dict):
                        evidence.append(
                            SupportingEvidence(
                                description=str(ev.get("description") or ev.get("source") or "evidence"),
                                source=str(ev.get("source") or "planner"),
                            )
                        )
            break
    return tuple(evidence)


def _decision_confidence(parsed: dict[str, Any], path: str) -> float:
    for item in parsed.get("decisions", []):
        if isinstance(item, dict) and item.get("path") == path:
            conf = item.get("confidence")
            if isinstance(conf, (int, float)) and not isinstance(conf, bool):
                return max(0.0, min(1.0, float(conf)))
            return 0.6
    return 0.6


def _decision_reason_codes(parsed: dict[str, Any], path: str) -> list[str]:
    for item in parsed.get("decisions", []):
        if isinstance(item, dict) and item.get("path") == path:
            rc = item.get("reason_codes") or []
            return [str(x) for x in rc]
    return []


# ---------------------------------------------------------------------------
# OpenRouter structured planner (real acceptance/study)
# ---------------------------------------------------------------------------

PLANNER_PROMPT_TEMPLATE = """You are an impact planner for a software repository.

Frozen scenario ({scenario_id}):
Requirement before:
{before}

Requirement after:
{after}

Acceptance criteria (visible, must hold in the final repository):
{acceptance_criteria}

Visible architecture constraints (non-gold, must never be violated):
{architecture_constraints}

Candidate artifacts:
{candidates}

Strategy-visible evidence (you may cite these ids):
{evidence}

Validation catalog (permitted, repository-native):
{validation_catalog}

Prior plan failure summary (only during the one bounded expansion):
{prior_summary}

Output ONLY one JSON object conforming EXACTLY to this schema (no prose, no
markdown fences):

{{
  "decisions": [
    {{
      "path": "<candidate path>",
      "action": "REGENERATE" | "PRESERVE" | "VALIDATE_ONLY" | "HUMAN_REVIEW",
      "rationale": "<one sentence>",
      "evidence": [{{"source": "<evidence_id or visible source>", "description": "..."}}],
      "confidence": <float in [0,1]>,
      "reason_codes": ["<short code>"]
    }}
  ],
  "context_set": ["<candidate paths to read as context>"],
  "validation_obligations": [
    {{
      "obligation_id": "<id>",
      "kind": "changed_requirement" | "regression" | "build" | "static" | "architecture",
      "target": "<repository-native test module or check name>",
      "reason": "<why>",
      "evidence_refs": ["<evidence_id>"]
    }}
  ],
  "architecture_checks": ["<visible architecture obligation to verify>"],
  "escalation_reason": ""
}}

Rules:
- Classify EVERY candidate path exactly once.
- REGENERATE only when an edit is justified by the visible requirement and cited
  strategy-visible evidence.
- PRESERVE when no edit is justified.
- VALIDATE_ONLY when no edit is expected but the artifact is inside the
  validation boundary (cite a validation/test/architecture reason).
- HUMAN_REVIEW when evidence is insufficient, conflicting, or the scope is unsafe
  (do NOT confidently regenerate).
- NEVER invent paths outside the candidate list.
- context_set is independent of action; a PRESERVE file may still be context.
- Keep validation obligations separate from artifact actions.
"""


class OpenRouterImpactPlanner:
    """Structured model ImpactPlanner through the existing OpenRouter backend.

    Planner cost (calls/tokens/latency) is counted and exposed so the runner
    adds it to the proposed-arm total.
    """

    def __init__(self, backend: Any) -> None:
        self._backend = backend
        self._token_usage = TokenUsage(0, 0, 0)
        self._model_calls = 0
        self._latency = 0.0

    @property
    def token_usage(self) -> TokenUsage:
        return self._token_usage

    @property
    def model_calls(self) -> int:
        return self._model_calls

    @property
    def latency_seconds(self) -> float:
        return self._latency

    def _prompt(self, inp: PlannerInput) -> str:
        return PLANNER_PROMPT_TEMPLATE.format(
            scenario_id=inp.scenario_id,
            before=inp.requirement_change.before,
            after=inp.requirement_change.after,
            acceptance_criteria=(
                "\n".join(f"- {c}" for c in inp.requirement_change.acceptance_criteria)
                or "- (none declared)"
            ),
            architecture_constraints=(
                "\n".join(f"- {c}" for c in inp.extra_architecture_constraints)
                or "- (none declared)"
            ),
            candidates="\n".join(f"- {a.path}" for a in inp.artifact_universe.artifacts),
            evidence="\n".join(
                f"- [{e.evidence_id}] {e.evidence_type} {e.artifact_path} {e.direction}: {e.description}"
                for e in inp.evidence
            ) or "- (none)",
            validation_catalog="- (permitted repository-native test modules only)",
            prior_summary=inp.prior_plan_summary or "- (none)",
        )

    def plan(self, inp: PlannerInput) -> ImpactPlan:
        import time

        prompt = self._prompt(inp)
        start = time.monotonic()
        response = _generate(self._backend, prompt)
        elapsed = time.monotonic() - start
        self._model_calls += 1
        tu = response.token_usage
        if tu:
            self._token_usage = TokenUsage(
                prompt_tokens=self._token_usage.prompt_tokens + tu.prompt_tokens,
                completion_tokens=self._token_usage.completion_tokens + tu.completion_tokens,
                total_tokens=self._token_usage.total_tokens + tu.total_tokens,
            )
        self._latency += elapsed

        parsed: dict[str, Any]
        try:
            parsed = _extract_json_object(response.text)
        except (ValueError, json.JSONDecodeError) as exc:
            raise ImpactPlanError(f"planner response not JSON: {exc}") from exc

        candidate_paths = tuple(a.path for a in inp.artifact_universe.artifacts)
        return impact_plan_from_json(
            parsed,
            run_id=inp.run_id,
            scenario_id=inp.scenario_id,
            source_commit=inp.source_commit,
            planner_version=PLANNER_VERSION,
            plan_version=inp.plan_version,
            parent_plan_hash=inp.parent_plan_hash,
            candidate_paths=candidate_paths,
            token_usage=self._token_usage,
            model_calls=self._model_calls,
            latency_seconds=self._latency,
        )


def _generate(backend: Any, prompt: str) -> LLMResponse:
    import asyncio

    async def _run() -> LLMResponse:
        resp: Any = await backend.generate(prompt=prompt, temperature=0.0, max_tokens=2048)
        assert isinstance(resp, LLMResponse)
        return resp

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    result = loop.run_until_complete(_run())
    assert isinstance(result, LLMResponse)
    return result


def _extract_json_object(text: str) -> dict[str, Any]:
    import re

    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    candidate = fence.group(1).strip() if fence else text.strip()
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start < 0 or end < 0 or end <= start:
        raise ValueError("no JSON object found")
    parsed: Any = json.loads(candidate[start : end + 1])
    assert isinstance(parsed, dict)
    return parsed


# ---------------------------------------------------------------------------
# Persistence serialization for the persisted ImpactPlan evidence
# ---------------------------------------------------------------------------

def to_plan_dict(plan: ImpactPlan) -> dict[str, Any]:
    """Serialize an ImpactPlan to a JSON-able dict (persisted before first write)."""
    tu = plan.planner_token_usage
    return {
        "run_id": plan.run_id,
        "scenario_id": plan.scenario_id,
        "source_commit": plan.source_commit,
        "planner_version": plan.planner_version,
        "plan_version": plan.plan_version,
        "parent_plan_hash": plan.parent_plan_hash,
        "plan_hash": plan.plan_hash,
        "decisions": [
            {
                "path": d.artifact.path,
                "action": d.action.value,
                "rationale": d.rationale,
                "confidence": d.confidence,
                "reason_codes": list(d.reason_codes),
                "evidence": [
                    {"source": e.source, "description": e.description}
                    for e in d.supporting_evidence
                ],
            }
            for d in plan.decisions
        ],
        "write_set": list(plan.write_set),
        "preserve_set": list(plan.preserve_set),
        "validate_set": list(plan.validate_set),
        "human_review_set": list(plan.human_review_set),
        "context_set": list(plan.context_set),
        "validation_obligations": [
            {
                "obligation_id": o.obligation_id,
                "kind": o.kind,
                "target": o.target,
                "reason": o.reason,
                "evidence_refs": list(o.evidence_refs),
            }
            for o in plan.validation_obligations
        ],
        "architecture_checks": list(plan.architecture_checks),
        "escalation_reason": plan.escalation_reason,
        "planner_token_usage": (
            {
                "prompt_tokens": tu.prompt_tokens,
                "completion_tokens": tu.completion_tokens,
                "total_tokens": tu.total_tokens,
            }
            if tu is not None
            else None
        ),
        "planner_model_calls": plan.planner_model_calls,
        "planner_latency_seconds": plan.planner_latency_seconds,
    }


def load_plan_dict(payload: dict[str, Any]) -> ImpactPlan:
    """Rebuild an ImpactPlan from a persisted dict (evidence reconstruction)."""
    from benchmark.core.enums import ArtifactType
    from benchmark.core.models import ArtifactRef

    decisions: list[ImpactDecision] = []
    for item in payload.get("decisions", []):
        decisions.append(
            ImpactDecision(
                artifact=ArtifactRef(
                    path=item["path"], artifact_type=ArtifactType.source
                ),
                action=ActionKind(str(item["action"]).lower()),
                rationale=item.get("rationale", ""),
                supporting_evidence=tuple(
                    SupportingEvidence(description=e.get("description", ""), source=e.get("source", ""))
                    for e in item.get("evidence", [])
                ),
                confidence=float(item.get("confidence", 1.0)),
                reason_codes=tuple(item.get("reason_codes", [])),
            )
        )
    obligations = [
        ValidationObligation(
            obligation_id=o["obligation_id"],
            kind=o["kind"],
            target=o["target"],
            reason=o.get("reason", ""),
            evidence_refs=tuple(o.get("evidence_refs", [])),
        )
        for o in payload.get("validation_obligations", [])
    ]
    tu_raw = payload.get("planner_token_usage")
    tu = None
    if isinstance(tu_raw, dict):
        tu = TokenUsage(
            prompt_tokens=int(tu_raw.get("prompt_tokens", 0)),
            completion_tokens=int(tu_raw.get("completion_tokens", 0)),
            total_tokens=int(
                tu_raw.get(
                    "total_tokens",
                    int(tu_raw.get("prompt_tokens", 0)) + int(tu_raw.get("completion_tokens", 0)),
                )
            ),
        )
    plan = ImpactPlan(
        run_id=payload["run_id"],
        scenario_id=payload["scenario_id"],
        source_commit=payload["source_commit"],
        planner_version=payload["planner_version"],
        plan_version=payload["plan_version"],
        parent_plan_hash=payload.get("parent_plan_hash"),
        decisions=tuple(decisions),
        context_set=tuple(payload.get("context_set", [])),
        validation_obligations=tuple(obligations),
        architecture_checks=tuple(payload.get("architecture_checks", [])),
        escalation_reason=payload.get("escalation_reason", ""),
        plan_hash=payload.get("plan_hash", ""),
        planner_token_usage=tu,
        planner_model_calls=int(payload.get("planner_model_calls", 0)),
        planner_latency_seconds=float(payload.get("planner_latency_seconds", 0.0)),
    )
    return plan
