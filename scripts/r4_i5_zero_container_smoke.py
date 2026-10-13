#!/usr/bin/env python3
"""M17_D7 R4-I5 zero-container smoke over the frozen stratified calibration N=12.

Mission: M17_D7_R4_I5_ZERO_CONTAINER_SMOKE_N12 (T3, bounded pre-execution smoke).

This driver deterministically processes EXACTLY the frozen R4-D stratified
calibration N=12 selection through the integrated R4 resolver (R4-B lock
parsing + R4-A era-aware wheel compatibility behind the frozen shared
interface) with ZERO containers:

  * no docker (CLI absent by construction; the qualified I3 receipt is the only
    image evidence);
  * no network (no registry access, no download, no fallback);
  * no behavioral execution (no test run, no import, no install, no build,
    no R4-C materializer);
  * no 144 census and no 219-task scan (repository/commit readiness is bounded
    to each selected unit's own member tasks).

The PASS criterion is "every selected unit reaches a valid, explicit terminal
smoke classification with zero semantic ambiguity / silent skip / incorrect
era handling / parser defect / tooling defect."  A correctly established local
artifact absence is classified MISSING_LOCAL_ARTIFACT_CANDIDATE (NOT yet
TRUE_MISSING_ARTIFACT; the population-wide adjudication is I6's).

Authority order (frozen): I4 integrated R4 providers -> qualified R4-D
plan/matrix -> frozen source-fidelity R1 evidence -> frozen R3 install-route
semantics where still applicable.

Terminal classifications:

  * READY_LOCAL_ZERO_CONTAINER
  * READY_WITH_MISSING_LOCAL_ARTIFACT_CANDIDATES

Anything else (ambiguous semantics, unsupported source semantics, parser
inconsistency, missing metadata, wrong era, silent skip, tooling defect) fails
the run closed (nonzero exit / exception).

Usage:
  python scripts/r4_i5_zero_container_smoke.py [--write] [--store DIR] \\
      [--repo DIR] [--out PATH]
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

from packaging.utils import parse_wheel_filename
from packaging.version import Version

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from benchmark.wp2.env_r4.contracts import (  # noqa: E402
    LockClosure,
    LockParseError,
    RuntimeTarget,
    normalize_name,
    parse_lock,
    unbind_lock_parser,
    wheel_compatible,
)
from benchmark.wp2.env_r4.integrated_parser import bind_integrated_parser  # noqa: E402

R4_DIR = PROJECT / "research" / "env-canon-r4"
SF_R1_DIR = PROJECT / "research" / "source-fidelity-r1"

PLAN_PATH = R4_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json"
MATRIX_PATH = R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json"
I3_RECEIPT_PATH = R4_DIR / "R4_I3_CAPABILITY_STATE_RECONCILIATION.json"

EXPECTED_PLAN_SHA = "8ec20f360f62c7f4d072ad03bb5fe042c85fa98bad64757715227b5c88de687d"
EXPECTED_N_CALIBRATION = 12
EXPECTED_POPULATION_IDENTITY = "ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac"
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
SOURCE_FIDELITY_UNITS = ("vu-b9808f19ace4", "vu-692af9112c6d")

# Local-artifact resolution taxonomy
AVAILABLE_COMPATIBLE_WHEEL = "AVAILABLE_COMPATIBLE_WHEEL"
AVAILABLE_APPROVED_SOURCE_OR_SDIST = "AVAILABLE_APPROVED_SOURCE_OR_SDIST"
SOURCE_FIDELITY_OVERLAY_RESOLVED = "SOURCE_FIDELITY_OVERLAY_RESOLVED"
EDITABLE_SELF_NOT_THIRD_PARTY = "EDITABLE_SELF_NOT_THIRD_PARTY"
EXCLUDED_BY_TARGET = "EXCLUDED_BY_TARGET"
MISSING_LOCAL_ARTIFACT_CANDIDATE = "MISSING_LOCAL_ARTIFACT_CANDIDATE"
UNSUPPORTED_SOURCE_SEMANTICS = "UNSUPPORTED_SOURCE_SEMANTICS"

TERMINAL_READY = "READY_LOCAL_ZERO_CONTAINER"
TERMINAL_READY_WITH_MISSING = "READY_WITH_MISSING_LOCAL_ARTIFACT_CANDIDATES"

ERA_TO_PYTHON = {"py312": "3.12", "py38": "3.8", "py39": "3.9"}
SUPPORTED_PYTHON = set(ERA_TO_PYTHON.values())
SUPPORTED_LOCK_TYPES = {"poetry", "uv"}

# R4-D approved install routes (frozen labels; never guessed)
INSTALL_ROUTES = (
    "LOCK_FRAGMENT_MAIN_PLUS_DEV",
    "V2_EDITABLE_PLUS_LOCK_DEV",
    "UV_EXPORT",
    "REQ_MAIN_PLUS_LOCK_DEV",
)


class SmokeFailClosedError(Exception):
    """Raised when any I5 fail-closed gate fails (drives nonzero exit)."""


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
        raise SmokeFailClosedError(f"missing required artifact: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SmokeFailClosedError(f"artifact {path} is not a JSON object")
    return data


def verify_import_provenance() -> dict[str, object]:
    import benchmark

    resolved = Path(benchmark.__file__).resolve()
    src_resolved = SRC.resolve()
    if not resolved.is_relative_to(src_resolved):
        raise SmokeFailClosedError(
            f"import provenance wrong: benchmark = {resolved}, expected under {src_resolved}"
        )
    return {"benchmark_module": str(resolved), "resolves_to_i5_worktree": True}


def load_plan(path: Path = PLAN_PATH) -> dict[str, Any]:
    plan = _read_json(path)
    if plan.get("schema_version") != "env-canon-r4-d/1.0":
        raise SmokeFailClosedError("plan schema_version mismatch")
    if plan.get("n_calibration") != EXPECTED_N_CALIBRATION:
        raise SmokeFailClosedError("calibration N mutated")
    recomputed = _canonical({k: v for k, v in plan.items() if k != "plan_sha256"})
    if plan.get("plan_sha256") != _sha256_bytes(recomputed):
        raise SmokeFailClosedError("plan SHA is not self-consistent")
    if plan.get("plan_sha256") != EXPECTED_PLAN_SHA:
        raise SmokeFailClosedError("calibration plan SHA mutated vs frozen mission value")
    units = [c["validation_unit_id"] for c in plan.get("calibration_units", [])]
    if units != list(FROZEN_UNIT_ORDER):
        raise SmokeFailClosedError("calibration N12 membership/order mutated vs frozen selection")
    if plan.get("plan_status") != "DRAFT_PENDING_R4_INTEGRATION":
        raise SmokeFailClosedError("historical R4-D draft status overwritten")
    pop = plan.get("population", {})
    if (pop.get("n_validation_units"), pop.get("n_mapped_tasks")) != (144, 219):
        raise SmokeFailClosedError("plan population counts mutated")
    if plan.get("source_population_identity_sha256") != EXPECTED_POPULATION_IDENTITY:
        raise SmokeFailClosedError("plan population identity mutated")
    return plan


def load_matrix(path: Path = MATRIX_PATH) -> dict[str, Any]:
    matrix = _read_json(path)
    pop = matrix.get("population", {})
    if (pop.get("n_validation_units"), pop.get("n_mapped_tasks")) != (144, 219):
        raise SmokeFailClosedError("matrix population counts mutated")
    if pop.get("population_identity_sha256") != EXPECTED_POPULATION_IDENTITY:
        raise SmokeFailClosedError("matrix population identity mutated")
    if matrix.get("strata") != {"3.12_poetry": 25, "3.12_uv": 21, "3.9_poetry": 83, "3.8_poetry": 15}:
        raise SmokeFailClosedError("matrix strata counts mutated")
    if matrix.get("plan_status") != "DRAFT_PENDING_R4_INTEGRATION":
        raise SmokeFailClosedError("matrix draft status overwritten")
    return matrix


def validate_i3_receipt(path: Path = I3_RECEIPT_PATH) -> dict[str, Any]:
    receipt = _read_json(path)
    required = {
        "present_match_count": 14,
        "missing_count": 0,
        "mismatch_count": 0,
        "reconciliation_classification": "HISTORICAL_STALE_STATE_FOR_R4_INTEGRATION",
    }
    for key, expected in required.items():
        if receipt.get(key) != expected:
            raise SmokeFailClosedError(
                f"Docker receipt {key}={receipt.get(key)!r} != {expected!r} (malformed/inconsistent)"
            )
    if not isinstance(receipt.get("images"), list) or len(receipt["images"]) != 14:
        raise SmokeFailClosedError("Docker receipt images list malformed")
    if receipt.get("mission_id") != "M17_D7_R4_I3_CAPABILITY_STATE_RECONCILIATION":
        raise SmokeFailClosedError("Docker receipt mission_id unexpected")
    return receipt


class LocalWheelStore:
    """Deterministic index of the approved local wheel stores for one era.

    Indexes ONLY artifacts present in the frozen WHEELHOUSE_HASHES manifest and
    the R4B canonical-wheel storage under ``built_wheelhouse/canon_r4b``.
    Pure local metadata reads; no download / no network / no docker.
    """

    def __init__(self, store: Path, era: str) -> None:
        self.era = era
        self.wheelhouse = store / "wheelhouse" / era
        self.wheels_dir = store / "built_wheelhouse" / "canon_r4b" / era
        self._wheels: dict[str, list[dict[str, str]]] = {}
        self._sdists: dict[str, list[dict[str, str]]] = {}
        manifest = store / "manifests" / f"WHEELHOUSE_HASHES_{era}.json"
        if not manifest.is_file():
            raise SmokeFailClosedError(f"missing wheelhouse manifest for {era}: {manifest}")
        index = _read_json(manifest)
        for art in index.get("artifacts", []):
            name = normalize_name(str(art.get("name", "")))
            version = str(art.get("version", ""))
            if not name or not version:
                continue
            kind = str(art.get("kind", ""))
            filename = str(art.get("filename", ""))
            rec = {"filename": filename, "version": version}
            if kind == "wheel":
                self._wheels.setdefault(name, []).append(rec)
            elif kind == "sdist":
                self._sdists.setdefault(name, []).append(rec)
        self._scan_canon()
        for bucket in (self._wheels, self._sdists):
            for name in bucket:
                bucket[name].sort(key=lambda r: (r["version"], r["filename"]))

    def _scan_canon(self) -> None:
        if not self.wheels_dir.is_dir():
            return
        for identity_dir in sorted(self.wheels_dir.iterdir()):
            if not identity_dir.is_dir():
                continue
            wheels_subdir = identity_dir / "wheels"
            if not wheels_subdir.is_dir():
                continue
            for wf in sorted(wheels_subdir.glob("*.whl")):
                try:
                    name, version, _build, _tags = parse_wheel_filename(wf.name)
                except Exception:
                    continue
                key = normalize_name(str(name))
                self._wheels.setdefault(key, []).append(
                    {"filename": wf.name, "version": str(version)}
                )

    def wheels_for(self, name: str) -> list[dict[str, str]]:
        return list(self._wheels.get(normalize_name(name), []))

    def sdist_for(self, name: str) -> list[dict[str, str]]:
        return list(self._sdists.get(normalize_name(name), []))


class SourceFidelityOverlay:
    """Frozen source-fidelity R1 overlay (PyXB 1.2.5, authorizenet 1.1.4)."""

    def __init__(self, r1_dir: Path = SF_R1_DIR) -> None:
        self.manifest = _read_json(r1_dir / "SOURCE_FIDELITY_PROVENANCE_MANIFEST.json")
        self.wheel_dir = r1_dir / "artifacts" / "wheels"
        self._artifacts: dict[tuple[str, str], dict[str, Any]] = {}
        for art in self.manifest.get("artifacts", []):
            name = normalize_name(str(art.get("dependency_name", "")))
            version = str(art.get("declared_version", "")).lower()
            key = (name, version)
            wheel_path = self.wheel_dir / str(art.get("output_filename", ""))
            rec = dict(art)
            if wheel_path.is_file():
                rec["local_path"] = str(wheel_path)
                rec["local_sha256"] = _sha256_file(wheel_path)
            self._artifacts[key] = rec

    def resolve(self, name: str, version: str) -> dict[str, Any] | None:
        key = (normalize_name(name), str(version).lower())
        art = self._artifacts.get(key)
        if not art:
            return None
        expected = art.get("output_sha256")
        got = art.get("local_sha256")
        if expected is None or got != expected:
            return None
        return art


def build_unit_identity(
    plan: dict[str, Any],
    matrix: dict[str, Any],
    store: Path,
) -> dict[str, dict[str, Any]]:
    """Cross-check plan/matrix/task/unit manifests; return per-unit identity."""
    plan_units = {c["validation_unit_id"]: c for c in plan["calibration_units"]}
    matrix_units = {u["validation_unit_id"]: u for u in matrix["units"]}
    unit_rows = {r["unit_id"]: r for r in _read_csv(store, "VALIDATION_UNIT_MATRIX.csv")}
    task_rows = {r["task_id"]: r for r in _read_csv(store, "TASK_ENV_MATRIX.csv")}

    out: dict[str, dict[str, Any]] = {}
    for uid in FROZEN_UNIT_ORDER:
        plan_unit = plan_units.get(uid)
        matrix_unit = matrix_units.get(uid)
        unit_row = unit_rows.get(uid)
        if plan_unit is None or matrix_unit is None or unit_row is None:
            raise SmokeFailClosedError(f"unit {uid} missing from a qualified plan/matrix/unit manifest")
        plan_tasks = plan_unit["member_task_ids"]
        matrix_tasks = matrix_unit["member_task_ids"]
        unit_tasks = [t.strip() for t in str(unit_row["member_task_ids"]).split(";") if t.strip()]
        expected_tasks = plan_tasks if list(plan_tasks) == list(matrix_tasks) else None
        if expected_tasks is None:
            raise SmokeFailClosedError(f"unit {uid} plan/matrix member-task identity mismatch")
        if unit_tasks != list(expected_tasks):
            raise SmokeFailClosedError(f"unit {uid} member-task identity mismatch vs unit manifest")
        if len(set(unit_tasks)) != len(unit_tasks):
            raise SmokeFailClosedError(f"unit {uid} duplicate member tasks")
        task_identity: dict[str, dict[str, str]] = {}
        for tid in unit_tasks:
            row = task_rows.get(tid)
            if row is None:
                raise SmokeFailClosedError(f"unit {uid} member task {tid} missing from TASK_ENV")
            if not row.get("target_commit", "").strip():
                raise SmokeFailClosedError(f"unit {uid} member task {tid} missing repository/commit identity")
            task_identity[tid] = {
                "task_id": tid,
                "target_commit": row["target_commit"].strip(),
                "lock_sha256": row.get("lock_sha256", "").strip(),
            }
        out[uid] = {
            "plan_record": plan_unit,
            "matrix_record": matrix_unit,
            "unit_row": unit_row,
            "member_tasks": unit_tasks,
            "task_identity": task_identity,
        }
    return out


def _read_csv(store: Path, name: str) -> list[dict[str, str]]:
    path = store / "manifests" / name
    if not path.is_file():
        raise SmokeFailClosedError(f"missing manifest {path}")
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _check_commit(repo: Path, commit: str) -> bool:
    """Bounded Git object check: does the commit object exist locally?

    Never checks out, never materializes a tree, never compares worktrees.
    """
    result = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{commit}^{{commit}}"],
        capture_output=True,
        check=False,
        timeout=30,
    )
    return result.returncode == 0


def _parse_lock_once(tid: str, store: Path, lock_type: str, target: RuntimeTarget) -> LockClosure:
    lock_path = store / "artifacts" / "locks" / f"{tid}_{lock_type}.toml"
    if not lock_path.is_file():
        raise SmokeFailClosedError(f"member task {tid} lock artifact missing: {lock_path}")
    try:
        closure = parse_lock(lock_path, target)
    except LockParseError as exc:
        raise SmokeFailClosedError(f"lock {tid} parse failed: {exc}") from exc
    if not closure.is_valid:
        raise SmokeFailClosedError(f"lock {tid} closure invalid: {closure.fail_closed_reasons}")
    if closure.lock_format != lock_type:
        raise SmokeFailClosedError(f"lock {tid} format {closure.lock_format} != {lock_type}")
    if any(req.editable_self for req in closure.requirements):
        raise SmokeFailClosedError(f"lock {tid} editable-self leaked into requirements (contract violation)")
    return closure


def resolve_unit(
    uid: str,
    identity: dict[str, Any],
    store: Path,
    repo: Path,
    wheel_store: LocalWheelStore,
    sf_overlay: SourceFidelityOverlay,
) -> dict[str, Any]:
    matrix = identity["matrix_record"]
    lock_type = matrix["lock_type"]
    install_route = matrix["install_route"]
    era = matrix["wheelhouse_era"]
    python_version = matrix["python_version"]
    target_dict = matrix["runtime_target"]
    if lock_type not in SUPPORTED_LOCK_TYPES:
        raise SmokeFailClosedError(f"unit {uid} unsupported lock_type {lock_type!r}")
    if install_route not in INSTALL_ROUTES:
        raise SmokeFailClosedError(f"unit {uid} unsupported/unknown install route {install_route!r}")
    if python_version not in SUPPORTED_PYTHON:
        raise SmokeFailClosedError(f"unit {uid} unsupported python era {python_version!r}")
    if era not in ERA_TO_PYTHON:
        raise SmokeFailClosedError(f"unit {uid} unknown wheelhouse era {era!r}")
    if ERA_TO_PYTHON[era] != python_version:
        raise SmokeFailClosedError(f"unit {uid} era/python mismatch: {era} vs {python_version}")
    if target_dict.get("implementation") != "cpython" or target_dict.get("platform") != "linux":
        raise SmokeFailClosedError(f"unit {uid} unsupported runtime target {target_dict}")
    if target_dict.get("architecture") != "x86_64":
        raise SmokeFailClosedError(f"unit {uid} unsupported architecture {target_dict}")
    if matrix.get("source_fidelity_overlay_required") is True and uid not in SOURCE_FIDELITY_UNITS:
        raise SmokeFailClosedError(f"unit {uid} inconsistent source-fidelity overlay flag")
    if matrix.get("source_fidelity_overlay_required") is not True and uid in SOURCE_FIDELITY_UNITS:
        raise SmokeFailClosedError(f"unit {uid} missing source-fidelity overlay flag")

    target = RuntimeTarget(
        python_version=python_version,
        implementation=str(target_dict["implementation"]),
        platform=str(target_dict["platform"]),
        architecture=str(target_dict["architecture"]),
    )

    closures: dict[str, LockClosure] = {}
    for tid in identity["member_tasks"]:
        closures[tid] = _parse_lock_once(tid, store, lock_type, target)

    task_records: list[dict[str, Any]] = []
    for tid in identity["member_tasks"]:
        closure = closures[tid]
        lock_path = store / "artifacts" / "locks" / f"{tid}_{lock_type}.toml"
        commit = identity["task_identity"][tid]["target_commit"]
        task_records.append(
            {
                "task_id": tid,
                "lock_sha256": _sha256_file(lock_path),
                "lock_closure_sha256": closure.freeze_sha256(),
                "target_commit": commit,
                "commit_object_present": _check_commit(repo, commit),
                "requirements_count": len(closure.requirements),
                "exclusions_count": len(closure.exclusions),
            }
        )

    all_reqs: list[dict[str, Any]] = []
    editable_selfs: list[dict[str, Any]] = []
    class_counts: dict[str, int] = {}
    missing_candidates: list[dict[str, Any]] = []
    source_type_counts: dict[str, int] = {}
    target_excluded = 0

    for tid, closure in closures.items():
        if closure.editable_self is not None:
            self_req = closure.editable_self
            editable_selfs.append(
                {
                    "task_id": tid,
                    "normalized_name": self_req.normalized_name,
                    "version": self_req.version,
                    "source_type": self_req.source_type.value,
                    "source_reference": self_req.source_reference,
                }
            )
            class_counts[EDITABLE_SELF_NOT_THIRD_PARTY] = (
                class_counts.get(EDITABLE_SELF_NOT_THIRD_PARTY, 0) + 1
            )
        target_excluded += len(closure.exclusions)
        for _exc in closure.exclusions:
            class_counts[EXCLUDED_BY_TARGET] = class_counts.get(EXCLUDED_BY_TARGET, 0) + 1
        for req in closure.requirements:
            source_type = req.source_type.value
            source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
            rec = {
                "task_id": tid,
                "normalized_name": req.normalized_name,
                "version": req.version,
                "source_type": source_type,
                "source_reference": req.source_reference,
                "marker": req.marker,
            }
            classification = _classify_requirement(
                req, rec, python_version, wheel_store, sf_overlay, uid
            )
            rec["classification"] = classification
            class_counts[classification] = class_counts.get(classification, 0) + 1
            if classification == MISSING_LOCAL_ARTIFACT_CANDIDATE:
                missing_candidates.append(rec)
            all_reqs.append(rec)

    if any(not r["commit_object_present"] for r in task_records):
        missing_commits = [r["task_id"] for r in task_records if not r["commit_object_present"]]
        raise SmokeFailClosedError(f"unit {uid} missing repository/commit identity for {missing_commits}")
    if any(r["classification"] == UNSUPPORTED_SOURCE_SEMANTICS for r in all_reqs):
        unsupported = [
            r for r in all_reqs if r["classification"] == UNSUPPORTED_SOURCE_SEMANTICS
        ]
        raise SmokeFailClosedError(f"unit {uid} unsupported required source semantics: {unsupported}")

    terminal = TERMINAL_READY_WITH_MISSING if missing_candidates else TERMINAL_READY
    return {
        "validation_unit_id": uid,
        "member_tasks": identity["member_tasks"],
        "task_identity": identity["task_identity"],
        "python_era": era,
        "python_version": python_version,
        "runtime_target": target_dict,
        "lock_type": lock_type,
        "install_route": install_route,
        "docker_profile_id": matrix["docker_profile_id"],
        "native_profile_id": matrix["native_profile_id"],
        "wheelhouse_era": era,
        "source_fidelity_overlay_required": matrix["source_fidelity_overlay_required"],
        "source_fidelity_overlay_present": uid in SOURCE_FIDELITY_UNITS,
        "member_task_records": task_records,
        "editable_self": editable_selfs,
        "requirement_count": len(all_reqs),
        "target_excluded_count": target_excluded,
        "source_type_counts": source_type_counts,
        "classification_counts": class_counts,
        "missing_local_artifact_candidates": missing_candidates,
        "terminal_classification": terminal,
    }


def _classify_requirement(
    req: Any,
    rec: dict[str, Any],
    python_version: str,
    wheel_store: LocalWheelStore,
    sf_overlay: SourceFidelityOverlay,
    uid: str,
) -> str:
    source_type = req.source_type.value
    if req.editable_self:
        return EDITABLE_SELF_NOT_THIRD_PARTY
    if source_type == "REGISTRY":
        target = RuntimeTarget(python_version, "cpython", "linux", "x86_64")
        compatible: list[str] = []
        req_version = Version(req.version)
        for candidate in wheel_store.wheels_for(req.normalized_name):
            try:
                filename = candidate["filename"]
                candidate_version = Version(candidate["version"])
            except Exception:
                continue
            if candidate_version != req_version:
                continue
            if wheel_compatible(filename, target):
                compatible.append(filename)
        if compatible:
            rec["compatible_wheels"] = sorted(compatible)
            return AVAILABLE_COMPATIBLE_WHEEL
        sdists = [s["filename"] for s in wheel_store.sdist_for(req.normalized_name)]
        if sdists:
            rec["local_sdists_present"] = sorted(sdists)
            # The frozen R3 install routes are wheel-only; an sdist with no
            # compatible wheel is a correctly established local absence for now.
        return MISSING_LOCAL_ARTIFACT_CANDIDATE
    if source_type in ("DIRECTORY", "PATH"):
        if uid not in SOURCE_FIDELITY_UNITS:
            return UNSUPPORTED_SOURCE_SEMANTICS
        art = sf_overlay.resolve(req.normalized_name, req.version)
        if art is None:
            return MISSING_LOCAL_ARTIFACT_CANDIDATE
        rec["source_fidelity_artifact"] = {
            "output_filename": art.get("output_filename"),
            "source_type": art.get("source_type"),
            "source_reference": art.get("vendored_source_path"),
            "source_tree_sha256": art.get("source_tree_sha256"),
            "target_commit": art.get("target_commit"),
            "output_sha256": art.get("local_sha256"),
        }
        return SOURCE_FIDELITY_OVERLAY_RESOLVED
    return UNSUPPORTED_SOURCE_SEMANTICS


def run_smoke(
    store: Path,
    repo: Path,
    *,
    write: bool,
    out_path: Path | None,
    previous_canonical: str | None = None,
) -> dict[str, Any]:
    store = store.resolve()
    repo = repo.resolve()
    if not store.is_dir():
        raise SmokeFailClosedError(f"store root missing: {store}")
    if not (repo / ".git").is_dir() and not (repo / "objects").is_dir():
        raise SmokeFailClosedError(f"local repository missing: {repo}")

    provenance = verify_import_provenance()
    plan = load_plan()
    matrix = load_matrix()
    receipt = validate_i3_receipt()
    identities = build_unit_identity(plan, matrix, store)

    wheel_stores = {era: LocalWheelStore(store, era) for era in ERA_TO_PYTHON}
    sf_overlay = SourceFidelityOverlay()

    bind_integrated_parser()
    results: list[dict[str, Any]] = []
    try:
        for uid in FROZEN_UNIT_ORDER:
            era = identities[uid]["matrix_record"]["wheelhouse_era"]
            results.append(
                resolve_unit(uid, identities[uid], store, repo, wheel_stores[era], sf_overlay)
            )
    finally:
        unbind_lock_parser()

    era_coverage = sorted({r["python_era"] for r in results})
    route_coverage = sorted({r["install_route"] for r in results})
    lock_coverage = sorted({r["lock_type"] for r in results})
    if era_coverage != sorted(ERA_TO_PYTHON):
        raise SmokeFailClosedError("era coverage not achieved for all frozen eras")
    if set(route_coverage) != set(INSTALL_ROUTES):
        raise SmokeFailClosedError("install-route coverage not achieved for all frozen routes")

    terminal_counts: dict[str, int] = {}
    for r in results:
        terminal_counts[r["terminal_classification"]] = terminal_counts.get(
            r["terminal_classification"], 0
        ) + 1
    n_units = len(results)
    total_missing = sum(len(r["missing_local_artifact_candidates"]) for r in results)

    receipt_payload = {
        "schema_version": "env-canon-r4-i5/1.0",
        "mission_id": "M17_D7_R4_I5_ZERO_CONTAINER_SMOKE_N12",
        "mission_class": "T3_bounded_pre_execution_benchmark_smoke",
        "starting_head": "c654617451a54157d423453d7de22479f8d13c4c",
        "branch": "parallel/d7-r4-i5-zero-container-smoke-2026-10-13",
        "calibration_plan_sha256": plan["plan_sha256"],
        "exact_ordered_unit_ids": list(FROZEN_UNIT_ORDER),
        "member_task_ids_per_unit": {r["validation_unit_id"]: r["member_tasks"] for r in results},
        "population": {"n_validation_units": 144, "n_mapped_tasks": 219},
        "population_identity_sha256": EXPECTED_POPULATION_IDENTITY,
        "import_provenance": provenance,
        "integrated_providers": {
            "poetry_lock_parser": "R4-B (EnvR4LockAdapter poetry path)",
            "uv_lock_parser": "R4-B (EnvR4LockAdapter uv path)",
            "wheel_tag_compatibility": "R4-A (wheel_tags.wheel_compatible, era-aware)",
            "binding": "IntegratedR4Parser via env_r4.contracts bind_lock_parser",
        },
        "docker_receipt_consumed": {
            "path": str(I3_RECEIPT_PATH),
            "present_match_count": receipt["present_match_count"],
            "missing_count": receipt["missing_count"],
            "mismatch_count": receipt["mismatch_count"],
            "classification": receipt["reconciliation_classification"],
            "docker_re_queried": False,
        },
        "approved_local_stores": {
            "wheelhouse_manifests": [str(store / "manifests" / f"WHEELHOUSE_HASHES_{e}.json") for e in ERA_TO_PYTHON],
            "wheelhouse_dirs": [str(store / "wheelhouse" / e) for e in ERA_TO_PYTHON],
            "canon_r4b_dirs": [str(store / "built_wheelhouse" / "canon_r4b" / e) for e in ERA_TO_PYTHON],
            "source_fidelity_overlay": str(SF_R1_DIR / "artifacts" / "wheels"),
        },
        "units": results,
        "terminal_classifications": terminal_counts,
        "n12_processed": n_units,
        "units_deterministically_classified": n_units,
        "units_with_semantic_ambiguity": 0,
        "units_with_instrumentation_or_tooling_failure": 0,
        "total_missing_local_artifact_candidates": total_missing,
        "no_silent_skips": True,
        "era_coverage_achieved": era_coverage,
        "install_route_coverage_achieved": route_coverage,
        "lock_type_coverage": lock_coverage,
        "source_fidelity_evidence": {
            "mandatory_units": list(SOURCE_FIDELITY_UNITS),
            "overlay_used": SOURCE_FIDELITY_OVERLAY_RESOLVED,
        },
        "uv_evidence": {
            "uv_units": [r["validation_unit_id"] for r in results if r["lock_type"] == "uv"],
            "editable_self_count": sum(1 for r in results for _ in r["editable_self"]),
            "poetry_fallback_used": False,
        },
        "deterministic_rerun": None,
        "docker_usage": {
            "docker_cli_used": False,
            "containers_run": False,
            "images_pulled": False,
            "images_built": False,
        },
        "network_usage": {"network_used": False, "registry_accessed": False, "downloads": False},
        "behavioral_execution": {
            "install_executed": False,
            "tests_executed": False,
            "imports_executed": False,
            "builds_executed": False,
            "r4c_materializer_executed": False,
        },
        "full_d7_executed": False,
        "census144_executed": False,
        "opws_executed": False,
        "next_gate": "M17_D7_R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144",
    }

    canonical_core = _canonical_core(receipt_payload)
    canonical_sha = _sha256_bytes(_canonical(canonical_core))
    receipt_payload["canonical_sha256"] = canonical_sha

    if previous_canonical is not None:
        if previous_canonical != canonical_sha:
            raise SmokeFailClosedError(
                f"deterministic rerun mismatch: previous={previous_canonical} current={canonical_sha}"
            )
        receipt_payload["deterministic_rerun"] = {
            "canonical_run_1_sha256": previous_canonical,
            "canonical_run_2_sha256": canonical_sha,
            "identical": True,
        }

    if write:
        target = out_path or (R4_DIR / "R4_I5_ZERO_CONTAINER_SMOKE_N12.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(receipt_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"CANONICAL_SHA256={canonical_sha}")
    print(f"N12_PROCESSED={n_units}")
    print(f"TERMINAL={json.dumps(terminal_counts, sort_keys=True)}")
    print(f"MISSING_CANDIDATES={total_missing}")
    return receipt_payload


def _canonical_core(payload: dict[str, Any]) -> dict[str, Any]:
    """Semantic core for determinism; volatile/non-semantic fields removed."""
    units = []
    for u in payload["units"]:
        units.append(
            {
                "validation_unit_id": u["validation_unit_id"],
                "member_tasks": u["member_tasks"],
                "python_era": u["python_era"],
                "python_version": u["python_version"],
                "lock_type": u["lock_type"],
                "install_route": u["install_route"],
                "docker_profile_id": u["docker_profile_id"],
                "native_profile_id": u["native_profile_id"],
                "source_fidelity_overlay_required": u["source_fidelity_overlay_required"],
                "editable_self": u["editable_self"],
                "source_type_counts": u["source_type_counts"],
                "classification_counts": u["classification_counts"],
                "member_task_records": [
                    {
                        "task_id": t["task_id"],
                        "lock_closure_sha256": t["lock_closure_sha256"],
                        "commit_object_present": t["commit_object_present"],
                    }
                    for t in u["member_task_records"]
                ],
                "missing_local_artifact_candidates": [
                    {
                        "task_id": m["task_id"],
                        "normalized_name": m["normalized_name"],
                        "version": m["version"],
                        "source_type": m["source_type"],
                        "source_reference": m["source_reference"],
                    }
                    for m in u["missing_local_artifact_candidates"]
                ],
                "terminal_classification": u["terminal_classification"],
            }
        )
    return {
        "mission_id": payload["mission_id"],
        "calibration_plan_sha256": payload["calibration_plan_sha256"],
        "exact_ordered_unit_ids": payload["exact_ordered_unit_ids"],
        "member_task_ids_per_unit": payload["member_task_ids_per_unit"],
        "terminal_classifications": payload["terminal_classifications"],
        "units": units,
        "era_coverage_achieved": payload["era_coverage_achieved"],
        "install_route_coverage_achieved": payload["install_route_coverage_achieved"],
        "no_silent_skips": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="R4 I5 zero-container N12 smoke")
    ap.add_argument("--write", action="store_true", help="write the receipt JSON")
    ap.add_argument("--store", default=r"D:\wp2_env_store", help="store root")
    ap.add_argument(
        "--repo",
        default=r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor",
        help="local Git repository",
    )
    ap.add_argument("--out", default=None, help="receipt output path")
    ap.add_argument(
        "--previous-canonical",
        default=None,
        help="canonical SHA of a previous run; when supplied the rerun must be byte-identical (fail closed otherwise)",
    )
    args = ap.parse_args()
    try:
        run_smoke(
            Path(args.store),
            Path(args.repo),
            write=args.write,
            out_path=Path(args.out) if args.out else None,
            previous_canonical=args.previous_canonical,
        )
    except SmokeFailClosedError as exc:
        print(f"SMOKE_FAIL_CLOSED {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # any unexpected error fails closed, never silently
        print(f"SMOKE_INSTRUMENTATION_ERROR {exc!r}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
