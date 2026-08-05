from __future__ import annotations

import os
import sys
import types
from pathlib import Path
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
        self._seed = None

    def manual_seed(self, seed: int) -> None:
        self._seed = seed

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

    def eval(self) -> _FakeModel:
        return self

    def get_memory_footprint(self) -> int:
        return 4000000000


class _FakeAutoTokenizer:
    last_args: tuple[Any, ...] = ()
    last_kwargs: dict[str, Any] = {}
    calls = 0

    @staticmethod
    def from_pretrained(*args: Any, **kwargs: Any) -> _FakeTokenizer:
        _FakeAutoTokenizer.last_args = args
        _FakeAutoTokenizer.last_kwargs = dict(kwargs)
        _FakeAutoTokenizer.calls += 1
        return _FakeTokenizer()


class _FakeAutoModelForCausalLM:
    last_args: tuple[Any, ...] = ()
    last_kwargs: dict[str, Any] = {}
    calls = 0

    @staticmethod
    def from_pretrained(*args: Any, **kwargs: Any) -> _FakeModel:
        _FakeAutoModelForCausalLM.last_args = args
        _FakeAutoModelForCausalLM.last_kwargs = dict(kwargs)
        _FakeAutoModelForCausalLM.calls += 1
        return _FakeModel(output_length=10)


class _FakeBitsAndBytesConfig:
    last_kwargs: dict[str, Any] = {}
    last_instance: _FakeBitsAndBytesConfig | None = None

    def __init__(self, **kwargs: Any) -> None:
        _FakeBitsAndBytesConfig.last_kwargs = dict(kwargs)
        _FakeBitsAndBytesConfig.last_instance = self


class _FakeTransformers(types.ModuleType):
    def __init__(self) -> None:
        super().__init__("transformers")
        self.AutoModelForCausalLM = _FakeAutoModelForCausalLM
        self.AutoTokenizer = _FakeAutoTokenizer
        self.BitsAndBytesConfig = _FakeBitsAndBytesConfig


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
        self.last_messages: object | None = None
        if chat_template_ok:
            self.apply_chat_template = self._apply  # type: ignore[method-assign]
        else:
            self.apply_chat_template = None  # type: ignore[method-assign]

    def _apply(self, messages: object, tokenize: bool = False, add_generation_prompt: bool = False) -> str:
        self.apply_calls += 1
        self.last_messages = messages
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
        # The backend must be importable without heavy Kaggle-only deps. Check
        # the module source for any TOP-LEVEL import of torch/transformers/
        # accelerate/bitsandbytes (imports inside functions and TYPE_CHECKING
        # are lazy and safe). Source inspection avoids the sys.modules / parent
        # package attribute poisoning that a real re-import would cause.
        import ast
        import inspect

        module_path = Path(inspect.getfile(KaggleQwenBackend))
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        heavy = {"torch", "transformers", "accelerate", "bitsandbytes"}
        found: list[str] = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                hit = {a.name.split(".")[0] for a in node.names} & heavy
                found.extend(sorted(hit))
        assert not found, f"top-level heavy imports in backend module: {sorted(set(found))}"
        _ = KaggleQwenBackend()

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
        assert tokenizer.last_messages == [
            {
                "role": "system",
                "content": (
                    "You are a precise source-code transformation engine. Follow "
                    "every scope, architecture, and output constraint literally. "
                    "Make minimal edits, preserve unrelated behavior, never invent "
                    "undeclared dependencies, and return only the requested complete "
                    "artifact content."
                ),
            },
            {"role": "user", "content": "write code"},
        ]

    @pytest.mark.asyncio
    async def test_zero_token_generation_is_empty_model_output_not_backend_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        backend, _tokenizer = self._inject_fakes(monkeypatch)
        backend._model = _FakeModel(output_length=8)
        response = await backend.generate("write code", max_tokens=64)
        assert response.text == ""
        assert response.token_usage.completion_tokens == 0
        assert response.finish_reason == "empty"

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

    def test_run_probe_seeds_fixed_and_generates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(sys.modules, "torch", _FakeTorch())
        backend, _tokenizer = self._inject_fakes(monkeypatch)
        response = backend.run_probe(max_tokens=64, prompt="def add(a, b):\n    return a + b\n")
        assert response.text == "generated output"
        torch_mod = sys.modules["torch"]
        assert torch_mod._seed == 0, "run_probe must seed torch deterministically"


def _write_qwen_config(
    path: Path,
    *,
    model_type: str = "qwen2",
    hidden_size: int,
    num_hidden_layers: int,
    num_attention_heads: int,
    quantization_config: dict[str, Any] | None = None,
) -> None:
    import json

    config: dict[str, Any] = {
        "model_type": model_type,
        "hidden_size": hidden_size,
        "num_hidden_layers": num_hidden_layers,
        "num_attention_heads": num_attention_heads,
    }
    if quantization_config is not None:
        config["quantization_config"] = quantization_config
    path.mkdir(parents=True, exist_ok=True)
    (path / "config.json").write_text(json.dumps(config), encoding="utf-8")


def _seven_b_checkpoint(tmp_path: Path) -> Path:
    checkpoint = tmp_path / "qwen2.5-coder-7b-instruct"
    _write_qwen_config(
        checkpoint,
        hidden_size=3584,
        num_hidden_layers=28,
        num_attention_heads=28,
    )
    return checkpoint


def _fourteen_b_checkpoint(tmp_path: Path) -> Path:
    checkpoint = tmp_path / "qwen2.5-coder-14b-instruct"
    _write_qwen_config(
        checkpoint,
        hidden_size=5120,
        num_hidden_layers=40,
        num_attention_heads=40,
    )
    return checkpoint


class TestR7CQuantization:
    """R7C-REAL-RUN-ROOT-CLOSURE: frozen quantization + identity contract."""

    def test_default_quantization_mode_is_bnb_int8(self) -> None:
        backend = KaggleQwenBackend()
        assert backend.quantization_mode == "bnb-int8"

    def test_model_identity_is_checkpoint_and_quantization_aware(
        self, tmp_path: Path
    ) -> None:
        seven_b = _seven_b_checkpoint(tmp_path)
        fourteen_b = _fourteen_b_checkpoint(tmp_path)

        id_7b = KaggleQwenBackend(model_path=str(seven_b)).model_identity
        id_14b_int8 = KaggleQwenBackend(model_path=str(fourteen_b)).model_identity
        id_14b_nf4 = KaggleQwenBackend(
            model_path=str(fourteen_b), quantization_mode="bnb-nf4"
        ).model_identity
        id_14b_fp16 = KaggleQwenBackend(
            model_path=str(fourteen_b), quantization_mode="fp16"
        ).model_identity

        assert id_7b != id_14b_int8
        assert id_14b_int8 != id_14b_nf4
        assert id_14b_int8 != id_14b_fp16
        assert id_14b_int8 != id_7b
        assert "bnb-int8" in id_7b
        assert "bnb-nf4" in id_14b_nf4
        assert "14b" in id_14b_nf4 or "qwen2.5-coder-14b-instruct" in id_14b_nf4

    def test_nf4_identity_is_not_colliding_with_legacy_7b_int8(
        self, tmp_path: Path
    ) -> None:
        fourteen_b = _fourteen_b_checkpoint(tmp_path)
        identity = KaggleQwenBackend(
            model_path=str(fourteen_b), quantization_mode="bnb-nf4"
        ).model_identity
        assert identity != "qwen:1:int8"
        assert not identity.startswith("qwen:1:")

    def test_model_identity_requires_model_path(self) -> None:
        with pytest.raises(ModelBackendError, match="model_path"):
            _ = KaggleQwenBackend().model_identity

    def test_rejects_unsupported_quantization_modes(self) -> None:
        with pytest.raises(ModelBackendError, match="bnb-int8"):
            KaggleQwenBackend(quantization_mode="int4")
        with pytest.raises(ModelBackendError, match="bnb-int8"):
            KaggleQwenBackend(quantization_mode="fp8")
        with pytest.raises(ModelBackendError, match="bnb-int8"):
            KaggleQwenBackend(quantization_mode="gptq")

    def test_canonical_alloc_conf_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import benchmark.llm.kaggle_qwen_backend as mod

        monkeypatch.delenv("PYTORCH_ALLOC_CONF", raising=False)
        mod._set_canonical_alloc_conf()
        assert os.environ.get("PYTORCH_ALLOC_CONF") == "expandable_segments:True"

    def test_load_delegates_to_ensure_loaded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[str] = []
        backend = KaggleQwenBackend()
        monkeypatch.setattr(backend, "_ensure_loaded", lambda: calls.append("ensure"))
        backend.load()
        assert calls == ["ensure"]


class TestCheckpointIdentitySlug:
    """Kaggle numeric-version directories produce readable, distinct slugs."""

    def test_kaggle_nested_7b_and_14b_slugs_are_readable_and_distinct(
        self, tmp_path: Path
    ) -> None:
        seven = tmp_path / "7b-instruct" / "1"
        fourteen = tmp_path / "14b-instruct" / "1"
        _write_qwen_config(seven, hidden_size=3584, num_hidden_layers=28, num_attention_heads=28)
        _write_qwen_config(fourteen, hidden_size=5120, num_hidden_layers=40, num_attention_heads=40)
        id_7b = KaggleQwenBackend(
            model_path=str(seven), quantization_mode="bnb-nf4"
        ).model_identity
        id_14b = KaggleQwenBackend(
            model_path=str(fourteen), quantization_mode="bnb-nf4"
        ).model_identity
        assert "7b-instruct-v1" in id_7b
        assert "14b-instruct-v1" in id_14b
        assert id_7b != id_14b
        assert not id_7b.startswith("qwen:1:")
        assert not id_14b.startswith("qwen:1:")

    def test_kaggle_version_1_and_2_identities_differ(self, tmp_path: Path) -> None:
        v1 = tmp_path / "14b-instruct" / "1"
        v2 = tmp_path / "14b-instruct" / "2"
        _write_qwen_config(v1, hidden_size=5120, num_hidden_layers=40, num_attention_heads=40)
        _write_qwen_config(v2, hidden_size=5120, num_hidden_layers=40, num_attention_heads=40)
        id_v1 = KaggleQwenBackend(
            model_path=str(v1), quantization_mode="bnb-nf4"
        ).model_identity
        id_v2 = KaggleQwenBackend(
            model_path=str(v2), quantization_mode="bnb-nf4"
        ).model_identity
        assert "14b-instruct-v1" in id_v1
        assert "14b-instruct-v2" in id_v2
        assert id_v1 != id_v2

    def test_checkpoint_basename_uses_slug_for_numeric_version_dir(
        self, tmp_path: Path
    ) -> None:
        v1 = tmp_path / "14b-instruct" / "1"
        _write_qwen_config(v1, hidden_size=5120, num_hidden_layers=40, num_attention_heads=40)
        backend = KaggleQwenBackend(model_path=str(v1))
        assert backend.checkpoint_basename == "14b-instruct-v1"

    def test_normal_non_numeric_directory_basename_is_unchanged(
        self, tmp_path: Path
    ) -> None:
        checkpoint = _fourteen_b_checkpoint(tmp_path)
        backend = KaggleQwenBackend(model_path=str(checkpoint))
        assert backend.checkpoint_basename == "qwen2.5-coder-14b-instruct"
        assert "qwen2.5-coder-14b-instruct" in backend.model_identity

    def test_identity_is_stable_for_same_path_config_and_mode(
        self, tmp_path: Path
    ) -> None:
        checkpoint = _fourteen_b_checkpoint(tmp_path)
        first = KaggleQwenBackend(
            model_path=str(checkpoint), quantization_mode="bnb-nf4"
        ).model_identity
        second = KaggleQwenBackend(
            model_path=str(checkpoint), quantization_mode="bnb-nf4"
        ).model_identity
        assert first == second

    def test_slug_is_sanitized_to_lowercase_ascii_safe(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "Qwen2.5-Coder 14B Instruct"
        _write_qwen_config(checkpoint, hidden_size=5120, num_hidden_layers=40, num_attention_heads=40)
        backend = KaggleQwenBackend(model_path=str(checkpoint))
        assert backend.checkpoint_basename == "qwen2.5-coder-14b-instruct"


class TestKaggleQuantizationLoad:
    """Quantization-aware model load: BNB int8, BNB NF4, fp16, and fail-fast."""

    def _install_runtime_fakes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(sys.modules, "torch", _FakeTorch())
        monkeypatch.setitem(sys.modules, "transformers", _FakeTransformers())
        _FakeAutoTokenizer.calls = 0
        _FakeAutoModelForCausalLM.calls = 0
        _FakeBitsAndBytesConfig.last_kwargs = {}
        _FakeBitsAndBytesConfig.last_instance = None

    def test_bnb_nf4_load_uses_canonical_nf4_profile(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_runtime_fakes(monkeypatch)
        checkpoint = _fourteen_b_checkpoint(tmp_path)
        backend = KaggleQwenBackend(
            model_path=str(checkpoint), quantization_mode="bnb-nf4"
        )
        backend._load_model()
        assert _FakeBitsAndBytesConfig.last_kwargs == {
            "load_in_4bit": True,
            "bnb_4bit_quant_type": "nf4",
            "bnb_4bit_compute_dtype": "float16",
            "bnb_4bit_use_double_quant": True,
        }
        assert _FakeAutoModelForCausalLM.last_kwargs["quantization_config"] is _FakeBitsAndBytesConfig.last_instance

    def test_bnb_int8_load_uses_load_in_8bit(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_runtime_fakes(monkeypatch)
        checkpoint = _seven_b_checkpoint(tmp_path)
        backend = KaggleQwenBackend(
            model_path=str(checkpoint), quantization_mode="bnb-int8"
        )
        backend._load_model()
        assert _FakeBitsAndBytesConfig.last_kwargs == {"load_in_8bit": True}

    def test_fp16_load_uses_float16_dtype_without_bnb(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_runtime_fakes(monkeypatch)
        checkpoint = _fourteen_b_checkpoint(tmp_path)
        backend = KaggleQwenBackend(
            model_path=str(checkpoint), quantization_mode="fp16"
        )
        backend._load_model()
        assert _FakeAutoModelForCausalLM.last_kwargs["torch_dtype"] == "float16"
        assert "quantization_config" not in _FakeAutoModelForCausalLM.last_kwargs

    def test_prequantized_gptq_checkpoint_is_rejected_before_from_pretrained(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_runtime_fakes(monkeypatch)
        checkpoint = _fourteen_b_checkpoint(tmp_path)
        _write_qwen_config(
            checkpoint,
            hidden_size=5120,
            num_hidden_layers=40,
            num_attention_heads=40,
            quantization_config={"quant_method": "gptq"},
        )
        backend = KaggleQwenBackend(
            model_path=str(checkpoint), quantization_mode="bnb-nf4"
        )
        with pytest.raises(ModelBackendError, match="PREQUANTIZED_CHECKPOINT_INCOMPATIBLE"):
            backend._load_model()
        assert _FakeAutoTokenizer.calls == 0, "tokenizer must not load before fail-fast"
        assert _FakeAutoModelForCausalLM.calls == 0, "model must not load before fail-fast"

    def test_unquantized_checkpoint_loads_under_bnb_modes(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_runtime_fakes(monkeypatch)
        checkpoint = _fourteen_b_checkpoint(tmp_path)
        backend = KaggleQwenBackend(
            model_path=str(checkpoint), quantization_mode="bnb-nf4"
        )
        backend._load_model()
        assert backend._loaded is True
        assert _FakeAutoModelForCausalLM.calls == 1


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
