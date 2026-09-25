#!/usr/bin/env python3
"""WP-2 MAIN unchanged-test P2P inventory - C4 zero-by-construction clarification.

Mission-08 Section B: the existing unchanged-test P2P candidate inventory covers
MAIN only. ``n_tasks_with_c4_exact_stable_p2p_nodes = 0`` is zero BY CONSTRUCTION
because C4 is the DEV sweep while the unchanged-test inventory is MAIN-only; it
must NOT be read as a P2P failure signal.

This script adds an explicit current-facing clarification to:
1. the final MAIN inventory artifact (oracle_confirmation_linux_v2 ... final);
2. the original MAIN inventory artifact.

The frozen ``inventory_sha256`` is preserved (it hashes the pre-clarification
bytes); a new ``c4_clarification.artifact_sha256_after_clarification`` records
the hash of the clarified file so the change is transparent and verifiable.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent

FINAL = (
    PROJECT
    / "research"
    / "wp2"
    / "oracle_confirmation_linux_v2_2026-09-23"
    / "wp2_unchanged_p2p_candidate_inventory_v1_final_2026-09-25.json"
)
ORIGINAL = PROJECT / "research" / "wp2" / "wp2_unchanged_p2p_candidate_inventory_v1_2026-09-23.json"

CLARIFICATION_TEXT = (
    "n_tasks_with_c4_exact_stable_p2p_nodes = 0 is zero BY CONSTRUCTION: "
    "C4 is the DEV changed-test sweep, while this unchanged-test inventory is "
    "MAIN-only (inventory(297) covers MAIN 220; inventory(297) intersect DEV = 0). "
    "It gives NO unchanged-test preservation measurement for DEV. "
    "Changed-test P2P_ONLY counts from C2/C4 are NOT the dedicated preservation "
    "oracle. This does NOT imply that P2P failed. preservation_validation_complete "
    "remains FALSE. A dedicated DEV unchanged-test P2P inventory is built under "
    "Mission-08."
)


def artifact_sha256(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def clarify(path: Path, *, note_extra: str = "") -> dict:
    if not path.exists():
        raise SystemExit(f"missing artifact: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    old_sha = payload.get("inventory_sha256")
    if "c4_clarification" in payload:
        print(f"[skip] already clarified: {path.name}")
        return payload
    payload["c4_clarification"] = {
        "date": "2026-09-25",
        "mission": "Mission-08 Phase A (Section B correction)",
        "text": CLARIFICATION_TEXT + note_extra,
        "inventory_sha256_before_clarification": old_sha,
        # Reproducible canonical hash over the payload with the clarification
        # block stripped (avoids a self-referential hash and the unknown
        # Mission-07 hashing method behind ``inventory_sha256``).
        "clarified_payload_canonical_sha256": artifact_sha256(
            {k: v for k, v in payload.items() if k != "c4_clarification"}
        ),
    }
    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[updated] {path.name}")
    return payload


def main() -> int:
    clarify(
        FINAL,
        note_extra=(
            " C4 is DEV; the unchanged-test inventory is MAIN-only; no DEV task "
            "appears in it."
        ),
    )
    clarify(
        ORIGINAL,
        note_extra=(
            " C4 is DEV; the unchanged-test inventory is MAIN-only; no DEV task "
            "appears in it."
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
