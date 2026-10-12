"""M17 STOP — create the mandatory filtered project audit ZIP.

Per AGENTS.md Project Export Rule: `project-YYYY-MM-DD-HHmm.zip` in the parent
directory, filtered to tracked files + .git + dist pilot upload artifacts.
Workflow/documentation only — no release/tag/move.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAMP = datetime.now().strftime("%Y-%m-%d-%H%M")
ZIP_PATH = ROOT.parent / f"project-{STAMP}.zip"

EXCLUDE_DIRS = {
    ".mypy_cache", ".ruff_cache", ".pytest_cache", "__pycache__",
    ".opencode/node_modules", "dist/_provcheck",
}
EXCLUDE_SUFFIXES = (".pyc",)
# extracted pilot dir (only the zip + sha256 are included)
EXCLUDE_PATHS = {
    "dist/pilot-kaggle-upload/",
    "dist/pilot-repo-cache/",
}


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if f.strip()]


def main() -> int:
    files = tracked()
    gitdir = Path(
        subprocess.run(
            ["git", "rev-parse", "--git-dir"], cwd=ROOT, capture_output=True,
            text=True, check=True,
        ).stdout.strip()
    )
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        for rel in files:
            if any(rel.startswith(p) for p in EXCLUDE_PATHS):
                continue
            if any(part in EXCLUDE_DIRS for part in Path(rel).parts):
                continue
            if rel.endswith(EXCLUDE_SUFFIXES):
                continue
            p = ROOT / rel
            if p.is_file():
                zf.write(p, rel)
        # include git metadata (HEAD/index + refs tree) from the real git dir
        for extra in ("HEAD", "index"):
            p = gitdir / extra
            if p.is_file():
                zf.write(p, f".git/{extra}")
        refs = gitdir / "refs"
        if refs.is_dir():
            for ref in sorted(refs.rglob("*")):
                if ref.is_file():
                    zf.write(ref, f".git/refs/{ref.relative_to(refs).as_posix()}")
        for dist in ("dist/pilot-kaggle-upload.zip", "dist/pilot-kaggle-upload.zip.sha256"):
            p = ROOT / dist
            if p.is_file():
                zf.write(p, dist)
    size = ZIP_PATH.stat().st_size
    sha = hashlib.sha256(ZIP_PATH.read_bytes()).hexdigest()
    with zipfile.ZipFile(ZIP_PATH) as zf:
        names = set(zf.namelist())
    ok = ".git/HEAD" in names
    if (ROOT / "dist/pilot-kaggle-upload.zip").is_file():
        ok = ok and "dist/pilot-kaggle-upload.zip" in names and "dist/pilot-kaggle-upload.zip.sha256" in names
    print("PROJECT_EXPORT_READY" if ok else "PROJECT_EXPORT_CHECK_FAILED")
    print("PROJECT_EXPORT_NAME=" + ZIP_PATH.name)
    print("PROJECT_EXPORT_PATH=" + str(ZIP_PATH))
    print(f"PROJECT_EXPORT_SIZE_BYTES={size}")
    print(f"PROJECT_EXPORT_SHA256={sha}")
    print("UPLOAD_THIS_FILE=" + ZIP_PATH.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
