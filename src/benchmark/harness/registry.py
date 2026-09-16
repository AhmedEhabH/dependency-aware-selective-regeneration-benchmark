"""Registry — name -> implementation resolution.

Config names concrete implementations; no algorithm branch lives in method
code. Registry population is explicit and lazy-free (import-time registration).
"""

from __future__ import annotations

from typing import TypeVar

from . import interfaces

T = TypeVar("T")

_DATASETS: dict[str, type[interfaces.DatasetAdapter]] = {}
_SNAPSHOTS: dict[str, type[interfaces.SnapshotProvider]] = {}
_RANKERS: dict[str, type[interfaces.Ranker]] = {}
_PLANNERS: dict[str, type[interfaces.Planner]] = {}
_BACKENDS: dict[str, type[interfaces.ModelBackend]] = {}
_RISK_SCORERS: dict[str, type[interfaces.RiskScorer]] = {}
_VERIFIERS: dict[str, type[interfaces.Verifier]] = {}


def register_dataset(cls: type[interfaces.DatasetAdapter]) -> type[interfaces.DatasetAdapter]:
    assert cls.name, f"{cls!r} must define a non-empty 'name'"
    _DATASETS[cls.name] = cls
    return cls


def register_snapshot(
    cls: type[interfaces.SnapshotProvider],
) -> type[interfaces.SnapshotProvider]:
    assert cls.name, f"{cls!r} must define a non-empty 'name'"
    _SNAPSHOTS[cls.name] = cls
    return cls


def register_ranker(cls: type[interfaces.Ranker]) -> type[interfaces.Ranker]:
    assert cls.name, f"{cls!r} must define a non-empty 'name'"
    _RANKERS[cls.name] = cls
    return cls


def register_planner(cls: type[interfaces.Planner]) -> type[interfaces.Planner]:
    assert cls.name, f"{cls!r} must define a non-empty 'name'"
    _PLANNERS[cls.name] = cls
    return cls


def register_backend(
    cls: type[interfaces.ModelBackend],
) -> type[interfaces.ModelBackend]:
    assert cls.name, f"{cls!r} must define a non-empty 'name'"
    _BACKENDS[cls.name] = cls
    return cls


def register_risk_scorer(
    cls: type[interfaces.RiskScorer],
) -> type[interfaces.RiskScorer]:
    assert cls.name, f"{cls!r} must define a non-empty 'name'"
    _RISK_SCORERS[cls.name] = cls
    return cls


def register_verifier(
    cls: type[interfaces.Verifier],
) -> type[interfaces.Verifier]:
    assert cls.name, f"{cls!r} must define a non-empty 'name'"
    _VERIFIERS[cls.name] = cls
    return cls


def _resolve(store: dict[str, type[T]], name: str, kind: str) -> type[T]:
    if name not in store:
        raise KeyError(f"unknown {kind} name {name!r}; known: {sorted(store)}")
    return store[name]


def resolve_dataset(name: str) -> type[interfaces.DatasetAdapter]:
    return _resolve(_DATASETS, name, "dataset")


def resolve_snapshot(name: str) -> type[interfaces.SnapshotProvider]:
    return _resolve(_SNAPSHOTS, name, "snapshot provider")


def resolve_ranker(name: str) -> type[interfaces.Ranker]:
    return _resolve(_RANKERS, name, "ranker")


def resolve_planner(name: str) -> type[interfaces.Planner]:
    return _resolve(_PLANNERS, name, "planner")


def resolve_backend(name: str) -> type[interfaces.ModelBackend]:
    return _resolve(_BACKENDS, name, "model backend")


def resolve_risk_scorer(name: str) -> type[interfaces.RiskScorer]:
    return _resolve(_RISK_SCORERS, name, "risk scorer")


def resolve_verifier(name: str) -> type[interfaces.Verifier]:
    return _resolve(_VERIFIERS, name, "verifier")


def known_names() -> dict[str, list[str]]:
    return {
        "datasets": sorted(_DATASETS),
        "snapshots": sorted(_SNAPSHOTS),
        "rankers": sorted(_RANKERS),
        "planners": sorted(_PLANNERS),
        "backends": sorted(_BACKENDS),
        "risk_scorers": sorted(_RISK_SCORERS),
        "verifiers": sorted(_VERIFIERS),
    }
