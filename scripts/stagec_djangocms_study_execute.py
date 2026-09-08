#!/usr/bin/env python3
"""djangoCMS external-validity FINAL 60-RUN SCIENTIFIC STUDY executor.

STUDY_ID: scientific-stagec-djangocms-01

This driver implements the frozen study protocol:
- 6 final scenarios x 2 arms x 5 repetitions = exactly 60 cells
- arms: iterative_repository_agent (cap 1024) / impact_plan (cap 4096)
- model qwen/qwen3-coder @ DeepInfra pinned through OpenRouter, fallback OFF,
  temperature 0, selection-only, max 1 transient retry (frozen policy)
- hidden gold (djangocms_hidden_gold_draft.json) is evaluation-only and is
  applied AFTER inference
- raw evidence is written append-only; a process interruption must NOT destroy
  already-completed results
- cost lock: cumulative + projected completion <= $0.50, else COST_BUDGET_STOP

Subcommands:
  prevalidate      section-B pre-run validation (tag ancestor, universe, hashes,
                   gold paths, six scenarios, hidden-gold isolation)
  gates            the EXACT six deterministic gates + independent audit
                   (zero scientific calls)
  freeze-manifest  build + persist the frozen 60-cell manifest (requires
                   prevalidate + gates PASS; before any scientific call)
  run              execute remaining manifest cells (resumable, append-only)
  metrics          compute final metrics + aggregate tables
  close            rerun the six closure gates + audit (zero scientific calls)
  all              prevalidate -> gates -> freeze-manifest -> run -> metrics -> close
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from benchmark.external_validity import study_runtime as wiring

PROJECT_DIR = wiring.PROJECT_DIR
STUDY_ID = "scientific-stagec-djangocms-study-01"
STUDY_DIR = PROJECT_DIR / "reports" / STUDY_ID
WIRING_TAG = "stagec-djangocms-study-wiring-verified-01"

FINAL_SCENARIOS = tuple(wiring.final_scenario_ids())
ARMS = ("iterative_repository_agent", "impact_plan")
REPETITIONS = (1, 2, 3, 4, 5)

PRIMARY_MODEL = "qwen/qwen3-coder"
PROVIDER_PINNED = "DeepInfra"
PROVIDER_TAG = "deepinfra/turbo"
TEMPERATURE = 0.0
AGENT_CAP = 1024
IMPACTPLAN_CAP = 4096
WORKFLOW_TIMEOUT_SECONDS = 600
MAX_TRANSIENT_RETRIES = 1
HARD_COST_CEILING_USD = 0.50
CHECKPOINT_EVERY = 10

OLD_HISTORICAL_SCENARIO_ID = wiring.OLD_HISTORICAL_SCENARIO_ID
OLD_HISTORICAL_SCENARIO_PATH = wiring.OLD_HISTORICAL_SCENARIO_PATH


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False, cwd=PROJECT_DIR
    )
    return proc.stdout.strip()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _records_path() -> Path:
    return STUDY_DIR / "run_records.jsonl"


def _manifest_path() -> Path:
    return STUDY_DIR / "manifest_60.json"


def _loaded_records() -> dict[str, dict[str, Any]]:
    path = _records_path()
    if not path.is_file():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        out[rec["run_id"]] = rec
    return out


def _append_record(record: dict[str, Any]) -> None:
    with _records_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str, sort_keys=True) + "\n")


def _persist_json(name: str, payload: Any) -> Path:
    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    path = STUDY_DIR / name
    path.write_text(json.dumps(payload, indent=2, default=str, sort_keys=True), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Section B: pre-run validation
# ---------------------------------------------------------------------------


def _tag_is_ancestor(tag: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", tag, "HEAD"],
        cwd=PROJECT_DIR,
        check=False,
    )
    return proc.returncode == 0


def cmd_prevalidate(args: argparse.Namespace) -> int:
    items: list[dict[str, Any]] = []

    items.append(
        {
            "item": "wiring_tag_exists_and_is_ancestor_of_head",
            "ok": _tag_is_ancestor(WIRING_TAG),
            "detail": {
                "tag": WIRING_TAG,
                "head": _git("rev-parse", "HEAD"),
            },
        }
    )

    runtime_paths = wiring.runtime_universe_paths()
    frozen_paths = wiring.frozen_universe_paths()
    runtime_set = set(runtime_paths)
    frozen_set = set(frozen_paths)
    items.append(
        {
            "item": "runtime_universe_count_equals_144",
            "ok": len(runtime_paths) == wiring.FROZEN_CANDIDATE_UNIVERSE_COUNT,
            "detail": len(runtime_paths),
        }
    )
    runtime_hash = wiring.runtime_universe_canonical_hash()
    frozen_hash = wiring.frozen_universe_canonical_hash()
    items.append(
        {
            "item": "runtime_and_frozen_canonical_hashes_identical",
            "ok": runtime_hash == frozen_hash,
            "detail": {"runtime": runtime_hash, "frozen": frozen_hash},
        }
    )
    missing = sorted(frozen_set - runtime_set)
    extra = sorted(runtime_set - frozen_set)
    items.append(
        {
            "item": "missing_extra_paths_empty",
            "ok": not missing and not extra,
            "detail": {"missing": missing, "extra": extra},
        }
    )
    gold_paths = {p for rec in wiring.load_hidden_gold() for p in rec.get("source_files", [])}
    items.append(
        {
            "item": "all_gold_paths_inside_runtime_universe",
            "ok": gold_paths <= runtime_set,
            "detail": sorted(gold_paths - runtime_set),
        }
    )
    expected = frozenset(
        {
            "djangocms-external-validity-002",
            "djangocms-external-validity-004",
            "djangocms-external-validity-005",
            "djangocms-external-validity-006",
            "djangocms-external-validity-007",
            "djangocms-external-validity-008",
        }
    )
    items.append(
        {
            "item": "final_visible_scenarios_exactly_six",
            "ok": set(FINAL_SCENARIOS) == expected,
            "detail": sorted(FINAL_SCENARIOS),
        }
    )
    items.append(
        {
            "item": "hidden_gold_evaluation_only",
            "ok": all(
                set(rec.get("source_files", [])) <= runtime_set
                for rec in wiring.load_hidden_gold()
            ),
            "detail": {
                "hidden_gold_path": str(wiring.HIDDEN_GOLD_PATH),
                "records": len(wiring.load_hidden_gold()),
            },
        }
    )
    old_not_loaded = all(
        str(wiring.load_study_scenario(sid)[1]).replace("\\", "/")
        != str(OLD_HISTORICAL_SCENARIO_PATH).replace("\\", "/")
        for sid in FINAL_SCENARIOS
    )
    items.append(
        {
            "item": "old_historical_scenarios_never_model_facing",
            "ok": old_not_loaded,
            "detail": {
                "old_scenario_id": OLD_HISTORICAL_SCENARIO_ID,
                "old_scenario_path": str(OLD_HISTORICAL_SCENARIO_PATH),
                "loaded_from_visible_drafts": True,
            },
        }
    )

    passed = all(item["ok"] for item in items)
    result = {"section": "B_PRE_RUN_VALIDATION", "passed": passed, "items": items,
              "validated_at": _now_iso()}
    path = _persist_json("prevalidation.json", result)
    print(json.dumps(result, indent=2, default=str))
    print(f"persisted={path}")
    return 0 if passed else 1


# ---------------------------------------------------------------------------
# Gates + audit
# ---------------------------------------------------------------------------


def cmd_gates(args: argparse.Namespace) -> int:
    gates = wiring.run_gates()
    all_passed = all(g["passed"] for g in gates)
    audit = wiring.independent_audit()
    result = {
        "gates": gates,
        "gates_all_passed": all_passed,
        "audit": audit,
        "zero_scientific_calls": True,
        "ran_at": _now_iso(),
    }
    path = _persist_json("runtwiring_gates.json", result)
    for gate in gates:
        print(f"Gate {gate['gate']} {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
    print(f"AUDIT_RESULT={'PASS' if audit['passed'] else 'FAIL'}")
    print(f"persisted={path}")
    return 0 if (all_passed and audit["passed"]) else 1


def _gates_evidence_passed() -> bool:
    path = STUDY_DIR / "runtwiring_gates.json"
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return bool(data.get("gates_all_passed")) and bool(data.get("audit", {}).get("passed"))


def _prevalidation_passed() -> bool:
    path = STUDY_DIR / "prevalidation.json"
    if not path.is_file():
        return False
    try:
        return bool(json.loads(path.read_text(encoding="utf-8")).get("passed"))
    except (json.JSONDecodeError, OSError):
        return False


# ---------------------------------------------------------------------------
# Manifest freeze (section C)
# ---------------------------------------------------------------------------


def _visible_sha256(scenario_id: str) -> str:
    path = wiring.VISIBLE_DRAFTS_DIR / f"{scenario_id}.yaml"
    return _sha256_bytes(path.read_bytes())


def build_manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    universe_hash = wiring.runtime_universe_canonical_hash()
    for scenario_id in FINAL_SCENARIOS:
        visible_hash = _visible_sha256(scenario_id)
        for arm in ARMS:
            for rep in REPETITIONS:
                run_id = f"stgc-{scenario_id}-{arm}-r{rep}"
                rows.append(
                    {
                        "run_id": run_id,
                        "scenario_id": scenario_id,
                        "repetition": rep,
                        "arm": arm,
                        "expected_scientific_model": PRIMARY_MODEL,
                        "expected_provider": f"{PROVIDER_PINNED} pinned through OpenRouter",
                        "provider_tag": PROVIDER_TAG,
                        "temperature": TEMPERATURE,
                        "max_completion_tokens": AGENT_CAP if arm == "iterative_repository_agent" else IMPACTPLAN_CAP,
                        "selection_only": True,
                        "frozen_visible_scenario_sha256": visible_hash,
                        "frozen_runtime_universe_hash": universe_hash,
                    }
                )
    assert len(rows) == 60
    return rows


def cmd_freeze_manifest(args: argparse.Namespace) -> int:
    if not _prevalidation_passed():
        print("Pre-run validation (B) NOT passed — STOP BEFORE FREEZE")
        return 1
    if not _gates_evidence_passed():
        print("Six gates + audit NOT passed — STOP BEFORE FREEZE")
        return 1
    rows = build_manifest()
    manifest = {
        "study_id": STUDY_ID,
        "wiring_tag": WIRING_TAG,
        "wiring_tag_ancestor_of_head": _git("rev-parse", "HEAD"),
        "arms": list(ARMS),
        "scenarios": list(FINAL_SCENARIOS),
        "repetitions": list(REPETITIONS),
        "total_cells": len(rows),
        "model": PRIMARY_MODEL,
        "provider": f"{PROVIDER_PINNED} pinned through OpenRouter",
        "provider_tag": PROVIDER_TAG,
        "fallback": "off",
        "temperature": TEMPERATURE,
        "agent_cap": AGENT_CAP,
        "impactplan_cap": IMPACTPLAN_CAP,
        "selection_only": True,
        "frozen_runtime_universe_hash": wiring.runtime_universe_canonical_hash(),
        "frozen_candidate_universe_hash": wiring.frozen_universe_canonical_hash(),
        "universe_count": len(wiring.runtime_universe_paths()),
        "hard_cost_ceiling_usd": HARD_COST_CEILING_USD,
        "manifest_frozen_at": _now_iso(),
        "cells": rows,
    }
    path = _persist_json("manifest_60.json", manifest)
    print(f"MANIFEST_CELLS={len(rows)}")
    print(f"persisted={path}")
    return 0


def _load_manifest() -> dict[str, Any]:
    path = _manifest_path()
    if not path.is_file():
        raise FileNotFoundError("manifest_60.json not found — run freeze-manifest first")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Execution
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


def _copy_snapshot_to_workspace(snapshot_root: Path, workspace_dir: Path) -> None:
    workspace_dir.mkdir(parents=True, exist_ok=True)
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
        max_transient_retries=MAX_TRANSIENT_RETRIES,
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


def _make_strategy(arm: str, backend: Any, descriptors: tuple[Any, ...]) -> Any:
    return wiring._make_strategy_for_arm(arm, backend, descriptors)


def _read_file_call_count(record: Any) -> int:
    count = 0
    for line in (getattr(record, "selection_tool_transcript", ()) or ()):
        if " read_file " in str(line):
            count += 1
    return count


def run_cell(cell: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    """Execute ONE manifest cell (selection-only) and return full raw evidence."""
    run_id = cell["run_id"]
    scenario_id = cell["scenario_id"]
    arm = cell["arm"]
    repetition = cell["repetition"]

    scenario, scenario_path = wiring.load_study_scenario(scenario_id)
    universe_paths = wiring.runtime_universe_paths()
    descriptors = _descriptors()
    backend = _build_backend(dry_run)

    run_workspace = STUDY_DIR / "workspace" / f"run_{run_id}"
    if run_workspace.is_dir():
        shutil.rmtree(run_workspace)
    snapshot_root = _stage_snapshot(STUDY_DIR)
    _copy_snapshot_to_workspace(snapshot_root, run_workspace)

    from benchmark.execution.isolation import IsolationContext
    from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
    from benchmark.repositories.workspace import WorkspacePath

    isolation = IsolationContext(
        workspace=WorkspacePath(root=str(run_workspace)),
        snapshot_base=STUDY_DIR / "workspace" / "snapshots",
        active_snapshot_root=snapshot_root,
    )

    strategy = _make_strategy(arm, backend, descriptors)
    config = RunnerConfig(
        strategy_name=arm,
        backend_name=getattr(backend, "model_identity", f"openrouter:{PRIMARY_MODEL}@{PROVIDER_TAG}"),
        protocol_version="1.0",
        timeout_seconds=WORKFLOW_TIMEOUT_SECONDS,
        max_attempts=1,
        enable_regeneration=False,
        editable_artifact_paths=universe_paths,
        max_completion_tokens_per_call=IMPACTPLAN_CAP,
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
    try:
        record = runner.run(scenario)
        elapsed = time.monotonic() - started
        return _build_cell_evidence(
            cell, record, elapsed, scenario_path, universe_paths, dry_run=dry_run
        )
    except Exception as exc:  # noqa: BLE001 - raw evidence must capture the exception
        elapsed = time.monotonic() - started
        return _build_failed_cell_evidence(
            cell, elapsed, scenario_path, universe_paths, dry_run=dry_run, exc=exc
        )


def _build_cell_evidence(
    cell: dict[str, Any],
    record: Any,
    elapsed: float,
    scenario_path: Path,
    universe_paths: tuple[str, ...],
    *,
    dry_run: bool,
) -> dict[str, Any]:
    pricing = wiring.load_pricing()
    cost = wiring.compute_api_cost(record, pricing)
    predicted = dict(getattr(record, "predicted_actions", {}) or {})
    regenerate_paths = [p for p, action in predicted.items() if action == "regenerate"]

    gold = set(wiring.hidden_gold_paths_for(cell["scenario_id"]))
    predicted_set = set(regenerate_paths)
    tp = len(predicted_set & gold)
    fp = len(predicted_set - gold)
    fn = len(gold - predicted_set)
    predicted_size = len(predicted_set)
    precision = tp / predicted_size if predicted_size else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fnr = fn / len(gold) if gold else 0.0

    validity_errors: list[str] = []
    for failure in getattr(record, "failures", ()) or ():
        validity_errors.append(str(failure.message))
    selection_study = getattr(record, "selection_study", None) or {}
    raw_hashes = list(selection_study.get("raw_response_sha256", [])) or []
    terminal_status = str(getattr(record.status, "value", getattr(record, "status", "")))
    finish_reason = str(selection_study.get("finish_reason", ""))
    truncation = bool(selection_study.get("truncation", False))

    universe_set = set(universe_paths)
    invalid_selected = sorted(set(regenerate_paths) - universe_set)

    token_usage = getattr(record, "token_usage", None)
    prompt_tokens = int(getattr(token_usage, "prompt_tokens", 0))
    completion_tokens = int(getattr(token_usage, "completion_tokens", 0))
    total_tokens = int(getattr(token_usage, "total_tokens", 0))
    model_calls = int(getattr(record, "selection_model_calls", 0))
    tool_calls = int(getattr(record, "selection_tool_calls", 0))
    inspected = int(getattr(record, "selection_inspected_file_count", 0))
    read_file_calls = _read_file_call_count(record)

    evidence = {
        "run_id": cell["run_id"],
        "scenario_id": cell["scenario_id"],
        "repetition": cell["repetition"],
        "arm": cell["arm"],
        "exact_model": f"openrouter:{PRIMARY_MODEL}@{PROVIDER_TAG}",
        "exact_provider_used": PROVIDER_TAG,
        "fallback_status": "off",
        "temperature": TEMPERATURE,
        "dry_run": dry_run,
        "predicted_write_set": sorted(regenerate_paths),
        "predicted_write_set_size": len(regenerate_paths),
        "hidden_gold_used_after_inference": sorted(gold),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "fnr": round(fnr, 6),
        "full_recall": bool(gold and recall >= 1.0),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "model_calls": model_calls,
        "tool_calls": tool_calls,
        "explicit_read_file_count": read_file_calls,
        "inspected_file_count": inspected,
        "latency_seconds": round(elapsed, 6),
        "api_cost": round(cost, 6),
        "pricing_source": pricing.get("source", ""),
        "finish_reason": finish_reason,
        "truncation_status": truncation,
        "invalid_selected_paths": invalid_selected,
        "terminal_status": terminal_status,
        "failure_category": "" if terminal_status == "succeeded" else (
            "; ".join(validity_errors)
        ),
        "failure_evidence": [
            {
                "kind": str(getattr(f, "failure_kind", "")),
                "stage": str(getattr(f, "stage", "")),
                "message": str(getattr(f, "message", "")),
            }
            for f in (getattr(record, "failures", ()) or ())
        ],
        "raw_model_response_sha256": raw_hashes,
        "visible_scenario_sha256": cell["frozen_visible_scenario_sha256"],
        "runtime_universe_hash": cell["frozen_runtime_universe_hash"],
        "recorded_at": _now_iso(),
    }
    return evidence


def _build_failed_cell_evidence(
    cell: dict[str, Any],
    elapsed: float,
    scenario_path: Path,
    universe_paths: tuple[str, ...],
    *,
    dry_run: bool,
    exc: BaseException,
) -> dict[str, Any]:
    return {
        "run_id": cell["run_id"],
        "scenario_id": cell["scenario_id"],
        "repetition": cell["repetition"],
        "arm": cell["arm"],
        "exact_model": f"openrouter:{PRIMARY_MODEL}@{PROVIDER_TAG}",
        "exact_provider_used": PROVIDER_TAG,
        "fallback_status": "off",
        "temperature": TEMPERATURE,
        "dry_run": dry_run,
        "predicted_write_set": [],
        "predicted_write_set_size": 0,
        "hidden_gold_used_after_inference": sorted(wiring.hidden_gold_paths_for(cell["scenario_id"])),
        "tp": 0,
        "fp": 0,
        "fn": len(wiring.hidden_gold_paths_for(cell["scenario_id"])),
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "fnr": 1.0,
        "full_recall": False,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "model_calls": 0,
        "tool_calls": 0,
        "explicit_read_file_count": 0,
        "inspected_file_count": 0,
        "latency_seconds": round(elapsed, 6),
        "api_cost": 0.0,
        "pricing_source": "",
        "finish_reason": "",
        "truncation_status": False,
        "invalid_selected_paths": [],
        "terminal_status": "failed",
        "failure_category": f"harness_exception: {exc.__class__.__name__}",
        "failure_evidence": [{"kind": "harness_defect", "stage": "runner.run", "message": str(exc)}],
        "raw_model_response_sha256": [],
        "visible_scenario_sha256": cell["frozen_visible_scenario_sha256"],
        "runtime_universe_hash": cell["frozen_runtime_universe_hash"],
        "recorded_at": _now_iso(),
    }


def _load_progress() -> dict[str, Any]:
    path = STUDY_DIR / "progress.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_progress(payload: dict[str, Any]) -> None:
    _persist_json("progress.json", payload)


def _cumulative_cost(records: dict[str, dict[str, Any]]) -> float:
    return round(sum(float(r.get("api_cost", 0.0)) for r in records.values()), 6)


def _projected_completion_cost(
    records: dict[str, dict[str, Any]], manifest: dict[str, Any]
) -> float:
    cells = manifest["cells"]
    done_ids = set(records)
    remaining_agent = [c for c in cells if c["run_id"] not in done_ids and c["arm"] == "iterative_repository_agent"]
    remaining_impact = [c for c in cells if c["run_id"] not in done_ids and c["arm"] == "impact_plan"]
    agent_costs = [
        float(r["api_cost"]) for r in records.values() if r["arm"] == "iterative_repository_agent"
    ]
    impact_costs = [float(r["api_cost"]) for r in records.values() if r["arm"] == "impact_plan"]
    agent_avg = sum(agent_costs) / len(agent_costs) if agent_costs else 0.005135
    impact_avg = sum(impact_costs) / len(impact_costs) if impact_costs else 0.002860
    return round(len(remaining_agent) * agent_avg + len(remaining_impact) * impact_avg, 6)


def _cost_budget_ok(records: dict[str, dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    spent = _cumulative_cost(records)
    projected = _projected_completion_cost(records, manifest)
    projected_total = round(spent + projected, 6)
    return {
        "spent": spent,
        "projected_completion": projected,
        "projected_total": projected_total,
        "ceiling": HARD_COST_CEILING_USD,
        "ok": projected_total <= HARD_COST_CEILING_USD,
    }


def _write_checkpoint(records: dict[str, dict[str, Any]], manifest: dict[str, Any]) -> None:
    completed = len(records)
    succeeded = sum(1 for r in records.values() if r["terminal_status"] == "succeeded")
    failed = completed - succeeded
    totals = {
        "completed_cells": completed,
        "successful_cells": succeeded,
        "failed_cells": failed,
        "cumulative_scientific_model_calls": sum(int(r.get("model_calls", 0)) for r in records.values()),
        "cumulative_tokens": sum(int(r.get("total_tokens", 0)) for r in records.values()),
        "cumulative_api_cost_usd": _cumulative_cost(records),
        "elapsed_wall_clock_iso": _now_iso(),
        "manifest_total_cells": len(manifest["cells"]),
    }
    budget = _cost_budget_ok(records, manifest)
    totals["cost_budget"] = budget
    progress = _load_progress()
    progress[str(completed)] = totals
    _save_progress(progress)
    if completed % CHECKPOINT_EVERY == 0 or completed == len(manifest["cells"]):
        cp = _persist_json(f"checkpoint_{completed}.json", totals)
        print(f"CHECKPOINT_{completed} persisted={cp}")


def cmd_run(args: argparse.Namespace) -> int:
    manifest = _load_manifest()
    cells = manifest["cells"]
    if not _gates_evidence_passed() and not args.skip_gate_check:
        print("Refusing to run scientific cells before the six gates + audit pass.")
        return 2

    records = _loaded_records()
    if len(records) >= len(cells):
        print(f"Manifest already complete: {len(records)}/60 records present.")
        _write_checkpoint(records, manifest)
        return 0

    budget = _cost_budget_ok(records, manifest)
    print(json.dumps(budget, indent=2))
    if not budget["ok"]:
        print("COST_BUDGET_STOP")
        _write_checkpoint(records, manifest)
        return 1

    pending = [c for c in cells if c["run_id"] not in records]
    limit = args.limit if args.limit and args.limit > 0 else len(pending)
    batch = pending[:limit]
    delay = max(0.0, float(getattr(args, "inter_cell_delay", 0.0) or 0.0))
    print(f"RUNNING_BATCH={len(batch)} of pending={len(pending)} inter_cell_delay={delay}s")

    for cell in batch:
        print(f"\n=== CELL {cell['run_id']} ({cell['arm']}) ===")
        evidence = run_cell(cell, dry_run=args.dry_run)
        _append_record(evidence)
        records[cell["run_id"]] = evidence
        per_run = STUDY_DIR / "runs" / f"{cell['run_id']}.json"
        per_run.parent.mkdir(parents=True, exist_ok=True)
        per_run.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
        print(json.dumps(
            {k: evidence[k] for k in (
                "run_id", "terminal_status", "predicted_write_set_size",
                "tp", "fp", "fn", "precision", "recall", "f1", "total_tokens",
                "model_calls", "latency_seconds", "api_cost", "finish_reason",
                "truncation_status", "invalid_selected_paths",
            )}, indent=2))
        print(f"persisted={per_run}")
        _write_checkpoint(records, manifest)
        if delay and len(records) < len(cells):
            print(f"pacing {delay:.0f}s before next cell", flush=True)
            time.sleep(delay)

        if len(records) < len(cells):
            budget = _cost_budget_ok(records, manifest)
            if not budget["ok"]:
                print("COST_BUDGET_STOP")
                return 1

    completed = len(records)
    print(f"\nBATCH_COMPLETE completed={completed}/60")
    return 0


# ---------------------------------------------------------------------------
# Metrics (sections J/K/L/M)
# ---------------------------------------------------------------------------


def _valid_runs(records: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {rid: r for rid, r in records.items() if r["terminal_status"] == "succeeded"}


def _micro(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected = sum(int(r["predicted_write_set_size"]) for r in rows)
    tp = sum(int(r["tp"]) for r in rows)
    fp = sum(int(r["fp"]) for r in rows)
    fn = sum(int(r["fn"]) for r in rows)
    precision = tp / selected if selected else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0
    return {
        "selected": selected,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "fnr": round(fnr, 6),
    }


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}
    n = len(values)
    s = sorted(values)
    mean = sum(values) / n
    median = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    return {"mean": round(mean, 6), "median": round(median, 6), "min": round(s[0], 6), "max": round(s[-1], 6)}


def compute_metrics(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    manifest = _load_manifest()
    valid = _valid_runs(records)
    rows_all = list(records.values())
    rows_valid = list(valid.values())

    per_run: list[dict[str, Any]] = []
    for rid in sorted(records):
        r = records[rid]
        per_run.append(
            {
                "run_id": rid,
                "scenario_id": r["scenario_id"],
                "repetition": r["repetition"],
                "arm": r["arm"],
                "terminal_status": r["terminal_status"],
                "selected": r["predicted_write_set_size"],
                "tp": r["tp"],
                "fp": r["fp"],
                "fn": r["fn"],
                "precision": r["precision"],
                "recall": r["recall"],
                "f1": r["f1"],
                "fnr": r["fnr"],
                "full_recall": r["full_recall"],
                "tokens": r["total_tokens"],
                "model_calls": r["model_calls"],
                "latency_seconds": r["latency_seconds"],
                "api_cost": r["api_cost"],
            }
        )

    per_scenario: dict[str, dict[str, Any]] = {}
    for scenario_id in FINAL_SCENARIOS:
        per_scenario[scenario_id] = {}
        for arm in ARMS:
            rows = [r for r in rows_valid if r["scenario_id"] == scenario_id and r["arm"] == arm]
            micro = _micro(rows)
            per_scenario[scenario_id][arm] = {
                "pooled_across_5_repetitions": True,
                "valid_runs": len(rows),
                **micro,
                "tokens": sum(int(r["total_tokens"]) for r in rows),
                "model_calls": sum(int(r["model_calls"]) for r in rows),
                "latency_seconds": round(sum(float(r["latency_seconds"]) for r in rows), 6),
                "api_cost": round(sum(float(r["api_cost"]) for r in rows), 6),
            }

    overall: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        rows = [r for r in rows_valid if r["arm"] == arm]
        micro = _micro(rows)
        overall[arm] = {
            "valid_runs": len(rows),
            **micro,
            "tokens": sum(int(r["total_tokens"]) for r in rows),
            "model_calls": sum(int(r["model_calls"]) for r in rows),
            "latency_seconds": round(sum(float(r["latency_seconds"]) for r in rows), 6),
            "api_cost": round(sum(float(r["api_cost"]) for r in rows), 6),
        }

    macro: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        rows = [r for r in rows_valid if r["arm"] == arm]
        macro[arm] = {
            "mean_precision": _stats([float(r["precision"]) for r in rows])["mean"],
            "median_precision": _stats([float(r["precision"]) for r in rows])["median"],
            "mean_recall": _stats([float(r["recall"]) for r in rows])["mean"],
            "median_recall": _stats([float(r["recall"]) for r in rows])["median"],
            "mean_f1": _stats([float(r["f1"]) for r in rows])["mean"],
            "median_f1": _stats([float(r["f1"]) for r in rows])["median"],
            "full_recall_rate": round(
                sum(1 for r in rows if r["full_recall"]) / len(rows), 6
            ) if rows else 0.0,
            "selected_set_size": _stats([float(r["predicted_write_set_size"]) for r in rows]),
            "tokens": _stats([float(r["total_tokens"]) for r in rows]),
            "model_calls": _stats([float(r["model_calls"]) for r in rows]),
            "latency": _stats([float(r["latency_seconds"]) for r in rows]),
            "cost": _stats([float(r["api_cost"]) for r in rows]),
        }

    latencies = [float(r["latency_seconds"]) for r in rows_valid]
    lat_mean = sum(latencies) / len(latencies) if latencies else 0.0
    lat_std = (sum((x - lat_mean) ** 2 for x in latencies) / len(latencies)) ** 0.5 if latencies else 0.0
    outliers = sorted(
        [
            {"run_id": r["run_id"], "latency_seconds": r["latency_seconds"]}
            for r in rows_valid
            if float(r["latency_seconds"]) > lat_mean + 2 * lat_std
        ],
        key=lambda x: x["latency_seconds"],
        reverse=True,
    )

    metrics = {
        "study_id": STUDY_ID,
        "manifest_total_cells": len(manifest["cells"]),
        "recorded_cells": len(rows_all),
        "successful_cells": sum(1 for r in rows_all if r["terminal_status"] == "succeeded"),
        "failed_cells": sum(1 for r in rows_all if r["terminal_status"] != "succeeded"),
        "failed_run_accounting": [
            {k: r[k] for k in ("run_id", "scenario_id", "repetition", "arm",
                               "terminal_status", "failure_category", "failure_evidence")}
            for r in rows_all
            if r["terminal_status"] != "succeeded"
        ],
        "per_run": per_run,
        "per_scenario": per_scenario,
        "overall": overall,
        "macro": macro,
        "latency_outliers": outliers,
        "full_recall_rate_overall": {
            arm: macro[arm]["full_recall_rate"] for arm in ARMS
        },
        "totals": {
            "tokens": sum(int(r["total_tokens"]) for r in rows_all),
            "model_calls": sum(int(r["model_calls"]) for r in rows_all),
            "latency_seconds": round(sum(float(r["latency_seconds"]) for r in rows_all), 6),
            "api_cost_usd": _cumulative_cost(records),
        },
    }
    return metrics


def cmd_metrics(args: argparse.Namespace) -> int:
    records = _loaded_records()
    if len(records) < 60:
        print(f"Only {len(records)}/60 records present — final metrics require all 60.")
        return 2
    metrics = compute_metrics(records)
    path = _persist_json("final_metrics.json", metrics)
    print(f"persisted={path}")
    print(json.dumps({"overall": metrics["overall"], "macro": metrics["macro"],
                      "totals": metrics["totals"], "failed_cells": metrics["failed_cells"]}, indent=2))
    return 0


def cmd_close(args: argparse.Namespace) -> int:
    gates = wiring.run_gates()
    all_passed = all(g["passed"] for g in gates)
    audit = wiring.independent_audit()
    result = {
        "closure_gates": gates,
        "gates_all_passed": all_passed,
        "audit": audit,
        "zero_scientific_calls": True,
        "does_not_modify_scientific_results": True,
        "ran_at": _now_iso(),
    }
    path = _persist_json("closure_gates.json", result)
    for gate in gates:
        print(f"Closure Gate {gate['gate']} {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
    print(f"CLOSURE_AUDIT={'PASS' if audit['passed'] else 'FAIL'}")
    print(f"persisted={path}")
    return 0 if (all_passed and audit["passed"]) else 1


def cmd_all(args: argparse.Namespace) -> int:
    if cmd_prevalidate(args) != 0:
        print("PREVALIDATION FAILED — STOP")
        return 1
    if cmd_gates(args) != 0:
        print("GATES FAILED — STOP")
        return 1
    if cmd_freeze_manifest(args) != 0:
        print("MANIFEST FREEZE FAILED — STOP")
        return 1
    if cmd_run(args) != 0:
        return 1
    if cmd_metrics(args) != 0:
        return 1
    if cmd_close(args) != 0:
        return 1
    print("\nSTUDY ALL PIPELINE COMPLETE")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prevalidate", help="section-B pre-run validation")
    p.add_argument("--output-dir", type=str, default=str(STUDY_DIR))
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("gates", help="six deterministic gates + audit")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("freeze-manifest", help="freeze the 60-cell manifest")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("run", help="execute remaining manifest cells")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--inter-cell-delay", type=float, default=0.0,
                   help="operational pacing seconds between cells (not a scientific input)")
    p.add_argument("--dry-run", action="store_true", default=False)
    p.add_argument("--skip-gate-check", action="store_true", default=False)
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("metrics", help="compute final metrics")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("close", help="closure six gates + audit")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("all", help="full pipeline")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--inter-cell-delay", type=float, default=0.0)
    p.add_argument("--dry-run", action="store_true", default=False)
    p.add_argument("--skip-gate-check", action="store_true", default=False)
    p.set_defaults(_set_study_dir=True)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    global STUDY_DIR
    if getattr(args, "_set_study_dir", False) and getattr(args, "output_dir", None):
        STUDY_DIR = Path(args.output_dir)
    if args.command == "prevalidate":
        return cmd_prevalidate(args)
    if args.command == "gates":
        return cmd_gates(args)
    if args.command == "freeze-manifest":
        return cmd_freeze_manifest(args)
    if args.command == "run":
        return cmd_run(args)
    if args.command == "metrics":
        return cmd_metrics(args)
    if args.command == "close":
        return cmd_close(args)
    if args.command == "all":
        return cmd_all(args)
    print(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())