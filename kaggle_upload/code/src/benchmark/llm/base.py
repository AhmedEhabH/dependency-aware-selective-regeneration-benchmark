from __future__ import annotations

from benchmark.core.protocols import LLMBackend
from benchmark.core.registry import Registry


class BackendFactory:
    def __init__(self) -> None:
        self._registry: Registry[LLMBackend] = Registry()

    def register(self, name: str, backend_cls: type[LLMBackend]) -> None:
        self._registry.register(name, backend_cls)

    def create(self, name: str, **kwargs: object) -> LLMBackend:
        return self._registry.create(name, **kwargs)

    def list_names(self) -> list[str]:
        return self._registry.list_names()

    def freeze(self) -> None:
        self._registry.freeze()

    @property
    def is_frozen(self) -> bool:
        return self._registry.is_frozen

    def __contains__(self, name: str) -> bool:
        return name in self._registry

    def __len__(self) -> int:
        return len(self._registry)
