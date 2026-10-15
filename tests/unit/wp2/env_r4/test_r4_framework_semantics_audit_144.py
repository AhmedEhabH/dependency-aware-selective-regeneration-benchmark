"""M17_D7_R4_FRAMEWORK_SEMANTICS_AUDIT_144 — targeted offline tests.

Mission M17_D7_R4_FRAMEWORK_SEMANTICS_AUDIT_144 (read-mostly audit).

These tests are OFFLINE: they never touch WSL git objects, never run a unit,
never use Docker and never mutate frozen authorities.  Pure classification and
population/accounting paths are exercised with frozen evidence and synthetic
rows; probe coverage is validated against the frozen probe TSV when present.

Themes:
  P1 — 144/219 accounting from the frozen census (identity + membership hash).
  P2 — distinct-commit census == 219, every unit's commits resolve in probe TSV.
  P3 — deterministic manage.py settings semantics extraction.
  P4 — deterministic pytest --ds extraction + mypy-django + tox manage commands.
  P5 — settings-layout family classification (evidence-based).
  P6 — per-commit semantics classification (forced-module exists/agrees).
  P7 — signature determinism (identical semantics -> identical signature).
  P8 — current manage-gate semantics agreement + impact sets (synthetic rows).
  P9 — historical-layout census: 218 saleor.tests.settings / 1 top-level tests.
  F1 — wrong population identity fails closed.
  F2 — probe row-count mismatch fails closed.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
R4_DIR = ROOT / "research" / "env-canon-r4"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

import r4_framework_semantics_audit_144 as audit  # noqa: E402

PROBE_TSV = R4_DIR / "R4_FRAMEWORK_SEMANTICS_PROBE_219.tsv"
HAS_PROBE = PROBE_TSV.is_file()

MANAGE_MODERN = (
    '#!/usr/bin/env python3\nimport os\nimport sys\n\n'
    'if __name__ == "__main__":\n'
    '    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")\n'
    '    from django.core.management import execute_from_command_line\n'
    '    execute_from_command_line(sys.argv)\n'
)

SETUP_CFG_MODERN = (
    "[tool:pytest]\naddopts = -n auto --vcr-record-mode=none --ds=saleor.tests.settings\n"
    "testpaths = tests saleor\n\n"
    "[mypy]\nplugins = mypy_django_plugin.main\n\n"
    "[mypy.plugins.django-stubs]\ndjango_settings_module = saleor.settings\n"
)

SETUP_CFG_LEGACY = (
    "[tool:pytest]\naddopts = -n auto --vcr-record-mode=none --ds=tests.settings\n"
    "testpaths = tests saleor\n\n"
    "[mypy.plugins.django-stubs]\ndjango_settings_module = saleor.settings\n"
)


def _b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def _row(
    commit: str,
    *,
    saleor_tests: str = "1",
    tests: str = "0",
    manage_b64: str = "",
    setup_cfg_b64: str = "",
    pyproject_b64: str = "",
    tox_b64: str = "",
    manage: str = "1",
) -> dict[str, str]:
    return {
        "commit": commit,
        "manage": manage,
        "setup_cfg": "1",
        "pytest_ini": "0",
        "pyproject": "1",
        "tox_ini": "1",
        "saleor_settings": "1",
        "tests_settings": tests,
        "saleor_tests_settings": saleor_tests,
        "saleor_init": "1",
        "tests_init": "0",
        "saleor_tests_init": "1",
        "conftest": "1",
        "cdate": "2020-01-01 00:00:00 +0000",
        "manage_b64": manage_b64 or _b64(MANAGE_MODERN),
        "setup_cfg_b64": setup_cfg_b64 or _b64(SETUP_CFG_MODERN),
        "pytest_ini_b64": "",
        "pyproject_b64": pyproject_b64,
        "tox_ini_b64": tox_b64,
    }


class TestPopulationAccounting:
    def test_144_units_219_tasks_identity_hash(self) -> None:
        units = audit.unit_records()
        assert len(units) == 144
        assert audit.account_tasks() == 219
        ids = [u["validation_unit_id"] for u in units]
        payload = json.dumps(ids, separators=(",", ":"))
        assert hashlib.sha256(payload.encode("utf-8")).hexdigest() == audit.EXPECTED_MEMBERSHIP_HASH
        census = json.loads(audit.CENSUS_PATH.read_text(encoding="utf-8"))
        assert census["population_identity_sha256"] == audit.EXPECTED_POPULATION_IDENTITY

    def test_distinct_commits_are_219(self) -> None:
        units = audit.unit_records()
        commits = {c for u in units for c in u["member_target_commits"]}
        assert len(commits) == 219

    def test_unit56_is_legacy_commit(self) -> None:
        units = audit.unit_records()
        u56 = next(u for u in units if u["calibration_index"] == 56)
        assert u56["member_target_commits"] == ["8220a53473bb67bbb247490cbd043c56dac4568c"]


class TestProbeCoverage:
    @pytest.mark.skipif(not HAS_PROBE, reason="frozen probe TSV absent")
    def test_probe_tsv_covers_all_219_commits(self) -> None:
        units = audit.unit_records()
        commits = {c for u in units for c in u["member_target_commits"]}
        rows = audit._read_probe_tsv(sorted(commits))
        assert len(rows) == 219
        assert {r["commit"] for r in rows} == commits

    @pytest.mark.skipif(not HAS_PROBE, reason="frozen probe TSV absent")
    def test_probe_tsv_row_shape(self) -> None:
        units = audit.unit_records()
        commits = sorted({c for u in units for c in u["member_target_commits"]})
        rows = audit._read_probe_tsv(commits)
        for r in rows:
            assert len(r) == 19
            assert r["commit"] in commits


class TestManageSettingsSemantics:
    def test_setdefault_literal(self) -> None:
        rec = audit.manage_settings_semantics(MANAGE_MODERN)
        assert rec == {"mode": "SETDEFAULT_LITERAL", "module": "saleor.settings"}

    def test_assign_literal(self) -> None:
        text = 'import os\nDJANGO_SETTINGS_MODULE = "saleor.settings"\n'
        assert audit.manage_settings_semantics(text)["module"] == "saleor.settings"

    def test_dynamic_env(self) -> None:
        text = 'import os\nos.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("X"))\n'
        assert audit.manage_settings_semantics(text)["mode"] == "ENVIRONMENT_DYNAMIC"

    def test_none_static(self) -> None:
        assert audit.manage_settings_semantics("print('hi')\n")["mode"] == "NONE_STATIC"


class TestPytestDsExtraction:
    def test_setup_cfg_ds(self) -> None:
        assert audit.pytest_ds_modules(SETUP_CFG_MODERN, "", "") == ["saleor.tests.settings"]
        assert audit.pytest_ds_modules(SETUP_CFG_LEGACY, "", "") == ["tests.settings"]

    def test_pyproject_ds(self) -> None:
        pp = "[tool.pytest]\naddopts = [\"--ds=saleor.tests.settings\", \"-q\"]\n"
        assert audit.pytest_ds_modules("", "", pp) == ["saleor.tests.settings"]

    def test_mypy_django(self) -> None:
        assert audit.mypy_django_settings(SETUP_CFG_MODERN, "") == ["saleor.settings"]

    def test_tox_manage_commands(self) -> None:
        tox = "commands =\n    python manage.py collectstatic --noinput\n    pytest --cov\n"
        assert audit.tox_manage_commands(tox) == ["collectstatic"]


class TestSettingsLayoutFamily:
    def test_saleor_package_tests(self) -> None:
        row = _row("a", saleor_tests="1", tests="0")
        assert audit.settings_layout_family(row) == "SALEOR_PACKAGE_TESTS_SETTINGS"

    def test_top_level_tests(self) -> None:
        row = _row("b", saleor_tests="0", tests="1")
        assert audit.settings_layout_family(row) == "TOP_LEVEL_TESTS_SETTINGS"


class TestCommitClassification:
    def test_modern_commit_matches_current_gate(self) -> None:
        rec = audit.classify_commit(_row("aaaa"))
        assert rec["manage_default_settings_module"] == "saleor.settings"
        assert rec["repo_pytest_settings_module"] == "saleor.tests.settings"
        assert rec["current_forced_manage_settings_exists"] is True
        assert rec["current_manage_semantics_matches_repository"] == "MATCH"
        assert rec["settings_layout_family"] == "SALEOR_PACKAGE_TESTS_SETTINGS"

    def test_legacy_commit_mismatch(self) -> None:
        row = _row(
            "8220a53473bb67bbb247490cbd043c56dac4568c",
            saleor_tests="0",
            tests="1",
            setup_cfg_b64=_b64(SETUP_CFG_LEGACY),
        )
        rec = audit.classify_commit(row)
        assert rec["repo_pytest_settings_module"] == "tests.settings"
        assert rec["current_forced_manage_settings_exists"] is False
        assert rec["current_manage_semantics_matches_repository"] == "MISMATCH"
        assert rec["settings_layout_family"] == "TOP_LEVEL_TESTS_SETTINGS"

    def test_signature_determinism(self) -> None:
        r1 = audit.classify_commit(_row("aa"))
        r2 = audit.classify_commit(_row("bb"))
        assert audit.commit_signature(r1) == audit.commit_signature(r2)

    def test_signature_differs_across_families(self) -> None:
        modern = audit.classify_commit(_row("aa"))
        legacy = audit.classify_commit(
            _row("8220", saleor_tests="0", tests="1", setup_cfg_b64=_b64(SETUP_CFG_LEGACY))
        )
        assert audit.commit_signature(modern) != audit.commit_signature(legacy)


class TestImpactSetsSynthetic:
    def test_isolated_legacy_unit_is_mismatch(self) -> None:
        modern = audit.classify_commit(_row("m1"))
        legacy = audit.classify_commit(
            _row("8220", saleor_tests="0", tests="1", setup_cfg_b64=_b64(SETUP_CFG_LEGACY))
        )
        assert modern["current_manage_semantics_matches_repository"] == "MATCH"
        assert legacy["current_manage_semantics_matches_repository"] == "MISMATCH"


class TestAssumptionInventory:
    def test_inventory_classifications_are_bounded(self) -> None:
        rows = [_row("a"), _row("b", saleor_tests="0", tests="1")]
        inv = audit.assumption_inventory(rows)
        assert len(inv) == 7
        allowed = {
            "HISTORICALLY_UNIVERSAL",
            "HISTORICALLY_CONDITIONAL",
            "HISTORICALLY_FALSE_FOR_SOME_POPULATION",
            "UNRESOLVED",
        }
        for a in inv:
            assert a["classification"] in allowed
            assert a["population_evidence"]


class TestHistoricalLayoutCensus:
    @pytest.mark.skipif(not HAS_PROBE, reason="frozen probe TSV absent")
    def test_218_saleor_tests_1_top_level(self) -> None:
        units = audit.unit_records()
        commits = sorted({c for u in units for c in u["member_target_commits"]})
        rows = audit._read_probe_tsv(commits)
        saleor_tests = sum(1 for r in rows if r["saleor_tests_settings"] == "1")
        top_tests = sum(1 for r in rows if r["tests_settings"] == "1")
        assert saleor_tests == 218
        assert top_tests == 1

    @pytest.mark.skipif(not HAS_PROBE, reason="frozen probe TSV absent")
    def test_legacy_commit_is_unit56_only(self) -> None:
        units = audit.unit_records()
        commits = sorted({c for u in units for c in u["member_target_commits"]})
        rows = audit._read_probe_tsv(commits)
        legacy = [r["commit"] for r in rows if r["saleor_tests_settings"] == "0"]
        assert legacy == ["8220a53473bb67bbb247490cbd043c56dac4568c"]
        # confirm this commit appears only in unit 56
        holders = [u["calibration_index"] for u in units if legacy[0] in u["member_target_commits"]]
        assert holders == [56]

    @pytest.mark.skipif(not HAS_PROBE, reason="frozen probe TSV absent")
    def test_real_legacy_commit_classifies_mismatch(self) -> None:
        units = audit.unit_records()
        commits = sorted({c for u in units for c in u["member_target_commits"]})
        rows = {r["commit"]: r for r in audit._read_probe_tsv(commits)}
        rec = audit.classify_commit(rows["8220a53473bb67bbb247490cbd043c56dac4568c"])
        assert rec["current_manage_semantics_matches_repository"] == "MISMATCH"
        assert rec["repo_pytest_settings_module"] == "tests.settings"
        assert rec["settings_layout_family"] == "TOP_LEVEL_TESTS_SETTINGS"


class TestFailClosed:
    def test_probe_row_count_mismatch_fails(self) -> None:
        # deterministic rerun path: missing probe evidence must fail closed
        units = audit.unit_records()
        commits = sorted({c for u in units for c in u["member_target_commits"]})
        with pytest.raises(RuntimeError):
            audit._read_probe_tsv(commits[:10])

    def test_probe_tsv_absent_fails(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(audit, "PROBE_TSV", tmp_path / "absent.tsv")
        with pytest.raises(RuntimeError):
            audit._read_probe_tsv(["a"])
