#!/usr/bin/env python3
"""WP-2 E2E Smoke v2.2 generation driver (brain-authored kit; hash-verified).

Invariants enforced here (not in prose):
- Only NO_SCOPE / INVALID_AFTER_REPAIR / APPLIED are terminal. A provider outage,
  HOLD, rejection or instrument error writes NO episode record (pending, resumable).
- Provider exhaustion -> circuit breaker: cooldown and retry the SAME episode; STOP
  (exit 75) when the outage is too long. The episode counter never advances on it.
- Budget checked before every episode (exit 77).
- A GENERATION_FAIL record anywhere in the v22 root is an invariant violation (exit 78).

Exit codes: 0 progress/complete, 3 HOLD, 4 stop flag, 75 provider outage,
76 request rejected, 77 budget, 78 invariant/instrument error.

Usage:
  python scripts/wp2_e2e_v22_generate.py --mode main --max-new-episodes 8
  python scripts/wp2_e2e_v22_generate.py --mode variance --max-new-episodes 6
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.e2e_v22.circuit import CircuitBreaker  # noqa: E402
from benchmark.wp2.e2e_v22.common import (  # noqa: E402
    FORBIDDEN_STATUS,
    SCIENTIFIC_CEILING_USD,
    TERMINAL,
    V22_ROOT,
    WORST_EPISODE_USD,
    episode_path,
    planned_main,
    planned_variance,
    read_status,
)
from benchmark.wp2.e2e_v22.transport import (  # noqa: E402
    AttemptLog,
    HoldActiveV22,
    ProviderUnavailable,
    RequestRejected,
    V22HttpClient,
)

EXIT_OK, EXIT_HOLD, EXIT_STOPFLAG = 0, 3, 4
EXIT_OUTAGE, EXIT_REJECTED, EXIT_BUDGET, EXIT_INVARIANT = 75, 76, 77, 78


def hold_files(root: Path) -> list[Path]:
    return [root / "HOLD"]


def stop_flag() -> Path:
    return PROJECT / "logs" / "E2E_STOP.flag"


def scan_forbidden(root: Path) -> list[str]:
    bad: list[str] = []
    for sub in ("episodes", "variance"):
        d = root / sub
        if d.exists():
            for p in d.rglob("episode.json"):
                if read_status(p) in FORBIDDEN_STATUS or read_status(p) == "UNREADABLE":
                    bad.append(str(p.relative_to(root)))
    return bad


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")


def drive(mode: str, root: Path, client: Any, ledger: Any, breaker: CircuitBreaker,
          episode_fn: Callable[..., dict], cache_factory: Callable[[str], Any],
          max_new: int, max_seconds: float,
          clock: Callable[[], float] = time.monotonic,
          sleep: Callable[[float], None] = time.sleep,
          stop_path: Path | None = None) -> tuple[int, dict[str, Any]]:
    subdir = "episodes" if mode == "main" else "variance"
    plan = planned_main() if mode == "main" else planned_variance()
    stop_path = stop_path or stop_flag()
    t_start = clock()
    info: dict[str, Any] = {"mode": mode, "new_terminal": 0, "planned": len(plan)}

    bad = scan_forbidden(root)
    if bad:
        info["invariant"] = f"forbidden/unreadable episode records: {bad[:5]}"
        return EXIT_INVARIANT, info
    breaker.on_start()

    for task_id, arm, label in plan:
        path = episode_path(root, subdir, task_id, label)
        if read_status(path) in TERMINAL:
            continue
        if info["new_terminal"] >= max_new or (clock() - t_start) >= max_seconds:
            break
        while True:
            if stop_path.exists():
                info["pending"] = [task_id, label]
                return EXIT_STOPFLAG, info
            if not ledger.can_spend(WORST_EPISODE_USD):
                info["budget_total"] = ledger.total()
                return EXIT_BUDGET, info
            client.set_context(task_id=task_id, arm=arm, label=label, mode=mode)
            try:
                rec = episode_fn(task_id, arm, client, ledger, cache_factory(label), root,
                                 subdir=subdir, label=None if mode == "main" else label)
            except HoldActiveV22 as exc:
                info["pending"] = [task_id, label]
                info["hold"] = str(exc)
                return EXIT_HOLD, info
            except ProviderUnavailable as exc:
                decision = breaker.on_unavailable(str(exc))
                if decision.action == "STOP":
                    info["pending"] = [task_id, label]
                    info["outage"] = decision.reason
                    _write_json(root / "transport" / "pending.json",
                                {"task_id": task_id, "arm": arm, "label": label, "mode": mode,
                                 "reason": decision.reason,
                                 "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
                    return EXIT_OUTAGE, info
                waited = 0.0
                while waited < decision.seconds:
                    if stop_path.exists():
                        info["pending"] = [task_id, label]
                        return EXIT_STOPFLAG, info
                    try:
                        client.check_hold()
                    except HoldActiveV22 as exc2:
                        info["pending"] = [task_id, label]
                        info["hold"] = str(exc2)
                        return EXIT_HOLD, info
                    step = min(15.0, decision.seconds - waited)
                    sleep(step)
                    waited += step
                continue
            except RequestRejected as exc:
                info["pending"] = [task_id, label]
                info["rejected"] = str(exc)
                _write_json(root / "transport" / "rejected.json",
                            {"task_id": task_id, "arm": arm, "label": label,
                             "error": str(exc), "attempts": exc.attempts})
                return EXIT_REJECTED, info
            except Exception as exc:
                info["pending"] = [task_id, label]
                info["instrument_error"] = f"{type(exc).__name__}: {exc}"
                _write_json(root / "transport" / "instrument_error.json",
                            {"task_id": task_id, "arm": arm, "label": label,
                             "traceback": traceback.format_exc()[-6000:]})
                return EXIT_INVARIANT, info
            status = rec.get("status")
            if status not in TERMINAL:
                info["invariant"] = f"non-terminal status written: {status} for {task_id}/{label}"
                return EXIT_INVARIANT, info
            breaker.on_success()
            info["new_terminal"] += 1
            break
    info["terminal"] = sum(1 for t, _a, lab in plan
                           if read_status(episode_path(root, subdir, t, lab)) in TERMINAL)
    return EXIT_OK, info


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("main", "variance"), required=True)
    ap.add_argument("--max-new-episodes", type=int, default=8)
    ap.add_argument("--max-seconds", type=float, default=5400.0)
    args = ap.parse_args(argv)

    from benchmark.wp2.e2e.response_cache import ResponseCache
    from benchmark.wp2.e2e_v21.generate import run_episode_v21
    from benchmark.wp2.e2e_v21.ledger import LedgerV21

    root = V22_ROOT
    ledger = LedgerV21(root / "ledger" / "spend_ledger_v22.jsonl",
                       {"SMOKE": SCIENTIFIC_CEILING_USD})
    client = V22HttpClient(hold_files(root), AttemptLog(root / "transport" / "attempts.jsonl"))
    breaker = CircuitBreaker(root / "transport" / "circuit.json")

    def cache_factory(label: str) -> Any:
        if args.mode == "main":
            return ResponseCache(root)
        return ResponseCache(root / "cache_variance" / label)

    code, info = drive(args.mode, root, client, ledger, breaker, run_episode_v21,
                       cache_factory, args.max_new_episodes, args.max_seconds)
    info.update({"exit": code, "spend_total_usd": round(ledger.total(), 6),
                 "network_attempts": client.network_attempts})
    print("DRIVER_RESULT " + json.dumps(info, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
