#!/usr/bin/env python3
"""Mission-10B TRUE LIGHT export (2026-09-26) - targeted allowlist.

LIGHT handoff sufficient for independent review of Mission-10B up to the
reconciliation checkpoint (Harness V3 recommended; ENG oracle ready; P2P-S V3
frozen; P2P-U V3 rediscovery frozen; awaiting GO before cap200/cap400
execution). Includes governance, Harness V3 freeze/spec, Phase-1..4 evidence,
gate, ENG reconciliation, P2P-S/P2P-U membership + rediscovery diffs, source
code, and the tests that validate them. Heavy raw evidence (Phase-1 fulltext
JSONL, per-task phase5 JSON, raw JUnit) is NOT duplicated; it is reproducible
from the frozen runner and referenced by the checkpoints.

Output: project-LIGHT-2026-09-26-<HHMM>.zip in the parent directory.
"""
from __future__ import annotations

import datetime
import hashlib
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
PARENT_DIR = PROJECT_DIR.parent
V3 = "research/wp2/harness_v3_2026-09-26"

INCLUDE = [
    # governance / current state
    "PROGRESS.md",
    "DECISIONS.md",
    "README.md",
    "00_CURRENT_RESEARCH_STATE.md",
    "docs/LIVE_STATUS.json",
    # Mission-10B docs
    "docs/MISSION_10B_HARNESS_V3_IMPACT_DECLARATION_2026-09-26.md",
    "docs/MISSION_10B_PHASE1_ROOTCAUSE_AUDIT_2026-09-26.md",
    "docs/MISSION_10B_PHASE1B_1F_RCA_2026-09-26.md",
    "docs/WP2_HARNESS_V3_FREEZE_2026-09-26.md",
    "docs/MISSION_10A_ENV_TEST_DEPENDENCY_AUDIT_STOP_REPORT_2026-09-26.md",
    # Harness V3 spec (machine-readable)
    f"{V3}/harness_v3_spec.json",
    # Phase-1 RCA machine-readable summaries (NOT the raw fulltext JSONL)
    f"{V3}/phase1_c4_node_attribution.json",
    f"{V3}/phase1_c2_rescue_attribution.json",
    f"{V3}/phase1_hypotheses_verification.json",
    f"{V3}/phase1_p2pu_eng_attribution.json",
    f"{V3}/phase1_summary.json",
    f"{V3}/phase1b_install_failure_audit.json",
    f"{V3}/phase1c_emfile_repro.json",
    f"{V3}/phase1d_db_reuse_rca.json",
    f"{V3}/phase1e_lockfile_audit.json",
    f"{V3}/phase1f_clock_audit.json",
    f"{V3}/phase1f_at_risk_f2p.json",
    # Phase-3 probe + Phase-4 gate
    f"{V3}/phase3_probe_summary.json",
    f"{V3}/gate.json",
    f"{V3}/gate.md",
    # Phase-5 ENG + P2P
    f"{V3}/eng_v3_oracle_ready.json",
    f"{V3}/p2p_s_v3_eng.json",
    f"{V3}/phase5_c4_v3_progress.json",
    # Mission-10B source + tests
    "src/benchmark/wp2/m10b_fulltext.py",
    "src/benchmark/wp2/harness_v3.py",
    "scripts/wp2_m10b_phase1_audit.py",
    "scripts/wp2_m10b_phase1b_install_audit.py",
    "scripts/wp2_m10b_phase1c_emfile_repro.py",
    "scripts/wp2_m10b_phase1d_db_reuse_rca.py",
    "scripts/wp2_m10b_phase1e_lockfile_audit.py",
    "scripts/wp2_m10b_phase1f_clock_audit.py",
    "scripts/wp2_m10b_phase3_probe.py",
    "scripts/wp2_m10b_phase4_gate.py",
    "scripts/wp2_m10b_phase5_c4_v3.py",
    "scripts/wp2_m10b_eng_oracle_ready.py",
    "scripts/wp2_m10b_p2ps_v3_eng.py",
    "scripts/wp2_m10b_p2pu_v3_eng.py",
    "scripts/export_light_project_mission10b.py",
    "tests/unit/wp2/test_m10b_fulltext.py",
    # frozen references (small) needed to verify
    "research/wp2/wp2_p2p_u_v2_rule_freeze_2026-09-25.json",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/summary_dev_v2.json",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/dev_split_v2_2026-09-23.json",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/dev_census_2026-09-23.json",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/harness_v2_freeze_2026-09-23_REVISED.json",
    "src/benchmark/wp2/oracle_semantics_v2.py",
    "src/benchmark/wp2/p2p_inventory_dev_v1.py",
    "src/benchmark/wp2/p2p_u_v2.py",
    "src/benchmark/wp2/oracle_confirmation.py",
    "scripts/wp2_linux_dryrun.py",
    "scripts/wp2_p2p_u_v2_exec.py",
    "scripts/wp2_resource_sampler.py",
]

# Directory prefixes: include ONLY selected files under these (not the whole
# tree, to keep under 50 MB). Selected rediscovery diffs:
INCLUDE_DIRS = []
REDISCOVERY_SELECT = [
    "saleor-rc-2d45b76a52f2",
    "saleor-rc-39b4138e8550",
    "saleor-rc-74538ea00ce9",
    "saleor-rc-82c56bde0e34",
    "saleor-rc-8f76ddc6267f",
    "saleor-rc-9258154b8a0b",
    "saleor-rc-d220843b5418",
    "saleor-rc-e03ee76d2b89",
]
for _tid in REDISCOVERY_SELECT:
    INCLUDE.append(f"{V3}/p2pu_v3_rediscovery_{_tid}.json")


def should_include(rel: str) -> bool:
    if rel in INCLUDE:
        return True
    return any(rel.startswith(prefix) for prefix in INCLUDE_DIRS)


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
        "docs/WP2_HARNESS_V3_FREEZE_2026-09-26.md",
        f"{V3}/harness_v3_spec.json",
        f"{V3}/gate.json",
        f"{V3}/eng_v3_oracle_ready.json",
        f"{V3}/p2p_s_v3_eng.json",
        "src/benchmark/wp2/harness_v3.py",
        "src/benchmark/wp2/m10b_fulltext.py",
        "tests/unit/wp2/test_m10b_fulltext.py",
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
