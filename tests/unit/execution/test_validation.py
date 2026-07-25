import sys
from pathlib import Path

from benchmark.execution.validation import FunctionalValidationResult, FunctionalValidator


class TestFunctionalValidator:
    def test_validation_pass(self, tmp_path: Path) -> None:
        validator = FunctionalValidator()
        result = validator.validate(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
        )
        assert result.passed is True
        assert result.exit_code == 0
        assert result.duration_seconds >= 0

    def test_validation_fail(self, tmp_path: Path) -> None:
        validator = FunctionalValidator()
        result = validator.validate(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(1)"],
        )
        assert result.passed is False
        assert result.exit_code == 1

    def test_timeout_handling(self, tmp_path: Path) -> None:
        validator = FunctionalValidator()
        result = validator.validate(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "import time; time.sleep(10)"],
            timeout=1,
        )
        assert result.passed is False
        assert "timed out" in result.stderr.lower()

    def test_command_not_found(self, tmp_path: Path) -> None:
        validator = FunctionalValidator()
        result = validator.validate(
            workspace_root=tmp_path,
            command=["nonexistent_command_xyz"],
        )
        assert result.passed is False
        assert "not found" in result.stderr

    def test_stdout_captured(self, tmp_path: Path) -> None:
        validator = FunctionalValidator()
        result = validator.validate(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "print('hello world')"],
        )
        assert result.passed is True
        assert "hello world" in result.stdout

    def test_stderr_captured(self, tmp_path: Path) -> None:
        validator = FunctionalValidator()
        result = validator.validate(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "import sys; sys.stderr.write('error msg')"],
        )
        assert "error msg" in result.stderr

    def test_result_is_frozen_dataclass(self, tmp_path: Path) -> None:
        validator = FunctionalValidator()
        result = validator.validate(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
        )
        assert isinstance(result, FunctionalValidationResult)
        assert result.passed is True

    def test_validation_passed_is_true_on_success(self, tmp_path: Path) -> None:
        validator = FunctionalValidator()
        result = validator.validate(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
        )
        assert result.passed is True

    def test_validation_passed_is_false_on_failure(self, tmp_path: Path) -> None:
        validator = FunctionalValidator()
        result = validator.validate(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(1)"],
        )
        assert result.passed is False
