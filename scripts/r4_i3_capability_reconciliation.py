#!/usr/bin/env python3
"""Generate R4_I3_CAPABILITY_STATE_RECONCILIATION.json for M17_D7_R4_I3_CAPABILITY_STATE_RECONCILIATION.

Metadata-only reconciliation: compares R4-D recorded immutable image IDs against
current local Docker daemon metadata via `docker image inspect`. No pull, no
build, no run, no registry access.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MATRIX = REPO / "research" / "env-canon-r4" / "R4_CAPABILITY_MATRIX_DRAFT.json"
OUT = REPO / "research" / "env-canon-r4" / "R4_I3_CAPABILITY_STATE_RECONCILIATION.json"

MISSION_ID = "M17_D7_R4_I3_CAPABILITY_STATE_RECONCILIATION"
R4D_COMMIT = "ecab678f2cbd3e3a35fcfa40392bef17afeb2c0d"
LOCAL_CHERRY_PICK = "d7a5b99e"


def docker_inspect_id(ref: str) -> str:
    proc = subprocess.run(
        ["docker", "image", "inspect", ref, "--format", "{{.Id}}"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        return "MISSING"
    return proc.stdout.strip()


def main() -> int:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    images = matrix["docker_image_inventory"]["images"]
    if len(images) != 14:
        print(f"FATAL: expected 14 images in inventory, got {len(images)}", file=sys.stderr)
        return 1

    per_image = []
    present = 0
    missing = 0
    mismatch = 0
    for img in images:
        ref = img["image"]
        expected = img["immutable_image_id"]
        current = docker_inspect_id(ref)
        if current == "MISSING":
            result = "MISSING"
            missing += 1
        elif current == expected:
            result = "PRESENT_MATCH"
            present += 1
        else:
            result = "ID_MISMATCH"
            mismatch += 1
        per_image.append(
            {
                "expected_reference": ref,
                "docker_profile_id": img.get("docker_profile_id"),
                "native_profile_id": img.get("native_profile_id"),
                "layer_role": img["layer_role"],
                "mapped_era": img["mapped_era"],
                "mapped_python_version": img["mapped_python_version"],
                "r4d_expected_immutable_image_id": expected,
                "current_immutable_image_id": current,
                "result": result,
            }
        )

    classification = (
        "HISTORICAL_STALE_STATE_FOR_R4_INTEGRATION"
        if present == 14 and missing == 0 and mismatch == 0
        else "RECONCILIATION_INCOMPLETE"
    )

    report = {
        "mission_id": MISSION_ID,
        "starting_head": "2f37afbc21a50c5b11afe7b13cb593d1e47dd54a",
        "R4-D authoritative commit": R4D_COMMIT,
        "local cherry-picked R4-D commit": LOCAL_CHERRY_PICK,
        "historical gate value": "all_docker_images_built: {built: null, pass: false, planned: null}",
        "historical gate source reference": (
            "D:\\wp2_env_store\\manifests\\ENV_CANON_GATE.json "
            "(phase=PHASE_B, ENV_CANON_READY=false, reason=PHASE_B_DYNAMIC_VALIDATION_NOT_YET_EXECUTED; "
            "recorded 2026-10-09, immutable historical receipt)"
        ),
        "current reconciliation timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expected_image_count": 14,
        "images": per_image,
        "present_match_count": present,
        "missing_count": missing,
        "mismatch_count": mismatch,
        "reconciliation_classification": classification,
        "R4-D plan status": "DRAFT_PENDING_R4_INTEGRATION",
        "population unchanged": True,
        "calibration selection unchanged": True,
        "frozen evidence modified": False,
        "Docker commands used": [
            "docker image inspect <ref> --format '{{.Id}}'",
            "docker image ls --no-trunc",
        ],
        "docker_pull_used": False,
        "docker_build_used": False,
        "docker_run_used": False,
        "network_used": False,
        "full_d7_executed": False,
        "population_census_executed": False,
        "calibration_executed": False,
        "OPWS_executed": False,
    }

    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"present_match_count={present} missing_count={missing} mismatch_count={mismatch}")
    print(f"classification={classification}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
