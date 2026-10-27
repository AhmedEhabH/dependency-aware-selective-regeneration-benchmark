#!/usr/bin/env python3
"""T12 M02-D2 — EXACT prospective F2P call contract (OFFLINE plan-only, stdlib).

Mission: T12_M02_D2_INPUT_CONTRACT_20261027 (Track 1.2), Task 3.

PURPOSE
-------
Produce, per arm, the EXACT prospective per-arm/one-task execution-plan ONLY
from source-confirmed interface semantics of the frozen engine:

* ``harness_v3.run_state_v3`` — keyword-only callable (line 691-703):
  ``(era_key, worktree_linux, tid, state, test_files, install_fragment,
  locked_dev_fragment='echo NO_LOCKED_DEV_GROUP', raw_junit_dir=None,
  timeout_s=7200, isolated=None)``; docstring: "One V3 container per state:
  fresh unique DB + lock-exact install + --ulimit nofile=65536, then 3x per
  changed-test-file."  With ``isolated`` set, the frozen py312 pilot runs in
  the dedicated internal-bridge runtime (``_run_state_v3_isolated``).
* The per-state fresh DB naming: ``fresh_db_name(task_id, state)`` (line 482)
  = ``saleor_v3_<12char>_<state>``; the isolated mode receipts use
  ``opws_m3b_<task8>_<stamp>_<nonce>`` (m3b smoke receipts).
* JUnit naming inside the container: ``{tid}_{state}_r{rep}_f{idx}.xml``
  (line ~758) -> 3 reps x 3 frozen F2P nodes = 9 JUnit per arm.
* The frozen 3 F2P nodes (R7 pin ``aa12d546...``) and REPETITIONS=3
  (arm_adapter F2P_NODES / F2P_REPETITIONS).
* Teardown contract: run_state_v3 drops the DB it created; the m3b smoke
  verifies ZERO ``opws_m3b_*`` databases remain after the run (lines 353-357,
  455-463, 475-483).

THE m3b SMOKE CLI is a SINGLE-node, TARGET-ONLY harness: it hardcodes
``SMOKE_TEST_NODE`` + ``TID`` and never reads argument positionals (source
lines 514-545 + opws_isolated_runtime_v1).  It therefore CANNOT execute the
pilot's 3-node x 3-repeat contract per arm — calling it with a task id is a
NO-OP on the argument.  The minimally provable offline wrapper for the pilot
contract is this module: it renders the exact ``run_state_v3`` call per arm
with the 3 frozen nodes and per-arm identities.  It has NO run mode:
 ``executable: false`` everywhere; values that can only exist after the
materialize/execution step are declared REQUIRED_INPUT_FROM_* with their
frozen producer, never fabricated.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("t12_m02_arm_adapter", _SCRIPTS / "t12_m02_arm_adapter.py")
assert _spec is not None and _spec.loader is not None
_adapt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_adapt)

SCHEMA = "t12_m02_f2p_invocation_plan_v1"
MATERIALIZER_REL = "scripts/opws_phase3b_patch_materialize.py"
HARNESS_REL = "src/benchmark/wp2/harness_v3.py"
M3B_SMOKE_REL = "scripts/wp2_m3b_runner_smoke.py"

# Frozen contract facts (source-verified 2026-10-27)
ERA_KEY = "py312"
TID = "7e42fc67ce72"
TIMEOUT_S = 7200
LOCKED_DEV_FRAGMENT = "echo NO_LOCKED_DEV_GROUP"

# m3b smoke contract (single node, target-only; NOT the 3-node pilot contract)
SMOKE_NODE_COUNT = 1
SMOKE_JUNIT_COUNT = 3  # 1 node x REPS=3


def f2p_plan_for(arm_id: str, *, out_root: Path | None = None,
                 node_list: list[str] | None = None,
                 run_token: str = "NOT_AUTHORIZED") -> dict[str, Any]:
    """Render the exact prospective run_state_v3 call plan for one arm.

    ``node_list`` defaults to the frozen F2P_NODES pin; ``run_token`` only
    affects the deterministic execution id.  Values that depend on a future
    materialize/execute step are labeled REQUIRED_INPUT_FROM_<producer>.
    """
    arms = [a for a in _adapt.load_arms() if a["arm_id"] == arm_id]
    if not arms:
        raise ValueError(f"UNKNOWN_ARM: {arm_id}")
    nodes = node_list if node_list is not None else _adapt.F2P_NODES
    if sorted(nodes) != sorted(_adapt.F2P_NODES):
        raise ValueError("NODE_LIST_MISMATCH: node list must equal the frozen F2P_NODES pin")
    reps = _adapt.F2P_REPETITIONS
    junit_count = len(nodes) * reps

    arm_dir = (out_root / f"arm_{arm_id}") if out_root else None
    raw_junit_dir = str(arm_dir / "receipts") if arm_dir else "REQUIRED_INPUT_FROM_DRIVER"

    return {
        "schema": SCHEMA,
        "arm_id": arm_id,
        "task_id": _adapt.FROZEN_TASK,
        "executable": False,
        "run_mode": "OFFLINE_DRY_RUN_PLAN_ONLY",
        "execution_id": _adapt.execution_id_for(arm_id, run_token),
        "run_token": run_token,
        "engine": {
            "function": "harness_v3.run_state_v3",
            "module": HARNESS_REL,
            "signature_source": "src/benchmark/wp2/harness_v3.py line 691 (read-only 2026-10-27)",
            "call_contract": {
                "era_key": ERA_KEY,
                "worktree_linux": "REQUIRED_INPUT_FROM_MATERIALIZE_STEP: path of the arm's "
                                  "materialized reference tree inside the Linux runtime "
                                  "(frozen pattern e.g. /root/m19b_r3_20261024/wt_t)",
                "tid": TID,
                "state": arm_id,
                "test_files": nodes,
                "test_files_pin": _adapt.F2P_NODES_SHA256,
                "install_fragment": "REQUIRED_INPUT_FROM_EXECUTION: output of frozen "
                                    "harness_v3.lock_install_script() at run time "
                                    "(m3b smoke line 575)",
                "locked_dev_fragment": LOCKED_DEV_FRAGMENT,
                "raw_junit_dir": raw_junit_dir,
                "timeout_s": TIMEOUT_S,
                "isolated": "REQUIRED_INPUT_FROM_EXECUTION: OpwsIsolatedRuntime("
                            "scratch_linux=out_linux, scratch_windows=out_dir, "
                            "db_commit_short=TID) — frozen py312 isolated mode "
                            "(m3b smoke lines 580-584; opws_isolated_runtime_v1.py)",
            },
        },
        "physical_execution_contract": {
            "option_b": "REUSE_NOT_PERMITTED: distinct physical arm execution, DBs, "
                        "receipts, wall/resource measurements",
            "db_identity": {
                "legacy_mode": f"saleor_v3_{TID}_{arm_id} (fresh_db_name, harness_v3 line 482)",
                "isolated_mode": f"opws_m3b_{TID}_<stamp>_<nonce> (isolated runtime receipts)",
                "fresh_per_state": True,
                "unique_per_arm": True,
            },
            "junit_count_plan": junit_count,
            "junit_naming": f"{TID}_{arm_id}_r<rep>_f<idx>.xml (harness_v3 line 758)",
            "repetitions": reps,
            "physical_test_invocations": junit_count,
            "nodes_count": len(nodes),
            "independent_repetitions": "FALSE (3 repeats = stability only; 1 research task)",
        },
        "teardown_contract": {
            "db_dropped_by_engine": "run_state_v3 drops the DB it created (fresh per state)",
            "isolated_cleanup_verification": "zero opws_m3b_* databases remain "
                                             "(m3b smoke lines 353-357/455-463)",
            "out_dir_reuse": "NEVER: fresh out_dir per execution (exist_ok=False; "
                             "m3b smoke line 530)",
        },
        "receipt_paths": {
            "run_receipt_schema": "t12_m02_run_receipt_v1 (scripts/t12_m02_receipts.py)",
            "junit_dir": raw_junit_dir,
            "log": str(arm_dir / "console.log") if arm_dir else "REQUIRED_INPUT_FROM_DRIVER",
        },
        "m3b_smoke_limitation": {
            "smoke_argv": f"python {M3B_SMOKE_REL} --dry-run [positional args IGNORED]",
            "smoke_nodes": SMOKE_NODE_COUNT,
            "smoke_junit": SMOKE_JUNIT_COUNT,
            "why_not_pilot_contract": "m3b smoke hardcodes SMOKE_TEST_NODE + TID and "
                                      "never parses argv positionals (lines 514-545); "
                                      "the 3-node/3-repeat pilot contract is planned "
                                      "here via run_state_v3 with the 3 frozen nodes",
        },
        "admission_note": "NOT_AUTHORIZED: no execution admission exists in this mission; "
                          "engineering contract closure only.",
    }


def render_materializer_argv(arm_id: str, *, worktree: Path, source_repo: Path,
                             scope_artifacts_dir: Path | None,
                             classification_artifact: Path | None,
                             test_authority_artifact: Path | None) -> dict[str, Any]:
    """Exact materializer argv for the arm under D2 (dry-run-safe; never executed)."""
    arms = [a for a in _adapt.load_arms() if a["arm_id"] == arm_id]
    if not arms:
        raise ValueError(f"UNKNOWN_ARM: {arm_id}")
    if scope_artifacts_dir is not None:
        scope_json = str(scope_artifacts_dir / f"scope_{arm_id}.json")
    else:
        scope_json = "REQUIRED_INPUT_FROM_SCOPE_NORMALIZER"
    argv = [
        "python", str(worktree / MATERIALIZER_REL),
        "--repo", str(source_repo),
        "--parent", _adapt.FROZEN_PARENT,
        "--target", _adapt.FROZEN_TARGET,
        "--task-id", _adapt.FROZEN_TASK,
        "--scope-json", scope_json,
        "--classification-json", str(classification_artifact or "REQUIRED_INPUT_FROM_RD8_DERIVATION"),
        "--dry-run",
    ]
    if test_authority_artifact is not None:
        argv += ["--test-authority-json", str(test_authority_artifact)]
    return {
        "arm_id": arm_id,
        "materializer": MATERIALIZER_REL,
        "argv": argv,
        "dry_run_only": True,
        "executable": False,
        "note": "argv built only from frozen parser (lines 1151-1164) + D2-normalized inputs",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="t12_m02_f2p_contract",
        description="Offline exact F2P invocation-plan renderer (no run mode).")
    ap.add_argument("--arms", default=None, help="comma-separated arms (default: all 13)")
    ap.add_argument("--out", default=None, help="output directory for <arm>_f2p_plan.json")
    ap.add_argument("--nodes", default=None, help="comma-separated node list (default frozen pin)")
    args = ap.parse_args(argv)

    nodes = args.nodes.split(",") if args.nodes else None
    arms = args.arms.split(",") if args.arms else [a["arm_id"] for a in _adapt.load_arms()]
    if nodes is not None and sorted(nodes) != sorted(_adapt.F2P_NODES):
        print(f"STOP:NODE_LIST_MISMATCH (frozen pin {_adapt.F2P_NODES_SHA256[:16]}...)",
              file=sys.stderr)
        return 3
    out_root = Path(args.out) if args.out else None
    plans = []
    for arm in arms:
        plans.append(f2p_plan_for(arm, out_root=out_root, node_list=nodes,
                                  run_token="NOT_AUTHORIZED"))
        if out_root is not None:
            (out_root / f"f2p_plan_{arm}.json").write_text(
                json.dumps(plans[-1], sort_keys=True, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
    print(json.dumps(plans, sort_keys=True, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
