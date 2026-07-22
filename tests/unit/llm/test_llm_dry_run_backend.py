from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from benchmark.llm.dry_run_backend import DryRunLLMBackend


class TestDryRunLLMBackend:
    @pytest.mark.asyncio
    async def test_default_response_when_no_fixture_dir(self) -> None:
        backend = DryRunLLMBackend()
        response = await backend.generate("test")
        assert response.text == "dry-run default response"
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_default_response_when_fixture_dir_missing(self) -> None:
        backend = DryRunLLMBackend(fixture_dir="/nonexistent/path")
        response = await backend.generate("test")
        assert response.text == "dry-run default response"

    @pytest.mark.asyncio
    async def test_loads_response_from_fixture_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "fixture_response.json"
            fixture.write_text(
                json.dumps({
                    "text": "from fixture",
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                    "finish_reason": "length",
                }),
                encoding="utf-8",
            )
            backend = DryRunLLMBackend(fixture_dir=tmp)
            response = await backend.generate("test")
            assert response.text == "from fixture"
            assert response.token_usage.prompt_tokens == 10
            assert response.token_usage.completion_tokens == 20
            assert response.token_usage.total_tokens == 30
            assert response.finish_reason == "length"

    @pytest.mark.asyncio
    async def test_ignores_non_fixture_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "other.json"
            other.write_text(json.dumps({"text": "ignored"}), encoding="utf-8")
            backend = DryRunLLMBackend(fixture_dir=tmp)
            response = await backend.generate("test")
            assert response.text == "dry-run default response"

    @pytest.mark.asyncio
    async def test_dry_run_protocol_conformance(self) -> None:
        from benchmark.core.protocols import LLMBackend
        backend = DryRunLLMBackend()
        assert isinstance(backend, LLMBackend)
