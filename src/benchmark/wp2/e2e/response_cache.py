"""WP-2 Mission-12 E2E Smoke v2 - run-level on-disk response cache (F03/E).

A single ``ResponseCache`` instance is shared across every episode of a run.
Requests are keyed by a canonical ``request_sha`` derived from the full request
specification (model, route, provider, temperature, top_p, max_tokens and the
complete messages list). Identical requests -- initial or repair -- across arms
reuse the stored provider response. The repair request has its own request_sha
and never overwrites the initial entry.

Persisted entries: research/wp2/e2e_smoke_eng_v2/cache/responses/<request_sha>.json

Each entry stores: raw text, response sha256, finish_reason, usage
(prompt/completion tokens), provider metadata, created time, provider_call flag.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmark.wp2.e2e.spec import MAX_TOKENS, MODEL, TEMPERATURE, TOP_P


class ResponseCache:
    """On-disk request->response cache keyed by canonical request_sha."""

    def __init__(self, root: Path) -> None:
        self._dir = root / "cache" / "responses"
        self._dir.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0

    @staticmethod
    def request_sha(model: str, route: str, provider: str, temperature: float,
                    top_p: float, max_tokens: int,
                    messages: list[dict[str, Any]]) -> str:
        """Canonical request hash (deterministic serialization)."""
        canonical = {
            "model": model,
            "route": route,
            "provider": provider,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        blob = json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def path_for(self, request_sha: str) -> Path:
        return self._dir / f"{request_sha}.json"

    def get(self, request_sha: str) -> dict[str, Any] | None:
        p = self.path_for(request_sha)
        if not p.exists():
            self.misses += 1
            return None
        try:
            entry = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.misses += 1
            return None
        if entry.get("request_sha") != request_sha:
            self.misses += 1
            return None
        self.hits += 1
        return dict(entry)

    def put(self, request_sha: str, entry: dict) -> Path:
        """Persist an entry. Never overwrites an existing entry."""
        p = self.path_for(request_sha)
        if p.exists():
            return p
        entry.setdefault("request_sha", request_sha)
        entry.setdefault("created_time", datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))
        p.write_text(json.dumps(entry, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return p


def default_request_sha(messages: list[dict[str, Any]],
                        route: str = "openrouter:qwen/qwen3-coder@deepinfra/turbo",
                        provider: str = "deepinfra/turbo") -> str:
    """Convenience: request_sha with the frozen v2 spec constants."""
    return ResponseCache.request_sha(MODEL, route, provider, TEMPERATURE, TOP_P,
                                     MAX_TOKENS, messages)
