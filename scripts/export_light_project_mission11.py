#!/usr/bin/env python3
"""Mission-11 current TRUE LIGHT export (2026-09-27) - targeted allowlist.

LIGHT handoff sufficient for independent technical/scientific review of the
WP-2 Environment Closure V3.1 state (current STOP: HARNESS_V3_DEV_DEPS_GAP)
and the Mission-11 run so far.

Includes: governance, live TODO/progress, decisions, Harness V3 freeze/spec +
source, P2P-U executor/summary, C4 executor, dev-deps audit, current STOP
report, unit tests, hashes/manifests, environment-closure scripts (as they are
created). Raw JUnit XML under p2pu_v3_junit/ is omitted (reproducible); the
unit result JSONs carry the per-file SHA-256 hashes.

Output: project-LIGHT-2026-09-27-<HHMM>.zip in the parent directory.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
PARENT_DIR = PROJECT_DIR.parent
V3 = "research/wp2/harness_v3_2026-09-26"

INCLUDE = [
    # governance / current state
    "AGENTS.md",
    "PROGRESS.md",
    "DECISIONS.md",
    "README.md",
    "00_CURRENT_RESEARCH_STATE.md",
    "docs/LIVE_STATUS.json",
    # Mission-10B / Mission-11 docs
    "docs/WP2_HARNESS_V3_FREEZE_2026-09-26.md",
    "docs/MISSION_10B_HARNESS_V3_IMPACT_DECLARATION_2026-09-26.md",
    "docs/MISSION_11_E2E_SMOKE_IMPACT_DECLARATION_2026-09-26.md",
    "docs/MISSION_11_STOP_HARNESS_V3_DEV_DEPS_GAP_2026-09-27-0145.md",
    "docs/WP2_DEV_SMOKE_DESIGN_DRAFT_2026-09-25.md",
    "docs/WP2_E2E_CAUSAL_DESIGN_V1_2026-09-22.md",
    "docs/WP2_DESIGN_V2_AMENDMENT_FREEZE_2026-09-23.md",
    # Harness V3 spec (machine-readable)
    f"{V3}/harness_v3_spec.json",
    f"{V3}/eng_v3_oracle_ready.json",
    f"{V3}/p2p_s_v3_eng.json",
    f"{V3}/phase5_c4_v3_progress.json",
    f"{V3}/gate.json",
    f"{V3}/gate.md",
    # P2P-U V3 results + progress + summary + audit + env-closure state
    f"{V3}/p2pu_v3_progress.json",
    f"{V3}/p2pu_v3_eng_summary.json",
    f"{V3}/dev_deps_gap_audit.json",
    f"{V3}/env_closure_v31_progress.json",
    f"{V3}/env_closure_v31_protected_hashes_before.json",
    f"{V3}/env_closure_v31_resource_baseline.json",
    # frozen references
    "research/wp2/wp2_p2p_u_v2_rule_freeze_2026-09-25.json",
    "research/wp2/wp2_p2p_u_v2_membership_2026-09-25.json",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/summary_dev_v2.json",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/dev_split_v2_2026-09-23.json",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/dev_census_2026-09-23.json",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/harness_v2_freeze_2026-09-23_REVISED.json",
    "research/wp2/oracle_confirmation_linux_v2_2026-09-23/per_task_dev_v2.jsonl",
    # source
    "src/benchmark/wp2/harness_v3.py",
    "src/benchmark/wp2/m10b_fulltext.py",
    "src/benchmark/wp2/oracle_semantics_v2.py",
    "src/benchmark/wp2/p2p_inventory_dev_v1.py",
    "src/benchmark/wp2/p2p_u_v2.py",
    "src/benchmark/wp2/oracle_confirmation.py",
    "scripts/wp2_linux_dryrun.py",
    "scripts/wp2_m10b_p2pu_v3_eng.py",
    "scripts/wp2_m10b_p2pu_v3_summary.py",
    "scripts/wp2_m10b_dev_deps_gap_audit.py",
    "scripts/wp2_m10b_phase5_c4_v3.py",
    "scripts/wp2_m10b_eng_oracle_ready.py",
    "scripts/wp2_m10b_p2ps_v3_eng.py",
    "scripts/export_light_project_mission11.py",
    "scripts/wp2_p2p_u_v2_exec.py",
    "scripts/wp2_resource_sampler.py",
    # tests
    "tests/unit/wp2/test_m10b_p2pu_v3_hardening.py",
    "tests/unit/wp2/test_m10b_fulltext.py",
    "tests/unit/wp2/test_oracle_semantics_v2.py",
    "tests/unit/wp2/test_p2p_u_v2.py",
    "tests/unit/wp2/test_p2p_u_v2_exec.py",
    "tests/unit/wp2/test_p2p_s_freeze_v1.py",
    "tests/unit/wp2/test_p2p_inventory_dev_v1.py",
]

# All 32 P2P-U V3 unit result JSONs (carry junit_files hashes; no raw XML).
for _cap in ("cap200", "cap400"):
    for _t in [
        "22ec4dab0154", "2d45b76a52f2", "39b4138e8550", "644f33094857",
        "6abb53f3407b", "74538ea00ce9", "823b899757ab", "82c56bde0e34",
        "8f76ddc6267f", "9258154b8a0b", "93b20d78c011", "c3b9e396b07d",
        "d220843b5418", "dc6ac9d252df", "e03ee76d2b89", "e25cf9b4a837",
    ]:
        INCLUDE.append(f"{V3}/p2pu_v3_eng_saleor-rc-{_t}_{_cap}.json")

# All 16 rediscovery records.
for _t in [
    "22ec4dab0154", "2d45b76a52f2", "39b4138e8550", "644f33094857",
    "6abb53f3407b", "74538ea00ce9", "823b899757ab", "82c56bde0e34",
    "8f76ddc6267f", "9258154b8a0b", "93b20d78c011", "c3b9e396b07d",
    "d220843b5418", "dc6ac9d252df", "e03ee76d2b89", "e25cf9b4a837",
]:
    INCLUDE.append(f"{V3}/p2pu_v3_rediscovery_saleor-rc-{_t}.json")

# All 29 C4 V3 per-task records.
for _tid in [f"phase5_c4v3_{n}" for n in [
    "22ec4dab0154", "2a7f13c25908", "2d45b76a52f2", "39b4138e8550",
    "644f33094857", "6abb53f3407b", "6e0a2cfc9287", "6f1f1720fc7c",
    "74538ea00ce9", "7dcf89985e0c", "823b899757ab", "82c56bde0e34",
    "836d01d8429f", "8f76ddc6267f", "9258154b8a0b", "939093a9c65c",
    "93b20d78c011", "9698135fe4fc", "a1a7a223bba2", "a8e6a4dd55fe",
    "ba60125e45a0", "c3b9e396b07d", "c662d3a7e759", "d220843b5418",
    "dc6ac9d252df", "dfe77ac1c5dc", "e03ee76d2b89", "e25cf9b4a837",
    "f73c4e95c828"]]:
    INCLUDE.append(f"{V3}/{_tid}.json")

# Mission-10A audit (prior dep-gap proof) - compact summaries only.
for _f in ["mission10a_summary.json", "dependency_declaration_matrix.json"]:
    INCLUDE.append(f"research/wp2/mission10a_env_audit_2026-09-26/{_f}")

# Phase-1E lockfile audit (historical dev-declared evidence).
INCLUDE.append(f"{V3}/phase1e_lockfile_audit.json")

# Environment-closure scripts (created during this mission; missing = skipped).
ENV_SCRIPTS = [
    "scripts/wp2_env_v31_dep_compiler.py",
    "scripts/wp2_env_v31_old_env_repro.py",
    "scripts/wp2_env_v31_corrected_env.py",
    "scripts/wp2_env_v31_preflight.py",
    "scripts/wp2_env_v31_rerun_scope.py",
]
INCLUDE.extend(ENV_SCRIPTS)


def should_include(rel: str) -> bool:
    return rel in INCLUDE


def main() -> int:
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    out = PARENT_DIR / f"project-LIGHT-{stamp}.zip"
    kept = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for rel in INCLUDE:
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
        "AGENTS.md", "PROGRESS.md", "DECISIONS.md",
        "docs/WP2_HARNESS_V3_FREEZE_2026-09-26.md",
        f"{V3}/harness_v3_spec.json",
        f"{V3}/eng_v3_oracle_ready.json",
        f"{V3}/p2pu_v3_progress.json",
        f"{V3}/dev_deps_gap_audit.json",
        "src/benchmark/wp2/harness_v3.py",
        "scripts/wp2_m10b_p2pu_v3_eng.py",
        "tests/unit/wp2/test_m10b_p2pu_v3_hardening.py",
    }
    missing = sorted(r for r in required if r not in names)
    within = size <= 50 * 1024 * 1024
    manifest = {
        "omitted_heavy_evidence": [
            "research/wp2/harness_v3_2026-09-26/p2pu_v3_junit/** (raw XML; "
            "SHA-256 per file recorded in the unit result JSONs)",
            "research/wp2/harness_v3_2026-09-26/phase1_*_fulltext_records.jsonl",
        ],
        "entries": kept,
        "required_members": sorted(required),
    }
    (PROJECT_DIR / f"{V3}/light_export_manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    print("LIGHT_EXPORT_READY")
    print(f"LIGHT_EXPORT_NAME={out.name}")
    print(f"LIGHT_EXPORT_PATH={out}")
    print(f"LIGHT_EXPORT_SIZE_BYTES={size}")
    print(f"LIGHT_EXPORT_SHA256={digest}")
    print(f"LIGHT_WITHIN_50MB={within}")
    print(f"entries={kept}")
    print(f"testzip={bad or 'PASS'}")
    print(f"missing_required={missing or 'NONE'}")
    return 0 if not missing and bad is None and within else 2


if __name__ == "__main__":
    raise SystemExit(main())
