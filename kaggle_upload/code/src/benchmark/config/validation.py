from __future__ import annotations

from benchmark.config.models import BenchmarkConfig
from benchmark.core.exceptions import ValidationError


def validate_config(config: BenchmarkConfig) -> list[str]:
    errors: list[str] = []

    if not config.strategies:
        errors.append("At least one strategy must be configured")

    if not config.backends:
        errors.append("At least one backend must be configured")

    if not config.repositories:
        errors.append("At least one repository must be configured")

    backend_names = {b.name for b in config.backends}
    for strategy in config.strategies:
        if strategy.llm_backend is not None and strategy.llm_backend not in backend_names:
            errors.append(
                f"Strategy '{strategy.name}' references unknown backend '{strategy.llm_backend}'"
            )

    if errors:
        raise ValidationError("Config validation failed", context={"errors": errors})

    return errors
