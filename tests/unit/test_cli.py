from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_DIR / "seven_arm_benchmark.py"
BENCHMARK_DATA = PROJECT_DIR / "benchmark_data"

assert SCRIPT.is_file(), f"Script not found: {SCRIPT}"
assert BENCHMARK_DATA.is_dir(), f"Benchmark data not found: {BENCHMARK_DATA}"


def _run(*args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    base_env = dict(os.environ)
    if env is not None:
        base_env.update(env)
        if "OPENROUTER_API_KEY" not in base_env:
            base_env["OPENROUTER_API_KEY"] = "sk-or-v1-DO-NOT-LEAK-12345"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=cwd or PROJECT_DIR,
        env=base_env,
    )


def _create_valid_data_dir(root: Path) -> Path:
    data_dir = root / "data"
    for subdir in ("scenarios", "manifests", "repository_profiles"):
        (data_dir / subdir).mkdir(parents=True)
    dummy_yaml = textwrap.dedent("""\
        scenario_id: "test-001"
        repository: todo
        change_type: "test"
        blast_radius: localized
        requirement_before: "before"
        requirement_after: "after"
        rationale: "test"
    """)
    (data_dir / "scenarios" / "test-001.yaml").write_text(dummy_yaml)
    return data_dir


def _create_valid_model_dir(root: Path) -> Path:
    model_dir = root / "model"
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text("{}")
    (model_dir / "model.safetensors").write_text("dummy")
    return model_dir


class TestCliArgsRejection:
    def test_rejects_missing_data_dir(self, tmp_path: Path) -> None:
        result = _run("--dry-run", "--data-dir", str(tmp_path / "nonexistent"))
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "does not exist" in combined

    def test_rejects_missing_scenarios_subdir(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "scenarios").mkdir()
        result = _run("--dry-run", "--data-dir", str(data_dir))
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "missing required subdirectory" in combined

    def test_rejects_missing_manifests_subdir(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "scenarios").mkdir()
        (data_dir / "repository_profiles").mkdir()
        result = _run("--dry-run", "--data-dir", str(data_dir))
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "missing required subdirectory" in combined

    def test_rejects_missing_repository_profiles_subdir(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "scenarios").mkdir()
        (data_dir / "manifests").mkdir()
        result = _run("--dry-run", "--data-dir", str(data_dir))
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "missing required subdirectory" in combined

    def test_real_mode_rejects_missing_model_path(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run("--profile", "smoke", "--data-dir", str(data_dir))
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "--model-path is required" in combined

    def test_real_mode_rejects_nonexistent_model_path(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run(
            "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--model-path", str(tmp_path / "no-such-model"),
        )
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "does not exist" in combined

    def test_rejects_model_path_missing_config(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        model_dir = tmp_path / "model"
        model_dir.mkdir(parents=True)
        (model_dir / "model.safetensors").write_text("dummy")
        result = _run(
            "--dry-run",
            "--data-dir", str(data_dir),
            "--model-path", str(model_dir),
        )
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "missing config.json" in combined

    def test_rejects_model_path_missing_weights(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        model_dir = tmp_path / "model"
        model_dir.mkdir(parents=True)
        (model_dir / "config.json").write_text("{}")
        result = _run(
            "--dry-run",
            "--data-dir", str(data_dir),
            "--model-path", str(model_dir),
        )
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "no weight files" in combined


class TestCliArgsAcceptance:
    def test_dry_run_with_valid_data_dir(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run(
            "--dry-run", "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--output-dir", str(tmp_path / "runs"),
        )
        assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    def test_dry_run_without_model_path(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run(
            "--dry-run", "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--output-dir", str(tmp_path / "runs"),
        )
        assert result.returncode == 0

    def test_valid_model_path_accepted_in_dry_run(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        model_dir = _create_valid_model_dir(tmp_path)
        result = _run(
            "--dry-run", "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--model-path", str(model_dir),
            "--output-dir", str(tmp_path / "runs"),
        )
        assert result.returncode == 0

    def test_output_dir_is_created(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        output_dir = tmp_path / "custom-runs"
        result = _run(
            "--dry-run", "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--output-dir", str(output_dir),
        )
        assert result.returncode == 0
        assert output_dir.is_dir()


class TestCliNoNetworkOrGit:
    SCRIPT_TEXT: str = ""

    @classmethod
    def setup_class(cls) -> None:
        cls.SCRIPT_TEXT = SCRIPT.read_text(encoding="utf-8")

    def test_no_network_libraries_imported(self) -> None:
        source = self.SCRIPT_TEXT
        assert "import requests" not in source
        assert "urllib.request" not in source
        assert "from huggingface_hub import" not in source
        assert "import huggingface_hub" not in source

    def test_no_git_libraries_imported(self) -> None:
        source = self.SCRIPT_TEXT
        assert "import git" not in source
        assert "from git import" not in source
        assert "gitpython" not in source.lower()
        assert "github" not in source.lower()

    def test_no_subprocess_git_call(self) -> None:
        source = self.SCRIPT_TEXT
        git_calls = 0
        for line in source.splitlines():
            if 'subprocess.run' in line and '"git"' in line:
                git_calls += 1
        # Allow exactly the _get_source_commit metadata function
        assert git_calls <= 1, f"Expected <= 1 git subprocess call, got {git_calls}"


class TestRunsDirBugFix:
    """Regression tests for the runs_dir NameError bug (SU-0002)."""

    def test_start_new_path_no_nameerror(self, tmp_path: Path) -> None:
        """Test START_NEW path (without --auto-resume-hf) does not raise NameError for runs_dir."""
        data_dir = _create_valid_data_dir(tmp_path)
        output_dir = tmp_path / "runs"
        result = _run(
            "--dry-run", "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--output-dir", str(output_dir),
        )
        assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        # output_dir should exist after successful run
        assert output_dir.is_dir()

    def test_resume_path_no_nameerror(self, tmp_path: Path) -> None:
        """Test RESUME path (with --resume) does not raise NameError for runs_dir."""
        data_dir = _create_valid_data_dir(tmp_path)
        output_dir = tmp_path / "runs"
        # First run creates the output dir
        result = _run(
            "--dry-run", "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--output-dir", str(output_dir),
        )
        assert result.returncode == 0
        # Second run with --resume should not raise NameError
        result = _run(
            "--dry-run", "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--output-dir", str(output_dir),
            "--resume",
        )
        assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"


class TestCliOpenRouter:
    def test_openrouter_backend_accepted(self, tmp_path: Path) -> None:
        """Arguments are accepted with --dry-run (no real API call)."""
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run(
            "--dry-run",
            "--backend", "openrouter",
            "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--output-dir", str(tmp_path / "runs"),
            env={},
        )
        assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    def test_openrouter_model_default_in_help(self) -> None:
        result = _run("--help")
        assert "openrouter" in result.stdout
        assert "OPENROUTER_API_KEY" in result.stdout.upper()

    def test_no_api_key_cli_parameter(self) -> None:
        """--api-key must NOT be a CLI argument."""
        script_text = SCRIPT.read_text(encoding="utf-8")
        assert '--api-key' not in script_text
        assert '--openrouter-api-key' not in script_text

    def test_openrouter_model_custom_value(self, tmp_path: Path) -> None:
        """Custom model is accepted with --dry-run (no real API call)."""
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run(
            "--dry-run",
            "--backend", "openrouter",
            "--openrouter-model", "anthropic/claude-3-opus",
            "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--output-dir", str(tmp_path / "runs"),
            env={},
        )
        assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    def test_openrouter_timeout_custom_value(self, tmp_path: Path) -> None:
        """Custom timeout is accepted with --dry-run (no real API call)."""
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run(
            "--dry-run",
            "--backend", "openrouter",
            "--openrouter-timeout", "60",
            "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--output-dir", str(tmp_path / "runs"),
            env={},
        )
        assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    def test_openrouter_rejects_missing_api_key(self, tmp_path: Path) -> None:
        """Preflight rejects missing key without network access."""
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run(
            "--backend", "openrouter",
            "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--output-dir", str(tmp_path / "runs"),
            env={"OPENROUTER_API_KEY": ""},
        )
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "OPENROUTER_API_KEY" in combined


class TestKaggleQwenFailClosed:
    """KAGGLE-SMOKE-V2: fail closed when the Qwen model is missing or unresolved."""

    def test_explicit_kaggle_qwen_empty_model_path_fails(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run(
            "--backend", "kaggle-qwen",
            "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--model-path", "",
        )
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "--model-path is required" in combined
        assert "kaggle-qwen" in combined

    def test_implicit_kaggle_qwen_empty_model_path_fails(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run(
            "--profile", "smoke",
            "--data-dir", str(data_dir),
        )
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "--model-path is required" in combined

    def test_explicit_kaggle_qwen_nonexistent_model_path_fails(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run(
            "--backend", "kaggle-qwen",
            "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--model-path", str(tmp_path / "no-such-qwen"),
        )
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "does not exist" in combined

    def test_kaggle_qwen_requires_config_and_weights(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        model_dir = tmp_path / "model"
        model_dir.mkdir(parents=True)
        (model_dir / "config.json").write_text("{}")
        result = _run(
            "--backend", "kaggle-qwen",
            "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--model-path", str(model_dir),
        )
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "no weight files" in combined

    def test_missing_model_does_not_create_experiment(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        output_dir = tmp_path / "runs"
        result = _run(
            "--backend", "kaggle-qwen",
            "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--model-path", "",
            "--output-dir", str(output_dir),
        )
        assert result.returncode == 1
        assert not output_dir.exists() or not (output_dir / "checkpoint.json").exists()


QWEN_CONFIG_JSON = (
    '{"model_type": "qwen2", "hidden_size": 2048, "num_hidden_layers": 28,'
    ' "num_attention_heads": 16}'
)


def _create_qwen_model_dir(root: Path, name: str = "qwen2.5-coder-14b-instruct") -> Path:
    model_dir = root / name
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text(QWEN_CONFIG_JSON)
    (model_dir / "model.safetensors").write_text("dummy")
    return model_dir


class TestModelIdentity:
    """QWEN14B-NF4-CANARY: identity is checkpoint-and-quantization-aware, never dry-run:mock."""

    @staticmethod
    def _identity(
        model_path: str | None = None,
        backend: str | None = None,
        openrouter: str = "",
        qwen_quantization: str = "bnb-int8",
    ) -> str:
        from seven_arm_benchmark import _get_model_identity

        return _get_model_identity(
            model_path=model_path,
            backend_name=backend,
            openrouter_model=openrouter,
            qwen_quantization=qwen_quantization,
        )

    def test_kaggle_qwen_with_model_path_is_model_aware_identity(self, tmp_path: Path) -> None:
        model_dir = _create_qwen_model_dir(tmp_path)
        identity = self._identity(model_path=str(model_dir), backend="kaggle-qwen")
        assert identity.startswith("qwen:qwen2.5-coder-14b-instruct:bnb-int8:cfg-")
        assert len(identity.split("cfg-")[1]) == 12
        assert identity != "qwen:1:int8"

    def test_kaggle_qwen_identity_changes_with_quantization_mode(self, tmp_path: Path) -> None:
        model_dir = _create_qwen_model_dir(tmp_path)
        int8 = self._identity(model_path=str(model_dir), backend="kaggle-qwen", qwen_quantization="bnb-int8")
        nf4 = self._identity(model_path=str(model_dir), backend="kaggle-qwen", qwen_quantization="bnb-nf4")
        assert int8 != nf4
        assert ":bnb-nf4:" in nf4
        assert ":bnb-int8:" in int8

    def test_kaggle_qwen_identity_changes_with_checkpoint(self, tmp_path: Path) -> None:
        model_dir = _create_qwen_model_dir(tmp_path, name="qwen2.5-coder-7b-instruct")
        identity = self._identity(model_path=str(model_dir), backend="kaggle-qwen")
        assert identity.startswith("qwen:qwen2.5-coder-7b-instruct:bnb-int8:cfg-")

    def test_kaggle_qwen_without_model_path_raises(self) -> None:
        from seven_arm_benchmark import _get_model_identity

        with pytest.raises(ValueError, match="model_path is required"):
            _get_model_identity(model_path=None, backend_name="kaggle-qwen")

    def test_mock_dry_run_identity_remains_dry_run_mock(self) -> None:
        assert self._identity(backend="mock") == "dry-run:mock"
        assert self._identity(backend=None) == "dry-run:mock"

    def test_openrouter_identity(self) -> None:
        identity = self._identity(backend="openrouter", openrouter="nvidia/nemotron-3-super-120b-a12b:free")
        assert identity == "openrouter:nvidia/nemotron-3-super-120b-a12b:free"


class TestKagglePreflightOnly:
    """R7C-REAL-RUN-ROOT-CLOSURE: preflight gate creates no experiment state."""

    def test_preflight_only_fails_locally_and_creates_no_experiment(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        model_dir = _create_valid_model_dir(tmp_path)
        output_dir = tmp_path / "runs"
        result = _run(
            "--kaggle-preflight-only",
            "--model-path", str(model_dir),
            "--data-dir", str(data_dir),
            "--output-dir", str(output_dir),
        )
        combined = result.stdout + result.stderr
        # Real preflight cannot pass on a torch-less local machine.
        assert result.returncode == 1, combined
        assert "KAGGLE SMOKE PREFLIGHT" in combined
        # No experiment / workspace / checkpoint state is created.
        assert not (output_dir / "checkpoint.json").exists()
        assert not (output_dir / "workspace").exists()
        # The preflight JSON report is still written for the audit trail.
        assert (output_dir / "kaggle_smoke_preflight.v1.json").is_file()

    def test_preflight_only_rejects_dry_run_combination(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        model_dir = _create_valid_model_dir(tmp_path)
        result = _run(
            "--kaggle-preflight-only",
            "--dry-run",
            "--model-path", str(model_dir),
            "--data-dir", str(data_dir),
        )
        assert result.returncode == 1
        assert "must not be combined with --dry-run" in (result.stdout + result.stderr)


class TestCliHelp:
    def test_scientific_smoke_v2_in_profile_help(self) -> None:
        result = _run("--help")
        assert result.returncode == 0
        help_text = " ".join(result.stdout.split())
        assert "scientific-smoke-v2" in help_text
        assert "three-arm" in help_text
        assert "3 scenarios x 3 arms x 1 repetition" in help_text
        assert "non-publication" in help_text
        assert "scientific-smoke-v1" in help_text

    def test_description_is_seven_arm_benchmark(self) -> None:
        result = _run("--help")
        assert "Seven-arm dependency-aware selective regeneration benchmark" in result.stdout


class TestQwenQuantizationFlag:
    """QWEN14B-NF4-CANARY: CLI exposes only the canonical BNB quantization modes."""

    def test_help_lists_canonical_choices(self) -> None:
        result = _run("--help")
        combined = result.stdout + result.stderr
        assert "--qwen-quantization" in combined
        assert "bnb-int8" in combined
        assert "bnb-nf4" in combined
        assert "fp16" in combined

    def test_unknown_quantization_exits_2(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run(
            "--dry-run",
            "--profile", "smoke",
            "--qwen-quantization", "gptq",
            "--data-dir", str(data_dir),
            "--output-dir", str(tmp_path / "runs"),
        )
        assert result.returncode == 2
        assert "invalid choice" in (result.stdout + result.stderr)

    def test_dry_run_accepts_bnb_nf4(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run(
            "--dry-run",
            "--profile", "smoke",
            "--qwen-quantization", "bnb-nf4",
            "--data-dir", str(data_dir),
            "--output-dir", str(tmp_path / "runs"),
        )
        assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    def test_dry_run_default_quantization_is_bnb_int8(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        result = _run(
            "--dry-run",
            "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--output-dir", str(tmp_path / "runs"),
        )
        assert result.returncode == 0
        combined = result.stdout + result.stderr
        assert "backend=mock" in combined
        assert "config_hash=" in combined

    def test_quantization_mode_changes_config_hash(self, tmp_path: Path) -> None:
        data_dir = _create_valid_data_dir(tmp_path)
        base = _run(
            "--dry-run",
            "--profile", "smoke",
            "--data-dir", str(data_dir),
            "--output-dir", str(tmp_path / "runs-base"),
        )
        nf4 = _run(
            "--dry-run",
            "--profile", "smoke",
            "--qwen-quantization", "bnb-nf4",
            "--data-dir", str(data_dir),
            "--output-dir", str(tmp_path / "runs-nf4"),
        )
        assert base.returncode == 0
        assert nf4.returncode == 0
        base_hash = re.search(r"config_hash=([0-9a-f]+)", base.stdout + base.stderr).group(1)
        nf4_hash = re.search(r"config_hash=([0-9a-f]+)", nf4.stdout + nf4.stderr).group(1)
        assert base_hash != nf4_hash


class TestEntryPointConversion:
    """SU-0010B2: _to_run_record_data forwards every scoped metric."""

    @staticmethod
    def _make_record_dict(**overrides: Any) -> dict[str, Any]:
        base: dict[str, Any] = {
            "run_id": "test-run-001",
            "scenario_id": "test-scenario-001",
            "strategy_name": "selective",
            "status": "succeeded",
            "duration_seconds": 12.5,
            "token_usage": {"prompt": 100, "completion": 50, "total": 150},
            "failures": [],
        }
        base.update(overrides)
        return base

    def _build(
        self,
        record_dict: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> object:
        from seven_arm_benchmark import _to_run_record_data

        kwargs.setdefault("failure_details", [])
        kwargs.setdefault("failure_classification", "")
        return _to_run_record_data(
            record_dict or self._make_record_dict(),
            run_id="test-run-001",
            profile="smoke",
            repository_id="todo",
            scenario_id="test-scenario-001",
            strategy_id="selective",
            repetition=1,
            model_identity="dry-run:mock",
            dry_run=True,
            protocol_version="1.0",
            source_commit="a1b2c3d",
            config_hash="cfg001",
            started_at="2026-07-26T00:00:00",
            ended_at="2026-07-26T00:01:00",
            hw_id="",
            sw_id="",
            max_attempts=3,
            **kwargs,
        )

    def test_all_metrics_forwarded(self) -> None:
        rd = self._make_record_dict(
            selection_prompt_tokens=10,
            selection_completion_tokens=11,
            selection_total_tokens=12,
            selection_model_calls=13,
            selection_duration_seconds=1.5,
            regeneration_prompt_tokens=20,
            regeneration_completion_tokens=21,
            regeneration_total_tokens=22,
            regeneration_model_calls=23,
            regeneration_duration_seconds=2.5,
            functional_validation_duration_seconds=3.5,
            functional_validation_passed=True,
            total_workflow_tokens=100,
            total_workflow_model_calls=5,
            total_workflow_duration_seconds=10.0,
            selected_artifact_count=3,
            regenerated_artifact_count=2,
            preserved_artifact_count=1,
            unresolved_human_review_count=0,
        )
        rec = self._build(record_dict=rd)
        assert rec.selection_prompt_tokens == 10
        assert rec.selection_completion_tokens == 11
        assert rec.selection_total_tokens == 12
        assert rec.selection_model_calls == 13
        assert rec.selection_duration_seconds == 1.5
        assert rec.regeneration_prompt_tokens == 20
        assert rec.regeneration_completion_tokens == 21
        assert rec.regeneration_total_tokens == 22
        assert rec.regeneration_model_calls == 23
        assert rec.regeneration_duration_seconds == 2.5
        assert rec.functional_validation_duration_seconds == 3.5
        assert rec.functional_validation_passed is True
        assert rec.total_workflow_tokens == 100
        assert rec.total_workflow_model_calls == 5
        assert rec.total_workflow_duration_seconds == 10.0
        assert rec.selected_artifact_count == 3
        assert rec.regenerated_artifact_count == 2
        assert rec.preserved_artifact_count == 1
        assert rec.unresolved_human_review_count == 0

    def test_functional_validation_passed_false(self) -> None:
        rd = self._make_record_dict(
            functional_validation_passed=False,
        )
        rec = self._build(record_dict=rd)
        assert rec.functional_validation_passed is False

    def test_functional_validation_passed_none(self) -> None:
        """When key is absent, functional_validation_passed defaults to None."""
        rec = self._build()
        assert rec.functional_validation_passed is None

    def test_functional_validation_passed_explicit_none(self) -> None:
        rd = self._make_record_dict(
            functional_validation_passed=None,
        )
        rec = self._build(record_dict=rd)
        assert rec.functional_validation_passed is None

    def test_total_workflow_tokens_not_replaced(self) -> None:
        """total_workflow_tokens is independent of token_usage total."""
        rd = self._make_record_dict(
            token_usage={"prompt": 500, "completion": 300, "total": 800},
            total_workflow_tokens=100,
        )
        rec = self._build(record_dict=rd)
        assert rec.total_workflow_tokens == 100
        assert rec.token_usage["total"] == 800

    def test_selection_and_regeneration_not_swapped(self) -> None:
        rd = self._make_record_dict(
            selection_total_tokens=10,
            regeneration_total_tokens=20,
        )
        rec = self._build(record_dict=rd)
        assert rec.selection_total_tokens == 10
        assert rec.regeneration_total_tokens == 20

    def test_artifact_counts_survive(self) -> None:
        rd = self._make_record_dict(
            selected_artifact_count=5,
            regenerated_artifact_count=3,
            preserved_artifact_count=7,
            unresolved_human_review_count=1,
        )
        rec = self._build(record_dict=rd)
        assert rec.selected_artifact_count == 5
        assert rec.regenerated_artifact_count == 3
        assert rec.preserved_artifact_count == 7
        assert rec.unresolved_human_review_count == 1

    def test_historical_compatibility(self) -> None:
        """Legacy record_dict without e2e keys: all new fields get defaults."""
        rec = self._build()
        assert rec.selection_prompt_tokens == 0
        assert rec.selection_completion_tokens == 0
        assert rec.selection_total_tokens == 0
        assert rec.selection_model_calls == 0
        assert rec.selection_duration_seconds == 0.0
        assert rec.regeneration_prompt_tokens == 0
        assert rec.regeneration_completion_tokens == 0
        assert rec.regeneration_total_tokens == 0
        assert rec.regeneration_model_calls == 0
        assert rec.regeneration_duration_seconds == 0.0
        assert rec.functional_validation_duration_seconds == 0.0
        assert rec.functional_validation_passed is None
        assert rec.total_workflow_tokens == 0
        assert rec.total_workflow_model_calls == 0
        assert rec.total_workflow_duration_seconds == 0.0
        assert rec.selected_artifact_count == 0
        assert rec.regenerated_artifact_count == 0
        assert rec.preserved_artifact_count == 0
        assert rec.unresolved_human_review_count == 0


class TestScientificSmokeV1Profile:
    """Targeted regression tests for the scientific-smoke-v1 profile."""

    def test_profile_contains_exact_three_strategies(self) -> None:
        from seven_arm_benchmark import PROFILES
        profile = PROFILES["scientific-smoke-v1"]
        assert profile.strategies == ["monolithic", "selective", "iterative_repository_agent"]
        assert len(profile.strategies) == 3

    def test_profile_repetitions_and_scenario_count(self) -> None:
        from seven_arm_benchmark import PROFILES
        profile = PROFILES["scientific-smoke-v1"]
        assert profile.repetitions == 1
        assert profile.scenario_count == 1

    def test_profile_has_exact_scenario_id(self) -> None:
        from seven_arm_benchmark import PROFILES
        profile = PROFILES["scientific-smoke-v1"]
        assert profile.scenario_ids == ["todo-loc-001"]

    def test_execution_plan_contains_exactly_three_runs(self) -> None:
        from benchmark.core.models import Scenario
        from seven_arm_benchmark import PROFILES, _build_execution_plan
        profile = PROFILES["scientific-smoke-v1"]
        scenario = Scenario(
            scenario_id="todo-loc-001",
            repository="todo",
            change_type="schema",
            blast_radius="localized",
            requirement_before="",
            requirement_after="",
            rationale="test",
        )
        plan = _build_execution_plan(
            profile=profile,
            scenario_provider=None,
            strategy_names=profile.strategies,
            scenarios=[scenario],
        )
        assert len(plan) == 3
        strategies_in_plan = [r["strategy_name"] for r in plan]
        assert strategies_in_plan.count("monolithic") == 1
        assert strategies_in_plan.count("selective") == 1
        assert strategies_in_plan.count("iterative_repository_agent") == 1

    def test_missing_scenario_id_fails_clearly(self) -> None:
        from seven_arm_benchmark import PROFILES
        profile = PROFILES["scientific-smoke-v1"]
        assert profile.scenario_ids is not None
        from benchmark.core.models import Scenario
        available = [
            Scenario(
                scenario_id="todo-loc-999", repository="todo",
                change_type="schema", blast_radius="localized",
                requirement_before="", requirement_after="", rationale="x",
            ),
        ]
        missing = [sid for sid in profile.scenario_ids if not any(s.scenario_id == sid for s in available)]
        assert missing == ["todo-loc-001"]

    def test_pilot_profile_selection_unchanged(self) -> None:
        from seven_arm_benchmark import PROFILES
        pilot = PROFILES["pilot"]
        assert pilot.strategies == ["agent", "selective"]
        assert pilot.repetitions == 2
        assert pilot.scenario_ids is None

    def test_research_profile_selection_unchanged(self) -> None:
        from seven_arm_benchmark import PROFILES
        research = PROFILES["research"]
        assert research.strategies == ["agent", "selective", "compiled_ai", "delta_mcp"]
        assert research.repetitions == 3
        assert research.scenario_ids is None

    def test_no_duplicate_profile_fields(self) -> None:
        from seven_arm_benchmark import ExecutionProfile
        members = [m for m in dir(ExecutionProfile) if not m.startswith("_")]
        assert members.count("repository_names") == 1
        assert members.count("blast_radii") == 1
        assert "scenario_ids" in members

    def test_notebook_benchmark_command_args(self) -> None:
        """Parse both notebooks and verify all V2 benchmark command cells."""
        import json
        canonical_nb = PROJECT_DIR / "notebooks" / "seven_arm_benchmark.ipynb"
        with open(canonical_nb, encoding="utf-8") as f:
            canonical = json.load(f)
        canonical_setup = "".join(
            next(c for c in canonical["cells"] if c.get("id") == "setup-cell")["source"]
        )
        runtime_source_commit = canonical_setup.split('SOURCE_COMMIT = "')[1].split('"')[0]
        runtime_build_id = runtime_source_commit[:7]

        notebook_paths = [
            PROJECT_DIR / "notebooks" / "seven_arm_benchmark.ipynb",
            PROJECT_DIR / "kaggle_upload" / "notebooks" / "seven_arm_benchmark.ipynb",
        ]

        parsed = []
        for nb_path in notebook_paths:
            if not nb_path.is_file():
                continue
            with open(nb_path) as f:
                nb = json.load(f)

            cells_by_id = {c.get("id"): c for c in nb["cells"]}
            setup_src = "".join(cells_by_id["setup-cell"]["source"])
            assert f'SOURCE_COMMIT = "{runtime_source_commit}"' in setup_src, nb_path
            assert f'DEPLOYED_BUILD_ID = "{runtime_build_id}"' in setup_src, nb_path
            assert "scientific-smoke-v2" in setup_src, nb_path
            assert "76ef349" not in setup_src, nb_path
            assert "scientific-smoke-v1" not in setup_src, nb_path

            exec_cmds: list[tuple[str, str]] = []
            for cell in nb["cells"]:
                if cell["cell_type"] != "code":
                    continue
                src = cell["source"]
                src_str = src if isinstance(src, str) else "".join(src)
                if "SCRIPT_PATH" in src_str and "exec_cmd = [" in src_str:
                    exec_cmds.append((cell.get("id", ""), src_str))

            assert len(exec_cmds) == 1, (
                f"{nb_path}: expected exactly one Full-9 benchmark cell, got {len(exec_cmds)}"
            )

            for cid, src_str in exec_cmds:
                required = [
                    ('"--backend", "kaggle-qwen"', "backend kaggle-qwen"),
                    ('"--profile", "scientific-smoke-v2"', "profile scientific-smoke-v2"),
                    ('"--protocol-version", "1.0"', "protocol-version 1.0"),
                    ('"--max-attempts", "3"', "max-attempts 3"),
                    ('"--max-completion-tokens-per-call", "1024"', "max-completion-tokens-per-call 1024"),
                    ('"--max-total-workflow-tokens", "0"', "max-total-workflow-tokens 0"),
                    ('"--timeout", "600"', "timeout 600"),
                ]
                for needle, label in required:
                    assert needle in src_str, f"{nb_path} cell [{cid}]: missing {label}"
                assert '"--timeout", "300"' not in src_str, (
                    f"{nb_path} cell [{cid}]: stale 300-second timeout still in the Full-9 command"
                )
                assert src_str.count('"--timeout"') == 1, (
                    f"{nb_path} cell [{cid}]: Full-9 must set exactly one per-run timeout "
                    "applying uniformly to all three strategies"
                )
                assert '"--max-tokens"' not in src_str, f"{nb_path} cell [{cid}]: still has --max-tokens"
                assert '"scientific-smoke-v1"' not in src_str, (
                    f"{nb_path} cell [{cid}]: still has --profile scientific-smoke-v1"
                )
                assert '"smoke"' not in src_str.replace("scientific-smoke-v2", ""), (
                    f"{nb_path} cell [{cid}]: still has old --profile smoke"
                )
                assert '"pilot"' not in src_str, f"{nb_path} cell [{cid}]: has pilot profile"
                assert '"research"' not in src_str, f"{nb_path} cell [{cid}]: has research profile"
                assert cid == "full9-execution-cell", (
                    f"{nb_path}: benchmark command must live in full9-execution-cell, got [{cid}]"
                )
                assert '"--max-runs"' not in src_str, (
                    f"{nb_path} cell [{cid}]: Full-9 cell must not use --max-runs"
                )
                assert '"--strategy"' not in src_str, (
                    f"{nb_path} cell [{cid}]: Full-9 cell must not use --strategy"
                )
                assert '"--auto-resume-hf"' not in src_str, (
                    f"{nb_path} cell [{cid}]: Full-9 cell must not use --auto-resume-hf"
                )
                assert '"--new-experiment"' in src_str, f"{nb_path} cell [{cid}]: missing --new-experiment"
                assert '"--hf-sync"' in src_str, f"{nb_path} cell [{cid}]: missing --hf-sync"
                tree = ast.parse(src_str)
                exec_assign = next(
                    node
                    for node in tree.body
                    if isinstance(node, ast.Assign)
                    and any(
                        isinstance(t, ast.Name) and t.id == "exec_cmd"
                        for t in node.targets
                    )
                )
                assert isinstance(exec_assign.value, ast.List)

                def _token(el: ast.AST) -> str:
                    if isinstance(el, ast.Constant) and isinstance(el.value, str):
                        return f'"{el.value}"'
                    return ast.unparse(el)

                actual_tokens = [_token(el) for el in exec_assign.value.elts]
                frozen_tokens = [
                    "sys.executable",
                    '"-u"',
                    "str(SCRIPT_PATH)",
                    '"--backend"',
                    '"kaggle-qwen"',
                    '"--profile"',
                    '"scientific-smoke-v2"',
                    '"--qwen-quantization"',
                    "QWEN_QUANTIZATION",
                    '"--max-attempts"',
                    '"3"',
                    '"--protocol-version"',
                    '"1.0"',
                    '"--max-completion-tokens-per-call"',
                    '"1024"',
                    '"--max-total-workflow-tokens"',
                    '"0"',
                    '"--timeout"',
                    '"600"',
                    '"--hf-repo-id"',
                    "HF_RESULTS_REPO_ID",
                    '"--source-commit"',
                    "SOURCE_COMMIT",
                    '"--deployed-build-id"',
                    "DEPLOYED_BUILD_ID",
                    '"--data-dir"',
                    "str(DATA_DIR)",
                    '"--model-path"',
                    "MODEL_PATH",
                    '"--output-dir"',
                    "str(FULL9_OUTPUT_DIR)",
                    '"--hf-sync"',
                    '"--new-experiment"',
                ]
                assert actual_tokens == frozen_tokens, (
                    f"{nb_path} cell [{cid}]: Full-9 command drift from the frozen form:\n"
                    f"expected={frozen_tokens}\nactual={actual_tokens}"
                )
            parsed.append((nb_path, nb))

        # After bundle build: canonical and generated notebooks are code-cell identical.
        if len(parsed) == 2:
            (_p0, nb1), (_p1, nb2) = parsed
            assert nb1["nbformat"] == nb2["nbformat"], "nbformat mismatch"
            assert nb1["nbformat_minor"] == nb2["nbformat_minor"], "nbformat_minor mismatch"
            cells1 = [c for c in nb1["cells"] if c["cell_type"] == "code"]
            cells2 = [c for c in nb2["cells"] if c["cell_type"] == "code"]
            assert len(cells1) == len(cells2), f"code cell count mismatch: {len(cells1)} vs {len(cells2)}"
            for c1, c2 in zip(cells1, cells2, strict=True):
                s1 = c1["source"] if isinstance(c1["source"], str) else "".join(c1["source"])
                s2 = c2["source"] if isinstance(c2["source"], str) else "".join(c2["source"])
                assert s1 == s2, f"code cell [{c1.get('id','')}] source mismatch between notebooks"

    @pytest.mark.parametrize(
        "notebook_path",
        [
            PROJECT_DIR / "notebooks" / "seven_arm_benchmark.ipynb",
            PROJECT_DIR / "kaggle_upload" / "notebooks" / "seven_arm_benchmark.ipynb",
        ],
    )
    def test_all_deployed_notebook_code_cells_compile(self, notebook_path: Path) -> None:
        """Every code cell in each deployed notebook must compile as Python."""
        import json

        assert notebook_path.is_file(), f"notebook not found: {notebook_path}"
        with open(notebook_path, encoding="utf-8") as f:
            nb = json.load(f)
        for idx, cell in enumerate(nb["cells"]):
            if cell.get("cell_type") != "code":
                continue
            cell_id = cell.get("id", "<no-id>")
            source = "".join(cell.get("source", []))
            try:
                compile(source, f"{notebook_path}:{cell_id}", "exec")
            except SyntaxError as exc:
                raise AssertionError(
                    f"{notebook_path}: code cell index {idx} id '{cell_id}' failed to compile: {exc}"
                ) from exc

    def test_notebook_runtime_lock_uses_distribution_and_import_names(self) -> None:
        """DRF's distribution is djangorestframework; its import is rest_framework."""
        import json

        nb_path = PROJECT_DIR / "notebooks" / "seven_arm_benchmark.ipynb"
        with open(nb_path, encoding="utf-8") as f:
            nb = json.load(f)
        cells_by_id = {c.get("id"): c for c in nb["cells"]}
        source = "".join(cells_by_id["install-lock-cell"]["source"])
        assert '("djangorestframework", "rest_framework", "3.17.1")' in source
        assert "importlib.import_module(module_name)" in source
        assert "importlib.metadata.version(distribution)" in source
        assert "sys.version_info[:2] not in ((3, 11), (3, 12))" in source
        assert '"python_version": PYTHON_RUNTIME' in source
        assert '__import__("djangorestframework")' not in source

    def test_notebook_source_commit_matches_deployed_runtime_tree(self) -> None:
        """The pinned source commit must contain the exact runtime files bundled for Kaggle."""
        import json
        import subprocess

        nb_path = PROJECT_DIR / "notebooks" / "seven_arm_benchmark.ipynb"
        with open(nb_path, encoding="utf-8") as f:
            nb = json.load(f)
        setup = "".join(
            next(c for c in nb["cells"] if c.get("id") == "setup-cell")["source"]
        )
        source_commit = setup.split('SOURCE_COMMIT = "')[1].split('"')[0]
        build_id = setup.split('DEPLOYED_BUILD_ID = "')[1].split('"')[0]
        assert len(source_commit) == 40
        assert build_id == source_commit[:7]

        runtime_files = (
            "seven_arm_benchmark.py",
            "pyproject.toml",
            "requirements-smoke-kaggle.lock",
            "src/benchmark/core/models.py",
            "src/benchmark/execution/preflight.py",
            "src/benchmark/execution/regeneration.py",
            "src/benchmark/execution/runner.py",
            "src/benchmark/llm/kaggle_qwen_backend.py",
            "src/benchmark/scenarios/models.py",
            "src/benchmark/strategies/iterative_agent.py",
        )
        for relative in runtime_files:
            result = subprocess.run(
                ["git", "show", f"{source_commit}:{relative}"],
                cwd=PROJECT_DIR,
                capture_output=True,
                check=False,
            )
            assert result.returncode == 0, (
                f"Notebook SOURCE_COMMIT does not contain {relative}: "
                f"{result.stderr.decode(errors='replace')}"
            )
            committed = result.stdout.decode("utf-8").replace("\r\n", "\n")
            current = (PROJECT_DIR / relative).read_text(encoding="utf-8").replace("\r\n", "\n")
            assert committed == current, (
                f"Notebook SOURCE_COMMIT {source_commit} is stale for {relative}"
            )

    def test_notebook_live_run_helpers_present(self) -> None:
        """KAGGLE-SMOKE-V2 section 12: live executor + actionable errors."""
        import json

        nb_path = PROJECT_DIR / "notebooks" / "seven_arm_benchmark.ipynb"
        with open(nb_path, encoding="utf-8") as f:
            nb = json.load(f)
        cells_by_id = {c.get("id"): c for c in nb["cells"]}

        setup_src = "".join(cells_by_id["setup-cell"]["source"])
        for helper in (
            "_run_benchmark_live",
            "_load_smoke_evidence",
            "_display_smoke_dashboard",
            "_raise_actionable_smoke_error",
            "_verify_full9_evidence",
            "_export_full9_evidence",
            "_label_bar_containers",
            "ScientificSmokeExecutionError",
        ):
            assert f"def {helper}" in setup_src or helper in setup_src, (
                f"setup-cell missing helper: {helper}"
            )

        for env in (
            '"PYTHONUNBUFFERED"',
            "expandable_segments:True",
            '"TOKENIZERS_PARALLELISM"',
        ):
            assert env in setup_src, f"setup-cell missing env: {env}"

        exec_src = "".join(cells_by_id["full9-execution-cell"]["source"])
        verify_src = "".join(cells_by_id["full9-verification-cell"]["source"])
        export_src = "".join(cells_by_id["export-evidence-cell"]["source"])
        assert "_run_benchmark_live(" in exec_src, "full9-execution-cell missing live runner"
        assert "FULL9_OUTPUT_DIR" in exec_src, "full9-execution-cell missing output dir"
        assert "_verify_full9_evidence(FULL9_OUTPUT_DIR)" in verify_src, (
            "full9-verification-cell missing Full-9 guardrail call"
        )
        assert "_export_full9_evidence(FULL9_OUTPUT_DIR)" in export_src, (
            "export-evidence-cell missing export call"
        )
        assert "kaggle_console.log" in setup_src, "live log file missing"


    def test_notebook_accepts_scientific_failure_and_blocks_engineering_failure(
        self, tmp_path: Path
    ) -> None:
        """Execute the deployed Full-9 evidence gate, not merely text-search it."""
        import ast
        import json

        nb_path = PROJECT_DIR / "notebooks" / "seven_arm_benchmark.ipynb"
        with open(nb_path, encoding="utf-8") as f:
            nb = json.load(f)
        setup_src = "".join(
            next(c for c in nb["cells"] if c.get("id") == "setup-cell")["source"]
        )
        tree = ast.parse(setup_src)
        wanted_assignments = {
            "SCIENTIFIC_FAILURE_KINDS",
            "ENGINEERING_FAILURE_KINDS",
            "EVIDENCE_FILES",
            "SOURCE_COMMIT",
            "DEPLOYED_BUILD_ID",
            "EXPECTED_MODEL_IDENTITY",
            "EXPECTED_PROFILE",
            "EXPECTED_PROTOCOL_VERSION",
            "FULL9_EXPECTED_MATRIX",
        }
        wanted_defs = {
            "ScientificSmokeExecutionError",
            "_load_smoke_evidence",
            "_terminal_record_outcome",
            "_verify_full9_evidence",
        }
        selected = []
        for node in tree.body:
            if isinstance(node, ast.Assign):
                names = {t.id for t in node.targets if isinstance(t, ast.Name)}
                if names & wanted_assignments:
                    selected.append(node)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in wanted_defs:
                selected.append(node)
        module = ast.Module(body=selected, type_ignores=[])
        ns: dict[str, Any] = {"Path": Path, "_json": json}
        exec(compile(module, "deployed-notebook-evidence-gates", "exec"), ns)

        source_commit = ns["SOURCE_COMMIT"]
        build_id = ns["DEPLOYED_BUILD_ID"]
        model_identity = ns["EXPECTED_MODEL_IDENTITY"]
        profile = ns["EXPECTED_PROFILE"]
        protocol = ns["EXPECTED_PROTOCOL_VERSION"]
        scenarios = ("todo-smoke-001", "todo-smoke-002", "todo-smoke-003")
        strategies = ("monolithic", "selective", "iterative_repository_agent")

        def record(index: int, status: str = "succeeded", kind: str | None = None) -> dict[str, Any]:
            scenario = scenarios[index % 3]
            strategy = strategies[(index // 3) % 3]
            return {
                "run_id": f"run-{index}",
                "scenario_id": scenario,
                "strategy_id": strategy,
                "strategy_name": strategy,
                "status": status,
                "source_commit": source_commit,
                "repetition": 1,
                "profile": profile,
                "failure_classification": kind or "",
                "failure_details": (
                    [{"kind": kind, "stage": "migration_generation", "message": "m"}]
                    if kind
                    else []
                ),
            }

        def write_full9_matrix(records: list[dict[str, Any]]) -> None:
            (tmp_path / "experiment_id.txt").write_text("exp-full9-test\n", encoding="utf-8")
            (tmp_path / "source_identity.json").write_text(
                json.dumps({
                    "source_commit": source_commit,
                    "deployed_build_id": build_id,
                    "model_identity": model_identity,
                    "profile": profile,
                    "protocol_version": protocol,
                }),
                encoding="utf-8",
            )
            (tmp_path / "run_records.jsonl").write_text(
                "".join(json.dumps(r) + "\n" for r in records),
                encoding="utf-8",
            )
            (tmp_path / "checkpoint.json").write_text(
                json.dumps({
                    "source_commit": source_commit,
                    "deployed_build_id": build_id,
                    "model_identity": model_identity,
                    "profile": profile,
                    "protocol_version": protocol,
                    "completion_status": "completed",
                    "total_planned": 9,
                    "total_completed": 9,
                    "pending_run_ids": [],
                }),
                encoding="utf-8",
            )

        base = [record(i) for i in range(9)]

        scientific_failure = list(base)
        scientific_failure[0]["status"] = "failed"
        scientific_failure[0]["failure_classification"] = "model_output"
        scientific_failure[0]["failure_details"] = [
            {"kind": "build", "stage": "migration_generation", "message": "bad"}
        ]
        write_full9_matrix(scientific_failure)
        assert ns["_terminal_record_outcome"](scientific_failure[0]) == "scientific_failure"
        ns["_verify_full9_evidence"](str(tmp_path))

        engineering_failure = list(base)
        engineering_failure[0]["status"] = "failed"
        engineering_failure[0]["failure_classification"] = "infrastructure_nonrepairable"
        engineering_failure[0]["failure_details"] = [
            {"kind": "infrastructure_nonrepairable", "stage": "migration_generation", "message": "m"}
        ]
        write_full9_matrix(engineering_failure)
        assert ns["_terminal_record_outcome"](engineering_failure[0]) == "engineering_blocker"
        with pytest.raises(ns["ScientificSmokeExecutionError"]) as exc_info:
            ns["_verify_full9_evidence"](str(tmp_path))
        assert "engineering blocker record: True" in str(exc_info.value)

        timed_out = list(base)
        timed_out[0]["status"] = "timed_out"
        write_full9_matrix(timed_out)
        with pytest.raises(ns["ScientificSmokeExecutionError"]):
            ns["_verify_full9_evidence"](str(tmp_path))

    def test_notebook_preflight_streams_with_deployed_pythonpath(self) -> None:
        """Preflight must not buffer output or depend on the parent kernel's sys.path."""
        import json

        nb_path = PROJECT_DIR / "notebooks" / "seven_arm_benchmark.ipynb"
        with open(nb_path, encoding="utf-8") as f:
            nb = json.load(f)
        cells_by_id = {c.get("id"): c for c in nb["cells"]}
        preflight_src = "".join(cells_by_id["preflight-cell"]["source"])
        setup_src = "".join(cells_by_id["setup-cell"]["source"])

        assert "subprocess.Popen(" in preflight_src
        assert "stdout=subprocess.PIPE" in preflight_src
        assert "stderr=subprocess.STDOUT" in preflight_src
        assert "bufsize=1" in preflight_src
        assert 'preflight_env["PYTHONPATH"]' in preflight_src
        assert 'preflight_env["PYTHONUNBUFFERED"] = "1"' in preflight_src
        assert 'preflight_env["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"' in preflight_src
        assert "kaggle_preflight_console.log" in setup_src
        assert 'KAGGLE_DEPLOYMENT_PATHS["preflight_console_name"]' in preflight_src
        assert 'KAGGLE_DEPLOYMENT_PATHS["preflight_output_dir"]' in preflight_src
        assert "capture_output=True" not in preflight_src
        assert 'sub_env["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"' in setup_src
        assert "PYTORCH_CUDA_ALLOC_CONF" not in setup_src

    def test_notebook_sync_display_uses_current_schema(self) -> None:
        """The export helper must read the current remote_sync schema keys."""
        import json

        nb_path = PROJECT_DIR / "notebooks" / "seven_arm_benchmark.ipynb"
        with open(nb_path, encoding="utf-8") as f:
            nb = json.load(f)
        cells_by_id = {c.get("id"): c for c in nb["cells"]}
        setup_src = "".join(cells_by_id["setup-cell"]["source"])
        export_src = "".join(cells_by_id["export-evidence-cell"]["source"])

        assert "_export_full9_evidence(FULL9_OUTPUT_DIR)" in export_src, (
            "export-evidence-cell missing the Full-9 export call"
        )
        for key in (
            'sync.get("last_sync"',
            'sync.get("timestamp"',
            'sync.get("remote_path"',
            'sync.get("details"',
        ):
            assert key in setup_src, f"setup-cell export helper missing current key: {key}"

        for obsolete in (
            'sync.get("last_sync_time"',
            'sync.get("experiments_synced"',
            'sync.get("runs_uploaded"',
        ):
            assert obsolete not in setup_src, (
                f"setup-cell export helper still uses obsolete key: {obsolete}"
            )


class _FakeRunRecord:
    def __init__(self, status: str, duration_seconds: float) -> None:
        self.status = status
        self.duration_seconds = duration_seconds


class _FakeRecordStore:
    def __init__(self, records: list[_FakeRunRecord]) -> None:
        self._records = records

    def load_all(self) -> list[_FakeRunRecord]:
        return self._records


class TestRunProgressAndEta:
    """KAGGLE-SMOKE-V2 section 10: progress line and cross-session ETA."""

    @staticmethod
    def _format(completed: int, total: int, eta: str = "estimating") -> str:
        from seven_arm_benchmark import _render_progress_line

        return _render_progress_line(
            completed=completed,
            total=total,
            current_label="scn-001/monolithic",
            stage="succeeded",
            elapsed_seconds=63,
            eta=eta,
        )

    def test_zero_completed_line(self) -> None:
        line = self._format(0, 9)
        assert line.startswith("[--------------------] 0/9 | current=scn-001/monolithic | stage=succeeded |")
        assert "elapsed=00:01:03" in line
        assert "ETA=estimating" in line

    def test_partial_line_three_of_nine(self) -> None:
        line = self._format(3, 9)
        assert line.startswith("[######--------------] 3/9 | current=scn-001/monolithic |")
        assert "ETA=estimating" in line

    def test_completed_plan_formats_full_bar(self) -> None:
        line = self._format(9, 9, eta="00:00:00")
        assert line.startswith("[####################] 9/9 | current=scn-001/monolithic |")
        assert "ETA=00:00:00" in line

    def test_eta_zero_completed_is_estimating(self) -> None:
        from seven_arm_benchmark import _estimate_run_eta

        store = _FakeRecordStore([])
        assert _estimate_run_eta(store, 9) == "estimating"

    def test_eta_one_completed_terminal_run(self) -> None:
        from seven_arm_benchmark import _estimate_run_eta

        store = _FakeRecordStore([_FakeRunRecord("succeeded", 600.0)])
        assert _estimate_run_eta(store, 3) == "00:30:00"

    def test_eta_uses_cross_session_terminal_records_only(self) -> None:
        from seven_arm_benchmark import _estimate_run_eta

        records = [
            _FakeRunRecord("succeeded", 500.0),  # session 1
            _FakeRunRecord("failed", 700.0),     # session 2
            _FakeRunRecord("pending", 9999.0),   # never counted
        ]
        store = _FakeRecordStore(records)
        assert _estimate_run_eta(store, 4) == "00:40:00"

    def test_eta_no_remaining_runs_is_zero(self) -> None:
        from seven_arm_benchmark import _estimate_run_eta

        store = _FakeRecordStore([_FakeRunRecord("succeeded", 600.0)])
        assert _estimate_run_eta(store, 0) == "00:00:00"
