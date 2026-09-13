"""RealCommitImpactDataset-v1 miner package (M4A-1).

Deterministic, auditable mining of real historical djangoCMS commits. ZERO
scientific LLM/API calls. The observed changed-file set is an OBSERVED
CHANGE-SET PROXY, never semantic P/R/V/H ground truth.
"""

from __future__ import annotations

from benchmark.real_commits.models import (
    MINER_VERSION,
    SCHEMA_VERSION,
    SplitRole,
)

__all__ = [
    "MINER_VERSION",
    "SCHEMA_VERSION",
    "SplitRole",
]
