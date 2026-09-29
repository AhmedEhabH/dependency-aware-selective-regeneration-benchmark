#!/usr/bin/env python3
"""WP-2 E2E v2.2 environment canary (brain-authored kit; hash-verified). Zero API.

Positive: gold non-test diff on the frozen parent+test-patch state must rebuild the
exact target tree and PASS F2P (P2P-S / P2P-U200 PASS or UNDEFINED, no flaky node).
Negative: the empty diff must FAIL F2P and keep P2P-S / P2P-U200 PASS or UNDEFINED.
The verdict is computed here, mechanically; exit 0 only if both hold.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.e2e_v22.common import V22_ROOT  # noqa: E402

CANARY_TASK = "saleor-rc-2d45b76a52f2"
OK_P2P = ("PASS", "UNDEFINED")


def pos_ok(res: dict[str, Any]) -> bool:
    return (res.get("tree_matches") is True and res.get("f2p_task") == "PASS"
            and res.get("p2p_s_task") in OK_P2P and res.get("p2p_u200_task") in OK_P2P
            and not res.get("flaky_under_patch"))


def neg_ok(res: dict[str, Any]) -> bool:
    return (res.get("f2p_task") == "FAIL" and res.get("p2p_s_task") in OK_P2P
            and res.get("p2p_u200_task") in OK_P2P)


def gold_nontest_diff(task_id: str) -> tuple[str, str]:
    from benchmark.wp2.e2e.scopes import commits_of
    from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2
    from scripts.wp2_linux_dryrun import WSL_CACHE, wsl
    parent, target = commits_of(task_id)
    names = wsl(f"git -C {WSL_CACHE} diff --name-only {parent} {target}").stdout.split()
    paths = [p for p in names if not is_test_path_v2(p)]
    quoted = " ".join(f"'{p}'" for p in paths)
    diff = wsl(f"git -C {WSL_CACHE} diff {parent} {target} -- {quoted}").stdout
    tree = wsl(f"git -C {WSL_CACHE} rev-parse {target}^{{tree}}").stdout.strip()
    return diff, tree


def main() -> int:
    from benchmark.wp2.e2e import evaluate as ev
    from benchmark.wp2.e2e.evaluate import evaluate_state, materialize, score
    ev.E2E_ROOT = V22_ROOT
    out: dict[str, Any] = {"artifact": "canary_v22", "task": CANARY_TASK,
                           "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    diff, target_tree = gold_nontest_diff(CANARY_TASK)
    wt, tree = materialize(CANARY_TASK, "v22_canary_pos", diff)
    rec = evaluate_state(CANARY_TASK, "v22_canary_pos", wt)
    pos = {"tree_sha": tree, "target_tree": target_tree, "tree_matches": tree == target_tree,
           **score(CANARY_TASK, "v22_canary_pos", rec["groups"])}
    wt2, _ = materialize(CANARY_TASK, "v22_canary_neg", "")
    rec2 = evaluate_state(CANARY_TASK, "v22_canary_neg", wt2)
    neg = dict(score(CANARY_TASK, "v22_canary_neg", rec2["groups"]))
    out.update({"positive": pos, "negative": neg,
                "positive_ok": pos_ok(pos), "negative_ok": neg_ok(neg)})
    out["pass"] = out["positive_ok"] and out["negative_ok"]
    (V22_ROOT / "controls").mkdir(parents=True, exist_ok=True)
    (V22_ROOT / "controls" / "canary_v22.json").write_text(
        json.dumps(out, indent=1, default=str), encoding="utf-8")
    print("CANARY " + json.dumps({"pass": out["pass"], "positive_ok": out["positive_ok"],
                                  "negative_ok": out["negative_ok"]}))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
