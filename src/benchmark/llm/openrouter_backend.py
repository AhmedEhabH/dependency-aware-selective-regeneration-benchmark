from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

from benchmark.core.exceptions import ModelBackendError
from benchmark.core.models import LLMResponse, TokenUsage

logger = logging.getLogger(__name__)

_MAX_SAFE_ERROR_LENGTH = 200
_REDACTED = "[REDACTED]"


def _redact(text: str, secret: str) -> str:
    if not secret:
        return text
    return text.replace(secret, _REDACTED)


class OpenRouterBackend:
    def __init__(
        self,
        model: str,
        api_key_env: str = "OPENROUTER_API_KEY",
        base_url: str = "https://openrouter.ai/api/v1",
        timeout_seconds: float = 120.0,
    ) -> None:
        if timeout_seconds < 0:
            raise ValueError("timeout_seconds must be >= 0")
        self._model = model
        self._api_key_env = api_key_env
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def __repr__(self) -> str:
        return f"OpenRouterBackend(model={self._model!r})"

    def count_prompt_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)

    def _get_api_key(self) -> str:
        key = os.environ.get(self._api_key_env, "")
        if not key or not key.strip():
            raise ModelBackendError(
                f"API key not found in environment variable {self._api_key_env}"
            )
        return key

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        api_key = self._get_api_key()
        url = f"{self._base_url}/chat/completions"

        body: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        request_data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            response_data: bytes = await asyncio.to_thread(
                self._do_request, req, api_key
            )
        except ModelBackendError:
            raise
        except Exception as exc:
            msg = _redact(_safe_exc_message(exc), api_key)
            raise ModelBackendError(
                f"OpenRouter request failed: {msg}"
            ) from exc

        try:
            parsed = json.loads(response_data)
        except json.JSONDecodeError as exc:
            msg = _redact(str(exc), api_key)
            raise ModelBackendError(
                f"OpenRouter returned malformed JSON: {msg}"
            ) from exc

        return _parse_openrouter_response(parsed)

    def _do_request(
        self, req: urllib.request.Request, api_key: str
    ) -> bytes:
        try:
            with urllib.request.urlopen(
                req, timeout=self._timeout_seconds
            ) as resp:
                return resp.read()  # type: ignore[no-any-return]
        except urllib.error.HTTPError as exc:
            safe_msg = _safe_error_from_http_error(exc, api_key)
            raise ModelBackendError(
                f"OpenRouter HTTP {exc.code}: {safe_msg}"
            ) from exc
        except urllib.error.URLError as exc:
            reason = _redact(_safe_exc_message(exc), api_key)
            raise ModelBackendError(
                f"OpenRouter connection failed: {reason}"
            ) from exc
        except TimeoutError as exc:
            raise ModelBackendError(
                f"OpenRouter request timed out after {self._timeout_seconds}s"
            ) from exc


def _safe_exc_message(exc: Exception) -> str:
    msg = str(exc)
    if len(msg) > _MAX_SAFE_ERROR_LENGTH:
        msg = msg[:_MAX_SAFE_ERROR_LENGTH] + "..."
    return msg


def _safe_error_from_http_error(
    exc: urllib.error.HTTPError, api_key: str
) -> str:
    try:
        body = exc.read()
        parsed = json.loads(body)
        error_info = parsed.get("error", {})
        if isinstance(error_info, dict):
            msg = error_info.get("message", "") or error_info.get("code", "")
            if msg:
                msg = _redact(str(msg), api_key)
                if len(msg) > _MAX_SAFE_ERROR_LENGTH:
                    msg = msg[:_MAX_SAFE_ERROR_LENGTH] + "..."
                return msg
    except (json.JSONDecodeError, AttributeError, UnicodeDecodeError):
        pass
    return f"HTTP {exc.code}"


def _validate_token_value(
    usage: dict[str, Any], key: str
) -> int:
    if key not in usage:
        raise ModelBackendError(
            f"OpenRouter response missing {key}"
        )
    val = usage[key]
    if val is None:
        raise ModelBackendError(
            f"OpenRouter response has None {key}"
        )
    if isinstance(val, bool):
        raise ModelBackendError(
            f"OpenRouter response has bool {key}"
        )
    if not isinstance(val, int):
        raise ModelBackendError(
            f"OpenRouter response has non-int {key}"
        )
    if val < 0:
        raise ModelBackendError(
            f"OpenRouter response has negative {key}"
        )
    return val


def _parse_openrouter_response(parsed: dict[str, Any]) -> LLMResponse:
    choices = parsed.get("choices")
    if not choices or not isinstance(choices, list) or len(choices) == 0:
        raise ModelBackendError(
            "OpenRouter response missing choices"
        )

    choice = choices[0]
    if not isinstance(choice, dict):
        raise ModelBackendError(
            "OpenRouter response choice is not an object"
        )

    message = choice.get("message")
    if not isinstance(message, dict):
        raise ModelBackendError(
            "OpenRouter response missing message in choice"
        )

    content = message.get("content")
    if not content or not isinstance(content, str):
        raise ModelBackendError(
            "OpenRouter response missing or empty assistant content"
        )

    finish_reason: str = choice.get("finish_reason", "") or ""

    usage = parsed.get("usage")
    if not isinstance(usage, dict):
        raise ModelBackendError(
            "OpenRouter response missing usage"
        )

    prompt_tokens = _validate_token_value(usage, "prompt_tokens")
    completion_tokens = _validate_token_value(usage, "completion_tokens")
    total_tokens = _validate_token_value(usage, "total_tokens")

    token_usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )

    return LLMResponse(
        text=content,
        token_usage=token_usage,
        finish_reason=finish_reason,
    )
