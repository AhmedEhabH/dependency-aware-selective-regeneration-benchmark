#!/usr/bin/env python3
"""WP-2 P2P-S primary preservation freeze V1 (Mission-09) - ZERO API.

Frozen extraction of P2P_ONLY node IDs from the FINAL Mission-07/C4 per-test
evidence for the 47 oracle-valid DEV tasks, emitted as
``research/wp2/wp2_dev_p2p_s_v1_2026-09-25.json``.

Usage:
    python scripts/wp2_p2p_s_freeze_v1.py --out research/wp2/wp2_dev_p2p_s_v1_2026-09-25.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.p2p_s_freeze_v1 import (  # noqa: E402
    build_p2p_s_artifact,
    verify_p2p_s_artifact,
)

INVENTORY = (
    PROJECT
    / "research"
    / "wp2"
    / "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json"
)
EVIDENCE = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" / "per_test_dev_v2.jsonl"
DEFAULT_OUT = PROJECT / "research" / "wp2" / "wp2_dev_p2p_s_v1_2026-09-25.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    out_path = Path(args.out)
    if not INVENTORY.exists() or not EVIDENCE.exists():
        print("missing input:", INVENTORY if not INVENTORY.exists() else EVIDENCE)
        return 2

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    if inventory["hashes"]["inventory_sha256"] != "0ae5699b890ed3fe7a18cdbfb59bcb53d31d21f091102bef87f15b241ce2bf61":
        print("FATAL: DEV inventory hash mismatch (frozen Mission-08 SHA expected)")
        return 2

    evidence_sha256 = hashlib.sha256(EVIDENCE.read_bytes()).hexdigest()
    records = []
    for line in EVIDENCE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))

    payload = build_p2p_s_artifact(
        inventory_payload=inventory,
        per_test_records=records,
        evidence_sha256=evidence_sha256,
        out_path=out_path,
    )
    verify = verify_p2p_s_artifact(payload)
    if not verify["all_pass"]:
        print("VERIFICATION FAILED:", json.dumps(verify["checks"], indent=1))
        return 2
    print("artifact:", out_path)
    print("artifact_sha256:", payload["hashes"]["artifact_sha256"])
    print("n_tasks:", len(payload["tasks"]))
    print("defined:", verify["n_defined"], "/ undefined:", verify["n_undefined"])
    print("undefined_tasks:", verify["undefined_tasks"])
    print("sparse_tasks:", verify["sparse_tasks"])
    print("coverage:", json.dumps(payload["coverage"], sort_keys=True))
    print("evidence_sha256:", evidence_sha256)
    print("VERIFICATION_PASS:", verify["all_pass"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
