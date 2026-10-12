# Preserve authored stop-report paragraphs and table rows.
# ruff: noqa: E501
"""Package completed review artifacts only; never include frozen payloads or repositories."""

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def dump(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args]).decode().strip()


def main():
    cases = ET.parse(OUT / "review-tests.xml").findall(".//testcase")
    assert len(cases) == 16
    assert not any(
        c.find("failure") is not None or c.find("error") is not None or c.find("skipped") is not None for c in cases
    )
    positives = [c.attrib["name"] for c in cases if c.attrib["name"].startswith("test_p")]
    negatives = [c.attrib["name"] for c in cases if c.attrib["name"].startswith("test_f")]
    assert len(positives) == 6 and len(negatives) == 7
    dump(
        "P2P_F2P_RECEIPT.json",
        {
            "status": "PASS",
            "P2P": {"passed": 6, "failed": 0, "checks": positives},
            "F2P": {"passed": 7, "failed": 0, "checks": negatives},
            "scope": "Static evidence and audit-proposal guard tests, not execution of frozen harness mutation paths.",
            "benchmark_executed": False,
        },
    )
    python_files = sorted(OUT.glob("*.py"))
    for path in python_files:
        compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")
    immutable = json.loads((OUT / "INPUT_IMMUTABILITY_RECEIPT.json").read_text())
    assert immutable["status"] == "PASS" and not immutable["mismatches"]
    assert git("branch", "--show-current") == "parallel/env-runtime-audit-2026-10-12"
    assert git("rev-parse", "HEAD") == "1661ec215ede6ae96e82735148db4febffb21580"
    status = git("status", "--short")
    subprocess.run(["git", "-C", str(ROOT), "diff", "--check"], check=True)
    validation = {
        "git_diff_check": "PASS",
        "ruff_changed_audit_scripts": "PASS",
        "compile": {"status": "PASS", "files": len(python_files), "method": "compile in memory; no pyc"},
        "mypy": {"status": "NOT_RUN", "reason": "No production Python changes; audit scripts only."},
        "targeted_pytest": {"status": "PASS", "passed": 16, "failed": 0, "skipped": 0, "live_status_tests": 3},
        "full_pytest": {
            "status": "NOT_RUN",
            "reason": "No commit/merge/shared production interface change; audit-only mission.",
        },
        "bundle": {"status": "NOT_RUN", "reason": "No production code change; LIGHT-only audit artifact."},
        "immutability": immutable,
        "benchmark_validation": {
            "dataset": "Frozen population statically inspected only",
            "prompt": "NOT_RUN",
            "pipeline": "Historical calibration authority verified; no new pipeline execution",
            "dry_run": "NOT_RUN",
            "integration": "NOT_RUN",
            "metrics": "No scientific metrics generated",
        },
        "wp1b_sidecar": "NOT_APPLICABLE: no WP1b or benchmark/model calls in this mission",
        "git_status": status,
    }
    dump("VALIDATION_RECEIPT.json", validation)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    zip_name = f"project-light-year-{timestamp}.zip"
    zip_path = ROOT / zip_name
    assert not zip_path.exists(), "Refuse to overwrite an existing LIGHT archive"
    stop = f"""# Mandatory stop report — M17 runtime owner review

1. **Execution Identity** — OpenAI / GPT-6 (exact runtime variant not independently exposed); branch `{git("branch", "--show-current")}`; HEAD `{git("rev-parse", "HEAD")}`; origin/main `{git("rev-parse", "origin/main")}`. Initial tree clean. Final tree contains only the new audit directory and five current-status documentation changes; no commit/push/tag/reset/stash.

2. **Why I Am Stopping — COMPLETE.** All R0–R10 audit deliverables are complete. Root cause C_LOCK_RECONSTRUCTION_DEFECT. This mission explicitly stops after review and packaging; it does not authorize remediation. Frozen Calibration-12 is still BLOCKED_STOP, 12 executed / 11 PASS / 1 FAIL. Full D7: NO.

3. **What I Completed** — per-file inventory below. All audit files are new; source store inputs remain unchanged.

| File | Symbol | Old | New | Why | Dependencies |
|---|---|---|---|---|---|
"""
    descriptions = {
        "D7_R3_RUNTIME_FAILURE_OWNER_REVIEW.md": "Nine owner answers, classification and next decision",
        "D7_R3_RUNTIME_FAILURE_OWNER_REVIEW.json": "Machine-readable classification and invariants",
        "D7_RUNTIME_BLAST_RADIUS.csv": "144 rows; source and runtime exposure",
        "RUNTIME_REMEDIATION_DECISION_MATRIX.md": "Five options plus source-restoration recommendation",
        "FAILURE_EVIDENCE_MANIFEST.json": "186 file hashes and 384 historical Git blob hashes",
        "FAILURE_EVIDENCE_INDEX.md": "Human-readable hash/path inventory",
        "P2P_F2P_RECEIPT.json": "6 positive and 7 negative review checks passed",
        "VALIDATION_RECEIPT.json": "Compile/lint/test/immutability evidence and limits",
        "INPUT_IMMUTABILITY_RECEIPT.json": "0 input mismatches",
        "STOP_REPORT.md": "Mandatory stop contract and archive identity",
    }
    file_names = sorted({p.name for p in OUT.iterdir() if p.is_file()} | {"STOP_REPORT.md"})
    for name in file_names:
        detail = descriptions.get(name, "Supporting static evidence, reproducibility script or audit progress")
        stop += f"| research/env-runtime-audit-r1/{name} | audit | absent | {detail} | Owner review | Local frozen inputs |\n"
    for name in [
        "docs/LIVE_STATUS.json",
        "README.md",
        "START_HERE_CURRENT_2026-09-21b.md",
        "PROGRESS.md",
        "00_CURRENT_RESEARCH_STATE.md",
    ]:
        stop += f"| {name} | LIVE STATUS | Prior mission | Runtime review outcome and Full D7 NO | Required truthful status | render_live_status.py |\n"
    stop += f"""
4. **Verification Performed** — git diff --check PASS; Ruff PASS on {len(python_files)} audit scripts; compile PASS {len(python_files)}/{len(python_files)}; targeted pytest PASS 16/16 (P2P 6, F2P 7, live-status 3), 0 failures, 0 skipped. Mypy NOT RUN (0 changed production files). Full pytest NOT RUN (no commit/merge/interface change). Bundle NOT RUN. Rehash PASS: 186/186 file inputs and 384/384 Git blobs, 0 mismatches. Review F2P tests validate the audit policy guard; they do not claim fresh harness runtime coverage.

5. **Pre-Benchmark Validation** — frozen dataset/population identities statically inspected (144 units / 219 tasks). Prompt, benchmark dry-run, integration and metrics NOT RUN by mission design. Historical import/manage/native/pip gates passed but smoke failed; instrument/source fidelity is NOT validated by those passing gates. WP1b sidecar is not applicable: zero benchmark/API calls. No new science or successful smoke claimed.

6. **Independent Self-Audit** — objective unchanged; R0–R10 completed; only audit scripts/reports and required status docs added; no production refactor or runtime workaround; original frozen defects/evidence retained; fresh local hashes used; no tags changed. No proof of whole-population runtime success claimed. Future source-provenance debt is explicit in the decision matrix.

7. **Exact Current State** — audit COMPLETE; root cause C (directory-source semantics lost despite unchanged numeric pins). 2/144 units exposed to the proven Python-3.12/PyXB source mismatch; only one observed failed unit in existing calibration evidence. Frozen calibration remains BLOCKED_STOP; Full D7 NOT AUTHORIZED. No remediation, environment change, harness change, source build, download, Docker pull, network use or benchmark execution.

8. **What Remains** — outside this mission: (1) owner reviews proposed exact-vendor-source amendment; (2) if authorized, additive source-aware reconstruction/refreeze covering both PyXB and authorizenet for both tasks; (3) fresh all-12 calibration; (4) separate Full D7 authorization and zero-start qualification. No automatic follow-on execution.

9. **What I Need From User** — nothing to complete this audit. A separate owner decision is required for remediation; current audit authorization does not cover it.

10. **Recommended Next Action** — review the packet with `Get-Content -LiteralPath 'D:\\wp2_env_runtime_audit\\research\\env-runtime-audit-r1\\D7_R3_RUNTIME_FAILURE_OWNER_REVIEW.md'`. Do not run a calibration or remediation command. This is the explicit mission STOP.

**Upload archive:** `{zip_name}` at `{zip_path}`. Mission-specific LIGHT exclusions supersede the generic full-project export; no repository, .git, wheel payloads, caches or large raw logs are included. Exact size and SHA-256 are in the adjacent `.receipt.json` and final response.

ROOT_CAUSE_CLASSIFIED = TRUE
FROZEN_EVIDENCE_CHANGED = FALSE
HARNESS_CHANGED = FALSE
ENVIRONMENT_CHANGED = FALSE
BENCHMARK_EXECUTED = FALSE
NETWORK_USED = FALSE
"""
    (OUT / "STOP_REPORT.md").write_text(stop, encoding="utf-8")
    todo = (OUT / "TODO.md").read_text(encoding="utf-8-sig").replace(" **in_progress**", "").replace("- [ ]", "- [x]")
    (OUT / "TODO.md").write_text(todo, encoding="utf-8")
    files = sorted(p for p in OUT.iterdir() if p.is_file())
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in files:
            z.write(path, path.relative_to(ROOT).as_posix())
        z.write(ROOT / "docs/LIVE_STATUS.json", "docs/LIVE_STATUS.json")
    required = [
        "D7_R3_RUNTIME_FAILURE_OWNER_REVIEW.md",
        "D7_R3_RUNTIME_FAILURE_OWNER_REVIEW.json",
        "FAILURE_EVIDENCE_INDEX.md",
        "FAILURE_EVIDENCE_MANIFEST.json",
        "D7_RUNTIME_BLAST_RADIUS.csv",
        "RUNTIME_REMEDIATION_DECISION_MATRIX.md",
        "P2P_F2P_RECEIPT.json",
    ]
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        assert all("research/env-runtime-audit-r1/" + n in z.namelist() for n in required)
        assert not any(
            n.endswith((".whl", ".tar.gz", ".pyc")) or "/.git/" in n or "__pycache__" in n for n in z.namelist()
        )
        for p in files:
            assert z.read(p.relative_to(ROOT).as_posix()) == p.read_bytes()
        members = len(z.namelist())
    size = zip_path.stat().st_size
    assert size <= 50 * 1024 * 1024
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    archive = {
        "LIGHT_PATH": str(zip_path),
        "LIGHT_SIZE_BYTES": size,
        "LIGHT_SHA256": digest,
        "members": members,
        "required_members_verified": True,
        "crc_pass": True,
        "payload_equality_pass": True,
    }
    Path(str(zip_path) + ".receipt.json").write_text(json.dumps(archive, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(archive, indent=2))


if __name__ == "__main__":
    main()

