"""OpenRouter embeddings client for the contamination-robustness bridge (T3).

PREPARED AND MOCK-TESTED ONLY. As of the 2026-09-19 audit the requested model
(`qwen/qwen3-embedding-8b`) is NOT available on OpenRouter (the full model
catalog contains zero embedding-capable models). This module documents the
frozen request contract so that a future authorized run is deterministic and
cannot silently change the model/provider.

Frozen contract (docs/QWEN3_EMBED_CONTAMINATION_ROBUSTNESS_PROTOCOL_FROZEN.md):
  - exact model id is a frozen constant (no fallback, no silent substitution);
  - batch size is frozen before any run;
  - transport retries are permitted ONLY for timeout/network/transient 5xx,
    with a frozen maximum retry count; NO result-based retry, NO provider swap;
  - every response's usage (prompt tokens + cost) is accumulated for the ledger;
  - inputs are hashed for audit; parent-only content is enforced by the caller;
  - a sealed-data guard refuses to embed any case from a sealed split role.

ZERO network calls are made by this module's tests (injected fake transport).
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass

# Frozen model identifier (verified present on OpenRouter's embeddings catalog
# 2026-09-19 via GET /api/v1/embeddings/models; the earlier generation-catalog
# probe was defective).
OPENROUTER_EMBED_MODEL = "qwen/qwen3-embedding-8b"

# Pinned provider (frozen before call 1; both Nebius and DeepInfra serve at
# $0.01/M; DeepInfra chosen for full 32,768 context, 100% 5m uptime, and the
# project's prior frozen DeepInfra route). Provider routing is pinned and
# fallback disabled per-request.
OPENROUTER_EMBED_PROVIDER = "DeepInfra"
OPENROUTER_EMBED_PRICE_PER_1M_USD = 0.01  # documented provider price (prompt)

# Frozen request-contract constants (do not change without a new freeze).
MAX_BATCH_SIZE = 64  # inputs per embeddings request (legal upper bound)
MAX_TRANSPORT_RETRIES = 3  # timeout/network/transient 5xx only
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
EMBED_ENDPOINT = "https://openrouter.ai/api/v1/embeddings"
# Availability discovery MUST use the DEDICATED embeddings-model catalog, never
# the generation-model catalog (the generation catalog has zero embedding
# models; the 2026-09-19 P71 probe defect).
EMBEDDINGS_CATALOG_ENDPOINT = "https://openrouter.ai/api/v1/embeddings/models"

SEALED_ROLES = ("RESERVE", "INTERNAL_TEST")


@dataclass
class EmbeddingLedger:
    """Accumulated API usage (permitted failures and retries recorded)."""
    requests: int = 0
    prompt_tokens: int = 0
    cost_usd: float = 0.0
    transport_failures: int = 0
    transport_retries: int = 0
    permanent_failures: int = 0


@dataclass
class NoFallbackError(RuntimeError):
    """Raised if a provider/model substitution would be required."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass
class SealedDataError(ValueError):
    """Raised when a sealed case id is passed to the client/caller."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


Transport = Callable[[dict], tuple[int, dict]]


def _default_transport(payload: dict, endpoint: str) -> tuple[int, dict]:
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {payload['api_key']}",
                 "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {"error": {"message": e.reason}}
        return e.code, body


class OpenRouterEmbeddingsClient:
    """POST /api/v1/embeddings client with frozen model id and no fallback."""

    def __init__(
        self,
        api_key: str,
        model: str = OPENROUTER_EMBED_MODEL,
        batch_size: int = MAX_BATCH_SIZE,
        max_retries: int = MAX_TRANSPORT_RETRIES,
        endpoint: str = EMBED_ENDPOINT,
        transport: Transport | None = None,
        retry_delay_seconds: float = 1.0,
    ) -> None:
        if model != OPENROUTER_EMBED_MODEL:
            raise NoFallbackError(
                f"frozen model is {OPENROUTER_EMBED_MODEL!r}; refusing {model!r}")
        if batch_size < 1 or batch_size > MAX_BATCH_SIZE:
            raise ValueError(f"batch_size must be in [1, {MAX_BATCH_SIZE}]")
        self.api_key = api_key
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.endpoint = endpoint
        self._transport = transport or (lambda p: _default_transport(p, endpoint))
        self.retry_delay_seconds = retry_delay_seconds
        self.ledger = EmbeddingLedger()

    def hash_input(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _post(self, payload: dict) -> tuple[int, dict]:
        attempt = 0
        while True:
            status, body = self._transport(payload)
            if status == 200:
                self.ledger.requests += 1
                self._record_usage(body)
                return status, body
            if status in RETRYABLE_STATUS and attempt < self.max_retries:
                self.ledger.transport_retries += 1
                attempt += 1
                time.sleep(self.retry_delay_seconds * (attempt ** 2))
                continue
            self.ledger.permanent_failures += 1
            raise RuntimeError(f"permanent embedding failure status={status}: {body}")

    def _record_usage(self, body: dict) -> None:
        usage = body.get("usage") or {}
        self.ledger.prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
        self.ledger.cost_usd += float(usage.get("cost", 0.0) or 0.0)

    def embed(self, inputs: Sequence[str]) -> list[list[float]]:
        """Embed all inputs in frozen batch-size chunks; returns row-major vectors."""
        if not inputs:
            return []
        if len(set(self.hash_input(i) for i in inputs)) != len(inputs):
            raise ValueError("duplicate inputs would break deterministic batching")
        out: list[list[float]] = []
        for start in range(0, len(inputs), self.batch_size):
            chunk = list(inputs[start:start + self.batch_size])
            payload = {
                "api_key": self.api_key,
                "model": self.model,
                "input": chunk,
                "encoding_format": "float",
                "provider": {
                    "order": [OPENROUTER_EMBED_PROVIDER],
                    "allow_fallbacks": False,
                },
            }
            _, body = self._post(payload)
            data = body.get("data", [])
            # The OpenRouter embeddings response returns one embedding per input.
            if len(data) != len(chunk):
                raise RuntimeError(
                    f"embedding count mismatch: expected {len(chunk)}, got {len(data)}")
            out.extend([list(d["embedding"]) for d in data])
        return out


def assert_not_sealed(case_ids: Sequence[str], role_map: dict[str, str]) -> None:
    """Sealed-data guard: raise if any case_id belongs to a sealed split role.

    role_map: case_id -> split role (DEV_TRAIN/DEV_VALIDATION/INTERNAL_TEST/RESERVE).
    Sealed roles are RESERVE and INTERNAL_TEST (frozen policy).
    """
    for cid in case_ids:
        role = (role_map.get(cid) or "").upper()
        if role in SEALED_ROLES:
            raise SealedDataError(f"case {cid} belongs to sealed role {role!r}")


def estimate_requests(n_inputs: int, batch_size: int = MAX_BATCH_SIZE) -> int:
    return -(-n_inputs // batch_size)  # ceil division
