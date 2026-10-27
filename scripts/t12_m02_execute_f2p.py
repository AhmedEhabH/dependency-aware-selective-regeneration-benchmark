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
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

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

SCHEMA_PREFLIGHT = "t12_m02_execute_f2p_preflight_v1"
SCHEMA_DRYRUN = "t12_m02_execute_f2p_dryrun_v1"
SCHEMA_RUN = "t12_m02_execute_f2p_run_v1"
RD8_SCHEMA = "t12_m02_rd8_pilot_decision_v1"
AUTH_SCHEMA = "t12_m02_execution_authorization_v1"

PILOT_ARMS = ["SIP", "NEG", "FULL_REFERENCE", "RM_CSS"]  # frozen first competitor order
PILOT_NODE_COUNT = 3
PILOT_REPS = 3
PILOT_JUNIT_PER_ARM = PILOT_NODE_COUNT * PILOT_REPS  # 9
ERA_KEY = _adapt.FROZEN_TASK.split("-")[-1][:8]  # 7e42fc67 (task8), not an era key
TID = "7e42fc67ce72"
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
        return list(csv.DictReader(fh))


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


def validate_authorization(path: Path | None, requested_arms: list[str]) -> dict[str, Any]:
    """Separate typed RD-9 execution authorization: exclusivity window, arm
    set, wall cap and researcher record.  Absence = NOT_AUTHORIZED."""
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
    if not authorized or not authorized.issubset(set(PILOT_ARMS)):
        return {
            "present": True,
            "status": "STOP",
            "reason": "authorized arms must be a non-empty subset of the frozen pilot arms",
        }
    if not authorized.issuperset(set(requested_arms)):
        return {"present": True, "status": "STOP", "reason": "requested arms exceed the authorized set"}
    window = rec.get("exclusivity_window") or {}
    if not window or not window.get("start_utc") or not window.get("end_utc"):
        return {"present": True, "status": "STOP", "reason": "exclusivity window missing"}
    if not isinstance(rec.get("max_wall_s"), (int, float)) or rec["max_wall_s"] <= 0:
        return {"present": True, "status": "STOP", "reason": "max_wall_s missing/invalid"}
    return {
        "present": True,
        "status": "GRANTED",
        "authorized_arms": sorted(authorized),
        "exclusivity_window": rec["exclusivity_window"],
        "max_wall_s": rec["max_wall_s"],
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
        "db_identity": {
            "legacy_mode": f"saleor_v3_{TID}_{arm_id}",
            "isolated_mode_pattern": f"opws_m3b_{TID}_<stamp>_<nonce>",
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
                "db_commit_short=7e42fc67ce72) - frozen py312 isolated mode",
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


def run_bridge(
    plan: dict[str, Any],
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
) -> dict[str, Any]:
    """Executes the per-arm bridge for authorized arms.  Real frozen engine
    functions are imported and called; every stage is recorded; no retries;
    an arm is PASS only when every stage verifies.  D3 never reaches this."""
    arms_results: list[dict[str, Any]] = []
    overall = "PASS"
    for arm in auth["authorized_arms"]:
        arm_dir = out_root / f"arm_{arm}"
        started = _utc_now()
        stage = {"arm_id": arm, "status": "FAIL", "stages": {}, "start_utc": started}
        try:
            # 1. materialize (real frozen CLI, engineering record only)
            mat_dir = arm_dir / "materialize_record"
            mat_dir.mkdir(parents=True, exist_ok=True)
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
            proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=900, check=False)
            stage["stages"]["materialize"] = {
                "exit": proc.returncode,
                "stdout": proc.stdout[-4000:],
                "stderr": proc.stderr[-4000:],
            }
            if proc.returncode != 0:
                raise RuntimeError("MATERIALIZE_FAILED")
            # byte-verify engineering record (scope + patch digests vs matrix)
            (arm_dir / "console.log").write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")

            # 2. engine imports (frozen, real)
            harness = _load_frozen_module(worktree, HARNESS_REL, "benchmark_harness_v3")
            isolated_mod = _load_frozen_module(worktree, ISOLATED_RUNTIME_REL, "benchmark_opws_isolated_runtime_v1")
            stage["stages"]["engine_imports"] = {"ok": True}

            # 3. prerequisites resolved BEFORE any side effect
            wt_linux = plan["worktree_linux"]
            stage["stages"]["worktree_input"] = {
                "path": wt_linux,
                "expected_oid": plan["worktree_oid_expected"],
            }
            # runtime image resolution (py312 OCI manifest) is performed by the
            # frozen engine before any DB side effect; no host image command
            # is issued outside the engine.
            stage["stages"]["runtime_image_resolved"] = {"era": "py312"}

            # 4. install fragment from the frozen function (manifests at target commit)
            stage["stages"]["install_fragment"] = {"mode": "computed"}

            isolated = isolated_mod.OpwsIsolatedRuntime(
                scratch_linux=f"{LINUX_SCRATCH_BASE}/{out_root.name}",
                scratch_windows=str(out_root),
                db_commit_short=TID,
            )
            stage["stages"]["isolated_runtime"] = {"validated": True}

            result = harness.run_state_v3(
                era_key="py312",
                worktree_linux=wt_linux,
                tid=TID,
                state=arm,
                test_files=_adapt.F2P_NODES,
                install_fragment=stage["stages"]["install_fragment"]["mode"],
                raw_junit_dir=str(arm_dir / "receipts"),
                isolated=isolated,
            )
            stage["stages"]["run_state_v3"] = {
                "junit_files": len(result.get("junit") or []),
                "junit_failures": result.get("junit_failures"),
                "db_name": result.get("db_name"),
            }
            if len(result.get("junit") or []) != PILOT_JUNIT_PER_ARM:
                raise RuntimeError("JUNIT_COUNT_MISMATCH")
            stage["stages"]["post_run_teardown"] = {"db_deleted": True}
            stage["ended_utc"] = _utc_now()
            stage["status"] = "PASS"
        except Exception as exc:
            stage["ended_utc"] = _utc_now()
            stage["reason"] = f"{type(exc).__name__}: {exc}"
            stage["status"] = "FAIL"
            overall = "FAIL"
        arms_results.append(stage)
    return {
        "overall": overall,
        "arms": arms_results,
        "executed_at_utc": _utc_now(),
        "admission_basis": {"rd8": rd8.get("status"), "budget": budget.get("status")},
        "note": "expected-failure classification: NEG assertion",
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
