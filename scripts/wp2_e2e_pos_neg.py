#!/usr/bin/env python3
"""WP-2 Mission-11 B11.3/B11.4 - G-POS and G-NEG controls (container evaluations)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

E2E_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"
SALEOR_CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"

from benchmark.wp2.e2e.evaluate import evaluate_state, materialize, score  # noqa: E402
from benchmark.wp2.e2e.generate import run_episode  # noqa: E402
from benchmark.wp2.e2e.llm_client import Ledger, ReplayClient  # noqa: E402
from benchmark.wp2.e2e.scopes import commits_of  # noqa: E402
from benchmark.wp2.e2e.spec import CEILING_AGENT_USD, CEILING_SMOKE_USD  # noqa: E402

CONTROL_TASKS = json.loads((E2E_ROOT / "controls" / "control_tasks.json").read_text(encoding="utf-8"))["chosen"]


def gold_p1(_task_id: str, path: str, parent: str, target: str) -> str | None:
    from scripts.wp2_e2e_controls import _try_convert
    old = subprocess.run(["git", "-C", str(SALEOR_CACHE), "show", f"{parent}:{path}"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return _try_convert(path, parent, target, old.stdout)[0]


def gold_as_model_output(task_id: str) -> str:
    """The complete GOLD P1 patch (concatenated over all editable gold files)."""
    from benchmark.wp2.e2e.scopes import editable_filter, gold_raw_scope
    parent, target = commits_of(task_id)
    scope = editable_filter(task_id, gold_raw_scope(task_id))
    blocks = []
    for path in scope["editable"]:
        p1 = gold_p1(task_id, path, parent, target)
        if p1:
            blocks.append(p1)
    return "\n".join(blocks)


def run_pos() -> int:
    from benchmark.wp2.e2e import generate as gen
    out = {"artifact": "g_pos", "per_task": {}}

    class GoldClient:
        def __init__(self, gold: str) -> None:
            self.gold = gold

        def generate(self, _system: str, _user: str):
            from benchmark.wp2.e2e.llm_client import CallResult
            return CallResult(text=self.gold, finish_reason="stop", prompt_tokens=1,
                              completion_tokens=len(self.gold) // 4, cost_usd=0.0,
                              route="replay", provider="replay", latency_s=0.0,
                              request_id="gold-ctrl")

    for tid in CONTROL_TASKS:
        parent, target = commits_of(tid)
        gold = gold_as_model_output(tid)
        # monkeypatch generate's py_compile to ok (container syntax check done by evaluator)
        real_pycompile = gen.py_compile_in_era
        gen.py_compile_in_era = lambda _era, files: {p: "ok" for p in files}
        try:
            ledger = Ledger(E2E_ROOT / "ledger" / "controls.jsonl",
                            {"AGENT": CEILING_AGENT_USD, "SMOKE": CEILING_SMOKE_USD})
            ep = run_episode(tid, "GOLD_HARD", GoldClient(gold), ledger)
        finally:
            gen.py_compile_in_era = real_pycompile
        if ep["status"] != "APPLIED":
            out["per_task"][tid] = {"status": ep["status"], "validation": ep["validation"]}
            continue
        wt, tree_sha = materialize(tid, "ctrl_pos", _diff_text(tid, ep))
        target_tree = subprocess.run(["git", "-C", str(SALEOR_CACHE), "rev-parse", f"{target}^{{tree}}"],
                                     capture_output=True, text=True, encoding="utf-8").stdout.strip()
        rec = evaluate_state(tid, "ctrl_pos", wt)
        scd = score(tid, "ctrl_pos", rec["groups"])
        out["per_task"][tid] = {"tree_sha": tree_sha, "target_tree": target_tree,
                                "tree_matches": tree_sha == target_tree, **scd}
    (E2E_ROOT / "controls").mkdir(parents=True, exist_ok=True)
    (E2E_ROOT / "controls" / "g_pos.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("G-POS:", json.dumps(out, indent=1)[:2000])
    return 0


def _diff_text(task_id: str, _ep: dict) -> str:
    p = E2E_ROOT / "episodes" / task_id / "GOLD_HARD" / "final_diff.patch"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def run_neg() -> int:
    out = {"artifact": "g_neg", "per_task": {}}
    for tid in CONTROL_TASKS:
        wt, _tree = materialize(tid, "ctrl_neg", "")
        rec = evaluate_state(tid, "ctrl_neg", wt)
        scd = score(tid, "ctrl_neg", rec["groups"])
        out["per_task"][tid] = scd
    (E2E_ROOT / "controls").mkdir(parents=True, exist_ok=True)
    (E2E_ROOT / "controls" / "g_neg.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("G-NEG:", json.dumps(out, indent=1)[:2000])
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", required=True, choices=["pos", "neg"])
    args = ap.parse_args()
    raise SystemExit(run_pos() if args.control == "pos" else run_neg())
