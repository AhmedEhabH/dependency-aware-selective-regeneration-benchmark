#!/usr/bin/env python3
"""Build the compact djangoCMS ImpactPlan-v2 30-CELL STUDY evidence ZIP.

ZIP: reports/STAGEC_DJANGOCMS_IMPACTPLAN_V2_STUDY_EVIDENCE.zip

Contents (task artifact #1): the complete 30-cell ImpactPlan-v2 study evidence
(per-run JSON + raw responses + SHA sidecars + checkpoints + metrics + gates +
parity + manifest), the results report/CSV, the implementation, tests, mapping
artifact, design note, and mathematical design note. The project transfer ZIP
is built separately (project export rule).
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

STUDY_ID = "scientific-stagec-djangocms-impactplan-v2-01"
EVIDENCE_DIR = PROJECT_DIR / "reports" / STUDY_ID
OUT = PROJECT_DIR / "reports" / "STAGEC_DJANGOCMS_IMPACTPLAN_V2_STUDY_EVIDENCE.zip"

ENTRIES: list[str] = [
    "reports/DJANGOCMS_IMPACTPLAN_V2_RESULTS.md",
    "reports/DJANGOCMS_IMPACTPLAN_V2_RESULTS.csv",
    "reports/DJANGOCMS_IMPACTPLAN_V2_DESIGN.md",
    "docs/RISK_AWARE_SPARSE_IMPACT_SELECTION_MODEL.md",
    "src/benchmark/selection/impact_planner_v2.py",
    "tests/unit/selection/test_impact_plan_v2.py",
    "scripts/stagec_djangocms_impactplan_v2_study_execute.py",
    "scripts/stagec_djangocms_impactplan_v2_parity_check.py",
    "benchmark_data/external_validity/impactplan_v2_candidate_id_map.json",
]


def main() -> int:
    if not EVIDENCE_DIR.is_dir():
        raise FileNotFoundError(EVIDENCE_DIR)

    def walk(p: Path) -> list[Path]:
        if p.is_file():
            return [p]
        return sorted(q for q in p.rglob("*") if q.is_file())

    evidence_files = walk(EVIDENCE_DIR)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in ENTRIES:
            src = PROJECT_DIR / rel
            if src.is_file():
                zf.write(src, rel)
        for p in evidence_files:
            zf.write(p, f"reports/{STUDY_ID}/{p.relative_to(EVIDENCE_DIR).as_posix()}")

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