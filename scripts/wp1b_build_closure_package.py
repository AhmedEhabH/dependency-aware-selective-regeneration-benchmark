#!/usr/bin/env python3
"""Build the WP-1a/WP-1b scientific closure export package.

Copies the closure evidence into
exports/WP1A_WP1B_SCIENTIFIC_CLOSURE_2026-09-21/ and writes MANIFEST.json,
SHA256SUMS.txt, and git_provenance.txt.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT = _PROJECT_DIR / "exports" / "WP1A_WP1B_SCIENTIFIC_CLOSURE_2026-09-21"

FILES = [
    "docs/WP1A_WP1B_SCIENTIFIC_CLOSURE_STOP_REPORT_2026-09-21.md",
    "docs/WP1A_WP1B_SCIENTIFIC_CLOSURE_IMPACT_DECLARATION_2026-09-21.md",
    "docs/WP1B_KNOB_REGISTRY_2026-09-21.md",
    "docs/WP1B_NI_MARGIN_DECISION_REQUIRED_2026-09-21.md",
    "docs/WP1B_AGENT_COMPLETION_CAP_PROVENANCE_2026-09-21.md",
    "docs/WP1B_AGENT_COMPLETION_CAP_AMENDMENT_2026-09-21.md",
    "docs/WP1B_AGENT_LOOP_TERMINATION_SEMANTICS_2026-09-21.md",
    "docs/WP1B_VARIANCE_SUBSTUDY_PREREGISTRATION_2026-09-21.md",
    "docs/WP1B_PROVIDER_PRICING_PREFLIGHT_2026-09-21.md",
    "docs/WP1B_CALIBRATION_3_GATE_2026-09-21.md",
    "docs/WP1A_INTEGRATION_CLOSURE_2026-09-21.md",
    "artifacts/wp1a_wp1b_scientific_closure_2026-09-21.json",
    "artifacts/wp1a_wp1b_closure_recomputation.json",
    "artifacts/wp1b_completion_cap_truncation_evidence.json",
    "artifacts/wp1b_ci_decision_rule_preregistration_2026-09-21.json",
    "artifacts/wp1b_variance_substudy_preregistration_2026-09-21.json",
    "artifacts/wp1b_provider_pricing_preflight_2026-09-21.json",
    "artifacts/wp1b_calibration_gate.json",
    "research/wp1a/wp1a_acceptance_report.json",
    "research/wp1a/wp1a_independent_audit.json",
    "research/wp1a/wp1_main_50_manifest.json",
    "research/wp1a/wp1_calibration_3_manifest.json",
    "research/wp1a/wp1_rederivation_verification.json",
    "research/wp1a/sip_scientific_model_provenance.json",
    "research/wp1a/sip_rmcss_per_task_predictions.json",
    "research/wp1a/sip_rmcss_per_task_predictions.sha256",
    "docs/WP1_REPOSITORY_AGENT_SELECTION_ONLY_BASELINE_DRAFT.md",
    "docs/STATISTICAL_ANALYSIS_PLAN.md",
    "docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md",
    "docs/WP1A_IMPACT_DECLARATION_2026-09-21.md",
    "PROGRESS.md",
    "DECISIONS.md",
]


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    audit_dir = OUT / "independent_audit_packet"
    audit_dir.mkdir(parents=True, exist_ok=True)
    for f in ("README_AUDITOR.md", "acceptance_criteria.json",
              "artifact_manifest.json", "sha256sums.txt", "recompute_instructions.md"):
        shutil.copy(_PROJECT_DIR / "exports" / "wp1a_independent_audit_packet_2026-09-21" / f,
                    audit_dir / f)

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
    for p in sorted(audit_dir.iterdir()):
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        sha_lines.append(f"{digest}  independent_audit_packet/{p.name}")

    git_log = subprocess.run(
        ["git", "log", "--oneline", "-40"], cwd=_PROJECT_DIR,
        capture_output=True, text=True, check=True).stdout
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=_PROJECT_DIR,
        capture_output=True, text=True, check=True).stdout.strip()
    provenance = f"HEAD={head}\n\n{git_log}"
    (OUT / "git_provenance.txt").write_text(provenance, encoding="utf-8")

    package_manifest = {
        "package": "WP1A_WP1B_SCIENTIFIC_CLOSURE_2026-09-21",
        "date": "2026-09-21",
        "head_commit": head,
        "files": manifest,
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(package_manifest, indent=1), encoding="utf-8")
    (OUT / "SHA256SUMS.txt").write_text("\n".join(sha_lines) + "\n", encoding="utf-8")

    print(f"closure package written: {OUT} ({sum(1 for _ in OUT.iterdir())} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())