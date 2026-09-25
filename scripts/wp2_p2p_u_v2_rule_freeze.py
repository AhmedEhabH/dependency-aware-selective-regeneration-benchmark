#!/usr/bin/env python3
"""WP-2 P2P-U V2 rule freeze artifact writer (Mission-09) - ZERO API.

Freezes the exact P2P-U V2 scientific rule as a standalone document with its
own canonical SHA256, so the rule is immutable before ANY V2 outcome execution.
The rule is identical to the one embedded in the membership artifact.

Usage:
    python scripts/wp2_p2p_u_v2_rule_freeze.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.p2p_u_v2 import (  # noqa: E402
    P2P_U_PRIMARY_CAP,
    P2P_U_SENSITIVITY_CAP,
    P2P_U_V2_SAMPLE_SALT,
    P2P_U_V2_VERSION,
    PRIMARY_DISTAL_TARGET,
    PRIMARY_PROXIMAL_TARGET,
    RULE_TEXT,
    SENSITIVITY_DISTAL_TARGET,
    SENSITIVITY_PROXIMAL_TARGET,
    canonical_sha256,
)

OUT = PROJECT / "research" / "wp2" / "wp2_p2p_u_v2_rule_freeze_2026-09-25.json"


def main() -> int:
    payload = {
        "artifact": "wp2_p2p_u_v2_rule_freeze",
        "artifact_version": P2P_U_V2_VERSION,
        "date": "2026-09-25",
        "status": "FROZEN_BEFORE_ANY_V2_OUTCOME_EXECUTION",
        "salt": P2P_U_V2_SAMPLE_SALT,
        "primary_cap": P2P_U_PRIMARY_CAP,
        "sensitivity_cap": P2P_U_SENSITIVITY_CAP,
        "primary_target_composition": {
            "proximal": PRIMARY_PROXIMAL_TARGET,
            "distal": PRIMARY_DISTAL_TARGET,
        },
        "sensitivity_target_composition": {
            "proximal": SENSITIVITY_PROXIMAL_TARGET,
            "distal": SENSITIVITY_DISTAL_TARGET,
        },
        "proximal_threshold": "file proximity >= 2",
        "distal_threshold": "file proximity <= 1 (incl. 0 / UNKNOWN-derived)",
        "salt_note": "Frozen BEFORE any V2 outcome execution; never changed after outcomes are observed.",
        "rule_text": RULE_TEXT,
    }
    payload["hashes"] = {
        "rule_sha256": canonical_sha256({"rule_text": RULE_TEXT}),
        "salt_sha256": canonical_sha256({"salt": payload["salt"]}),
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT)
    print("rule_sha256:", payload["hashes"]["rule_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
