from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from benchmark.core.enums import EvidenceTier
from benchmark.core.models import Budget, RepositoryIdentity


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class ExecutionContext:
    protocol_version: str
    run_id: str
    repository_identity: RepositoryIdentity
    scenario_id: str
    strategy_name: str
    backend_name: str
    working_directory: str
    public_data_paths: tuple[str, ...]
    private_evaluation_access: bool = False
    random_seed: int = 0
    budget: Budget = field(default_factory=Budget)
    start_timestamp: datetime = field(default_factory=_utc_now)
    evidence_tier: EvidenceTier = EvidenceTier.engineering_validation
    publication_eligible: bool = False

    def __post_init__(self) -> None:
        if not self.protocol_version:
            raise ValueError("ExecutionContext.protocol_version must not be empty")
        if not self.run_id:
            raise ValueError("ExecutionContext.run_id must not be empty")

    def update_budget(self, budget: Budget) -> None:
        object.__setattr__(self, "budget", budget)

    def update_random_seed(self, seed: int) -> None:
        object.__setattr__(self, "random_seed", seed)
