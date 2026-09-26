#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 5: ENG_V3_ORACLE_READY checkpoint (18) - CORRECTED.

CORRECTION (2026-09-26, directive): oracle_valid semantics must be the UNION of
behavioral and symbol tasks, computed mechanically, never len(behavioral).
V2 baseline reports V2 union and V2 behavioral separately. All recovered/lost
sets are computed as set differences (no hard-coded bookkeeping). A
bookkeeping_corrections section records the dfe77ac1c5dc reclassification
before-state.

Output: research/wp2/harness_v3_2026-09-26/eng_v3_oracle_ready.json
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"

ENG_V3_ORACLE_READY_VERSION = "eng-v3-oracle-ready-v2-2026-09-26"
CLASS_FIELDS = ("BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P", "PARENT_COLLECTION_ERROR",
                "FLAKY", "TARGET_ORACLE_INVALID", "P2P_ONLY", "OTHER_REVIEW_REQUIRED")


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


def v3_counts(v3rec: dict) -> dict[str, int]:
    counts = {f: 0 for f in CLASS_FIELDS}
    for nr in v3rec.get("node_records", []):
        c = nr.get("v3_class")
        if c in counts:
            counts[c] += 1
    return counts


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

    # --- populations (mechanical) ---
    v2_behavioral = {t for t in eng if t in v2_rows
                     and v2_rows[t]["counts"].get("BEHAVIORAL_F2P", 0) >= 1}
    v2_symbol = {t for t in eng if t in v2_rows
                 and v2_rows[t]["counts"].get("SYMBOL_ABSENCE_F2P", 0) >= 1}
    v2_union = v2_behavioral | v2_symbol

    v3_behavioral = {t for t, r in v3.items() if v3_counts(r)["BEHAVIORAL_F2P"] >= 1}
    v3_symbol = {t for t, r in v3.items() if v3_counts(r)["SYMBOL_ABSENCE_F2P"] >= 1}
    v3_union = v3_behavioral | v3_symbol
    v3_overlap = v3_behavioral & v3_symbol
    v3_symbol_only = v3_symbol - v3_behavioral
    v3_primary = {t for t in v3_union
                  if v3[t].get("eligibility", {}).get("PRIMARY_BEHAVIORAL_F2P_ELIGIBLE")}
    env_blocked = {t for t, r in v3.items() if r.get("status") == "ENV_INSTALL_BLOCKED"}
    executable = set(v3) - env_blocked

    # --- transitions (S2' defective-evidence rule) ---
    v2_per_test = {}
    for line in (V2_ROOT / "per_test_dev_v2.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["task_id"] in eng:
            v2_per_test.setdefault(r["task_id"], {})[r["node_id"]] = r["classification"]

    transitions = {}
    regressions = 0
    v2_defect_corrections = 0
    recovered_nodes = 0
    for tid, v3rec in v3.items():
        v2p = v2_per_test.get(tid, {})
        for rec in v3rec.get("node_records", []):
            nid = rec["node_id"]
            v2c = v2p.get(nid)
            v3c = rec["v3_class"]
            if v2c and v2c != v3c and v2c in ("BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P", "P2P_ONLY"):
                key = f"{tid}::{nid}"
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
                recovered_nodes += 1

    # --- recovered / lost tasks (set differences, mechanical) ---
    recovered_tasks = sorted(v3_union - v2_union)
    lost_tasks = sorted(v2_union - v3_union)

    checkpoint = {
        "artifact": "eng_v3_oracle_ready",
        "version": ENG_V3_ORACLE_READY_VERSION,
        "supersedes": "eng-v3-oracle-ready-2026-09-26 (v1; behavioral-only oracle-valid defn)",
        "created_utc": _now_utc(),
        "exact_eng_candidate_count": len(eng_c4),
        "environment_failed_count": len(env_blocked),
        "environment_failed_task_ids": sorted(env_blocked),
        "executable_count": len(executable),
        "behavioral_task_ids": sorted(v3_behavioral),
        "behavioral_count": len(v3_behavioral),
        "symbol_task_ids": sorted(v3_symbol),
        "symbol_count": len(v3_symbol),
        "behavioral_intersect_symbol": sorted(v3_overlap),
        "overlap_count": len(v3_overlap),
        "symbol_only_task_ids": sorted(v3_symbol_only),
        "symbol_only_count": len(v3_symbol_only),
        "oracle_valid_count": len(v3_union),
        "oracle_valid_union_task_ids": sorted(v3_union),
        "primary_behavioral_count": len(v3_primary),
        "primary_behavioral_task_ids": sorted(v3_primary),
        "per_task_node_counts": {t: v3[t].get("n_nodes", 0) for t in sorted(v3)},
        "v2_to_v3_transitions": transitions,
        "recovered_tasks": recovered_tasks,
        "lost_tasks": lost_tasks,
        "v2_defect_corrections": v2_defect_corrections,
        "REGRESSIONS": regressions,
        "recovered_invalid_nodes": recovered_nodes,
        "compare": {
            "V2_ENG_oracle_valid_union": len(v2_union),
            "V2_ENG_oracle_valid_behavioral": len(v2_behavioral),
            "V2_ENG_behavioral_smoke_expected": 8,
            "V3_ENG_oracle_valid_union": len(v3_union),
            "V3_ENG_oracle_valid_behavioral": len(v3_behavioral),
        },
        "bookkeeping_corrections": [
            {
                "task_id": "saleor-rc-dfe77ac1c5dc",
                "correction": "reclassified DONE -> ENV_INSTALL_BLOCKED "
                              "(whole-file collection failure; no test-level nodes)",
                "before_status": "DONE",
                "before_classification": "NOT_PRIMARY",
                "before_evidence_sha256": "recorded in the commit c9412b9d "
                                          "before reclassification (2026-09-26)",
                "after_status": "ENV_INSTALL_BLOCKED",
                "after_classification": "ENV_INSTALL_BLOCKED",
                "note": "No rerun performed per directive; bookkeeping only.",
            }
        ],
        "hashes": {"checkpoint_sha256": ""},
        "note": "oracle_valid_count = len(behavioral UNION symbol), computed "
                "mechanically. V2 baseline reported as union and behavioral "
                "separately. Recovered/lost are set differences.",
    }
    checkpoint["hashes"]["checkpoint_sha256"] = _sha256(checkpoint)
    (OUT_ROOT / "eng_v3_oracle_ready.json").write_text(
        json.dumps(checkpoint, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"[ENG] candidates={len(eng_c4)} blocked={len(env_blocked)} "
          f"executable={len(executable)}")
    print(f"[ENG] behavioral={len(v3_behavioral)} symbol={len(v3_symbol)} "
          f"overlap={len(v3_overlap)} symbol_only={len(v3_symbol_only)} "
          f"union={len(v3_union)} primary={len(v3_primary)}")
    print(f"[ENG] V2 union={len(v2_union)} (beh {len(v2_behavioral)} + sym "
          f"{len(v2_symbol)}) -> V3 union={len(v3_union)}")
    print(f"[ENG] recovered={recovered_tasks} lost={lost_tasks}")
    print(f"[ENG] REGRESSIONS={regressions} V2_DEFECT_CORRECTIONS={v2_defect_corrections} "
          f"recovered_nodes={recovered_nodes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
