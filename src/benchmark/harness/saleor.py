"""Saleor adapter — FUTURE SEAM (document-only, fail-closed).

Saleor remains the second-repository confirmatory line (roadmap Pillar 7). No
Saleor scientific execution exists in this milestone and none is started here.
This module reserves the seam: Saleor-specific rules (repo identity, candidate
universe semantics, mining rules) belong in THIS adapter and nowhere else.

Scientific use fails closed: instantiating :class:`SaleorRealCommitDataset`
raises :class:`NotImplementedError` until a separate, authorized milestone
freezes Saleor preconditions (see
``docs/SALEOR_CONFIRMATORY_PROTOCOL_DRAFT.md``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from . import interfaces
from .registry import register_dataset, register_snapshot

SALEOR_REPOSITORY: str = "saleor"
SALEOR_REPOSITORY_URL: str = "https://github.com/saleor/saleor"


@register_dataset
@dataclass(frozen=True)
class SaleorRealCommitDataset(interfaces.DatasetAdapter):
    """Future Saleor dataset adapter — NOT available for scientific use.

    The class exists so the harness registry can name it, but every method
    fails closed with :class:`NotImplementedError`. Saleor-specific rules will
    be implemented here in a future, separately-authorized milestone.
    """

    name: ClassVar[str] = "saleor-real-commit-v1"
    splits_allowed: ClassVar[tuple[str, ...]] = ("TRAIN", "VALIDATION")

    dataset_dir: Path = field(default=Path("."))

    def __post_init__(self) -> None:
        if self.dataset_dir == Path("."):
            raise NotImplementedError(
                "SaleorRealCommitDataset is a future seam; Saleor scientific "
                "execution is NOT authorized (see SALEOR_CONFIRMATORY_PROTOCOL_DRAFT.md)"
            )

    def case_ids(self) -> tuple[str, ...]:
        raise NotImplementedError("Saleor scientific execution not authorized")

    def split_of(self, case_id: str) -> str:
        raise NotImplementedError("Saleor scientific execution not authorized")

    def load_public_case(self, case_id: str) -> interfaces.PublicCase:
        raise NotImplementedError("Saleor scientific execution not authorized")

    def load_hidden_proxy_paths(self, case_id: str) -> tuple[str, ...]:
        raise NotImplementedError("Saleor scientific execution not authorized")


@register_snapshot
@dataclass(frozen=True)
class SaleorParentSnapshot(interfaces.SnapshotProvider):
    """Future Saleor snapshot provider — fail-closed in V1."""

    name: ClassVar[str] = "saleor-parent-snapshot"

    def snapshot(self, case: interfaces.PublicCase) -> interfaces.CandidateSnapshot:
        raise NotImplementedError("Saleor scientific execution not authorized")
