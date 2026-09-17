#!/usr/bin/env python3
"""RealCommitImpactDataset-Saleor — Sparse development-inference executor.

LIVE API, authorized (continuation mission, Block C re-authorized 2026-09-17):
cells <= 450, tokens <= 9M, cost <= $3.00. Runs Saleor DEV_TRAIN +
DEV_VALIDATION
(150 cases x 3 reps = 450 cells) with the frozen Sparse-v2 config
(qwen/qwen3-coder @ deepinfra/turbo, temp 0, cap 16384, Graph OFF).
INTERNAL_TEST / RESERVE never called.

Subcommands:
  run     execute remaining manifest cells (resumable, raw persisted)
  close   closure gates + audit
"""

# ruff: noqa: E501
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.real_commits import p1_evaluation as p1  # noqa: E402
from scripts.saleor_inference_manifest import (  # noqa: E402
    COST_CEILING_USD,
    DATASET_DIR,
    TOKEN_CEILING,
    build_saleor_manifest,
)

STUDY_DIR = _PROJECT_DIR / "research" / "saleor-sparse-inference"
GATES_JSON = _PROJECT_DIR / "reports" / "saleor_inference_gates.json"

MODEL = p1.P1_MODEL
PROVIDER_TAG = p1.P1_PROVIDER_TAG
CAP = p1.P1_MAX_COMPLETION_TOKENS
MAX_TRANSIENT_RETRIES = 4
RETRY_BACKOFF_SECONDS = 20.0
SCHEMA_NAME = "real_commit_p1_common"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _persist_json(name: str, payload: Any) -> Path:
    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    path = STUDY_DIR / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _records_path() -> Path:
    return STUDY_DIR / "saleor_dev_run_records.jsonl"


def _loaded_records() -> dict[str, dict[str, Any]]:
    path = _records_path()
    if not path.is_file():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            out[rec["run_id"]] = rec
    return out


def _append_record(record: dict[str, Any]) -> None:
    _records_path().parent.mkdir(parents=True, exist_ok=True)
    with _records_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _gates_passed() -> bool:
    if not GATES_JSON.is_file():
        return False
    return bool(json.loads(GATES_JSON.read_text(encoding="utf-8")).get("all_passed"))


def _raw_openrouter_call(schema: dict[str, Any], prompt: str) -> dict[str, Any]:
    import urllib.error
    import urllib.request

    from benchmark.llm.openrouter_backend import (
        _redact,
        _safe_error_from_http_error,
        _safe_exc_message,
    )

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"').strip("'").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": p1.P1_TEMPERATURE,
        "max_tokens": CAP,
        "stream": False,
        "response_format": {"type": "json_schema", "json_schema": {"name": SCHEMA_NAME, "strict": True, "schema": schema}},
        "provider": {"order": [PROVIDER_TAG], "allow_fallbacks": False, "require_parameters": True},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    last_error: BaseException | None = None
    for attempt in range(1, MAX_TRANSIENT_RETRIES + 1):
        if attempt > 1:
            print(f"  retrying in {RETRY_BACKOFF_SECONDS:.0f}s (attempt {attempt}/{MAX_TRANSIENT_RETRIES})", flush=True)
            time.sleep(RETRY_BACKOFF_SECONDS)
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                raw = resp.read()
            return {"ok": True, "attempt": attempt, "raw": raw.decode("utf-8"), "dispatched": True}
        except Exception as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError):
                msg = _redact(_safe_error_from_http_error(exc, api_key), api_key)
            else:
                msg = _redact(_safe_exc_message(exc), api_key)
            print(f"  call attempt {attempt}/{MAX_TRANSIENT_RETRIES} failed: {msg}")
    return {"ok": False, "error": str(last_error), "dispatched": True}


def _render_cell_prompt(cell: dict[str, Any]) -> str:
    bundle = p1.load_case_public_bundle(DATASET_DIR, cell["case_id"])
    mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
    return str(p1.render_p1_sparse_prompt(case=bundle, mapping=mapping))


def _build_cell_evidence(cell, prompt, result, elapsed, pricing) -> dict[str, Any]:
    raw_text = result.get("raw") if result.get("ok") else None
    raw_sha = _sha256_text(raw_text) if raw_text is not None else ""
    entry = {
        "run_id": cell["run_id"], "case_id": cell["case_id"], "repetition": cell["repetition"],
        "arm": "sparse_v2", "serialization_policy": "sparse_v2",
        "scientific_model": MODEL, "provider_tag": PROVIDER_TAG,
        "exact_model": f"openrouter:{MODEL}@{PROVIDER_TAG}",
        "temperature": p1.P1_TEMPERATURE, "completion_cap": CAP, "graph": "OFF",
        "request_dispatched": bool(result.get("dispatched", True)),
        "prompt_sha256": _sha256_text(prompt),
        "raw_response_sha256": raw_sha, "latency_seconds": round(elapsed, 6), "recorded_at": _now_iso(),
    }
    proxy = set(p1.load_hidden_proxy_paths(DATASET_DIR, cell["case_id"]))
    if not result.get("ok"):
        entry.update({
            "terminal_status": "failed", "schema_valid": False, "finish_reason": "",
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "model_calls": 0,
            "api_cost": 0.0, "failure_category": result.get("error", "transport failed"),
            "tp": 0, "fp": 0, "fn": len(proxy), "precision": 0.0, "recall": 0.0, "f1": 0.0,
            "fnr": 1.0, "full_recall": False, "proxy_size": len(proxy),
            "serialized_decision_count": 0, "decoded_write_set_ids": [], "predicted_write_set": [],
            "predicted_write_set_size": 0, "raw_response_persisted": False, "usage_known": False,
        })
        return entry
    parsed = json.loads(raw_text or "{}")
    choice = (parsed.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = message.get("content") or ""
    finish_reason = choice.get("finish_reason", "")
    provider_name = parsed.get("provider")
    if isinstance(provider_name, dict):
        provider_name = provider_name.get("provider_name")
    usage = parsed.get("usage") or {}
    pt = int(usage.get("prompt_tokens") or 0)
    ct = int(usage.get("completion_tokens") or 0)
    usage_known = usage.get("prompt_tokens") is not None and usage.get("completion_tokens") is not None
    cap_hit = finish_reason == "length"
    api_cost = round(pt * float(pricing["prompt_per_token_usd"]) + ct * float(pricing["completion_per_token_usd"]), 6)
    entry.update({
        "provider_response_received": True, "raw_response_persisted": True, "usage_known": usage_known,
        "provider_name": provider_name, "finish_reason": finish_reason, "truncation_status": cap_hit,
        "prompt_tokens": pt, "completion_tokens": ct, "total_tokens": pt + ct, "model_calls": 1,
        "api_cost": api_cost, "pricing_source": pricing.get("source", ""),
    })
    validator_errors: list[str] = []
    decoded_ids: list[int] = []
    serialized = 0
    if content:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            payload = None
            validator_errors.append(str(exc))
        if isinstance(payload, dict):
            vres = p1.validate_p1_sparse(payload, candidate_count=cell["candidate_count"])
            validator_errors = list(vres.get("errors") or [])
            decoded_ids = vres.get("decoded_write_set_ids") or []
            decisions = payload.get("decisions")
            if isinstance(decisions, list):
                serialized = len(decisions)
    entry.update({
        "schema_valid": not validator_errors, "failure_category": "; ".join(validator_errors),
        "serialized_decision_count": serialized, "decoded_write_set_ids": decoded_ids,
        "predicted_write_set_size": len(decoded_ids),
    })
    terminal = "succeeded" if (not validator_errors and not cap_hit) else "failed"
    bundle = p1.load_case_public_bundle(DATASET_DIR, cell["case_id"])
    mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
    write_set = {mapping.path_for(i) for i in decoded_ids}
    m = p1.p1_selection_metrics(write_set, proxy)
    entry.update({
        "terminal_status": terminal, "predicted_write_set": sorted(write_set),
        "hidden_proxy_used_after_inference": sorted(proxy),
        "tp": m["tp"], "fp": m["fp"], "fn": m["fn"], "precision": round(m["precision"], 6),
        "recall": round(m["recall"], 6), "f1": round(m["f1"], 6), "fnr": round(m["fnr"], 6),
        "full_recall": m["full_recall"], "proxy_size": m["proxy_size"],
    })
    return entry


def cmd_run(args: argparse.Namespace) -> int:
    if not _gates_passed() and not args.skip_gate_check:
        print("Refusing to run before Saleor gates pass.")
        return 2
    cells = build_saleor_manifest()
    records = _loaded_records()
    if len(records) >= len(cells):
        print(f"Already complete: {len(records)}/{len(cells)}")
        return 0
    pricing = {
        "prompt_per_token_usd": 0.30 / 1_000_000,
        "completion_per_token_usd": 1.00 / 1_000_000,
        "source": "frozen DeepInfra-through-OpenRouter pricing ($0.30/$1.00 per 1M)",
    }
    pending = [c for c in cells if c["run_id"] not in records]
    limit = args.limit if args.limit and args.limit > 0 else len(pending)
    batch = pending[:limit]
    print(f"RUNNING_BATCH={len(batch)} pending={len(pending)}")
    for idx, cell in enumerate(batch, start=1):
        prompt = _render_cell_prompt(cell)
        schema = p1.p1_common_schema(cell["candidate_count"])
        t0 = time.monotonic()
        result = _raw_openrouter_call(schema, prompt)
        elapsed = time.monotonic() - t0
        evidence = _build_cell_evidence(cell, prompt, result, elapsed, pricing)
        _append_record(evidence)
        records[cell["run_id"]] = evidence
        _write_bytes(STUDY_DIR / "saleor_dev_runs" / f"{cell['run_id']}.json", json.dumps(evidence, indent=2, default=str).encode("utf-8"))
        if result.get("ok") and result.get("raw") is not None:
            rawdir = STUDY_DIR / "saleor_dev_runs" / "raw"
            _write_bytes(rawdir / f"{cell['run_id']}.txt", result["raw"].encode("utf-8"))
            _write_bytes(rawdir / f"{cell['run_id']}.sha256", (evidence["raw_response_sha256"] + "\n").encode("utf-8"))
        print(f"[{idx}/{len(batch)}] {cell['run_id']} {evidence['terminal_status']} tok={evidence['total_tokens']} cost={evidence['api_cost']}", flush=True)
        # budget check
        tot_tok = sum(int(r["total_tokens"]) for r in records.values())
        tot_cost = round(sum(float(r.get("api_cost", 0.0)) for r in records.values()), 6)
        if tot_tok > TOKEN_CEILING or tot_cost > COST_CEILING_USD:
            print(f"BUDGET_STOP tokens={tot_tok} cost={tot_cost}")
            _persist_json("saleor_dev_closure.json", {"budget_stopped": True, "tokens": tot_tok, "cost": tot_cost, "ran_at": _now_iso()})
            return 1
    _persist_json("saleor_dev_checkpoint_final.json", {"completed": len(records), "total_cells": len(cells), "ran_at": _now_iso()})
    print(f"BATCH_COMPLETE {len(records)}/{len(cells)}")
    return 0


def cmd_close(_args: argparse.Namespace) -> int:
    records = _loaded_records()
    cells = build_saleor_manifest()
    tot_tok = sum(int(r["total_tokens"]) for r in records.values())
    tot_cost = round(sum(float(r.get("api_cost", 0.0)) for r in records.values()), 6)
    result = {
        "study_id": "real-commit-impact-saleor-dev-inference",
        "gates_all_passed": _gates_passed(),
        "manifest_cells": len(cells),
        "recorded_cells": len(records),
        "run_complete": len(records) == len(cells),
        "valid": sum(1 for r in records.values() if r["terminal_status"] == "succeeded"),
        "failed": sum(1 for r in records.values() if r["terminal_status"] != "succeeded"),
        "total_tokens": tot_tok, "total_cost_usd": tot_cost,
        "token_ceiling": TOKEN_CEILING, "cost_ceiling_usd": COST_CEILING_USD,
        "token_ceiling_respected": tot_tok <= TOKEN_CEILING,
        "cost_ceiling_respected": tot_cost <= COST_CEILING_USD,
        "independent_tasks": len({r["case_id"] for r in records.values()}),
        "nested_repetitions": 3,
        "no_replacement_reruns": True, "no_result_dependent_reruns": True,
        "ran_at": _now_iso(),
    }
    _persist_json("saleor_dev_closure.json", result)
    for k, v in result.items():
        print(f"{k}={v}")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run")
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--skip-gate-check", action="store_true", default=False)
    sub.add_parser("close")
    return p


def main() -> int:
    args = build_arg_parser().parse_args()
    if args.command == "run":
        return cmd_run(args)
    return cmd_close(args)


if __name__ == "__main__":
    raise SystemExit(main())
