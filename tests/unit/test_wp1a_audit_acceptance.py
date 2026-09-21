"""WP-1a same-session cross-check + acceptance tests (AC-1A.10, section 14).

TERMINOLOGY CORRECTED 2026-09-21: the WP-1a 19-check pass is a same-session
alternate-implementation cross-check, NOT an independent/external audit.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

WP1A = PROJECT_DIR / "research" / "wp1a"


def _run_script(name: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PROJECT_DIR / "scripts" / name)],
        cwd=PROJECT_DIR, capture_output=True, text=True, timeout=300,
    )


def test_independent_audit_passes() -> None:
    result = _run_script("wp1a_independent_audit.py")
    assert result.returncode == 0, result.stdout + result.stderr
    audit = json.loads((WP1A / "wp1a_independent_audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "PASS"
    assert audit["pass"] == audit["total"]


def test_acceptance_report_all_pass() -> None:
    result = _run_script("wp1a_acceptance_report.py")
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((WP1A / "wp1a_acceptance_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "ALL_PASS"
    for c in report["criteria"]:
        assert c["pass"], c["criterion"]
    assert report["criteria"][0]["criterion"] == "AC-1A.1"
    assert report["criteria"][-1]["criterion"] == "AC-1A.12"


def test_acceptance_report_scientific_spend_zero() -> None:
    report = json.loads((WP1A / "wp1a_acceptance_report.json").read_text(encoding="utf-8"))
    ac11 = next(c for c in report["criteria"] if c["criterion"] == "AC-1A.11")
    assert ac11["pass"] is True
    assert "$0.00" in ac11["evidence"] or "no paid model/API call" in ac11["evidence"]
