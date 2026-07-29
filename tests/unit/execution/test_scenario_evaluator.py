from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from benchmark.execution.scenario_evaluator import (
    _EvaluatorCommandOutcome,
    _execute_evaluator_subprocess,
    _load_trusted_evaluator_asset,
    _parse_evaluator_payload,
    _ParsedEvaluatorPayload,
    _TrustedEvaluatorAsset,
    _validate_evaluator_request,
    _ValidatedEvaluatorRequest,
    run_scenario_evaluator,
)


def _make_cpr_ws_asset(tmp_path, asset_content=b"print('ok')", asset_name="checks.py"):
    cpr = tmp_path / "project"
    cpr.mkdir()
    (cpr / "tests").mkdir()
    (cpr / "tests" / "evaluator_assets").mkdir()
    asset = cpr / "tests" / "evaluator_assets" / asset_name
    asset.write_bytes(asset_content)
    ws = tmp_path / "workspace"
    ws.mkdir()
    return cpr, ws, asset


def _make_request(tmp_path):
    cpr, ws, _ = _make_cpr_ws_asset(tmp_path)
    result = _validate_evaluator_request(
        str(cpr), "tests/evaluator_assets/checks.py", str(ws),
        python_executable=sys.executable, timeout=60,
    )
    assert isinstance(result, _ValidatedEvaluatorRequest)
    return result


class TestEvaluatorInputValidation:
    def test_valid_paths(self, tmp_path):
        cpr, ws, asset = _make_cpr_ws_asset(tmp_path)
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws),
            python_executable="python", timeout=60,
        )
        assert isinstance(result, _ValidatedEvaluatorRequest)
        assert result.canonical_project_root == cpr.resolve()
        assert result.generated_workspace == ws.resolve()

    def test_missing_canonical_root(self, tmp_path):
        cpr = tmp_path / "nonexistent"
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_canonical_root_file(self, tmp_path):
        cpr = tmp_path / "afile"
        cpr.write_text("")
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_missing_evaluator_root(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_evaluator_root_symlink(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        real_assets = tmp_path / "real_assets"
        real_assets.mkdir()
        (cpr / "tests").mkdir()
        link = cpr / "tests" / "evaluator_assets"
        try:
            link.symlink_to(real_assets)
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation not supported")
        ws = tmp_path / "workspace"
        ws.mkdir()
        asset = real_assets / "checks.py"
        asset.write_text("")
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_empty_asset(self, tmp_path):
        cpr, ws, _ = _make_cpr_ws_asset(tmp_path)
        result = _validate_evaluator_request(
            str(cpr), "", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_whitespace_asset(self, tmp_path):
        cpr, ws, _ = _make_cpr_ws_asset(tmp_path)
        result = _validate_evaluator_request(
            str(cpr), "   ", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_asset_with_nul(self, tmp_path):
        cpr, ws, _ = _make_cpr_ws_asset(tmp_path)
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks\x00.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_asset_with_backslash(self, tmp_path):
        cpr, ws, _ = _make_cpr_ws_asset(tmp_path)
        result = _validate_evaluator_request(
            str(cpr), "tests\\evaluator_assets\\checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_traversal(self, tmp_path):
        cpr, ws, _ = _make_cpr_ws_asset(tmp_path)
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/../checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_absolute_asset(self, tmp_path):
        cpr, ws, _ = _make_cpr_ws_asset(tmp_path)
        result = _validate_evaluator_request(
            str(cpr), "/etc/passwd", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_wrong_extension(self, tmp_path):
        cpr, ws, _ = _make_cpr_ws_asset(tmp_path)
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.txt", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_missing_asset_file(self, tmp_path):
        cpr, ws, _ = _make_cpr_ws_asset(tmp_path)
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/nonexistent.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_asset_symlink(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        real_asset = tmp_path / "real_checks.py"
        real_asset.write_text("")
        link = cpr / "tests" / "evaluator_assets" / "checks.py"
        try:
            link.symlink_to(real_asset)
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation not supported")
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_asset_internal_symlink_fails_closed(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        real_asset = tmp_path / "real_checks.py"
        real_asset.write_text("")
        link = cpr / "tests" / "evaluator_assets" / "checks.py"
        try:
            link.symlink_to(real_asset)
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation not supported")
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)
        result2 = run_scenario_evaluator(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws),
            python_executable="python", timeout=60,
        )
        assert not result2.passed
        assert result2.exit_code == -1
        assert result2.error

    def test_asset_parent_symlink_component_fails_closed(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        real_dir = tmp_path / "real_subdir"
        real_dir.mkdir()
        link = cpr / "tests" / "sub"
        try:
            link.symlink_to(real_dir)
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation not supported")
        (real_dir / "evaluator_assets").mkdir()
        asset = real_dir / "evaluator_assets" / "checks.py"
        asset.write_text("")
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_workspace_evaluator_root_directory_fails_closed(self, tmp_path):
        cpr, ws, asset = _make_cpr_ws_asset(tmp_path)
        leaker = ws / "tests" / "evaluator_assets"
        leaker.mkdir(parents=True)
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_workspace_evaluator_root_file_fails_closed(self, tmp_path):
        cpr, ws, asset = _make_cpr_ws_asset(tmp_path)
        leaker = ws / "tests" / "evaluator_assets"
        leaker.parent.mkdir(parents=True, exist_ok=True)
        leaker.write_text("leak")
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_workspace_evaluator_root_symlink_fails_closed(self, tmp_path):
        cpr, ws, asset = _make_cpr_ws_asset(tmp_path)
        leaker = ws / "tests" / "evaluator_assets"
        leaker.parent.mkdir(parents=True, exist_ok=True)
        real = tmp_path / "real_leak"
        real.mkdir()
        try:
            leaker.symlink_to(real)
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation not supported")
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)
        result2 = run_scenario_evaluator(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws),
            python_executable="python", timeout=60,
        )
        assert not result2.passed
        assert result2.exit_code == -1
        assert result2.error

    def test_sibling_prefix_is_not_treated_as_containment(self, tmp_path):
        cpr = tmp_path / "project_abc"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("")
        ws = tmp_path / "project_abcdef"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, _ValidatedEvaluatorRequest)

    def test_workspace_missing(self, tmp_path):
        cpr, _, _ = _make_cpr_ws_asset(tmp_path)
        ws = tmp_path / "nonexistent"
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_workspace_file(self, tmp_path):
        cpr, _, _ = _make_cpr_ws_asset(tmp_path)
        ws = tmp_path / "afile"
        ws.write_text("")
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_workspace_equals_canonical_root(self, tmp_path):
        cpr, _, _ = _make_cpr_ws_asset(tmp_path)
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(cpr), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_workspace_nested_under_canonical_root(self, tmp_path):
        cpr, _, _ = _make_cpr_ws_asset(tmp_path)
        ws = cpr / "sub"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_canonical_root_nested_under_workspace(self, tmp_path):
        ws = tmp_path / "workspace"
        ws.mkdir()
        cpr = ws / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("")
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_empty_python_executable(self, tmp_path):
        cpr, ws, _ = _make_cpr_ws_asset(tmp_path)
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="", timeout=60
        )
        assert isinstance(result, str)

    def test_nul_executable(self, tmp_path):
        cpr, ws, _ = _make_cpr_ws_asset(tmp_path)
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="py\x00thon", timeout=60
        )
        assert isinstance(result, str)

    def test_invalid_timeout_type(self, tmp_path):
        cpr, ws, _ = _make_cpr_ws_asset(tmp_path)
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60.5
        )
        assert isinstance(result, str)


class TestTrustedEvaluatorAsset:
    def test_valid_content_and_sha256(self, tmp_path):
        request = _make_request(tmp_path)
        content = request.evaluator_asset_path.read_bytes()
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, _TrustedEvaluatorAsset)
        assert trusted.content == content
        expected_sha = hashlib.sha256(content).hexdigest()
        assert trusted.sha256 == expected_sha

    def test_read_failure(self, tmp_path):
        request = _make_request(tmp_path)
        request.evaluator_asset_path.unlink()
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, str)


class FakeCompletedProcess:
    def __init__(self, stdout, returncode=0):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


class TestEvaluatorSubprocess:
    def test_exact_command_and_cwd(self, tmp_path):
        request = _make_request(tmp_path)
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, _TrustedEvaluatorAsset)
        captured = {}

        def fake_run(command, **kwargs):
            captured["command"] = command
            captured["cwd"] = kwargs.get("cwd")
            captured["capture_output"] = kwargs.get("capture_output")
            captured["text"] = kwargs.get("text")
            captured["timeout"] = kwargs.get("timeout")
            captured["shell"] = kwargs.get("shell")
            captured["env"] = kwargs.get("env")
            return FakeCompletedProcess(
                json.dumps({"passed": True, "checks": ["ok"], "error": ""}),
                returncode=0,
            )

        with patch("subprocess.run", fake_run):
            outcome = _execute_evaluator_subprocess(request, trusted)

        assert outcome.succeeded
        assert captured["command"][0] == request.python_executable
        assert captured["command"][2] == str(request.generated_workspace)
        assert captured["capture_output"] is True
        assert captured["text"] is True
        assert captured["timeout"] == request.timeout
        assert "shell" not in captured or captured["shell"] is None
        pythonpath = captured["env"]["PYTHONPATH"].split(os.pathsep)
        assert pythonpath[0] == str(request.generated_workspace)
        assert captured["env"]["PYTHONDONTWRITEBYTECODE"] == "1"

    def test_timeout_with_string_output(self, tmp_path):
        request = _make_request(tmp_path)
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, _TrustedEvaluatorAsset)

        def fake_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="test", timeout=60, output="some stdout", stderr="some stderr")

        with patch("subprocess.run", fake_run):
            outcome = _execute_evaluator_subprocess(request, trusted)
        assert not outcome.succeeded
        assert outcome.exit_code == -1
        assert "timed out" in outcome.stderr.lower()

    def test_timeout_with_byte_output(self, tmp_path):
        request = _make_request(tmp_path)
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, _TrustedEvaluatorAsset)

        def fake_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="test", timeout=60, output=b"byte stdout", stderr=b"byte stderr")

        with patch("subprocess.run", fake_run):
            outcome = _execute_evaluator_subprocess(request, trusted)
        assert not outcome.succeeded
        assert outcome.exit_code == -1

    def test_subprocess_value_error(self, tmp_path):
        request = _make_request(tmp_path)
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, _TrustedEvaluatorAsset)

        def fake_run(*args, **kwargs):
            raise ValueError("bad arg")

        with patch("subprocess.run", fake_run):
            outcome = _execute_evaluator_subprocess(request, trusted)
        assert not outcome.succeeded
        assert outcome.exit_code == -1
        assert "Invalid" in outcome.stderr

    def test_subprocess_os_error(self, tmp_path):
        request = _make_request(tmp_path)
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, _TrustedEvaluatorAsset)

        def fake_run(*args, **kwargs):
            raise OSError("disk full")

        with patch("subprocess.run", fake_run):
            outcome = _execute_evaluator_subprocess(request, trusted)
        assert not outcome.succeeded
        assert outcome.exit_code == -1
        assert "OS error" in outcome.stderr

    def test_subprocess_error(self, tmp_path):
        request = _make_request(tmp_path)
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, _TrustedEvaluatorAsset)

        def fake_run(*args, **kwargs):
            raise subprocess.SubprocessError("generic failure")

        with patch("subprocess.run", fake_run):
            outcome = _execute_evaluator_subprocess(request, trusted)
        assert not outcome.succeeded
        assert outcome.exit_code == -1
        assert "Subprocess error" in outcome.stderr

    def test_source_change_after_trust_does_not_change_copied_bytes(self, tmp_path):
        request = _make_request(tmp_path)
        original_content = request.evaluator_asset_path.read_bytes()
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, _TrustedEvaluatorAsset)
        assert trusted.content == original_content
        request.evaluator_asset_path.write_bytes(b"# modified after trust")
        assert trusted.content == original_content
        assert trusted.sha256 == hashlib.sha256(original_content).hexdigest()

    def test_copy_write_failure_returns_typed_outcome(self, tmp_path):
        request = _make_request(tmp_path)
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, _TrustedEvaluatorAsset)

        def fake_run(*args, **kwargs):
            return FakeCompletedProcess('{"passed": true, "checks": ["ok"], "error": ""}')

        with patch("subprocess.run", fake_run):
            outcome = _execute_evaluator_subprocess(request, trusted)
        assert isinstance(outcome, _EvaluatorCommandOutcome)

    def test_command_not_found(self, tmp_path):
        cpr, ws, asset = _make_cpr_ws_asset(tmp_path)
        request = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws),
            python_executable="nonexistent_python_xyz", timeout=60,
        )
        assert isinstance(request, _ValidatedEvaluatorRequest)
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, _TrustedEvaluatorAsset)
        outcome = _execute_evaluator_subprocess(request, trusted)
        assert not outcome.succeeded


class TestEvaluatorPayloadParsing:
    def _make_outcome(self, stdout: str, exit_code: int = 0) -> _EvaluatorCommandOutcome:
        return _EvaluatorCommandOutcome(succeeded=exit_code == 0, exit_code=exit_code, stdout=stdout, stderr="")

    def test_valid(self):
        payload = _parse_evaluator_payload(self._make_outcome('{"passed": true, "checks": ["a"], "error": ""}'))
        assert isinstance(payload, _ParsedEvaluatorPayload)
        assert payload.passed
        assert payload.checks == ("a",)
        assert payload.error == ""

    def test_whitespace_around_json(self):
        payload = _parse_evaluator_payload(self._make_outcome('  \n{"passed": true, "checks": ["a"], "error": ""}\n  '))
        assert isinstance(payload, _ParsedEvaluatorPayload)

    def test_extra_stdout_before(self):
        out = self._make_outcome('logging\n{"passed": true, "checks": ["a"], "error": ""}')
        assert isinstance(_parse_evaluator_payload(out), str)

    def test_extra_stdout_after(self):
        out = self._make_outcome('{"passed": true, "checks": ["a"], "error": ""}\ncleanup')
        assert isinstance(_parse_evaluator_payload(out), str)

    def test_malformed_json(self):
        payload = _parse_evaluator_payload(self._make_outcome("not json"))
        assert isinstance(payload, str)

    def test_non_object(self):
        payload = _parse_evaluator_payload(self._make_outcome('"string"'))
        assert isinstance(payload, str)

    def test_missing_keys(self):
        payload = _parse_evaluator_payload(self._make_outcome('{"passed": true}'))
        assert isinstance(payload, str)

    def test_unknown_keys(self):
        out = self._make_outcome('{"passed": true, "checks": [], "error": "", "extra": 1}')
        assert isinstance(_parse_evaluator_payload(out), str)

    def test_wrong_types(self):
        payload = _parse_evaluator_payload(self._make_outcome('{"passed": 1, "checks": [], "error": ""}'))
        assert isinstance(payload, str)

    def test_empty_check(self):
        payload = _parse_evaluator_payload(self._make_outcome('{"passed": true, "checks": [""], "error": ""}'))
        assert isinstance(payload, str)

    def test_duplicate_check(self):
        payload = _parse_evaluator_payload(self._make_outcome('{"passed": true, "checks": ["a", "a"], "error": ""}'))
        assert isinstance(payload, str)

    def test_contradictory_passed_error(self):
        out = self._make_outcome('{"passed": true, "checks": ["a"], "error": "something"}')
        assert isinstance(_parse_evaluator_payload(out), str)

    def test_passed_false_empty_error(self):
        payload = _parse_evaluator_payload(self._make_outcome('{"passed": false, "checks": ["a"], "error": ""}'))
        assert isinstance(payload, str)


class TestEvaluatorSuccessTruthTable:
    @pytest.mark.parametrize(
        "exit_code,payload_passed,payload_error,payload_checks,expected_passed",
        [
            (0, True, "", ["a"], True),
            (1, True, "", ["a"], False),
            (0, False, "err", ["a"], False),
            (0, True, "", [], False),
        ],
    )
    def test_truth_table(self, tmp_path, exit_code, payload_passed, payload_error, payload_checks, expected_passed):
        cpr, ws, _ = _make_cpr_ws_asset(tmp_path)
        json_payload = json.dumps({"passed": payload_passed, "checks": payload_checks, "error": payload_error})

        def fake_run(command, **kwargs):
            return FakeCompletedProcess(json_payload, returncode=exit_code)

        with patch("subprocess.run", fake_run):
            result = run_scenario_evaluator(
                str(cpr), "tests/evaluator_assets/checks.py", str(ws),
                python_executable=sys.executable, timeout=60,
            )
        if expected_passed:
            assert result.passed, f"Expected pass but got: {result.error}"
        else:
            assert not result.passed, "Expected failure but got pass"
            assert result.duration_seconds >= 0


class TestEvaluatorIsolation:
    def test_temp_outside_workspace(self, tmp_path):
        cpr, ws, asset = _make_cpr_ws_asset(tmp_path)
        captured_cwd = []

        def fake_run(command, **kwargs):
            captured_cwd.append(kwargs.get("cwd"))
            return FakeCompletedProcess(
                json.dumps({"passed": True, "checks": ["ok"], "error": ""}),
                returncode=0,
            )

        with patch("subprocess.run", fake_run):
            result = run_scenario_evaluator(
                str(cpr), "tests/evaluator_assets/checks.py", str(ws),
                python_executable=sys.executable, timeout=60,
            )
        assert result.passed
        assert captured_cwd
        cwd_path = Path(captured_cwd[0]).resolve()
        assert not str(cwd_path).startswith(str(ws.resolve()))
        assert not str(cwd_path).startswith(str(cpr.resolve()))

    def test_temp_directory_removed_after_success(self, tmp_path):
        cpr, ws, asset = _make_cpr_ws_asset(tmp_path)
        temp_paths = []

        original_temp = __import__("tempfile").TemporaryDirectory

        def tracking_temp(*args, **kwargs):
            td = original_temp(*args, **kwargs)
            temp_paths.append(Path(td.name))
            return td

        with patch("tempfile.TemporaryDirectory", tracking_temp), patch("subprocess.run") as mock_run:
            mock_run.return_value = FakeCompletedProcess(
                json.dumps({"passed": True, "checks": ["ok"], "error": ""}),
                returncode=0,
            )
            result = run_scenario_evaluator(
                str(cpr), "tests/evaluator_assets/checks.py", str(ws),
                python_executable=sys.executable, timeout=60,
            )
        assert result.passed
        for tp in temp_paths:
            assert not tp.exists(), f"Temp directory {tp} was not removed"

    def test_temp_directory_removed_after_failure(self, tmp_path):
        cpr, ws, asset = _make_cpr_ws_asset(tmp_path)
        temp_paths = []

        original_temp = __import__("tempfile").TemporaryDirectory

        def tracking_temp(*args, **kwargs):
            td = original_temp(*args, **kwargs)
            temp_paths.append(Path(td.name))
            return td

        def fake_run(*args, **kwargs):
            raise ValueError("simulated failure")

        with patch("tempfile.TemporaryDirectory", tracking_temp), patch("subprocess.run", fake_run):
            result = run_scenario_evaluator(
                str(cpr), "tests/evaluator_assets/checks.py", str(ws),
                python_executable=sys.executable, timeout=60,
            )
        assert not result.passed
        for tp in temp_paths:
            assert not tp.exists(), f"Temp directory {tp} was not removed"

    def test_source_not_copied_into_workspace(self, tmp_path):
        cpr, ws, asset = _make_cpr_ws_asset(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = FakeCompletedProcess(
                json.dumps({"passed": True, "checks": ["ok"], "error": ""}),
                returncode=0,
            )
            result = run_scenario_evaluator(
                str(cpr), "tests/evaluator_assets/checks.py", str(ws),
                python_executable=sys.executable, timeout=60,
            )
        assert result.passed
        assert not (ws / "scenario_evaluator.py").exists()

    def test_only_selected_asset_is_present_in_temp(self, tmp_path):
        cpr, ws, asset = _make_cpr_ws_asset(tmp_path)
        extra_asset = cpr / "tests" / "evaluator_assets" / "extra.py"
        extra_asset.write_text("")
        temp_files = []

        def fake_run(command, **kwargs):
            cwd = kwargs.get("cwd", "")
            temp_files.extend([str(p) for p in Path(cwd).iterdir()])
            return FakeCompletedProcess(
                json.dumps({"passed": True, "checks": ["ok"], "error": ""}),
                returncode=0,
            )

        with patch("subprocess.run", fake_run):
            result = run_scenario_evaluator(
                str(cpr), "tests/evaluator_assets/checks.py", str(ws),
                python_executable=sys.executable, timeout=60,
            )
        assert result.passed
        temp_names = [Path(f).name for f in temp_files]
        assert "scenario_evaluator.py" in temp_names
        assert "extra.py" not in temp_names

    def test_evaluator_never_written_to_workspace(self, tmp_path):
        cpr, ws, asset = _make_cpr_ws_asset(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = FakeCompletedProcess(
                json.dumps({"passed": True, "checks": ["ok"], "error": ""}),
                returncode=0,
            )
            result = run_scenario_evaluator(
                str(cpr), "tests/evaluator_assets/checks.py", str(ws),
                python_executable=sys.executable, timeout=60,
            )
        assert result.passed
        evaluator_in_ws = list(ws.rglob("scenario_evaluator.py"))
        assert len(evaluator_in_ws) == 0
