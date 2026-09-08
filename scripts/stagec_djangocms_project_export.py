#!/usr/bin/env python3
"""Project export ZIP per AGENTS.md mandatory-stop rule (filtered audit export).

Handles the git worktree layout: `.git` is a pointer file; the worktree gitdir
lives under the common repo's `worktrees/<name>/`. The export bundles a merged
`.git/` tree (common dir + current worktree gitdir overlay) so `.git/HEAD`
reflects the current worktree branch and full object history is included.
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
EXCLUDE_PREFIXES = ("dist/_provcheck", "dist/pilot-kaggle-upload", "dist/pilot-repo-cache")
EXCLUDE_SUFFIXES = {".pyc"}


def excluded(rel_parts: tuple[str, ...], rel_str: str) -> bool:
    if any(ex in rel_parts for ex in EXCLUDE_DIRS):
        return True
    if any(rel_str.startswith(p) for p in EXCLUDE_PREFIXES):
        return True
    if rel_str.endswith(".pyc"):
        return True
    return False


def collect_git_entries() -> dict[str, Path]:
    """Merge common .git dir + current worktree gitdir into {zip_rel: src}."""
    git_pointer = PROJECT_DIR / ".git"
    entries: dict[str, Path] = {}

    if git_pointer.is_dir():
        common = git_pointer
        for p in common.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(common).as_posix()
            if rel.startswith("worktrees/"):
                continue
            entries[f".git/{rel}"] = p
    elif git_pointer.is_file():
        pointer = git_pointer.read_text(encoding="utf-8").strip()
        gitdir = Path(pointer.replace("gitdir:", "").strip())
        # Resolve the common git dir via commondir (present in worktree gitdirs)
        common = None
        commondir_file = gitdir / "commondir"
        if commondir_file.is_file():
            rel = commondir_file.read_text(encoding="utf-8").strip()
            cand = (gitdir / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
            if (cand / "objects").is_dir():
                common = cand
        if common is None:
            # fall back to parent-of-worktrees layout: <main>/.git
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
        # overlay current worktree gitdir
        if gitdir.is_dir():
            for p in gitdir.rglob("*"):
                if not p.is_file():
                    continue
                rel = p.relative_to(gitdir).as_posix()
                entries[f".git/{rel}"] = p
        entries[".git"] = git_pointer  # pointer file itself
    return entries


def main() -> int:
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=PROJECT_DIR, capture_output=True, text=True, check=True
    ).stdout.splitlines()

    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    out = PARENT_DIR / f"project-{stamp}.zip"

    git_entries = collect_git_entries()

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        seen: set[str] = set()
        for rel in tracked:
            p = Path(rel)
            if excluded(p.parts, str(p)):
                continue
            full = PROJECT_DIR / p
            if full.is_file() and rel not in seen:
                zf.write(full, rel)
                seen.add(rel)
        for name, src in sorted(git_entries.items()):
            if name in seen:
                continue
            zf.write(src, name)
            seen.add(name)
        for name in ("dist/pilot-kaggle-upload.zip", "dist/pilot-kaggle-upload.zip.sha256"):
            full = PROJECT_DIR / name
            if full.is_file() and name not in seen:
                zf.write(full, name)
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
    print(f"REQUIRED_MISSING={missing} (dist pilot artifacts absent on disk; .git/HEAD expected)")
    print(f"UPLOAD_THIS_FILE={out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())