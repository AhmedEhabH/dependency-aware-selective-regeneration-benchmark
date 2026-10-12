"""M17 D12 — build the project-light LIGHT zip (ZERO API, offline).

Includes: mission artifacts, final git diff, commit/tag/remote verification,
and all edited documentation files. Excludes caches/environments/weights.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "research" / "documentation-hygiene-r1"
STAMP = datetime.now().strftime("%Y-%m-%d-%H%M")
ZIP_PATH = ROOT.parent / f"project-light-year-{STAMP}.zip"

INCLUDES = [
    # mission artifacts
    "research/documentation-hygiene-r1/DOCUMENTATION_PROVENANCE_CENSUS.csv",
    "research/documentation-hygiene-r1/DOCUMENTATION_PROVENANCE_CENSUS.md",
    "research/documentation-hygiene-r1/DOCUMENT_CLASSIFICATION.csv",
    "research/documentation-hygiene-r1/DOCUMENTATION_MUTATION_PLAN.csv",
    "research/documentation-hygiene-r1/BENCHMARK_MODEL_REGISTRY.md",
    "research/documentation-hygiene-r1/BENCHMARK_MODEL_REGISTRY.json",
    "research/documentation-hygiene-r1/SCIENTIFIC_INVARIANCE_RECEIPT.json",
    "research/documentation-hygiene-r1/DOCUMENTATION_HYGIENE_REPORT.md",
    # edited documentation files
    "README.md",
    "START_HERE_CURRENT_2026-09-21b.md",
    "PROGRESS.md",
    "00_CURRENT_RESEARCH_STATE.md",
    "docs/CLAIM_REGISTRY.md",
    "docs/LIVE_STATUS.json",
    "docs/RESEARCH_STATUS_2026-10-02.md",
    # supporting scripts
    "scripts/m17_gen_doc_hygiene_artifacts.py",
    "scripts/m17_review_rewrites.py",
    "scripts/m17_p2p_f2p_tests.py",
    "scripts/m17_invariance_audit.py",
    "scripts/m17_build_light.py",
]

EXCLUDE_SUFFIXES = (b".pyc",)
EXCLUDE_DIRS = {".mypy_cache", ".ruff_cache", ".pytest_cache", "__pycache__", ".git"}


def git(cmd: list[str]) -> str:
    return subprocess.run(["git", *cmd], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout


def collect() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for rel in INCLUDES:
        p = ROOT / rel
        if p.is_file():
            files[rel] = p.read_bytes()
    # final git diff (unstaged + staged vs HEAD)
    files["m17/final_git_diff.patch"] = git(["diff", "HEAD"]).encode("utf-8")
    # verification records
    files["m17/commit_verification.txt"] = (
        "BRANCH=" + git(["branch", "--show-current"]).strip() + "\n"
        "HEAD=" + git(["rev-parse", "HEAD"]).strip() + "\n"
        "ORIGIN_HEAD="
        + git(["rev-parse", "origin/parallel/documentation-provenance-hygiene-2026-10-12"]).strip()
        + "\n"
        "TAG=" + git(["rev-parse", "m17-documentation-provenance-hygiene-r1-2026-10-12"]).strip() + "\n"
        "TAG_PEEL=" + git(["rev-list", "-n", "1", "m17-documentation-provenance-hygiene-r1-2026-10-12"]).strip() + "\n"
        "TREE_CLEAN=" + ("YES" if not git(["status", "--porcelain"]).strip() else "NO") + "\n"
    ).encode("utf-8")
    return files


def main() -> int:
    files = collect()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel, data in sorted(files.items()):
            if any(data.endswith(s) for s in EXCLUDE_SUFFIXES):
                continue
            zf.writestr(rel, data)
    size = ZIP_PATH.stat().st_size
    sha = hashlib.sha256(ZIP_PATH.read_bytes()).hexdigest()
    assert size <= 50 * 1024 * 1024, f"LIGHT too large: {size}"
    print("LIGHT_PATH=" + str(ZIP_PATH))
    print(f"LIGHT_BYTES={size}")
    print(f"LIGHT_SHA256={sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
