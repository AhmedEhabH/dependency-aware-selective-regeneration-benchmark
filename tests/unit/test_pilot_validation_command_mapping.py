"""PILOT-EXEC-01 frozen per-repository validation command mapping.

Proves the requirements of ``03_VALIDATION_CONTRACT.md``:

- all three Pilot repositories (todo, djangocms, saleor) are mapped to a
  frozen validation command;
- the resolver has no ``break``/first-repository-only behavior;
- no selected Pilot repository resolves to ``None`` validation;
- the exact frozen mapping loads from the bundle manifest;
- an unknown or missing mapping fails closed.

The frozen manifest ``benchmark_data/manifests/pilot_validation_commands.yaml``
is the single source of truth for Pilot baseline validation commands.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from benchmark.core.exceptions import RepositoryError
from benchmark.repositories.validation_commands import (
    FrozenValidationCommand,
    ValidationCommandMap,
    load_validation_commands,
    resolve_validation_command,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
FROZEN_MANIFEST = PROJECT_DIR / "benchmark_data" / "manifests" / "pilot_validation_commands.yaml"
PILOT_CONFIG = PROJECT_DIR / "configs" / "pilot.yaml"
BENCHMARK_SCRIPT = PROJECT_DIR / "seven_arm_benchmark.py"

PILOT_REPOSITORIES = ("todo", "djangocms", "saleor")

PYTHON_TOKEN = "{python}"
FAKE_PYTHON = "/opt/venv/bin/python"


def _load_pilot_config() -> dict:
    return yaml.safe_load(PILOT_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def command_map() -> ValidationCommandMap:
    return load_validation_commands(FROZEN_MANIFEST)


def test_all_three_pilot_repositories_mapped(command_map: ValidationCommandMap) -> None:
    assert set(command_map.repo_ids()) == set(PILOT_REPOSITORIES)


def test_no_selected_repository_resolves_none(
    command_map: ValidationCommandMap,
) -> None:
    config = _load_pilot_config()
    for repo in config["repositories"]:
        name = repo["name"]
        assert name in command_map.repo_ids(), (
            f"Pilot repository '{name}' has no frozen validation command"
        )
        assert command_map.get(name) is not None


def test_frozen_mapping_scenario_ids_match_pilot_config(
    command_map: ValidationCommandMap,
) -> None:
    config = _load_pilot_config()
    selected = set(config["scenario_selection"]["scenario_ids"])
    repo_to_scenarios: dict[str, set[str]] = {}
    for scenario in selected:
        repo_id = scenario.split("-", 1)[0]
        repo_to_scenarios.setdefault(repo_id, set()).add(scenario)
    assert set(repo_to_scenarios) == set(PILOT_REPOSITORIES)
    for repo_id, scenario_ids in repo_to_scenarios.items():
        frozen = command_map.require(repo_id)
        assert set(frozen.scenario_ids) == scenario_ids, (
            f"frozen scenario_ids for '{repo_id}' do not match pilot.yaml"
        )


def test_frozen_command_is_non_empty_and_resolves(
    command_map: ValidationCommandMap,
) -> None:
    for repo_id in PILOT_REPOSITORIES:
        frozen = command_map.require(repo_id)
        assert frozen.command
        resolved = frozen.resolve_interpreter(FAKE_PYTHON)
        assert resolved[0] == FAKE_PYTHON
        assert PYTHON_TOKEN not in resolved
        for extra in frozen.resolved_additional_commands(FAKE_PYTHON):
            assert extra
            assert PYTHON_TOKEN not in extra


def test_todo_frozen_command_is_complete_suite(command_map: ValidationCommandMap) -> None:
    todo = command_map.require("todo")
    assert todo.command == ("{python}", "-m", "pytest")
    assert todo.dependency_runtime == "benchmark"
    assert not todo.services


def test_djangocms_frozen_command_covers_obligation_union(
    command_map: ValidationCommandMap,
) -> None:
    djangocms = command_map.require("djangocms")
    modules = set(djangocms.command[3:])
    assert modules == {
        "cms.tests.test_api",
        "cms.tests.test_page",
        "cms.tests.test_page_admin",
        "cms.tests.test_permissions",
        "cms.tests.test_permmod",
        "cms.tests.test_signals",
        "cms.tests.test_toolbar",
        "cms.tests.test_views",
    }
    assert djangocms.env_dict()["DATABASE_URL"] == "sqlite://localhost/testdb.sqlite"


def test_saleor_frozen_command_covers_all_obligation_areas(
    command_map: ValidationCommandMap,
) -> None:
    saleor = command_map.require("saleor")
    paths = set(saleor.command[saleor.command.index("logical") + 1 :])
    assert paths == {
        "saleor/product/tests",
        "saleor/graphql/product/tests",
        "saleor/graphql/checkout/tests",
        "saleor/graphql/order/tests",
        "saleor/webhook/tests",
    }
    assert set(saleor.services) == {"postgresql", "valkey"}
    env = saleor.env_dict()
    assert env["DATABASE_URL"].startswith("postgres://")
    assert env["CACHE_URL"].startswith("redis://")
    assert len(saleor.additional_commands) >= 1
    migration_check = saleor.additional_commands[0]
    assert "makemigrations" in migration_check


def test_require_fails_closed_on_unknown_repository(
    command_map: ValidationCommandMap,
) -> None:
    with pytest.raises(RepositoryError):
        command_map.require("unknown-repo")
    assert resolve_validation_command(
        command_map, "unknown-repo", FAKE_PYTHON, required=False
    ) is None


def test_resolver_has_no_break_in_validation_block() -> None:
    """Defect 1: the validation resolver must not stop after the first repo."""
    source = BENCHMARK_SCRIPT.read_text(encoding="utf-8")
    block_start = source.index("# ---- Resolve validation command per repository")
    block_end = source.index("# ---- Resolve canonical active snapshot per repository")
    block = source[block_start:block_end]
    assert "break" not in block, (
        "validation resolver must not contain a single-repository break"
    )


def test_loader_fails_closed_on_missing_command(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "protocol_version": "1.0",
                "repositories": {
                    "todo": {
                        "scenario_ids": ["todo-loc-001"],
                        "command": [],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RepositoryError):
        load_validation_commands(path)


def test_loader_fails_closed_on_unknown_shape(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("repositories: 42\n", encoding="utf-8")
    with pytest.raises(RepositoryError):
        load_validation_commands(path)


def test_loader_fails_closed_when_manifest_missing(tmp_path: Path) -> None:
    with pytest.raises(RepositoryError):
        load_validation_commands(tmp_path / "does-not-exist.yaml")


def test_frozen_command_dataclass_rejects_empty_command() -> None:
    with pytest.raises(ValueError):
        FrozenValidationCommand(
            repo_id="todo",
            scenario_ids=("todo-loc-001",),
            dependency_runtime="benchmark",
            dependency_file="",
            services=(),
            env=(),
            command=(),
            additional_commands=(),
            description="",
        )
