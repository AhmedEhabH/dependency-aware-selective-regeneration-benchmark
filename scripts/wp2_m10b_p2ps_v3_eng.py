#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 5A: P2P-S V3 ENG extraction + membership diff (19).

Extracts P2P-S from V3 changed-test per-node records using the SAME frozen
definition as P2P-S V1 (stable pass parent+test-patch 3/3 AND stable pass
target 3/3), for each V3 oracle-valid ENG task, and reports the V2->V3
membership diff.

Output: research/wp2/harness_v3_2026-09-26/p2p_s_v3_eng.json
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
P2PS_V1 = PROJECT / "research" / "wp2" / "wp2_dev_p2p_s_v1_2026-09-25.json"

P2PS_V3_VERSION = "p2p-s-v3-eng-2026-09-26"
SPARSE_THRESHOLD = 10


def _now_utc() -> str:
    import datetime
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _sha256(payload: object) -> str:
    import hashlib
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def main() -> int:
    ds = json.loads((V2_ROOT / "dev_split_v2_2026-09-23.json").read_text(encoding="utf-8"))
    eng = set(ds["membership"].get("DEV_TRAIN_ENG", []))
    v2_rows = {}
    for line in (V2_ROOT / "per_task_dev_v2.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        v2_rows[r["task_id"]] = r
    eng_c4 = [t for t in v2_rows if t in eng]

    v1 = json.loads(P2PS_V1.read_text(encoding="utf-8"))
    v1_by_task = {}
    for t in v1.get("tasks", []):
        if t["task_id"] in eng:
            v1_by_task[t["task_id"]] = set(t.get("p2p_s_node_ids", []))

    v3_by_task = {}
    for tid in eng_c4:
        f = OUT_ROOT / f"phase5_c4v3_{tid}.json"
        if not f.exists():
            continue
        rec = json.loads(f.read_text(encoding="utf-8"))
        if rec.get("status") != "DONE":
            continue
        p2p_s = []
        for nr in rec.get("node_records", []):
            t = nr.get("target_outcomes", [])
            p = nr.get("parent_outcomes", [])
            if all(o == "passed" for o in t) and all(o == "passed" for o in p):
                p2p_s.append(nr["node_id"])
        v3_by_task[tid] = sorted(set(p2p_s))

    tasks = []
    for tid in sorted(eng_c4):
        v3_ids = set(v3_by_task.get(tid, []))
        v2_ids = v1_by_task.get(tid, set())
        if not v3_ids and not v2_ids:
            continue
        defined = len(v3_ids) > 0 or len(v2_ids) > 0
        tasks.append({
            "task_id": tid,
            "era": v2_rows[tid].get("era_key"),
            "defined": defined,
            "sparse": 0 < len(v3_ids) < SPARSE_THRESHOLD,
            "v2_count": len(v2_ids),
            "v3_count": len(v3_ids),
            "intersection": sorted(v3_ids & v2_ids),
            "additions_v3": sorted(v3_ids - v2_ids),
            "removals_v2": sorted(v2_ids - v3_ids),
        })

    defined_count = sum(1 for t in tasks if t["defined"])
    sparse_count = sum(1 for t in tasks if t["sparse"])
    membership = {
        "artifact": "p2p_s_v3_eng",
        "version": P2PS_V3_VERSION,
        "created_utc": _now_utc(),
        "definition": "stable pass parent+test-patch 3/3 AND stable pass target 3/3 "
                      "(SAME frozen definition as P2P-S V1; no new semantic rule)",
        "scope": "V3 oracle-valid ENG changed-test per-node records",
        "per_task": tasks,
        "totals": {
            "tasks": len(tasks),
            "defined": defined_count,
            "sparse_lt10": sparse_count,
            "total_v3_nodes": sum(t["v3_count"] for t in tasks),
            "total_v2_nodes": sum(t["v2_count"] for t in tasks),
        },
        "freeze": {
            "membership_sha256": "",
            "note": "ENG P2P-S V3 membership frozen here (19). Zero nodes = UNDEFINED, never automatic PASS.",
        },
    }
    payload = dict(membership)
    membership["freeze"]["membership_sha256"] = _sha256(payload)
    (OUT_ROOT / "p2p_s_v3_eng.json").write_text(
        json.dumps(membership, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[P2P-S] tasks={len(tasks)} defined={defined_count} sparse={sparse_count} "
          f"v3_nodes={membership['totals']['total_v3_nodes']}")
    for t in tasks:
        print(f"  {t['task_id']} v2={t['v2_count']} v3={t['v3_count']} "
              f"add={len(t['additions_v3'])} rem={len(t['removals_v2'])} "
              f"sparse={t['sparse']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
