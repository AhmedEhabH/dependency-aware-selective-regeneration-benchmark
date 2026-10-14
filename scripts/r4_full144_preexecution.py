#!/usr/bin/env python3
"""M17_D7_R4_FULL144_PREEXECUTION_FREEZE — Full144 preexecution CLI.

PRE-EXECUTION QUALIFICATION ONLY: this mission prepares and freezes the
canonical Full D7 144-unit execution.  It does NOT execute any Full-D7 unit.

Usage:
  python scripts/r4_full144_preexecution.py --preflight
  python scripts/r4_full144_preexecution.py --verify-images
  python scripts/r4_full144_preexecution.py --readiness
  python scripts/r4_full144_preexecution.py --contingency
  python scripts/r4_full144_preexecution.py --host-safety
  python scripts/r4_full144_preexecution.py --freeze
  # Future execution gate (NOT launched here):
  python scripts/r4_full144_preexecution.py --unit N
  python scripts/r4_full144_preexecution.py --next
  python scripts/r4_full144_preexecution.py --aggregate
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from benchmark.wp2.full144 import driver, population  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="M17_D7_R4 Full144 preexecution freeze")
    ap.add_argument("--preflight", action="store_true", help="population + binding authority gate")
    ap.add_argument("--verify-images", action="store_true", help="11/11 local image binding check")
    ap.add_argument("--readiness", action="store_true", help="write readiness manifest (PRE6)")
    ap.add_argument("--contingency", action="store_true", help="write contingency matrix (PRE8)")
    ap.add_argument("--host-safety", action="store_true", help="host/disk observations (PRE7)")
    ap.add_argument("--freeze", action="store_true", help="write PRE_EXECUTION_FREEZE.json (PRE9)")
    ap.add_argument("--unit", type=int, default=None, help="run exactly one unit (1..144)")
    ap.add_argument("--next", action="store_true", help="run next uncompleted unit (future gate)")
    ap.add_argument("--aggregate", action="store_true", help="Full-D7 144/144 aggregate")
    args = ap.parse_args()

    try:
        driver.configure_runner()

        if args.preflight:
            pop = population.validate_population()
            driver.verify_image_bindings()
            print(json.dumps({"population": pop, "image_pairs_verified": 11}, indent=2, sort_keys=True))
            print("PREFLIGHT_PASS")
            return 0
        if args.verify_images:
            print(json.dumps(driver.verify_image_bindings(), indent=2, sort_keys=True))
            print("IMAGE_BINDING_11_11_PASS")
            return 0
        if args.readiness:
            payload = driver.write_readiness_manifest()
            print(json.dumps(payload, indent=2, sort_keys=True))
            print(f"READINESS_AGGREGATE {payload['aggregate']}")
            return 0
        if args.contingency:
            payload = driver.write_contingency()
            print(json.dumps(payload, indent=2, sort_keys=True))
            print("CONTINGENCY_WRITTEN")
            return 0
        if args.host_safety:
            print(json.dumps(driver.host_safety_observations(), indent=2, sort_keys=True))
            print("HOST_SAFETY_OBSERVED")
            return 0
        if args.freeze:
            import subprocess

            head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
            remote = subprocess.run(
                ["git", "rev-parse", "origin/parallel/d7-r4-full144-preexecution-2026-10-14"],
                capture_output=True,
                text=True,
            ).stdout.strip()
            payload = driver.write_freeze_record(head, remote)
            print(json.dumps(payload, indent=2, sort_keys=True))
            print("PRE_EXECUTION_FREEZE_WRITTEN")
            return 0
        if args.unit is not None:
            record = driver.run_unit(args.unit)
            print(json.dumps({k: record.get(k) for k in (
                "calibration_index", "validation_unit_id", "result", "classification",
                "elapsed_seconds", "execution_image_ref", "immutable_image_id",
            )}, indent=2, sort_keys=True))
            print(f"UNIT_PASS {record['validation_unit_id']}")
            return 0
        if args.next:
            result = driver.run_next()
            print(json.dumps(result, indent=2, sort_keys=True))
            print("NEXT_RAN" if "validation_unit_id" in str(result) else "RUN_COMPLETE")
            return 0
        if args.aggregate:
            print(json.dumps(driver.aggregate(), indent=2, sort_keys=True))
            print("AGGREGATE_PASS")
            return 0
    except (driver.Full144FailClosedError, population.PopulationError) as exc:
        print(f"FAIL_CLOSED {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"UNEXPECTED_FAILURE {exc!r}", file=sys.stderr)
        return 2

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
