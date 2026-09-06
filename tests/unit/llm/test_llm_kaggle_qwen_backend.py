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


class _RecordingSdpaPolicyContext:
    """Context manager mimicking torch.nn.attention.sdpa_kernel(...)."""

    def __init__(self, recorder: dict[str, Any], backend_names: list[str]) -> None:
        self._recorder = recorder
        self._backend_names = backend_names

    def __enter__(self) -> _RecordingSdpaPolicyContext:
        self._recorder["depth"] += 1
        self._recorder["active"] = True
        self._recorder["active_allowed"] = list(self._backend_names)
        return self

    def __exit__(self, *exc: object) -> None:
        self._recorder["depth"] -= 1
        if self._recorder["depth"] <= 0:
            self._recorder["active"] = False
            self._recorder["active_allowed"] = []


class _FakeSdpaKernelFactory:
    """Callable mimicking torch.nn.attention.sdpa_kernel."""

    def __init__(self, recorder: dict[str, Any]) -> None:
        self._recorder = recorder

    def __call__(self, backends: Any) -> _RecordingSdpaPolicyContext:
        names = [str(getattr(b, "name", b)) for b in backends]
        self._recorder["calls"].append(names)
        return _RecordingSdpaPolicyContext(self._recorder, names)


class _FakeSDPBackend:
    FLASH_ATTENTION = "FLASH_ATTENTION"
    EFFICIENT_ATTENTION = "EFFICIENT_ATTENTION"
    MATH = "MATH"


def _build_fake_torch_nn(recorder: dict[str, Any]) -> types.ModuleType:
    nn_module = types.ModuleType("torch.nn")
    attention_module = types.ModuleType("torch.nn.attention")
    attention_module.SDPBackend = _FakeSDPBackend  # type: ignore[attr-defined]
    attention_module.sdpa_kernel = _FakeSdpaKernelFactory(recorder)  # type: ignore[attr-defined]
    nn_module.attention = attention_module  # type: ignore[attr-defined]
    return nn_module


def _install_fake_torch_modules(
    monkeypatch: pytest.MonkeyPatch,
    fake_torch: types.ModuleType | None = None,
) -> types.ModuleType:
    fake = fake_torch if fake_torch is not None else _FakeTorch()
    monkeypatch.setitem(sys.modules, "torch", fake)
    monkeypatch.setitem(sys.modules, "torch.nn", fake.nn)
    monkeypatch.setitem(sys.modules, "torch.nn.attention", fake.nn.attention)
    monkeypatch.setitem(sys.modules, "transformers", _build_fake_transformers())
    return fake


class _FakeStoppingCriteriaList:
    """Minimal stand-in so ``from transformers import StoppingCriteriaList``
    resolves in unit tests without a real torch. The fake model.generate records
    the stopping_criteria kwarg but never invokes it, so this only needs to wrap
    and retain the criteria."""

    def __init__(self, criteria: list[object]) -> None:
        self.criteria = list(criteria)

    def __iter__(self):  # pragma: no cover
        return iter(self.criteria)


def _build_fake_transformers() -> types.ModuleType:
    mod = types.ModuleType("transformers")
    mod.StoppingCriteriaList = _FakeStoppingCriteriaList
    return mod


class _FakeTorch(types.ModuleType):
    def __init__(self) -> None:
        super().__init__("torch")
        self.cuda = _FakeCuda()
        self._seed = None
        self.sdpa_recorder: dict[str, Any] = {
            "calls": [],
            "active": False,
            "active_allowed": [],
            "depth": 0,
        }
        self.nn = _build_fake_torch_nn(self.sdpa_recorder)

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
        self.last_generate_kwargs: dict[str, object] = {}

    def generate(self, **kwargs: object) -> _FakeTensor:
        self.last_generate_kwargs = dict(kwargs)
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

    def __init__(self, chat_template_ok: bool = True, token_length: int = 8) -> None:
        self._token_length = token_length
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
        return {
            "input_ids": _FakeTensor(self._token_length),
            "attention_mask": _FakeTensor(self._token_length),
        }

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
        _install_fake_torch_modules(monkeypatch)

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
        _install_fake_torch_modules(monkeypatch)
        backend, _tokenizer = self._inject_fakes(monkeypatch)
        response = backend.run_probe(max_tokens=64, prompt="def add(a, b):\n    return a + b\n")
        assert response.text == "generated output"
        torch_mod = sys.modules["torch"]
        assert torch_mod._seed == 0, "run_probe must seed torch deterministically"


class TestRunProbeEventLoopClosure:
    """RUN-PROBE-ASYNC-CLOSURE: run_probe must never drive its own event loop.

    ``run_probe`` is executed inside the already-running ipykernel loop of the
    pilot notebook's model-preflight cell. Calling ``asyncio.run`` there raises
    ``RuntimeError: asyncio.run() cannot be called from a running event loop``
    and aborts the preflight. These tests lock the fix: synchronous generation
    inside ``run_probe``, byte-identical to ``await generate(temperature=0.0)``.
    """

    _PROBE_PROMPT = "def add(a, b):\n    return a + b\n"

    def _inject_fakes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> tuple[KaggleQwenBackend, _FakeTokenizer]:
        _install_fake_torch_modules(monkeypatch)
        tokenizer = _FakeTokenizer()
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = tokenizer
        backend._model = _FakeModel(output_length=10)
        return backend, tokenizer

    @pytest.mark.asyncio
    async def test_run_probe_succeeds_inside_a_running_event_loop(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        backend, _tokenizer = self._inject_fakes(monkeypatch)
        response = backend.run_probe(max_tokens=64, prompt=self._PROBE_PROMPT)
        assert response.text == "generated output"
        assert response.finish_reason == "eos"

    @pytest.mark.asyncio
    async def test_run_probe_and_generate_share_identical_generation_contract(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        backend, _tokenizer = self._inject_fakes(monkeypatch)
        probe = backend.run_probe(max_tokens=64, prompt=self._PROBE_PROMPT)
        generated = await backend.generate(
            prompt=self._PROBE_PROMPT, temperature=0.0, max_tokens=64
        )
        assert probe.text == generated.text
        assert probe.finish_reason == generated.finish_reason
        assert probe.token_usage == generated.token_usage
        torch_mod = sys.modules["torch"]
        assert torch_mod._seed == 0

    def test_run_probe_never_calls_asyncio_run(self) -> None:
        import ast
        import inspect

        module_path = Path(inspect.getfile(KaggleQwenBackend))
        tree = ast.parse(module_path.read_text(encoding="utf-8"))

        top_imports: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                top_imports.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                top_imports.append(node.module or "")
        assert "asyncio" not in top_imports, (
            "no top-level asyncio import allowed; run_probe must run inline",
        )

        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "run"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "asyncio"
        ]
        assert not calls, "run_probe must not invoke asyncio.run"


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
        _install_fake_torch_modules(monkeypatch)
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

    def test_bnb_nf4_load_passes_low_cpu_mem_usage(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Qwen14B NF4 v4 closure: BNB loading must avoid the full-precision copy."""
        self._install_runtime_fakes(monkeypatch)
        checkpoint = _fourteen_b_checkpoint(tmp_path)
        backend = KaggleQwenBackend(
            model_path=str(checkpoint), quantization_mode="bnb-nf4"
        )
        backend._load_model()
        assert _FakeAutoModelForCausalLM.last_kwargs["low_cpu_mem_usage"] is True
        assert _FakeAutoModelForCausalLM.last_kwargs["quantization_config"] is (
            _FakeBitsAndBytesConfig.last_instance
        )

    def test_bnb_int8_load_passes_low_cpu_mem_usage(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_runtime_fakes(monkeypatch)
        checkpoint = _seven_b_checkpoint(tmp_path)
        backend = KaggleQwenBackend(
            model_path=str(checkpoint), quantization_mode="bnb-int8"
        )
        backend._load_model()
        assert _FakeAutoModelForCausalLM.last_kwargs["low_cpu_mem_usage"] is True
        assert _FakeAutoModelForCausalLM.last_kwargs["quantization_config"] is (
            _FakeBitsAndBytesConfig.last_instance
        )

    def test_fp16_load_does_not_set_low_cpu_mem_usage(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_runtime_fakes(monkeypatch)
        checkpoint = _fourteen_b_checkpoint(tmp_path)
        backend = KaggleQwenBackend(
            model_path=str(checkpoint), quantization_mode="fp16"
        )
        backend._load_model()
        assert "low_cpu_mem_usage" not in _FakeAutoModelForCausalLM.last_kwargs

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
        _install_fake_torch_modules(monkeypatch)
        backend = self._install_backend(monkeypatch, _FakeModel(output_length=10))
        gc_calls, empty_calls = self._track_cleanup(monkeypatch)

        response = await backend.generate("write code", max_tokens=64)
        assert response.text == "generated output"
        assert gc_calls == [1], "gc.collect must run exactly once after success"
        assert empty_calls == [1], "torch.cuda.empty_cache must run exactly once after success"

    @pytest.mark.asyncio
    async def test_cleanup_after_oom(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_fake_torch_modules(monkeypatch)
        oom = type("OutOfMemoryError", (RuntimeError,), {"__module__": "torch.cuda"})
        backend = self._install_backend(monkeypatch, _RaisingModel(oom("simulated CUDA OOM")))
        gc_calls, empty_calls = self._track_cleanup(monkeypatch)

        with pytest.raises(ModelBackendError, match="out-of-memory"):
            await backend.generate("write code")
        assert gc_calls == [1], "gc.collect must run exactly once after OOM"
        assert empty_calls == [1], "torch.cuda.empty_cache must run exactly once after OOM"

    @pytest.mark.asyncio
    async def test_cleanup_after_other_generation_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_fake_torch_modules(monkeypatch)
        backend = self._install_backend(monkeypatch, _RaisingModel(RuntimeError("boom")))
        gc_calls, empty_calls = self._track_cleanup(monkeypatch)

        with pytest.raises(ModelBackendError, match="boom"):
            await backend.generate("write code")
        assert gc_calls == [1], "gc.collect must run exactly once after a generic generation exception"
        assert empty_calls == [1], "torch.cuda.empty_cache must run exactly once after a generic exception"


class TestCacheImplementationAlwaysOffloaded:
    """Every generation path must pass cache_implementation='offloaded' to model.generate()."""

    def _install_model(self, monkeypatch: pytest.MonkeyPatch) -> _FakeModel:
        _install_fake_torch_modules(monkeypatch)
        model = _FakeModel(output_length=10)
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = _FakeTokenizer()
        backend._model = model
        return model

    @pytest.mark.asyncio
    async def test_generate_passes_offloaded_cache(self, monkeypatch: pytest.MonkeyPatch) -> None:
        model = self._install_model(monkeypatch)
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = _FakeTokenizer()
        backend._model = model
        await backend.generate("write code", max_tokens=64)
        assert model.last_generate_kwargs.get("cache_implementation") == "offloaded"

    def test_run_probe_passes_offloaded_cache(self, monkeypatch: pytest.MonkeyPatch) -> None:
        model = self._install_model(monkeypatch)
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = _FakeTokenizer()
        backend._model = model
        backend.run_probe(max_tokens=64, prompt="def add(a, b):\n    return a + b\n")
        assert model.last_generate_kwargs.get("cache_implementation") == "offloaded"

    @pytest.mark.asyncio
    async def test_oom_still_passes_offloaded_cache(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """OOM on generate still uses cache_implementation='offloaded' before raising."""
        model = self._install_model(monkeypatch)
        oom = type("OutOfMemoryError", (RuntimeError,), {"__module__": "torch.cuda"})

        def _oom_generate(**kw: object) -> _FakeTensor:
            model.last_generate_kwargs = dict(kw)
            raise oom("simulated CUDA OOM")

        model.generate = _oom_generate  # type: ignore[assignment]
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = _FakeTokenizer()
        backend._model = model
        with pytest.raises(ModelBackendError, match="out-of-memory"):
            await backend.generate("write code", max_tokens=64)
        assert model.last_generate_kwargs.get("cache_implementation") == "offloaded"


class _FakeCalibratingTokenizer:
    """Tokenizer where character count != token count (1 token = 3 chars)."""

    eos_token_id = 1

    def __init__(self, tokens_per_char: float = 1 / 3) -> None:
        self.apply_calls = 0
        self.last_messages: object | None = None
        self._tokens_per_char = tokens_per_char
        self.apply_chat_template = self._apply

    def _apply(self, messages: object, tokenize: bool = False, add_generation_prompt: bool = False) -> str:
        self.apply_calls += 1
        self.last_messages = messages
        # Build a formatted string whose length is proportional to the input
        # content, so that _compute_probe_repeat_count exponential search works.
        parts: list[str] = []
        if isinstance(messages, list):
            for msg in messages:
                if isinstance(msg, dict):
                    parts.append(str(msg.get("content", "")))
        joined = "".join(parts)
        # Add overhead tokens (chat template overhead)
        return "t " + joined + " e"

    def __call__(self, text: str, return_tensors: str | None = None) -> dict[str, _FakeTensor]:
        token_count = max(1, int(len(text) * self._tokens_per_char))
        return {"input_ids": _FakeTensor(token_count), "attention_mask": _FakeTensor(token_count)}

    def decode(self, ids: object, skip_special_tokens: bool = True) -> str:
        return "generated output"


class TestLongContextProbeTokenCalibration:
    """E: Long-context calibration must use actual tokenizer, not char-length."""

    def _install_fakes(self, monkeypatch: pytest.MonkeyPatch) -> tuple[_FakeModel, _FakeCalibratingTokenizer]:
        _install_fake_torch_modules(monkeypatch)
        tokenizer = _FakeCalibratingTokenizer(tokens_per_char=1 / 3)
        model = _FakeModel(output_length=512)
        return model, tokenizer

    def test_probe_repeats_until_target_tokens_reached(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        model, tokenizer = self._install_fakes(monkeypatch)
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = tokenizer
        backend._model = model
        result = backend.run_long_context_probe(target_prompt_tokens=100, max_tokens=10)
        assert result["passed"] is True
        assert result["prompt_tokens"] >= 100
        assert result["completion_tokens"] > 0
        assert result["cache_implementation"] == "offloaded"

    def test_minimal_repeat_count_is_deterministic(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_fake_torch_modules(monkeypatch)
        tokenizer = _FakeCalibratingTokenizer(tokens_per_char=1 / 5)
        model = _FakeModel(output_length=512)
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = tokenizer
        backend._model = model

        r1 = backend.run_long_context_probe(target_prompt_tokens=50, max_tokens=10)
        r2 = backend.run_long_context_probe(target_prompt_tokens=50, max_tokens=10)
        assert r1["prompt_tokens"] == r2["prompt_tokens"]
        assert r1["completion_tokens"] == r2["completion_tokens"]

    def test_long_context_probe_passes_offloaded_cache(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """H: Long-context probe must pass cache_implementation='offloaded'."""
        model, _tokenizer = self._install_fakes(monkeypatch)
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = _FakeCalibratingTokenizer()
        backend._model = model
        backend.run_long_context_probe(target_prompt_tokens=100, max_tokens=10)
        assert model.last_generate_kwargs.get("cache_implementation") == "offloaded"


class TestSingleModelLoad:
    """F: model-preflight creates/loads exactly ONE backend/model."""

    def test_preflight_reuses_shared_backend(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        from benchmark.core.models import LLMResponse, TokenUsage
        from benchmark.execution import preflight as pf_mod

        load_count = 0
        probe_count = 0

        class CountingBackend:
            def __init__(self, **kwargs: object) -> None:
                nonlocal load_count
                load_count += 1
                self.model_identity = "qwen:test"
                self.quantization_mode = "bnb-int8"
                self.checkpoint_basename = "test"
                self.checkpoint_quantization_method = ""
                self.model_memory_footprint_bytes = 4000000000
                self.device_map_summary = "cuda:0"

            def load(self) -> None:
                pass

            def run_probe(self, max_tokens: int = 64, prompt: str = "") -> LLMResponse:
                nonlocal probe_count
                probe_count += 1
                return LLMResponse(
                    text="ok",
                    token_usage=TokenUsage(prompt_tokens=8, completion_tokens=64, total_tokens=72),
                    finish_reason="eos",
                )

        monkeypatch.setattr(pf_mod, "_python_runtime_status", lambda: ("3.12.13", True))
        monkeypatch.setattr(
            pf_mod,
            "collect_dependency_versions",
            lambda: (("django", "5.2.16"),),
        )
        staged = tmp_path / "staged"
        staged.mkdir()
        monkeypatch.setattr(pf_mod, "_stage_baseline_workspace", lambda data_dir, root: staged)
        monkeypatch.setattr(
            pf_mod, "_run_in_workspace", lambda ws, *a, **kw: (0, "", "")
        )

        monkeypatch.setattr(pf_mod, "_create_qwen_backend", lambda mp, qm: CountingBackend())

        gpu_snapshot = pf_mod.GpuVramSnapshot(
            device_index=0, gpu_name="T4",
            allocated_gib=12.5, reserved_gib=14.0,
            free_gib=2.5, total_gib=14.56,
        )

        def fake_probe(mp, qm, **kw):
            return {
                "model_identity": "qwen:test",
                "requested_quantization_mode": qm,
                "model_checkpoint_basename": "test",
                "checkpoint_quantization_method": "",
                "model_memory_footprint_bytes": 4000000000,
                "device_map_summary": "cuda:0",
                "requested_attn_implementation": "sdpa",
                "effective_attn_implementation": "sdpa",
                "sdpa_kernel_policy": "flash_or_efficient_no_math",
                "gpu_count": 1,
                "gpu_name": "T4",
                "gpu_vram_by_device": (gpu_snapshot,),
                "allocated_vram_gib": 12.5,
                "reserved_vram_gib": 14.0,
                "free_vram_after_probe_gib": 2.5,
                "probe_prompt_tokens": 8,
                "probe_completion_tokens": 64,
            }

        monkeypatch.setattr(pf_mod, "_qwen_probe_metrics", fake_probe)
        monkeypatch.setattr(pf_mod, "_run_long_context_probe", lambda mp, qm, **kw: {
            "passed": True,
            "prompt_tokens": 12000,
            "target_prompt_tokens": 12000,
            "completion_tokens": 64,
            "elapsed_seconds": 0.1,
            "cache_implementation": "offloaded",
            "requested_attn_implementation": "sdpa",
            "effective_attn_implementation": "sdpa",
            "sdpa_kernel_policy": "flash_or_efficient_no_math",
        })

        result = pf_mod.run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
        )
        assert result.passed is True
        assert load_count == 1


class _PolicyProbingModel(_FakeModel):
    """_FakeModel that records the SDPA policy state at generate() time."""

    def __init__(self, output_length: int, fake_torch: types.ModuleType) -> None:
        super().__init__(output_length)
        self._fake_torch = fake_torch
        self.policy_active_at_generate: bool | None = None
        self.policy_allowed_at_generate: list[str] = []

    def generate(self, **kwargs: object) -> _FakeTensor:
        recorder = self._fake_torch.sdpa_recorder
        self.policy_active_at_generate = bool(recorder["active"])
        self.policy_allowed_at_generate = list(recorder["active_allowed"])
        return super().generate(**kwargs)


def _assert_canonical_sdpa_policy(
    calls: list[list[str]],
    active: bool,
    allowed_at_generate: list[str],
) -> None:
    """The v0.9.22 attention contract, encoded independently of production code.

    A malformed implementation that claims ``sdpa`` but permits only the
    quadratic math fallback must fail at least one assertion here.
    """
    assert calls, "CUDA generation must enter an sdpa_kernel policy context"
    allowed = set(calls[-1])
    assert "MATH" not in allowed, f"math fallback permitted: {allowed}"
    assert allowed & {"FLASH_ATTENTION", "EFFICIENT_ATTENTION"}, (
        f"no fused/memory-efficient backend permitted: {allowed}"
    )
    assert active, "policy must be ACTIVE while model.generate() runs"
    assert "MATH" not in set(allowed_at_generate)


class TestSDPAAttentionContract:
    """V0.9.22: explicit SDPA + fail-closed fused-kernel policy on CUDA.

    v0.9.21 target evidence: the 12,044-token probe attempted a 21.62 GiB
    allocation == the full float32 40-head 12044x12044 attention matrix,
    proving the effective attention path materialized the quadratic math
    fallback. These tests lock the replacement contract.
    """

    def _install_backend(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_torch: types.ModuleType,
    ) -> tuple[KaggleQwenBackend, _PolicyProbingModel]:
        tokenizer = _FakeTokenizer()
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = tokenizer
        model = _PolicyProbingModel(output_length=18, fake_torch=fake_torch)
        backend._model = model
        return backend, model

    def test_from_pretrained_receives_explicit_sdpa_nf4(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _install_fake_torch_modules(monkeypatch)
        monkeypatch.setitem(sys.modules, "transformers", _FakeTransformers())
        checkpoint = _fourteen_b_checkpoint(tmp_path)
        backend = KaggleQwenBackend(
            model_path=str(checkpoint), quantization_mode="bnb-nf4"
        )
        backend._load_model()
        assert _FakeAutoModelForCausalLM.last_kwargs["attn_implementation"] == "sdpa"
        assert _FakeAutoModelForCausalLM.last_kwargs["device_map"] == "auto"

    @pytest.mark.parametrize("mode", ["bnb-int8", "fp16"])
    def test_from_pretrained_receives_explicit_sdpa_other_modes(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mode: str
    ) -> None:
        _install_fake_torch_modules(monkeypatch)
        monkeypatch.setitem(sys.modules, "transformers", _FakeTransformers())
        checkpoint = _fourteen_b_checkpoint(tmp_path)
        backend = KaggleQwenBackend(model_path=str(checkpoint), quantization_mode=mode)
        backend._load_model()
        assert _FakeAutoModelForCausalLM.last_kwargs["attn_implementation"] == "sdpa"

    def test_cuda_generation_runs_inside_fused_no_math_policy(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_torch = _install_fake_torch_modules(monkeypatch)
        backend, model = self._install_backend(monkeypatch, fake_torch)
        response = backend.run_probe(max_tokens=16, prompt="def add(a, b):\n    return a + b\n")
        assert response.text == "generated output"
        recorder = fake_torch.sdpa_recorder
        _assert_canonical_sdpa_policy(
            recorder["calls"],
            # The context has been exited by the time we assert; the recorded
            # call list and the state captured INSIDE generate are the evidence.
            model.policy_active_at_generate or False,
            model.policy_allowed_at_generate,
        )

    def test_generate_contract_matches_probe_contract(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import asyncio

        fake_torch = _install_fake_torch_modules(monkeypatch)
        backend, model = self._install_backend(monkeypatch, fake_torch)
        asyncio.run(backend.generate("write code", max_tokens=16))
        recorder = fake_torch.sdpa_recorder
        _assert_canonical_sdpa_policy(
            recorder["calls"],
            model.policy_active_at_generate or False,
            model.policy_allowed_at_generate,
        )

    def test_non_cuda_generation_preserves_current_behavior(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _CpuCuda(_FakeCuda):
            def is_available(self) -> bool:
                return False

        fake_torch = _install_fake_torch_modules(monkeypatch)
        fake_torch.cuda = _CpuCuda()  # type: ignore[assignment]
        backend, _model = self._install_backend(monkeypatch, fake_torch)
        response = backend.run_probe(max_tokens=16, prompt="def add(a, b):\n    return a + b\n")
        assert response.text == "generated output"
        assert fake_torch.sdpa_recorder["calls"] == [], (
            "non-CUDA execution must not require the CUDA kernel policy"
        )

    def test_missing_sdpa_api_on_cuda_fails_closed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CUDA runtime without torch.nn.attention must FAIL, never fall back.

        Order-independent regression guard: a previously imported
        ``torch.nn.attention`` child module can linger in ``sys.modules``
        from an earlier test. The cached child must be dropped before the
        fake no-attention runtime is installed, otherwise the lazy import in
        ``_sdpa_kernel_policy_context`` is satisfied from the cache and the
        fail-closed contract silently degrades.
        """
        cached_attention = types.ModuleType("torch.nn.attention")
        cached_attention.SDPBackend = _FakeSDPBackend  # type: ignore[attr-defined]
        cached_recorder: dict[str, Any] = {
            "calls": [],
            "active": False,
            "active_allowed": [],
            "depth": 0,
        }
        cached_attention.sdpa_kernel = _FakeSdpaKernelFactory(cached_recorder)  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "torch.nn.attention", cached_attention)
        monkeypatch.delitem(sys.modules, "torch.nn.attention", raising=False)
        fake_torch = _FakeTorch()
        fake_torch.nn = types.ModuleType("torch.nn")  # no .attention attribute
        monkeypatch.setitem(sys.modules, "torch", fake_torch)
        monkeypatch.setitem(sys.modules, "torch.nn", fake_torch.nn)  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "transformers", _build_fake_transformers())
        tokenizer = _FakeTokenizer()
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = tokenizer
        backend._model = _FakeModel(output_length=10)
        with pytest.raises(ModelBackendError, match="sdpa_kernel"):
            backend.run_probe(max_tokens=8, prompt="def add():\n    pass\n")

    def test_math_only_sdpa_claim_does_not_satisfy_the_contract(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """RED discriminator: a 'sdpa' claim that permits only MATH must fail."""
        fake_torch = _install_fake_torch_modules(monkeypatch)

        class _MathOnlyFactory(_FakeSdpaKernelFactory):
            def __call__(self, backends: Any) -> _RecordingSdpaPolicyContext:
                return super().__call__([_FakeSDPBackend.MATH])

        fake_torch.nn.attention.sdpa_kernel = _MathOnlyFactory(fake_torch.sdpa_recorder)  # type: ignore[attr-defined]
        backend, model = self._install_backend(monkeypatch, fake_torch)
        backend.run_probe(max_tokens=8, prompt="def add():\n    pass\n")
        # The malformed policy WAS actually entered during generation...
        assert fake_torch.sdpa_recorder["calls"][-1] == ["MATH"]
        # ...and the contract STILL rejects it.
        with pytest.raises(AssertionError):
            _assert_canonical_sdpa_policy(
                fake_torch.sdpa_recorder["calls"],
                model.policy_active_at_generate or False,
                model.policy_allowed_at_generate,
            )


class TestAttentionEvidenceProperties:
    """Task C: requested/effective/policy attention evidence on the backend."""

    def test_requested_and_policy_constants(self) -> None:
        from benchmark.llm.kaggle_qwen_backend import (
            KAGGLE_ATTENTION_IMPLEMENTATION,
            KAGGLE_SDPA_KERNEL_POLICY,
        )

        backend = KaggleQwenBackend()
        assert KAGGLE_ATTENTION_IMPLEMENTATION == "sdpa"
        assert KAGGLE_SDPA_KERNEL_POLICY == "flash_or_efficient_no_math"
        assert backend.requested_attention_implementation == "sdpa"
        assert backend.sdpa_kernel_policy == "flash_or_efficient_no_math"

    def test_effective_attention_empty_before_load(self) -> None:
        backend = KaggleQwenBackend()
        assert backend.effective_attention_implementation == ""

    def test_effective_attention_reads_model_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_fake_torch_modules(monkeypatch)
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = _FakeTokenizer()
        model = _FakeModel(output_length=8)
        model.config = types.SimpleNamespace(_attn_implementation="sdpa")  # type: ignore[attr-defined]
        backend._model = model
        assert backend.effective_attention_implementation == "sdpa"

    def test_long_context_probe_reports_attention_evidence(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from benchmark.llm.kaggle_qwen_backend import (
            KAGGLE_ATTENTION_IMPLEMENTATION,
            KAGGLE_SDPA_KERNEL_POLICY,
        )

        _install_fake_torch_modules(monkeypatch)
        model = _FakeModel(output_length=512)
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = _FakeCalibratingTokenizer()
        model.config = types.SimpleNamespace(_attn_implementation="sdpa")  # type: ignore[attr-defined]
        backend._model = model
        evidence = backend.run_long_context_probe(target_prompt_tokens=100, max_tokens=10)
        assert evidence["requested_attn_implementation"] == KAGGLE_ATTENTION_IMPLEMENTATION
        assert evidence["effective_attn_implementation"] == "sdpa"
        assert evidence["sdpa_kernel_policy"] == KAGGLE_SDPA_KERNEL_POLICY


class TestOOMDiagnosisLongPrompt:
    """Task D: long-prompt OOM must diagnose prompt-prefill attention, not the
    completion budget. Target evidence: v0.9.21 failed a max_tokens=64 probe
    yet the old message advised reducing max_completion_tokens_per_call."""

    def _oom_backend(
        self, monkeypatch: pytest.MonkeyPatch, token_length: int
    ) -> KaggleQwenBackend:
        _install_fake_torch_modules(monkeypatch)
        oom = type("OutOfMemoryError", (RuntimeError,), {"__module__": "torch.cuda"})
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = _FakeTokenizer(token_length=token_length)
        backend._model = _RaisingModel(oom("CUDA out of memory. Tried to allocate 21.62 GiB"))
        return backend

    def test_long_prompt_oom_reports_prefill_attention_not_completion_cap(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from benchmark.llm.kaggle_qwen_backend import LONG_PROMPT_PREFILL_OOM_TOKEN_THRESHOLD

        backend = self._oom_backend(monkeypatch, token_length=12044)
        assert LONG_PROMPT_PREFILL_OOM_TOKEN_THRESHOLD <= 12044
        with pytest.raises(ModelBackendError) as exc_info:
            backend.run_long_context_probe(target_prompt_tokens=12000, max_tokens=64)
        message = str(exc_info.value)
        assert "prompt_tokens=12044" in message
        assert "requested_completion_tokens=64" in message
        lowered = message.lower()
        assert "prefill" in lowered
        assert "attention implementation" in lowered
        assert "flash_or_efficient_no_math" in message
        assert "free_gib=" in message
        assert "Reduce max_completion_tokens_per_call" not in message
        assert exc_info.value.__cause__ is not None

    def test_short_prompt_oom_keeps_completion_advice(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        backend = self._oom_backend(monkeypatch, token_length=8)
        with pytest.raises(ModelBackendError) as exc_info:
            backend.run_probe(max_tokens=1024, prompt="short")
        message = str(exc_info.value)
        assert "Reduce max_completion_tokens_per_call" in message
        assert exc_info.value.__cause__ is not None


class TestPreservedMemoryFixesV0922:
    """Task E/F regression guards: no prior memory fix may regress."""

    def test_transformers_pin_remains_4_57_6(self) -> None:
        from benchmark.execution.preflight import _REQUIRED_IMPORTS

        assert ("transformers", "transformers", "transformers", "4.57.6") in _REQUIRED_IMPORTS

    def test_long_context_gate_constants_unchanged(self) -> None:
        from benchmark.execution.preflight import (
            LONG_CONTEXT_MAX_TOKENS,
            LONG_CONTEXT_TARGET_PROMPT_TOKENS,
        )

        assert LONG_CONTEXT_TARGET_PROMPT_TOKENS == 12000
        assert LONG_CONTEXT_MAX_TOKENS == 64

    def test_offloaded_cache_constant_unchanged(self) -> None:
        from benchmark.llm.kaggle_qwen_backend import KAGGLE_CACHE_IMPLEMENTATION

        assert KAGGLE_CACHE_IMPLEMENTATION == "offloaded"

    def test_nf4_load_config_unchanged(self) -> None:
        from benchmark.llm.kaggle_qwen_backend import NF4_LOAD_CONFIG

        assert NF4_LOAD_CONFIG == {
            "load_in_4bit": True,
            "bnb_4bit_quant_type": "nf4",
            "bnb_4bit_compute_dtype": "float16",
            "bnb_4bit_use_double_quant": True,
        }


class _DeadlineDecodingModel(_FakeModel):
    """Drives the installed stopping criteria per decode step, like real HF.

    The workflow-deadline criterion is polled once per step; when it returns
    True (deadline fired) generation stops. The returned tensor reflects the
    sequence length observed when the deadline fired.
    """

    def __init__(self, prompt_tokens: int = 8, max_steps: int = 64) -> None:
        super().__init__(output_length=11)
        self._prompt_tokens = prompt_tokens
        self._max_steps = max_steps
        self.last_generate_kwargs: dict[str, object] = {}

    def generate(self, **kwargs: object) -> _FakeTensor:
        self.last_generate_kwargs = dict(kwargs)
        criteria = list(kwargs.get("stopping_criteria") or ())  # type: ignore[arg-type]
        fired = False
        seq = self._prompt_tokens
        for _step in range(self._max_steps):
            seq += 1
            for c in criteria:
                if c(_FakeTensor(length=seq)):  # type: ignore[operator]
                    fired = True
                    break
            if fired:
                break
        return _FakeTensor(length=seq)


class TestWorkflowDeadlineStoppingCriteria:
    """D9.1: parametric deadline/heartbeat stopping criterion (no model)."""

    def _criterion(self, **kw: object) -> Any:
        from benchmark.llm.kaggle_qwen_backend import _WorkflowDeadlineHeartbeatStoppingCriteria

        base: dict[str, object] = dict(
            prompt_length=5,
            max_completion=64,
            model_call_guard=lambda: True,
            clock=lambda: 1.0,
        )
        base.update(kw)
        return _WorkflowDeadlineHeartbeatStoppingCriteria(**base)  # type: ignore[arg-type]

    def test_never_fires_while_guard_true(self) -> None:
        crit = self._criterion(prompt_length=5)
        assert crit(_FakeTensor(length=8)) is False
        assert crit.deadline_fired is False
        assert crit.observed_tokens == 3

    def test_fires_when_guard_goes_false(self) -> None:
        crit = self._criterion(model_call_guard=lambda: False, clock=lambda: 10.0)
        assert crit(_FakeTensor(length=8)) is True
        assert crit.deadline_fired is True
        assert crit.observed_tokens == 3
        assert crit.elapsed_seconds == 0.0

    def test_terminal_repeat_does_not_repeat_log(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        crit = self._criterion(model_call_guard=lambda: False, clock=lambda: 10.0)
        with caplog.at_level(logging.INFO):
            crit(_FakeTensor(length=8))
            crit(_FakeTensor(length=8))
        assert (
            sum("GENERATION_STOPPED" in r.message for r in caplog.records) == 1
        )

    def test_heartbeat_emitted_at_interval(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        current = [0.0]

        def growing_clock() -> float:
            current[0] += 1.0
            return current[0]

        crit = self._criterion(
            model_call_guard=lambda: True,
            clock=growing_clock,
            heartbeat_interval=1.0,
        )
        with caplog.at_level(logging.INFO):
            crit(_FakeTensor(length=8))
            crit(_FakeTensor(length=8))
            crit(_FakeTensor(length=8))
        assert crit.heartbeat_count >= 2
        assert any("GENERATION_RUNNING" in r.message for r in caplog.records)

    def test_default_heartbeat_interval_is_30s(self) -> None:
        from benchmark.llm.kaggle_qwen_backend import DEFAULT_HEARTBEAT_INTERVAL_SECONDS

        assert DEFAULT_HEARTBEAT_INTERVAL_SECONDS == 30.0


class TestGenerateSyncDeadlinePath:
    """D9.1: an in-flight workflow-deadline fires finish_reason='timeout' with a
    partial completion, and the shared backend guard is honored."""

    def _loaded_backend(
        self, monkeypatch: pytest.MonkeyPatch, model: _FakeModel
    ) -> KaggleQwenBackend:
        _install_fake_torch_modules(monkeypatch)
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = _FakeTokenizer()
        backend._model = model
        return backend

    def test_deadline_fires_timeout_with_partial_tokens(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        model = _DeadlineDecodingModel(prompt_tokens=8)
        backend = self._loaded_backend(monkeypatch, model)

        counter = {"n": 0}
        guard_limit = 3

        def canary_guard() -> bool:
            counter["n"] += 1
            return counter["n"] <= guard_limit

        response = backend._generate_sync(
            prompt="def add(a, b):\n    return a + b\n",
            temperature=0.0,
            max_tokens=128,
            model_call_guard=canary_guard,
            heartbeat_interval=3600.0,
        )
        assert response.finish_reason == "timeout"
        assert response.token_usage.completion_tokens >= 1
        assert response.token_usage.completion_tokens <= 8

    def test_shared_guard_installed_via_set_model_call_guard(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        model = _DeadlineDecodingModel(prompt_tokens=8)
        backend = self._loaded_backend(monkeypatch, model)

        fired = {"n": 0}

        def always_false() -> bool:
            fired["n"] += 1
            return False

        backend.set_model_call_guard(always_false)
        response = backend._generate_sync(
            prompt="x", temperature=0.0, max_tokens=16,
            heartbeat_interval=3600.0,
        )
        assert response.finish_reason == "timeout"
        assert fired["n"] >= 1


class TestRunGenerationDeadlineProbe:
    """D9.1/D9.3: the real-backend canary returns canonical evidence and never
    leaks the guard onto the shared backend."""

    def _loaded_backend(
        self, monkeypatch: pytest.MonkeyPatch, model: _FakeModel
    ) -> KaggleQwenBackend:
        _install_fake_torch_modules(monkeypatch)
        backend = KaggleQwenBackend()
        backend._loaded = True
        backend._tokenizer = _FakeTokenizer()
        backend._model = model
        return backend

    def test_probe_returns_canonical_evidence_and_resets_guard(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        backend = self._loaded_backend(
            monkeypatch, _DeadlineDecodingModel(prompt_tokens=8)
        )
        evidence = backend.run_generation_deadline_probe()
        assert evidence == {
            "passed": True,
            "deadline_fired": True,
            "finish_reason": "timeout",
            "completion_tokens": evidence["completion_tokens"],
            "max_checks_before_deadline": 3,
        }
        # guard reset: no deadline guard remains on the shared backend
        assert backend._model_call_guard is None

    def test_probe_fails_closed_when_deadline_does_not_fire(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A normal model that does not drive the criterion to fire -> the probe
        # must raise rather than report a false PASS.
        backend = self._loaded_backend(monkeypatch, _FakeModel(output_length=10))
        with pytest.raises(RuntimeError, match="expected finish_reason='timeout'"):
            backend.run_generation_deadline_probe()

    def test_probe_bounds_completion_by_canonical_max_check_bound(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from benchmark.llm.kaggle_qwen_backend import (
            GENERATION_DEADLINE_PROBE_MAX_CHECK_BOUND,
        )

        assert GENERATION_DEADLINE_PROBE_MAX_CHECK_BOUND == 8
        backend = self._loaded_backend(
            monkeypatch, _DeadlineDecodingModel(prompt_tokens=8)
        )
        evidence = backend.run_generation_deadline_probe()
        assert 1 <= evidence["completion_tokens"] <= 8
