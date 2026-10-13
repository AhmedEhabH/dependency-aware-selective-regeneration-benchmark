#!/usr/bin/env python3
"""M17_D7_R4_BEHAVIORAL_CALIBRATION_N12_R2 — real N12 behavioral calibration driver.

Mission: M17_D7_R4_BEHAVIORAL_CALIBRATION_N12_R2 (T3, real behavioral
environment calibration after qualified native-image composition repair).

This driver is SMALLEST ADDITIVE mission-local orchestration on top of frozen
authority.  It does NOT modify any frozen file and does NOT invent scientific
semantics:

* N12 membership/order/coverage are read from the frozen R4-D plan.
* Execution images resolve ONLY through the qualified
  ``R4_EXECUTION_IMAGE_COMPOSITE_BINDING.json`` (general
  ``(docker_profile_id, native_profile_id)`` key; no unit/task special casing).
* Lock closures are derived with the qualified R4-B integrated parser
  (``env_r4.contracts.parse_lock``) and install pins retain the frozen R3
  platform/exclusion semantics (marker audit + pyproject ``platform=win32``).
* Wheel compatibility uses qualified R4-A semantics; Linux-faithful
  materialization uses the qualified R4-C materializer.
* The frozen D7/R3 behavioral container semantics are reused verbatim
  (``--network=none``, netprobe, wheel-only offline install, toolhouse audit,
  pip check, native probes, import/manage/pytest smoke).
* Source-fidelity (units 1,2) and R4-E recovery overlay (unit 10) inputs are
  the exact qualified frozen artifacts.

Execution rules: exactly one unit at a time, deterministic frozen order,
checkpoint after each unit, fail closed on the first mandatory gate failure,
no semantic retries, no adaptive decisions, no Docker pull/build.

Usage:
  python scripts/r4_behavioral_calibration_n12_r2.py --preflight
  python scripts/r4_behavioral_calibration_n12_r2.py --unit N
  python scripts/r4_behavioral_calibration_n12_r2.py --aggregate
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from benchmark.wp2.env_r4.contracts import (  # noqa: E402
    LockClosure,
    RuntimeTarget,
    normalize_name,
    parse_lock,
    unbind_lock_parser,
    wheel_compatible,
)
from benchmark.wp2.env_r4.integrated_parser import bind_integrated_parser  # noqa: E402
from benchmark.wp2.env_r4.linux_tree_materialize import (  # noqa: E402
    MaterializeError,
    ensure_empty_volume,
    remove_volume,
)
from benchmark.wp2.env_r4.linux_tree_wiring import (  # noqa: E402
    LinuxTreeWiring,
    R4MaterializationSource,
)
from benchmark.wp2.linux_adapter import WslDockerBackend  # noqa: E402

R4_DIR = PROJECT / "research" / "env-canon-r4"
SF_R1_DIR = PROJECT / "research" / "source-fidelity-r1"

PLAN_PATH = R4_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json"
MATRIX_PATH = R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json"
BINDING_PATH = R4_DIR / "R4_EXECUTION_IMAGE_COMPOSITE_BINDING.json"
REPAIR_RECEIPT_PATH = R4_DIR / "R4_NATIVE_IMAGE_COMPOSITION_REPAIR_RECEIPT.json"
POST_REPAIR_CENSUS_PATH = R4_DIR / "R4_POST_REPAIR_COMPOSITION_CENSUS.json"
E3_RECEIPT_PATH = R4_DIR / "R4_E3_AFFECTED_REVALIDATION_RECEIPT.json"
E1_PLAN_PATH = R4_DIR / "R4_E1_PYLINT_RECOVERY_PLAN.json"
E2_RECEIPT_PATH = R4_DIR / "R4_E2_PYLINT_ACQUISITION_RECEIPT.json"

BINDING_OUT = R4_DIR / "R4_BEHAVIORAL_CALIBRATION_N12_R2_BINDING.json"

EXPECTED_PLAN_SHA = "8ec20f360f62c7f4d072ad03bb5fe042c85fa98bad64757715227b5c88de687d"
EXPECTED_BINDING_HASH = "3878e75a7f5f4b676af3633cad5cd64eeab05d4b9155ef9b61b2b8c1dd9607b3"
EXPECTED_POPULATION_IDENTITY = "ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac"
REPAIRED_IMAGE_REF = "envcanon/saleor-env-native-nat-f65b9bf250fd-py312-bookworm:r4-composite-20261013"
REPAIRED_IMAGE_ID = "sha256:1be41dd22a934cc56ed10fa1046234a450f6d2946f8099d7bcb501f696f1d759"
OLD_PY39_REF = "envcanon/saleor-env-native-nat-f65b9bf250fd:latest"
OLD_PY39_ID = "sha256:baea6c4b01e1b5bfb40b5910074c4b145c91c2c1d19b815889df4f1d76d86f24"

SOURCE_FIDELITY_UNITS = ("vu-b9808f19ace4", "vu-692af9112c6d")
RECOVERY_UNIT = "vu-457f26c93ff1"
REPAIRED_UNIT = "vu-692af9112c6d"

FROZEN_UNIT_ORDER = (
    "vu-b9808f19ace4",
    "vu-692af9112c6d",
    "vu-e4998719ee01",
    "vu-db74b3640c98",
    "vu-422bca69f329",
    "vu-13c1de1de71e",
    "vu-b78ebcf3e530",
    "vu-bfe987de6e53",
    "vu-eda4e9f82401",
    "vu-457f26c93ff1",
    "vu-ffe68ddec229",
    "vu-0e0ef31c7634",
)

# Frozen R3 closure exclusions (exactly two, from MARKER_FILTER_AUDIT and the
# frozen pyproject platform=win32 declarations).  Re-derived from frozen
# authority in verify_unit (never hard-added per unit ID).
STORE = Path(r"D:\wp2_env_store")
MARKER_AUDIT = STORE / "manifests" / "MARKER_FILTER_AUDIT.json"
D4_CODECOV_EXCLUSION = STORE / "manifests" / "D4_CODECOV_NONRUNTIME_EXCLUSION_AMENDMENT_R5.json"
DOCKER_PROFILES = STORE / "manifests" / "DOCKER_PROFILE_MANIFEST.json"
TASK_ENV_CSV = STORE / "manifests" / "TASK_ENV_MATRIX.csv"
LOCK_DIR = STORE / "artifacts" / "locks"
WHEELHOUSE_DIR = STORE / "wheelhouse"
CANON_DIR = STORE / "built_wheelhouse" / "canon_r4b"
RECOVERY_WHEELS = STORE / "recovery" / "r4e_pylint_py39" / "wheels"
RECOVERY_MANIFEST = (
    STORE / "recovery" / "r4e_pylint_py39" / "manifests" / "R4_E2_PYLINT_ACQUISITION_MANIFEST.json"
)
HARNESS_DIR = STORE / "harness" / "d7_r3"
SF_MANIFEST = SF_R1_DIR / "SOURCE_FIDELITY_PROVENANCE_MANIFEST.json"
SF_WHEELS = SF_R1_DIR / "artifacts" / "wheels"

RUN_ROOT = Path(r"D:\WP2\runs\r4-behavioral-calibration-n12-r2-2026-10-13")
FREEZE_DIR = RUN_ROOT / "freeze"
UNITS_DIR = RUN_ROOT / "units"
LOGS_DIR = RUN_ROOT / "logs"
PROGRESS_DIR = RUN_ROOT / "progress"
MATERIALIZED_DIR = RUN_ROOT / "materialized"
RECEIPTS_DIR = RUN_ROOT / "receipts"
PROGRESS_JSON = PROGRESS_DIR / "progress.json"

# WSL-local Docker engine parameters (qualified R4-C substrate).
WSL_DISTRO = "Ubuntu-24.04"
WSL_REPO = "/opt/wp2_v2/saleor-cache"
MATERIALIZE_IMAGE = "envcanon/saleor-env-base-py312-bookworm:latest"

INSTALL_TIMEOUT_S = 5400  # 90 minutes, mirrors the frozen R3 per-container timeout.

# Failure taxonomy (frozen)
F_ENV_ARTIFACT_RESOLUTION = "ENV_ARTIFACT_RESOLUTION_FAILURE"
F_ENV_DOCKER_IMAGE = "ENV_DOCKER_IMAGE_FAILURE"
F_ENV_LINUX_MATERIALIZATION = "ENV_LINUX_MATERIALIZATION_FAILURE"
F_ENV_OFFLINE_INSTALL = "ENV_OFFLINE_INSTALL_FAILURE"
F_ENV_DEPENDENCY_CONSISTENCY = "ENV_DEPENDENCY_CONSISTENCY_FAILURE"
F_ENV_NATIVE_PROBE = "ENV_NATIVE_PROBE_FAILURE"
F_ENV_IMPORT_SMOKE = "ENV_IMPORT_SMOKE_FAILURE"
F_ENV_FRAMEWORK_GATE = "ENV_FRAMEWORK_GATE_FAILURE"
F_ENV_PYTEST_COLLECTION = "ENV_PYTEST_COLLECTION_FAILURE"
F_ENV_TIMEOUT = "ENV_TIMEOUT"
F_TOOLING_OR_INSTRUMENTATION = "TOOLING_OR_INSTRUMENTATION_FAILURE"
F_SCIENTIFIC_AUTHORITY_AMBIGUITY = "SCIENTIFIC_AUTHORITY_AMBIGUITY"
F_UNCLASSIFIED = "UNCLASSIFIED_STOP"

ALLOWED_INSTALL_ROUTES = (
    "LOCK_FRAGMENT_MAIN_PLUS_DEV",
    "REQ_MAIN_PLUS_LOCK_DEV",
    "UV_EXPORT",
    "V2_EDITABLE_PLUS_LOCK_DEV",
)


class CalibrationFailClosedError(Exception):
    """Raised on any mandatory fail-closed gate."""


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CalibrationFailClosedError(f"missing artifact: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CalibrationFailClosedError(f"artifact {path} is not a JSON object")
    return data


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise CalibrationFailClosedError(f"missing manifest {path}")
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def verify_import_provenance() -> dict[str, str]:
    import benchmark

    resolved = Path(benchmark.__file__).resolve()
    src_resolved = SRC.resolve()
    if not resolved.is_relative_to(src_resolved):
        raise CalibrationFailClosedError(
            f"import provenance wrong: benchmark = {resolved}, expected under {src_resolved}"
        )
    return {"benchmark_module": str(resolved), "resolves_to_expected_src": "true"}


def load_plan() -> dict[str, Any]:
    plan = _read_json(PLAN_PATH)
    if plan.get("schema_version") != "env-canon-r4-d/1.0":
        raise CalibrationFailClosedError("plan schema_version mismatch")
    if plan.get("n_calibration") != 12:
        raise CalibrationFailClosedError("plan N != 12")
    recomputed = _canonical({k: v for k, v in plan.items() if k != "plan_sha256"})
    if plan.get("plan_sha256") != _sha256_bytes(recomputed):
        raise CalibrationFailClosedError("plan SHA not self-consistent")
    if plan.get("plan_sha256") != EXPECTED_PLAN_SHA:
        raise CalibrationFailClosedError("plan SHA != frozen mission value")
    units = [c["validation_unit_id"] for c in plan.get("calibration_units", [])]
    if units != list(FROZEN_UNIT_ORDER):
        raise CalibrationFailClosedError("N12 membership/order mutated")
    pop = plan.get("population", {})
    if (pop.get("n_validation_units"), pop.get("n_mapped_tasks")) != (144, 219):
        raise CalibrationFailClosedError("plan population counts mutated")
    if plan.get("source_population_identity_sha256") != EXPECTED_POPULATION_IDENTITY:
        raise CalibrationFailClosedError("plan population identity mutated")
    if len(plan.get("required_categories", [])) != 27:
        raise CalibrationFailClosedError("required categories != 27")
    if plan.get("uncovered_categories") != []:
        raise CalibrationFailClosedError("plan uncovered categories not empty")
    return plan


def load_binding() -> dict[str, Any]:
    binding = _read_json(BINDING_PATH)
    recomputed = _canonical({k: v for k, v in binding.items() if k != "deterministic_binding_hash"})
    if binding.get("deterministic_binding_hash") != _sha256_bytes(recomputed):
        raise CalibrationFailClosedError("binding hash not self-consistent")
    if binding.get("deterministic_binding_hash") != EXPECTED_BINDING_HASH:
        raise CalibrationFailClosedError("binding hash != frozen mission value")
    if binding.get("unique_pair_count") != 11:
        raise CalibrationFailClosedError("unique_pair_count != 11")
    pairs = [(r["docker_profile_id"], r["native_profile_id"]) for r in binding.get("pairs", [])]
    if len(pairs) != len(set(pairs)):
        raise CalibrationFailClosedError("binding duplicate pair")
    return binding


def load_matrix() -> dict[str, Any]:
    matrix = _read_json(MATRIX_PATH)
    pop = matrix.get("population", {})
    if (pop.get("n_validation_units"), pop.get("n_mapped_tasks")) != (144, 219):
        raise CalibrationFailClosedError("matrix population counts mutated")
    if pop.get("population_identity_sha256") != EXPECTED_POPULATION_IDENTITY:
        raise CalibrationFailClosedError("matrix population identity mutated")
    return matrix


def task_target_commit(tid: str) -> str:
    for row in _read_csv(TASK_ENV_CSV):
        if row["task_id"] == tid:
            commit = row.get("target_commit", "").strip()
            if not commit:
                raise CalibrationFailClosedError(f"task {tid} missing target_commit")
            return commit
    raise CalibrationFailClosedError(f"task {tid} missing from TASK_ENV_MATRIX")


def resolve_execution_image(dp: str, np_id: str) -> dict[str, str]:
    """General execution-image resolution (composite binding; no special cases)."""
    binding = _read_json(BINDING_PATH)
    for rec in binding["pairs"]:
        if rec["docker_profile_id"] == dp and rec["native_profile_id"] == np_id:
            return {
                "docker_profile_id": dp,
                "native_profile_id": np_id,
                "execution_image_ref": rec["execution_image_ref"],
                "immutable_image_id": rec["immutable_image_id"],
                "provenance": rec["provenance"],
            }
    raise CalibrationFailClosedError(f"no binding for ({dp}, {np_id})")


def local_image_id(image: str) -> str | None:
    r = subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "docker", "image", "inspect", "-f", "{{.Id}}", image],
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = r.stdout.strip()
    return out if r.returncode == 0 and out else None


def verify_execution_image_binding(dp: str, np_id: str, uid: str | None = None) -> dict[str, str]:
    """General G11 gate: binding-derived image must exist locally with exact ID.

    ``uid`` is used ONLY to assert the special repaired/recovery evidence
    expectations; resolution itself never special-cases a unit.
    """
    info = resolve_execution_image(dp, np_id)
    image_ref = info["execution_image_ref"]
    image_id = info["immutable_image_id"]
    local = local_image_id(image_ref)
    if local != image_id:
        raise CalibrationFailClosedError(
            f"EXECUTION_IMAGE_BINDING_FAILURE {dp}/{np_id}: local {local} != binding {image_id}"
        )
    if uid == REPAIRED_UNIT:
        if image_ref != REPAIRED_IMAGE_REF or image_id != REPAIRED_IMAGE_ID:
            raise CalibrationFailClosedError(f"unit {uid} not resolved to repaired image")
        if image_ref == OLD_PY39_REF or image_id == OLD_PY39_ID:
            raise CalibrationFailClosedError(f"unit {uid} accidentally py39 image")
    return info


def _win32_names_from_pyproject_commits(commits: list[str]) -> set[str]:
    """Frozen R3 ``win32_platform_names`` over per-member pyproject.toml content.

    Reads each target-commit ``pyproject.toml`` object-authoritatively from the
    local Git object store (WSL) — never from the Windows working tree.
    """
    sys.path.insert(0, str(HARNESS_DIR))
    try:
        from d7_r3_closure import win32_platform_names

        def _win32_names(pyproject_files: list[str]) -> set[str]:
            return set(win32_platform_names(pyproject_files))
    except Exception as exc:  # pragma: no cover - host missing harness
        raise CalibrationFailClosedError(f"R3 harness pyproject parser unavailable: {exc}") from exc
    names: set[str] = set()
    for commit in commits:
        r = subprocess.run(
            ["wsl", "-d", WSL_DISTRO, "--", "git", "-C", WSL_REPO, "show", f"{commit}:pyproject.toml"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode != 0 or not r.stdout.strip():
            continue  # frozen R3 ignores missing pyproject files
        tmp = RUN_ROOT / "materialized" / "tmp_pyproject_refs"
        tmp.mkdir(parents=True, exist_ok=True)
        p = tmp / f"{commit[:12]}_pyproject.toml"
        p.write_text(r.stdout, encoding="utf-8")
        names |= set(_win32_names([str(p)]))
    return names


def marker_excluded_names() -> set[str]:
    audit = _read_json(MARKER_AUDIT)
    out: set[str] = set()
    for name, info in (audit.get("packages") or {}).items():
        if isinstance(info, dict) and info.get("classification") == "MARKER_EXCLUDED_ON_LINUX":
            out.add(name.lower().replace("_", "-"))
    return out


def codecov_excluded_versions() -> set[str]:
    """Frozen D4 non-runtime codecov exclusions (exact affected versions only).

    ``NON_RUNTIME_DEV_CI_TOOL_EXCLUDED`` (owner-authorized D4 amendment).  Any
    other codecov version (e.g. 2.1.11/2.1.12 present in approved stores) is
    NOT excluded by this authority.
    """
    amendment = _read_json(D4_CODECOV_EXCLUSION)
    if amendment.get("classification") != "NON_RUNTIME_DEV_CI_TOOL_EXCLUDED":
        raise CalibrationFailClosedError("D4 codecov amendment classification drift")
    return {str(v) for v in amendment.get("affected_versions", [])}


def runtime_pins(uid: str) -> dict[str, Any]:
    """Derive the frozen R3 platform-compatible install pins for a unit.

    Uses the qualified R4-B integrated parser for the lock closure, then applies
    the frozen R3 platform exclusions (marker audit + pyproject ``platform=win32``).
    """
    plan = load_plan()
    unit = next(c for c in plan["calibration_units"] if c["validation_unit_id"] == uid)
    lock_type = unit["lock_type"]
    python_version = unit["python_version"]
    target = RuntimeTarget(python_version, "cpython", "linux", "x86_64")

    bind_integrated_parser()
    try:
        closures: list[LockClosure] = []
        for tid in unit["member_task_ids"]:
            lock_path = LOCK_DIR / f"{tid}_{lock_type}.toml"
            if not lock_path.is_file():
                raise CalibrationFailClosedError(f"lock artifact missing: {lock_path}")
            closure = parse_lock(lock_path, target)
            if not closure.is_valid:
                raise CalibrationFailClosedError(
                    f"unit {uid} closure invalid: {closure.fail_closed_reasons}"
                )
            closures.append(closure)
    finally:
        unbind_lock_parser()

    # Deduplicate pins across member tasks deterministically.
    pins: dict[str, str] = {}
    editable_selfs: list[str] = []
    for closure in closures:
        if closure.editable_self is not None:
            editable_selfs.append(
                f"{closure.editable_self.normalized_name}=={closure.editable_self.version}"
            )
        for req in closure.requirements:
            pins[req.normalized_name] = req.version

    excluded_marker = marker_excluded_names()
    excluded_codecov_versions = codecov_excluded_versions()
    commits = [task_target_commit(t) for t in unit["member_task_ids"]]
    excluded_win32 = _win32_names_from_pyproject_commits(commits)

    runtime_pin_list: list[str] = []
    excluded_pins: list[dict[str, str]] = []
    for name in sorted(pins):
        version = pins[name]
        if name in excluded_marker or name in excluded_win32:
            excluded_pins.append({"pin": f"{name}=={version}", "reason": "R3_PLATFORM_EXCLUDED"})
            continue
        if name == "codecov" and version in excluded_codecov_versions:
            excluded_pins.append(
                {"pin": f"{name}=={version}", "reason": "D4_NON_RUNTIME_DEV_CI_TOOL_EXCLUDED"}
            )
            continue
        runtime_pin_list.append(f"{name}=={version}")

    return {
        "validation_unit_id": uid,
        "lock_type": lock_type,
        "python_version": python_version,
        "runtime_pins": runtime_pin_list,
        "editable_self_pins": editable_selfs,
        "excluded_pins": excluded_pins,
        "excluded_names": sorted({e["pin"] for e in excluded_pins}),
    }


def build_merged_wheelhouse(era: str) -> Path:
    """Materialize the era's merged wheel input ONCE (wheelhouse + canon_r4b).

    canon wins on filename collision (frozen R3 assemble_runtime_input rule).
    Cached with a completion marker; reused read-only across the run.
    """
    dest = MATERIALIZED_DIR / "merged" / era
    marker = dest / ".complete"
    if marker.is_file():
        return dest
    dest.mkdir(parents=True, exist_ok=True)
    src_wh = WHEELHOUSE_DIR / era
    if not src_wh.is_dir():
        raise CalibrationFailClosedError(f"wheelhouse era dir missing: {src_wh}")
    for wh_file in sorted(src_wh.glob("*.whl")):
        (dest / wh_file.name).write_bytes(wh_file.read_bytes())
    canon = CANON_DIR / era
    if canon.is_dir():
        for identity_dir in sorted(canon.iterdir()):
            wd = identity_dir / "wheels"
            if not wd.is_dir():
                continue
            for cw in sorted(wd.glob("*.whl")):
                (dest / cw.name).write_bytes(cw.read_bytes())
    marker.write_text("complete\n", encoding="utf-8")
    return dest


def build_unit_wheelhouse(
    uid: str,
    era: str,
    sf_inputs: list[dict[str, Any]],
    recovery_input: dict[str, Any] | None,
) -> Path:
    """Frozen per-unit wheel input: base merged + SF/recovery overlay wheels.

    Mirrors the frozen ``sf_calibration12_driver`` precedent: base wheelhouse +
    canon merged once, then the exact overlay wheels overwrite same-named files
    so the frozen overlay artifact is what the container install consumes.
    """
    base = build_merged_wheelhouse(era)
    needs_overlay = uid in SOURCE_FIDELITY_UNITS or uid == RECOVERY_UNIT
    if not needs_overlay:
        return base
    dest = MATERIALIZED_DIR / "unit_wheelhouse" / uid
    marker = dest / ".complete"
    if marker.is_file():
        return dest
    dest.mkdir(parents=True, exist_ok=True)
    for base_file in base.glob("*.whl"):
        (dest / base_file.name).write_bytes(base_file.read_bytes())
    for art in sf_inputs:
        src = Path(art["local_path"])
        if not src.is_file():
            raise CalibrationFailClosedError(f"SF wheel missing for unit {uid}: {src}")
        if _sha256_file(src) != art["output_sha256"]:
            raise CalibrationFailClosedError(f"SF wheel hash drift for {src}")
        (dest / art["output_filename"]).write_bytes(src.read_bytes())
    if recovery_input:
        src = Path(recovery_input["overlay_path"])
        if not src.is_file():
            raise CalibrationFailClosedError(f"recovery wheel missing for {uid}: {src}")
        if _sha256_file(src) != recovery_input["sha256"]:
            raise CalibrationFailClosedError("recovery wheel hash drift")
        (dest / recovery_input["filename"]).write_bytes(src.read_bytes())
    marker.write_text("complete\n", encoding="utf-8")
    return dest


def _resolve_pin_wheels(
    runtime_pins: list[str],
    era: str,
    *,
    wheel_dir: Path | None = None,
) -> dict[str, Any]:
    """R4-A era-aware resolution of every runtime pin against a wheel input.

    Defaults to the era merged wheelhouse; ``wheel_dir`` may point at a
    per-unit wheelhouse that already includes SF/recovery overlay wheels.
    """
    merged = wheel_dir or build_merged_wheelhouse(era)
    wheel_names = sorted(p.name for p in merged.glob("*.whl"))
    target = RuntimeTarget({"py312": "3.12", "py39": "3.9", "py38": "3.8"}[era], "cpython", "linux", "x86_64")
    bind_integrated_parser()
    try:
        from packaging.utils import parse_wheel_filename

        artifacts: dict[tuple[str, str], list[str]] = {}
        for fn in wheel_names:
            try:
                name, version, _b, _tags = parse_wheel_filename(fn)
            except Exception:
                continue
            key = (normalize_name(str(name)), str(version).lower())
            artifacts.setdefault(key, []).append(fn)

        resolved: dict[str, str] = {}
        missing: list[str] = []
        incompatible: list[dict[str, Any]] = []
        for pin in runtime_pins:
            pname, pver = pin.split("==", 1)
            key = (normalize_name(pname), pver.lower())
            cands = artifacts.get(key, [])
            if not cands:
                missing.append(pin)
                continue
            ok = [fn for fn in cands if wheel_compatible(fn, target)]
            if not ok:
                incompatible.append({"pin": pin, "candidates": cands})
                continue
            resolved[pin] = sorted(ok)[0]
    finally:
        unbind_lock_parser()
    return {"resolved": resolved, "missing": sorted(set(missing)), "incompatible": incompatible,
            "wheel_dir": str(merged)}


def source_fidelity_overlay_inputs(uid: str) -> list[dict[str, Any]]:
    """Frozen source-fidelity overlay wheel inputs for units 1 and 2."""
    manifest = _read_json(SF_MANIFEST)
    out: list[dict[str, Any]] = []
    for art in manifest.get("artifacts", []):
        if not art.get("promoted", True):
            continue
        wpath = SF_WHEELS / str(art.get("output_filename", ""))
        if not wpath.is_file():
            raise CalibrationFailClosedError(f"SF wheel missing: {wpath}")
        disk = _sha256_file(wpath)
        expected = art.get("output_sha256")
        if not expected or disk != expected:
            raise CalibrationFailClosedError(
                f"SF wheel hash mismatch {wpath.name}: expected {expected} got {disk}"
            )
        out.append(
            {
                "dependency_name": art.get("dependency_name"),
                "declared_version": art.get("declared_version"),
                "output_filename": art.get("output_filename"),
                "output_sha256": disk,
                "source_type": art.get("source_type"),
                "vendored_source_path": art.get("vendored_source_path"),
                "source_tree_sha256": art.get("source_tree_sha256"),
                "target_commit": art.get("target_commit"),
                "local_path": str(wpath),
            }
        )
    if uid in SOURCE_FIDELITY_UNITS and len(out) != 2:
        raise CalibrationFailClosedError(f"unit {uid} expected exactly 2 SF wheels, got {len(out)}")
    return out


def recovery_overlay_input() -> dict[str, Any]:
    """Frozen R4-E recovery overlay wheel (pylint==2.9.6) for unit 10."""
    manifest = _read_json(RECOVERY_MANIFEST)
    for art in manifest.get("artifacts", []):
        if str(art.get("version")) != "2.9.6":
            continue
        wpath = RECOVERY_WHEELS / str(art["filename"])
        if not wpath.is_file():
            raise CalibrationFailClosedError(f"recovery wheel missing: {wpath}")
        disk = _sha256_file(wpath)
        expected = art.get("actual_sha256")
        if not expected or disk != expected:
            raise CalibrationFailClosedError(
                f"recovery wheel hash mismatch: expected {expected} got {disk}"
            )
        return {
            "package": art.get("package"),
            "version": art.get("version"),
            "filename": art.get("filename"),
            "sha256": disk,
            "overlay_path": str(wpath),
            "manifest_sha256": _sha256_file(RECOVERY_MANIFEST),
            "e2_receipt_mission": _read_json(E2_RECEIPT_PATH).get("mission_id"),
        }
    raise CalibrationFailClosedError("recovery manifest missing pylint == 2.9.6")


def container_script(_uid: str, wt_count: int, native_pkgs: list[str],
                     special: dict[str, Any]) -> str:
    """Frozen D7/R3 behavioral container script (semantics reused verbatim)."""
    wts = " ".join(f"/wt{i}" for i in range(wt_count))
    lines = [
        "set +e",
        "mkdir -p /tmp/d7 /out",
        "echo '=== NETPROBE ==='",
        r'''python - <<'PYEOF'
import socket, json
host="pypi.org"; port=443
socket.setdefaulttimeout(3)
res={"dns":{"reachable":False},"tcp":[]}
try:
    infos=socket.getaddrinfo(host,port,proto=socket.IPPROTO_TCP)
    addrs=sorted({i[4][0] for i in infos})
    res["dns"]={"reachable":True,"addrs":addrs}
except socket.gaierror as e:
    res["dns"]={"reachable":False,"errstr":str(e)}
tcp_ok=False
for tgt in (res["dns"].get("addrs",[])[:2] or [host]):
    try:
        s=socket.create_connection((tgt,port),timeout=3); s.close(); tcp_ok=True
    except Exception:
        pass
if res["dns"]["reachable"] and tcp_ok:
    st="NETWORK_REACHABLE"
elif not res["dns"]["reachable"] and not tcp_ok:
    st="NETWORK_UNAVAILABLE"
else:
    st="AMBIGUOUS"
res["status"]=st
print("NET_STATUS="+st)
open("/tmp/d7/netprobe.json","w").write(json.dumps(res))
PYEOF''',
        "cp /tmp/d7/netprobe.json /out/netprobe.json",
        "echo '=== PYVER ==='",
        "python --version >/tmp/d7/pyver.txt 2>&1",
        "cat /tmp/d7/pyver.txt",
        "cp /tmp/d7/pyver.txt /out/pyver.txt",
        "echo '=== INSTALL (wheel-only, frozen closure) ==='",
        "T0=$(date +%s%3N)",
        "uv pip install --system --no-index --find-links /wheelhouse --only-binary=:all: -r /reqs/requirements-lock.txt >/tmp/d7/install.log 2>&1",  # noqa: E501
        "IR=$?",
        "T1=$(date +%s%3N)",
        "echo \"INSTALL_RC=$IR\"",
        "echo \"INSTALL_MS=$((T1-T0))\"",
        "cp /tmp/d7/install.log /out/install.log",
        "echo '=== PIPLIST ==='",
        "python -m pip list --format=freeze >/tmp/d7/pipfreeze.txt 2>&1",
        "cp /tmp/d7/pipfreeze.txt /out/pipfreeze.txt",
        "echo '=== TOOLHOUSE AUDIT (frozen) ==='",
        r'''PYTHONPATH=/harness python - <<'PYEOF'
import json, importlib.metadata
from d7_r3_probes import audit_toolhouse_contamination
names = sorted({d.metadata["Name"].lower().replace("_","-") for d in importlib.metadata.distributions()
              if d.metadata and d.metadata.get("Name")})
contam = audit_toolhouse_contamination(names)
print("TOOLHOUSE_PRESENT=" + json.dumps(contam))
data = {"contamination": contam, "n_installed": len(names)}
open("/out/toolhouse.json","w").write(json.dumps(data, indent=2, sort_keys=True))
PYEOF''',
        "echo '=== PIPCHECK ==='",
        "pip check >/tmp/d7/pipcheck.log 2>&1",
        "echo \"PIPCHECK_RC=$?\"",
        "cp /tmp/d7/pipcheck.log /out/pipcheck.log",
        "echo '=== NATIVE (frozen modules) ==='",
        f"echo '{{\"packages\": {json.dumps(native_pkgs)}}}' >/tmp/d7/profile.json",
        r'''PYTHONPATH=/harness python - <<'PYEOF'
import json, subprocess, os
from d7_r3_native_specs import PATH_PROBE, EXEC_PROBE
from d7_r3_probes import derive_probe_payload, run_native_probes
profile = json.load(open("/tmp/d7/profile.json", encoding="utf-8"))
pkgs = profile["packages"]
try:
    payload = derive_probe_payload(pkgs)
except KeyError as e:
    print("NATIVE_SPEC_GAP=" + str(e))
    open("/out/native.json","w").write(json.dumps({"spec_gap": str(e)}))
    raise SystemExit(0)
out = subprocess.run(["ldconfig","-p"], capture_output=True, text=True).stdout or ""
loader_tokens = [ln.strip() for ln in out.splitlines() if ln.strip()]
fs = {}
exec_resolutions = {}
for pkg, spec in payload.items():
    if spec["kind"] == PATH_PROBE:
        fs[spec["path"]] = os.path.exists(spec["path"])
    elif spec["kind"] == EXEC_PROBE:
        exe = spec["executable"]
        r = subprocess.run(["sh","-lc","command -v " + exe], capture_output=True, text=True)
        resolved = (r.stdout or "").strip().splitlines()
        resolved = resolved[0] if resolved else ""
        if resolved:
            exec_resolutions[exe] = resolved
            fs[resolved] = os.path.exists(resolved)
failures = run_native_probes(payload, loader_tokens, fs, exec_resolutions)
print("NATIVE_FAILURES=" + json.dumps(failures))
print("EXEC_RESOLUTIONS=" + json.dumps(exec_resolutions))
open("/out/native.json","w").write(json.dumps({"failures": failures,
    "profile_packages": pkgs,
    "loader_tokens": loader_tokens[:40],
    "fs": fs,
    "exec_resolutions": exec_resolutions}, indent=2, sort_keys=True))
PYEOF''',
    ]
    # Special evidence probes (only when applicable; no semantic change).
    if special.get("pyver_major_minor"):
        lines.append("echo '=== SPECIAL PYVER PROBE ==='")
        lines.append("python - <<'PYEOF'\n"
                     "import sys, json\n"
                     "print('SPECIAL_PYVER=' + '%d.%d' % (sys.version_info[0], sys.version_info[1]))\n"
                     "mm = '%d.%d' % (sys.version_info[0], sys.version_info[1])\n"
                     "open('/out/special_pyver.json','w').write(json.dumps({'major_minor': mm}))\n"
                     "PYEOF"
                     )
    if special.get("version_probes"):
        pkgs = special["version_probes"]
        lines.append("echo '=== SPECIAL VERSION PROBES ==='")
        lines.append(
            "python - <<'PYEOF'\n"
            "import json, importlib.metadata\n"
            "probes = " + json.dumps(pkgs) + "\n"
            "out = {}\n"
            "for pkg in probes:\n"
            "    try:\n"
            "        v = importlib.metadata.version(pkg)\n"
            "        out[pkg] = v\n"
            "        print('VERSION_%s=' % pkg.upper().replace('-','_') + v)\n"
            "    except Exception as e:\n"
            "        out[pkg] = 'MISSING'\n"
            "        print('VERSION_%s=MISSING' % pkg.upper().replace('-','_'))\n"
            "open('/out/version_probes.json','w').write(json.dumps(out, indent=2, sort_keys=True))\n"
            "PYEOF"
        )
    if wts:
        lines += [
            "echo '=== SMOKE ==='",
            f"for wt in {wts}; do",
            "  if [ -d \"$wt\" ]; then",
            "    echo \"== SMOKE $(basename $wt) ==\"",
            "    cd \"$wt\"",
            "    python -c \"import saleor\" >/tmp/d7/import_$(basename $wt).log 2>&1",
            "    echo \"IMPORT_RC_$(basename $wt)=$?\"",
            "    cp /tmp/d7/import_$(basename $wt).log /out/import_$(basename $wt).log",
            "    if [ -f manage.py ]; then",
            "      python manage.py check --settings=saleor.tests.settings >/tmp/d7/manage_$(basename $wt).log 2>&1",
            "      echo \"MANAGE_RC_$(basename $wt)=$?\"",
            "      cp /tmp/d7/manage_$(basename $wt).log /out/manage_$(basename $wt).log",
            "    else",
            "      echo \"MANAGE_RC_$(basename $wt)=SKIP\"",
            "    fi",
            "    if [ -f pytest.ini ] || [ -f pyproject.toml ]; then",
            "      python -m pytest --collect-only -q >/tmp/d7/pytest_$(basename $wt).log 2>&1",
            "      echo \"PYTEST_RC_$(basename $wt)=$?\"",
            "      cp /tmp/d7/pytest_$(basename $wt).log /out/pytest_$(basename $wt).log",
            "    else",
            "      echo \"PYTEST_RC_$(basename $wt)=SKIP\"",
            "    fi",
            "  fi",
            "done",
        ]
    lines.append("echo 'D7_UNIT_DONE'")
    return "\n".join(lines)


def parse_output(out: str) -> dict[str, Any]:
    res: dict[str, Any] = {}
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("NET_STATUS="):
            res["network_status"] = line.split("=", 1)[1]
        elif line.startswith("SPECIAL_PYVER="):
            res["special_pyver"] = line.split("=", 1)[1]
        elif line.startswith("VERSION_"):
            k, v = line.split("=", 1)
            res.setdefault("version_probes", {})[k[len("VERSION_"):].lower()] = v
        elif line.startswith("INSTALL_RC="):
            res["install_rc"] = int(line.split("=", 1)[1])
        elif line.startswith("INSTALL_MS="):
            res["install_ms"] = int(line.split("=", 1)[1])
        elif line.startswith("TOOLHOUSE_PRESENT="):
            res["toolhouse_present"] = json.loads(line.split("=", 1)[1] or "[]")
        elif line.startswith("PIPCHECK_RC="):
            res["pipcheck_rc"] = int(line.split("=", 1)[1])
        elif line.startswith("NATIVE_FAILURES="):
            res["native_failures"] = json.loads(line.split("=", 1)[1] or "[]")
        elif line.startswith("NATIVE_SPEC_GAP="):
            res["native_spec_gap"] = line.split("=", 1)[1]
        elif line.startswith("EXEC_RESOLUTIONS="):
            res["exec_resolutions"] = json.loads(line.split("=", 1)[1] or "{}")
        elif line.startswith("IMPORT_RC_"):
            k = line.split("=", 1)[0][len("IMPORT_RC_"):]
            res.setdefault("smoke", {})[f"import_{k}"] = line.split("=", 1)[1]
        elif line.startswith("MANAGE_RC_"):
            k = line.split("=", 1)[0][len("MANAGE_RC_"):]
            res.setdefault("smoke", {})[f"manage_{k}"] = line.split("=", 1)[1]
        elif line.startswith("PYTEST_RC_"):
            k = line.split("=", 1)[0][len("PYTEST_RC_"):]
            res.setdefault("smoke", {})[f"pytest_{k}"] = line.split("=", 1)[1]
    return res


def classify_unit(run: dict[str, Any], *, special: dict[str, Any]) -> str:
    """Fail-closed gate order mirroring the frozen R3 driver."""
    if run.get("network_status") != "NETWORK_UNAVAILABLE":
        return F_ENV_DOCKER_IMAGE
    if run.get("install_rc") != 0:
        return F_ENV_OFFLINE_INSTALL
    if run.get("toolhouse_present"):
        return F_ENV_DEPENDENCY_CONSISTENCY
    if run.get("pipcheck_rc") != 0:
        return F_ENV_DEPENDENCY_CONSISTENCY
    if run.get("native_spec_gap"):
        return F_ENV_NATIVE_PROBE
    if run.get("native_failures"):
        return F_ENV_NATIVE_PROBE
    if special.get("pyver_major_minor") and run.get("special_pyver") != special["pyver_major_minor"]:
        return F_ENV_IMPORT_SMOKE
    smoke = run.get("smoke", {})
    for k, v in smoke.items():
        if k.startswith("import_") and v not in ("0", "SKIP"):
            return F_ENV_IMPORT_SMOKE
    for k, v in smoke.items():
        if k.startswith("manage_") and v not in ("0", "SKIP"):
            return F_ENV_FRAMEWORK_GATE
    for k, v in smoke.items():
        if k.startswith("pytest_") and v not in ("0", "SKIP"):
            return F_ENV_PYTEST_COLLECTION
    vp = run.get("version_probes", {})
    for pkg, expected in (special.get("version_probes") or {}).items():
        if str(vp.get(pkg.lower(), "")) != str(expected):
            return F_ENV_IMPORT_SMOKE
    return "PASS"


def _translate_mount(win_path: Path) -> str:
    p = str(win_path.resolve()).replace("\\", "/")
    if ":" in p.split("/", 1)[0]:
        drive, rest = p.split(":", 1)
        return f"/mnt/{drive.lower()}{rest}"
    return p


class UnitRunner:
    """Runs exactly one calibration unit under frozen authority."""

    def __init__(self) -> None:
        self.backend = WslDockerBackend(distro=WSL_DISTRO)

    def _wiring(self) -> LinuxTreeWiring:
        source = R4MaterializationSource(
            image=MATERIALIZE_IMAGE,
            repo_linux_path=WSL_REPO,
            image_verified=True,
        )
        return LinuxTreeWiring(self.backend, source)

    def materialize(self, commit: str, uid: str, tid: str, index: int) -> tuple[str, int]:
        """Materialize one member task commit into a fresh Linux volume."""
        vol = f"r4n12_{uid.replace('-', '_')}_{tid.replace('-', '_')}_{index}"
        ensure_empty_volume(self.backend, vol)
        try:
            count = self._wiring().materialize(commit, vol)
        except MaterializeError as exc:
            raise CalibrationFailClosedError(
                f"LINUX_MATERIALIZATION_FAILURE {uid} {tid}: {exc}"
            ) from exc
        if count <= 0:
            raise CalibrationFailClosedError(f"materialization produced 0 files for {tid}")
        return vol, count

    @staticmethod
    def cleanup_volume(vol: str) -> None:
        remove_volume(WslDockerBackend(distro=WSL_DISTRO), vol)

    def run_unit(self, idx: int) -> dict[str, Any]:
        plan = load_plan()
        # Fail-fast: prior frozen-order units must all be PASS before this one.
        progress: dict[str, Any] = {"completed": []}
        if PROGRESS_JSON.is_file():
            progress = _read_json(PROGRESS_JSON)
        completed = progress.get("completed", [])
        existing = {c["calibration_index"]: c for c in completed}
        for prior in range(1, idx):
            c = existing.get(prior)
            if c is None:
                raise CalibrationFailClosedError(
                    f"prior unit {FROZEN_UNIT_ORDER[prior - 1]} (index {prior}) not executed; "
                    "fail-fast order violated"
                )
            if c["result"] != "PASS":
                raise CalibrationFailClosedError(
                    f"prior unit {c['validation_unit_id']} FAILED ({c['classification']}); "
                    "refusing to run later units"
                )
        if idx in existing:
            raise CalibrationFailClosedError(
                f"unit index {idx} already executed -> {existing[idx]['result']}; "
                "output overwrite is prohibited"
            )

        unit = plan["calibration_units"][idx - 1]
        uid = unit["validation_unit_id"]
        member_tasks = list(unit["member_task_ids"])
        dp = unit["docker_profile_id"]
        np_id = unit["native_profile_id"]
        era = unit["wheelhouse_era"]
        python_version = unit["python_version"]
        lock_type = unit["lock_type"]
        install_route = unit["install_route"]

        if install_route not in ALLOWED_INSTALL_ROUTES:
            raise CalibrationFailClosedError(f"unit {uid} unknown install route {install_route}")

        image_info = verify_execution_image_binding(dp, np_id, uid=uid)
        image_ref = image_info["execution_image_ref"]
        image_id = image_info["immutable_image_id"]

        pins_info = runtime_pins(uid)
        pins = pins_info["runtime_pins"]

        start_utc = utcnow()
        t0 = time.time()
        out_dir = UNITS_DIR / uid
        out_dir.mkdir(parents=True, exist_ok=True)

        # Source-fidelity / recovery overlay inputs (bounded to exact units).
        sf_inputs: list[dict[str, Any]] = []
        recovery_input: dict[str, Any] | None = None
        if uid in SOURCE_FIDELITY_UNITS:
            sf_inputs = source_fidelity_overlay_inputs(uid)
        if uid == RECOVERY_UNIT:
            recovery_input = recovery_overlay_input()

        wheel_input = build_unit_wheelhouse(uid, era, sf_inputs, recovery_input)
        resolution = _resolve_pin_wheels(pins, era, wheel_dir=wheel_input)
        if resolution["missing"] or resolution["incompatible"]:
            raise CalibrationFailClosedError(
                f"ENV_ARTIFACT_RESOLUTION_FAILURE {uid}: "
                f"missing={resolution['missing']} incompatible={resolution['incompatible']}"
            )

        # requirements-lock.txt
        req_file = out_dir / "requirements-lock.txt"
        req_file.write_text("\n".join(pins) + "\n", encoding="utf-8", newline="\n")
        lock_sha = _sha256_file(req_file)

        # Native profile packages
        profiles = _read_json(DOCKER_PROFILES)
        native_pkgs = profiles.get("native_profiles", {}).get(np_id, [])

        # Materialize each member task commit (Linux-faithful, R4-C).
        volumes: list[str] = []
        materialized: list[dict[str, Any]] = []
        try:
            for i, tid in enumerate(member_tasks):
                commit = task_target_commit(tid)
                vol, count = self.materialize(commit, uid, tid, i)
                volumes.append(vol)
                materialized.append(
                    {"task_id": tid, "target_commit": commit, "volume": vol, "file_count": count}
                )

            special: dict[str, Any] = {"version_probes": {}}
            if uid == REPAIRED_UNIT:
                special["pyver_major_minor"] = "3.12"
            if uid in SOURCE_FIDELITY_UNITS:
                for art in sf_inputs:
                    special["version_probes"][art["dependency_name"]] = art["declared_version"]
            if uid == RECOVERY_UNIT and recovery_input:
                special["version_probes"]["pylint"] = "2.9.6"

            script = container_script(uid, len(member_tasks), native_pkgs, special)
            volumes_flag = []
            for i in range(len(member_tasks)):
                volumes_flag += ["-v", f"{volumes[i]}:/wt{i}:ro"]
            req_local = _translate_mount(req_file)
            merged_mnt = _translate_mount(wheel_input)
            harness_mnt = _translate_mount(HARNESS_DIR)
            out_mnt = _translate_mount(out_dir)

            cmd = [
                "docker", "run", "--rm", "--network=none",
                *volumes_flag,
                "-v", f"{merged_mnt}:/wheelhouse:ro",
                "-v", f"{req_local}:/reqs/requirements-lock.txt:ro",
                "-v", f"{harness_mnt}:/harness:ro",
                "-v", f"{out_mnt}:/out:rw",
                image_ref, "sh", "-lc", script,
            ]
            r = self.backend.run(cmd, timeout_s=INSTALL_TIMEOUT_S)
            if r.returncode == 124:
                parsed: dict[str, Any] = {}
                elapsed = round(time.time() - t0, 2)
                return self._finish_unit(uid, idx, member_tasks, image_ref, image_id,
                                          dp, np_id, python_version, lock_type, install_route,
                                          era, pins, lock_sha, sf_inputs, recovery_input,
                                          parsed, elapsed, F_ENV_TIMEOUT, start_utc,
                                          materialized, "TIMEOUT", volumes, r.stdout, r.stderr,
                                          wheel_input=wheel_input, resolution=resolution)
            parsed = parse_output(r.stdout)
            elapsed = round(time.time() - t0, 2)
            classification = classify_unit(parsed, special=special)
            return self._finish_unit(uid, idx, member_tasks, image_ref, image_id,
                                      dp, np_id, python_version, lock_type, install_route,
                                      era, pins, lock_sha, sf_inputs, recovery_input,
                                      parsed, elapsed, classification, start_utc,
                                      materialized, ("PASS" if classification == "PASS" else "FAIL"),
                                      volumes, r.stdout, r.stderr,
                                      wheel_input=wheel_input, resolution=resolution)
        finally:
            import contextlib

            for vol in volumes:
                with contextlib.suppress(Exception):
                    self.cleanup_volume(vol)

    def _finish_unit(self, uid: str, idx: int, member_tasks: list[str],
                     image_ref: str, image_id: str, dp: str, np_id: str,
                     python_version: str, lock_type: str, install_route: str,
                     era: str, pins: list[str], lock_sha: str,
                     sf_inputs: list[dict[str, Any]], recovery_input: dict[str, Any] | None,
                     parsed: dict[str, Any], elapsed_seconds: float,
                     classification: str, start_utc: str,
                     materialized: list[dict[str, Any]], result: str,
                     _volumes: list[str], stdout: str, stderr: str,
                     wheel_input: Path | None = None,
                     resolution: dict[str, Any] | None = None) -> dict[str, Any]:
        out_dir = UNITS_DIR / uid
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "docker_stdout.log").write_text(stdout, encoding="utf-8")
        if stderr:
            (out_dir / "docker_stderr.log").write_text(stderr, encoding="utf-8")
        record: dict[str, Any] = {
            "schema_version": "env-canon-r4-behavioral-calibration-n12-r2/1.0",
            "calibration_index": idx,
            "validation_unit_id": uid,
            "member_task_ids": member_tasks,
            "docker_profile_id": dp,
            "native_profile_id": np_id,
            "python_version": python_version,
            "lock_type": lock_type,
            "install_route": install_route,
            "wheelhouse_era": era,
            "execution_image_ref": image_ref,
            "immutable_image_id": image_id,
            "resolved_image_matches_binding": True,
            "runtime_pins_count": len(pins),
            "requirements_lock_sha256": lock_sha,
            "wheel_input_dir": str(wheel_input) if wheel_input else None,
            "artifact_provenance": {
                "resolved_wheels": (resolution or {}).get("resolved"),
                "missing": (resolution or {}).get("missing", []),
                "incompatible": (resolution or {}).get("incompatible", []),
            },
            "source_fidelity_inputs": sf_inputs,
            "recovery_overlay_input": recovery_input,
            "materialized": materialized,
            "start_utc": start_utc,
            "elapsed_seconds": elapsed_seconds,
            "run": parsed,
            "result": result,
            "classification": classification,
        }
        if recovery_input:
            record["recovery_overlay_consumed"] = {
                "expected_pylint": "2.9.6",
                "wheel_filename": recovery_input["filename"],
                "wheel_sha256": recovery_input["sha256"],
                "overlay_path": recovery_input["overlay_path"],
                "manifest_sha256": recovery_input["manifest_sha256"],
                "installed_pylint": parsed.get("version_probes", {}).get("pylint"),
            }
        result_path = out_dir / "result.json"
        result_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self._save_progress(record)
        return record

    @staticmethod
    def _save_progress(record: dict[str, Any]) -> None:
        PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
        progress: dict[str, Any] = {"completed": [], "stopped_early": False}
        if PROGRESS_JSON.is_file():
            progress = _read_json(PROGRESS_JSON)
        completed = [c for c in progress["completed"] if c["validation_unit_id"] != record["validation_unit_id"]]
        completed.append(
            {
                "validation_unit_id": record["validation_unit_id"],
                "calibration_index": record["calibration_index"],
                "result": record["result"],
                "classification": record["classification"],
                "elapsed_seconds": record["elapsed_seconds"],
            }
        )
        progress["completed"] = completed
        PROGRESS_JSON.write_text(json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_authority() -> dict[str, Any]:
    """CAL2-A: branch/HEAD/clean-tree/provenance/population/plan/hash coverage."""
    provenance = verify_import_provenance()
    plan = load_plan()
    load_binding()
    load_matrix()
    evidence = {
        "authority": "PASS",
        "import_provenance": provenance,
        "plan_sha256": plan["plan_sha256"],
        "n_calibration": plan["n_calibration"],
        "ordered_unit_ids": [c["validation_unit_id"] for c in plan["calibration_units"]],
        "population": plan["population"],
        "population_identity_sha256": plan["source_population_identity_sha256"],
        "required_categories": len(plan["required_categories"]),
        "uncovered_categories": plan["uncovered_categories"],
    }
    return evidence


def verify_images() -> dict[str, Any]:
    """CAL2-B: every N12 pair resolves through the binding with exact local IDs."""
    plan = load_plan()
    results: list[dict[str, Any]] = []
    all_ok = True
    for c in plan["calibration_units"]:
        uid = c["validation_unit_id"]
        info = resolve_execution_image(c["docker_profile_id"], c["native_profile_id"])
        local = local_image_id(info["execution_image_ref"])
        ok = local == info["immutable_image_id"]
        if not ok:
            all_ok = False
        results.append(
            {
                "validation_unit_id": uid,
                "docker_profile_id": c["docker_profile_id"],
                "native_profile_id": c["native_profile_id"],
                "execution_image_ref": info["execution_image_ref"],
                "immutable_image_id": info["immutable_image_id"],
                "local_image_id": local,
                "match": ok,
            }
        )
    repaired = next(r for r in results if r["validation_unit_id"] == REPAIRED_UNIT)
    if repaired["execution_image_ref"] != REPAIRED_IMAGE_REF:
        all_ok = False
    if repaired["immutable_image_id"] != REPAIRED_IMAGE_ID:
        all_ok = False
    if not all_ok:
        raise CalibrationFailClosedError("CAL2-B image binding mismatch")
    return {"authority": "PASS", "units": results}


def verify_readiness() -> dict[str, Any]:
    """CAL2-C: bounded artifact/readiness closure for the exact N12 only."""
    plan = load_plan()
    rows: list[dict[str, Any]] = []
    for c in plan["calibration_units"]:
        uid = c["validation_unit_id"]
        pins_info = runtime_pins(uid)
        sf_inputs: list[dict[str, Any]] = []
        recovery_input: dict[str, Any] | None = None
        if uid in SOURCE_FIDELITY_UNITS:
            sf_inputs = source_fidelity_overlay_inputs(uid)
        if uid == RECOVERY_UNIT:
            recovery_input = recovery_overlay_input()
        wheel_input = build_unit_wheelhouse(uid, c["wheelhouse_era"], sf_inputs, recovery_input)
        resolution = _resolve_pin_wheels(pins_info["runtime_pins"], c["wheelhouse_era"],
                                         wheel_dir=wheel_input)
        row = {
            "validation_unit_id": uid,
            "runtime_pins_count": len(pins_info["runtime_pins"]),
            "wheel_input": str(wheel_input),
            "missing": resolution["missing"],
            "incompatible": resolution["incompatible"],
            "editable_self_pins": pins_info["editable_self_pins"],
            "excluded_pins": pins_info["excluded_pins"],
            "excluded_names": pins_info["excluded_names"],
        }
        if sf_inputs:
            row["source_fidelity_inputs"] = sf_inputs
        if recovery_input:
            row["recovery_overlay_input"] = recovery_input
        if row["missing"] or row["incompatible"]:
            raise CalibrationFailClosedError(
                f"CAL2-C artifact closure failed for {uid}: "
                f"missing={row['missing']} incompatible={row['incompatible']}"
            )
        rows.append(row)
    return {"authority": "PASS", "units": rows}


def write_binding_evidence() -> dict[str, Any]:
    """CAL2-D: write additive behavioral binding evidence."""
    plan = load_plan()
    binding = load_binding()
    evidence: dict[str, Any] = {
        "schema_version": "env-canon-r4-behavioral-calibration-n12-r2/1.0",
        "mission_id": "M17_D7_R4_BEHAVIORAL_CALIBRATION_N12_R2",
        "authority_hierarchy": [
            "frozen R4-D population/calibration plan",
            "qualified execution-image composite binding",
            "qualified R4-A/B/C providers",
            "qualified R4-E3 artifact/readiness evidence",
            "source-fidelity frozen evidence",
            "frozen D7/R3 behavioral execution semantics",
            "mission-local additive orchestration only",
        ],
        "plan_sha256": plan["plan_sha256"],
        "binding_semantic_hash": binding["deterministic_binding_hash"],
        "install_command": (
            "uv pip install --system --no-index --find-links /wheelhouse "
            "--only-binary=:all: -r /reqs/requirements-lock.txt"
        ),
        "network_isolation": "--network=none",
        "timeout_seconds": INSTALL_TIMEOUT_S,
        "mandatory_gates": [
            "G1 MATERIALIZATION",
            "G2 OFFLINE_ARTIFACT_RESOLUTION",
            "G3 NETWORK_ISOLATION",
            "G4 INSTALL",
            "G5 PIP_CHECK",
            "G6 NATIVE_PROFILE",
            "G7 IMPORT_SMOKE",
            "G8 FRAMEWORK_MANAGE",
            "G9 PYTEST_COLLECTION",
            "G10 ARTIFACT_PROVENANCE",
            "G11 EXECUTION_IMAGE_BINDING",
        ],
        "units": [],
    }
    for c in plan["calibration_units"]:
        uid = c["validation_unit_id"]
        image = resolve_execution_image(c["docker_profile_id"], c["native_profile_id"])
        evidence["units"].append(
            {
                "calibration_index": FROZEN_UNIT_ORDER.index(uid) + 1,
                "validation_unit_id": uid,
                "member_task_ids": c["member_task_ids"],
                "python_version": c["python_version"],
                "lock_type": c["lock_type"],
                "install_route": c["install_route"],
                "wheelhouse_era": c["wheelhouse_era"],
                "docker_profile_id": c["docker_profile_id"],
                "native_profile_id": c["native_profile_id"],
                "execution_image_ref": image["execution_image_ref"],
                "immutable_image_id": image["immutable_image_id"],
                "source_fidelity_overlay": uid in SOURCE_FIDELITY_UNITS,
                "recovery_overlay": uid == RECOVERY_UNIT,
            }
        )
    BINDING_OUT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"authority": "PASS", "binding_evidence_path": str(BINDING_OUT)}


def aggregate() -> dict[str, Any]:
    """CAL2-K: aggregate only after 12/12 PASS."""
    if not PROGRESS_JSON.is_file():
        raise CalibrationFailClosedError("no progress file")
    progress = _read_json(PROGRESS_JSON)
    completed = progress["completed"]
    if len(completed) != 12:
        raise CalibrationFailClosedError(f"N_EXECUTED={len(completed)} != 12")
    order = [c["validation_unit_id"] for c in completed]
    if order != list(FROZEN_UNIT_ORDER):
        raise CalibrationFailClosedError("aggregate order mismatch")
    if any(c["result"] != "PASS" for c in completed):
        raise CalibrationFailClosedError("aggregate contains a FAIL")
    return {
        "N_EXECUTED": len(completed),
        "N_PASS": sum(1 for c in completed if c["result"] == "PASS"),
        "N_FAIL": sum(1 for c in completed if c["result"] != "PASS"),
        "order_preserved": order == list(FROZEN_UNIT_ORDER),
        "units": completed,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="M17_D7_R4 Behavioral Calibration N12 R2")
    ap.add_argument("--preflight", action="store_true", help="CAL2-A/B/C authority preflight")
    ap.add_argument("--unit", type=int, default=None, help="run exactly one unit (1..12)")
    ap.add_argument("--binding", action="store_true", help="write CAL2-D binding evidence")
    ap.add_argument("--aggregate", action="store_true", help="CAL2-K aggregate")
    ap.add_argument("--verify-images", action="store_true", help="CAL2-B only")
    args = ap.parse_args()

    try:
        if args.preflight:
            a = verify_authority()
            b = verify_images()
            c = verify_readiness()
            print(json.dumps({"CAL2_A": a, "CAL2_B": b, "CAL2_C": c}, indent=2, sort_keys=True))
            print("PREFLIGHT_PASS")
            return 0
        if args.verify_images:
            print(json.dumps(verify_images(), indent=2, sort_keys=True))
            print("CAL2_B_PASS")
            return 0
        if args.binding:
            print(json.dumps(write_binding_evidence(), indent=2, sort_keys=True))
            print("BINDING_WRITTEN")
            return 0
        if args.aggregate:
            print(json.dumps(aggregate(), indent=2, sort_keys=True))
            print("AGGREGATE_PASS")
            return 0
        if args.unit is not None:
            if not (1 <= args.unit <= 12):
                print("UNIT_INDEX_OUT_OF_RANGE")
                return 2
            runner = UnitRunner()
            record = runner.run_unit(args.unit)
            print(json.dumps(
                {k: record.get(k) for k in (
                    "calibration_index", "validation_unit_id", "result", "classification",
                    "elapsed_seconds", "network_status", "install_rc", "pipcheck_rc",
                    "native_failures", "resolved_image_matches_binding", "execution_image_ref",
                )} | {"run": {k: record["run"].get(k) for k in (
                    "network_status", "install_rc", "pipcheck_rc", "native_failures",
                    "special_pyver", "version_probes", "smoke",
                )}},
                indent=2, sort_keys=True))
            if record["result"] != "PASS":
                print(f"UNIT_FAIL {record['validation_unit_id']} -> {record['classification']}")
                return 1
            print(f"UNIT_PASS {record['validation_unit_id']}")
            return 0
    except CalibrationFailClosedError as exc:
        print(f"FAIL_CLOSED {exc}", file=sys.stderr)
        return 1
    except TimeoutError as exc:
        print(f"TIMEOUT {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"UNEXPECTED_FAILURE {exc!r}", file=sys.stderr)
        return 2

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
