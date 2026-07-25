#!/usr/bin/env python3
"""Offline report rebuild script.

Rebuilds all derived reporting artifacts from persisted checkpoint.json
and run_records.jsonl.  Requires no GPU, no HF token, no model inference.

Usage:
    python scripts/rebuild_experiment_reports.py <runs-dir>
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/rebuild_experiment_reports.py <runs-dir>")
        return 1

    runs_dir = Path(sys.argv[1])
    if not runs_dir.is_dir():
        print(f"ERROR: {runs_dir} is not a directory")
        return 1

    # --- Hash raw evidence before rebuild ---
    cp_path = runs_dir / "checkpoint.json"
    rec_path = runs_dir / "run_records.jsonl"

    hashes_before: dict[str, str] = {}
    for p in [cp_path, rec_path]:
        if p.is_file():
            hashes_before[p.name] = sha256_of(p)

    # --- Rebuild ---
    from benchmark.checkpoint.reports import rebuild_experiment_reports, ReportRebuildError

    try:
        audit = rebuild_experiment_reports(runs_dir)
    except ReportRebuildError as exc:
        print(f"FAILED: {exc}")
        return 1

    # --- Hash raw evidence after rebuild ---
    hashes_after: dict[str, str] = {}
    for p in [cp_path, rec_path]:
        if p.is_file():
            hashes_after[p.name] = sha256_of(p)

    # --- Verify raw evidence unchanged ---
    raw_unchanged = hashes_before == hashes_after

    # --- Print audit report ---
    print("=== Report Rebuild Audit ===")
    print(f"Runs directory:        {runs_dir}")
    print(f"Raw RunRecord count:   {audit['raw_run_record_count']}")
    print(f"Planned Run ID count:  {audit['planned_run_id_count']}")
    print(f"Matched Run IDs:       {len(audit['matched_run_ids'])}")
    print(f"Missing Run IDs:       {len(audit['missing_run_ids'])}")
    print(f"Duplicate Run IDs:     {len(audit['duplicate_run_ids'])}")
    print(f"Unexpected Run IDs:    {len(audit['unexpected_run_ids'])}")
    print()
    print(f"Total model calls:     {audit['token_totals']['total_model_calls']}")
    print(f"Total prompt tokens:   {audit['token_totals']['total_prompt_tokens']}")
    print(f"Total completion tok:  {audit['token_totals']['total_completion_tokens']}")
    print(f"Total tokens:          {audit['token_totals']['total_tokens']}")
    print()
    print(f"Experiment duration:   {audit['duration_totals']['experiment_run_duration_seconds']:.6f}s")
    print(f"Final status:          {audit['final_status']}")
    print(f"Succeeded:             {audit['total_succeeded']}")
    print(f"Failed:                {audit['total_failed']}")
    print(f"Retryable:             {audit['total_retryable']}")
    print(f"Pending:               {audit['total_pending']}")
    print()

    if audit["missing_run_ids"]:
        print(f"Missing: {audit['missing_run_ids']}")
    if audit["duplicate_run_ids"]:
        print(f"Duplicates: {audit['duplicate_run_ids']}")
    if audit["unexpected_run_ids"]:
        print(f"Unexpected: {audit['unexpected_run_ids']}")

    print()
    print("Raw evidence hashes:")
    for name, h in sorted(hashes_before.items()):
        changed = h != hashes_after.get(name)
        status = "CHANGED" if changed else "OK"
        print(f"  {name}: {h[:16]}... [{status}]")

    print()
    if raw_unchanged:
        print("Raw evidence: UNCHANGED (as expected)")
    else:
        print("WARNING: Raw evidence was modified during rebuild!")
        return 1

    # --- Validate consistency ---
    errors = 0
    if audit["missing_run_ids"]:
        print(f"ERROR: {len(audit['missing_run_ids'])} missing Run IDs")
        errors += 1
    if audit["duplicate_run_ids"]:
        print(f"ERROR: {len(audit['duplicate_run_ids'])} duplicate Run IDs")
        errors += 1
    if audit["unexpected_run_ids"]:
        print(f"ERROR: {len(audit['unexpected_run_ids'])} unexpected Run IDs")
        errors += 1

    if errors:
        print(f"\nFAILED: {errors} inconsistency error(s)")
        return 1

    print("\nREPORTS REBUILT SUCCESSFULLY")
    return 0


if __name__ == "__main__":
    sys.exit(main())
