#!/usr/bin/env python3
"""WP-2 Mission-11 B4.5/C3.1 - build per-arm scopes (14 Smoke tasks, 4 arms)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

E2E_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"
OUT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"

from benchmark.wp2.e2e.scopes import (  # noqa: E402
    build_arm_scopes,
    editable_filter,
)
from benchmark.wp2.e2e.spec import ARMS, SMOKE_TASKS  # noqa: E402
from benchmark.wp2.e2e.task_inputs import record_intent_source  # noqa: E402


def sha(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def main() -> int:
    out = {}
    for arm in ARMS:
        out[arm] = {"artifact": f"scopes_{arm}", "per_task": {}}
    for tid in SMOKE_TASKS:
        for arm in ARMS:
            if arm == "AGENT_HARD":
                agent = json.loads((E2E_ROOT / "scopes/agent_scopes_dev_eng.json").read_text(encoding="utf-8"))
                raw = sorted(agent["per_task"].get(tid, {}).get("selected_paths", []))
                sc = editable_filter(tid, raw)
            else:
                sc = build_arm_scopes(tid, arm)
            rec = {k: sc.get(k) for k in ("raw", "editable", "excluded_large", "excluded_budget", "status")}
            rec["scope_sha256"] = sha({"editable": sc.get("editable", [])})
            out[arm]["per_task"][tid] = rec
    (E2E_ROOT / "scopes").mkdir(parents=True, exist_ok=True)
    for arm in ARMS:
        p = E2E_ROOT / "scopes" / f"scopes_{arm}.json"
        p.write_text(json.dumps(out[arm], indent=1, ensure_ascii=False), encoding="utf-8")
    # intent source record
    eng = json.loads((OUT / "eng_v3_oracle_ready.json").read_text(encoding="utf-8"))
    record_intent_source(sorted(eng["oracle_valid_union_task_ids"]))
    print("scopes built for", len(SMOKE_TASKS), "tasks x", len(ARMS), "arms")
    for arm in ARMS:
        editable_counts = {t: len(v["editable"]) for t, v in out[arm]["per_task"].items()}
        print(arm, "editable totals:", sum(editable_counts.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
