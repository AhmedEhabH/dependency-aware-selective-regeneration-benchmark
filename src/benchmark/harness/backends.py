"""Concrete model backends (V1).

V1 ships exactly two backends:

- ``none`` — the ZERO-LLM backend used by Protocol A. Any call raises
  :class:`BudgetExceededError` (fail-closed).
- ``mock`` — a deterministic test backend that records usage but never issues a
  scientific API call (used only for budget-enforcement tests).

Model/provider names are configuration; no algorithm branch lives in method
code.
"""

from __future__ import annotations

from typing import Any

from . import interfaces
from .registry import register_backend


@register_backend
class NoneBackend(interfaces.ModelBackend):
    """Zero-LLM backend: any complete() call is a budget violation."""

    name = "none"
    model_name = ""
    provider = ""

    def __init__(self) -> None:
        self._calls = 0
        self._tokens = 0

    def complete(self, *, prompt: str, **kwargs: Any) -> dict[str, Any]:
        del prompt, kwargs
        self._calls += 1
        raise interfaces.BudgetExceededError(
            "zero-LLM backend: model calls are forbidden for this spec"
        )

    @property
    def llm_calls(self) -> int:
        return self._calls

    @property
    def llm_tokens(self) -> int:
        return self._tokens


@register_backend
class MockBackend(interfaces.ModelBackend):
    """Deterministic test backend (records usage; no external call)."""

    name = "mock"
    model_name = "mock-model"
    provider = "mock-provider"

    def __init__(self) -> None:
        self._calls = 0
        self._tokens = 0
        self._responses: list[dict[str, Any]] = []

    def complete(self, *, prompt: str, **kwargs: Any) -> dict[str, Any]:
        del prompt
        self._calls += 1
        self._tokens += max(0, int(kwargs.get("estimated_tokens", 0)))
        response = {"text": f"mock[{self._calls}]", "finish_reason": "stop"}
        self._responses.append(response)
        return response

    @property
    def llm_calls(self) -> int:
        return self._calls

    @property
    def llm_tokens(self) -> int:
        return self._tokens
