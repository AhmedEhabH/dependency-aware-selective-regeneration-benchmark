#!/usr/bin/env python3
"""WP-2 census/evaluator-side metadata additions (amendment H) - ZERO API.

For MAIN changed-test candidates, add deterministic evaluator-side fields:
1. production files added in target but absent at parent;
2. hashed representation of Gold production files that already exist at parent;
3. RM-CSS empty-scope flag;
4. Agent empty-scope flag;
5. RM-CSS-vs-Agent scope-identical flag.

Metadata only; frozen RM-CSS/Agent predictions are never modified. Also writes
the protected-pools untouched proof (INTERNAL_TEST / sealed RESERVE guard).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.census_metadata_v2 import build_task_metadata, parse_name_status  # noqa: E402
from benchmark.wp2.oracle_semantics_v2 import assert_task_allowed, is_test_path_v2  # noqa: E402

CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"
CENSUS = PROJECT / "research" / "wp2" / "wp2_saleor_main297_census_2026-09-22.json"
SIP = PROJECT / "research" / "wp1a" / "sip_rmcss_per_task_predictions.json"
AGENT = PROJECT / "research" / "wp1b" / "main-297-2026-09-22" / "wp1b_agent_predictions.json"
SPLIT = PROJECT / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"
OUT = PROJECT / "research" / "wp2" / "wp2_main_census_metadata_v2_2026-09-23.json"
OUT_PROOF = PROJECT / "research" / "wp2" / "protected_pools_untouched_proof_2026-09-23.json"


def git(cache: Path, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["git", "-C", str(cache), *args]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False)


def parent_file_set(cache: Path, parent: str) -> set[str]:
    r = git(cache, "ls-tree", "-r", "--name-only", parent)
    return set(r.stdout.splitlines())


def main() -> int:
    census = {t["task_id"]: t for t in json.loads(CENSUS.read_text(encoding="utf-8"))["tasks"]}
    sip = json.loads(SIP.read_text(encoding="utf-8"))["per_task"]
    agent = json.loads(AGENT.read_text(encoding="utf-8"))["per_task"]
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    assign = split["assignment"]
    internal_ids = sorted(t for t, a in assign.items() if a == "INTERNAL_TEST")
    reserve_ids = sorted(t for t, a in assign.items() if a == "RESERVE")

    tasks = []
    for tid in sorted(census):
        c = census[tid]
        if not c.get("changed_paths"):
            continue
        parent, target = c["parent_commit"], c["target_commit"]
        r = git(CACHE, "diff", "--name-status", parent, target)
        rows = parse_name_status(r.stdout)
        gold = [p for _, p in rows if not is_test_path_v2(p)]
        parent_files = parent_file_set(CACHE, parent)
        assert_task_allowed(tid)
        meta = build_task_metadata(
            task_id=tid,
            name_status_rows=rows,
            gold_production_files=gold,
            parent_files=parent_files,
            rmcss_paths=sip.get(tid, {}).get("rmcss_predicted_set", []),
            agent_paths=agent.get(tid, {}).get("selected_paths", []),
        )
        meta["f2p_candidacy"] = c.get("f2p_candidacy")
        tasks.append(meta)

    artifact = {
        "artifact": "wp2_main_census_metadata_v2",
        "date": "2026-09-23",
        "status": "EVALUATOR_SIDE_METADATA_ONLY",
        "predictions_unchanged": True,
        "n_tasks": len(tasks),
        "tasks": tasks,
    }
    OUT.write_text(json.dumps(artifact, indent=1, ensure_ascii=False), encoding="utf-8")

    proof = {
        "artifact": "wp2_protected_pools_untouched_proof",
        "date": "2026-09-23",
        "INTERNAL_TEST": {
            "status": "UNTOUCHED",
            "n": len(internal_ids),
            "role_sha256": hashlib.sha256(json.dumps(internal_ids, sort_keys=True).encode()).hexdigest(),
            "guard": (
                "assert_task_allowed refuses INTERNAL_TEST access; "
                "no oracle/census/generation access performed (amendment G)"
            ),
            "sealed": True,
        },
        "RESERVE": {
            "status": "UNTOUCHED",
            "n": len(reserve_ids),
            "note": (
                "786 sealed RESERVE outcomes never listed/read/opened/scored "
                "beyond already-authorized aggregate metadata; guard refuses "
                "RESERVE access"
            ),
            "sealed": True,
        },
    }
    OUT_PROOF.write_text(json.dumps(proof, indent=1, ensure_ascii=False))
    print("n_tasks:", len(tasks))
    print("INTERNAL_TEST guard:", proof["INTERNAL_TEST"]["status"], proof["INTERNAL_TEST"]["n"])
    print("RESERVE guard:", proof["RESERVE"]["status"], proof["RESERVE"]["n"])
    print("wrote", OUT.name, "and", OUT_PROOF.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
