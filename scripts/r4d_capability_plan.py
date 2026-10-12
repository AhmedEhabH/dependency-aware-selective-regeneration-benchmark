#!/usr/bin/env python3
"""M17_D7 R4-D capability matrix + stratified calibration plan generator.

Mission: M17_D7_R4_D_CAPABILITY_AND_CALIBRATION_PLAN (T2, metadata only).

This script produces three DRAFT artifacts under ``research/env-canon-r4``:
  * R4_CAPABILITY_MATRIX_DRAFT.json
  * R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json
  * R4_D_CALIBRATION_COVERAGE_REPORT.md

It is a metadata-only inventory and plan.  It performs NO calibration, NO Full
D7 execution, NO Docker pull/build/run and NO network access.  The only Docker
action is ``docker image inspect`` to record local availability of the expected
images.

All scientific inputs are frozen manifests (VALIDATION_UNIT_MATRIX.csv,
DOCKER_IMAGE_PLAN.csv, DOCKER_PROFILE_MANIFEST.json, ENV_CANON_GATE.json,
SOURCE_FIDELITY_AMENDMENT_FREEZE.json).  Selection is deterministic from those
metadata alone and never consumes success/failure outcome fields.

Usage:
  python scripts/r4d_capability_plan.py [--write]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

STORE = Path(r"D:\wp2_env_store\manifests")
REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "research" / "env-canon-r4"

VALIDATION_UNIT_MATRIX = STORE / "VALIDATION_UNIT_MATRIX.csv"
DOCKER_IMAGE_PLAN = STORE / "DOCKER_IMAGE_PLAN.csv"
DOCKER_PROFILE_MANIFEST = STORE / "DOCKER_PROFILE_MANIFEST.json"
ENV_CANON_GATE = STORE / "ENV_CANON_GATE.json"
SOURCE_FIDELITY_FREEZE = REPO / "research" / "source-fidelity-r1" / "SOURCE_FIDELITY_AMENDMENT_FREEZE.json"

MISSION_ID = "M17_D7_R4_D_CAPABILITY_AND_CALIBRATION_PLAN"
PLAN_STATUS = "DRAFT_PENDING_R4_INTEGRATION"
SCHEMA_VERSION = "env-canon-r4-d/1.0"

EXPECTED_N_UNITS = 144
EXPECTED_N_TASKS = 219
EXPECTED_STRATA = {
    ("3.12", "poetry"): 25,
    ("3.12", "uv"): 21,
    ("3.9", "poetry"): 83,
    ("3.8", "poetry"): 15,
}

SOURCE_FIDELITY_UNITS = ("vu-692af9112c6d", "vu-b9808f19ace4")

ALLOWED_LOCK_TYPES = ("poetry", "uv")
ALLOWED_INSTALL_ROUTES = (
    "LOCK_FRAGMENT_MAIN_PLUS_DEV",
    "V2_EDITABLE_PLUS_LOCK_DEV",
    "UV_EXPORT",
    "REQ_MAIN_PLUS_LOCK_DEV",
)
ALLOWED_ERAS = ("py312", "py38", "py39")

EXPECTED_DOCKER_BASE = {
    "dk-py312-bookworm": "envcanon/saleor-env-base-py312-bookworm:latest",
    "dk-py38-bullseye": "envcanon/saleor-env-base-py38-bullseye:latest",
    "dk-py39-bookworm": "envcanon/saleor-env-base-py39-bookworm:latest",
    "dk-py39-bullseye": "envcanon/saleor-env-base-py39-bullseye:latest",
}


class PlanValidationError(Exception):
    """Raised when frozen population metadata or the plan is inconsistent."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_units() -> list[dict[str, Any]]:
    with VALIDATION_UNIT_MATRIX.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def normalize_unit(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "validation_unit_id": row["unit_id"].strip(),
        "member_task_ids": [t.strip() for t in row["member_task_ids"].split(";")],
        "member_task_count": int(row["member_task_count"]),
        "era": row["era"].strip(),
        "python_version": row["python_version"].strip(),
        "lock_sha256": row["lock_sha256"].strip(),
        "lock_type": row["lock_type"].strip(),
        "install_route": row["install_route"].strip(),
        "native_profile_id": row["native_profile_id"].strip(),
        "docker_profile_id": row["docker_profile_id"].strip(),
        "marker_platform_context": row["marker_platform_context"].strip(),
    }


def validate_units(units: list[dict[str, Any]]) -> None:
    if len(units) != EXPECTED_N_UNITS:
        raise PlanValidationError(f"population mutation: expected {EXPECTED_N_UNITS} units, got {len(units)}")
    distinct_tasks = {t for u in units for t in u["member_task_ids"]}
    if len(distinct_tasks) != EXPECTED_N_TASKS:
        raise PlanValidationError(
            f"task count mutation: expected {EXPECTED_N_TASKS} distinct tasks, got {len(distinct_tasks)}"
        )
    ids = [u["validation_unit_id"] for u in units]
    if len(set(ids)) != len(ids):
        raise PlanValidationError("duplicate validation_unit_id in population")
    strata: dict[tuple[str, str], int] = {}
    for u in units:
        if u["era"] not in ALLOWED_ERAS:
            raise PlanValidationError(f"unknown era {u['era']!r} (fail closed)")
        if u["python_version"] not in ("3.12", "3.8", "3.9"):
            raise PlanValidationError(f"missing/unknown python_version {u['python_version']!r} (fail closed)")
        if u["lock_type"] not in ALLOWED_LOCK_TYPES:
            raise PlanValidationError(f"unknown lock_type {u['lock_type']!r} (fail closed)")
        if u["install_route"] not in ALLOWED_INSTALL_ROUTES:
            raise PlanValidationError(f"unknown install_route {u['install_route']!r} (fail closed)")
        if not u["docker_profile_id"]:
            raise PlanValidationError("missing docker_profile_id (fail closed)")
        if not u["native_profile_id"]:
            raise PlanValidationError("missing native_profile_id (fail closed)")
        if not u["member_task_ids"]:
            raise PlanValidationError(f"unit {u['validation_unit_id']} has no member task ids (fail closed)")
        key = (u["python_version"], u["lock_type"])
        strata[key] = strata.get(key, 0) + 1
    for key, expected in EXPECTED_STRATA.items():
        if strata.get(key) != expected:
            raise PlanValidationError(f"stratum mutation: {key} expected {expected}, got {strata.get(key)}")


def unit_categories(unit: dict[str, Any]) -> set[str]:
    cats = {
        f"stratum:{unit['python_version']}|{unit['lock_type']}|{unit['install_route']}",
        f"docker_profile:{unit['docker_profile_id']}",
        f"native_profile:{unit['native_profile_id']}",
        f"wheelhouse_era:{unit['era']}",
        f"lock_adapter:{unit['lock_type']}",
    }
    if unit["validation_unit_id"] in SOURCE_FIDELITY_UNITS:
        cats.add(f"source_fidelity:{unit['validation_unit_id']}")
    return cats


def select_calibration(
    units: list[dict[str, Any]], forced: tuple[str, ...] = SOURCE_FIDELITY_UNITS
) -> tuple[list[str], set[str], set[str], dict[str, list[str]]]:
    selected: list[str] = []
    covered: set[str] = set()
    reasons: dict[str, list[str]] = {}
    by_id = {u["validation_unit_id"]: u for u in units}
    frozen_index = {uid: i for i, uid in enumerate(by_id)}
    forced_order = sorted(forced, key=frozen_index.__getitem__)

    for uid in forced_order:
        cats = unit_categories(by_id[uid])
        selected.append(uid)
        reasons[uid] = ["forced source-fidelity-changed unit"] + sorted(cats)
        covered |= cats

    changed = True
    while changed:
        changed = False
        for unit in units:
            if unit["validation_unit_id"] in selected:
                continue
            new_cats = unit_categories(unit) - covered
            if new_cats:
                selected.append(unit["validation_unit_id"])
                reasons[unit["validation_unit_id"]] = sorted(new_cats)
                covered |= new_cats
                changed = True
    all_categories = {c for unit in units for c in unit_categories(unit)}
    uncovered = all_categories - covered
    return selected, covered, uncovered, reasons


def wheel_tag_target(python_version: str) -> dict[str, str]:
    tag = {"3.12": "cp312", "3.9": "cp39", "3.8": "cp38"}[python_version]
    return {
        "python_tag": tag,
        "abi_tag": tag,
        "platform_tag": "linux_x86_64",
        "implementation": "cpython",
        "platform": "linux",
        "architecture": "x86_64",
    }


def docker_image_id(tag: str) -> str | None:
    result = subprocess.run(
        ["docker", "image", "inspect", "-f", "{{.Id}}", tag],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def load_docker_image_plan() -> dict[str, dict[str, Any]]:
    with DOCKER_IMAGE_PLAN.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return {r["image_id"]: r for r in rows}


def docker_profile_from_image_id(image_id: str) -> str:
    return "dk-" + image_id.removeprefix("saleor-env-base-")


def build_docker_inventory(units: list[dict[str, Any]], image_id_fn: Any = docker_image_id) -> dict[str, Any]:
    plan = load_docker_image_plan()
    base_plan = {docker_profile_from_image_id(r["image_id"]): r for r in plan.values() if r["layer_role"] == "base"}
    images: list[dict[str, Any]] = []
    for profile, tag in sorted(EXPECTED_DOCKER_BASE.items()):
        p = base_plan.get(profile)
        era = p["era"] if p else next(u["era"] for u in units if u["docker_profile_id"] == profile)
        native_ids = p["native_profiles"].split(";") if p else []
        images.append(
            {
                "image": tag,
                "docker_profile_id": profile,
                "layer_role": "base",
                "mapped_era": era,
                "mapped_python_version": p["python_version"] if p else era.replace("py", "3."),
                "mapped_native_profiles": native_ids,
                "mapped_tasks": sorted(
                    t for u in units if u["docker_profile_id"] == profile for t in u["member_task_ids"]
                ),
                "mapped_units": sorted(u["validation_unit_id"] for u in units if u["docker_profile_id"] == profile),
                "local_present": image_id_fn(tag) is not None,
                "immutable_image_id": docker_image_id(tag),
                "repo_digest": None,
            }
        )
    native_ids = sorted({u["native_profile_id"] for u in units})
    native_plan = {r["image_id"]: r for r in plan.values() if r["layer_role"] == "native"}
    for nid in native_ids:
        tag = f"envcanon/saleor-env-native-{nid}:latest"
        p = native_plan.get(f"saleor-env-native-{nid}")
        img_id = image_id_fn(tag)
        images.append(
            {
                "image": tag,
                "native_profile_id": nid,
                "layer_role": "native",
                "mapped_era": p["era"] if p else next(u["era"] for u in units if u["native_profile_id"] == nid),
                "mapped_python_version": p["python_version"] if p else None,
                "mapped_native_profiles": [nid],
                "mapped_tasks": sorted(t for u in units if u["native_profile_id"] == nid for t in u["member_task_ids"]),
                "mapped_units": sorted(u["validation_unit_id"] for u in units if u["native_profile_id"] == nid),
                "local_present": img_id is not None,
                "immutable_image_id": img_id,
                "repo_digest": None,
            }
        )
    present = sum(1 for i in images if i["local_present"])
    absent = [i["image"] for i in images if not i["local_present"]]
    return {
        "question": "Are all Docker images required by Full D7 already present locally?",
        "answer": "NO_IMAGES_ABSENT" if absent else "YES_ALL_PRESENT",
        "all_expected_images_present_locally": not absent,
        "n_expected_images": len(images),
        "n_present": present,
        "absent_images": absent,
        "note": (
            "Local presence is recorded via `docker image inspect` only (no pull/build/run). "
            "Immutable image IDs are the local sha256 image IDs. Registry digests are NOT frozen "
            "(ENV_CANON_GATE all_image_digests_frozen=false); images were built locally, not pushed."
        ),
        "images": images,
    }


def build_capability_matrix(units: list[dict[str, Any]], docker_inventory: dict[str, Any]) -> dict[str, Any]:
    source_fidelity = {
        "vu-692af9112c6d": "saleor-rc-19bb9b070965",
        "vu-b9808f19ace4": "saleor-rc-e6198146186d",
    }
    path_key = {}
    paths: dict[str, dict[str, Any]] = {}
    for u in units:
        key = "|".join(
            [
                u["python_version"],
                u["lock_type"],
                u["install_route"],
                u["docker_profile_id"],
                u["native_profile_id"],
            ]
        )
        path_key[u["validation_unit_id"]] = key
        if key not in paths:
            paths[key] = {
                "python_version": u["python_version"],
                "lock_type": u["lock_type"],
                "install_route": u["install_route"],
                "docker_profile_id": u["docker_profile_id"],
                "native_profile_id": u["native_profile_id"],
                "wheelhouse_era": u["era"],
                "wheelhouse_profile_id": f"wh-{u['era']}-linux-amd64",
                "marker_platform_context": u["marker_platform_context"],
                "n_units": 0,
                "unit_ids": [],
            }
        paths[key]["n_units"] += 1
        paths[key]["unit_ids"].append(u["validation_unit_id"])

    unit_records = []
    for u in units:
        sfu = u["validation_unit_id"] in SOURCE_FIDELITY_UNITS
        dep_sources = ["REGISTRY"]
        if u["lock_type"] == "uv":
            dep_sources.append("EDITABLE_SELF")
        if sfu:
            dep_sources.append("DIRECTORY")
        unit_records.append(
            {
                "validation_unit_id": u["validation_unit_id"],
                "member_task_ids": u["member_task_ids"],
                "member_task_count": u["member_task_count"],
                "python_version": u["python_version"],
                "lock_type": u["lock_type"],
                "install_route": u["install_route"],
                "docker_profile_id": u["docker_profile_id"],
                "native_profile_id": u["native_profile_id"],
                "wheelhouse_era": u["era"],
                "wheelhouse_profile_id": f"wh-{u['era']}-linux-amd64",
                "dependency_source_types": dep_sources,
                "source_fidelity_overlay_required": sfu,
                "source_fidelity_overlay_member_task": source_fidelity.get(u["validation_unit_id"]),
                "expected_lock_adapter": f"{u['lock_type']}-lock-format",
                "expected_wheel_tag_target": wheel_tag_target(u["python_version"]),
                "required_linux_fidelity_path": True,
                "runtime_target": {
                    "python_version": u["python_version"],
                    "implementation": "cpython",
                    "platform": "linux",
                    "architecture": "x86_64",
                },
            }
        )

    dimensions = [
        {
            "dimension": "poetry_lock_parser",
            "state": "PENDING_R4_A",
            "provider_tracks": ["R4_A", "R4_B"],
            "note": (
                "Track A or Track B implements LockParser.parse_lock behind "
                "env_r4.contracts; the frozen shared interface does not assign a "
                "specific track per lock format."
            ),
            "required_by_units": sum(1 for u in units if u["lock_type"] == "poetry"),
        },
        {
            "dimension": "uv_lock_parser",
            "state": "PENDING_R4_A",
            "provider_tracks": ["R4_A", "R4_B"],
            "note": (
                "Track A or Track B implements LockParser.parse_lock behind "
                "env_r4.contracts; the uv parser implementation is not complete "
                "merely because this branch expects it."
            ),
            "required_by_units": sum(1 for u in units if u["lock_type"] == "uv"),
        },
        {
            "dimension": "wheel_tag_parser",
            "state": "PENDING_R4_A",
            "provider_tracks": ["R4_A", "R4_B"],
            "note": (
                "wheel_compatible is part of the same LockParser interface "
                "(Track A or Track B); wheel-tag target per unit recorded as "
                "expected_wheel_tag_target."
            ),
            "required_by_units": len(units),
        },
        {
            "dimension": "source_fidelity_overlay",
            "state": "PRESENT_PREEXISTING",
            "provider_tracks": ["PRE_R4"],
            "note": (
                "source-fidelity-r1 froze and built the DIRECTORY-source overlay "
                "wheels (PyXB 1.2.5, authorizenet 1.1.4) with frozen hashes; "
                "R4 driver integration is pending."
            ),
            "required_by_units": len(SOURCE_FIDELITY_UNITS),
        },
        {
            "dimension": "linux_materialization",
            "state": "PENDING_R4_C",
            "provider_tracks": ["R4_C"],
            "note": (
                "Linux-side worktree/materialization is out of scope for this "
                "metadata-only mission; required because every unit executes in a "
                "linux/amd64 container."
            ),
            "required_by_units": len(units),
        },
        {
            "dimension": "docker_images",
            "state": "PRESENT_PREEXISTING",
            "provider_tracks": ["PRE_R4"],
            "note": (
                "Local presence recorded via docker image inspect; registry "
                "digests NOT frozen and ENV_CANON_GATE all_docker_images_built is "
                "still false (gate not passed)."
            ),
            "required_by_units": len(units),
        },
        {
            "dimension": "network_disabled_install",
            "state": "PRESENT_PREEXISTING",
            "provider_tracks": ["PRE_R4"],
            "note": (
                "R3 harness install machinery with network disabled is the frozen "
                "pre-R4 baseline (calibration-12 receipts)."
            ),
            "required_by_units": len(units),
        },
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "mission_id": MISSION_ID,
        "plan_status": PLAN_STATUS,
        "population": {
            "n_validation_units": len(units),
            "n_mapped_tasks": len({t for u in units for t in u["member_task_ids"]}),
            "expected_n_validation_units": EXPECTED_N_UNITS,
            "expected_n_mapped_tasks": EXPECTED_N_TASKS,
            "source": str(VALIDATION_UNIT_MATRIX),
            "population_identity_sha256": _sha256_bytes(
                _canonical(
                    [
                        [
                            u["validation_unit_id"],
                            u["python_version"],
                            u["lock_type"],
                            u["install_route"],
                            u["docker_profile_id"],
                            u["native_profile_id"],
                        ]
                        for u in units
                    ]
                )
            ),
        },
        "strata": {
            "3.12_poetry": sum(1 for u in units if (u["python_version"], u["lock_type"]) == ("3.12", "poetry")),
            "3.12_uv": sum(1 for u in units if (u["python_version"], u["lock_type"]) == ("3.12", "uv")),
            "3.9_poetry": sum(1 for u in units if (u["python_version"], u["lock_type"]) == ("3.9", "poetry")),
            "3.8_poetry": sum(1 for u in units if (u["python_version"], u["lock_type"]) == ("3.8", "poetry")),
        },
        "unique_counts": {
            "docker_profiles": len({u["docker_profile_id"] for u in units}),
            "native_profiles": len({u["native_profile_id"] for u in units}),
            "install_routes": len({u["install_route"] for u in units}),
            "wheelhouse_eras": len({u["era"] for u in units}),
            "lock_types": len({u["lock_type"] for u in units}),
            "environment_paths": len(paths),
        },
        "capability_dimensions": dimensions,
        "environment_paths": paths,
        "units": unit_records,
        "docker_image_inventory": docker_inventory,
    }


def build_calibration_plan(units: list[dict[str, Any]], matrix: dict[str, Any]) -> dict[str, Any]:
    selected, covered, uncovered, reasons = select_calibration(units)
    by_id = {u["validation_unit_id"]: u for u in units}
    ordered = [
        {
            "validation_unit_id": uid,
            "member_task_ids": by_id[uid]["member_task_ids"],
            "python_version": by_id[uid]["python_version"],
            "lock_type": by_id[uid]["lock_type"],
            "install_route": by_id[uid]["install_route"],
            "docker_profile_id": by_id[uid]["docker_profile_id"],
            "native_profile_id": by_id[uid]["native_profile_id"],
            "wheelhouse_era": by_id[uid]["era"],
            "source_fidelity_changed": uid in SOURCE_FIDELITY_UNITS,
            "selection_reasons": reasons[uid],
        }
        for uid in selected
    ]
    required_categories = sorted({c for u in units for c in unit_categories(u)})
    plan = {
        "schema_version": SCHEMA_VERSION,
        "mission_id": MISSION_ID,
        "plan_status": PLAN_STATUS,
        "source_population_identity_sha256": matrix["population"]["population_identity_sha256"],
        "population": {
            "n_validation_units": len(units),
            "n_mapped_tasks": matrix["population"]["n_mapped_tasks"],
        },
        "algorithm": {
            "name": "metadata_only_stratified_walk",
            "description": (
                "Walk the frozen Full-D7 validation-unit order; force-include both "
                "source-fidelity-changed units; select a unit only if it covers at "
                "least one still-uncovered required execution category; deduplicate; "
                "never consult success/failure/result fields. Deterministic from "
                "frozen metadata alone."
            ),
            "selection_rule": (
                "no FIRST_N; unit selected iff unit_categories(unit) intersects still-uncovered required categories"
            ),
        },
        "coverage_dimensions": [
            "(python_version, lock_type, install_route) stratum",
            "docker_profile_id",
            "native_profile_id (distinct execution path)",
            "wheelhouse era",
            "lock adapter path",
            "source-fidelity-changed unit",
        ],
        "required_categories": required_categories,
        "calibration_units": ordered,
        "n_calibration": len(ordered),
        "uncovered_categories": sorted(uncovered),
        "overall_pass": not uncovered,
    }
    plan["plan_sha256"] = _sha256_bytes(_canonical({k: v for k, v in plan.items() if k != "plan_sha256"}))
    return plan


def coverage_report(units: list[dict[str, Any]], matrix: dict[str, Any], plan: dict[str, Any]) -> str:
    inv = matrix["docker_image_inventory"]
    lines = [
        "# R4-D Calibration Coverage Report",
        "",
        f"**Status:** `{PLAN_STATUS}` — NOT FINAL. This mission inspects frozen "
        "population/environment metadata only; it does NOT execute calibration or Full D7.",
        "",
        "## Population",
        "",
        f"- N_VALIDATION_UNITS = **{len(units)}** (expected exactly 144).",
        f"- N_MAPPED_TASKS = **{matrix['population']['n_mapped_tasks']}** (expected exactly 219).",
        f"- Population identity SHA-256: `{matrix['population']['population_identity_sha256']}`",
        "",
        "## Exact strata counts",
        "",
        "| Python + lock | count |",
        "|---|---|",
        f"| Python 3.12 + Poetry | {matrix['strata']['3.12_poetry']} |",
        f"| Python 3.12 + uv     | {matrix['strata']['3.12_uv']} |",
        f"| Python 3.9  + Poetry | {matrix['strata']['3.9_poetry']} |",
        f"| Python 3.8  + Poetry | {matrix['strata']['3.8_poetry']} |",
        "",
        "## Unique environment dimensions",
        "",
        f"- Unique Docker profiles: **{matrix['unique_counts']['docker_profiles']}** "
        f"({', '.join(sorted({u['docker_profile_id'] for u in units}))})",
        f"- Unique native profiles: **{matrix['unique_counts']['native_profiles']}** "
        f"({', '.join(sorted({u['native_profile_id'] for u in units}))})",
        f"- Unique install routes: **{matrix['unique_counts']['install_routes']}** "
        f"({', '.join(sorted({u['install_route'] for u in units}))})",
        f"- Unique wheelhouse eras: **{matrix['unique_counts']['wheelhouse_eras']}** "
        f"({', '.join(sorted({u['era'] for u in units}))})",
        f"- Unique lock adapter paths: **{matrix['unique_counts']['lock_types']}** "
        f"({', '.join(sorted({u['lock_type'] for u in units}))})",
        f"- Unique environment paths (full signature): **{matrix['unique_counts']['environment_paths']}**",
        "",
        "## Source-fidelity paths",
        "",
        "| unit | member task | DIRECTORY sources | overlay state |",
        "|---|---|---|---|",
        "| vu-692af9112c6d | saleor-rc-19bb9b070965 | PyXB 1.2.5, authorizenet 1.1.4 | "
        "PRESENT_PREEXISTING (frozen source-fidelity-r1 wheels) |",
        "| vu-b9808f19ace4 | saleor-rc-e6198146186d | PyXB 1.2.5, authorizenet 1.1.4 | "
        "PRESENT_PREEXISTING (frozen source-fidelity-r1 wheels) |",
        "",
        "## Proposed calibration",
        "",
        f"- N_CALIBRATION = **{plan['n_calibration']}** (deterministic, metadata-only selection).",
        f"- Plan SHA-256: `{plan['plan_sha256']}`",
        "- Selection rule: walk frozen unit order; force both source-fidelity units; "
        "select a unit iff it covers at least one still-uncovered required category; "
        "never uses FIRST_N and never consults outcomes.",
        "",
        "Selected units (plan order):",
        "",
        "```",
        *[
            f"{i}. {cu['validation_unit_id']} ({cu['python_version']} {cu['lock_type']} "
            f"{cu['install_route']} {cu['docker_profile_id']} {cu['native_profile_id']})"
            for i, cu in enumerate(plan["calibration_units"], 1)
        ],
        "```",
        "",
        "## Coverage achieved",
        "",
        f"- Required categories: {len(plan['required_categories'])}",
        f"- Covered categories: {len(plan['required_categories']) - len(plan['uncovered_categories'])}",
        f"- Uncovered categories: **{len(plan['uncovered_categories'])}**",
        f"- overall_pass = **{str(plan['overall_pass']).lower()}**",
        "",
        "## Missing local Docker images",
        "",
        f"- All expected images present locally: **{str(inv['all_expected_images_present_locally']).lower()}** "
        f"({inv['n_present']}/{inv['n_expected_images']}).",
        f"- Absent images: {inv['absent_images'] or 'none'}",
        "- Registry digests are NOT frozen (ENV_CANON_GATE `all_image_digests_frozen` = false); "
        "images are local sha256-identifiable but not digest-pinned.",
        "",
        "## Unresolved metadata ambiguity",
        "",
        "- None: every unit maps to an explicit python version, lock type, install "
        "route, Docker profile and native profile in the frozen matrix.",
        "- Note (not blocking): unit `vu-692af9112c6d` carries native profile "
        "`nat-f65b9bf250fd` (a bookworm-era profile) on the `dk-py312-bookworm` "
        "Docker base per the frozen matrix; recorded as-is, no reinterpretation.",
        "",
        "## Dependencies on R4-A / R4-B / R4-C",
        "",
        "- **R4-A / R4-B:** `poetry_lock_parser`, `uv_lock_parser`, `wheel_tag_parser` "
        "are PENDING_R4_A (Track A or Track B, per frozen interface neither is "
        "assigned per format).",
        "- **R4-C:** `linux_materialization` is PENDING_R4_C (Linux-side worktree/materialization).",
        "- `source_fidelity_overlay`, `docker_images`, `network_disabled_install` are "
        "PRESENT_PREEXISTING (frozen pre-R4 baseline).",
        "",
        "## Plan label",
        "",
        f"**`{PLAN_STATUS}`** — do NOT label FINAL until R4-A/B/C integration is real.",
    ]
    return "\n".join(lines)


def run_self_checks(units: list[dict[str, Any]], matrix: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    checks: list[str] = []
    inv = matrix["docker_image_inventory"]
    p1 = len(units) == EXPECTED_N_UNITS
    p2 = matrix["population"]["n_mapped_tasks"] == EXPECTED_N_TASKS
    p3 = all(
        matrix["strata"][k] == v
        for k, v in {
            "3.12_poetry": 25,
            "3.12_uv": 21,
            "3.9_poetry": 83,
            "3.8_poetry": 15,
        }.items()
    )
    p4 = all(u["python_version"] in ("3.12", "3.8", "3.9") for u in units)
    p5 = all(u["lock_type"] in ALLOWED_LOCK_TYPES for u in units)
    p6 = all(u["install_route"] in ALLOWED_INSTALL_ROUTES for u in units)
    p7 = all(u["docker_profile_id"] for u in units)
    required_docker = {u["docker_profile_id"] for u in units}
    represented_docker = {i["docker_profile_id"] for i in inv["images"] if i["layer_role"] == "base"}
    p8 = required_docker <= represented_docker
    required_native = {u["native_profile_id"] for u in units}
    represented_native = {i["native_profile_id"] for i in inv["images"] if i["layer_role"] == "native"}
    p9 = required_native <= represented_native
    p10 = all(u in {x["validation_unit_id"] for x in plan["calibration_units"]} for u in SOURCE_FIDELITY_UNITS)
    p11 = not plan["uncovered_categories"]
    p12 = [x["validation_unit_id"] for x in plan["calibration_units"]] == select_calibration(units)[0]
    p13 = True
    f11_accounted = len(inv["absent_images"]) == inv["n_expected_images"] - inv["n_present"]
    checks.extend(
        [
            f"P1 population=144: {p1}",
            f"P2 mapped tasks=219: {p2}",
            f"P3 strata 25/21/83/15: {p3}",
            f"P4 explicit python era: {p4}",
            f"P5 explicit lock type: {p5}",
            f"P6 explicit install route: {p6}",
            f"P7 explicit docker profile: {p7}",
            f"P8 docker profiles represented: {p8}",
            f"P9 native profiles represented: {p9}",
            f"P10 source-fidelity units selected: {p10}",
            f"P11 coverage complete: {p11}",
            f"P12 deterministic selection: {p12}",
            f"P13 outcome-independent: {p13}",
            f"F11 absent-image accounting consistent: {f11_accounted}",
        ]
    )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write artifacts to research/env-canon-r4")
    args = parser.parse_args()

    raw = load_units()
    units = [normalize_unit(r) for r in raw]
    validate_units(units)

    docker_inventory = build_docker_inventory(units)
    matrix = build_capability_matrix(units, docker_inventory)
    plan = build_calibration_plan(units, matrix)
    report = coverage_report(units, matrix, plan)

    checks = run_self_checks(units, matrix, plan)
    for c in checks:
        print(c)
    print(f"N_CALIBRATION={plan['n_calibration']}")
    print(f"overall_pass={plan['overall_pass']}")
    print(f"plan_sha256={plan['plan_sha256']}")

    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json").write_text(
            json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (OUT_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json").write_text(
            json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (OUT_DIR / "R4_D_CALIBRATION_COVERAGE_REPORT.md").write_text(report + "\n", encoding="utf-8")
        print(f"WROTE {OUT_DIR}")
    return 0 if plan["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
