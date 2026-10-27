#!/usr/bin/env python3
"""T12 M02-D1 — minimal per-arm F2P/P2P driver feasibility (PRE-FLIGHT + DRY-RUN ONLY).

Mission: T12_M02_D1_20261027 (Track 1.2), Task 5.

WHAT THIS IS
------------
A provable, minimal orchestration driver for the frozen M02-E pipeline composed
EXCLUSIVELY from real, frozen, source-verified interfaces (read-only): the
patch materializer ``opws_phase3b_patch_materialize.py``, the F2P engine
``harness_v3.run_state_v3``/``wp2_m3b_runner_smoke.py``, and the P2P engine
``wp2_p2p_u_v2_exec.py``.  Each argv/callable contract was verified by reading
the frozen sources on 2026-10-27 (see DRIVER_FEASIBILITY.md).

THIS DRIVER RUNS NOTHING.  It provides:
  * ``preflight`` — admission-style verification that the frozen worktree,
    per-arm byte-pinned scope sources, source git repo (parent/target OIDs),
    engine scripts and test nodes are all present and matching, per arm;
  * ``dry-run``   — the deterministic per-arm command plan (all NOT_RUN) and
    the DRY_RUN_MANIFEST.csv (13 rows, all NOT_RUN, USD 0.00).

There is intentionally NO ``run`` subcommand and no mock: if any needed
API/fixture/path cannot be proven, preflight says so with a typed STOP:
  * REQUIRED_WORKTREE_MISSING / PIN_DRIFT        — frozen worktree problems
  * SCOPE_SOURCE_MISSING / SCOPE_PIN_DRIFT       — per-arm frozen scope inputs
  * SOURCE_REPO_MISSING / OID_UNRESOLVED         — materializer --repo input
  * ENGINE_SCRIPT_MISSING / ENGINE_HASH_DRIFT    — frozen runner scripts
  * RD8_DERIVATION_PENDING_RESEARCHER_APPROVAL  — the classification input
    is DERIVED offline from the frozen parent->target diff (M02-D2) and
    byte-pinned, but the NEW artifact waits for researcher RD-8 approval;
    EXECUTION_NOT_AUTHORIZED keeps every arm NOT_RUN.

Exit codes: 0 PASS (preflight/dry-run ok) | 4 typed STOP | 3 usage.
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "t12_m02_arm_adapter", _SCRIPTS / "t12_m02_arm_adapter.py")
assert _spec is not None and _spec.loader is not None
_adapt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_adapt)

SCHEMA = "t12_m02_driver_v1"
MATERIALIZER_REL = "scripts/opws_phase3b_patch_materialize.py"
M3B_SMOKE_REL = "scripts/wp2_m3b_runner_smoke.py"
P2P_EXEC_REL = "scripts/wp2_p2p_u_v2_exec.py"
HARNESS_REL = "src/benchmark/wp2/harness_v3.py"

MANIFEST_HEADER = [
    "frozen_order", "arm_id", "task_id", "effective_tree_oid", "scope_hash",
    "scope_source", "scope_pin_sha256", "scope_pin_status",
    "classification_input", "materialize_engine", "materialize_inputs",
    "f2p_execution_engine", "f2p_driver", "p2p_engine",
    "junit_count_plan", "expected_control_junit", "prospective_m02e_status",
    "prospective_model_usd", "execution_id",
]


def _git_oid_exists(repo: Path, oid: str) -> bool:
    if not repo.is_dir():
        return False
    r = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{oid}^{{commit}}"],
        capture_output=True, text=True, check=False)
    return r.returncode == 0


def engine_scripts_pin_status(worktree: Path) -> dict:
    out: dict[str, Any] = {}
    for rel, pin in _adapt.STAGE_HASH_PINS.items():
        fp = worktree / rel
        if not fp.is_file():
            out[rel] = {"ok": False, "reason": "ENGINE_SCRIPT_MISSING"}
            continue
        dig = _adapt.sha256_file(fp)
        out[rel] = {"ok": dig == pin, "reason": "OK" if dig == pin else "ENGINE_HASH_DRIFT"}
    for rel in (M3B_SMOKE_REL, P2P_EXEC_REL):
        fp = worktree / rel
        out.setdefault(rel, {"ok": fp.is_file(),
                             "reason": None if fp.is_file() else "ENGINE_SCRIPT_MISSING"})
    return out


def arm_preflight_status(arm_id: str, _worktree: Path, scope_base: Path | None) -> dict:
    pin = _adapt.resolve_scope_source(arm_id, base=scope_base)
    if pin["kind"] == "DERIVED_CONTROL":
        return {"arm_id": arm_id, "scope_status": "DERIVED_CONTROL", "stop": None}
    if not pin["present"]:
        return {"arm_id": arm_id, "scope_status": "SCOPE_SOURCE_MISSING",
                "stop": "SCOPE_SOURCE_MISSING", "path": pin["path"]}
    if not pin["match"]:
        return {"arm_id": arm_id, "scope_status": "SCOPE_PIN_DRIFT",
                "stop": "SCOPE_PIN_DRIFT", "path": pin["path"]}
    return {"arm_id": arm_id, "scope_status": "PIN_MATCH", "stop": None,
            "path": pin["path"], "sha256": pin.get("sha256")}


def preflight(worktree: Path, source_repo: Path | None = None,
              matrix_path: Path | None = None,
              plan_path: Path | None = None,
              _route_path: Path | None = None,
              admission_required: bool = True,
              classification_artifact: Path | None = None,
              test_authority_artifact: Path | None = None) -> dict:
    """Driver admission preflight: per-arm + engine + repo + frozen pins."""
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "worktree": str(worktree),
        "worktree_present": worktree.is_dir(),
        "worktree_head": None,
        "worktree_head_match": None,
        "engines": {},
        "per_arm": [],
        "source_repo": str(source_repo) if source_repo else None,
        "source_repo_oid_ok": None,
        "classification_input": _adapt.CLASSIFICATION_INPUT_STATUS,
        "classification_artifact": str(classification_artifact) if classification_artifact else None,
        "test_authority_artifact": str(test_authority_artifact) if test_authority_artifact else None,
        "hard_stops": [],
        "generated_utc": datetime.datetime.now(datetime.UTC).isoformat(),
    }
    result["input_contract_status"] = "INPUT_CONTRACT_ENGINEERING_PROVEN_RD8_ARTIFACTS_NOT_YET_GENERATED"
    result["runner_integration_gap"] = None  # M02-D2: gap CLOSED (derivation provable)
    if not worktree.is_dir():
        result["hard_stops"] = ["REQUIRED_WORKTREE_MISSING", "EXECUTION_NOT_AUTHORIZED"]
        result["admission_ready"] = False
        result["exit_code"] = 4
        return result
    result["worktree_head"] = _adapt.resolve_git_head(worktree)
    result["worktree_head_match"] = result["worktree_head"] == _adapt.FROZEN_WORKTREE_HEAD
    result["engines"] = engine_scripts_pin_status(worktree)
    src = source_repo or _adapt.FROZEN_SOURCE_SALEOR_REPO
    result["source_repo"] = str(src)
    result["source_repo_oid_ok"] = (
        _git_oid_exists(src, _adapt.FROZEN_PARENT)
        and _git_oid_exists(src, _adapt.FROZEN_TARGET))
    per_arm = []
    for arm in _adapt.load_arms():
        st = arm_preflight_status(arm["arm_id"], worktree, None)
        per_arm.append(st)
    result["per_arm"] = per_arm
    hard: list[str] = []
    if not result["worktree_head_match"]:
        hard.append("FROZEN_WORKTREE_DRIFT")
    for rel, st in result["engines"].items():
        if not st["ok"]:
            hard.append(f"{rel}:{st['reason']}")
    if not result["source_repo_oid_ok"]:
        hard.append("SOURCE_REPO_MISSING_OR_OID_UNRESOLVED")
    if admission_required:
        if matrix_path is None:
            hard.append("REQUIRED_MATRIX_MISSING")
        elif not _adapt.check_matrix_file(matrix_path)[0]:
            hard.append("MATRIX_HASH_MISMATCH")
        if plan_path is None:
            hard.append("REQUIRED_PLAN_MISSING")
        elif not _adapt.check_plan_file(plan_path)[0]:
            hard.append("PLAN_HASH_MISMATCH")
    for st in per_arm:
        if st["stop"]:
            hard.append(f"{st['arm_id']}:{st['stop']}")
    # M02-D2: the classification/test-authority inputs are DERIVED offline and
    # byte-pinned (PROPOSED_NEW_DERIVATION_PENDING_RESEARCHER_RD8_APPROVAL).
    # Engineering closure is PROVEN; execution is still NOT authorized: the
    # preflight STOPs with the researcher decision + missing-autorization.
    if classification_artifact is not None:
        if not classification_artifact.is_file():
            hard.append("RD8_CLASSIFICATION_ARTIFACT_MISSING")
        elif test_authority_artifact is None or not test_authority_artifact.is_file():
            hard.append("RD8_TEST_AUTHORITY_ARTIFACT_MISSING")
        else:
            result["input_contract_status"] = "INPUT_CONTRACT_READY_FOR_RESEARCHER_REVIEW"
    if admission_required:
        hard.append("RD8_DERIVATION_PENDING_RESEARCHER_APPROVAL")
        hard.append("EXECUTION_NOT_AUTHORIZED")
    else:
        hard.append("EXECUTION_NOT_AUTHORIZED")
    result["hard_stops"] = hard
    result["admission_ready"] = not hard
    result["exit_code"] = 4 if hard else 0
    return result


def dry_run_rows(_worktree: Path, source_repo: Path | None = None,
                 scope_artifacts_dir: Path | None = None,
                 classification_artifact: Path | None = None,
                 test_authority_artifact: Path | None = None) -> list[dict]:
    """Deterministic per-arm command plan.  All rows NOT_RUN; no execution.

    The materializer argv uses the D2-normalized per-arm ``scope_<arm>.json``
    (the ONLY materializer-schema object) plus the derived classification /
    test-authority artifacts when provided; otherwise each placeholder is a
    real typed marker, never invented.  The m3b smoke line remains the frozen
    CLI verbatim (positionals ignored) with an explicit note that the 3-node
    pilot contract is planned via ``run_state_v3`` (see f2p_contract module).
    """
    src = source_repo or _adapt.FROZEN_SOURCE_SALEOR_REPO
    rows = []
    has_rd8 = (classification_artifact is not None and classification_artifact.is_file()
               and test_authority_artifact is not None and test_authority_artifact.is_file())
    for arm in _adapt.load_arms():
        pin = _adapt.resolve_scope_source(arm["arm_id"])
        if pin["kind"] == "DERIVED_CONTROL":
            scope_json = pin["source"]
            scope_status = "DERIVED_CONTROL"
        elif scope_artifacts_dir is not None and (scope_artifacts_dir / f"scope_{arm['arm_id']}.json").is_file():
            # D2: materializer-ready per-arm scope-json (normalized, single task)
            scope_json = str(scope_artifacts_dir / f"scope_{arm['arm_id']}.json")
            scope_status = "NORMALIZED_MATERIALIZER_READY"
        elif pin["present"] and pin["match"]:
            scope_json = f"<NOT_MATERIALIZER_READY:{pin['path']}>"
            scope_status = "PIN_MATCH_BUT_MULTI_TASK_SOURCE"
        else:
            scope_json = f"<UNRESOLVED:{pin['reason']}>"
            scope_status = pin["reason"] or "SCOPE_SOURCE_MISSING"
        cls_json = (str(classification_artifact) if has_rd8
                    else "<PROPOSED_DERIVATION_RD8_APPROVAL_PENDING>")
        mat_cmd = [
            "python", MATERIALIZER_REL,
            "--repo", str(src),
            "--parent", _adapt.FROZEN_PARENT,
            "--target", _adapt.FROZEN_TARGET,
            "--task-id", _adapt.FROZEN_TASK,
            "--scope-json", scope_json,
            "--classification-json", cls_json,
            "--dry-run",
        ]
        if has_rd8:
            mat_cmd += ["--test-authority-json", str(test_authority_artifact)]
        # Frozen CLI verbatim (argparse has NO optionals beyond --dry-run/
        # --verify-only; positionals are ignored): kept to show the provable
        # part; the 3-node pilot contract is planned through run_state_v3 in
        # scripts/t12_m02_f2p_contract.py (executable=false).
        f2p_cmd = [
            "python", M3B_SMOKE_REL,
            "--dry-run",
            f"{_adapt.FROZEN_TASK}",
        ]
        p2p_cmd = [
            "python", P2P_EXEC_REL, "--task", _adapt.FROZEN_TASK,
            "--cap", "<200|400 RESEARCHER_DECISION>", "--dry-run",
        ]
        rows.append({
            "frozen_order": arm["frozen_order"],
            "arm_id": arm["arm_id"],
            "task_id": _adapt.FROZEN_TASK,
            "effective_tree_oid": arm["effective_tree_oid"],
            "scope_hash": arm["scope_hash"],
            "scope_source": pin.get("source"),
            "scope_pin_sha256": pin.get("sha256"),
            "scope_pin_status": scope_status,
            "classification_input": _adapt.CLASSIFICATION_INPUT_STATUS,
            "materialize_engine": "AVAILABLE",
            "materialize_inputs": ("MATERIALIZE_INPUTS_DERIVED"
                                   if pin["kind"] == "DERIVED_CONTROL" else
                                   ("MATERIALIZE_INPUTS_FROZEN_SCOPE_NORMALIZED"
                                    if scope_status == "NORMALIZED_MATERIALIZER_READY" else
                                    ("MATERIALIZE_INPUTS_FROZEN_SOURCE_NOT_NORMALIZED"
                                     if scope_status == "PIN_MATCH_BUT_MULTI_TASK_SOURCE"
                                     else "MATERIALIZE_INPUTS_UNRESOLVED"))),
            "materialize_dry_run_cmd": " ".join(mat_cmd),
            "f2p_execution_engine": "run_state_v3 (fresh unique DB, 3x per changed test file)",
            "f2p_driver": ("PILOT_CONTRACT_PLANNED_VIA_RUN_STATE_V3 (f2p_contract module "
                           "render; executable=false); m3b smoke is single-node only"),
            "f2p_dry_run_cmd": " ".join(f2p_cmd),
            "p2p_engine": "wp2_p2p_u_v2_exec.py --task --cap 200|400",
            "p2p_dry_run_cmd": " ".join(p2p_cmd),
            "junit_count_plan": _adapt.JUNIT_COUNT_PER_ARM_PILOT,
            "expected_control_junit": _adapt.CONTROL_EXPECTED_JUNIT.get(arm["arm_id"], "UNKNOWN"),
            "prospective_m02e_status": "NOT_RUN",
            "prospective_model_usd": 0.0,
            "execution_id": _adapt.execution_id_for(arm["arm_id"], "M02E-D2-DRYRUN-NOTAUTHORIZED"),
        })
    return rows


def write_manifest_csv(out_path: Path, rows: list[dict]) -> None:
    import csv
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=MANIFEST_HEADER, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="T12 M02-D1 minimal driver (preflight + dry-run only).")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("preflight", help="admission preflight (fail-closed typed STOPs)")
    p.add_argument("--worktree", default=str(_adapt.FROZEN_WORKTREE_ROOT_DEFAULT))
    p.add_argument("--source-repo", default=None)
    p.add_argument("--matrix", default=None)
    p.add_argument("--plan", default=None)
    p.add_argument("--classification", default=None, help="D2 derived classification JSON")
    p.add_argument("--test-authority", default=None, help="D2 derived test-authority JSON")
    p.add_argument("--admission-required", action="store_true")
    p = sub.add_parser("dry-run", help="deterministic per-arm NOT_RUN plan")
    p.add_argument("--worktree", default=str(_adapt.FROZEN_WORKTREE_ROOT_DEFAULT))
    p.add_argument("--source-repo", default=None)
    p.add_argument("--scopes", default=None, help="D2 scope artifacts dir (scope_<arm>.json)")
    p.add_argument("--classification", default=None, help="D2 derived classification JSON")
    p.add_argument("--test-authority", default=None, help="D2 derived test-authority JSON")
    p.add_argument("--out", default=None, help="write DRY_RUN_MANIFEST.csv")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "preflight":
        res = preflight(Path(args.worktree),
                        Path(args.source_repo) if args.source_repo else None,
                        Path(args.matrix) if args.matrix else None,
                        Path(args.plan) if args.plan else None,
                        admission_required=args.admission_required,
                        classification_artifact=(
                            Path(args.classification) if getattr(args, "classification", None) else None),
                        test_authority_artifact=(
                            Path(args.test_authority) if getattr(args, "test_authority", None) else None))
        print(json.dumps(res, indent=2, default=str))
        if res["hard_stops"]:
            return 4
        return 0
    if args.command == "dry-run":
        rows = dry_run_rows(Path(args.worktree),
                            Path(args.source_repo) if args.source_repo else None,
                            Path(args.scopes) if getattr(args, "scopes", None) else None,
                            Path(args.classification) if getattr(args, "classification", None) else None,
                            Path(args.test_authority) if getattr(args, "test_authority", None) else None)
        for r in rows:
            print(f"{r['frozen_order']:>2} {r['arm_id']:<26} "
                  f"scope={r['scope_pin_status']:<18} "
                  f"inputs={r['materialize_inputs']:<26} "
                  f"status={r['prospective_m02e_status']} junit={r['junit_count_plan']}")
        if args.out:
            write_manifest_csv(Path(args.out), rows)
            print(f"WROTE_MANIFEST {args.out} ({len(rows)} rows, all NOT_RUN)")
        return 0
    return 3


if __name__ == "__main__":
    sys.exit(main())
