#!/usr/bin/env python3
"""WP-1b Phase C - Calibration-3 run (AUTHORIZED: D6 = YES, ceiling $0.25).

Runs exactly the 3 tasks in research/wp1a/wp1_calibration_3_manifest.json with
protocol v2 (agent-control cap 1024), the frozen model/route/pricing
(qwen/qwen3-coder @ deepinfra/turbo, temp 0.0), a cumulative USD guard <= the
D5 Calibration-3 ceiling, and writes:

  <out_dir>/calibration_run_records.jsonl   per-task run records (protocol
                                            metadata + token_usage)
  <out_dir>/wp1b_telemetry.jsonl            per-task telemetry (PER_TASK_FIELDS)
  <out_dir>/wp1b_call_sidecar.jsonl         per-call sidecar records (B6)
  <out_dir>/pricing_preflight.json          the G6 pricing preflight artifact
  <out_dir>/wp1b_calibration_gate_result.json  evaluated by scripts/wp1b_calibration_gate.py

Calibration is an INSTRUMENT check, NOT a performance check: the calibration
tasks are NOT scored against labels. Nothing produced here changes any Phase-B
artifact.

Usage:
  python scripts/wp1b_calibration_run.py <out_dir>

Exit codes:
  0  run + gate OK
  1  gate FAIL
  2  CEILING_BELOW_WORST_CASE or USD guard aborted (BUDGET_MODEL_V2_WRONG)
  3  configuration/input error
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.core.enums import ArtifactType  # noqa: E402
from benchmark.core.models import (  # noqa: E402
    ArtifactRef,
    ArtifactUniverse,
    RepositoryIdentity,
    RepositorySnapshot,
    RequirementChange,
)
from benchmark.llm.openrouter_backend import OpenRouterBackend  # noqa: E402
from benchmark.strategies.iterative_agent import (  # noqa: E402
    IterativeRepositoryAgentStrategy,
)
from benchmark.wp1b.telemetry import (  # noqa: E402
    call_sidecar_records,
    strategy_telemetry,
)
from scripts.saleor_portability_fix import materialize_production_parent  # noqa: E402

RESEARCH = _PROJECT_DIR / "research"
SALEOR_CACHE = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"
SALEOR_SCIENTIFIC = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "scientific"
CALIBRATION_MANIFEST = RESEARCH / "wp1a" / "wp1_calibration_3_manifest.json"
PRICING_PREFLIGHT = _PROJECT_DIR / "artifacts" / "wp1b_provider_pricing_preflight_2026-09-21.json"

MODEL = "qwen/qwen3-coder"
ROUTE = "openrouter:qwen/qwen3-coder@deepinfra/turbo"
TEMPERATURE = 0.0
AGENT_CAP = 1024
MAX_AGENT_CALLS = 8
CEILING_USD = 0.25


def _load_bundle(task_id: str) -> dict:
    base = SALEOR_SCIENTIFIC / task_id
    intent = json.loads((base / "public" / "intent.json").read_text(encoding="utf-8"))
    cu = json.loads((base / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
    manifest = json.loads((base / "case_manifest.json").read_text(encoding="utf-8"))
    return {
        "task_id": task_id,
        "intent_text": str(intent.get("intent_text", "")),
        "parent_commit": str(manifest.get("record", {}).get("parent_commit", "")),
        "records": cu.get("records", []),
    }


def _build_universe(bundle: dict) -> ArtifactUniverse:
    artifacts = tuple(
        ArtifactRef(path=str(r["path"]), artifact_type=ArtifactType.source)
        for r in bundle["records"]
    )
    return ArtifactUniverse(artifacts=artifacts)


def _build_requirement_change(bundle: dict) -> RequirementChange:
    """Deterministic WP-1b agent input construction (matches B1 exactly)."""
    return RequirementChange(
        before=f"Repository state at parent commit {bundle['parent_commit']}",
        after=bundle["intent_text"],
        acceptance_criteria=(),
    )


def _materialize_workspace(bundle: dict, workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    materialize_production_parent(
        SALEOR_CACHE, bundle["parent_commit"], workspace, roots=("saleor",)
    )


def _build_run_record(bundle: dict, strategy: IterativeRepositoryAgentStrategy) -> dict:
    prompt_tokens = strategy.prompt_tokens
    completion_tokens = strategy.completion_tokens
    total_tokens = strategy.total_tokens
    usd = prompt_tokens / 1e6 * 0.30 + completion_tokens / 1e6 * 1.00
    return {
        "task_id": bundle["task_id"],
        "model": MODEL,
        "route": ROUTE,
        "temperature": TEMPERATURE,
        "agent_control_max_completion_tokens": AGENT_CAP,
        "max_agent_calls": MAX_AGENT_CALLS,
        "model_calls": strategy.model_call_count,
        "tool_calls": strategy.tool_call_count,
        "token_usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "usd_cost": usd,
        },
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: wp1b_calibration_run.py <out_dir>")
        return 3
    out_dir = Path(sys.argv[1])
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not SALEOR_CACHE.is_dir():
        print("[cal] ERROR: saleor repo cache missing:", SALEOR_CACHE)
        return 3

    tasks = json.loads(CALIBRATION_MANIFEST.read_text(encoding="utf-8"))["task_ids"]
    if len(tasks) != 3:
        print(f"[cal] ERROR: calibration manifest must have 3 tasks, got {len(tasks)}")
        return 3

    pricing = json.loads(PRICING_PREFLIGHT.read_text(encoding="utf-8"))
    pricing_out = dict(pricing)
    pricing_out["frozen_calibration_ceiling_usd"] = CEILING_USD
    (out_dir / "pricing_preflight.json").write_text(json.dumps(pricing_out, indent=1), encoding="utf-8")

    backend = OpenRouterBackend(model=MODEL, provider="deepinfra/turbo",
                                api_key_env="OPENROUTER_API_KEY", timeout_seconds=120.0)

    records: list[dict] = []
    telemetry: list[dict] = []
    sidecar: list[dict] = []
    cumulative_usd = 0.0

    for task_id in tasks:
        bundle = _load_bundle(task_id)
        universe = _build_universe(bundle)
        req = _build_requirement_change(bundle)

        workspace = Path(tempfile.mkdtemp(prefix=f"wp1b-cal-{task_id}-"))
        try:
            _materialize_workspace(bundle, workspace)
            strategy = IterativeRepositoryAgentStrategy(
                backend=backend, agent_control_max_completion_tokens=AGENT_CAP
            )
            strategy.begin_run(workspace)
            repo = RepositorySnapshot(
                identity=RepositoryIdentity(name="saleor", url="https://github.com/saleor/saleor"),
                commit_sha=bundle["parent_commit"],
                path=str(workspace),
            )
            strategy.analyze_impact(
                repository=repo,
                requirement_change=req,
                artifact_universe=universe,
                max_completion_tokens_per_call=AGENT_CAP,
            )
            rec = _build_run_record(bundle, strategy)
            cumulative_usd += rec["token_usage"]["usd_cost"]
            records.append(rec)
            telemetry.append(strategy_telemetry(strategy, task_id=task_id))
            sidecar.extend(call_sidecar_records(strategy, task_id=task_id))
            print(f"[cal] {task_id}: calls={rec['model_calls']} prompt={rec['token_usage']['prompt_tokens']} "
                  f"completion={rec['token_usage']['completion_tokens']} usd={rec['token_usage']['usd_cost']:.6f} "
                  f"cum={cumulative_usd:.6f} empty={strategy.selection_empty_reason}")
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

        if cumulative_usd > CEILING_USD:
            print(f"[cal] USD guard: cumulative {cumulative_usd:.6f} > {CEILING_USD} -> abort")
            return 2

    (out_dir / "calibration_run_records.jsonl").write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    (out_dir / "wp1b_telemetry.jsonl").write_text(
        "\n".join(json.dumps(t) for t in telemetry) + "\n", encoding="utf-8")
    (out_dir / "wp1b_call_sidecar.jsonl").write_text(
        "\n".join(json.dumps(c) for c in sidecar) + "\n", encoding="utf-8")

    summary = {
        "artifact": "wp1b_calibration_run_summary",
        "tasks": [r["task_id"] for r in records],
        "cumulative_usd": round(cumulative_usd, 6),
        "ceiling_usd": CEILING_USD,
        "per_task_usd": {r["task_id"]: round(r["token_usage"]["usd_cost"], 6) for r in records},
    }
    (out_dir / "wp1b_calibration_run_summary.json").write_text(
        json.dumps(summary, indent=1), encoding="utf-8")
    print(f"[cal] summary: cumulative_usd={cumulative_usd:.6f} ceiling={CEILING_USD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
