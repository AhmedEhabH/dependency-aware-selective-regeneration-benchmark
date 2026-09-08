#!/usr/bin/env python3
"""Build the compact djangoCMS ImpactPlan-v2 probe evidence ZIP.

ZIP: reports/STAGEC_DJANGOCMS_IMPACTPLAN_V2_EVIDENCE.zip

Contents (task artifact #1): the complete v2 cost/smoke probe evidence plus
the v2 implementation, tests, mapping artifact, and reports. The project
transfer ZIP is built separately (stagec_djangocms_16k_transfer_export.py).
"""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

EVIDENCE_DIR = PROJECT_DIR / "reports" / "scientific-stagec-djangocms-impactplan-v2-costprobe-01"
OUT = PROJECT_DIR / "reports" / "STAGEC_DJANGOCMS_IMPACTPLAN_V2_EVIDENCE.zip"

ENTRIES: list[str] = [
    "reports/DJANGOCMS_IMPACTPLAN_V2_DESIGN.md",
    "reports/DJANGOCMS_IMPACTPLAN_V2_COSTPROBE.md",
    "src/benchmark/selection/impact_planner_v2.py",
    "tests/unit/selection/test_impact_plan_v2.py",
    "scripts/stagec_djangocms_impactplan_v2_costprobe_execute.py",
    "benchmark_data/external_validity/impactplan_v2_candidate_id_map.json",
]


def main() -> int:
    if not EVIDENCE_DIR.is_dir():
        raise FileNotFoundError(EVIDENCE_DIR)
    evidence_files = sorted(
        p for p in EVIDENCE_DIR.iterdir() if p.is_file()
    )
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in ENTRIES:
            src = PROJECT_DIR / rel
            if src.is_file():
                zf.write(src, rel)
        for p in evidence_files:
            zf.write(p, f"reports/scientific-stagec-djangocms-impactplan-v2-costprobe-01/{p.name}")

    size = OUT.stat().st_size
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    with zipfile.ZipFile(OUT) as zf:
        names = zf.namelist()
    print("EVIDENCE_ZIP_READY")
    print(f"EVIDENCE_ZIP_NAME={OUT.name}")
    print(f"EVIDENCE_ZIP_PATH={OUT}")
    print(f"EVIDENCE_ZIP_SIZE_BYTES={size}")
    print(f"EVIDENCE_ZIP_SHA256={digest}")
    print(f"ENTRIES={len(names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())