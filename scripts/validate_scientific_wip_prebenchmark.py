"""SCIENTIFIC-WIP-IMPACTPLAN-V1 — six Pre-Benchmark validation gates (D047).

Two arms for the WIP profile:
- baseline: ``iterative_repository_agent``;
- proposed: ``impact_plan`` (ImpactPlanSelectiveStrategy).

Each gate references the NEW protocol/treatment, NOT the old binary R/P one.
No model call is made by this validator (G4 uses the CLI dry-run = mock).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
SCENARIOS_DIR = ROOT / "benchmark_data" / "scenarios"
PROFILES_DIR = ROOT / "benchmark_data" / "repository_profiles"

SCENARIO_BLAST = {
    "todo-smoke-001": "localized",
    "todo-smoke-002": "moderate",
    "todo-smoke-003": "cross_cutting",
}
CANDIDATES = (
    "todo/models.py",
    "todo/serializers.py",
    "todo/views.py",
    "todo/permissions.py",
    "todo/urls.py",
)


@dataclass
class GateResult:
    name: str
    passed: bool
    details: list[str] = field(default_factory=list)

    def add(self, ok: bool, msg: str) -> None:
        self.details.append(("PASS " if ok else "FAIL ") + msg)
        if not ok:
            self.passed = False


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    if not path.is_file():
        return out
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


# ---------------------------------------------------------------------------
# G1 Dataset Validation
# ---------------------------------------------------------------------------

def gate_g1_dataset() -> GateResult:
    g = GateResult("G1 Dataset Validation (scientific-wip-impactplan-v1)", passed=True)
    data: dict[str, dict[str, Any]] = {}
    for sid in SCENARIO_BLAST:
        p = SCENARIOS_DIR / f"{sid}.yaml"
        try:
            data[sid] = yaml.safe_load(p.read_text(encoding="utf-8"))
            g.add(data[sid].get("scenario_id") == sid, f"{sid} parses")
        except Exception as exc:
            g.add(False, f"{sid} parse failed: {exc}")
    for sid, radius in SCENARIO_BLAST.items():
        g.add(data.get(sid, {}).get("blast_radius") == radius, f"{sid} blast_radius {radius}")

    # Five-file source universe is exact (scored universe)
    profile_path = PROFILES_DIR / "todo.yaml"
    if profile_path.is_file():
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
        editable = set(profile.get("artifact_universe", {}).get("llm_editable") or [])
        g.add(set(CANDIDATES) == editable, f"five-file universe exact ({sorted(editable)})")

    # Evaluator SHA sidecars exist and hidden evaluators stay strategy-inaccessible
    for sid, asset in {
        "todo-smoke-001": "todo_smoke_001_checks.py",
        "todo-smoke-002": "todo_smoke_002_checks.py",
        "todo-smoke-003": "todo_smoke_003_checks.py",
    }.items():
        ap = ROOT / "tests" / "evaluator_assets" / asset
        sc = ap.with_suffix(ap.suffix + ".sha256")
        ok = sc.is_file()
        g.add(ok, f"{sid} evaluator sidecar exists")
        if ok:
            g.add(
                hashlib.sha256(ap.read_bytes()).hexdigest() == sc.read_text().strip(),
                f"{sid} evaluator SHA matches sidecar",
            )

    # Hidden evaluator/gold names never appear in planner or executor prompts
    planner_src = (ROOT / "src" / "benchmark" / "selection" / "impact_planner.py").read_text(
        encoding="utf-8", errors="replace"
    )
    regen_src = (ROOT / "src" / "benchmark" / "execution" / "regeneration.py").read_text(
        encoding="utf-8", errors="replace"
    )
    for marker in ("todo_smoke_001_checks", "todo_smoke_002_checks", "todo_smoke_003_checks"):
        g.add(marker not in planner_src, f"planner prompt/source has no {marker}")
        g.add(marker not in regen_src, f"executor prompt/source has no {marker}")

    # Evaluator integration suite green on the real environment
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/integration/test_todo_smoke_evaluator_assets.py", "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=900,
    )
    g.add(proc.returncode == 0, f"test_todo_smoke_evaluator_assets.py (exit {proc.returncode})")
    return g


# ---------------------------------------------------------------------------
# G2 Prompt Validation
# ---------------------------------------------------------------------------

def gate_g2_prompt() -> GateResult:
    g = GateResult("G2 Prompt Validation (scientific-wip-impactplan-v1)", passed=True)
    try:
        from benchmark.core.models import RegenerationScenarioContext
        from benchmark.execution.regeneration import build_generation_prompt
        from benchmark.selection.impact_planner import PLANNER_PROMPT_TEMPLATE

        ctx = RegenerationScenarioContext(
            scenario_id="todo-smoke-001",
            requirement_before="old",
            requirement_after="new",
            acceptance_criteria=("Task has priority field",),
            architecture_constraints=("Filtering goes in the view",),
            expected_actions=(),
            artifact_instructions=(),
            gold_isolated=True,
        )
        prompt = build_generation_prompt(
            artifact_path="todo/models.py",
            current_content="from django.db import models\n",
            requirement_delta="old -> new",
            language_hint="python",
            scenario_context=ctx,
            expected_action="modify",
        )
        g.add("Task has priority field" in prompt, "prompt has visible acceptance")
        g.add("GOLD_SENTINEL" not in prompt, "prompt has no gold sentinel")
        g.add("todo_smoke_001_checks" not in prompt, "prompt has no evaluator name")

        # Planner prompt input contract: no gold, no result tables
        g.add("expected_actions" not in PLANNER_PROMPT_TEMPLATE, "planner prompt has no expected_actions")
        g.add("GOLD_SENTINEL" not in PLANNER_PROMPT_TEMPLATE, "planner prompt has no gold sentinel")
    except Exception as exc:
        g.add(False, f"prompt build failed: {exc}")
    return g


# ---------------------------------------------------------------------------
# G3 Pipeline Smoke Test (throwaway stub, no model call)
# ---------------------------------------------------------------------------

def gate_g3_pipeline_smoke() -> GateResult:
    g = GateResult("G3 Pipeline Smoke Test (scientific-wip-impactplan-v1)", passed=True)
    try:
        _wip_pipeline_smoke()
        g.add(True, "ImpactPlan -> gate -> write_set plan -> executor -> write -> usage OK (stub, 0 model calls)")
    except Exception as exc:
        g.add(False, f"pipeline smoke failed: {exc}")
    return g


def _wip_pipeline_smoke() -> None:
    import tempfile

    from benchmark.core.enums import ArtifactType
    from benchmark.core.models import (
        ArtifactRef,
        ArtifactUniverse,
        LLMResponse,
        RequirementChange,
        TokenUsage,
    )
    from benchmark.execution.isolation import IsolationContext
    from benchmark.execution.regeneration import SharedRegenerationExecutor
    from benchmark.repositories.workspace import WorkspacePath
    from benchmark.selection.impact_planner import MockImpactPlanner, PlannerInput, gate_plan
    from benchmark.selection.planner import plan_from_impact_plan

    class _FakeBackend:
        async def generate(self, prompt: str = "", temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:  # noqa: ARG002
            return LLMResponse(text="<<<<<<< SEARCH\nold line\n=======\nnew line\n>>>>>>> REPLACE",
                               token_usage=TokenUsage(40, 12, 52), finish_reason="stop")

    tmp = Path(tempfile.mkdtemp())
    ws_root = tmp / "ws"
    ws_root.mkdir()
    (ws_root / "a.py").write_text("old line\n", encoding="utf-8", newline="")
    iso = IsolationContext(workspace=WorkspacePath(root=str(ws_root)), snapshot_base=tmp / "snap")

    uni = ArtifactUniverse(artifacts=(ArtifactRef(path="a.py", artifact_type=ArtifactType.source),))
    planner = MockImpactPlanner(r_paths=frozenset({"a.py"}))
    inp = PlannerInput(
        requirement_change=RequirementChange(before="x", after="y"),
        artifact_universe=uni,
        evidence=(),
        run_id="r1", scenario_id="todo-smoke-001", source_commit="abc",
    )
    plan = planner.plan(inp)
    gated = gate_plan(plan, ("a.py",))
    assert gated.passed, gated.violations
    regen_plan = plan_from_impact_plan(gated.plan)
    assert set(regen_plan.regenerate_artifact_paths) == {"a.py"}
    result = SharedRegenerationExecutor(_FakeBackend()).execute(regen_plan, iso, enable_exact_patch=True)
    assert any(a.status == "generated" for a in result.artifacts), result.failures
    assert (ws_root / "a.py").read_text(encoding="utf-8") == "new line\n"
    assert result.total_tokens == 52
    assert result.prohibited_write_attempts == 0


# ---------------------------------------------------------------------------
# G4 Dry Run (30-cell WIP profile, CLI mock)
# ---------------------------------------------------------------------------

def gate_g4_dry_run(dry_run_dir: Path) -> GateResult:
    g = GateResult("G4 Dry Run (scientific-wip-impactplan-v1)", passed=True)
    if dry_run_dir.exists():
        shutil.rmtree(dry_run_dir, ignore_errors=True)
    dry_run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(ROOT / "seven_arm_benchmark.py"),
        "--profile", "scientific-wip-impactplan-v1",
        "--dry-run", "--output-dir", str(dry_run_dir),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900)
    if proc.returncode != 0:
        g.add(False, f"dry-run CLI exit {proc.returncode}: {proc.stderr[-1200:]}")
        return g
    records = _load_jsonl(dry_run_dir / "run_records.jsonl")
    g.add(len(records) == 30, f"30/30 records ({len(records)})")
    g.add(len({r.get("run_id") for r in records}) == 30, "30 unique run IDs")
    counts = {}
    for r in records:
        counts[r.get("strategy_id")] = counts.get(r.get("strategy_id"), 0) + 1
    g.add(counts.get("iterative_repository_agent") == 15, f"15 agent ({counts.get('iterative_repository_agent')})")
    g.add(counts.get("impact_plan") == 15, f"15 impact_plan ({counts.get('impact_plan')})")
    scen_counts = {}
    for r in records:
        scen_counts[r.get("scenario_id")] = scen_counts.get(r.get("scenario_id"), 0) + 1
    g.add(all(scen_counts.get(s) == 10 for s in SCENARIO_BLAST), f"10/scenario ({scen_counts})")
    rep_counts = {}
    for r in records:
        rep_counts[r.get("repetition")] = rep_counts.get(r.get("repetition"), 0) + 1
    g.add(sorted(rep_counts) == [1, 2, 3, 4, 5] and all(v == 6 for v in rep_counts.values()),
          f"reps 1..5 x 6 ({rep_counts})")
    calls = sum(r.get("total_workflow_model_calls", 0) for r in records)
    tokens = sum((r.get("token_usage") or {}).get("total", 0) for r in records)
    g.add(calls == 0 and tokens == 0, "0 model calls / 0 tokens")
    sid = json.loads((dry_run_dir / "source_identity.json").read_text(encoding="utf-8"))
    g.add(sid.get("profile") == "scientific-wip-impactplan-v1", "config profile frozen")
    g.add(bool(sid.get("config_hash")), "config_hash frozen")
    return g


# ---------------------------------------------------------------------------
# G5 Integration Test (new seams)
# ---------------------------------------------------------------------------

def gate_g5_integration() -> GateResult:
    g = GateResult("G5 Integration Test (scientific-wip-impactplan-v1)", passed=True)
    suites = [
        "tests/unit/selection/test_impact_plan_contract.py",
        "tests/unit/selection/test_impact_evidence_and_planner.py",
        "tests/unit/execution/test_impact_plan_runner.py",
        "tests/unit/llm/test_llm_openrouter_provider_pin.py",
        "tests/unit/test_scientific_identity.py",
        "tests/unit/test_scientific_evidence_persistence.py",
        "tests/unit/test_acceptance_gate_script.py",
        "tests/integration/test_todo_smoke_evaluator_assets.py",
    ]
    for suite in suites:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", suite, "-q"],
            cwd=ROOT, capture_output=True, text=True, timeout=1200,
        )
        g.add(proc.returncode == 0, f"{suite} (exit {proc.returncode})")
    return g


# ---------------------------------------------------------------------------
# G6 Metric Verification
# ---------------------------------------------------------------------------

def gate_g6_metric_verification() -> GateResult:
    g = GateResult("G6 Metric Verification (scientific-wip-impactplan-v1)", passed=True)
    # Impact-plan metrics: R recall/F1, class support, expansion rate, planner cost.
    try:
        from benchmark.core.enums import ActionKind, ArtifactType
        from benchmark.core.models import (
            ArtifactRef,
            ImpactDecision,
            ImpactPrediction,
            TokenUsage,
        )
        from benchmark.selection.planner import compute_artifact_counts

        pred = ImpactPrediction(
            decisions=tuple(
                ImpactDecision(artifact=ArtifactRef(path=p, artifact_type=ArtifactType.source), action=a)
                for p, a in (
                    ("todo/models.py", ActionKind.regenerate),
                    ("todo/views.py", ActionKind.validate_only),
                    ("todo/urls.py", ActionKind.preserve),
                    ("todo/permissions.py", ActionKind.preserve),
                    ("todo/serializers.py", ActionKind.preserve),
                )
            ),
            token_usage=TokenUsage(10, 5, 15),
        )
        counts = compute_artifact_counts(pred)
        g.add(counts["regenerate"] == 1, "regenerate count == 1")
        g.add(counts["validate_only"] == 1, "validate_only count == 1")
        g.add(counts["preserve"] == 3, "preserve count == 3")
        action_total = (
            counts["regenerate"] + counts["preserve"]
            + counts["validate_only"] + counts["human_review"]
        )
        g.add(action_total == 5, f"all candidates counted exactly once ({action_total})")
    except Exception as exc:
        g.add(False, f"metric verification failed: {exc}")
    return g


def run_all(dry_run_dir: Path) -> list[GateResult]:
    return [
        gate_g1_dataset(),
        gate_g2_prompt(),
        gate_g3_pipeline_smoke(),
        gate_g4_dry_run(dry_run_dir),
        gate_g5_integration(),
        gate_g6_metric_verification(),
    ]


def render(results: list[GateResult]) -> str:
    lines = [
        "# SCIENTIFIC-WIP-IMPACTPLAN-V1 — PRE-BENCHMARK VALIDATION",
        "",
    ]
    for g in results:
        lines.append(f"## {g.name}: {'PASS' if g.passed else 'FAIL'}")
        for d in g.details:
            lines.append(f"- {d}")
        lines.append("")
    lines.append("## Gate summary")
    for g in results:
        lines.append(f"- {g.name}: {'PASS' if g.passed else 'FAIL'}")
    lines.append("")
    lines.append("## Microstudy real-run authorization")
    lines.append(
        "MICROSTUDY_REAL_RUN_AUTHORIZED="
        + ("YES" if all(g.passed for g in results) else "NO")
    )
    return "\n".join(lines)


if __name__ == "__main__":
    dry_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else REPORTS_DIR / "dryrun_wip_impactplan"
    results = run_all(dry_dir)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "SCIENTIFIC_WIP_PREBENCHMARK_VALIDATION.md"
    out.write_text(render(results), encoding="utf-8")
    print("WIP_PRE_BENCHMARK_DONE")
    for g in results:
        print(f"{g.name}: {'PASS' if g.passed else 'FAIL'}")
    print(f"Wrote {out}")
    if not all(g.passed for g in results):
        print("GATE_FAILURE_DETECTED")
        raise SystemExit(1)
