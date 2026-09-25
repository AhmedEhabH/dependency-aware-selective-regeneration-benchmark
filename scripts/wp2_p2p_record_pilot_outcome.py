#!/usr/bin/env python3
"""WP-2 DEV P2P - record a completed serial-pilot outcome into the inventory.

Fills the post-stability fields (n_stable_p2p_nodes_before_cap /
n_stable_p2p_nodes_after_cap / capped_stable / preservation_nodes) for a task
using the frozen cap applied to STABLE_P2P nodes only (addendum Q7). Also
records the Q2 class distribution from the pilot evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent

INVENTORY_ARTIFACT = PROJECT / "research" / "wp2" / "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json"
EVIDENCE_ROOT = PROJECT / "research" / "wp2" / "p2p_serial_pilot_2026-09-25"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--run-label", default="A")
    args = ap.parse_args()

    artifact = json.loads(INVENTORY_ARTIFACT.read_text(encoding="utf-8"))
    row = next(r for r in artifact["tasks"] if r["task_id"] == args.task)
    evidence = EVIDENCE_ROOT / args.task / args.run_label
    manifest = json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))
    node_classes = json.loads((evidence / "node_classes.json").read_text(encoding="utf-8"))

    from benchmark.wp2.p2p_inventory_dev_v1 import record_p2p_outcomes

    record_p2p_outcomes(row, node_classes)
    row["p2p_pilot"] = {
        "run_label": args.run_label,
        "class_counts": manifest["class_counts"],
        "n_stable_p2p": manifest["n_stable_p2p"],
        "stable_over_discovered": manifest["stable_over_discovered"],
        "total_wall_s": manifest["measurements"]["total_wall_s"],
        "evidence": str(evidence),
        "evidence_integrity": manifest["evidence_integrity"],
        "note": "PILOT ONLY - SMALL task; NOT a 47-task evaluation.",
    }
    artifact["hashes"]["inventory_sha256"] = None  # placeholder replaced below
    from benchmark.wp2.p2p_inventory_dev_v1 import dev_inventory_sha256

    blob = {k: v for k, v in artifact.items() if k != "hashes"}
    artifact["hashes"]["inventory_sha256"] = dev_inventory_sha256(blob)
    INVENTORY_ARTIFACT.write_text(json.dumps(artifact, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"recorded pilot outcome for {args.task}")
    print("  n_stable_before_cap:", row["n_stable_p2p_nodes_before_cap"],
          "after_cap:", row["n_stable_p2p_nodes_after_cap"],
          "capped:", row["capped_stable"])
    print("  inventory_sha256:", artifact["hashes"]["inventory_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
