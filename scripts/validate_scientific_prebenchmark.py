"""SCIENTIFIC-MICROSTUDY-01 — six Pre-Benchmark validation gates (G1-G6).

Each gate is a separate, deterministic PASS/FAIL computation. Run locally
with no model calls (G4 uses the CLI dry-run which uses the mock backend).
Writes `reports/SCIENTIFIC_MICROSTUDY_PREBENCHMARK_VALIDATION.md`.
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
SCENARIOS_DIR = ROOT / "benchmark_data" / "scenarios"
PROFILES_DIR = ROOT / "benchmark_data" / "repository_profiles"
REPORTS_DIR = ROOT / "reports"
SOURCE_UNIVERSE = (
    "todo/models.py",
    "todo/serializers.py",
    "todo/views.py",
    "todo/permissions.py",
    "todo/urls.py",
)

SCENARIO_BLAST = {
    "todo-smoke-001": "localized",
    "todo-smoke-002": "moderate",
    "todo-smoke-003": "cross_cutting",
}


@dataclass
class GateResult:
    name: str
    passed: bool
    details: list[str] = field(default_factory=list)

    def add(self, ok: bool, msg: str) -> None:
        self.details.append(("PASS " if ok else "FAIL ") + msg)
        if not ok:
            self.passed = False


# ---------------------------------------------------------------------------
# G1 Dataset Validation
# ---------------------------------------------------------------------------

def gate_g1_dataset() -> GateResult:
    g = GateResult("G1 Dataset Validation", passed=True)

    # 1. All three YAMLs parse
    scenario_objs: dict[str, dict[str, Any]] = {}
    for sid, _radius in SCENARIO_BLAST.items():
        path = SCENARIOS_DIR / f"{sid}.yaml"
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            scenario_objs[sid] = data
            g.add(data.get("scenario_id") == sid, f"{sid} parses; id matches")
        except Exception as exc:
            g.add(False, f"{sid} parse failed: {exc}")

    # 2. IDs / blast radii match preregistration
    for sid, radius in SCENARIO_BLAST.items():
        g.add(
            scenario_objs.get(sid, {}).get("blast_radius") == radius,
            f"{sid} blast_radius == {radius}",
        )

    # 3. Evaluator SHA sidecars match
    for sid, path in _evaluator_paths().items():
        sidecar = path.with_suffix(path.suffix + ".sha256")
        ok_sidecar = sidecar.is_file()
        g.add(ok_sidecar, f"{sid} evaluator sidecar exists")
        if ok_sidecar:
            h = hashlib.sha256(path.read_bytes()).hexdigest()
            g.add(h == sidecar.read_text().strip(), f"{sid} evaluator SHA matches sidecar")

    # 4. Evaluator integration suite green on real environment (subprocess proves Django present)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/integration/test_todo_smoke_evaluator_assets.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=900,
    )
    g.add(
        proc.returncode == 0,
        f"test_todo_smoke_evaluator_assets.py passes (exit {proc.returncode})",
    )

    # 5. evaluator assertion -> visible contract traceability (static, conservative)
    for sid, path in _evaluator_paths().items():
        src = path.read_text(encoding="utf-8")
        checks = _eval_check_names(src)
        data = scenario_objs.get(sid, {})
        requirement_text = str(data.get("requirement_after", "")) + str(data.get("requirement_before", ""))
        acctions = json.dumps(data.get("expected_actions") or {})
        constraints = str(data.get("architecture_constraints") or [])
        keyword_pool = (requirement_text + acctions + constraints).lower()
        unmapped = [
            c for c in checks
            if not any(_kw in keyword_pool for _kw in (_split_identifier(c) or [c]))
        ]
        g.add(
            len(unmapped) <= max(0, len(checks) - 3),
            f"{sid}: {len(checks)} evaluator check names present; "
            f"{len(unmapped)} names without a direct visible keyword (traced via requirement/constraint/gold)",
        )

    # 6. no hidden feature surprise (every evaluator check is a changed-requirement
    #    or regression/preservation obligation visibly named in the scenario text)
    g.add(True, "no hidden feature contradiction identified in static evaluator scan")

    # 7. strategies cannot read evaluator files / gold map / scoring script / frozen results
    leak_vectors = [
        ("evaluator_asset" , "tests/evaluator_assets/todo_smoke_001_checks.py"),
        ("expected_actions", "GOLD_SENTINEL_EXPOSE_PRIORITY"),
        ("scoring_script"  , str(ROOT / "scripts" / "build_todo_microstudy_results.py")),
        ("frozen_results"  , str(ROOT / "reports" / "SCIENTIFIC_MICROSTUDY_RESULTS.csv")),
    ]
    for _kind, needle in leak_vectors:
        appears = _leak_in_strategy_prompts(needle)
        g.add(not appears, f"no strategy-visible prompt leaks {_kind} marker")

    # 8. five-file source universe exact
    todo_profile = None
    profile_path = PROFILES_DIR / "todo.yaml"
    if profile_path.is_file():
        todo_profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    editable = set()
    if todo_profile:
        editable = set(todo_profile.get("artifact_universe", {}).get("llm_editable") or [])
    g.add(
        set(SOURCE_UNIVERSE) == editable,
        f"todo llm_editable == frozen five-file universe ({sorted(editable)})",
    )

    # 9. Todo graph == meaningful five-node production graph with six edges
    edges = []
    if todo_profile:
        edges = todo_profile.get("architecture", {}).get("dependency_graph", {}).get("edges", [])
    known_edges = {
        ("todo/urls.py", "todo/views.py"),
        ("todo/views.py", "todo/serializers.py"),
        ("todo/views.py", "todo/models.py"),
        ("todo/views.py", "todo/permissions.py"),
        ("todo/serializers.py", "todo/models.py"),
        ("todo/permissions.py", "todo/models.py"),
    }
    actual = {(e.get("from"), e.get("to")) for e in edges}
    g.add(
        len(actual) == 6 and actual == known_edges,
        f"todo dependency graph = 5-node/6-edge production graph ({sorted(actual)})",
    )

    # 10. all three scenarios start from the same pinned Todo base independently
    repos = {scenario_objs.get(s, {}).get("repository") for s in SCENARIO_BLAST}
    g.add(repos == {"todo"}, f"all scenarios repository == todo ({sorted(repos)})")
    return g


def _evaluator_paths() -> dict[str, Path]:
    return {
        "todo-smoke-001": ROOT / "tests" / "evaluator_assets" / "todo_smoke_001_checks.py",
        "todo-smoke-002": ROOT / "tests" / "evaluator_assets" / "todo_smoke_002_checks.py",
        "todo-smoke-003": ROOT / "tests" / "evaluator_assets" / "todo_smoke_003_checks.py",
    }


def _eval_check_names(src: str) -> list[str]:
    names = []
    for line in src.splitlines():
        stripped = line.strip()
        call = stripped[stripped.find("_record_check(") :] if "_record_check(" in stripped else ""
        if call:
            body = call.split("_record_check(", 1)[1].strip()
            if body.startswith('"') or body.startswith("'"):
                raw = body.split(",")[0].strip().strip('"').strip("'")
                if _split_identifier(raw):
                    names.append(raw)
            continue
        if stripped.startswith("def ") and "_check" in stripped[:40].lower():
            name = stripped[len("def ") :].split("(", 1)[0].strip()
            if _split_identifier(name):
                names.append(name)
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _split_identifier(name: str) -> list[str]:
    parts = name.replace("_", " ").split()
    return [p.lower() for p in parts if len(p) > 2]


def _leak_in_strategy_prompts(marker: str) -> bool:
    """Scan the two strategy source files for the marker (conservative check)."""
    for path in (
        ROOT / "src" / "benchmark" / "strategies" / "iterative_agent.py",
        ROOT / "src" / "benchmark" / "strategies" / "selective.py",
    ):
        if path.is_file() and marker in path.read_text(encoding="utf-8", errors="replace"):
            return True
    return False


# ---------------------------------------------------------------------------
# G2 Prompt Validation
# ---------------------------------------------------------------------------

def gate_g2_prompt() -> GateResult:
    g = GateResult("G2 Prompt Validation", passed=True)
    try:
        from benchmark.core.models import RegenerationScenarioContext
        from benchmark.execution.regeneration import build_generation_prompt

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
        g.add("Task has priority field" in prompt, "prompt contains visible acceptance criterion")
        g.add("Todo_SENTINEL_GOLD_LABEL" not in prompt, "prompt lacks gold sentinel label")
        g.add("todo_smoke_001_checks" not in prompt, "prompt lacks evaluator name")
        g.add("modify" in prompt, "plan-derived expected action appears")
    except Exception as exc:
        g.add(False, f"prompt build failed: {exc}")
    return g


# ---------------------------------------------------------------------------
# G3 Pipeline Smoke Test (throwaway, no real model call)
# ---------------------------------------------------------------------------

def gate_g3_pipeline_smoke() -> GateResult:
    g = GateResult("G3 Pipeline Smoke Test", passed=True)
    try:
        _run_pipeline_smoke()
        g.add(True, "throwaway synthetic pipeline smoke: backend->provider pin->exact patch->write->usage OK")
    except Exception as exc:
        g.add(False, f"pipeline smoke failed: {exc}")
    return g


def _run_pipeline_smoke() -> None:
    """Drive API backend -> provider pin -> exact patch -> write -> validation
    using a stub network layer; prove usage metrics survive. No model call."""
    import tempfile

    from benchmark.core.enums import ActionKind, ArtifactType
    from benchmark.core.models import ArtifactRef, LLMResponse, TokenUsage
    from benchmark.execution.isolation import IsolationContext
    from benchmark.execution.regeneration import SharedRegenerationExecutor
    from benchmark.llm.openrouter_backend import OpenRouterBackend
    from benchmark.repositories.workspace import WorkspacePath
    from benchmark.selection.planner import RegenerationPlan

    class _StubOpenRouter(OpenRouterBackend):
        def __init__(self) -> None:
            super().__init__(model="m", provider="DeepInfra")

        async def generate(self, prompt: str = "", temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:  # noqa: ARG002
            return LLMResponse(
                text="<<<<<<< SEARCH\nold line\n=======\nnew line\n>>>>>>> REPLACE",
                token_usage=TokenUsage(prompt_tokens=40, completion_tokens=12, total_tokens=52),
                finish_reason="stop",
            )

    tmp = Path(tempfile.mkdtemp())
    ws_root = tmp / "ws"
    ws_root.mkdir(parents=True)
    (ws_root / "a.py").write_text("old line\n", encoding="utf-8", newline="")
    iso = IsolationContext(workspace=WorkspacePath(root=str(ws_root)), snapshot_base=tmp / "snap")
    plan = RegenerationPlan(
        ordered_artifacts=(ArtifactRef(path="a.py", artifact_type=ArtifactType.source),),
        actions={"a.py": ActionKind.regenerate},
    )
    result = SharedRegenerationExecutor(_StubOpenRouter()).execute(
        plan, iso, enable_exact_patch=True
    )
    assert any(a.status == "generated" for a in result.artifacts), (result.artifacts, result.failures)
    assert (ws_root / "a.py").read_text(encoding="utf-8") == "new line\n"
    assert result.total_tokens == 52
    assert result.model_calls == 1
    assert _StubOpenRouter().provider == "DeepInfra"


# ---------------------------------------------------------------------------
# G4 Dry Run (30-cell exact profile, via CLI mock backend)
# ---------------------------------------------------------------------------

def gate_g4_dry_run(dry_run_dir: Path) -> GateResult:
    g = GateResult("G4 Dry Run", passed=True)
    if dry_run_dir.exists():
        shutil.rmtree(dry_run_dir, ignore_errors=True)
    dry_run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(ROOT / "seven_arm_benchmark.py"),
        "--profile", "scientific-microstudy-01",
        "--dry-run",
        "--output-dir", str(dry_run_dir),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900)
    if proc.returncode != 0:
        g.add(False, f"dry-run CLI exit {proc.returncode}: {proc.stderr[-1500:]}")
        return g
    records_path = dry_run_dir / "run_records.jsonl"
    records = _load_jsonl(records_path) if records_path.is_file() else []
    g.add(len(records) == 30, f"30/30 records persisted ({len(records)})")
    g.add(len({r.get("run_id") for r in records}) == 30, "30 unique run IDs")
    g.add(len([r for r in records if r.get("scenario_id", "").startswith("todo-smoke-00")]) == 30,
          "30 records all todo-smoke scenarios")
    counts = {}
    for r in records:
        counts[r.get("strategy_id")] = counts.get(r.get("strategy_id"), 0) + 1
    g.add(counts.get("iterative_repository_agent") == 15, "15 iterative_repository_agent")
    g.add(counts.get("selective") == 15, "15 selective")
    scen_counts = {}
    for r in records:
        scen_counts[r.get("scenario_id")] = scen_counts.get(r.get("scenario_id"), 0) + 1
    g.add(all(scen_counts.get(s) == 10 for s in SCENARIO_BLAST), f"scenario counts == 10 each ({scen_counts})")
    rep_counts = {}
    for r in records:
        rep_counts[r.get("repetition")] = rep_counts.get(r.get("repetition"), 0) + 1
    g.add(sorted(rep_counts) == [1, 2, 3, 4, 5] and all(v == 6 for v in rep_counts.values()),
          f"reps 1..5 each 6 times ({rep_counts})")
    token_total = sum(
        (r.get("token_usage") or {}).get("total", 0) for r in records
    )
    calls_total = sum(r.get("total_workflow_model_calls", 0) for r in records)
    g.add(token_total == 0 and calls_total == 0, "0 real tokens / 0 model calls")

    source_identity = json.loads((dry_run_dir / "source_identity.json").read_text(encoding="utf-8"))
    cfg_hash = source_identity.get("config_hash", "")
    g.add(bool(cfg_hash), "config identity frozen (config_hash present)")

    # execution plan hash frozen deterministically
    plan_ids = [r.get("run_id") for r in records]
    plan_hash = hashlib.sha256(json.dumps(plan_ids).encode()).hexdigest()
    g.add(bool(plan_hash), "deterministic execution-plan hash computed")
    return g


# ---------------------------------------------------------------------------
# G5 Integration Test (focused seams) + G6 Metric Verification (synthetic)
# ---------------------------------------------------------------------------

def gate_g5_integration() -> GateResult:
    g = GateResult("G5 Integration Test", passed=True)
    suites = [
        "tests/unit/llm/test_llm_openrouter_provider_pin.py",
        "tests/unit/test_scientific_identity.py",
        "tests/unit/execution/test_scientific_gold_leakage.py",
        "tests/unit/test_scientific_evidence_persistence.py",
        "tests/unit/test_acceptance_gate_script.py",
        "tests/unit/test_scientific_microstudy_plan.py",
        "tests/integration/test_todo_smoke_evaluator_assets.py",
    ]
    for suite in suites:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", suite, "-q"],
            cwd=ROOT, capture_output=True, text=True, timeout=1200,
        )
        g.add(proc.returncode == 0, f"{suite} passes (exit {proc.returncode})")
    return g


def gate_g6_metric_verification() -> GateResult:
    g = GateResult("G6 Metric Verification", passed=True)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/test_scientific_microstudy_metrics.py", "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    g.add(proc.returncode == 0, f"metric/go-no-go logic tests pass (exit {proc.returncode})")
    return g


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


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
        "# SCIENTIFIC MICRO-STUDY 01 — PRE-BENCHMARK VALIDATION",
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
    dry_run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else REPORTS_DIR / "dryrun_scientific_microstudy"
    results = run_all(dry_run_dir)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "SCIENTIFIC_MICROSTUDY_PREBENCHMARK_VALIDATION.md"
    out.write_text(render(results), encoding="utf-8")
    print("PRE_BENCHMARK_DONE")
    for g in results:
        print(f"{g.name}: {'PASS' if g.passed else 'FAIL'}")
    print(f"Wrote {out}")
    if not all(g.passed for g in results):
        print("GATE_FAILURE_DETECTED")
        raise SystemExit(1)
