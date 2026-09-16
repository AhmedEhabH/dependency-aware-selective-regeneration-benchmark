"""RiskScorer / Verifier interface-only tests (ZERO API).

V1 must NOT provide any concrete scientific risk scorer or verifier: the
omission-risk feature study is the next scientific step and is not started
here. These tests prove the seams are interface-only and cannot be invoked
silently.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.harness import interfaces, registry

DATASET_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "benchmark_data"
    / "real_commit_impact_v1"
)


def test_no_concrete_risk_scorer_registered() -> None:
    assert registry.known_names()["risk_scorers"] == []


def test_no_concrete_verifier_registered() -> None:
    assert registry.known_names()["verifiers"] == []


def test_risk_scorer_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        interfaces.RiskScorer()  # type: ignore[abstract]


def test_verifier_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        interfaces.Verifier()  # type: ignore[abstract]


def test_risk_scorer_method_signature_contract() -> None:
    import inspect

    sig = inspect.signature(interfaces.RiskScorer.score)
    params = list(sig.parameters)
    assert "case" in params
    assert "prediction" in params


def test_verifier_method_signature_contract() -> None:
    import inspect

    sig = inspect.signature(interfaces.Verifier.verify)
    params = list(sig.parameters)
    assert "case" in params
    assert "prediction" in params
    assert "budget" in params
