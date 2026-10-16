#!/usr/bin/env python3
"""M17_D7_R4_POPULATION_QUALIFICATION_144_HARNESS — deterministic qualification wrapper.

Population-qualification harness for all 144 frozen Full-D7 units (Phase4 repair
execution-code freeze).  It EXERCISES the exact frozen per-unit Phase4 execution
path (``driver.Full144UnitRunner`` -> qualified Attempt-6 runner) while adding
sweep-level orchestration that the frozen scientific driver deliberately does
NOT provide: continue-on-unit-failure, resumability, and fail-closed global
integrity guards.

Hard rules:
  * NO modification of frozen execution code (driver / population / runner /
    route_closure).  They are invoked read-only.
  * NO scientific classification invented.  Per-unit outcomes are ONLY:
    PASS / UNIT_GATE_FAILURE / UNIT_HARNESS_FAILURE.
  * Global integrity failures fail closed immediately (git/code-set drift,
    population/order drift, artifact closure drift, image binding drift, Docker
    unavailable, source repo unavailable, unsafe low disk, checkpoint
    corruption).  Per-unit failures NEVER stop the sweep when global integrity
    holds.
  * Zero network: every container runs with ``--network=none``; no pull/build/
    download/acquire anywhere in the harness.
  * Qualification root is explicitly NON-SCIENTIFIC (separate from the frozen
    scientific run roots).

Subcommands:
  --preflight  run every global gate (git, code-set, population/order, artifact
               closure, image bindings, docker, source repo, disk) and list the
               frozen 144-unit order.  NEVER executes a unit.
  --static     static checks: --network=none present; no pull/build literals;
               no LLM/OpenCode dependency.
  --list       print the deterministic frozen 144-unit order (one uid per line).
  --run        run the deterministic qualification sweep (resumable).  This is
               the ONLY command that executes qualification units.
  --status     print the compact manifest status (safe while a run executes).
  --manifest   print the full compact manifest JSON.

Exit codes: 0 PASS, 1 fail-closed global integrity, 2 unexpected internal error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
SCRIPTS = PROJECT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

# ---------------------------------------------------------------------------
# Frozen Phase4 authority (git-blob LF-normalized hashes; see
# R4_FRAMEWORK_GATE_PHASE4_EFFECTIVE_EXECUTION_CODE_SET.json)
# ---------------------------------------------------------------------------
FROZEN_BRANCH = "parallel/r4-population-qualification-144-2026-10-16"
FROZEN_HEAD = "581cd2dd607fe15b1bebc415abd3ca268a3afd16"
FROZEN_CODE_SET_AGGREGATE = "4f3a651199b5d5626b6bea971a6d5d47cd14f73e66e55c24993f9ecc94c998ec"
FROZEN_CODE_SET_MANIFEST = (
    PROJECT / "research" / "env-canon-r4" / "R4_FRAMEWORK_GATE_PHASE4_EFFECTIVE_EXECUTION_CODE_SET.json"
)
CLOSURE_SCRIPT = SCRIPTS / "r4_full144_static_artifact_closure.py"

WSL_DISTRO = "Ubuntu-24.04"
WSL_REPO = "/opt/wp2_v2/saleor-cache"
DRIVE = "D:"

N_UNITS = 144
EXPECTED_IMAGE_PAIRS = 11

DISK_WARN_GIB = 160.0
DISK_STOP_GIB = 120.0

# Unique qualification-owned Docker volume prefix (P2 guard #3): the harness
# materializes into volumes it OWNS, so it can never collide with or corrupt the
# scientific ``r4full144_`` / ``r4n12_`` namespaces, and cleanup ownership is
# unambiguous.
VOLUME_PREFIX = "r4qual144_"

QUAL_ROOT = Path(
    os.environ.get(
        "R4_FULL144_QUAL_ROOT",
        r"D:\WP2\runs\r4-full-d7-144-qualification-2026-10-16",
    )
)
MANIFEST_NAME = "QUALIFICATION_MANIFEST.json"
NON_SCIENTIFIC_MARKER = "QUALIFICATION_ROOT_NON_SCIENTIFIC.txt"

# Ambient execution variables that could change run-root or test behaviour
# (P2 guard #1).  R4_FULL144_RUN_ROOT is re-forced to the qualification root.
SANITIZE_ENV_KEYS = (
    "R4_FULL144_RUN_ROOT",
    "PYTEST_CURRENT_TEST",
    "PYTEST_ADDOPTS",
    "TOX_ENV_DIR",
    "PYTHONSTARTUP",
    "PYTHONINSPECT",
)


class QualificationError(Exception):
    """Fail-closed harness error."""


class GlobalIntegrityError(QualificationError):
    """Any mandatory fail-closed global integrity violation."""


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise QualificationError(f"missing artifact: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise QualificationError(f"artifact {path} is not a JSON object")
    return data


def _run(
    cmd: list[str], cwd: Path | None = None, timeout: int = 120, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        timeout=timeout,
        env=env,
    )


# ---------------------------------------------------------------------------
# P2 guard #1 — environment sanitization
# ---------------------------------------------------------------------------
def sanitized_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in SANITIZE_ENV_KEYS:
        env.pop(key, None)
    env["R4_FULL144_RUN_ROOT"] = str(QUAL_ROOT)
    return env


def apply_env_sanitization() -> None:
    for key in SANITIZE_ENV_KEYS:
        os.environ.pop(key, None)
    os.environ["R4_FULL144_RUN_ROOT"] = str(QUAL_ROOT)


# ---------------------------------------------------------------------------
# Lazy driver binding: R4_FULL144_RUN_ROOT must be set before the frozen driver
# module is imported (its run root is a module-level constant).
# ---------------------------------------------------------------------------
_LOADED: tuple[Any, Any] | None = None


def load_driver() -> tuple[Any, Any]:
    global _LOADED
    if _LOADED is None:
        apply_env_sanitization()
        from benchmark.wp2.full144 import driver, population

        if str(driver.FULL144_ROOT.resolve()) != str(QUAL_ROOT.resolve()):
            raise GlobalIntegrityError(
                f"driver run root {driver.FULL144_ROOT} != qualification root {QUAL_ROOT}"
            )
        _LOADED = (driver, population)
    return _LOADED


# ---------------------------------------------------------------------------
# Git / frozen execution-code verification
# ---------------------------------------------------------------------------
def git_head() -> str:
    proc = _run(["git", "rev-parse", "HEAD"], cwd=PROJECT)
    if proc.returncode != 0:
        raise QualificationError(f"git rev-parse HEAD failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def git_branch() -> str:
    proc = _run(["git", "branch", "--show-current"], cwd=PROJECT)
    if proc.returncode != 0:
        raise QualificationError(f"git branch failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def git_clean_tracked() -> bool:
    proc = _run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=PROJECT)
    if proc.returncode != 0:
        raise QualificationError(f"git status failed: {proc.stderr.strip()}")
    return proc.stdout.strip() == ""


def effective_code_set_hash_from_worktree() -> str:
    """Recompute the Phase4 aggregate execution-code hash from committed blobs.

    Identical method to the frozen successor preflight: SHA-256 over LF-joined
    sorted lines ``<sha256>  <path>`` where each sha256 is of the LF-normalized
    git blob bytes at HEAD.
    """
    manifest = json.loads(FROZEN_CODE_SET_MANIFEST.read_text(encoding="utf-8"))
    members = [dict(m) for m in manifest["members"]]
    lines: list[str] = []
    for member in sorted(members, key=lambda m: m["path"]):
        path = str(member["path"])
        blob = _run(["git", "rev-parse", f"HEAD:{path}"], cwd=PROJECT)
        if blob.returncode != 0:
            raise QualificationError(f"blob identity missing for {path}: {blob.stderr.strip()}")
        data = subprocess.run(
            ["git", "cat-file", "blob", blob.stdout.strip()],
            capture_output=True,
            cwd=str(PROJECT),
            timeout=120,
        ).stdout
        lines.append(f"{_sha256_bytes(data)}  {path}")
    payload = ("\n".join(sorted(lines)) + "\n").encode("utf-8")
    return _sha256_bytes(payload)


# ---------------------------------------------------------------------------
# Global integrity probes (P2 guards #7/#8/#9 + global list)
# ---------------------------------------------------------------------------
def docker_reachable() -> bool:
    proc = _run(
        ["wsl", "-d", WSL_DISTRO, "--", "docker", "info", "--format", "{{.ServerVersion}}"],
        env=sanitized_env(),
    )
    return proc.returncode == 0 and bool((proc.stdout or "").strip())


def source_repo_reachable() -> bool:
    proc = _run(
        ["wsl", "-d", WSL_DISTRO, "--", "test", "-d", WSL_REPO],
        env=sanitized_env(),
        timeout=60,
    )
    return proc.returncode == 0


def disk_free_gib() -> float:
    return shutil.disk_usage(DRIVE).free / (1024.0**3)


def image_bindings_ok() -> bool:
    try:
        driver, _ = load_driver()
        driver.verify_image_bindings()
        return True
    except Exception:
        return False


def owned_volumes() -> list[str]:
    proc = _run(
        ["wsl", "-d", WSL_DISTRO, "--", "docker", "volume", "ls", "-q"],
        env=sanitized_env(),
    )
    if proc.returncode != 0:
        return []
    return [
        line.strip()
        for line in (proc.stdout or "").splitlines()
        if line.strip().startswith(VOLUME_PREFIX)
    ]


def cleanup_owned_volumes(names: list[str]) -> None:
    for name in names:
        _run(
            ["wsl", "-d", WSL_DISTRO, "--", "docker", "volume", "rm", "-f", name],
            env=sanitized_env(),
        )


def verify_artifact_closure() -> dict[str, Any]:
    """Run the frozen static artifact-closure gate to a TEMP root (never the
    qualification root, and never the repo evidence path).  Returns a stable
    deterministic closure hash over the semantic subset of the generated
    evidence."""
    import tempfile

    with tempfile.TemporaryDirectory(prefix="r4qual_closure_") as td:
        run_root = Path(td)
        evid = run_root / "closure.json"
        proc = _run(
            [
                sys.executable,
                str(CLOSURE_SCRIPT),
                "--run-root",
                str(run_root),
                "--repo-evidence",
                str(evid),
            ],
            cwd=PROJECT,
            env=sanitized_env(),
            timeout=1800,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0 or "FULL144_STATIC_ARTIFACT_CLOSURE_PASS_144_144" not in out:
            raise GlobalIntegrityError(
                f"artifact closure not 144/144 (rc={proc.returncode}): {out[-2000:]}"
            )
        payload = _read_json(evid)
        semantic = {
            "N_UNITS": payload["N_UNITS"],
            "N_RESOLVABLE": payload["N_RESOLVABLE"],
            "N_MISSING": payload["N_MISSING"],
            "N_INCOMPATIBLE": payload["N_INCOMPATIBLE"],
            "population_identity": payload["population_identity"],
            "ordered_membership_hash": payload["ordered_membership_hash"],
        }
        return {
            "verdict": "PASS_FULL144_STATIC_ARTIFACT_CLOSURE",
            "n_units": int(payload["N_UNITS"]),
            "n_resolvable": int(payload["N_RESOLVABLE"]),
            "artifact_closure_hash": _sha256_bytes(
                json.dumps(semantic, sort_keys=True).encode("utf-8")
            ),
        }


# ---------------------------------------------------------------------------
# Global preflight / freshness gate (runs before ANY root file is created)
# ---------------------------------------------------------------------------
def freshness_check() -> dict[str, Any]:
    branch = git_branch()
    if branch != FROZEN_BRANCH:
        raise GlobalIntegrityError(f"branch {branch} != frozen {FROZEN_BRANCH}")
    head = git_head()
    if head != FROZEN_HEAD:
        raise GlobalIntegrityError(f"git HEAD {head} != frozen {FROZEN_HEAD}")
    if not git_clean_tracked():
        raise GlobalIntegrityError("tracked worktree is not clean")

    code_hash = effective_code_set_hash_from_worktree()
    if code_hash != FROZEN_CODE_SET_AGGREGATE:
        raise GlobalIntegrityError(
            f"execution-code hash drift: {code_hash} != frozen {FROZEN_CODE_SET_AGGREGATE}"
        )

    driver, population = load_driver()
    try:
        pop = population.validate_population()
    except Exception as exc:
        raise GlobalIntegrityError(f"population/order authority gate failed: {exc}") from exc
    if pop["ordered_membership_hash"] != population.EXPECTED_ORDERED_MEMBERSHIP_HASH:
        raise GlobalIntegrityError("population/order hash drift")
    if pop["binding_hash"] != population.EXPECTED_BINDING_HASH:
        raise GlobalIntegrityError("image binding hash drift")

    try:
        driver.verify_image_bindings()
    except Exception as exc:
        raise GlobalIntegrityError(f"required immutable image missing/drifted: {exc}") from exc

    if not docker_reachable():
        raise GlobalIntegrityError("Docker daemon unavailable")
    if not source_repo_reachable():
        raise GlobalIntegrityError(f"source repository unavailable: {WSL_REPO}")

    free = disk_free_gib()
    if free < DISK_STOP_GIB:
        raise GlobalIntegrityError(f"unsafe low disk: {free:.1f} GiB < {DISK_STOP_GIB:.0f} GiB")

    return {
        "branch": branch,
        "git_head": head,
        "tracked_clean": True,
        "effective_execution_code_set_hash": code_hash,
        "population_identity": pop["population_identity"],
        "ordered_membership_hash": pop["ordered_membership_hash"],
        "binding_hash": pop["binding_hash"],
        "image_pairs_verified": EXPECTED_IMAGE_PAIRS,
        "disk_free_gib": free,
        "docker_reachable": True,
        "source_repo_reachable": True,
    }


# ---------------------------------------------------------------------------
# Manifest (P3) — compact, authoritative, non-scientific checkpoint
# ---------------------------------------------------------------------------
def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _counts(units: dict[str, str]) -> dict[str, int]:
    c = Counter(units.values())
    failed = c["UNIT_GATE_FAILURE"] + c["UNIT_HARNESS_FAILURE"]
    return {
        "completed": c["PASS"] + failed,
        "pass": c["PASS"],
        "unit_gate_failure": c["UNIT_GATE_FAILURE"],
        "unit_harness_failure": c["UNIT_HARNESS_FAILURE"],
        "pending": c["PENDING"],
    }


def new_manifest(fresh: dict[str, Any], closure: dict[str, Any]) -> dict[str, Any]:
    units = {str(i): "PENDING" for i in range(1, N_UNITS + 1)}
    manifest: dict[str, Any] = {
        "schema_version": "env-canon-r4/population-qualification-144/1.0",
        "mission_id": "M17_D7_R4_POPULATION_QUALIFICATION_144_HARNESS",
        "non_scientific_root": True,
        "qualification_root": str(QUAL_ROOT),
        "frozen_git_head": fresh["git_head"],
        "frozen_branch": fresh["branch"],
        "frozen_execution_code_hash": fresh["effective_execution_code_set_hash"],
        "population_identity": fresh["population_identity"],
        "population_order_hash": fresh["ordered_membership_hash"],
        "artifact_closure_hash": closure["artifact_closure_hash"],
        "image_binding_hash": fresh["binding_hash"],
        "image_pairs_verified": EXPECTED_IMAGE_PAIRS,
        "total": N_UNITS,
        "units": units,
        "failed_units": [],
        "start_utc": utcnow(),
        "last_update_utc": utcnow(),
        "disk_free_gib": {
            "start": round(fresh["disk_free_gib"], 2),
            "current": round(fresh["disk_free_gib"], 2),
            "minimum": round(fresh["disk_free_gib"], 2),
        },
        "zero_network": True,
        "network_policy": "--network=none; no pull/build/download/acquire",
    }
    manifest.update(_counts(units))
    return manifest


def load_manifest() -> dict[str, Any] | None:
    path = QUAL_ROOT / MANIFEST_NAME
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GlobalIntegrityError(f"checkpoint corruption (invalid JSON): {path}") from exc
    if not isinstance(data, dict):
        raise GlobalIntegrityError(f"checkpoint corruption (not an object): {path}")
    return data


def verify_manifest_frozen(manifest: dict[str, Any], closure: dict[str, Any]) -> None:
    """Resume rejects code/population/artifact/image hash drift (P2 #14)."""
    checks = {
        "frozen_git_head": FROZEN_HEAD,
        "frozen_branch": FROZEN_BRANCH,
        "frozen_execution_code_hash": FROZEN_CODE_SET_AGGREGATE,
    }
    for key, expected in checks.items():
        if manifest.get(key) != expected:
            raise GlobalIntegrityError(f"resume drift {key}: {manifest.get(key)} != {expected}")
    driver, population = load_driver()
    pop = population.validate_population()
    if manifest.get("population_identity") != pop["population_identity"]:
        raise GlobalIntegrityError("resume population identity drift")
    if manifest.get("population_order_hash") != pop["ordered_membership_hash"]:
        raise GlobalIntegrityError("resume population order drift")
    if manifest.get("image_binding_hash") != pop["binding_hash"]:
        raise GlobalIntegrityError("resume image binding drift")
    if manifest.get("artifact_closure_hash") != closure["artifact_closure_hash"]:
        raise GlobalIntegrityError("resume artifact closure drift")
    if manifest.get("total") != N_UNITS:
        raise GlobalIntegrityError(f"resume total {manifest.get('total')} != {N_UNITS}")
    if manifest.get("zero_network") is not True:
        raise GlobalIntegrityError("resume zero_network assertion lost")
    if set(manifest.get("units", {}).keys()) != {str(i) for i in range(1, N_UNITS + 1)}:
        raise GlobalIntegrityError("resume unit set drift")
    for result in manifest["units"].values():
        if result not in ("PENDING", "PASS", "UNIT_GATE_FAILURE", "UNIT_HARNESS_FAILURE"):
            raise GlobalIntegrityError(f"resume unknown unit result {result!r}")


def ordered_uids() -> list[str]:
    driver, population = load_driver()
    uids: list[str] = population.ordered_unit_ids()
    if len(uids) != N_UNITS:
        raise GlobalIntegrityError(f"population unit count {len(uids)} != {N_UNITS}")
    if population.ordered_membership_hash() != population.EXPECTED_ORDERED_MEMBERSHIP_HASH:
        raise GlobalIntegrityError("population order hash drift")
    return uids


# ---------------------------------------------------------------------------
# Per-unit execution — exercises the exact frozen Phase4 unit path
# ---------------------------------------------------------------------------
def make_qual_runner() -> Any:
    """Frozen Full144 unit runner bound to a qualification-owned volume prefix
    (P2 guard #3).  Only the ephemeral Docker volume NAME differs; every
    materialization/install/parse/classify semantic is the frozen qualified
    runner's."""
    driver, _ = load_driver()
    r2 = driver.r2
    runner_cls: type = driver.Full144UnitRunner

    class QualUnitRunner(runner_cls):
        def materialize(self, commit: str, uid: str, tid: str, index: int) -> tuple[str, int]:
            vol = f"{VOLUME_PREFIX}{uid.replace('-', '_')}_{tid.replace('-', '_')}_{index}"
            r2.ensure_empty_volume(self.backend, vol)
            try:
                count = self._wiring().materialize(commit, vol)
            except r2.MaterializeError as exc:
                raise driver.Full144FailClosedError(
                    f"LINUX_MATERIALIZATION_FAILURE {uid} {tid}: {exc}"
                ) from exc
            if count <= 0:
                raise driver.Full144FailClosedError(f"materialization produced 0 files for {tid}")
            return vol, count

    return QualUnitRunner()


def seed_runner_progress(idx: int, uids: list[str]) -> None:
    """Satisfy the frozen runner's fail-fast precondition (prior indices PASS)
    inside the NON-SCIENTIFIC qualification root.  The qualification manifest is
    the authoritative record; this is orchestration scratch only."""
    driver, _ = load_driver()
    driver.PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    completed = [
        {
            "validation_unit_id": uids[i - 1],
            "calibration_index": i,
            "result": "PASS",
            "classification": "PASS",
            "elapsed_seconds": 0.0,
        }
        for i in range(1, idx)
    ]
    _atomic_write_json(driver.PROGRESS_JSON, {"completed": completed, "stopped_early": False})


def run_one_unit(idx: int, uids: list[str]) -> dict[str, Any]:
    """Execute exactly one frozen Phase4 unit; returns its frozen record."""
    from typing import cast

    driver, _ = load_driver()
    driver.configure_runner()
    seed_runner_progress(idx, uids)
    runner = make_qual_runner()
    return cast(dict[str, Any], runner.run_unit(idx))


def _persist_harness_failure(uid: str, exc: BaseException) -> Path:
    from typing import cast

    driver, _ = load_driver()
    out_dir = driver.UNITS_DIR / uid
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "qualification_harness_failure.json"
    payload = {
        "validation_unit_id": uid,
        "result": "UNIT_HARNESS_FAILURE",
        "exception": type(exc).__name__,
        "detail": str(exc)[:2000],
        "utc": utcnow(),
    }
    _atomic_write_json(path, payload)
    return cast(Path, path)


def cleanup_unit_wheelhouse(uid: str) -> None:
    """P2 guard #5/#6: remove per-unit temporary wheelhouse data after evidence
    is safely persisted; preserve shared era caches (materialized/merged)."""
    driver, _ = load_driver()
    mat = driver.MATERIALIZED_DIR
    for target in (mat / "unit_wheelhouse" / uid, mat / "tmp_pyproject_refs"):
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)


# ---------------------------------------------------------------------------
# Deterministic sweep (resumable, atomic checkpoint after every unit)
# ---------------------------------------------------------------------------
def run_sweep() -> dict[str, Any]:
    driver, population = load_driver()
    apply_env_sanitization()

    uids = ordered_uids()
    fresh = freshness_check()
    closure = verify_artifact_closure()

    manifest = load_manifest()
    if manifest is None:
        manifest = new_manifest(fresh, closure)
        _atomic_write_json(QUAL_ROOT / MANIFEST_NAME, manifest)
    else:
        verify_manifest_frozen(manifest, closure)

    # Roots created only AFTER freshness validation (P2 guard #2: no
    # stdout/stderr redirect files inside a root before freshness).
    driver.configure_runner()
    (QUAL_ROOT / NON_SCIENTIFIC_MARKER).write_text(
        "NON-SCIENTIFIC qualification root for M17_D7_R4_POPULATION_QUALIFICATION_144_HARNESS\n",
        encoding="utf-8",
    )

    for idx in range(1, N_UNITS + 1):
        uid = uids[idx - 1]
        key = str(idx)
        if manifest["units"][key] != "PENDING":
            continue

        free = disk_free_gib()
        manifest["disk_free_gib"]["current"] = round(free, 2)
        manifest["disk_free_gib"]["minimum"] = round(
            min(manifest["disk_free_gib"]["minimum"], free), 2
        )
        if free < DISK_STOP_GIB:
            raise GlobalIntegrityError(
                f"unsafe low disk before unit {idx}: {free:.1f} GiB < {DISK_STOP_GIB:.0f} GiB"
            )

        result: str
        classification: str = ""
        detail: str = ""
        try:
            record = run_one_unit(idx, uids)
            result = "PASS" if record.get("result") == "PASS" else "UNIT_GATE_FAILURE"
            classification = str(record.get("classification", ""))
        except Exception as exc:
            if not image_bindings_ok() or not docker_reachable() or not source_repo_reachable():
                raise GlobalIntegrityError(
                    f"global integrity broken during unit {idx} ({uid}): {exc}"
                ) from exc
            if disk_free_gib() < DISK_STOP_GIB:
                raise GlobalIntegrityError(
                    f"unsafe low disk during unit {idx} ({uid}): {exc}"
                ) from exc
            result = "UNIT_HARNESS_FAILURE"
            classification = type(exc).__name__
            detail = str(exc)[:2000]
            _persist_harness_failure(uid, exc)

        leftovers = owned_volumes()
        if leftovers:
            cleanup_owned_volumes(leftovers)

        cleanup_unit_wheelhouse(uid)

        manifest["units"][key] = result
        manifest["last_update_utc"] = utcnow()
        if result != "PASS":
            manifest["failed_units"] = [
                f for f in manifest["failed_units"] if f["index"] != idx
            ]
            manifest["failed_units"].append(
                {
                    "index": idx,
                    "validation_unit_id": uid,
                    "result": result,
                    "classification": classification,
                    "detail": detail[:500],
                }
            )
        manifest.update(_counts(manifest["units"]))
        _atomic_write_json(QUAL_ROOT / MANIFEST_NAME, manifest)

    return manifest


def preflight() -> dict[str, Any]:
    """Every global gate + the frozen 144-unit order.  NEVER executes a unit."""
    uids = ordered_uids()
    fresh = freshness_check()
    closure = verify_artifact_closure()
    return {
        "preflight": "PASS",
        "n_units": len(uids),
        "order_membership_hash": fresh["ordered_membership_hash"],
        "effective_execution_code_set_hash": fresh["effective_execution_code_set_hash"],
        "artifact_closure": closure["verdict"],
        "artifact_closure_hash": closure["artifact_closure_hash"],
        "image_pairs_verified": fresh["image_pairs_verified"],
        "disk_free_gib": round(fresh["disk_free_gib"], 2),
        "zero_scientific_units_executed": True,
        "zero_qualification_units_executed": True,
        "units": uids,
    }


def static_checks() -> dict[str, Any]:
    """No pull/build/network/LLM dependency in the execution path (P2 #10/#11)."""
    runner_src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
    driver_src = (SRC / "benchmark" / "wp2" / "full144" / "driver.py").read_text(encoding="utf-8")
    ps1_src = (SCRIPTS / "r4_full144_qualification_launcher.ps1").read_text(encoding="utf-8")

    if '"--network=none"' not in runner_src:
        raise QualificationError("runner does not require --network=none")
    for forbidden in ("OpenCode", "OpenRouter", "LLM", "openai", "anthropic"):
        if forbidden.lower() in ps1_src.lower():
            raise QualificationError(f"launcher must not depend on {forbidden!r}")
    for src in (runner_src, driver_src):
        if '"pull"' in src or '"build"' in src:
            raise QualificationError("pull/build literal present in execution code")

    return {
        "static": "PASS",
        "network_isolation": "--network=none",
        "no_pull_build": True,
        "no_llm_dependency": True,
    }


def status() -> dict[str, Any]:
    manifest = load_manifest()
    if manifest is None:
        return {
            "status": "NOT_STARTED",
            "qualification_root": str(QUAL_ROOT),
            "hint": "run the qualification launcher; --preflight is safe at any time",
        }
    return {
        "status": "RUNNING" if manifest["pending"] else "COMPLETE",
        "total": manifest["total"],
        "completed": manifest["completed"],
        "pass": manifest["pass"],
        "unit_gate_failure": manifest["unit_gate_failure"],
        "unit_harness_failure": manifest["unit_harness_failure"],
        "pending": manifest["pending"],
        "failed_units": [
            {"index": f["index"], "validation_unit_id": f["validation_unit_id"], "result": f["result"]}
            for f in manifest["failed_units"]
        ],
        "start_utc": manifest["start_utc"],
        "last_update_utc": manifest["last_update_utc"],
        "disk_free_gib": manifest["disk_free_gib"],
        "zero_network": manifest["zero_network"],
        "qualification_root": manifest["qualification_root"],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="R4 Full-D7 144-unit population-qualification harness")
    ap.add_argument("--preflight", action="store_true", help="all global gates + 144-unit order; NO execution")
    ap.add_argument("--static", action="store_true", help="static no-pull/build/network checks")
    ap.add_argument("--list", action="store_true", help="print the deterministic frozen 144-unit order")
    ap.add_argument("--run", action="store_true", help="run the deterministic qualification sweep (resumable)")
    ap.add_argument("--status", action="store_true", help="print compact manifest status")
    ap.add_argument("--manifest", action="store_true", help="print the full compact manifest JSON")
    args = ap.parse_args(argv)

    try:
        if args.preflight:
            print(json.dumps(preflight(), indent=2, sort_keys=True))
            print("PREFLIGHT_PASS 144_UNITS_ZERO_EXECUTED")
            return 0
        if args.static:
            print(json.dumps(static_checks(), indent=2, sort_keys=True))
            print("STATIC_PASS")
            return 0
        if args.list:
            for uid in ordered_uids():
                print(uid)
            return 0
        if args.run:
            manifest = run_sweep()
            print(json.dumps(status(), indent=2, sort_keys=True))
            print(
                "POPULATION_QUALIFICATION_144_RUN_COMPLETE"
                if manifest["pending"] == 0
                else "POPULATION_QUALIFICATION_144_SWEEP_STOPPED"
            )
            return 0
        if args.status:
            print(json.dumps(status(), indent=2, sort_keys=True))
            return 0
        if args.manifest:
            m = load_manifest()
            if m is None:
                print(json.dumps({"manifest": None}, indent=2, sort_keys=True))
                return 0
            print(json.dumps(m, indent=2, sort_keys=True))
            return 0
    except GlobalIntegrityError as exc:
        print(f"FAIL_CLOSED_GLOBAL_INTEGRITY {exc}", file=sys.stderr)
        return 1
    except QualificationError as exc:
        print(f"FAIL_CLOSED {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"UNEXPECTED_FAILURE {exc!r}", file=sys.stderr)
        return 2

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
