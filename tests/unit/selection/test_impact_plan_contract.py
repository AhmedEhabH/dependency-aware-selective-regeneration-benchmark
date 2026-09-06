from __future__ import annotations

import pytest

from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import (
    ArtifactRef,
    ArtifactUniverse,
    ImpactDecision,
    ImpactPlan,
    RequirementChange,
    SupportingEvidence,
    ValidationObligation,
)
from benchmark.selection.impact_planner import (
    MIN_CONFIDENCE,
    MockImpactPlanner,
    PlannerInput,
    apply_uncertainty_rule,
    compute_plan_hash,
    gate_plan,
    to_plan_dict,
    validate_impact_plan_invariants,
)

_CANDIDATES = (
    "todo/models.py",
    "todo/serializers.py",
    "todo/views.py",
    "todo/permissions.py",
    "todo/urls.py",
)


def _universe(paths=_CANDIDATES) -> ArtifactUniverse:
    return ArtifactUniverse(
        artifacts=tuple(
            ArtifactRef(path=p, artifact_type=ArtifactType.source) for p in paths
        )
    )


def _requirement() -> RequirementChange:
    return RequirementChange(
        before="Task has no priority",
        after="Task gains Priority with HIGH, MEDIUM, LOW",
        acceptance_criteria=("TaskSerializer exposes priority",),
    )


def _decision(path: str, action: ActionKind, *, evidence: bool = True, confidence: float = 0.9) -> ImpactDecision:
    return ImpactDecision(
        artifact=ArtifactRef(path=path, artifact_type=ArtifactType.source),
        action=action,
        rationale=f"{action.value} for {path}",
        supporting_evidence=(
            (SupportingEvidence(description="dep graph", source="static-graph-edge-0"),)
            if evidence
            else ()
        ),
        confidence=confidence,
        reason_codes=("test",),
    )


def _plan_for(actions: dict[str, ActionKind], **kw) -> ImpactPlan:
    paths = list(_CANDIDATES)
    decisions = tuple(
        _decision(p, actions.get(p, ActionKind.preserve)) for p in paths
    )
    plan = ImpactPlan(
        run_id="r1",
        scenario_id="todo-smoke-001",
        source_commit="abc123",
        planner_version="v1",
        plan_version="v1",
        decisions=decisions,
        context_set=tuple(paths),
        validation_obligations=(
            ValidationObligation(
                obligation_id="o1", kind="regression", target="todo/tests/test_models.py",
            ),
        ),
        architecture_checks=("single app",),
    )
    return ImpactPlan(**{**plan.__dict__, "plan_hash": compute_plan_hash(plan), **kw})


class TestImpactPlanSchemaRoundtrip:
    def test_serialize_roundtrip_preserves_core_fields(self) -> None:
        plan = _plan_for({"todo/models.py": ActionKind.regenerate})
        payload = to_plan_dict(plan)
        assert payload["write_set"] == ["todo/models.py"]
        assert payload["plan_hash"] == plan.plan_hash
        assert payload["planner_version"] == "v1"
        assert payload["validation_obligations"][0]["target"] == "todo/tests/test_models.py"


class TestEveryCandidateClassifiedExactlyOnce:
    def test_all_five_classified_in_plan(self) -> None:
        plan = _plan_for({"todo/models.py": ActionKind.regenerate})
        paths = {d.artifact.path for d in plan.decisions}
        assert paths == set(_CANDIDATES)

    def test_missing_classification_detected_by_gate(self) -> None:
        partial = _plan_for({"todo/models.py": ActionKind.regenerate})
        # Remove views from decisions -> gate must flag candidate_not_classified
        kept = [d for d in partial.decisions if d.artifact.path != "todo/views.py"]
        bad = ImpactPlan(**{**partial.__dict__, "decisions": tuple(kept)})
        violations = validate_impact_plan_invariants(bad, _CANDIDATES)
        assert any("candidate_not_classified" in v for v in violations)


class TestWriteSetEqualsR:
    def test_write_set_only_regenerate(self) -> None:
        plan = _plan_for({
            "todo/models.py": ActionKind.regenerate,
            "todo/serializers.py": ActionKind.regenerate,
            "todo/views.py": ActionKind.preserve,
        })
        assert set(plan.write_set) == {"todo/models.py", "todo/serializers.py"}
        assert "todo/views.py" not in plan.write_set

    def test_write_set_consistent_with_r_decisions(self) -> None:
        """write_set is a derived property == {paths with action R}.

        The invariant is enforced by construction; the gate re-validates it."""
        plan = _plan_for({
            "todo/models.py": ActionKind.regenerate,
            "todo/serializers.py": ActionKind.regenerate,
            "todo/views.py": ActionKind.preserve,
        })
        r_paths = {
            d.artifact.path
            for d in plan.decisions if d.action == ActionKind.regenerate
        }
        assert set(plan.write_set) == r_paths
        assert validate_impact_plan_invariants(plan, _CANDIDATES) == ()


class TestPvhNotWritable:
    def test_preserve_cannot_be_writable(self) -> None:
        plan = _plan_for({"todo/urls.py": ActionKind.preserve})
        assert "todo/urls.py" not in plan.write_set

    def test_validate_only_cannot_be_writable(self) -> None:
        plan = _plan_for({"todo/views.py": ActionKind.validate_only})
        assert "todo/views.py" not in plan.write_set

    def test_human_review_cannot_be_writable(self) -> None:
        plan = _plan_for({"todo/permissions.py": ActionKind.human_review})
        assert "todo/permissions.py" not in plan.write_set


class TestActionSetsDisjoint:
    def test_sets_pairwise_disjoint(self) -> None:
        plan = _plan_for({
            "todo/models.py": ActionKind.regenerate,
            "todo/serializers.py": ActionKind.validate_only,
            "todo/views.py": ActionKind.preserve,
            "todo/permissions.py": ActionKind.human_review,
        })
        s1, s2, s3, s4 = (
            set(plan.write_set), set(plan.validate_set),
            set(plan.preserve_set), set(plan.human_review_set),
        )
        assert s1.isdisjoint(s2) and s1.isdisjoint(s3) and s1.isdisjoint(s4)
        assert s2.isdisjoint(s3) and s2.isdisjoint(s4) and s3.isdisjoint(s4)


class TestContextSetIndependence:
    def test_context_set_may_include_preserve(self) -> None:
        plan = _plan_for({"todo/models.py": ActionKind.regenerate})
        assert "todo/urls.py" in plan.context_set  # preserve path in context

    def test_context_set_does_not_grant_write(self) -> None:
        plan = _plan_for({"todo/models.py": ActionKind.regenerate})
        assert "todo/urls.py" not in plan.write_set


class TestEveryRCitesEvidence:
    def test_r_without_evidence_fails_gate(self) -> None:
        plan = _plan_for(
            {"todo/serializers.py": ActionKind.regenerate},
        )
        # remove evidence from the R decision
        no_evidence = tuple(
            _decision(d.artifact.path, d.action, evidence=False) if d.artifact.path == "todo/serializers.py" else d
            for d in plan.decisions
        )
        bad = ImpactPlan(**{**plan.__dict__, "decisions": no_evidence})
        violations = validate_impact_plan_invariants(bad, _CANDIDATES)
        assert any("r_missing_evidence" in v for v in violations)


class TestVRequiresValidationReason:
    def test_v_without_reason_fails_gate(self) -> None:
        plan = _plan_for({"todo/views.py": ActionKind.validate_only})
        no_evidence = tuple(
            _decision(d.artifact.path, d.action, evidence=False) if d.artifact.path == "todo/views.py" else d
            for d in plan.decisions
        )
        bad = ImpactPlan(**{**plan.__dict__, "decisions": no_evidence})
        violations = validate_impact_plan_invariants(bad, _CANDIDATES)
        assert any("v_missing_validation_reason" in v for v in violations)


class TestUnknownPathsRejected:
    def test_unknown_path_in_plan_fails_gate(self) -> None:
        plan = _plan_for({"todo/models.py": ActionKind.regenerate})
        extra = _decision("todo/nonexistent.py", ActionKind.regenerate)
        bad = ImpactPlan(**{**plan.__dict__, "decisions": (extra, *plan.decisions)})
        violations = validate_impact_plan_invariants(bad, _CANDIDATES)
        assert any("unknown_paths_in_plan" in v for v in violations)


class TestUncertaintyRule:
    def test_low_confidence_r_becomes_h(self) -> None:
        plan = _plan_for(
            {"todo/models.py": ActionKind.regenerate},
        )
        low = tuple(
            _decision(d.artifact.path, d.action, confidence=0.3) if d.artifact.path == "todo/models.py" else d
            for d in plan.decisions
        )
        p = ImpactPlan(**{**plan.__dict__, "decisions": low})
        out = apply_uncertainty_rule(p)
        assert out.write_set == ()
        assert "todo/models.py" in out.human_review_set

    def test_confidence_threshold_constant(self) -> None:
        assert MIN_CONFIDENCE == 0.60

    def test_no_auto_promote_p_to_r(self) -> None:
        plan = _plan_for({"todo/urls.py": ActionKind.preserve})
        out = apply_uncertainty_rule(plan)
        assert "todo/urls.py" not in out.write_set

    def test_gate_converts_low_confidence_to_h(self) -> None:
        plan = _plan_for(
            {"todo/models.py": ActionKind.regenerate},
        )
        low = tuple(
            _decision(d.artifact.path, d.action, confidence=0.1) if d.artifact.path == "todo/models.py" else d
            for d in plan.decisions
        )
        p = ImpactPlan(**{**plan.__dict__, "decisions": low})
        result = gate_plan(p, _CANDIDATES)
        assert result.passed
        assert "todo/models.py" in result.plan.human_review_set


class TestPlanHashStable:
    def test_identical_plan_same_hash(self) -> None:
        a = _plan_for({"todo/models.py": ActionKind.regenerate})
        b = _plan_for({"todo/models.py": ActionKind.regenerate})
        assert compute_plan_hash(a) == compute_plan_hash(b)

    def test_different_action_different_hash(self) -> None:
        a = _plan_for({"todo/models.py": ActionKind.regenerate})
        b = _plan_for({"todo/models.py": ActionKind.preserve})
        assert compute_plan_hash(a) != compute_plan_hash(b)


class TestMockPlanner:
    def test_mock_planner_no_model_calls(self) -> None:
        p = MockImpactPlanner(r_paths=frozenset({"todo/models.py"}))
        inp = PlannerInput(
            requirement_change=_requirement(),
            artifact_universe=_universe(),
            evidence=(),
            run_id="r1",
            scenario_id="todo-smoke-001",
            source_commit="abc",
        )
        plan = p.plan(inp)
        assert p.model_calls == 0
        assert p.token_usage.total_tokens == 0
        assert set(plan.write_set) == {"todo/models.py"}

    def test_mock_planner_marks_v_with_obligation(self) -> None:
        p = MockImpactPlanner(v_paths=frozenset({"todo/views.py"}))
        inp = PlannerInput(
            requirement_change=_requirement(),
            artifact_universe=_universe(),
            evidence=(),
            run_id="r1",
            scenario_id="todo-smoke-001",
            source_commit="abc",
        )
        plan = p.plan(inp)
        assert "todo/views.py" in plan.validate_set
        assert any(o.target == "todo/tests/test_views.py" for o in plan.validation_obligations)

    def test_disjoint_r_v_required(self) -> None:
        with pytest.raises(ValueError):
            MockImpactPlanner(
                r_paths=frozenset({"todo/models.py"}),
                v_paths=frozenset({"todo/models.py"}),
            )
