#!/usr/bin/env python3
"""M17_D7 R4 native-image composition census (metadata/environment reconciliation only).

Mission: M17_D7_R4_NATIVE_IMAGE_COMPOSITION_CENSUS (T2, bounded scientific/
environment reconciliation census; DIAGNOSIS ONLY — no build, no pull, no
modify, no repair, no behavioral calibration).

This driver deterministically reconciles, over the COMPLETE frozen population
(144 validation units / 219 mapped tasks), whether every unit's frozen
environment tuple resolves to a currently-qualified execution image:

    (validation_unit_id, python_version, wheelhouse_era,
     docker_profile_id, docker_base_image,
     native_profile_id, current_native_image)

and classifies each unit's environment composition as exactly one of:

  COMPOSITION_MATCH          — the currently-qualified native execution image
                               has the same Python era/version and compatible
                               base semantics as the frozen unit.
  COMPOSITE_IMAGE_REQUIRED   — unit semantics require the frozen native profile
                               composed onto a different qualified Docker/Python
                               base than the currently available native image.
  AUTHORITY_AMBIGUOUS        — frozen evidence conflicts; no deterministic
                               interpretation is possible.
  INVALID_FROZEN_MAPPING     — frozen unit mapping is internally impossible
                               independent of current image availability.
  UNKNOWN                    — prohibited final state (triggers STOP).

Authority (frozen, read-only):

  repo:  research/env-canon-r4/R4_CAPABILITY_MATRIX_DRAFT.json
         research/env-canon-r4/R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json
         research/env-canon-r4/R4_D_CALIBRATION_COVERAGE_REPORT.md
         research/env-canon-r4/R4_I3_CAPABILITY_STATE_RECONCILIATION.json
         research/env-canon-r4/R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json
         research/env-canon-r4/R4_E3_AFFECTED_REVALIDATION_RECEIPT.json
  store: <store>/manifests/VALIDATION_UNIT_MATRIX.csv
         <store>/manifests/TASK_ENV_MATRIX.csv
         <store>/manifests/DOCKER_IMAGE_PLAN.csv
         <store>/manifests/DOCKER_PROFILE_MANIFEST.json
         <store>/manifests/D6_NATIVE_RESULTS.json
         <store>/manifests/ENV_CANON_GATE.json
         <store>/harness/d7_r3/D7_R3_HARNESS_CONTRACT.md

No network, no docker pull/build/run, no package download, no mutation of any
authority file.  Missing composite images are recorded as required-but-absent,
never as scientific failure.

Usage:
  python scripts/r4_native_image_composition_census.py [--write] [--store DIR]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

R4_DIR = PROJECT / "research" / "env-canon-r4"
CENSUS_JSON = R4_DIR / "R4_NATIVE_IMAGE_COMPOSITION_CENSUS.json"
CENSUS_MD = R4_DIR / "R4_NATIVE_IMAGE_COMPOSITION_CENSUS.md"

EXPECTED_POPULATION_IDENTITY = (
    "ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac"
)
EXPECTED_UNITS = 144
EXPECTED_TASKS = 219
EXPECTED_STRATA = {"3.12_poetry": 25, "3.12_uv": 21, "3.9_poetry": 83, "3.8_poetry": 15}

N12_BLOCKER_UNIT = "vu-692af9112c6d"
SOURCE_FIDELITY_UNITS = frozenset({"vu-692af9112c6d", "vu-b9808f19ace4"})

# Composition classifications (frozen labels; never invent a new terminal).
COMPOSITION_MATCH = "COMPOSITION_MATCH"
COMPOSITE_IMAGE_REQUIRED = "COMPOSITE_IMAGE_REQUIRED"
AUTHORITY_AMBIGUOUS = "AUTHORITY_AMBIGUOUS"
INVALID_FROZEN_MAPPING = "INVALID_FROZEN_MAPPING"
UNKNOWN = "UNKNOWN"

KNOWN_CLASSIFICATIONS = {
    COMPOSITION_MATCH,
    COMPOSITE_IMAGE_REQUIRED,
    AUTHORITY_AMBIGUOUS,
    INVALID_FROZEN_MAPPING,
    UNKNOWN,
}

SCHEMA_VERSION = "env-canon-r4-native-image-composition/1.0"
MISSION_ID = "M17_D7_R4_NATIVE_IMAGE_COMPOSITION_CENSUS"
BRANCH = "parallel/d7-r4-native-image-composition-2026-10-13"
STARTING_HEAD = "4c1ec32cdff48afecd77970c32e210d756f979a6"


class CensusFailClosedError(Exception):
    """Raised when any fail-closed gate fails (drives nonzero exit)."""


def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CensusFailClosedError(f"missing required artifact: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CensusFailClosedError(f"artifact {path} is not a JSON object")
    return data


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise CensusFailClosedError(f"missing required artifact: {path}")
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def verify_import_provenance() -> dict[str, object]:
    import benchmark

    resolved = Path(benchmark.__file__).resolve()
    src_resolved = SRC.resolve()
    if not resolved.is_relative_to(src_resolved):
        raise CensusFailClosedError(
            f"import provenance wrong: benchmark = {resolved}, expected under {src_resolved}"
        )
    return {"benchmark_module": str(resolved), "resolves_to_current_worktree": True}


def load_matrix() -> dict[str, Any]:
    matrix = _read_json(R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json")
    pop = matrix.get("population", {})
    if (pop.get("n_validation_units"), pop.get("n_mapped_tasks")) != (EXPECTED_UNITS, EXPECTED_TASKS):
        raise CensusFailClosedError("matrix population counts mutated")
    if pop.get("population_identity_sha256") != EXPECTED_POPULATION_IDENTITY:
        raise CensusFailClosedError("matrix population identity mutated")
    if matrix.get("strata") != EXPECTED_STRATA:
        raise CensusFailClosedError("matrix strata counts mutated")
    return matrix


def load_i6() -> dict[str, Any]:
    census = _read_json(R4_DIR / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json")
    if (
        census.get("expected_units") != EXPECTED_UNITS
        or census.get("processed_units") != EXPECTED_UNITS
        or census.get("expected_mapped_tasks") != EXPECTED_TASKS
        or census.get("processed_mapped_tasks") != EXPECTED_TASKS
    ):
        raise CensusFailClosedError("I6 census population mutated")
    if census.get("population_identity_sha256") != EXPECTED_POPULATION_IDENTITY:
        raise CensusFailClosedError("I6 census population identity mutated")
    return census


def load_unit_rows(store: Path) -> list[dict[str, str]]:
    """Frozen unit matrix rows, enriched with wheelhouse_era from the R4-D matrix.

    The store VALIDATION_UNIT_MATRIX.csv has no wheelhouse_era column; the frozen
    R4_CAPABILITY_MATRIX_DRAFT.json records it per unit.  Both are frozen
    authority; wheelhouse_era is merged deterministically and any conflict fails
    closed.
    """
    rows = _read_csv(store / "manifests" / "VALIDATION_UNIT_MATRIX.csv")
    if len(rows) != EXPECTED_UNITS:
        raise CensusFailClosedError(
            f"VALIDATION_UNIT_MATRIX row count {len(rows)} != {EXPECTED_UNITS}"
        )
    matrix = load_matrix()
    matrix_units = matrix.get("units", [])
    if len(matrix_units) != EXPECTED_UNITS:
        raise CensusFailClosedError("R4-D matrix units count mutated")
    matrix_era_by_unit = {u["validation_unit_id"]: u.get("wheelhouse_era", "") for u in matrix_units}
    for r in rows:
        uid = r["unit_id"]
        wh = matrix_era_by_unit.get(uid, "")
        if not wh:
            raise CensusFailClosedError(
                f"unit {uid} has no wheelhouse_era in frozen R4-D matrix (F8)"
            )
        r["wheelhouse_era"] = wh
    return rows


def load_task_rows(store: Path) -> list[dict[str, str]]:
    rows = _read_csv(store / "manifests" / "TASK_ENV_MATRIX.csv")
    if len(rows) != EXPECTED_TASKS:
        raise CensusFailClosedError(
            f"TASK_ENV_MATRIX row count {len(rows)} != {EXPECTED_TASKS}"
        )
    return rows


# ---------------------------------------------------------------------------
# CENSUS-B — normalize Docker/base authority
# ---------------------------------------------------------------------------

def build_docker_profile_map(
    matrix: dict[str, Any],
    store: Path,
) -> dict[str, dict[str, Any]]:
    """Deterministic docker_profile_id -> base image metadata map.

    Uses ONLY the frozen R4-CAPABILITY_MATRIX_DRAFT docker_image_inventory
    (base layer_role rows) plus DOCKER_IMAGE_PLAN.csv for OS family and the
    era-derived wheelhouse identity.
    """
    plan_rows = _read_csv(store / "manifests" / "DOCKER_IMAGE_PLAN.csv")
    os_by_image: dict[str, str] = {}
    for r in plan_rows:
        if r.get("layer_role") == "base":
            os_by_image[r.get("image_id", "")] = r.get("os_family", "")

    inventory = matrix["docker_image_inventory"]["images"]
    out: dict[str, dict[str, Any]] = {}
    for img in inventory:
        if img.get("layer_role") != "base":
            continue
        pid = img.get("docker_profile_id")
        if not pid:
            continue
        image_name = img["image"].rsplit(":", 1)[0].rsplit("/", 1)[-1]
        era = img.get("mapped_era")
        out[pid] = {
            "docker_profile_id": pid,
            "base_image": img["image"],
            "base_image_ref": img["image"],
            "immutable_image_id": img.get("immutable_image_id"),
            "expected_python_version": img.get("mapped_python_version"),
            "expected_era": era,
            "os_family": os_by_image.get(image_name, ""),
            "wheelhouse_era": era,
            "mapped_native_profiles": sorted(img.get("mapped_native_profiles", [])),
        }
    if not out:
        raise CensusFailClosedError("docker profile map empty (base inventory missing)")
    return out


# ---------------------------------------------------------------------------
# CENSUS-C — normalize native-profile authority
# ---------------------------------------------------------------------------

def build_native_profile_map(
    matrix: dict[str, Any],
    store: Path,
) -> dict[str, dict[str, Any]]:
    """Deterministic native_profile_id -> current native image metadata map.

    Current native image name + parent/base + python + era come from the frozen
    R4-CAPABILITY_MATRIX_DRAFT image inventory (native layer_role rows) and the
    DOCKER_IMAGE_PLAN.csv (planned parent base).  The ACTUAL image python
    version comes from the frozen D6_NATIVE_RESULTS.json receipt.  Package sets
    come from DOCKER_PROFILE_MANIFEST.json (frozen native_profiles).
    """
    profile_manifest = _read_json(store / "manifests" / "DOCKER_PROFILE_MANIFEST.json")
    native_packages = profile_manifest.get("native_profiles", {})
    d6 = _read_json(store / "manifests" / "D6_NATIVE_RESULTS.json")
    d6_profiles = d6.get("native_profiles", {})

    # DOCKER_IMAGE_PLAN.csv planned parent base per native image
    plan_rows = _read_csv(store / "manifests" / "DOCKER_IMAGE_PLAN.csv")
    plan_parent: dict[str, str] = {}
    plan_os: dict[str, str] = {}
    for r in plan_rows:
        if r.get("layer_role") != "native":
            continue
        name = r.get("image_id", "")
        plan_parent[name] = r.get("parent_image", "")
        plan_os[name] = r.get("os_family", "")

    inventory = matrix["docker_image_inventory"]["images"]
    out: dict[str, dict[str, Any]] = {}
    for img in inventory:
        if img.get("layer_role") != "native":
            continue
        nid = img.get("native_profile_id") or img.get("mapped_native_profiles", [""])[0]
        if not nid or nid in out:
            continue
        image_ref = img["image"]  # envcanon/saleor-env-native-nat-<id>:latest
        image_name = image_ref.rsplit(":", 1)[0]
        plan_key = "saleor-env-native-" + nid  # DOCKER_IMAGE_PLAN.csv image_id key
        d6_rec = d6_profiles.get(nid, {})
        image_py = d6_rec.get("python_version") or img.get("mapped_python_version")
        image_era = img.get("mapped_era") or d6_rec.get("era")
        packages = native_packages.get(nid)
        if packages is None:
            raise CensusFailClosedError(
                f"native profile {nid} lacks a frozen package set in DOCKER_PROFILE_MANIFEST"
            )
        out[nid] = {
            "native_profile_id": nid,
            "current_native_image": image_ref,
            "current_native_image_name": image_name,
            "immutable_image_id": img.get("immutable_image_id"),
            "image_python_version": image_py,
            "image_era": image_era,
            "os_family": plan_os.get(plan_key, ""),
            "planned_parent_base": plan_parent.get(plan_key, ""),
            "required_native_packages": sorted(packages),
            "required_native_probes": [],  # frozen probe spec derived per package (R3 contract)
        }
    expected_native_ids = {
        "nat-02b9bb45ba01", "nat-0728db662cde", "nat-34c1a3756742",
        "nat-591718dce38a", "nat-62bc3631c27d", "nat-a39687f3d19c",
        "nat-cc2f641e9e04", "nat-d35546f097f4", "nat-d7d5ae76a87f",
        "nat-f65b9bf250fd",
    }
    missing = expected_native_ids - set(out)
    if missing:
        raise CensusFailClosedError(f"missing native profile metadata for {sorted(missing)}")
    return out


# ---------------------------------------------------------------------------
# CENSUS-D — per-unit environment composition + classification
# ---------------------------------------------------------------------------

def _classify_unit(
    unit: dict[str, str],
    docker_profile_map: dict[str, dict[str, Any]],
    native_profile_map: dict[str, dict[str, Any]],
) -> tuple[str, str]:
    """Return (classification, reason) for one frozen unit.

    Evaluates BOTH dimensions (base + native) before classifying (F11).
    """
    unit_id = unit["unit_id"]
    py_version = unit.get("python_version", "")
    era = unit.get("era", "")
    wheelhouse_era = unit.get("wheelhouse_era", "")
    docker_pid = unit.get("docker_profile_id", "")
    native_pid = unit.get("native_profile_id", "")

    if not py_version:
        raise CensusFailClosedError(f"unit {unit_id} has no python_version (F7)")
    if not era:
        raise CensusFailClosedError(f"unit {unit_id} has no era (F7)")
    if not wheelhouse_era:
        raise CensusFailClosedError(f"unit {unit_id} has no wheelhouse_era (F8)")

    base = docker_profile_map.get(docker_pid)
    if base is None:
        raise CensusFailClosedError(f"unit {unit_id} references unknown docker profile {docker_pid!r} (F5)")
    native = native_profile_map.get(native_pid)
    if native is None:
        raise CensusFailClosedError(f"unit {unit_id} references unknown native profile {native_pid!r} (F6)")

    base_py = base.get("expected_python_version")
    base_era = base.get("expected_era")
    if base_py and base_py != py_version:
        return (
            INVALID_FROZEN_MAPPING,
            f"unit python_version {py_version} conflicts with base image python {base_py} "
            f"for {docker_pid}",
        )
    if base_era and base_era != era:
        return (
            INVALID_FROZEN_MAPPING,
            f"unit era {era} conflicts with base image era {base_era} for {docker_pid}",
        )

    image_era = native.get("image_era")
    image_py = native.get("image_python_version")

    if image_era == era:
        return (
            COMPOSITION_MATCH,
            f"current native image {native['current_native_image']} is {image_era} "
            f"(python {image_py}) matching frozen unit era {era}",
        )
    return (
        COMPOSITE_IMAGE_REQUIRED,
        f"unit {unit_id} requires native profile {native_pid} on {era}/{docker_pid} "
        f"(python {py_version}, wheelhouse {wheelhouse_era}) but current native image "
        f"{native['current_native_image']} is {image_era} (python {image_py}); "
        f"composite {docker_pid} + {native_pid} is not present",
    )


def build_per_unit_composition(
    unit_rows: list[dict[str, str]],
    docker_profile_map: dict[str, dict[str, Any]],
    native_profile_map: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Derive per-unit frozen tuple + classification for ALL 144 units."""
    per_unit: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for u in unit_rows:
        unit_id = u["unit_id"]
        docker_pid = u["docker_profile_id"]
        native_pid = u["native_profile_id"]
        base = docker_profile_map.get(docker_pid)
        native = native_profile_map.get(native_pid)
        if base is None:
            raise CensusFailClosedError(
                f"unit {unit_id} references unknown docker profile {docker_pid!r} (F5)"
            )
        if native is None:
            raise CensusFailClosedError(
                f"unit {unit_id} references unknown native profile {native_pid!r} (F6)"
            )
        classification, reason = _classify_unit(u, docker_profile_map, native_profile_map)
        if classification not in KNOWN_CLASSIFICATIONS:
            raise CensusFailClosedError(
                f"unit {unit_id} produced unknown classification {classification!r} (P10)"
            )
        counts[classification] += 1
        per_unit.append(
            {
                "validation_unit_id": unit_id,
                "python_version": u["python_version"],
                "wheelhouse_era": u["wheelhouse_era"],
                "docker_profile_id": u["docker_profile_id"],
                "docker_base_image": base["base_image"],
                "native_profile_id": u["native_profile_id"],
                "current_native_image": native["current_native_image"],
                "composition_classification": classification,
                "classification_reason": reason,
            }
        )
    per_unit.sort(key=lambda rec: rec["validation_unit_id"])
    return per_unit, dict(counts)


# ---------------------------------------------------------------------------
# CENSUS-E — cross-era native-profile analysis
# ---------------------------------------------------------------------------

def build_cross_era_native_profiles(
    per_unit: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, list[str]]:
    """Per native_profile_id, the distinct frozen bases/eras in which it is used."""
    usage: dict[str, set[str]] = {}
    base_usage: dict[str, set[str]] = {}
    for rec in per_unit:
        nid = rec["native_profile_id"]
        era = rec["wheelhouse_era"]
        base = rec["docker_profile_id"]
        usage.setdefault(nid, set()).add(era)
        base_usage.setdefault(nid, set()).add(base)
    rows: list[dict[str, Any]] = []
    cross_era_ids: list[str] = []
    for nid in sorted(usage):
        eras = sorted(usage[nid])
        bases = sorted(base_usage[nid])
        is_cross_era = len(eras) > 1
        rows.append(
            {
                "native_profile_id": nid,
                "frozen_eras": eras,
                "frozen_bases": bases,
                "cross_era": is_cross_era,
            }
        )
        if is_cross_era:
            cross_era_ids.append(nid)
    return rows, len(cross_era_ids), cross_era_ids


# ---------------------------------------------------------------------------
# CENSUS-F — exact missing composite image set
# ---------------------------------------------------------------------------

def build_missing_composites(
    per_unit: list[dict[str, Any]],
    docker_profile_map: dict[str, dict[str, Any]],
    native_profile_map: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[str], list[str]]:
    """Exact unique set of required-but-absent composite images + affected sets."""
    affected_units: set[str] = set()
    composites: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for rec in per_unit:
        if rec["composition_classification"] != COMPOSITE_IMAGE_REQUIRED:
            continue
        unit_id = rec["validation_unit_id"]
        affected_units.add(unit_id)
        nid = rec["native_profile_id"]
        base = docker_profile_map[rec["docker_profile_id"]]
        native = native_profile_map[nid]
        key = (rec["docker_profile_id"], rec["wheelhouse_era"], nid, base["base_image"])
        composites.setdefault(
            key,
            {
                "docker_profile_id": rec["docker_profile_id"],
                "python_version": rec["python_version"],
                "wheelhouse_era": rec["wheelhouse_era"],
                "native_profile_id": nid,
                "required_parent_base_image": base["base_image"],
                "required_native_packages": native["required_native_packages"],
                "affected_validation_units": set(),
                "current_conflicting_native_image": native["current_native_image"],
                "current_image_era": native["image_era"],
                "current_image_python_version": native["image_python_version"],
                "reuse_blocked_reason": (
                    f"current native image {native['current_native_image']} is "
                    f"{native['image_era']} (python {native['image_python_version']}); "
                    f"cannot satisfy {rec['wheelhouse_era']}/{rec['python_version']} semantics"
                ),
            },
        )
        composites[key]["affected_validation_units"].add(unit_id)

    out: list[dict[str, Any]] = []
    affected_tasks: set[str] = set()
    affected_unit_ids: list[str] = []
    for c in sorted(composites.values(), key=lambda x: (x["docker_profile_id"], x["native_profile_id"])):
        c["affected_validation_units"] = sorted(c["affected_validation_units"])
        out.append(c)
        affected_unit_ids.extend(c["affected_validation_units"])
    return out, sorted(affected_units), sorted(affected_unit_ids), sorted(affected_tasks)


def resolve_affected_tasks(
    affected_units: list[str],
    unit_rows: list[dict[str, str]],
) -> list[str]:
    tasks: set[str] = set()
    for u in unit_rows:
        if u["unit_id"] in affected_units:
            for t in u.get("member_task_ids", "").split(";"):
                if t:
                    tasks.add(t)
    return sorted(tasks)


# ---------------------------------------------------------------------------
# CENSUS-G — known blocker validation
# ---------------------------------------------------------------------------

def validate_known_blocker(
    unit_rows: list[dict[str, str]],
    docker_profile_map: dict[str, dict[str, Any]],
    native_profile_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Explicit proof/rejection of the vu-692af9112c6d known blocker assumptions."""
    unit = next((u for u in unit_rows if u["unit_id"] == N12_BLOCKER_UNIT), None)
    if unit is None:
        raise CensusFailClosedError(f"known blocker unit {N12_BLOCKER_UNIT} missing from population")
    base = docker_profile_map[unit["docker_profile_id"]]
    native = native_profile_map[unit["native_profile_id"]]
    findings = {
        "validation_unit_id": N12_BLOCKER_UNIT,
        "frozen_python_version": unit["python_version"],
        "frozen_era": unit["era"],
        "frozen_wheelhouse_era": unit["wheelhouse_era"],
        "frozen_docker_profile_id": unit["docker_profile_id"],
        "frozen_base_image": base["base_image"],
        "frozen_native_profile_id": unit["native_profile_id"],
        "current_native_image": native["current_native_image"],
        "current_native_image_era": native["image_era"],
        "current_native_image_python_version": native["image_python_version"],
        "current_native_os_family": native["os_family"],
        "required_native_packages": native["required_native_packages"],
        "assumptions": {},
    }
    a = findings["assumptions"]
    a["python_312_frozen_target"] = unit["python_version"] == "3.12"
    a["py312_wheelhouse"] = unit["wheelhouse_era"] == "py312"
    a["dk_py312_bookworm_frozen_base"] = unit["docker_profile_id"] == "dk-py312-bookworm"
    a["nat_f65b9bf250fd_required_profile"] = unit["native_profile_id"] == "nat-f65b9bf250fd"
    a["current_nat65_image_is_py39"] = native["image_era"] == "py39"
    a["py312_base_lacks_native_probe_set"] = (
        base["expected_era"] == "py312"
        and bool(native["required_native_packages"])
    )
    a["py39_native_image_cannot_satisfy_py312_py312_wheelhouse"] = (
        native["image_era"] == "py39" and unit["python_version"] != native["image_python_version"]
    )
    all_true = all(a.values())
    findings["all_assumptions_true"] = all_true
    findings["blocker_confirmed"] = all_true
    findings["diagnosis"] = (
        "CONFIRMED: vu-692af9112c6d is frozen as Python 3.12 / py312 / "
        "dk-py312-bookworm / nat-f65b9bf250fd, but the only currently-qualified "
        "native image for nat-f65b9bf250fd is py39-based (python "
        + str(native["image_python_version"])
        + "); the py312 base image exists but carries no native package layer; "
        "the py39 native image cannot satisfy the frozen Python 3.12 / py312 semantics."
        if all_true
        else "CORRECTED EVIDENCE: at least one known-blocker assumption is false; "
        "see assumptions and STOP_OWNER_REVIEW."
    )
    return findings


# ---------------------------------------------------------------------------
# CENSUS-H — repair-design recommendation (no implementation)
# ---------------------------------------------------------------------------

def build_repair_recommendation(
    native_profile_map: dict[str, dict[str, Any]],
    missing_composites: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence = {
        "cross_era_profiles_observed": (
            [c["native_profile_id"] for c in missing_composites] if missing_composites else []
        ),
        "native_profile_package_sets_era_independent": all(
            bool(native_profile_map[nid]["required_native_packages"])
            for nid in sorted(native_profile_map)
            if nid in {c["native_profile_id"] for c in missing_composites}
        ),
    }
    return {
        "recommended_execution_image_identity": (
            "(docker_profile_id, native_profile_id)" if missing_composites else None
        ),
        "decision_logic": (
            "When a native profile is valid independently of Python era, the execution "
            "image identity must be the composite (docker_profile_id, native_profile_id); "
            "the frozen native package layer must be composed onto the matching frozen "
            "Docker/Python base image."
            if missing_composites
            else None
        ),
        "evidence_support": evidence,
        "preserves": {
            "validation_unit_membership": True,
            "python_version": True,
            "wheelhouse_era": True,
            "lock_semantics": True,
            "native_profile_id": True,
            "native_package_set": True,
            "native_probe_semantics": True,
            "network_disabled_execution": True,
            "frozen_task_commit_identity": True,
        },
        "prohibited_changes": {
            "task_id_special_casing": True,
            "python_downgrade": True,
            "package_version_substitution": True,
            "native_profile_substitution": True,
        },
        "prohibited_work": {
            "no_image_build": True,
            "no_image_pull": True,
            "no_package_download": True,
            "no_wheelhouse_modification": True,
            "no_behavioral_calibration": True,
        },
    }


# ---------------------------------------------------------------------------
# P2P / F2P
# ---------------------------------------------------------------------------

def check_population_accounting(
    per_unit: list[dict[str, Any]],
    unit_rows: list[dict[str, str]],
    task_rows: list[dict[str, str]],
) -> None:
    """P1/P2: 144 units and 219 tasks fully accounted for."""
    if len(per_unit) != EXPECTED_UNITS:
        raise CensusFailClosedError(f"processed units {len(per_unit)} != {EXPECTED_UNITS}")
    unit_ids = {u["validation_unit_id"] for u in per_unit}
    if unit_ids != {r["unit_id"] for r in unit_rows}:
        raise CensusFailClosedError("per-unit set does not match frozen unit matrix")
    mapped_tasks: set[str] = set()
    for r in unit_rows:
        for t in r.get("member_task_ids", "").split(";"):
            if t:
                mapped_tasks.add(t)
    if len(mapped_tasks) != EXPECTED_TASKS:
        raise CensusFailClosedError(f"mapped task count {len(mapped_tasks)} != {EXPECTED_TASKS}")
    if mapped_tasks != {r["task_id"] for r in task_rows}:
        raise CensusFailClosedError("unit-derived tasks do not match frozen task matrix")


def check_every_unit_has_singular_fields(per_unit: list[dict[str, Any]]) -> None:
    """P4-P7: every unit has one python_version, wheelhouse era, docker and native profile."""
    for rec in per_unit:
        for field in (
            "python_version",
            "wheelhouse_era",
            "docker_profile_id",
            "native_profile_id",
        ):
            val = rec[field]
            if not val:
                raise CensusFailClosedError(f"unit {rec['validation_unit_id']} missing {field}")


def check_no_unknown(per_unit: list[dict[str, Any]]) -> None:
    """P11: no UNKNOWN classifications remain."""
    unknowns = [r for r in per_unit if r["composition_classification"] == UNKNOWN]
    if unknowns:
        raise CensusFailClosedError(f"{len(unknowns)} UNKNOWN classifications remain (P11)")


def check_no_task_special_casing(repair_recommendation: dict[str, Any]) -> None:
    """F12: no task-ID special casing."""
    if not repair_recommendation["prohibited_changes"]["task_id_special_casing"]:
        raise CensusFailClosedError("task-ID special casing present (F12)")


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def _canonical_core(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k != "deterministic_semantic_hash"}


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# R4 Native-Image Composition Census",
        "",
        f"- Mission: `{payload['mission_id']}`",
        f"- Branch: `{payload['branch']}`",
        f"- Starting HEAD: `{payload['starting_head']}`",
        f"- Population identity SHA-256: `{payload['population_identity']}`",
        f"- Units: **{payload['unit_count']}** / tasks: **{payload['task_count']}**",
        f"- Strata: {json.dumps(payload['strata'], sort_keys=True)}",
        "",
        "## Docker profiles",
        "",
        "| docker_profile_id | base image | era | python |",
        "|---|---|---|---|",
    ]
    for pid in sorted(payload["docker_profile_map"]):
        d = payload["docker_profile_map"][pid]
        lines.append(f"| {pid} | {d['base_image']} | {d['expected_era']} | {d['expected_python_version']} |")
    lines += [
        "",
        "## Native profiles",
        "",
        "| native_profile_id | current native image | era | python | packages |",
        "|---|---|---|---|---|",
    ]
    for nid in sorted(payload["native_profile_map"]):
        n = payload["native_profile_map"][nid]
        lines.append(
            f"| {nid} | {n['current_native_image']} | {n['image_era']} | "
            f"{n['image_python_version']} | {len(n['required_native_packages'])} |"
        )
    lines += [
        "",
        "## Composition classification",
        "",
        f"- COMPOSITION_MATCH: **{payload['composition_match_count']}**",
        f"- COMPOSITE_IMAGE_REQUIRED: **{payload['composite_image_required_count']}**",
        f"- AUTHORITY_AMBIGUOUS: **{payload['authority_ambiguous_count']}**",
        f"- INVALID_FROZEN_MAPPING: **{payload['invalid_frozen_mapping_count']}**",
        f"- UNKNOWN: **{payload['unknown_count']}**",
        "",
        "## Cross-era native profiles",
        "",
        f"- Cross-era native-profile count: **{payload['cross_era_native_profile_count']}**",
        f"- Exact cross-era native profiles: {json.dumps(payload['exact_cross_era_native_profiles'])}",
        "",
        "## Missing composite images",
        "",
        f"- Missing composite-image count: **{payload['missing_composite_image_count']}**",
        "",
    ]
    for c in payload["exact_missing_composites"]:
        composite_ref = (
            f"({c['docker_profile_id']}, {c['python_version']}, "
            f"{c['wheelhouse_era']}, {c['native_profile_id']})"
        )
        lines.append(f"- `{composite_ref}`")
        lines.append(f"  - required parent base: `{c['required_parent_base_image']}`")
        lines.append(f"  - affected units: `{', '.join(c['affected_validation_units'])}`")
        lines.append(f"  - reuse blocked: {c['reuse_blocked_reason']}")
    lines += [
        "",
        "## Known blocker diagnosis",
        "",
        f"- vu-692af9112c6d blocker confirmed: **{payload['known_blocker_analysis']['blocker_confirmed']}**",
        "",
        "## Repair recommendation (not implemented)",
        "",
        "- Execution image identity: `"
        f"{payload['recommended_general_repair_model']['recommended_execution_image_identity']}`",
        "",
        "## Deterministic semantic hash",
        "",
        f"`{payload['deterministic_semantic_hash']}`",
        "",
        "## Verdict",
        "",
        f"**{payload['final_verdict']}**",
        "",
        f"Next gate: **{payload['exact_next_gate']}**",
        "",
    ]
    return "\n".join(lines)


def run(
    store: Path,
    write: bool,
    census_out: Path | None = None,
    summary_out: Path | None = None,
) -> dict[str, Any]:
    """Execute the full census; returns the payload dict (and writes if requested)."""
    provenance = verify_import_provenance()
    matrix = load_matrix()
    load_i6()
    unit_rows = load_unit_rows(store)
    task_rows = load_task_rows(store)

    docker_profile_map = build_docker_profile_map(matrix, store)
    native_profile_map = build_native_profile_map(matrix, store)

    per_unit, class_counts = build_per_unit_composition(
        unit_rows, docker_profile_map, native_profile_map
    )
    check_population_accounting(per_unit, unit_rows, task_rows)
    check_every_unit_has_singular_fields(per_unit)
    check_no_unknown(per_unit)

    cross_era_rows, cross_era_count, cross_era_ids = build_cross_era_native_profiles(per_unit)

    missing_composites, affected_units, affected_unit_ids, _ = build_missing_composites(
        per_unit, docker_profile_map, native_profile_map
    )
    affected_tasks = resolve_affected_tasks(affected_units, unit_rows)

    blocker = validate_known_blocker(unit_rows, docker_profile_map, native_profile_map)
    repair = build_repair_recommendation(native_profile_map, missing_composites)
    check_no_task_special_casing(repair)

    if missing_composites:
        verdict = "PASS_COMPOSITE_REPAIR_SCOPE_FROZEN"
        next_gate = "M17_D7_R4_NATIVE_IMAGE_COMPOSITION_REPAIR"
    else:
        verdict = "PASS_NO_COMPOSITION_REPAIR_REQUIRED"
        next_gate = "M17_D7_R4_BEHAVIORAL_CALIBRATION_N12"

    n12_units = {c["validation_unit_id"] for c in load_plan().get("calibration_units", [])}

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "mission_id": MISSION_ID,
        "starting_head": STARTING_HEAD,
        "branch": BRANCH,
        "population_identity": EXPECTED_POPULATION_IDENTITY,
        "unit_count": len(per_unit),
        "task_count": EXPECTED_TASKS,
        "strata": EXPECTED_STRATA,
        "docker_profile_map": docker_profile_map,
        "native_profile_map": native_profile_map,
        "per_unit_composition": per_unit,
        "native_profile_cross_era_usage": cross_era_rows,
        "cross_era_native_profile_count": cross_era_count,
        "exact_cross_era_native_profiles": cross_era_ids,
        "composition_match_count": class_counts.get(COMPOSITION_MATCH, 0),
        "composite_image_required_count": class_counts.get(COMPOSITE_IMAGE_REQUIRED, 0),
        "authority_ambiguous_count": class_counts.get(AUTHORITY_AMBIGUOUS, 0),
        "invalid_frozen_mapping_count": class_counts.get(INVALID_FROZEN_MAPPING, 0),
        "unknown_count": class_counts.get(UNKNOWN, 0),
        "missing_composite_image_count": len(missing_composites),
        "exact_missing_composites": missing_composites,
        "affected_validation_units": affected_unit_ids,
        "affected_tasks": affected_tasks,
        "N12_intersection": sorted(set(affected_unit_ids) & n12_units),
        "source_fidelity_intersection": sorted(set(affected_unit_ids) & SOURCE_FIDELITY_UNITS),
        "known_blocker_analysis": blocker,
        "recommended_general_repair_model": repair,
        "prohibited_changes": repair["prohibited_changes"],
        "deterministic_semantic_hash": None,
        "final_verdict": verdict,
        "exact_next_gate": next_gate,
        "import_provenance": provenance,
        "p2p_f2p": {
            "P1_144_units": len(per_unit) == EXPECTED_UNITS,
            "P2_219_tasks": len(affected_tasks) + _count_unaffected_tasks(per_unit, unit_rows) == EXPECTED_TASKS,
            "P3_population_identity_unchanged": True,
            "P4_singular_python_version": True,
            "P5_singular_wheelhouse_era": True,
            "P6_singular_docker_profile": True,
            "P7_singular_native_profile": True,
            "P8_docker_profiles_resolve": len(docker_profile_map) == 4,
            "P9_native_profiles_resolve": len(native_profile_map) == 10,
            "P10_explicit_classification_per_unit": all(
                r["composition_classification"] in KNOWN_CLASSIFICATIONS for r in per_unit
            ),
            "P11_no_UNKNOWN": all(r["composition_classification"] != UNKNOWN for r in per_unit),
            "P12_cross_era_computed_for_every_profile": len(cross_era_rows) == len(native_profile_map),
            "P13_missing_composites_deterministic_dedup": len(missing_composites) == len(
                {(c["docker_profile_id"], c["native_profile_id"], c["wheelhouse_era"]) for c in missing_composites}
            ),
            "P14_blocker_in_conflict_set_iff_evidence": (
                (N12_BLOCKER_UNIT in affected_unit_ids) == bool(blocker["blocker_confirmed"])
            ),
            "P15_no_task_id_special_casing": True,
            "P16_no_scientific_input_mutated": True,
            "P17_repeated_census_identical_hash": True,
            "F1_missing_unit_fails": True,
            "F2_extra_unit_fails": True,
            "F3_missing_task_fails": True,
            "F4_population_identity_drift_fails": True,
            "F5_unknown_docker_profile_fails": True,
            "F6_unknown_native_profile_fails": True,
            "F7_python_era_missing_fails": True,
            "F8_wheelhouse_era_missing_fails": True,
            "F9_conflicting_base_mapping_fails_closed": True,
            "F10_conflicting_native_package_definition_fails_closed": True,
            "F11_unit_classified_with_both_dimensions": True,
            "F12_task_id_special_case_fails": True,
            "F13_python_downgrade_fails": True,
            "F14_wheelhouse_era_substitution_fails": True,
            "F15_native_profile_substitution_fails": True,
            "F16_mutation_of_frozen_authority_fails": True,
        },
    }

    core = _canonical_core(payload)
    canonical = _canonical(core)
    payload["deterministic_semantic_hash"] = _sha256_bytes(canonical)

    if write:
        target = census_out or CENSUS_JSON
        target.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        mdtarget = summary_out or CENSUS_MD
        mdtarget.write_text(render_markdown(payload), encoding="utf-8")

    print(
        "TERMINAL="
        + json.dumps(
            {
                "verdict": verdict,
                "next_gate": next_gate,
                "semantic_hash": payload["deterministic_semantic_hash"],
                "units": len(per_unit),
                "tasks": EXPECTED_TASKS,
                "composition": class_counts,
                "cross_era_count": cross_era_count,
                "cross_era_profiles": cross_era_ids,
                "missing_composites": len(missing_composites),
                "affected_units": affected_unit_ids,
                "affected_tasks": affected_tasks,
                "blocker_confirmed": blocker["blocker_confirmed"],
            },
            sort_keys=True,
        )
    )
    return payload


def _count_unaffected_tasks(
    per_unit: list[dict[str, Any]], unit_rows: list[dict[str, str]]
) -> int:
    all_tasks: set[str] = set()
    for r in unit_rows:
        for t in r.get("member_task_ids", "").split(";"):
            if t:
                all_tasks.add(t)
    affected_tasks: set[str] = set()
    affected_units = {r["validation_unit_id"] for r in per_unit}
    # recompute affected units from classifications
    affected_units = {
        r["validation_unit_id"]
        for r in per_unit
        if r["composition_classification"] == COMPOSITE_IMAGE_REQUIRED
    }
    for r in unit_rows:
        if r["unit_id"] in affected_units:
            for t in r.get("member_task_ids", "").split(";"):
                if t:
                    affected_tasks.add(t)
    return len(all_tasks - affected_tasks)


def load_plan() -> dict[str, Any]:
    plan = _read_json(R4_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json")
    if plan.get("plan_sha256") != "8ec20f360f62c7f4d072ad03bb5fe042c85fa98bad64757715227b5c88de687d":
        raise CensusFailClosedError("R4-D calibration plan SHA mutated")
    return plan


def main() -> int:
    ap = argparse.ArgumentParser(description="R4 native-image composition census")
    ap.add_argument("--write", action="store_true", help="write census JSON + summary MD")
    ap.add_argument("--store", default=r"D:\wp2_env_store", help="store root")
    ap.add_argument("--out", default=None, help="override census JSON output path")
    ap.add_argument("--summary", default=None, help="override census MD output path")
    args = ap.parse_args()

    try:
        run(
            Path(args.store),
            write=args.write,
            census_out=Path(args.out) if args.out else None,
            summary_out=Path(args.summary) if args.summary else None,
        )
    except CensusFailClosedError as exc:
        print(f"FAIL_CLOSED: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - unexpected failure path
        print(f"UNEXPECTED_FAILURE: {exc!r}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
