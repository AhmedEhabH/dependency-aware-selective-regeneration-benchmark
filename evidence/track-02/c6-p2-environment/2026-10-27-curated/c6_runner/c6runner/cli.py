# -*- coding: utf-8 -*-
"""C6 runner CLI (fail-closed, plan-bound).

Usage (operator): every executable detail comes from ONE task plan file whose
canonical SHA-256 must equal the value bound in the operator authorization
receipt for that task. The CLI accepts NO free-form command/test-path/resource/
network overrides:

  python -m c6runner.cli --freeze <FREEZE.json> --authorization <AUTH.json>
      --plan <TASK_PLAN.json> [--preflight] [--dry-run] [--out-dir OUT]

Read-only diagnostics:
  python -m c6runner.cli --isolation-check
"""
import argparse
import json
import os
import sys
import time

from .errors import C6Stop
from .runner import C6Runner
from .taskplan import TaskPlan, TaskPlanError

DEFAULT_GIT_DIR = r"D:\wp2_env_store\git_cache\saleor.git"
DEFAULT_LEDGER = r"D:\WP2\audit_results\TRACK02_WPB_C4_EVIDENCE_V2\C1_C5_PER_SHA.jsonl"
DEFAULT_H2 = r"D:\WP2\audit_results\FULL_HISTORY_V2_H2_20261026T115058\D0_FILE_EVENTS.jsonl"
DEFAULT_PROTECTED = r"D:\WP2\audit_results\TRACK02_CE_WPB_C4_C5_20261027T024421Z\protected_source_cache"
HERE = os.path.dirname(os.path.abspath(__file__))


def load_frozen_inputs(path):
    """Load the frozen-input manifest (schema c6-frozen-inputs-v2).

    Returns (frozen {path: sha256}, roles {role: path}). The `roles` section
    binds the ACTUAL git store / ledger / H2 events / protected cache / this
    manifest itself. A v1 manifest WITHOUT roles is refused by the CLI
    (finding F6): the execution inputs must be bound to the frozen contract.
    """
    doc = json.load(open(path, encoding="utf-8"))
    frozen = {v["path"]: v["sha256"] for v in doc.values()
              if isinstance(v, dict) and v.get("path") and v.get("sha256")}
    roles = dict(doc.get("roles") or {})
    return frozen, roles


def main(argv=None):
    ap = argparse.ArgumentParser(prog="c6runner")
    ap.add_argument("--freeze", default=None)
    ap.add_argument("--authorization", default=None)
    ap.add_argument("--plan", default=None,
                    help="task plan JSON (canonical sha must equal the "
                         "authorization-bound binding)")
    ap.add_argument("--preflight", action="store_true",
                    help="verify inputs+eligibility+identity WITHOUT running")
    ap.add_argument("--dry-run", action="store_true",
                    help="authorized run but skip the actual command")
    ap.add_argument("--frozen-inputs",
                    default=os.path.join(os.path.dirname(HERE), "frozen_inputs.json"))
    ap.add_argument("--git-dir", default=DEFAULT_GIT_DIR)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--h2-events", default=DEFAULT_H2)
    ap.add_argument("--protected-cache", default=DEFAULT_PROTECTED)
    ap.add_argument("--out-dir", default="runs")
    ap.add_argument("--isolation-check", action="store_true",
                    help="probe and print OS isolation backends; no run")
    ap.add_argument("--plan-sha", default=None, metavar="PLAN.json",
                    help="print the canonical SHA-256 of a task plan (used by "
                         "the operator to bind plan_sha256 into the auth receipt)")
    args = ap.parse_args(argv)

    if args.plan_sha:
        try:
            plan = TaskPlan.from_dict(json.load(open(args.plan_sha, encoding="utf-8")))
        except (OSError, json.JSONDecodeError, KeyError, TypeError, TaskPlanError) as e:
            print("C6_STOP: PLAN_MALFORMED |", e)
            return 3
        print(plan.canonical_sha256())
        return 0

    if args.isolation_check:
        from . import isolation as _iso
        backends = _iso.detect_backends()
        print("C6_ISOLATION_CHECK")
        for name in sorted(backends):
            print(f"{name}: {json.dumps(backends[name].as_dict())}")
        print("RESULT:", "AVAILABLE" if backends else "NONE")
        return 3 if not backends else 0

    if not (args.freeze and args.authorization and args.plan):
        print("C6_STOP: NOT_AUTHORIZED | freeze, authorization AND plan "
              "are all required (no free-form overrides are accepted)")
        print("LAST_STEP: pre-construction")
        return 3

    try:
        plan = TaskPlan.from_dict(json.load(open(args.plan, encoding="utf-8")))
    except (OSError, json.JSONDecodeError, KeyError, TypeError, TaskPlanError) as e:
        print("C6_STOP: PLAN_MALFORMED |", e)
        print("LAST_STEP: plan parse")
        return 3

    frozen_inputs, roles = load_frozen_inputs(args.frozen_inputs)
    if not roles:
        print("C6_STOP: INPUT_BINDING_MANIFEST | the frozen-input manifest "
              "(schema c6-frozen-inputs-v2) must declare `roles` binding the "
              "actual git store / ledger / H2 events / protected cache paths; "
              "free-form source substitution is not accepted")
        print("LAST_STEP: manifest roles")
        return 3
    roles = dict(roles)
    roles["frozen_manifest"] = os.path.abspath(args.frozen_inputs)
    if os.path.normcase(os.path.abspath(args.frozen_inputs)) != \
            os.path.normcase(os.path.abspath(
                roles.get("frozen_manifest"))):
        print("C6_STOP: INPUT_BINDING_MISMATCH | frozen-input manifest")
        print("LAST_STEP: manifest binding")
        return 3
    try:
        runner = C6Runner(
            freeze_path=args.freeze,
            auth_path=args.authorization,
            git_dir=args.git_dir,
            ledger_path=args.ledger,
            h2_events_path=args.h2_events,
            protected_cache_dir=args.protected_cache,
            out_root=os.path.abspath(args.out_dir),
            frozen_inputs=frozen_inputs,
            input_roles=roles,
        )
    except C6Stop as e:
        print("C6_STOP:", e.classification, "|", e.detail)
        print("LAST_STEP: pre-construction")
        return 3

    t0 = time.monotonic()
    try:
        result = runner.run_task(plan.task, plan=plan,
                                 preflight_only=args.preflight,
                                 dry_run=args.dry_run)
        elapsed = time.monotonic() - t0
        print("VERDICT:", result["verdict"].value)
        print("RECEIPT:", result["receipt_path"])
        print("WORKSPACE:", result["workspace"])
        print("ELAPSED_S:", round(elapsed, 2))
        return 0
    except C6Stop as e:
        print("C6_STOP:", e.classification, "|", e.detail)
        print("LAST_STEP:", e.context or "pre-execution")
        return 3
    except Exception as e:  # noqa: BLE001
        print("C6_ERROR:", type(e).__name__, "|", e)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())