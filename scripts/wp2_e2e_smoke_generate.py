#!/usr/bin/env python3
"""WP-2 Mission-11 D1 - E2E Smoke generation (PAID <= $4.50, outcome-blind)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

E2E_ROOT = PROJECT / "research/wp2/e2e_smoke_eng_v1"

from benchmark.wp2.e2e.generate import _PromptResponseCache, run_episode  # noqa: E402
from benchmark.wp2.e2e.llm_client import Ledger, OpenRouterClient  # noqa: E402
from benchmark.wp2.e2e.spec import (  # noqa: E402
    CEILING_AGENT_USD,
    CEILING_SMOKE_USD,
)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--max-episodes", type=int, default=None)
    ap.add_argument("--stop-file", default=None)
    args = ap.parse_args()

    freeze = json.loads((E2E_ROOT / "smoke_freeze.json").read_text(encoding="utf-8"))
    episodes = [(e["task"], e["arm"]) for e in freeze["planned_episodes"]]
    ledger = Ledger(E2E_ROOT / "ledger/spend_ledger.jsonl",
                    {"AGENT": CEILING_AGENT_USD, "SMOKE": CEILING_SMOKE_USD})
    client = OpenRouterClient()
    cache = _PromptResponseCache()

    progress_path = E2E_ROOT / "episodes/progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8")) if progress_path.exists() else {}

    stop_file = Path(args.stop_file) if args.stop_file else PROJECT / "logs" / "E2E_STOP.flag"
    done = 0
    for tid, arm in episodes:
        if args.max_episodes is not None and done >= args.max_episodes:
            break
        if stop_file.exists():
            print("[smoke] E2E_STOP.flag present; stopping")
            break
        ep_file = E2E_ROOT / "episodes" / tid / arm / "episode.json"
        if ep_file.exists():
            ep = json.loads(ep_file.read_text(encoding="utf-8"))
            ok, reason = _verify_episode(ep)
            if ok:
                print(f"  {tid} {arm} verified; skip (resume)")
                done += 1
                continue
            print(f"  {tid} {arm} verify FAILED ({reason}); rerun")
        ep = run_episode(tid, arm, client, ledger, cache)
        progress.setdefault("episodes", {})
        progress["episodes"][f"{tid}|{arm}"] = {"status": ep["status"],
                                                 "diff_sha256": ep["diff_sha256"],
                                                 "prompt_sha256": ep["prompt_sha256"]}
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        progress_path.write_text(json.dumps(progress, indent=1), encoding="utf-8")
        print(f"  {tid} {arm} -> {ep['status']} cost={sum(c['cost_usd_actual'] for c in ep['calls']):.5f}")
        done += 1
    totals = ledger.totals()
    print(f"[smoke] done this invocation: {done}; ledger totals: {totals}; "
          f"total ${ledger.total():.6f}")
    return 0


def _verify_episode(ep: dict) -> tuple[bool, str]:
    if "episode_sha256" not in ep:
        return False, "no sha"
    computed = hashlib.sha256(
        json.dumps({k: v for k, v in ep.items() if k != "episode_sha256"},
                   sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    if computed != ep["episode_sha256"]:
        return False, "hash mismatch"
    return True, "OK"


if __name__ == "__main__":
    raise SystemExit(main())
