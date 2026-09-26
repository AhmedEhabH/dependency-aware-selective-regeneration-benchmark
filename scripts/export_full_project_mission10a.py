#!/usr/bin/env python3
"""Mission-10A FULL audit export (2026-09-26).

Filtered audit ZIP per the standing Project Export Rule: ALL git-tracked files,
.git/, dist/pilot-kaggle-upload.zip + .sha256 (if present). Excludes caches and
derived artifacts. Output: project-2026-09-26-<HHMM>.zip in the parent dir.
"""
from __future__ import annotations

import datetime
import hashlib
import subprocess
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
PARENT_DIR = PROJECT_DIR.parent

EXCLUDE_SUFFIXES = (".pyc", ".pyo", ".pyd")
EXCLUDE_PARTS = (
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "__pycache__",
    ".opencode",
    ".venv",
    "node_modules",
)


def should_exclude(rel: str) -> bool:
    if rel.endswith(EXCLUDE_SUFFIXES):
        return True
    parts = rel.split("/")
    return any(seg in EXCLUDE_PARTS for seg in parts)


def main() -> int:
    # Tracked files + .git metadata + dist pilot bundles (if present).
    tracked = subprocess.run(
        ["git", "-C", str(PROJECT_DIR), "ls-files"],
        capture_output=True, text=True, encoding="utf-8", timeout=180, check=True,
    ).stdout.splitlines()

    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    out = PARENT_DIR / f"project-{stamp}.zip"
    kept = dropped = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        # .git (HEAD + refs + objects) - include for provenance
        git_dir = PROJECT_DIR / ".git"
        for p in git_dir.rglob("*"):
            if p.is_file() and not p.name.endswith((".lock",)):
                rel = ".git/" + p.relative_to(git_dir).as_posix()
                zout.write(p, rel)
                kept += 1
        # tracked files
        for rel in sorted(set(tracked)):
            if should_exclude(rel):
                dropped += 1
                continue
            full = PROJECT_DIR / rel
            if full.is_file():
                zout.write(full, rel)
                kept += 1
        # dist pilot bundles (may be archived externally)
        for extra in ("dist/pilot-kaggle-upload.zip", "dist/pilot-kaggle-upload.zip.sha256"):
            full = PROJECT_DIR / extra
            if full.is_file():
                zout.write(full, extra)
                kept += 1

    size = out.stat().st_size
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        bad = z.testzip()

    required = {".git/HEAD", "PROGRESS.md", "docs/MISSION_10A_ENV_TEST_DEPENDENCY_AUDIT_STOP_REPORT_2026-09-26.md"}
    missing = sorted(r for r in required if r not in names)
    has_pilot = any("dist/pilot-kaggle-upload.zip" in n for n in names)
    print("PROJECT_EXPORT_READY")
    print(f"PROJECT_EXPORT_NAME={out.name}")
    print(f"PROJECT_EXPORT_PATH={out}")
    print(f"PROJECT_EXPORT_SIZE_BYTES={size}")
    print(f"PROJECT_EXPORT_SHA256={digest}")
    print(f"entries={kept} kept / {dropped} dropped")
    print(f"testzip={bad or 'PASS'}")
    print(f"missing_required={missing or 'NONE'}")
    print(f"pilot_bundle_present={has_pilot}")
    if not has_pilot:
        print("KNOWN_ARCHIVED_EXPORT_MEMBER_MISSING")
    return 0 if not missing and bad is None else 2


if __name__ == "__main__":
    raise SystemExit(main())