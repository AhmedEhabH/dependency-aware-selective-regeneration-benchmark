from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmark.execution import preflight as mod
from benchmark.execution.preflight import (
    MIN_FREE_VRAM_GIB,
    KaggleSmokePreflightResult,
    collect_dependency_versions,
    render_preflight_table,
    run_kaggle_smoke_preflight,
)


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

        def _probe(model_path: str, quantization_mode: str) -> dict[str, object]:
            if probe_exc is not None:
                raise probe_exc
            return probe_metrics or {
                "model_identity": "qwen:qwen2.5-coder-7b-instruct:bnb-int8:cfg-abc123",
                "requested_quantization_mode": quantization_mode,
                "model_checkpoint_basename": "qwen2.5-coder-7b-instruct",
                "checkpoint_quantization_method": "",
                "model_memory_footprint_bytes": 4000000000,
                "device_map_summary": "cuda:0",
                "gpu_count": 1,
                "gpu_name": "T4",
                "allocated_vram_gib": 12.5,
                "reserved_vram_gib": 14.0,
                "free_vram_after_probe_gib": 2.5,
                "probe_prompt_tokens": 8,
                "probe_completion_tokens": 64,
            }

        monkeypatch.setattr(mod, "_qwen_probe_metrics", _probe)

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

    def test_nf4_quantization_is_forwarded_to_probe_and_check_name(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        received: list[str] = []

        def probe(model_path: str, quantization_mode: str) -> dict[str, object]:
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

        def probe(_model_path: str, _quantization_mode: str) -> dict[str, object]:
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

        def probe(_model_path: str, _quantization_mode: str) -> dict[str, object]:
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

    def test_baseline_failure_skips_expensive_model_probe(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch(monkeypatch, deps=(("django", "5.2.16"),))
        calls = 0

        def run_command(_ws: Path, *argv: str, timeout: int = 180):
            if argv[-1] == "check":
                return 1, "", "baseline broken"
            return 0, "", ""

        def probe(_model_path: str, _quantization_mode: str) -> dict[str, object]:
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

