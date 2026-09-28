"""WP-2 Mission-11 E2E Smoke - LLM client + spend ledger (B7).

``OpenRouterClient`` is a minimal plain-text client over the frozen
DeepInfra-through-OpenRouter route with the SAME headers, provider block,
retry policy (3 attempts, 5/20/60s) and frozen pricing ($0.30/$1.00 per 1M).
``ReplayClient`` returns canned responses for tests and zero-API controls.
``Ledger`` is a persistent JSONL spend ledger with per-stage ceilings.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmark.wp2.e2e.spec import MAX_TOKENS, MODEL, TEMPERATURE

FROZEN_PROMPT_USD_PER_1M = 0.30
FROZEN_COMPLETION_USD_PER_1M = 1.00
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
PROVIDER = "deepinfra/turbo"


@dataclass
class CallResult:
    text: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    route: str
    provider: str
    latency_s: float
    request_id: str


class GenerationError(RuntimeError):
    pass


class OpenRouterClient:
    def __init__(self, api_key_env: str = "OPENROUTER_API_KEY",
                 model: str = MODEL, max_tokens: int = MAX_TOKENS,
                 temperature: float = TEMPERATURE) -> None:
        self._api_key_env = api_key_env
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    def _api_key(self) -> str:
        key = os.environ.get(self._api_key_env, "")
        if not key or not key.strip():
            raise GenerationError(f"API key not found in {self._api_key_env}")
        return key.strip().strip('"').strip("'").strip()

    def generate_messages(self, messages: list[dict[str, Any]]) -> CallResult:
        api_key = self._api_key()
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "stream": False,
            "provider": {"order": [PROVIDER], "allow_fallbacks": False,
                         "require_parameters": True},
        }
        data = json.dumps(body).encode("utf-8")
        t0 = time.monotonic()
        last_exc: Exception | None = None
        backoffs = (0, 5, 20, 60, 120, 180)
        for attempt, backoff in enumerate(backoffs, start=1):
            if attempt > 1:
                time.sleep(backoff)
            req = urllib.request.Request(
                BASE_URL, data=data,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {api_key}"},
                method="POST")
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    raw = resp.read().decode("utf-8")
                payload = json.loads(raw)
                choice = payload["choices"][0]
                message = choice["message"]
                content = message.get("content") or ""
                finish_reason = choice.get("finish_reason", "stop")
                usage = payload.get("usage", {})
                pt = int(usage.get("prompt_tokens", 0) or 0)
                ct = int(usage.get("completion_tokens", 0) or 0)
                cost = usage.get("cost") if usage.get("cost") is not None else None
                if cost is None:
                    cost = (pt / 1e6 * FROZEN_PROMPT_USD_PER_1M
                            + ct / 1e6 * FROZEN_COMPLETION_USD_PER_1M)
                return CallResult(
                    text=content, finish_reason=finish_reason,
                    prompt_tokens=pt, completion_tokens=ct, cost_usd=float(cost),
                    route=f"openrouter:{self._model}@{PROVIDER}",
                    provider=PROVIDER, latency_s=round(time.monotonic() - t0, 3),
                    request_id=payload.get("id", hashlib.sha256(raw.encode()).hexdigest()[:16]))
            except Exception as exc:
                last_exc = exc
        raise GenerationError(f"{len(backoffs)} consecutive transport failures: {last_exc}")

    def generate(self, system: str, user: str) -> CallResult:
        return self.generate_messages([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])


class ReplayClient:
    """Deterministic client for tests / zero-API controls (cost 0).

    ``generate_messages`` keys on the sha256 of the whole messages list so
    that identical multi-message requests (including the full-context repair)
    produce identical responses.
    """

    def __init__(self, responses: dict[str, str]) -> None:
        self._responses = responses
        self.calls: list[tuple[str, str]] = []

    def generate_messages(self, messages: list[dict[str, Any]]) -> CallResult:
        canonical = json.dumps(messages, sort_keys=True, ensure_ascii=False)
        sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        self.calls.append((sha, canonical))
        text = self._responses.get(sha, self._responses.get(canonical, ""))
        return CallResult(text=text, finish_reason="stop",
                          prompt_tokens=len(canonical) // 4,
                          completion_tokens=len(text) // 4,
                          cost_usd=0.0, route="replay", provider="replay",
                          latency_s=0.0, request_id=f"replay-{sha[:8]}")

    def generate(self, system: str, user: str) -> CallResult:
        return self.generate_messages([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])


class Ledger:
    def __init__(self, path: Path, ceilings: dict[str, float]) -> None:
        self._path = path
        self._ceilings = ceilings
        self._totals: dict[str, float] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            stage = entry.get("stage", "SMOKE")
            self._totals[stage] = self._totals.get(stage, 0.0) + float(entry.get("cost_usd", 0.0))

    def totals(self) -> dict[str, float]:
        return dict(self._totals)

    def total(self) -> float:
        return sum(self._totals.values())

    def can_spend(self, worst_case_usd: float) -> bool:
        return all(self._totals.get(stage, 0.0) + worst_case_usd <= ceil
                   for stage, ceil in self._ceilings.items())

    def record(self, call: dict) -> None:
        stage = call.get("stage", "SMOKE")
        self._totals[stage] = self._totals.get(stage, 0.0) + float(call.get("cost_usd", 0.0))
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(call, sort_keys=True) + "\n")
