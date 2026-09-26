#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 5A: P2P-S V3 ENG extraction + membership diff (19).

CORRECTED (2026-09-26, directive): P2P-S V3 population = oracle_valid_union
(from the corrected ENG_V3_ORACLE_READY artifact), NOT all ENG DONE tasks.
V3_DEFINED iff v3_p2p_s_node_count > 0 (exactly 3 parent + 3 target outcomes,
all "passed"); V2 membership is comparison baseline only.

Invariants (STOP if any fails):
  set(P2P-S V3 task IDs) subset of set(oracle_valid_union)
  set(P2P-S V3 task IDs) intersect set(ENV_INSTALL_BLOCKED) == empty
  for every task with v3_count == 0: defined == false

Output: research/wp2/harness_v3_2026-09-26/p2p_s_v3_eng.json (v2, supersedes v1)
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
P2PS_V1 = PROJECT / "research" / "wp2" / "wp2_dev_p2p_s_v1_2026-09-25.json"

P2PS_V3_VERSION = "p2p-s-v3-eng-v2-2026-09-26"
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
    eng_ready = json.loads((OUT_ROOT / "eng_v3_oracle_ready.json").read_text(encoding="utf-8"))
    union = set(eng_ready["oracle_valid_union_task_ids"])
    blocked = set(eng_ready["environment_failed_task_ids"])

    v1 = json.loads(P2PS_V1.read_text(encoding="utf-8"))
    v1_by_task = {}
    for t in v1.get("tasks", []):
        if t["task_id"] in union:
            v1_by_task[t["task_id"]] = set(t.get("p2p_s_node_ids", []))

    v3_by_task = {}
    for tid in union:
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
            if len(t) == 3 and len(p) == 3 and all(o == "passed" for o in t) \
                    and all(o == "passed" for o in p):
                if nr.get("v3_class") == "P2P_ONLY":
                    p2p_s.append(nr["node_id"])
                else:
                    # invariant D: every P2P-S node must have v3_class P2P_ONLY
                    raise RuntimeError(
                        f"[P2P-S] invariant D violated: {tid}::{nr['node_id']} "
                        f"has 3/3 pass both sides but v3_class={nr.get('v3_class')}")
        v3_by_task[tid] = sorted(set(p2p_s))

    tasks = []
    for tid in sorted(union):
        v3_ids = set(v3_by_task.get(tid, []))
        v2_ids = v1_by_task.get(tid, set())
        defined = len(v3_ids) > 0
        tasks.append({
            "task_id": tid,
            "era": eng_ready["per_task_node_counts"].get(tid) and _era(tid),
            "defined": defined,
            "sparse": defined and 0 < len(v3_ids) < SPARSE_THRESHOLD,
            "v3_count": len(v3_ids),
            "v2_count": len(v2_ids),
            "intersection": sorted(v3_ids & v2_ids),
            "additions_v3": sorted(v3_ids - v2_ids),
            "removals_v2": sorted(v2_ids - v3_ids),
        })

    defined_count = sum(1 for t in tasks if t["defined"])
    undefined_count = len(tasks) - defined_count
    sparse_count = sum(1 for t in tasks if t["sparse"])
    total_v3 = sum(t["v3_count"] for t in tasks)

    # invariants
    p2ps_ids = {t["task_id"] for t in tasks}
    inv1 = p2ps_ids.issubset(union)
    inv2 = p2ps_ids.isdisjoint(blocked)
    inv3 = all(t["defined"] == (t["v3_count"] > 0) for t in tasks)
    if not (inv1 and inv2 and inv3):
        raise RuntimeError(
            f"[P2P-S] invariant failure: subset_union={inv1} disjoint_blocked={inv2} "
            f"defined_iff_count={inv3}")

    membership = {
        "artifact": "p2p_s_v3_eng",
        "version": P2PS_V3_VERSION,
        "supersedes": "p2p-s-v3-eng-2026-09-26 (v1; population was all ENG DONE, "
                      "defined rule was v3 OR v2)",
        "created_utc": _now_utc(),
        "definition": "stable pass parent+test-patch 3/3 AND stable pass target 3/3 "
                      "(SAME frozen definition as P2P-S V1; no new semantic rule). "
                      "V3_DEFINED iff v3_p2p_s_node_count > 0.",
        "population": "oracle_valid_union (from eng_v3_oracle_ready.json v2)",
        "per_task": tasks,
        "totals": {
            "population_tasks": len(tasks),
            "defined": defined_count,
            "undefined": undefined_count,
            "sparse_lt10": sparse_count,
            "total_v3_nodes": total_v3,
        },
        "invariants": {
            "subset_oracle_valid_union": inv1,
            "disjoint_env_blocked": inv2,
            "defined_iff_count_gt0": inv3,
        },
        "freeze": {
            "membership_sha256": "",
            "note": "ENG P2P-S V3 membership frozen here (19). Zero nodes = "
                    "UNDEFINED, never automatic PASS.",
        },
    }
    payload = dict(membership)
    membership["freeze"]["membership_sha256"] = _sha256(payload)
    (OUT_ROOT / "p2p_s_v3_eng.json").write_text(
        json.dumps(membership, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[P2P-S] population={len(tasks)} defined={defined_count} "
          f"undefined={undefined_count} sparse={sparse_count} v3_nodes={total_v3}")
    print(f"[P2P-S] invariants subset={inv1} disjoint={inv2} defined_iff={inv3}")
    for t in tasks:
        print(f"  {t['task_id']} v3={t['v3_count']} v2={t['v2_count']} "
              f"add={len(t['additions_v3'])} rem={len(t['removals_v2'])} "
              f"defined={t['defined']} sparse={t['sparse']}")
    return 0


def _era(task_id: str) -> str | None:
    import json as _j
    for line in (V2_ROOT / "per_task_dev_v2.jsonl").read_text(encoding="utf-8").splitlines():
        r = _j.loads(line)
        if r["task_id"] == task_id:
            return r.get("era_key")
    return None


if __name__ == "__main__":
    raise SystemExit(main())
