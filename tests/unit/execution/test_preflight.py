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
            model_identity="qwen:1:int8",
            quantization_mode="int8",
            free_vram_after_probe_gib=0.1,
            probe_prompt_tokens=8,
            probe_completion_tokens=64,
            dependencies=(("torch", "2.4.0"),),
        )
        table = render_preflight_table(result)
        assert "KAGGLE SMOKE PREFLIGHT" in table
        assert "passed: False" in table
        assert "model_identity: qwen:1:int8" in table
        assert "quantization_mode: int8" in table
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

        def _probe(model_path: str) -> dict[str, object]:
            if probe_exc is not None:
                raise probe_exc
            return probe_metrics or {
                "model_identity": "qwen:1:int8",
                "quantization_mode": "int8",
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
        assert any(c.startswith("qwen_int8_load: PASS") for c in result.checks)
        assert any(c.startswith("vram_headroom: PASS") for c in result.checks)
        assert result.model_identity == "qwen:1:int8"

    def test_fail_when_missing_dependency(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        self._patch(monkeypatch, deps=(("torch", "NOT_INSTALLED"),))
        result = run_kaggle_smoke_preflight(
            model_path="/kaggle/input/qwen",
            data_dir=tmp_path,
            preflight_root=tmp_path / "preflight-root",
        )
        assert result.passed is False
        assert any(c.startswith("dependency_import_verification: FAIL") for c in result.checks)
        assert "torch" in result.rejection_reason

    def test_fail_when_vram_headroom_below_threshold(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._patch(
            monkeypatch,
            deps=(("django", "5.2.16"),),
            probe_metrics={
                "model_identity": "qwen:1:int8",
                "quantization_mode": "int8",
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
        assert any(c.startswith("qwen_int8_load: FAIL") for c in result.checks)
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
        assert payload["model_identity"] == "qwen:1:int8"

