"""Frozen Full-D7 population authority for the Full144 preexecution freeze.

Reads the frozen qualified R4 population/census authorities only.  Never
reconstructs population membership or order from memory or heuristics.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

R4_DIR = Path(__file__).resolve().parents[4] / "research" / "env-canon-r4"
CENSUS_PATH = R4_DIR / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json"
MATRIX_PATH = R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json"
BINDING_PATH = R4_DIR / "R4_EXECUTION_IMAGE_BINDING_RUNTIME_CLEAN.json"

EXPECTED_POPULATION_IDENTITY = "ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac"
EXPECTED_N_UNITS = 144
EXPECTED_N_TASKS = 219
EXPECTED_STRATA = {"3.12_poetry": 25, "3.12_uv": 21, "3.8_poetry": 15, "3.9_poetry": 83}
EXPECTED_ORDERED_MEMBERSHIP_HASH = "8eb4a7242e12bb03715adac5fffdea2e4340585843fc137ececd38952ad6a19e"
EXPECTED_BINDING_HASH = "5169c69d45f0761c85792ec182c9e949f58d8c9f5a29355d5a371944293d2ef2"
EXPECTED_UNIQUE_PAIRS = 11

SOURCE_FIDELITY_UNITS = ("vu-b9808f19ace4", "vu-692af9112c6d")


class PopulationError(Exception):
    """Fail-closed population authority violation."""


def _read_json(path: Path) -> Any:
    if not path.is_file():
        raise PopulationError(f"missing frozen authority: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def ordered_unit_ids() -> list[str]:
    """Exact frozen Full-D7 unit identity/order (I6 census == matrix order)."""
    census = _read_json(CENSUS_PATH)
    if census.get("population_identity_sha256") != EXPECTED_POPULATION_IDENTITY:
        raise PopulationError("census population identity mismatch")
    units = census.get("units")
    if not isinstance(units, list) or len(units) != EXPECTED_N_UNITS:
        raise PopulationError(f"census units != {EXPECTED_N_UNITS}")
    ids = [str(u["validation_unit_id"]) for u in units]
    if len(set(ids)) != EXPECTED_N_UNITS:
        raise PopulationError("census unit ids not unique")
    return ids


def ordered_membership_hash() -> str:
    """sha256 of the canonical compact JSON of the ordered 144 unit ids."""
    payload = json.dumps(ordered_unit_ids(), separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_population() -> dict[str, Any]:
    """P2P authority gate: identity, counts, strata, order hash, binding."""
    census = _read_json(CENSUS_PATH)
    matrix = _read_json(MATRIX_PATH)
    binding = _read_json(BINDING_PATH)

    identity = census.get("population_identity_sha256")
    if identity != EXPECTED_POPULATION_IDENTITY:
        raise PopulationError("census population identity mismatch")

    census_strata = census.get("strata_counts")
    if census_strata != EXPECTED_STRATA:
        raise PopulationError(f"census strata mismatch: {census_strata}")

    census_tasks = census.get("processed_mapped_tasks")
    if census_tasks != EXPECTED_N_TASKS:
        raise PopulationError(f"census processed tasks != {EXPECTED_N_TASKS}")

    matrix_pop = matrix.get("population", {})
    if matrix_pop.get("n_validation_units") != EXPECTED_N_UNITS:
        raise PopulationError("matrix n_validation_units mismatch")
    if matrix_pop.get("n_mapped_tasks") != EXPECTED_N_TASKS:
        raise PopulationError("matrix n_mapped_tasks mismatch")
    if matrix_pop.get("population_identity_sha256") != EXPECTED_POPULATION_IDENTITY:
        raise PopulationError("matrix population identity mismatch")

    # exact frozen order: census units == matrix units == store CSV (frozen)
    census_ids = ordered_unit_ids()
    matrix_units = matrix.get("units")
    matrix_ids = [str(u["validation_unit_id"]) for u in matrix_units]
    if matrix_ids != census_ids:
        raise PopulationError("matrix order != census order")

    binding_hash = binding.get("deterministic_binding_hash")
    if binding_hash != EXPECTED_BINDING_HASH:
        raise PopulationError(f"binding hash mismatch: {binding_hash}")
    if binding.get("unique_pair_count") != EXPECTED_UNIQUE_PAIRS:
        raise PopulationError("binding unique_pair_count mismatch")
    pairs = binding.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != EXPECTED_UNIQUE_PAIRS:
        raise PopulationError("binding pairs != 11")

    bound: list[str] = []
    for p in pairs:
        bound.extend(p.get("member_validation_unit_ids", []))
    if len(set(bound)) != EXPECTED_N_UNITS:
        raise PopulationError("binding members != 144 unique")
    if set(bound) != set(census_ids):
        raise PopulationError("binding membership != census membership")

    membership_hash = ordered_membership_hash()
    if membership_hash != EXPECTED_ORDERED_MEMBERSHIP_HASH:
        raise PopulationError(
            f"ordered membership hash mismatch: {membership_hash} != {EXPECTED_ORDERED_MEMBERSHIP_HASH}"
        )

    return {
        "population_identity": identity,
        "n_validation_units": EXPECTED_N_UNITS,
        "n_mapped_tasks": EXPECTED_N_TASKS,
        "strata": EXPECTED_STRATA,
        "ordered_membership_hash": membership_hash,
        "binding_hash": binding_hash,
        "unique_pairs": EXPECTED_UNIQUE_PAIRS,
        "order_authority": "R4_I6 census == R4_CAPABILITY_MATRIX == VALIDATION_UNIT_MATRIX.csv",
    }
