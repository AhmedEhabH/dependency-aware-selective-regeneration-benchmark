from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.core.enums import ArtifactType
from benchmark.core.models import ArtifactRef, Scenario
from benchmark.execution.semantic_executability import (
    check_scenario_executability,
    check_scenario_set_executability,
)


def _make_scenario(scenario_id: str, repository: str) -> Scenario:
    return Scenario(
        scenario_id=scenario_id,
        repository=repository,
        change_type="test",
        blast_radius="localized",
        requirement_before="before",
        requirement_after="after",
        rationale="test",
        expected_affected_artifacts=(
            ArtifactRef(path="a.py", artifact_type=ArtifactType.source),
        ),
    )


class TestSemanticExecutabilityGate:
    def test_todo_loc_001_executable_against_staged_todo(self) -> None:
        repo_root = Path(__file__).resolve().parents[3] / "benchmark_data" / "repositories" / "todo"
        if not (repo_root / "todo" / "models.py").is_file():
            pytest.skip("staged todo repository not available in this environment")
        verdict = check_scenario_executability(
            _make_scenario("todo-loc-001", "todo"),
            repository_root=repo_root,
        )
        assert verdict.executable is True
        assert verdict.verifiable is True

    def test_todo_loc_001_fail_closed_without_repo(self) -> None:
        verdict = check_scenario_executability(_make_scenario("todo-loc-001", "todo"))
        assert verdict.executable is False
        assert verdict.verifiable is False
        assert any("could not be verified" in r for r in verdict.reasons)

    def test_saleor_loc_002_is_featured_missing_fails_closed(self) -> None:
        verdict = check_scenario_executability(
            _make_scenario("saleor-loc-002", "saleor")
        )
        assert verdict.executable is False
        assert any("is_featured" in r for r in verdict.reasons)
        assert any("lacks required capability" in r for r in verdict.reasons)

    def test_saleor_cross_007_fails_closed_when_unverifiable(self) -> None:
        verdict = check_scenario_executability(
            _make_scenario("saleor-cross-007", "saleor")
        )
        assert verdict.executable is False
        assert verdict.verifiable is False

    def test_unknown_scenario_fails_closed(self) -> None:
        verdict = check_scenario_executability(
            _make_scenario("no-such-scenario", "unknown")
        )
        assert verdict.executable is False
        assert verdict.verifiable is False
        assert any("no pinned-base capability probes" in r for r in verdict.reasons)

    def test_gate_never_fabricates_pass_for_registered_but_absent(self) -> None:
        scenarios = [
            _make_scenario("saleor-loc-002", "saleor"),
            _make_scenario("todo-loc-001", "todo"),
        ]
        verdicts = check_scenario_set_executability(scenarios)
        by_id = {v.scenario_id: v for v in verdicts}
        assert by_id["saleor-loc-002"].executable is False
        assert by_id["todo-loc-001"].executable is False  # unverifiable w/o repo
