from __future__ import annotations

import sys
import types
from typing import Any

import pytest

from benchmark.core.exceptions import ModelBackendError
from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend


class _FakeCuda:
    def empty_cache(self) -> None:
        return None

    def is_available(self) -> bool:
        return True

    def get_device_name(self, index: int) -> str:
        return "fake-gpu"

    def get_device_capability(self, index: int) -> tuple[int, int]:
        return (8, 0)

    def get_device_properties(self, index: int) -> Any:
        return types.SimpleNamespace(total_memory=1024**3)

    def memory_allocated(self, index: int = 0) -> int:
        return 0

    def memory_reserved(self, index: int = 0) -> int:
        return 0


class _FakeTorch(types.ModuleType):
    def __init__(self) -> None:
        super().__init__("torch")
        self.cuda = _FakeCuda()

    def inference_mode(self) -> Any:
        import contextlib

        return contextlib.nullcontext()

    def no_grad(self) -> Any:
        import contextlib

        return contextlib.nullcontext()

    @property
    def bfloat16(self) -> str:
        return "bfloat16"

    @property
    def float16(self) -> str:
        return "float16"

    @property
    def float32(self) -> str:
        return "float32"


class _FakeTensor:
    def __init__(self, length: int, eos_value: int = 1) -> None:
        self._length = length
        self._eos_value = eos_value

    @property
    def shape(self) -> tuple[int, int]:
        return (1, self._length)

    def to(self, device: object) -> _FakeTensor:
        return self

    def __getitem__(self, key: object) -> object:
        if isinstance(key, int):
            return _FakeTensor(self._length, self._eos_value)
        if isinstance(key, tuple):
            sl = key[1]
            start = sl.start if sl.start is not None else 0
            return _FakeTensor(max(0, self._length - start), self._eos_value)
        raise TypeError(key)

    def item(self) -> int:
        return self._eos_value

    def __len__(self) -> int:
        return self._length


class _FakeModel:
    device = "cuda:0"

    def __init__(self, output_length: int) -> None:
        self._output_length = output_length

    def generate(self, **kwargs: object) -> _FakeTensor:
        return _FakeTensor(self._output_length)


class _RaisingModel:
    device = "cuda:0"

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def generate(self, **kwargs: object) -> _FakeTensor:
        raise self._exc


class _FakeTokenizer:
    eos_token_id = 1

    def __init__(self, chat_template_ok: bool = True) -> None:
        self.apply_calls = 0
        if chat_template_ok:
            self.apply_chat_template = self._apply  # type: ignore[method-assign]
        else:
            self.apply_chat_template = None  # type: ignore[method-assign]

    def _apply(self, messages: object, tokenize: bool = False, add_generation_prompt: bool = False) -> str:
        self.apply_calls += 1
        return "<im_start>user\nprompt<im_end>"

    def __call__(self, text: str, return_tensors: str | None = None) -> dict[str, _FakeTensor]:
        return {"input_ids": _FakeTensor(8), "attention_mask": _FakeTensor(8)}

    def decode(self, ids: object, skip_special_tokens: bool = True) -> str:
        return "generated output"


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

    def _install_fake_torch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(sys.modules, "torch", _FakeTorch())

    def _inject_fakes(
        self,
        monkeypatch: pytest.MonkeyPatch,
        chat_template_ok: bool = True,
    ) -> tuple[KaggleQwenBackend, _FakeTokenizer]:
        self._install_fake_torch(monkeypatch)
        tokenizer = _FakeTokenizer(chat_template_ok=chat_template_ok)
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = tokenizer
        backend._model = _FakeModel(output_length=10)
        return backend, tokenizer

    @pytest.mark.asyncio
    async def test_apply_chat_template_called_exactly_once_per_generation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        backend, tokenizer = self._inject_fakes(monkeypatch)
        response = await backend.generate("write code", max_tokens=64)
        assert tokenizer.apply_calls == 1
        assert response.text == "generated output"
        assert response.finish_reason == "eos"

    @pytest.mark.asyncio
    async def test_generate_fails_without_usable_chat_template(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        backend, _tokenizer = self._inject_fakes(monkeypatch, chat_template_ok=False)
        with pytest.raises(ModelBackendError, match="chat template"):
            await backend.generate("write code")

    @pytest.mark.asyncio
    async def test_count_prompt_tokens_uses_formatted_chat_prompt(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        backend, tokenizer = self._inject_fakes(monkeypatch)
        count = backend.count_prompt_tokens("write code")
        assert count == 8
        assert tokenizer.apply_calls == 1


class TestCleanup:
    """R7B-SMOKE-FINISH: per-call tensor cleanup runs after every generate exit."""

    def _install_backend(self, monkeypatch: pytest.MonkeyPatch, model: _FakeModel | _RaisingModel) -> KaggleQwenBackend:
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = _FakeTokenizer()
        backend._model = model
        return backend

    def _track_cleanup(self, monkeypatch: pytest.MonkeyPatch) -> tuple[list[int], list[int]]:
        import gc

        import benchmark.llm.kaggle_qwen_backend as mod

        gc_calls: list[int] = []
        empty_calls: list[int] = []
        monkeypatch.setattr(gc, "collect", lambda: gc_calls.append(1) or 0)
        monkeypatch.setattr(mod, "_empty_cuda_cache", lambda: empty_calls.append(1))
        return gc_calls, empty_calls

    @pytest.mark.asyncio
    async def test_cleanup_after_successful_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(sys.modules, "torch", _FakeTorch())
        backend = self._install_backend(monkeypatch, _FakeModel(output_length=10))
        gc_calls, empty_calls = self._track_cleanup(monkeypatch)

        response = await backend.generate("write code", max_tokens=64)
        assert response.text == "generated output"
        assert gc_calls == [1], "gc.collect must run exactly once after success"
        assert empty_calls == [1], "torch.cuda.empty_cache must run exactly once after success"

    @pytest.mark.asyncio
    async def test_cleanup_after_oom(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(sys.modules, "torch", _FakeTorch())
        oom = type("OutOfMemoryError", (RuntimeError,), {"__module__": "torch.cuda"})
        backend = self._install_backend(monkeypatch, _RaisingModel(oom("simulated CUDA OOM")))
        gc_calls, empty_calls = self._track_cleanup(monkeypatch)

        with pytest.raises(ModelBackendError, match="out-of-memory"):
            await backend.generate("write code")
        assert gc_calls == [1], "gc.collect must run exactly once after OOM"
        assert empty_calls == [1], "torch.cuda.empty_cache must run exactly once after OOM"

    @pytest.mark.asyncio
    async def test_cleanup_after_other_generation_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(sys.modules, "torch", _FakeTorch())
        backend = self._install_backend(monkeypatch, _RaisingModel(RuntimeError("boom")))
        gc_calls, empty_calls = self._track_cleanup(monkeypatch)

        with pytest.raises(ModelBackendError, match="boom"):
            await backend.generate("write code")
        assert gc_calls == [1], "gc.collect must run exactly once after a generic generation exception"
        assert empty_calls == [1], "torch.cuda.empty_cache must run exactly once after a generic exception"
