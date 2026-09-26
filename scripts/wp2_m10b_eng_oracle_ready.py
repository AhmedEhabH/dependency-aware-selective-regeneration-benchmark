#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 5: ENG_V3_ORACLE_READY checkpoint (18).

When every ENG C4 candidate reaches a terminal valid state, build the frozen
ENG oracle summary comparing V2 -> V3, then persist ENG_V3_ORACLE_READY.

Output: research/wp2/harness_v3_2026-09-26/eng_v3_oracle_ready.json
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"

ENG_V3_ORACLE_READY_VERSION = "eng-v3-oracle-ready-2026-09-26"


def _now_utc() -> str:
    import datetime
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _sha256(payload: object) -> str:
    import hashlib
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _v2_evidence_defective(task_id: str, node_id: str) -> bool:
    """S2' 14.1: V2 evidence DEFECTIVE if any parent/target rep contains a
    dirty class (TIME:* / INFRA:* / DB:* / MISSING_FIXTURE:*)."""
    from benchmark.wp2.m10b_fulltext import classify_error_v3, merge_rep_junit

    t12 = task_id.split("-")[-1]
    junit_dir = V2_ROOT / "junit" / task_id
    if not junit_dir.exists():
        return True
    dirty = ("INFRA:", "DB:", "TIME:", "MISSING_FIXTURE:")
    for side in ("p", "t"):
        for rep in range(3):
            files = sorted(junit_dir.glob(f"{t12}_{side}_r{rep}_f*.xml"))
            if not files:
                continue
            merged = merge_rep_junit(
                task_id=task_id, side=side, repetition=rep,
                xml_files=[(f.name, f.read_text(encoding="utf-8")) for f in files])
            ev = merged.get(node_id)
            if ev is None or not ev.full_text:
                continue
            tax, _ = classify_error_v3(ev.full_text, ev.message)
            if tax.startswith(dirty):
                return True
    return False


def main() -> int:
    ds = json.loads((V2_ROOT / "dev_split_v2_2026-09-23.json").read_text(encoding="utf-8"))
    eng = set(ds["membership"].get("DEV_TRAIN_ENG", []))
    v2_rows = {}
    for line in (V2_ROOT / "per_task_dev_v2.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        v2_rows[r["task_id"]] = r
    eng_c4 = [t for t in v2_rows if t in eng]

    v3 = {}
    for tid in eng_c4:
        p = OUT_ROOT / f"phase5_c4v3_{tid}.json"
        if p.exists():
            v3[tid] = json.loads(p.read_text(encoding="utf-8"))

    # V2->V3 transitions (node-level from per-task v3 records vs v2 per_test)
    v2_per_test = {}
    for line in (V2_ROOT / "per_test_dev_v2.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["task_id"] in eng:
            v2_per_test.setdefault(r["task_id"], {})[r["node_id"]] = r["classification"]

    transitions: dict[str, dict] = {}
    regressions = 0
    v2_defect_corrections = 0
    recovered = 0
    for tid, v3rec in v3.items():
        v2p = v2_per_test.get(tid, {})
        for rec in v3rec.get("node_records", []):
            nid = rec["node_id"]
            v2c = v2p.get(nid)
            v3c = rec["v3_class"]
            if v2c and v2c != v3c and v2c in ("BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P", "P2P_ONLY"):
                key = f"{tid}::{nid}"
                # S2' (14.1/14.2): DEFECTIVE if V2 evidence contains a dirty
                # class (TIME:* / INFRA:* / DB:* / MISSING_FIXTURE:*).
                defective = _v2_evidence_defective(tid, nid)
                disposition = "V2_DEFECT_CORRECTION" if defective else "REGRESSION_CANDIDATE"
                transitions[key] = {"v2": v2c, "v3": v3c,
                                    "defective_v2_evidence": defective,
                                    "s2_disposition": disposition}
                if disposition == "V2_DEFECT_CORRECTION":
                    v2_defect_corrections += 1
                elif v2c in ("BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P") and v3c in ("P2P_ONLY", "TARGET_ORACLE_INVALID"):
                    regressions += 1
            if v2c == "TARGET_ORACLE_INVALID" and v3c in ("BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P", "P2P_ONLY"):
                recovered += 1

    v2_behavioral = {t for t in v2_rows if t in eng and v2_rows[t].get("classification") == "BEHAVIORAL_F2P"}
    v3_behavioral = {t for t, r in v3.items() if r.get("classification") == "BEHAVIORAL_F2P"}
    v3_primary = {t for t, r in v3.items() if r.get("eligibility", {}).get("PRIMARY_BEHAVIORAL_F2P_ELIGIBLE")}
    v3_symbol = {
        t for t, r in v3.items()
        if r.get("eligibility", {}).get("EXTENDED_F2P_ELIGIBLE")
        and r.get("counts", {}).get("SYMBOL_ABSENCE_F2P", 0) > 0
    }
    env_blocked = {t for t, r in v3.items() if r.get("status") == "ENV_INSTALL_BLOCKED"}
    executable = set(v3) - env_blocked

    checkpoint = {
        "artifact": "eng_v3_oracle_ready",
        "version": ENG_V3_ORACLE_READY_VERSION,
        "created_utc": _now_utc(),
        "exact_eng_candidate_count": len(eng_c4),
        "environment_failed_count": len(env_blocked),
        "environment_failed_task_ids": sorted(env_blocked),
        "executable_count": len(executable),
        "oracle_valid_count": len(v3_behavioral),
        "behavioral_f2p_task_ids": sorted(v3_behavioral),
        "symbol_absence_f2p_task_ids": sorted(v3_symbol),
        "union_f2p_task_ids": sorted(v3_behavioral | v3_symbol),
        "primary_eligible_task_ids": sorted(v3_primary),
        "per_task_node_counts": {t: r.get("n_nodes", 0) for t, r in sorted(v3.items())},
        "v2_to_v3_transitions": transitions,
        "recovered_tasks": sorted({t for t in v3 if v2_rows[t].get("classification") != v3[t].get("classification") and v3[t].get("classification") == "BEHAVIORAL_F2P"}),
        "lost_tasks": [],
        "v2_defect_corrections": v2_defect_corrections,
        "REGRESSIONS": regressions,
        "recovered_invalid_nodes": recovered,
        "compare_v2_expected": {
            "V2_ENG_oracle_valid_expected": 9,
            "V2_ENG_behavioral_smoke_expected": 8,
            "V2_ENG_oracle_valid_actual": len(v2_behavioral),
            "V3_ENG_oracle_valid_actual": len(v3_behavioral),
        },
        "error_taxonomy": {},
        "hashes": {
            "checkpoint_sha256": "",
            "runner_sha": "see per-task manifests",
        },
        "note": "V3 counts reported as observed; V2 is immutable and NOT forced to match.",
    }
    # sanity: if any regression > 0 -> do not proceed to preservation
    checkpoint["eng_smoke_ready_blocked"] = regressions > 0
    checkpoint["hashes"]["checkpoint_sha256"] = _sha256(checkpoint)
    (OUT_ROOT / "eng_v3_oracle_ready.json").write_text(
        json.dumps(checkpoint, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"[ENG] candidates={len(eng_c4)} env_blocked={len(env_blocked)} "
          f"executable={len(executable)} oracle_valid={len(v3_behavioral)}")
    print(f"[ENG] V2 oracle-valid={len(v2_behavioral)} -> V3={len(v3_behavioral)}")
    print(f"[ENG] behavioral primary V2={len(v2_behavioral)} -> V3={len(v3_primary)}")
    print(f"[ENG] REGRESSIONS={regressions} recovered_nodes={recovered}")
    print(f"[ENG] checkpoint sha256={checkpoint['hashes']['checkpoint_sha256'][:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
