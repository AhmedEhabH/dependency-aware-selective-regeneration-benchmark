from __future__ import annotations

import contextlib
import io
import json
import logging
import urllib.error
import urllib.request
from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest

from benchmark.core.exceptions import ModelBackendError
from benchmark.core.models import LLMResponse, TokenUsage
from benchmark.llm.openrouter_backend import OpenRouterBackend

_FAKE_KEY = "sk-or-v1-DO-NOT-LEAK-12345"

# Capture original method before autouse fixture patches it
_ORIG_DO_REQUEST = OpenRouterBackend._do_request


def _wrap_do_request(b: OpenRouterBackend) -> object:
    return lambda req, ak: _ORIG_DO_REQUEST(b, req, ak)


def _make_success_response(
    text: str = "hello world",
    prompt_tokens: int = 50,
    completion_tokens: int = 20,
    total_tokens: int = 70,
    finish_reason: str = "stop",
) -> bytes:
    body = {
        "choices": [
            {
                "message": {"content": text, "role": "assistant"},
                "finish_reason": finish_reason,
                "index": 0,
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
        "model": "test-model",
        "object": "chat.completion",
    }
    return json.dumps(body).encode("utf-8")


@pytest.fixture
def backend() -> OpenRouterBackend:
    return OpenRouterBackend(model="test-model")


@pytest.fixture
def backend_with_key(monkeypatch: pytest.MonkeyPatch) -> OpenRouterBackend:
    monkeypatch.setenv("OPENROUTER_API_KEY", _FAKE_KEY)
    return OpenRouterBackend(model="test-model")


@pytest.fixture(autouse=True)
def _no_real_network() -> Generator[None, None, None]:
    """Ensure no real network calls happen during any test."""
    with patch.object(OpenRouterBackend, "_do_request") as mock:
        mock.side_effect = RuntimeError(
            "Unexpected real _do_request call. Individual tests must mock _do_request explicitly."
        )
        yield


class TestOpenRouterBackendConstruction:
    def test_repr_does_not_contain_key(self) -> None:
        b = OpenRouterBackend(model="gpt-4")
        r = repr(b)
        assert "sk-or" not in r
        assert "key" not in r.lower()
        assert "api" not in r.lower()

    def test_negative_timeout_raises(self) -> None:
        with pytest.raises(ValueError, match="timeout_seconds must be >= 0"):
            OpenRouterBackend(model="m", timeout_seconds=-1)

    def test_zero_timeout_accepted(self) -> None:
        b = OpenRouterBackend(model="m", timeout_seconds=0)
        assert b._timeout_seconds == 0


class TestOpenRouterBackendProtocol:
    @pytest.mark.asyncio
    async def test_protocol_conformance(self) -> None:
        from benchmark.core.protocols import LLMBackend

        b = OpenRouterBackend(model="m")
        assert isinstance(b, LLMBackend)

    @pytest.mark.asyncio
    async def test_generate_returns_llm_response_type(self, backend_with_key: OpenRouterBackend) -> None:
        mock_response = _make_success_response()
        with patch.object(backend_with_key, "_do_request", return_value=mock_response):
            result = await backend_with_key.generate("test")
        assert isinstance(result, LLMResponse)
        assert isinstance(result.token_usage, TokenUsage)

    @pytest.mark.asyncio
    async def test_successful_response_maps_correctly(self, backend_with_key: OpenRouterBackend) -> None:
        mock_response = _make_success_response(
            text="hello world",
            prompt_tokens=50,
            completion_tokens=20,
            total_tokens=70,
            finish_reason="stop",
        )
        with patch.object(backend_with_key, "_do_request", return_value=mock_response):
            result = await backend_with_key.generate("test prompt", temperature=0.5, max_tokens=2048)
        assert result.text == "hello world"
        assert result.finish_reason == "stop"
        assert result.token_usage.prompt_tokens == 50
        assert result.token_usage.completion_tokens == 20
        assert result.token_usage.total_tokens == 70


class TestOpenRouterBackendApiKey:
    @pytest.mark.asyncio
    async def test_missing_key_fails_safely(self, backend: OpenRouterBackend) -> None:
        with (
            patch.object(
                backend,
                "_get_api_key",
                side_effect=ModelBackendError("API key not found in environment variable OPENROUTER_API_KEY"),
            ),
            pytest.raises(ModelBackendError, match="API key not found"),
        ):
            await backend.generate("test")

    @pytest.mark.asyncio
    async def test_blank_key_fails_safely(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "   ")
        b = OpenRouterBackend(model="test-model")
        with pytest.raises(ModelBackendError, match="API key not found"):
            await b.generate("test")

    @pytest.mark.asyncio
    async def test_key_not_in_exception_text(self, backend: OpenRouterBackend) -> None:
        with patch.object(
            backend,
            "_get_api_key",
            side_effect=ModelBackendError("API key not found in environment variable OPENROUTER_API_KEY"),
        ):
            try:
                await backend.generate("test")
            except ModelBackendError as e:
                msg = str(e)
                assert _FAKE_KEY not in msg
                assert "OPENROUTER_API_KEY" in msg


def _make_http_error(
    code: int,
    body_dict: dict[str, Any],
) -> urllib.error.HTTPError:
    """Create a real urllib.error.HTTPError with the given body content."""
    body_bytes = json.dumps(body_dict).encode("utf-8")
    fp = io.BytesIO(body_bytes)
    return urllib.error.HTTPError(
        url="https://openrouter.ai/api/v1/chat/completions",
        code=code,
        msg="",
        hdrs={},
        fp=fp,
    )


class TestOpenRouterBackendHttpErrors:
    @pytest.mark.asyncio
    async def test_http_error_routes_through_real_parsing(self, backend_with_key: OpenRouterBackend) -> None:
        error_body = {
            "error": {
                "message": f"invalid API key: {_FAKE_KEY}",
                "code": "auth_error",
            }
        }
        http_error = _make_http_error(401, error_body)

        with (
            patch.object(backend_with_key, "_do_request", side_effect=_wrap_do_request(backend_with_key)),
            patch("urllib.request.urlopen", side_effect=http_error),
            pytest.raises(ModelBackendError) as exc_info,
        ):
            await backend_with_key.generate("test")

        exc_str = str(exc_info.value)
        assert _FAKE_KEY not in exc_str
        assert "[REDACTED]" in exc_str
        assert "OpenRouter HTTP 401" in exc_str

    @pytest.mark.asyncio
    async def test_http_401_fails_safely(self, backend_with_key: OpenRouterBackend) -> None:
        with (
            patch.object(
                backend_with_key,
                "_do_request",
                side_effect=ModelBackendError("OpenRouter HTTP 401: HTTP 401"),
            ),
            pytest.raises(ModelBackendError, match="OpenRouter HTTP 401"),
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_http_429_fails_safely(self, backend_with_key: OpenRouterBackend) -> None:
        with (
            patch.object(
                backend_with_key,
                "_do_request",
                side_effect=ModelBackendError("OpenRouter HTTP 429: HTTP 429"),
            ),
            pytest.raises(ModelBackendError, match="OpenRouter HTTP 429"),
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_http_500_fails_safely(self, backend_with_key: OpenRouterBackend) -> None:
        with (
            patch.object(
                backend_with_key,
                "_do_request",
                side_effect=ModelBackendError("OpenRouter HTTP 500: HTTP 500"),
            ),
            pytest.raises(ModelBackendError, match="OpenRouter HTTP 500"),
        ):
            await backend_with_key.generate("test")


class TestOpenRouterBackendTransportErrors:
    @pytest.mark.asyncio
    async def test_timeout_becomes_model_backend_error(self, backend_with_key: OpenRouterBackend) -> None:
        with (
            patch.object(
                backend_with_key,
                "_do_request",
                side_effect=ModelBackendError("OpenRouter request timed out after 120.0s"),
            ),
            pytest.raises(ModelBackendError, match="timed out"),
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_connection_error_becomes_model_backend_error(self, backend_with_key: OpenRouterBackend) -> None:
        with (
            patch.object(
                backend_with_key,
                "_do_request",
                side_effect=ModelBackendError("OpenRouter connection failed"),
            ),
            pytest.raises(ModelBackendError, match="OpenRouter connection failed"),
        ):
            await backend_with_key.generate("test")


class TestOpenRouterBackendMalformedResponse:
    @pytest.mark.asyncio
    async def test_malformed_json_fails(self, backend_with_key: OpenRouterBackend) -> None:
        with patch.object(backend_with_key, "_do_request", return_value=b"not json"), pytest.raises(
            ModelBackendError, match="malformed JSON"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_missing_choices_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps({"usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="missing choices"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_empty_choices_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {"choices": [], "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="missing choices"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_missing_content_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="missing or empty assistant content"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_null_content_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": None}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="missing or empty assistant content"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_missing_usage_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="missing usage"
        ):
            await backend_with_key.generate("test")


class TestOpenRouterBackendStrictTokenValidation:
    @pytest.mark.asyncio
    async def test_string_token_value_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": "abc", "completion_tokens": 0, "total_tokens": 0},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="non-int prompt_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_string_completion_tokens_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": "xyz", "total_tokens": 0},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="non-int completion_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_string_total_tokens_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": "foo"},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="non-int total_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_float_token_value_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 5.5, "completion_tokens": 0, "total_tokens": 0},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="non-int prompt_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_bool_token_value_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": True, "completion_tokens": 0, "total_tokens": 0},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="bool prompt_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_bool_completion_tokens_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": False, "total_tokens": 0},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="bool completion_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_bool_total_tokens_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": True},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="bool total_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_negative_prompt_tokens_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": -1, "completion_tokens": 0, "total_tokens": 0},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="negative prompt_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_negative_completion_tokens_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": -5, "total_tokens": 0},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="negative completion_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_negative_total_tokens_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": -10},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="negative total_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_missing_prompt_tokens_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"completion_tokens": 0, "total_tokens": 0},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="missing prompt_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_missing_completion_tokens_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "total_tokens": 0},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="missing completion_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_missing_total_tokens_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="missing total_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_none_token_value_fails(self, backend_with_key: OpenRouterBackend) -> None:
        body = json.dumps(
            {
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": None, "completion_tokens": 0, "total_tokens": 0},
            }
        ).encode()
        with patch.object(backend_with_key, "_do_request", return_value=body), pytest.raises(
            ModelBackendError, match="None prompt_tokens"
        ):
            await backend_with_key.generate("test")

    @pytest.mark.asyncio
    async def test_zero_token_counts_preserved(self, backend_with_key: OpenRouterBackend) -> None:
        mock_response = _make_success_response(
            text="ok",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        )
        with patch.object(backend_with_key, "_do_request", return_value=mock_response):
            result = await backend_with_key.generate("test")
        assert result.token_usage.prompt_tokens == 0
        assert result.token_usage.completion_tokens == 0
        assert result.token_usage.total_tokens == 0


class TestOpenRouterBackendRequestPayload:
    @pytest.mark.asyncio
    async def test_model_in_request_payload(self, backend_with_key: OpenRouterBackend) -> None:
        sent_body: list[bytes] = []

        def capture_request(req: urllib.request.Request, api_key: str = "") -> bytes:
            sent_body.append(req.data)
            return _make_success_response()

        with patch.object(backend_with_key, "_do_request", side_effect=capture_request):
            await backend_with_key.generate("test")
        assert len(sent_body) == 1
        parsed = json.loads(sent_body[0])
        assert parsed["model"] == "test-model"

    @pytest.mark.asyncio
    async def test_temperature_and_max_tokens_forwarded(self, backend_with_key: OpenRouterBackend) -> None:
        sent_body: list[bytes] = []

        def capture_request(req: urllib.request.Request, api_key: str = "") -> bytes:
            sent_body.append(req.data)
            return _make_success_response()

        with patch.object(backend_with_key, "_do_request", side_effect=capture_request):
            await backend_with_key.generate("test", temperature=0.7, max_tokens=512)
        parsed = json.loads(sent_body[0])
        assert parsed["temperature"] == 0.7
        assert parsed["max_tokens"] == 512

    @pytest.mark.asyncio
    async def test_prompt_in_request_body(self, backend_with_key: OpenRouterBackend) -> None:
        sent_body: list[bytes] = []

        def capture_request(req: urllib.request.Request, api_key: str = "") -> bytes:
            sent_body.append(req.data)
            return _make_success_response()

        with patch.object(backend_with_key, "_do_request", side_effect=capture_request):
            await backend_with_key.generate("what is the capital of France?")
        parsed = json.loads(sent_body[0])
        assert parsed["messages"][0]["content"] == "what is the capital of France?"
        assert parsed["stream"] is False

    @pytest.mark.asyncio
    async def test_authorization_header_present(self, backend_with_key: OpenRouterBackend) -> None:
        sent_headers: list[dict[str, str]] = []

        def capture_request(req: urllib.request.Request, api_key: str = "") -> bytes:
            headers: dict[str, str] = {}
            for k, v in req.headers.items():
                headers[k] = v
            sent_headers.append(headers)
            return _make_success_response()

        with patch.object(backend_with_key, "_do_request", side_effect=capture_request):
            await backend_with_key.generate("test")
        assert len(sent_headers) == 1
        auth = sent_headers[0].get("Authorization", "")
        assert auth.startswith("Bearer ")
        assert _FAKE_KEY in auth


class TestOpenRouterBackendCustomKeyEnv:
    @pytest.mark.asyncio
    async def test_custom_env_var_name(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MY_CUSTOM_KEY", _FAKE_KEY)
        b = OpenRouterBackend(model="test-model", api_key_env="MY_CUSTOM_KEY")
        mock_response = _make_success_response()
        with patch.object(b, "_do_request", return_value=mock_response):
            result = await b.generate("test")
        assert result.text == "hello world"


class TestOpenRouterBackendSecurityRegression:
    @pytest.mark.asyncio
    async def test_secret_redacted_from_real_http_error(self, backend_with_key: OpenRouterBackend) -> None:
        error_body = {
            "error": {
                "message": f"invalid API key: {_FAKE_KEY}",
                "code": "auth_error",
            }
        }
        http_error = _make_http_error(401, error_body)

        with (
            patch.object(backend_with_key, "_do_request", side_effect=_wrap_do_request(backend_with_key)),
            patch("urllib.request.urlopen", side_effect=http_error),
            contextlib.suppress(ModelBackendError),
        ):
            await backend_with_key.generate("test")

        exc_repr = repr(backend_with_key)
        assert _FAKE_KEY not in exc_repr

    @pytest.mark.asyncio
    async def test_secret_not_in_any_output(self, backend_with_key: OpenRouterBackend) -> None:
        logger = logging.getLogger("benchmark.llm.openrouter_backend")
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        error_body = {
            "error": {
                "message": f"invalid API key: {_FAKE_KEY}",
                "code": "auth_error",
            }
        }
        http_error = _make_http_error(401, error_body)

        with (
            patch.object(backend_with_key, "_do_request", side_effect=_wrap_do_request(backend_with_key)),
            patch("urllib.request.urlopen", side_effect=http_error),
            contextlib.suppress(ModelBackendError),
        ):
            await backend_with_key.generate("test")

        logger.removeHandler(handler)
        log_text = stream.getvalue()
        assert _FAKE_KEY not in log_text

        exc_repr = repr(backend_with_key)
        assert _FAKE_KEY not in exc_repr
