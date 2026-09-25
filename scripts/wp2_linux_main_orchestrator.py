#!/usr/bin/env python3
"""WP-2 C2 MAIN 220 orchestrator (orchestration ONLY - no semantic changes).

Thin driver that invokes the frozen C2 runner (scripts/wp2_linux_main_sweep.py)
in chunks of 4, sequentially, until all 220 changed-test MAIN candidates are
processed. Uses the per-task JSONL resume/checkpoint records; never reruns
completed tasks; stops on a failure-spike or stop-flag condition; writes a
persistent c2_progress.json (completed/220, current chunk/task, elapsed,
rolling median task runtime, ETA, classification counts, env-fail count, last
heartbeat).

Orchestration only: does not alter oracle semantics, runner parameters, worker
count, 3/3 policy, Postgres settings, image digests, test selection, or
classification rules.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
RUN_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
PER_TASK = Path(os.environ.get("WP2_PER_TASK", RUN_ROOT / "per_task_v2.jsonl"))
PROGRESS = Path(os.environ.get("WP2_PROGRESS", RUN_ROOT / "c2_progress.json"))
MASTER_LOG = Path(os.environ.get("WP2_MASTER_LOG", PROJECT / "logs" / "c2_orchestrator.log"))
STOP_FLAG = Path(os.environ.get("WP2_STOP_FLAG", PROJECT / "logs" / "C2_STOP.flag"))
SWEEP = Path(os.environ.get("WP2_SWEEP", PROJECT / "scripts" / "wp2_linux_main_sweep.py"))
CHUNK = 4
TOTAL = int(os.environ.get("WP2_TOTAL", "220"))
MAX_CONSECUTIVE_CRASH = 3
MAX_ERRORS_PER_CHUNK = 4
MAX_CONSECUTIVE_ERRORS = 12
CLASS_FIELDS = ("BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P", "PARENT_COLLECTION_ERROR",
                "FLAKY", "TARGET_ORACLE_INVALID", "P2P_ONLY", "OTHER_REVIEW_REQUIRED")


def load_rows() -> list[dict]:
    rows: list[dict] = []
    if PER_TASK.exists():
        for line in PER_TASK.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_progress(*, rows: list[dict], completed: int, current_chunk: int,
                   current_task: str | None, elapsed_s: float, status: str,
                   last_chunk_wall_s: float) -> None:
    walls = [r["wall_s"] for r in rows if r.get("wall_s")]
    window = walls[-20:]
    rolling_median = statistics.median(window) if window else None
    eta_s = (TOTAL - completed) * rolling_median if rolling_median else None
    counts = {f: sum(r.get("counts", {}).get(f, 0) for r in rows) for f in CLASS_FIELDS}
    env_fail = sum(1 for r in rows if r.get("status") in ("ENV_UNAVAILABLE", "ERROR"))
    progress = {
        "completed": completed,
        "total": TOTAL,
        "current_chunk": current_chunk,
        "current_task": current_task,
        "elapsed_s": round(elapsed_s, 1),
        "last_chunk_wall_s": round(last_chunk_wall_s, 1),
        "rolling_median_runtime_s": round(rolling_median, 1) if rolling_median else None,
        "eta_s": round(eta_s, 0) if eta_s else None,
        "classification_counts": counts,
        "env_fail_count": env_fail,
        "status": status,
        "last_heartbeat": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    PROGRESS.write_text(json.dumps(progress, indent=1, ensure_ascii=False), encoding="utf-8")


def log(msg: str) -> None:
    with open(MASTER_LOG, "a", encoding="utf-8") as fh:
        fh.write(f"[{datetime.now(UTC).isoformat(timespec='seconds')}] {msg}\n")


def main() -> int:
    start = time.monotonic()
    chunk_idx = 0
    consecutive_crash = 0
    while True:
        rows = load_rows()
        completed = len(rows)
        if completed >= TOTAL:
            write_progress(rows=rows, completed=completed, current_chunk=chunk_idx,
                           current_task=None, elapsed_s=time.monotonic() - start,
                           status="COMPLETE", last_chunk_wall_s=0.0)
            log(f"COMPLETE: {completed}/{TOTAL}")
            break
        if STOP_FLAG.exists():
            write_progress(rows=rows, completed=completed, current_chunk=chunk_idx,
                           current_task=None, elapsed_s=time.monotonic() - start,
                           status="STOPPED", last_chunk_wall_s=0.0)
            log("STOP_FLAG present; stopped gracefully.")
            break
        chunk_idx += 1
        log(f"chunk {chunk_idx}: completed before={completed}/{TOTAL}")
        rows_before = rows
        t0 = time.monotonic()
        r = subprocess.run(
            [sys.executable, str(SWEEP), "--start", "0", "--max-tasks", str(CHUNK)],
            capture_output=True, text=True, encoding="utf-8", timeout=7200,
        )
        chunk_wall = time.monotonic() - t0
        with open(MASTER_LOG, "a", encoding="utf-8") as fh:
            fh.write(r.stdout[-3000:])
            fh.write(r.stderr[-1000:])
        rows = load_rows()
        completed = len(rows)
        if r.returncode != 0:
            consecutive_crash += 1
            if consecutive_crash >= MAX_CONSECUTIVE_CRASH:
                write_progress(rows=rows, completed=completed, current_chunk=chunk_idx,
                               current_task=None, elapsed_s=time.monotonic() - start,
                               status=f"STOPPED_CRASH_RC={r.returncode}", last_chunk_wall_s=chunk_wall)
                log(f"CRASH_SPIKE: {consecutive_crash} consecutive chunk crashes; stopping.")
                break
        else:
            consecutive_crash = 0
        # Per-chunk spike: errors ADDED in THIS chunk, not cumulative total.
        def fail_status(x: dict) -> bool:
            return x.get("status") in ("ENV_UNAVAILABLE", "ERROR")

        rows_before_set = {x["task_id"] for x in rows_before}
        added = [x for x in rows if x["task_id"] not in rows_before_set]
        errors_added = sum(1 for x in added if fail_status(x))
        # trailing consecutive env/error records at the tail of the file
        trailing = 0
        for x in reversed(rows):
            if fail_status(x):
                trailing += 1
            else:
                break
        chunk_spike = errors_added >= MAX_ERRORS_PER_CHUNK
        if chunk_spike or trailing >= MAX_CONSECUTIVE_ERRORS:
            write_progress(rows=rows, completed=completed, current_chunk=chunk_idx,
                           current_task=rows[-1]["task_id"] if rows else None,
                           elapsed_s=time.monotonic() - start,
                           status=f"STOPPED_ERROR_SPIKE=chunk:{errors_added},trailing:{trailing}",
                           last_chunk_wall_s=chunk_wall)
            log(f"ERROR_SPIKE: chunk_added={errors_added} trailing_consecutive={trailing}; stopping.")
            break
        last_task = rows[-1]["task_id"] if rows else None
        write_progress(rows=rows, completed=completed, current_chunk=chunk_idx,
                       current_task=last_task, elapsed_s=time.monotonic() - start,
                       status="RUNNING", last_chunk_wall_s=chunk_wall)
        log(f"chunk {chunk_idx} done: completed={completed}/{TOTAL} wall={chunk_wall:.1f}s")
        time.sleep(2)
    return 0


if __name__ == "__main__":
    import statistics
    raise SystemExit(main())
