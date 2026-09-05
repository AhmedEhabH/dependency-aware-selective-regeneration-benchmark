from __future__ import annotations

import json
from pathlib import Path

from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import (
    ArtifactRef,
    ArtifactUniverse,
    DependencyGraph,
    EvidenceItem,
    ImpactPrediction,
    RequirementChange,
)
from benchmark.selection.dependency_scope import ArtifactDescriptor
from benchmark.selection.impact_evidence import collect_impact_evidence
from benchmark.selection.impact_planner import (
    MockImpactPlanner,
    PlannerInput,
    gate_plan,
    to_plan_dict,
)
from benchmark.selection.planner import (
    compute_artifact_counts,
    plan_from_impact_plan,
)

_CANDIDATES = (
    "todo/models.py",
    "todo/serializers.py",
    "todo/views.py",
    "todo/permissions.py",
    "todo/urls.py",
)

_DESCRIPTORS = tuple(
    ArtifactDescriptor(
        path=p,
        category="source",
        description="todo source file",
        provides_symbols=(),
        typical_change_triggers=("schema and field changes", "api additions"),
    )
    for p in _CANDIDATES
)

_GRAPH = DependencyGraph(
    nodes=list(_CANDIDATES),
    edges=(
        ("todo/urls.py", "todo/views.py"),
        ("todo/views.py", "todo/serializers.py"),
        ("todo/views.py", "todo/models.py"),
        ("todo/views.py", "todo/permissions.py"),
        ("todo/serializers.py", "todo/models.py"),
        ("todo/permissions.py", "todo/models.py"),
    ),
)


def _universe(paths=_CANDIDATES) -> ArtifactUniverse:
    return ArtifactUniverse(
        artifacts=tuple(ArtifactRef(path=p, artifact_type=ArtifactType.source) for p in paths)
    )


def _requirement() -> RequirementChange:
    return RequirementChange(
        before="Task has no priority",
        after="Task gains Priority with HIGH, MEDIUM, LOW",
        acceptance_criteria=("TaskSerializer exposes priority",),
    )


class TestEvidenceCollector:
    def test_static_edges_emitted(self) -> None:
        evidence = collect_impact_evidence(
            _requirement(), _universe(), _DESCRIPTORS, _GRAPH
        )
        static = [e for e in evidence if e.evidence_type == "static"]
        assert len(static) == 6

    def test_evidence_items_cited_visible(self) -> None:
        evidence = collect_impact_evidence(
            _requirement(), _universe(), _DESCRIPTORS, _GRAPH
        )
        assert all(isinstance(e, EvidenceItem) for e in evidence)
        assert all(e.evidence_id for e in evidence)

    def test_test_links_discovered_from_workspace(self, tmp_path: Path) -> None:
        todo_dir = tmp_path / "todo"
        tests_dir = todo_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "test_models.py").write_text("from todo import models\n", encoding="utf-8")
        (tests_dir / "test_views.py").write_text("from todo import views\n", encoding="utf-8")
        evidence = collect_impact_evidence(
            _requirement(), _universe(), _DESCRIPTORS, _GRAPH,
            workspace_root=str(tmp_path),
        )
        links = [e for e in evidence if e.evidence_type == "test_link"]
        paths = {e.artifact_path for e in links}
        assert "todo/models.py" in paths
        assert "todo/views.py" in paths

    def test_architecture_constraints_normalized(self) -> None:
        evidence = collect_impact_evidence(
            _requirement(), _universe(), _DESCRIPTORS, _GRAPH,
            extra_architecture_constraints=("Priority filtering must be in the view",),
        )
        arch = [e for e in evidence if e.evidence_type == "architecture"]
        assert len(arch) == 1
        assert "view" in arch[0].description


class TestPlanFromImpactPlan:
    def test_write_set_only(self) -> None:
        planner = MockImpactPlanner(r_paths=frozenset({"todo/models.py", "todo/views.py"}))
        inp = PlannerInput(
            requirement_change=_requirement(),
            artifact_universe=_universe(),
            evidence=(),
            run_id="r1",
            scenario_id="todo-smoke-001",
            source_commit="abc",
        )
        plan = planner.plan(inp)
        gated = gate_plan(plan, _CANDIDATES)
        assert gated.passed
        regen_plan = plan_from_impact_plan(gated.plan)
        assert set(regen_plan.regenerate_artifact_paths) == {"todo/models.py", "todo/views.py"}
        for rp in regen_plan.ordered_artifacts:
            assert regen_plan.actions[rp.path] == ActionKind.regenerate

    def test_preserve_never_in_executable_plan(self) -> None:
        planner = MockImpactPlanner(r_paths=frozenset({"todo/models.py"}))
        inp = PlannerInput(
            requirement_change=_requirement(),
            artifact_universe=_universe(),
            evidence=(),
            run_id="r1",
            scenario_id="todo-smoke-001",
            source_commit="abc",
        )
        plan = planner.plan(inp)
        regen_plan = plan_from_impact_plan(plan)
        r_artifacts = {
            r.artifact for r in plan.decisions if r.action == ActionKind.regenerate
        }
        assert set(regen_plan.ordered_artifacts) <= r_artifacts


class TestComputeArtifactCountsValidateOnly:
    def test_validate_only_counted(self) -> None:
        planner = MockImpactPlanner(
            r_paths=frozenset({"todo/models.py"}),
            v_paths=frozenset({"todo/views.py"}),
        )
        inp = PlannerInput(
            requirement_change=_requirement(),
            artifact_universe=_universe(),
            evidence=(),
            run_id="r1",
            scenario_id="todo-smoke-001",
            source_commit="abc",
        )
        plan = planner.plan(inp)
        prediction = ImpactPrediction(decisions=plan.decisions)
        counts = compute_artifact_counts(prediction)
        assert counts["regenerate"] == 1
        assert counts["validate_only"] == 1
        assert counts["preserve"] == 3

    def test_validate_only_reachable_in_selection(self) -> None:
        from benchmark.selection.planner import ArtifactSelector, RegenerationPlanner

        planner = MockImpactPlanner(v_paths=frozenset({"todo/views.py"}))
        inp = PlannerInput(
            requirement_change=_requirement(),
            artifact_universe=_universe(),
            evidence=(),
            run_id="r1",
            scenario_id="todo-smoke-001",
            source_commit="abc",
        )
        plan = planner.plan(inp)
        prediction = ImpactPrediction(decisions=plan.decisions)
        selection = ArtifactSelector().select(prediction, _universe())
        regen = RegenerationPlanner().plan(selection, prediction)
        # validate_last ordering reachable: V artifact recorded, not written
        assert any(a.path == "todo/views.py" for a in regen.ordered_artifacts)


class TestPlannerCostPersists:
    def test_plan_dict_includes_planner_cost(self) -> None:

        planner = MockImpactPlanner(r_paths=frozenset({"todo/models.py"}))
        inp = PlannerInput(
            requirement_change=_requirement(),
            artifact_universe=_universe(),
            evidence=(),
            run_id="r1",
            scenario_id="todo-smoke-001",
            source_commit="abc",
        )
        plan = planner.plan(inp)
        payload = to_plan_dict(plan)
        assert payload["planner_model_calls"] >= 0
        assert payload["planner_latency_seconds"] >= 0

    def test_real_planner_token_usage_exposed(self) -> None:
        """OpenRouter planner exposes counted token usage for the proposed-arm total."""
        from benchmark.selection.impact_planner import OpenRouterImpactPlanner

        class _FakeBackend:
            async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096):
                from benchmark.core.models import LLMResponse, TokenUsage

                return LLMResponse(
                    text=json.dumps({
                        "decisions": [
                            {
                                "path": "todo/models.py",
                                "action": "REGENERATE",
                                "rationale": "pending",
                                "evidence": [{"source": "static-graph-edge-0", "description": "edge"}],
                                "confidence": 0.9,
                                "reason_codes": ["static"],
                            },
                            {
                                "path": "todo/serializers.py",
                                "action": "PRESERVE",
                                "rationale": "no edit",
                                "evidence": [],
                                "confidence": 0.9,
                                "reason_codes": [],
                            },
                        ],
                        "context_set": ["todo/models.py", "todo/serializers.py"],
                        "validation_obligations": [],
                        "architecture_checks": [],
                        "escalation_reason": "",
                    }),
                    token_usage=TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
                    finish_reason="stop",
                )

        planner = OpenRouterImpactPlanner(_FakeBackend())
        inp = PlannerInput(
            requirement_change=_requirement(),
            artifact_universe=_universe(paths=("todo/models.py", "todo/serializers.py")),
            evidence=(),
            run_id="r1",
            scenario_id="todo-smoke-001",
            source_commit="abc",
        )
        plan = planner.plan(inp)
        assert planner.model_calls == 1
        assert planner.token_usage.total_tokens == 70
        assert plan.planner_token_usage is not None
        assert plan.planner_token_usage.total_tokens == 70


class TestRunRecordImpactPlanFields:
    def test_run_record_accepts_new_fields(self) -> None:
        from benchmark.core.enums import RunStatus
        from benchmark.core.models import RunIdentity, RunRecord, TokenUsage

        rec = RunRecord(
            identity=RunIdentity(
                run_id="r1",
                protocol_version="1.0",
                repository_commit_sha="abc",
                scenario_id="todo-smoke-001",
                strategy_name="impact_plan",
            ),
            status=RunStatus.succeeded,
            token_usage=TokenUsage(1, 2, 3),
            impact_plan={"plan": {"write_set": ["todo/models.py"]}, "final_after_expansion": False},
            impact_plan_hash="abc123",
            impact_plan_version="v1",
            impact_expansion_count=0,
            escalated_to_human_review=False,
            prohibited_write_attempts=0,
            planner_prompt_tokens=50,
            planner_completion_tokens=20,
            planner_total_tokens=70,
            planner_model_calls=1,
            planner_latency_seconds=0.5,
        )
        assert rec.impact_plan_hash == "abc123"
        assert rec.planner_total_tokens == 70
