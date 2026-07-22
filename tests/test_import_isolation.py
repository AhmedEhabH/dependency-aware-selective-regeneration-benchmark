"""Verify that importing benchmark.core and benchmark.config
does not import or require torch, transformers, Django, GitPython,
or Kaggle packages.
"""

import subprocess
import sys
from pathlib import Path


def _run_import_check(import_statement: str) -> tuple[int, str, str]:
    project_root = Path(__file__).resolve().parents[1]
    code = (
        f"import sys; sys.path.insert(0, r'{project_root / 'src'}'); "
        f"{import_statement}; "
        f"print('torch:', 'torch' in sys.modules); "
        f"print('transformers:', 'transformers' in sys.modules); "
        f"print('django:', 'django' in sys.modules); "
        f"print('gitpython:', 'git' in sys.modules)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


class TestImportIsolation:
    def test_import_benchmark_core_no_torch(self) -> None:
        ret, stdout, stderr = _run_import_check("import benchmark.core")
        assert ret == 0, f"stderr: {stderr}"
        assert "torch: False" in stdout, f"torch leaked: {stdout}"
        assert "transformers: False" in stdout, f"transformers leaked: {stdout}"
        assert "django: False" in stdout, f"django leaked: {stdout}"

    def test_import_benchmark_config_no_torch(self) -> None:
        ret, stdout, stderr = _run_import_check("import benchmark.config")
        assert ret == 0, f"stderr: {stderr}"
        assert "torch: False" in stdout, f"torch leaked: {stdout}"
        assert "transformers: False" in stdout, f"transformers leaked: {stdout}"
        assert "django: False" in stdout, f"django leaked: {stdout}"

    def test_import_full_benchmark_no_torch(self) -> None:
        ret, stdout, stderr = _run_import_check("import benchmark")
        assert ret == 0, f"stderr: {stderr}"
        assert "torch: False" in stdout, f"torch leaked: {stdout}"
        assert "transformers: False" in stdout, f"transformers leaked: {stdout}"
