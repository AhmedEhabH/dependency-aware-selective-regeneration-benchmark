from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.core.enums import ArtifactType
from benchmark.core.models import ArtifactRef, Scenario
from benchmark.execution.semantic_executability import (
    _CANARY_MIGRATION_FIXTURES,
    check_scenario_executability,
    check_scenario_set_executability,
)

CANARY_SCENARIO_IDS = ("todo-loc-001", "djangocms-cross-007", "saleor-loc-001")


def _make_scenario(
    scenario_id: str,
    repository: str,
    *,
    post_generation_command: tuple[str, ...] = (),
    require_new_migration: bool = False,
    migration_directory: str = "todo/migrations",
) -> Scenario:
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
        post_generation_command=post_generation_command,
        require_new_migration=require_new_migration,
        migration_directory=migration_directory,
    )


def _canary_scenario(scenario_id: str, repository: str) -> Scenario:
    command, require_new, migration_dir = _CANARY_MIGRATION_FIXTURES[scenario_id]
    return _make_scenario(
        scenario_id,
        repository,
        post_generation_command=command,
        require_new_migration=require_new,
        migration_directory=migration_dir,
    )


class TestSemanticExecutabilityGate:
    def test_todo_loc_001_executable_against_staged_todo(self) -> None:
        repo_root = Path(__file__).resolve().parents[3] / "benchmark_data" / "repositories" / "todo"
        if not (repo_root / "todo" / "models.py").is_file():
            pytest.skip("staged todo repository not available in this environment")
        verdict = check_scenario_executability(
            _canary_scenario("todo-loc-001", "todo"),
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


class TestCanaryMigrationExecutability:
    """D13R2 Fix 2 — the semantic gate proves migration executability for the
    3 canary scenarios using an explicit frozen map (never inferred from English
    requirement text at runtime)."""

    def _repo_roots(self, tmp_path: Path) -> dict[str, Path]:
        repos = tmp_path / "repositories"
        (repos / "todo" / "todo").mkdir(parents=True)
        (repos / "djangocms" / "cms" / "models").mkdir(parents=True)
        (repos / "saleor" / "saleor" / "product").mkdir(parents=True)
        (repos / "todo" / "todo" / "models.py").write_text(
            "class Task:\n    pass\n", encoding="utf-8"
        )
        (repos / "djangocms" / "cms" / "models" / "pagemodel.py").write_text(
            "class Page:\n    pass\n", encoding="utf-8"
        )
        (repos / "saleor" / "saleor" / "product" / "models.py").write_text(
            "class Product:\n    pass\n", encoding="utf-8"
        )
        return {
            "todo": repos / "todo",
            "djangocms": repos / "djangocms",
            "saleor": repos / "saleor",
        }

    def test_registry_covers_exactly_administered_canary_scenarios(self) -> None:
        assert set(_CANARY_MIGRATION_FIXTURES) == set(CANARY_SCENARIO_IDS)

    def test_canonical_canary_scenarios_pass_with_staged_pinned_bases(
        self, tmp_path: Path
    ) -> None:
        roots = self._repo_roots(tmp_path)
        for scenario_id, repository in (
            ("todo-loc-001", "todo"),
            ("djangocms-cross-007", "djangocms"),
            ("saleor-loc-001", "saleor"),
        ):
            verdict = check_scenario_executability(
                _canary_scenario(scenario_id, repository),
                repository_root=roots[repository],
            )
            assert verdict.executable is True, (
                f"{scenario_id} should be executable: {verdict.reasons}"
            )
            assert verdict.verifiable is True

    def test_require_new_migration_false_fails_closed(self, tmp_path: Path) -> None:
        roots = self._repo_roots(tmp_path)
        command, _, migration_dir = _CANARY_MIGRATION_FIXTURES["todo-loc-001"]
        verdict = check_scenario_executability(
            _make_scenario(
                "todo-loc-001",
                "todo",
                post_generation_command=command,
                require_new_migration=False,
                migration_directory=migration_dir,
            ),
            repository_root=roots["todo"],
        )
        assert verdict.executable is False
        assert any("require_new_migration" in r for r in verdict.reasons)

    def test_empty_command_fails_closed(self, tmp_path: Path) -> None:
        roots = self._repo_roots(tmp_path)
        _, require_new, migration_dir = _CANARY_MIGRATION_FIXTURES["todo-loc-001"]
        verdict = check_scenario_executability(
            _make_scenario(
                "todo-loc-001",
                "todo",
                post_generation_command=(),
                require_new_migration=require_new,
                migration_directory=migration_dir,
            ),
            repository_root=roots["todo"],
        )
        assert verdict.executable is False
        assert any("post_generation_command" in r for r in verdict.reasons)

    def test_wrong_app_label_fails_closed(self, tmp_path: Path) -> None:
        roots = self._repo_roots(tmp_path)
        wrong_command = (
            "python", "manage.py", "makemigrations", "WRONG", "--noinput",
        )
        _, require_new, migration_dir = _CANARY_MIGRATION_FIXTURES["todo-loc-001"]
        verdict = check_scenario_executability(
            _make_scenario(
                "todo-loc-001",
                "todo",
                post_generation_command=wrong_command,
                require_new_migration=require_new,
                migration_directory=migration_dir,
            ),
            repository_root=roots["todo"],
        )
        assert verdict.executable is False
        assert any("post_generation_command" in r for r in verdict.reasons)

    def test_wrong_migration_directory_fails_closed(self, tmp_path: Path) -> None:
        roots = self._repo_roots(tmp_path)
        command, require_new, _ = _CANARY_MIGRATION_FIXTURES["todo-loc-001"]
        verdict = check_scenario_executability(
            _make_scenario(
                "todo-loc-001",
                "todo",
                post_generation_command=command,
                require_new_migration=require_new,
                migration_directory="other/migrations",
            ),
            repository_root=roots["todo"],
        )
        assert verdict.executable is False
        assert any("migration_directory" in r for r in verdict.reasons)

    def test_registered_but_missing_migration_metadata_fails_closed(
        self, tmp_path: Path
    ) -> None:
        roots = self._repo_roots(tmp_path)
        verdict = check_scenario_executability(
            _make_scenario("todo-loc-001", "todo"),
            repository_root=roots["todo"],
        )
        assert verdict.executable is False
        joined = " ".join(verdict.reasons)
        assert "post_generation_command" in joined
        assert "require_new_migration" in joined
