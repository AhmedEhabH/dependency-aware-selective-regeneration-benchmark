"""Versioned experiment spec (V1).

An :class:`ExperimentSpec` is a frozen, hashable description of one study: the
dataset, the method, the model/provider configuration, the K grid, the allowed
splits, the seed, and the explicit budget. Identical config must produce an
identical SHA-256 (config reproducibility).

Model and provider names are CONFIGURATION, never algorithm branches.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .interfaces import BudgetPolicy

SPEC_SCHEMA_VERSION: str = "harness-experiment-spec-v1"


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_of(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExperimentSpec:
    """Frozen description of one experiment through the harness."""

    spec_id: str
    protocol_version: str
    dataset_name: str
    repository: str
    method_name: str
    model_name: str
    provider: str
    k_values: tuple[int, ...]
    splits_allowed: tuple[str, ...]
    seed: int
    budget: BudgetPolicy
    spec_schema_version: str = SPEC_SCHEMA_VERSION
    frozen_rules: tuple[str, ...] = ()
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "spec_schema_version": self.spec_schema_version,
            "spec_id": self.spec_id,
            "protocol_version": self.protocol_version,
            "dataset_name": self.dataset_name,
            "repository": self.repository,
            "method_name": self.method_name,
            "model_name": self.model_name,
            "provider": self.provider,
            "k_values": list(self.k_values),
            "splits_allowed": list(self.splits_allowed),
            "seed": self.seed,
            "budget": self.budget.to_dict(),
            "frozen_rules": list(self.frozen_rules),
            "notes": self.notes,
        }

    @property
    def sha256(self) -> str:
        """Deterministic config hash (config reproducibility)."""
        return sha256_of(self.to_dict())

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ExperimentSpec:
        return cls(
            spec_id=str(payload["spec_id"]),
            protocol_version=str(payload["protocol_version"]),
            dataset_name=str(payload["dataset_name"]),
            repository=str(payload["repository"]),
            method_name=str(payload["method_name"]),
            model_name=str(payload["model_name"]),
            provider=str(payload["provider"]),
            k_values=tuple(int(k) for k in payload["k_values"]),
            splits_allowed=tuple(str(s) for s in payload["splits_allowed"]),
            seed=int(payload["seed"]),
            budget=BudgetPolicy.from_dict(payload["budget"]),
            spec_schema_version=str(
                payload.get("spec_schema_version", SPEC_SCHEMA_VERSION)
            ),
            frozen_rules=tuple(str(r) for r in payload.get("frozen_rules", ())),
            notes=str(payload.get("notes", "")),
        )


def load_spec(path: str) -> ExperimentSpec:
    """Load a spec from a JSON file (persisted spec)."""
    with open(path, encoding="utf-8") as fh:
        return ExperimentSpec.from_dict(json.load(fh))


def dump_spec(spec: ExperimentSpec, path: str) -> None:
    """Persist a spec to a JSON file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(spec.to_dict(), fh, indent=2, ensure_ascii=False)
        fh.write("\n")
