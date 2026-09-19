"""OpenRouter embeddings client tests (T3, ZERO network).

The bridge is STOPPED before call 1 (model unavailable on OpenRouter as of
2026-09-19); these tests exercise the frozen request contract through an
injected fake transport only. No network call is made.
"""
from __future__ import annotations

import pytest

from benchmark.signal.or_embeddings import (
    MAX_BATCH_SIZE,
    NoFallbackError,
    OpenRouterEmbeddingsClient,
    SealedDataError,
    assert_not_sealed,
    estimate_requests,
)


def _fake_transport(handler):
    """Return a transport closure whose responses come from `handler(payload)`."""
    def transport(payload):
        return handler(payload)
    return transport


def _ok_body(n):
    return {
        "data": [{"embedding": [0.1 * (i + 1)] * 4, "index": i} for i in range(n)],
        "model": "qwen/qwen3-embedding-8b",
        "usage": {"prompt_tokens": n * 10, "total_tokens": n * 10, "cost": n * 0.0001},
    }


def test_request_format_fixed_model_and_batch():
    seen = {}

    def handler(payload):
        seen.update(payload)
        return 200, _ok_body(len(payload["input"]))

    client = OpenRouterEmbeddingsClient(api_key="k", transport=_fake_transport(handler))
    client.embed(["a", "b", "c"])
    assert seen["model"] == "qwen/qwen3-embedding-8b"
    assert seen["input"] == ["a", "b", "c"]
    assert seen["encoding_format"] == "float"
    assert "api_key" in seen


def test_fixed_model_no_fallback():
    with pytest.raises(NoFallbackError):
        OpenRouterEmbeddingsClient(api_key="k", model="other/model")


def test_batching_deterministic_chunking():
    batches = []

    def handler(payload):
        batches.append(list(payload["input"]))
        return 200, _ok_body(len(payload["input"]))

    client = OpenRouterEmbeddingsClient(api_key="k", batch_size=2,
                                        transport=_fake_transport(handler))
    client.embed([f"x{i}" for i in range(5)])
    assert batches == [["x0", "x1"], ["x2", "x3"], ["x4"]]


def test_duplicate_inputs_rejected():
    def handler(payload):
        return 200, _ok_body(len(payload["input"]))

    client = OpenRouterEmbeddingsClient(api_key="k", transport=_fake_transport(handler))
    with pytest.raises(ValueError):
        client.embed(["same", "same"])


def test_input_hashing():
    client = OpenRouterEmbeddingsClient(api_key="k")
    h1 = client.hash_input("def f():\n    return 1")
    h2 = client.hash_input("def f():\n    return 1")
    h3 = client.hash_input("def f():\n    return 2")
    assert h1 == h2 and len(h1) == 64
    assert h1 != h3


def test_cost_accounting_accumulates():
    def handler(payload):
        return 200, _ok_body(len(payload["input"]))

    client = OpenRouterEmbeddingsClient(api_key="k", batch_size=2,
                                        transport=_fake_transport(handler))
    client.embed([f"q{i}" for i in range(4)])
    assert client.ledger.requests == 2
    assert client.ledger.prompt_tokens == 40
    assert abs(client.ledger.cost_usd - 0.0004) < 1e-9


def test_retry_on_transient_then_success():
    calls = []

    def handler(payload):
        calls.append(1)
        if len(calls) == 1:
            return 503, {"error": {"message": "busy"}}
        return 200, _ok_body(len(payload["input"]))

    client = OpenRouterEmbeddingsClient(api_key="k", max_retries=3,
                                        retry_delay_seconds=0.0,
                                        transport=_fake_transport(handler))
    client.embed(["a"])
    assert client.ledger.transport_retries == 1
    assert client.ledger.permanent_failures == 0
    assert client.ledger.requests == 1


def test_permanent_failure_after_max_retries():
    calls = []

    def handler(payload):
        calls.append(1)
        return 500, {"error": {"message": "boom"}}

    client = OpenRouterEmbeddingsClient(api_key="k", max_retries=2,
                                        retry_delay_seconds=0.0,
                                        transport=_fake_transport(handler))
    with pytest.raises(RuntimeError):
        client.embed(["a"])
    assert len(calls) == 3  # 1 + max_retries
    assert client.ledger.permanent_failures == 1


def test_embedding_count_mismatch_raises():
    def handler(payload):
        return 200, {"data": [], "usage": {"prompt_tokens": 1, "cost": 0.0}}

    client = OpenRouterEmbeddingsClient(api_key="k", transport=_fake_transport(handler))
    with pytest.raises(RuntimeError):
        client.embed(["a"])


def test_sealed_data_guard():
    role_map = {"dev1": "DEV_TRAIN", "sealed1": "RESERVE", "sealed2": "INTERNAL_TEST"}
    assert_not_sealed(["dev1"], role_map)
    with pytest.raises(SealedDataError):
        assert_not_sealed(["dev1", "sealed1"], role_map)
    with pytest.raises(SealedDataError):
        assert_not_sealed(["sealed2"], role_map)


def test_estimate_requests_ceil():
    assert estimate_requests(0, 64) == 0
    assert estimate_requests(1, 64) == 1
    assert estimate_requests(64, 64) == 1
    assert estimate_requests(65, 64) == 2


def test_batch_size_boundaries():
    with pytest.raises(ValueError):
        OpenRouterEmbeddingsClient(api_key="k", batch_size=0)
    with pytest.raises(ValueError):
        OpenRouterEmbeddingsClient(api_key="k", batch_size=MAX_BATCH_SIZE + 1)


def test_empty_inputs_no_calls():
    calls = []

    def handler(payload):
        calls.append(1)
        return 200, _ok_body(len(payload["input"]))

    client = OpenRouterEmbeddingsClient(api_key="k", transport=_fake_transport(handler))
    assert client.embed([]) == []
    assert calls == []
