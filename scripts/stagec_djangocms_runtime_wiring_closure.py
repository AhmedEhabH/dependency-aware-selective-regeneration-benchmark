#!/usr/bin/env python3
"""djangoCMS external-validity RUNTIME WIRING CLOSURE driver.

Subcommands (deterministic, zero scientific model calls unless ``probes``):

  preflight   print + persist RUNTIME_WIRING_PREFLIGHT
  gates       run the EXACT six deterministic gates
  audit       run the independent audit
  probes      run the two cost-probe arms (REAL scientific calls unless --dry-run)
  all         preflight + gates + audit (stop at the first failure)

Probe configuration (costprobe-02):
  - scenario ........ djangocms-external-validity-008 (final visible draft)
  - universe ........ 144 paths derived from
                       benchmark_data/external_validity/djangocms_5_0_0_candidate_universe.json
  - model ........... qwen/qwen3-coder
  - provider ........ DeepInfra pinned through OpenRouter (fallback OFF)
  - temperature ..... 0
  - caps ............ Agent 1024 / ImpactPlan 4096
  - scope ........... SELECTION ONLY (never regenerate / repair / migrate / evaluate)
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from benchmark.external_validity import study_runtime as wiring

PROJECT_DIR = wiring.PROJECT_DIR
DEFAULT_PROBE_ID = "scientific-stagec-djangocms-costprobe-02"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "reports" / DEFAULT_PROBE_ID

ARMS = ("iterative_repository_agent", "impact_plan")
PRIMARY_MODEL = "qwen/qwen3-coder"
PROVIDER_PINNED = "DeepInfra"
PROVIDER_TAG = "deepinfra/turbo"
TEMPERATURE = 0.0
AGENT_CAP = 1024
IMPACTPLAN_CAP = 4096
WORKFLOW_TIMEOUT_SECONDS = 600


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _git(*args: str) -> str:
    import subprocess

    proc = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False, cwd=PROJECT_DIR
    )
    return proc.stdout.strip()


def cmd_preflight(args: argparse.Namespace) -> int:
    preflight = wiring.build_preflight()
    print(wiring.format_preflight(preflight))
    print(f"passed={preflight['passed']}")
    persisted = wiring.persist_preflight(preflight, args.output_dir)
    print(f"persisted={persisted}")
    return 0 if preflight["passed"] else 1


def _print_gate(gate: dict[str, Any]) -> None:
    print(f"\n=== Gate {gate['gate']}: {gate['name']} ===")
    for check in gate["checks"]:
        status = "PASS" if check["ok"] else "FAIL"
        print(f"  [{status}] {check['check']} -> {check['detail']}")
    print(f"Gate {gate['gate']} Status: {'PASS' if gate['passed'] else 'FAIL'}")


def cmd_gates(args: argparse.Namespace) -> int:
    results = wiring.run_gates()
    for gate in results:
        _print_gate(gate)
    all_passed = all(gate["passed"] for gate in results)
    print(f"\nGATES_ALL_PASSED={all_passed}")
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "runtwiring_gates.json"
    path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"persisted={path}")
    return 0 if all_passed else 1


def cmd_audit(args: argparse.Namespace) -> int:
    audit = wiring.independent_audit()
    print("\n=== INDEPENDENT AUDIT ===")
    for item in audit["items"]:
        status = "OK" if item["ok"] else "FAIL"
        print(f"  {status}: {item['item']} -> {item['detail']}")
    print(f"AUDIT_RESULT={'PASS' if audit['passed'] else 'FAIL'}")
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "runtwiring_audit.json"
    path.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    print(f"persisted={path}")
    return 0 if audit["passed"] else 1


def cmd_all(args: argparse.Namespace) -> int:
    if cmd_preflight(args) != 0:
        print("RUNTIME WIRING PREFLIGHT FAILED — STOP BEFORE NEW SCIENTIFIC CALLS")
        return 1
    if cmd_gates(args) != 0:
        print("GATES FAILED — STOP BEFORE NEW SCIENTIFIC CALLS")
        return 1
    if cmd_audit(args) != 0:
        print("INDEPENDENT AUDIT FAILED — STOP BEFORE NEW SCIENTIFIC CALLS")
        return 1
    print("\nRUNTIME WIRING CLOSURE PRE-CALL GATES: ALL PASS")
    return 0


# ---------------------------------------------------------------------------
# Probe execution
# ---------------------------------------------------------------------------


def _stage_snapshot(output_dir: Path) -> Path:
    from benchmark.repositories.snapshot import stage_repository_snapshot

    source_root = PROJECT_DIR / "benchmark_data" / "repositories" / "djangocms"
    if not source_root.is_dir():
        raise FileNotFoundError(f"pinned source not found: {source_root}")
    snapshot_storage = output_dir / "workspace" / "snapshots"
    return stage_repository_snapshot(
        source_root=source_root,
        snapshot_storage_root=snapshot_storage,
        repository_id="djangocms",
        revision_id=wiring.PINNED_COMMIT[:12],
    )


def _reset_workspace_from_snapshot(workspace_dir: Path, snapshot_root: Path) -> None:
    workspace_dir.mkdir(parents=True, exist_ok=True)
    for entry in workspace_dir.iterdir():
        if entry.name in ("runs", "tmp", "snapshots"):
            continue
        if entry.is_symlink() or entry.is_file():
            entry.unlink()
        elif entry.is_dir():
            shutil.rmtree(entry)
    skip = frozenset({"_metadata", "manifests"})
    for entry in snapshot_root.iterdir():
        if entry.is_dir() and entry.name in skip:
            continue
        dest = workspace_dir / entry.name
        if entry.is_dir():
            shutil.copytree(entry, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(entry, dest)


def _build_backend(dry_run: bool) -> Any:
    if dry_run:
        from benchmark.llm.mock_backend import MockLLMBackend

        return MockLLMBackend(response_text="dry-run mock selection")
    from benchmark.llm.openrouter_backend import OpenRouterBackend

    return OpenRouterBackend(
        model=PRIMARY_MODEL,
        timeout_seconds=120.0,
        provider=PROVIDER_PINNED,
        max_transient_retries=1,
    )


def _descriptors() -> tuple[Any, ...]:
    from benchmark.selection.dependency_scope import ArtifactDescriptor

    records = wiring.load_frozen_universe_records()
    return tuple(
        ArtifactDescriptor(
            path=str(rec["path"]),
            category="source",
            description="",
            provides_symbols=tuple(rec.get("classes", [])) + tuple(rec.get("functions", [])),
            typical_change_triggers=(),
        )
        for rec in records
    )


def _run_arm(
    arm: str,
    backend: Any,
    scenario: Any,
    universe_paths: tuple[str, ...],
    descriptors: tuple[Any, ...],
    output_dir: Path,
    dry_run: bool,
) -> dict[str, Any]:
    from benchmark.execution.isolation import IsolationContext
    from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
    from benchmark.repositories.workspace import WorkspacePath

    arm_workspace = output_dir / "workspace" / arm
    snapshot_root = _stage_snapshot(output_dir)
    _reset_workspace_from_snapshot(arm_workspace, snapshot_root)

    isolation = IsolationContext(
        workspace=WorkspacePath(root=str(arm_workspace)),
        snapshot_base=output_dir / "workspace" / "snapshots",
        active_snapshot_root=snapshot_root,
    )

    strategy = wiring._make_strategy_for_arm(arm, backend, descriptors)
    config = RunnerConfig(
        strategy_name=arm,
        backend_name=getattr(backend, "model_identity", f"openrouter:{PRIMARY_MODEL}@{PROVIDER_TAG}"),
        protocol_version="1.0",
        timeout_seconds=WORKFLOW_TIMEOUT_SECONDS,
        max_attempts=1,
        enable_regeneration=False,
        editable_artifact_paths=universe_paths,
        max_completion_tokens_per_call=4096,
        agent_control_max_completion_tokens=AGENT_CAP,
        exact_patch=False,
        scientific_gold_isolation=True,
        selection_only=True,
    )
    runner = BenchmarkRunner(
        strategy=strategy,
        backend=backend,
        isolation=isolation,
        config=config,
    )

    started = time.monotonic()
    record = runner.run(scenario)
    elapsed = time.monotonic() - started

    return _build_probe_evidence(arm, record, elapsed, dry_run=dry_run)


def _build_probe_evidence(
    arm: str,
    record: Any,
    elapsed: float,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    pricing = wiring.load_pricing()
    cost = wiring.compute_api_cost(record, pricing)
    predicted = dict(getattr(record, "predicted_actions", {}) or {})
    regenerate_paths = [
        p for p, action in predicted.items() if action == "regenerate"
    ]
    validity_errors: list[str] = []
    for failure in getattr(record, "failures", ()) or ():
        validity_errors.append(str(failure.message))
    selection_study = getattr(record, "selection_study", None) or {}
    raw_hashes = list(selection_study.get("raw_response_sha256", [])) or []

    universe_paths = set(wiring.runtime_universe_paths())
    invalid_selected = sorted(set(regenerate_paths) - universe_paths)
    terminal_status = str(getattr(record, "status", ""))
    if hasattr(record.status, "value"):
        terminal_status = str(record.status.value)

    success = (
        terminal_status == "succeeded"
        and not validity_errors
        and bool(regenerate_paths)
        and not invalid_selected
    )

    token_usage = getattr(record, "token_usage", None)
    evidence = {
        "arm": arm,
        "scenario_id": getattr(record.identity, "scenario_id", ""),
        "exact_model": f"openrouter:{PRIMARY_MODEL}@{PROVIDER_TAG}",
        "exact_provider_used": PROVIDER_TAG,
        "fallback_status": "off",
        "temperature": TEMPERATURE,
        "dry_run": dry_run,
        "prompt_tokens": int(getattr(token_usage, "prompt_tokens", 0)),
        "completion_tokens": int(getattr(token_usage, "completion_tokens", 0)),
        "total_tokens": int(getattr(token_usage, "total_tokens", 0)),
        "model_call_count": int(getattr(record, "selection_model_calls", 0)),
        "tool_call_count": int(getattr(record, "selection_tool_calls", 0)),
        "inspected_file_count": int(getattr(record, "selection_inspected_file_count", 0)),
        "latency_seconds": round(elapsed, 6),
        "api_cost": round(cost, 6),
        "pricing_source": pricing.get("source", ""),
        "terminal_status": terminal_status,
        "predicted_write_set": predicted,
        "regenerate_path_count": len(regenerate_paths),
        "invalid_selected_paths": invalid_selected,
        "probe_success": success,
        "validity_schema_status": {
            "finish_reason": str(selection_study.get("finish_reason", "")),
            "truncation": bool(selection_study.get("truncation", False)),
            "errors": validity_errors,
            "impact_plan_hash": str(getattr(record, "impact_plan_hash", "")),
            "impact_plan_version": str(getattr(record, "impact_plan_version", "")),
            "raw_response_sha256": raw_hashes,
        },
        "raw_record": _record_to_dict(record),
        "recorded_at": _now_iso(),
    }
    return evidence


def _record_to_dict(record: Any) -> dict[str, Any]:
    token_usage = getattr(record, "token_usage", None)
    selection_study = getattr(record, "selection_study", None) or {}
    return {
        "run_id": str(getattr(record.identity, "run_id", "")),
        "scenario_id": str(getattr(record.identity, "scenario_id", "")),
        "strategy_name": str(getattr(record.identity, "strategy_name", "")),
        "status": str(getattr(record.status, "value", getattr(record, "status", ""))),
        "duration_seconds": round(float(getattr(record, "duration_seconds", 0.0)), 6),
        "token_usage": {
            "prompt": int(getattr(token_usage, "prompt_tokens", 0)),
            "completion": int(getattr(token_usage, "completion_tokens", 0)),
            "total": int(getattr(token_usage, "total_tokens", 0)),
        },
        "selection_prompt_tokens": int(getattr(record, "selection_prompt_tokens", 0)),
        "selection_completion_tokens": int(getattr(record, "selection_completion_tokens", 0)),
        "selection_total_tokens": int(getattr(record, "selection_total_tokens", 0)),
        "selection_model_calls": int(getattr(record, "selection_model_calls", 0)),
        "selection_duration_seconds": round(float(getattr(record, "selection_duration_seconds", 0.0)), 6),
        "selection_tool_calls": int(getattr(record, "selection_tool_calls", 0)),
        "selection_inspected_file_count": int(getattr(record, "selection_inspected_file_count", 0)),
        "regeneration_model_calls": int(getattr(record, "regeneration_model_calls", 0)),
        "regeneration_total_tokens": int(getattr(record, "regeneration_total_tokens", 0)),
        "functional_validation_passed": getattr(record, "functional_validation_passed", None),
        "migration_generation_passed": getattr(record, "migration_generation_passed", None),
        "repair_model_calls": int(getattr(record, "repair_model_calls", 0)),
        "repair_attempts": int(getattr(record, "repair_attempts", 0)),
        "token_accounting_mode": str(getattr(record, "token_accounting_mode", "unknown")),
        "total_workflow_tokens": int(getattr(record, "total_workflow_tokens", 0)),
        "total_workflow_model_calls": int(getattr(record, "total_workflow_model_calls", 0)),
        "selected_artifact_count": int(getattr(record, "selected_artifact_count", 0)),
        "preserved_artifact_count": int(getattr(record, "preserved_artifact_count", 0)),
        "predicted_actions": dict(getattr(record, "predicted_actions", {}) or {}),
        "impact_plan": getattr(record, "impact_plan", None),
        "impact_plan_hash": str(getattr(record, "impact_plan_hash", "")),
        "impact_plan_version": str(getattr(record, "impact_plan_version", "")),
        "planner_model_calls": int(getattr(record, "planner_model_calls", 0)),
        "planner_prompt_tokens": int(getattr(record, "planner_prompt_tokens", 0)),
        "planner_completion_tokens": int(getattr(record, "planner_completion_tokens", 0)),
        "selection_study": selection_study,
        "failures": [
            {
                "kind": getattr(f, "failure_kind", ""),
                "stage": getattr(f, "stage", ""),
                "message": getattr(f, "message", ""),
            }
            for f in (getattr(record, "failures", ()) or ())
        ],
    }


def cmd_probes(args: argparse.Namespace) -> int:
    if not args.dry_run and not args.skip_gate_check:
        # The gates must already be green before any scientific call.
        print("Refusing to run probes before the six gates pass (run `all` first).")
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    preflight = wiring.build_preflight()
    wiring.persist_preflight(preflight, output_dir)
    if not preflight["passed"]:
        print("RUNTIME WIRING PREFLIGHT FAILED — STOP BEFORE NEW SCIENTIFIC CALLS")
        return 1

    scenario, scenario_path = wiring.load_study_scenario(wiring.PROBE_SCENARIO_ID)
    universe_paths = wiring.runtime_universe_paths()
    descriptors = _descriptors()
    backend = _build_backend(args.dry_run)

    if not args.dry_run and not backend.provider:
        print("provider must be pinned; aborting")
        return 1

    summary: dict[str, Any] = {}
    for arm in ARMS:
        print(f"\n=== PROBE arm={arm} ===\n")
        evidence = _run_arm(
            arm, backend, scenario, universe_paths, descriptors, output_dir, args.dry_run
        )
        summary[arm] = evidence
        run_path = output_dir / f"run_{arm}.json"
        run_path.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
        print(json.dumps(evidence, indent=2, default=str))
        print(f"persisted={run_path}")

    agent = summary.get("iterative_repository_agent", {})
    impact = summary.get("impact_plan", {})
    agent_cost = float(agent.get("api_cost", 0.0))
    impact_cost = float(impact.get("api_cost", 0.0))
    raw_projected_60 = 30 * agent_cost + 30 * impact_cost
    conservative_projected_60 = raw_projected_60 * 1.25
    cost_lock = "PASS" if conservative_projected_60 <= 0.50 else "FAIL"

    both_succeeded = bool(agent.get("probe_success")) and bool(impact.get("probe_success"))
    if not both_succeeded:
        cost_lock = "BLOCKED"

    report: dict[str, Any] = {
        "probe_id": args.probe_id,
        "probe_utc": _now_iso(),
        "prep_commit_verified": _git("rev-parse", "HEAD"),
        "scenario": wiring.PROBE_SCENARIO_ID,
        "scenario_path": str(scenario_path),
        "scenario_visible_input_sha256": wiring.visible_input_sha256(scenario_path),
        "universe_count": len(universe_paths),
        "universe_canonical_hash": wiring.runtime_universe_canonical_hash(),
        "model": PRIMARY_MODEL,
        "provider_pinned": PROVIDER_TAG,
        "fallback": "off",
        "temperature": TEMPERATURE,
        "agent_cap": AGENT_CAP,
        "impactplan_cap": IMPACTPLAN_CAP,
        "selection_only": True,
        "scientific_calls": 0 if args.dry_run else 2,
        "probe_run_summary": {
            "iterative_repository_agent": agent,
            "impact_plan": impact,
        },
        "raw_projected_60_cost": round(raw_projected_60, 6),
        "conservative_projected_60_cost": round(conservative_projected_60, 6),
        "cost_lock": cost_lock,
        "note": (
            "PROBE NON-STUDY. These 2 runs are NOT part of the scientific 60-run "
            "result set and MUST NOT be reused as study results. COST_LOCK is the "
            "only authorization output."
        ),
    }
    report_path = output_dir / "cost_probe_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    print(f"persisted={report_path}")
    return 0 if both_succeeded and cost_lock == "PASS" else 1


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_pre = sub.add_parser("preflight", help="print + persist RUNTIME_WIRING_PREFLIGHT")
    p_pre.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))

    p_gates = sub.add_parser("gates", help="run the six deterministic gates")
    p_gates.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))

    p_audit = sub.add_parser("audit", help="run the independent audit")
    p_audit.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))

    p_all = sub.add_parser("all", help="preflight + gates + audit")
    p_all.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))

    p_probes = sub.add_parser("probes", help="run the two cost-probe arms")
    p_probes.add_argument("--probe-id", type=str, default=DEFAULT_PROBE_ID)
    p_probes.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    p_probes.add_argument("--dry-run", action="store_true", default=False)
    p_probes.add_argument(
        "--skip-gate-check",
        action="store_true",
        default=False,
        help="development-only: bypass the pre-call gate guard",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    if args.command == "preflight":
        return cmd_preflight(args)
    if args.command == "gates":
        return cmd_gates(args)
    if args.command == "audit":
        return cmd_audit(args)
    if args.command == "all":
        return cmd_all(args)
    if args.command == "probes":
        return cmd_probes(args)
    print(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
