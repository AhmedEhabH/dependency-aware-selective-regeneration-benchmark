#!/usr/bin/env python3
"""TRUE LIGHT export filter (2026-09-20, PARENT-ONLY REPOSITORY MEMORY RESCUE V2).

Takes the full filtered-audit export produced by scripts/export_light_project.py
and removes the documented TRUE LIGHT exclusion categories (same practice as
reports/LIGHT_EXPORT_CONTRIBUTOR_REPORT_2026-09-19.md):

  - .git/*                      git metadata (facts verified separately)
  - *.zip                       tracked zip artifacts (historical submission,
                                evidence bundles; regenerable/reproducible)
  - research/strong-localization-signal/swerank/unit_manifest.json
                                derived/reproducible 21 MB embedding manifest
  - research/locagent-p5b/**/localize.log + loc_trajs.jsonl
  - research/locagent-p5r1/**/localize.log + loc_trajs.jsonl
                                verbose raw agent logs (authoritative numbers
                                live in tracked JSON + reports)

Output: project-LIGHT-<stamp>.zip in the parent directory (<= 50 MB).
No source file is deleted.
"""
from __future__ import annotations

import datetime
import hashlib
import shutil
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
PARENT_DIR = PROJECT_DIR.parent


def should_exclude(rel: str) -> bool:
    low = rel.lower()
    if rel.startswith(".git/"):
        return True
    if low.endswith(".zip"):
        return True
    if rel == "research/strong-localization-signal/swerank/unit_manifest.json":
        return True
    if ("/locagent-p5b/" in rel or "/locagent-p5r1/" in rel) and (
        rel.endswith("localize.log") or rel.endswith("loc_trajs.jsonl")
    ):
        return True
    return False


def main() -> int:
    # The full audit export (must be re-run after commit to reflect HEAD).
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
    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if should_exclude(item.filename):
                dropped += 1
                continue
            zout.writestr(item, zin.read(item.filename))
            kept += 1

    size = out.stat().st_size
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
    print("LIGHT_EXPORT_READY")
    print(f"SOURCE={src.name}")
    print(f"LIGHT_EXPORT_NAME={out.name}")
    print(f"LIGHT_EXPORT_PATH={out}")
    print(f"LIGHT_EXPORT_SIZE_BYTES={size}")
    print(f"LIGHT_EXPORT_MB={round(size / 1e6, 2)}")
    print(f"LIGHT_EXPORT_SHA256={digest}")
    print(f"ENTRIES_KEPT={kept} ENTRIES_DROPPED={dropped}")
    print(f"HAS_HEAD={'.git/HEAD' in names}")
    print(f"HAS_PILOT_ZIP={'dist/pilot-kaggle-upload.zip' in names}")
    print("WITHIN_50MB=" + str(size <= 50_000_000))
    return 0 if size <= 50_000_000 else 2


if __name__ == "__main__":
    raise SystemExit(main())