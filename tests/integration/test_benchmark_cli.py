"""Integration tests for the unified benchmark CLI (ZERO API)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/benchmark_cli.py", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def test_models_lists_all_profiles() -> None:
    proc = _run_cli("models")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    for pid in (
        "qwen3-coder-openrouter-deepinfra",
        "deepseek-v4-flash-openrouter",
        "deepseek-v4-flash-direct",
        "deepseek-v4-pro-openrouter",
        "hf-example",
    ):
        assert pid in proc.stdout


def test_dry_run_resolves_profile_no_token_required() -> None:
    proc = _run_cli("dry-run", "--study", "real-commit-p1")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PROFILE=qwen3-coder-openrouter-deepinfra" in proc.stdout
    assert "EXACT_MODEL=openrouter:qwen/qwen3-coder@deepinfra/turbo" in proc.stdout
    assert "PROFILE_SHA256=" in proc.stdout
    assert "API_KEY_PRESENT=" in proc.stdout


def test_verify_runs_study_gates() -> None:
    proc = _run_cli("verify", "--study", "real-commit-p1")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OVERALL=PASS" in proc.stdout


def test_verify_controlled_encoding_16k() -> None:
    proc = _run_cli("verify", "--study", "controlled-encoding-16k")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "M1B_VERIFIER=PASS" in proc.stdout


def test_unknown_study_fails() -> None:
    proc = _run_cli("dry-run", "--study", "nope")
    assert proc.returncode == 2


def test_probe_missing_token_fails_clearly(monkeypatch) -> None:
    # The default P1 profile requires OPENROUTER_API_KEY. With the token
    # absent, the CLI must fail clearly WITHOUT dispatching a probe (no API
    # call). The env var is removed for the duration of this test so the
    # assertion is deterministic and the probe is never dispatched.
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    proc = _run_cli("probe", "--study", "real-commit-p1")
    assert proc.returncode == 1
    assert "missing API token" in proc.stdout
    assert "OPENROUTER_API_KEY" in proc.stdout


def test_models_never_logs_secret() -> None:
    proc = _run_cli("models")
    assert proc.returncode == 0
    # the profile YAML only references env NAMES, never literal tokens
    assert "sk-" not in proc.stdout.lower()
