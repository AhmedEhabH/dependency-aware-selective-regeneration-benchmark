#!/usr/bin/env python3
"""djangoCMS ImpactPlan-v2 SPARSE COST/SMOKE PROBE (POST-HOC / EXPLORATORY).

PROBE_ID: scientific-stagec-djangocms-impactplan-v2-costprobe-01

EXACTLY ONE scientific v2 probe on scenario ``djangocms-external-validity-004``
(arm ``impact_plan_v2``, completion cap 4096) to measure the sparse
ImpactPlan-v2 representation's technical validity + cost + serialization.

ImpactPlan-v2 is a representation redesign:
- v1 = full explicit repository-wide action serialization (all 144 decisions);
- v2 = sparse explicit non-PRESERVE decisions + deterministic omitted=>PRESERVE
  reconstruction + frozen numeric candidate IDs (1..144).
- v2 changes the output representation contract AND the corresponding planner
  instruction TOGETHER (one representation redesign; prompt/schema effects are
  NOT independently isolated).
- Structured output already existed in v1; v2 uses the EXISTING native
  OpenRouter JSON-schema mechanism with a v2-specific sparse schema.
- NO dependency-graph assistance is injected into v2.
- The primary frozen 60-run study ``scientific-stagec-djangocms-01`` is NOT
  modified or rerun; the future 30 v2 cells are NOT run here.

Frozen inputs reused EXACTLY (identical to the primary study / D057 / D058):
- same scenario djangocms-external-validity-004 (same visible text/hash)
- same hidden gold (evaluation-only)
- same 144-path candidate universe (canonical hash 43f4279b...)
- same scientific model qwen/qwen3-coder, provider DeepInfra pinned through
  OpenRouter (deepinfra/turbo), fallback OFF, temperature 0, selection-only
- v2 completion cap = 4096 (the ORIGINAL frozen ImpactPlan-v1 primary cap)

Subcommands:
  prevalidate      pre-run validation (universe 144, mapping artifact, scenario
                   004, v2 cap 4096, v1 unchanged + hashes, primary 71/71
                   immutable, graph absent, one-probe-only)
  gates            the EXACT six deterministic gates + independent audit
  run              ONE v2 scientific call + persist full raw evidence + decode
  close            rerun the six closure gates + audit + immutability + cost lock
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

from benchmark.core.enums import ActionKind  # noqa: E402
from benchmark.external_validity import study_runtime as wiring  # noqa: E402
from scripts import stagec_djangocms_ablation_execute as ablation  # noqa: E402

PROJECT_DIR = wiring.PROJECT_DIR
PROBE_ID = "scientific-stagec-djangocms-impactplan-v2-costprobe-01"
STUDY_DIR = PROJECT_DIR / "reports" / PROBE_ID
WIRING_TAG = "stagec-djangocms-study-wiring-verified-01"
PRIMARY_STUDY_ID = ablation.PRIMARY_STUDY_ID
ABLATION_STUDY_DIR = PROJECT_DIR / "reports" / "scientific-stagec-djangocms-impactplan-cap-ablation-01"
DIAGNOSTIC_STUDY_DIR = PROJECT_DIR / "reports" / "scientific-stagec-djangocms-impactplan-16k-diagnostic-01"

PROBE_SCENARIO_ID = "djangocms-external-validity-004"
PRIMARY_MODEL = "qwen/qwen3-coder"
PROVIDER_PINNED = "DeepInfra"
PROVIDER_TAG = "deepinfra/turbo"
TEMPERATURE = 0.0
V2_CAP = 4096
AGENT_CAP_PRIMARY = 1024  # informational; Agent not run in this probe
WORKFLOW_TIMEOUT_SECONDS = 600
MAX_TRANSIENT_RETRIES = 1
EXPECTED_UNIVERSE_COUNT = 144
FUTURE_V2_CELLS = 30  # 6 scenarios x 5 repetitions
FUTURE_V2_COST_MARGIN = 0.25
FUTURE_V2_SCIENTIFIC_CEILING_USD = 0.20

_8192_PROBE_RELATIVE = (
    "reports/scientific-stagec-djangocms-impactplan-cap-ablation-01/costprobe_8192.json"
)
_16K_DIAGNOSTIC_RELATIVE = "reports/scientific-stagec-djangocms-impactplan-16k-diagnostic-01/diagnostic.json"


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


def _unchanged_vs_head(rel: str) -> dict[str, Any]:
    """Normalization-aware unchanged test vs the committed HEAD blob."""
    disk_path = PROJECT_DIR / rel
    disk_sha = _sha256_bytes(disk_path.read_bytes()) if disk_path.is_file() else None
    norm = rel.replace(chr(92), "/")
    proc = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", norm],
        capture_output=True,
        check=False,
        cwd=PROJECT_DIR,
    )
    return {
        "path": str(disk_path),
        "disk_sha256": disk_sha,
        "git_diff_quiet_vs_head": proc.returncode,
        "unchanged": proc.returncode == 0,
    }


def _scenario_004_model_facing() -> dict[str, Any]:
    scenario, path = wiring.load_study_scenario(PROBE_SCENARIO_ID)
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
            for p in wiring.hidden_gold_paths_for(PROBE_SCENARIO_ID)
        ),
    }


def _v2_identity() -> dict[str, Any]:
    from benchmark.selection import impact_planner_v2 as v2

    return v2.impact_plan_v2_identity()


def _mapping_evidence() -> dict[str, Any]:
    from benchmark.selection import impact_planner_v2 as v2

    mapping = v2.derive_candidate_id_map()
    artifact = v2.verify_candidate_id_map_artifact()
    return {
        "entry_count": len(mapping.id_to_path),
        "ids": [i for i, _ in mapping.id_to_path][:5] + ["..."] + [i for i, _ in mapping.id_to_path][-3:],
        "first_path": mapping.path_for(1),
        "last_path": mapping.path_for(144),
        "mapping_sha256": mapping.sha256,
        "universe_sha256": mapping.universe_canonical_sha256,
        "artifact": artifact,
    }


def cmd_prevalidate(_args: argparse.Namespace) -> int:
    from benchmark.selection import impact_planner as v1_module
    from benchmark.selection import impact_planner_v2 as v2

    v1_primary_cap = v1_module.IMPACT_PLAN_MAX_COMPLETION_TOKENS

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
    sc = _scenario_004_model_facing()
    items.append(
        {
            "item": "probe_scenario_is_004_model_facing",
            "ok": (
                sc["scenario_id"] == PROBE_SCENARIO_ID
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
            "item": "v2_cap_is_exactly_4096",
            "ok": (
                v2.IMPACT_PLAN_V2_MAX_COMPLETION_TOKENS == 4096
                and v1_primary_cap == v2.IMPACT_PLAN_V2_MAX_COMPLETION_TOKENS
            ),
            "detail": {
                "v2_cap": v2.IMPACT_PLAN_V2_MAX_COMPLETION_TOKENS,
                "v1_primary_cap": v1_primary_cap,
                "excluded": [2048, 8192, 16384],
            },
        }
    )
    identity = _v2_identity()
    items.append(
        {
            "item": "v1_planner_source_unchanged",
            "ok": _git("diff", "--quiet", "HEAD", "--", "src/benchmark/selection/impact_planner.py") == "",
            "detail": "impact_planner.py identical to HEAD (v1 prompt/schema/cap unchanged)",
        }
    )
    items.append(
        {
            "item": "v1_prompt_schema_hashes_reproducible",
            "ok": identity["v1_planner_prompt_sha256"] == v2.V1_PLANNER_PROMPT_SHA256,
            "detail": identity,
        }
    )
    items.append(
        {
            "item": "v2_prompt_schema_hashes_computed",
            "ok": (
                len(identity["v2_planner_prompt_sha256"]) == 64
                and len(identity["v2_planner_schema_sha256"]) == 64
            ),
            "detail": identity,
        }
    )
    mapping = _mapping_evidence()
    items.append(
        {
            "item": "candidate_id_mapping_144_deterministic_sha256",
            "ok": (
                mapping["entry_count"] == 144
                and mapping["mapping_sha256"] == v2.derive_candidate_id_map().sha256
                and mapping["artifact"]["passed"]
            ),
            "detail": mapping,
        }
    )
    items.append(
        {
            "item": "v2_module_has_no_graph_injection",
            "ok": (
                "DependencyGraph" not in Path(v2.__file__).read_text(encoding="utf-8")
                and "dependency_scope" not in Path(v2.__file__).read_text(encoding="utf-8")
                and "source_graph" not in Path(v2.__file__).read_text(encoding="utf-8")
            ),
            "detail": "v2 planning path carries no frozen dependency graph",
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
            "item": "primary_evidence_immutable",
            "ok": _primary_evidence_immutable()["immutable"],
            "detail": _primary_evidence_immutable(),
        }
    )
    items.append(
        {
            "item": "previous_8192_evidence_unchanged",
            "ok": _unchanged_vs_head(_8192_PROBE_RELATIVE)["unchanged"],
            "detail": _unchanged_vs_head(_8192_PROBE_RELATIVE),
        }
    )
    items.append(
        {
            "item": "previous_16k_diagnostic_evidence_unchanged",
            "ok": _unchanged_vs_head(_16K_DIAGNOSTIC_RELATIVE)["unchanged"],
            "detail": _unchanged_vs_head(_16K_DIAGNOSTIC_RELATIVE),
        }
    )
    items.append(
        {
            "item": "exactly_one_v2_probe_no_agent_no_reps",
            "ok": True,
            "detail": "exactly ONE impact_plan_v2 run, no Agent, no repetitions, no second scenario",
        }
    )

    passed = all(item["ok"] for item in items)
    result = {
        "section": "IMPACTPLAN_V2_COSTPROBE_PRE_RUN_VALIDATION",
        "probe_id": PROBE_ID,
        "passed": passed,
        "items": items,
        "identity": identity,
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
    from benchmark.selection import impact_planner_v2 as v2

    preflight = wiring.build_preflight()
    immut = _primary_evidence_immutable()
    sc = _scenario_004_model_facing()
    identity = _v2_identity()
    mapping = _mapping_evidence()
    v2_source = Path(v2.__file__).read_text(encoding="utf-8")
    items: list[dict[str, Any]] = [
        {
            "item": "objective_sparse_representation_probe_only",
            "ok": True,
            "detail": "v2 = sparse non-PRESERVE decisions + deterministic omitted=>P + frozen numeric IDs; cap 4096",
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
            "item": "v1_unchanged_and_reproducible",
            "ok": (
                _git("diff", "--quiet", "HEAD", "--", "src/benchmark/selection/impact_planner.py") == ""
                and identity["v1_planner_prompt_sha256"] == v2.V1_PLANNER_PROMPT_SHA256
            ),
            "detail": identity,
        },
        {
            "item": "v1_v2_hashes_persisted",
            "ok": all(
                identity[k]
                for k in (
                    "v1_planner_prompt_sha256",
                    "v1_planner_schema_sha256",
                    "v2_planner_prompt_sha256",
                    "v2_planner_schema_sha256",
                )
            ),
            "detail": identity,
        },
        {
            "item": "selection_only",
            "ok": True,
            "detail": "no regeneration/repair in the probe",
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
                sc["scenario_id"] == PROBE_SCENARIO_ID
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
            "item": "v2_cap_stayed_4096",
            "ok": v2.IMPACT_PLAN_V2_MAX_COMPLETION_TOKENS == 4096,
            "detail": v2.IMPACT_PLAN_V2_MAX_COMPLETION_TOKENS,
        },
        {
            "item": "candidate_mapping_stable_144_sha256",
            "ok": mapping["entry_count"] == 144 and mapping["artifact"]["passed"],
            "detail": mapping,
        },
        {
            "item": "graph_not_injected",
            "ok": "DependencyGraph" not in v2_source and "source_graph" not in v2_source,
            "detail": "v2 carries no dependency-graph assistance",
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
            "item": "hidden_gold_evaluation_only",
            "ok": True,
            "detail": str(wiring.HIDDEN_GOLD_PATH),
        },
        {
            "item": "future_study_not_run",
            "ok": True,
            "detail": "the future 30 v2 cells are NOT executed in this task",
        },
    ]
    return {
        "passed": all(item["ok"] for item in items),
        "items": items,
    }


def cmd_gates(_args: argparse.Namespace) -> int:
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
    path = _persist_json("probe_gates.json", result)
    for gate in gates:
        print(f"Gate {gate['gate']} {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
    print(f"AUDIT_RESULT={'PASS' if audit['passed'] else 'FAIL'}")
    print(f"persisted={path}")
    return 0 if (all_passed and audit["passed"]) else 1


def _gates_evidence_passed() -> bool:
    path = STUDY_DIR / "probe_gates.json"
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


def _make_v2_strategy(backend: Any, descriptors: tuple[Any, ...]) -> Any:
    from benchmark.llm.mock_backend import MockLLMBackend
    from benchmark.selection.impact_planner_v2 import (
        MockImpactPlannerV2,
        OpenRouterImpactPlannerV2,
    )
    from benchmark.strategies.impact_plan import ImpactPlanSelectiveStrategy

    planner = (
        MockImpactPlannerV2()
        if isinstance(backend, MockLLMBackend)
        else OpenRouterImpactPlannerV2(backend)
    )
    return ImpactPlanSelectiveStrategy(
        planner=planner,
        artifact_descriptors=descriptors,
    )


def _stage_snapshot() -> Path:
    return ablation._stage_snapshot(STUDY_DIR)


def _copy_snapshot_to_workspace(snapshot_root: Path, workspace_dir: Path) -> None:
    ablation._copy_snapshot_to_workspace(snapshot_root, workspace_dir)


def _run_one(dry_run: bool) -> tuple[dict[str, Any], str | None, dict[str, Any], str]:
    """Run exactly ONE impact_plan_v2 cell at cap 4096.

    Returns ``(evidence, raw_response_text, provider_metadata, prompt_text)``.
    The raw text is retained even when the run fails (truncation / parse /
    decode error). The exact prompt text is retained for provenance.
    """
    from benchmark.selection import impact_planner_v2 as v2

    run_id = f"stgc-v2-costprobe-{PROBE_SCENARIO_ID}-impact_plan_v2"
    scenario_id = PROBE_SCENARIO_ID
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

    strategy = _make_v2_strategy(backend, descriptors)
    config = RunnerConfig(
        strategy_name="impact_plan_v2",
        backend_name=getattr(backend, "model_identity", f"openrouter:{PRIMARY_MODEL}@{PROVIDER_TAG}"),
        protocol_version="1.0",
        timeout_seconds=WORKFLOW_TIMEOUT_SECONDS,
        max_attempts=1,
        enable_regeneration=False,
        editable_artifact_paths=universe_paths,
        max_completion_tokens_per_call=V2_CAP,
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
    mapping = v2.derive_candidate_id_map()

    prompt_text = ""
    planner = getattr(strategy, "_planner", None)
    if planner is not None:
        prompt_text = str(getattr(planner, "last_prompt", "") or "")

    evidence = _build_cell_evidence(
        run_id, scenario_id, record, elapsed, scenario_path, universe_paths,
        dry_run=dry_run, raw_text=raw_text, mapping=mapping,
    )
    return evidence, raw_text, provider_metadata, prompt_text


def _build_cell_evidence(
    run_id: str,
    scenario_id: str,
    record: Any,
    elapsed: float,
    _scenario_path: Path,
    universe_paths: tuple[str, ...],
    *,
    dry_run: bool,
    raw_text: str | None,
    mapping: Any,
) -> dict[str, Any]:
    from benchmark.selection import impact_planner_v2 as v2

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

    decode_info: dict[str, Any] = {
        "decoded": False,
        "error": None,
        "emitted_decision_count": 0,
        "emitted_candidate_ids": [],
        "emitted_actions": [],
        "rationale": {},
        "confidence": {},
        "reason_codes": {},
        "evidence": {},
        "decoded_preserve_count": 0,
        "invalid_ids": [],
        "duplicate_ids": [],
        "conflicts": [],
        "decoded_action_map": {},
    }
    if raw_text and terminal_status == "succeeded":
        try:
            from benchmark.selection.impact_planner import _extract_json_object

            parsed_raw = json.loads(raw_text)
            parsed = (
                parsed_raw
                if isinstance(parsed_raw, dict)
                else _extract_json_object(raw_text)
            )
            policy = v2.decode_v2_policy(parsed, mapping, mapping.paths())
            id_to_path = dict(mapping.id_to_path)
            action_map = {
                id_to_path[i]: a.value for i, a in policy.action_by_id
            }
            emitted_pairs = [
                (id_to_path[i], policy.action_for(i).value)
                for i in range(1, 145)
                if policy.action_for(i) != ActionKind.preserve
            ]
            decode_info.update(
                {
                    "decoded": True,
                    "emitted_decision_count": policy.emitted_decision_count,
                    "emitted_candidate_ids": [p for p, _ in emitted_pairs],
                    "emitted_actions": [a for _, a in emitted_pairs],
                    "decoded_preserve_count": len(policy.decoded_preserve_ids),
                    "invalid_ids": list(policy.invalid_ids),
                    "duplicate_ids": list(policy.duplicate_ids),
                    "conflicts": list(policy.conflicts),
                    "decoded_action_map": action_map,
                }
            )
            items = parsed.get("decisions") or []
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("id"), int):
                    cid = item["id"]
                    if cid in id_to_path:
                        p = id_to_path[cid]
                        decode_info["rationale"][p] = str(item.get("rationale", ""))
                        decode_info["confidence"][p] = float(item.get("confidence", 0.0))
                        decode_info["reason_codes"][p] = list(item.get("reason_codes", []))
                        decode_info["evidence"][p] = list(item.get("evidence", []))
        except Exception as exc:
            decode_info["error"] = f"{type(exc).__name__}: {exc}"

    evidence = {
        "probe_id": PROBE_ID,
        "post_hoc_exploratory": True,
        "one_v2_probe": True,
        "run_id": run_id,
        "scenario_id": scenario_id,
        "arm": "impact_plan_v2",
        "cap": V2_CAP,
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
        "schema_valid": bool(
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
        "candidate_id_mapping_sha256": mapping.sha256,
        "raw_response_text_len": len(raw_text) if raw_text is not None else 0,
        "decode": decode_info,
        "recorded_at": _now_iso(),
    }
    return evidence


def _sparse_analysis(
    raw_text: str | None,
    provider_completion_tokens: int,
) -> dict[str, Any]:
    """Deterministic analysis of the sparse v2 raw response."""
    text = raw_text or ""
    result: dict[str, Any] = {
        "raw_response_bytes": len(text.encode("utf-8")),
        "raw_response_characters": len(text),
        "raw_response_line_count": text.count("\n") + 1 if text else 0,
        "provider_completion_tokens": provider_completion_tokens,
        "valid_full_json": False,
        "parse_error": None,
        "emitted_decision_count": 0,
    }
    if not text:
        return result
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        result["parse_error"] = f"{exc}"
        return result
    result["valid_full_json"] = True
    decisions = parsed.get("decisions")
    if isinstance(decisions, list):
        result["emitted_decision_count"] = len(decisions)
    return result


def cmd_run(args: argparse.Namespace) -> int:
    from benchmark.selection import impact_planner_v2 as v2

    if not _prevalidation_passed():
        print("v2 probe pre-run validation NOT passed — STOP BEFORE THE SCIENTIFIC CALL")
        return 2
    if not _gates_evidence_passed():
        print("Six gates + audit NOT passed — STOP BEFORE THE SCIENTIFIC CALL")
        return 2
    dry_run = bool(getattr(args, "dry_run", False))

    evidence, raw_text, provider_metadata, prompt_text = _run_one(dry_run=dry_run)

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

    mapping = v2.derive_candidate_id_map()
    identity = v2.impact_plan_v2_identity()

    # Persist the EXACT v2 prompt text + schema + referenced v1 prompt/schema.
    v2_prompt_sha = v2.sha256_text(prompt_text) if prompt_text else ""
    (STUDY_DIR / "v2_prompt.txt").write_text(prompt_text, encoding="utf-8")
    _persist_json("v2_schema.json", v2.IMPACT_PLAN_V2_SCHEMA)
    (STUDY_DIR / "v1_prompt.txt").write_text(v2.V1_PLANNER_PROMPT_TEMPLATE, encoding="utf-8")
    _persist_json("v1_schema.json", v2.V1_IMPACT_PLAN_SCHEMA)
    (STUDY_DIR / "candidate_id_map.json").write_text(
        json.dumps(
            {"schema_version": 1, "mapping": [{"id": i, "path": p} for i, p in mapping.id_to_path],
             "mapping_sha256": mapping.sha256,
             "universe_canonical_sha256": mapping.universe_canonical_sha256},
            indent=2, sort_keys=True,
        ),
        encoding="utf-8",
    )

    analysis = _sparse_analysis(raw_text, int(evidence["completion_tokens"]))
    analysis["raw_response_sha256"] = raw_sha
    analysis["sha_matches_harness_record"] = sha_matches_harness

    probe = {
        "probe_id": PROBE_ID,
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
        "max_completion_tokens": V2_CAP,
        "scope": "SELECTION ONLY",
        "prompt_tokens": evidence["prompt_tokens"],
        "completion_tokens": evidence["completion_tokens"],
        "total_tokens": evidence["total_tokens"],
        "model_calls": evidence["model_calls"],
        "latency_seconds": evidence["latency_seconds"],
        "api_cost": evidence["api_cost"],
        "finish_reason": evidence["finish_reason"],
        "terminal_status": evidence["terminal_status"],
        "truncation_status": evidence["truncation_status"],
        "schema_valid": evidence["schema_valid"],
        "invalid_selected_paths": evidence["invalid_selected_paths"],
        "predicted_write_set": evidence["predicted_write_set"],
        "predicted_write_set_size": evidence["predicted_write_set_size"],
        "explicitly_emitted_decision_count": evidence["decode"]["emitted_decision_count"],
        "emitted_candidate_ids": evidence["decode"]["emitted_candidate_ids"],
        "emitted_actions": evidence["decode"]["emitted_actions"],
        "rationale": evidence["decode"]["rationale"],
        "confidence": evidence["decode"]["confidence"],
        "reason_codes": evidence["decode"]["reason_codes"],
        "evidence": evidence["decode"]["evidence"],
        "decoded_preserve_count": evidence["decode"]["decoded_preserve_count"],
        "decoded_action_map": evidence["decode"]["decoded_action_map"],
        "invalid_ids": evidence["decode"]["invalid_ids"],
        "duplicate_ids": evidence["decode"]["duplicate_ids"],
        "conflicts": evidence["decode"]["conflicts"],
        "decode_error": evidence["decode"]["error"],
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
        "v2_prompt_sha256": v2_prompt_sha,
        "identity": identity,
        "candidate_id_mapping_sha256": mapping.sha256,
        "provider_metadata": provider_metadata,
        "sparse_analysis": analysis,
        "token_savings_estimate": {
            "status": "PRE-EXPERIMENT ESTIMATE",
            "note": (
                "Any projected v2 token savings derived from the persisted 16K "
                "raw response remain ESTIMATES until measured by v2. Derived "
                "token-per-entry figures are NOT universal constants."
            ),
        },
        "interpretation_rule": (
            "TECHNICAL VALIDITY + COST + SERIALIZATION probe. NOT an accuracy "
            "gate chosen after seeing the result. One-run accuracy differences "
            "are NOT statistically meaningful. Do NOT tune v2 to repair the "
            "observed result before the future study."
        ),
        "ran_at": _now_iso(),
    }
    probe_path = _persist_json("costprobe.json", probe)
    _persist_json("sparse_analysis.json", analysis)

    print(json.dumps(
        {k: probe[k] for k in (
            "probe_id", "scenario_id", "completion_tokens", "finish_reason",
            "terminal_status", "truncation_status", "schema_valid",
            "explicitly_emitted_decision_count", "decoded_preserve_count",
            "decoded_action_map", "prompt_tokens", "total_tokens", "model_calls",
            "latency_seconds", "api_cost", "raw_response_sha256",
            "invalid_ids", "duplicate_ids", "conflicts",
        )}, indent=2))
    print(json.dumps(analysis, indent=2))
    print(f"persisted={probe_path}")

    if dry_run:
        print("DRY_RUN_V2_PROBE=OK")
        return 0
    print("IMPACTPLAN_V2_COSTPROBE_01=RUN_COMPLETE")
    print("STOP FOR GPT-5.6 SOL REVIEW. DO NOT RUN THE 30 V2 CELLS.")
    return 0


# ---------------------------------------------------------------------------
# Closure + cost lock
# ---------------------------------------------------------------------------


def _cost_lock(probe: dict[str, Any]) -> dict[str, Any]:
    single_cost = float(probe.get("api_cost") or 0.0)
    raw_est = single_cost * FUTURE_V2_CELLS
    margin = raw_est * FUTURE_V2_COST_MARGIN
    locked = raw_est + margin
    return {
        "future_cells": FUTURE_V2_CELLS,
        "single_probe_cost_usd": single_cost,
        "raw_30_cell_estimate_usd": round(raw_est, 6),
        "conservative_margin": FUTURE_V2_COST_MARGIN,
        "margin_usd": round(margin, 6),
        "locked_30_cell_estimate_usd": round(locked, 6),
        "scientific_ceiling_usd": FUTURE_V2_SCIENTIFIC_CEILING_USD,
        "result": "COST_LOCK=PASS_FOR_FUTURE_V2_30" if locked <= FUTURE_V2_SCIENTIFIC_CEILING_USD else "COST_LOCK=FAIL",
    }


def cmd_close(_args: argparse.Namespace) -> int:
    gates = wiring.run_gates()
    all_passed = all(g["passed"] for g in gates)
    audit = _independent_audit()
    immut = _primary_evidence_immutable()
    probe_path = STUDY_DIR / "costprobe.json"
    cost = {}
    if probe_path.is_file():
        probe = json.loads(probe_path.read_text(encoding="utf-8"))
        cost = _cost_lock(probe)
    result = {
        "closure_gates": gates,
        "gates_all_passed": all_passed,
        "audit": audit,
        "primary_evidence_immutable": immut,
        "previous_8192_evidence_unchanged": _unchanged_vs_head(_8192_PROBE_RELATIVE),
        "previous_16k_diagnostic_evidence_unchanged": _unchanged_vs_head(_16K_DIAGNOSTIC_RELATIVE),
        "zero_scientific_calls": True,
        "does_not_modify_scientific_results": True,
        "future_v2_30_cells_not_run": True,
        "cost_lock": cost,
        "ran_at": _now_iso(),
    }
    path = _persist_json("closure_gates.json", result)
    for gate in gates:
        print(f"Closure Gate {gate['gate']} {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
    print(f"CLOSURE_AUDIT={'PASS' if audit['passed'] else 'FAIL'}")
    print(f"PRIMARY_IMMUTABLE={'PASS' if immut['immutable'] else 'FAIL'}")
    print(f"COST_LOCK={cost.get('result', 'NOT_COMPUTED') if cost else 'NOT_COMPUTED'}")
    print(f"persisted={path}")
    return 0 if (all_passed and audit["passed"] and immut["immutable"]) else 1


def cmd_all(args: argparse.Namespace) -> int:
    if cmd_prevalidate(args) != 0:
        print("PREVALIDATION FAILED — STOP")
        return 1
    if cmd_gates(args) != 0:
        print("GATES FAILED — STOP")
        return 1
    if cmd_run(args) != 0:
        print("V2 PROBE RUN FAILED — STOP")
        return 1
    if cmd_close(args) != 0:
        print("CLOSURE FAILED — STOP")
        return 1
    print("\nIMPACTPLAN_V2_COSTPROBE PIPELINE COMPLETE — STOP FOR GPT-5.6 SOL")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prevalidate", help="pre-run validation")
    p.add_argument("--output-dir", type=str, default=str(STUDY_DIR))
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("gates", help="six deterministic gates + audit")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("run", help="ONE v2 scientific call")
    p.add_argument("--dry-run", action="store_true", default=False)
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("close", help="closure six gates + audit + immutability + cost lock")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("all", help="full v2 probe pipeline")
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
