#!/usr/bin/env python3
"""M17_D7_R4_FRAMEWORK_GATE_PHASE3_REPAIR - static replay over frozen Phase-1 probe.

Proves the implemented manage-gate settings-resolution rule is consistent with
the FROZEN Phase-1 repository-authored semantics, using only the frozen probe
artifacts (NO git rescan, NO new census):

  expected: 219/219 resolvable
            218 -> saleor.tests.settings
            1   -> tests.settings
            0 unresolved
            0 conflicting

It reuses the exact resolver functions shipped in the qualified runner
(``scripts/r4_behavioral_calibration_n12_r2.py``), so the rule under test is
the rule that runs in the corrected manage gate.
"""
from __future__ import annotations

import base64
import csv
import json
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
R4_DIR = ROOT / "research" / "env-canon-r4"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import r4_behavioral_calibration_n12_r2 as r2  # noqa: E402

PROBE_TSV = R4_DIR / "R4_FRAMEWORK_SEMANTICS_PROBE_219.tsv"
AUDIT_JSON = R4_DIR / "R4_FRAMEWORK_SEMANTICS_AUDIT_144.json"
EXPECTED_TOTAL = 219
EXPECTED_MODERN = 218
EXPECTED_LEGACY = 1
MODERN_MODULE = "saleor.tests.settings"
LEGACY_MODULE = "tests.settings"


def _b64(text: str) -> str:
    if not text:
        return ""
    try:
        return base64.b64decode(text).decode("utf-8", errors="replace")
    except Exception:
        return ""


def module_exists_from_probe(row: dict[str, str]) -> Callable[[str], bool]:
    """Existence check keyed to the frozen probe file-presence columns.

    The probe records, per commit, the exact repository layout presence flags
    used by Phase-1: ``saleor_tests_settings`` / ``tests_settings`` /
    ``saleor_settings`` and their ``__init__`` markers.  For the two frozen
    signatures only ``saleor.tests.settings`` and ``tests.settings`` are
    authored, so presence maps directly to those flags.
    """

    def _exists(module: str) -> bool:
        if module == MODERN_MODULE:
            return row.get("saleor_tests_settings") == "1" or row.get("saleor_tests_init") == "1"
        if module == LEGACY_MODULE:
            return row.get("tests_settings") == "1" or row.get("tests_init") == "1"
        if module == "saleor.settings":
            return row.get("saleor_settings") == "1" or row.get("saleor_init") == "1"
        # generic: probe has no per-module flag; a settings.py under that path
        # is implied by the layout families only for the frozen modules.
        return False

    return _exists


def main() -> int:
    with open(PROBE_TSV, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(
            fh,
            delimiter="\t",
            fieldnames=[
                "commit", "manage", "setup_cfg", "pytest_ini", "pyproject", "tox_ini",
                "saleor_settings", "tests_settings", "saleor_tests_settings", "saleor_init",
                "tests_init", "saleor_tests_init", "conftest", "cdate",
                "manage_b64", "setup_cfg_b64", "pytest_ini_b64", "pyproject_b64", "tox_ini_b64",
            ],
        ))
    if len(rows) != EXPECTED_TOTAL:
        print(f"FAIL probe rows {len(rows)} != {EXPECTED_TOTAL}")
        return 1

    counts: dict[str, int] = {}
    unresolved: list[str] = []
    conflicting: list[str] = []
    mismatches: list[str] = []
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    per_commit = audit["per_commit_records"]

    for row in rows:
        commit = row["commit"]
        try:
            module = r2.resolve_repo_pytest_settings_from_texts(
                _b64(row["setup_cfg_b64"]),
                _b64(row["pytest_ini_b64"]),
                _b64(row["pyproject_b64"]),
                module_exists_from_probe(row),
            )
        except r2.SettingsResolutionError as exc:
            reason = str(exc)
            if "CONFLICT" in reason:
                conflicting.append(commit)
            else:
                unresolved.append(commit)
            continue
        counts[module] = counts.get(module, 0) + 1
        frozen_repo_module = str(per_commit[commit].get("repo_pytest_settings_module", "NONE_AUTHORED"))
        if module != frozen_repo_module:
            mismatches.append(f"{commit[:12]} resolved={module} frozen={frozen_repo_module}")

    modern = counts.get(MODERN_MODULE, 0)
    legacy = counts.get(LEGACY_MODULE, 0)
    ok = (
        len(rows) == EXPECTED_TOTAL
        and modern == EXPECTED_MODERN
        and legacy == EXPECTED_LEGACY
        and not unresolved
        and not conflicting
        and not mismatches
    )
    summary = {
        "total_commits": len(rows),
        "resolvable": modern + legacy,
        "modern": {MODERN_MODULE: modern},
        "legacy": {LEGACY_MODULE: legacy},
        "unresolved": len(unresolved),
        "unresolved_commits": unresolved,
        "conflicting": len(conflicting),
        "conflicting_commits": conflicting,
        "frozen_repo_module_mismatches": mismatches,
        "verdict": "PASS" if ok else "FAIL",
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("STATIC_REPLAY_PASS" if ok else "STATIC_REPLAY_FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
