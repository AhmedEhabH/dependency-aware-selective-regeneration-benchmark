from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from benchmark.core.exceptions import RepositoryError

_PYTHON_TOKEN = "{python}"


def _validate_command(repo_id: str, label: str, raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list) or not raw:
        raise RepositoryError(
            f"{label} for repository '{repo_id}' must be a non-empty list of "
            f"argv tokens, got {raw!r}"
        )
    for token in raw:
        if not isinstance(token, str) or not token:
            raise RepositoryError(
                f"{label} for repository '{repo_id}' contains an invalid "
                f"token: {token!r}"
            )
    return tuple(raw)


def _validate_env(repo_id: str, raw: Any) -> tuple[tuple[str, str], ...]:
    if raw is None:
        return ()
    if not isinstance(raw, dict):
        raise RepositoryError(
            f"env for repository '{repo_id}' must be a mapping, got {type(raw).__name__}"
        )
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise RepositoryError(
                f"env for repository '{repo_id}' must map str -> str, got "
                f"{key!r}: {value!r}"
            )
    return tuple(sorted(raw.items()))


@dataclass(frozen=True)
class FrozenValidationCommand:
    """One repository's frozen baseline validation contract.

    ``command`` is the primary argv used by the Pilot runner for per-cell
    baseline validation. ``additional_commands`` are proven by the engineering
    preflight but are not part of the per-cell baseline validation argv.
    """

    repo_id: str
    scenario_ids: tuple[str, ...]
    dependency_runtime: str
    dependency_file: str
    services: tuple[str, ...]
    env: tuple[tuple[str, str], ...]
    command: tuple[str, ...]
    additional_commands: tuple[tuple[str, ...], ...]
    description: str

    def __post_init__(self) -> None:
        if not self.repo_id:
            raise ValueError("FrozenValidationCommand.repo_id must not be empty")
        if not self.scenario_ids:
            raise ValueError(
                f"FrozenValidationCommand({self.repo_id}).scenario_ids must "
                "not be empty"
            )
        if not self.command:
            raise ValueError(
                f"FrozenValidationCommand({self.repo_id}).command must not be empty"
            )
        if any(not cmd for cmd in self.additional_commands):
            raise ValueError(
                f"FrozenValidationCommand({self.repo_id}) has an empty "
                "additional_command"
            )
        if _PYTHON_TOKEN not in self.command and not any(
            _PYTHON_TOKEN in cmd for cmd in self.additional_commands
        ):
            raise ValueError(
                f"FrozenValidationCommand({self.repo_id}).command must use "
                f"the '{_PYTHON_TOKEN}' interpreter token"
            )

    def env_dict(self) -> dict[str, str]:
        return dict(self.env)

    def resolve_interpreter(self, python: str) -> tuple[str, ...]:
        if not python:
            raise ValueError(
                f"cannot resolve '{_PYTHON_TOKEN}' for '{self.repo_id}': "
                "empty interpreter"
            )
        return tuple(python if token == _PYTHON_TOKEN else token for token in self.command)

    def resolved_additional_commands(self, python: str) -> tuple[tuple[str, ...], ...]:
        return tuple(
            tuple(python if token == _PYTHON_TOKEN else token for token in cmd)
            for cmd in self.additional_commands
        )


@dataclass(frozen=True)
class ValidationCommandMap:
    commands: Mapping[str, FrozenValidationCommand]

    def __post_init__(self) -> None:
        if not self.commands:
            raise ValueError("ValidationCommandMap must not be empty")

    def get(self, repo_id: str) -> FrozenValidationCommand | None:
        return self.commands.get(repo_id)

    def require(self, repo_id: str) -> FrozenValidationCommand:
        command = self.commands.get(repo_id)
        if command is None:
            raise RepositoryError(
                "no frozen validation command mapped for repository "
                f"'{repo_id}' (Pilot requires todo, djangocms and saleor)",
                context={"repo_id": repo_id},
            )
        return command

    def repo_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.commands))


def load_validation_commands(path: str | Path) -> ValidationCommandMap:
    """Load and strictly validate the frozen validation-commands manifest.

    Fails closed on any structural defect so the Pilot never runs with a
    partial or permissive validation contract.
    """
    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise RepositoryError(
            f"validation commands manifest not found: {manifest_path}"
        )
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except OSError as e:
        raise RepositoryError(
            f"failed to read validation commands manifest: {e}",
            context={"path": str(manifest_path)},
        ) from e
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise RepositoryError(
            f"failed to parse validation commands manifest: {e}",
            context={"path": str(manifest_path)},
        ) from e
    if not isinstance(data, dict):
        raise RepositoryError(
            "validation commands manifest must be a mapping, got "
            f"{type(data).__name__}"
        )
    repositories = data.get("repositories")
    if not isinstance(repositories, dict) or not repositories:
        raise RepositoryError(
            "validation commands manifest must contain a non-empty "
            "'repositories' mapping"
        )

    commands: dict[str, FrozenValidationCommand] = {}
    for repo_id, entry in repositories.items():
        if not isinstance(entry, dict):
            raise RepositoryError(f"repository '{repo_id}' entry must be a mapping")
        scenario_ids = entry.get("scenario_ids")
        if not isinstance(scenario_ids, list) or not all(
            isinstance(sid, str) and sid for sid in scenario_ids
        ):
            raise RepositoryError(
                f"repository '{repo_id}' scenario_ids must be a non-empty "
                "list of strings"
            )
        raw_additional = entry.get("additional_commands", [])
        if not isinstance(raw_additional, list):
            raise RepositoryError(
                f"repository '{repo_id}' additional_commands must be a list"
            )
        additional: list[tuple[str, ...]] = []
        for item in raw_additional:
            if isinstance(item, dict):
                additional.append(_validate_command(repo_id, "additional command", item.get("command")))
            elif isinstance(item, list):
                additional.append(_validate_command(repo_id, "additional command", item))
            else:
                raise RepositoryError(
                    f"repository '{repo_id}' additional command must be a "
                    f"list, got {item!r}"
                )
        dependency_file = entry.get("dependency_file", "")
        if not isinstance(dependency_file, str):
            raise RepositoryError(
                f"repository '{repo_id}' dependency_file must be a string"
            )
        services = entry.get("services", [])
        if not isinstance(services, list) or not all(
            isinstance(svc, str) for svc in services
        ):
            raise RepositoryError(
                f"repository '{repo_id}' services must be a list of strings"
            )
        description = entry.get("description", "")
        if not isinstance(description, str):
            raise RepositoryError(
                f"repository '{repo_id}' description must be a string"
            )
        commands[repo_id] = FrozenValidationCommand(
            repo_id=repo_id,
            scenario_ids=tuple(scenario_ids),
            dependency_runtime=entry.get("dependency_runtime", ""),
            dependency_file=dependency_file,
            services=tuple(services),
            env=_validate_env(repo_id, entry.get("env")),
            command=_validate_command(repo_id, "command", entry.get("command")),
            additional_commands=tuple(additional),
            description=description,
        )
    return ValidationCommandMap(commands=commands)


def resolve_validation_command(
    commands: ValidationCommandMap,
    repo_id: str,
    python: str,
    *,
    required: bool = True,
) -> tuple[str, ...] | None:
    """Resolve ``repo_id``'s frozen command with ``python`` substituted.

    Returns ``None`` when the repository has no frozen command and
    ``required=False``. Raises ``RepositoryError`` otherwise.
    """
    if required:
        return commands.require(repo_id).resolve_interpreter(python)
    command = commands.get(repo_id)
    if command is None:
        return None
    return command.resolve_interpreter(python)
