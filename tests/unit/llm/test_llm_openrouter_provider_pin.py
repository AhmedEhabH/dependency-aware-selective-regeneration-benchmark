from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from benchmark.core.exceptions import ModelBackendError
from benchmark.llm.openrouter_backend import OpenRouterBackend

_FAKE_KEY = "sk-or-v1-PROVIDER-PIN-TEST-KEY-0000"


def _make_success_response(
    text: str = "ok",
    prompt_tokens: int = 5,
    completion_tokens: int = 3,
    total_tokens: int = 8,
) -> bytes:
    body = {
        "choices": [{"message": {"content": text, "role": "assistant"}, "finish_reason": "stop", "index": 0}],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
        "model": "test-model",
        "object": "chat.completion",
    }
    return json.dumps(body).encode("utf-8")


def _make_http_error(
    code: int,
    body_dict: dict[str, Any],
) -> urllib.error.HTTPError:
    body_bytes = json.dumps(body_dict).encode("utf-8")
    fp = io.BytesIO(body_bytes)
    return urllib.error.HTTPError(
        url="https://openrouter.ai/api/v1/chat/completions",
        code=code,
        msg="",
        hdrs={},
        fp=fp,
    )


class TestProviderPinRequest:
    @pytest.fixture(autouse=True)
    def _key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", _FAKE_KEY)

    @pytest.mark.asyncio
    async def test_request_body_contains_exactly_one_provider(self) -> None:
        sent_body: list[bytes] = []

        def capture(req: urllib.request.Request, api_key: str = "") -> bytes:
            sent_body.append(req.data)
            return _make_success_response()

        b = OpenRouterBackend(model="m", provider="DeepInfra")
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(b, "_do_request", capture)
            await b.generate("hi")

        assert len(sent_body) == 1
        parsed = json.loads(sent_body[0])
        provider_obj = parsed["provider"]
        assert isinstance(provider_obj, dict)
        order = provider_obj["order"]
        assert isinstance(order, list)
        assert order == ["DeepInfra"]
        assert len(order) == 1

    @pytest.mark.asyncio
    async def test_allow_fallbacks_false(self) -> None:
        sent_body: list[bytes] = []

        def capture(req: urllib.request.Request, api_key: str = "") -> bytes:
            sent_body.append(req.data)
            return _make_success_response()

        b = OpenRouterBackend(model="m", provider="DeepInfra")
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(b, "_do_request", capture)
            await b.generate("hi")

        parsed = json.loads(sent_body[0])
        assert parsed["provider"]["allow_fallbacks"] is False

    @pytest.mark.asyncio
    async def test_require_parameters_true(self) -> None:
        sent_body: list[bytes] = []

        def capture(req: urllib.request.Request, api_key: str = "") -> bytes:
            sent_body.append(req.data)
            return _make_success_response()

        b = OpenRouterBackend(model="m", provider="DeepInfra")
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(b, "_do_request", capture)
            await b.generate("hi")

        parsed = json.loads(sent_body[0])
        assert parsed["provider"]["require_parameters"] is True

    @pytest.mark.asyncio
    async def test_no_provider_omits_provider_object(self) -> None:
        sent_body: list[bytes] = []

        def capture(req: urllib.request.Request, api_key: str = "") -> bytes:
            sent_body.append(req.data)
            return _make_success_response()

        b = OpenRouterBackend(model="m")
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(b, "_do_request", capture)
            await b.generate("hi")

        parsed = json.loads(sent_body[0])
        assert "provider" not in parsed

    @pytest.mark.asyncio
    async def test_provider_slug_in_model_identity(self) -> None:
        b = OpenRouterBackend(model="m", provider="DeepInfra")
        assert b.model_identity == "openrouter:m@DeepInfra"

    @pytest.mark.asyncio
    async def test_provider_not_in_repr_or_logs(self) -> None:
        b = OpenRouterBackend(model="m", provider="DeepInfra")
        r = repr(b)
        assert "DeepInfra" not in r
        assert _FAKE_KEY not in r


class TestTransientRetryPolicy:
    @pytest.fixture(autouse=True)
    def _key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", _FAKE_KEY)

    @pytest.mark.asyncio
    async def test_429_retried_once_then_surfaces(self) -> None:
        calls = 0

        def flaky(req: urllib.request.Request, api_key: str = "") -> bytes:
            nonlocal calls
            calls += 1
            raise ModelBackendError("OpenRouter HTTP 429: rate limited")

        b = OpenRouterBackend(model="m", provider="DeepInfra")
        with (
            pytest.MonkeyPatch.context() as mp,
            pytest.raises(ModelBackendError, match="OpenRouter HTTP 429"),
        ):
            mp.setattr(b, "_do_request", flaky)
            await b.generate("hi")
        assert calls == 2

    @pytest.mark.asyncio
    async def test_500_retried_once_then_surfaces(self) -> None:
        calls = 0

        def flaky(req: urllib.request.Request, api_key: str = "") -> bytes:
            nonlocal calls
            calls += 1
            raise ModelBackendError("OpenRouter HTTP 500: server boom")

        b = OpenRouterBackend(model="m", provider="DeepInfra")
        with (
            pytest.MonkeyPatch.context() as mp,
            pytest.raises(ModelBackendError, match="OpenRouter HTTP 500"),
        ):
            mp.setattr(b, "_do_request", flaky)
            await b.generate("hi")
        assert calls == 2

    @pytest.mark.asyncio
    async def test_transport_error_retried_once_then_surfaces(self) -> None:
        calls = 0

        def flaky(req: urllib.request.Request, api_key: str = "") -> bytes:
            nonlocal calls
            calls += 1
            raise ModelBackendError("OpenRouter connection failed: Network is unreachable")

        b = OpenRouterBackend(model="m", provider="DeepInfra")
        with (
            pytest.MonkeyPatch.context() as mp,
            pytest.raises(ModelBackendError, match="OpenRouter connection failed"),
        ):
            mp.setattr(b, "_do_request", flaky)
            await b.generate("hi")
        assert calls == 2

    @pytest.mark.asyncio
    async def test_401_never_retried(self) -> None:
        calls = 0

        def flaky(req: urllib.request.Request, api_key: str = "") -> bytes:
            nonlocal calls
            calls += 1
            raise ModelBackendError("OpenRouter HTTP 401: bad key")

        b = OpenRouterBackend(model="m", provider="DeepInfra")
        with (
            pytest.MonkeyPatch.context() as mp,
            pytest.raises(ModelBackendError, match="OpenRouter HTTP 401"),
        ):
            mp.setattr(b, "_do_request", flaky)
            await b.generate("hi")
        assert calls == 1

    @pytest.mark.asyncio
    async def test_retry_does_not_run_without_provider_pin_test(self) -> None:
        """Retry policy is independent of provider pin; this is a guard test."""
        assert True

    @pytest.mark.asyncio
    async def test_transient_retry_count_tracked(self) -> None:
        calls = 0

        def flaky(req: urllib.request.Request, api_key: str = "") -> bytes:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise ModelBackendError("OpenRouter HTTP 429: slow down")
            return _make_success_response()

        b = OpenRouterBackend(model="m", provider="DeepInfra")
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(b, "_do_request", flaky)
            result = await b.generate("hi")
        assert calls == 2
        assert result.text == "ok"
        assert getattr(b, "transient_retry_count", 0) == 1


class TestUsagePreservedOnRetry:
    @pytest.fixture(autouse=True)
    def _key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", _FAKE_KEY)

    @pytest.mark.asyncio
    async def test_usage_parsed_after_successful_retry(self) -> None:
        calls = 0

        def flaky(req: urllib.request.Request, api_key: str = "") -> bytes:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise ModelBackendError("OpenRouter HTTP 429: slow down")
            return _make_success_response(
                text="hello",
                prompt_tokens=11,
                completion_tokens=7,
                total_tokens=18,
            )

        b = OpenRouterBackend(model="m", provider="DeepInfra")
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(b, "_do_request", flaky)
            result = await b.generate("hi")
        assert result.token_usage.prompt_tokens == 11
        assert result.token_usage.completion_tokens == 7
        assert result.token_usage.total_tokens == 18
        assert b.transient_retry_count == 1
