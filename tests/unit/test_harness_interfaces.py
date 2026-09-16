"""Interface contract tests for the pluggable research harness (ZERO API).

Proves the seams exist with the documented contracts:
- every seam is an ABC with the required abstract methods;
- BudgetPolicy is frozen / explicit / serializable;
- ExperimentSpec is versioned, frozen, and hashable;
- the registry resolves the V1 concrete implementations by name.
"""

from __future__ import annotations

import abc
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from benchmark.harness import interfaces, registry
from benchmark.harness.backends import MockBackend, NoneBackend
from benchmark.harness.djangocms import (
    DjangoCMSParentSnapshot,
    DjangoCMSRealCommitDataset,
    FrozenBM25Ranker,
    FrozenGraphRanker,
    FrozenHybridRanker,
    FrozenPathTokenRanker,
    FrozenRandomRanker,
)
from benchmark.harness.interfaces import BudgetPolicy
from benchmark.harness.protocol_a import (
    FROZEN_K_VALUES,
    build_protocol_a_spec,
)
from benchmark.harness.spec import ExperimentSpec, dump_spec, load_spec

DATASET_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "benchmark_data"
    / "real_commit_impact_v1"
)


# ---------------------------------------------------------------------------
# Seam existence + abstractness
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cls,methods",
    [
        (interfaces.DatasetAdapter, {"case_ids", "split_of", "load_public_case", "load_hidden_proxy_paths"}),
        (interfaces.SnapshotProvider, {"snapshot"}),
        (interfaces.Ranker, {"rank"}),
        (interfaces.Planner, {"plan"}),
        (interfaces.ModelBackend, {"complete"}),
        (interfaces.RiskScorer, {"score"}),
        (interfaces.Verifier, {"verify"}),
    ],
)
def test_seam_is_abstract_with_required_methods(cls: type, methods: set[str]) -> None:
    assert abc.ABC in cls.__mro__
    abstract = set(getattr(cls, "__abstractmethods__", ()))
    assert methods <= abstract


def test_risk_scorer_and_verifier_are_interface_only() -> None:
    # No concrete subclass is registered in V1; instantiating the ABC fails.
    with pytest.raises(TypeError):
        interfaces.RiskScorer()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        interfaces.Verifier()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# BudgetPolicy
# ---------------------------------------------------------------------------


def test_budget_policy_is_frozen_and_explicit() -> None:
    b = BudgetPolicy(max_llm_calls=10, max_llm_tokens=1000, zero_llm=True)
    with pytest.raises(FrozenInstanceError):
        b.max_llm_calls = 99  # type: ignore[misc]
    assert b.to_dict()["zero_llm"] is True
    restored = BudgetPolicy.from_dict(b.to_dict())
    assert restored == b


def test_budget_zero_llm_fails_on_any_call() -> None:
    b = BudgetPolicy(zero_llm=True)
    with pytest.raises(interfaces.BudgetExceededError):
        b.check_llm(calls=1, tokens=0)


def test_budget_tracks_call_and_token_bounds() -> None:
    b = BudgetPolicy(max_llm_calls=2, max_llm_tokens=100, zero_llm=False)
    b.check_llm(calls=2, tokens=100)
    with pytest.raises(interfaces.BudgetExceededError):
        b.check_llm(calls=3, tokens=100)
    with pytest.raises(interfaces.BudgetExceededError):
        b.check_llm(calls=2, tokens=101)


# ---------------------------------------------------------------------------
# ExperimentSpec — versioned, frozen, reproducible
# ---------------------------------------------------------------------------


def test_spec_is_versioned_frozen_and_hashable() -> None:
    spec = build_protocol_a_spec(method_name="bm25", corpus_mode="metadata")
    assert spec.spec_schema_version.startswith("harness-experiment-spec")
    assert spec.budget.zero_llm is True
    assert spec.k_values == FROZEN_K_VALUES
    with pytest.raises(FrozenInstanceError):
        spec.method_name = "other"  # type: ignore[misc]
    assert len(spec.sha256) == 64


def test_spec_roundtrip_via_json(tmp_path: Path) -> None:
    spec = build_protocol_a_spec(method_name="graph", corpus_mode="metadata")
    path = tmp_path / "spec.json"
    dump_spec(spec, str(path))
    restored = load_spec(str(path))
    assert restored == spec
    assert restored.sha256 == spec.sha256


# ---------------------------------------------------------------------------
# Registry resolution
# ---------------------------------------------------------------------------


def test_registry_resolves_concrete_v1_implementations() -> None:
    assert registry.resolve_dataset("djangocms-real-commit-v1") is DjangoCMSRealCommitDataset
    assert registry.resolve_snapshot("djangocms-parent-snapshot") is DjangoCMSParentSnapshot
    for name, cls in [
        ("random", FrozenRandomRanker),
        ("bm25", FrozenBM25Ranker),
        ("path_token", FrozenPathTokenRanker),
        ("graph", FrozenGraphRanker),
        ("hybrid", FrozenHybridRanker),
    ]:
        assert registry.resolve_ranker(name) is cls
    assert registry.resolve_backend("none") is NoneBackend
    assert registry.resolve_backend("mock") is MockBackend


def test_registry_rejects_unknown_names() -> None:
    with pytest.raises(KeyError):
        registry.resolve_ranker("not-a-ranker")
    with pytest.raises(KeyError):
        registry.resolve_dataset("nope")


# ---------------------------------------------------------------------------
# Saleor seam fails closed
# ---------------------------------------------------------------------------


def test_saleor_seam_fails_closed() -> None:
    from benchmark.harness.saleor import SaleorRealCommitDataset

    with pytest.raises(NotImplementedError):
        SaleorRealCommitDataset()


def test_spec_sha256_is_config_deterministic() -> None:
    s1 = build_protocol_a_spec(method_name="bm25", corpus_mode="metadata")
    s2 = ExperimentSpec.from_dict(json.loads(json.dumps(s1.to_dict())))
    assert s1.sha256 == s2.sha256
