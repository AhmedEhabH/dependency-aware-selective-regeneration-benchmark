"""Pluggable research harness — seam interfaces (V1).

This module defines the *minimal* generalization seams for the research
harness. It deliberately does NOT build a universal plugin framework: each seam
is a Python ABC plus configuration that names concrete implementations. Frozen
historical generators and artifacts are never rewritten; this package ADAPTS
them.

Seams:

- :class:`DatasetAdapter`       — per-repository dataset access (public case
                                 bundle + evaluation-only hidden proxy).
- :class:`SnapshotProvider`     — RepositoryView: parent-commit snapshot /
                                 corpus text for a case.
- :class:`Ranker`               — selection method that ranks candidate paths.
- :class:`Planner`              — selection method that emits a structured
                                 plan (future LLM planners).
- :class:`ModelBackend`         — model/provider access. Provider and model
                                 names are CONFIG, never algorithm branches.
- :class:`RiskScorer`           — INTERFACE ONLY in V1 (omission-risk study).
- :class:`Verifier`             — INTERFACE ONLY in V1 (future verifier).
- :class:`BudgetPolicy`         — explicit, persisted, enforced budget.

Leakage rule (hard): method code (Ranker/Planner) receives ONLY the public
case bundle. The hidden observed-change proxy is loaded by the dataset adapter
and passed exclusively to the evaluator after ranking.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, ClassVar, final

CandidateRecord = dict[str, Any]


# ---------------------------------------------------------------------------
# Public data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PublicCase:
    """Parent-visible inputs for ONE task (never the hidden proxy)."""

    case_id: str
    repository: str
    repository_url: str
    parent_commit: str
    target_commit: str
    intent_text: str
    candidate_paths: tuple[str, ...]
    candidate_records: tuple[CandidateRecord, ...]
    graph_edges: tuple[tuple[str, str], ...]
    public_bundle_sha256: str


@dataclass(frozen=True)
class CandidateSnapshot:
    """Parent-commit snapshot / corpus representation for one case."""

    source: str
    parent_commit: str
    texts: dict[str, str]
    sha256: str = field(default="")


@dataclass(frozen=True)
class RankedPrediction:
    """Deterministic ranked output of a Ranker for one case at one K."""

    method: str
    case_id: str
    k: int
    ranked_paths: tuple[str, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def selected_paths(self) -> tuple[str, ...]:
        return self.ranked_paths[: self.k]


@dataclass(frozen=True)
class PlanPrediction:
    """Structured plan output of a Planner for one case."""

    method: str
    case_id: str
    selected_paths: tuple[str, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Dataset adapter
# ---------------------------------------------------------------------------


class DatasetAdapter(abc.ABC):
    """Per-repository dataset access.

    django-specific rules live in the django adapter
    (:mod:`benchmark.harness.djangocms`); future Saleor-specific rules live in
    a Saleor adapter (:mod:`benchmark.harness.saleor`). Method code consumes
    only :meth:`load_public_case`; the hidden proxy is evaluation-only.
    """

    name: ClassVar[str] = ""
    splits_allowed: ClassVar[tuple[str, ...]] = ()

    @abc.abstractmethod
    def case_ids(self) -> tuple[str, ...]:
        """Case ids the adapter may process (split-filtered, sorted)."""

    @abc.abstractmethod
    def split_of(self, case_id: str) -> str:
        """Return the split label of a case; fail closed on unknown."""

    @abc.abstractmethod
    def load_public_case(self, case_id: str) -> PublicCase:
        """Load the parent-only public bundle for a case."""

    @abc.abstractmethod
    def load_hidden_proxy_paths(self, case_id: str) -> tuple[str, ...]:
        """Load the evaluation-only observed-change proxy paths.

        MUST never be passed to a Ranker/Planner. Callers are the evaluator and
        the runner's scoring step only.
        """


# ---------------------------------------------------------------------------
# Repository view / snapshot provider
# ---------------------------------------------------------------------------


class SnapshotProvider(abc.ABC):
    """RepositoryView: builds a parent-commit snapshot for a case."""

    name: ClassVar[str] = ""

    @abc.abstractmethod
    def snapshot(self, case: PublicCase) -> CandidateSnapshot:
        """Build the parent-commit snapshot for one case.

        The snapshot is a pure function of parent-visible repository state.
        """


# ---------------------------------------------------------------------------
# Selection methods (rankers / planners)
# ---------------------------------------------------------------------------


class Ranker(abc.ABC):
    """A selection method that ranks candidate paths for a case.

    Contract: may read ONLY the public case bundle and the parent snapshot.
    Must be deterministic given the same inputs and a frozen seed.
    """

    name: ClassVar[str] = ""

    @abc.abstractmethod
    def rank(
        self,
        *,
        case: PublicCase,
        snapshot: CandidateSnapshot | None,
        k: int,
    ) -> RankedPrediction:
        """Rank candidate paths; return top-K as :attr:`RankedPrediction.ranked_paths`."""


class Planner(abc.ABC):
    """A selection method that emits a structured plan for a case.

    V1 provides the seam; the frozen LLM planners remain in their own frozen
    modules. A planner may read ONLY the public case bundle and parent snapshot.
    """

    name: ClassVar[str] = ""

    @abc.abstractmethod
    def plan(
        self,
        *,
        case: PublicCase,
        snapshot: CandidateSnapshot | None,
    ) -> PlanPrediction:
        """Emit a plan (selected paths) for the case."""


# ---------------------------------------------------------------------------
# Model backend
# ---------------------------------------------------------------------------


class ModelBackend(abc.ABC):
    """Model/provider access.

    Provider and model names are configuration, never algorithm branches.
    Concrete backends are selected by name from configuration
    (:mod:`benchmark.harness.registry`).
    """

    name: ClassVar[str] = ""
    model_name: ClassVar[str] = ""
    provider: ClassVar[str] = ""

    @abc.abstractmethod
    def complete(self, *, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Complete a prompt; returns a dict with at least ``text``.

        Must record ``llm_calls``/``tokens`` counters for budget enforcement.
        """

    @property
    @abc.abstractmethod
    def llm_calls(self) -> int:
        """Cumulative model calls made by this backend."""

    @property
    @abc.abstractmethod
    def llm_tokens(self) -> int:
        """Cumulative tokens consumed by this backend."""


# ---------------------------------------------------------------------------
# Interface-only seams (V1)
# ---------------------------------------------------------------------------


class RiskScorer(abc.ABC):
    """Omission-risk scorer — INTERFACE ONLY in V1.

    No concrete scientific implementation exists in this milestone. This seam
    exists so the Omission-Risk Feature Study v1 can be prepared without
    touching frozen machinery. Hidden gold must never be an input.
    """

    name: ClassVar[str] = ""

    @abc.abstractmethod
    def score(
        self,
        *,
        case: PublicCase,
        prediction: RankedPrediction | PlanPrediction,
    ) -> float:
        """Return a risk score in [0, 1] (higher = more omission risk)."""


class Verifier(abc.ABC):
    """Bounded false-negative verifier — INTERFACE ONLY in V1.

    No concrete scientific implementation exists in this milestone. The seam
    reserves the escalation target for the selective-escalation pipeline.
    """

    name: ClassVar[str] = ""

    @abc.abstractmethod
    def verify(
        self,
        *,
        case: PublicCase,
        prediction: RankedPrediction | PlanPrediction,
        budget: BudgetPolicy,
    ) -> dict[str, Any]:
        """Verify a prediction under an explicit budget; returns evidence dict."""


# ---------------------------------------------------------------------------
# Budget policy
# ---------------------------------------------------------------------------


@final
@dataclass(frozen=True)
class BudgetPolicy:
    """Explicit, persisted, enforced budget for a study.

    All fields are optional (None = no bound). ``zero_llm`` is the Protocol-A
    marker: when True, any model call raises :class:`BudgetExceededError`.
    """

    max_llm_calls: int | None = None
    max_llm_tokens: int | None = None
    max_estimated_cost_usd: float | None = None
    max_wallclock_seconds: float | None = None
    zero_llm: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_llm_calls": self.max_llm_calls,
            "max_llm_tokens": self.max_llm_tokens,
            "max_estimated_cost_usd": self.max_estimated_cost_usd,
            "max_wallclock_seconds": self.max_wallclock_seconds,
            "zero_llm": self.zero_llm,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> BudgetPolicy:
        return cls(
            max_llm_calls=payload.get("max_llm_calls"),
            max_llm_tokens=payload.get("max_llm_tokens"),
            max_estimated_cost_usd=payload.get("max_estimated_cost_usd"),
            max_wallclock_seconds=payload.get("max_wallclock_seconds"),
            zero_llm=bool(payload.get("zero_llm", True)),
        )

    def check_llm(
        self,
        *,
        calls: int,
        tokens: int,
        estimated_cost_usd: float = 0.0,
    ) -> None:
        """Raise :class:`BudgetExceededError` if LLM usage exceeds the policy."""
        if self.zero_llm and calls > 0:
            raise BudgetExceededError(
                f"zero_llm budget violated: {calls} model calls made"
            )
        if self.max_llm_calls is not None and calls > self.max_llm_calls:
            raise BudgetExceededError(
                f"llm call budget exceeded: {calls} > {self.max_llm_calls}"
            )
        if self.max_llm_tokens is not None and tokens > self.max_llm_tokens:
            raise BudgetExceededError(
                f"llm token budget exceeded: {tokens} > {self.max_llm_tokens}"
            )
        if (
            self.max_estimated_cost_usd is not None
            and estimated_cost_usd > self.max_estimated_cost_usd
        ):
            raise BudgetExceededError(
                f"cost budget exceeded: {estimated_cost_usd} > "
                f"{self.max_estimated_cost_usd}"
            )


class BudgetExceededError(RuntimeError):
    """Raised when an explicit budget is exceeded."""


class HiddenGoldAccessError(RuntimeError):
    """Raised when hidden proxy data is passed to method code."""
