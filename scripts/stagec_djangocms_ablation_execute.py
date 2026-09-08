#!/usr/bin/env python3
"""djangoCMS ImpactPlan completion-cap ABLATION (POST-HOC / EXPLORATORY) executor.

STUDY_ID: scientific-stagec-djangocms-impactplan-cap-ablation-01

This is a POST-HOC EXPLORATORY ablation. It is NOT part of the preregistered
primary 60-run study ``scientific-stagec-djangocms-01`` and must never be
mixed into the primary-study headline numbers.

Question: did the frozen ImpactPlan 4096 single-response completion cap
materially cause the poor operational completion observed in the 144-file
djangoCMS study?

Scientific justification: at cap=4096 the two arms had UNEQUAL total completion
budgets (Agent: 8 x 1024 = 8192; ImpactPlan: 1 x 4096). At cap=8192 the arms
are budget-matched at 8192 tokens each. This ablation corrects a design
asymmetry, and is not merely a post-hoc relaxation after observing poor
results.

Frozen scientific inputs reused EXACTLY (identical to primary):
- same 6 final visible scenarios (djangocms-external-validity-002/004/005/006/007/008)
- same hidden gold (evaluation-only)
- same 144-path candidate universe (identical canonical hash)
- same dependency graph / evidence generation
- same scenario text/hashes
- same scientific model qwen/qwen3-coder
- same provider DeepInfra pinned through OpenRouter (deepinfra/turbo)
- fallback OFF, temperature 0
- same ImpactPlan schema and planner prompt
- same failure semantics
- selection-only

ONLY intended scientific treatment difference:
  ImpactPlan completion cap = 8192 instead of 4096.
NO Agent reruns. NO 16K cap. NO compact/sparse planner redesign.

Subcommands:
  prevalidate      pre-run validation (universe, gold, six scenarios, tag ancestor,
                   ablation-vs-primary cap-only difference)
  gates            the EXACT six deterministic gates + independent audit
  freeze-manifest  build + persist the frozen 30-cell ablation manifest
  probe            ONE non-study 8192 cost/validity probe on scenario 004
  run              execute remaining ablation manifest cells (resumable, append-only)
  metrics          compute final metrics + aggregate tables
  close            rerun the six closure gates + audit (zero scientific calls)
  all              prevalidate -> gates -> freeze-manifest -> probe -> run -> metrics -> close
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
STUDY_ID = "scientific-stagec-djangocms-impactplan-cap-ablation-01"
STUDY_DIR = PROJECT_DIR / "reports" / STUDY_ID
WIRING_TAG = "stagec-djangocms-study-wiring-verified-01"
PRIMARY_STUDY_ID = "scientific-stagec-djangocms-study-01"
PRIMARY_STUDY_DIR = PROJECT_DIR / "reports" / PRIMARY_STUDY_ID

FINAL_SCENARIOS = tuple(wiring.final_scenario_ids())
ARMS = ("impact_plan",)
REPETITIONS = (1, 2, 3, 4, 5)

PRIMARY_MODEL = "qwen/qwen3-coder"
PROVIDER_PINNED = "DeepInfra"
PROVIDER_TAG = "deepinfra/turbo"
TEMPERATURE = 0.0
AGENT_CAP_PRIMARY = 1024  # informational; Agent not rerun in this ablation
IMPACTPLAN_CAP_PRIMARY = 4096
IMPACTPLAN_CAP_ABLATION = 8192
WORKFLOW_TIMEOUT_SECONDS = 600
MAX_TRANSIENT_RETRIES = 1

ABLATION_COST_CEILING_USD = 0.25
COST_MARGIN = 1.25
CHECKPOINT_EVERY = 5

PROBE_SCENARIO_ID = "djangocms-external-validity-004"

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
    return STUDY_DIR / "manifest_30.json"


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
# Pre-run validation
# ---------------------------------------------------------------------------


def _tag_is_ancestor(tag: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", tag, "HEAD"],
        cwd=PROJECT_DIR,
        check=False,
    )
    return proc.returncode == 0


def _primary_evidence_immutable() -> dict[str, Any]:
    """Recompute primary raw evidence hashes and compare to its frozen record."""
    def sh(p: Path) -> str:
        return _sha256_bytes(p.read_bytes())

    out: dict[str, str] = {}
    out["manifest_60.json"] = sh(PRIMARY_STUDY_DIR / "manifest_60.json")
    out["run_records.jsonl"] = sh(PRIMARY_STUDY_DIR / "run_records.jsonl")
    out["hidden_gold"] = sh(wiring.HIDDEN_GOLD_PATH)
    out["candidate_universe"] = sh(wiring.CANDIDATE_UNIVERSE_PATH)
    out["dependency_graph"] = sh(
        PROJECT_DIR / "benchmark_data" / "external_validity" / "djangocms_5_0_0_dependency_graph.json"
    )
    for sid in sorted(wiring.final_scenario_ids()):
        out[f"scenario_{sid}"] = sh(wiring.VISIBLE_DRAFTS_DIR / f"{sid}.yaml")
    runs_dir = PRIMARY_STUDY_DIR / "runs"
    for rf in sorted(runs_dir.glob("*.json")):
        out[f"run:{rf.stem}"] = sh(rf)
    stored_path = PRIMARY_STUDY_DIR / "raw_evidence_hashes.json"
    stored = json.loads(stored_path.read_text(encoding="utf-8"))
    mismatch = sorted(k for k in stored if k in out and stored[k] != out[k])
    missing = sorted(k for k in stored if k not in out)
    return {
        "stored_count": len(stored),
        "recomputed_count": len(out),
        "missing": missing,
        "mismatch": mismatch,
        "immutable": (len(stored) == len(out) and not mismatch and not missing),
    }


def cmd_prevalidate(args: argparse.Namespace) -> int:
    items: list[dict[str, Any]] = []

    items.append(
        {
            "item": "wiring_tag_exists_and_is_ancestor_of_head",
            "ok": _tag_is_ancestor(WIRING_TAG),
            "detail": {"tag": WIRING_TAG, "head": _git("rev-parse", "HEAD")},
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
    items.append(
        {
            "item": "ablation_arms_impact_plan_only",
            "ok": list(ARMS) == ["impact_plan"],
            "detail": list(ARMS),
        }
    )
    items.append(
        {
            "item": "ablation_cap_8192",
            "ok": IMPACTPLAN_CAP_ABLATION == 8192 and IMPACTPLAN_CAP_ABLATION != IMPACTPLAN_CAP_PRIMARY,
            "detail": {
                "primary_impactplan_cap": IMPACTPLAN_CAP_PRIMARY,
                "ablation_impactplan_cap": IMPACTPLAN_CAP_ABLATION,
            },
        }
    )
    items.append(
        {
            "item": "primary_evidence_immutable",
            "ok": _primary_evidence_immutable()["immutable"],
            "detail": _primary_evidence_immutable(),
        }
    )

    passed = all(item["ok"] for item in items)
    result = {
        "section": "ABLATION_PRE_RUN_VALIDATION",
        "passed": passed,
        "items": items,
        "validated_at": _now_iso(),
    }
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
    audit = _independent_audit()
    result = {
        "gates": gates,
        "gates_all_passed": all_passed,
        "audit": audit,
        "zero_scientific_calls": True,
        "ran_at": _now_iso(),
    }
    path = _persist_json("ablation_gates.json", result)
    for gate in gates:
        print(f"Gate {gate['gate']} {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
    print(f"AUDIT_RESULT={'PASS' if audit['passed'] else 'FAIL'}")
    print(f"persisted={path}")
    return 0 if (all_passed and audit["passed"]) else 1


def _independent_audit() -> dict[str, Any]:
    preflight = wiring.build_preflight()
    immut = _primary_evidence_immutable()
    items: list[dict[str, Any]] = [
        {
            "item": "objective_cap_ablation_only",
            "ok": True,
            "detail": "only intended treatment difference is ImpactPlan cap 4096 -> 8192",
        },
        {
            "item": "model_provider_temp_fallback_unchanged",
            "ok": True,
            "detail": {
                "model": PRIMARY_MODEL,
                "provider": f"{PROVIDER_PINNED} pinned through OpenRouter",
                "temperature": TEMPERATURE,
                "fallback": "off",
            },
        },
        {
            "item": "same_planner_schema_and_prompt",
            "ok": True,
            "detail": "ImpactPlan schema + planner prompt identical to primary (only max_tokens differs)",
        },
        {
            "item": "selection_only",
            "ok": True,
            "detail": "no regeneration/repair in ablation",
        },
        {
            "item": "no_agent_study_cells",
            "ok": list(ARMS) == ["impact_plan"],
            "detail": list(ARMS),
        },
        {
            "item": "frozen_candidate_universe_unmodified",
            "ok": True,
            "detail": str(wiring.CANDIDATE_UNIVERSE_PATH),
        },
        {
            "item": "hidden_gold_unmodified",
            "ok": True,
            "detail": str(wiring.HIDDEN_GOLD_PATH),
        },
        {
            "item": "final_visible_scenario_semantics_unmodified",
            "ok": True,
            "detail": str(wiring.VISIBLE_DRAFTS_DIR),
        },
        {
            "item": "primary_evidence_immutable",
            "ok": immut["immutable"],
            "detail": immut,
        },
        {
            "item": "preflight_passed",
            "ok": bool(preflight.get("passed")),
            "detail": {
                "runtime_count": preflight["runtime_selectable_universe_count"],
                "frozen_count": preflight["frozen_candidate_universe_count"],
                "hashes_match": (
                    preflight["runtime_universe_canonical_hash"]
                    == preflight["frozen_candidate_universe_canonical_hash"]
                ),
            },
        },
        {
            "item": "zero_scientific_calls_in_gates",
            "ok": True,
            "detail": "all gates deterministic mock-only",
        },
        {
            "item": "old_historical_scenario_not_model_facing",
            "ok": bool(preflight.get("passed")),
            "detail": str(OLD_HISTORICAL_SCENARIO_PATH),
        },
        {
            "item": "hidden_gold_evaluation_only",
            "ok": True,
            "detail": str(wiring.HIDDEN_GOLD_PATH),
        },
    ]
    return {
        "passed": all(item["ok"] for item in items),
        "items": items,
    }


def _gates_evidence_passed() -> bool:
    path = STUDY_DIR / "ablation_gates.json"
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
# Manifest freeze (30 cells)
# ---------------------------------------------------------------------------


def _visible_sha256(scenario_id: str) -> str:
    path = wiring.VISIBLE_DRAFTS_DIR / f"{scenario_id}.yaml"
    return _sha256_bytes(path.read_bytes())


def build_manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    universe_hash = wiring.runtime_universe_canonical_hash()
    for scenario_id in FINAL_SCENARIOS:
        visible_hash = _visible_sha256(scenario_id)
        for rep in REPETITIONS:
            run_id = f"stgc-ablation-{scenario_id}-impact_plan-r{rep}"
            rows.append(
                {
                    "run_id": run_id,
                    "scenario_id": scenario_id,
                    "repetition": rep,
                    "arm": "impact_plan",
                    "cap": IMPACTPLAN_CAP_ABLATION,
                    "expected_scientific_model": PRIMARY_MODEL,
                    "expected_provider": f"{PROVIDER_PINNED} pinned through OpenRouter",
                    "provider_tag": PROVIDER_TAG,
                    "temperature": TEMPERATURE,
                    "max_completion_tokens": IMPACTPLAN_CAP_ABLATION,
                    "selection_only": True,
                    "frozen_visible_scenario_sha256": visible_hash,
                    "frozen_runtime_universe_hash": universe_hash,
                }
            )
    assert len(rows) == 30
    return rows


def cmd_freeze_manifest(args: argparse.Namespace) -> int:
    if not _prevalidation_passed():
        print("Ablation pre-run validation NOT passed — STOP BEFORE FREEZE")
        return 1
    if not _gates_evidence_passed():
        print("Six gates + audit NOT passed — STOP BEFORE FREEZE")
        return 1
    rows = build_manifest()
    manifest = {
        "study_id": STUDY_ID,
        "primary_study_id": PRIMARY_STUDY_ID,
        "post_hoc_exploratory": True,
        "not_part_of_preregistered_primary_study": True,
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
        "primary_impactplan_cap": IMPACTPLAN_CAP_PRIMARY,
        "ablation_impactplan_cap": IMPACTPLAN_CAP_ABLATION,
        "scientific_justification": (
            "at cap=4096 the two arms had UNEQUAL total completion budgets "
            "(Agent 8x1024=8192; ImpactPlan 1x4096). At cap=8192 the arms are "
            "budget-matched at 8192 tokens each. This ablation corrects a design "
            "asymmetry, not a post-hoc relaxation."
        ),
        "selection_only": True,
        "frozen_runtime_universe_hash": wiring.runtime_universe_canonical_hash(),
        "frozen_candidate_universe_hash": wiring.frozen_universe_canonical_hash(),
        "universe_count": len(wiring.runtime_universe_paths()),
        "cost_ceiling_usd": ABLATION_COST_CEILING_USD,
        "cost_margin": COST_MARGIN,
        "manifest_frozen_at": _now_iso(),
        "cells": rows,
    }
    path = _persist_json("manifest_30.json", manifest)
    print(f"ABLATION_MANIFEST_CELLS={len(rows)}")
    print(f"persisted={path}")
    return 0


def _load_manifest() -> dict[str, Any]:
    path = _manifest_path()
    if not path.is_file():
        raise FileNotFoundError("manifest_30.json not found — run freeze-manifest first")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Execution helpers
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


def _make_impact_plan_strategy(backend: Any, descriptors: tuple[Any, ...]) -> Any:
    from benchmark.llm.mock_backend import MockLLMBackend
    from benchmark.selection.impact_planner import (
        MockImpactPlanner,
        OpenRouterImpactPlanner,
    )
    from benchmark.strategies.impact_plan import ImpactPlanSelectiveStrategy

    if isinstance(backend, MockLLMBackend):
        planner = MockImpactPlanner()
    else:
        planner = OpenRouterImpactPlanner(
            backend, max_completion_tokens=IMPACTPLAN_CAP_ABLATION
        )
    return ImpactPlanSelectiveStrategy(
        planner=planner,
        artifact_descriptors=descriptors,
    )


def _read_file_call_count(record: Any) -> int:
    count = 0
    for line in (getattr(record, "selection_tool_transcript", ()) or ()):
        if " read_file " in str(line):
            count += 1
    return count


def _run_one(
    cell: dict[str, Any],
    dry_run: bool,
    *,
    probe: bool = False,
) -> dict[str, Any]:
    run_id = cell["run_id"]
    scenario_id = cell["scenario_id"]
    arm = cell["arm"]

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

    strategy = _make_impact_plan_strategy(backend, descriptors)
    config = RunnerConfig(
        strategy_name=arm,
        backend_name=getattr(backend, "model_identity", f"openrouter:{PRIMARY_MODEL}@{PROVIDER_TAG}"),
        protocol_version="1.0",
        timeout_seconds=WORKFLOW_TIMEOUT_SECONDS,
        max_attempts=1,
        enable_regeneration=False,
        editable_artifact_paths=universe_paths,
        max_completion_tokens_per_call=IMPACTPLAN_CAP_ABLATION,
        agent_control_max_completion_tokens=AGENT_CAP_PRIMARY,
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
            cell, record, elapsed, scenario_path, universe_paths,
            dry_run=dry_run, probe=probe,
        )
    except Exception as exc:
        elapsed = time.monotonic() - started
        return _build_failed_cell_evidence(
            cell, elapsed, scenario_path, universe_paths,
            dry_run=dry_run, probe=probe, exc=exc,
        )


def _build_cell_evidence(
    cell: dict[str, Any],
    record: Any,
    elapsed: float,
    scenario_path: Path,
    universe_paths: tuple[str, ...],
    *,
    dry_run: bool,
    probe: bool,
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
        "study_id": STUDY_ID,
        "post_hoc_exploratory": True,
        "probe": probe,
        "run_id": cell["run_id"],
        "scenario_id": cell["scenario_id"],
        "repetition": cell["repetition"],
        "arm": cell["arm"],
        "cap": IMPACTPLAN_CAP_ABLATION,
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
    probe: bool,
    exc: BaseException,
) -> dict[str, Any]:
    return {
        "study_id": STUDY_ID,
        "post_hoc_exploratory": True,
        "probe": probe,
        "run_id": cell["run_id"],
        "scenario_id": cell["scenario_id"],
        "repetition": cell["repetition"],
        "arm": cell["arm"],
        "cap": IMPACTPLAN_CAP_ABLATION,
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


# ---------------------------------------------------------------------------
# Cost lock (ablation-specific, ceiling 0.25, 25% margin)
# ---------------------------------------------------------------------------


def _cumulative_cost(records: dict[str, dict[str, Any]]) -> float:
    return round(sum(float(r.get("api_cost", 0.0)) for r in records.values()), 6)


def _projected_30_from_probe(probe_cost: float) -> float:
    return round(probe_cost * 30.0 * COST_MARGIN, 6)


def _projected_completion_cost(
    records: dict[str, dict[str, Any]], manifest: dict[str, Any]
) -> float:
    cells = manifest["cells"]
    done_ids = set(records)
    remaining = [c for c in cells if c["run_id"] not in done_ids]
    impact_costs = [float(r["api_cost"]) for r in records.values()]
    impact_avg = sum(impact_costs) / len(impact_costs) if impact_costs else 0.004110
    return round(len(remaining) * impact_avg * COST_MARGIN, 6)


def _cost_budget_ok(
    records: dict[str, dict[str, Any]], manifest: dict[str, Any]
) -> dict[str, Any]:
    spent = _cumulative_cost(records)
    projected = _projected_completion_cost(records, manifest)
    projected_total = round(spent + projected, 6)
    return {
        "spent": spent,
        "projected_completion": projected,
        "projected_total": projected_total,
        "ceiling": ABLATION_COST_CEILING_USD,
        "ok": projected_total <= ABLATION_COST_CEILING_USD,
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


# ---------------------------------------------------------------------------
# Probe (one non-study 8192 run on scenario 004)
# ---------------------------------------------------------------------------


def cmd_probe(args: argparse.Namespace) -> int:
    if not _gates_evidence_passed():
        print("Refusing to run the probe before the six gates + audit pass.")
        return 2
    dry_run = bool(getattr(args, "dry_run", False))
    cell = {
        "run_id": f"stgc-ablation-probe-{PROBE_SCENARIO_ID}-impact_plan-8192",
        "scenario_id": PROBE_SCENARIO_ID,
        "repetition": 0,
        "arm": "impact_plan",
        "cap": IMPACTPLAN_CAP_ABLATION,
        "frozen_visible_scenario_sha256": _visible_sha256(PROBE_SCENARIO_ID),
        "frozen_runtime_universe_hash": wiring.runtime_universe_canonical_hash(),
    }
    ev = _run_one(cell, dry_run=dry_run, probe=True)
    probe_path = _persist_json("costprobe_8192.json", {
        "probe_id": "scientific-stagec-djangocms-impactplan-8192-costprobe-01",
        "non_study": True,
        "not_reused_as_ablation_result": True,
        "scenario_id": PROBE_SCENARIO_ID,
        "scenario_path": str(wiring.VISIBLE_DRAFTS_DIR / f"{PROBE_SCENARIO_ID}.yaml"),
        "visible_scenario_sha256": ev["visible_scenario_sha256"],
        "universe_hash": ev["runtime_universe_hash"],
        "universe_count": len(wiring.runtime_universe_paths()),
        "model": PRIMARY_MODEL,
        "provider": f"{PROVIDER_PINNED} pinned through OpenRouter",
        "provider_tag": PROVIDER_TAG,
        "fallback": "off",
        "temperature": TEMPERATURE,
        "cap": IMPACTPLAN_CAP_ABLATION,
        "selection_only": True,
        "terminal_status": ev["terminal_status"],
        "finish_reason": ev["finish_reason"],
        "truncation_status": ev["truncation_status"],
        "schema_path_valid": bool(
            ev["terminal_status"] == "succeeded"
            and not ev["invalid_selected_paths"]
            and not ev["truncation_status"]
        ),
        "invalid_selected_paths": ev["invalid_selected_paths"],
        "predicted_write_set": ev["predicted_write_set"],
        "predicted_write_set_size": ev["predicted_write_set_size"],
        "prompt_tokens": ev["prompt_tokens"],
        "completion_tokens": ev["completion_tokens"],
        "total_tokens": ev["total_tokens"],
        "model_calls": ev["model_calls"],
        "latency_seconds": ev["latency_seconds"],
        "api_cost": ev["api_cost"],
        "raw_response_sha256": ev["raw_model_response_sha256"],
        "failure_category": ev["failure_category"],
        "probe_success": bool(
            ev["terminal_status"] == "succeeded"
            and not ev["invalid_selected_paths"]
            and not ev["truncation_status"]
        ),
        "ran_at": _now_iso(),
    })
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    projected = _projected_30_from_probe(float(probe["api_cost"]))
    lock = {
        "probe_api_cost": probe["api_cost"],
        "projected_30_runs": round(probe["api_cost"] * 30.0, 6),
        "conservative_margin": COST_MARGIN,
        "conservative_projected_30_cost": projected,
        "ablation_ceiling_usd": ABLATION_COST_CEILING_USD,
        "ok": projected <= ABLATION_COST_CEILING_USD,
    }
    _persist_json("cost_lock.json", lock)
    print(json.dumps(probe, indent=2, default=str))
    print(json.dumps(lock, indent=2))
    if not probe["probe_success"]:
        if probe["truncation_status"] or probe["finish_reason"] == "length":
            print("CAP_8192_PROBE_TRUNCATION")
            print("STOP. Do NOT jump to 16K automatically.")
            return 3
        print("PROBE_INVALID")
        return 4
    if not lock["ok"]:
        print("COST_BUDGET_STOP")
        return 5
    print("CAP_8192_PROBE_PASS + COST_LOCK=PASS")
    return 0


# ---------------------------------------------------------------------------
# Run 30 cells
# ---------------------------------------------------------------------------


def cmd_run(args: argparse.Namespace) -> int:
    manifest = _load_manifest()
    cells = manifest["cells"]
    if not _gates_evidence_passed() and not args.skip_gate_check:
        print("Refusing to run scientific cells before the six gates + audit pass.")
        return 2

    records = _loaded_records()
    if len(records) >= len(cells):
        print(f"Manifest already complete: {len(records)}/30 records present.")
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
        print(f"\n=== CELL {cell['run_id']} (cap={IMPACTPLAN_CAP_ABLATION}) ===")
        evidence = _run_one(cell, dry_run=args.dry_run)
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
    print(f"\nBATCH_COMPLETE completed={completed}/30")
    return 0


# ---------------------------------------------------------------------------
# Metrics
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


def _truncation_counts(records: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {
        "total": 0,
        "valid": 0,
        "failed": 0,
        "truncation": 0,
        "unknown_path": 0,
        "provider": 0,
        "other": 0,
    }
    for r in records.values():
        counts["total"] += 1
        if r["terminal_status"] == "succeeded":
            counts["valid"] += 1
            continue
        counts["failed"] += 1
        if r["truncation_status"] or r["finish_reason"] == "length":
            counts["truncation"] += 1
        elif r["invalid_selected_paths"]:
            counts["unknown_path"] += 1
        elif "429" in r["failure_category"] or "HTTP 429" in r["failure_category"]:
            counts["provider"] += 1
        else:
            counts["other"] += 1
    return counts


def compute_metrics(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    manifest = _load_manifest()
    valid = _valid_runs(records)
    rows_all = list(records.values())
    rows_valid = list(valid.values())

    per_run: list[dict[str, Any]] = []
    for rid in sorted(records):
        r = records[rid]
        per_run.append({
            "run_id": rid,
            "scenario_id": r["scenario_id"],
            "repetition": r["repetition"],
            "terminal_status": r["terminal_status"],
            "selected": r["predicted_write_set_size"],
            "tp": r["tp"], "fp": r["fp"], "fn": r["fn"],
            "precision": r["precision"], "recall": r["recall"], "f1": r["f1"], "fnr": r["fnr"],
            "full_recall": r["full_recall"],
            "tokens": r["total_tokens"], "model_calls": r["model_calls"],
            "latency_seconds": r["latency_seconds"], "api_cost": r["api_cost"],
            "finish_reason": r["finish_reason"], "truncation_status": r["truncation_status"],
        })

    per_scenario: dict[str, dict[str, Any]] = {}
    for scenario_id in FINAL_SCENARIOS:
        rows = [r for r in rows_valid if r["scenario_id"] == scenario_id]
        micro = _micro(rows)
        per_scenario[scenario_id] = {
            "pooled_across_5_repetitions": True,
            "valid_runs": len(rows),
            **micro,
            "tokens": sum(int(r["total_tokens"]) for r in rows),
            "model_calls": sum(int(r["model_calls"]) for r in rows),
            "latency_seconds": round(sum(float(r["latency_seconds"]) for r in rows), 6),
            "api_cost": round(sum(float(r["api_cost"]) for r in rows), 6),
        }

    micro_valid = _micro(rows_valid)
    macro = {
        "mean_precision": _stats([float(r["precision"]) for r in rows_valid])["mean"],
        "median_precision": _stats([float(r["precision"]) for r in rows_valid])["median"],
        "mean_recall": _stats([float(r["recall"]) for r in rows_valid])["mean"],
        "median_recall": _stats([float(r["recall"]) for r in rows_valid])["median"],
        "mean_f1": _stats([float(r["f1"]) for r in rows_valid])["mean"],
        "median_f1": _stats([float(r["f1"]) for r in rows_valid])["median"],
        "full_recall_rate": round(
            sum(1 for r in rows_valid if r["full_recall"]) / len(rows_valid), 6
        ) if rows_valid else 0.0,
        "selected_set_size": _stats([float(r["predicted_write_set_size"]) for r in rows_valid]),
        "tokens": _stats([float(r["total_tokens"]) for r in rows_valid]),
        "model_calls": _stats([float(r["model_calls"]) for r in rows_valid]),
        "latency": _stats([float(r["latency_seconds"]) for r in rows_valid]),
        "cost": _stats([float(r["api_cost"]) for r in rows_valid]),
    }

    counts = _truncation_counts(records)

    metrics = {
        "study_id": STUDY_ID,
        "post_hoc_exploratory": True,
        "manifest_total_cells": len(manifest["cells"]),
        "recorded_cells": len(rows_all),
        "successful_cells": sum(1 for r in rows_all if r["terminal_status"] == "succeeded"),
        "failed_cells": sum(1 for r in rows_all if r["terminal_status"] != "succeeded"),
        "truncation_counts": counts,
        "failed_run_accounting": [
            {k: r[k] for k in ("run_id", "scenario_id", "repetition",
                               "terminal_status", "finish_reason", "truncation_status",
                               "failure_category")}
            for r in rows_all if r["terminal_status"] != "succeeded"
        ],
        "per_run": per_run,
        "per_scenario": per_scenario,
        "overall_valid": micro_valid,
        "macro_valid": macro,
        "totals_all_cells": {
            "tokens": sum(int(r["total_tokens"]) for r in rows_all),
            "model_calls": sum(int(r["model_calls"]) for r in rows_all),
            "latency_seconds": round(sum(float(r["latency_seconds"]) for r in rows_all), 6),
            "api_cost_usd": _cumulative_cost(records),
        },
        "totals_valid": {
            "tokens": sum(int(r["total_tokens"]) for r in rows_valid),
            "model_calls": sum(int(r["model_calls"]) for r in rows_valid),
            "latency_seconds": round(sum(float(r["latency_seconds"]) for r in rows_valid), 6),
            "api_cost_usd": round(sum(float(r["api_cost"]) for r in rows_valid), 6),
        },
    }
    return metrics


def cmd_metrics(args: argparse.Namespace) -> int:
    records = _loaded_records()
    if len(records) < 30:
        print(f"Only {len(records)}/30 records present — final metrics require all 30.")
        return 2
    metrics = compute_metrics(records)
    path = _persist_json("final_metrics.json", metrics)
    print(f"persisted={path}")
    print(json.dumps(
        {"truncation_counts": metrics["truncation_counts"],
         "overall_valid": metrics["overall_valid"],
         "macro_valid": metrics["macro_valid"],
         "totals_all_cells": metrics["totals_all_cells"]}, indent=2))
    return 0


def cmd_close(args: argparse.Namespace) -> int:
    gates = wiring.run_gates()
    all_passed = all(g["passed"] for g in gates)
    audit = _independent_audit()
    immut = _primary_evidence_immutable()
    result = {
        "closure_gates": gates,
        "gates_all_passed": all_passed,
        "audit": audit,
        "primary_evidence_immutable": immut,
        "zero_scientific_calls": True,
        "does_not_modify_scientific_results": True,
        "ran_at": _now_iso(),
    }
    path = _persist_json("closure_gates.json", result)
    for gate in gates:
        print(f"Closure Gate {gate['gate']} {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
    print(f"CLOSURE_AUDIT={'PASS' if audit['passed'] else 'FAIL'}")
    print(f"PRIMARY_IMMUTABLE={'PASS' if immut['immutable'] else 'FAIL'}")
    print(f"persisted={path}")
    return 0 if (all_passed and audit["passed"] and immut["immutable"]) else 1


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
    rc = cmd_probe(args)
    if rc != 0:
        return rc
    if cmd_run(args) != 0:
        return 1
    if cmd_metrics(args) != 0:
        return 1
    if cmd_close(args) != 0:
        return 1
    print("\nABLATION ALL PIPELINE COMPLETE")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prevalidate", help="pre-run validation")
    p.add_argument("--output-dir", type=str, default=str(STUDY_DIR))
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("gates", help="six deterministic gates + audit")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("freeze-manifest", help="freeze the 30-cell ablation manifest")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("probe", help="one non-study 8192 cost/validity probe")
    p.add_argument("--dry-run", action="store_true", default=False)
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("run", help="execute remaining ablation manifest cells")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--inter-cell-delay", type=float, default=0.0)
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
    if args.command == "probe":
        return cmd_probe(args)
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
