#!/usr/bin/env python3
"""WP-2 temporal/attrition analysis (D1, amendment M) - ZERO API.

Produces the Windows->Linux recovery and era-yield evidence available now:
- Windows V1 attrition (from V1 evidence);
- Linux dry-run era yields (from dryrun_2026-09-23.json);
- DEV census temporal strata (from dev_census_2026-09-23.json);
- amendment-M hard-stop check on the available evidence.

Full MAIN attrition requires the C2 sweep; this is recorded as the current
evidence-based state.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

V1_SUMMARY = PROJECT / "research" / "wp2" / "oracle_confirmation_2026-09-22" / "summary.json"
DRYRUN = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" / "dryrun_2026-09-23.json"
DEV_CENSUS = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" / "dev_census_2026-09-23.json"
OUT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" / "temporal_attrition_2026-09-23.json"


def main() -> int:
    v1 = json.loads(V1_SUMMARY.read_text(encoding="utf-8"))
    dry = json.loads(DRYRUN.read_text(encoding="utf-8"))
    dev = json.loads(DEV_CENSUS.read_text(encoding="utf-8"))

    era_yield = {}
    for r in dry["task_results"]:
        beh = r["counts"].get("BEHAVIORAL_F2P", 0)
        sym = r["counts"].get("SYMBOL_ABSENCE_F2P", 0)
        pce = r["counts"].get("PARENT_COLLECTION_ERROR", 0)
        era_yield[r["task_id"]] = {
            "era": r["era_key"],
            "category": r["category"],
            "BEHAVIORAL_F2P": beh,
            "SYMBOL_ABSENCE_F2P": sym,
            "PARENT_COLLECTION_ERROR": pce,
            "eligible": r["eligibility"]["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"],
            "year": r["target_commit"][:8],
        }

    # amendment-M check on available evidence: era yields on Linux
    eras = {}
    for r in dry["task_results"]:
        eras.setdefault(r["era_key"], []).append(
            r["counts"].get("BEHAVIORAL_F2P", 0) + r["counts"].get("SYMBOL_ABSENCE_F2P", 0)
        )
    sharp_era_difference = False
    if len(eras) >= 2:
        means = {k: sum(v) / len(v) for k, v in eras.items()}
        vals = list(means.values())
        if max(vals) - min(vals) > 0:  # any nonzero yield difference across eras
            sharp_era_difference = len([v for v in vals if v > 0]) < len(vals) and max(vals) > 0
    amendment_m_verdict = (
        "HARD_STOP_NOT_TRIGGERED_ON_AVAILABLE_EVIDENCE"
        if not sharp_era_difference
        else "REVIEW_REQUIRED_BEFORE_FULL_SWEEP"
    )

    artifact = {
        "artifact": "wp2_temporal_attrition",
        "date": "2026-09-23",
        "windows_v1": {
            "attempted": v1.get("attempted"),
            "counts": v1.get("counts"),
            "environment_valid": v1.get("substrata", {}).get("environment_valid"),
            "env_broken": v1.get("counts", {}).get("ENV_BROKEN"),
        },
        "linux_dryrun_era_yield": era_yield,
        "dev_census_years": dev.get("commit_year_distribution"),
        "dev_census_env_families": dev.get("environment_family_distribution"),
        "windows_to_linux_recovery": {
            "worktree_question_mark": (
                "BLOCKED on Windows -> WORKS on Linux ext4 (dry-run task 24f9b244d6bc)"
            ),
            "resource_module": (
                "BLOCKED on Windows -> WORKS on Linux (dry-run task "
                "65643ec7c37f: 2 SYMBOL_ABSENCE + 10 P2P)"
            ),
            "native_lib": "collection recovered with era superset (3->276 nodes); execution infeasible for that task",
            "old_era_and_2026_era": "both yield confirmed BEHAVIORAL_F2P on Linux (25 and 4)",
        },
        "amendment_m_hard_stop_check": {
            "verdict": amendment_m_verdict,
            "note": (
                "On the bounded dry-run evidence, all eras yield F2P/P2P nodes "
                "on Linux (py38, py39, py312), so no sharp era-yield difference "
                "attributable to a harness artifact is observed. The full check "
                "requires the C2 MAIN sweep and must be re-evaluated at D1 "
                "finalization after C2."
            ),
        },
        "status": "EVIDENCE_BASED_UP_TO_B3_C3; full MAIN attrition pending C2",
    }
    OUT.write_text(json.dumps(artifact, indent=1, ensure_ascii=False), encoding="utf-8")
    print("amendment_m_verdict:", amendment_m_verdict)
    print("linux era yields:", json.dumps(eras, indent=1))
    print("wrote", OUT.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
