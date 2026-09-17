#!/usr/bin/env python3
"""LIGHT project export (P2 Phase-1 closure, 2026-09-18).

Follows the AGENTS.md Project Export Rule:
- INCLUDE: all `git ls-files` tracked files, `.git/`, and the git-ignored but
  on-disk `dist/pilot-kaggle-upload.zip` + `.sha256` sidecar.
- EXCLUDE: `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `__pycache__/`,
  `*.pyc`, `.opencode/node_modules/`, `dist/_provcheck*`, extracted
  `dist/pilot-kaggle-upload/`, `dist/pilot-repo-cache/` (and other heavy
  git-ignored runtime dirs: locagent-*, real-commit-cache, pilot-repo-cache).
- Verified: `.git/HEAD`, `dist/pilot-kaggle-upload.zip`, `.sha256` present.
"""

from __future__ import annotations

import datetime
import hashlib
import subprocess
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
PARENT_DIR = PROJECT_DIR.parent

EXCLUDE_DIRS = {
    ".mypy_cache", ".ruff_cache", ".pytest_cache", "__pycache__",
    "node_modules",
}
EXCLUDE_PATH_FRAGMENTS = (
    "dist/_provcheck",
    "dist/_provcheck_m",
    "dist/pilot-kaggle-upload/",
    "dist/pilot-repo-cache/",
    "dist/locagent-repo/",
    "dist/locagent-venv/",
    "dist/real-commit-cache/",
)
EXCLUDE_SUFFIXES = {".pyc"}


def excluded(rel_str: str) -> bool:
    parts = Path(rel_str).parts
    if any(ex in parts for ex in EXCLUDE_DIRS):
        return True
    low = rel_str.lower()
    if any(low.startswith(frag) for frag in EXCLUDE_PATH_FRAGMENTS):
        return True
    if rel_str.endswith(tuple(EXCLUDE_SUFFIXES)):
        return True
    return False


def collect_git_entries() -> dict[str, Path]:
    git_pointer = PROJECT_DIR / ".git"
    entries: dict[str, Path] = {}
    if git_pointer.is_dir():
        for p in git_pointer.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(git_pointer).as_posix()
            if rel.startswith("worktrees/"):
                continue
            entries[f".git/{rel}"] = p
    elif git_pointer.is_file():
        gitdir = Path(git_pointer.read_text(encoding="utf-8").strip().replace("gitdir:", "").strip())
        common = None
        commondir_file = gitdir / "commondir"
        if commondir_file.is_file():
            rel = commondir_file.read_text(encoding="utf-8").strip()
            cand = (gitdir / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
            if (cand / "objects").is_dir():
                common = cand
        if common is None:
            cand = gitdir.parent if gitdir.parent.name == ".git" else gitdir.parent.parent
            if (cand / "objects").is_dir():
                common = cand
            else:
                common = gitdir
        if common.is_dir():
            for p in common.rglob("*"):
                if not p.is_file():
                    continue
                rel = p.relative_to(common).as_posix()
                if rel.startswith("worktrees/"):
                    continue
                entries[f".git/{rel}"] = p
        if gitdir.is_dir():
            for p in gitdir.rglob("*"):
                if not p.is_file():
                    continue
                rel = p.relative_to(gitdir).as_posix()
                entries[f".git/{rel}"] = p
        entries[".git"] = git_pointer
    return entries


def main() -> int:
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=PROJECT_DIR, capture_output=True, text=True, check=True
    ).stdout.splitlines()

    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    out = PARENT_DIR / f"project-{stamp}.zip"

    # Git-ignored but REQUIRED by the AGENTS.md rule (present on disk).
    extra: list[tuple[str, Path]] = []
    for rel in ("dist/pilot-kaggle-upload.zip", "dist/pilot-kaggle-upload.zip.sha256"):
        p = PROJECT_DIR / rel
        if p.is_file():
            extra.append((rel, p))

    git_entries = collect_git_entries()

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        seen: set[str] = set()
        for rel in tracked:
            if excluded(rel):
                continue
            full = PROJECT_DIR / rel
            if full.is_file() and rel not in seen:
                zf.write(full, rel)
                seen.add(rel)
        for rel, src in extra:
            if rel in seen:
                continue
            zf.write(src, rel)
            seen.add(rel)
        for name, src in sorted(git_entries.items()):
            if name in seen:
                continue
            zf.write(src, name)
            seen.add(name)

    size = out.stat().st_size
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    required = [".git/HEAD", "dist/pilot-kaggle-upload.zip", "dist/pilot-kaggle-upload.zip.sha256"]
    present = sorted({r for r in required if r in names})
    missing = sorted(set(required) - set(present))
    print("PROJECT_EXPORT_READY")
    print(f"PROJECT_EXPORT_NAME={out.name}")
    print(f"PROJECT_EXPORT_PATH={out}")
    print(f"PROJECT_EXPORT_SIZE_BYTES={size}")
    print(f"PROJECT_EXPORT_SHA256={digest}")
    print(f"ENTRIES={len(names)}")
    print(f"REQUIRED_PRESENT={present}")
    print(f"REQUIRED_MISSING={missing}")
    print(f"UPLOAD_THIS_FILE={out.name}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())