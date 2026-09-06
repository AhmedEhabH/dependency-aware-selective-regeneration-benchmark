"""STAGE-C-HELDOUT-CHALLENGE-01 — exactly six Pre-Benchmark gates (D053).

Two arms for the selection-only held-out profile:
- ``iterative_repository_agent``;
- ``impact_plan``.

Per ``04_TESTS_SIX_GATES_AND_AUDIT.md`` the six gates are:

  G1 Dataset Validation
  G2 Prompt Validation
  G3 Pipeline Smoke Test (mock backends, no model calls)
  G4 Dry Run (CLI mock, exact 60-cell topology, 0 calls / 0 tokens)
  G5 Integration Test (one real NON-STUDY initial-selection probe per arm)
  G6 Metric Verification (synthetic known predictions exact)

Then an independent Audit runs, then the full test suite runs once.
This validator performs gates G1-G6 only; Audit and full suite are run
separately by the executor.
"""

from __future__ import annotations

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

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCENARIO_IDS = tuple(f"todo-heldout-{i:03d}" for i in range(1, 7))
SCENARIO_BLAST = {
    "todo-heldout-001": "localized",
    "todo-heldout-002": "localized",
    "todo-heldout-003": "moderate",
    "todo-heldout-004": "localized",
    "todo-heldout-005": "moderate",
    "todo-heldout-006": "moderate",
}
CANDIDATES = (
    "todo/models.py",
    "todo/serializers.py",
    "todo/views.py",
    "todo/permissions.py",
    "todo/urls.py",
)
PROTOCOL = "scientific-stagec-heldout-01"
AGENT = "iterative_repository_agent"
IMPACT_PLAN = "impact_plan"

# Tokens that must NOT appear in any visible requirement text (focused item 7).
FORBIDDEN_VISIBLE_TOKENS = (
    "todo/",
    ".py",
    "models.py",
    "serializers.py",
    "views.py",
    "permissions.py",
    "urls.py",
)

# Frozen gold normalized to source-file paths ONLY (D053 measurement contract).
GOLD_REGENERATE = {
    "todo-heldout-001": {"todo/models.py", "todo/serializers.py"},
    "todo-heldout-002": {"todo/views.py"},
    "todo-heldout-003": {"todo/models.py", "todo/serializers.py", "todo/views.py"},
    "todo-heldout-004": {"todo/models.py"},
    "todo-heldout-005": {"todo/permissions.py", "todo/views.py"},
    "todo-heldout-006": {"todo/models.py", "todo/serializers.py", "todo/permissions.py"},
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


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
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
    g = GateResult(f"G1 Dataset Validation ({PROTOCOL})", passed=True)
    data: dict[str, dict[str, Any]] = {}
    for sid in SCENARIO_IDS:
        p = SCENARIOS_DIR / f"{sid}.yaml"
        try:
            data[sid] = yaml.safe_load(p.read_text(encoding="utf-8"))
            g.add(data[sid].get("scenario_id") == sid, f"{sid} parses")
        except Exception as exc:
            g.add(False, f"{sid} parse failed: {exc}")
    for sid, radius in SCENARIO_BLAST.items():
        g.add(data.get(sid, {}).get("blast_radius") == radius, f"{sid} blast_radius {radius}")

    # Five-file source universe is exact (scored universe).
    profile_path = PROFILES_DIR / "todo.yaml"
    if profile_path.is_file():
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
        editable = set(profile.get("artifact_universe", {}).get("llm_editable") or [])
        g.add(set(CANDIDATES) == editable, f"five-file universe exact ({sorted(editable)})")

    # Focused item 9: architecture_constraints must be [] in every scenario.
    for sid in SCENARIO_IDS:
        cons = data.get(sid, {}).get("architecture_constraints", None)
        g.add(cons == [], f"{sid} architecture_constraints empty list ({cons!r})")

    # Focused item 7: no forbidden source-file token in visible requirements.
    for sid in SCENARIO_IDS:
        before = str(data.get(sid, {}).get("requirement_before", ""))
        after = str(data.get(sid, {}).get("requirement_after", ""))
        rationale = str(data.get(sid, {}).get("rationale", ""))
        criteria = str(data.get(sid, {}).get("acceptance_criteria", ""))
        visible = "\n".join((before, after, rationale, criteria))
        hits = [t for t in FORBIDDEN_VISIBLE_TOKENS if t in visible]
        g.add(not hits, f"{sid} visible text free of source-file names ({hits})")

    # Normalized gold audited: source-file paths only, migration/test/symbol excluded.
    from scripts.build_stagec_selection_results import FIVE_FILE_UNIVERSE

    for sid in SCENARIO_IDS:
        gold = GOLD_REGENERATE[sid]
        # Focused item 8: non-empty and within the five-file universe.
        g.add(bool(gold), f"{sid} gold non-empty")
        g.add(gold <= FIVE_FILE_UNIVERSE, f"{sid} gold subset of source universe")
        scenario_gold = set()
        actions = data[sid].get("expected_actions") or {}
        for path, action in actions.items():
            clean = path.split("#", 1)[0]
            segs = clean.split("/")
            if "migrations" in segs or "tests" in segs or clean.endswith("/"):
                continue
            if clean in FIVE_FILE_UNIVERSE and action in ("modify", "create"):
                scenario_gold.add(clean)
        g.add(scenario_gold == gold, f"{sid} normalized gold exact ({sorted(scenario_gold)})")

    return g


# ---------------------------------------------------------------------------
# G2 Prompt Validation
# ---------------------------------------------------------------------------

def gate_g2_prompt() -> GateResult:
    g = GateResult(f"G2 Prompt Validation ({PROTOCOL})", passed=True)
    try:
        from benchmark.selection.impact_planner import PLANNER_PROMPT_TEMPLATE
        from benchmark.strategies.iterative_agent import INITIAL_SYSTEM_PROMPT

        # Agent prompt: only requirement/visible criteria/editable universe/tool scope.
        g.add("Before: " in INITIAL_SYSTEM_PROMPT, "agent prompt has requirement before")
        g.add("After: " in INITIAL_SYSTEM_PROMPT, "agent prompt has requirement after")
        g.add("Acceptance criteria:" in INITIAL_SYSTEM_PROMPT, "agent prompt has visible criteria")
        g.add("Editable paths:" in INITIAL_SYSTEM_PROMPT, "agent prompt has editable universe")
        g.add("expected_actions" not in INITIAL_SYSTEM_PROMPT, "agent prompt has no expected_actions")
        g.add("GOLD_SENTINEL" not in INITIAL_SYSTEM_PROMPT, "agent prompt has no gold sentinel")
        g.add("todo_smoke_001_checks" not in INITIAL_SYSTEM_PROMPT, "agent prompt has no evaluator name")

        # No held-out gold path ever appears in the prompt templates.
        for tok in ("expected_actions", "GOLD_SENTINEL", "todo-heldout", "heldout"):
            g.add(tok not in INITIAL_SYSTEM_PROMPT, f"agent prompt has no {tok}")
            g.add(tok not in PLANNER_PROMPT_TEMPLATE, f"planner prompt has no {tok}")

        # Planner prompt: visible evidence only.
        g.add("context_set" in PLANNER_PROMPT_TEMPLATE or "candidate" in PLANNER_PROMPT_TEMPLATE,
              "planner prompt exercises candidate/evidence surface")
    except Exception as exc:
        g.add(False, f"prompt validation failed: {exc}")
    return g


# ---------------------------------------------------------------------------
# G3 Pipeline Smoke Test (selection request -> prediction -> persistence -> metrics)
# ---------------------------------------------------------------------------

def gate_g3_pipeline_smoke() -> GateResult:
    g = GateResult(f"G3 Pipeline Smoke Test ({PROTOCOL})", passed=True)
    try:
        _selection_smoke()
        g.add(True, "selection-only AnalyzeImpact -> RunRecord(selection_study) -> "
                    "RunRecordData persisted -> metrics computed (mock, 0 model calls)")
    except Exception as exc:
        g.add(False, f"pipeline smoke failed: {exc}")
    return g


def _selection_smoke() -> None:
    import tempfile

    from benchmark.checkpoint.persistence import RunRecordData
    from scripts.build_stagec_heldout_results import build

    tmp = Path(tempfile.mkdtemp())
    runs_dir = tmp / "runs"
    runs_dir.mkdir()
    run_id = "todo-heldout-001_iterative_repository_agent_rep1_smoke"
    rec = RunRecordData(
        run_id=run_id,
        profile=PROTOCOL,
        repository_id="todo",
        scenario_id="todo-heldout-001",
        strategy_id=AGENT,
        repetition=1,
        seed=42,
        status="succeeded",
        protocol_version=PROTOCOL,
        config_hash="smokehash",
        model_metadata={"model": "dry-run:mock"},
        token_usage={"prompt": 37, "completion": 11, "total": 48},
        selection_total_tokens=48,
        total_workflow_tokens=48,
        total_workflow_model_calls=1,
        predicted_actions={
            "todo/models.py": "regenerate",
            "todo/serializers.py": "regenerate",
            "todo/views.py": "preserve",
            "todo/urls.py": "preserve",
            "todo/permissions.py": "preserve",
        },
        selection_study={
            "initial_predicted_actions": {
                "todo/models.py": "regenerate",
                "todo/serializers.py": "regenerate",
                "todo/views.py": "preserve",
                "todo/urls.py": "preserve",
                "todo/permissions.py": "preserve",
            },
            "initial_regenerate_source_paths": ["todo/models.py", "todo/serializers.py"],
            "agent_selected_paths": ["todo/models.py", "todo/serializers.py"],
            "impact_plan_actions": {},
            "context_set": [],
            "validation_obligations": [],
            "finish_reason": "stop",
            "truncation": False,
            "raw_response_sha256": [],
            "failure_evidence": "",
        },
    )
    with open(runs_dir / "run_records.jsonl", "a", encoding="utf-8") as f:
        import dataclasses

        f.write(json.dumps(dataclasses.asdict(rec), sort_keys=True) + "\n")

    out = build(runs_dir, SCENARIOS_DIR, tmp / "reports")
    assert out["records"] == 1
    assert out["rows"]
    row = out["rows"][0]
    assert row["valid_finals"] == 1
    assert row["full_recall_count"] == 1


# ---------------------------------------------------------------------------
# G4 Dry Run (exact 60-cell topology, CLI mock, 0 calls / 0 tokens)
# ---------------------------------------------------------------------------

def gate_g4_dry_run(dry_run_dir: Path) -> GateResult:
    g = GateResult(f"G4 Dry Run ({PROTOCOL})", passed=True)
    if dry_run_dir.exists():
        shutil.rmtree(dry_run_dir, ignore_errors=True)
    dry_run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(ROOT / "seven_arm_benchmark.py"),
        "--profile", PROTOCOL,
        "--dry-run", "--output-dir", str(dry_run_dir),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900)
    if proc.returncode != 0:
        g.add(False, f"dry-run CLI exit {proc.returncode}: {proc.stderr[-1200:]}")
        return g
    records = _load_jsonl(dry_run_dir / "run_records.jsonl")
    g.add(len(records) == 60, f"60/60 records ({len(records)})")
    g.add(len({r.get("run_id") for r in records}) == 60, "60 unique run IDs")
    counts: dict[str, int] = {}
    scen_counts: dict[str, int] = {}
    rep_counts: dict[int, int] = {}
    for r in records:
        strategy_id = str(r.get("strategy_id"))
        scenario_id = str(r.get("scenario_id"))
        repetition = int(r.get("repetition", 0))
        counts[strategy_id] = counts.get(strategy_id, 0) + 1
        scen_counts[scenario_id] = scen_counts.get(scenario_id, 0) + 1
        rep_counts[repetition] = rep_counts.get(repetition, 0) + 1
    g.add(counts.get(AGENT) == 30, f"30 {AGENT} ({counts.get(AGENT)})")
    g.add(counts.get(IMPACT_PLAN) == 30, f"30 {IMPACT_PLAN} ({counts.get(IMPACT_PLAN)})")
    g.add(all(scen_counts.get(s) == 10 for s in SCENARIO_IDS), f"10/scenario ({scen_counts})")
    g.add(all(v == 12 for v in rep_counts.values()), f"reps 1..5 x 12 ({rep_counts})")
    calls = sum(r.get("total_workflow_model_calls", 0) for r in records)
    tokens = sum((r.get("token_usage") or {}).get("total", 0) for r in records)
    g.add(calls == 0 and tokens == 0, "0 model calls / 0 tokens")
    sid = json.loads((dry_run_dir / "source_identity.json").read_text(encoding="utf-8"))
    g.add(sid.get("profile") == PROTOCOL, "config profile frozen")
    g.add(sid.get("protocol_version") == PROTOCOL, "protocol identity frozen")
    g.add(bool(sid.get("config_hash")), "config_hash frozen")
    g.add(str(sid.get("agent_control_max_completion_tokens")) == "1024", "agent control cap frozen 1024")
    return g


# ---------------------------------------------------------------------------
# G5 Integration Test (real NON-STUDY initial-selection probe per arm)
# ---------------------------------------------------------------------------

def _real_probe(strategy: str, probe_dir: Path) -> bool:
    cmd = [
        sys.executable, str(ROOT / "seven_arm_benchmark.py"),
        "--profile", PROTOCOL,
        "--strategy", strategy,
        "--backend", "openrouter",
        "--openrouter-model", "qwen/qwen3-coder",
        "--openrouter-provider", "DeepInfra",
        "--output-dir", str(probe_dir),
        "--max-runs", "1",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=1800)
    return proc.returncode == 0


def gate_g5_integration(probe_base: Path) -> GateResult:
    g = GateResult(f"G5 Integration Test ({PROTOCOL})", passed=True)
    if probe_base.exists():
        shutil.rmtree(probe_base, ignore_errors=True)
    probe_base.mkdir(parents=True, exist_ok=True)
    for strategy in (AGENT, IMPACT_PLAN):
        probe_dir = probe_base / strategy
        ok = _real_probe(strategy, probe_dir)
        g.add(ok, f"{strategy} real NON-STUDY probe exit 0")
        if ok:
            records = _load_jsonl(probe_dir / "run_records.jsonl")
            g.add(len(records) == 1, f"{strategy} produced exactly 1 probe record")
            if records:
                rec = records[0]
                g.add(rec.get("status") == "succeeded", f"{strategy} probe terminal valid selection")
                study = rec.get("selection_study") or {}
                g.add(bool(study.get("initial_predicted_actions")), f"{strategy} INITIAL prediction captured")
                g.add(bool(study.get("initial_regenerate_source_paths") is not None),
                      f"{strategy} regenerate-source set captured")
                tok = rec.get("token_usage") or {}
                g.add(int(tok.get("total", 0)) > 0, f"{strategy} probe consumed tokens")
        else:
            g.add(False, f"{strategy} probe failed")
            probe_base.joinpath("logs").mkdir(parents=True, exist_ok=True)
            g.add(True, f"{strategy} probe artifacts at {probe_dir}")
    return g


# ---------------------------------------------------------------------------
# G6 Metric Verification (synthetic known predictions exact)
# ---------------------------------------------------------------------------

def gate_g6_metric_verification() -> GateResult:
    g = GateResult(f"G6 Metric Verification ({PROTOCOL})", passed=True)
    try:
        from scripts.build_stagec_selection_results import compute_run_metrics

        gold = {"a.py", "b.py", "c.py"}
        cases = [
            ({"a.py", "b.py", "c.py"}, (1.0, 1.0, 1.0, 0.0, True, 3)),
            ({"a.py", "b.py"}, (1.0, 2 / 3, 0.8, 1 / 3, False, 2)),
            ({"a.py", "d.py"}, (0.5, 1 / 3, 0.4, 2 / 3, False, 2)),
            ({"d.py"}, (0.0, 0.0, 0.0, 1.0, False, 1)),
            (set(), (0.0, 0.0, 0.0, 1.0, False, 0)),
        ]
        for pred, (p_expected, r_expected, f1_expected, fnr_expected, full_expected, size_expected) in cases:
            m = compute_run_metrics(set(pred), set(gold))
            assert abs(m["precision"] - p_expected) < 1e-9, (pred, m)
            assert abs(m["recall"] - r_expected) < 1e-9, (pred, m)
            assert abs(m["f1"] - f1_expected) < 1e-9, (pred, m)
            assert abs(m["fnr"] - fnr_expected) < 1e-9, (pred, m)
            assert m["full_recall"] == full_expected, (pred, m)
            assert m["write_set_size"] == size_expected, (pred, m)
        g.add(True, "synthetic precision/recall/F1/FNR/full-recall/write-set exact across 5 cases")
    except Exception as exc:
        g.add(False, f"metric verification failed: {exc}")
    return g


def run_all(dry_run_dir: Path, probe_base: Path) -> list[GateResult]:
    return [
        gate_g1_dataset(),
        gate_g2_prompt(),
        gate_g3_pipeline_smoke(),
        gate_g4_dry_run(dry_run_dir),
        gate_g5_integration(probe_base),
        gate_g6_metric_verification(),
    ]


def render(results: list[GateResult]) -> str:
    lines = [
        "# STAGE-C-HELDOUT-CHALLENGE-01 (D053) - PRE-BENCHMARK VALIDATION",
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
    lines.append("STAGEC_HELDOUT_01_REAL_RUN_AUTHORIZED=")
    lines.append("YES" if all(g.passed for g in results) else "NO")
    return "\n".join(lines)


if __name__ == "__main__":
    dry = Path(sys.argv[1]) if len(sys.argv) > 1 else REPORTS_DIR / "dryrun_stagec_heldout_01"
    probe = Path(sys.argv[2]) if len(sys.argv) > 2 else REPORTS_DIR / "stagec_heldout_01_probes"
    results = run_all(dry, probe)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "STAGEC_HELDOUT_01_PREBENCHMARK_VALIDATION.md"
    out.write_text(render(results), encoding="utf-8")
    print("STAGEC_HELDOUT_01_PRE_BENCHMARK_DONE")
    for g in results:
        print(f"{g.name}: {'PASS' if g.passed else 'FAIL'}")
    print(f"Wrote {out}")
    if not all(g.passed for g in results):
        print("GATE_FAILURE_DETECTED")
        raise SystemExit(1)
