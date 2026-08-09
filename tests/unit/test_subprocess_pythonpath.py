"""Regression test: PYTHONPATH fix for subprocess calls in Kaggle notebook.

The notebook sets PYTHONPATH=str(CODE_DIR / "src") so that subprocess
invocations of seven_arm_benchmark.py can import benchmark.* modules.
This test validates that the fix works by running from a temp directory.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


def _find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def test_subprocess_pythonpath_from_arbitrary_cwd(tmp_path: Path) -> None:
    project_root = _find_project_root()
    script = project_root / "seven_arm_benchmark.py"
    if not script.is_file():
        pytest.skip(f"seven_arm_benchmark.py not found at {script}")

    src_dir = project_root / "src"
    data_dir = project_root / "benchmark_data"
    output_dir = tmp_path / "runs"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_dir) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )

    # Run from a temp directory (simulates Kaggle where CWD != repo root)
    cmd = [
        sys.executable, str(script),
        "--dry-run",
        "--profile", "smoke",
        "--data-dir", str(data_dir),
        "--output-dir", str(output_dir),
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env, cwd=str(tmp_path),
    )
    combined = result.stdout + result.stderr

    assert result.returncode == 0, (
        f"Exit code {result.returncode}.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "Loaded 27 scenarios" in combined, (
        f"Missing 'Loaded 27 scenarios'.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "Benchmark complete" in combined, (
        f"Missing 'Benchmark complete'.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
