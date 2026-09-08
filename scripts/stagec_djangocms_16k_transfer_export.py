"""D058 project transfer ZIP (filtered audit export).

Same as stagec_djangocms_project_export.py but additionally EXCLUDES
nested evidence ZIPs, old project ZIPs, handoff ZIPs, and never bundles
external djangoCMS source bytes / caches / scratch (git ls-files only).
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

# Task-mandated transfer exclusions: previous evidence ZIPs, nested old
# project ZIPs, handoff ZIPs. The new D058 diagnostic evidence ZIP is
# delivered separately (compact evidence ZIP artifact #1).
EXCLUDE_ZIP_SUFFIX = ".zip"
EXCLUDE_PATH_FRAGMENTS = (
    "handoff",
)


def excluded(rel_parts: tuple[str, ...], rel_str: str) -> bool:
    if any(ex in rel_parts for ex in EXCLUDE_DIRS):
        return True
    if any(rel_str.startswith(p) for p in EXCLUDE_PREFIXES):
        return True
    if rel_str.endswith(".pyc"):
        return True
    if rel_str.endswith(EXCLUDE_ZIP_SUFFIX):
        return True
    low = rel_str.lower()
    if any(frag in low for frag in EXCLUDE_PATH_FRAGMENTS):
        return True
    return False


def collect_git_entries() -> dict[str, Path]:
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

    size = out.stat().st_size
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    required = [".git/HEAD"]
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())