#!/usr/bin/env python3
"""WP-2 Mission-10A: preregister materiality rule + select 2 ENG probe tasks.

ZERO API. Writes preregistered_materiality_rule.json (BEFORE any probe
outcome) and probe_selection.json (deterministic from pre-probe audit
evidence).

Probe-task selection (Mission-10A section 16):
  1. ENG task with the highest number of error-TOI / P2P-U setup-error nodes
     attributable to the declared-but-missing/misloaded dependency.
  2. second-highest.
  Tie: lexicographic task_id.
  Prefer tasks covering distinct suspected dependencies ONLY if it does not
  violate the primary rank rule; if a strict ranking selects the same cause
  twice, report that explicitly.

Usage:
    python scripts/wp2_m10a_probe_preregister.py [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.m10a_audit import (  # noqa: E402
    preregister_materiality_rule,
    sha256_json,
)

ERROR_RECORDS = PROJECT / "research" / "wp2" / "mission10a_env_audit_2026-09-26" / "error_records.jsonl"
OUT_ROOT = PROJECT / "research" / "wp2" / "mission10a_env_audit_2026-09-26"


def count_attributable_per_task() -> dict[str, dict]:
    """Count ENG error nodes attributable to declared-but-missing causes.

    Attributable taxonomy: MISSING_FIXTURE:count_queries (pytest-django-queries)
    and MISSING_FIXTURE:mocker (pytest-mock), whose packages were proven
    declared-but-not-installed in Phase C/B and plugin-state introspection.
    """
    per: dict[str, dict] = defaultdict(lambda: {"total": 0, "count_queries": 0, "mocker": 0, "other_declared": 0})
    seen: set[tuple[str, str]] = set()
    with ERROR_RECORDS.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["dataset"] != "P2P_U_ENG":
                continue
            if not r["evidence_path"].startswith("cap200/"):
                continue
            key = (r["task_id"], r["node_id"])
            if key in seen:
                continue
            seen.add(key)
            tax = r["taxonomy"]
            per[r["task_id"]]["total"] += 1
            if tax == "MISSING_FIXTURE:count_queries":
                per[r["task_id"]]["count_queries"] += 1
            elif tax == "MISSING_FIXTURE:mocker":
                per[r["task_id"]]["mocker"] += 1
            else:
                per[r["task_id"]]["other_declared"] += 1
    return {k: dict(v) for k, v in per.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out_root = Path(args.out) if args.out else OUT_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    # 1. Preregistered materiality rule (BEFORE probe outcomes are visible).
    rule = preregister_materiality_rule(_now_utc())
    rule_json = {
        "artifact": "preregistered_materiality_rule",
        "schema_version": "mission10a-materiality-prereg-v1",
        "created_utc": _now_utc(),
        "preregistered_before_probe": rule.preregistered_before_probe,
        "rule_text": rule.rule_text,
        "conditions": rule.conditions,
        "rule_sha256": sha256_json(rule.conditions),
        "note": "Written BEFORE any scratch-probe outcome. Do NOT change the "
                "rule after probe outcomes are visible (Mission-10A section 14).",
    }
    (out_root / "preregistered_materiality_rule.json").write_text(
        json.dumps(rule_json, indent=1, ensure_ascii=False), encoding="utf-8"
    )

    # 2. Probe task selection (deterministic).
    per = count_attributable_per_task()
    # Primary rank: attributable error-node count descending, tie lexicographic.
    ranked = sorted(
        ((tid, v["total"], v["count_queries"], v["mocker"]) for tid, v in per.items()),
        key=lambda t: (-t[1], t[0]),
    )
    selected = ranked[:2] if len(ranked) >= 2 else ranked
    sel = [
        {
            "task_id": tid,
            "rank": i + 1,
            "attributable_error_nodes": total,
            "count_queries_nodes": cq,
            "mocker_nodes": mk,
            "primary_dependency": "pytest-django-queries" if cq >= mk else "pytest-mock",
        }
        for i, (tid, total, cq, mk) in enumerate(selected)
    ]
    sel_json = {
        "artifact": "probe_selection",
        "schema_version": "mission10a-probe-selection-v1",
        "created_utc": _now_utc(),
        "selection_rule": "1) highest attributable ENG error-node count; "
                         "2) second-highest; tie -> lexicographic task_id. "
                         "Distinct-dependency preference only if it does not "
                         "violate the primary rank rule.",
        "attributable_per_task": dict(sorted(per.items())),
        "ranked_tasks": [{"task_id": t[0], "attributable": t[1]} for t in ranked],
        "selected_tasks": sel,
        "distinct_dependency_cover": (
            len({s["primary_dependency"] for s in sel}) == 2
        ),
    }
    (out_root / "probe_selection.json").write_text(
        json.dumps(sel_json, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    print("wrote preregistered_materiality_rule.json + probe_selection.json")
    for s in sel:
        print(f"  selected: {s['task_id']} (attributable={s['attributable_error_nodes']}, "
              f"count_queries={s['count_queries_nodes']}, mocker={s['mocker_nodes']})")
    return 0


def _now_utc() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
