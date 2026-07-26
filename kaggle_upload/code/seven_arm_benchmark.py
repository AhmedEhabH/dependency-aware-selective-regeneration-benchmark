#!/usr/bin/env python3
"""Seven-arm benchmark orchestrator.

Runs 7 impact-analysis strategies across 24 scenarios (3 repos x 8 scenarios).
Supports dry-run (mock backend) and three execution profiles:

  smoke (orchestration smoke):
    1 scenario, all 7 strategies, 1 repetition.  Non-publication evidence.
    Default profile for Kaggle orchestration validation.

  pilot (protocol pilot):
    3 repos x 4 scenarios x 2 strategies (agent, selective) x 2 repetitions.
    Descriptive only; not for publication.

  research (protocol research):
    All 24 scenarios.  Impact-only for all 7 strategies.
    Full evolution for agent, selective, compiled_ai, delta_mcp.
    3 repetitions per stochastic cell.

Usage:
    # Dry-run (no API calls, deterministic mock responses):
    python seven_arm_benchmark.py --dry-run

    # Real run on Kaggle (model path discovered automatically):
    python seven_arm_benchmark.py --output-dir /kaggle/working/runs

    # Real run with explicit paths:
    python seven_arm_benchmark.py \
        --data-dir /kaggle/input/dependency-aware-selective-regeneration-data \
        --model-path /kaggle/input/models/qwen-lm/qwen2.5-coder/transformers/7b-instruct/1 \
        --output-dir /kaggle/working/runs
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from benchmark.core.models import Scenario

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("benchmark")

BENCHMARK_ROOT = Path(__file__).resolve().parent
SCENARIOS_DIR = BENCHMARK_ROOT / "benchmark_data" / "scenarios"
OUTPUT_DIR = BENCHMARK_ROOT / "runs"
DEFAULT_DATA_DIR = BENCHMARK_ROOT / "benchmark_data"

STRATEGY_NAMES = [
    "monolithic",
    "agent",
    "selective",
    "compiled_ai",
    "delta_mcp",
    "incr_rtl",
    "code_plan",
    "iterative_repository_agent",
]

# Frozen protocol design: which strategies are expected to use an LLM backend
# or a dependency graph.
STRATEGY_CAPABILITIES_DESIGN: dict[str, dict[str, bool]] = {
    "monolithic": {"llm": True, "graph": False},
    "agent": {"llm": True, "graph": False},
    "selective": {"llm": True, "graph": True},
    "compiled_ai": {"llm": False, "graph": True},
    "delta_mcp": {"llm": True, "graph": False},
    "incr_rtl": {"llm": False, "graph": False},
    "code_plan": {"llm": True, "graph": True},
    "iterative_repository_agent": {"llm": True, "graph": False},
}


def describe_capabilities(strategy_name: str) -> dict[str, bool]:
    """Report actual strategy capabilities at runtime.

    Returns:
        uses_llm_by_design:  protocol-level expectation (from frozen design)
        llm_backend_attached: strategy was constructed with an LLM backend
        uses_dependency_graph_by_design: strategy expects a graph per protocol
        dependency_graph_attached: strategy was constructed with a graph
    """
    design = STRATEGY_CAPABILITIES_DESIGN.get(strategy_name, {})
    from benchmark.strategies import (
        FullContextStrategy,
        HybridSelectiveStrategy,
        IterativeRepositoryAgentStrategy,
        RepositoryAgentStrategy,
        StaticOnlyStrategy,
    )
    graph_classes: set[type] = {HybridSelectiveStrategy, FullContextStrategy, StaticOnlyStrategy}
    llm_classes: set[type] = {RepositoryAgentStrategy, IterativeRepositoryAgentStrategy}
    cls_map = {
        "monolithic": None,
        "agent": RepositoryAgentStrategy,
        "selective": HybridSelectiveStrategy,
        "compiled_ai": StaticOnlyStrategy,
        "delta_mcp": None,
        "incr_rtl": None,
        "code_plan": FullContextStrategy,
        "iterative_repository_agent": IterativeRepositoryAgentStrategy,
    }
    cls = cls_map.get(strategy_name)
    return {
        "uses_llm_by_design": design.get("llm", False),
        "llm_backend_attached": (cls in llm_classes) if cls else False,
        "uses_dependency_graph_by_design": design.get("graph", False),
        "dependency_graph_attached": (cls in graph_classes) if cls else False,
    }

def _to_run_record_data(
    record_dict: dict[str, Any],
    *,
    run_id: str,
    profile: str,
    repository_id: str,
    scenario_id: str,
    strategy_id: str,
    repetition: int,
    model_identity: str,
    dry_run: bool,
    protocol_version: str,
    source_commit: str,
    config_hash: str,
    started_at: str,
    ended_at: str,
    hw_id: str,
    sw_id: str,
    max_attempts: int,
    failure_details: list[dict[str, Any]] | None = None,
    failure_classification: str = "",
) -> object:
    """Convert record_dict plus metadata into RunRecordData.

    This is the single entry-point conversion for seven_arm_benchmark.py.
    All end-to-end scoped metrics are forwarded with backward-compatible defaults.
    """
    from benchmark.checkpoint.persistence import RunRecordData

    tok = record_dict.get("token_usage", {"prompt": 0, "completion": 0, "total": 0})
    status = record_dict.get("status", "")
    fdetails = failure_details or record_dict.get("failures", [])

    return RunRecordData(
        run_id=run_id,
        profile=profile,
        repository_id=repository_id,
        scenario_id=scenario_id,
        strategy_id=strategy_id,
        repetition=repetition,
        seed=42,
        status=status,
        failure_details=fdetails,
        token_usage=tok,
        duration_seconds=record_dict.get("duration_seconds", 0.0),
        model_metadata={"model": model_identity, "dry_run": str(dry_run)},
        protocol_version=protocol_version,
        source_commit=source_commit,
        config_hash=config_hash,
        timestamp=started_at,
        started_at=started_at,
        ended_at=ended_at,
        model_calls=1 if tok.get("total", 0) > 0 else 0,
        repair_attempts=max(0, max_attempts - 1) if status != "succeeded" else 0,
        hardware_identity=hw_id or "dry-run:mock" if dry_run else hw_id,
        software_environment_identity=sw_id or "dry-run:mock" if dry_run else sw_id,
        failure_classification=failure_classification,
        # End-to-end workflow metrics with backward-compatible defaults
        selection_prompt_tokens=record_dict.get("selection_prompt_tokens", 0),
        selection_completion_tokens=record_dict.get("selection_completion_tokens", 0),
        selection_total_tokens=record_dict.get("selection_total_tokens", 0),
        selection_model_calls=record_dict.get("selection_model_calls", 0),
        selection_duration_seconds=record_dict.get("selection_duration_seconds", 0.0),
        regeneration_prompt_tokens=record_dict.get("regeneration_prompt_tokens", 0),
        regeneration_completion_tokens=record_dict.get("regeneration_completion_tokens", 0),
        regeneration_total_tokens=record_dict.get("regeneration_total_tokens", 0),
        regeneration_model_calls=record_dict.get("regeneration_model_calls", 0),
        regeneration_duration_seconds=record_dict.get("regeneration_duration_seconds", 0.0),
        functional_validation_duration_seconds=record_dict.get("functional_validation_duration_seconds", 0.0),
        functional_validation_passed=record_dict.get("functional_validation_passed"),
        total_workflow_tokens=record_dict.get("total_workflow_tokens", 0),
        total_workflow_model_calls=record_dict.get("total_workflow_model_calls", 0),
        total_workflow_duration_seconds=record_dict.get("total_workflow_duration_seconds", 0.0),
        selected_artifact_count=record_dict.get("selected_artifact_count", 0),
        regenerated_artifact_count=record_dict.get("regenerated_artifact_count", 0),
        preserved_artifact_count=record_dict.get("preserved_artifact_count", 0),
        unresolved_human_review_count=record_dict.get("unresolved_human_review_count", 0),
    )


REPO_IDS = ["todo", "djangocms", "saleor"]


@dataclass
class ExecutionProfile:
    name: str
    label: str
    scenario_count: int
    strategies: list[str]
    repetitions: int
    is_publication: bool
    description: str = ""
    repository_names: list[str] | None = None
    blast_radii: list[str] | None = None
    scenario_ids: list[str] | None = None
    timeout_seconds: int = 0


PROFILES: dict[str, ExecutionProfile] = {
    "smoke": ExecutionProfile(
        name="smoke",
        label="orchestration-smoke",
        scenario_count=1,
        strategies=list(STRATEGY_NAMES),
        repetitions=1,
        is_publication=False,
        description="1 scenario, 7 strategies, 1 rep, non-publication",
    ),
    "pilot": ExecutionProfile(
        name="pilot",
        label="protocol-pilot",
        scenario_count=12,
        strategies=["agent", "selective"],
        repetitions=2,
        is_publication=False,
        description="3 repos x 4 scenarios x 2 strategies x 2 reps, descriptive only",
        repository_names=["todo", "djangocms", "saleor"],
        blast_radii=["localized", "moderate"],
    ),
    "research": ExecutionProfile(
        name="research",
        label="protocol-research",
        scenario_count=24,
        strategies=["agent", "selective", "compiled_ai", "delta_mcp"],
        repetitions=3,
        is_publication=True,
        description="24 scenarios, full-evolution strategies, 3 reps, publication",
        repository_names=["todo", "djangocms", "saleor"],
        blast_radii=["localized", "moderate", "cross_cutting"],
    ),
    "scientific-smoke-v1": ExecutionProfile(
        name="scientific-smoke-v1",
        label="scientific-smoke-v1",
        scenario_count=1,
        strategies=["monolithic", "selective", "iterative_repository_agent"],
        repetitions=1,
        is_publication=False,
        description="1 repo (todo) x 1 scenario (todo-loc-001) x 3 arms x 1 run, non-publication scientific smoke",
        repository_names=["todo"],
        blast_radii=["localized"],
        scenario_ids=["todo-loc-001"],
        timeout_seconds=180,
    ),
}

# ---------------------------------------------------------------------------
# ScenarioProvider wrapper
# ---------------------------------------------------------------------------

class ScenarioProvider:
    """Thin wrapper around ScenarioLoader that satisfies the ScenarioProvider protocol."""

    def __init__(self, scenarios_dir: Path) -> None:
        from benchmark.scenarios.loader import ScenarioLoader

        self._loader = ScenarioLoader(scenarios_dir)
        self._all: list[Scenario] | None = None

    def _ensure_loaded(self) -> None:
        if self._all is None:
            self._all = self._loader.load_all()

    def get_scenario(self, scenario_id: str):  # type: ignore[no-untyped-def]
        self._ensure_loaded()
        for s in self._all:  # type: ignore[union-attr]
            if s.scenario_id == scenario_id:
                return s
        raise KeyError(f"Scenario not found: {scenario_id}")

    def list_scenarios(self, repo_id: str | None = None):  # type: ignore[no-untyped-def]
        self._ensure_loaded()
        if repo_id:
            return [s for s in self._all if s.repository == repo_id]  # type: ignore[union-attr]
        return list(self._all or [])


# ---------------------------------------------------------------------------
# Strategy factory
# ---------------------------------------------------------------------------

def make_strategy(name: str, backend=None, graph=None):  # type: ignore[no-untyped-def]
    from benchmark.strategies import (
        FullContextStrategy,
        HybridSelectiveStrategy,
        IterativeRepositoryAgentStrategy,
        MonolithicRegenerationStrategy,
        RepositoryAgentStrategy,
        SemanticOnlyStrategy,
        StaticOnlyStrategy,
        TraceabilityOnlyStrategy,
    )

    if name == "agent":
        if backend is None:
            raise ValueError("RepositoryAgentStrategy requires a backend")
        return RepositoryAgentStrategy(backend=backend)

    if name == "iterative_repository_agent":
        if backend is None:
            raise ValueError("IterativeRepositoryAgentStrategy requires a backend")
        return IterativeRepositoryAgentStrategy(backend=backend)

    strategies = {
        "monolithic": (MonolithicRegenerationStrategy, {}),
        "selective": (HybridSelectiveStrategy, {"graph": graph}),
        "compiled_ai": (StaticOnlyStrategy, {"graph": graph}),
        "delta_mcp": (SemanticOnlyStrategy, {}),
        "incr_rtl": (TraceabilityOnlyStrategy, {}),
        "code_plan": (FullContextStrategy, {"graph": graph}),
    }
    entry = strategies.get(name)
    if entry is None:
        raise ValueError(f"Unknown strategy: {name}")
    cls, kwargs = entry
    return cls(**{k: v for k, v in kwargs.items() if v is not None})


# ---------------------------------------------------------------------------
# Backend factory
# ---------------------------------------------------------------------------

def make_backend(  # type: ignore[no-untyped-def]
    dry_run: bool,
    model_path: str | None = None,
    backend_name: str | None = None,
    openrouter_model: str = "nvidia/nemotron-3-super-120b-a12b:free",
    openrouter_timeout: float = 120.0,
):
    if dry_run or backend_name == "mock":
        from benchmark.llm.mock_backend import MockLLMBackend
        return MockLLMBackend(response_text="dry-run-response")
    if backend_name == "openrouter":
        from benchmark.llm.openrouter_backend import OpenRouterBackend
        return OpenRouterBackend(
            model=openrouter_model,
            timeout_seconds=openrouter_timeout,
        )
    from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend
    kwargs: dict[str, str] = {}
    if model_path:
        kwargs["model_path"] = model_path
    return KaggleQwenBackend(**kwargs)


# ---------------------------------------------------------------------------
# Workspace / IsolationContext
# ---------------------------------------------------------------------------

def make_isolation(workspace_dir: Path):  # type: ignore[no-untyped-def]
    from benchmark.execution.isolation import IsolationContext
    from benchmark.repositories.workspace import WorkspacePath

    ws = WorkspacePath(root=str(workspace_dir))
    workspace_dir.mkdir(parents=True, exist_ok=True)
    (workspace_dir / "snapshots").mkdir(exist_ok=True)
    (workspace_dir / "runs").mkdir(exist_ok=True)
    (workspace_dir / "tmp").mkdir(exist_ok=True)
    return IsolationContext(workspace=ws)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def build_dependency_graph(data_dir: Path, scenarios: list) -> object:  # type: ignore[no-untyped-def]
    """Build a DependencyGraph from the repo profile for the given scenarios.

    Priority:
      1. Profile-based graph with real dependency edges.
      2. Profile-based edgeless graph (nodes from architecture data only).
      3. Neutral repository-derived edgeless fallback (no Ground Truth).

    Never creates graph nodes from scenario.expected_affected_artifacts.
    """
    from benchmark.core.models import DependencyGraph
    from benchmark.graph.builder import ProfileGraphBuilder

    repo_id = None
    for s in scenarios:
        if repo_id is None:
            repo_id = s.repository

    if not repo_id:
        return None

    builder = ProfileGraphBuilder()

    # 1. Profile-based graph with real dependency edges
    profile_dir = data_dir / "repository_profiles"
    if profile_dir.is_dir():
        from benchmark.repositories.loader import RepositoryLoader
        try:
            loader = RepositoryLoader(data_dir)
            collection = loader.load_manifest()
            profile = collection.get_profile(repo_id)
            if profile is not None:
                graph = builder.build_from_profile(profile)
                if graph is not None:
                    logger.info(
                        "Profile graph for repo=%s  nodes=%d  edges=%d",
                        repo_id, len(graph.nodes), len(graph.edges),
                    )
                    return graph
                # 2. Profile exists but no edges — try nodes-only from architecture
                arch: dict[str, Any] = {}
                arch_attr = getattr(profile, "architecture", None)
                if isinstance(arch_attr, dict):
                    arch = arch_attr
                if arch:
                    node_graph = builder.build_nodes_from_architecture(arch)
                    if node_graph is not None:
                        logger.info(
                            "Architecture node graph for repo=%s  nodes=%d  edges=0",
                            repo_id, len(node_graph.nodes),
                        )
                        return node_graph
            logger.info(
                "No profile graph for '%s' — returning neutral edgeless fallback", repo_id
            )
        except Exception:
            logger.warning(
                "Failed to load profile graph for '%s' — returning neutral fallback",
                repo_id, exc_info=True,
            )
    else:
        logger.info(
            "No repository_profiles dir — returning neutral edgeless fallback",
        )

    # 3. Neutral repository-derived edgeless fallback.
    #    No Ground Truth — no fabricated edges — intentionally conservative.
    neutral = DependencyGraph(
        nodes=(),
        edges=(),
        metadata={"source": "neutral_edgeless_fallback", "repo_id": repo_id},
    )
    logger.info(
        "Neutral edgeless fallback graph for repo=%s  nodes=0  edges=0",
        repo_id,
    )
    return neutral


def run_arm(
    strategy_name: str,
    scenario_provider: ScenarioProvider,
    isolation_workspace: Path,
    dry_run: bool,
    profile: ExecutionProfile,
    model_path: str | None = None,
    protocol_version: str = "1.0",
    max_attempts: int = 3,
    timeout_seconds: int = 0,
    dep_graph=None,
    backend_name: str | None = None,
    openrouter_model: str = "nvidia/nemotron-3-super-120b-a12b:free",
    openrouter_timeout: float = 120.0,
) -> object:
    """Run a single strategy arm and return a PipelineResult."""
    from benchmark.execution.pipeline import BenchmarkPipeline, PipelineConfig

    scenario_count = profile.scenario_count
    all_scenarios = scenario_provider.list_scenarios()
    selected = all_scenarios[:scenario_count]
    scenario_ids = [s.scenario_id for s in selected]

    design = STRATEGY_CAPABILITIES_DESIGN.get(strategy_name, {})
    needs_llm = design.get("llm", False)

    backend = make_backend(
        dry_run, model_path=model_path,
        backend_name=backend_name,
        openrouter_model=openrouter_model,
        openrouter_timeout=openrouter_timeout,
    ) if needs_llm else None
    strategy = make_strategy(strategy_name, backend=backend, graph=dep_graph)

    isolation = make_isolation(isolation_workspace)

    config = PipelineConfig(
        protocol_version=protocol_version,
        timeout_seconds=timeout_seconds,
        max_attempts_per_run=max_attempts,
        dry_run=dry_run,
    )

    pipeline = BenchmarkPipeline(
        strategy=strategy,
        backend=backend,
        scenario_provider=scenario_provider,
        isolation=isolation,
        config=config,
        strategy_name=strategy_name,
    )

    logger.info(
        "Running arm=%s  profile=%s  scenarios=%d  label=%s  graph=%s",
        strategy_name, profile.name, len(scenario_ids), profile.label,
        "yes" if dep_graph else "no",
    )
    t0 = time.monotonic()
    result = pipeline.run_all(scenario_ids=scenario_ids)
    elapsed = time.monotonic() - t0

    logger.info(
        "Arm %s finished: success=%d failure=%d timeout=%d elapsed=%.1fs",
        strategy_name,
        result.success_count,
        result.failure_count,
        result.timeout_count,
        elapsed,
    )
    return result


# ---------------------------------------------------------------------------
# Aggregate results
# ---------------------------------------------------------------------------

def aggregate_results(results: dict, output_dir: Path, is_publication: bool = False):  # type: ignore[no-untyped-def]
    """Serialize per-arm results to JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary: dict = {}
    for arm_name, result in results.items():
        records = []
        for r in result.records:
            record_dict: dict = {
                "run_id": r.identity.run_id,
                "scenario_id": r.identity.scenario_id,
                "strategy_name": r.identity.strategy_name,
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                "duration_seconds": r.duration_seconds,
                "token_usage": {
                    "prompt_tokens": r.token_usage.prompt_tokens,
                    "completion_tokens": r.token_usage.completion_tokens,
                    "total_tokens": r.token_usage.total_tokens,
                } if r.token_usage else None,
            }
            if r.failures:
                record_dict["failures"] = [
                    {
                        "kind": f.failure_kind.value if hasattr(f.failure_kind, "value") else str(f.failure_kind),
                        "message": f.message,
                        "details": f.details,
                        "stage": f.stage,
                    }
                    for f in r.failures
                ]
            records.append(record_dict)
        summary[arm_name] = {
            "success_count": result.success_count,
            "failure_count": result.failure_count,
            "timeout_count": result.timeout_count,
            "total_duration": result.total_duration,
            "record_count": len(records),
            "records": records,
        }

    summary["_meta"] = {
        "publication_evidence": is_publication,
        "label": "protocol-research" if is_publication else "orchestration-smoke",
    }
    summary_path = output_dir / "benchmark_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("Summary written to %s", summary_path)
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seven-arm dependency-aware selective regeneration benchmark",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Use mock backend (no real LLM calls)",
    )
    parser.add_argument(
        "--backend",
        choices=["mock", "kaggle-qwen", "openrouter"],
        default=None,
        help=(
            "LLM backend: mock (dry-run only), kaggle-qwen (default for non-dry-run), "
            "openrouter (API-based). Requires OPENROUTER_API_KEY env var."
        ),
    )
    parser.add_argument(
        "--openrouter-model",
        type=str,
        default="nvidia/nemotron-3-super-120b-a12b:free",
        help="Model identifier for OpenRouter API",
    )
    parser.add_argument(
        "--openrouter-timeout",
        type=float,
        default=120.0,
        help="Request timeout in seconds for OpenRouter API calls",
    )
    parser.add_argument(
        "--profile",
        choices=list(PROFILES.keys()),
        default="smoke",
        help=(
            "Execution profile: smoke (orchestration, 1 scenario, 7 strategies, non-publication), "
            "pilot (protocol, 12 scenarios, 2 strategies, 2 reps, descriptive), "
            "research (protocol, 24 scenarios, 4 full-evolution strategies, 3 reps, publication)"
        ),
    )
    parser.add_argument(
        "--strategy",
        choices=STRATEGY_NAMES,
        default=None,
        help="Run a single strategy instead of the profile's default set",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="Directory for output artifacts",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Maximum repair-loop attempts per scenario",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=0,
        help="Per-run timeout in seconds (0 = no limit)",
    )
    parser.add_argument(
        "--protocol-version",
        type=str,
        default="1.0",
        help="Research protocol version string",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Directory containing scenarios/, manifests/, repository_profiles/",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Explicit path to the Qwen model directory on Kaggle",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="Resume from checkpoint in the output directory",
    )
    parser.add_argument(
        "--resume-from",
        type=str,
        default=None,
        help="Path to previous Kaggle results Dataset to resume from",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=0,
        help="Maximum number of runs to execute in this session (0 = no limit)",
    )
    parser.add_argument(
        "--hf-sync",
        action="store_true",
        default=False,
        help="Enable automatic Hugging Face result synchronization after every run",
    )
    parser.add_argument(
        "--hf-repo-id",
        type=str,
        default=None,
        help="Hugging Face Dataset repository ID (e.g. NabilDo/selective-regeneration-experiment-results)",
    )
    parser.add_argument(
        "--resume-from-hf",
        action="store_true",
        default=False,
        help="Resume benchmark from a previous experiment on Hugging Face",
    )
    parser.add_argument(
        "--auto-resume-hf",
        action="store_true",
        default=False,
        help=(
            "Automatically discover and resume from a compatible remote experiment. "
            "Searches under the canonical prefix for the requested profile and "
            "validates compatibility. Combined with --hf-sync."
        ),
    )
    parser.add_argument(
        "--new-experiment",
        action="store_true",
        default=False,
        help="Intentionally bypass auto-resume and create a new experiment",
    )
    parser.add_argument(
        "--experiment-id",
        type=str,
        default=None,
        help="Unique experiment identifier for HF remote layout",
    )
    parser.add_argument(
        "--source-commit",
        type=str,
        default=None,
        help="Explicit Git commit SHA. Overrides auto-detection.",
    )
    parser.add_argument(
        "--source-tag",
        type=str,
        default=None,
        help="Explicit Git tag or release name for this source version.",
    )
    parser.add_argument(
        "--deployed-build-id",
        type=str,
        default=None,
        help="Immutable build/bundle ID for the deployed code. Overrides auto-detection.",
    )
    args = parser.parse_args()
    _validate_cli_args(args)
    return args


def _validate_cli_args(args: argparse.Namespace) -> None:
    errors: list[str] = []

    if args.data_dir:
        data_dir = Path(args.data_dir)
        if not data_dir.is_dir():
            errors.append(f"--data-dir does not exist: {data_dir}")
        else:
            for subdir in ("scenarios", "manifests", "repository_profiles"):
                if not (data_dir / subdir).is_dir():
                    errors.append(f"--data-dir missing required subdirectory '{subdir}/' in {data_dir}")

    if args.model_path:
        model_dir = Path(args.model_path)
        if not model_dir.is_dir():
            errors.append(f"--model-path does not exist: {model_dir}")
        else:
            if not (model_dir / "config.json").is_file():
                errors.append(f"--model-path missing config.json in {model_dir}")
            weight_files = (
                list(model_dir.rglob("*.safetensors"))
                + list(model_dir.rglob("*.bin"))
                + list(model_dir.rglob("*.pt"))
            )
            if not weight_files:
                errors.append(f"--model-path no weight files (.safetensors/.bin/.pt) found in {model_dir}")

    if args.backend == "openrouter":
        if not args.openrouter_model or not args.openrouter_model.strip():
            errors.append("--openrouter-model must be a non-empty string")
        if args.openrouter_timeout <= 0:
            errors.append("--openrouter-timeout must be positive")
        if not os.environ.get("OPENROUTER_API_KEY", "").strip():
            errors.append(
                "OPENROUTER_API_KEY environment variable is required for --backend openrouter"
            )
    elif not args.dry_run and not args.backend:
        if not args.model_path:
            errors.append("--model-path is required when not using --dry-run")

    if errors:
        for err in errors:
            logger.error("Validation error: %s", err)
        sys.exit(1)


EXPECTED_SCENARIO_TOTAL = 24
EXPECTED_REPO_SCENARIOS = 8


def _validate_scenario_count(
    scenarios: list[Scenario],
    profile: ExecutionProfile,
) -> None:
    actual = len(scenarios)

    if profile.name == "research":
        if actual < EXPECTED_SCENARIO_TOTAL:
            logger.error(
                "Research profile requires %d scenarios, loaded %d. "
                "Check scenario YAML files for errors.",
                EXPECTED_SCENARIO_TOTAL, actual,
            )
            sys.exit(1)
        repo_counts = Counter(s.repository for s in scenarios)
        for repo, count in repo_counts.items():
            if count != EXPECTED_REPO_SCENARIOS:
                logger.error(
                    "Research profile: repository '%s' has %d scenarios, expected %d. "
                    "Distribution: %s",
                    repo, count, EXPECTED_REPO_SCENARIOS, dict(repo_counts),
                )
                sys.exit(1)
    elif profile.name == "pilot":
        if actual < 12:
            logger.error(
                "Pilot profile requires at least 12 scenarios, loaded %d. "
                "Select 4 per repo from the full 24.",
                actual,
            )
            sys.exit(1)
    elif profile.name == "smoke" and actual < EXPECTED_SCENARIO_TOTAL:
        logger.warning(
            "Smoke profile: only %d / %d scenarios loaded. "
            "Continuing with 1 scenario, but data may be incomplete.",
            actual, EXPECTED_SCENARIO_TOTAL,
        )


def _get_source_commit(explicit_commit: str | None = None, explicit_tag: str | None = None) -> str:
    if explicit_commit:
        return explicit_commit
    if explicit_tag:
        return explicit_tag
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown-source"


def _get_deployed_build_id(
    explicit_build_id: str | None = None,
    source_commit: str = "",
) -> str:
    """Return the immutable deployed-build identity.

    Priority: explicit --deployed-build-id > source_commit (actual git SHA) > unknown.
    This is NOT the declared source tag — it is the code that is actually running.
    """
    if explicit_build_id:
        return explicit_build_id
    return source_commit


def _get_model_identity(
    model_path: str | None = None,
    backend_name: str | None = None,
    openrouter_model: str = "",
) -> str:
    if backend_name == "openrouter" and openrouter_model:
        return f"openrouter:{openrouter_model}"
    if model_path:
        p = Path(model_path)
        return f"qwen:{p.name}"
    return "dry-run:mock"


def _build_execution_plan(
    profile: ExecutionProfile,
    scenario_provider: ScenarioProvider,
    strategy_names: list[str],
    skip_run_ids: set[str] | None = None,
    config_hash: str = "",
    protocol_version: str = "1.0",
    scenarios: list | None = None,
) -> list[dict[str, Any]]:
    skip_run_ids = skip_run_ids or set()
    if scenarios is not None:
        selected = scenarios
    else:
        all_scenarios = scenario_provider.list_scenarios()
        selected = all_scenarios[:profile.scenario_count]
    plan: list[dict[str, Any]] = []

    for scenario in selected:
        for strategy_name in strategy_names:
            for rep in range(1, profile.repetitions + 1):
                run_id = _make_run_id(scenario.scenario_id, strategy_name, rep, config_hash, protocol_version)
                if run_id in skip_run_ids:
                    logger.info("Skipping completed run: %s", run_id)
                    continue
                plan.append({
                    "run_id": run_id,
                    "scenario_id": scenario.scenario_id,
                    "repository_id": scenario.repository,
                    "strategy_name": strategy_name,
                    "repetition": rep,
                })
    return plan


def _make_run_id(scenario_id: str, strategy_name: str, rep: int, config_hash: str = "", protocol_version: str = "1.0") -> str:
    payload = json.dumps({
        "scenario_id": scenario_id,
        "strategy_name": strategy_name,
        "repetition": rep,
        "protocol_version": protocol_version,
        "config_hash": config_hash,
    }, sort_keys=True)
    suffix = hashlib.sha256(payload.encode()).hexdigest()[:8]
    return f"{scenario_id}_{strategy_name}_rep{rep}_{suffix}"


def _run_single_scenario_strategy(
    scenario_id: str,
    strategy_name: str,
    scenario_provider: ScenarioProvider,
    dry_run: bool,
    profile: ExecutionProfile,
    model_path: str | None,
    protocol_version: str,
    max_attempts: int,
    timeout_seconds: int,
    dep_graph: object,
    workspace_dir: Path,
    backend_name: str | None = None,
    openrouter_model: str = "nvidia/nemotron-3-super-120b-a12b:free",
    openrouter_timeout: float = 120.0,
) -> tuple[dict[str, Any], int]:
    from benchmark.execution.pipeline import BenchmarkPipeline, PipelineConfig, PipelineResult

    scenario = scenario_provider.get_scenario(scenario_id)

    design = STRATEGY_CAPABILITIES_DESIGN.get(strategy_name, {})
    needs_llm = design.get("llm", False)

    backend = make_backend(
        dry_run=dry_run,
        model_path=model_path,
        backend_name=backend_name,
        openrouter_model=openrouter_model,
        openrouter_timeout=openrouter_timeout,
    ) if needs_llm else None

    strategy = make_strategy(strategy_name, backend=backend, graph=dep_graph)

    isolation = make_isolation(workspace_dir)

    config = PipelineConfig(
        protocol_version=protocol_version,
        timeout_seconds=timeout_seconds,
        max_attempts_per_run=max_attempts,
        dry_run=dry_run,
    )

    pipeline = BenchmarkPipeline(
        strategy=strategy,
        backend=backend,
        scenario_provider=scenario_provider,
        isolation=isolation,
        config=config,
        strategy_name=strategy_name,
    )

    t0 = time.monotonic()
    record = pipeline.run_scenario_by_id(scenario_id)
    elapsed = time.monotonic() - t0

    status = record.status.value if hasattr(record.status, "value") else str(record.status)
    success = 1 if status == "succeeded" else 0
    failure = 1 if status in ("failed",) else 0
    timeout = 1 if status == "timed_out" else 0

    record_dict: dict[str, Any] = {
        "run_id": record.identity.run_id,
        "scenario_id": record.identity.scenario_id,
        "strategy_name": record.identity.strategy_name,
        "status": status,
        "duration_seconds": record.duration_seconds,
        "token_usage": {
            "prompt": record.token_usage.prompt_tokens,
            "completion": record.token_usage.completion_tokens,
            "total": record.token_usage.total_tokens,
        } if record.token_usage else {"prompt": 0, "completion": 0, "total": 0},
        # End-to-end workflow metrics (SU-0010A)
        "selection_prompt_tokens": record.selection_prompt_tokens,
        "selection_completion_tokens": record.selection_completion_tokens,
        "selection_total_tokens": record.selection_total_tokens,
        "selection_model_calls": record.selection_model_calls,
        "selection_duration_seconds": record.selection_duration_seconds,
        "regeneration_prompt_tokens": record.regeneration_prompt_tokens,
        "regeneration_completion_tokens": record.regeneration_completion_tokens,
        "regeneration_total_tokens": record.regeneration_total_tokens,
        "regeneration_model_calls": record.regeneration_model_calls,
        "regeneration_duration_seconds": record.regeneration_duration_seconds,
        "functional_validation_duration_seconds": record.functional_validation_duration_seconds,
        "functional_validation_passed": record.functional_validation_passed,
        "total_workflow_tokens": record.total_workflow_tokens,
        "total_workflow_model_calls": record.total_workflow_model_calls,
        "total_workflow_duration_seconds": record.total_workflow_duration_seconds,
        "selected_artifact_count": record.selected_artifact_count,
        "regenerated_artifact_count": record.regenerated_artifact_count,
        "preserved_artifact_count": record.preserved_artifact_count,
        "unresolved_human_review_count": record.unresolved_human_review_count,
    }
    if record.failures:
        record_dict["failures"] = [
            {
                "kind": f.failure_kind.value if hasattr(f.failure_kind, "value") else str(f.failure_kind),
                "message": f.message,
                "details": f.details,
                "stage": f.stage,
            }
            for f in record.failures
        ]
    return record_dict, int(success or failure or timeout)


def _compute_config_hash(args: argparse.Namespace) -> str:
    config_obj = {
        "dry_run": args.dry_run,
        "profile": args.profile,
        "strategy": args.strategy,
        "max_attempts": args.max_attempts,
        "timeout": args.timeout,
        "protocol_version": args.protocol_version,
    }
    raw = json.dumps(config_obj, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _build_smoke_progress_summary(
    all_strategy_names: list[str],
    results_agg: dict[str, dict[str, Any]],
    planned_run_ids: list[str],
    checkpoint_completed: list[str],
    checkpoint_failed: list[str],
    pending_run_ids: list[str],
) -> list[dict[str, Any]]:
    """Build a one-row-per-strategy smoke progress summary.

    Each row includes:
      strategy_name, not_yet_run, environment_failed, succeeded, failed, timed_out,
      total_planned_for_strategy, total_completed_for_strategy
    """
    summary_rows: list[dict[str, Any]] = []
    for sname in all_strategy_names:
        plan_ids = [rid for rid in planned_run_ids if f"_{sname}_" in rid]
        completed_ids = [rid for rid in checkpoint_completed if f"_{sname}_" in rid]
        failed_ids = [rid for rid in checkpoint_failed if f"_{sname}_" in rid]
        pending_ids = [rid for rid in pending_run_ids if f"_{sname}_" in rid]

        agg = results_agg.get(sname, {})
        records = agg.get("records", [])
        succeeded = sum(1 for r in records if r.get("status") == "succeeded")
        failed = sum(1 for r in records if r.get("status") == "failed")
        timed_out = sum(1 for r in records if r.get("status") == "timed_out")
        env_failed = sum(
            1 for r in records
            if r.get("failure_classification") == "environment_preflight"
        )

        row = {
            "strategy_name": sname,
            "total_planned": len(plan_ids),
            "total_completed": len(completed_ids),
            "succeeded": succeeded,
            "failed": failed,
            "timed_out": timed_out,
            "environment_failed": env_failed,
            "not_yet_run": len(pending_ids),
        }
        summary_rows.append(row)
    return summary_rows


def _preflight_check(
    dry_run: bool,
    needs_llm: bool,
    strategy_name: str,
    backend_name: str | None = None,
) -> tuple[bool, str, str, str]:
    """Run a preflight if the strategy needs an LLM.

    For OpenRouter: local validation only (no network call).
    For Kaggle Qwen: GPU compatibility check.
    For dry_run or non-LLM strategies, always returns (True, "", "", "").

    Returns (ok, hardware_identity, software_identity, rejection_reason).
    """
    if dry_run or not needs_llm:
        return True, "", "", ""

    if backend_name == "openrouter":
        from benchmark.checkpoint.persistence import (
            detect_hardware_identity,
            detect_software_environment_identity,
        )
        hw = detect_hardware_identity()
        sw = detect_software_environment_identity()
        return True, hw, sw, ""

    try:
        from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend
        result = KaggleQwenBackend.preflight()
        return (
            result.compatible,
            result.hardware_identity,
            result.software_identity,
            result.rejection_reason,
        )
    except Exception as exc:
        return False, "unknown", "unknown", f"Preflight exception: {exc}"


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    workspace_dir = output_dir / "workspace"

    data_dir = Path(args.data_dir) if args.data_dir else DEFAULT_DATA_DIR
    scenarios_dir = data_dir / "scenarios"

    profile = PROFILES[args.profile]

    # Use profile timeout if CLI arg not explicitly set (default 0 = no limit)
    if args.timeout == 0 and profile.timeout_seconds > 0:
        args.timeout = profile.timeout_seconds

    source_commit = _get_source_commit(
        explicit_commit=args.source_commit,
        explicit_tag=args.source_tag,
    )
    deployed_build_id = _get_deployed_build_id(
        explicit_build_id=args.deployed_build_id,
        source_commit=source_commit,
    )
    config_hash = _compute_config_hash(args)
    resolved_backend = args.backend or ("kaggle-qwen" if not args.dry_run else "mock")
    model_identity = _get_model_identity(
        model_path=args.model_path,
        backend_name=resolved_backend,
        openrouter_model=args.openrouter_model,
    )

    logger.info(
        "Benchmark config: dry_run=%s  profile=%s  label=%s  output=%s  data_dir=%s  "
        "commit=%s  deployed_build=%s  config_hash=%s  source_tag=%s  backend=%s",
        args.dry_run, profile.name, profile.label, output_dir, data_dir,
        source_commit, deployed_build_id, config_hash,
        args.source_tag or "", resolved_backend,
    )

    # ---- Checkpoint / Resume setup -----------------------------------------
    from benchmark.checkpoint.checkpoint import CheckpointManager, CheckpointData, ProgressManager, ProgressData
    from benchmark.checkpoint.persistence import RunRecordStore
    from benchmark.checkpoint.resume import ResumeManager, ResumeValidationError
    from benchmark.checkpoint.package import ResultsPackager

    resume_mgr = ResumeManager(
        runs_dir=output_dir,
        protocol_version=args.protocol_version,
        config_hash=config_hash,
        model_identity=model_identity,
        source_commit=source_commit,
        deployed_build_id=deployed_build_id,
    )
    checkpoint_mgr = CheckpointManager(output_dir)
    progress_mgr = ProgressManager(output_dir)
    record_store = RunRecordStore(output_dir)
    packager = ResultsPackager(output_dir)

    # ---- HF Sync setup ----------------------------------------------------
    hf_uploader: Any = None
    hf_experiment_id = args.experiment_id or time.strftime("exp-%Y%m%d-%H%M%S")
    hf_enabled = bool(args.hf_sync and args.hf_repo_id)
    skip_run_ids: set[str] = set()
    resume_result = None

    if hf_enabled:
        from benchmark.checkpoint.hf_sync import (
            HfUploader,
            RemoteLayout,
            verify_repo_private,
            RepoVisibilityError,
            HfResumeManager,
            resolve_auto_resume,
            ResumeValidationError as HfResumeError,
        )

        hf_token = os.environ.get("HF_TOKEN", "")
        if not hf_token:
            logger.error("--hf-sync requires HF_TOKEN environment variable")
            return 1

        try:
            verify_repo_private(args.hf_repo_id)
        except RepoVisibilityError as e:
            logger.error("HF repo visibility check failed: %s", e)
            return 1

        # ---- Auto-resume mode -------------------------------------------------
        if args.auto_resume_hf:
            # Print build/module identity to verify deployed code version
            import benchmark.checkpoint.hf_sync as hf_sync_module
            logger.info(
                "AUTO_RESUME_BUILD_ID: source_tag=%s source_commit=%s "
                "seven_arm_benchmark_sha256=%s hf_sync_sha256=%s hf_sync_path=%s",
                args.source_tag or "none",
                source_commit,
                hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16],
                hashlib.sha256(Path(hf_sync_module.__file__).read_bytes()).hexdigest()[:16],
                hf_sync_module.__file__,
            )
            scenario_provider_for_auto = ScenarioProvider(scenarios_dir)
            all_scenarios_for_auto = scenario_provider_for_auto.list_scenarios()
            selected_for_auto = all_scenarios_for_auto[:profile.scenario_count]
            strategy_names_for_auto = [args.strategy] if args.strategy else profile.strategies

            resume_result = resolve_auto_resume(
                repo_id=args.hf_repo_id,
                token=hf_token,
                profile=profile.name,
                protocol_version=args.protocol_version,
                source_commit=source_commit,
                config_hash=config_hash,
                model_identity=model_identity,
                scenario_ids=[s.scenario_id for s in selected_for_auto],
                strategy_names=strategy_names_for_auto,
                explicit_experiment_id=args.experiment_id,
                new_experiment=args.new_experiment,
            )

            print(resume_result.message)

            if resume_result.action == "error":
                logger.error("Auto-resume: %s", resume_result.message)
                return 1

            if resume_result.action == "already_complete":
                logger.info("Auto-resume: experiment %s is already complete", resume_result.experiment_id)
                return 0

            if resume_result.action == "resume":
                hf_experiment_id = resume_result.experiment_id

                hf_resume_layout = RemoteLayout(
                    profile=profile.name,
                    protocol_version=args.protocol_version,
                    source_commit=source_commit,
                    experiment_id=hf_experiment_id,
                )
                hf_resume = HfResumeManager(
                    runs_dir=output_dir,
                    repo_id=args.hf_repo_id,
                    layout=hf_resume_layout,
                    token=hf_token,
                    protocol_version=args.protocol_version,
                    config_hash=config_hash,
                    model_identity=model_identity,
                    source_commit=source_commit,
                    scenario_ids=[s.scenario_id for s in selected_for_auto],
                    strategy_names=strategy_names_for_auto,
                )
                try:
                    skip_run_ids = hf_resume.download_and_validate()
                    logger.info("Auto-resume: skipping %d completed run IDs", len(skip_run_ids))
                except HfResumeError as e:
                    logger.error("Auto-resume validation failed: %s", e)
                    return 1
            else:
                hf_experiment_id = args.experiment_id or time.strftime("exp-%Y%m%d-%H%M%S")
                # Clear stale local state from any previous experiment
                if output_dir.is_dir():
                    for f in output_dir.iterdir():
                        if f.is_file():
                            f.unlink(missing_ok=True)
                    logger.info("Start-new: cleared %s", output_dir)

        remote_layout = RemoteLayout(
            profile=profile.name,
            protocol_version=args.protocol_version,
            source_commit=source_commit,
            experiment_id=hf_experiment_id,
        )
        hf_uploader = HfUploader(
            runs_dir=output_dir,
            repo_id=args.hf_repo_id,
            layout=remote_layout,
            token=hf_token,
        )
        logger.info(
            "HF sync enabled: repo=%s  experiment=%s  remote_prefix=%s",
            args.hf_repo_id, hf_experiment_id, remote_layout.recovery(),
        )

    # Handle --resume-from: copy previous results into output dir
    if args.resume_from:
        prev_dir = Path(args.resume_from)
        logger.info("Resuming from previous results: %s", prev_dir)
        try:
            resume_mgr.resume_from(prev_dir)
        except ResumeValidationError as e:
            logger.error("Resume validation failed: %s", e)
            return 1

    # Handle --resume-from-hf: download recovery state from Hugging Face
    if args.resume_from_hf and not skip_run_ids:
        if not args.hf_repo_id:
            logger.error("--resume-from-hf requires --hf-repo-id")
            return 1
        hf_token = os.environ.get("HF_TOKEN", "")
        if not hf_token:
            logger.error("--resume-from-hf requires HF_TOKEN environment variable")
            return 1
        from benchmark.checkpoint.hf_sync import (
            HfResumeManager, RemoteLayout, ResumeValidationError as HfResumeError,
        )

        scenario_provider_for_resume = ScenarioProvider(scenarios_dir)
        all_scenarios_for_resume = scenario_provider_for_resume.list_scenarios()
        selected_for_resume = all_scenarios_for_resume[:profile.scenario_count]
        strategy_names_for_resume = [args.strategy] if args.strategy else profile.strategies

        hf_resume_layout = RemoteLayout(
            profile=profile.name,
            protocol_version=args.protocol_version,
            source_commit=source_commit,
            experiment_id=hf_experiment_id,
        )
        hf_resume = HfResumeManager(
            runs_dir=output_dir,
            repo_id=args.hf_repo_id,
            layout=hf_resume_layout,
            token=hf_token,
            protocol_version=args.protocol_version,
            config_hash=config_hash,
            model_identity=model_identity,
            source_commit=source_commit,
            scenario_ids=[s.scenario_id for s in selected_for_resume],
            strategy_names=strategy_names_for_resume,
        )
        try:
            skip_run_ids = hf_resume.download_and_validate()
            logger.info("HF resume: skipping %d completed run IDs", len(skip_run_ids))
        except HfResumeError as e:
            logger.error("HF resume validation failed: %s", e)
            return 1

    if args.resume:
        logger.info("Resume mode: checking checkpoint in %s", output_dir)
        try:
            skip_run_ids = resume_mgr.validate_and_get_skip_ids()
            logger.info("Resume: skipping %d completed run IDs", len(skip_run_ids))
        except ResumeValidationError as e:
            logger.error("Resume validation failed: %s", e)
            return 1
        except ValueError as e:
            logger.error("Corrupted checkpoint: %s", e)
            return 1

    # ---- Validate scenarios -------------------------------------------------
    scenario_provider = ScenarioProvider(scenarios_dir)
    all_scenarios = scenario_provider.list_scenarios()
    logger.info("Loaded %d scenarios from %s", len(all_scenarios), scenarios_dir)
    _validate_scenario_count(all_scenarios, profile)

    strategy_names = [args.strategy] if args.strategy else profile.strategies

    # Filter scenarios by repository, blast radius, and explicit IDs if specified
    selected_scenarios = all_scenarios
    if profile.repository_names:
        selected_scenarios = [s for s in selected_scenarios if s.repository in profile.repository_names]
    if profile.blast_radii:
        selected_scenarios = [s for s in selected_scenarios if s.blast_radius in profile.blast_radii]
    if profile.scenario_ids:
        missing = [sid for sid in profile.scenario_ids if not any(s.scenario_id == sid for s in selected_scenarios)]
        if missing:
            logger.error(
                "Configured scenario IDs not found: %s. Loaded scenarios: %s",
                missing, [s.scenario_id for s in selected_scenarios],
            )
            sys.exit(1)
        selected_scenarios = [s for s in selected_scenarios if s.scenario_id in profile.scenario_ids]
    selected_scenarios = selected_scenarios[:profile.scenario_count]
    logger.info(
        "Selected %d scenario(s) for profile=%s: %s",
        len(selected_scenarios), profile.name,
        [s.scenario_id for s in selected_scenarios],
    )

    # Report strategy capabilities per arm
    for sn in strategy_names:
        cap = describe_capabilities(sn)
        llm_match = (
            "MATCH" if cap["uses_llm_by_design"] == cap["llm_backend_attached"] else "MISMATCH"
        )
        graph_match = (
            "MATCH"
            if cap["uses_dependency_graph_by_design"] == cap["dependency_graph_attached"]
            else "MISMATCH"
        )
        logger.info(
            "Strategy audit: %s  llm_by_design=%s  llm_attached=%s  %s  "
            "graph_by_design=%s  graph_attached=%s  %s",
            sn,
            cap["uses_llm_by_design"], cap["llm_backend_attached"], llm_match,
            cap["uses_dependency_graph_by_design"], cap["dependency_graph_attached"], graph_match,
        )

    # Build dependency graph once and reuse across all arms
    dep_graph = None
    if selected_scenarios:
        dep_graph = build_dependency_graph(data_dir, selected_scenarios)

    # ---- Build execution plan -----------------------------------------------
    # Full plan (no skip) to get complete planned_run_ids for checkpoint.
    # This ensures the strategy/scenario set in checkpoint always matches
    # the full expected set, so auto-resume validation doesn't reject
    # experiments when some runs have already completed.
    full_plan = _build_execution_plan(
        profile=profile,
        scenario_provider=scenario_provider,
        strategy_names=strategy_names,
        skip_run_ids=None,
        config_hash=config_hash,
        protocol_version=args.protocol_version,
        scenarios=selected_scenarios,
    )
    planned_run_ids = [run["run_id"] for run in full_plan]

    execution_plan = _build_execution_plan(
        profile=profile,
        scenario_provider=scenario_provider,
        strategy_names=strategy_names,
        skip_run_ids=skip_run_ids,
        config_hash=config_hash,
        protocol_version=args.protocol_version,
        scenarios=selected_scenarios,
    )

    total_planned = len(planned_run_ids)

    logger.info(
        "Execution plan: %d pending, %d completed (skipped), %d total",
        len(execution_plan), len(skip_run_ids), total_planned,
    )

    if not execution_plan and skip_run_ids:
        logger.info("All runs already completed. Nothing to do.")
        checkpoint_data = checkpoint_mgr.read()
        if checkpoint_data:
            checkpoint_data.completion_status = "completed"
            checkpoint_mgr.write_atomic(checkpoint_data)
        progress_mgr.mark_completed()
        results: dict[str, Any] = {}
        for rec in record_store.load_all():
            sid = rec.strategy_id
            if sid not in results:
                results[sid] = {"success_count": 0, "failure_count": 0, "timeout_count": 0, "records": []}
            results[sid]["records"].append({
                "run_id": rec.run_id,
                "scenario_id": rec.scenario_id,
                "strategy_name": rec.strategy_id,
                "status": rec.status,
                "duration_seconds": rec.duration_seconds,
                "token_usage": rec.token_usage,
            })
            if rec.status == "succeeded":
                results[sid]["success_count"] += 1
            elif rec.status == "failed":
                results[sid]["failure_count"] += 1
            elif rec.status == "timed_out":
                results[sid]["timeout_count"] += 1
        progress_mgr.write_final_summary(results)
        return 0

    # Apply --max-runs limit
    if args.max_runs > 0 and len(execution_plan) > args.max_runs:
        logger.info("--max-runs=%d: limiting plan from %d to %d runs", args.max_runs, len(execution_plan), args.max_runs)
        execution_plan = execution_plan[:args.max_runs]

    # ---- Human-readable execution summary -----------------------------------
    if execution_plan:
        next_run = execution_plan[0]
        completed_so_far = len(skip_run_ids)
        total_all = completed_so_far + len(execution_plan)
        failed_count = 0
        if args.auto_resume_hf:
            for er in (resume_result.compatible_experiments if resume_result else []):
                failed_count = er.failed_count
        print(
            f"Experiment ID: {hf_experiment_id}\n"
            f"Completed: {completed_so_far}/{total_all}\n"
            f"Failed: {failed_count}\n"
            f"Pending: {len(execution_plan)}\n"
            f"Next run: {next_run['run_id']}"
        )

    # ---- Initialize checkpoint -----------------------------------------------
    selected_scenario_ids = [s.scenario_id for s in all_scenarios[:profile.scenario_count]]
    pending_run_ids = [rid for rid in planned_run_ids if rid not in skip_run_ids]

    # Determine if this is a RESUME or START_NEW session.
    # RESUME: prior state was downloaded/copied and normalized; we must
    #         preserve and extend it.  START_NEW: no prior state; initialize empty.
    # NOTE: do NOT infer resume from bool(skip_run_ids) — a resumed experiment
    #       with only retryable failures has an empty skip set but must still
    #       preserve the downloaded normalized checkpoint.
    is_resume = (
        args.auto_resume_hf
        and resume_result is not None
        and resume_result.action == "resume"
    )

    if is_resume:
        existing = resume_mgr.get_normalized_checkpoint()
        if existing is not None:
            # Preserve all normalized prior state from the remote checkpoint.
            checkpoint_data = existing
            checkpoint_data.planned_run_ids = planned_run_ids
            checkpoint_data.pending_run_ids = [
                rid for rid in planned_run_ids
                if rid not in existing.completed_run_ids
            ]
            checkpoint_data.total_planned = total_planned
            checkpoint_data.protocol_version = args.protocol_version
            checkpoint_data.model_identity = model_identity
            checkpoint_data.config_hash = config_hash
            checkpoint_data.source_commit = source_commit
            checkpoint_data.declared_source_tag = args.source_tag or ""
            checkpoint_data.deployed_build_id = deployed_build_id
            checkpoint_data.scenario_ids = selected_scenario_ids
            checkpoint_data.strategy_names = strategy_names
            checkpoint_data.completion_status = "running"
        else:
            # Fallback: prior files exist but normalization produced nothing.
            # Initialize with skip set only — no scientific state to preserve.
            checkpoint_data = CheckpointData(
                profile=profile.name,
                execution_plan_hash=config_hash,
                planned_run_ids=planned_run_ids,
                completed_run_ids=list(skip_run_ids),
                attempted_run_ids=list(skip_run_ids),
                succeeded_run_ids=[],
                retryable_run_ids=[],
                failed_run_ids=[],
                pending_run_ids=pending_run_ids,
                total_planned=total_planned,
                total_completed=len(skip_run_ids),
                protocol_version=args.protocol_version,
                model_identity=model_identity,
                config_hash=config_hash,
                source_commit=source_commit,
                completion_status="running",
                scenario_ids=selected_scenario_ids,
                strategy_names=strategy_names,
                declared_source_tag=args.source_tag or "",
                deployed_build_id=deployed_build_id,
            )
    else:
        checkpoint_data = CheckpointData(
            profile=profile.name,
            execution_plan_hash=config_hash,
            planned_run_ids=planned_run_ids,
            completed_run_ids=[],
            attempted_run_ids=[],
            succeeded_run_ids=[],
            retryable_run_ids=[],
            failed_run_ids=[],
            pending_run_ids=list(planned_run_ids),
            total_planned=total_planned,
            total_completed=0,
            protocol_version=args.protocol_version,
            model_identity=model_identity,
            config_hash=config_hash,
            source_commit=source_commit,
            completion_status="running",
            scenario_ids=selected_scenario_ids,
            strategy_names=strategy_names,
            declared_source_tag=args.source_tag or "",
            deployed_build_id=deployed_build_id,
        )
    checkpoint_mgr.write_atomic(checkpoint_data)

    # ---- Save experiment identity -------------------------------------------
    exp_id_file = output_dir / "experiment_id.txt"
    exp_id_file.write_text(hf_experiment_id, encoding="utf-8")
    source_identity = {
        "source_commit": source_commit,
        "source_tag": args.source_tag or "",
        "deployed_build_id": deployed_build_id,
        "config_hash": config_hash,
        "model_identity": model_identity,
        "profile": profile.name,
        "protocol_version": args.protocol_version,
        "experiment_id": hf_experiment_id,
        "hf_repo_id": args.hf_repo_id or "",
        "dry_run": args.dry_run,
    }
    if hf_enabled:
        source_identity["remote_prefix"] = remote_layout._base()
    src_id_file = output_dir / "source_identity.json"
    src_id_file.write_text(json.dumps(source_identity, indent=2), encoding="utf-8")

    # ---- Execute plan -------------------------------------------------------
    t_start = time.monotonic()
    results_agg: dict[str, dict[str, Any]] = {}
    run_count = 0

    for run_spec in execution_plan:
        run_id = run_spec["run_id"]
        scenario_id = run_spec["scenario_id"]
        strategy_name = run_spec["strategy_name"]
        repository_id = run_spec["repository_id"]
        rep = run_spec["repetition"]

        checkpoint_data.current_run_id = run_id
        checkpoint_mgr.write_atomic(checkpoint_data)

        logger.info(
            "Executing run %d/%d: %s  scenario=%s  strategy=%s  rep=%d",
            run_count + 1, len(execution_plan), run_id, scenario_id, strategy_name, rep,
        )

        # ---- Preflight gate for LLM-backed strategies ----------------------
        design = STRATEGY_CAPABILITIES_DESIGN.get(strategy_name, {})
        needs_llm = design.get("llm", False)
        hw_id = ""
        sw_id = ""
        preflight_ok = True
        rejection_reason = ""

        if needs_llm and not args.dry_run:
            preflight_ok, hw_id, sw_id, rejection_reason = _preflight_check(
                dry_run=args.dry_run,
                needs_llm=needs_llm,
                strategy_name=strategy_name,
                backend_name=resolved_backend,
            )
            if not preflight_ok:
                logger.error(
                    "Preflight FAILED for strategy=%s: %s",
                    strategy_name, rejection_reason,
                )
                # Environment error — abort immediately.
                # NO RunRecord is created (not a scientific result).
                # NO strategy failure is recorded.
                # The checkpoint remains resumable for the next session.
                checkpoint_data.completion_status = "incomplete"
                checkpoint_data.current_run_id = ""
                checkpoint_mgr.write_atomic(checkpoint_data)
                return 1

        # ---- Execute strategy -----------------------------------------------
        run_started_at = datetime.now(timezone.utc).isoformat()
        arm_workspace = workspace_dir / strategy_name
        record_dict, _ = _run_single_scenario_strategy(
            scenario_id=scenario_id,
            strategy_name=strategy_name,
            scenario_provider=scenario_provider,
            dry_run=args.dry_run,
            profile=profile,
            model_path=args.model_path,
            protocol_version=args.protocol_version,
            max_attempts=args.max_attempts,
            timeout_seconds=args.timeout,
            dep_graph=dep_graph,
            workspace_dir=arm_workspace,
            backend_name=resolved_backend,
            openrouter_model=args.openrouter_model,
            openrouter_timeout=args.openrouter_timeout,
        )
        run_ended_at = datetime.now(timezone.utc).isoformat()

        # Build persistent record
        failure_details: list[dict[str, Any]] = []
        for f in record_dict.get("failures", []):
            failure_details.append({
                "kind": f.get("kind", ""),
                "message": f.get("message", ""),
                "details": f.get("details", ""),
                "stage": f.get("stage", ""),
            })

        # Determine failure classification
        status = record_dict.get("status", "")
        failure_classification = ""
        if status in ("failed", "timed_out", "cancelled"):
            if failure_details:
                failure_classification = failure_details[0].get("kind", "")
            else:
                failure_classification = "unknown"

        # Enforce canonical execution-plan Run ID
        record_dict["run_id"] = run_id
        record_dict["scenario_id"] = scenario_id
        record_dict["strategy_name"] = strategy_name

        # Assert canonical Run ID is in planned set
        if run_id not in checkpoint_data.planned_run_ids:
            raise RuntimeError(
                f"Canonical Run ID '{run_id}' not found in planned_run_ids. "
                "This indicates an execution plan / checkpoint inconsistency."
            )

        run_record_data = _to_run_record_data(
            record_dict,
            run_id=run_id,
            profile=profile.name,
            repository_id=repository_id,
            scenario_id=scenario_id,
            strategy_id=strategy_name,
            repetition=rep,
            model_identity=model_identity,
            dry_run=args.dry_run,
            protocol_version=args.protocol_version,
            source_commit=source_commit,
            config_hash=config_hash,
            started_at=run_started_at,
            ended_at=run_ended_at,
            hw_id=hw_id,
            sw_id=sw_id,
            max_attempts=args.max_attempts,
            failure_details=failure_details,
            failure_classification=failure_classification,
        )

        # Persist immediately
        record_store.append(run_record_data)

        # Update checkpoint
        if run_id in checkpoint_data.pending_run_ids:
            checkpoint_data.pending_run_ids.remove(run_id)
        checkpoint_data.completed_run_ids.append(run_id)
        if run_id not in checkpoint_data.attempted_run_ids:
            checkpoint_data.attempted_run_ids.append(run_id)

        if status == "succeeded":
            checkpoint_data.succeeded_run_ids.append(run_id)
        else:
            checkpoint_data.failed_run_ids.append(run_id)
            if failure_classification in ("environment_preflight", "environment", "gpu_incompatible", "cuda_error"):
                checkpoint_data.retryable_run_ids.append(run_id)

        checkpoint_data.total_completed = len(checkpoint_data.completed_run_ids)
        checkpoint_mgr.write_atomic(checkpoint_data)

        # Update progress
        elapsed = time.monotonic() - t_start
        progress_data = ProgressData(
            profile=profile.name,
            total_planned=total_planned,
            total_completed=checkpoint_data.total_completed,
            total_failed=len(checkpoint_data.failed_run_ids),
            total_pending=len(checkpoint_data.pending_run_ids),
            elapsed_seconds=elapsed,
            completion_ratio=checkpoint_data.total_completed / max(total_planned, 1),
            stage="running",
        )
        progress_mgr.write(progress_data)

        # Update partial summary
        if strategy_name not in results_agg:
            results_agg[strategy_name] = {
                "success_count": 0, "failure_count": 0, "timeout_count": 0, "records": [],
            }
        results_agg[strategy_name]["records"].append(record_dict)
        if status == "succeeded":
            results_agg[strategy_name]["success_count"] += 1
        elif status == "failed":
            results_agg[strategy_name]["failure_count"] += 1
        elif status == "timed_out":
            results_agg[strategy_name]["timeout_count"] += 1

        progress_mgr.write_partial_summary(results_agg)

        # ---- HF sync after every completed/failed run --------------------
        if hf_uploader is not None:
            hf_uploader.upload_recovery()
            # Snapshot after every 2 runs (chunk)
            if run_count > 0 and run_count % 2 == 0:
                hf_uploader.upload_snapshot(packager)

        run_count += 1

        # ---- Human-readable chunk complete message ------------------------
        completed_now = checkpoint_data.total_completed
        pending_now = len(checkpoint_data.pending_run_ids)
        remote_status = "SYNCED" if hf_uploader is not None else "N/A"
        remaining = pending_now
        next_action = "run this same cell again." if remaining > 0 else "all runs complete."
        print(
            f"Chunk complete.\n"
            f"Completed: {completed_now}/{total_planned}\n"
            f"Pending: {remaining}\n"
            f"Remote checkpoint: {remote_status}\n"
            f"Next session action: {next_action}"
        )

        if run_count >= len(execution_plan):
            break

    # ---- Finalize -----------------------------------------------------------
    total_elapsed = time.monotonic() - t_start
    all_runs_completed = checkpoint_data.total_completed >= total_planned

    # ---- Rebuild all reports from persisted records (cross-session safe) ----
    from benchmark.checkpoint.reports import rebuild_experiment_reports

    audit = rebuild_experiment_reports(
        runs_dir=output_dir,
        session_elapsed_seconds=total_elapsed,
    )
    logger.info(
        "Report rebuild: %d records, %d planned, matched=%d missing=%d duplicate=%d",
        audit["raw_run_record_count"],
        audit["planned_run_id_count"],
        len(audit["matched_run_ids"]),
        len(audit["missing_run_ids"]),
        len(audit["duplicate_run_ids"]),
    )

    if all_runs_completed:
        checkpoint_data.completion_status = "completed"
        checkpoint_data.current_run_id = ""
        checkpoint_mgr.write_atomic(checkpoint_data)

        progress_mgr.mark_completed()

        logger.info(
            "Benchmark complete: %d/%d runs  success=%d failure=%d elapsed=%.1fs  label=%s",
            checkpoint_data.total_completed, total_planned,
            audit["total_succeeded"],
            audit["total_failed"],
            total_elapsed, profile.label,
        )

        # Create results ZIP
        zip_path = output_dir.parent / "benchmark-results.zip"
        packager.create_zip(zip_path)
        logger.info("Results package created: %s", zip_path)

        # HF final sync
        if hf_uploader is not None:
            hf_uploader.upload_snapshot(packager)
            hf_uploader.upload_final(packager)
            hf_uploader.upload_recovery()

        if audit["total_failed"] > 0 or audit["duration_totals"].get("experiment_run_duration_seconds", 0) > 0:
            # Use audit for exit code decision
            non_zero = audit["total_failed"] > 0
        else:
            non_zero = False
        if non_zero:
            logger.warning("Non-zero exit due to %d failures", audit["total_failed"])
            return 1
        return 0

    # Incomplete -- save progress and exit cleanly
    checkpoint_data.completion_status = "incomplete"
    checkpoint_mgr.write_atomic(checkpoint_data)

    final_progress = ProgressData(
        profile=profile.name,
        total_planned=total_planned,
        total_completed=checkpoint_data.total_completed,
        total_failed=len(checkpoint_data.failed_run_ids),
        total_pending=len(checkpoint_data.pending_run_ids),
        elapsed_seconds=total_elapsed,
        completion_ratio=checkpoint_data.total_completed / max(total_planned, 1),
        stage="interrupted",
        total_attempted=len(checkpoint_data.attempted_run_ids),
        total_succeeded=audit["total_succeeded"],
        total_retryable=audit["total_retryable"],
        completion_status="incomplete",
        experiment_run_duration_seconds=audit["duration_totals"]["experiment_run_duration_seconds"],
        session_elapsed_seconds=total_elapsed,
        report_generated_at=datetime.now(UTC).isoformat(),
        experiment_wall_clock_seconds=None,
        experiment_wall_clock_unavailable_reason="cross-session idle intervals are not measured",
    )
    progress_mgr.write(final_progress)

    if hf_uploader is not None:
        hf_uploader.upload_snapshot(packager)
        hf_uploader.upload_recovery()

    logger.info(
        "Session incomplete: %d/%d runs completed. Resume with --resume or --resume-from-hf to continue.",
        checkpoint_data.total_completed, total_planned,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
