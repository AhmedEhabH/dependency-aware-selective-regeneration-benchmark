#!/usr/bin/env python3
"""Build the WP-1b preflight-freeze export package (B8).

Copies the WP-1b preflight-freeze evidence into
exports/WP1B_PREFLIGHT_FREEZE_2026-09-21/ and writes MANIFEST.json,
SHA256SUMS.txt, and git_provenance.txt (the TRUE LIGHT export contains these
members, satisfying B8.5).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT = _PROJECT_DIR / "exports" / "WP1B_PREFLIGHT_FREEZE_2026-09-21"

FILES = [
    "docs/WP1B_PREFLIGHT_FREEZE_STOP_REPORT_2026-09-21.md",
    "docs/WP1B_NI_MARGIN_FROZEN_2026-09-21.md",
    "docs/WP1B_POWER_AND_SAMPLE_SIZE_2026-09-21.md",
    "docs/WP1B_AGENT_BASELINE_DISCLOSURE_2026-09-21.md",
    "docs/KNOWN_TEST_FAILURES_2026-09-21.md",
    "research/wp1b/wp1b_ni_margin_frozen.json",
    "research/wp1b/wp1b_decision_rules_v2.json",
    "research/wp1b/wp1b_frozen_agent_protocol_v2.json",
    "research/wp1b/wp1b_budget_model_v2.json",
    "research/wp1b/wp1b_main_297_manifest.json",
    "research/wp1b/wp1b_main_150_manifest.json",
    "research/wp1b/wp1b_main_50_manifest.json",
    "research/wp1b/wp1b_exploratory_prereg.json",
    "research/wp1b/wp1b_appendix_r_agreement.json",
    "artifacts/known_test_failures_2026-09-21.json",
    "artifacts/wp1b_calibration_gate.json",
    "artifacts/wp1b_ci_decision_rule_preregistration_2026-09-21.json",
    "artifacts/wp1b_variance_substudy_preregistration_2026-09-21.json",
    "research/wp1a/wp1_calibration_3_manifest.json",
    "research/wp1a/wp1_main_50_manifest.json",
    "research/wp1a/wp1a_frozen_agent_protocol.json",
    "research/wp1a/wp1a_budget_model.json",
    "research/wp1a/wp1a_shared_scorer_schema.json",
    "research/wp1a/wp1a_accounting_schema.json",
    "research/wp1a/wp1a_intent_parity.json",
    "research/wp1a/wp1a_cost_quality_categories.json",
    "START_HERE_CURRENT_2026-09-21.md",
    "PROGRESS.md",
    "DECISIONS.md",
]


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    audit_v2 = OUT / "independent_audit_packet_v2"
    audit_v2.mkdir(parents=True, exist_ok=True)
    for f in ("README_AUDITOR.md", "acceptance_criteria.json",
              "artifact_manifest.json", "sha256sums.txt", "recompute_instructions.md"):
        src = _PROJECT_DIR / "exports" / "wp1a_independent_audit_packet_2026-09-21_v2" / f
        shutil.copy(src, audit_v2 / f)

    manifest: dict[str, dict] = {}
    sha_lines: list[str] = []
    for rel in FILES:
        src = _PROJECT_DIR / rel
        if not src.is_file():
            print(f"WARN missing: {rel}")
            continue
        dst = OUT / rel.replace("/", "__")
        shutil.copy(src, dst)
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        size = src.stat().st_size
        manifest[rel] = {"sha256": digest, "size_bytes": size}
        sha_lines.append(f"{digest}  {dst.name}")
    for p in sorted(audit_v2.iterdir()):
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        sha_lines.append(f"{digest}  independent_audit_packet_v2/{p.name}")

    git_log = subprocess.run(
        ["git", "log", "--oneline", "-40"], cwd=_PROJECT_DIR,
        capture_output=True, text=True, check=True).stdout
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=_PROJECT_DIR,
        capture_output=True, text=True, check=True).stdout.strip()
    provenance = f"HEAD={head}\n\n{git_log}"
    (OUT / "git_provenance.txt").write_text(provenance, encoding="utf-8")

    package_manifest = {
        "package": "WP1B_PREFLIGHT_FREEZE_2026-09-21",
        "date": "2026-09-21",
        "head_commit": head,
        "files": manifest,
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(package_manifest, indent=1), encoding="utf-8")
    (OUT / "SHA256SUMS.txt").write_text("\n".join(sha_lines) + "\n", encoding="utf-8")

    print(f"preflight-freeze package written: {OUT} ({sum(1 for _ in OUT.iterdir())} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
