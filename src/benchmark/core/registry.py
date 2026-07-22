from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar

from benchmark.core.exceptions import DuplicateRegistrationError, UnknownRegistrationError

T = TypeVar("T")


class Registry(Generic[T]):
    def __init__(self) -> None:
        self._entries: dict[str, Callable[..., T] | type[T]] = {}
        self._frozen: bool = False

    def register(self, name: str, entry: Callable[..., T] | type[T]) -> None:
        if self._frozen:
            raise RuntimeError(f"Cannot register '{name}': registry is frozen")
        if name in self._entries:
            raise DuplicateRegistrationError(
                f"Duplicate registration: '{name}'",
                context={"name": name},
            )
        self._entries[name] = entry

    def create(self, name: str, **kwargs: Any) -> T:
        entry = self._entries.get(name)
        if entry is None:
            raise UnknownRegistrationError(
                f"Unknown registration: '{name}'",
                context={"name": name, "available": list(self._entries.keys())},
            )
        return entry(**kwargs)

    def get(self, name: str) -> Callable[..., T] | type[T]:
        entry = self._entries.get(name)
        if entry is None:
            raise UnknownRegistrationError(
                f"Unknown registration: '{name}'",
                context={"name": name, "available": list(self._entries.keys())},
            )
        return entry

    def list_names(self) -> list[str]:
        return list(self._entries.keys())

    def freeze(self) -> None:
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    def __contains__(self, name: str) -> bool:
        return name in self._entries

    def __len__(self) -> int:
        return len(self._entries)
