"""WP-1b prediction freeze (label-free): run records -> frozen predictions + SHA-256.

The freeze is built ONLY from the runner's own records. It is committed and
tagged BEFORE any label is loaded (AC-10). Nothing here reads labels.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from benchmark.wp1b.main_runner import (
    RECORDS_FILE,
    SUMMARY_FILE,
    WorkItem,
    prediction_sha256,
    read_jsonl_tolerant,
)

FREEZE_FILE = "wp1b_agent_predictions.json"


class FreezeError(RuntimeError):
    """The run directory cannot be frozen as a valid prediction set."""


def build_freeze(
    run_dir: Path,
    items: Sequence[WorkItem],
    *,
    kind: str,
    allow_main50_fallback: bool = False,
) -> dict[str, Any]:
    records, bad = read_jsonl_tolerant(run_dir / RECORDS_FILE)
    if bad:
        raise FreezeError(f"{len(bad)} torn record lines; resume the run before freezing")
    by_key: dict[str, dict[str, Any]] = {}
    for r in records:
        key = str(r["work_key"])
        if key in by_key:
            raise FreezeError(f"duplicate record for {key}")
        by_key[key] = r
    expected = [it.key for it in items]
    summary_path = run_dir / SUMMARY_FILE
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    status = str(summary.get("status", ""))
    fallback = False
    if set(by_key) != set(expected):
        missing = [k for k in expected if k not in by_key]
        extra = sorted(set(by_key) - set(expected))
        if extra:
            raise FreezeError(f"records outside the manifest: {extra[:5]}")
        first50 = expected[:50]
        if not (allow_main50_fallback and kind == "main297" and all(k in by_key for k in first50)
                and status.startswith("H1_BUDGET_ABORT")):
            raise FreezeError(f"{len(missing)} manifest items have no record (first: {missing[:3]})")
        fallback = True
        expected = first50
    elif status != "COMPLETE":
        raise FreezeError(f"run summary status is {status!r}, expected COMPLETE")

    per: dict[str, dict[str, Any]] = {}
    for key in expected:
        r = by_key[key]
        paths = sorted(str(p) for p in r["selected_paths"])
        if prediction_sha256(paths) != r["prediction_sha256"]:
            raise FreezeError(f"prediction hash mismatch in record {key}")
        if r.get("allow_ground_truth_universe") is not False:
            raise FreezeError(f"allow_ground_truth_universe must be False ({key})")
        tok = r["token_usage"]
        per[key] = {
            "task_id": r["task_id"],
            "replicate": int(r.get("replicate", 0)),
            "selected_paths": paths,
            "prediction_sha256": r["prediction_sha256"],
            "prediction_empty": bool(r["prediction_empty"]),
            "empty_reason": r["empty_reason"],
            "infra_failure": bool(r.get("infra_failure", False)),
            "forced_final": bool(r.get("forced_final", False)),
            "model_calls": int(r["model_calls"]),
            "http_attempts": int(r.get("http_attempts", 0)),
            "prompt_tokens": int(tok["prompt_tokens"]),
            "completion_tokens": int(tok["completion_tokens"]),
            "total_tokens": int(tok["total_tokens"]),
            "usd_cost": float(tok["usd_cost"]),
            "latency_s_sum": float(r.get("latency_s_sum", 0.0)),
            "wall_seconds": float(r.get("wall_seconds", 0.0)),
        }
    empty = sum(1 for v in per.values() if v["prediction_empty"])
    return {
        "artifact": "wp1b_agent_predictions",
        "kind": kind,
        "analysis_scope": "MAIN_50_UNDERPOWERED_FALLBACK" if fallback else ("MAIN_297" if kind == "main297" else kind),
        "protocol": records[0]["protocol"] if records else None,
        "model": records[0]["model"] if records else None,
        "route": records[0]["route"] if records else None,
        "n": len(per),
        "task_ids": expected,
        "empty_count": empty,
        "run_summary": summary,
        "code_sha256": records[0].get("code_sha256") if records else None,
        "labels_used": False,
        "per_task": per,
    }


def write_freeze(run_dir: Path, payload: dict[str, Any]) -> tuple[Path, str]:
    """Write the freeze with LF line endings on every platform and hash those bytes."""
    path = run_dir / FREEZE_FILE
    data = (json.dumps(payload, indent=1, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    (run_dir / (FREEZE_FILE + ".sha256")).write_bytes(f"{digest}  {FREEZE_FILE}\n".encode())
    return path, digest
