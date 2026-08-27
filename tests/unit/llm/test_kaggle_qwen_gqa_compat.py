from __future__ import annotations

import sys
import types
from typing import Any

import pytest

import benchmark.llm.kaggle_qwen_backend as backend_mod
from benchmark.llm.kaggle_qwen_backend import (
    KAGGLE_SDPA_GQA_COMPATIBILITY,
    KAGGLE_SDPA_KERNEL_POLICY,
    _gqa_microprobe_build_qkv,
    _gqa_microprobe_expand_kv,
    _reset_sm75_gqa_compat_sentinel,
    _sm75_gqa_compat_active,
    probe_sdpa_gqa_kernel_compatibility,
)


class _FakeDevice:
    def __init__(self, index: int) -> None:
        self.type = "cuda"
        self.index = index

    def __str__(self) -> str:
        return f"cuda:{self.index}"

    def __repr__(self) -> str:
        return f"cuda:{self.index}"


class _FakeTensor:
    def __init__(self, shape: tuple[int, ...], dtype: Any = None, device: Any = None) -> None:
        self.shape = tuple(shape)
        self.dtype = dtype
        # A real device string like "cuda:0" proves tensors are allocated on the
        # exact GPU being tested (the probe records this in per-device evidence).
        self.device = str(device) if device is not None else "cpu"

    def size(self, dim: int) -> int:
        return self.shape[dim]

    def expand(self, *dims: int) -> _FakeTensor:
        new = list(self.shape)
        for i, d in enumerate(dims):
            if d != -1:
                new[i] = d
        return _FakeTensor(tuple(new), self.dtype, self.device)

    def repeat_interleave(self, repeats: int, dim: int) -> _FakeTensor:
        new = list(self.shape)
        new[dim] = new[dim] * repeats
        return _FakeTensor(tuple(new), self.dtype, self.device)

    def all(self) -> bool:  # numpy-style reduction used via torch.isfinite(...).all()
        return True

    def __repr__(self) -> str:
        return f"_FakeTensor{self.shape}"


class _NullCtx:
    def __enter__(self) -> _NullCtx:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


class _RecordingSdpaKernel:
    def __init__(self, state: dict[str, Any]) -> None:
        self._state = state

    def __call__(self, backends: Any) -> Any:
        self._state["allowed"] = [str(getattr(b, "name", b)) for b in backends]
        return _NullCtx()


class _FakeSDPBackend:
    FLASH_ATTENTION = "FLASH_ATTENTION"
    EFFICIENT_ATTENTION = "EFFICIENT_ATTENTION"
    MATH = "MATH"


class _NoRepeatKvFunctional:
    """Functional module WITHOUT ``torch.nn.functional.repeat_kv``.

    D1: the microprobe must not depend on a fabricated PyTorch functional API,
    so this deliberately omits ``repeat_kv``. If the production code referenced it,
    the probe would raise AttributeError and fail the test.
    """

    def scaled_dot_product_attention(self, q: _FakeTensor, k: _FakeTensor, v: _FakeTensor) -> _FakeTensor:
        return _FakeTensor(q.shape, q.dtype, q.device)


class _SetDeviceLog:
    def __init__(self) -> None:
        self.calls: list[Any] = []


def _make_fake_torch(
    capability: tuple[int, int] = (7, 5),
    device_count: int = 1,
    sdpa_state: dict[str, Any] | None = None,
) -> types.ModuleType:
    torch = types.ModuleType("torch")
    torch.float16 = "float16"

    def _device(*args: Any) -> _FakeDevice:
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, str):
                if ":" in arg:
                    return _FakeDevice(int(arg.split(":")[1]))
                return _FakeDevice(0)
            if isinstance(arg, _FakeDevice):
                return arg
        if len(args) == 2:
            kind, idx = args
            if str(kind).startswith("cuda"):
                return _FakeDevice(int(idx))
            return _FakeDevice(0)
        return _FakeDevice(0)

    torch.device = staticmethod(_device)

    def _randn(*shape_and_kw: Any, dtype: Any = None, device: Any = None) -> _FakeTensor:
        shape = tuple(int(s) for s in shape_and_kw)
        return _FakeTensor(shape, dtype, device)

    torch.randn = staticmethod(_randn)
    torch.isfinite = staticmethod(lambda t: t)

    state = sdpa_state if sdpa_state is not None else {"allowed": []}

    class _Cuda:
        def is_available(self) -> bool:
            return True

        def device_count(self) -> int:
            return device_count

        def get_device_name(self, index: int) -> str:
            return "fake-t4" if capability == (7, 5) else "fake-a100"

        def get_device_capability(self, index: int) -> tuple[int, int]:
            return capability

        def get_device_properties(self, index: int) -> Any:
            return types.SimpleNamespace(total_memory=1024**3)

        def memory_allocated(self, index: int = 0) -> int:
            return 0

        def memory_reserved(self, index: int = 0) -> int:
            return 0

        def empty_cache(self) -> None:
            return None

        def current_device(self) -> int:
            return 0

        def set_device(self, device: Any) -> None:
            return None

        def synchronize(self, device: Any = None) -> None:
            return None

    torch.cuda = _Cuda()

    functional = _NoRepeatKvFunctional()
    nn = types.ModuleType("torch.nn")
    attention = types.ModuleType("torch.nn.attention")
    attention.SDPBackend = _FakeSDPBackend
    attention.sdpa_kernel = _RecordingSdpaKernel(state)
    nn.attention = attention
    nn.functional = functional
    torch.nn = nn
    return torch


def _make_fake_transformers_sdpa_attention() -> types.ModuleType:
    mod = types.ModuleType("transformers.integrations.sdpa_attention")
    mod.use_gqa_in_sdpa = lambda *args: True  # native path default
    return mod


@pytest.fixture(autouse=True)
def _reset_sentinel():
    _reset_sm75_gqa_compat_sentinel()
    yield
    _reset_sm75_gqa_compat_sentinel()


def _install_fakes(
    monkeypatch: pytest.MonkeyPatch,
    capability: tuple[int, int] = (7, 5),
    device_count: int = 1,
    sdpa_state: dict[str, Any] | None = None,
) -> types.ModuleType:
    torch = _make_fake_torch(capability, device_count, sdpa_state)
    sdpa_attn = _make_fake_transformers_sdpa_attention()
    integrations = types.ModuleType("transformers.integrations")
    integrations.sdpa_attention = sdpa_attn
    transformers = types.ModuleType("transformers")
    transformers.integrations = integrations
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "torch.nn", torch.nn)
    monkeypatch.setitem(sys.modules, "torch.nn.attention", torch.nn.attention)
    monkeypatch.setitem(sys.modules, "transformers", transformers)
    monkeypatch.setitem(sys.modules, "transformers.integrations", integrations)
    monkeypatch.setitem(sys.modules, "transformers.integrations.sdpa_attention", sdpa_attn)
    return torch


def test_no_math_sdpa_policy_constant_is_fused_and_excludes_math() -> None:
    assert KAGGLE_SDPA_KERNEL_POLICY == "flash_or_efficient_no_math"
    # The fused policy must restrict to flash/efficient and must NOT enable math.
    assert "flash_or_efficient" in KAGGLE_SDPA_KERNEL_POLICY
    assert "no_math" in KAGGLE_SDPA_KERNEL_POLICY


def test_sm75_gqa_compat_install_wraps_and_forces_repeat_kv(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fakes(monkeypatch, capability=(7, 5))
    sdpa_attn = sys.modules["transformers.integrations.sdpa_attention"]
    backend_mod._install_sm75_sdpa_gqa_compatibility()
    wrapped = sdpa_attn.use_gqa_in_sdpa
    assert hasattr(wrapped, "_wrapped_original")
    # On sm75 the hook forces the repeat-KV path (returns False).
    assert wrapped() is False


def test_sm75_gqa_compat_delegates_on_non_sm75(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fakes(monkeypatch, capability=(8, 0))
    sdpa_attn = sys.modules["transformers.integrations.sdpa_attention"]
    backend_mod._install_sm75_sdpa_gqa_compatibility()
    # The hook always wraps, but on non-sm75 it delegates unchanged to the
    # original native GQA-decision function.
    assert hasattr(sdpa_attn.use_gqa_in_sdpa, "_wrapped_original")
    assert sdpa_attn.use_gqa_in_sdpa() is True


def test_sm75_gqa_compat_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fakes(monkeypatch, capability=(7, 5))
    sdpa_attn = sys.modules["transformers.integrations.sdpa_attention"]
    backend_mod._install_sm75_sdpa_gqa_compatibility()
    first = sdpa_attn.use_gqa_in_sdpa
    backend_mod._install_sm75_sdpa_gqa_compatibility()
    # Second install must not re-wrap (same object, original still reachable).
    assert sdpa_attn.use_gqa_in_sdpa is first
    assert hasattr(sdpa_attn.use_gqa_in_sdpa, "_wrapped_original")


def test_sm75_gqa_compat_active_reports_mode_only_on_sm75(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fakes(monkeypatch, capability=(7, 5))
    backend_mod._install_sm75_sdpa_gqa_compatibility()
    assert _sm75_gqa_compat_active() == KAGGLE_SDPA_GQA_COMPATIBILITY
    # A different device must not report the shim as active.
    _install_fakes(monkeypatch, capability=(8, 0))
    backend_mod._install_sm75_sdpa_gqa_compatibility()
    assert _sm75_gqa_compat_active() == ""


def test_missing_pinned_hook_symbol_fails_closed_not_active(monkeypatch: pytest.MonkeyPatch) -> None:
    # D1 req 6: if the pinned hook/symbol is absent, compatibility must NOT be
    # reported active merely because the import/sentinel path succeeded.
    torch = _make_fake_torch(capability=(7, 5))
    sdpa_attn = types.ModuleType("transformers.integrations.sdpa_attention")
    # No `use_gqa_in_sdpa` symbol at all.
    integrations = types.ModuleType("transformers.integrations")
    integrations.sdpa_attention = sdpa_attn
    transformers = types.ModuleType("transformers")
    transformers.integrations = integrations
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "torch.nn", torch.nn)
    monkeypatch.setitem(sys.modules, "torch.nn.attention", torch.nn.attention)
    monkeypatch.setitem(sys.modules, "transformers", transformers)
    monkeypatch.setitem(sys.modules, "transformers.integrations", integrations)
    monkeypatch.setitem(sys.modules, "transformers.integrations.sdpa_attention", sdpa_attn)
    backend_mod._install_sm75_sdpa_gqa_compatibility()
    # The hook cannot be active when the pinned symbol is missing; it fails
    # closed rather than claiming repeat-KV compatibility is in effect.
    assert _sm75_gqa_compat_active() == ""


def test_gqa_microprobe_build_qkv_allocates_on_requested_device(monkeypatch: pytest.MonkeyPatch) -> None:
    # D1 req 2: Q/K/V allocation records the exact requested CUDA device.
    torch = _make_fake_torch(capability=(7, 5), device_count=2)
    for index in (0, 1):
        device = torch.device("cuda", index)
        q, k, v = _gqa_microprobe_build_qkv(torch, 68, device)
        assert str(q.device) == f"cuda:{index}"
        assert str(k.device) == f"cuda:{index}"
        assert str(v.device) == f"cuda:{index}"


def test_gqa_microprobe_expand_kv_repeats_heads_without_repeat_kv_api() -> None:
    # D1 req 1: repeat-KV works with tensor ops while torch.nn.functional.repeat_kv
    # is ABSENT (the fake functional module does not define it). Expected 1/40/68/128.
    torch = _make_fake_torch()
    assert not hasattr(torch.nn.functional, "repeat_kv")
    k = _FakeTensor((1, 8, 68, 128), device="cuda:0")
    v = _FakeTensor((1, 8, 68, 128), device="cuda:0")
    k_exp, v_exp = _gqa_microprobe_expand_kv(k, v, num_key_value_groups=5)
    assert k_exp.shape == (1, 40, 68, 128)
    assert v_exp.shape == (1, 40, 68, 128)
    assert k_exp.device == "cuda:0"
    assert v_exp.device == "cuda:0"


def test_gqa_microprobe_expand_kv_rejects_non_positive_groups() -> None:
    k = _FakeTensor((1, 8, 68, 128))
    v = _FakeTensor((1, 8, 68, 128))
    with pytest.raises(ValueError):
        _gqa_microprobe_expand_kv(k, v, num_key_value_groups=0)
    with pytest.raises(ValueError):
        _gqa_microprobe_expand_kv(k, v, num_key_value_groups=-1)


def test_probe_math_absent_from_allowed_sdpa_backends(monkeypatch: pytest.MonkeyPatch) -> None:
    # D1 req 4: MATH must be absent from the allowed SDPA backends used by the probe.
    sdpa_state: dict[str, Any] = {"allowed": []}
    _install_fakes(monkeypatch, capability=(7, 5), device_count=1, sdpa_state=sdpa_state)
    result = probe_sdpa_gqa_kernel_compatibility()
    assert result["all_passed"] is True
    assert "MATH" not in sdpa_state["allowed"]
    assert sdpa_state["allowed"] == [
        _FakeSDPBackend.FLASH_ATTENTION,
        _FakeSDPBackend.EFFICIENT_ATTENTION,
    ]


def test_probe_sdpa_gqa_kernel_compatibility_sm75_all_passed(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fakes(monkeypatch, capability=(7, 5))
    result = probe_sdpa_gqa_kernel_compatibility()
    assert result["available"] is True
    assert result["all_passed"] is True
    assert result["gqa_compatibility_mode"] == KAGGLE_SDPA_GQA_COMPATIBILITY
    assert result["sdpa_kernel_policy"] == KAGGLE_SDPA_KERNEL_POLICY
    assert len(result["devices"]) == 1
    dev = result["devices"][0]
    assert dev["before_heads"] == "40/8/8"
    assert dev["after_heads"] == "40/40/40"
    assert dev["device"] == "cuda:0"
    assert dev["q_device"] == "cuda:0"
    assert dev["k_device"] == "cuda:0"
    assert dev["v_device"] == "cuda:0"
    assert dev["output_device"] == "cuda:0"
    assert dev["passed"] is True


def test_probe_enumerates_every_gpu_and_asserts_device_0_and_1(monkeypatch: pytest.MonkeyPatch) -> None:
    # D1 req 2: per-enumerated-GPU evidence; device 0 and device 1 must both be
    # asserted and each must show a CUDA device (never CPU).
    _install_fakes(monkeypatch, capability=(7, 5), device_count=2)
    result = probe_sdpa_gqa_kernel_compatibility()
    assert result["all_passed"] is True
    assert result["device_count"] == 2
    assert len(result["devices"]) == 2
    for entry in result["devices"]:
        assert entry["passed"] is True
        assert entry["device"] == f"cuda:{entry['device_index']}"
        assert entry["q_device"] == f"cuda:{entry['device_index']}"
        assert entry["output_device"] == f"cuda:{entry['device_index']}"
    assert result["devices"][0]["device_index"] == 0
    assert result["devices"][1]["device_index"] == 1


def test_probe_rejects_non_cuda_output_device(monkeypatch: pytest.MonkeyPatch) -> None:
    # D1 req 3: per-device output evidence rejects CPU or wrong-device output.
    class _WrongDeviceFunctional:
        def scaled_dot_product_attention(self, q: _FakeTensor, k: _FakeTensor, v: _FakeTensor) -> _FakeTensor:
            # Intentionally return output on "cpu" (wrong device).
            return _FakeTensor(q.shape, q.dtype, "cpu")

    torch = _make_fake_torch(capability=(7, 5), device_count=1)
    torch.nn.functional = _WrongDeviceFunctional()
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "torch.nn", torch.nn)
    monkeypatch.setitem(sys.modules, "torch.nn.attention", torch.nn.attention)
    sdpa_attn = _make_fake_transformers_sdpa_attention()
    integrations = types.ModuleType("transformers.integrations")
    integrations.sdpa_attention = sdpa_attn
    transformers = types.ModuleType("transformers")
    transformers.integrations = integrations
    monkeypatch.setitem(sys.modules, "transformers", transformers)
    monkeypatch.setitem(sys.modules, "transformers.integrations", integrations)
    monkeypatch.setitem(sys.modules, "transformers.integrations.sdpa_attention", sdpa_attn)
    result = probe_sdpa_gqa_kernel_compatibility()
    assert result["all_passed"] is False
    assert result["devices"][0]["passed"] is False
    assert result["devices"][0]["output_device"] == "cpu"
    assert "expected CUDA device" in result["devices"][0]["error"]


def test_probe_sdpa_gqa_kernel_compatibility_non_sm75_all_passed(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fakes(monkeypatch, capability=(8, 0))
    result = probe_sdpa_gqa_kernel_compatibility()
    assert result["all_passed"] is True
    assert result["gqa_compatibility_mode"] == ""
