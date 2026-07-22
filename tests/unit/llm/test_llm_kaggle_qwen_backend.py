from __future__ import annotations

import sys

import pytest

from benchmark.core.exceptions import ModelBackendError
from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend


class TestKaggleQwenBackend:
    @pytest.mark.asyncio
    async def test_generate_raises_when_called_locally(self) -> None:
        backend = KaggleQwenBackend()
        with pytest.raises(ModelBackendError, match="requires torch and transformers"):
            await backend.generate("test")

    def test_import_does_not_require_torch(self) -> None:
        assert "torch" not in sys.modules
        assert "transformers" not in sys.modules
        _ = KaggleQwenBackend()
        assert "torch" not in sys.modules
        assert "transformers" not in sys.modules

    def test_kaggle_protocol_conformance(self) -> None:
        from benchmark.core.protocols import LLMBackend
        backend = KaggleQwenBackend()
        assert isinstance(backend, LLMBackend)
