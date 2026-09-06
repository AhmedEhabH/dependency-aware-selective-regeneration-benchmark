"""PILOT-READY-01 frozen Pilot readiness contracts.

These tests express the exact Pilot design as configuration source-of-truth
and prove that the runtime adapter (``PROFILES["pilot"]``) matches it.

Config source-of-truth hierarchy (frozen):
    1. frozen protocol documents = research design authority
    2. repository/scenario manifests = data/revision authority
    3. configs/pilot.yaml = Pilot stage configuration authority
    4. seven_arm_benchmark.py profile = thin execution adapter

Protocol labels (frozen mapping, see 01_FROZEN_PROTOCOL_AND_DECISIONS.md):
    repository_agent  -> iterative_repository_agent
    hybrid_selective  -> selective
"""

from __future__ import annotations

from pathlib import Path

import yaml

from benchmark.core.enums import EvidenceTier
from benchmark.core.models import Scenario

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
PILOT_CONFIG_PATH = PROJECT_DIR / "configs" / "pilot.yaml"

PILOT_PROFILE_LABEL = "protocol-pilot"
PILOT_PROTOCOL_VERSION = "1.2"
PILOT_TIMEOUT_SECONDS = 1200
PILOT_REPETITIONS = 2
PILOT_MAX_ITERATIONS = 3  # initial generation + max 2 repairs (frozen AC-05)

# Frozen model identity (04_PILOT_MATRIX_AND_CONFIG_FREEZE.md, Blocker C):
#   Qwen2.5-Coder-14B-Instruct + bnb-nf4 + temperature 0.
# This is the exact model/quantization accepted for Scientific Smoke V2 and
# carried forward for Pilot. It is NOT the 7B checkpoint.
PILOT_MODEL_NAME = "Qwen/Qwen2.5-Coder-14B-Instruct"
PILOT_QUANTIZATION_MODE = "bnb-nf4"
PILOT_TEMPERATURE = 0

PILOT_SCENARIO_IDS = [
    "todo-loc-001",
    "todo-loc-002",
    "todo-mod-004",
    "todo-cross-007",
    "djangocms-mod-005",
    "djangocms-loc-002",
    "djangocms-mod-004",
    "djangocms-cross-007",
    "saleor-loc-001",
    "saleor-loc-002",
    "saleor-mod-004",
    "saleor-cross-007",
]

PILOT_STRATEGIES = ["iterative_repository_agent", "selective"]

# Protocol label -> Pilot implementation ID (frozen mapping).
STRATEGY_PROTOCOL_MAP = {
    "repository_agent": "iterative_repository_agent",
    "hybrid_selective": "selective",
}

# Repository versions frozen in benchmark_data/manifests/repository_versions.yaml.
PINNED_REFS = {
    "todo": "b8a33e20bdaf5b329114273063fbe8d5aa66e9cf",
    "djangocms": "0f633fc9fa213357f4202482aab2b0edad680f95",
    "saleor": "e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10",
}

CANONICAL_TODO_URL = "https://github.com/ahmed-ehab/controlled-django-todo"


def _load_pilot_config():
    from benchmark.config.loader import load_config

    return load_config(PILOT_CONFIG_PATH)


def _pilot_scenarios() -> list[Scenario]:
    blast = {
        "todo-loc-001": "localized",
        "todo-loc-002": "localized",
        "todo-mod-004": "moderate",
        "todo-cross-007": "cross_cutting",
        "djangocms-mod-005": "moderate",
        "djangocms-loc-002": "localized",
        "djangocms-mod-004": "moderate",
        "djangocms-cross-007": "cross_cutting",
        "saleor-loc-001": "localized",
        "saleor-loc-002": "localized",
        "saleor-mod-004": "moderate",
        "saleor-cross-007": "cross_cutting",
    }
    scenarios = []
    for sid in PILOT_SCENARIO_IDS:
        repo = sid.split("-")[0]
        scenarios.append(
            Scenario(
                scenario_id=sid,
                repository=repo,
                change_type="schema",
                blast_radius=blast[sid],
                requirement_before="before",
                requirement_after="after",
                rationale="pilot readiness contract",
            )
        )
    return scenarios


class TestPilotConfigFrozen:
    """Gate 1/6: configs/pilot.yaml carries the frozen Pilot design exactly."""

    def test_pilot_config_loads(self) -> None:
        config = _load_pilot_config()
        assert config.protocol_version == PILOT_PROTOCOL_VERSION
        assert config.execution_mode == "kaggle"

    def test_exact_strategies(self) -> None:
        config = _load_pilot_config()
        assert [s.name for s in config.strategies] == PILOT_STRATEGIES

    def test_exact_two_repetitions(self) -> None:
        config = _load_pilot_config()
        assert config.execution.repetitions == PILOT_REPETITIONS

    def test_uniform_timeout_600(self) -> None:
        config = _load_pilot_config()
        assert config.execution.timeout_seconds == PILOT_TIMEOUT_SECONDS

    def test_repair_budget_max_three_attempts(self) -> None:
        config = _load_pilot_config()
        assert config.execution.max_iterations == PILOT_MAX_ITERATIONS

    def test_evidence_tier_engineering_validation(self) -> None:
        config = _load_pilot_config()
        assert config.execution.evidence_tier == EvidenceTier.engineering_validation

    def test_exact_model_identity_frozen_14b_bnb_nf4(self) -> None:
        """Blocker C: exact Pilot model + quantization identity, no silent 7B drift."""
        config = _load_pilot_config()
        assert len(config.backends) == 1
        backend = config.backends[0]
        assert backend.kind == "kaggle_qwen"
        assert backend.params.get("model_name") == PILOT_MODEL_NAME
        assert backend.params.get("quantization_mode") == PILOT_QUANTIZATION_MODE
        assert backend.params.get("temperature") == PILOT_TEMPERATURE
        assert PILOT_MODEL_NAME.lower() not in ("7b",)
        assert "7b" not in PILOT_MODEL_NAME.lower()

    def test_exact_twelve_scenario_ids(self) -> None:
        config = _load_pilot_config()
        assert config.scenario_selection.scenario_ids == PILOT_SCENARIO_IDS

    def test_three_repos_four_each(self) -> None:
        config = _load_pilot_config()
        ids = config.scenario_selection.scenario_ids
        counts: dict[str, int] = {}
        for sid in ids:
            repo = sid.split("-")[0]
            counts[repo] = counts.get(repo, 0) + 1
        assert counts == {"todo": 4, "djangocms": 4, "saleor": 4}

    def test_blast_radii_represented(self) -> None:
        config = _load_pilot_config()
        radii = {sid.split("-")[1] for sid in config.scenario_selection.scenario_ids}
        assert {"loc", "mod", "cross"} == radii

    def test_no_floating_repo_refs(self) -> None:
        config = _load_pilot_config()
        for repo in config.repositories:
            assert repo.ref == PINNED_REFS[repo.name], (
                f"{repo.name} ref {repo.ref!r} is not the pinned immutable SHA"
            )
            assert repo.ref != "main"

    def test_no_placeholder_url(self) -> None:
        config = _load_pilot_config()
        for repo in config.repositories:
            assert "example" not in repo.url, f"{repo.name} has placeholder URL"

    def test_todo_canonical_url(self) -> None:
        config = _load_pilot_config()
        todo = next(r for r in config.repositories if r.name == "todo")
        assert todo.url == CANONICAL_TODO_URL

    def test_strategy_protocol_label_mapping(self) -> None:
        """Protocol label repository_agent/hybrid_selective -> implementation IDs."""
        config = _load_pilot_config()
        impl_by_label = {s.protocol_label: s.name for s in config.strategies}
        assert impl_by_label == STRATEGY_PROTOCOL_MAP

    def test_expected_total_48(self) -> None:
        config = _load_pilot_config()
        total = (
            len(config.scenario_selection.scenario_ids)
            * len(config.strategies)
            * config.execution.repetitions
        )
        assert total == 48


class TestPilotProfileParity:
    """Gate 1: runtime adapter PROFILES['pilot'] matches configs/pilot.yaml."""

    def test_profile_label_matches_config(self) -> None:
        from seven_arm_benchmark import PROFILES

        raw = yaml.safe_load(PILOT_CONFIG_PATH.read_text(encoding="utf-8"))
        assert raw["profile_label"] == PILOT_PROFILE_LABEL
        assert PROFILES["pilot"].label == PILOT_PROFILE_LABEL

    def test_profile_matches_config_exactly(self) -> None:
        from seven_arm_benchmark import PROFILES

        config = _load_pilot_config()
        profile = PROFILES["pilot"]

        assert profile.scenario_count == len(PILOT_SCENARIO_IDS)
        assert profile.scenario_ids == PILOT_SCENARIO_IDS
        assert profile.strategies == [s.name for s in config.strategies]
        assert profile.repetitions == config.execution.repetitions
        assert profile.timeout_seconds == config.execution.timeout_seconds
        assert profile.repository_names == [r.name for r in config.repositories]
        assert profile.blast_radii == config.scenario_selection.blast_radii
        assert profile.is_publication is False

    def test_profile_has_exact_twelve_scenarios(self) -> None:
        from seven_arm_benchmark import PROFILES

        profile = PROFILES["pilot"]
        assert profile.scenario_ids is not None
        assert len(profile.scenario_ids) == 12
        assert len(set(profile.scenario_ids)) == 12

    def test_profile_repositories_cover_three(self) -> None:
        from seven_arm_benchmark import PROFILES

        assert PROFILES["pilot"].repository_names == ["todo", "djangocms", "saleor"]


class TestPilotMatrix:
    """Gate 6: exact 48-cell plan, no duplicates, no missing cells."""

    def test_exact_48_unique_planned_run_ids(self) -> None:
        from seven_arm_benchmark import PROFILES, _build_execution_plan

        profile = PROFILES["pilot"]
        plan = _build_execution_plan(
            profile=profile,
            scenario_provider=None,
            strategy_names=profile.strategies,
            scenarios=_pilot_scenarios(),
        )
        assert len(plan) == 48
        run_ids = [r["run_id"] for r in plan]
        assert len(run_ids) == len(set(run_ids)), "duplicate planned run IDs"
        strategies = [r["strategy_name"] for r in plan]
        assert set(strategies) == set(PILOT_STRATEGIES)
        reps = [r["repetition"] for r in plan]
        assert set(reps) == {1, 2}
        repos = {r["repository_id"] for r in plan}
        assert repos == {"todo", "djangocms", "saleor"}

    def test_each_repo_has_16_cells(self) -> None:
        from seven_arm_benchmark import PROFILES, _build_execution_plan

        profile = PROFILES["pilot"]
        plan = _build_execution_plan(
            profile=profile,
            scenario_provider=None,
            strategy_names=profile.strategies,
            scenarios=_pilot_scenarios(),
        )
        from collections import Counter

        counts = Counter(r["repository_id"] for r in plan)
        assert counts == {"todo": 16, "djangocms": 16, "saleor": 16}


class TestPilotStrategySemantics:
    """Gate 5: protocol repository_agent/hybrid_selective use the right implementation."""

    def test_both_pilot_strategies_approved_for_regeneration(self) -> None:
        from seven_arm_benchmark import REGENERATION_APPROVED_STRATEGIES

        assert "iterative_repository_agent" in REGENERATION_APPROVED_STRATEGIES
        assert "selective" in REGENERATION_APPROVED_STRATEGIES

    def test_repository_agent_maps_to_iterative_strategy(self) -> None:
        from benchmark.llm.mock_backend import MockLLMBackend
        from benchmark.strategies import IterativeRepositoryAgentStrategy
        from seven_arm_benchmark import make_strategy

        strategy = make_strategy(
            "iterative_repository_agent",
            backend=MockLLMBackend(response_text="dry-run-response"),
        )
        assert isinstance(strategy, IterativeRepositoryAgentStrategy)

    def test_hybrid_selective_maps_to_hybrid_strategy(self) -> None:
        from benchmark.strategies import HybridSelectiveStrategy
        from seven_arm_benchmark import make_strategy

        strategy = make_strategy("selective")
        assert isinstance(strategy, HybridSelectiveStrategy)

    def test_agent_not_required_for_pilot(self) -> None:
        """'agent' must not be the Pilot baseline; iterative_repository_agent is."""
        from seven_arm_benchmark import PROFILES

        assert "agent" not in PROFILES["pilot"].strategies


class TestPilotManifestProtocolParity:
    """D11 B3: Pilot validation manifest must mirror the active Pilot contract.

    The Pilot runtime protocol is 1.1 (configs/pilot.yaml). The frozen per-cell
    validation-command manifest claims to mirror the active Pilot contract, so
    it must agree on ``protocol_version``. A silent drift here (e.g. a manifest
    left on 1.0 while the runtime moved to 1.1) must fail a test.
    """

    PILOT_CONFIG = PROJECT_DIR / "configs" / "pilot.yaml"
    VALIDATION_MANIFEST = PROJECT_DIR / "benchmark_data" / "manifests" / "pilot_validation_commands.yaml"

    def test_manifest_protocol_matches_pilot_config(self) -> None:
        with self.PILOT_CONFIG.open(encoding="utf-8") as f:
            pilot_yaml = yaml.safe_load(f)
        with self.VALIDATION_MANIFEST.open(encoding="utf-8") as f:
            manifest_yaml = yaml.safe_load(f)

        pilot_protocol = str(pilot_yaml["protocol_version"])
        manifest_protocol = str(manifest_yaml["protocol_version"])
        assert manifest_protocol == pilot_protocol, (
            "pilot_validation_commands.yaml protocol_version "
            f"{manifest_protocol!r} must mirror configs/pilot.yaml "
            f"protocol_version {pilot_protocol!r}"
        )

    def test_manifest_protocol_is_active_version(self) -> None:
        with self.VALIDATION_MANIFEST.open(encoding="utf-8") as f:
            manifest_yaml = yaml.safe_load(f)
        assert str(manifest_yaml["protocol_version"]) == PILOT_PROTOCOL_VERSION


class TestPilotCanaryTopology:
    """D11 B1: the pre-Pilot canary must represent ALL three repositories."""

    def test_canary_profile_covers_three_repositories(self) -> None:
        from seven_arm_benchmark import PROFILES

        canary = PROFILES["pilot-canary"]
        assert canary.repository_names == ["todo", "djangocms", "saleor"]
        assert canary.scenario_ids == [
            "todo-loc-001",
            "djangocms-cross-007",
            "saleor-loc-001",
        ]

    def test_canary_profile_scenario_count_is_three(self) -> None:
        from seven_arm_benchmark import PROFILES

        assert PROFILES["pilot-canary"].scenario_count == 3

    def test_canary_profile_blast_radii_cover_canary_scenarios(self) -> None:
        from seven_arm_benchmark import PROFILES

        canary = PROFILES["pilot-canary"]
        # todo-loc-001 (localized) and djangocms-cross-007 (cross_cutting) and
        # saleor-loc-001 (localized) must all survive the blast-radius filter.
        assert "localized" in canary.blast_radii
        assert "cross_cutting" in canary.blast_radii
        assert canary.scenario_count == len(canary.scenario_ids)
