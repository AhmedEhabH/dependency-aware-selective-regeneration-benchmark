from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_DIR / "seven_arm_benchmark.py"
BENCHMARK_DATA = PROJECT_DIR / "benchmark_data"

assert SCRIPT.is_file(), f"Script not found: {SCRIPT}"
assert BENCHMARK_DATA.is_dir(), f"Benchmark data not found: {BENCHMARK_DATA}"


def _run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=cwd or PROJECT_DIR,
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
