"""WP-2 Mission-11 E2E Smoke - py_compile in era container (B9.2, label-free).

Runs ``python -m py_compile`` inside the frozen era container on a temp dir
of the edited file texts. No dependency install is needed for a syntax check.
Generator-side (validator) uses this; it never imports the evaluator.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path


def _wsl_path(win: Path) -> str:
    s = str(win.resolve()).replace("\\", "/")
    return "/mnt/c" + s[2:]


def py_compile_in_era(era_key: str, files: dict[str, str]) -> dict[str, str]:
    """Return {path: "ok" | error-text} after py_compile under wp2-era-<era>."""
    results: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for path, text in files.items():
            p = td / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8", newline="")
        names = [p.relative_to(td).as_posix() for p in td.rglob("*.py")]
        if not names:
            return results
        mount = _wsl_path(td)
        r = subprocess.run(
            ["wsl", "-d", "Ubuntu-24.04", "--", "docker", "run", "--rm",
             "-v", f"{mount}:/work", f"wp2-era-{era_key}",
             "bash", "-lc", "cd /work && python -m py_compile " + " ".join(names)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        if r.returncode == 0:
            for path in files:
                results[path] = "ok"
            return results
        lines = (r.stderr or "").splitlines()
        current = None
        for line in lines:
            m = re.search(r'"/work/([^"]+)"', line)
            if m:
                current = m.group(1)
            if current is not None and ("Error" in line or "error" in line or "SyntaxError" in line):
                results.setdefault(current, line.strip())
        for path in files:
            results.setdefault(path, "py_compile_failed")
    return results