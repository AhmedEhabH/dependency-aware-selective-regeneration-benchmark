#!/usr/bin/env python3
"""WP-2 P2P-U V2 ENG orchestration driver (Mission-09) - ZERO API.

Runs the frozen P2P-U V2 execution on the 8 executable oracle-valid ENG tasks
(9 ENG minus the zero-node P2P-U-UNDEFINED task saleor-rc-9258154b8a0b), for
BOTH caps (200 primary, 400 sensitivity) INDEPENDENTLY, workers=1.

Deterministic task order (frozen before execution): sorted task-id order;
within each task cap200 first, then cap400 (each fully persisted/verified and
worktrees/DB cleaned before the next). Resumable: a cap is skipped if its
manifest already exists with evidence_integrity.ok == True.

Usage:
    python scripts/wp2_p2p_u_v2_eng_run.py [--task saleor-rc-...] [--cap 200]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
EVIDENCE_ROOT = PROJECT / "research" / "wp2" / "p2p_u_v2_eng_2026-09-25"
PROGRESS_FILE = EVIDENCE_ROOT / "progress.json"

# Frozen deterministic order: sorted ENG task ids; 9258154b8a0b (zero-node,
# P2P-U UNDEFINED) is recorded but never executed.
ENG_TASKS = [
    "saleor-rc-2d45b76a52f2",
    "saleor-rc-39b4138e8550",
    "saleor-rc-74538ea00ce9",
    "saleor-rc-82c56bde0e34",
    "saleor-rc-8f76ddc6267f",
    "saleor-rc-9258154b8a0b",  # UNDEFINED (zero candidates) - no execution
    "saleor-rc-d220843b5418",
    "saleor-rc-dfe77ac1c5dc",
    "saleor-rc-e03ee76d2b89",
]


def cap_done(task_id: str, cap: int) -> bool:
    mf = EVIDENCE_ROOT / task_id / f"cap{cap}" / "A" / "manifest.json"
    if not mf.exists():
        return False
    try:
        m = json.loads(mf.read_text(encoding="utf-8"))
    except Exception:
        return False
    return bool(m.get("evidence_integrity", {}).get("ok"))


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_progress(progress: dict) -> None:
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(progress, indent=1, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default=None)
    ap.add_argument("--cap", type=int, default=None, choices=(200, 400))
    args = ap.parse_args()

    tasks = [args.task] if args.task else ENG_TASKS
    caps = [args.cap] if args.cap else [200, 400]
    progress = load_progress()
    exit_code = 0
    for tid in tasks:
        for cap in caps:
            if tid == "saleor-rc-9258154b8a0b":
                progress[tid] = {"cap": None, "status": "UNDEFINED_ZERO_CANDIDATES", "skipped": True}
                save_progress(progress)
                print(f"[skip] {tid}: P2P-U UNDEFINED (zero candidates)", flush=True)
                continue
            if cap_done(tid, cap):
                progress[tid] = {**progress.get(tid, {}), f"cap{cap}": "DONE"}
                save_progress(progress)
                print(f"[skip] {tid} cap{cap}: already complete+verified", flush=True)
                continue
            t0 = time.monotonic()
            print(f"\n=== RUN {tid} cap{cap} ===", flush=True)
            r = subprocess.run(
                [sys.executable, str(PROJECT / "scripts" / "wp2_p2p_u_v2_exec.py"),
                 "--task", tid, "--cap", str(cap), "--run-label", "A"],
                capture_output=True, text=True,
            )
            wall = round(time.monotonic() - t0, 1)
            ok = cap_done(tid, cap)
            progress[tid] = {**progress.get(tid, {}), f"cap{cap}": "DONE" if ok else "FAILED"}
            progress[tid]["_last"] = {"cap": cap, "wall_s": wall, "rc": r.returncode}
            save_progress(progress)
            print(f"[{tid} cap{cap}] rc={r.returncode} verified={ok} wall={wall}s", flush=True)
            if not ok:
                print("---- exec tail ----", flush=True)
                print((r.stdout or r.stderr)[-3000:], flush=True)
                exit_code = 2
    print("\nPROGRESS:", json.dumps(progress, indent=1))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
