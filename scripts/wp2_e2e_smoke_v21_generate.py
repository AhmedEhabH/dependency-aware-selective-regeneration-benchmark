#!/usr/bin/env python3
"""Mission-12B v2.1 - M main generation driver (T2).

56 episodes: task sorted; arm order GOLD, RMCSS, AGENT, PLACEBO. Uses the
v21 TRANSPORT_V21 client, v21 cache only, v21 ledger (fsync after every call),
raw responses persisted immediately, and persistent progress after each
terminal episode.

Invariants:
- --max-new-episodes counts only NEWLY terminal episodes, never skipped ones.
- --resume never deletes evidence.
- GENERATION_FAIL records never replace an existing calls list with [].
- v2 cache is never read; no v2 path is written by this driver.
- no evaluation in this driver.

Usage:
  python scripts/wp2_e2e_smoke_v21_generate.py --resume [--max-new-episodes N]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

V21_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v21"
HOLD = V21_ROOT / "HOLD"

from benchmark.wp2.e2e.response_cache import ResponseCache  # noqa: E402
from benchmark.wp2.e2e.spec import ARMS, SMOKE_TASKS  # noqa: E402
from benchmark.wp2.e2e_v21.generate import E2E_ROOT_V21, run_episode_v21  # noqa: E402
from benchmark.wp2.e2e_v21.ledger import LedgerV21  # noqa: E402
from benchmark.wp2.e2e_v21.transport import V21HttpClient  # noqa: E402

SCIENTIFIC_CEILING_USD = 2.00


def _planned() -> list[tuple[str, str]]:
    episodes = []
    for tid in sorted(SMOKE_TASKS):
        for arm in ARMS:
            episodes.append((tid, arm))
    return episodes


def _progress() -> dict:
    p = V21_ROOT / "progress.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _save_progress(prog: dict) -> None:
    (V21_ROOT / "progress.json").write_text(
        json.dumps(prog, indent=1, ensure_ascii=False), encoding="utf-8")


def _is_terminal(ep_file: Path) -> bool:
    if not ep_file.exists():
        return False
    try:
        rec = json.loads(ep_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return rec.get("status") in ("NO_SCOPE", "GENERATION_FAIL",
                                 "INVALID_AFTER_REPAIR", "APPLIED")


def _drive(episodes: list[tuple[str, str]], ledger: LedgerV21, client: V21HttpClient,
           cache: ResponseCache, prog: dict, root: Path, stop_file: Path,
           max_new_episodes: int | None) -> int:
    """Run the episode loop. Returns the count of NEWLY terminal episodes."""
    new_terminal = 0
    for tid, arm in episodes:
        if max_new_episodes is not None and new_terminal >= max_new_episodes:
            print(f"[smoke] max-new-episodes reached ({new_terminal}); stopping")
            break
        if stop_file.exists():
            print("[smoke] E2E_STOP.flag present; stopping")
            break
        ep_file = root / "episodes" / tid / arm / "episode.json"
        if _is_terminal(ep_file):
            print(f"  {tid} {arm} already terminal; skip (resume)")
            continue
        worst_episode = (1.0 / 1e6) * 8192 * 2 + 0.02
        if not ledger.can_spend(worst_episode):
            print("[smoke] spend guard would exceed ceiling; stopping")
            break
        ep = run_episode_v21(tid, arm, client, ledger, cache, root=root)
        prog.setdefault("episodes", {})
        prog["episodes"][f"{tid}|{arm}"] = {
            "status": ep["status"], "diff_sha256": ep["diff_sha256"],
            "repair_used": ep.get("repair_used", False),
            "request_sha_initial": ep.get("request_sha_initial", "")}
        _save_progress(prog)
        cost = sum(c["cost_usd_actual"] for c in ep["calls"])
        print(f"  {tid} {arm} -> {ep['status']} cost=${cost:.5f}")
        new_terminal += 1
    return new_terminal


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--max-new-episodes", type=int, default=None)
    ap.add_argument("--stop-file", default=None)
    args = ap.parse_args()

    episodes = _planned()
    ledger = LedgerV21(V21_ROOT / "ledger" / "spend_ledger_v21.jsonl",
                       {"SMOKE": SCIENTIFIC_CEILING_USD})
    client = V21HttpClient(hold_file=HOLD)
    cache = ResponseCache(E2E_ROOT_V21)
    prog = _progress()
    stop_file = Path(args.stop_file) if args.stop_file else PROJECT / "logs" / "E2E_STOP.flag"

    new_terminal = _drive(episodes, ledger, client, cache, prog,
                          E2E_ROOT_V21, stop_file, args.max_new_episodes)
    totals = ledger.totals()
    print(f"[smoke] new terminal this invocation: {new_terminal}; "
          f"ledger totals: {totals}; total ${ledger.total():.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
