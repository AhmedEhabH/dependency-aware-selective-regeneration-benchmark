from __future__ import annotations

import json
from pathlib import Path

from benchmark.core.models import LLMResponse, TokenUsage


class DryRunLLMBackend:
    def __init__(self, fixture_dir: str | None = None) -> None:
        self._fixture_dir = Path(fixture_dir) if fixture_dir else None

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        if self._fixture_dir and self._fixture_dir.is_dir():
            fixture = self._fixture_dir / "fixture_response.json"
            if fixture.is_file():
                data = json.loads(fixture.read_text(encoding="utf-8"))
                return LLMResponse(
                    text=data.get("text", "dry-run fixture"),
                    token_usage=TokenUsage(
                        prompt_tokens=data.get("prompt_tokens", 0),
                        completion_tokens=data.get("completion_tokens", 0),
                        total_tokens=data.get("total_tokens", 0),
                    ),
                    finish_reason=data.get("finish_reason", "stop"),
                )
        return LLMResponse(
            text="dry-run default response",
            token_usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
            finish_reason="stop",
        )
