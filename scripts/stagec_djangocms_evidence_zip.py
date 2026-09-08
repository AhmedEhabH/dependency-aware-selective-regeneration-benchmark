#!/usr/bin/env python3
"""Build the compact result-evidence ZIP for the djangoCMS external-validity study."""

from __future__ import annotations
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
STUDY_DIR = PROJECT_DIR / "reports" / "scientific-stagec-djangocms-study-01"
OUT = PROJECT_DIR / "reports" / "STAGEC_DJANGOCMS_STUDY_01_RESULT_EVIDENCE.zip"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=PROJECT_DIR, capture_output=True, text=True).stdout.strip()


def git_evidence() -> str:
    lines = [
        f"branch={git('branch', '--show-current')}",
        f"head={git('rev-parse', 'HEAD')}",
        f"remote_head={git('rev-parse', 'origin/research/djangocms-external-validity-prep-01')}",
        f"parity={'YES' if git('rev-parse','HEAD')==git('rev-parse','origin/research/djangocms-external-validity-prep-01') else 'NO'}",
        f"tree_clean={'YES' if not git('status','--porcelain') else 'NO'}",
        f"wiring_tag={git('rev-parse','--verify','stagec-djangocms-study-wiring-verified-01')}",
        f"wiring_tag_ancestor_of_head={'YES' if subprocess.run(['git','merge-base','--is-ancestor','stagec-djangocms-study-wiring-verified-01','HEAD'],cwd=PROJECT_DIR).returncode==0 else 'NO'}",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    if OUT.is_file():
        OUT.unlink()

    study_files = sorted(p for p in STUDY_DIR.rglob("*") if p.is_file())
    extra_files = [
        PROJECT_DIR / "reports" / "FINAL_BENCHMARK_RESULTS.md",
        PROJECT_DIR / "reports" / "FINAL_BENCHMARK_RESULTS.csv",
        PROJECT_DIR / "reports" / "BENCHMARK_VALIDITY_AND_LIMITATIONS.md",
        PROJECT_DIR / "reports" / "BENCHMARK_REPRODUCIBILITY_INDEX.md",
        PROJECT_DIR / "reports" / "RESEARCH_TRUTH_MATRIX.md",
    ]
    excludes = {
        "workspace",
    }

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in study_files:
            if any(seg in excludes for seg in p.parts):
                continue
            zf.write(p, f"scientific-stagec-djangocms-study-01/{p.name}")
        for p in extra_files:
            if p.is_file():
                zf.write(p, f"reports/{p.name}")
        zf.writestr("GIT_EVIDENCE.txt", git_evidence())

    size = OUT.stat().st_size
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    names = zipfile.ZipFile(OUT).namelist()
    print(f"RESULT_EVIDENCE_ZIP_READY")
    print(f"PATH={OUT}")
    print(f"SIZE_BYTES={size}")
    print(f"SHA256={digest}")
    print(f"ENTRIES={len(names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())