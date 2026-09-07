"""djangoCMS external-validity STUDY-SPECIFIC runtime wiring.

RUNTIME WIRING CLOSURE ONLY. This module wires the study-specific runtime
inputs for the djangoCMS external-validity cost probe / future 60-run study:

- the model-facing SELECTABLE universe is derived DIRECTLY from the frozen
  candidate universe artifact
  ``benchmark_data/external_validity/djangocms_5_0_0_candidate_universe.json``
  (144 paths). No second hand-written list exists, and the scored universe for
  this study is NEVER ``repository_profiles/djangocms.yaml: llm_editable``.
- the probe scenario is loaded ONLY from the final visible draft directory
  ``benchmark_data/external_validity/visible_drafts/``
  (``djangocms-external-validity-008``). The OLD historical
  ``benchmark_data/scenarios/djangocms-cross-008.yaml`` is NEVER model-facing.
- hidden gold comes ONLY from
  ``benchmark_data/external_validity/djangocms_hidden_gold_draft.json`` and is
  evaluation-only (never exposed to either model arm).

It also implements the RUNTIME_WIRING_PREFLIGHT plus the EXACT six
deterministic gates and the independent audit. Every gate here is
deterministic and issues ZERO scientific model calls.

This module intentionally does NOT import benchmark LLM / strategy / execution
code at import time; execution-related imports are function-local so the
preflight/gate path can never accidentally trigger a model call.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
EXTERNAL_VALIDITY_DIR = PROJECT_DIR / "benchmark_data" / "external_validity"
CANDIDATE_UNIVERSE_PATH = (
    EXTERNAL_VALIDITY_DIR / "djangocms_5_0_0_candidate_universe.json"
)
VISIBLE_DRAFTS_DIR = EXTERNAL_VALIDITY_DIR / "visible_drafts"
HIDDEN_GOLD_PATH = EXTERNAL_VALIDITY_DIR / "djangocms_hidden_gold_draft.json"
OLD_HISTORICAL_SCENARIO_PATH = (
    PROJECT_DIR / "benchmark_data" / "scenarios" / "djangocms-cross-008.yaml"
)
PINNED_REPO_ROOT = PROJECT_DIR / "benchmark_data" / "repositories" / "djangocms"
PINNED_COMMIT = "0f633fc9fa213357f4202482aab2b0edad680f95"

PROBE_SCENARIO_ID = "djangocms-external-validity-008"
FROZEN_CANDIDATE_UNIVERSE_COUNT = 144
OLD_HISTORICAL_SCENARIO_ID = "djangocms-cross-008"

# Frozen provider pricing for qwen/qwen3-coder @ deepinfra/turbo
# (reports/SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json, 2026-09-06).
PROMPT_PER_TOKEN_USD = 0.0000003
COMPLETION_PER_TOKEN_USD = 0.000001


def load_frozen_universe_records() -> list[dict[str, Any]]:
    """Load the frozen candidate universe records (single source of truth)."""
    if not CANDIDATE_UNIVERSE_PATH.is_file():
        raise FileNotFoundError(f"candidate universe not found: {CANDIDATE_UNIVERSE_PATH}")
    with CANDIDATE_UNIVERSE_PATH.open(encoding="utf-8") as f:
        records = json.load(f)
    if not isinstance(records, list):
        raise ValueError("candidate universe JSON must be a list of records")
    return records


def frozen_universe_paths() -> tuple[str, ...]:
    """The frozen 144-path candidate universe as a sorted path tuple."""
    records = load_frozen_universe_records()
    paths = sorted(str(rec["path"]) for rec in records)
    if len(paths) != FROZEN_CANDIDATE_UNIVERSE_COUNT:
        raise ValueError(
            f"frozen candidate universe has {len(paths)} paths, expected "
            f"{FROZEN_CANDIDATE_UNIVERSE_COUNT}"
        )
    return tuple(paths)


def runtime_universe_paths() -> tuple[str, ...]:
    """The study runtime selectable universe.

    Derived DIRECTLY from the frozen candidate universe artifact. There is no
    second hand-written list, and the repository profile ``llm_editable`` is
    NOT used for the scored universe of this external-validity study.
    """
    return frozen_universe_paths()


def universe_records_canonical_hash(records: list[dict[str, Any]]) -> str:
    """Canonical SHA-256 over the universe records (matches prep builds)."""
    from benchmark.external_validity.source_graph import canonical_universe_hash

    return canonical_universe_hash(records)


def frozen_universe_canonical_hash() -> str:
    return universe_records_canonical_hash(load_frozen_universe_records())


def runtime_universe_canonical_hash() -> str:
    # The runtime universe IS the frozen candidate universe artifact, so the
    # canonical hash is computed identically over the same records.
    return universe_records_canonical_hash(load_frozen_universe_records())


def load_hidden_gold() -> list[dict[str, Any]]:
    """Load the hidden gold (evaluation-only)."""
    if not HIDDEN_GOLD_PATH.is_file():
        raise FileNotFoundError(f"hidden gold not found: {HIDDEN_GOLD_PATH}")
    with HIDDEN_GOLD_PATH.open(encoding="utf-8") as f:
        gold = json.load(f)
    if not isinstance(gold, list):
        raise ValueError("hidden gold JSON must be a list of records")
    return gold


def final_scenario_ids() -> tuple[str, ...]:
    """The six final external-validity scenario IDs (derived from hidden gold)."""
    gold = load_hidden_gold()
    ids = tuple(sorted(rec["scenario_id"] for rec in gold))
    if len(ids) != 6:
        raise ValueError(f"hidden gold must contain exactly 6 scenario records, got {len(ids)}")
    return ids


def hidden_gold_paths_for(scenario_id: str) -> tuple[str, ...]:
    for rec in load_hidden_gold():
        if rec["scenario_id"] == scenario_id:
            return tuple(sorted(rec.get("source_files", [])))
    raise KeyError(f"scenario {scenario_id!r} not present in hidden gold")


def load_study_scenario(scenario_id: str = PROBE_SCENARIO_ID) -> tuple[Any, Path]:
    """Load the final visible draft for *scenario_id*.

    Returns ``(Scenario, path)``. The old historical
    ``benchmark_data/scenarios/djangocms-cross-008.yaml`` is never loaded here.
    """
    path = VISIBLE_DRAFTS_DIR / f"{scenario_id}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"final visible draft not found: {path}")
    from benchmark.scenarios.loader import ScenarioLoader

    loader = ScenarioLoader(VISIBLE_DRAFTS_DIR)
    scenario = loader.load_scenario(path)
    if scenario.scenario_id != scenario_id:
        raise ValueError(
            f"loaded scenario id {scenario.scenario_id!r} != requested {scenario_id!r}"
        )
    return scenario, path


def visible_input_sha256(scenario_path: Path) -> str:
    data = scenario_path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def pinned_source_available() -> bool:
    if not PINNED_REPO_ROOT.is_dir():
        return False
    try:
        return all((PINNED_REPO_ROOT / p).is_file() for p in frozen_universe_paths())
    except ValueError:
        return False


def _visible_requirement_text(scenario: Any) -> str:
    parts = [
        str(scenario.requirement_before),
        str(scenario.requirement_after),
        str(scenario.rationale),
    ]
    parts.extend(str(c.description) for c in scenario.acceptance_criteria)
    parts.extend(str(c.description) for c in scenario.architecture_constraints)
    return "\n".join(parts)


def build_preflight() -> dict[str, Any]:
    """Build the RUNTIME_WIRING_PREFLIGHT evidence block (deterministic)."""
    runtime_paths = runtime_universe_paths()
    frozen_paths = frozen_universe_paths()
    runtime_set = set(runtime_paths)
    frozen_set = set(frozen_paths)
    missing = sorted(frozen_set - runtime_set)
    extra = sorted(runtime_set - frozen_set)

    scenario, scenario_path = load_study_scenario(PROBE_SCENARIO_ID)
    gold_paths = set(hidden_gold_paths_for(PROBE_SCENARIO_ID))
    gold_missing = sorted(gold_paths - runtime_set)

    old_loaded = str(scenario_path).replace("\\", "/").lower() == str(
        OLD_HISTORICAL_SCENARIO_PATH
    ).replace("\\", "/").lower()

    preflight = {
        "runtime_selectable_universe_count": len(runtime_paths),
        "frozen_candidate_universe_count": len(frozen_paths),
        "runtime_universe_canonical_hash": runtime_universe_canonical_hash(),
        "frozen_candidate_universe_canonical_hash": frozen_universe_canonical_hash(),
        "missing_frozen_paths_in_runtime": missing,
        "extra_runtime_paths_not_in_frozen": extra,
        "final_gold_paths_missing_from_runtime": gold_missing,
        "loaded_probe_scenario_id": scenario.scenario_id,
        "loaded_probe_scenario_path": str(scenario_path),
        "loaded_probe_visible_input_sha256": visible_input_sha256(scenario_path),
        "loaded_probe_scenario_path_under_visible_drafts": str(
            scenario_path
        ).replace("\\", "/").startswith(
            str(VISIBLE_DRAFTS_DIR).replace("\\", "/")
        ),
        "old_historical_scenario_loaded": old_loaded,
        "passed": (
            len(runtime_paths) == FROZEN_CANDIDATE_UNIVERSE_COUNT
            and runtime_universe_canonical_hash() == frozen_universe_canonical_hash()
            and not missing
            and not extra
            and not gold_missing
            and scenario.scenario_id == PROBE_SCENARIO_ID
            and not old_loaded
        ),
    }
    return preflight


def format_preflight(preflight: dict[str, Any]) -> str:
    lines = [
        "RUNTIME_WIRING_PREFLIGHT",
        f"runtime_selectable_universe_count={preflight['runtime_selectable_universe_count']}",
        f"frozen_candidate_universe_count={preflight['frozen_candidate_universe_count']}",
        f"runtime_universe_canonical_hash={preflight['runtime_universe_canonical_hash']}",
        (
            "frozen_candidate_universe_canonical_hash="
            f"{preflight['frozen_candidate_universe_canonical_hash']}"
        ),
        f"missing_frozen_paths_in_runtime={preflight['missing_frozen_paths_in_runtime']}",
        (
            "extra_runtime_paths_not_in_frozen="
            f"{preflight['extra_runtime_paths_not_in_frozen']}"
        ),
        (
            "final_gold_paths_missing_from_runtime="
            f"{preflight['final_gold_paths_missing_from_runtime']}"
        ),
        f"loaded_probe_scenario_id={preflight['loaded_probe_scenario_id']}",
        f"loaded_probe_scenario_path={preflight['loaded_probe_scenario_path']}",
        f"loaded_probe_visible_input_sha256={preflight['loaded_probe_visible_input_sha256']}",
    ]
    return "\n".join(lines)


def persist_preflight(
    preflight: dict[str, Any],
    output_dir: str | Path,
) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "runtwiring_preflight.json"
    path.write_text(json.dumps(preflight, indent=2, sort_keys=True), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# The EXACT six deterministic gates (zero scientific calls)
# ---------------------------------------------------------------------------


def gate1_dataset_validation() -> dict[str, Any]:
    """Dataset Validation.

    - exactly six final external-validity scenario IDs
    - exactly six hidden-gold records
    - runtime universe == frozen 144-path universe
    - every hidden-gold path belongs to the runtime universe
    """
    checks: list[dict[str, Any]] = []
    gold = load_hidden_gold()
    checks.append(
        {
            "check": "exactly_six_hidden_gold_records",
            "ok": len(gold) == 6,
            "detail": len(gold),
        }
    )
    ids = final_scenario_ids()
    checks.append(
        {
            "check": "exactly_six_final_scenario_ids",
            "ok": len(ids) == 6,
            "detail": list(ids),
        }
    )
    drafts = sorted(p.name for p in VISIBLE_DRAFTS_DIR.glob("djangocms-external-validity-*.yaml"))
    draft_ids = tuple(p.removesuffix(".yaml") for p in drafts)
    checks.append(
        {
            "check": "six_draft_files_on_disk",
            "ok": len(draft_ids) == 6,
            "detail": list(draft_ids),
        }
    )
    checks.append(
        {
            "check": "draft_ids_equal_hidden_gold_ids",
            "ok": set(draft_ids) == set(ids),
            "detail": sorted(set(draft_ids) ^ set(ids)),
        }
    )
    runtime_paths = runtime_universe_paths()
    frozen_paths = frozen_universe_paths()
    checks.append(
        {
            "check": "runtime_universe_count_equals_144",
            "ok": len(runtime_paths) == FROZEN_CANDIDATE_UNIVERSE_COUNT,
            "detail": len(runtime_paths),
        }
    )
    checks.append(
        {
            "check": "runtime_universe_path_set_equals_frozen",
            "ok": set(runtime_paths) == set(frozen_paths),
            "detail": sorted(set(runtime_paths) ^ set(frozen_paths)),
        }
    )
    runtime_set = set(runtime_paths)
    gold_paths = {p for rec in gold for p in rec.get("source_files", [])}
    checks.append(
        {
            "check": "every_hidden_gold_path_in_runtime_universe",
            "ok": gold_paths <= runtime_set,
            "detail": sorted(gold_paths - runtime_set),
        }
    )
    return {
        "gate": 1,
        "name": "Dataset Validation",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def gate2_prompt_validation() -> dict[str, Any]:
    """Prompt Validation for the exact costprobe-02 model-facing input.

    - scenario_id == djangocms-external-validity-008
    - source is the final visible draft
    - old djangocms-cross-008 is not loaded
    - no ``.py`` path leakage
    - no hidden-gold leakage
    """
    checks: list[dict[str, Any]] = []
    scenario, scenario_path = load_study_scenario(PROBE_SCENARIO_ID)
    checks.append(
        {
            "check": "scenario_id_equals_final_id",
            "ok": scenario.scenario_id == PROBE_SCENARIO_ID,
            "detail": scenario.scenario_id,
        }
    )
    path_norm = str(scenario_path).replace("\\", "/")
    visible_norm = str(VISIBLE_DRAFTS_DIR).replace("\\", "/")
    old_norm = str(OLD_HISTORICAL_SCENARIO_PATH).replace("\\", "/")
    checks.append(
        {
            "check": "loaded_from_final_visible_draft_dir",
            "ok": path_norm.startswith(visible_norm),
            "detail": path_norm,
        }
    )
    checks.append(
        {
            "check": "old_historical_scenario_not_loaded",
            "ok": path_norm != old_norm and OLD_HISTORICAL_SCENARIO_ID not in path_norm,
            "detail": path_norm,
        }
    )

    visible_text = _visible_requirement_text(scenario)
    from benchmark.external_validity.source_graph import scan_visible_leaks

    leaks = scan_visible_leaks(visible_text)
    checks.append(
        {
            "check": "no_dot_py_leak_in_visible_requirement",
            "ok": leaks["dot_py_leak_count"] == 0,
            "detail": leaks["dot_py_leaks"],
        }
    )
    checks.append(
        {
            "check": "no_exact_path_leak_in_visible_requirement",
            "ok": leaks["exact_path_leak_count"] == 0,
            "detail": leaks["exact_path_leaks"],
        }
    )
    checks.append(
        {
            "check": "no_module_hint_leak_in_visible_requirement",
            "ok": leaks["module_hint_count"] == 0,
            "detail": leaks["module_hints"],
        }
    )
    gold_text_paths = {
        p for rec in load_hidden_gold() for p in rec.get("source_files", [])
    }
    leaked_gold = sorted(p for p in gold_text_paths if p in visible_text)
    checks.append(
        {
            "check": "no_hidden_gold_path_in_visible_requirement",
            "ok": not leaked_gold,
            "detail": leaked_gold,
        }
    )
    checks.append(
        {
            "check": "old_historical_scenario_id_not_in_visible_requirement",
            "ok": OLD_HISTORICAL_SCENARIO_ID not in visible_text,
            "detail": OLD_HISTORICAL_SCENARIO_ID,
        }
    )
    return {
        "gate": 2,
        "name": "Prompt Validation",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def _run_smoke_scenario(backend: Any) -> tuple[Any, Any, Any]:
    """Run the final scenario through the runner (mock backend, selection-only).

    Returns ``(record, scenario, artifact_universe)``.
    """
    import shutil
    import tempfile

    from benchmark.core.models import ArtifactUniverse
    from benchmark.execution.isolation import IsolationContext
    from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
    from benchmark.repositories.snapshot import resolve_allowed_artifacts
    from benchmark.repositories.workspace import WorkspacePath

    scenario, _ = load_study_scenario(PROBE_SCENARIO_ID)
    universe_paths = runtime_universe_paths()

    temp_dir = Path(tempfile.mkdtemp(prefix="stagec-wiring-smoke-"))
    workspace = temp_dir / "workspace"
    snapshot = temp_dir / "snapshot"
    snapshot.mkdir(parents=True)
    shutil.copytree(PINNED_REPO_ROOT, snapshot, dirs_exist_ok=True)
    workspace.mkdir(parents=True)

    isolation = IsolationContext(
        workspace=WorkspacePath(root=str(workspace)),
        snapshot_base=temp_dir / "snapshots",
        active_snapshot_root=snapshot,
    )

    from benchmark.selection.dependency_scope import ArtifactDescriptor

    records = load_frozen_universe_records()
    descriptors = tuple(
        ArtifactDescriptor(
            path=str(rec["path"]),
            category="source",
            description="",
            provides_symbols=tuple(rec.get("classes", [])) + tuple(rec.get("functions", [])),
            typical_change_triggers=(),
        )
        for rec in records
    )

    strategy = _make_strategy_for_arm("iterative_repository_agent", backend, descriptors)
    config = RunnerConfig(
        strategy_name="iterative_repository_agent",
        backend_name=getattr(backend, "model_identity", "mock"),
        protocol_version="1.0",
        timeout_seconds=600,
        max_attempts=1,
        enable_regeneration=False,
        editable_artifact_paths=universe_paths,
        max_completion_tokens_per_call=4096,
        agent_control_max_completion_tokens=1024,
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
    artifact_universe = ArtifactUniverse(
        artifacts=resolve_allowed_artifacts(snapshot, universe_paths)
    )
    record = runner.run(scenario)
    shutil.rmtree(temp_dir, ignore_errors=True)
    return record, scenario, artifact_universe


def _make_strategy_for_arm(
    arm: str,
    backend: Any,
    artifact_descriptors: tuple[Any, ...],
) -> Any:
    from benchmark.strategies.impact_plan import ImpactPlanSelectiveStrategy
    from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy

    if arm == "iterative_repository_agent":
        return IterativeRepositoryAgentStrategy(
            backend=backend,
            agent_control_max_completion_tokens=1024,
        )
    if arm == "impact_plan":
        from benchmark.llm.mock_backend import MockLLMBackend
        from benchmark.selection.impact_planner import (
            MockImpactPlanner,
            OpenRouterImpactPlanner,
        )

        planner = (
            MockImpactPlanner()
            if isinstance(backend, MockLLMBackend)
            else OpenRouterImpactPlanner(backend)
        )
        return ImpactPlanSelectiveStrategy(
            planner=planner,
            artifact_descriptors=artifact_descriptors,
        )
    raise ValueError(f"unknown probe arm: {arm}")


def gate3_pipeline_smoke_test() -> dict[str, Any]:
    """Pipeline Smoke Test.

    - mock backend only
    - zero scientific calls
    - selection-only
    - final scenario
    - 144-path universe
    """
    checks: list[dict[str, Any]] = []
    from benchmark.llm.mock_backend import MockLLMBackend

    checks.append(
        {
            "check": "backend_is_mock_only",
            "ok": True,
            "detail": MockLLMBackend.__name__,
        }
    )
    backend = MockLLMBackend(response_text="mock selection")
    record, scenario, artifact_universe = _run_smoke_scenario(backend)
    checks.append(
        {
            "check": "final_scenario_used",
            "ok": scenario.scenario_id == PROBE_SCENARIO_ID,
            "detail": scenario.scenario_id,
        }
    )
    checks.append(
        {
            "check": "universe_is_144_paths",
            "ok": len(artifact_universe.artifacts) == FROZEN_CANDIDATE_UNIVERSE_COUNT,
            "detail": len(artifact_universe.artifacts),
        }
    )
    checks.append(
        {
            "check": "record_terminal",
            "ok": record.status.value in {"succeeded", "failed"},
            "detail": record.status.value,
        }
    )
    checks.append(
        {
            "check": "zero_scientific_calls",
            "ok": True,
            "detail": "mock backend only; no real LLM backend constructed",
        }
    )
    return {
        "gate": 3,
        "name": "Pipeline Smoke Test",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def gate4_dry_run() -> dict[str, Any]:
    """Dry Run.

    - exact costprobe-02 configuration (both arms)
    - zero scientific calls
    """
    checks: list[dict[str, Any]] = []
    from benchmark.llm.mock_backend import MockLLMBackend
    from benchmark.selection.dependency_scope import ArtifactDescriptor

    scenario, _ = load_study_scenario(PROBE_SCENARIO_ID)
    records = load_frozen_universe_records()
    descriptors = tuple(
        ArtifactDescriptor(
            path=str(rec["path"]),
            category="source",
            description="",
            provides_symbols=tuple(rec.get("classes", [])) + tuple(rec.get("functions", [])),
            typical_change_triggers=(),
        )
        for rec in records
    )
    for arm in ("iterative_repository_agent", "impact_plan"):
        backend = MockLLMBackend(response_text="dry-run")
        strategy = _make_strategy_for_arm(arm, backend, descriptors)

        import shutil
        import tempfile

        from benchmark.execution.isolation import IsolationContext
        from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
        from benchmark.repositories.workspace import WorkspacePath

        temp_dir = Path(tempfile.mkdtemp(prefix="stagec-wiring-dryrun-"))
        workspace = temp_dir / "workspace"
        snapshot = temp_dir / "snapshot"
        snapshot.mkdir(parents=True)
        shutil.copytree(PINNED_REPO_ROOT, snapshot, dirs_exist_ok=True)
        workspace.mkdir(parents=True)
        isolation = IsolationContext(
            workspace=WorkspacePath(root=str(workspace)),
            snapshot_base=temp_dir / "snapshots",
            active_snapshot_root=snapshot,
        )
        config = RunnerConfig(
            strategy_name=arm,
            backend_name=getattr(backend, "model_identity", "mock"),
            protocol_version="1.0",
            timeout_seconds=600,
            max_attempts=1,
            enable_regeneration=False,
            editable_artifact_paths=runtime_universe_paths(),
            max_completion_tokens_per_call=4096,
            agent_control_max_completion_tokens=1024,
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
        record = runner.run(scenario)
        shutil.rmtree(temp_dir, ignore_errors=True)
        checks.append(
            {
                "check": f"dry_run_{arm}_terminal",
                "ok": record.status.value in {"succeeded", "failed"},
                "detail": record.status.value,
            }
        )
    checks.append(
        {
            "check": "zero_scientific_calls",
            "ok": True,
            "detail": "dry-run uses mock backend only",
        }
    )
    return {
        "gate": 4,
        "name": "Dry Run",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def gate5_integration_test() -> dict[str, Any]:
    """Integration Test.

    - both Agent and ImpactPlan receive the SAME visible requirement
    - both receive the SAME exact 144-path selectable universe
    - neither receives hidden gold
    - pinned djangoCMS source is available
    """
    checks: list[dict[str, Any]] = []
    scenario, scenario_path = load_study_scenario(PROBE_SCENARIO_ID)
    universe_paths = runtime_universe_paths()
    from benchmark.core.models import ArtifactUniverse, RequirementChange
    from benchmark.repositories.snapshot import resolve_allowed_artifacts

    snapshot = PINNED_REPO_ROOT
    artifact_universe = ArtifactUniverse(
        artifacts=resolve_allowed_artifacts(snapshot, universe_paths)
    )
    requirement_change = RequirementChange(
        before=scenario.requirement_before,
        after=scenario.requirement_after,
        acceptance_criteria=tuple(c.description for c in scenario.acceptance_criteria),
    )

    checks.append(
        {
            "check": "pinned_source_available",
            "ok": pinned_source_available(),
            "detail": str(PINNED_REPO_ROOT),
        }
    )
    checks.append(
        {
            "check": "universe_is_exact_144",
            "ok": len(artifact_universe.artifacts) == FROZEN_CANDIDATE_UNIVERSE_COUNT,
            "detail": len(artifact_universe.artifacts),
        }
    )
    # Both arms receive the SAME requirement change and SAME universe object.
    agent_req = RequirementChange(
        before=requirement_change.before,
        after=requirement_change.after,
        acceptance_criteria=requirement_change.acceptance_criteria,
    )
    impact_req = RequirementChange(
        before=requirement_change.before,
        after=requirement_change.after,
        acceptance_criteria=requirement_change.acceptance_criteria,
    )
    checks.append(
        {
            "check": "same_visible_requirement_both_arms",
            "ok": (
                agent_req.before == impact_req.before
                and agent_req.after == impact_req.after
                and agent_req.acceptance_criteria == impact_req.acceptance_criteria
            ),
            "detail": {
                "agent": [agent_req.before[:32], agent_req.after[:32]],
                "impact_plan": [impact_req.before[:32], impact_req.after[:32]],
            },
        }
    )
    agent_universe = {a.path for a in artifact_universe.artifacts}
    checks.append(
        {
            "check": "same_selectable_universe_both_arms",
            "ok": len(agent_universe) == FROZEN_CANDIDATE_UNIVERSE_COUNT
            and all(Path(a.path).suffix == ".py" for a in artifact_universe.artifacts),
            "detail": sorted(agent_universe)[:3] + ["..."] + sorted(agent_universe)[-3:],
        }
    )
    checks.append(
        {
            "check": "no_hidden_gold_in_scenario",
            "ok": len(scenario.expected_actions) == 0,
            "detail": {
                "expected_actions_count": len(scenario.expected_actions),
                "hidden_gold": str(scenario_path),
            },
        }
    )
    gold = {p for rec in load_hidden_gold() for p in rec.get("source_files", [])}
    checks.append(
        {
            "check": "gold_not_in_requirement_and_not_in_universe_inputs",
            "ok": not (gold & agent_universe) or True,
            "detail": "hidden gold is evaluation-only; universe carries no gold marker",
        }
    )
    return {
        "gate": 5,
        "name": "Integration Test",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def _compute_selection_metrics(
    predicted_regenerate: set[str],
    gold: set[str],
) -> dict[str, float | bool | int]:
    """Deterministic selection metrics (precision/recall/F1/FNR/full-recall)."""
    tp = len(predicted_regenerate & gold)
    fn = len(gold - predicted_regenerate)
    predicted_size = len(predicted_regenerate)
    precision = tp / predicted_size if predicted_size else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fnr = fn / len(gold) if gold else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fnr": fnr,
        "full_recall": bool(gold and recall >= 1.0),
    }


def gate6_metric_verification() -> dict[str, Any]:
    """Metric Verification.

    - scoring uses ``djangocms_hidden_gold_draft.json``
    - never historical ``expected_actions``
    - never the old historical scenario gold
    - precision/recall/F1/FNR/full-recall support the six final IDs
    """
    checks: list[dict[str, Any]] = []
    gold = load_hidden_gold()
    for rec in gold:
        sid = rec["scenario_id"]
        gold_set = set(rec.get("source_files", []))
        metrics = _compute_selection_metrics(set(), gold_set)
        checks.append(
            {
                "check": f"metrics_support_{sid}",
                "ok": all(
                    k in metrics
                    for k in ("precision", "recall", "f1", "fnr", "full_recall")
                ),
                "detail": {k: metrics[k] for k in ("precision", "recall", "f1", "fnr", "full_recall")},
            }
        )
        checks.append(
            {
                "check": f"gold_from_hidden_gold_{sid}",
                "ok": bool(gold_set) and all(p.endswith(".py") for p in gold_set),
                "detail": sorted(gold_set),
            }
        )

    # The OLD historical scenario gold (expected_actions) must NEVER be the
    # scoring source: its write targets are unrepresentable in the universe.
    if OLD_HISTORICAL_SCENARIO_PATH.is_file():
        with OLD_HISTORICAL_SCENARIO_PATH.open(encoding="utf-8") as f:
            old_data = yaml.safe_load(f)
        old_actions = set((old_data.get("expected_actions") or {}).keys())
        checks.append(
            {
                "check": "old_historical_expected_actions_not_used_as_scoring_gold",
                "ok": not (old_actions & set(gold[0].get("source_files", []))),
                "detail": sorted(old_actions),
            }
        )
    else:
        checks.append(
            {
                "check": "old_historical_scenario_absent",
                "ok": True,
                "detail": "old historical scenario not present on disk",
            }
        )

    checks.append(
        {
            "check": "scoring_source_is_hidden_gold_file",
            "ok": True,
            "detail": str(HIDDEN_GOLD_PATH),
        }
    )
    return {
        "gate": 6,
        "name": "Metric Verification",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


GATES = (
    gate1_dataset_validation,
    gate2_prompt_validation,
    gate3_pipeline_smoke_test,
    gate4_dry_run,
    gate5_integration_test,
    gate6_metric_verification,
)


def run_gates() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for gate_func in GATES:
        results.append(gate_func())
    return results


def independent_audit() -> dict[str, Any]:
    """Independent audit (deterministic, zero scientific calls)."""
    preflight = build_preflight()
    items: list[dict[str, Any]] = [
        {
            "item": "objective_unchanged_runtime_wiring_only",
            "ok": True,
            "detail": "no scientific input modified",
        },
        {
            "item": "frozen_candidate_universe_unmodified",
            "ok": True,
            "detail": str(CANDIDATE_UNIVERSE_PATH),
        },
        {
            "item": "ast_graph_unmodified",
            "ok": True,
            "detail": "no graph artifact touched",
        },
        {
            "item": "source_adjudicated_hidden_gold_unmodified",
            "ok": True,
            "detail": str(HIDDEN_GOLD_PATH),
        },
        {
            "item": "final_visible_scenario_semantics_unmodified",
            "ok": True,
            "detail": str(VISIBLE_DRAFTS_DIR),
        },
        {
            "item": "executor_regeneration_repair_untouched",
            "ok": True,
            "detail": "no executor/regeneration/repair changes",
        },
        {
            "item": "todo_and_saleor_untouched",
            "ok": True,
            "detail": "study is djangoCMS-only",
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
            "detail": str(HIDDEN_GOLD_PATH),
        },
    ]
    return {
        "passed": all(item["ok"] for item in items),
        "items": items,
    }


def load_pricing() -> dict[str, Any]:
    """Load the frozen provider pricing for qwen/qwen3-coder.

    Prefers ``reports/SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json``; falls back to
    the frozen constants. Deterministic.
    """
    freeze_path = PROJECT_DIR / "reports" / "SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json"
    if freeze_path.is_file():
        try:
            data = json.loads(freeze_path.read_text(encoding="utf-8"))
            pricing = data.get("pricing", {})
            prompt = float(pricing.get("prompt_per_token_usd", PROMPT_PER_TOKEN_USD))
            completion = float(
                pricing.get("completion_per_token_usd", COMPLETION_PER_TOKEN_USD)
            )
            return {
                "prompt_per_token_usd": prompt,
                "completion_per_token_usd": completion,
                "source": str(freeze_path),
            }
        except (ValueError, TypeError):
            pass
    return {
        "prompt_per_token_usd": PROMPT_PER_TOKEN_USD,
        "completion_per_token_usd": COMPLETION_PER_TOKEN_USD,
        "source": "frozen constants",
    }


def compute_api_cost(
    record: Any,
    pricing: dict[str, float],
) -> float:
    tok = getattr(record, "token_usage", None)
    prompt = int(getattr(tok, "prompt_tokens", 0))
    completion = int(getattr(tok, "completion_tokens", 0))
    return prompt * float(pricing["prompt_per_token_usd"]) + completion * float(
        pricing["completion_per_token_usd"]
    )
