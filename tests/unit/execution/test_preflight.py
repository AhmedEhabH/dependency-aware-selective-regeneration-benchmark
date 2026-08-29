from __future__ import annotations

import argparse
import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from benchmark.execution import preflight as mod
from benchmark.execution.preflight import (
    EXPECTED_VISIBLE_GPU_COUNTS,
    MIN_FREE_VRAM_GIB,
    GpuVramSnapshot,
    KaggleSmokePreflightResult,
    RepositoryPreflightUnavailableError,
    collect_dependency_versions,
    load_repo_preflight_evidence,
    render_preflight_table,
    run_kaggle_smoke_preflight,
)


def _install_fake_torch(monkeypatch: pytest.MonkeyPatch, cuda: object) -> types.ModuleType:
    fake = types.ModuleType("torch")
    fake.cuda = cuda  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", fake)
    return fake


class FakeCuda:
    def __init__(
        self,
        devices: list[tuple[int, int, int, int, str]],
        *,
        available: bool = True,
    ) -> None:
        self._devices = devices
        self._available = available
        self.sync_calls: list[int] = []
        self.allocated_calls: list[int] = []
        self.reserved_calls: list[int] = []
        self.mem_get_info_calls: list[int] = []
        self.name_calls: list[int] = []

    def is_available(self) -> bool:
        return self._available

    def device_count(self) -> int:
        return len(self._devices)

    def get_device_name(self, index: int) -> str:
        self.name_calls.append(index)
        return self._devices[index][4]

    def synchronize(self, index: int) -> None:
        self.sync_calls.append(index)

    def memory_allocated(self, index: int) -> int:
        self.allocated_calls.append(index)
        return self._devices[index][0]

    def memory_reserved(self, index: int) -> int:
        self.reserved_calls.append(index)
        return self._devices[index][1]

    def mem_get_info(self, index: int) -> tuple[int, int]:
        self.mem_get_info_calls.append(index)
        return self._devices[index][2], self._devices[index][3]


class TestCollectDependencyVersions:
    def test_returns_pinned_runtime_and_kaggle_stack(self) -> None:
        deps = collect_dependency_versions()
        assert len(deps) == 8
        names = [name for name, _ in deps]
        assert "django" in names
        assert "djangorestframework" in names
        assert "pytest" in names
        assert "pytest_django" in names
        assert "torch" in names
        assert "transformers" in names
        assert "accelerate" in names
        assert "bitsandbytes" in names

    def test_drf_uses_rest_framework_import_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        imported: list[str] = []

        def fake_import(name: str):
            imported.append(name)
            return object()

        monkeypatch.setattr(mod.importlib, "import_module", fake_import)
        monkeypatch.setattr(mod.importlib.metadata, "version", lambda _name: "x")
        collect_dependency_versions()
        assert "rest_framework" in imported
        assert "djangorestframework" not in imported

    def test_local_machine_marks_torch_as_not_installed(self) -> None:
        deps = dict(collect_dependency_versions())
        try:
            import torch  # noqa: F401

            assert deps["torch"] != "NOT_INSTALLED"
        except ImportError:
            assert deps["torch"] == "NOT_INSTALLED"


class TestRenderPreflightTable:
    def test_contains_key_fields(self) -> None:
        result = KaggleSmokePreflightResult(
            passed=False,
            checks=("dependency_import_verification: PASS", "vram_headroom: FAIL"),
            rejection_reason="vram_headroom: FAIL (free=0.10 GiB < 2.0 GiB)",
            model_identity="qwen:qwen2.5-coder-7b-instruct:bnb-int8:cfg-abc123",
            requested_quantization_mode="bnb-int8",
            model_checkpoint_basename="qwen2.5-coder-7b-instruct",
            free_vram_after_probe_gib=0.1,
            probe_prompt_tokens=8,
            probe_completion_tokens=64,
            dependencies=(("torch", "2.4.0"),),
        )
        table = render_preflight_table(result)
        assert "KAGGLE SMOKE PREFLIGHT" in table
        assert "passed: False" in table
        assert "model_identity: qwen:qwen2.5-coder-7b-instruct:bnb-int8:cfg-abc123" in table
        assert "requested_quantization_mode: bnb-int8" in table
        assert "model_checkpoint_basename: qwen2.5-coder-7b-instruct" in table
        assert "vram_headroom: FAIL" in table
        assert "probe_tokens: 8+64" in table
        assert "dep torch: 2.4.0" in table

    def test_renders_every_gpu_snapshot_line(self) -> None:
        result = KaggleSmokePreflightResult(
            passed=True,
            gpu_count=2,
            gpu_name="Tesla T4",
            gpu_vram_by_device=(
                GpuVramSnapshot(0, "Tesla T4", 7.125, 7.25, 7.0, 14.56),
                GpuVramSnapshot(1, "Tesla T4", 6.875, 7.0, 0.125, 14.56),
            ),
        )
        table = render_preflight_table(result)
        assert "gpu_vram[0] Tesla T4 alloc=7.125 reserved=7.250 free=7.000 total=14.560 GiB" in table
        assert "gpu_vram[1] Tesla T4 alloc=6.875 reserved=7.000 free=0.125 total=14.560 GiB" in table


class TestRunKaggleSmokePreflight:
    def _patch(
        self,
        monkeypatch: pytest.MonkeyPatch,
        *,
        deps: tuple[tuple[str, str], ...] | None = None,
        probe_metrics: dict[str, object] | None = None,
        probe_exc: BaseException | None = None,
    ) -> None:
        monkeypatch.setattr(mod, "_python_runtime_status", lambda: ("3.12.13", True))
        if deps is not None:
            monkeypatch.setattr(mod, "collect_dependency_versions", lambda: deps)
        else:
            monkeypatch.setattr(
                mod,
                "collect_dependency_versions",
                lambda: (("django", "5.2.16"), ("djangorestframework", "3.17.1")),
            )

        staged = Path("fake-staged")
        monkeypatch.setattr(mod, "_stage_baseline_workspace", lambda data_dir, root: staged)
        monkeypatch.setattr(mod, "_run_in_workspace", lambda ws, *argv, timeout=180: (0, "", ""))

        # Patch _create_qwen_backend to return a dummy object (no real model load).
        monkeypatch.setattr(mod, "_create_qwen_backend", lambda model_path, quantization_mode: None)

        def _probe(model_path: str, quantization_mode: str, **_kw: object) -> dict[str, object]:
            if probe_exc is not None:
                raise probe_exc
            return probe_metrics or {
                "model_identity": "qwen:qwen2.5-coder-7b-instruct:bnb-int8:cfg-abc123",
                "requested_quantization_mode": quantization_mode,
                "model_checkpoint_basename": "qwen2.5-coder-7b-instruct",
                "checkpoint_quantization_method": "",
                "model_memory_footprint_bytes": 4000000000,
                "device_map_summary": "cuda:0",
                "requested_attn_implementation": "sdpa",
                "effective_attn_implementation": "sdpa",
                "sdpa_kernel_policy": "flash_or_efficient_no_math",
                "gpu_count": 1,
                "gpu_name": "T4",
                "gpu_vram_by_device": (GpuVramSnapshot(0, "T4", 12.5, 14.0, 2.5, 14.56),),
                "allocated_vram_gib": 12.5,
                "reserved_vram_gib": 14.0,
                "free_vram_after_probe_gib": 2.5,
                "probe_prompt_tokens": 8,
                "probe_completion_tokens": 64,
            }

        monkeypatch.setattr(mod, "_qwen_probe_metrics", _probe)

        # Patch long-context probe to succeed in unit tests (no real GPU/model).
        def _lc_probe(model_path: str, quantization_mode: str, **_kw: object) -> dict[str, object]:
            return {
                "passed": True,
                "prompt_tokens": 12000,
                "target_prompt_tokens": 12000,
                "completion_tokens": 64,
                "elapsed_seconds": 0.1,
                "cache_implementation": "offloaded",
                "requested_attn_implementation": "sdpa",
                "effective_attn_implementation": "sdpa",
                "sdpa_kernel_policy": "flash_or_efficient_no_math",
                "gpu_name": "T4",
                "gpu_count": True,
                "peak_allocated_gib": 12.5,
                "peak_reserved_gib": 14.0,
                "finish_reason": "eos",
            }
        monkeypatch.setattr(mod, "_run_long_context_probe", _lc_probe)

    def test_pass_when_all_checks_succeed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        self._patch(monkeypatch, deps=(("django", "5.2.16"),))
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
        )
        assert result.passed is True
        assert any(c.startswith("dependency_import_verification: PASS") for c in result.checks)
        assert any(c.startswith("manage_py_check: PASS") for c in result.checks)
        assert any(c.startswith("makemigrations_check: PASS") for c in result.checks)
        assert any(c.startswith("qwen_model_load[bnb-int8]: PASS") for c in result.checks)
        assert any(c.startswith("gpu_count_expected: PASS") for c in result.checks)
        assert any(c.startswith("checkpoint_not_prequantized: PASS") for c in result.checks)
        assert any(c.startswith("vram_headroom: PASS") for c in result.checks)
        assert result.model_identity == "qwen:qwen2.5-coder-7b-instruct:bnb-int8:cfg-abc123"
        assert result.requested_quantization_mode == "bnb-int8"

    @pytest.mark.parametrize(
        ("gpu_count", "expected_check"),
        [
            (1, "gpu_count_expected: PASS (1)"),
            (2, "gpu_count_expected: PASS (2)"),
            (0, "gpu_count_expected: FAIL (0; expected 1 or 2)"),
            (3, "gpu_count_expected: FAIL (3; expected 1 or 2)"),
        ],
    )
    def test_gpu_count_matrix(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        gpu_count: int,
        expected_check: str,
    ) -> None:
        self._patch(
            monkeypatch,
            deps=(("django", "5.2.16"),),
            probe_metrics={
                "model_identity": "qwen:qwen2.5-coder-7b-instruct:bnb-int8:cfg-abc123",
                "requested_quantization_mode": "bnb-int8",
                "model_checkpoint_basename": "qwen2.5-coder-7b-instruct",
                "checkpoint_quantization_method": "",
                "model_memory_footprint_bytes": 4000000000,
                "device_map_summary": "cuda:0",
                "requested_attn_implementation": "sdpa",
                "effective_attn_implementation": "sdpa",
                "sdpa_kernel_policy": "flash_or_efficient_no_math",
                "gpu_count": gpu_count,
                "gpu_name": "T4",
                "gpu_vram_by_device": tuple(
                    GpuVramSnapshot(index, "T4", 12.5, 14.0, 2.5, 14.56)
                    for index in range(gpu_count)
                ),
                "allocated_vram_gib": 12.5,
                "reserved_vram_gib": 14.0,
                "free_vram_after_probe_gib": 2.5,
                "probe_prompt_tokens": 8,
                "probe_completion_tokens": 64,
            },
        )
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
        )
        assert any(c == expected_check for c in result.checks)
        assert result.passed is (gpu_count in EXPECTED_VISIBLE_GPU_COUNTS)

    def test_two_visible_gpus_otherwise_valid_preflight_passes(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Regression proof: the real 2x Tesla T4 Kaggle environment must pass."""
        self._patch(
            monkeypatch,
            deps=(("django", "5.2.16"),),
            probe_metrics={
                "model_identity": "qwen:qwen2.5-coder-14b-instruct:bnb-nf4:cfg-def456",
                "requested_quantization_mode": "bnb-nf4",
                "model_checkpoint_basename": "qwen2.5-coder-14b-instruct",
                "checkpoint_quantization_method": "",
                "model_memory_footprint_bytes": 9000000000,
                "device_map_summary": "{'model.layers.0': 0, 'model.layers.10': 1}",
                "requested_attn_implementation": "sdpa",
                "effective_attn_implementation": "sdpa",
                "sdpa_kernel_policy": "flash_or_efficient_no_math",
                "gpu_count": 2,
                "gpu_name": "Tesla T4",
                "gpu_vram_by_device": (
                    GpuVramSnapshot(0, "Tesla T4", 13.0, 14.0, 3.0, 14.56),
                    GpuVramSnapshot(1, "Tesla T4", 13.0, 14.0, 3.0, 14.56),
                ),
                "allocated_vram_gib": 13.0,
                "reserved_vram_gib": 14.0,
                "free_vram_after_probe_gib": 3.0,
                "probe_prompt_tokens": 8,
                "probe_completion_tokens": 64,
            },
        )
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen14b",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
            quantization_mode="bnb-nf4",
        )
        assert result.passed is True
        assert any(c == "gpu_count_expected: PASS (2)" for c in result.checks)
        assert any(c.startswith("device_map_gpu_only: PASS") for c in result.checks)
        assert any(c.startswith("vram_headroom: PASS") for c in result.checks)

    def test_nf4_quantization_is_forwarded_to_probe_and_check_name(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        received: list[str] = []

        def probe(model_path: str, quantization_mode: str, **_kw: object) -> dict[str, object]:
            received.append(quantization_mode)
            return {
                "model_identity": "qwen:qwen2.5-coder-14b-instruct:bnb-nf4:cfg-def456",
                "requested_quantization_mode": quantization_mode,
                "model_checkpoint_basename": "qwen2.5-coder-14b-instruct",
                "checkpoint_quantization_method": "",
                "model_memory_footprint_bytes": 4000000000,
                "device_map_summary": "cuda:0",
                "gpu_count": 1,
                "gpu_name": "T4",
                "gpu_vram_by_device": (GpuVramSnapshot(0, "T4", 10.0, 11.0, 3.0, 14.56),),
                "allocated_vram_gib": 10.0,
                "reserved_vram_gib": 11.0,
                "free_vram_after_probe_gib": 3.0,
                "probe_prompt_tokens": 8,
                "probe_completion_tokens": 64,
            }

        self._patch(monkeypatch, deps=(("django", "5.2.16"),))
        monkeypatch.setattr(mod, "_qwen_probe_metrics", probe)
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen14b",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
            quantization_mode="bnb-nf4",
        )
        assert received == ["bnb-nf4"]
        assert any(c.startswith("qwen_model_load[bnb-nf4]: PASS") for c in result.checks)
        assert result.requested_quantization_mode == "bnb-nf4"
        assert result.model_checkpoint_basename == "qwen2.5-coder-14b-instruct"

    def test_fail_when_missing_dependency(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        probe_calls = 0

        def probe(_model_path: str, _quantization_mode: str, **_kw: object) -> dict[str, object]:
            nonlocal probe_calls
            probe_calls += 1
            return {}

        self._patch(monkeypatch, deps=(("torch", "NOT_INSTALLED"),))
        monkeypatch.setattr(mod, "_qwen_probe_metrics", probe)
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
        )
        assert result.passed is False
        assert any(c.startswith("dependency_import_verification: FAIL") for c in result.checks)
        assert "torch" in result.rejection_reason
        assert probe_calls == 0

    def test_unsupported_python_skips_expensive_model_probe(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch(monkeypatch, deps=(("django", "5.2.16"),))
        monkeypatch.setattr(mod, "_python_runtime_status", lambda: ("3.13.5", False))
        calls = 0

        def probe(_model_path: str, _quantization_mode: str, **_kw: object) -> dict[str, object]:
            nonlocal calls
            calls += 1
            return {}

        monkeypatch.setattr(mod, "_qwen_probe_metrics", probe)
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
        )
        assert result.passed is False
        assert calls == 0
        assert any(c.startswith("python_runtime: FAIL") for c in result.checks)

    def test_fail_when_pinned_dependency_version_drifts(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch(monkeypatch, deps=(("django", "5.2.15"),))
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
        )
        assert result.passed is False
        assert "expected 5.2.16" in result.rejection_reason

    def test_fail_when_transformers_version_drifts(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Qwen14B NF4 v4 closure: the exact transformers 4.57.6 is mandatory.

        The OOM audit reproduced transformers 5.0.0 materializing the 14B BF16
        weights on GPU before BNB-NF4 quantization; any version other than the
        pinned loader must fail the preflight before staging/model load.
        """
        self._patch(monkeypatch, deps=(("transformers", "5.0.0"),))
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen14b",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
            quantization_mode="bnb-nf4",
        )
        assert result.passed is False
        assert "transformers=5.0.0 (expected 4.57.6)" in result.rejection_reason
        assert any(
            c.startswith("qwen_model_load[bnb-nf4]: SKIP") for c in result.checks
        )

    def test_fail_when_transformers_not_installed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch(monkeypatch, deps=(("transformers", "NOT_INSTALLED"),))
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
        )
        assert result.passed is False
        assert "transformers=NOT_INSTALLED" in result.rejection_reason

    def test_baseline_failure_skips_expensive_model_probe(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch(monkeypatch, deps=(("django", "5.2.16"),))
        calls = 0

        def run_command(_ws: Path, *argv: str, timeout: int = 180):
            if argv[-1] == "check":
                return 1, "", "baseline broken"
            return 0, "", ""

        def probe(_model_path: str, _quantization_mode: str, **_kw: object) -> dict[str, object]:
            nonlocal calls
            calls += 1
            return {}

        monkeypatch.setattr(mod, "_run_in_workspace", run_command)
        monkeypatch.setattr(mod, "_qwen_probe_metrics", probe)
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
        )
        assert result.passed is False
        assert calls == 0
        assert any(c.startswith("qwen_model_load[bnb-int8]: SKIP") for c in result.checks)

    def test_fail_when_vram_headroom_below_threshold(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch(
            monkeypatch,
            deps=(("django", "5.2.16"),),
            probe_metrics={
                "model_identity": "qwen:qwen2.5-coder-7b-instruct:bnb-int8:cfg-abc123",
                "requested_quantization_mode": "bnb-int8",
                "model_checkpoint_basename": "qwen2.5-coder-7b-instruct",
                "checkpoint_quantization_method": "",
                "model_memory_footprint_bytes": 4000000000,
                "device_map_summary": "cuda:0",
                "gpu_count": 1,
                "gpu_name": "T4",
                "gpu_vram_by_device": (GpuVramSnapshot(0, "T4", 14.5, 15.5, 0.4, 14.56),),
                "allocated_vram_gib": 14.5,
                "reserved_vram_gib": 15.5,
                "free_vram_after_probe_gib": 0.4,
                "probe_prompt_tokens": 8,
                "probe_completion_tokens": 64,
            },
        )
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
        )
        assert result.passed is False
        assert any(c.startswith("vram_headroom: FAIL") for c in result.checks)
        assert f"{MIN_FREE_VRAM_GIB:.1f} GiB" in result.rejection_reason

    def test_fail_when_device_map_offloads_to_cpu(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch(
            monkeypatch,
            deps=(("django", "5.2.16"),),
            probe_metrics={
                "model_identity": "qwen:qwen2.5-coder-7b-instruct:bnb-int8:cfg-abc123",
                "requested_quantization_mode": "bnb-int8",
                "model_checkpoint_basename": "qwen2.5-coder-7b-instruct",
                "checkpoint_quantization_method": "",
                "model_memory_footprint_bytes": 4000000000,
                "device_map_summary": "{'model.layers.0': 0, 'lm_head': 'cpu'}",
                "gpu_count": 1,
                "gpu_name": "T4",
                "gpu_vram_by_device": (GpuVramSnapshot(0, "T4", 8.0, 8.5, 6.0, 14.56),),
                "allocated_vram_gib": 8.0,
                "reserved_vram_gib": 8.5,
                "free_vram_after_probe_gib": 6.0,
                "probe_prompt_tokens": 8,
                "probe_completion_tokens": 64,
            },
        )
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
        )
        assert result.passed is False
        assert any(c.startswith("device_map_gpu_only: FAIL") for c in result.checks)

    def test_fail_when_checkpoint_is_prequantized(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch(
            monkeypatch,
            deps=(("django", "5.2.16"),),
            probe_metrics={
                "model_identity": "qwen:qwen2.5-coder-14b-instruct-gptq-int4:bnb-nf4:cfg-def456",
                "requested_quantization_mode": "bnb-nf4",
                "model_checkpoint_basename": "qwen2.5-coder-14b-instruct-gptq-int4",
                "checkpoint_quantization_method": "gptq",
                "model_memory_footprint_bytes": 4000000000,
                "device_map_summary": "cuda:0",
                "gpu_count": 1,
                "gpu_name": "T4",
                "gpu_vram_by_device": (GpuVramSnapshot(0, "T4", 9.0, 10.0, 4.0, 14.56),),
                "allocated_vram_gib": 9.0,
                "reserved_vram_gib": 10.0,
                "free_vram_after_probe_gib": 4.0,
                "probe_prompt_tokens": 8,
                "probe_completion_tokens": 64,
            },
        )
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen14b_gptq",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
        )
        assert result.passed is False
        assert any(c.startswith("checkpoint_not_prequantized: FAIL") for c in result.checks)

    def test_fail_when_probe_raises(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        self._patch(
            monkeypatch,
            deps=(("django", "5.2.16"),),
            probe_exc=RuntimeError("simulated CUDA OOM"),
        )
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
        )
        assert result.passed is False
        assert any(c.startswith("qwen_model_load[bnb-int8]: FAIL") for c in result.checks)
        assert any(c.startswith("vram_headroom: FAIL") for c in result.checks)

    def test_static_model_metadata_preserved_when_probe_fails(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Model/GPU metadata stays truthful when the model load OOMs/fails.

        Qwen14B NF4 v4 closure: the OOM audit needed the real model identity and
        GPU state after from_pretrained died; the preflight must not zero them.
        """
        self._patch(
            monkeypatch,
            deps=(("django", "5.2.16"),),
            probe_exc=RuntimeError("simulated CUDA OOM"),
        )
        monkeypatch.setattr(
            mod,
            "_static_model_metadata",
            lambda model_path, quantization_mode: {
                "requested_quantization_mode": quantization_mode,
                "model_identity": "qwen:qwen2.5-coder-14b-instruct:bnb-nf4:cfg-def456",
                "model_checkpoint_basename": "qwen2.5-coder-14b-instruct",
                "checkpoint_quantization_method": "",
                "gpu_count": 2,
                "gpu_name": "Tesla T4",
                "gpu_vram_by_device": (
                    GpuVramSnapshot(0, "Tesla T4", 7.125, 7.25, 3.0, 14.56),
                    GpuVramSnapshot(1, "Tesla T4", 6.875, 7.0, 0.125, 14.56),
                ),
            },
        )
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen14b",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
            quantization_mode="bnb-nf4",
        )
        assert result.passed is False
        assert any(c.startswith("qwen_model_load[bnb-nf4]: FAIL") for c in result.checks)
        assert result.model_identity == "qwen:qwen2.5-coder-14b-instruct:bnb-nf4:cfg-def456"
        assert result.model_checkpoint_basename == "qwen2.5-coder-14b-instruct"
        assert result.requested_quantization_mode == "bnb-nf4"
        assert result.checkpoint_quantization_method == ""
        assert result.gpu_count == 2
        assert result.gpu_name == "Tesla T4"
        assert result.free_vram_after_probe_gib == 0.0
        assert [s.device_index for s in result.gpu_vram_by_device] == [0, 1]
        assert [s.free_gib for s in result.gpu_vram_by_device] == [3.0, 0.125]
        assert result.gpu_vram_by_device[0].gpu_name == "Tesla T4"
        assert result.gpu_vram_by_device[1].total_gib == 14.56

    def test_writes_v1_json_schema(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        self._patch(monkeypatch, deps=(("django", "5.2.16"),))
        out = tmp_path / "kaggle_smoke_preflight.v1.json"
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
            json_output_path=out,
        )
        assert out.is_file()
        payload = json.loads(out.read_text("utf-8"))
        assert payload["schema"] == "kaggle_smoke_preflight.v1"
        assert payload["passed"] == result.passed
        assert payload["model_identity"] == "qwen:qwen2.5-coder-7b-instruct:bnb-int8:cfg-abc123"
        assert payload["requested_quantization_mode"] == "bnb-int8"
        assert payload["model_checkpoint_basename"] == "qwen2.5-coder-7b-instruct"
        assert payload["gpu_vram_by_device"] == [
            {
                "device_index": 0,
                "gpu_name": "T4",
                "allocated_gib": 12.5,
                "reserved_gib": 14.0,
                "free_gib": 2.5,
                "total_gib": 14.56,
            }
        ]
        assert payload["free_vram_after_probe_gib"] == 2.5


class TestRepositoryPreflightEvidence:
    """REPO-PREFLIGHT-EVIDENCE: the repo-preflight gate is fail-closed."""

    def test_missing_evidence_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(RepositoryPreflightUnavailableError, match="missing"):
            load_repo_preflight_evidence(tmp_path / "repo_preflight.json")

    def test_unreadable_evidence_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "repo_preflight.json"
        path.write_text("{not json", encoding="utf-8")
        with pytest.raises(RepositoryPreflightUnavailableError, match="invalid json"):
            load_repo_preflight_evidence(path)

    def test_non_pass_overall_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "repo_preflight.json"
        path.write_text('{"overall": "FAIL"}', encoding="utf-8")
        with pytest.raises(RepositoryPreflightUnavailableError, match="overall != PASS"):
            load_repo_preflight_evidence(path)

    def test_pass_overall_returns_evidence(self, tmp_path: Path) -> None:
        path = tmp_path / "repo_preflight.json"
        path.write_text(
            '{"overall": "PASS", "repositories": {"todo": {"passed": true}}}',
            encoding="utf-8",
        )
        evidence = load_repo_preflight_evidence(path)
        assert evidence["overall"] == "PASS"
        assert evidence["repositories"]["todo"]["passed"] is True


class TestRepositoryPreflightGating:
    """REPO-PREFLIGHT-GATING: a failed repo preflight blocks the model probe."""

    def _patch(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> list[int]:
        monkeypatch.setattr(mod, "_python_runtime_status", lambda: ("3.12.13", True))
        monkeypatch.setattr(
            mod,
            "collect_dependency_versions",
            lambda: (("django", "5.2.16"), ("djangorestframework", "3.17.1")),
        )
        staged = Path("fake-staged")
        monkeypatch.setattr(mod, "_stage_baseline_workspace", lambda data_dir, root: staged)
        monkeypatch.setattr(mod, "_run_in_workspace", lambda ws, *argv, timeout=180: (0, "", ""))

        # Patch _create_qwen_backend to return a dummy object (no real model load).
        monkeypatch.setattr(mod, "_create_qwen_backend", lambda model_path, quantization_mode: None)

        probe_calls: list[int] = []

        def _probe(model_path: str, quantization_mode: str, **_kw: object) -> dict[str, object]:
            probe_calls.append(1)
            return {
                "model_identity": "qwen:qwen2.5-coder-7b-instruct:bnb-int8:cfg-abc123",
                "requested_quantization_mode": quantization_mode,
                "model_checkpoint_basename": "qwen2.5-coder-7b-instruct",
                "checkpoint_quantization_method": "",
                "model_memory_footprint_bytes": 4000000000,
                "device_map_summary": "cuda:0",
                "requested_attn_implementation": "sdpa",
                "effective_attn_implementation": "sdpa",
                "sdpa_kernel_policy": "flash_or_efficient_no_math",
                "gpu_count": 1,
                "gpu_name": "T4",
                "gpu_vram_by_device": (GpuVramSnapshot(0, "T4", 12.5, 14.0, 2.5, 14.56),),
                "allocated_vram_gib": 12.5,
                "reserved_vram_gib": 14.0,
                "free_vram_after_probe_gib": 2.5,
                "probe_prompt_tokens": 8,
                "probe_completion_tokens": 64,
            }

        monkeypatch.setattr(mod, "_qwen_probe_metrics", _probe)

        def _lc_probe(model_path: str, quantization_mode: str, **_kw: object) -> dict[str, object]:
            return {
                "passed": True,
                "prompt_tokens": 12000,
                "target_prompt_tokens": 12000,
                "completion_tokens": 64,
                "elapsed_seconds": 0.1,
                "cache_implementation": "offloaded",
                "requested_attn_implementation": "sdpa",
                "effective_attn_implementation": "sdpa",
                "sdpa_kernel_policy": "flash_or_efficient_no_math",
                "gpu_name": "T4",
                "gpu_count": True,
                "peak_allocated_gib": 12.5,
                "peak_reserved_gib": 14.0,
                "finish_reason": "eos",
            }
        monkeypatch.setattr(mod, "_run_long_context_probe", _lc_probe)

        return probe_calls

    def test_missing_repo_preflight_blocks_model_load(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        probe_calls = self._patch(monkeypatch)
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
            repo_preflight_json_path=tmp_path / "missing-repo-preflight.json",
        )
        assert result.passed is False
        assert probe_calls == [], (
            "the model probe must never run when the repo preflight failed"
        )
        assert any(
            c.startswith("repository_preflight_evidence: FAIL") for c in result.checks
        )
        assert any(
            c == "baseline_staging: SKIP (repository preflight failed)" for c in result.checks
        )
        assert any(
            c == "manage_py_check: SKIP (repository preflight failed)" for c in result.checks
        )
        assert any(
            c == "makemigrations_check: SKIP (repository preflight failed)" for c in result.checks
        )
        assert any(
            c == "qwen_model_load[bnb-int8]: SKIP (repository preflight failed)"
            for c in result.checks
        )
        assert any(
            c == "device_map_gpu_only: SKIP (repository preflight failed)" for c in result.checks
        )
        assert any(
            c == "vram_headroom: SKIP (repository preflight failed)" for c in result.checks
        )
        assert any(
            c == "gpu_count_expected: SKIP (repository preflight failed)" for c in result.checks
        )
        assert any(
            c == "checkpoint_not_prequantized: SKIP (repository preflight failed)"
            for c in result.checks
        )

    def test_failed_overall_in_evidence_blocks_model_load(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        probe_calls = self._patch(monkeypatch)
        path = tmp_path / "repo_preflight.json"
        path.write_text(
            '{"overall": "FAIL", "repositories": {"saleor": {"passed": false}}}',
            encoding="utf-8",
        )
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
            repo_preflight_json_path=path,
        )
        assert result.passed is False
        assert probe_calls == []
        assert any(
            c.startswith("repository_preflight_evidence: FAIL") for c in result.checks
        )
        assert "overall != PASS" in result.rejection_reason

    def test_pass_overall_in_evidence_allows_model_load(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        probe_calls = self._patch(monkeypatch)
        path = tmp_path / "repo_preflight.json"
        path.write_text(
            '{"overall": "PASS", "repositories": {"todo": {"passed": true}}}',
            encoding="utf-8",
        )
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
            repo_preflight_json_path=path,
        )
        assert result.passed is True
        assert probe_calls == [1]
        assert any(c == "repository_preflight_evidence: PASS" for c in result.checks)


class TestCollectGpuVramSnapshots:
    """Per-device VRAM snapshot collection across every visible GPU."""

    def test_returns_empty_when_cuda_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_fake_torch(monkeypatch, FakeCuda([], available=False))
        assert mod._collect_gpu_vram_snapshots() == ()

    def test_returns_empty_when_torch_not_importable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        real_import = __import__

        def fake_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "torch":
                raise ModuleNotFoundError("No module named 'torch'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", fake_import)
        assert mod._collect_gpu_vram_snapshots() == ()

    def test_synchronizes_and_reads_every_visible_gpu(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cuda = FakeCuda(
            [
                (7 * 1024**3, 8 * 1024**3, 7 * 1024**3, 16 * 1024**3, "Tesla T4"),
                (6 * 1024**3, 7 * 1024**3, 3 * 1024**3, 16 * 1024**3, "Tesla T4"),
            ]
        )
        _install_fake_torch(monkeypatch, cuda)
        snapshots = mod._collect_gpu_vram_snapshots()
        assert cuda.sync_calls == [0, 1]
        assert cuda.allocated_calls == [0, 1]
        assert cuda.reserved_calls == [0, 1]
        assert cuda.mem_get_info_calls == [0, 1]
        assert cuda.name_calls == [0, 1]
        assert [s.device_index for s in snapshots] == [0, 1]
        assert [s.gpu_name for s in snapshots] == ["Tesla T4", "Tesla T4"]

    def test_rounds_gib_values_to_three_decimals(self, monkeypatch: pytest.MonkeyPatch) -> None:
        allocated = int(7.1236 * 1024**3)
        free = int(0.12501 * 1024**3)
        cuda = FakeCuda([(allocated, int(8.0 * 1024**3), free, int(16.0 * 1024**3), "Tesla T4")])
        _install_fake_torch(monkeypatch, cuda)
        snapshots = mod._collect_gpu_vram_snapshots()
        assert snapshots[0].allocated_gib == 7.124
        assert snapshots[0].free_gib == 0.125
        assert snapshots[0].total_gib == 16.0

    def test_failure_on_one_gpu_is_not_swallowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class FailingCuda(FakeCuda):
            def mem_get_info(self, index: int) -> tuple[int, int]:
                if index == 1:
                    raise RuntimeError("device 1 not queryable")
                return super().mem_get_info(index)

        cuda = FailingCuda(
            [
                (7 * 1024**3, 8 * 1024**3, 7 * 1024**3, 16 * 1024**3, "Tesla T4"),
                (6 * 1024**3, 7 * 1024**3, 3 * 1024**3, 16 * 1024**3, "Tesla T4"),
            ]
        )
        _install_fake_torch(monkeypatch, cuda)
        with pytest.raises(RuntimeError, match="device 1 not queryable"):
            mod._collect_gpu_vram_snapshots()


class TestQwenProbeMetricsMultiGpu:
    """The real probe path with fake Torch/CUDA and a fake backend."""

    @staticmethod
    def _install_fake_backend(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
        module = types.ModuleType("benchmark.llm.kaggle_qwen_backend")

        class TokenUsage:
            prompt_tokens = 8
            completion_tokens = 64

        class FakeResponse:
            token_usage = TokenUsage()

        class FakeBackend:
            model_identity = "qwen:qwen2.5-coder-14b-instruct:bnb-nf4:cfg-def456"
            quantization_mode = "bnb-nf4"
            checkpoint_basename = "qwen2.5-coder-14b-instruct"
            checkpoint_quantization_method = ""
            model_memory_footprint_bytes = 9000000000
            device_map_summary = "{'model.layers.0': 0, 'model.layers.10': 1}"
            requested_attention_implementation = "sdpa"
            effective_attention_implementation = "sdpa"
            sdpa_kernel_policy = "flash_or_efficient_no_math"

            def __init__(self, model_name: str, model_path: str, quantization_mode: str) -> None:
                return None

            def load(self) -> None:
                return None

            def run_probe(self, max_tokens: int = 0, prompt: str = "") -> FakeResponse:
                return FakeResponse()

        module.KaggleQwenBackend = FakeBackend  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "benchmark.llm.kaggle_qwen_backend", module)
        return module

    @staticmethod
    def _two_t4_devices() -> FakeCuda:
        return FakeCuda(
            [
                (7 * 1024**3, 8 * 1024**3, 7 * 1024**3, 16 * 1024**3, "Tesla T4"),
                (6 * 1024**3, 7 * 1024**3, 3 * 1024**3, 16 * 1024**3, "Tesla T4"),
            ]
        )

    def test_synchronizes_and_reads_every_visible_gpu(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cuda = self._two_t4_devices()
        self._install_fake_backend(monkeypatch)
        _install_fake_torch(monkeypatch, cuda)
        metrics = mod._qwen_probe_metrics("/kaggle/input/qwen14b", "bnb-nf4")
        assert cuda.sync_calls == [0, 1]
        assert cuda.mem_get_info_calls == [0, 1]
        assert cuda.allocated_calls == [0, 1]
        assert cuda.reserved_calls == [0, 1]
        assert metrics["gpu_count"] == 2
        assert metrics["gpu_name"] == "Tesla T4"

    def test_free_scalar_equals_minimum_not_gpu0_not_sum(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._install_fake_backend(monkeypatch)
        _install_fake_torch(monkeypatch, self._two_t4_devices())
        metrics = mod._qwen_probe_metrics("/kaggle/input/qwen14b", "bnb-nf4")
        assert metrics["free_vram_after_probe_gib"] == 3.0
        assert metrics["free_vram_after_probe_gib"] != 7.0
        assert metrics["free_vram_after_probe_gib"] != 10.0

    def test_allocated_reserved_scalars_equal_sums(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._install_fake_backend(monkeypatch)
        _install_fake_torch(monkeypatch, self._two_t4_devices())
        metrics = mod._qwen_probe_metrics("/kaggle/input/qwen14b", "bnb-nf4")
        assert metrics["allocated_vram_gib"] == 13.0
        assert metrics["reserved_vram_gib"] == 15.0

    def test_raises_when_gpu_count_positive_but_no_snapshots(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._install_fake_backend(monkeypatch)
        cuda = FakeCuda(
            [(7 * 1024**3, 8 * 1024**3, 7 * 1024**3, 16 * 1024**3, "Tesla T4")]
        )
        _install_fake_torch(monkeypatch, cuda)
        monkeypatch.setattr(mod, "_collect_gpu_vram_snapshots", lambda: ())
        with pytest.raises(RuntimeError, match="no per-GPU VRAM snapshots"):
            mod._qwen_probe_metrics("/kaggle/input/qwen14b", "bnb-nf4")


class TestVramHeadroomMultiGpuGate:
    """Adversarial 1-GPU / 2-GPU headroom gate matrix over fake snapshots."""

    def _run(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        *,
        snapshots: tuple[GpuVramSnapshot, ...],
        gpu_count: int = 2,
        free_scalar: float | None = None,
        json_output_path: Path | None = None,
    ) -> KaggleSmokePreflightResult:
        if free_scalar is None:
            free_scalar = min(s.free_gib for s in snapshots) if snapshots else 0.0
        probe_metrics = {
            "model_identity": "qwen:qwen2.5-coder-14b-instruct:bnb-nf4:cfg-def456",
            "requested_quantization_mode": "bnb-nf4",
            "model_checkpoint_basename": "qwen2.5-coder-14b-instruct",
            "checkpoint_quantization_method": "",
            "model_memory_footprint_bytes": 9000000000,
            "device_map_summary": "{'model.layers.0': 0, 'model.layers.10': 1}",
            "requested_attn_implementation": "sdpa",
            "effective_attn_implementation": "sdpa",
            "sdpa_kernel_policy": "flash_or_efficient_no_math",
            "gpu_count": gpu_count,
            "gpu_name": "Tesla T4",
            "gpu_vram_by_device": snapshots,
            "allocated_vram_gib": round(sum(s.allocated_gib for s in snapshots), 3),
            "reserved_vram_gib": round(sum(s.reserved_gib for s in snapshots), 3),
            "free_vram_after_probe_gib": free_scalar,
            "probe_prompt_tokens": 8,
            "probe_completion_tokens": 64,
        }
        TestRunKaggleSmokePreflight()._patch(
            monkeypatch, deps=(("django", "5.2.16"),), probe_metrics=probe_metrics
        )
        return run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen14b",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
            quantization_mode="bnb-nf4",
            json_output_path=json_output_path,
        )

    def test_one_gpu_with_two_gib_free_passes(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        result = self._run(
            monkeypatch,
            tmp_path,
            snapshots=(GpuVramSnapshot(0, "Tesla T4", 7.0, 8.0, 3.0, 16.0),),
            gpu_count=1,
        )
        assert result.passed is True
        assert any(
            c == "vram_headroom: PASS (minimum free across 1 GPU(s)=3.00 GiB)"
            for c in result.checks
        )

    def test_two_gpus_both_healthy_pass(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        result = self._run(
            monkeypatch,
            tmp_path,
            snapshots=(
                GpuVramSnapshot(0, "Tesla T4", 7.0, 8.0, 3.0, 16.0),
                GpuVramSnapshot(1, "Tesla T4", 6.0, 7.0, 2.5, 16.0),
            ),
            gpu_count=2,
        )
        assert result.passed is True
        assert any(
            c == "vram_headroom: PASS (minimum free across 2 GPU(s)=2.50 GiB)"
            for c in result.checks
        )

    def test_asymmetric_gpu0_healthy_gpu1_low_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Mandatory audit reproduction: GPU0 free 3.0 GiB, GPU1 free 0.125 GiB -> FAIL."""
        result = self._run(
            monkeypatch,
            tmp_path,
            snapshots=(
                GpuVramSnapshot(0, "Tesla T4", 7.0, 8.0, 3.0, 16.0),
                GpuVramSnapshot(1, "Tesla T4", 6.875, 7.0, 0.125, 16.0),
            ),
            gpu_count=2,
            free_scalar=0.125,
        )
        assert result.passed is False
        assert any(
            c == "vram_headroom: FAIL (GPU 1 free=0.12 GiB < 2.0 GiB)"
            for c in result.checks
        )
        assert result.free_vram_after_probe_gib == 0.125

    def test_gpu0_low_gpu1_healthy_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        result = self._run(
            monkeypatch,
            tmp_path,
            snapshots=(
                GpuVramSnapshot(0, "Tesla T4", 7.0, 8.0, 1.5, 16.0),
                GpuVramSnapshot(1, "Tesla T4", 6.0, 7.0, 3.0, 16.0),
            ),
            gpu_count=2,
        )
        assert result.passed is False
        assert any(
            c == "vram_headroom: FAIL (GPU 0 free=1.50 GiB < 2.0 GiB)"
            for c in result.checks
        )

    def test_both_gpus_low_lists_devices_in_order(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        result = self._run(
            monkeypatch,
            tmp_path,
            snapshots=(
                GpuVramSnapshot(0, "Tesla T4", 7.0, 8.0, 0.4, 16.0),
                GpuVramSnapshot(1, "Tesla T4", 6.0, 7.0, 1.5, 16.0),
            ),
            gpu_count=2,
        )
        assert result.passed is False
        assert any(
            c == "vram_headroom: FAIL (GPU 0 free=0.40 GiB < 2.0 GiB; GPU 1 free=1.50 GiB < 2.0 GiB)"
            for c in result.checks
        )

    def test_fails_when_gpu_count_positive_but_no_snapshots(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        result = self._run(
            monkeypatch,
            tmp_path,
            snapshots=(),
            gpu_count=2,
            free_scalar=3.0,
        )
        assert result.passed is False
        assert any(
            c == "vram_headroom: FAIL (no per-GPU VRAM snapshots collected)"
            for c in result.checks
        )

    def test_json_persists_ordered_per_gpu_objects(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        out = tmp_path / "kaggle_smoke_preflight.v1.json"
        result = self._run(
            monkeypatch,
            tmp_path,
            snapshots=(
                GpuVramSnapshot(0, "Tesla T4", 7.125, 7.25, 7.0, 14.56),
                GpuVramSnapshot(1, "Tesla T4", 6.875, 7.0, 0.125, 14.56),
            ),
            gpu_count=2,
            free_scalar=0.125,
            json_output_path=out,
        )
        assert out.is_file()
        payload = json.loads(out.read_text("utf-8"))
        assert payload["gpu_vram_by_device"] == [
            {
                "device_index": 0,
                "gpu_name": "Tesla T4",
                "allocated_gib": 7.125,
                "reserved_gib": 7.25,
                "free_gib": 7.0,
                "total_gib": 14.56,
            },
            {
                "device_index": 1,
                "gpu_name": "Tesla T4",
                "allocated_gib": 6.875,
                "reserved_gib": 7.0,
                "free_gib": 0.125,
                "total_gib": 14.56,
            },
        ]
        assert result.free_vram_after_probe_gib == 0.125


class TestStaticModelMetadata:
    """Qwen14B NF4 v4 closure: static config.json + GPU metadata without loading."""

    def _write_qwen_config(self, checkpoint: Path) -> None:
        checkpoint.mkdir(parents=True, exist_ok=True)
        (checkpoint / "config.json").write_text(
            json.dumps(
                {
                    "model_type": "qwen2",
                    "hidden_size": 5120,
                    "num_hidden_layers": 40,
                    "num_attention_heads": 40,
                    "quantization_config": None,
                }
            ),
            encoding="utf-8",
        )

    def test_reads_static_metadata_without_loading_weights(self, tmp_path: Path) -> None:
        from benchmark.llm.kaggle_qwen_backend import compute_model_identity

        checkpoint = tmp_path / "qwen2.5-coder-14b-instruct"
        self._write_qwen_config(checkpoint)
        meta = mod._static_model_metadata(str(checkpoint), "bnb-nf4")
        assert meta["model_identity"] == compute_model_identity(str(checkpoint), "bnb-nf4")
        assert meta["requested_quantization_mode"] == "bnb-nf4"
        assert meta["model_checkpoint_basename"] == "qwen2.5-coder-14b-instruct"
        assert meta["checkpoint_quantization_method"] == ""
        assert isinstance(meta["gpu_count"], int)
        assert isinstance(meta["gpu_name"], str)
        assert isinstance(meta["gpu_vram_by_device"], tuple)

    def test_missing_checkpoint_preserves_mode_and_blank_identity(
        self, tmp_path: Path
    ) -> None:
        meta = mod._static_model_metadata(str(tmp_path / "missing"), "bnb-int8")
        assert meta["model_identity"] == ""
        assert meta["requested_quantization_mode"] == "bnb-int8"
        assert meta["gpu_count"] == 0
        assert meta["gpu_vram_by_device"] == ()


CANONICAL_ATTENTION_FIELDS: dict[str, str] = {
    "requested_attn_implementation": "sdpa",
    "effective_attn_implementation": "sdpa",
    "sdpa_kernel_policy": "flash_or_efficient_no_math",
}


class TestAttentionPolicyGate:
    """V0.9.22: the canonical attention evidence must gate the model preflight.

    v0.9.21 target evidence: the real 12,044-token probe attempted a
    21.62 GiB allocation == the full float32 40-head 12044x12044 attention
    score matrix, so the effective attention path had materialized the
    quadratic math fallback. The preflight must now fail closed unless the
    requested/effective attention implementation and the fused-kernel policy
    are all canonical.
    """

    def _base_probe_metrics(self) -> dict[str, object]:
        return {
            "model_identity": "qwen:qwen2.5-coder-14b-instruct:bnb-nf4:cfg-def456",
            "requested_quantization_mode": "bnb-nf4",
            "model_checkpoint_basename": "qwen2.5-coder-14b-instruct",
            "checkpoint_quantization_method": "",
            "model_memory_footprint_bytes": 9000000000,
            "device_map_summary": "{'model.layers.0': 0, 'model.layers.10': 1}",
            **CANONICAL_ATTENTION_FIELDS,
            "gpu_count": 2,
            "gpu_name": "Tesla T4",
            "gpu_vram_by_device": (
                GpuVramSnapshot(0, "Tesla T4", 7.0, 8.0, 3.0, 16.0),
                GpuVramSnapshot(1, "Tesla T4", 6.0, 7.0, 2.5, 16.0),
            ),
            "allocated_vram_gib": 13.0,
            "reserved_vram_gib": 15.0,
            "free_vram_after_probe_gib": 2.5,
            "probe_prompt_tokens": 8,
            "probe_completion_tokens": 64,
        }

    def _run(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        attention: dict[str, str] | None = None,
        *,
        omit_attention_fields: bool = False,
    ) -> KaggleSmokePreflightResult:
        metrics = self._base_probe_metrics()
        if omit_attention_fields:
            for key in CANONICAL_ATTENTION_FIELDS:
                metrics.pop(key, None)
        elif attention is not None:
            metrics.update(attention)
        out = tmp_path / "kaggle_smoke_preflight.v1.json"
        TestRunKaggleSmokePreflight()._patch(
            monkeypatch, deps=(("django", "5.2.16"),), probe_metrics=metrics
        )
        return run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen14b",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
            quantization_mode="bnb-nf4",
            json_output_path=out,
        )

    def test_canonical_attention_evidence_passes(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        result = self._run(monkeypatch, tmp_path)
        assert result.passed is True
        assert any(
            c.startswith(
                "attention_policy: PASS (requested=sdpa effective=sdpa "
                "kernel_policy=flash_or_efficient_no_math"
            )
            for c in result.checks
        )

    @pytest.mark.parametrize(
        ("attention"),
        [
            {"requested_attn_implementation": ""},
            {"requested_attn_implementation": "eager"},
            {"effective_attn_implementation": ""},
            {"effective_attn_implementation": "eager"},
            {"sdpa_kernel_policy": ""},
            {"sdpa_kernel_policy": "math_only"},
        ],
    )
    def test_non_canonical_attention_fails_closed(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        attention: dict[str, str],
    ) -> None:
        result = self._run(monkeypatch, tmp_path, attention)
        assert result.passed is False
        assert any(c.startswith("attention_policy: FAIL") for c in result.checks)

    def test_missing_attention_fields_fail_closed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        result = self._run(monkeypatch, tmp_path, omit_attention_fields=True)
        assert result.passed is False
        assert any(c.startswith("attention_policy: FAIL") for c in result.checks)

    def test_attention_failure_prevents_long_context_probe(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Fail-closed: never stress a non-canonical attention path at 12k."""
        result = self._run(
            monkeypatch, tmp_path, {"effective_attn_implementation": "eager"}
        )
        assert result.passed is False
        assert not any(c.startswith("long_context_probe: PASS") for c in result.checks)
        assert result.long_context_probe is None

    def test_json_payload_contains_attention_evidence(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        out = tmp_path / "kaggle_smoke_preflight.v1.json"
        self._run(monkeypatch, tmp_path)
        payload = json.loads(out.read_text("utf-8"))
        assert payload["requested_attn_implementation"] == "sdpa"
        assert payload["effective_attn_implementation"] == "sdpa"
        assert payload["sdpa_kernel_policy"] == "flash_or_efficient_no_math"

    def test_render_table_shows_attention_evidence(self) -> None:
        result = KaggleSmokePreflightResult(
            passed=True,
            requested_quantization_mode="bnb-nf4",
            device_map_summary="cuda:0",
            requested_attn_implementation="sdpa",
            effective_attn_implementation="sdpa",
            sdpa_kernel_policy="flash_or_efficient_no_math",
        )
        table = render_preflight_table(result)
        assert "requested_attn_implementation: sdpa" in table
        assert "effective_attn_implementation: sdpa" in table
        assert "sdpa_kernel_policy: flash_or_efficient_no_math" in table

    def test_gate_constants_unchanged(self) -> None:
        from benchmark.llm.kaggle_qwen_backend import (
            KAGGLE_ATTENTION_IMPLEMENTATION,
            KAGGLE_CACHE_IMPLEMENTATION,
            KAGGLE_SDPA_KERNEL_POLICY,
        )

        assert mod.LONG_CONTEXT_TARGET_PROMPT_TOKENS == 12000
        assert mod.LONG_CONTEXT_MAX_TOKENS == 64
        assert mod.PROBE_MAX_TOKENS == 64
        assert KAGGLE_ATTENTION_IMPLEMENTATION == "sdpa"
        assert KAGGLE_SDPA_KERNEL_POLICY == "flash_or_efficient_no_math"
        assert KAGGLE_CACHE_IMPLEMENTATION == "offloaded"


def _real_dryrun_record(
    index: int,
    *,
    source_commit: str = "abc123",
    source_tag: str = "v0.9.18-pilot-exec-ready",
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one ``RunRecordData`` serialization EXACTLY as the real CLI dry-run
    writes it.

    The real serializer stores token accounting under the nested ``token_usage``
    mapping plus the ``total_workflow_*`` and phase ``*_model_calls`` /
    ``*_total_tokens`` fields. There is NO top-level ``total_tokens`` key. Tests
    must exercise this real shape so a fabricated legacy record can never satisfy
    the canonical dry-run evidence validator.
    """
    repos = ["todo"] * 16 + ["djangocms"] * 16 + ["saleor"] * 16
    strats = ["iterative_repository_agent"] * 24 + ["selective"] * 24
    record: dict[str, Any] = {
        "run_id": f"run-{index:03d}",
        "status": "succeeded",
        "repository_id": repos[index],
        "strategy_id": strats[index],
        "repetition": 1 if index < 24 else 2,
        "source_commit": source_commit,
        "source_tag": source_tag,
        "model_calls": 0,
        "token_usage": {"prompt": 0, "completion": 0, "total": 0},
        "total_workflow_model_calls": 0,
        "total_workflow_tokens": 0,
        "selection_model_calls": 0,
        "regeneration_model_calls": 0,
        "repair_model_calls": 0,
        "selection_total_tokens": 0,
        "regeneration_total_tokens": 0,
        "repair_total_tokens": 0,
        "protocol_version": "1.0",
        "profile": "pilot",
    }
    if overrides:
        record.update(overrides)
    return record


def _write_real_dryrun(
    dryrun_dir: Path,
    *,
    source_commit: str = "abc123",
    source_tag: str = "v0.9.18-pilot-exec-ready",
    deployed_build_id: str = "build-001",
    record_overrides: dict[str, Any] | None = None,
    record_indices: set[int] | None = None,
) -> Path:
    dryrun_dir.mkdir(parents=True, exist_ok=True)
    records = [
        _real_dryrun_record(
            i,
            source_commit=source_commit,
            source_tag=source_tag,
            overrides=(
                record_overrides
                if record_indices is None or i in record_indices
                else None
            ),
        )
        for i in range(48)
    ]
    (dryrun_dir / "run_records.jsonl").write_text(
        "\n".join(json.dumps(record) for record in records),
        encoding="utf-8",
    )
    (dryrun_dir / "source_identity.json").write_text(
        json.dumps({
            "dry_run": True,
            "profile": "pilot",
            "protocol_version": "1.0",
            "source_commit": source_commit,
            "source_tag": source_tag,
            "deployed_build_id": deployed_build_id,
            "model_identity": "dry-run:mock",
        }),
        encoding="utf-8",
    )
    return dryrun_dir


def _drop_record_fields(
    dryrun_dir: Path,
    fields: list[str],
    indices: set[int] | None = None,
) -> None:
    path = dryrun_dir / "run_records.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    output = []
    for index, line in enumerate(lines):
        record = json.loads(line)
        if indices is None or index in indices:
            for field in fields:
                record.pop(field, None)
        output.append(json.dumps(record))
    path.write_text("\n".join(output), encoding="utf-8")


def _set_record_field(dryrun_dir: Path, field: str, value: Any) -> None:
    path = dryrun_dir / "run_records.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    output = []
    for line in lines:
        record = json.loads(line)
        record[field] = value
        output.append(json.dumps(record))
    path.write_text("\n".join(output), encoding="utf-8")


def _set_token_usage_value(dryrun_dir: Path, key: str, value: Any) -> None:
    path = dryrun_dir / "run_records.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    output = []
    for line in lines:
        record = json.loads(line)
        token_usage = record.get("token_usage")
        if isinstance(token_usage, dict):
            token_usage[key] = value
        output.append(json.dumps(record))
    path.write_text("\n".join(output), encoding="utf-8")


class TestValidatePilotLaunchAuthorization:
    """C1-C5 + D: strict launch authorization with required long-context evidence."""

    def _write_valid_repo_preflight(self, path: Path) -> None:
        path.write_text(
            json.dumps({
                "overall": "PASS",
                "repositories": {
                    "todo": {"passed": True},
                    "djangocms": {"passed": True},
                    "saleor": {"passed": True},
                },
            }),
            encoding="utf-8",
        )

    def _write_valid_model_preflight(self, path: Path, *, lc_passed: bool = True) -> None:
        path.write_text(
            json.dumps({
                "passed": True,
                "model_identity": "Qwen2.5-Coder-14B-Instruct-bnb-nf4",
                "requested_quantization_mode": "bnb-nf4",
                "requested_attn_implementation": "sdpa",
                "effective_attn_implementation": "sdpa",
                "sdpa_kernel_policy": "flash_or_efficient_no_math",
                "checks": ["repository_preflight_evidence: PASS"],
                "long_context_probe": {
                    "passed": lc_passed,
                    "target_prompt_tokens": 16000,
                    "prompt_tokens": 16384,
                    "completion_tokens": 512,
                    "cache_implementation": "offloaded",
                },
                "generation_deadline_probe": {
                    "passed": True,
                    "deadline_fired": True,
                    "finish_reason": "timeout",
                    "completion_tokens": 1,
                },
            }),
            encoding="utf-8",
        )

    def _write_valid_dryrun(self, dryrun_dir: Path, *, source_commit: str = "abc123") -> None:
        _write_real_dryrun(
            dryrun_dir,
            source_commit=source_commit,
            source_tag="v0.9.18-pilot-exec-ready",
            deployed_build_id="build-001",
        )

    def test_passes_with_valid_evidence(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_valid_model_preflight(tmp_path / "model.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        from benchmark.execution.preflight import validate_pilot_launch_authorization
        validate_pilot_launch_authorization(
            repo_preflight_json=tmp_path / "repo.json",
            model_preflight_json=tmp_path / "model.json",
            dryrun_dir=tmp_path / "dryrun",
            expected_source_commit="abc123",
            expected_source_tag="v0.9.18-pilot-exec-ready",
            expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            expected_deployed_build_id="build-001",
        )

    def test_fails_on_missing_repo_preflight(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_model_preflight(tmp_path / "model.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        from benchmark.execution.preflight import LaunchAuthorizationError, validate_pilot_launch_authorization
        with pytest.raises(LaunchAuthorizationError, match="repo_preflight.json missing"):
            validate_pilot_launch_authorization(
                repo_preflight_json=tmp_path / "missing.json",
                model_preflight_json=tmp_path / "model.json",
                dryrun_dir=tmp_path / "dryrun",
                expected_source_commit="abc123",
                expected_source_tag="v0.9.18-pilot-exec-ready",
                expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            )

    def test_fails_on_missing_long_context_probe(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        (tmp_path / "model.json").write_text(json.dumps({
            "passed": True,
            "model_identity": "Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            "requested_quantization_mode": "bnb-nf4",
            "checks": [],
        }), encoding="utf-8")
        from benchmark.execution.preflight import LaunchAuthorizationError, validate_pilot_launch_authorization
        with pytest.raises(LaunchAuthorizationError, match="long_context_probe missing"):
            validate_pilot_launch_authorization(
                repo_preflight_json=tmp_path / "repo.json",
                model_preflight_json=tmp_path / "model.json",
                dryrun_dir=tmp_path / "dryrun",
                expected_source_commit="abc123",
                expected_source_tag="v0.9.18-pilot-exec-ready",
                expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            )

    def test_fails_on_long_context_probe_not_passed(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        self._write_valid_model_preflight(tmp_path / "model.json", lc_passed=False)
        from benchmark.execution.preflight import LaunchAuthorizationError, validate_pilot_launch_authorization
        with pytest.raises(LaunchAuthorizationError, match="long_context_probe passed != true"):
            validate_pilot_launch_authorization(
                repo_preflight_json=tmp_path / "repo.json",
                model_preflight_json=tmp_path / "model.json",
                dryrun_dir=tmp_path / "dryrun",
                expected_source_commit="abc123",
                expected_source_tag="v0.9.18-pilot-exec-ready",
                expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            )

    @pytest.mark.parametrize(
        "attention_override",
        [
            {"requested_attn_implementation": "eager"},
            {"requested_attn_implementation": ""},
            {"effective_attn_implementation": "eager"},
            {"effective_attn_implementation": ""},
            {"sdpa_kernel_policy": "math_only"},
            {"sdpa_kernel_policy": ""},
        ],
    )
    def test_fails_on_non_canonical_attention_evidence(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        attention_override: dict[str, str],
    ) -> None:
        """V0.9.22: launch authorization fails closed without canonical attention."""
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        self._write_valid_model_preflight(tmp_path / "model.json")
        evidence = json.loads((tmp_path / "model.json").read_text(encoding="utf-8"))
        evidence.update(attention_override)
        (tmp_path / "model.json").write_text(json.dumps(evidence), encoding="utf-8")
        from benchmark.execution.preflight import LaunchAuthorizationError, validate_pilot_launch_authorization
        with pytest.raises(
            LaunchAuthorizationError, match="attn_implementation|sdpa_kernel_policy"
        ):
            validate_pilot_launch_authorization(
                repo_preflight_json=tmp_path / "repo.json",
                model_preflight_json=tmp_path / "model.json",
                dryrun_dir=tmp_path / "dryrun",
                expected_source_commit="abc123",
                expected_source_tag="v0.9.18-pilot-exec-ready",
                expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            )

    def test_fails_on_missing_attention_fields(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        self._write_valid_model_preflight(tmp_path / "model.json")
        evidence = json.loads((tmp_path / "model.json").read_text(encoding="utf-8"))
        for key in CANONICAL_ATTENTION_FIELDS:
            evidence.pop(key, None)
        (tmp_path / "model.json").write_text(json.dumps(evidence), encoding="utf-8")
        from benchmark.execution.preflight import LaunchAuthorizationError, validate_pilot_launch_authorization
        with pytest.raises(LaunchAuthorizationError, match="attn_implementation|sdpa_kernel_policy"):
            validate_pilot_launch_authorization(
                repo_preflight_json=tmp_path / "repo.json",
                model_preflight_json=tmp_path / "model.json",
                dryrun_dir=tmp_path / "dryrun",
                expected_source_commit="abc123",
                expected_source_tag="v0.9.18-pilot-exec-ready",
                expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            )

    def test_fails_on_wrong_source_commit(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_valid_model_preflight(tmp_path / "model.json")
        self._write_valid_dryrun(tmp_path / "dryrun", source_commit="wrong-commit")
        from benchmark.execution.preflight import LaunchAuthorizationError, validate_pilot_launch_authorization
        with pytest.raises(LaunchAuthorizationError, match="source_commit"):
            validate_pilot_launch_authorization(
                repo_preflight_json=tmp_path / "repo.json",
                model_preflight_json=tmp_path / "model.json",
                dryrun_dir=tmp_path / "dryrun",
                expected_source_commit="abc123",
                expected_source_tag="v0.9.18-pilot-exec-ready",
                expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            )

    def test_fails_on_wrong_source_tag(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_valid_model_preflight(tmp_path / "model.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        (tmp_path / "dryrun" / "source_identity.json").write_text(json.dumps({
            "dry_run": True,
            "profile": "pilot",
            "protocol_version": "1.0",
            "source_commit": "abc123",
            "source_tag": "v0.9.14-pilot-exec-ready",
            "deployed_build_id": "build-001",
            "model_identity": "dry-run:mock",
        }), encoding="utf-8")
        from benchmark.execution.preflight import LaunchAuthorizationError, validate_pilot_launch_authorization
        with pytest.raises(LaunchAuthorizationError, match="source_tag"):
            validate_pilot_launch_authorization(
                repo_preflight_json=tmp_path / "repo.json",
                model_preflight_json=tmp_path / "model.json",
                dryrun_dir=tmp_path / "dryrun",
                expected_source_commit="abc123",
                expected_source_tag="v0.9.18-pilot-exec-ready",
                expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            )

    def test_fails_on_nonzero_model_calls(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_valid_model_preflight(tmp_path / "model.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        # Overwrite one record with model_calls != 0
        lines = (tmp_path / "dryrun" / "run_records.jsonl").read_text(encoding="utf-8").splitlines()
        bad = json.loads(lines[0])
        bad["model_calls"] = 1
        lines[0] = json.dumps(bad)
        (tmp_path / "dryrun" / "run_records.jsonl").write_text("\n".join(lines), encoding="utf-8")
        from benchmark.execution.preflight import LaunchAuthorizationError, validate_pilot_launch_authorization
        with pytest.raises(LaunchAuthorizationError, match="model_calls != 0"):
            validate_pilot_launch_authorization(
                repo_preflight_json=tmp_path / "repo.json",
                model_preflight_json=tmp_path / "model.json",
                dryrun_dir=tmp_path / "dryrun",
                expected_source_commit="abc123",
                expected_source_tag="v0.9.18-pilot-exec-ready",
                expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            )

    def test_fails_on_missing_hf_token(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HF_TOKEN", raising=False)
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_valid_model_preflight(tmp_path / "model.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        from benchmark.execution.preflight import LaunchAuthorizationError, validate_pilot_launch_authorization
        with pytest.raises(LaunchAuthorizationError, match="HF_TOKEN"):
            validate_pilot_launch_authorization(
                repo_preflight_json=tmp_path / "repo.json",
                model_preflight_json=tmp_path / "model.json",
                dryrun_dir=tmp_path / "dryrun",
                expected_source_commit="abc123",
                expected_source_tag="v0.9.18-pilot-exec-ready",
                expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            )

    def test_fails_when_repository_preflight_evidence_missing_from_checks(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        # Model preflight with NO repository_preflight_evidence in checks
        (tmp_path / "model.json").write_text(json.dumps({
            "passed": True,
            "model_identity": "Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            "requested_quantization_mode": "bnb-nf4",
            "checks": ["qwen_model_load: PASS"],
            "long_context_probe": {
                "passed": True,
                "target_prompt_tokens": 16000,
                "prompt_tokens": 16384,
                "completion_tokens": 512,
                "cache_implementation": "offloaded",
            },
        }), encoding="utf-8")
        from benchmark.execution.preflight import LaunchAuthorizationError, validate_pilot_launch_authorization
        with pytest.raises(LaunchAuthorizationError, match="missing repository_preflight_evidence"):
            validate_pilot_launch_authorization(
                repo_preflight_json=tmp_path / "repo.json",
                model_preflight_json=tmp_path / "model.json",
                dryrun_dir=tmp_path / "dryrun",
                expected_source_commit="abc123",
                expected_source_tag="v0.9.18-pilot-exec-ready",
                expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            )

    def test_fails_when_repository_preflight_evidence_exists_but_no_pass(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        # Check exists but has neither PASS nor FAIL
        (tmp_path / "model.json").write_text(json.dumps({
            "passed": True,
            "model_identity": "Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            "requested_quantization_mode": "bnb-nf4",
            "checks": ["repository_preflight_evidence: SKIP (not run)"],
            "long_context_probe": {
                "passed": True,
                "target_prompt_tokens": 16000,
                "prompt_tokens": 16384,
                "completion_tokens": 512,
                "cache_implementation": "offloaded",
            },
        }), encoding="utf-8")
        from benchmark.execution.preflight import LaunchAuthorizationError, validate_pilot_launch_authorization
        with pytest.raises(LaunchAuthorizationError, match="contains no PASS signal"):
            validate_pilot_launch_authorization(
                repo_preflight_json=tmp_path / "repo.json",
                model_preflight_json=tmp_path / "model.json",
                dryrun_dir=tmp_path / "dryrun",
                expected_source_commit="abc123",
                expected_source_tag="v0.9.18-pilot-exec-ready",
                expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            )

    def test_fails_on_wrong_repo_preflight_overall(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        (tmp_path / "repo.json").write_text(json.dumps({"overall": "FAIL", "repositories": {}}), encoding="utf-8")
        self._write_valid_model_preflight(tmp_path / "model.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        from benchmark.execution.preflight import LaunchAuthorizationError, validate_pilot_launch_authorization
        with pytest.raises(LaunchAuthorizationError, match="repo_preflight.json overall=.FAIL"):
            validate_pilot_launch_authorization(
                repo_preflight_json=tmp_path / "repo.json",
                model_preflight_json=tmp_path / "model.json",
                dryrun_dir=tmp_path / "dryrun",
                expected_source_commit="abc123",
                expected_source_tag="v0.9.18-pilot-exec-ready",
                expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            )


class TestCLIAuthorizationPath:
    """G: CLI real-path authorization integration with seven_arm_benchmark.main."""

    def test_invalid_evidence_blocks_launch_and_returns_nonzero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        dryrun_dir = tmp_path / "dryrun"
        dryrun_dir.mkdir()
        (dryrun_dir / "source_identity.json").write_text(json.dumps({
            "dry_run": True, "profile": "pilot", "protocol_version": "1.0",
            "source_commit": "abc", "source_tag": "v0.9.18-pilot-exec-ready",
            "deployed_build_id": "b1", "model_identity": "dry-run:mock",
        }), encoding="utf-8")
        records = [
            json.dumps(_real_dryrun_record(
                i, source_commit="abc", source_tag="v0.9.18-pilot-exec-ready",
            ))
            for i in range(48)
        ]
        (dryrun_dir / "run_records.jsonl").write_text("\n".join(records), encoding="utf-8")

        import seven_arm_benchmark as saber
        monkeypatch.setattr(saber, "_get_model_identity", lambda **kw: "qwen:test:nf4")
        monkeypatch.setattr(saber, "parse_args", lambda: argparse.Namespace(
            dry_run=False, profile="pilot", strategy=None,
            output_dir=str(output_dir), data_dir=str(tmp_path / "data"),
            max_attempts=3, timeout=0, max_tokens=0,
            max_completion_tokens_per_call=4096,
            max_total_workflow_tokens=0, validation_command=None,
            validation_python=[], validation_timeout=None,
            protocol_version="1.0", model_path=None,
            qwen_quantization="bnb-nf4", resume=False,
            resume_from=None, max_runs=0, hf_sync=False,
            hf_repo_id=None, resume_from_hf=False,
            auto_resume_hf=False, new_experiment=False,
            experiment_id=None, source_commit="abc",
            source_tag="v0.9.18-pilot-exec-ready",
            deployed_build_id="b1", kaggle_preflight_only=False,
            require_launch_authorization=True,
            repo_preflight_json=None, model_preflight_json=None,
            expected_model_identity=None, launch_auth_dryrun_dir=None,
            backend=None, openrouter_model="", openrouter_timeout=120.0,
        ))
        rc = saber.main()
        assert rc != 0

    def test_valid_evidence_passes_authorization_gate(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        dryrun_dir = tmp_path / "dryrun"
        dryrun_dir.mkdir()
        (dryrun_dir / "source_identity.json").write_text(json.dumps({
            "dry_run": True, "profile": "pilot", "protocol_version": "1.0",
            "source_commit": "abc", "source_tag": "v0.9.18-pilot-exec-ready",
            "deployed_build_id": "b1", "model_identity": "dry-run:mock",
        }), encoding="utf-8")
        records = [
            json.dumps(_real_dryrun_record(
                i, source_commit="abc", source_tag="v0.9.18-pilot-exec-ready",
            ))
            for i in range(48)
        ]
        (dryrun_dir / "run_records.jsonl").write_text("\n".join(records), encoding="utf-8")

        repo_json = tmp_path / "repo.json"
        repo_json.write_text(json.dumps({
            "overall": "PASS",
            "repositories": {"todo": {"passed": True}, "djangocms": {"passed": True}, "saleor": {"passed": True}},
        }), encoding="utf-8")

        model_json = tmp_path / "model.json"
        model_json.write_text(json.dumps({
            "passed": True,
            "model_identity": "qwen:test:nf4",
            "requested_quantization_mode": "bnb-nf4",
            "requested_attn_implementation": "sdpa",
            "effective_attn_implementation": "sdpa",
            "sdpa_kernel_policy": "flash_or_efficient_no_math",
            "checks": ["repository_preflight_evidence: PASS"],
            "long_context_probe": {
                "passed": True,
                "target_prompt_tokens": 16000,
                "prompt_tokens": 16384,
                "completion_tokens": 512,
                "cache_implementation": "offloaded",
            },
            "generation_deadline_probe": {
                "passed": True,
                "deadline_fired": True,
                "finish_reason": "timeout",
                "completion_tokens": 1,
            },
        }), encoding="utf-8")

        import seven_arm_benchmark as saber
        from benchmark.execution import preflight as pf_mod

        monkeypatch.setattr(saber, "_get_model_identity", lambda **kw: "qwen:test:nf4")
        monkeypatch.setattr(saber, "parse_args", lambda: argparse.Namespace(
            dry_run=False, profile="pilot", strategy=None,
            output_dir=str(output_dir), data_dir=str(tmp_path / "data"),
            max_attempts=3, timeout=0, max_tokens=0,
            max_completion_tokens_per_call=4096,
            max_total_workflow_tokens=0, validation_command=None,
            validation_python=[], validation_timeout=None,
            protocol_version="1.0", model_path=None,
            qwen_quantization="bnb-nf4", resume=False,
            resume_from=None, max_runs=0, hf_sync=False,
            hf_repo_id=None, resume_from_hf=False,
            auto_resume_hf=False, new_experiment=False,
            experiment_id=None, source_commit="abc",
            source_tag="v0.9.18-pilot-exec-ready",
            deployed_build_id="b1", kaggle_preflight_only=False,
            require_launch_authorization=True,
            repo_preflight_json=str(repo_json),
            model_preflight_json=str(model_json),
            expected_model_identity="qwen:test:nf4",
            launch_auth_dryrun_dir=str(dryrun_dir),
            backend=None, openrouter_model="", openrouter_timeout=120.0,
        ))
        auth_passed: list[bool] = []
        real_validate = pf_mod.validate_pilot_launch_authorization

        def counting_validate(**kwargs: object) -> None:
            real_validate(**kwargs)  # type: ignore[arg-type]
            auth_passed.append(True)

        monkeypatch.setattr(pf_mod, "validate_pilot_launch_authorization", counting_validate)
        # main() proceeds past auth but may fail later on missing data/scenarios.
        # That's fine — we only need to verify authorization was invoked and passed.
        with pytest.raises((SystemExit, Exception)):
            saber.main()
        assert auth_passed, "authorization must have been invoked and passed"


class TestShortGenerationProbeTruthfulReporting:
    """V0.9.22 T4 GQA: model-load evidence is reported independently of the
    short-generation probe, and a broken generation path fails closed (SKIP 12k)
    without rewriting the load verdict.
    """

    def _patch_probe(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        metrics: dict[str, object],
        *,
        backend: object | None = None,
    ) -> Path:
        monkeypatch.setattr(mod, "_python_runtime_status", lambda: ("3.12.13", True))
        monkeypatch.setattr(
            mod, "collect_dependency_versions", lambda: (("django", "5.2.16"),)
        )
        monkeypatch.setattr(mod, "_stage_baseline_workspace", lambda data_dir, root: Path("fake-staged"))
        monkeypatch.setattr(mod, "_run_in_workspace", lambda ws, *a, timeout=180: (0, "", ""))
        monkeypatch.setattr(mod, "_create_qwen_backend", lambda mp, qm: backend)
        monkeypatch.setattr(mod, "_qwen_probe_metrics", lambda mp, qm, **_k: metrics)
        return tmp_path / "kaggle_smoke_preflight.v1.json"

    def _ok_metrics(self) -> dict[str, object]:
        return {
            "model_identity": "qwen:qwen2.5-coder-14b-instruct:bnb-nf4:cfg-x",
            "requested_quantization_mode": "bnb-nf4",
            "model_checkpoint_basename": "qwen2.5-coder-14b-instruct",
            "checkpoint_quantization_method": "",
            "model_memory_footprint_bytes": 9000000000,
            "device_map_summary": "GPU",
            "gpu_count": 2,
            "gpu_name": "Tesla T4",
            "gpu_vram_by_device": (),
            "free_vram_after_probe_gib": 7.0,
            "allocated_vram_gib": 1.0,
            "reserved_vram_gib": 1.0,
            "probe_prompt_tokens": 40,
            "probe_completion_tokens": 64,
            "requested_attn_implementation": "sdpa",
            "effective_attn_implementation": "sdpa",
            "sdpa_kernel_policy": "flash_or_efficient_no_math",
            "gqa_compatibility_mode": "",
            "short_generation_probe_error": "",
        }

    def test_load_pass_short_probe_fail_reports_separately_and_skips_12k(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        metrics = self._ok_metrics()
        metrics["short_generation_probe_error"] = "RuntimeError: No available kernel"
        out = self._patch_probe(monkeypatch, tmp_path, metrics, backend=object())
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen14b",
            data_dir=tmp_path,
            preflight_root=tmp_path / "r",
            quantization_mode="bnb-nf4",
            json_output_path=out,
        )
        assert any(c.startswith("qwen_model_load[bnb-nf4]: PASS") for c in result.checks)
        assert any(c.startswith("short_generation_probe: FAIL") for c in result.checks)
        assert any(c.startswith("long_context_probe: SKIP") for c in result.checks)
        assert result.passed is False

    def test_short_probe_pass_emits_pass(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        out = self._patch_probe(monkeypatch, tmp_path, self._ok_metrics())
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen14b",
            data_dir=tmp_path,
            preflight_root=tmp_path / "r",
            quantization_mode="bnb-nf4",
            json_output_path=out,
        )
        assert any(c.startswith("short_generation_probe: PASS") for c in result.checks)

    def test_gqa_compatibility_mode_persisted_to_json(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        metrics = self._ok_metrics()
        metrics["gqa_compatibility_mode"] = "repeat_kv_sm75"
        out = self._patch_probe(monkeypatch, tmp_path, metrics)
        run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen14b",
            data_dir=tmp_path,
            preflight_root=tmp_path / "r",
            quantization_mode="bnb-nf4",
            json_output_path=out,
        )
        payload = json.loads(out.read_text("utf-8"))
        assert payload["gqa_compatibility_mode"] == "repeat_kv_sm75"


class TestValidatePilotLaunchAuthorizationGqa:
    """V0.9.22 T4 GQA: launch authorization enforces the GQA compat mode."""

    def _write_valid_repo_preflight(self, path: Path) -> None:
        path.write_text(
            json.dumps({
                "overall": "PASS",
                "repositories": {
                    "todo": {"passed": True},
                    "djangocms": {"passed": True},
                    "saleor": {"passed": True},
                },
            }),
            encoding="utf-8",
        )

    def _write_valid_dryrun(self, dryrun_dir: Path) -> None:
        _write_real_dryrun(dryrun_dir, source_commit="abc123")

    def _model_json(self, path: Path, *, gqa_mode: str | None = None) -> None:
        payload = {
            "passed": True,
            "model_identity": "Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            "requested_quantization_mode": "bnb-nf4",
            "requested_attn_implementation": "sdpa",
            "effective_attn_implementation": "sdpa",
            "sdpa_kernel_policy": "flash_or_efficient_no_math",
            "checks": ["repository_preflight_evidence: PASS"],
            "long_context_probe": {
                "passed": True,
                "target_prompt_tokens": 16000,
                "prompt_tokens": 16384,
                "completion_tokens": 512,
                "cache_implementation": "offloaded",
            },
            "generation_deadline_probe": {
                "passed": True,
                "deadline_fired": True,
                "finish_reason": "timeout",
                "completion_tokens": 1,
            },
        }
        if gqa_mode is not None:
            payload["gqa_compatibility_mode"] = gqa_mode
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_passes_with_correct_gqa_compatibility_mode(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        self._model_json(tmp_path / "model.json", gqa_mode="repeat_kv_sm75")
        from benchmark.execution.preflight import validate_pilot_launch_authorization
        validate_pilot_launch_authorization(
            repo_preflight_json=tmp_path / "repo.json",
            model_preflight_json=tmp_path / "model.json",
            dryrun_dir=tmp_path / "dryrun",
            expected_source_commit="abc123",
            expected_source_tag="v0.9.18-pilot-exec-ready",
            expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            expected_deployed_build_id="build-001",
        )

    def test_fails_on_wrong_gqa_compatibility_mode(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_valid_dryrun(tmp_path / "dryrun")
        self._model_json(tmp_path / "model.json", gqa_mode="native")
        from benchmark.execution.preflight import (
            LaunchAuthorizationError,
            validate_pilot_launch_authorization,
        )
        with pytest.raises(LaunchAuthorizationError, match="gqa_compatibility_mode"):
            validate_pilot_launch_authorization(
                repo_preflight_json=tmp_path / "repo.json",
                model_preflight_json=tmp_path / "model.json",
                dryrun_dir=tmp_path / "dryrun",
                expected_source_commit="abc123",
                expected_source_tag="v0.9.18-pilot-exec-ready",
                expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
                expected_deployed_build_id="build-001",
            )


class TestValidatePilotDryrunEvidence:
    """PILOT-EXEC-01 D8: the canonical dry-run evidence validator enforces the
    REAL ``RunRecordData`` serialization schema (nested ``token_usage`` plus the
    ``total_workflow_*`` and phase ``*_model_calls`` / ``*_total_tokens``
    fields), never a fabricated top-level ``total_tokens``. Every negative case
    is fail-closed: missing / ``None`` / bool / string / float / non-zero all
    fail. The shared fixture writes the exact real record shape.
    """

    def _validate(self, dryrun_dir: Path) -> dict[str, Any]:
        from benchmark.execution.preflight import validate_pilot_dryrun_evidence
        return validate_pilot_dryrun_evidence(
            dryrun_dir=dryrun_dir,
            expected_source_commit="abc123",
            expected_source_tag="v0.9.18-pilot-exec-ready",
            expected_deployed_build_id="build-001",
            expected_model_identity="dry-run:mock",
        )

    def _assert_raises(self, dryrun_dir: Path, match: str) -> None:
        from benchmark.execution.preflight import LaunchAuthorizationError
        with pytest.raises(LaunchAuthorizationError, match=match):
            self._validate(dryrun_dir)

    def test_real_schema_evidence_passes(self, tmp_path: Path) -> None:
        dryrun = _write_real_dryrun(tmp_path / "dryrun")
        summary = self._validate(dryrun)
        assert summary["passed"] is True
        assert summary["record_count"] == 48
        assert summary["unique_run_ids"] == 48
        assert summary["repo_counts"] == {"todo": 16, "djangocms": 16, "saleor": 16}
        assert summary["strategy_counts"] == {
            "iterative_repository_agent": 24,
            "selective": 24,
        }
        assert summary["rep_counts"] == {1: 24, 2: 24}
        assert summary["model_calls"] == 0
        assert summary["prompt_tokens"] == 0
        assert summary["completion_tokens"] == 0
        assert summary["total_tokens"] == 0
        assert summary["total_workflow_model_calls"] == 0
        assert summary["total_workflow_tokens"] == 0
        assert summary["source_commit"] == "abc123"
        assert summary["source_tag"] == "v0.9.18-pilot-exec-ready"
        assert summary["deployed_build_id"] == "build-001"
        assert summary["model_identity"] == "dry-run:mock"

    def test_real_schema_passes_launch_authorization(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        (tmp_path / "repo.json").write_text(json.dumps({
            "overall": "PASS",
            "repositories": {
                "todo": {"passed": True},
                "djangocms": {"passed": True},
                "saleor": {"passed": True},
            },
        }), encoding="utf-8")
        (tmp_path / "model.json").write_text(json.dumps({
            "passed": True,
            "model_identity": "Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            "requested_quantization_mode": "bnb-nf4",
            "requested_attn_implementation": "sdpa",
            "effective_attn_implementation": "sdpa",
            "sdpa_kernel_policy": "flash_or_efficient_no_math",
            "checks": [
                "repository_preflight_evidence: PASS",
                "qwen_model_load[bnb-nf4]: PASS",
                "short_generation_probe: PASS",
                "long_context_probe: PASS",
            ],
            "long_context_probe": {
                "passed": True,
                "target_prompt_tokens": 16000,
                "prompt_tokens": 16384,
                "completion_tokens": 512,
                "cache_implementation": "offloaded",
            },
            "generation_deadline_probe": {
                "passed": True,
                "deadline_fired": True,
                "finish_reason": "timeout",
                "completion_tokens": 1,
            },
        }), encoding="utf-8")
        dryrun = _write_real_dryrun(tmp_path / "dryrun")
        from benchmark.execution.preflight import validate_pilot_launch_authorization
        validate_pilot_launch_authorization(
            repo_preflight_json=tmp_path / "repo.json",
            model_preflight_json=tmp_path / "model.json",
            dryrun_dir=dryrun,
            expected_source_commit="abc123",
            expected_source_tag="v0.9.18-pilot-exec-ready",
            expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            expected_deployed_build_id="build-001",
        )

    def test_missing_token_usage_fails(self, tmp_path: Path) -> None:
        dryrun = _write_real_dryrun(tmp_path / "dryrun")
        _drop_record_fields(dryrun, ["token_usage"])
        self._assert_raises(dryrun, "token_usage")

    def test_missing_token_usage_total_fails(self, tmp_path: Path) -> None:
        dryrun = _write_real_dryrun(tmp_path / "dryrun")
        path = dryrun / "run_records.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        output = []
        for line in lines:
            record = json.loads(line)
            token_usage = record.get("token_usage")
            if isinstance(token_usage, dict):
                token_usage.pop("total", None)
            output.append(json.dumps(record))
        path.write_text("\n".join(output), encoding="utf-8")
        self._assert_raises(dryrun, "token_usage.total")

    @pytest.mark.parametrize("key,value", [
        ("prompt", None), ("completion", None), ("total", None),
        ("prompt", "0"), ("completion", "0"), ("total", "0"),
        ("prompt", False), ("completion", False), ("total", False),
        ("prompt", 1), ("completion", 1), ("total", 1),
    ])
    def test_token_usage_invalid_or_nonzero_fails(
        self, tmp_path: Path, key: str, value: Any
    ) -> None:
        dryrun = _write_real_dryrun(tmp_path / "dryrun")
        _set_token_usage_value(dryrun, key, value)
        self._assert_raises(dryrun, "token_usage")

    @pytest.mark.parametrize("value,is_override", [
        (None, False), (1, True), (None, True), ("0", True), (False, True),
    ])
    def test_total_workflow_tokens_missing_nonzero_invalid_fail(
        self, tmp_path: Path, value: Any, is_override: bool
    ) -> None:
        dryrun = _write_real_dryrun(tmp_path / "dryrun")
        if is_override:
            _set_record_field(dryrun, "total_workflow_tokens", value)
        else:
            _drop_record_fields(dryrun, ["total_workflow_tokens"])
        self._assert_raises(dryrun, "total_workflow_tokens")

    @pytest.mark.parametrize("value,is_override", [
        (None, False), (1, True), (None, True), ("0", True), (True, True),
    ])
    def test_total_workflow_model_calls_missing_nonzero_invalid_fail(
        self, tmp_path: Path, value: Any, is_override: bool
    ) -> None:
        dryrun = _write_real_dryrun(tmp_path / "dryrun")
        if is_override:
            _set_record_field(dryrun, "total_workflow_model_calls", value)
        else:
            _drop_record_fields(dryrun, ["total_workflow_model_calls"])
        self._assert_raises(dryrun, "total_workflow_model_calls")

    def test_legacy_only_top_level_total_tokens_fails(self, tmp_path: Path) -> None:
        """A fabricated legacy record carrying ONLY top-level ``total_tokens``
        (the pre-D8 false-green shape) must fail: the canonical schema needs the
        nested ``token_usage`` plus workflow/phase fields."""
        dryrun = _write_real_dryrun(tmp_path / "dryrun")
        _drop_record_fields(dryrun, [
            "token_usage",
            "total_workflow_model_calls",
            "total_workflow_tokens",
            "selection_model_calls",
            "regeneration_model_calls",
            "repair_model_calls",
            "selection_total_tokens",
            "regeneration_total_tokens",
            "repair_total_tokens",
        ])
        _set_record_field(dryrun, "total_tokens", 0)
        self._assert_raises(dryrun, "token_usage")

    @pytest.mark.parametrize("phase_field,value", [
        ("selection_model_calls", 1),
        ("regeneration_model_calls", 1),
        ("repair_model_calls", 1),
        ("selection_total_tokens", 1),
        ("regeneration_total_tokens", 1),
        ("repair_total_tokens", 1),
        ("selection_model_calls", None),
        ("selection_model_calls", "0"),
        ("selection_model_calls", False),
        ("repair_total_tokens", 1.5),
    ])
    def test_nonzero_or_invalid_phase_field_fails(
        self, tmp_path: Path, phase_field: str, value: Any
    ) -> None:
        dryrun = _write_real_dryrun(
            tmp_path / "dryrun", record_overrides={phase_field: value}
        )
        self._assert_raises(dryrun, phase_field)

    def test_nonzero_model_calls_fails(self, tmp_path: Path) -> None:
        dryrun = _write_real_dryrun(
            tmp_path / "dryrun",
            record_indices={0},
            record_overrides={"model_calls": 1},
        )
        self._assert_raises(dryrun, "model_calls != 0")

    def test_missing_source_identity_fails(self, tmp_path: Path) -> None:
        dryrun = _write_real_dryrun(tmp_path / "dryrun")
        (dryrun / "source_identity.json").unlink()
        self._assert_raises(dryrun, "source_identity.json")

    def test_source_identity_model_identity_mismatch_fails(self, tmp_path: Path) -> None:
        dryrun = _write_real_dryrun(tmp_path / "dryrun")
        (dryrun / "source_identity.json").write_text(json.dumps({
            "dry_run": True,
            "profile": "pilot",
            "protocol_version": "1.0",
            "source_commit": "abc123",
            "source_tag": "v0.9.18-pilot-exec-ready",
            "deployed_build_id": "build-001",
            "model_identity": "qwen:real",
        }), encoding="utf-8")
        self._assert_raises(dryrun, "model_identity")


class TestGenerationDeadlineProbeErrors:
    """D9.3: fail-closed launch-gate audit of the real-Qwen deadline canary."""

    @staticmethod
    def _errors(value: Any) -> list[str]:
        from benchmark.execution.preflight import _generation_deadline_probe_errors

        return _generation_deadline_probe_errors(value)

    def test_valid_canary_is_clean(self) -> None:
        assert self._errors({
            "passed": True,
            "deadline_fired": True,
            "finish_reason": "timeout",
            "completion_tokens": 1,
        }) == []

    @pytest.mark.parametrize(
        "value, needle",
        [
            (None, "missing or not a dict"),
            ([], "missing or not a dict"),
            ("x", "missing or not a dict"),
            ({"passed": False, "deadline_fired": True,
              "finish_reason": "timeout", "completion_tokens": 1}, "passed != true"),
            ({"passed": True, "deadline_fired": False,
              "finish_reason": "timeout", "completion_tokens": 1}, "deadline_fired != true"),
            ({"passed": True, "deadline_fired": True,
              "finish_reason": "eos", "completion_tokens": 1}, "expected 'timeout'"),
            ({"passed": True, "deadline_fired": True,
              "finish_reason": "timeout", "completion_tokens": True}, "expected int"),
            ({"passed": True, "deadline_fired": True,
              "finish_reason": "timeout", "completion_tokens": 0}, "expected >= 1"),
            ({"passed": True, "deadline_fired": True,
              "finish_reason": "timeout", "completion_tokens": 9}, "upper bound"),
        ],
    )
    def test_fail_closed_invalid_evidence(
        self, value: Any, needle: str
    ) -> None:
        errors = self._errors(value)
        assert any(needle in e for e in errors)

    def test_upper_bound_is_canonical_eight(self) -> None:
        from benchmark.execution.preflight import (
            GENERATION_DEADLINE_PROBE_MAX_CHECK_BOUND,
        )

        assert GENERATION_DEADLINE_PROBE_MAX_CHECK_BOUND == 8
        assert self._errors({
            "passed": True, "deadline_fired": True,
            "finish_reason": "timeout", "completion_tokens": 8,
        }) == []
        assert any(
            "upper bound" in e
            for e in self._errors({
                "passed": True, "deadline_fired": True,
                "finish_reason": "timeout", "completion_tokens": 9,
            })
        )


class _FakeCompleted:
    def __init__(self, returncode: int, stdout: str, stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TestRemoteTagPeelProof:
    """D9.5: launch/resume annotated-tag peel proof (no network, no shell)."""

    @staticmethod
    def _patch_subprocess(
        monkeypatch: pytest.MonkeyPatch, completed: _FakeCompleted
    ) -> list[list[str]]:

        import benchmark.execution.preflight as pf

        captured: list[list[str]] = []

        def fake_run(argv: list[str], **_kw: object) -> _FakeCompleted:
            captured.append(argv)
            return completed

        monkeypatch.setattr(pf.subprocess, "run", fake_run)
        return captured

    def test_pass_with_annotated_tag_matching_source(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from benchmark.execution.preflight import verify_remote_annotated_tag_peel

        sha = "9" * 40
        completed = _FakeCompleted(
            returncode=0,
            stdout=f"{sha}\trefs/tags/v0.9.22-pilot-exec-ready\n"
                   f"{sha}\trefs/tags/v0.9.22-pilot-exec-ready^{{}}\n",
        )
        captured = self._patch_subprocess(monkeypatch, completed)
        result = verify_remote_annotated_tag_peel(source_commit=sha)
        assert result["peel"] == sha
        assert result["tag"] == "v0.9.22-pilot-exec-ready"
        assert "ls-remote" in captured[0][1]
        assert "--tags" in captured[0]
        assert any(
            a == "refs/tags/v0.9.22-pilot-exec-ready^{}" for a in captured[0]
        )

    def test_fails_when_peel_does_not_match_source(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from benchmark.execution.preflight import (
            LaunchAuthorizationError,
            verify_remote_annotated_tag_peel,
        )

        ref_sha = "8" * 40
        peel_sha = "7" * 40
        completed = _FakeCompleted(
            returncode=0,
            stdout=f"{ref_sha}\trefs/tags/v0.9.22-pilot-exec-ready\n"
                   f"{peel_sha}\trefs/tags/v0.9.22-pilot-exec-ready^{{}}\n",
        )
        self._patch_subprocess(monkeypatch, completed)
        with pytest.raises(LaunchAuthorizationError, match="peel .* != source_commit"):
            verify_remote_annotated_tag_peel(source_commit="1" * 40)

    def test_fails_when_lightweight_tag_missing_peel(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from benchmark.execution.preflight import (
            LaunchAuthorizationError,
            verify_remote_annotated_tag_peel,
        )

        sha = "2" * 40
        completed = _FakeCompleted(
            returncode=0,
            stdout=f"{sha}\trefs/tags/v0.9.22-pilot-exec-ready\n",
        )
        self._patch_subprocess(monkeypatch, completed)
        with pytest.raises(LaunchAuthorizationError, match="not present"):
            verify_remote_annotated_tag_peel(source_commit=sha)

    def test_fails_on_nonzero_exit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from benchmark.execution.preflight import (
            LaunchAuthorizationError,
            verify_remote_annotated_tag_peel,
        )

        self._patch_subprocess(
            monkeypatch, _FakeCompleted(returncode=128, stdout="")
        )
        with pytest.raises(LaunchAuthorizationError, match="exited 128"):
            verify_remote_annotated_tag_peel(source_commit="3" * 40)

    def test_fails_when_git_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:

        import benchmark.execution.preflight as pf
        from benchmark.execution.preflight import (
            LaunchAuthorizationError,
            verify_remote_annotated_tag_peel,
        )

        def raise_fnf(argv: list[str], **_kw: object) -> _FakeCompleted:
            raise FileNotFoundError()

        monkeypatch.setattr(pf.subprocess, "run", raise_fnf)
        with pytest.raises(LaunchAuthorizationError, match="'git' is not installed"):
            verify_remote_annotated_tag_peel(source_commit="4" * 40)

    def test_fails_on_timeout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import subprocess

        import benchmark.execution.preflight as pf
        from benchmark.execution.preflight import (
            LaunchAuthorizationError,
            verify_remote_annotated_tag_peel,
        )

        def raise_timeout(argv: list[str], **_kw: object) -> _FakeCompleted:
            raise subprocess.TimeoutExpired(argv, timeout=30)

        monkeypatch.setattr(pf.subprocess, "run", raise_timeout)
        with pytest.raises(LaunchAuthorizationError, match="timed out"):
            verify_remote_annotated_tag_peel(source_commit="5" * 40)


class TestLaunchAuthMandatoryDeadlineCanary:
    """D9.3: launch authorization fails closed without a valid deadline canary."""

    def _write_valid_repo_preflight(self, path: Path) -> None:
        path.write_text(json.dumps({
            "overall": "PASS",
            "repositories": {
                "todo": {"passed": True},
                "djangocms": {"passed": True},
                "saleor": {"passed": True},
            },
        }), encoding="utf-8")

    def _write_dryrun(self, dryrun_dir: Path) -> None:
        _write_real_dryrun(
            dryrun_dir,
            source_commit="abc123",
            source_tag="v0.9.18-pilot-exec-ready",
            deployed_build_id="build-001",
        )

    def _write_model(self, path: Path, *, canary: Any) -> None:
        path.write_text(json.dumps({
            "passed": True,
            "model_identity": "Qwen2.5-Coder-14B-Instruct-bnb-nf4",
            "requested_quantization_mode": "bnb-nf4",
            "requested_attn_implementation": "sdpa",
            "effective_attn_implementation": "sdpa",
            "sdpa_kernel_policy": "flash_or_efficient_no_math",
            "checks": ["repository_preflight_evidence: PASS"],
            "long_context_probe": {
                "passed": True,
                "target_prompt_tokens": 16000,
                "prompt_tokens": 16384,
                "completion_tokens": 512,
                "cache_implementation": "offloaded",
            },
            "generation_deadline_probe": canary,
        }), encoding="utf-8")

    def _validate(self, tmp_path: Path, **_kw: object) -> None:
        from benchmark.execution.preflight import validate_pilot_launch_authorization

        validate_pilot_launch_authorization(
            repo_preflight_json=tmp_path / "repo.json",
            model_preflight_json=tmp_path / "model.json",
            dryrun_dir=tmp_path / "dryrun",
            expected_source_commit="abc123",
            expected_source_tag="v0.9.18-pilot-exec-ready",
            expected_model_identity="Qwen2.5-Coder-14B-Instruct-bnb-nf4",
        )

    def test_missing_canary_fails_closed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_dryrun(tmp_path / "dryrun")
        self._write_model(tmp_path / "model.json", canary=None)
        from benchmark.execution.preflight import LaunchAuthorizationError

        with pytest.raises(LaunchAuthorizationError, match="generation_deadline_probe"):
            self._validate(tmp_path)

    def test_eos_canary_fails_closed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_dryrun(tmp_path / "dryrun")
        self._write_model(
            tmp_path / "model.json",
            canary={
                "passed": True,
                "deadline_fired": False,
                "finish_reason": "eos",
                "completion_tokens": 512,
            },
        )
        from benchmark.execution.preflight import LaunchAuthorizationError

        with pytest.raises(LaunchAuthorizationError, match="deadline_fired != true"):
            self._validate(tmp_path)

    def test_valid_canary_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HF_TOKEN", "test-token-123")
        self._write_valid_repo_preflight(tmp_path / "repo.json")
        self._write_dryrun(tmp_path / "dryrun")
        self._write_model(tmp_path / "model.json", canary={
            "passed": True,
            "deadline_fired": True,
            "finish_reason": "timeout",
            "completion_tokens": 1,
        })
        self._validate(tmp_path)

