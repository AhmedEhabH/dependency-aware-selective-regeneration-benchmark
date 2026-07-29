from __future__ import annotations

import hashlib
import json

import pytest

from benchmark.execution.scenario_evaluator import (
    ScenarioEvaluatorResult,
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


class TestEvaluatorInputValidation:
    def test_valid_paths(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("")
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr),
            "tests/evaluator_assets/checks.py",
            str(ws),
            python_executable="python",
            timeout=60,
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
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_whitespace_asset(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "   ", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_asset_with_nul(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks\x00.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_asset_with_backslash(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests\\evaluator_assets\\checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_traversal(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/../checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_absolute_asset(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "/etc/passwd", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_wrong_extension(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.txt", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_missing_asset_file(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        ws = tmp_path / "workspace"
        ws.mkdir()
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

    def test_workspace_missing(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("")
        ws = tmp_path / "nonexistent"
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_workspace_file(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("")
        ws = tmp_path / "afile"
        ws.write_text("")
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_workspace_equals_canonical_root(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("")
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(cpr), python_executable="python", timeout=60
        )
        assert isinstance(result, str)

    def test_workspace_nested_under_canonical_root(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("")
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
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("")
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="", timeout=60
        )
        assert isinstance(result, str)

    def test_nul_executable(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("")
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="py\x00thon", timeout=60
        )
        assert isinstance(result, str)

    def test_invalid_timeout_type(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("")
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60.5
        )
        assert isinstance(result, str)


class TestTrustedEvaluatorAsset:
    def test_valid_content_and_sha256(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        content = b"print('ok')"
        asset.write_bytes(content)
        ws = tmp_path / "workspace"
        ws.mkdir()
        request = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(request, _ValidatedEvaluatorRequest)
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, _TrustedEvaluatorAsset)
        assert trusted.content == content
        expected_sha = hashlib.sha256(content).hexdigest()
        assert trusted.sha256 == expected_sha

    def test_read_failure(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("ok")
        ws = tmp_path / "workspace"
        ws.mkdir()
        request = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(request, _ValidatedEvaluatorRequest)
        asset.unlink()
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, str)


class TestEvaluatorSubprocess:
    def test_exact_command_and_cwd(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("import sys; import json; print(json.dumps({'passed': True, 'checks': ['ok'], 'error': ''}))")
        ws = tmp_path / "workspace"
        ws.mkdir()
        request = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(request, _ValidatedEvaluatorRequest)
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, _TrustedEvaluatorAsset)
        outcome = _execute_evaluator_subprocess(request, trusted)
        assert outcome.succeeded
        assert outcome.exit_code == 0

    def test_workspace_in_pythonpath(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("import sys; import json; print(json.dumps({'passed': True, 'checks': ['pp'], 'error': ''}))")
        ws = tmp_path / "workspace"
        ws.mkdir()
        request = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws), python_executable="python", timeout=60
        )
        assert isinstance(request, _ValidatedEvaluatorRequest)
        trusted = _load_trusted_evaluator_asset(request)
        assert isinstance(trusted, _TrustedEvaluatorAsset)
        outcome = _execute_evaluator_subprocess(request, trusted)
        assert outcome.succeeded

    def test_command_not_found(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("")
        ws = tmp_path / "workspace"
        ws.mkdir()
        request = _validate_evaluator_request(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws),
            python_executable="nonexistent_python_xyz", timeout=60
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
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        ws = tmp_path / "workspace"
        ws.mkdir()

        result = ScenarioEvaluatorResult(
            passed=expected_passed,
            exit_code=exit_code,
            checks=tuple(payload_checks),
            error=payload_error,
            stdout=json.dumps({"passed": payload_passed, "checks": payload_checks, "error": payload_error}),
            stderr="",
            duration_seconds=0.1,
        )
        if expected_passed:
            assert result.passed
        else:
            assert not result.passed


class TestEvaluatorIsolation:
    def test_temp_outside_workspace(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("import sys; import json; print(json.dumps({'passed': True, 'checks': ['ok'], 'error': ''}))")
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = run_scenario_evaluator(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws),
            python_executable="python", timeout=60,
        )
        assert result.passed

    def test_source_not_copied_into_workspace(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("import sys; import json; print(json.dumps({'passed': True, 'checks': ['ok'], 'error': ''}))")
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = run_scenario_evaluator(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws),
            python_executable="python", timeout=60,
        )
        assert result.passed
        assert not (ws / "scenario_evaluator.py").exists()

    def test_only_one_asset_copied(self, tmp_path):
        cpr = tmp_path / "project"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset = cpr / "tests" / "evaluator_assets" / "checks.py"
        asset.write_text("import sys; import json; print(json.dumps({'passed': True, 'checks': ['ok'], 'error': ''}))")
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = run_scenario_evaluator(
            str(cpr), "tests/evaluator_assets/checks.py", str(ws),
            python_executable="python", timeout=60,
        )
        assert result.passed
