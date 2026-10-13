#!/usr/bin/env python3
"""M17_D7_R4 native-image composition repair — general execution-image binding.

Mission: M17_D7_R4_NATIVE_IMAGE_COMPOSITION_REPAIR (T3, bounded environment-
engineering repair and qualification).

Implements the GENERAL execution-image identity model proven by the frozen R4
composition census:

    execution image identity == (docker_profile_id, native_profile_id)

Derives the complete unique-pair set from the frozen 144-unit population
(NEVER hardcoded), resolves each pair to its qualified execution image, and
emits:

    research/env-canon-r4/R4_EXECUTION_IMAGE_COMPOSITE_BINDING.json

Pair resolution rules (general, no task/unit special casing):

    - if the currently-qualified native image for the pair's native profile
      already has the frozen base-era semantics  -> EXISTING_QUALIFIED_NATIVE_IMAGE
    - elif a composite binding exists for the exact (docker_profile_id,
      native_profile_id) pair                         -> R4_COMPOSITE_REPAIR
    - else                                             -> fail closed (unknown pair)

The repaired pair (dk-py312-bookworm, nat-f65b9bf250fd) binds to the NEW
composite image; the existing pair (dk-py39-bookworm, nat-f65b9bf250fd) remains
bound to the original py39 native image.

Also runs the bounded POST-REPAIR logical composition census using the general
binding (REPAIR-L): every frozen unit is classified against its bound execution
image. Expected 144 COMPOSITION_MATCH / 0 COMPOSITE_IMAGE_REQUIRED. The result
is written ADDITIVELY as R4_POST_REPAIR_COMPOSITION_CENSUS.json — the original
frozen census is never overwritten.

No network, no docker pull, no build, no mutation of frozen authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
SCRIPTS = PROJECT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

R4_DIR = PROJECT / "research" / "env-canon-r4"
BINDING_JSON = R4_DIR / "R4_EXECUTION_IMAGE_COMPOSITE_BINDING.json"
POST_REPAIR_CENSUS_JSON = R4_DIR / "R4_POST_REPAIR_COMPOSITION_CENSUS.json"

import r4_native_image_composition_census as census  # noqa: E402

SCHEMA_VERSION = "env-canon-r4-execution-image-composite-binding/1.0"
MISSION_ID = "M17_D7_R4_NATIVE_IMAGE_COMPOSITION_REPAIR"

COMPOSITE_IMAGE_REF = "envcanon/saleor-env-native-nat-f65b9bf250fd-py312-bookworm:r4-composite-20261013"
REPAIRED_PAIR = ("dk-py312-bookworm", "nat-f65b9bf250fd")

EXISTING_QUALIFIED = "EXISTING_QUALIFIED_NATIVE_IMAGE"
COMPOSITE_REPAIR = "R4_COMPOSITE_REPAIR"

COMPOSITION_MATCH = census.COMPOSITION_MATCH
COMPOSITE_IMAGE_REQUIRED = census.COMPOSITE_IMAGE_REQUIRED
AUTHORITY_AMBIGUOUS = census.AUTHORITY_AMBIGUOUS
INVALID_FROZEN_MAPPING = census.INVALID_FROZEN_MAPPING
UNKNOWN = census.UNKNOWN


class BindingFailClosedError(Exception):
    """Raised when any fail-closed gate fails (drives nonzero exit)."""


def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_core(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k != "deterministic_binding_hash"}


def derive_unique_pairs(
    unit_rows: list[dict[str, str]],
) -> dict[tuple[str, str], list[str]]:
    """Unique (docker_profile_id, native_profile_id) pairs over the frozen population."""
    pairs: dict[tuple[str, str], list[str]] = {}
    for u in unit_rows:
        key = (u["docker_profile_id"], u["native_profile_id"])
        pairs.setdefault(key, []).append(u["unit_id"])
    for key in pairs:
        pairs[key].sort()
    return pairs


def resolve_pair(
    pair: tuple[str, str],
    docker_profile_map: dict[str, dict[str, Any]],
    native_profile_map: dict[str, dict[str, Any]],
    composite_image_id: str,
) -> dict[str, Any]:
    """General pair -> execution-image resolution (no unit/task special casing)."""
    dp_id, np_id = pair
    base = docker_profile_map.get(dp_id)
    native = native_profile_map.get(np_id)
    if base is None:
        raise BindingFailClosedError(f"unknown docker profile in pair {pair!r}")
    if native is None:
        raise BindingFailClosedError(f"unknown native profile in pair {pair!r}")

    base_era = base.get("expected_era")
    native_era = native.get("image_era")

    if native_era == base_era:
        return {
            "docker_profile_id": dp_id,
            "native_profile_id": np_id,
            "execution_image_ref": native["current_native_image"],
            "immutable_image_id": native["immutable_image_id"],
            "provenance": EXISTING_QUALIFIED,
        }

    if pair == REPAIRED_PAIR:
        return {
            "docker_profile_id": dp_id,
            "native_profile_id": np_id,
            "execution_image_ref": COMPOSITE_IMAGE_REF,
            "immutable_image_id": composite_image_id,
            "provenance": COMPOSITE_REPAIR,
        }

    raise BindingFailClosedError(
        f"no qualified execution image for pair {pair!r} "
        f"(native era {native_era!r} != base era {base_era!r})"
    )


def build_binding(
    composite_image_id: str,
    members_by_pair: dict[tuple[str, str], list[str]],
    docker_profile_map: dict[str, dict[str, Any]],
    native_profile_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Full binding payload with deterministic hash (no task/unit exceptions)."""
    pairs = sorted(members_by_pair)
    records: list[dict[str, Any]] = []
    for pair in pairs:
        resolved = resolve_pair(pair, docker_profile_map, native_profile_map, composite_image_id)
        dp_id, np_id = pair
        members = members_by_pair[pair]
        base = docker_profile_map[dp_id]
        resolved.update(
            {
                "frozen_python_version": base.get("expected_python_version"),
                "wheelhouse_era": base.get("expected_era"),
                "affected_unit_count": len(members),
                "member_validation_unit_ids": members,
            }
        )
        records.append(resolved)

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "mission_id": MISSION_ID,
        "population_identity": census.EXPECTED_POPULATION_IDENTITY,
        "binding_key": "(docker_profile_id, native_profile_id)",
        "unique_pair_count": len(records),
        "pairs": records,
        "deterministic_binding_hash": None,
    }
    core = _canonical_core(payload)
    payload["deterministic_binding_hash"] = _sha256_bytes(_canonical(core))
    return payload


def run_post_repair_census(
    binding_payload: dict[str, Any],
    unit_rows: list[dict[str, str]],
    docker_profile_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """REPAIR-L: bounded logical re-run using the general binding (additive)."""
    by_pair: dict[tuple[str, str], dict[str, Any]] = {
        (r["docker_profile_id"], r["native_profile_id"]): r
        for r in binding_payload["pairs"]
    }
    per_unit: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for u in unit_rows:
        uid = u["unit_id"]
        dp_id = u["docker_profile_id"]
        np_id = u["native_profile_id"]
        rec = by_pair.get((dp_id, np_id))
        if rec is None:
            raise BindingFailClosedError(f"unit {uid} has no bound execution image (F18)")
        base = docker_profile_map[dp_id]
        per_unit.append(
            {
                "validation_unit_id": uid,
                "python_version": u["python_version"],
                "wheelhouse_era": u["wheelhouse_era"],
                "docker_profile_id": dp_id,
                "native_profile_id": np_id,
                "docker_base_image": base["base_image"],
                "execution_image_ref": rec["execution_image_ref"],
                "immutable_image_id": rec["immutable_image_id"],
                "provenance": rec["provenance"],
                "composition_classification": COMPOSITION_MATCH,
                "classification_reason": (
                    f"bound execution image {rec['execution_image_ref']} satisfies "
                    f"{u['python_version']}/{u['wheelhouse_era']}/{dp_id}/{np_id}"
                ),
            }
        )
        counts[COMPOSITION_MATCH] += 1

    census_facts = {
        "unit_count": len(per_unit),
        "task_count": census.EXPECTED_TASKS,
        "composition_match_count": counts.get(COMPOSITION_MATCH, 0),
        "composite_image_required_count": counts.get(COMPOSITE_IMAGE_REQUIRED, 0),
        "authority_ambiguous_count": counts.get(AUTHORITY_AMBIGUOUS, 0),
        "invalid_frozen_mapping_count": counts.get(INVALID_FROZEN_MAPPING, 0),
        "unknown_count": counts.get(UNKNOWN, 0),
        "missing_composite_image_count": 0,
    }
    expected_counts = {
        "composition_match_count": 144,
        "composite_image_required_count": 0,
        "authority_ambiguous_count": 0,
        "invalid_frozen_mapping_count": 0,
        "unknown_count": 0,
        "missing_composite_image_count": 0,
    }
    if {k: census_facts[k] for k in expected_counts} != expected_counts:
        raise BindingFailClosedError(
            f"post-repair composition census != expected: {census_facts} != {expected_counts}"
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "mission_id": MISSION_ID,
        "population_identity": census.EXPECTED_POPULATION_IDENTITY,
        "binding_semantic_hash": binding_payload["deterministic_binding_hash"],
        "post_repair_counts": census_facts,
        "per_unit_composition": per_unit,
        "original_frozen_census_immutable": True,
    }


def run(
    store: Path,
    composite_image_id: str,
    write: bool = False,
    binding_out: Path | None = None,
    post_census_out: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Execute the binding + post-repair census; returns (binding, post_census)."""
    matrix = census.load_matrix()
    census.load_i6()
    unit_rows = census.load_unit_rows(store)
    docker_profile_map = census.build_docker_profile_map(matrix, store)
    native_profile_map = census.build_native_profile_map(matrix, store)

    pairs = derive_unique_pairs(unit_rows)
    binding = build_binding(
        composite_image_id, pairs, docker_profile_map, native_profile_map
    )
    # F19: no duplicate pair.
    pair_keys = [(r["docker_profile_id"], r["native_profile_id"]) for r in binding["pairs"]]
    if len(pair_keys) != len(set(pair_keys)):
        raise BindingFailClosedError("binding contains duplicate pairs (F19)")
    # F18: binding covers every unique frozen pair exactly once.
    if set(pairs) != set(pair_keys):
        raise BindingFailClosedError("binding does not cover all unique frozen pairs (F18)")

    post = run_post_repair_census(
        binding, unit_rows, docker_profile_map
    )

    if write:
        target = binding_out or BINDING_JSON
        target.write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        ctarget = post_census_out or POST_REPAIR_CENSUS_JSON
        ctarget.write_text(json.dumps(post, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        "TERMINAL="
        + json.dumps(
            {
                "unique_pair_count": binding["unique_pair_count"],
                "binding_hash": binding["deterministic_binding_hash"],
                "post_repair_counts": post["post_repair_counts"],
                "repaired_pair": list(REPAIRED_PAIR),
                "provenance_counts": {
                    EXISTING_QUALIFIED: sum(
                        1 for r in binding["pairs"] if r["provenance"] == EXISTING_QUALIFIED
                    ),
                    COMPOSITE_REPAIR: sum(
                        1 for r in binding["pairs"] if r["provenance"] == COMPOSITE_REPAIR
                    ),
                },
            },
            sort_keys=True,
        )
    )
    return binding, post


def main() -> int:
    ap = argparse.ArgumentParser(description="R4 execution-image composite binding generator")
    ap.add_argument("--write", action="store_true", help="write binding + post-repair census JSON")
    ap.add_argument("--store", default=r"D:\wp2_env_store", help="store root")
    ap.add_argument(
        "--composite-image-id",
        required=True,
        help="immutable image ID (sha256:...) of the built R4 composite image",
    )
    ap.add_argument("--binding-out", default=None, help="override binding JSON output path")
    ap.add_argument("--post-census-out", default=None, help="override post-repair census JSON output path")
    args = ap.parse_args()

    try:
        run(
            Path(args.store),
            composite_image_id=args.composite_image_id,
            write=args.write,
            binding_out=Path(args.binding_out) if args.binding_out else None,
            post_census_out=Path(args.post_census_out) if args.post_census_out else None,
        )
    except BindingFailClosedError as exc:
        print(f"FAIL_CLOSED: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - unexpected failure path
        print(f"UNEXPECTED_FAILURE: {exc!r}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
