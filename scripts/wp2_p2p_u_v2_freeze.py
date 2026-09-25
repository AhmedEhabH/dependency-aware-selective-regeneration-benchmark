#!/usr/bin/env python3
"""WP-2 P2P-U V2 membership freeze (Mission-09) - ZERO API, OUTCOME-BLIND.

Frozen BEFORE any P2P-U V2 outcome execution (Mission-09 sections 9-10):

- reads the FINAL Mission-08 frozen DEV unchanged-test inventory (raw
  discovered candidate nodes per task);
- derives evaluator-only gold touched production paths from the frozen target
  diff via the read-only Saleor git cache (NO rediscovery of nodes);
- computes per-file proximity, PROXIMAL/DISTAL pools, deterministic
  outcome-blind ordering under the frozen salt ``wp2-p2p-u-v2-2026-09-25``;
- freezes cap200 (primary, target 150/50) and cap400 (sensitivity, target
  300/100) memberships, both prefixes of the same ordered list so
  first_200 subset first_400 exactly;
- records all hashes (rule, ordered candidate, cap memberships, task
  membership, proximal/distal labels, proximity, source file, ordering).

Usage:
    python scripts/wp2_p2p_u_v2_freeze.py --out research/wp2/wp2_p2p_u_v2_membership_2026-09-25.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2  # noqa: E402
from benchmark.wp2.p2p_inventory_dev_v1 import membership_sha256  # noqa: E402
from benchmark.wp2.p2p_u_v2 import (  # noqa: E402
    P2P_U_V2_SAMPLE_SALT,
    P2P_U_V2_VERSION,
    RULE_TEXT,
    canonical_sha256,
    changed_test_contamination,
    verify_freeze,
)

INVENTORY = (
    PROJECT
    / "research"
    / "wp2"
    / "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json"
)
CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"
DEFAULT_OUT = PROJECT / "research" / "wp2" / "wp2_p2p_u_v2_membership_2026-09-25.json"

FROZEN_INVENTORY_SHA = "0ae5699b890ed3fe7a18cdbfb59bcb53d31d21f091102bef87f15b241ce2bf61"


def git(cache: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cache), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def changed_paths(parent: str, target: str) -> dict:
    """Target diff paths (production only). Evaluator-only gold construction."""
    r = git(CACHE, "diff", "--name-status", parent, target)
    prod_paths: list[str] = []
    changed_test_paths: list[str] = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        path = parts[1]
        (changed_test_paths if is_test_path_v2(path) else prod_paths).append(path)
    return {
        "prod_files": sorted(prod_paths),
        "changed_test_files": sorted(changed_test_paths),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    out_path = Path(args.out)

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    if inventory["hashes"]["inventory_sha256"] != FROZEN_INVENTORY_SHA:
        print("FATAL: DEV inventory hash mismatch")
        return 2

    # Candidate pool = frozen Mission-08 discovered nodes for the 47 union.
    tasks: dict[str, dict] = {}
    for row in sorted(
        (r for r in inventory["tasks"] if r.get("oracle_valid")), key=lambda r: r["task_id"]
    ):
        task_id = row["task_id"]
        cp = changed_paths(row["parent_commit"], row["target_commit"])
        from benchmark.wp2.p2p_u_v2 import build_task_selection

        sel = build_task_selection(
            task_id=task_id,
            candidate_node_ids=list(row["candidate_node_ids"] or []),
            touched_production_files=cp["prod_files"],
            salt=P2P_U_V2_SAMPLE_SALT,
        )
        sel["changed_test_files_in_target_diff"] = cp["changed_test_files"]
        tasks[task_id] = sel

    # No changed test file may enter the candidate pool (Mission-09 section 24).

    changed_test_contamination_map: dict[str, list[str]] = {}
    for task_id, sel in tasks.items():
        contaminated = changed_test_contamination(
            sel["ordered_node_ids"], sel["changed_test_files_in_target_diff"]
        )
        if contaminated:
            changed_test_contamination_map[task_id] = contaminated
    if changed_test_contamination_map:
        print(
            "FATAL: changed-test contamination in candidate pool:",
            json.dumps(changed_test_contamination_map, indent=1),
        )
        return 2

    # Freeze hashes over the FULL membership payload (minus its own hashes block).
    payload: dict = {
        "artifact": "wp2_p2p_u_v2_membership",
        "artifact_version": P2P_U_V2_VERSION,
        "date": "2026-09-25",
        "scope": "oracle-valid DEV union (47 tasks); execution limited to ENG in Mission-09",
        "salt": P2P_U_V2_SAMPLE_SALT,
        "inventory_sha256": FROZEN_INVENTORY_SHA,
        "rule_text": RULE_TEXT,
        "rule_sha256": canonical_sha256({"rule_text": RULE_TEXT}),
        "rule": (
            "P2P-U V2 extended preservation: outcome-blind, proximity-aware, "
            "deterministic PRE-execution selection over the frozen Mission-08 "
            "unchanged-test candidate pool. proximity(test_file) = max over "
            "KNOWN touched production files of longest common leading component "
            "count after saleor/. PROXIMAL = file proximity >= 2; DISTAL = <= 1 "
            "including 0/UNKNOWN-derived. Order by sha256(salt|file_path) within "
            "proximity stratum, sha256(salt|node_id) within file, round-robin "
            "one node per file per round; exhaust higher strata first. "
            "Interleave P,P,P,D; first_200 subset first_400 exactly. "
            "Primary K=200 target 150/50; sensitivity K=400 target 300/100; "
            "pool shortage backfills deterministically from the other pool; "
            "never invent candidates. UNKNOWN touched paths contribute no "
            "proximity; all-UNKNOWN task => all proximity=0 + flag. "
            "Cap never depends on outcomes."
        ),
        "evaluator_only": True,
        "invisible_to_generation": True,
        "tasks": tasks,
    }
    # ordering hash = sha256 over the deterministic ordered lists (task-sorted)
    ordering_hash = canonical_sha256(
        {"ordered": {tid: sel["ordered_node_ids"] for tid, sel in sorted(tasks.items())}}
    )
    cap200_hash = canonical_sha256(
        {"cap200": {tid: sel["cap200_node_ids"] for tid, sel in sorted(tasks.items())}}
    )
    cap400_hash = canonical_sha256(
        {"cap400": {tid: sel["cap400_node_ids"] for tid, sel in sorted(tasks.items())}}
    )
    proxdist_hash = canonical_sha256(
        {
            "proximal": {tid: sel["proximal_nodes"] for tid, sel in sorted(tasks.items())},
            "distal": {tid: sel["distal_nodes"] for tid, sel in sorted(tasks.items())},
        }
    )
    proxscore_hash = canonical_sha256(
        {"proximity": {tid: sel["proximity_by_file"] for tid, sel in sorted(tasks.items())}}
    )
    srcfile_hash = canonical_sha256(
        {
            "files": {
                tid: sorted({n.split("::", 1)[0] for n in sel["ordered_node_ids"]})
                for tid, sel in sorted(tasks.items())
            }
        }
    )
    payload["hashes"] = {
        "rule_sha256": canonical_sha256({"rule_text": RULE_TEXT}),
        "ordered_candidate_sha256": ordering_hash,
        "cap200_membership_sha256": cap200_hash,
        "cap400_membership_sha256": cap400_hash,
        "task_membership_sha256": membership_sha256(sorted(tasks)),
        "proximal_distal_labels_sha256": proxdist_hash,
        "proximity_score_sha256": proxscore_hash,
        "source_file_sha256": srcfile_hash,
        "ordering_hash": ordering_hash,
        "artifact_sha256": canonical_sha256(
            {k: v for k, v in payload.items() if k != "hashes"}
        ),
    }

    verify = verify_freeze(payload)
    if not verify["all_pass"]:
        print("VERIFICATION FAILED:", json.dumps(verify, indent=1))
        return 2

    out_path.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")

    n_eng = len(inventory["membership"]["DEV_TRAIN_ENG"])
    print("artifact:", out_path)
    print("artifact_sha256:", payload["hashes"]["artifact_sha256"])
    print("rule_sha256:", payload["hashes"]["rule_sha256"])
    print("ordered_candidate_sha256:", payload["hashes"]["ordered_candidate_sha256"])
    print("cap200_membership_sha256:", payload["hashes"]["cap200_membership_sha256"])
    print("cap400_membership_sha256:", payload["hashes"]["cap400_membership_sha256"])
    print("n_tasks:", len(tasks), "(47 union)")
    print("n_eng:", n_eng)
    for tid in sorted(tasks):
        sel = tasks[tid]
        print(
            f"  {tid}: raw={sel['n_raw_candidates']} "
            f"cap200={len(sel['cap200_node_ids'])} (P{sel['composition_cap200']['n_proximal']}/"
            f"D{sel['composition_cap200']['n_distal']}) "
            f"cap400={len(sel['cap400_node_ids'])} (P{sel['composition_cap400']['n_proximal']}/"
            f"D{sel['composition_cap400']['n_distal']}) "
            f"all_unknown={sel['all_touched_paths_unknown']}"
        )
    print("verify:", json.dumps(verify, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
