from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

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


class TestModelIdentity:
    """KAGGLE-SMOKE-V2: a non-dry Kaggle backend can never be dry-run:mock."""

    @staticmethod
    def _identity(model_path: str | None = None, backend: str | None = None, openrouter: str = "") -> str:
        from seven_arm_benchmark import _get_model_identity

        return _get_model_identity(
            model_path=model_path,
            backend_name=backend,
            openrouter_model=openrouter,
        )

    def test_kaggle_qwen_with_model_path_is_qwen_directory(self) -> None:
        identity = self._identity(model_path="/kaggle/input/qwen2.5-coder-7b", backend="kaggle-qwen")
        assert identity == "qwen:qwen2.5-coder-7b"

    def test_kaggle_qwen_without_model_path_never_dry_run_mock(self) -> None:
        identity = self._identity(backend="kaggle-qwen")
        assert identity != "dry-run:mock"
        assert identity.startswith("qwen:")

    def test_mock_dry_run_identity_remains_dry_run_mock(self) -> None:
        assert self._identity(backend="mock") == "dry-run:mock"
        assert self._identity(backend=None) == "dry-run:mock"

    def test_openrouter_identity(self) -> None:
        identity = self._identity(backend="openrouter", openrouter="nvidia/nemotron-3-super-120b-a12b:free")
        assert identity == "openrouter:nvidia/nemotron-3-super-120b-a12b:free"


class TestSessionExitCode:
    """KAGGLE-SMOKE-V2: one-run cell fails immediately on a failed scientific run."""

    @staticmethod
    def _decide(**kwargs: Any) -> int:
        from seven_arm_benchmark import _decide_session_exit_code

        defaults: dict[str, Any] = {
            "max_runs": 1,
            "all_runs_completed": False,
            "session_created_run_count": 1,
            "last_run_status": "succeeded",
            "hf_uploader_configured": False,
            "hf_sync_ok": True,
            "total_failed": 0,
        }
        defaults.update(kwargs)
        return _decide_session_exit_code(**defaults)

    def test_one_succeeded_cell_returns_zero(self) -> None:
        assert self._decide(last_run_status="succeeded") == 0

    def test_one_failed_cell_returns_nonzero(self) -> None:
        assert self._decide(last_run_status="failed") == 1
        assert self._decide(last_run_status="timed_out") == 1
        assert self._decide(last_run_status="cancelled") == 1

    def test_nine_terminal_failures_returns_nonzero(self) -> None:
        assert self._decide(
            all_runs_completed=True,
            total_failed=9,
        ) == 1

    def test_complete_plan_with_all_success_returns_zero(self) -> None:
        assert self._decide(all_runs_completed=True, total_failed=0) == 0

    def test_hf_sync_failure_returns_nonzero(self) -> None:
        assert self._decide(
            hf_uploader_configured=True,
            hf_sync_ok=False,
        ) == 1

    def test_incomplete_without_max_runs_returns_zero(self) -> None:
        assert self._decide(max_runs=0, last_run_status="failed") == 0


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
            assert "scientific_smoke_v2" in setup_src, nb_path
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

            assert len(exec_cmds) >= 2, f"{nb_path}: expected >=2 benchmark cells, got {len(exec_cmds)}"

            for cid, src_str in exec_cmds:
                required = [
                    ('"--backend", "kaggle-qwen"', "backend kaggle-qwen"),
                    ('"--profile", "scientific-smoke-v2"', "profile scientific-smoke-v2"),
                    ('"--protocol-version", "1.0"', "protocol-version 1.0"),
                    ('"--max-attempts", "3"', "max-attempts 3"),
                    ('"--max-completion-tokens-per-call", "4096"', "max-completion-tokens-per-call 4096"),
                    ('"--max-total-workflow-tokens", "0"', "max-total-workflow-tokens 0"),
                    ('"--timeout", "300"', "timeout 300"),
                ]
                for needle, label in required:
                    assert needle in src_str, f"{nb_path} cell [{cid}]: missing {label}"
                assert '"--max-tokens"' not in src_str, f"{nb_path} cell [{cid}]: still has --max-tokens"
                assert '"scientific-smoke-v1"' not in src_str, (
                    f"{nb_path} cell [{cid}]: still has --profile scientific-smoke-v1"
                )
                assert '"smoke"' not in src_str.replace("scientific-smoke-v2", ""), (
                    f"{nb_path} cell [{cid}]: still has old --profile smoke"
                )
                assert '"pilot"' not in src_str, f"{nb_path} cell [{cid}]: has pilot profile"
                assert '"research"' not in src_str, f"{nb_path} cell [{cid}]: has research profile"
                if cid == "exec-cell":
                    assert '"--max-runs", "1"' in src_str, (
                        f"{nb_path} cell [{cid}]: resume cell missing --max-runs 1"
                    )
                if cid == "continuous-smoke-cell":
                    assert '"--max-runs"' not in src_str, (
                        f"{nb_path} cell [{cid}]: continuous cell should not have --max-runs"
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

    def test_notebook_sync_display_uses_current_schema(self) -> None:
        """The inspection cell must read the current remote_sync schema keys."""
        import json

        nb_path = PROJECT_DIR / "notebooks" / "seven_arm_benchmark.ipynb"
        with open(nb_path, encoding="utf-8") as f:
            nb = json.load(f)
        cells_by_id = {c.get("id"): c for c in nb["cells"]}
        progress_src = "".join(cells_by_id["progress-cell"]["source"])

        for key in (
            'sync.get("last_sync"',
            'sync.get("timestamp"',
            'sync.get("remote_path"',
            'sync.get("details"',
        ):
            assert key in progress_src, f"inspection cell missing current key: {key}"

        for obsolete in (
            'sync.get("last_sync_time"',
            'sync.get("experiments_synced"',
            'sync.get("runs_uploaded"',
        ):
            assert obsolete not in progress_src, f"inspection cell still uses obsolete key: {obsolete}"
