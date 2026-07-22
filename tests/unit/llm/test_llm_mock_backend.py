from __future__ import annotations

import pytest

from benchmark.llm.mock_backend import MockLLMBackend


class TestMockLLMBackend:
    @pytest.mark.asyncio
    async def test_generate_returns_expected_text(self) -> None:
        backend = MockLLMBackend(response_text="hello world")
        response = await backend.generate("test prompt")
        assert response.text == "hello world"

    @pytest.mark.asyncio
    async def test_generate_returns_llm_response_type(self) -> None:
        backend = MockLLMBackend()
        response = await backend.generate("test")
        assert hasattr(response, "text")
        assert hasattr(response, "token_usage")
        assert hasattr(response, "finish_reason")

    @pytest.mark.asyncio
    async def test_generate_token_usage_non_negative(self) -> None:
        backend = MockLLMBackend()
        response = await backend.generate("test")
        assert response.token_usage.prompt_tokens >= 0
        assert response.token_usage.completion_tokens >= 0
        assert response.token_usage.total_tokens >= 0

    @pytest.mark.asyncio
    async def test_generate_finish_reason_is_stop(self) -> None:
        backend = MockLLMBackend()
        response = await backend.generate("test")
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_deterministic_output(self) -> None:
        backend = MockLLMBackend(response_text="deterministic")
        r1 = await backend.generate("prompt")
        r2 = await backend.generate("prompt")
        assert r1.text == r2.text
        assert r1.token_usage == r2.token_usage

    @pytest.mark.asyncio
    async def test_mock_protocol_conformance(self) -> None:
        from benchmark.core.protocols import LLMBackend
        backend = MockLLMBackend()
        assert isinstance(backend, LLMBackend)
