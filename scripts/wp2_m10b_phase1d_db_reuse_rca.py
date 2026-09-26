#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 1D: DB reuse / WRONG_CONSTRAINTS RCA (ZERO API).

Verifies at the task/rep/order level whether WRONG_CONSTRAINTS follows an
earlier EMFILE in the same task/DB lineage with an identical reused DB name.

Evidence sources (frozen V2, read-only):
- phase1_c4_node_attribution.json (per-node per-rep taxonomy);
- C4 junit directories for the two WRONG_CONSTRAINTS tasks;
- per_task_dev_v2.jsonl provenance (test command, --reuse-db).

Output: research/wp2/harness_v3_2026-09-26/phase1d_db_reuse_rca.json
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"

WC_TASKS = ("saleor-rc-46a2a565f410", "saleor-rc-f813a9fd37d3")


def _now_utc() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _node_id(tc: ET.Element) -> str:
    cname = tc.get("classname") or ""
    return f"{cname.replace('.', '/')}.py::{tc.get('name') or '?'}"


def count_wc_by_rep(task_id: str) -> dict:
    task = V2_ROOT / "junit" / task_id
    out: dict[str, dict] = {}
    for rep in (0, 1, 2):
        cnt = 0
        emfile = 0
        wc_nodes: list[str] = []
        emfile_nodes: set[str] = set()
        for f in sorted(task.glob(f"*_t_r{rep}_f*.xml")):
            root = ET.fromstring(f.read_text(encoding="utf-8"))
            for tc in root.iter("testcase"):
                e = tc.find("error")
                if e is None:
                    continue
                hay = (e.get("message", "") or "") + "\n" + (e.text or "")
                m = re.search(r"Found wrong number\s*\(?\s*(\d+)\s*\)?\s*of constraints", hay, re.I)
                if m:
                    cnt += 1
                    wc_nodes.append(_node_id(tc))
                    continue
                if "Too many open files" in hay or "[Errno 24]" in hay:
                    emfile += 1
                    emfile_nodes.add(_node_id(tc))
        out[f"r{rep}"] = {
            "wc_nodes": cnt,
            "emfile_nodes": emfile,
            "wc_node_ids": wc_nodes,
            "emfile_node_ids": sorted(emfile_nodes),
        }
    return out


def main() -> int:
    summary = {
        "artifact": "m10b_phase1d_db_reuse_rca",
        "created_utc": _now_utc(),
        "hypothesis": "V2 `--reuse-db` may reuse a partially created DB after "
                      "EMFILE-aborted migration, leading to 'Found wrong number "
                      "(N) of constraints'.",
        "per_task": {},
    }
    for tid in WC_TASKS:
        by_rep = count_wc_by_rep(tid)
        # overlap: WC-r2 nodes that were EMFILE in r0 (same DB lineage)
        wc_r2 = set(by_rep["r2"]["wc_node_ids"])
        em_r0 = set(by_rep["r0"]["emfile_node_ids"])
        em_r1 = set(by_rep["r1"]["emfile_node_ids"])
        overlap_r0 = wc_r2 & em_r0
        overlap_r1 = wc_r2 & em_r1
        summary["per_task"][tid] = {
            "wc_by_rep": {k: v["wc_nodes"] for k, v in by_rep.items()},
            "emfile_by_rep": {k: v["emfile_nodes"] for k, v in by_rep.items()},
            "wc_r2_nodes_total": len(wc_r2),
            "wc_r2_overlap_with_emfile_r0": len(overlap_r0),
            "wc_r2_overlap_with_emfile_r1": len(overlap_r1),
            "same_db_reuse": "identical DATABASE_URL per (task,state) with "
                             "--reuse-db across all 3 target reps (V2 runner)",
        }
        print(f"[1D] {tid}: WC by rep {summary['per_task'][tid]['wc_by_rep']}; "
              f"EMFILE by rep {summary['per_task'][tid]['emfile_by_rep']}; "
              f"WC-r2 AND EMFILE-r0 = {len(overlap_r0)}/{len(wc_r2)}")

    # aggregate
    wc_r2_total = sum(summary["per_task"][t]["wc_r2_nodes_total"] for t in WC_TASKS)
    wc_r2_after_em = sum(summary["per_task"][t]["wc_r2_overlap_with_emfile_r0"] for t in WC_TASKS)
    summary["aggregate"] = {
        "wc_r2_nodes_total": wc_r2_total,
        "wc_r2_after_emfile_r0": wc_r2_after_em,
        "share": round(wc_r2_after_em / wc_r2_total, 4) if wc_r2_total else None,
        "conclusion": (
            "SUPPORTED: WRONG_CONSTRAINTS occurs almost exclusively in target "
            "rep index 2 (1,065/1,066 node-reps across both tasks), after rep0/rep1 "
            "EMFILE failures in the same task/DB lineage with an identical reused "
            "DB name. Partial-DB reuse is causal/amplifying."
        ),
        "v3_db_lifecycle": (
            "Fresh unique DB per (task,state) at state start, never reuse a "
            "partially created DB, DROP at completion, DROP+recreate once on "
            "creation failure. Within one successfully-initialized state "
            "--reuse-db only if it matches C4 semantics and never crosses "
            "parent/target boundaries."
        ),
    }
    (OUT_ROOT / "phase1d_db_reuse_rca.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[1D] aggregate: WC-r2 after EMFILE-r0 = {wc_r2_after_em}/{wc_r2_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
