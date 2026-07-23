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
import json
import logging
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

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
        RepositoryAgentStrategy,
        StaticOnlyStrategy,
    )
    graph_classes: set[type] = {HybridSelectiveStrategy, FullContextStrategy, StaticOnlyStrategy}
    llm_classes: set[type] = {RepositoryAgentStrategy}
    cls_map = {
        "monolithic": None,
        "agent": RepositoryAgentStrategy,
        "selective": HybridSelectiveStrategy,
        "compiled_ai": StaticOnlyStrategy,
        "delta_mcp": None,
        "incr_rtl": None,
        "code_plan": FullContextStrategy,
    }
    cls = cls_map.get(strategy_name)
    return {
        "uses_llm_by_design": design.get("llm", False),
        "llm_backend_attached": (cls in llm_classes) if cls else False,
        "uses_dependency_graph_by_design": design.get("graph", False),
        "dependency_graph_attached": (cls in graph_classes) if cls else False,
    }

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
    ),
    "research": ExecutionProfile(
        name="research",
        label="protocol-research",
        scenario_count=24,
        strategies=["agent", "selective", "compiled_ai", "delta_mcp"],
        repetitions=3,
        is_publication=True,
        description="24 scenarios, full-evolution strategies, 3 reps, publication",
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

def make_backend(dry_run: bool, model_path: str | None = None):  # type: ignore[no-untyped-def]
    if dry_run:
        from benchmark.llm.mock_backend import MockLLMBackend
        return MockLLMBackend(response_text="dry-run-response")
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

    Falls back to a minimal graph containing the artifact-universe paths
    as nodes (zero edges) when the profile has no declared dependency edges.
    """
    from benchmark.core.models import DependencyGraph
    from benchmark.graph.builder import ProfileGraphBuilder

    repo_id = None
    artifacts: set[str] = set()
    for s in scenarios:
        if repo_id is None:
            repo_id = s.repository
        for a in s.expected_affected_artifacts:
            artifacts.add(a.path)

    if not repo_id:
        return None

    # Try profile-based graph first
    profile_dir = data_dir / "repository_profiles"
    if profile_dir.is_dir():
        from benchmark.repositories.loader import RepositoryLoader
        try:
            loader = RepositoryLoader(data_dir)
            collection = loader.load_manifest()
            profile = collection.get_profile(repo_id)
            if profile is not None:
                builder = ProfileGraphBuilder()
                graph = builder.build_from_profile(profile)
                if graph is not None:
                    logger.info(
                        "Profile graph for repo=%s  nodes=%d  edges=%d",
                        repo_id, len(graph.nodes), len(graph.edges),
                    )
                    return graph
            logger.info("No profile graph for '%s' — building minimal graph from artifacts", repo_id)
        except Exception:
            logger.warning("Failed to load profile graph for '%s'", repo_id, exc_info=True)
    else:
        logger.info("No repository_profiles dir — building minimal graph from artifacts")

    # Fallback: minimal graph with artifact paths as nodes
    if not artifacts:
        logger.warning("No artifacts available to build even a minimal graph")
        return None
    minimal = DependencyGraph(
        nodes=tuple(sorted(artifacts)),
        edges=(),
        metadata={"source": "artifact_fallback", "repo_id": repo_id},
    )
    logger.info(
        "Minimal graph for repo=%s  nodes=%d  edges=0 (artifact fallback)",
        repo_id, len(minimal.nodes),
    )
    return minimal


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
) -> object:
    """Run a single strategy arm and return a PipelineResult."""
    from benchmark.execution.pipeline import BenchmarkPipeline, PipelineConfig

    scenario_count = profile.scenario_count
    all_scenarios = scenario_provider.list_scenarios()
    selected = all_scenarios[:scenario_count]
    scenario_ids = [s.scenario_id for s in selected]

    design = STRATEGY_CAPABILITIES_DESIGN.get(strategy_name, {})
    needs_llm = design.get("llm", False)

    backend = make_backend(dry_run, model_path=model_path) if needs_llm else None
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

    if not args.dry_run and not args.model_path:
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


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    workspace_dir = output_dir / "workspace"

    data_dir = Path(args.data_dir) if args.data_dir else DEFAULT_DATA_DIR
    scenarios_dir = data_dir / "scenarios"

    profile = PROFILES[args.profile]

    logger.info(
        "Benchmark config: dry_run=%s  profile=%s  label=%s  output=%s  data_dir=%s",
        args.dry_run, profile.name, profile.label, output_dir, data_dir,
    )

    scenario_provider = ScenarioProvider(scenarios_dir)
    all_scenarios = scenario_provider.list_scenarios()
    logger.info("Loaded %d scenarios from %s", len(all_scenarios), scenarios_dir)
    _validate_scenario_count(all_scenarios, profile)

    strategy_names = [args.strategy] if args.strategy else profile.strategies

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
    first_scenarios = all_scenarios[:profile.scenario_count]
    if first_scenarios:
        dep_graph = build_dependency_graph(data_dir, first_scenarios)

    results: dict = {}

    for strategy_name in strategy_names:
        arm_workspace = workspace_dir / strategy_name
        result = run_arm(
            strategy_name=strategy_name,
            scenario_provider=scenario_provider,
            isolation_workspace=arm_workspace,
            dry_run=args.dry_run,
            profile=profile,
            model_path=args.model_path,
            protocol_version=args.protocol_version,
            max_attempts=args.max_attempts,
            timeout_seconds=args.timeout,
            dep_graph=dep_graph,
        )
        results[strategy_name] = result

    aggregate_results(results, output_dir, is_publication=profile.is_publication)

    total_success = sum(r.success_count for r in results.values())
    total_failure = sum(r.failure_count for r in results.values())
    total_timeout = sum(r.timeout_count for r in results.values())

    # Detailed arm-level report
    for arm_name, result in results.items():
        cap = describe_capabilities(arm_name)
        for rec in result.records:
            tok = rec.token_usage
            gen_called = cap["llm_backend_attached"]
            gen_succeeded = gen_called and tok.total_tokens > 0
            logger.info(
                "Arm report: strategy=%s  llm_by_design=%s  llm_attached=%s  "
                "gen_called=%s  gen_succeeded=%s  graph_by_design=%s  graph_attached=%s  "
                "status=%s  tokens=%d/%d/%d  duration=%.1fs",
                arm_name,
                cap["uses_llm_by_design"], cap["llm_backend_attached"],
                gen_called, gen_succeeded,
                cap["uses_dependency_graph_by_design"], cap["dependency_graph_attached"],
                rec.status.value,
                tok.prompt_tokens, tok.completion_tokens, tok.total_tokens,
                rec.duration_seconds,
            )

    logger.info(
        "Benchmark complete: %d success / %d failure / %d timeout across %d arms  label=%s",
        total_success, total_failure, total_timeout, len(results), profile.label,
    )
    if total_failure > 0 or total_timeout > 0:
        logger.warning("Non-zero exit due to %d failures, %d timeouts", total_failure, total_timeout)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
