from __future__ import annotations

from typing import Any

from benchmark.core.exceptions import BenchmarkError, DuplicateRegistrationError, UnknownRegistrationError
from benchmark.core.protocols import ImpactStrategy


class StrategyRegistry:
    """Registry for ImpactStrategy implementations."""

    def __init__(self) -> None:
        self._strategies: dict[str, type[ImpactStrategy]] = {}
        self._frozen = False

    def register(self, name: str, strategy_cls: type[ImpactStrategy]) -> None:
        if self._frozen:
            raise BenchmarkError(
                "Cannot register on frozen StrategyRegistry",
                context={"name": name},
            )
        if name in self._strategies:
            raise DuplicateRegistrationError(
                f"Strategy '{name}' already registered",
                context={"name": name, "existing": list(self._strategies)},
            )
        self._strategies[name] = strategy_cls

    def create(self, name: str, **kwargs: Any) -> ImpactStrategy:
        if name not in self._strategies:
            raise UnknownRegistrationError(
                f"Unknown strategy: '{name}'",
                context={"name": name, "available": list(self._strategies)},
            )
        return self._strategies[name](**kwargs)

    def get(self, name: str) -> type[ImpactStrategy]:
        if name not in self._strategies:
            raise UnknownRegistrationError(
                f"Unknown strategy: '{name}'",
                context={"name": name, "available": list(self._strategies)},
            )
        return self._strategies[name]

    def contains(self, name: str) -> bool:
        return name in self._strategies

    def list_names(self) -> list[str]:
        return sorted(self._strategies.keys())

    def freeze(self) -> None:
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    def __len__(self) -> int:
        return len(self._strategies)
