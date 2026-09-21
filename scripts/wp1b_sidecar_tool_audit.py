#!/usr/bin/env python3
"""WP-1b Calibration-3 tool-call audit (ZERO API).

Mechanically re-derives the per-call and per-task tool-call classification
from a wp1b_call_sidecar.jsonl produced by the WP-1b agent telemetry (G10).

Each sidecar record is classified as exactly one of:
  final                       the reserved call-8 forced final answer
  tool_ok                     a tool call that returned data (list_files /
                              search_text with results, or a successful
                              read_file)
  tool_error:<message>        a tool call that failed with a tool error
  rejected_repeat             a repeated identical tool request rejected by
                              the control loop (no tool invoked)

Classification rules (mechanical, not prose):
  1. action == "final"                     -> final
  2. action == ""  and not force_final     -> rejected_repeat
     (the model asked for a tool but the request was rejected as a repeated
     identical request; the strategy never invoked the tool, so the sidecar
     action stays empty)
  3. otherwise (action is a real tool):
       prefer the recorded tool_ok / tool_error fields when present (A4);
       otherwise fall back to matching tool_output_chars_raw against the
       exact lengths of the frozen error-message catalog of
       src/benchmark/strategies/repository_tools.py and classify an exact
       match as tool_error:<message> and everything else as tool_ok.

The script also emits the ERROR_CATALOG with each message classified into the
three conceptual classes (INSTRUMENT_ERROR / AGENT_MISUSE /
FROZEN_POLICY_LIMIT) used by gate v2 (CG-10).

Usage:
  python scripts/wp1b_sidecar_tool_audit.py <calibration_dir> [--out <audit.json>]

Output:
  <calibration_dir>/wp1b_tool_audit.json   (or --out)

Exit codes:
  0  audit written
  2  input error
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.strategies.repository_tools import (  # noqa: E402
    MAX_DISTINCT_FILES,
)

# ---------------------------------------------------------------------------
# Frozen error-message catalog (mirrors repository_tools.py exactly).
# The 30 is substituted at runtime via f-string; the catalog stores the exact
# message as produced for the frozen MAX_DISTINCT_FILES = 30.
# ---------------------------------------------------------------------------
LIMIT_ERROR = f"Max distinct files limit ({MAX_DISTINCT_FILES}) reached"

ERROR_CATALOG: dict[str, str] = {
    LIMIT_ERROR: "INSTRUMENT_ERROR",
    "Cannot read file": "INSTRUMENT_ERROR",
    "Skipped path": "INSTRUMENT_ERROR",
    "Invalid path": "AGENT_MISUSE",
    "Not a file": "AGENT_MISUSE",
    "Not a directory": "AGENT_MISUSE",
    "Not a file or directory": "AGENT_MISUSE",
    "Empty query": "AGENT_MISUSE",
    "File too large": "FROZEN_POLICY_LIMIT",
    "Binary file": "FROZEN_POLICY_LIMIT",
}

# Length -> list of messages (used only when tool_ok/tool_error are absent).
_ERROR_LENGTH_MAP: dict[int, list[str]] = {}
for _msg, _cls in ERROR_CATALOG.items():
    _ERROR_LENGTH_MAP.setdefault(len(_msg), []).append(_msg)

_KNOWN_LENGTHS: frozenset[int] = frozenset(len(m) for m in ERROR_CATALOG)


def error_class(message: str) -> str:
    """Map a tool error message to its conceptual class (CG-10 vocabulary).

    Unknown messages are classified as INSTRUMENT_ERROR (fail-closed): a tool
    error that is not a documented agent misuse or frozen policy limit is an
    instrument condition.
    """
    if message in ERROR_CATALOG:
        return ERROR_CATALOG[message]
    if message.startswith("Max distinct files limit ("):
        return "INSTRUMENT_ERROR"
    return "INSTRUMENT_ERROR"


def classify_record(record: dict[str, Any]) -> str:
    """Return the per-call classification string for one sidecar record."""
    action = record.get("action", "")
    force_final = bool(record.get("force_final", False))
    if action == "final":
        return "final"
    if action == "" and not force_final:
        return "rejected_repeat"
    # action is a real tool call (list_files | read_file | search_text)
    tool_ok = record.get("tool_ok")
    tool_error = record.get("tool_error")
    if tool_ok is not None or tool_error is not None:
        return "tool_ok" if tool_ok else f"tool_error:{tool_error or ''}"
    # Legacy records (Calibration-3, pre-A4): reconstruct from the recorded
    # output/error char count against the frozen error-message lengths.
    raw = int(record.get("tool_output_chars_raw", 0))
    if raw in _KNOWN_LENGTHS:
        msgs = _ERROR_LENGTH_MAP[raw]
        if len(msgs) == 1:
            return f"tool_error:{msgs[0]}"
    return "tool_ok"


def audit_sidecar(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify every call and aggregate per task.

    Returns a dict with per-call classification (in sidecar order), the
    aggregate counts, per-task tallies, and the successful-read count.
    """
    per_call: list[dict[str, Any]] = []
    per_task: dict[str, dict[str, Any]] = {}
    for rec in records:
        cls = classify_record(rec)
        per_call.append({
            "task_id": rec.get("task_id", ""),
            "call_index": rec.get("call_index", 0),
            "classification": cls,
        })
        tid = rec.get("task_id", "")
        agg = per_task.setdefault(tid, {
            "task_id": tid,
            "final": 0,
            "tool_ok": 0,
            "tool_error": 0,
            "tool_error_messages": {},
            "rejected_repeat": 0,
            "successful_reads": 0,
        })
        if cls == "final":
            agg["final"] += 1
        elif cls == "tool_ok":
            agg["tool_ok"] += 1
            if rec.get("action") == "read_file":
                agg["successful_reads"] += 1
        elif cls == "rejected_repeat":
            agg["rejected_repeat"] += 1
        elif cls.startswith("tool_error:"):
            agg["tool_error"] += 1
            msg = cls.split(":", 1)[1]
            agg["tool_error_messages"][msg] = agg["tool_error_messages"].get(msg, 0) + 1

    total_final = sum(a["final"] for a in per_task.values())
    total_ok = sum(a["tool_ok"] for a in per_task.values())
    total_err = sum(a["tool_error"] for a in per_task.values())
    total_rep = sum(a["rejected_repeat"] for a in per_task.values())
    total_successful_reads = sum(a["successful_reads"] for a in per_task.values())

    return {
        "artifact": "wp1b_tool_audit",
        "classification": per_call,
        "per_task": sorted(per_task.values(), key=lambda a: a["task_id"]),
        "aggregate": {
            "final": total_final,
            "tool_ok": total_ok,
            "tool_error": total_err,
            "rejected_repeat": total_rep,
            "successful_reads": total_successful_reads,
            "calls": total_final + total_ok + total_err + total_rep,
        },
        "error_catalog": {
            msg: ERROR_CATALOG[msg] for msg in sorted(ERROR_CATALOG)
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("calibration_dir", help="calibration results directory")
    parser.add_argument("--out", help="output audit path (default <dir>/wp1b_tool_audit.json)")
    args = parser.parse_args(argv)

    cal_dir = Path(args.calibration_dir)
    sidecar_path = cal_dir / "wp1b_call_sidecar.jsonl"
    if not sidecar_path.is_file():
        print(f"[audit] ERROR: sidecar not found: {sidecar_path}")
        return 2
    records = []
    for line in sidecar_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    if not records:
        print(f"[audit] ERROR: empty sidecar: {sidecar_path}")
        return 2

    audit = audit_sidecar(records)
    out = Path(args.out) if args.out else cal_dir / "wp1b_tool_audit.json"
    out.write_text(json.dumps(audit, indent=1), encoding="utf-8")

    agg = audit["aggregate"]
    print(f"[audit] calls={agg['calls']} final={agg['final']} "
          f"tool_ok={agg['tool_ok']} tool_error={agg['tool_error']} "
          f"rejected_repeat={agg['rejected_repeat']} "
          f"successful_reads={agg['successful_reads']}")
    for ta in audit["per_task"]:
        print(f"[audit] task {ta['task_id']}: final={ta['final']} "
              f"ok={ta['tool_ok']} err={ta['tool_error']} "
              f"reject={ta['rejected_repeat']} reads={ta['successful_reads']}")
    print(f"[audit] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
