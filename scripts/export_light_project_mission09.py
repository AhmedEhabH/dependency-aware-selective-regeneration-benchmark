#!/usr/bin/env python3
"""Mission-09 TRUE LIGHT export (2026-09-25).

Extends the established TRUE LIGHT filter (export_light_project_v2.py) by
additionally excluding the single deterministically-reproducible heavy artifact:

  - research/wp2/wp2_p2p_u_v2_membership_2026-09-25.json (63.79 MB raw)

This membership artifact is FULLY and deterministically regenerable from the
frozen rule + frozen DEV inventory + the included freeze script
(scripts/wp2_p2p_u_v2_freeze.py), which was verified SHA-stable across repeated
runs. Its artifact SHA256 (8325747f...) is pinned in the Mission-09 STOP report,
so any auditor can regenerate it and verify the hash. The consolidated results,
sensitivity report, per-task manifests, and frozen hashes remain in the LIGHT
export, so nothing needed to audit Mission-09 scientific claims is omitted.

All other established TRUE LIGHT exclusions apply (.git/, *.zip, locagent logs,
reproducible candidate_universe/dependency_graph, etc.).

Output: project-LIGHT-<stamp>.zip in the parent directory (<= 50 MB).
"""
from __future__ import annotations

import datetime
import hashlib
import importlib.util
import sys
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
PARENT_DIR = PROJECT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

_orig = importlib.util.spec_from_file_location(
    "export_light_project_v2", PROJECT_DIR / "scripts" / "export_light_project_v2.py"
)
_mod = importlib.util.module_from_spec(_orig)
_orig.loader.exec_module(_mod)
_should_exclude = _mod.should_exclude

REPRODUCIBLE_MEMBERSHIP = "research/wp2/wp2_p2p_u_v2_membership_2026-09-25.json"


def should_exclude(rel: str) -> bool:
    if rel == REPRODUCIBLE_MEMBERSHIP:
        return True
    return _should_exclude(rel)


def main() -> int:
    full_candidates = sorted(
        p for p in PARENT_DIR.glob("project-*.zip")
        if not p.name.startswith("project-LIGHT-"))
    if not full_candidates:
        print("no full export found; run scripts/export_light_project.py first")
        return 1
    src = full_candidates[-1]

    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    out = PARENT_DIR / f"project-LIGHT-{stamp}.zip"
    kept = dropped = 0
    membership_dropped = 0
    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == REPRODUCIBLE_MEMBERSHIP:
                membership_dropped += 1
                dropped += 1
                continue
            if should_exclude(item.filename):
                dropped += 1
                continue
            zout.writestr(item, zin.read(item.filename))
            kept += 1

    size = out.stat().st_size
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
    # verify reproducibility: the membership SHA is recorded in the STOP report;
    # the regenerability is proven by the freeze script (SHA-stable). Here we
    # verify the frozen artifact is absent (as documented) and that consolidated
    # results + reports are present.
    report_present = "docs/MISSION_09_P2P_V2_STOP_REPORT_2026-09-25.md" in names
    consolidated_present = "research/wp2/p2p_u_v2_eng_2026-09-25/consolidated_results_2026-09-25.json" in names
    sens_present = "research/wp2/p2p_u_v2_eng_2026-09-25/SENSITIVITY_REPORT_200_vs_400_2026-09-25.md" in names
    rule_present = "research/wp2/wp2_p2p_u_v2_rule_freeze_2026-09-25.json" in names
    p2ps_present = "research/wp2/wp2_dev_p2p_s_v1_2026-09-25.json" in names
    freeze_script_present = "scripts/wp2_p2p_u_v2_freeze.py" in names
    audit_ok = all([
        report_present, consolidated_present, sens_present,
        rule_present, p2ps_present, freeze_script_present,
    ])

    print("LIGHT_EXPORT_READY")
    print(f"SOURCE={src.name}")
    print(f"LIGHT_EXPORT_NAME={out.name}")
    print(f"LIGHT_EXPORT_PATH={out}")
    print(f"LIGHT_EXPORT_SIZE_BYTES={size}")
    print(f"LIGHT_EXPORT_MB={round(size / 1e6, 2)}")
    print(f"LIGHT_EXPORT_SHA256={digest}")
    print(f"ENTRIES_KEPT={kept} ENTRIES_DROPPED={dropped} MEMBERSHIP_DROPPED_REPRODUCIBLE={membership_dropped}")
    print("HAS_HEAD=" + str(".git/HEAD" in names))
    print("HAS_PILOT_ZIP=" + str("dist/pilot-kaggle-upload.zip" in names))
    print(f"AUDIT_EVIDENCE_PRESENT={audit_ok}")
    print("WITHIN_50MB=" + str(size <= 50_000_000))
    print("MEMBERSHIP_EXCLUDED_AS_REPRODUCIBLE=" + str(membership_dropped == 1))
    return 0 if (size <= 50_000_000 and audit_ok) else 2


if __name__ == "__main__":
    raise SystemExit(main())
