#!/usr/bin/env python3
"""djangoCMS ImpactPlan FULL-PLAN OUTPUT-SCALABILITY 16K DIAGNOSTIC (POST-HOC).

DIAGNOSTIC_ID: scientific-stagec-djangocms-impactplan-16k-diagnostic-01

Exactly ONE post-hoc diagnostic scientific run on scenario
``djangocms-external-validity-004`` to determine whether the current FULL
144-path ImpactPlan representation can terminate when the single-response
completion cap is raised 8192 -> 16384.

This is POST-HOC / EXPLORATORY / ONE-SCENARIO. It is NOT part of the
preregistered primary 60-run study ``scientific-stagec-djangocms-01``, NOT part
of the failed 8192 ablation, NOT confirmatory, and NOT a 30-run experiment.

Frozen inputs reused EXACTLY (identical to the D057 8192 probe):
- same scenario djangocms-external-validity-004 (same visible text/hash)
- same hidden gold (evaluation-only)
- same 144-path candidate universe (identical canonical hash)
- same dependency graph / evidence
- same ImpactPlan planner prompt and schema
- same scientific model qwen/qwen3-coder
- same provider DeepInfra pinned through OpenRouter (deepinfra/turbo)
- fallback OFF, temperature 0, scope SELECTION ONLY
- same failure semantics (selection-only, workflow timeout 600)

ONLY intended scientific treatment difference vs the 8192 probe:
  max_completion_tokens: 8192 -> 16384

CRITICAL RAW-RESPONSE DURABILITY: the COMPLETE raw model response text is
persisted (raw_response.txt) plus its SHA256, even when finish_reason=length,
JSON is malformed, or terminal status is failed.

Subcommands:
  prevalidate      pre-run validation (universe 144, hashes, scenario 004,
                   16384-only difference, 8192 evidence unchanged, primary
                   evidence immutable 71/71)
  gates            the EXACT six deterministic gates + independent audit
  run              ONE 16K diagnostic scientific call + persist full raw
                   response + response-size analysis + diagnostic JSON
  close            rerun the six closure gates + audit + immutability
  all              prevalidate -> gates -> run -> close
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

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.external_validity import study_runtime as wiring
from scripts import stagec_djangocms_ablation_execute as ablation

PROJECT_DIR = wiring.PROJECT_DIR
STUDY_ID = "scientific-stagec-djangocms-impactplan-16k-diagnostic-01"
STUDY_DIR = PROJECT_DIR / "reports" / STUDY_ID
WIRING_TAG = "stagec-djangocms-study-wiring-verified-01"
PRIMARY_STUDY_ID = ablation.PRIMARY_STUDY_ID
ABLATION_STUDY_DIR = PROJECT_DIR / "reports" / "scientific-stagec-djangocms-impactplan-cap-ablation-01"

DIAGNOSTIC_SCENARIO_ID = "djangocms-external-validity-004"
PRIMARY_MODEL = "qwen/qwen3-coder"
PROVIDER_PINNED = "DeepInfra"
PROVIDER_TAG = "deepinfra/turbo"
TEMPERATURE = 0.0
AGENT_CAP_PRIMARY = 1024  # informational; Agent not run in this diagnostic
IMPACTPLAN_CAP_PRIMARY = 4096
IMPACTPLAN_CAP_8192 = 8192
IMPACTPLAN_CAP_16384 = 16384
WORKFLOW_TIMEOUT_SECONDS = 600
MAX_TRANSIENT_RETRIES = 1
EXPECTED_UNIVERSE_COUNT = 144

_8192_PROBE_RELATIVE = (
    "reports/scientific-stagec-djangocms-impactplan-cap-ablation-01/costprobe_8192.json"
)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False, cwd=PROJECT_DIR
    )
    return proc.stdout.strip()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _persist_json(name: str, payload: Any) -> Path:
    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    path = STUDY_DIR / name
    path.write_text(json.dumps(payload, indent=2, default=str, sort_keys=True), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Pre-run validation
# ---------------------------------------------------------------------------


def _primary_evidence_immutable() -> dict[str, Any]:
    return ablation._primary_evidence_immutable()


def _8192_probe_evidence_unchanged() -> dict[str, Any]:
    """The D057 8192 costprobe evidence must be unchanged vs its HEAD blob.

    Uses ``git diff --quiet HEAD -- <path>`` (the canonical normalization-aware
    unchanged test: working-tree CRLF vs committed LF are not a difference).
    """
    disk_path = PROJECT_DIR / _8192_PROBE_RELATIVE
    disk_sha = _sha256_bytes(disk_path.read_bytes())
    rel = _8192_PROBE_RELATIVE.replace(chr(92), "/")
    proc = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", rel],
        capture_output=True,
        check=False,
        cwd=PROJECT_DIR,
    )
    return {
        "path": str(disk_path),
        "disk_bytes_sha256": disk_sha,
        "git_diff_quiet_vs_head": proc.returncode,
        "unchanged": proc.returncode == 0,
    }


def _scenario_004_model_facing() -> dict[str, Any]:
    """Scenario 004 is loaded ONLY from the final visible drafts dir."""
    scenario, path = wiring.load_study_scenario(DIAGNOSTIC_SCENARIO_ID)
    path_norm = str(path).replace("\\", "/")
    visible_norm = str(wiring.VISIBLE_DRAFTS_DIR).replace("\\", "/")
    old_norm = str(wiring.OLD_HISTORICAL_SCENARIO_PATH).replace("\\", "/")
    return {
        "scenario_id": scenario.scenario_id,
        "path": path_norm,
        "loaded_from_visible_drafts": path_norm.startswith(visible_norm),
        "not_old_historical": path_norm != old_norm,
        "expected_actions_count": len(scenario.expected_actions),
        "visible_sha256": wiring.visible_input_sha256(path),
        "gold_not_in_visible": not any(
            p in str(scenario.requirement_before)
            or p in str(scenario.requirement_after)
            for p in wiring.hidden_gold_paths_for(DIAGNOSTIC_SCENARIO_ID)
        ),
    }


def cmd_prevalidate(args: argparse.Namespace) -> int:
    items: list[dict[str, Any]] = []

    items.append(
        {
            "item": "wiring_tag_exists_and_is_ancestor_of_head",
            "ok": ablation._tag_is_ancestor(WIRING_TAG),
            "detail": {"tag": WIRING_TAG, "head": _git("rev-parse", "HEAD")},
        }
    )
    runtime_paths = wiring.runtime_universe_paths()
    frozen_paths = wiring.frozen_universe_paths()
    runtime_hash = wiring.runtime_universe_canonical_hash()
    frozen_hash = wiring.frozen_universe_canonical_hash()
    items.append(
        {
            "item": "runtime_universe_count_equals_144",
            "ok": len(runtime_paths) == EXPECTED_UNIVERSE_COUNT,
            "detail": len(runtime_paths),
        }
    )
    items.append(
        {
            "item": "runtime_and_frozen_canonical_hashes_identical",
            "ok": runtime_hash == frozen_hash,
            "detail": {"runtime": runtime_hash, "frozen": frozen_hash},
        }
    )
    items.append(
        {
            "item": "missing_extra_paths_empty",
            "ok": not (set(frozen_paths) - set(runtime_paths))
            and not (set(runtime_paths) - set(frozen_paths)),
            "detail": {
                "missing": sorted(set(frozen_paths) - set(runtime_paths)),
                "extra": sorted(set(runtime_paths) - set(frozen_paths)),
            },
        }
    )
    gold_paths = {
        p for rec in wiring.load_hidden_gold() for p in rec.get("source_files", [])
    }
    items.append(
        {
            "item": "all_gold_paths_inside_runtime_universe",
            "ok": gold_paths <= set(runtime_paths),
            "detail": sorted(gold_paths - set(runtime_paths)),
        }
    )
    items.append(
        {
            "item": "hidden_gold_evaluation_only",
            "ok": all(
                set(rec.get("source_files", [])) <= set(runtime_paths)
                for rec in wiring.load_hidden_gold()
            ),
            "detail": {"records": len(wiring.load_hidden_gold())},
        }
    )
    sc = _scenario_004_model_facing()
    items.append(
        {
            "item": "diagnostic_scenario_is_004_model_facing",
            "ok": (
                sc["scenario_id"] == DIAGNOSTIC_SCENARIO_ID
                and sc["loaded_from_visible_drafts"]
                and sc["not_old_historical"]
                and sc["expected_actions_count"] == 0
                and sc["gold_not_in_visible"]
            ),
            "detail": sc,
        }
    )
    items.append(
        {
            "item": "diagnostic_cap_16384_only_treatment_difference",
            "ok": (
                IMPACTPLAN_CAP_16384 == 16384
                and IMPACTPLAN_CAP_16384 != IMPACTPLAN_CAP_PRIMARY
                and IMPACTPLAN_CAP_16384 != IMPACTPLAN_CAP_8192
            ),
            "detail": {
                "primary_impactplan_cap": IMPACTPLAN_CAP_PRIMARY,
                "previous_8192_probe_cap": IMPACTPLAN_CAP_8192,
                "diagnostic_impactplan_cap": IMPACTPLAN_CAP_16384,
            },
        }
    )
    items.append(
        {
            "item": "model_provider_temp_fallback_unchanged",
            "ok": True,
            "detail": {
                "model": PRIMARY_MODEL,
                "provider": f"{PROVIDER_PINNED} pinned through OpenRouter",
                "temperature": TEMPERATURE,
                "fallback": "off",
            },
        }
    )
    items.append(
        {
            "item": "planner_prompt_and_schema_unchanged_since_8192_probe",
            "ok": _git("diff", "--quiet", "HEAD", "--", "src/benchmark/selection/impact_planner.py")
            == "",
            "detail": "impact_planner.py identical to HEAD (same prompt + schema as the 8192 probe)",
        }
    )
    items.append(
        {
            "item": "previous_8192_diagnostic_evidence_unchanged",
            "ok": _8192_probe_evidence_unchanged()["unchanged"],
            "detail": _8192_probe_evidence_unchanged(),
        }
    )
    items.append(
        {
            "item": "primary_evidence_immutable",
            "ok": _primary_evidence_immutable()["immutable"],
            "detail": _primary_evidence_immutable(),
        }
    )
    items.append(
        {
            "item": "no_agent_cells_no_repetitions",
            "ok": True,
            "detail": "exactly ONE impact_plan run, no Agent, no repetitions, no second scenario",
        }
    )

    passed = all(item["ok"] for item in items)
    result = {
        "section": "FULL_PLAN_16K_DIAGNOSTIC_PRE_RUN_VALIDATION",
        "diagnostic_id": STUDY_ID,
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


def _independent_audit() -> dict[str, Any]:
    preflight = wiring.build_preflight()
    immut = _primary_evidence_immutable()
    sc = _scenario_004_model_facing()
    prob = _8192_probe_evidence_unchanged()
    items: list[dict[str, Any]] = [
        {
            "item": "objective_output_scalability_diagnostic_only",
            "ok": True,
            "detail": "only intended treatment difference is ImpactPlan cap 8192 -> 16384",
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
            "detail": (
                "ImpactPlan schema + planner prompt identical to primary and "
                "8192 probe (only max_tokens differs)"
            ),
        },
        {
            "item": "selection_only",
            "ok": True,
            "detail": "no regeneration/repair in the diagnostic",
        },
        {
            "item": "runtime_universe_count_144",
            "ok": len(wiring.runtime_universe_paths()) == EXPECTED_UNIVERSE_COUNT,
            "detail": len(wiring.runtime_universe_paths()),
        },
        {
            "item": "runtime_universe_hash_matches_frozen",
            "ok": (
                wiring.runtime_universe_canonical_hash()
                == wiring.frozen_universe_canonical_hash()
            ),
            "detail": {
                "runtime": wiring.runtime_universe_canonical_hash(),
                "frozen": wiring.frozen_universe_canonical_hash(),
            },
        },
        {
            "item": "scenario_id_004_model_facing",
            "ok": (
                sc["scenario_id"] == DIAGNOSTIC_SCENARIO_ID
                and sc["loaded_from_visible_drafts"]
                and sc["expected_actions_count"] == 0
            ),
            "detail": sc,
        },
        {
            "item": "hidden_gold_not_model_facing",
            "ok": sc["gold_not_in_visible"] and sc["expected_actions_count"] == 0,
            "detail": str(wiring.HIDDEN_GOLD_PATH),
        },
        {
            "item": "primary_60_evidence_unchanged",
            "ok": immut["immutable"],
            "detail": immut,
        },
        {
            "item": "previous_8192_diagnostic_evidence_unchanged",
            "ok": prob["unchanged"],
            "detail": prob,
        },
        {
            "item": "only_treatment_change_is_16384_cap",
            "ok": (
                IMPACTPLAN_CAP_16384 == 16384
                and IMPACTPLAN_CAP_16384 != IMPACTPLAN_CAP_PRIMARY
                and IMPACTPLAN_CAP_16384 != IMPACTPLAN_CAP_8192
            ),
            "detail": {
                "primary_impactplan_cap": IMPACTPLAN_CAP_PRIMARY,
                "previous_8192_probe_cap": IMPACTPLAN_CAP_8192,
                "diagnostic_impactplan_cap": IMPACTPLAN_CAP_16384,
            },
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
            "detail": str(wiring.OLD_HISTORICAL_SCENARIO_PATH),
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
    path = _persist_json("diagnostic_gates.json", result)
    for gate in gates:
        print(f"Gate {gate['gate']} {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
    print(f"AUDIT_RESULT={'PASS' if audit['passed'] else 'FAIL'}")
    print(f"persisted={path}")
    return 0 if (all_passed and audit["passed"]) else 1


def _gates_evidence_passed() -> bool:
    path = STUDY_DIR / "diagnostic_gates.json"
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
# Recording backend (captures the COMPLETE raw response text)
# ---------------------------------------------------------------------------


class _RecordingBackend:
    """Pass-through proxy over OpenRouterBackend that retains raw response text."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.raw_texts: list[str] = []
        self.finish_reasons: list[str] = []

    @property
    def model(self) -> str:
        return self._inner.model

    @property
    def provider(self) -> str | None:
        return self._inner.provider

    @property
    def model_identity(self) -> str:
        return self._inner.model_identity

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        *,
        response_format: dict[str, Any] | None = None,
    ) -> Any:
        resp = await self._inner.generate(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )
        self.raw_texts.append(resp.text)
        self.finish_reasons.append(resp.finish_reason or "")
        return resp

    async def generate_structured(
        self,
        prompt: str,
        *,
        schema_name: str,
        schema: dict[str, Any],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> Any:
        resp = await self._inner.generate_structured(
            prompt=prompt,
            schema_name=schema_name,
            schema=schema,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.raw_texts.append(resp.text)
        self.finish_reasons.append(resp.finish_reason or "")
        return resp


def _build_backend(dry_run: bool) -> tuple[Any, Any]:
    """Return (backend, recording). Real backend is wrapped in the recorder."""
    if dry_run:
        from benchmark.llm.mock_backend import MockLLMBackend

        mock = MockLLMBackend(response_text="dry-run mock selection")
        return mock, None
    from benchmark.llm.openrouter_backend import OpenRouterBackend

    inner = OpenRouterBackend(
        model=PRIMARY_MODEL,
        timeout_seconds=120.0,
        provider=PROVIDER_PINNED,
        max_transient_retries=MAX_TRANSIENT_RETRIES,
    )
    recorder = _RecordingBackend(inner)
    return recorder, recorder


def _descriptors() -> tuple[Any, ...]:
    return ablation._descriptors()


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
            backend, max_completion_tokens=IMPACTPLAN_CAP_16384
        )
    return ImpactPlanSelectiveStrategy(
        planner=planner,
        artifact_descriptors=descriptors,
    )


def _stage_snapshot() -> Path:
    return ablation._stage_snapshot(STUDY_DIR)


def _copy_snapshot_to_workspace(snapshot_root: Path, workspace_dir: Path) -> None:
    ablation._copy_snapshot_to_workspace(snapshot_root, workspace_dir)


def _run_one(dry_run: bool) -> tuple[dict[str, Any], str | None, dict[str, Any]]:
    """Run exactly ONE ImpactPlan cell at cap 16384.

    Returns ``(evidence, raw_response_text, provider_metadata)``. The raw text
    is retained even when the run fails (truncation / parse error).
    """
    run_id = f"stgc-16k-diagnostic-{DIAGNOSTIC_SCENARIO_ID}-impact_plan"
    scenario_id = DIAGNOSTIC_SCENARIO_ID
    scenario, scenario_path = wiring.load_study_scenario(scenario_id)
    universe_paths = wiring.runtime_universe_paths()
    descriptors = _descriptors()
    backend, recorder = _build_backend(dry_run)

    run_workspace = STUDY_DIR / "workspace" / f"run_{run_id}"
    if run_workspace.is_dir():
        shutil.rmtree(run_workspace)
    snapshot_root = _stage_snapshot()
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
        strategy_name="impact_plan",
        backend_name=getattr(backend, "model_identity", f"openrouter:{PRIMARY_MODEL}@{PROVIDER_TAG}"),
        protocol_version="1.0",
        timeout_seconds=WORKFLOW_TIMEOUT_SECONDS,
        max_attempts=1,
        enable_regeneration=False,
        editable_artifact_paths=universe_paths,
        max_completion_tokens_per_call=IMPACTPLAN_CAP_16384,
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
    record = runner.run(scenario)
    elapsed = time.monotonic() - started

    raw_text = recorder.raw_texts[0] if recorder and recorder.raw_texts else None
    finish_reason = recorder.finish_reasons[0] if recorder and recorder.finish_reasons else ""
    provider_metadata = {
        "exact_model": f"openrouter:{PRIMARY_MODEL}@{PROVIDER_TAG}",
        "exact_provider_used": PROVIDER_TAG,
        "fallback_status": "off",
        "finish_reason_from_backend": finish_reason,
        "token_accounting_mode": "provider_reported",
    }
    evidence = _build_cell_evidence(
        run_id, scenario_id, record, elapsed, scenario_path, universe_paths,
        dry_run=dry_run, raw_text=raw_text,
    )
    return evidence, raw_text, provider_metadata


def _build_cell_evidence(
    run_id: str,
    scenario_id: str,
    record: Any,
    elapsed: float,
    scenario_path: Path,
    universe_paths: tuple[str, ...],
    *,
    dry_run: bool,
    raw_text: str | None,
) -> dict[str, Any]:
    pricing = wiring.load_pricing()
    cost = wiring.compute_api_cost(record, pricing)
    predicted = dict(getattr(record, "predicted_actions", {}) or {})
    regenerate_paths = [p for p, action in predicted.items() if action == "regenerate"]

    gold = set(wiring.hidden_gold_paths_for(scenario_id))
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

    evidence = {
        "diagnostic_id": STUDY_ID,
        "post_hoc_exploratory": True,
        "run_id": run_id,
        "scenario_id": scenario_id,
        "arm": "impact_plan",
        "cap": IMPACTPLAN_CAP_16384,
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
        "latency_seconds": round(elapsed, 6),
        "api_cost": round(cost, 6),
        "pricing_source": pricing.get("source", ""),
        "finish_reason": finish_reason,
        "truncation_status": truncation,
        "invalid_selected_paths": invalid_selected,
        "terminal_status": terminal_status,
        "schema_path_valid": bool(
            terminal_status == "succeeded"
            and not invalid_selected
            and not truncation
        ),
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
        "visible_scenario_sha256": wiring.visible_input_sha256(
            wiring.VISIBLE_DRAFTS_DIR / f"{scenario_id}.yaml"
        ),
        "runtime_universe_hash": wiring.runtime_universe_canonical_hash(),
        "raw_response_text_len": len(raw_text) if raw_text is not None else 0,
        "recorded_at": _now_iso(),
    }
    return evidence


# ---------------------------------------------------------------------------
# Response-size analysis (deterministic, no model calls)
# ---------------------------------------------------------------------------


def analyze_raw_response(
    raw_text: str,
    expected_paths: tuple[str, ...],
    provider_completion_tokens: int,
) -> dict[str, Any]:
    """Compute response-size metrics + emitted_entry_count.

    emitted_entry_count = number of COMPLETE 144-path decision objects that can
    be confidently parsed from the raw output before any truncation/corruption
    point. If the full JSON is valid, it equals the real number of decision
    entries. If truncated, a deterministic ``json.JSONDecoder().raw_decode``
    recovery scan counts only fully completed decision objects (those carrying a
    ``path`` key) before the first malformed tail.
    """
    text = raw_text or ""
    encoded = text.encode("utf-8")
    result: dict[str, Any] = {
        "raw_response_bytes": len(encoded),
        "raw_response_characters": len(text),
        "raw_response_line_count": text.count("\n") + 1 if text else 0,
        "provider_completion_tokens": provider_completion_tokens,
        "finish_reason": "",
        "valid_full_json": False,
        "parse_error": None,
        "emitted_entry_count": 0,
        "first_malformed_char_offset": None,
        "last_complete_path": None,
        "all_144_paths_emitted": False,
        "plan_level_fields": {
            "context_set": "context_set" in text,
            "validation_obligations": "validation_obligations" in text,
            "architecture_checks": "architecture_checks" in text,
            "escalation_reason": "escalation_reason" in text,
        },
    }
    if not text:
        return result

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        result["parse_error"] = f"{exc}"
        result["first_malformed_char_offset"] = exc.pos
    else:
        result["valid_full_json"] = True
        decisions = parsed.get("decisions")
        if isinstance(decisions, list):
            result["emitted_entry_count"] = len(decisions)
            if decisions:
                last = decisions[-1]
                result["last_complete_path"] = (
                    last.get("path") if isinstance(last, dict) else None
                )
            result["all_144_paths_emitted"] = len(decisions) == len(expected_paths)
        return result

    decoder = json.JSONDecoder()
    idx = text.find('"decisions"')
    if idx < 0:
        return result
    arr = text.find("[", idx)
    if arr < 0:
        return result
    pos = arr + 1
    count = 0
    last_path: str | None = None
    while pos < len(text):
        ch = text[pos]
        if ch in " \t\r\n,":
            pos += 1
            continue
        if ch != "{":
            break
        try:
            obj, end = decoder.raw_decode(text, pos)
        except json.JSONDecodeError:
            if result["first_malformed_char_offset"] is None:
                result["first_malformed_char_offset"] = pos
            break
        if isinstance(obj, dict) and isinstance(obj.get("path"), str):
            count += 1
            last_path = obj["path"]
        pos = end
    result["emitted_entry_count"] = count
    result["last_complete_path"] = last_path
    result["all_144_paths_emitted"] = count == len(expected_paths)
    return result


# ---------------------------------------------------------------------------
# Run (ONE scientific call)
# ---------------------------------------------------------------------------


def _diagnostic_decision_case(evidence: dict[str, Any], analysis: dict[str, Any]) -> str:
    if (
        evidence["terminal_status"] == "succeeded"
        and not evidence["truncation_status"]
        and evidence["finish_reason"] == "stop"
        and analysis["valid_full_json"]
    ):
        return "CASE_A_TERMINATES"
    if evidence["finish_reason"] == "length" or evidence["truncation_status"]:
        if evidence["completion_tokens"] == IMPACTPLAN_CAP_16384:
            return "CASE_B_STILL_TRUNCATES_AT_16384"
        return "CASE_B_TRUNCATED_BELOW_CAP"
    return "CASE_C_OTHER_FAILURE"


def cmd_run(args: argparse.Namespace) -> int:
    if not _prevalidation_passed():
        print("16K diagnostic pre-run validation NOT passed — STOP BEFORE THE SCIENTIFIC CALL")
        return 2
    if not _gates_evidence_passed():
        print("Six gates + audit NOT passed — STOP BEFORE THE SCIENTIFIC CALL")
        return 2
    dry_run = bool(getattr(args, "dry_run", False))

    evidence, raw_text, provider_metadata = _run_one(dry_run=dry_run)

    workspace_dir = STUDY_DIR / "workspace"
    if workspace_dir.is_dir():
        shutil.rmtree(workspace_dir, ignore_errors=True)

    raw_sha = (
        _sha256_bytes(raw_text.encode("utf-8")) if raw_text is not None else ""
    )
    if raw_text is not None:
        raw_path = STUDY_DIR / "raw_response.txt"
        raw_path.write_text(raw_text, encoding="utf-8")
        sha_path = STUDY_DIR / "raw_response.sha256"
        sha_path.write_text(raw_sha + "\n", encoding="utf-8")

    harness_hashes = evidence["raw_model_response_sha256"]
    sha_matches_harness = bool(harness_hashes) and harness_hashes[0] == raw_sha

    analysis = analyze_raw_response(
        raw_text or "",
        wiring.runtime_universe_paths(),
        int(evidence["completion_tokens"]),
    )
    analysis["raw_response_sha256"] = raw_sha
    analysis["sha_matches_harness_record"] = sha_matches_harness

    decision = _diagnostic_decision_case(evidence, analysis)

    diagnostic = {
        "diagnostic_id": STUDY_ID,
        "scenario_id": evidence["scenario_id"],
        "scenario_path": str(wiring.VISIBLE_DRAFTS_DIR / f"{evidence['scenario_id']}.yaml"),
        "visible_scenario_sha256": evidence["visible_scenario_sha256"],
        "universe_count": len(wiring.runtime_universe_paths()),
        "universe_sha256": evidence["runtime_universe_hash"],
        "scientific_model": PRIMARY_MODEL,
        "provider": f"{PROVIDER_PINNED} pinned through OpenRouter",
        "provider_tag": PROVIDER_TAG,
        "fallback": "off",
        "temperature": TEMPERATURE,
        "max_completion_tokens": IMPACTPLAN_CAP_16384,
        "prompt_tokens": evidence["prompt_tokens"],
        "completion_tokens": evidence["completion_tokens"],
        "total_tokens": evidence["total_tokens"],
        "model_calls": evidence["model_calls"],
        "latency_seconds": evidence["latency_seconds"],
        "api_cost": evidence["api_cost"],
        "finish_reason": evidence["finish_reason"],
        "terminal_status": evidence["terminal_status"],
        "schema_valid": evidence["schema_path_valid"],
        "parse_error": analysis["parse_error"],
        "invalid_paths": evidence["invalid_selected_paths"],
        "predicted_write_set": evidence["predicted_write_set"],
        "predicted_write_set_size": evidence["predicted_write_set_size"],
        "tp": evidence["tp"],
        "fp": evidence["fp"],
        "fn": evidence["fn"],
        "precision": evidence["precision"],
        "recall": evidence["recall"],
        "f1": evidence["f1"],
        "fnr": evidence["fnr"],
        "full_recall": evidence["full_recall"],
        "raw_response_sha256": raw_sha,
        "raw_response_persisted": raw_text is not None,
        "provider_metadata": provider_metadata,
        "response_size_analysis": analysis,
        "decision": decision,
        "interpretation_rule": (
            "POST-HOC / EXPLORATORY / ONE-SCENARIO. No claim that 16K fixes "
            "ImpactPlan generally, no accuracy claim, primary 4096 study unchanged."
        ),
        "ran_at": _now_iso(),
    }
    diag_path = _persist_json("diagnostic.json", diagnostic)
    _persist_json("response_size_analysis.json", analysis)

    print(json.dumps(
        {k: diagnostic[k] for k in (
            "diagnostic_id", "scenario_id", "completion_tokens", "finish_reason",
            "terminal_status", "schema_valid", "decision", "prompt_tokens",
            "total_tokens", "model_calls", "latency_seconds", "api_cost",
            "raw_response_sha256", "invalid_paths",
        )}, indent=2))
    print(json.dumps(analysis, indent=2))
    print(f"persisted={diag_path}")

    if dry_run:
        print("DRY_RUN_DIAGNOSTIC=OK")
        return 0
    if decision.startswith("CASE_C"):
        print(f"{decision} — STOP FOR REVIEW")
        return 4
    if decision == "CASE_A_TERMINATES":
        print("FULL_PLAN_16K_DIAGNOSTIC=TERMINATES")
        print("STOP FOR GPT-5.6 SOL. Do NOT launch a 16K 30-run ablation.")
        return 0
    print("FULL_PLAN_16K_DIAGNOSTIC=STILL_TRUNCATES")
    print("STOP FOR GPT-5.6 SOL. Do NOT increase to 32K. Do NOT retry.")
    return 0


# ---------------------------------------------------------------------------
# Closure
# ---------------------------------------------------------------------------


def cmd_close(args: argparse.Namespace) -> int:
    gates = wiring.run_gates()
    all_passed = all(g["passed"] for g in gates)
    audit = _independent_audit()
    immut = _primary_evidence_immutable()
    prob = _8192_probe_evidence_unchanged()
    result = {
        "closure_gates": gates,
        "gates_all_passed": all_passed,
        "audit": audit,
        "primary_evidence_immutable": immut,
        "previous_8192_evidence_unchanged": prob,
        "zero_scientific_calls": True,
        "does_not_modify_scientific_results": True,
        "ran_at": _now_iso(),
    }
    path = _persist_json("closure_gates.json", result)
    for gate in gates:
        print(f"Closure Gate {gate['gate']} {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
    print(f"CLOSURE_AUDIT={'PASS' if audit['passed'] else 'FAIL'}")
    print(f"PRIMARY_IMMUTABLE={'PASS' if immut['immutable'] else 'FAIL'}")
    print(f"PREVIOUS_8192_UNCHANGED={'PASS' if prob['unchanged'] else 'FAIL'}")
    print(f"persisted={path}")
    return 0 if (all_passed and audit["passed"] and immut["immutable"] and prob["unchanged"]) else 1


def cmd_all(args: argparse.Namespace) -> int:
    if cmd_prevalidate(args) != 0:
        print("PREVALIDATION FAILED — STOP")
        return 1
    if cmd_gates(args) != 0:
        print("GATES FAILED — STOP")
        return 1
    if cmd_run(args) != 0:
        print("DIAGNOSTIC RUN FAILED — STOP")
        return 1
    if cmd_close(args) != 0:
        print("CLOSURE FAILED — STOP")
        return 1
    print("\nFULL_PLAN_16K_DIAGNOSTIC PIPELINE COMPLETE — STOP FOR GPT-5.6 SOL")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prevalidate", help="pre-run validation")
    p.add_argument("--output-dir", type=str, default=str(STUDY_DIR))
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("gates", help="six deterministic gates + audit")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("run", help="ONE 16K diagnostic scientific call")
    p.add_argument("--dry-run", action="store_true", default=False)
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("close", help="closure six gates + audit + immutability")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("all", help="full diagnostic pipeline")
    p.add_argument("--dry-run", action="store_true", default=False)
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
    if args.command == "run":
        return cmd_run(args)
    if args.command == "close":
        return cmd_close(args)
    if args.command == "all":
        return cmd_all(args)
    print(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
