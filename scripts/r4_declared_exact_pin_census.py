#!/usr/bin/env python3
"""Implemented-rule census for the GENERAL declared-but-unlocked pin rule.

Mission ``M17_D7_R4_PHASE1B_SCIENTIFIC_SUCCESSOR_RESOLUTION_REPAIR`` (TASK D).

This is a REQUIRED acceptance gate.  It executes the ACTUAL implemented rule
logic (``declared_pins_for_commit`` / ``task_lock_pin_names`` -- the same code
path and normalization semantics used during scientific execution) against the
frozen 219 mapped commits from the authoritative population census.

Acceptance: affected unique commits = 1, affected validation units = 1,
affected package/version pairs = 1, and the single hit must be exactly:

  commit            484ce8815cf4c6724d49ce26dce5da7fc07ba174
  validation unit   vu-cd262bbb641d
  package           posuto==2021.10.0

The result is compared against the Phase-1A census and must match exactly.
Any additional hit is a STOP_OWNER_REVIEW_UNCOVERED_RESOLUTION_CASE.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT / "scripts"
SRC = PROJECT / "src"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import r4_behavioral_calibration_n12_r2 as r2  # noqa: E402

CENSUS_PATH = PROJECT / "research" / "env-canon-r4" / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json"

EXPECTED_HIT = {
    "commit": "484ce8815cf4c6724d49ce26dce5da7fc07ba174",
    "validation_unit": "vu-cd262bbb641d",
    "pin": "posuto==2021.10.0",
}


def run_census() -> dict:
    census = json.loads(CENSUS_PATH.read_text(encoding="utf-8"))
    hits: dict[str, dict] = {}
    for unit in census["units"]:
        uid = unit["validation_unit_id"]
        lock_type = unit["lock_type"]
        python_version = unit["python_version"]
        for rec in unit["member_task_records"]:
            tid = rec["task_id"]
            commit = rec["target_commit"]
            lock_names = r2.task_lock_pin_names(tid, lock_type, python_version)
            if lock_names is None:
                continue  # non-poetry lock: rule predicate not satisfiable
            pins = r2.declared_pins_for_commit(commit, lock_names)
            if pins:
                hits[commit] = {
                    "commit": commit,
                    "validation_units": sorted({uid}),
                    "pins": sorted(pins),
                    "task_id": tid,
                    "lock_type": lock_type,
                }
    return hits


def main() -> int:
    hits = run_census()
    commits = set(hits)
    units = {u for h in hits.values() for u in h["validation_units"]}
    pins = {p for h in hits.values() for p in h["pins"]}

    report = {
        "implemented_rule_census": {
            "affected_unique_commits": len(commits),
            "affected_validation_units": len(units),
            "affected_package_version_pairs": len(pins),
            "hits": hits,
        },
        "phase1a_census": {
            "affected_unique_commits": 1,
            "affected_validation_units": 1,
            "affected_package_version_pairs": 1,
            "hit": EXPECTED_HIT,
        },
        "census_equality": (
            commits == {EXPECTED_HIT["commit"]}
            and units == {EXPECTED_HIT["validation_unit"]}
            and pins == {EXPECTED_HIT["pin"]}
        ),
    }
    out = PROJECT / "research" / "env-canon-r4" / "R4_PHASE1B_IMPLEMENTED_RULE_CENSUS.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))

    if report["census_equality"]:
        print("CENSUS_EQUALITY=PASS  (implemented-rule census == Phase-1A census == 1 hit)")
        return 0
    print("CENSUS_EQUALITY=FAIL  -> STOP_OWNER_REVIEW_UNCOVERED_RESOLUTION_CASE")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
