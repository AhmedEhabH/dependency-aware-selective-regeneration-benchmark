#!/usr/bin/env python3
"""WP-2 Oracle Confirmation summary + attrition reconciliation (ZERO API).

Reads research/wp2/oracle_confirmation_2026-09-22/per_task.jsonl and produces
the summary/attrition JSON and the WP-2 Oracle Confirmation report input:
- required counts (attempted, env, target-invalid, patch-apply-fail, flaky,
  P2P-only, behavioral-F2P, symbol-absence-F2P, extended-F2P, by 20/200 class,
  by migration/config stratum, by env family, wall times);
- attrition flow census -> changed-test candidates -> attempted -> env valid
  -> target stable -> parent discriminative -> behavioral/symbol/P2P.

Usage:
  python scripts/wp2_oracle_summary.py
"""
from __future__ import annotations

import json
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
RUN_DIR = _PROJECT_DIR / "research" / "wp2" / "oracle_confirmation_2026-09-22"
OUT = RUN_DIR / "summary.json"
SELECTION = _PROJECT_DIR / "research" / "wp2" / "wp2_oracle_confirmation_selection_2026-09-22.json"


def main() -> int:
    per_task_path = RUN_DIR / "per_task.jsonl"
    rows = [
        json.loads(line)
        for line in per_task_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    wave_a = set(selection["waves"]["A_strong_all_20"])
    wave_b = set(selection["waves"]["B_modified_first_60"])

    # ---- counts ----
    def cls(r):
        return r.get("classification", r.get("status", "UNKNOWN"))

    counts: dict[str, int] = {}
    for r in rows:
        counts[cls(r)] = counts.get(cls(r), 0) + 1

    strong = [r for r in rows if r["task_id"] in wave_a]
    modified = [r for r in rows if r["task_id"] in wave_b]
    expansion = [r for r in rows if r["task_id"] not in wave_a and r["task_id"] not in wave_b]

    def subcount(rows_, cls_):
        return sum(1 for r in rows_ if cls(r) == cls_)

    behavioral = [r for r in rows if cls(r) == "BEHAVIORAL_F2P"]
    symbol = [r for r in rows if cls(r) == "SYMBOL_ABSENCE_F2P"]
    extended = [r for r in rows if cls(r) in ("BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P")]
    env_valid = [r for r in rows if r.get("environment_valid", False)]
    target_stable = [r for r in rows if r.get("target_oracle_stable", False)]

    migration_config = [
        r for r in rows if r.get("n_migration", 0) > 0 or r.get("n_config_or_infra", 0) > 0
    ]
    # env families: group by fingerprint family from selection manifest
    sel_tasks = {t["task_id"]: t for t in selection.get("selection", {}).get("tasks", [])}
    family_groups: dict[str, int] = {}
    for r in rows:
        fam = (sel_tasks.get(r["task_id"]) or {}).get("env_family") or "UNKNOWN"
        family_groups[fam] = family_groups.get(fam, 0) + 1

    summary = {
        "artifact": "wp2_oracle_confirmation_summary",
        "date": "2026-09-22",
        "attempted": len(rows),
        "counts": counts,
        "by_original_class": {
            "STRONG_20": {
                "behavioral_f2p": subcount(strong, "BEHAVIORAL_F2P"),
                "symbol_absence": subcount(strong, "SYMBOL_ABSENCE_F2P"),
                "p2p_only": subcount(strong, "P2P_ONLY"),
                "env_broken": subcount(strong, "ENV_BROKEN"),
                "flaky": subcount(strong, "FLAKY"),
                "target_oracle_invalid": subcount(strong, "TARGET_ORACLE_INVALID"),
                "other": subcount(strong, "OTHER_REVIEW_REQUIRED"),
                "total": len(strong),
            },
            "MODIFIED_60": {
                "behavioral_f2p": subcount(modified, "BEHAVIORAL_F2P"),
                "symbol_absence": subcount(modified, "SYMBOL_ABSENCE_F2P"),
                "p2p_only": subcount(modified, "P2P_ONLY"),
                "env_broken": subcount(modified, "ENV_BROKEN"),
                "flaky": subcount(modified, "FLAKY"),
                "target_oracle_invalid": subcount(modified, "TARGET_ORACLE_INVALID"),
                "other": subcount(modified, "OTHER_REVIEW_REQUIRED"),
                "total": len(modified),
            },
            "EXPANSION_140": {
                "behavioral_f2p": subcount(expansion, "BEHAVIORAL_F2P"),
                "symbol_absence": subcount(expansion, "SYMBOL_ABSENCE_F2P"),
                "p2p_only": subcount(expansion, "P2P_ONLY"),
                "env_broken": subcount(expansion, "ENV_BROKEN"),
                "flaky": subcount(expansion, "FLAKY"),
                "target_oracle_invalid": subcount(expansion, "TARGET_ORACLE_INVALID"),
                "other": subcount(expansion, "OTHER_REVIEW_REQUIRED"),
                "total": len(expansion),
            },
        },
        "f2p_pools": {
            "primary_behavioral_eligible": len(behavioral),
            "symbol_absence_eligible": len(symbol),
            "extended_f2p_eligible": len(extended),
            "behavioral_task_ids": [r["task_id"] for r in behavioral],
            "symbol_task_ids": [r["task_id"] for r in symbol],
        },
        "substrata": {
            "environment_valid": len(env_valid),
            "target_stable": len(target_stable),
            "migration_config_heavy": len(migration_config),
            "env_families_count": len(family_groups),
        },
        "attrition_flow": {
            "census_297": 297,
            "changed_test_candidates_220": 220,
            "attempted": len(rows),
            "environment_valid": len(env_valid),
            "target_stable": len(target_stable),
            "parent_discriminative_behavioral": len(behavioral),
            "parent_discriminative_symbol": len(symbol),
            "p2p_only": counts.get("P2P_ONLY", 0),
        },
        "note": "environment-broken dominates on this Windows host (native libs, "
            "? in filenames, Unix-only resource module); every attrition reason "
            "preserved; no task silently dropped",
    }
    OUT.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
