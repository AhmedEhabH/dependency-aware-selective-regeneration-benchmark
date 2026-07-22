from __future__ import annotations

from benchmark.core.models import LLMResponse, TokenUsage


class MockLLMBackend:
    def __init__(self, response_text: str = "mock response") -> None:
        self._response_text = response_text

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        prompt_tokens = max(1, len(prompt) // 4)
        output_text = self._response_text
        completion_tokens = max(1, len(output_text) // 4)
        return LLMResponse(
            text=output_text,
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            finish_reason="stop",
        )
