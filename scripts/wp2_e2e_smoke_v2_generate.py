#!/usr/bin/env python3
"""WP-2 Mission-12 C3 - E2E Smoke v2 generation (PAID <= $2.00, outcome-blind).

56 episodes: task sorted; arm order GOLD, RMCSS, AGENT, PLACEBO. Shared
run-level ResponseCache. Full-context repair. Raw responses persisted
immediately. Stop-flag + ledger spend guard before every call.

Also runs the K11 transport capability probe (one minimal four-message request,
counted against the $2 ceiling) before the first main episode.

Variance probe (S04): 3 control tasks x GOLD_HARD x 2 extra replicates
(var_r1, var_r2) with cache bypassed, persisted under variance/.

Usage:
  python scripts/wp2_e2e_smoke_v2_generate.py --resume [--max-episodes N]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

V2_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v2"
V1_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"

from benchmark.wp2.e2e.generate_v2 import E2E_ROOT_V2, run_episode_v2  # noqa: E402
from benchmark.wp2.e2e.llm_client import Ledger, OpenRouterClient  # noqa: E402
from benchmark.wp2.e2e.response_cache import ResponseCache  # noqa: E402
from benchmark.wp2.e2e.spec import ARMS, SMOKE_TASKS  # noqa: E402


def _planned() -> list[tuple[str, str]]:
    episodes = []
    for tid in sorted(SMOKE_TASKS):
        for arm in ARMS:
            episodes.append((tid, arm))
    return episodes


def _progress() -> dict:
    p = V2_ROOT / "progress.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _save_progress(prog: dict) -> None:
    (V2_ROOT / "progress.json").write_text(json.dumps(prog, indent=1), encoding="utf-8")


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--max-episodes", type=int, default=None)
    ap.add_argument("--stop-file", default=None)
    ap.add_argument("--skip-probe", action="store_true")
    ap.add_argument("--variance", action="store_true",
                    help="run the variance probe (3 control tasks x GOLD x 2 extra, cache bypass)")
    args = ap.parse_args()

    freeze = json.loads((V2_ROOT / "smoke_v2_freeze.json").read_text(encoding="utf-8"))
    episodes = _planned()
    ledger = Ledger(V2_ROOT / "ledger" / "spend_ledger_v2.jsonl",
                    {"SMOKE": freeze["ceilings"]["smoke_v2_usd"]})
    client = OpenRouterClient()
    cache = ResponseCache(E2E_ROOT_V2)
    prog = _progress()
    stop_file = Path(args.stop_file) if args.stop_file else PROJECT / "logs" / "E2E_STOP.flag"

    if not args.skip_probe:
        if not prog.get("transport_probe_done"):
            print("[probe] K11 transport capability probe (four-message structure)")
            # minimal, non-scientific, low-token request with the exact message
            # structure required by repair; no repository content.
            from benchmark.wp2.e2e.generate_v2 import _record_ledger
            messages = [
                {"role": "system", "content": "You are a minimal probe. Reply with exactly: PONG"},
                {"role": "user", "content": "Probe request. Reply PONG only."},
                {"role": "assistant", "content": "PONG"},
                {"role": "user", "content": "Reply PONG again."},
            ]
            try:
                call = client.generate_messages(messages)
            except Exception as exc:  # transport reject
                print(f"[probe] FAILED: {type(exc).__name__}: {exc}")
                return 3
            _record_ledger(ledger, call, "PROBE", "PROBE", "probe")
            cache.put(ResponseCache.request_sha(
                "qwen/qwen3-coder", "openrouter:qwen/qwen3-coder@deepinfra/turbo",
                "deepinfra/turbo", 0.0, 1.0, 8192, messages),
                {"request_sha": "", "text": call.text, "finish_reason": call.finish_reason,
                 "prompt_tokens": call.prompt_tokens,
                 "completion_tokens": call.completion_tokens,
                 "cost_usd": call.cost_usd})
            print(f"[probe] OK text={call.text[:40]!r} finish={call.finish_reason} "
                  f"cost=${call.cost_usd:.6f}")
            prog["transport_probe_done"] = True
            prog["transport_probe"] = {"finish_reason": call.finish_reason,
                                       "cost_usd": call.cost_usd,
                                       "prompt_tokens": call.prompt_tokens,
                                       "completion_tokens": call.completion_tokens}
            _save_progress(prog)
        else:
            print("[probe] already done; skipping")

    done = 0
    for tid, arm in episodes:
        if args.max_episodes is not None and done >= args.max_episodes:
            break
        if stop_file.exists():
            print("[smoke] E2E_STOP.flag present; stopping")
            break
        ep_file = V2_ROOT / "episodes" / tid / arm / "episode.json"
        if ep_file.exists():
            print(f"  {tid} {arm} already present; skip (resume)")
            done += 1
            continue
        # spend guard: worst case for this episode = full-context initial+repair
        if not ledger.can_spend(freeze["ceilings"]["smoke_v2_usd"]):
            print("[smoke] spend guard would exceed ceiling; stopping")
            break
        ep = run_episode_v2(tid, arm, client, ledger, cache, root=E2E_ROOT_V2)
        prog.setdefault("episodes", {})
        prog["episodes"][f"{tid}|{arm}"] = {"status": ep["status"],
                                            "diff_sha256": ep["diff_sha256"],
                                            "repair_used": ep.get("repair_used", False),
                                            "request_sha_initial": ep.get("request_sha_initial", "")}
        _save_progress(prog)
        cost = sum(c["cost_usd_actual"] for c in ep["calls"])
        print(f"  {tid} {arm} -> {ep['status']} cost=${cost:.5f}")
        done += 1
    totals = ledger.totals()
    print(f"[smoke] done this invocation: {done}; ledger totals: {totals}; "
          f"total ${ledger.total():.6f}")
    return 0


def run_variance() -> int:
    """S04: 3 control tasks x GOLD_HARD x 2 extra replicates, cache bypassed.

    Persists under research/wp2/e2e_smoke_eng_v2/variance/. Each replicate is a
    fresh provider call (no cache reuse). Descriptive only.
    """
    freeze = json.loads((V2_ROOT / "smoke_v2_freeze.json").read_text(encoding="utf-8"))
    control_tasks = freeze["variance_probe"]["tasks"]
    ledger = Ledger(V2_ROOT / "ledger" / "spend_ledger_v2.jsonl",
                    {"SMOKE": freeze["ceilings"]["smoke_v2_usd"]})
    client = OpenRouterClient()
    cache = ResponseCache(E2E_ROOT_V2 / "cache_variance_disabled")
    recs = []
    for tid in sorted(control_tasks):
        for label in ("var_r1", "var_r2"):
            rec = run_episode_v2(tid, "GOLD_HARD", client, ledger, cache,
                                 root=E2E_ROOT_V2, episodes_subdir="variance")
            recs.append({"label": label, "task_id": tid, "status": rec["status"],
                         "diff_sha256": rec["diff_sha256"],
                         "repair_used": rec.get("repair_used", False),
                         "request_sha_initial": rec.get("request_sha_initial", ""),
                         "actual_cost": rec.get("_actual_cost", 0.0)})
            print(f"[variance] {tid} {label} -> {rec['status']}")
    out = {"artifact": "variance_probe_v2", "episodes": recs,
           "note": "descriptive only; no CI / population variance estimate / causal statement"}
    (V2_ROOT / "variance").mkdir(parents=True, exist_ok=True)
    (V2_ROOT / "variance" / "variance_probe_v2.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    totals = ledger.totals()
    print(f"[variance] ledger totals: {totals}; total ${ledger.total():.6f}")
    return 0


if __name__ == "__main__":
    import sys as _sys
    if "--variance" in _sys.argv:
        raise SystemExit(run_variance())
    raise SystemExit(main())
