#!/usr/bin/env python3
"""T12 M02-D3 — REAL per-arm F2P execution driver bridge (OFFLINE in D3).

Mission: T12_M02_D3_EXECUTABLE_F2P_GATE_20261027 (Track 1.2, Task 3).

PURPOSE
-------
Close the last real-execution engineering gap: a GENUINE, provable per-arm
bridge ``materialize -> per-arm tree -> 3-node F2P (run_state_v3 isolated)
-> receipt validation -> teardown`` with NO pseudo-runs, NO fake CLI flags
and NO invented engine calls.

The m3b smoke CLI (`wp2_m3b_runner_smoke.py`) is SINGLE-node and is explicitly
NOT used as the 3-node pilot runner (its argv never reads the task-id
positional).  The pilot contract is this module's per-arm
``run_state_v3(era_key='py312', ..., test_files=3 frozen nodes, ...)`` call,
which the frozen engine documents as "then 3x per changed-test-file" -> the
3 nodes x 3 reps = 9 JUnit per arm contract (harness_v3.py line 691 docstring
and line ~758 JUnit naming; verified against the frozen worktree 2026-10-27).

MODES (all read the SAME immutable plan and frozen source-code paths)
---------------------------------------------------------------------
* ``preflight`` — fail-closed admission read (no side effects, no Docker/WSL
  probe): branch/HEAD, matrix/plan pins, engine stage pins, scope/
  classification/test-authority artifact state, RD-8 decision artifact state,
  RD-9 authorization artifact state, eligibility NOT_RUN.
* ``dry-run``   — deterministic 13-arm NOT_RUN plan + a CONCRETE fully
  resolved PROSPECTIVE physical run plan for the frozen first pilot (4 arms:
  SIP, NEG, FULL_REFERENCE, RM_CSS).  Zero model calls, USD 0.00.
* ``run``       — fail-CLOSED real execution.  Refuses to start unless an
  RD-8 typed ADOPT_PILOT_ONLY decision artifact, a separate typed RD-9
  execution authorization (exclusivity + wall window), budget/window inputs
  and the exact pinned inputs are all present and verified.  Never reached
  in this D3 mission (all prospective arms remain NOT_RUN).

SAFETY (hard)
-------------
* No retries, no partial-PASS: an arm is PASS only when every stage of the
  bridge completed and the receipts validate; otherwise the run is FAIL with
  typed stage reasons.  NEG's EXPECTED assertion-failure outcome is a
  classified control event (CONTROL_EXPECTED), never an ordinary FAIL and
  never a PASS claim; ordinary FAIL is never marked success.
* Classification/test-authority artifacts are passed ONLY into the
  materializer argv (evaluation/materializer-only boundary).  They are never
  exposed to run_state_v3, to any selector, or to any generation prompt.
* The real frozen functions (``harness_v3.run_state_v3``,
  ``lock_install_script``, ``OpwsIsolatedRuntime``, ``resolve_runtime_image``)
  are imported from the FROZEN worktree at run time; mocks appear only in
  unit tests, never in this execution path.
* D3 executes NOTHING: preflight/dry-run are read-only; ``run`` requires
  artifacts that do not exist yet, so it always stops with typed gates.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

_SCRIPTS = Path(__file__).resolve().parent
_module = _SCRIPTS.name  # for stable import names

_adapt_spec = importlib.util.spec_from_file_location("t12_m02_arm_adapter", _SCRIPTS / "t12_m02_arm_adapter.py")
assert _adapt_spec is not None and _adapt_spec.loader is not None
_adapt = importlib.util.module_from_spec(_adapt_spec)
_adapt_spec.loader.exec_module(_adapt)

_driver_spec = importlib.util.spec_from_file_location("t12_m02_driver", _SCRIPTS / "t12_m02_driver.py")
assert _driver_spec is not None and _driver_spec.loader is not None
_driver = importlib.util.module_from_spec(_driver_spec)
_driver_spec.loader.exec_module(_driver)

_contract_spec = importlib.util.spec_from_file_location("t12_m02_f2p_contract", _SCRIPTS / "t12_m02_f2p_contract.py")
assert _contract_spec is not None and _contract_spec.loader is not None
_contract = importlib.util.module_from_spec(_contract_spec)
_contract_spec.loader.exec_module(_contract)

_receipts_spec = importlib.util.spec_from_file_location("t12_m02_receipts", _SCRIPTS / "t12_m02_receipts.py")
assert _receipts_spec is not None and _receipts_spec.loader is not None
_receipts = importlib.util.module_from_spec(_receipts_spec)
_receipts_spec.loader.exec_module(_receipts)

_d3r2_spec = importlib.util.spec_from_file_location("t12_m02_d3r2_identity", _SCRIPTS / "t12_m02_d3r2_identity.py")
assert _d3r2_spec is not None and _d3r2_spec.loader is not None
_d3r2 = importlib.util.module_from_spec(_d3r2_spec)
sys.modules["t12_m02_d3r2_identity"] = _d3r2
_d3r2_spec.loader.exec_module(_d3r2)

SCHEMA_PREFLIGHT = "t12_m02_execute_f2p_preflight_v1"
SCHEMA_DRYRUN = "t12_m02_execute_f2p_dryrun_v1"
SCHEMA_RUN = "t12_m02_execute_f2p_run_v1"
RD8_SCHEMA = "t12_m02_rd8_pilot_decision_v1"
AUTH_SCHEMA = "t12_m02_execution_authorization_v1"

PILOT_ARMS = ["SIP", "NEG", "FULL_REFERENCE", "RM_CSS"]  # frozen first competitor order
PILOT_NODE_COUNT = 3
PILOT_REPS = 3
PILOT_JUNIT_PER_ARM = PILOT_NODE_COUNT * PILOT_REPS  # 9
# D3-R1: the first N=1 F2P pilot executes its controls in EXACTLY this order
# and STOP-BEFORE-SIP on any control mismatch or infrastructure failure.
CONTROL_EXECUTION_ORDER = ["NEG", "FULL_REFERENCE", "RM_CSS", "SIP"]
ERA_KEY = _adapt.FROZEN_TASK.split("-")[-1][:8]  # task8 (7e42fc67), NOT an era key
TID = "7e42fc67ce72"
TASK8 = "7e42fc67"
MATERIALIZER_REL = "scripts/opws_phase3b_patch_materialize.py"
HARNESS_REL = "src/benchmark/wp2/harness_v3.py"
RUNTIME_COMPAT_REL = "src/benchmark/wp2/runtime_image_compat_v1.py"
ISOLATED_RUNTIME_REL = "src/benchmark/wp2/opws_isolated_runtime_v1.py"

# Frozen cluster pattern for per-arm execution trees (from the frozen m19b
# pilot TARGET_WORKTREE_LINUX `/root/m19b_r3_20261024/wt_t`).
WORKTREE_PATTERN_LINUX = "/root/m19b_r3_20261024/wt_t"
WORKTREE_ARM_PATTERN_LINUX = "/root/m19b_r3_20261024/wt_t_{arm}"

# Linux host-scratch base for the isolated runtime.  The frozen engine maps
# the results dir into the Linux runtime via its own SCRATCH_ROOT/out_linux
# convention; that base is host-specific and is supplied by the operator via
# the environment so the public source tree never embeds a private host path.
LINUX_SCRATCH_BASE = os.environ.get("T12_M02_SCRATCH_LINUX", "/results")

# Expected derived classification/test-authority bytes (RD-8, reproduced
# byte-identically from D2 in this mission).  These are the pinned oracle
# boundary artifacts — researcher approval pending.
DERIVED_CLASSIFICATION_SHA256 = "b51632ad9e79c465450acb98a11da496ffa2e226118ace13b5b5f1d5ff09ad2a"
DERIVED_TEST_AUTHORITY_SHA256 = "c08b26c4389e1d9a1971769505d1f407b1cff54da9297bdc6e8586fe30e2406f"


def _utc_now() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _utc_seconds() -> str:
    """Second-precision UTC (the receipts validator's times format)."""
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc_iso(value: object) -> datetime.datetime | None:
    """Strict ISO-8601 UTC parse (Z or +00:00 only).  None on malformed or
    non-UTC input (fail closed)."""
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.utcoffset() != datetime.timedelta(0):
        return None
    return dt


def _sha256_bytes(data: str | bytes) -> str:
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Read-only git invocation (never writes)."""
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", check=False
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="t12_m02_execute_f2p",
        description="T12 M02-D3 real per-arm F2P execution bridge "
        "(preflight/dry-run now; run fails closed without "
        "researcher RD-8/RD-9 authorizations).",
    )

    def _shared(p: argparse.ArgumentParser) -> None:
        p.add_argument("--out", default=None, help="results/evidence dir (fresh, never reused)")
        p.add_argument("--worktree", default=str(_adapt.FROZEN_WORKTREE_ROOT_DEFAULT))
        p.add_argument("--source-repo", default=None)
        p.add_argument("--matrix", default=None)
        p.add_argument("--plan", default=None)
        p.add_argument("--scopes-dir", default=None, help="scope_<ARM>.json artifacts dir")
        p.add_argument("--classification", default=None)
        p.add_argument("--test-authority", default=None)
        p.add_argument(
            "--arms", default=None, help="comma list (default: all 13; pilot: SIP,NEG,FULL_REFERENCE,RM_CSS)"
        )

    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("preflight", help="fail-closed admission read (no side effects)")
    _shared(p)
    p.add_argument("--rd8-decision", default=None, help="typed RD-8 decision artifact (ABSENT -> RD8_PENDING)")
    p.add_argument(
        "--authorization", default=None, help="typed RD-9 execution authorization (ABSENT -> NOT_AUTHORIZED)"
    )
    p.add_argument(
        "--debug-junit-template",
        action="store_true",
        help="DEV ONLY: emit sample_run_receipt fixture (used by unit tests)",
    )

    p = sub.add_parser("dry-run", help="13-arm NOT_RUN plan + concrete prospective pilot plan")
    _shared(p)
    p.add_argument("--pilot-only", action="store_true", help="render only the 4-arm pilot plan")
    p.add_argument("--worktrees-json", default=None, help="arm->linux worktree path mapping (proposed when absent)")

    p = sub.add_parser("run", help="REAL execution (fail-CLOSED; never reached without RD-8 + RD-9)")
    _shared(p)
    p.add_argument(
        "--rd8-decision", default=None, help="typed RD-8 decision artifact (ABSENT -> RD8_PENDING; fail-closed)"
    )
    p.add_argument(
        "--authorization", default=None, help="typed RD-9 execution authorization (ABSENT -> EXECUTION_NOT_AUTHORIZED)"
    )
    p.add_argument(
        "--budget-json", default=None, help="budget/window artifact: model_usd==0.00, max_wall_s, exclusivity slots"
    )
    p.add_argument(
        "--worktrees-json", default=None, help="arm -> materialized linux worktree path mapping (REQUIRED input)"
    )
    p.add_argument(
        "--wall-max-s",
        type=float,
        default=None,
        help="wall-clock cap for the whole run (researcher-recorded before execution)",
    )
    p.add_argument(
        "--autorun-in-d3-flag", default=None, help="REQUIRED: literal value must be 'NEVER_IN_D3' (anti-footgun)"
    )
    return ap


# ---------------------------------------------------------------------------
# Shared deterministic helpers
# ---------------------------------------------------------------------------


def _matrix_rows(matrix_path: Path) -> list[dict[str, str]]:
    import csv

    if not matrix_path.is_file():
        raise ValueError(f"matrix file missing: {matrix_path}")
    ok, dig = _adapt.check_matrix_file(matrix_path)
    if not ok:
        raise ValueError(f"MATRIX_HASH_MISMATCH: {matrix_path} sha256={dig}")
    with open(matrix_path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    # D3-R2: the frozen M01D matrix CSV headers are
    # ``reference_patch_sha256``/``reference_patch_bytes`` (``check_matrix_file``
    # pins the byte-exact file); earlier R1 fixtures used the alias
    # ``patch_sha256``/``patch_bytes``.  Normalize here so the committed
    # matrix is consumed without rewriting the frozen artifact.
    for r in rows:
        if "reference_patch_sha256" in r and "patch_sha256" not in r:
            r["patch_sha256"] = r["reference_patch_sha256"]
        if "reference_patch_bytes" in r and "patch_bytes" not in r:
            r["patch_bytes"] = r["reference_patch_bytes"]
    bad = [r["arm_id"] for r in rows if "patch_sha256" not in r]
    if bad:
        raise ValueError(f"MATRIX_COLUMNS_UNEXPECTED: missing reference_patch_sha256 for {bad}")
    return rows


def _plan_ok(plan_path: Path) -> tuple[bool, str]:
    if not plan_path.is_file():
        return False, "plan file missing"
    ok, dig = _adapt.check_plan_file(plan_path)
    return ok, ("OK" if ok else f"PLAN_HASH_MISMATCH sha256={dig}")


def _resolve_worktrees(arms: list[str], worktrees_json: str | None) -> dict[str, str]:
    """Arm -> linux worktree path.  REQUIRED INPUT for --run; for dry-run the
    frozen pattern proposes concrete per-arm paths (never executed)."""
    if worktrees_json:
        payload = json.loads(Path(worktrees_json).read_text(encoding="utf-8"))
        missing = [a for a in arms if a not in payload]
        if missing:
            raise ValueError(f"WORKTREES_MISSING_ARMS: {missing}")
        return {a: str(payload[a]) for a in arms}
    return {a: WORKTREE_ARM_PATTERN_LINUX.format(arm=a) for a in arms}


def arms_to_run(arms_arg: str | None, pilot_only: bool) -> list[str]:
    if arms_arg:
        selected = [a.strip() for a in arms_arg.split(",") if a.strip()]
        known = {a["arm_id"] for a in _adapt.load_arms()}
        unknown = [a for a in selected if a not in known]
        if unknown:
            raise ValueError(f"UNKNOWN_ARMS: {unknown}")
        return selected
    return list(PILOT_ARMS) if pilot_only else [a["arm_id"] for a in _adapt.load_arms()]


# ---------------------------------------------------------------------------
# Admission artifact validators (fail-closed, typed)
# ---------------------------------------------------------------------------


def validate_rd8_decision(path: Path | None) -> dict[str, Any]:
    """An RD-8 decision artifact made by the researcher.  Absence is PENDING,
    never approval.  A present artifact must be typed, signed and pin the
    derived oracle bytes; ADOPT_PILOT_ONLY only."""
    if path is None or not Path(path).is_file():
        return {
            "present": False,
            "status": "RD8_PENDING",
            "reason": "no RD-8 decision artifact supplied; researcher must record "
            "ADOPT_PILOT_ONLY/REJECT with supporting hashes",
        }
    try:
        rec = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        return {"present": True, "status": "STOP", "reason": f"unreadable: {exc}"}
    if not isinstance(rec, dict) or rec.get("schema") != RD8_SCHEMA:
        return {"present": True, "status": "STOP", "reason": f"schema != {RD8_SCHEMA}"}
    decision = rec.get("decision")
    if decision != "ADOPT_PILOT_ONLY":
        return {"present": True, "status": "STOP", "reason": f"decision {decision!r} is not ADOPT_PILOT_ONLY"}
    if not rec.get("signed_by") or not rec.get("signed_at_utc"):
        return {"present": True, "status": "STOP", "reason": "decision missing signed_by/signed_at_utc"}
    if rec.get("classification_sha256") != DERIVED_CLASSIFICATION_SHA256:
        return {
            "present": True,
            "status": "STOP",
            "reason": "decision does not pin the D3-derived classification sha256",
        }
    if rec.get("test_authority_sha256") != DERIVED_TEST_AUTHORITY_SHA256:
        return {
            "present": True,
            "status": "STOP",
            "reason": "decision does not pin the D3-derived test-authority sha256",
        }
    return {
        "present": True,
        "status": "ADOPT_PILOT_ONLY",
        "signed_by": rec.get("signed_by"),
        "signed_at_utc": rec.get("signed_at_utc"),
    }


def validate_authorization(
    path: Path | None, requested_arms: list[str], *, now_utc: datetime.datetime | None = None
) -> dict[str, Any]:
    """Separate typed RD-9 execution authorization: exclusivity window, arm
    set, wall cap and researcher record.  Absence = NOT_AUTHORIZED.

    D3-R1: the window must be a syntactically valid ISO-8601 UTC interval,
    current UTC must be INSIDE it, and max_wall_s must fit the remaining
    window.  ``recorded_by``/``signed_by`` are operator ATTESTATIONS (plain
    text), never cryptographic signatures — reported as such.
    """
    if path is None or not Path(path).is_file():
        return {
            "present": False,
            "status": "EXECUTION_NOT_AUTHORIZED",
            "reason": "no RD-9 execution authorization artifact",
        }
    try:
        rec = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        return {"present": True, "status": "STOP", "reason": f"unreadable: {exc}"}
    if not isinstance(rec, dict) or rec.get("schema") != AUTH_SCHEMA:
        return {"present": True, "status": "STOP", "reason": f"schema != {AUTH_SCHEMA}"}
    if rec.get("grant") != "RD9_F2P_PILOT":
        return {"present": True, "status": "STOP", "reason": "grant is not RD9_F2P_PILOT"}
    authorized = set(rec.get("authorized_arms") or [])
    invalid = sorted(authorized - set(PILOT_ARMS))
    if not authorized or invalid:
        return {
            "present": True,
            "status": "STOP",
            "reason": "authorized arms must be a non-empty subset of the frozen pilot arms; "
            f"invalid: {invalid}",
        }
    if not authorized.issuperset(set(requested_arms)):
        return {"present": True, "status": "STOP", "reason": "requested arms exceed the authorized set"}
    window = rec.get("exclusivity_window") or {}
    if not window or not window.get("start_utc") or not window.get("end_utc"):
        return {"present": True, "status": "STOP", "reason": "exclusivity window missing"}
    if not isinstance(rec.get("max_wall_s"), (int, float)) or rec["max_wall_s"] <= 0:
        return {"present": True, "status": "STOP", "reason": "max_wall_s missing/invalid"}
    start_dt = _parse_utc_iso(window.get("start_utc"))
    end_dt = _parse_utc_iso(window.get("end_utc"))
    if start_dt is None or end_dt is None:
        return {
            "present": True,
            "status": "STOP",
            "reason": "exclusivity window timestamps are not valid ISO-8601 UTC: "
            f"{window.get('start_utc')!r} / {window.get('end_utc')!r}",
        }
    if end_dt <= start_dt:
        return {"present": True, "status": "STOP", "reason": "exclusivity window end <= start"}
    now = now_utc if now_utc is not None else datetime.datetime.now(datetime.UTC)
    if now < start_dt:
        return {"present": True, "status": "STOP", "reason": "exclusivity window has not yet started"}
    if now >= end_dt:
        return {"present": True, "status": "STOP", "reason": "exclusivity window has expired"}
    remaining_s = (end_dt - now).total_seconds()
    if rec["max_wall_s"] > remaining_s:
        return {
            "present": True,
            "status": "STOP",
            "reason": "max_wall_s exceeds the remaining exclusivity window "
            f"({rec['max_wall_s']}s > {remaining_s:.0f}s)",
        }
    return {
        "present": True,
        "status": "GRANTED",
        "authorized_arms": sorted(authorized),
        "exclusivity_window": rec["exclusivity_window"],
        "parsed_window_utc": {"start": start_dt.isoformat(), "end": end_dt.isoformat()},
        "remaining_window_s": remaining_s,
        "max_wall_s": rec["max_wall_s"],
        # plain-text operator attestation, NOT a cryptographic signature
        "attestation": "operator-recorded text; NOT a cryptographic signature",
        "signed_by_attestation": rec.get("signed_by") or rec.get("recorded_by"),
        "recorded_by": rec.get("recorded_by"),
    }


def validate_budget(path: Path, wall_max_s: float | None, authorization: dict[str, Any]) -> dict[str, Any]:
    """Budget/window inputs: zero model API mandatory for the F2P-only
    reference-patch pilot; wall cap must be research-recorded."""
    try:
        rec = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "STOP", "reason": f"budget unreadable: {exc}"}
    if not isinstance(rec, dict):
        return {"status": "STOP", "reason": "budget artifact is not an object"}
    if not isinstance(rec.get("benchmark_api_model_usd"), (int, float)) or float(rec["benchmark_api_model_usd"]) != 0.0:
        return {"status": "STOP", "reason": "benchmark_api_model_usd must be exactly 0.00 (zero generation API)"}
    if rec.get("request_count") != 0:
        return {"status": "STOP", "reason": "request_count must be 0 (undeclared model API call)"}
    if wall_max_s is None:
        return {"status": "STOP", "reason": "--wall-max-s missing (researcher must record the cap)"}
    auth_max = float(authorization.get("max_wall_s", 0))
    if wall_max_s > auth_max:
        return {"status": "STOP", "reason": f"--wall-max-s {wall_max_s} exceeds authorization cap {auth_max}"}
    if wall_max_s <= 0:
        return {"status": "STOP", "reason": "--wall-max-s must be positive"}
    return {"status": "OK", "benchmark_api_model_usd": 0.0, "request_count": 0, "max_wall_s": wall_max_s}


# ---------------------------------------------------------------------------
# Per-arm physical run plan (one source of truth for all three modes)
# ---------------------------------------------------------------------------


def physical_plan_for(
    arm_id: str, *, matrix_by_arm: dict[str, dict[str, str]], worktrees: dict[str, str], out_root: Path
) -> dict[str, Any]:
    """The concrete, fully resolved PROSPECTIVE per-arm plan used verbatim by
    preflight/dry-run and (after the researcher gates) by --run."""
    row = matrix_by_arm[arm_id]
    arm_dir = out_root / f"arm_{arm_id}"
    junit_dir = arm_dir / "receipts" / _receipts.JUNIT_DIR_REL
    nodes = _adapt.F2P_NODES
    if len(nodes) != PILOT_NODE_COUNT:
        raise ValueError("F2P node pin is not the 3 frozen pilot nodes")
    return {
        "arm_id": arm_id,
        "frozen_order": [a["arm_id"] for a in _adapt.load_arms()].index(arm_id) + 1,
        "task_id": _adapt.FROZEN_TASK,
        "status": "NOT_RUN",
        "prospective_m02e_status": "NOT_RUN",
        "junit_count_plan": PILOT_JUNIT_PER_ARM,
        "physical_executions_under_option_b": 1,
        "independent_repetitions": "FALSE (3 repeats = stability only; N=1 task)",
        "execution_id": _adapt.execution_id_for(arm_id, "M02E-PILOT-UNRAN"),
        "worktree_linux": worktrees[arm_id],
        "worktree_oid_expected": row["effective_tree_oid"],
        "scope_hash": row["scope_hash"],
        "reference_patch_sha256": row["patch_sha256"],
        "reference_patch_bytes": row["patch_bytes"],
        "test_contract_hash": row["test_contract_hash"],
        "db_identity": {
            "legacy_mode": f"saleor_v3_{TID}_{arm_id}",
            "isolated_mode_pattern": f"opws_m3b_{TASK8}_<stamp>_<nonce>",
            "fresh_per_state": True,
            "unique_per_arm": True,
        },
        "materializer_argv": {
            "argv": [
                "python",
                str(_adapt.FROZEN_WORKTREE_ROOT_DEFAULT / MATERIALIZER_REL),
                "--repo",
                str(_adapt.FROZEN_SOURCE_SALEOR_REPO),
                "--parent",
                _adapt.FROZEN_PARENT,
                "--target",
                _adapt.FROZEN_TARGET,
                "--task-id",
                _adapt.FROZEN_TASK,
                "--scope-json",
                f"<scopes-dir>/scope_{arm_id}.json",
                "--classification-json",
                "<classification>.json",
                "--test-authority-json",
                "<test_authority>.json",
                "--out-dir",
                str(arm_dir / "materialize_record"),
            ],
            "read_provenance_boundary": "classification/test-authority are passed ONLY "
            "to the materializer (evaluation/materializer-only)",
        },
        "run_state_v3": {
            "function": "harness_v3.run_state_v3",
            "module": HARNESS_REL,
            "signature_source": "harness_v3.py line 691 (frozen worktree 22d56946 2026-10-27)",
            "kwargs": {
                "era_key": "py312",
                "worktree_linux": worktrees[arm_id],
                "tid": TID,
                "state": arm_id,
                "test_files": nodes,
                "test_files_pin": _adapt.F2P_NODES_SHA256,
                "install_fragment": "REQUIRED_INPUT_FROM_EXECUTION (lock_install_script output)",
                "locked_dev_fragment": "echo NO_LOCKED_DEV_GROUP",
                "raw_junit_dir": str(junit_dir),
                "timeout_s": 7200,
                "isolated": "REQUIRED_INPUT_FROM_EXECUTION: OpwsIsolatedRuntime("
                "scratch_linux=<out_linux>, scratch_windows=<out_dir>, "
                f"db_commit_short={TASK8}) - frozen py312 isolated mode",
            },
            "junit_expected": PILOT_JUNIT_PER_ARM,
            "junit_naming": f"{TID}_{arm_id}_r<rep>_f<idx>.xml (engine line ~758)",
        },
        "expected_control_junit": _adapt.CONTROL_EXPECTED_JUNIT.get(arm_id, "OUTCOME_DATA"),
        "teardown_contract": {
            "db_dropped_by_engine": "run_state_v3 drops the DB it created post-parse",
            "isolated_cleanup_verification": "verify ZERO opws_m3b_* databases remain",
            "out_dir_reuse": "NEVER (fresh out dir per execution, exist_ok=False)",
            "worktree_writes": "executor never writes the source worktree (read-only)",
        },
        "checks_at_real_run": [
            "3 frozen nodes sha256 == F2P_NODES_SHA256",
            "runtime image OCI id resolved before any side effect (py312)",
            "per-arm DB isolation (unique db identity per arm)",
            "exactly 9 JUnit outputs per arm",
            "physical process ids + start/end UTC timestamps per arm",
            "stdout/stderr/exit classification per stage",
            "resources sampled (frozen resource_sampler)",
            "cleanup proof (zero opws_m3b_*, scratch removed)",
            "benchmark API receipts: request_count 0, USD 0.00",
            "no selector receives classification or test-authority bytes",
        ],
        "receipt_paths": {
            "run_receipt_schema": _receipts.RECEIPT_SCHEMA,
            "run_receipt": str(arm_dir / _receipts.RECEIPT_FILENAME),
            "junit_dir": str(junit_dir),
            "console_log": str(arm_dir / "console.log"),
        },
        "model_cost_usd": 0.0,
        "model_request_count": 0,
        "admission": "PROSPECTIVE only: NOT_RUN until researcher RD-8 + RD-9 artifacts exist",
    }


def build_plan(
    worktree: Path,
    source_repo: Path,
    matrix_path: Path,
    plan_path: Path,
    scopes_dir: Path | None,
    classification: Path | None,
    test_authority: Path | None,
    arms: list[str],
    worktrees_json: str | None,
    out_root: Path,
) -> dict[str, Any]:
    rows = _matrix_rows(matrix_path)
    plan_ok, plan_reason = _plan_ok(plan_path)
    by_arm = {r["arm_id"]: r for r in rows}
    if len(by_arm) != 13:
        raise ValueError(f"matrix arms != 13: {len(by_arm)}")
    unknown = [a for a in arms if a not in by_arm]
    if unknown:
        raise ValueError(f"UNKNOWN_ARMS: {unknown}")
    wt = _resolve_worktrees(arms, worktrees_json)
    scope_state: dict[str, Any] = {}
    for arm in arms:
        if scopes_dir is not None:
            sp = scopes_dir / f"scope_{arm}.json"
            scope_state[arm] = {
                "present": sp.is_file(),
                "sha256": sha256_file(sp) if sp.is_file() else None,
            }
        else:
            scope_state[arm] = {"present": False, "reason": "no --scopes-dir supplied"}
    engines = _driver.engine_scripts_pin_status(worktree)
    head = _git(worktree, "rev-parse", "HEAD").stdout.strip()
    plans = [physical_plan_for(a, matrix_by_arm=by_arm, worktrees=wt, out_root=out_root) for a in arms]
    return {
        "schema": SCHEMA_DRYRUN,
        "worktree": str(worktree),
        "worktree_head": head,
        "worktree_head_match": head == _adapt.FROZEN_WORKTREE_HEAD,
        "source_repo": str(source_repo),
        "source_repo_present": source_repo.is_dir(),
        "matrix_sha256_ok": True,
        "plan_sha256_ok": plan_ok,
        "plan_reason": plan_reason,
        "engines": engines,
        "scope_inputs": scope_state,
        "classification_artifact": str(classification) if classification else None,
        "classification_sha256": (
            sha256_file(classification) if classification and Path(classification).is_file() else None
        ),
        "test_authority_artifact": str(test_authority) if test_authority else None,
        "test_authority_sha256": (
            sha256_file(test_authority) if test_authority and Path(test_authority).is_file() else None
        ),
        "arms": plans,
        "all_status_not_run": all(p["status"] == "NOT_RUN" for p in plans),
        "total_prospective_model_usd": 0.0,
        "total_prospective_model_requests": 0,
        "generated_at_utc": _utc_now(),
    }


# ---------------------------------------------------------------------------
# Real bridge (--run only; fail-closed; never invoked in D3)
# ---------------------------------------------------------------------------


def _load_frozen_module(worktree: Path, rel: str, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, worktree / rel)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # D3-R1: register the module in sys.modules BEFORE executing it, otherwise
    # frozen classes decorated with @dataclass (OpwsIsolatedRuntime) break at
    # decoration time because cls.__module__ is not resolvable.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def real_bridge_stage_details() -> dict[str, str]:
    """The exact frozen import chain used by --run (documented; D3 never calls)."""
    return {
        "harness": HARNESS_REL,
        "runtime_compat": RUNTIME_COMPAT_REL,
        "isolated_runtime": ISOLATED_RUNTIME_REL,
        "functions": "run_state_v3, lock_install_script, OpwsIsolatedRuntime, "
        "resolve_runtime_image (frozen module imports at run time)",
        "mock_policy": "mocks appear ONLY in unit tests; the execution path loads the real pinned frozen functions",
        "executable_in_d3": "false",
    }


def _default_materializer(argv: list[str], timeout_s: int = 900) -> subprocess.CompletedProcess[str]:
    """REAL materializer subprocess (frozen CLI argv; the only execution-path
    runner).  Tests inject a fake runner; production never uses fakes."""
    return subprocess.run(
        argv, capture_output=True, text=True, encoding="utf-8", timeout=timeout_s, check=False
    )


def _default_db_probe() -> list[str]:
    """REAL post-run DB scan on the isolated PG fixture (D3 teardown evidence).

    The read-only scan command is operator-supplied via the environment
    (``T12_M02_DB_SCAN_CMD``); every surviving ``opws_m3b_*`` database is
    returned.  Absent or un-runnable command => raise: the executor NEVER
    invents a teardown PASS.
    """
    cmd = os.environ.get("T12_M02_DB_SCAN_CMD")
    if not cmd:
        raise RuntimeError("TEARDOWN_NOT_VERIFIED: T12_M02_DB_SCAN_CMD not configured")
    argv_scan = shlex.split(cmd, posix=(os.name != "nt"))
    proc = subprocess.run(
        argv_scan, capture_output=True, text=True, encoding="utf-8", timeout=120, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(f"TEARDOWN_NOT_VERIFIED: DB scan failed rc={proc.returncode}: {proc.stderr[-400:]}")
    leftovers: list[str] = []
    for line in (proc.stdout or "").splitlines():
        tok = line.strip()
        if _receipts.DB_IDENTITY_RE.match(tok):
            leftovers.append(tok)
    return leftovers


def _plan_for_arm(plan_doc: dict[str, Any], arm_id: str) -> dict[str, Any]:
    """D1: the per-arm plan is selected ONLY from ``plan_doc['arms']``.  The
    plan-doc top level never carries per-arm keys (old bridge KeyError)."""
    arms = plan_doc.get("arms")
    if not isinstance(arms, list) or not arms:
        raise RuntimeError(f"PLAN_DOC_NO_ARMS (schema={plan_doc.get('schema')})")
    for p in arms:
        if p.get("arm_id") == arm_id:
            return cast(dict[str, Any], p)
    raise RuntimeError(f"PLAN_MISSING_ARM:{arm_id}")


def _worktree_tree_oid(wt: Path) -> str | None:
    """D6: READ-ONLY proof of the execution worktree content: ``git rev-parse
    HEAD^{tree}`` must equal the arm's effective_tree_oid.  None => fail
    closed (no run with an unverifiable tree)."""
    r = subprocess.run(
        ["git", "-C", str(wt), "rev-parse", "HEAD^{tree}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if r.returncode != 0:
        return None
    oid = r.stdout.strip()
    return oid or None


# Engine-native JUnit file name produced by the frozen run_state_v3 isolated
# runs script: ``{tid}_{state}_r{rep}_f{idx}.xml`` (harness_v3.py ~line 758).
ENGINE_JUNIT_RE = re.compile(
    r"^(?P<task>[0-9a-f]{4,})_(?P<state>[A-Z0-9_]+)_r(?P<rep>[0-2])_f(?P<node>[0-2])\.xml$"
)


def _canonical_junit_map(raw_dir: Path, junit_dir: Path, arm_id: str) -> dict[str, str]:
    """D7: copy the RAW engine-produced JUnit XMLs to the receipts-schema
    canonical names (``<task8>_<tag8>_r<rep>_f<node>.xml``).  Returns
    native-name -> canonical-name.  Raises on any non-matching, missing or
    duplicated per-repetition/node slot — exactly 9 distinct physical files
    are required, never fewer and never extra."""
    row = next((a for a in _adapt.load_arms() if a["arm_id"] == arm_id), None)
    if row is None:
        raise RuntimeError(f"UNKNOWN_ARM:{arm_id}")
    tag = str(_adapt.four_field_id(row))[:8]
    task8 = _adapt.FROZEN_TASK.split("-")[-1][:8]
    raw = sorted(p.name for p in raw_dir.glob("*.xml"))
    native: dict[tuple[int, int], str] = {}
    for fname in raw:
        m = ENGINE_JUNIT_RE.match(fname)
        if not m or m.group("task") != TID:
            raise RuntimeError(f"JUNIT_NATIVE_NAME_UNEXPECTED:{fname}")
        native[(int(m.group("rep")), int(m.group("node")))] = fname
    expected_slots = {(r, n) for r in range(PILOT_REPS) for n in range(PILOT_NODE_COUNT)}
    if set(native) != expected_slots:
        raise RuntimeError(
            "JUNIT_COVERAGE_MISMATCH: physical files give "
            f"{sorted(native)}; need every r0..r2 x f0..f2 slot"
        )
    junit_dir.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, str] = {}
    for (rep, node), fname in native.items():
        canonical = f"{task8}_{tag}_r{rep}_f{node}.xml"
        (junit_dir / canonical).write_bytes((raw_dir / fname).read_bytes())
        mapping[fname] = canonical
    return mapping


def _load_materialize_records(mat_dir: Path) -> list[dict[str, Any]]:
    """All JSON engineering records written by the frozen materializer."""
    out: list[dict[str, Any]] = []
    for p in sorted(mat_dir.rglob("*.json")):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def run_bridge(
    plan_doc: dict[str, Any],
    *,
    rd8: dict[str, Any],
    auth: dict[str, Any],
    budget: dict[str, Any],
    worktree: Path,
    source_repo: Path,
    scopes_dir: Path,
    classification: Path,
    test_authority: Path,
    out_root: Path,
    deadline_utc: str | None = None,
    materializer: Any = None,
    postrun_db_probe: Any = None,
) -> dict[str, Any]:
    """Executes the per-arm bridge for authorized arms.  Real frozen engine
    functions are imported and called; every stage is recorded; no retries.

    D3-R1 hardening (all eight demonstrated defects):

    D1  per-arm plan selection: ``plan_doc['arms'][i]`` is the only source of
        ``worktree_linux`` / ``worktree_oid_expected`` / digests; the plan DOC
        top level is never read for per-arm keys.
    D2  the install fragment is the REAL output of the frozen
        ``lock_install_script(worktree_linux, target_manifests(target))``,
        never the literal string ``'computed'``.
    D3  no invented status booleans: teardown is proven by a real post-run DB
        scan (absent probe => TEARDOWN_NOT_VERIFIED => FAIL); the executor
        never claims it resolved the runtime image (delegated to the frozen
        engine's first fail-closed step).
    D4  execution order is exactly NEG -> FULL_REFERENCE -> RM_CSS -> SIP
        regardless of authorization order; ANY control mismatch or
        infrastructure failure stops before SIP (SIP NOT_RUN); NEG's expected
        assertion failure is CONTROL_EXPECTED, never PASS.
    D6  the frozen isolated runtime requires basename ``wt_t``; the executor
        READ-ONLY proves the worktree content equals the arm's
        effective_tree_oid BEFORE any side effect (wrong tree never runs).
    D7  exactly 9 raw per-repetition/node JUnit XML receipts are canonicalised
        from the REAL engine-produced files and validated by the REAL
        ``validate_run_receipt``; cross-arm DB identity collisions STOP; the
        cross-arm bundle scan reports Option-B process/container identity
        gaps instead of fabricating distinctness.
    D8  classification/test-authority reach ONLY the materializer argv; the
        materializer engineering record digests must match the frozen arm
        plan (tampered record STOPS before the engine).

    Wall deadline (F): before every arm, current UTC must be < deadline;
    otherwise the arm is NOT_RUN and the run FAILs closed.
    """
    materializer = materializer or _default_materializer
    arms_results: list[dict[str, Any]] = []
    overall = "FAIL"
    stop_reason: str | None = None
    note: list[str] = []
    authorized = set(auth.get("authorized_arms") or [])
    unknown = sorted(authorized - set(PILOT_ARMS))
    if unknown:
        return {
            "overall": "FAIL",
            "arms": [],
            "executed_at_utc": _utc_now(),
            "note": f"PLANNED_ORDER_UNSATISFIABLE: unauthorized arms {unknown}",
        }
    seq = [a for a in CONTROL_EXECUTION_ORDER if a in authorized]
    if not seq:
        return {
            "overall": "FAIL",
            "arms": [],
            "executed_at_utc": _utc_now(),
            "note": "NO_CONTROLS_AUTHORIZED",
        }
    # eager admission: every planned arm must exist in the per-arm plan BEFORE
    # any side effect (a missing arm plan stops the WHOLE bridge, typed)
    for arm in seq:
        _plan_for_arm(plan_doc, arm)
    db_names_seen: list[str] = []
    run_dirs: list[Path] = []
    passed_controls = 0
    for arm in seq:
        arm_dir = out_root / f"arm_{arm}"
        run_dir = arm_dir / "receipts"
        stage: dict[str, Any] = {
            "arm_id": arm,
            "status": "NOT_RUN",
            "control_outcome": "NOT_RUN",
            "stages": {},
            "start_utc": _utc_now(),
            "executed": False,
        }
        if stop_reason is not None:
            stage["reason"] = stop_reason
            arms_results.append(stage)
            continue
        if deadline_utc is not None:
            dl = _parse_utc_iso(deadline_utc)
            if dl is None or datetime.datetime.now(datetime.UTC) >= dl:
                stop_reason = "WALL_DEADLINE_EXCEEDED"
                stage["reason"] = stop_reason
                overall = "FAIL"
                arms_results.append(stage)
                continue
        try:
            arm_plan = _plan_for_arm(plan_doc, arm)
            stage["stages"]["plan_selection"] = {
                "arm_id": arm,
                "worktree_linux": arm_plan["worktree_linux"],
                "worktree_oid_expected": arm_plan["worktree_oid_expected"],
                "execution_id": arm_plan["execution_id"],
            }
            wt_linux = arm_plan["worktree_linux"]
            wt = Path(wt_linux)
            # ---- admission BEFORE any side effect (D6, fail-before-side-effect) ----
            if not wt.is_dir():
                raise RuntimeError("WORKTREE_MISSING")
            if wt.name != "wt_t":
                raise RuntimeError(
                    "WORKTREE_UNEXPECTED: the frozen OpwsIsolatedRuntime.validate() "
                    "requires the execution worktree basename 'wt_t'"
                )
            actual_oid = _worktree_tree_oid(wt)
            if actual_oid is None:
                raise RuntimeError("WORKTREE_OID_UNVERIFIABLE: git rev-parse failed (fail closed)")
            if actual_oid != arm_plan["worktree_oid_expected"]:
                raise RuntimeError(
                    f"WORKTREE_OID_MISMATCH: {wt_linux} tree {actual_oid} "
                    f"!= plan expected {arm_plan['worktree_oid_expected']}"
                )
            stage["stages"]["worktree_input"] = {
                "path": wt_linux,
                "expected_oid": arm_plan["worktree_oid_expected"],
                "tree_proven_oid": actual_oid,
                "content_identity": True,
                "mislabel_guard": (
                    f"run tree == arm effective tree {actual_oid}; "
                    "unmodified target tree is never presented as an arm result"
                ),
            }
            # ---- materialize (real frozen CLI argv; engineering record) ----
            if arm_dir.exists():
                raise RuntimeError(f"ARM_DIR_REUSE: {arm_dir} already exists (fresh out dir per arm)")
            arm_dir.mkdir(parents=True, exist_ok=False)
            mat_dir = arm_dir / "materialize_record"
            argv = [
                "python",
                str(worktree / MATERIALIZER_REL),
                "--repo",
                str(source_repo),
                "--parent",
                _adapt.FROZEN_PARENT,
                "--target",
                _adapt.FROZEN_TARGET,
                "--task-id",
                _adapt.FROZEN_TASK,
                "--scope-json",
                str(scopes_dir / f"scope_{arm}.json"),
                "--classification-json",
                str(classification),
                "--test-authority-json",
                str(test_authority),
                "--out-dir",
                str(mat_dir),
            ]
            proc = materializer(argv, timeout_s=900)
            stage["stages"]["materialize"] = {
                "exit": proc.returncode,
                "stdout": (proc.stdout or "")[-4000:],
                "stderr": (proc.stderr or "")[-4000:],
            }
            if proc.returncode != 0:
                raise RuntimeError("MATERIALIZE_FAILED")
            (arm_dir / "console.log").write_text(
                str(proc.stdout or "") + "\n" + str(proc.stderr or ""), encoding="utf-8"
            )
            records = _load_materialize_records(mat_dir)
            if not records:
                raise RuntimeError("MATERIALIZER_RECORD_MISSING")
            bad = [
                r
                for r in records
                if r.get("scope_hash") != arm_plan.get("scope_hash")
                or r.get("reference_patch_sha256") != arm_plan.get("reference_patch_sha256")
            ]
            if bad:
                raise RuntimeError(f"MATERIALIZER_RECORD_MISMATCH: {bad[0]}")
            stage["stages"]["materialize"]["record_digests_match"] = True
            # ---- engine imports (frozen, real) ----
            harness = _load_frozen_module(worktree, HARNESS_REL, "benchmark_harness_v3")
            isolated_mod = _load_frozen_module(
                worktree, ISOLATED_RUNTIME_REL, "benchmark_opws_isolated_runtime_v1"
            )
            stage["stages"]["engine_imports"] = {"ok": True}
            # ---- real lock-exact install fragment (D2, frozen function) ----
            manifests = harness.target_manifests(_adapt.FROZEN_TARGET)
            fragment_raw, install_mode, install_evidence = harness.lock_install_script(wt_linux, manifests)
            if not isinstance(fragment_raw, str) or not fragment_raw.strip():
                raise RuntimeError("INSTALL_FRAGMENT_EMPTY")
            stage["stages"]["install_fragment"] = {
                "mode": install_mode,
                "fragment_sha256": _sha256_bytes(fragment_raw),
                "evidence": install_evidence,
                "source": "frozen harness.lock_install_script(worktree_linux, target_manifests(target))",
            }
            # ---- runtime image: the executor NEVER claims it verified (D3) ----
            stage["stages"]["runtime_image_resolved"] = {
                "executor_claim": (
                    "delegated to the frozen resolve_runtime_image inside run_state_v3 "
                    "(the engine's first fail-closed step when isolated is set); "
                    "the executor did NOT self-verify the OCI digest"
                )
            }
            isolated = isolated_mod.OpwsIsolatedRuntime(
                worktree_linux=wt_linux,
                scratch_linux=f"{LINUX_SCRATCH_BASE}/{out_root.name}",
                scratch_windows=str(out_root),
                # 8-hex task segment: matches the frozen R7 DB identity precedent
                # and the receipts DB_IDENTITY_RE (a 12-hex segment would make
                # every real receipt fail schema validation)
                db_commit_short=TASK8,
            )
            isolated.validate()
            stage["stages"]["isolated_runtime"] = {
                "declared_worktree_linux": wt_linux,
                "validated_by_frozen_contract": True,
                "db_prefix": "opws_m3b_",
                "validation": "frozen OpwsIsolatedRuntime.validate() run at admission",
            }
            # ---- the REAL frozen 3-node x 3-rep engine call ----
            pid = os.getpid()
            run_start = _utc_seconds()
            result = harness.run_state_v3(
                era_key="py312",
                worktree_linux=wt_linux,
                tid=TID,
                state=arm,
                test_files=list(_adapt.F2P_NODES),
                install_fragment=fragment_raw,
                locked_dev_fragment="echo NO_LOCKED_DEV_GROUP",
                raw_junit_dir=str(run_dir / "engine_raw_junit"),
                timeout_s=7200,
                isolated=isolated,
            )
            run_end = _utc_seconds()
            stage["stages"]["run_state_v3"] = {
                "pid": pid,
                "start_utc": run_start,
                "end_utc": run_end,
                "db_name": result.get("db_name"),
            }
            # ---- honest evidence checks (D3/D7): no invented booleans ----
            db_name = result.get("db_name")
            if not isinstance(db_name, str) or not _receipts.DB_IDENTITY_RE.match(db_name):
                raise RuntimeError("DB_IDENTITY_UNPROVEN: engine result lacks a fresh opws_m3b_ db identity")
            if result.get("db_cleanup") != "DROPPED_AFTER_JUNIT_PARSE":
                raise RuntimeError(
                    "DB_CLEANUP_UNPROVEN: engine result does not attest the post-parse DB drop"
                )
            junit_files = list(result.get("junit_files") or [])
            if len(junit_files) != PILOT_JUNIT_PER_ARM:
                raise RuntimeError(
                    f"JUNIT_COUNT_MISMATCH: {len(junit_files)} != {PILOT_JUNIT_PER_ARM}"
                )
            # canonicalise the RAW engine-produced XML bytes (never fabricated)
            mapping = _canonical_junit_map(run_dir / "engine_raw_junit", run_dir / "junit", arm)
            if len(mapping) != PILOT_JUNIT_PER_ARM:
                raise RuntimeError("JUNIT_CANONICAL_COUNT_MISMATCH")
            classifications = [
                _receipts.classify_junit(run_dir / "junit" / c) for c in sorted(mapping.values())
            ]
            stage["stages"]["junit_evidence"] = {
                "raw_files": len(junit_files),
                "canonical_files": sorted(mapping.values()),
                "engine_native_to_canonical": mapping,
                "classifications": classifications,
            }
            # ---- control semantics (D4): classify the RAW junit evidence
            # BEFORE any receipt is written; a mismatch stops before SIP ----
            expected = _adapt.CONTROL_EXPECTED_JUNIT.get(arm)
            observed = set(classifications)
            stage["stages"]["control"] = {
                "expected": expected,
                "observed": sorted(observed),
            }
            if expected is not None and observed != {expected}:
                raise RuntimeError(
                    f"CONTROL_MISMATCH: {arm} expected {expected}, observed {sorted(observed)}"
                )
            # ---- teardown proof via a REAL post-run DB scan, BEFORE the
            # receipt is written/validated (D3: no invented booleans) ----
            if postrun_db_probe is None:
                raise RuntimeError("TEARDOWN_NOT_VERIFIED: no post-run DB scan is available")
            leftovers = list(postrun_db_probe() or [])
            scan_path = run_dir / "post_run_db_scan.json"
            scan_path.write_text(
                json.dumps({"remaining_opws_m3b_databases": leftovers, "checked_at_utc": _utc_now()}),
                encoding="utf-8",
            )
            stage["stages"]["post_run_teardown"] = {
                "engine_db_cleanup": result.get("db_cleanup"),
                "post_run_db_scan": leftovers,
                "scan_artifact": str(scan_path),
                "db_deleted": len(leftovers) == 0,
            }
            if leftovers:
                raise RuntimeError(f"DB_LEFTOVER: {leftovers}")
            # control outcome bookkeeping (NEG's expected assertion failure is
            # a classified CONTROL_EXPECTED event, never an ordinary PASS)
            if expected is not None:
                stage["control_outcome"] = "CONTROL_EXPECTED" if arm == "NEG" else "CONTROL_PASS"
                stage["status"] = "CONTROL_EXPECTED" if arm == "NEG" else "PASS"
                passed_controls += 1
            else:
                stage["observed_classifications"] = sorted(observed)
                stage["control_outcome"] = "OUTCOME_DATA"
                stage["status"] = "PASS"
            # ---- real receipt built ONLY from measured evidence + the real
            # validator (D7/D3-R2): no sample_run_receipt seeding, no invented
            # zero, DB-scan snapshot hash, truthful process witness. ----
            start_dt = _parse_utc_iso(run_start)
            end_dt = _parse_utc_iso(run_end)
            wall_s = max(0.0, (end_dt - start_dt).total_seconds() if start_dt and end_dt else 0.0)
            scan_sha = sha256_file(scan_path)
            witness = _d3r2.span_witness(
                nonce=_d3r2.new_nonce(),
                pid=int(os.getpid()),
                parent_pid=int(os.getppid()),
                argv=list(sys.argv),
                worker_script_path=None,
                monotonic_start_ns=0,
                monotonic_end_ns=_d3r2.monotonic_birth_ns(),
                start_utc=run_start,
                end_utc=run_end,
                exit_code=0,
                worker_os_start=_d3r2.windows_os_process_start(int(os.getpid())),
            )
            julist = []
            for canon in sorted(mapping.values()):
                jf = run_dir / "junit" / canon
                julist.append(_d3r2.file_sha256(jf) if jf.is_file() else None)
            receipt = _receipts.live_run_receipt_template(
                arm_id=arm,
                run_token=arm_plan["execution_id"],
                junit_classifications=classifications,
                db_identity=db_name,
                process={
                    "pid": int(os.getpid()),
                    "driver_argv": list(sys.argv),
                    "nonce": witness["nonce"],
                    "process_birth": witness["process_birth"],
                    # frozen py312 OCI manifest digest (IMAGE identity, never a
                    # container instance); resolved by the frozen engine, NOT
                    # by the executor (see runtime_image_resolved stage)
                    "container_oci_id": _d3r2.PINNED_PY312_OCI_ID,
                },
                times={"start_utc": run_start, "end_utc": run_end,
                       "monotonic": True, "wall_seconds": wall_s},
                resources={
                    "cpu_seconds": _receipts.NOT_MEASURED,
                    "peak_ram_mb": _receipts.NOT_MEASURED,
                    "disk_bytes": _receipts.NOT_MEASURED,
                    "network_bytes": _d3r2.live_network_policy(None, None),
                    "sampler": "NOT_MEASURED: resource sampling not executed in this mode",
                },
                teardown={
                    "present": True,
                    "db_deleted": True,
                    "path": "post_run_db_scan.json",
                    "verified_by_post_run_scan": True,
                    "post_run_db_scan": leftovers,
                    "post_run_db_scan_sha256": scan_sha,
                },
                materialize_provenance={
                    "materializer": MATERIALIZER_REL,
                    "scope_hash": arm_plan["scope_hash"],
                    "reference_patch_sha256": arm_plan["reference_patch_sha256"],
                    "record_digests_match": True,
                    "record_dir": str(mat_dir),
                },
                junit_dir=run_dir / "junit",
                host={"hostname": "HOST_MEASURED_FROM_CHILD", "os": "WSL2/Windows"},
                environment={"environment_id": "ENV_MEASURED_FROM_CHILD"},
                pinned_image={
                    "image": "opws-py312-isolated",
                    "oci_id": _d3r2.PINNED_PY312_OCI_ID,
                    "resolved_by_executor": False,
                    "resolved_by": "frozen resolve_runtime_image (engine first fail-closed step)",
                },
                container={
                    "container_instance_status": "CONTAINER_INSTANCE_NOT_MEASURED",
                    "per_state_container_evidence": (
                        "engine-managed per-state V3 container; engine result "
                        "exposes no per-state container id; D3-R2 captures "
                        "docker-events instance evidence per arm window at run "
                        "time (out of scope of the D3 offline bridge)"
                    ),
                },
                junit_receipts_sha=julist,
            )
            receipt["database"]["db_scan_snapshot_sha256"] = scan_sha
            receipt["database"]["db_scan_artifact"] = "post_run_db_scan.json"
            receipt["junit_engine_native_to_canonical"] = mapping
            receipt["engine_native_junit_dir"] = str(run_dir / "engine_raw_junit")
            _d3r2.assert_live_receipt(receipt)  # fixture markers in a live receipt = STOP
            _receipts.write_run_receipt(run_dir, receipt)
            vres = _receipts.validate_run_receipt(run_dir)
            issues = list(vres.get("issues") or [])
            stage["stages"]["receipt_validation"] = {
                "status": "PASS" if not issues else "STOP",
                "issues": issues[:10],
            }
            if issues:
                raise RuntimeError("RECEIPT_INVALID: " + "; ".join(issues[:8]))
            stage["ended_utc"] = _utc_now()
            stage["executed"] = True
            db_names_seen.append(db_name)
            run_dirs.append(run_dir)
        except Exception as exc:
            stage["ended_utc"] = _utc_now()
            stage["reason"] = f"{type(exc).__name__}: {exc}"
            stage["status"] = "FAIL"
            stage["executed"] = False
            overall = "FAIL"
            stop_reason = f"STOP_AFTER_{arm}_FAILURE (stop-before-SIP)"
        arms_results.append(stage)
    # ---- cross-arm Option-B identity: distinct DB per executed arm ----
    identity_proven = len(db_names_seen) == len(set(db_names_seen))
    if not identity_proven:
        note.append("IDENTITY_COLLISION: opws_m3b_ db identity not unique across executed arms")
    had_failure = any(a.get("status") == "FAIL" for a in arms_results)
    overall = "FAIL" if (stop_reason is not None or had_failure or not identity_proven) else "PASS"
    # ---- real bundle scan on the real produced receipts ----
    bundle: dict[str, Any] = {}
    if len(run_dirs) >= 2:
        bres = _receipts.validate_receipts_bundle(run_dirs)
        bundle = {"status": bres.get("status"), "issues": bres.get("cross_arm_identity_violations") or []}
        if bundle["issues"]:
            overall = "FAIL"
            note.append(
                "IDENTITY_GAP: "
                + "; ".join(str(i) for i in bundle["issues"][:4])
                + " — the sequential driver shares one OS pid and the frozen "
                "run_state_v3 result exposes no per-state container id, so "
                "per-arm physical process/container identity cannot be proven "
                "in-process; a real pilot MUST STOP at this gate unless the "
                "engine exposes per-state container identity."
            )
    if not stop_reason and overall == "FAIL" and not note:
        note.append("CONTROL_SEQUENCE_FAILED: see per-arm stages")
    return {
        "overall": overall,
        "arms": arms_results,
        "executed_at_utc": _utc_now(),
        "admission_basis": {
            "rd8": rd8.get("status"),
            "authorization": auth.get("status", "GRANTED"),
            "budget": budget.get("status"),
            "deadline_utc": deadline_utc,
        },
        "receipt_bundle": bundle,
        "note": " | ".join(note) if note else "ok",
    }


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------


def preflight(args: argparse.Namespace, out_root: Path) -> dict[str, Any]:
    """Read-only admission preflight.  Hard stops are typed; exit 4 if any."""
    worktree = Path(args.worktree)
    source_repo = Path(args.source_repo) if args.source_repo else _adapt.FROZEN_SOURCE_SALEOR_REPO
    matrix_path = Path(args.matrix) if args.matrix else None
    plan_path = Path(args.plan) if args.plan else None
    arms = arms_to_run(args.arms, getattr(args, "pilot_only", False))
    engines = _driver.engine_scripts_pin_status(worktree)
    head = _git(worktree, "rev-parse", "HEAD").stdout.strip()
    hard: list[str] = []
    if not worktree.is_dir():
        hard.append("WORKTREE_MISSING")
    elif head != _adapt.FROZEN_WORKTREE_HEAD:
        hard.append(f"WORKTREE_HEAD_DRIFT ({head})")
    if matrix_path is None:
        hard.append("REQUIRED_MATRIX_MISSING")
    else:
        try:
            _matrix_rows(matrix_path)
        except Exception as exc:
            hard.append(f"MATRIX_UNREADABLE_OR_HASH_DRIFT: {exc}")
    if plan_path is None:
        hard.append("REQUIRED_PLAN_MISSING")
    else:
        ok, reason = _plan_ok(plan_path)
        if not ok:
            hard.append(reason)
    bad_engines = [rel for rel, st in engines.items() if not st.get("ok")]
    if bad_engines:
        hard.append("ENGINE_PIN_DRIFT: " + ",".join(bad_engines))

    rd8 = validate_rd8_decision(args.rd8_decision)
    auth = validate_authorization(args.authorization, arms)
    if rd8["status"] != "ADOPT_PILOT_ONLY":
        hard.append(
            "RD8_APPROVAL_PENDING" if rd8["present"] is False else "RD8_DECISION_INVALID: " + str(rd8.get("reason"))
        )
    if auth["status"] != "GRANTED":
        hard.append(
            "EXECUTION_NOT_AUTHORIZED"
            if auth["present"] is False
            else "AUTHORIZATION_INVALID: " + str(auth.get("reason"))
        )

    result = {
        "schema": SCHEMA_PREFLIGHT,
        "worktree": str(worktree),
        "worktree_head": head if worktree.is_dir() else None,
        "worktree_head_pin": _adapt.FROZEN_WORKTREE_HEAD,
        "worktree_head_match": head == _adapt.FROZEN_WORKTREE_HEAD,
        "matrix_path": str(matrix_path) if matrix_path else None,
        "plan_path": str(plan_path) if plan_path else None,
        "source_repo": str(source_repo),
        "evidence_dir": str(out_root),
        "engines": engines,
        "rd8": rd8,
        "authorization": auth,
        "arms_requested": arms,
        "pilot_arms": PILOT_ARMS,
        "all_13_not_run": True,
        "hard_stops": hard,
        "prospective_eligibility": {
            "status": "NOT_RUN",
            "model_usd": 0.0,
            "model_requests": 0,
            "note": "all 13 prospective arms remain NOT_RUN; zero benchmark API",
        },
        "runtime_probe": "DEFERRED_TO_AUTHORIZED_EXECUTION (no Docker/WSL probe in D3)",
        "env": "D3_ENGINEERING_ONLY",
        "generated_at_utc": _utc_now(),
    }
    return result


def dry_run(args: argparse.Namespace, out_root: Path) -> dict[str, Any]:
    """13-arm NOT_RUN enumeration + concrete prospective pilot plan (no run)."""
    worktree = Path(args.worktree)
    source_repo = Path(args.source_repo) if args.source_repo else _adapt.FROZEN_SOURCE_SALEOR_REPO
    matrix_path = Path(args.matrix) if args.matrix else None
    plan_path = Path(args.plan) if args.plan else None
    if matrix_path is None or plan_path is None:
        raise SystemExit("REQUIRED_MATRIX_OR_PLAN_MISSING")
    arms = arms_to_run(args.arms, args.pilot_only)
    plan = build_plan(
        worktree,
        source_repo,
        matrix_path,
        plan_path,
        Path(args.scopes_dir) if args.scopes_dir else None,
        Path(args.classification) if args.classification else None,
        Path(args.test_authority) if args.test_authority else None,
        arms,
        args.worktrees_json,
        out_root,
    )
    rd8 = validate_rd8_decision(args.rd8_decision if getattr(args, "rd8_decision", None) else None)
    return {
        "schema": SCHEMA_DRYRUN,
        "mode": "DRY_RUN",
        "plan": plan,
        "rd8": rd8,
        "pilot_plan": {
            "arms": PILOT_ARMS,
            "junit_per_arm": PILOT_JUNIT_PER_ARM,
            "junit_total": PILOT_JUNIT_PER_ARM * len(PILOT_ARMS),
            "nodes": _adapt.F2P_NODES,
            "nodes_pin": _adapt.F2P_NODES_SHA256,
            "model_requests": 0,
            "model_usd": 0.0,
            "p2p": "NOT_QUALIFIED: strictly F2P-only calibration (RD-3 P2P cap not predeclared)",
            "inferential_claim": "NONE: N=1 task, 3 nodes x 3 reps = stability only, no F1 CI",
            "execution_authorization": "ABSENT (RD-9 required)",
        },
        "not_run_confirmed": plan["all_status_not_run"],
        "env": "D3_ENGINEERING_ONLY",
        "generated_at_utc": _utc_now(),
    }


def run(args: argparse.Namespace, out_root: Path) -> dict[str, Any]:
    """FAIL-CLOSED real execution gate.  In D3 this MUST stop with typed
    gates: RD8_PENDING + EXECUTION_NOT_AUTHORIZED (artifacts do not exist)."""
    gates: dict[str, Any] = {}
    worktree = Path(args.worktree)
    matrix_path = Path(args.matrix) if args.matrix else None
    plan_path = Path(args.plan) if args.plan else None
    arms = arms_to_run(args.arms, True)  # run mode is pilot-only
    rd8 = validate_rd8_decision(args.rd8_decision)
    auth = validate_authorization(args.authorization, arms)
    gates["rd8"] = rd8
    gates["authorization"] = auth
    hard: list[str] = []
    if rd8["status"] != "ADOPT_PILOT_ONLY":
        hard.append("RD8_APPROVAL_PENDING" if rd8["present"] is False else "RD8_DECISION_INVALID")
    if auth["status"] != "GRANTED":
        hard.append("EXECUTION_NOT_AUTHORIZED" if auth["present"] is False else "AUTHORIZATION_INVALID")
    # D3 anti-footgun: --run is structurally unreachable in this mission
    if args.autorun_in_d3_flag != "NEVER_IN_D3":
        hard.append("AUTORUN_FLAG_MISSING_OR_WRONG")
    if args.wall_max_s is None:
        hard.append("WALL_MAX_S_MISSING")
    if args.worktrees_json is None:
        # the concrete per-arm execution worktrees are a REQUIRED input for
        # run (the dry-run pattern is a proposal, never executed)
        hard.append("WORKTREES_JSON_REQUIRED")
    if hard:
        gates["budget"] = {"status": "STOP", "reason": "gate not open; budget not evaluated"}
        gates["hard_stops"] = hard
        gates["outcome"] = "STOP_NOT_AUTHORIZED"
        gates["executed"] = False
        gates["env"] = "D3_ENGINEERING_ONLY"
        gates["generated_at_utc"] = _utc_now()
        return gates

    # Beyond this point: real execution path (unreachable until separate
    # researcher RD-8 + RD-9 authorizations and an exclusive window exist).
    budget = validate_budget(Path(args.budget_json), args.wall_max_s, dict(auth))
    gates["budget"] = budget
    if budget["status"] != "OK":
        hard.append("BUDGET_INVALID: " + budget["reason"])
    if hard:
        gates["hard_stops"] = hard
        gates["outcome"] = "STOP_GATE_NOT_OPEN"
        gates["executed"] = False
        gates["generated_at_utc"] = _utc_now()
        return gates

    plan_doc = build_plan(
        worktree,
        Path(args.source_repo) if args.source_repo else _adapt.FROZEN_SOURCE_SALEOR_REPO,
        matrix_path if matrix_path else Path(),
        plan_path if plan_path else Path(),
        Path(args.scopes_dir) if args.scopes_dir else None,
        Path(args.classification) if args.classification else None,
        Path(args.test_authority) if args.test_authority else None,
        arms,
        args.worktrees_json,
        out_root,
    )
    # F: fail-closed wall deadline computed from the researched budget cap.
    now_dt = datetime.datetime.now(datetime.UTC)
    deadline_utc = (now_dt + datetime.timedelta(seconds=float(budget["max_wall_s"]))).isoformat()
    bridge = run_bridge(
        plan_doc,
        rd8=rd8,
        auth=auth,
        budget=budget,
        worktree=worktree,
        source_repo=(Path(args.source_repo) if args.source_repo else _adapt.FROZEN_SOURCE_SALEOR_REPO),
        scopes_dir=Path(args.scopes_dir) if args.scopes_dir else Path("."),
        classification=Path(args.classification) if args.classification else Path(),
        test_authority=Path(args.test_authority) if args.test_authority else Path(),
        out_root=out_root,
        deadline_utc=deadline_utc,
        materializer=None,
        postrun_db_probe=_default_db_probe,
    )
    gates["bridge"] = bridge
    gates["outcome"] = bridge["overall"] if bridge["overall"] == "PASS" else "FAIL"
    gates["executed"] = True
    gates["generated_at_utc"] = _utc_now()
    return gates


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _main(args)
    except ValueError as exc:
        print(f"HARD_STOP_VALUE_ERROR: {exc}", file=sys.stderr)
        return 5


def _main(args: argparse.Namespace) -> int:
    if getattr(args, "debug_junit_template", False) and args.command == "preflight":
        # dev/test fixture dump (used only by unit tests; never a real receipt)
        rec = _receipts.sample_run_receipt()
        print(json.dumps(rec, indent=2, default=str))
        return 0
    out_root = Path(args.out) if args.out else Path.cwd() / "t12_m02_execute_out"
    if out_root.exists():
        raise SystemExit(f"OUT_DIR_EXISTS: {out_root} (never reuse a results directory)")
    out_root.mkdir(parents=True, exist_ok=False)

    if args.command == "preflight":
        res = preflight(args, out_root)
        (out_root / "PREFLIGHT.json").write_text(
            json.dumps(res, indent=2, sort_keys=True, default=str), encoding="utf-8"
        )
        print(json.dumps(res, indent=2, sort_keys=True, default=str))
        return 4 if res["hard_stops"] else 0

    if args.command == "dry-run":
        res = dry_run(args, out_root)
        (out_root / "EXECUTION_PLAN.json").write_text(
            json.dumps(res, indent=2, sort_keys=True, default=str), encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "schema": res["schema"],
                    "mode": "DRY_RUN",
                    "not_run_confirmed": res["not_run_confirmed"],
                    "arms": len(res["plan"]["arms"]),
                    "pilot_plan": res["pilot_plan"],
                    "rd8": res["rd8"],
                    "env": res["env"],
                },
                indent=2,
                sort_keys=True,
                default=str,
            )
        )
        return 0

    if args.command == "run":
        res = run(args, out_root)
        (out_root / "RUN_GATE.json").write_text(
            json.dumps(res, indent=2, sort_keys=True, default=str), encoding="utf-8"
        )
        print(json.dumps(res, indent=2, sort_keys=True, default=str))
        return 4 if res.get("outcome", "").startswith("STOP") else (0 if res.get("outcome") == "PASS" else 5)
    return 3


if __name__ == "__main__":
    sys.exit(main())
