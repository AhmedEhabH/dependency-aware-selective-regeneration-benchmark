#!/usr/bin/env python3
"""M17_D7_R4_RUNTIME_TOOLHOUSE_CLEAN — additive runtime-clean successor binding.

Mission: bounded environment-repair successor for the proven
RUNTIME_TOOLHOUSE_CONTAMINATION defect.  The frozen R3 runtime-cleanliness
contract forbids any ``BUILD_TOOLHOUSE_ONLY_DISTS`` distribution in the final
runtime environment; the qualified py38/py39 execution images pre-install
``wheel``, which the gate correctly flags.  This tool derives the additive
successor binding:

* key remains exactly ``(docker_profile_id, native_profile_id)``;
* clean bindings retain their existing qualified image ID;
* only the four proven contaminated py38/py39 bindings map to additive
  runtime-clean successors (``FROM <parent> ; RUN python -m pip uninstall -y wheel``);
* no unit-ID / task-ID special cases;
* deterministic successor binding semantic hash.

No network, no Docker pull, no Docker build here (builds are performed by the
mission's bounded repair step).  Pure metadata transform + local image ID
verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
R4_DIR = PROJECT / "research" / "env-canon-r4"
PARENT_BINDING = R4_DIR / "R4_EXECUTION_IMAGE_COMPOSITE_BINDING.json"
OUT_BINDING = R4_DIR / "R4_EXECUTION_IMAGE_BINDING_RUNTIME_CLEAN.json"

DISTRO = "Ubuntu-24.04"
EXPECTED_POPULATION_IDENTITY = "ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac"
EXPECTED_UNITS = 144
EXPECTED_PAIRS = 11

# (docker_profile_id, native_profile_id) -> (successor_ref, successor_id, parent_ref, parent_id)
SUCCESSORS: dict[tuple[str, str], dict[str, str]] = {
    ("dk-py38-bullseye", "nat-62bc3631c27d"): {
        "execution_image_ref": "envcanon/saleor-env-native-nat-62bc3631c27d-runtimeclean:r4-toolhouse-clean-20261014",
        "immutable_image_id": "sha256:b3e7e8903350e8c3c89801df6113009a114b0553cca428d096c0847ac6122403",
        "parent_image_ref": "envcanon/saleor-env-native-nat-62bc3631c27d:latest",
        "parent_image_id": "sha256:a8b198cf86806747c521d6c3256961822bd81702369af4fec1de8a3430d9caff",
    },
    ("dk-py39-bookworm", "nat-f65b9bf250fd"): {
        "execution_image_ref": "envcanon/saleor-env-native-nat-f65b9bf250fd-runtimeclean:r4-toolhouse-clean-20261014",
        "immutable_image_id": "sha256:4332cce523045c92934bb5b1c6f422c9527d9c01fa70aa9dc7bb3b70d7776523",
        "parent_image_ref": "envcanon/saleor-env-native-nat-f65b9bf250fd:latest",
        "parent_image_id": "sha256:baea6c4b01e1b5bfb40b5910074c4b145c91c2c1d19b815889df4f1d76d86f24",
    },
    ("dk-py39-bullseye", "nat-d35546f097f4"): {
        "execution_image_ref": "envcanon/saleor-env-native-nat-d35546f097f4-runtimeclean:r4-toolhouse-clean-20261014",
        "immutable_image_id": "sha256:94246e6bc8ae952f2172bac25973118a3d5d99f5fbed54bb451b55954067ac28",
        "parent_image_ref": "envcanon/saleor-env-native-nat-d35546f097f4:latest",
        "parent_image_id": "sha256:d6f910882d1d27ce878df535815630a190a57b19932ab58dcb96d193665f2796",
    },
    ("dk-py39-bullseye", "nat-d7d5ae76a87f"): {
        "execution_image_ref": "envcanon/saleor-env-native-nat-d7d5ae76a87f-runtimeclean:r4-toolhouse-clean-20261014",
        "immutable_image_id": "sha256:8c90d36aca1393a619f4448e1adfd6c307f27518c44df7baa6320d1ebaaec3ae",
        "parent_image_ref": "envcanon/saleor-env-native-nat-d7d5ae76a87f:latest",
        "parent_image_id": "sha256:dc6a421b28d86aab1c6bca0a32b11b40fefc74535105c4240348208ca3773233",
    },
}


class CleanRepairError(Exception):
    """Raised on any fail-closed successor-binding gate."""


def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _local_image_id(image: str) -> str | None:
    r = subprocess.run(
        ["wsl", "-d", DISTRO, "--", "docker", "image", "inspect", "-f", "{{.Id}}", image],
        capture_output=True, text=True, timeout=120,
    )
    out = r.stdout.strip()
    return out if r.returncode == 0 and out else None


def build_successor_binding(parent: dict[str, Any]) -> dict[str, Any]:
    if parent.get("population_identity") != EXPECTED_POPULATION_IDENTITY:
        raise CleanRepairError("population identity drift")
    if parent.get("unique_pair_count") != EXPECTED_PAIRS:
        raise CleanRepairError("parent pair count drift")

    pairs: list[dict[str, Any]] = []
    for rec in parent["pairs"]:
        dp = rec["docker_profile_id"]
        np_id = rec["native_profile_id"]
        out = {
            "docker_profile_id": dp,
            "native_profile_id": np_id,
            "frozen_python_version": rec["frozen_python_version"],
            "wheelhouse_era": rec["wheelhouse_era"],
            "affected_unit_count": rec["affected_unit_count"],
            "member_validation_unit_ids": rec["member_validation_unit_ids"],
        }
        succ = SUCCESSORS.get((dp, np_id))
        if succ is None:
            out["execution_image_ref"] = rec["execution_image_ref"]
            out["immutable_image_id"] = rec["immutable_image_id"]
            out["provenance"] = rec["provenance"]
        else:
            out["execution_image_ref"] = succ["execution_image_ref"]
            out["immutable_image_id"] = succ["immutable_image_id"]
            out["provenance"] = "R4_RUNTIME_TOOLHOUSE_CLEAN"
            out["parent_image_ref"] = succ["parent_image_ref"]
            out["parent_image_id"] = succ["parent_image_id"]
            out["removed_toolhouse_dists"] = ["wheel"]
        pairs.append(out)

    payload: dict[str, Any] = {
        "schema_version": "env-canon-r4-execution-image-binding-runtime-clean/1.0",
        "mission_id": "M17_D7_R4_RUNTIME_TOOLHOUSE_CLEAN",
        "population_identity": EXPECTED_POPULATION_IDENTITY,
        "binding_key": "(docker_profile_id, native_profile_id)",
        "unique_pair_count": len(pairs),
        "pairs": pairs,
        "deterministic_binding_hash": None,
    }
    payload["deterministic_binding_hash"] = _sha256_bytes(
        _canonical({k: v for k, v in payload.items() if k != "deterministic_binding_hash"})
    )
    return payload


def verify_accounting(binding: dict[str, Any]) -> dict[str, Any]:
    keys = [(r["docker_profile_id"], r["native_profile_id"]) for r in binding["pairs"]]
    if len(keys) != len(set(keys)):
        raise CleanRepairError("duplicate binding pair")
    if len(keys) != EXPECTED_PAIRS:
        raise CleanRepairError(f"pair count {len(keys)} != {EXPECTED_PAIRS}")
    units = sum(r["affected_unit_count"] for r in binding["pairs"])
    if units != EXPECTED_UNITS:
        raise CleanRepairError(f"unit accounting {units} != {EXPECTED_UNITS}")
    for r in binding["pairs"]:
        if not r["execution_image_ref"] or not r["immutable_image_id"].startswith("sha256:"):
            raise CleanRepairError(f"malformed pair {r['docker_profile_id']}/{r['native_profile_id']}")
    return {"unique_pair_count": len(keys), "units_resolved": units, "no_missing": True,
            "no_duplicate": True, "no_ambiguity": True, "no_fallback": True}


def main() -> int:
    ap = argparse.ArgumentParser(description="R4 runtime-toolhouse-clean successor binding")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--verify-local-images", action="store_true")
    args = ap.parse_args()

    try:
        parent = json.loads(PARENT_BINDING.read_text(encoding="utf-8"))
        binding = build_successor_binding(parent)
        accounting = verify_accounting(binding)

        if args.verify_local_images:
            for r in binding["pairs"]:
                local = _local_image_id(r["execution_image_ref"])
                if local != r["immutable_image_id"]:
                    raise CleanRepairError(
                        f"image {r['execution_image_ref']} local {local} != binding {r['immutable_image_id']}"
                    )
            accounting["local_image_ids_verified"] = True

        if args.write:
            OUT_BINDING.write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        print(json.dumps({
            "binding_hash": binding["deterministic_binding_hash"],
            "unique_pair_count": binding["unique_pair_count"],
            "accounting": accounting,
            "successor_pairs": [f"{r['docker_profile_id']}/{r['native_profile_id']}"
                                for r in binding["pairs"] if r["provenance"] == "R4_RUNTIME_TOOLHOUSE_CLEAN"],
            "output": str(OUT_BINDING),
        }, indent=2, sort_keys=True))
        return 0
    except CleanRepairError as exc:
        print(f"FAIL_CLOSED {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
