#!/usr/bin/env python3
"""WP-2 Mission-11 A5.1 - evaluator-only sets (ZERO API).

Reads the CORRECTED (V3.1) C4 V3 records + P2P-S + P2P-U V3 results and freezes
the evaluator-only node sets used by the Smoke evaluator. This file is
EVALUATOR-ONLY and must never be readable by generator/prompt modules.

Output: research/wp2/harness_v3_2026-09-26/evaluator_only/eng_evaluator_sets_v3.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
CENSUS = json.loads((PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" /
                     "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
SALEOR_CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"


def _now_utc() -> str:
    import datetime
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _sha256(payload: object) -> str:
    import hashlib
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def git_show(commit: str, path: str) -> str | None:
    r = subprocess.run(["git", "-C", str(SALEOR_CACHE), "show", f"{commit}:{path}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def main() -> int:
    eng = json.loads((OUT_ROOT / "eng_v3_oracle_ready.json").read_text(encoding="utf-8"))
    union = sorted(eng["oracle_valid_union_task_ids"])
    behavioral = sorted(eng["behavioral_task_ids"])
    symbol = sorted(eng["symbol_only_task_ids"])
    p2ps = json.loads((OUT_ROOT / "p2p_s_v3_eng.json").read_text(encoding="utf-8"))
    p2ps_by_task = {r["task_id"]: r for r in p2ps["per_task"]}

    commit_of = {t["task_id"]: (t["parent_commit"], t["target_commit"]) for t in CENSUS["tasks"]}

    tasks: dict = {}
    for tid in union:
        parent, target = commit_of[tid]
        c4 = json.loads((OUT_ROOT / f"phase5_c4v3_{tid}.json").read_text(encoding="utf-8"))
        recs = c4.get("node_records", [])
        beh_f2p = sorted(r["node_id"] for r in recs if r["v3_class"] == "BEHAVIORAL_F2P")
        sym_f2p = sorted(r["node_id"] for r in recs if r["v3_class"] == "SYMBOL_ABSENCE_F2P")

        # P2P-S: intersection U additions_v3 from p2p_s_v3_eng.json
        p2ps_rec = p2ps_by_task.get(tid)
        if p2ps_rec and p2ps_rec.get("defined"):
            p2ps_ids = sorted(set(p2ps_rec.get("intersection", [])) | set(p2ps_rec.get("additions_v3", [])))
            p2ps_defined = True
        else:
            p2ps_ids = []
            p2ps_defined = False
        # recompute from C4 records and assert equal: P2P_ONLY nodes 3/3 pass both sides
        recomputed_p2ps = sorted(
            r["node_id"] for r in recs
            if r["v3_class"] == "P2P_ONLY"
            and all(o == "passed" for o in r.get("target_outcomes", []))
            and all(o == "passed" for o in r.get("parent_outcomes", [])))
        if p2ps_defined:
            assert recomputed_p2ps == p2ps_ids, f"{tid} P2P-S recompute mismatch"

        # P2P-U stable ids (frozen order from the corrected results)
        cap_stable = {}
        cap_defined = {}
        for cap in (200, 400):
            u = json.loads((OUT_ROOT / f"p2pu_v3_eng_{tid}_cap{cap}.json").read_text(encoding="utf-8"))
            if u.get("status") == "DONE":
                cap_defined[cap] = True
                cap_stable[cap] = [n for n, cls in u.get("node_classes", {}).items()
                                   if cls == "STABLE_P2P"]
            else:
                cap_defined[cap] = False
                cap_stable[cap] = []

        # changed test paths + gold name status (non-test only)
        r = subprocess.run(["git", "-C", str(SALEOR_CACHE), "diff", "--name-status", parent, target],
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
        from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2
        gold_name_status = {"A": [], "M": [], "D": [], "R": []}
        changed_test_paths = []
        for line in r.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            st, path = parts[0], parts[-1]
            if is_test_path_v2(path):
                changed_test_paths.append(path)
                continue
            if st in ("A", "M", "D", "R"):
                gold_name_status[st].append(path)
        changed_test_paths = sorted(changed_test_paths)

        tasks[tid] = {
            "era_key": c4.get("era_key"),
            "parent_commit": parent,
            "target_commit": target,
            "behavioral_f2p_node_ids": beh_f2p,
            "symbol_f2p_node_ids": sym_f2p,
            "p2p_s_node_ids": p2ps_ids,
            "p2p_u_cap200_stable_ids": cap_stable[200],
            "p2p_u_cap400_stable_ids": cap_stable[400],
            "p2p_s_defined": p2ps_defined,
            "p2p_u_cap200_defined": cap_defined[200],
            "p2p_u_cap400_defined": cap_defined[400],
            "changed_test_paths": changed_test_paths,
            "gold_name_status": gold_name_status,
        }

    hashes = {tid: _sha256(tasks[tid]) for tid in sorted(tasks)}
    artifact = {
        "artifact": "eng-evaluator-sets-v3",
        "version": "eng-evaluator-sets-v3-2026-09-27",
        "created_utc": _now_utc(),
        "note": "Built from CORRECTED (V3.1 environment closure) C4/P2P-S/P2P-U evidence.",
        "population": {
            "behavioral": behavioral,
            "symbol_only": symbol,
            "p2pu_defined_cap200": sorted(t for t in tasks if tasks[t]["p2p_u_cap200_defined"]),
        },
        "tasks": tasks,
        "hashes": {"per_task_sha256": hashes, "artifact_sha256": ""},
        "leakage_note": "EVALUATOR-ONLY. Never readable by generator/prompt modules.",
    }
    artifact["hashes"]["artifact_sha256"] = _sha256(artifact)
    out = OUT_ROOT / "evaluator_only" / "eng_evaluator_sets_v3.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out}")
    print(f"population: behavioral={len(behavioral)} symbol_only={len(symbol)} "
          f"p2pu_defined_cap200={len(artifact['population']['p2pu_defined_cap200'])}")
    print(f"artifact_sha256={artifact['hashes']['artifact_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
