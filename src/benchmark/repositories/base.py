from __future__ import annotations

from abc import ABC, abstractmethod

from benchmark.core.models import RepositoryIdentity, RepositorySnapshot


class RepositoryLoaderBase(ABC):
    @abstractmethod
    def resolve_identity(self, repo_id: str) -> RepositoryIdentity:
        ...

    @abstractmethod
    def resolve_snapshot(self, repo_id: str) -> RepositorySnapshot:
        ...
