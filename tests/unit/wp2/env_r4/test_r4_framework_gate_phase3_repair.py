"""M17_D7_R4_FRAMEWORK_GATE_PHASE3_REPAIR - manage-gate settings resolution tests.

Mission M17_D7_R4_FRAMEWORK_GATE_PHASE3_REPAIR_AND_REFREEZE (T3).

These tests are OFFLINE: no real container is run.  They prove the corrected
manage-gate semantics required by the Phase-2 frozen ruling (Candidate C):

  1. modern config resolves saleor.tests.settings;
  2. legacy config resolves tests.settings;
  3. missing settings declaration fails closed;
  4. conflicting settings declarations fail closed;
  5. referenced settings module absent from worktree fails closed;
  6. no task/unit/commit-specific selection exists;
  7. manage command uses the resolved module;
  8. pytest/import smoke behavior is unchanged.

Plus a frozen Phase-1 static replay: 219/219 resolvable, 218 modern, 1 legacy,
0 unresolved, 0 conflicting (uses the frozen probe/audit artifacts only).
"""
from __future__ import annotations

import base64
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
R4_DIR = ROOT / "research" / "env-canon-r4"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

import r4_behavioral_calibration_n12_r2 as r2  # noqa: E402

MODERN_MODULE = "saleor.tests.settings"
LEGACY_MODULE = "tests.settings"
PROBE_TSV = R4_DIR / "R4_FRAMEWORK_SEMANTICS_PROBE_219.tsv"
AUDIT_JSON = R4_DIR / "R4_FRAMEWORK_SEMANTICS_AUDIT_144.json"

MODERN_SETUP_CFG = "[tool:pytest]\naddopts = --ds=saleor.tests.settings\n"
LEGACY_SETUP_CFG = "[tool:pytest]\naddopts = --ds=tests.settings\n"


def _modern_wt(tmp_path: Path) -> Path:
    wt = tmp_path / "modern"
    (wt / "saleor" / "tests").mkdir(parents=True)
    (wt / "setup.cfg").write_text(MODERN_SETUP_CFG, encoding="utf-8")
    (wt / "saleor" / "tests" / "settings.py").write_text("", encoding="utf-8")
    return wt


def _legacy_wt(tmp_path: Path) -> Path:
    wt = tmp_path / "legacy"
    (wt / "tests").mkdir(parents=True)
    (wt / "setup.cfg").write_text(LEGACY_SETUP_CFG, encoding="utf-8")
    (wt / "tests" / "settings.py").write_text("", encoding="utf-8")
    return wt


def _run_container_program(wt: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-", str(wt)],
        input=r2.REPO_SETTINGS_RESOLVER_PROGRAM,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return proc.returncode, (proc.stdout or "").strip()


# ---------------------------------------------------------------------------
# 1 / 2 - P2P: modern + legacy resolve
# ---------------------------------------------------------------------------
class TestResolveP2P:
    def test_modern_config_resolves_saleor_tests_settings(self, tmp_path: Path) -> None:
        assert r2.resolve_repo_pytest_settings(_modern_wt(tmp_path)) == MODERN_MODULE

    def test_legacy_config_resolves_tests_settings(self, tmp_path: Path) -> None:
        assert r2.resolve_repo_pytest_settings(_legacy_wt(tmp_path)) == LEGACY_MODULE

    def test_container_program_matches_host_modern(self, tmp_path: Path) -> None:
        wt = _modern_wt(tmp_path)
        rc, out = _run_container_program(wt)
        assert rc == 0 and out == f"OK:{MODERN_MODULE}"

    def test_container_program_matches_host_legacy(self, tmp_path: Path) -> None:
        wt = _legacy_wt(tmp_path)
        rc, out = _run_container_program(wt)
        assert rc == 0 and out == f"OK:{LEGACY_MODULE}"


# ---------------------------------------------------------------------------
# 3 / 4 / 5 - F2P: fail-closed cases
# ---------------------------------------------------------------------------
class TestResolutionFailClosed:
    def test_missing_settings_declaration_fails_closed(self, tmp_path: Path) -> None:
        wt = tmp_path / "none"
        wt.mkdir()
        (wt / "setup.cfg").write_text("[tool:pytest]\naddopts = -q\n", encoding="utf-8")
        with pytest.raises(r2.SettingsResolutionError, match="NO_REPO_AUTHORED"):
            r2.resolve_repo_pytest_settings(wt)
        rc, out = _run_container_program(wt)
        assert rc != 0 and out.startswith("FAIL:NO_REPO_AUTHORIZED")

    def test_conflicting_settings_declarations_fail_closed(self, tmp_path: Path) -> None:
        wt = tmp_path / "conflict"
        wt.mkdir()
        (wt / "setup.cfg").write_text(
            "[tool:pytest]\naddopts = --ds=a.b --ds=c.d\n", encoding="utf-8"
        )
        with pytest.raises(r2.SettingsResolutionError, match="CONFLICT"):
            r2.resolve_repo_pytest_settings(wt)
        rc, out = _run_container_program(wt)
        assert rc != 0 and out.startswith("FAIL:CONFLICTING")

    def test_referenced_module_absent_from_worktree_fails_closed(self, tmp_path: Path) -> None:
        wt = tmp_path / "absent"
        (wt / "saleor" / "tests").mkdir(parents=True)
        (wt / "setup.cfg").write_text(MODERN_SETUP_CFG, encoding="utf-8")  # no settings.py file
        with pytest.raises(r2.SettingsResolutionError, match="ABSENT"):
            r2.resolve_repo_pytest_settings(wt)
        rc, out = _run_container_program(wt)
        assert rc != 0 and out.startswith("FAIL:SETTINGS_MODULE_ABSENT")

    def test_malformed_module_fails_closed(self, tmp_path: Path) -> None:
        wt = tmp_path / "malformed"
        wt.mkdir()
        (wt / "setup.cfg").write_text(
            "[tool:pytest]\naddopts = --ds=not a module\n", encoding="utf-8"
        )
        with pytest.raises(r2.SettingsResolutionError, match="MALFORMED"):
            r2.resolve_repo_pytest_settings(wt)


# ---------------------------------------------------------------------------
# 6 - no task/unit/commit-specific selection
# ---------------------------------------------------------------------------
class TestNoIdentitySelection:
    def test_resolver_has_no_identity_conditionals(self) -> None:
        src = r2.REPO_SETTINGS_RESOLVER_PROGRAM
        assert "FROZEN_UNIT_ORDER" not in src
        assert "validation_unit_id" not in src
        assert "task_id" not in src
        assert "commit" not in src
        assert "8220a534" not in src
        assert "56" not in src

    def test_host_resolver_is_general(self, tmp_path: Path) -> None:
        # same rule for any worktree; no unit/task/commit argument anywhere.
        wt = _modern_wt(tmp_path)
        module = r2.resolve_repo_pytest_settings(wt)
        assert module == MODERN_MODULE


# ---------------------------------------------------------------------------
# 7 / 8 - manage gate uses resolved module; pytest/import unchanged
# ---------------------------------------------------------------------------
class TestManageGateAndSmokeUnchanged:
    def test_manage_command_uses_resolved_module(self) -> None:
        script = r2.container_script("vu-test", 2, [], {"version_probes": {}})
        assert "python manage.py check --settings=\"$R4_SETTINGS_MODULE\"" in script
        assert "saleor.tests.settings" not in script  # no hardcoded universal module
        assert "R4_SETTINGS_MODULE" in script
        assert "MANAGE_RC_$(basename $wt)=SKIP" in script

    def test_import_smoke_unchanged(self) -> None:
        script = r2.container_script("vu-test", 1, [], {"version_probes": {}})
        assert 'python -c "import saleor"' in script
        assert "IMPORT_RC_$(basename $wt)=$?" in script

    def test_pytest_smoke_unchanged(self) -> None:
        script = r2.container_script("vu-test", 1, [], {"version_probes": {}})
        assert "python -m pytest --collect-only -q" in script
        assert "PYTEST_RC_$(basename $wt)=$?" in script
        assert "PYTEST_RC_$(basename $wt)=SKIP" in script

    def test_gate_ordering_unchanged(self) -> None:
        script = r2.container_script("vu-test", 1, [], {"version_probes": {}})
        idx_import = script.index('python -c "import saleor"')
        idx_manage = script.index("python manage.py check")
        idx_pytest = script.index("python -m pytest --collect-only")
        assert idx_import < idx_manage < idx_pytest

    def test_rc_classification_preserved(self) -> None:
        # MANAGE_RC semantics unchanged: 0 => pass, SKIP when no manage.py,
        # anything else => framework smoke failure.
        parsed = r2.parse_output(
            "NET_STATUS=NETWORK_UNAVAILABLE\n"
            "INSTALL_RC=0\nINSTALL_MS=1\nPIPCHECK_RC=0\n"
            "WT_wt0_IS_DIR=1\n"
            "IMPORT_RC_wt0=0\nMANAGE_RC_wt0=0\nPYTEST_RC_wt0=0\n"
        )
        assert r2.classify_unit(parsed, special={"version_probes": {}}, wt_count=1) == "PASS"
        parsed = r2.parse_output(
            "NET_STATUS=NETWORK_UNAVAILABLE\n"
            "INSTALL_RC=0\nINSTALL_MS=1\nPIPCHECK_RC=0\n"
            "WT_wt0_IS_DIR=1\n"
            "IMPORT_RC_wt0=0\nMANAGE_RC_wt0=7\nPYTEST_RC_wt0=0\n"
        )
        assert r2.classify_unit(parsed, special={"version_probes": {}}, wt_count=1) == r2.F_ENV_FRAMEWORK_GATE


# ---------------------------------------------------------------------------
# Frozen Phase-1 static replay
# ---------------------------------------------------------------------------
class TestStaticReplayFrozen219:
    @pytest.mark.skipif(not PROBE_TSV.is_file(), reason="frozen probe tsv unavailable")
    def test_frozen_219_replay(self) -> None:
        with open(PROBE_TSV, encoding="utf-8", newline="") as fh:
            rows = list(
                csv.DictReader(
                    fh,
                    delimiter="\t",
                    fieldnames=[
                        "commit", "manage", "setup_cfg", "pytest_ini", "pyproject", "tox_ini",
                        "saleor_settings", "tests_settings", "saleor_tests_settings", "saleor_init",
                        "tests_init", "saleor_tests_init", "conftest", "cdate",
                        "manage_b64", "setup_cfg_b64", "pytest_ini_b64", "pyproject_b64", "tox_ini_b64",
                    ],
                )
            )
        assert len(rows) == 219
        audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
        per_commit = audit["per_commit_records"]
        counts: dict[str, int] = {}
        unresolved = conflicting = mismatches = 0

        def _exists(row: dict[str, str], module: str) -> bool:
            if module == MODERN_MODULE:
                return row["saleor_tests_settings"] == "1" or row["saleor_tests_init"] == "1"
            if module == LEGACY_MODULE:
                return row["tests_settings"] == "1" or row["tests_init"] == "1"
            if module == "saleor.settings":
                return row["saleor_settings"] == "1" or row["saleor_init"] == "1"
            return False

        for row in rows:
            try:
                module = r2.resolve_repo_pytest_settings_from_texts(
                    _b64(row["setup_cfg_b64"]),
                    _b64(row["pytest_ini_b64"]),
                    _b64(row["pyproject_b64"]),
                    lambda m, r=row: _exists(r, m),
                )
            except r2.SettingsResolutionError as exc:
                if "CONFLICT" in str(exc):
                    conflicting += 1
                else:
                    unresolved += 1
                continue
            counts[module] = counts.get(module, 0) + 1
            frozen = str(per_commit[row["commit"]].get("repo_pytest_settings_module", "NONE_AUTHORED"))
            if module != frozen:
                mismatches += 1

        assert counts.get(MODERN_MODULE) == 218
        assert counts.get(LEGACY_MODULE) == 1
        assert unresolved == 0
        assert conflicting == 0
        assert mismatches == 0


def _b64(text: str) -> str:
    if not text:
        return ""
    try:
        return base64.b64decode(text).decode("utf-8", errors="replace")
    except Exception:
        return ""
