"""Pluggable research harness V1.

Minimal generalization of the research harness through explicit seams:
DatasetAdapter, SnapshotProvider (RepositoryView), Ranker, Planner,
ModelBackend, RiskScorer (interface only), Verifier (interface only),
BudgetPolicy, common Evaluator, versioned ExperimentSpec.

Frozen historical generators and artifacts are NEVER rewritten; this package
adapts them (see :mod:`benchmark.harness.protocol_a` for the Protocol-A
compatibility layer).
"""

from __future__ import annotations

from . import backends, djangocms, registry, saleor  # noqa: F401  (registration)
from .evaluator import COMMON_EVALUATOR_VERSION
from .interfaces import (
    BudgetExceededError,
    BudgetPolicy,
    CandidateSnapshot,
    DatasetAdapter,
    HiddenGoldAccessError,
    ModelBackend,
    Planner,
    PlanPrediction,
    PublicCase,
    RankedPrediction,
    Ranker,
    RiskScorer,
    SnapshotProvider,
    Verifier,
)
from .spec import SPEC_SCHEMA_VERSION, ExperimentSpec

__all__ = [
    "BudgetPolicy",
    "BudgetExceededError",
    "CandidateSnapshot",
    "COMMON_EVALUATOR_VERSION",
    "DatasetAdapter",
    "ExperimentSpec",
    "HiddenGoldAccessError",
    "ModelBackend",
    "PlanPrediction",
    "Planner",
    "PublicCase",
    "RankedPrediction",
    "Ranker",
    "RiskScorer",
    "SPEC_SCHEMA_VERSION",
    "SnapshotProvider",
    "Verifier",
]
