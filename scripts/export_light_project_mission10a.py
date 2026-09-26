#!/usr/bin/env python3
"""Mission-10A TRUE LIGHT export (2026-09-26) - targeted allowlist.

Single LIGHT handoff sufficient for independent review of Mission-10A
(environment test-dependency audit) per Mission-10A section 33. Includes:
PROGRESS.md, DECISIONS.md, Mission-10A STOP report + Impact Declaration, audit
scripts, machine-readable audit artifacts, probe evidence, and the frozen
manifest references/hashes needed to verify conclusions. The heavy frozen
evidence (Mission-09 membership 63.79 MB, DEV inventory 34.20 MB, raw discovery
JSONL, JUnit rescue tarballs) is NOT duplicated - it lives in the existing
Mission-09 LIGHT archive and is referenced by pinned SHA.

error_records.jsonl (38.7 MB) is a REQUIRED Mission-10A machine-readable output
(Mission-10A section 29 item 1) and IS included; the allowlist keeps the total
under ~50 MB.

Output: project-LIGHT-2026-09-26-<HHMM>.zip in the parent directory.
"""
from __future__ import annotations

import datetime
import hashlib
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
PARENT_DIR = PROJECT_DIR.parent
AUDIT_ROOT = "research/wp2/mission10a_env_audit_2026-09-26"

# Explicit allowlist (relative paths or directory prefixes).
INCLUDE = [
    "PROGRESS.md",
    "DECISIONS.md",
    "README.md",
    "00_CURRENT_RESEARCH_STATE.md",
    "docs/LIVE_STATUS.json",
    "docs/MISSION_10A_ENV_TEST_DEPENDENCY_AUDIT_STOP_REPORT_2026-09-26.md",
    "docs/MISSION_10A_ENV_TEST_DEPENDENCY_AUDIT_IMPACT_DECLARATION_2026-09-26.md",
    "docs/WP2_DEV_P2P_PHASE_A_STOP_REPORT_2026-09-25.md",  # Mission-08 errata ref
    "scripts/wp2_m10a_category_exclusion.py",
    "scripts/wp2_m10a_dependency_matrix.py",
    "scripts/wp2_m10a_error_taxonomy.py",
    "scripts/wp2_m10a_plugin_state.py",
    "scripts/wp2_m10a_probe.py",
    "scripts/wp2_m10a_probe_preregister.py",
    "scripts/wp2_m10a_summary.py",
    "scripts/export_light_project_mission10a.py",
    "src/benchmark/wp2/m10a_audit.py",
    "tests/unit/wp2/test_m10a_audit.py",
    # machine-readable audit artifacts (whole dir, incl. error_records.jsonl)
    AUDIT_ROOT + "/",
    # frozen manifest references needed to verify conclusions (small)
    "research/wp2/wp2_p2p_u_v2_rule_freeze_2026-09-25.json",
    "research/wp2/mission07_result_summary_2026-09-25.json",
    "research/wp2/p2p_u_v2_eng_2026-09-25/consolidated_results_2026-09-25.json",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/per_test_dev_v2.jsonl",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/summary_dev_v2.json",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/c4_progress.json",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/c2_progress.json",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/junit_manifest_2026-09-23.tsv",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/c2_artifact_manifest_2026-09-23.tsv",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/dev_census_2026-09-23.json",
    "scripts/wp2_linux_dryrun.py",  # frozen V2 installer logic reference
    "scripts/wp2_p2p_u_v2_exec.py",  # frozen V2 execution reference
    "src/benchmark/wp2/era_resolver.py",  # frozen era images reference
    "src/benchmark/wp2/environment_manager.py",  # frozen env manager reference
    "src/benchmark/wp2/oracle_semantics_v2.py",
    "src/benchmark/wp2/p2p_inventory_dev_v1.py",
    "src/benchmark/wp2/oracle_confirmation.py",
]

# Directory prefixes (include everything under these)
INCLUDE_DIRS = [
    f"{AUDIT_ROOT}/",
]


def should_include(rel: str) -> bool:
    if rel in INCLUDE:
        return True
    for prefix in INCLUDE_DIRS:
        if rel.startswith(prefix):
            return True
    return False


def main() -> int:
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    out = PARENT_DIR / f"project-LIGHT-{stamp}.zip"
    kept = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for rel in INCLUDE:
            if rel.endswith("/"):
                base = PROJECT_DIR / rel
                if not base.is_dir():
                    continue
                for p in sorted(base.rglob("*")):
                    if p.is_file():
                        zout.write(p, p.relative_to(PROJECT_DIR).as_posix())
                        kept += 1
                continue
            full = PROJECT_DIR / rel
            if full.is_file():
                zout.write(full, rel)
                kept += 1

    size = out.stat().st_size
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        bad = z.testzip()

    required = {
        "PROGRESS.md",
        "DECISIONS.md",
        "docs/MISSION_10A_ENV_TEST_DEPENDENCY_AUDIT_STOP_REPORT_2026-09-26.md",
        "src/benchmark/wp2/m10a_audit.py",
        "tests/unit/wp2/test_m10a_audit.py",
        f"{AUDIT_ROOT}/mission10a_summary.json",
        f"{AUDIT_ROOT}/preregistered_materiality_rule.json",
        f"{AUDIT_ROOT}/probe/saleor-rc-74538ea00ce9/probe_results.json",
        f"{AUDIT_ROOT}/error_records.jsonl",
    }
    missing = sorted(r for r in required if r not in names)
    print("LIGHT_EXPORT_READY")
    print(f"LIGHT_EXPORT_NAME={out.name}")
    print(f"LIGHT_EXPORT_PATH={out}")
    print(f"LIGHT_EXPORT_SIZE_BYTES={size}")
    print(f"LIGHT_EXPORT_SHA256={digest}")
    print(f"WITHIN_50MB={size <= 50 * 1024 * 1024}")
    print(f"entries={kept}")
    print(f"testzip={bad or 'PASS'}")
    print(f"missing_required={missing or 'NONE'}")
    return 0 if not missing and bad is None else 2


if __name__ == "__main__":
    raise SystemExit(main())