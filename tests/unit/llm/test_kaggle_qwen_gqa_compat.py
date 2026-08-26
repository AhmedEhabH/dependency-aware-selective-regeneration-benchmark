from __future__ import annotations

import sys
import types
from typing import Any

import pytest

import benchmark.llm.kaggle_qwen_backend as backend_mod
from benchmark.llm.kaggle_qwen_backend import (
    KAGGLE_SDPA_GQA_COMPATIBILITY,
    KAGGLE_SDPA_KERNEL_POLICY,
    _gqa_microprobe_expand_kv,
    _reset_sm75_gqa_compat_sentinel,
    _sm75_gqa_compat_active,
    probe_sdpa_gqa_kernel_compatibility,
)


class _FakeTensor:
    def __init__(self, shape: tuple[int, ...], dtype: Any = None) -> None:
        self.shape = tuple(shape)
        self.dtype = dtype

    def size(self, dim: int) -> int:
        return self.shape[dim]

    def expand(self, *dims: int) -> _FakeTensor:
        new = list(self.shape)
        for i, d in enumerate(dims):
            if d != -1:
                new[i] = d
        return _FakeTensor(tuple(new), self.dtype)

    def all(self) -> bool:  # numpy-style reduction used via torch.isfinite(...).all()
        return True

    def __repr__(self) -> str:
        return f"_FakeTensor{self.shape}"


class _FakeSDPBackend:
    FLASH_ATTENTION = "FLASH_ATTENTION"
    EFFICIENT_ATTENTION = "EFFICIENT_ATTENTION"
    MATH = "MATH"


class _RecordingSdpaKernel:
    def __init__(self, state: dict[str, Any]) -> None:
        self._state = state

    def __call__(self, backends: Any) -> Any:
        self._state["allowed"] = [str(getattr(b, "name", b)) for b in backends]
        return _NullCtx()


class _NullCtx:
    def __enter__(self) -> _NullCtx:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


class _FakeFunctional:
    def repeat_kv(self, x: _FakeTensor, groups: int) -> _FakeTensor:
        s = x.shape
        return _FakeTensor((s[0], s[1] * groups, s[2], s[3]), x.dtype)

    def scaled_dot_product_attention(self, q: _FakeTensor, k: _FakeTensor, v: _FakeTensor) -> _FakeTensor:
        return _FakeTensor(q.shape, q.dtype)


def _make_fake_torch(capability: tuple[int, int] = (7, 5), device_count: int = 1) -> types.ModuleType:
    torch = types.ModuleType("torch")
    torch.float16 = "float16"
    torch.randn = staticmethod(lambda *shape, dtype=None: _FakeTensor(tuple(shape), dtype))
    torch.isfinite = staticmethod(lambda t: t)

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

    torch.cuda = _Cuda()

    functional = _FakeFunctional()
    nn = types.ModuleType("torch.nn")
    attention = types.ModuleType("torch.nn.attention")
    attention.SDPBackend = _FakeSDPBackend
    attention.sdpa_kernel = _RecordingSdpaKernel({"allowed": []})
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


def _install_fakes(monkeypatch: pytest.MonkeyPatch, capability: tuple[int, int] = (7, 5)) -> types.ModuleType:
    torch = _make_fake_torch(capability)
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


def test_gqa_microprobe_expand_kv_repeats_heads_to_query_count() -> None:
    torch = _make_fake_torch()
    k = _FakeTensor((1, 8, 68, 128))
    v = _FakeTensor((1, 8, 68, 128))
    k_exp, v_exp = _gqa_microprobe_expand_kv(torch, k, v, num_key_value_groups=5)
    assert k_exp.shape == (1, 40, 68, 128)
    assert v_exp.shape == (1, 40, 68, 128)


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
    assert dev["passed"] is True


def test_probe_sdpa_gqa_kernel_compatibility_non_sm75_all_passed(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fakes(monkeypatch, capability=(8, 0))
    result = probe_sdpa_gqa_kernel_compatibility()
    assert result["all_passed"] is True
    assert result["gqa_compatibility_mode"] == ""
