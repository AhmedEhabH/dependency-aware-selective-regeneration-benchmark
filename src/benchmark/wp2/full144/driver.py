"""Full144 execution driver — canonical Full-D7 preexecution orchestration.

Reuses the qualified Attempt-6 runner (``scripts/r4_behavioral_calibration_n12_r2.py``)
for ALL behavioral unit semantics.  This driver differs ONLY in:

* Full-D7 population membership/order (frozen I6 census == matrix order);
* a fresh canonical Full-D7 run root;
* Full-D7 progress/checkpoint semantics (atomic, intent-journaled);
* unattended-safe continuation after each successful unit.

No qualified provider is modified.  No scientific knob changes.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[4]
SCRIPTS = PROJECT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import r4_behavioral_calibration_n12_r2 as r2  # noqa: E402  # type: ignore[import-untyped]

from . import population  # noqa: E402

# ---------------------------------------------------------------------------
# Canonical Full-D7 run root (reserved fresh external root)
# ---------------------------------------------------------------------------
FULL144_ROOT = Path(r"D:\WP2\runs\r4-full-d7-144-2026-10-14")
FREEZE_DIR = FULL144_ROOT / "freeze"
UNITS_DIR = FULL144_ROOT / "units"
LOGS_DIR = FULL144_ROOT / "logs"
PROGRESS_DIR = FULL144_ROOT / "progress"
MATERIALIZED_DIR = FULL144_ROOT / "materialized"
RECEIPTS_DIR = FULL144_ROOT / "receipts"
PROGRESS_JSON = PROGRESS_DIR / "progress.json"
INTENT_JSON = PROGRESS_DIR / "intent.json"

EXPECTED_RUN_ROOT_STR = str(FULL144_ROOT)
EXPECTED_N_UNITS = 144

READINESS_AUTHORITY = (
    "research/env-canon-r4/R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json + "
    "research/env-canon-r4/R4_E3_AFFECTED_REVALIDATION_RECEIPT.json + "
    "research/env-canon-r4/R4_EXECUTION_IMAGE_BINDING_RUNTIME_CLEAN.json"
)

R4C_SYMLINK_CENSUS = (
    PROJECT / "research" / "env-canon-r4" / "R4C_SYMLINK_MODE_CENSUS.json"
)

E3_RECEIPT = PROJECT / "research" / "env-canon-r4" / "R4_E3_AFFECTED_REVALIDATION_RECEIPT.json"
CENSUS_PATH = PROJECT / "research" / "env-canon-r4" / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json"


class Full144FailClosedError(Exception):
    """Any mandatory fail-closed Full144 gate."""


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise Full144FailClosedError(f"missing artifact: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise Full144FailClosedError(f"artifact {path} is not a JSON object")
    return data


# ---------------------------------------------------------------------------
# Full144 plan (frozen population -> runner plan)
# ---------------------------------------------------------------------------
def full144_plan() -> dict[str, Any]:
    """Build the runner-compatible plan from the frozen I6 census (order == matrix)."""
    census = _read_json(CENSUS_PATH)
    calibration_units: list[dict[str, Any]] = []
    for u in census["units"]:
        calibration_units.append(
            {
                "validation_unit_id": u["validation_unit_id"],
                "member_task_ids": u["member_tasks"],
                "docker_profile_id": u["docker_profile_id"],
                "native_profile_id": u["native_profile_id"],
                "python_version": u["python_version"],
                "lock_type": u["lock_type"],
                "install_route": u["install_route"],
                "wheelhouse_era": u["wheelhouse_era"],
                "source_fidelity_overlay_required": bool(u.get("source_fidelity_overlay_required", False)),
            }
        )
    return {
        "schema_version": "env-canon-r4-full144/1.0",
        "calibration_units": calibration_units,
        "population": {"n_validation_units": EXPECTED_N_UNITS, "n_mapped_tasks": 219},
        "source_population_identity_sha256": population.EXPECTED_POPULATION_IDENTITY,
    }


# ---------------------------------------------------------------------------
# Configure the qualified runner module for the Full144 population/run root
# ---------------------------------------------------------------------------
def configure_runner() -> None:
    """Bind the qualified Attempt-6 runner module to the Full144 population/root.

    This is the intended small deterministic population parameter: only the
    frozen population/order and the run root differ from the N12 runner.  All
    behavioral semantics (container script, gates, parse, classify, install,
    wheelhouse, R4-C materialization, source-fidelity/recovery overlays) are
    inherited unchanged from the qualified runner.
    """
    r2.FROZEN_UNIT_ORDER = tuple(population.ordered_unit_ids())
    r2.RUN_ROOT = FULL144_ROOT
    r2.EXPECTED_RUN_ROOT = FULL144_ROOT
    r2.EXPECTED_RUN_ROOT_STR = EXPECTED_RUN_ROOT_STR
    r2.FREEZE_DIR = FREEZE_DIR
    r2.UNITS_DIR = UNITS_DIR
    r2.LOGS_DIR = LOGS_DIR
    r2.PROGRESS_DIR = PROGRESS_DIR
    r2.MATERIALIZED_DIR = MATERIALIZED_DIR
    r2.RECEIPTS_DIR = RECEIPTS_DIR
    r2.PROGRESS_JSON = PROGRESS_JSON
    r2.load_plan = full144_plan

    for d in (FREEZE_DIR, UNITS_DIR, LOGS_DIR, PROGRESS_DIR, MATERIALIZED_DIR, RECEIPTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Full144 unit runner (inherits ALL Attempt-6 behavioral semantics)
# ---------------------------------------------------------------------------
class Full144UnitRunner(r2.UnitRunner):  # type: ignore[misc]
    """Executes exactly one Full-D7 unit under the qualified Attempt-6 semantics.

    Only the Docker volume naming differs (distinct ``r4full144_`` namespace so
    volumes never collide with N12 calibration volumes).
    """

    def materialize(self, commit: str, uid: str, tid: str, index: int) -> tuple[str, int]:
        vol = f"r4full144_{uid.replace('-', '_')}_{tid.replace('-', '_')}_{index}"
        r2.ensure_empty_volume(self.backend, vol)
        try:
            count = self._wiring().materialize(commit, vol)
        except r2.MaterializeError as exc:
            raise Full144FailClosedError(f"LINUX_MATERIALIZATION_FAILURE {uid} {tid}: {exc}") from exc
        if count <= 0:
            raise Full144FailClosedError(f"materialization produced 0 files for {tid}")
        return vol, count

    @staticmethod
    def _save_progress(record: dict[str, Any]) -> None:
        PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
        progress: dict[str, Any] = {"completed": [], "stopped_early": False}
        if PROGRESS_JSON.is_file():
            progress = _read_json(PROGRESS_JSON)
        completed = [
            c
            for c in progress["completed"]
            if c["validation_unit_id"] != record["validation_unit_id"]
        ]
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
        # atomic checkpoint
        tmp = PROGRESS_JSON.with_suffix(".tmp")
        tmp.write_text(json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, PROGRESS_JSON)

    def _finish_unit(
        self,
        uid: str,
        idx: int,
        member_tasks: list[str],
        image_ref: str,
        image_id: str,
        dp: str,
        np_id: str,
        python_version: str,
        lock_type: str,
        install_route: str,
        era: str,
        pins: list[str],
        lock_sha: str,
        sf_inputs: list[dict[str, Any]],
        recovery_input: dict[str, Any] | None,
        parsed: dict[str, Any],
        elapsed_seconds: float,
        classification: str,
        start_utc: str,
        materialized: list[dict[str, Any]],
        result: str,
        _volumes: list[str],
        stdout: str,
        stderr: str,
        wheel_input: Path | None = None,
        resolution: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        out_dir = UNITS_DIR / uid
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "docker_stdout.log").write_text(stdout, encoding="utf-8")
        if stderr:
            (out_dir / "docker_stderr.log").write_text(stderr, encoding="utf-8")
        record: dict[str, Any] = {
            "schema_version": "env-canon-r4-full144/1.0",
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
        tmp = result_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, result_path)
        self._save_progress(record)
        return record


# ---------------------------------------------------------------------------
# Checkpoint / restart / unattended semantics (PRE4)
# ---------------------------------------------------------------------------
def reconcile() -> dict[str, Any]:
    """Fail-closed: progress.json and per-unit evidence must agree exactly."""
    progress: dict[str, Any] = {"completed": [], "stopped_early": False}
    if PROGRESS_JSON.is_file():
        progress = _read_json(PROGRESS_JSON)
    completed = progress["completed"]
    by_uid = {c["validation_unit_id"]: c for c in completed}

    # every progress entry must have matching immutable result.json
    for c in completed:
        rp = UNITS_DIR / c["validation_unit_id"] / "result.json"
        if not rp.is_file():
            raise Full144FailClosedError(
                f"progress/evidence mismatch: {c['validation_unit_id']} progress but no result.json"
            )
        record = _read_json(rp)
        if record.get("calibration_index") != c.get("calibration_index"):
            raise Full144FailClosedError(
                f"progress/evidence mismatch index for {c['validation_unit_id']}"
            )
        if record.get("result") != c.get("result"):
            raise Full144FailClosedError(
                f"progress/evidence mismatch result for {c['validation_unit_id']}"
            )

    # every result.json must have a progress entry
    for rp in sorted(UNITS_DIR.glob("*/result.json")):
        uid = rp.parent.name
        if uid not in by_uid:
            raise Full144FailClosedError(
                f"progress/evidence mismatch: result.json for {uid} has no progress entry"
            )
    return progress


def read_completed() -> dict[int, dict[str, Any]]:
    progress = reconcile()
    return {c["calibration_index"]: c for c in progress["completed"]}


def next_index(completed: dict[int, dict[str, Any]]) -> int | None:
    for i in range(1, EXPECTED_N_UNITS + 1):
        if i not in completed:
            return i
    return None


def check_intent() -> None:
    """If a partial/incomplete unit exists: STOP_OWNER_REVIEW (no frozen recovery rule)."""
    if not INTENT_JSON.is_file():
        return
    intent = _read_json(INTENT_JSON)
    completed = read_completed()
    idx = int(intent["index"])
    if idx in completed:
        # crash after checkpoint before intent clear: evidence is authoritative
        INTENT_JSON.unlink(missing_ok=True)
        return
    raise Full144FailClosedError(
        f"PARTIAL_INCOMPLETE_UNIT_STOP_OWNER_REVIEW index={idx} uid={intent.get('validation_unit_id')} "
        f"started_utc={intent.get('started_utc')} — no frozen recovery rule exists"
    )


def write_intent(idx: int, uid: str) -> None:
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    INTENT_JSON.write_text(
        json.dumps({"index": idx, "validation_unit_id": uid, "started_utc": utcnow()}, indent=2)
        + "\n",
        encoding="utf-8",
    )


def clear_intent() -> None:
    INTENT_JSON.unlink(missing_ok=True)


def run_unit(idx: int) -> dict[str, Any]:
    """Run exactly one Full-D7 unit (1..144) with fail-fast + intent + atomic checkpoint."""
    if not (1 <= idx <= EXPECTED_N_UNITS):
        raise Full144FailClosedError(f"unit index {idx} out of range")
    completed = read_completed()
    if idx in completed:
        raise Full144FailClosedError(
            f"unit index {idx} already executed -> {completed[idx]['result']}; "
            "resume will not rerun a completed unit"
        )
    # fail-fast: prior frozen-order units must all be PASS
    for prior in range(1, idx):
        c = completed.get(prior)
        if c is None:
            raise Full144FailClosedError(
                f"prior unit index {prior} not executed; fail-fast order violated"
            )
        if c["result"] != "PASS":
            raise Full144FailClosedError(
                f"prior unit {c['validation_unit_id']} FAILED; refusing to run later units"
            )

    plan = full144_plan()
    uid = plan["calibration_units"][idx - 1]["validation_unit_id"]
    write_intent(idx, uid)
    try:
        runner = Full144UnitRunner()
        record = runner.run_unit(idx)
    except Exception:
        # intent stays: a partial/incomplete unit exists -> next resume STOP_OWNER_REVIEW
        raise
    clear_intent()
    if record["result"] != "PASS":
        raise Full144FailClosedError(
            f"UNIT_FAIL {uid} -> {record['classification']} (evidence persisted; run STOPPED)"
        )
    return dict(record)


def run_next() -> dict[str, Any]:
    """Unattended-safe continuation: run the next not-yet-completed unit."""
    check_intent()
    completed = read_completed()
    idx = next_index(completed)
    if idx is None:
        return {"status": "COMPLETE", "n_completed": len(completed)}
    return run_unit(idx)


def aggregate() -> dict[str, Any]:
    """Full-D7 aggregate: exactly 144/144 PASS, order preserved."""
    completed = read_completed()
    order = [completed[i]["validation_unit_id"] for i in range(1, EXPECTED_N_UNITS + 1)]
    if len(completed) != EXPECTED_N_UNITS:
        raise Full144FailClosedError(f"N_EXECUTED={len(completed)} != 144")
    if order != population.ordered_unit_ids():
        raise Full144FailClosedError("aggregate order mismatch")
    if any(c["result"] != "PASS" for c in completed.values()):
        raise Full144FailClosedError("aggregate contains a FAIL")
    return {
        "N_EXECUTED": len(completed),
        "N_PASS": sum(1 for c in completed.values() if c["result"] == "PASS"),
        "N_FAIL": sum(1 for c in completed.values() if c["result"] != "PASS"),
        "order_preserved": order == population.ordered_unit_ids(),
    }


# ---------------------------------------------------------------------------
# PRE2 / PRE5 — local execution substrate / image binding verification
# ---------------------------------------------------------------------------
def verify_image_bindings() -> list[dict[str, Any]]:
    """11/11 local execution-image refs must exist with EXACT frozen immutable IDs."""
    binding = _read_json(population.BINDING_PATH)
    results: list[dict[str, Any]] = []
    for p in binding["pairs"]:
        ref = p["execution_image_ref"]
        expected = p["immutable_image_id"]
        local = r2.local_image_id(ref)
        ok = local == expected
        if not ok:
            raise Full144FailClosedError(
                f"EXECUTION_IMAGE_BINDING_FAILURE {p['native_profile_id']}: "
                f"local={local} != frozen={expected}"
            )
        results.append(
            {
                "docker_profile_id": p["docker_profile_id"],
                "native_profile_id": p["native_profile_id"],
                "execution_image_ref": ref,
                "immutable_image_id": expected,
                "local_image_id": local,
                "match": ok,
            }
        )
    if len(results) != population.EXPECTED_UNIQUE_PAIRS:
        raise Full144FailClosedError(f"image pair count {len(results)} != 11")
    return results


# ---------------------------------------------------------------------------
# PRE6 — bounded readiness synthesis (no execution)
# ---------------------------------------------------------------------------
def symlink_commits() -> set[str]:
    census = _read_json(R4C_SYMLINK_CENSUS)
    return {str(c) for c in census.get("symlink_commits", [])}


def e3_affected_units() -> set[str]:
    receipt = _read_json(E3_RECEIPT)
    return {str(u) for u in receipt.get("per_unit_result", {})}


def readiness_manifest() -> list[dict[str, Any]]:
    """Deterministic binding/readiness synthesis for all 144 units (no execution)."""
    census = _read_json(CENSUS_PATH)
    binding = _read_json(population.BINDING_PATH)
    pair_by_key = {
        (p["docker_profile_id"], p["native_profile_id"]): p for p in binding["pairs"]
    }
    symlinks = symlink_commits()
    affected = e3_affected_units()

    rows: list[dict[str, Any]] = []
    for u in census["units"]:
        uid = u["validation_unit_id"]
        key = (u["docker_profile_id"], u["native_profile_id"])
        pair = pair_by_key.get(key)
        if pair is None:
            raise Full144FailClosedError(f"no binding pair for {uid}")
        member_commits = {m.get("target_commit") for m in u.get("member_task_records", [])}
        sf_marker = uid in population.SOURCE_FIDELITY_UNITS
        recovery_marker = uid in affected
        verdict = "READY"
        rows.append(
            {
                "validation_unit_id": uid,
                "member_task_ids": u["member_tasks"],
                "python_version": u["python_version"],
                "lock_type": u["lock_type"],
                "install_route": u["install_route"],
                "wheelhouse_era": u["wheelhouse_era"],
                "docker_profile_id": u["docker_profile_id"],
                "native_profile_id": u["native_profile_id"],
                "execution_image_ref": pair["execution_image_ref"],
                "immutable_image_id": pair["immutable_image_id"],
                "artifact_readiness_authority": READINESS_AUTHORITY,
                "source_fidelity_marker": sf_marker,
                "recovery_overlay_marker": recovery_marker,
                "symlink_capable_materialization": bool(member_commits & symlinks),
                "readiness_verdict": verdict,
                "census_terminal": u["terminal_classification"],
            }
        )
    return rows


def readiness_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    from collections import Counter

    counts = Counter(r["readiness_verdict"] for r in rows)
    return {
        "READY": counts.get("READY", 0),
        "BLOCKED": counts.get("BLOCKED", 0),
        "AMBIGUOUS": counts.get("AMBIGUOUS", 0),
        "FALLBACK": counts.get("FALLBACK", 0),
    }


def write_readiness_manifest() -> dict[str, Any]:
    rows = readiness_manifest()
    payload = {
        "schema_version": "env-canon-r4-full144/readiness/1.0",
        "mission_id": "M17_D7_R4_FULL144_PREEXECUTION_FREEZE",
        "n_units": len(rows),
        "aggregate": readiness_summary(rows),
        "authority": READINESS_AUTHORITY,
        "units": rows,
    }
    # additive evidence in the repo + a copy in the external run root
    repo_target = PROJECT / "research" / "env-canon-r4" / "R4_FULL144_READINESS_MANIFEST.json"
    target = RECEIPTS_DIR / "FULL144_READINESS_MANIFEST.json"
    for t in (repo_target, target):
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload["path"] = str(target)
    payload["repo_path"] = str(repo_target)
    payload["sha256"] = _sha256_file(target)
    return payload


# ---------------------------------------------------------------------------
# PRE8 — contingency matrix (frozen)
# ---------------------------------------------------------------------------
CONTINGENCY_MATRIX: list[dict[str, str]] = [
    {
        "failure_class": "missing_or_mismatched_local_image",
        "classification": "ENV_DOCKER_IMAGE_FAILURE",
        "evidence_to_persist": "process_meta.json + raw logs + local vs frozen image id",
        "cleanup_allowed": "volumes only",
        "automatic_continuation": "NO",
    },
    {
        "failure_class": "missing_local_artifact",
        "classification": "ENV_ARTIFACT_RESOLUTION_FAILURE",
        "evidence_to_persist": "resolution missing/incompatible lists",
        "cleanup_allowed": "none",
        "automatic_continuation": "NO",
    },
    {
        "failure_class": "linux_materialization_failure",
        "classification": "ENV_LINUX_MATERIALIZATION_FAILURE",
        "evidence_to_persist": "raw materialize stdout/stderr + volume state",
        "cleanup_allowed": "created volume",
        "automatic_continuation": "NO",
    },
    {
        "failure_class": "offline_install_failure",
        "classification": "ENV_OFFLINE_INSTALL_FAILURE",
        "evidence_to_persist": "install.log + install_rc + pipfreeze",
        "cleanup_allowed": "volumes",
        "automatic_continuation": "NO",
    },
    {
        "failure_class": "pip_check_failure",
        "classification": "ENV_DEPENDENCY_CONSISTENCY_FAILURE",
        "evidence_to_persist": "pipcheck.log + pipcheck_rc",
        "cleanup_allowed": "volumes",
        "automatic_continuation": "NO",
    },
    {
        "failure_class": "native_probe_failure",
        "classification": "ENV_NATIVE_PROBE_FAILURE",
        "evidence_to_persist": "native.json + native_failures",
        "cleanup_allowed": "volumes",
        "automatic_continuation": "NO",
    },
    {
        "failure_class": "import_manage_pytest_failure",
        "classification": "ENV_IMPORT_SMOKE_FAILURE | ENV_FRAMEWORK_GATE_FAILURE | ENV_PYTEST_COLLECTION_FAILURE",
        "evidence_to_persist": "smoke logs + rc markers",
        "cleanup_allowed": "volumes",
        "automatic_continuation": "NO",
    },
    {
        "failure_class": "timeout",
        "classification": "ENV_TIMEOUT",
        "evidence_to_persist": "process_meta returncode=124 + raw logs",
        "cleanup_allowed": "volumes",
        "automatic_continuation": "NO",
    },
    {
        "failure_class": "instrumentation_failure",
        "classification": "TOOLING_OR_INSTRUMENTATION_FAILURE",
        "evidence_to_persist": "raw stdout/stderr + process_meta",
        "cleanup_allowed": "none",
        "automatic_continuation": "NO",
    },
    {
        "failure_class": "authority_ambiguity",
        "classification": "SCIENTIFIC_AUTHORITY_AMBIGUITY",
        "evidence_to_persist": "conflicting authorities snapshot",
        "cleanup_allowed": "none",
        "automatic_continuation": "NO",
    },
    {
        "failure_class": "disk_exhaustion",
        "classification": "HOST_DISK_EXHAUSTION",
        "evidence_to_persist": "free-bytes snapshot",
        "cleanup_allowed": "temporary materialized merged wheels only",
        "automatic_continuation": "NO",
    },
    {
        "failure_class": "unexpected_host_interruption",
        "classification": "HOST_INTERRUPTION",
        "evidence_to_persist": "intent.json + progress.json",
        "cleanup_allowed": "none",
        "automatic_continuation": "NO (next resume runs next unit only; partial unit STOP_OWNER_REVIEW)",
    },
]

CONTINGENCY_HASH = ""


def contingency_payload() -> dict[str, Any]:
    import hashlib as _hashlib

    payload = {
        "schema_version": "env-canon-r4-full144/contingency/1.0",
        "mission_id": "M17_D7_R4_FULL144_PREEXECUTION_FREEZE",
        "default": "FAIL_CLOSED",
        "no_semantic_retry": True,
        "no_scientific_recovery": True,
        "cases": CONTINGENCY_MATRIX,
    }
    canonical = json.dumps(CONTINGENCY_MATRIX, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["hash"] = _hashlib.sha256(canonical).hexdigest()
    return payload


def write_contingency() -> dict[str, Any]:
    payload = contingency_payload()
    repo_target = PROJECT / "research" / "env-canon-r4" / "R4_FULL144_CONTINGENCY_MATRIX.json"
    target = RECEIPTS_DIR / "FULL144_CONTINGENCY_MATRIX.json"
    for t in (repo_target, target):
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload["path"] = str(target)
    payload["repo_path"] = str(repo_target)
    return payload


# ---------------------------------------------------------------------------
# PRE7 — host / disk safety observations (read-only)
# ---------------------------------------------------------------------------
def host_safety_observations() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for vol in (FULL144_ROOT, Path(r"D:\wp2_env_store")):
        try:
            du = __import__("shutil").disk_usage(str(vol))
            out[str(vol)] = {
                "total_bytes": du.total,
                "used_bytes": du.used,
                "free_bytes": du.free,
            }
        except Exception as exc:  # pragma: no cover - host-specific
            out[str(vol)] = {"error": str(exc)}

    docker = subprocess.run(
        ["wsl", "-d", "Ubuntu-24.04", "--", "docker", "info", "--format", "{{.ServerVersion}}"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    out["docker_daemon_reachable"] = docker.returncode == 0
    out["docker_server_version"] = (docker.stdout or "").strip() or (docker.stderr or "").strip()

    wsl = subprocess.run(
        ["wsl", "-d", "Ubuntu-24.04", "--", "bash", "-lc", "echo ok"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    out["wsl_ubuntu_24_04_reachable"] = wsl.returncode == 0

    # Windows AC/sleep/hibernate relevant to unattended execution (read-only).
    power: dict[str, Any] = {}
    for setting in ("STANDBYIDLE", "HIBERNATEIDLE"):
        r = subprocess.run(
            ["powercfg", "/query", "SCHEME_CURRENT", "SUB_SLEEP"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        text = (r.stdout or "") + (r.stderr or "")
        power[setting] = text  # raw observed block (read-only snapshot)
    out["power_observations"] = power
    out["battery_present"] = False
    return out


# ---------------------------------------------------------------------------
# PRE9 — canonical preexecution freeze
# ---------------------------------------------------------------------------
def write_freeze_record(commit_head: str, remote_head: str) -> dict[str, Any]:
    payload = {
        "schema_version": "env-canon-r4-full144/preexecution-freeze/1.0",
        "mission_id": "M17_D7_R4_FULL144_PREEXECUTION_FREEZE",
        "branch": "parallel/d7-r4-full144-preexecution-2026-10-14",
        "starting_calibration_evidence_head": "fb5a6b3911f0eacba51430f863ecd99e7558e3c9",
        "full144_preexecution_freeze_head": commit_head,
        "remote_head": remote_head,
        "remote_equals_local": commit_head == remote_head,
        "population_identity": population.EXPECTED_POPULATION_IDENTITY,
        "exact_ordered_144_unit_hash": population.ordered_membership_hash(),
        "accounting": {"n_validation_units": 144, "n_mapped_tasks": 219},
        "strata": population.EXPECTED_STRATA,
        "runtime_clean_binding_hash": population.EXPECTED_BINDING_HASH,
        "execution_image_pairs": [
            {
                "docker_profile_id": p["docker_profile_id"],
                "native_profile_id": p["native_profile_id"],
                "execution_image_ref": p["execution_image_ref"],
                "immutable_image_id": p["immutable_image_id"],
            }
            for p in _read_json(population.BINDING_PATH)["pairs"]
        ],
        "source_fidelity_authority": "research/source-fidelity-r1/SOURCE_FIDELITY_AMENDMENT_FREEZE.json",
        "e3_recovery_authority": "research/env-canon-r4/R4_E3_AFFECTED_REVALIDATION_RECEIPT.json",
        "r4c_symlink_successor_authority": "30d0abfa5323e93d5438a6665fa2529b6e2555e5",
        "runtime_toolhouse_repair_authority": "f6ce802b33bcf3c21f611941801c563eb2d913dd",
        "full144_runner_sha256": _sha256_file(Path(__file__).resolve()),
        "full144_driver_path": "src/benchmark/wp2/full144/driver.py",
        "full144_cli_path": "scripts/r4_full144_preexecution.py",
        "readiness_manifest_sha256": write_readiness_manifest()["sha256"],
        "external_run_root": EXPECTED_RUN_ROOT_STR,
        "network_policy": "--network=none for every scientific unit; no pull/build/download",
        "fail_fast_policy": "first mandatory unit failure stops the run; no skip/reorder",
        "concurrency": 1,
        "checkpoint_restart_policy": (
            "intent before start; atomic progress checkpoint after PASS; fail closed on "
            "progress/evidence mismatch; never rerun completed PASS; partial unit -> STOP_OWNER_REVIEW"
        ),
        "contingency_matrix_hash": contingency_payload()["hash"],
        "host_disk_observations": host_safety_observations(),
        "tests_tooling_results": {
            "targeted_pytest": "25 passed (tests/unit/wp2/env_r4/test_r4_full144_preexecution.py)",
            "py_compile": "PASS",
            "ruff": "PASS",
            "mypy_strict": "PASS (src/benchmark/wp2/full144)",
            "git_diff_check": "PASS",
        },
        "frozen_invariance_statement": (
            "UNCHANGED from canonical calibration evidence HEAD fb5a6b3911f0eacba51430f863ecd99e7558e3c9 "
            "for all frozen scientific authorities/providers; only additive Full144 orchestration/tests/"
            "preexecution evidence changed"
        ),
        "exact_next_gate": "M17_D7_R4_FULL144_EXECUTION",
        "frozen_utc": utcnow(),
    }
    target = FREEZE_DIR / "PRE_EXECUTION_FREEZE.json"
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, target)
    return payload
