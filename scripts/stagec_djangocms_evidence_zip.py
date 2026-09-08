#!/usr/bin/env python3
"""Build the CORRECTED compact result-evidence ZIP for the djangoCMS study.

Includes corrected reports, recompute/audit artifacts, output-budget analysis,
ablation proposal, Git state evidence, and raw-evidence immutability hashes.
Excludes: previous ZIPs, handoff ZIPs, external djangoCMS source bytes, caches,
scratch workspaces, nested project exports.
"""

from __future__ import annotations
import hashlib
import subprocess
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
STUDY_DIR = PROJECT_DIR / "reports" / "scientific-stagec-djangocms-study-01"
OUT = PROJECT_DIR / "reports" / "STAGEC_DJANGOCMS_STUDY_01_RESULT_EVIDENCE.zip"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=PROJECT_DIR, capture_output=True, text=True).stdout.strip()


def git_evidence() -> str:
    head = git("rev-parse", "HEAD")
    remote = git("rev-parse", "origin/research/djangocms-external-validity-prep-01")
    lines = [
        f"branch={git('branch', '--show-current')}",
        f"head={head}",
        f"remote_head={remote}",
        f"parity={'YES' if head == remote else 'NO'}",
        f"tree_clean={'YES' if not git('status', '--porcelain') else 'NO'}",
        f"wiring_tag={git('rev-parse', '--verify', 'stagec-djangocms-study-wiring-verified-01')}",
        f"wiring_tag_ancestor_of_head={'YES' if subprocess.run(['git', 'merge-base', '--is-ancestor', 'stagec-djangocms-study-wiring-verified-01', 'HEAD'], cwd=PROJECT_DIR).returncode == 0 else 'NO'}",
        "scientific_results_commit=0c110bb1e42788ea68f0c23e70a729e695153a46 (frozen manifest + 60 raw records)",
        "post_study_correction_commits=06d1dd5 (first STOP_REPORT+ZIP), ddb5f67 (export script), + corrected-closure commit (this pass)",
        "no_main_merge=true",
        "final_tag_not_created=true",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    if OUT.is_file():
        OUT.unlink()

    include = sorted(p for p in STUDY_DIR.rglob("*") if p.is_file())
    extra = [
        PROJECT_DIR / "reports" / "FINAL_BENCHMARK_RESULTS.md",
        PROJECT_DIR / "reports" / "FINAL_BENCHMARK_RESULTS.csv",
        PROJECT_DIR / "reports" / "BENCHMARK_VALIDITY_AND_LIMITATIONS.md",
        PROJECT_DIR / "reports" / "BENCHMARK_REPRODUCIBILITY_INDEX.md",
        PROJECT_DIR / "reports" / "DJANGOCMS_IMPACTPLAN_CAP_ABLATION_PROPOSAL.md",
        PROJECT_DIR / "reports" / "RESEARCH_TRUTH_MATRIX.md",
    ]
    excludes = {"workspace"}

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in include:
            if any(seg in excludes for seg in p.parts):
                continue
            zf.write(p, f"scientific-stagec-djangocms-study-01/{p.name}")
        for p in extra:
            if p.is_file():
                zf.write(p, f"reports/{p.name}")
        zf.writestr("GIT_EVIDENCE.txt", git_evidence())

    size = OUT.stat().st_size
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    names = zipfile.ZipFile(OUT).namelist()
    print("CORRECTED_RESULT_EVIDENCE_ZIP_READY")
    print(f"PATH={OUT}")
    print(f"SIZE_BYTES={size}")
    print(f"SHA256={digest}")
    print(f"ENTRIES={len(names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())