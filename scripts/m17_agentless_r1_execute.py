#!/usr/bin/env python3
# ruff: noqa: E501
"""M17 Agentless-style R1 - Phase A8: MAIN_297 execution (frozen protocol).

Executes exactly the frozen 297 Agentless-style file-level localization calls
(one per task, qwen/qwen3-coder @ deepinfra/turbo, temp 0, cap 1024) using the
pre-built offline prompt manifest. Records every call with full accounting and
freezes the per-task predictions.

Subcommands:
  dry-run   deterministic mock responses (ZERO API), used by P2P
  run       real API calls (requires OPENROUTER_API_KEY)

NO adaptive protocol changes after seeing outputs. Hard cost ceiling $2.00.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.agentless_r1.execution import CallEvidence, call_agentless, compute_cost_usd  # noqa: E402
from benchmark.agentless_r1.parser import parse_file_list  # noqa: E402

FREEZE = PROJECT / "research" / "competitor-agentless-r1" / "AGENTLESS_STYLE_ADAPTATION_PROTOCOL_FREEZE.json"
PROMPT_MANIFEST = PROJECT / "research" / "competitor-agentless-r1" / "agentless_r1_prompt_manifest.json"
OUT_DIR = PROJECT / "research" / "competitor-agentless-r1" / "run"

COST_CEILING_USD = 2.0
SYSTEMIC_FAILURE_THRESHOLD = 10


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _records_path() -> Path:
    return OUT_DIR / "agentless_r1_run_records.jsonl"


def _raw_dir() -> Path:
    return OUT_DIR / "raw"


def _load_prompt_manifest() -> dict:
    return json.loads(PROMPT_MANIFEST.read_text(encoding="utf-8"))


def _set_out_dir(out: str | None) -> None:
    global OUT_DIR
    if out:
        OUT_DIR = PROJECT / out


def mock_call_agentless(_prompt: str, _api_key: str) -> CallEvidence:
    """Deterministic mock: returns a fixed fenced 2-file list (ZERO API)."""
    return CallEvidence(
        ok=True,
        dispatched=True,
        attempt_count=1,
        raw_text="```\nsaleor/graphql/page/dataloaders.py\nsaleor/page/models.py\n```",
        prompt_tokens=8000,
        completion_tokens=30,
        api_cost_usd=compute_cost_usd(8000, 30),
    )


def _evidence_to_record(tid: str, prompt: str, ev: CallEvidence, parsed, elapsed: float, source: str) -> dict:
    return {
        "task_id": tid,
        "request_identity": _sha256_text(prompt)[:16],
        "prompt_sha256": _sha256_text(prompt),
        "started_utc": _now_iso(),
        "latency_seconds": round(elapsed, 6),
        "provider": "deepinfra/turbo",
        "model": "qwen/qwen3-coder",
        "temperature": 0.0,
        "max_completion_tokens": 1024,
        "retry_count": (ev.attempt_count - 1) if ev.attempt_count else 0,
        "execution_source": source,
        "dispatched": ev.dispatched,
        "ok": ev.ok,
        "error": ev.error,
        "raw_output_sha256": _sha256_text(ev.raw_text) if ev.raw_text is not None else "",
        "prompt_tokens": ev.prompt_tokens or 0,
        "completion_tokens": ev.completion_tokens or 0,
        "total_tokens": (ev.prompt_tokens or 0) + (ev.completion_tokens or 0),
        "api_cost_usd": ev.api_cost_usd,
        "classification": parsed.classification,
        "parsed_files": list(parsed.top_n_slice),
        "prediction_set": sorted(parsed.prediction_set),
        "dropped_line_count": parsed.dropped_line_count,
        "duplicate_count": parsed.duplicate_count,
        "more_than_top_n": parsed.more_than_top_n,
    }


def _load_records() -> dict[str, dict]:
    path = _records_path()
    if not path.is_file():
        return {}
    out: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            out[str(rec["task_id"])] = rec
    return out


def _append_record(record: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with _records_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _calibration_active() -> bool:
    """One-shot A7 check for M17_ENV_CANON_D7_R3_CALIBRATION_12.

    Detects a live ''python'' process whose command line references a
    Calibration-12 run directory / script. Conservative: any match blocks.
    """
    import subprocess

    try:
        out = subprocess.run(
            ["wmic", "process", "get", "ProcessId,CommandLine"],
            capture_output=True, text=True, check=False, timeout=30,
        ).stdout
    except Exception:
        return True
    markers = ("calibration-12", "calibration_12", "d7_r3_calibration_12", "calibration-12-run")
    for line in out.splitlines():
        low = line.lower()
        if "python" in low and any(m in low for m in markers):
            return True
    return False


def cmd_dry_run(_args: argparse.Namespace) -> int:
    m = _load_prompt_manifest()
    task_ids = list(m["per_task"])
    existing = _load_records()
    done = 0
    for tid in task_ids:
        if tid in existing:
            continue
        row = m["per_task"][tid]
        prompt = row["prompt"]
        file_set = set(row["structure_files"])
        t0 = time.monotonic()
        ev = mock_call_agentless(prompt, "mock")
        elapsed = time.monotonic() - t0
        parsed = parse_file_list(ev.raw_text or "", file_set)
        _append_record(_evidence_to_record(tid, prompt, ev, parsed, elapsed, "dry-run-mock"))
        done += 1
        if (done % 50) == 0:
            print(f"  dry-run [{done}]", flush=True)
    print(f"DRY_RUN_CALLS={done}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if args.check_calibration and _calibration_active():
        print("\nM17_AGENTLESS_MAIN297_PREFLIGHT_COMPLETE_WAITING_FOR_D7_CALIBRATION")
        print("Calibration-12 appears active; not starting API calls.")
        return 3

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"').strip("'").strip()
    if not api_key:
        print("BLOCKED: OPENROUTER_API_KEY not set")
        return 2

    m = _load_prompt_manifest()
    task_ids = list(m["per_task"])
    existing = _load_records()
    pending = [t for t in task_ids if t not in existing]
    print(f"PENDING={len(pending)}/{len(task_ids)}")

    total_cost = sum(float(r.get("api_cost_usd", 0.0)) for r in existing.values())
    consec_fail = 0
    for i, tid in enumerate(pending, start=1):
        row = m["per_task"][tid]
        prompt = row["prompt"]
        file_set = set(row["structure_files"])
        t0 = time.monotonic()
        ev = call_agentless(prompt, api_key)
        elapsed = time.monotonic() - t0
        parsed = parse_file_list(ev.raw_text or "", file_set)
        rec = _evidence_to_record(tid, prompt, ev, parsed, elapsed, "real")
        _append_record(rec)
        if ev.raw_text:
            raw = _raw_dir()
            raw.mkdir(parents=True, exist_ok=True)
            (raw / f"{tid}.txt").write_text(ev.raw_text, encoding="utf-8")
            (raw / f"{tid}.sha256").write_text(_sha256_text(ev.raw_text) + "\n", encoding="utf-8")
        total_cost += ev.api_cost_usd
        consec_fail = 0 if ev.ok else consec_fail + 1
        print(f"[{i}/{len(pending)}] {tid} ok={ev.ok} cls={parsed.classification} tok={rec['total_tokens']} cost={ev.api_cost_usd:.6f} cum={total_cost:.4f}", flush=True)
        if total_cost > COST_CEILING_USD:
            print(f"BUDGET_STOP ceiling={COST_CEILING_USD} reached={total_cost:.4f}")
            break
        if consec_fail >= SYSTEMIC_FAILURE_THRESHOLD:
            print(f"SYSTEMIC_FAILURE_STOP consecutive_failures={consec_fail}")
            break
    print("RUN_TERMINATED", "records", len(_load_records()))


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    d = sub.add_parser("dry-run")
    d.add_argument("--out", type=str, default="research/competitor-agentless-r1/run_dryrun")
    r = sub.add_parser("run")
    r.add_argument("--check-calibration", action="store_true", default=False)
    return p


def main() -> int:
    args = build_arg_parser().parse_args()
    if args.command == "dry-run":
        _set_out_dir(args.out)
        return cmd_dry_run(args)
    return cmd_run(args)


if __name__ == "__main__":
    raise SystemExit(main())
