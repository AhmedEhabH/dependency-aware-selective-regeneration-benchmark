from __future__ import annotations

from pathlib import Path

import yaml

from benchmark.config.models import BenchmarkConfig
from benchmark.core.exceptions import ConfigurationError


def load_config(path: str | Path) -> BenchmarkConfig:
    path = Path(path)
    if not path.exists():
        raise ConfigurationError(f"Config file not found: {path}")
    if not path.is_file():
        raise ConfigurationError(f"Config path is not a file: {path}")

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigurationError(f"Failed to read config file: {e}", context={"path": str(path)}) from e

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise ConfigurationError(
            f"Failed to parse YAML config: {e}",
            context={"path": str(path)},
        ) from e

    if not isinstance(data, dict):
        raise ConfigurationError(
            f"Config must be a YAML mapping, got {type(data).__name__}",
            context={"path": str(path)},
        )

    try:
        return BenchmarkConfig(**data)
    except Exception as e:
        raise ConfigurationError(
            f"Config validation failed: {e}",
            context={"path": str(path)},
        ) from e
