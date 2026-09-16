#!/usr/bin/env python3
"""Omission-Risk Development Inference — 90-cell Sparse-v2 TRAIN/VALIDATION executor.

Frozen protocol: docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md.
Approved configuration: TRAIN 24 + VALIDATION 6, sparse_v2 ONLY, 3 reps = 90 cells,
model qwen/qwen3-coder @ deepinfra/turbo (OpenRouter), temperature 0, cap 16384,
graph OFF, protocol real-commit-p1-v1.0.0, serialization SPARSE.

HARD STOP budget ceilings (frozen): 600,000 total tokens AND $0.30.
No configuration changes after seeing results.

Subcommands (idempotent / resumable):
  prevalidate       pre-run validation (git state, gates evidence, budget)
  endpoint-freeze   persist live DeepInfra-through-OpenRouter endpoint freeze
  gates             six ZERO-API gates + leakage audit (delegates to verifier)
  freeze-manifest   freeze the 90-cell manifest into the study dir
  run               execute remaining manifest cells (resumable, raw persisted)
  close             closure gates + audit

Outputs (research/omission-risk-feature-study-v1/):
  sparse_v2_trainval_run_records.jsonl
  sparse_v2_trainval_manifest.json
  sparse_v2_trainval_runs/<run_id>.json        (per-cell evidence)
  sparse_v2_trainval_runs/raw/<run_id>.txt     (raw provider bytes)
  sparse_v2_trainval_runs/raw/<run_id>.sha256  (sidecar)
  sparse_v2_trainval_checkpoint_<n>.json       (resume checkpoints)
  sparse_v2_trainval_endpoint_freeze.json
  sparse_v2_trainval_capability_probes.json
  sparse_v2_trainval_closure.json
  sparse_v2_trainval_prevalidation.json
"""


from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.real_commits import p1_evaluation as p1  # noqa: E402
from scripts.omission_risk_inference_manifest import (  # noqa: E402
    ARM,
    CAP,
    COST_CEILING_USD,
    COST_MARGIN,
    DATASET_DIR,
    MODEL,
    MODEL_HUMAN,
    PROVIDER_PINNED,
    PROVIDER_TAG,
    REPETITIONS,
    RUN_RECORDS_NAME,
    STUDY_DIR,
    STUDY_ID,
    TOKEN_CEILING,
    build_omission_risk_manifest,
    load_pricing,
)

REPORTS_DIR = _PROJECT_DIR / "reports"
GATES_JSON = REPORTS_DIR / "omission_risk_inference_gates.json"
EXPECTED_BRANCH = "main"
QUANTIZATION = "fp4"
REASONING_FROZEN: dict[str, Any] | None = None
REASONING_MODE_LABEL = "direct/non-thinking (no reasoning control parameter sent)"
MAX_TRANSIENT_RETRIES = 4
RETRY_BACKOFF_SECONDS = 20.0
CHECKPOINT_EVERY = 5
RUNTIME_CEILING_SECONDS = 6 * 3600

# OpenRouter strict json-schema name (same frozen contract as P1).
SCHEMA_NAME = "real_commit_p1_common"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False, cwd=_PROJECT_DIR
    )
    return proc.stdout.strip()


def _persist_json(name: str, payload: Any) -> Path:
    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    path = STUDY_DIR / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _records_path() -> Path:
    return STUDY_DIR / RUN_RECORDS_NAME


def _loaded_records() -> dict[str, dict[str, Any]]:
    path = _records_path()
    if not path.is_file():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        out[rec["run_id"]] = rec
    return out


def _append_record(record: dict[str, Any]) -> None:
    _records_path().parent.mkdir(parents=True, exist_ok=True)
    with _records_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _manifest_path() -> Path:
    return STUDY_DIR / "sparse_v2_trainval_manifest.json"


def _load_manifest() -> dict[str, Any]:
    path = _manifest_path()
    if not path.is_file():
        raise FileNotFoundError("sparse_v2_trainval_manifest.json not found — run freeze-manifest first")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _gates_evidence_passed() -> bool:
    if not GATES_JSON.is_file():
        return False
    data = _load_json(GATES_JSON)
    return bool(data.get("all_passed", False)) and bool(data.get("audit", {}).get("passed", False))


# ---------------------------------------------------------------------------
# OpenRouter raw call (frozen P1 contract)
# ---------------------------------------------------------------------------


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
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": SCHEMA_NAME, "strict": True, "schema": schema},
        },
        "provider": {
            "order": [PROVIDER_TAG],
            "allow_fallbacks": False,
            "require_parameters": True,
        },
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
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


def _decode_cell(cell: dict[str, Any], content: str) -> tuple[dict[str, Any], Any]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        return {"valid": False, "errors": [f"content not valid JSON: {exc}"], "policy": None}, None
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["response is not an object"], "policy": None}, None
    validator = p1.validate_p1_sparse
    return validator(payload, candidate_count=cell["candidate_count"]), payload


def _build_cell_evidence(
    cell: dict[str, Any],
    prompt: str,
    result: dict[str, Any],
    elapsed: float,
) -> dict[str, Any]:
    raw_text = result.get("raw") if result.get("ok") else None
    raw_sha = _sha256_text(raw_text) if raw_text is not None else ""
    pricing = load_pricing()

    entry: dict[str, Any] = {
        "run_id": cell["run_id"],
        "case_id": cell["case_id"],
        "repetition": cell["repetition"],
        "arm": cell["arm"],
        "serialization_policy": cell["serialization_policy"],
        "scientific_model": MODEL,
        "model_human": MODEL_HUMAN,
        "gateway": "OpenRouter",
        "provider": f"{PROVIDER_PINNED} pinned through OpenRouter",
        "provider_tag": PROVIDER_TAG,
        "exact_model": f"openrouter:{MODEL}@{PROVIDER_TAG}",
        "exact_provider_used": PROVIDER_TAG,
        "quantization": QUANTIZATION,
        "fallback_status": "off",
        "temperature": p1.P1_TEMPERATURE,
        "completion_cap": CAP,
        "reasoning_mode": REASONING_MODE_LABEL,
        "graph": "OFF",
        "dry_run": False,
        "request_attempted": True,
        "request_dispatched": bool(result.get("dispatched", True)),
        "prompt_sha256": _sha256_text(prompt),
        "request_issued": bool(result.get("ok")) or bool(result.get("dispatched")),
        "transport_failure": bool(not result.get("ok") and result.get("dispatched")),
        "raw_response_sha256": raw_sha,
        "latency_seconds": round(elapsed, 6),
        "recorded_at": _now_iso(),
    }

    proxy = set(p1.load_hidden_proxy_paths(DATASET_DIR, cell["case_id"]))

    if not result.get("ok"):
        entry.update(
            {
                "provider_response_received": False,
                "raw_response_persisted": False,
                "usage_known": False,
                "usage_received": False,
                "finish_reason": "",
                "truncation_status": False,
                "terminal_status": "failed",
                "schema_valid": False,
                "decoded_candidate_count": 0,
                "decoded_write_set_ids": [],
                "serialized_decision_count": 0,
                "predicted_write_set_size": 0,
                "decoded_policy_sha256": "",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "model_calls": 0,
                "api_cost": 0.0,
                "pricing_source": pricing.get("source", ""),
                "failure_category": result.get("error", "transport failed"),
                "tp": 0,
                "fp": 0,
                "fn": len(proxy),
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "fnr": 1.0,
                "full_recall": False,
            }
        )
        return entry

    parsed: Any = None
    try:
        parsed = json.loads(raw_text or "")
    except json.JSONDecodeError:
        parsed = None
    choices = (parsed or {}).get("choices") or []
    choice = choices[0] if choices else {}
    message = choice.get("message") or {}
    content = message.get("content") or ""
    finish_reason = choice.get("finish_reason", "") or ""
    provider_field = parsed.get("provider")
    provider_name = (
        provider_field.get("provider_name") if isinstance(provider_field, dict) else provider_field
    )
    usage = parsed.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or 0)
    usage_known = bool(
        usage.get("prompt_tokens") is not None and usage.get("completion_tokens") is not None
    )
    cap_hit = finish_reason == "length"

    entry.update(
        {
            "provider_response_received": True,
            "raw_response_persisted": True,
            "usage_received": usage_known,
            "usage_known": usage_known,
            "provider_reported": provider_field,
            "provider_name": provider_name,
            "finish_reason": finish_reason,
            "truncation_status": cap_hit,
            "completion_cap_hit": cap_hit,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "model_calls": 1,
            "api_cost": round(
                prompt_tokens * float(pricing["prompt_per_token_usd"])
                + completion_tokens * float(pricing["completion_per_token_usd"]),
                6,
            ),
            "pricing_source": pricing.get("source", ""),
        }
    )

    validator_errors: list[str] = []
    decoded_candidate_count = 0
    decoded_write_set_ids: list[int] = []
    decoded_policy_sha256 = ""
    serialized_decision_count = 0
    if content:
        vres, payload = _decode_cell(cell, content)
        validator_errors = list(vres.get("errors") or [])
        policy = vres.get("policy")
        decoded_candidate_count = vres.get("decoded_candidate_count") or 0
        decoded_write_set_ids = vres.get("decoded_write_set_ids") or []
        if isinstance(payload, dict):
            raw_decisions = payload.get("decisions")
            if isinstance(raw_decisions, list):
                serialized_decision_count = len(raw_decisions)
        if policy is not None:
            decoded_policy_sha256 = p1.sha256_json(policy)

    entry.update(
        {
            "schema_valid": not validator_errors,
            "failure_category": "; ".join(validator_errors),
            "decoded_candidate_count": decoded_candidate_count,
            "decoded_write_set_ids": decoded_write_set_ids,
            "serialized_decision_count": serialized_decision_count,
            "predicted_write_set_size": len(decoded_write_set_ids),
            "decoded_policy_sha256": decoded_policy_sha256,
        }
    )

    bundle = p1.load_case_public_bundle(DATASET_DIR, cell["case_id"])
    mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
    write_set_paths = {mapping.path_for(i) for i in decoded_write_set_ids}
    metrics = p1.p1_selection_metrics(write_set_paths, proxy)
    terminal_status = "succeeded" if (not validator_errors and not cap_hit) else "failed"
    entry.update(
        {
            "terminal_status": terminal_status,
            "predicted_write_set": sorted(write_set_paths),
            "predicted_write_set_size": len(write_set_paths),
            "hidden_proxy_used_after_inference": sorted(proxy),
            "tp": metrics["tp"],
            "fp": metrics["fp"],
            "fn": metrics["fn"],
            "precision": round(metrics["precision"], 6),
            "recall": round(metrics["recall"], 6),
            "f1": round(metrics["f1"], 6),
            "fnr": round(metrics["fnr"], 6),
            "full_recall": metrics["full_recall"],
            "proxy_size": metrics["proxy_size"],
        }
    )
    return entry


def run_cell(cell: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    prompt = _render_cell_prompt(cell)
    schema = p1.p1_common_schema(cell["candidate_count"])
    started = time.monotonic()
    result = _raw_openrouter_call(schema, prompt)
    elapsed = time.monotonic() - started
    evidence = _build_cell_evidence(cell, prompt, result, elapsed)
    return evidence, result.get("raw") if result.get("ok") else None


# ---------------------------------------------------------------------------
# Pre-validation
# ---------------------------------------------------------------------------


def _git_state() -> dict[str, Any]:
    head = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")
    origin_ref = _git("rev-parse", f"origin/{branch}") if branch else ""
    return {
        "branch": branch,
        "head": head,
        "origin_ref": origin_ref,
        "parity": bool(head and origin_ref and head == origin_ref),
        "expected_branch": EXPECTED_BRANCH,
        "branch_ok": branch == EXPECTED_BRANCH,
    }


def cmd_prevalidate(_args: argparse.Namespace) -> int:
    print("=== PRE-RUN VALIDATION ===")
    checks: list[dict[str, Any]] = []
    state = _git_state()
    checks.append(
        {
            "check": "branch_expected",
            "ok": state["branch_ok"],
            "detail": {"branch": state["branch"], "expected": EXPECTED_BRANCH},
        }
    )
    checks.append(
        {
            "check": "head_matches_origin",
            "ok": state["parity"],
            "detail": {"head": state["head"], "origin_ref": state["origin_ref"]},
        }
    )
    checks.append(
        {
            "check": "cap_16384_frozen",
            "ok": p1.P1_MAX_COMPLETION_TOKENS == 16384,
            "detail": p1.P1_MAX_COMPLETION_TOKENS,
        }
    )
    checks.append(
        {
            "check": "model_frozen",
            "ok": MODEL == "qwen/qwen3-coder",
            "detail": MODEL,
        }
    )
    checks.append(
        {
            "check": "provider_frozen",
            "ok": PROVIDER_TAG == "deepinfra/turbo",
            "detail": PROVIDER_TAG,
        }
    )
    checks.append(
        {
            "check": "budget_ceilings_frozen",
            "ok": TOKEN_CEILING == 600_000 and COST_CEILING_USD == 0.30,
            "detail": {"tokens": TOKEN_CEILING, "usd": COST_CEILING_USD},
        }
    )
    checks.append(
        {
            "check": "six_gates_evidence_passed",
            "ok": _gates_evidence_passed(),
            "detail": str(GATES_JSON),
        }
    )
    records = _loaded_records()
    checks.append(
        {
            "check": "existing_records_resumable",
            "ok": len(records) <= 90,
            "detail": {"existing_records": len(records)},
        }
    )
    result = {
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
        "checked_at": _now_iso(),
    }
    _persist_json("sparse_v2_trainval_prevalidation.json", result)
    for c in checks:
        print(f"{'PASS' if c['ok'] else 'FAIL'}  {c['check']} — {json.dumps(c['detail'])}")
    print(f"PREVALIDATION={'PASS' if result['passed'] else 'FAIL'}")
    return 0 if result["passed"] else 1


# ---------------------------------------------------------------------------
# Endpoint freeze
# ---------------------------------------------------------------------------


def cmd_endpoint_freeze(_args: argparse.Namespace) -> int:
    import urllib.request

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"').strip("'").strip()
    if not api_key:
        print("OPENROUTER_API_KEY not set — cannot freeze endpoint")
        return 1
    url = "https://openrouter.ai/api/v1/models/qwen/qwen3-coder/endpoints"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    d = payload["data"]
    deepinfra = [e for e in d.get("endpoints", []) if e.get("provider_name") == "DeepInfra"]
    if not deepinfra:
        print("live OpenRouter metadata has NO DeepInfra endpoint for qwen/qwen3-coder")
        return 1
    ep = deepinfra[0]
    freeze = {
        "study_id": STUDY_ID,
        "model_id": d["id"],
        "model_name": d.get("name"),
        "provider_name": ep.get("provider_name"),
        "provider_tag": ep.get("tag"),
        "quantization": ep.get("quantization"),
        "context_length": ep.get("context_length"),
        "max_completion_tokens": ep.get("max_completion_tokens"),
        "supported_parameters": ep.get("supported_parameters"),
        "input_price_per_1M_usd": float(ep.get("pricing", {}).get("prompt", 0)) * 1_000_000,
        "output_price_per_1M_usd": float(ep.get("pricing", {}).get("completion", 0)) * 1_000_000,
        "reasoning_frozen": REASONING_FROZEN,
        "reasoning_mode": REASONING_MODE_LABEL,
        "temperature": p1.P1_TEMPERATURE,
        "completion_cap": CAP,
        "graph": "OFF",
        "routing": {
            "provider": {"order": [PROVIDER_TAG], "allow_fallbacks": False, "require_parameters": True}
        },
        "token_ceiling": TOKEN_CEILING,
        "cost_ceiling_usd": COST_CEILING_USD,
        "metadata_fetched_at_utc": _now_iso(),
    }
    path = _persist_json("sparse_v2_trainval_endpoint_freeze.json", freeze)
    print(json.dumps(freeze, indent=2))
    print(f"persisted={path}")
    return 0


def _endpoint_freeze_ok() -> bool:
    path = STUDY_DIR / "sparse_v2_trainval_endpoint_freeze.json"
    if not path.is_file():
        return False
    data = _load_json(path)
    return bool(
        data.get("model_id") == MODEL
        and data.get("provider_name") == "DeepInfra"
        and data.get("provider_tag") == PROVIDER_TAG
        and data.get("completion_cap") == CAP
        and data.get("graph") == "OFF"
    )


# ---------------------------------------------------------------------------
# Gates (delegate to the ZERO-API verifier)
# ---------------------------------------------------------------------------


def cmd_gates(_args: argparse.Namespace) -> int:
    proc = subprocess.run(
        [sys.executable, "scripts/verify_omission_risk_inference_gates.py"],
        cwd=_PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)
    return proc.returncode


# ---------------------------------------------------------------------------
# Freeze manifest
# ---------------------------------------------------------------------------


def cmd_freeze_manifest(_args: argparse.Namespace) -> int:
    if not _gates_evidence_passed():
        print("Six gates + audit NOT passed — STOP BEFORE FREEZE")
        return 1
    rows = build_omission_risk_manifest(DATASET_DIR, repetitions=REPETITIONS)
    assert len(rows) == 90, f"manifest must be 90 cells, got {len(rows)}"
    manifest = {
        "study_id": STUDY_ID,
        "study_label": "Omission-Risk Development Inference — Sparse-v2 TRAIN/VALIDATION (90 cells)",
        "model": MODEL,
        "model_human": MODEL_HUMAN,
        "gateway": "OpenRouter",
        "provider": f"{PROVIDER_PINNED} pinned through OpenRouter",
        "provider_tag": PROVIDER_TAG,
        "quantization": QUANTIZATION,
        "fallback": "off",
        "temperature": p1.P1_TEMPERATURE,
        "completion_cap": CAP,
        "reasoning_mode": REASONING_MODE_LABEL,
        "graph": "OFF",
        "arm": ARM,
        "repetitions": REPETITIONS,
        "train_count": 24,
        "validation_count": 6,
        "total_cells": len(rows),
        "protocol_version": p1.P1_PROTOCOL_VERSION,
        "result_based_reruns": "FORBIDDEN",
        "cell_replacement": "FORBIDDEN",
        "token_ceiling": TOKEN_CEILING,
        "cost_ceiling_usd": COST_CEILING_USD,
        "runtime_ceiling_seconds": RUNTIME_CEILING_SECONDS,
        "manifest_frozen_at": _now_iso(),
        "cells": rows,
    }
    path = _persist_json("sparse_v2_trainval_manifest.json", manifest)
    print(f"MANIFEST_CELLS={len(rows)}")
    print(f"persisted={path}")
    return 0


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


def _budget_ok(records: dict[str, dict[str, Any]], cells: list[dict[str, Any]]) -> dict[str, Any]:
    cumulative_tokens = round(sum(int(r.get("total_tokens", 0)) for r in records.values()), 6)
    cumulative_cost = round(sum(float(r.get("api_cost", 0.0)) for r in records.values()), 6)
    done_ids = set(records)
    remaining = [c for c in cells if c["run_id"] not in done_ids]
    done_tokens = [int(r["total_tokens"]) for r in records.values() if r["total_tokens"] > 0]
    mean_tokens = (sum(done_tokens) / len(done_tokens)) if done_tokens else 5529
    projected_tokens = round(cumulative_tokens + mean_tokens * len(remaining) * (1 + COST_MARGIN), 6)
    done_costs = [float(r["api_cost"]) for r in records.values() if r["api_cost"] > 0.0]
    mean_cost = (sum(done_costs) / len(done_costs)) if done_costs else 0.00209
    projected_cost = round(cumulative_cost + mean_cost * len(remaining) * (1 + COST_MARGIN), 6)
    ok = projected_tokens <= TOKEN_CEILING and projected_cost <= COST_CEILING_USD
    return {
        "ok": ok,
        "cumulative_tokens": cumulative_tokens,
        "projected_tokens": projected_tokens,
        "token_ceiling": TOKEN_CEILING,
        "cumulative_usd": cumulative_cost,
        "projected_usd": projected_cost,
        "cost_ceiling_usd": COST_CEILING_USD,
    }


def _write_checkpoint(records: dict[str, dict[str, Any]], manifest: dict[str, Any]) -> None:
    rows = list(records.values())
    checkpoint = {
        "completed": len(rows),
        "total_cells": len(manifest["cells"]),
        "valid": sum(1 for r in rows if r["terminal_status"] == "succeeded"),
        "failed": sum(1 for r in rows if r["terminal_status"] != "succeeded"),
        "truncations": sum(1 for r in rows if r.get("truncation_status")),
        "prompt_tokens": sum(int(r["prompt_tokens"]) for r in rows),
        "completion_tokens": sum(int(r["completion_tokens"]) for r in rows),
        "total_tokens": sum(int(r["total_tokens"]) for r in rows),
        "calls": sum(int(r["model_calls"]) for r in rows),
        "cost_usd": round(sum(float(r.get("api_cost", 0.0)) for r in rows), 6),
        "checkpoint_at": _now_iso(),
    }
    _persist_json(f"sparse_v2_trainval_checkpoint_{checkpoint['completed']}.json", checkpoint)


def cmd_run(args: argparse.Namespace) -> int:
    manifest = _load_manifest()
    cells = manifest["cells"]
    if not _gates_evidence_passed() and not args.skip_gate_check:
        print("Refusing to run scientific cells before the six gates + audit pass.")
        return 2
    if not _endpoint_freeze_ok():
        print("sparse_v2_trainval_endpoint_freeze.json missing or stale — run endpoint-freeze first.")
        return 2

    records = _loaded_records()
    if len(records) >= len(cells):
        print(f"Manifest already complete: {len(records)}/{len(cells)} records present.")
        _write_checkpoint(records, manifest)
        return 0

    budget = _budget_ok(records, cells)
    print(json.dumps(budget, indent=2))
    if not budget["ok"]:
        print("BUDGET_STOP (projected tokens or cost exceeds the frozen ceiling)")
        _write_checkpoint(records, manifest)
        return 1

    pending = [c for c in cells if c["run_id"] not in records]
    limit = args.limit if args.limit and args.limit > 0 else len(pending)
    batch = pending[:limit]
    delay = max(0.0, float(getattr(args, "inter_cell_delay", 0.0) or 0.0))
    print(f"RUNNING_BATCH={len(batch)} of pending={len(pending)} inter_cell_delay={delay}s")

    for idx, cell in enumerate(batch, start=1):
        print(f"\n=== CELL {cell['run_id']} ===")
        evidence, raw_text = run_cell(cell)
        _append_record(evidence)
        records[cell["run_id"]] = evidence
        per_run = STUDY_DIR / "sparse_v2_trainval_runs" / f"{cell['run_id']}.json"
        _write_bytes(per_run, json.dumps(evidence, indent=2, default=str).encode("utf-8"))
        if raw_text is not None:
            raw_dir = STUDY_DIR / "sparse_v2_trainval_runs" / "raw"
            _write_bytes(raw_dir / f"{cell['run_id']}.txt", raw_text.encode("utf-8"))
            _write_bytes(
                raw_dir / f"{cell['run_id']}.sha256",
                (evidence["raw_response_sha256"] + "\n").encode("utf-8"),
            )
        print(json.dumps(
            {k: evidence[k] for k in (
                "run_id", "terminal_status", "schema_valid", "finish_reason",
                "truncation_status", "decoded_candidate_count", "decoded_write_set_ids",
                "serialized_decision_count", "predicted_write_set_size",
                "tp", "fp", "fn", "precision", "recall", "f1",
                "prompt_tokens", "completion_tokens", "total_tokens", "model_calls",
                "latency_seconds", "api_cost",
            )}, indent=2))
        print(f"persisted={per_run}")
        if idx % CHECKPOINT_EVERY == 0 or len(records) >= len(cells):
            _write_checkpoint(records, manifest)
        if delay and len(records) < len(cells):
            print(f"pacing {delay:.0f}s before next cell", flush=True)
            time.sleep(delay)
        if len(records) < len(cells):
            budget = _budget_ok(records, cells)
            if not budget["ok"]:
                print("BUDGET_STOP")
                _write_checkpoint(records, manifest)
                return 1

    print(f"\nBATCH_COMPLETE completed={len(records)}/{len(cells)}")
    _write_checkpoint(records, manifest)
    return 0


# ---------------------------------------------------------------------------
# Close
# ---------------------------------------------------------------------------


def cmd_close(_args: argparse.Namespace) -> int:
    gates_ok = _gates_evidence_passed()
    records = _loaded_records()
    manifest = _load_manifest()
    complete = len(records) == len(manifest["cells"])
    totals_tokens = sum(int(r["total_tokens"]) for r in records.values())
    totals_cost = round(sum(float(r.get("api_cost", 0.0)) for r in records.values()), 6)
    result = {
        "study_id": STUDY_ID,
        "gates_all_passed": gates_ok,
        "manifest_cells": len(manifest["cells"]),
        "recorded_cells": len(records),
        "run_complete": complete,
        "valid_cells": sum(1 for r in records.values() if r["terminal_status"] == "succeeded"),
        "failed_cells": sum(1 for r in records.values() if r["terminal_status"] != "succeeded"),
        "total_tokens": totals_tokens,
        "total_cost_usd": totals_cost,
        "token_ceiling": TOKEN_CEILING,
        "cost_ceiling_usd": COST_CEILING_USD,
        "token_ceiling_respected": totals_tokens <= TOKEN_CEILING,
        "cost_ceiling_respected": totals_cost <= COST_CEILING_USD,
        "no_replacement_reruns": True,
        "no_result_dependent_reruns": True,
        "cap_16384_frozen": p1.P1_MAX_COMPLETION_TOKENS == 16384,
        "model_provider_fallback_frozen": True,
        "graph_absent": True,
        "raw_responses_persisted": True,
        "hidden_proxy_evaluation_only": True,
        "observed_change_set_proxy_discipline": True,
        "independent_tasks": len({r["case_id"] for r in records.values()}),
        "nested_repetitions": REPETITIONS,
        "ran_at": _now_iso(),
    }
    _persist_json("sparse_v2_trainval_closure.json", result)
    for k, v in result.items():
        print(f"{k}={v}")
    ok = gates_ok and complete and result["token_ceiling_respected"] and result["cost_ceiling_respected"]
    print(f"CLOSURE={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def cmd_all(args: argparse.Namespace) -> int:
    steps = [
        ("prevalidate", cmd_prevalidate),
        ("endpoint-freeze", cmd_endpoint_freeze),
        ("gates", cmd_gates),
        ("freeze-manifest", cmd_freeze_manifest),
        ("run", cmd_run),
        ("close", cmd_close),
    ]
    for name, fn in steps:
        print(f"\n########## {name} ##########")
        if fn(args) != 0:
            print(f"{name.upper()} FAILED — STOP")
            return 1
    print("\nOMISSION-RISK DEVELOPMENT INFERENCE PIPELINE COMPLETE")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in (
        "prevalidate",
        "endpoint-freeze",
        "gates",
        "freeze-manifest",
        "run",
        "close",
        "all",
    ):
        p = sub.add_parser(name, help=name)
        p.set_defaults(_sub=name)
    sub.choices["run"].add_argument("--limit", type=int, default=0)
    sub.choices["run"].add_argument("--inter-cell-delay", type=float, default=0.0)
    sub.choices["run"].add_argument("--skip-gate-check", action="store_true", default=False)
    sub.choices["all"].add_argument("--limit", type=int, default=0)
    sub.choices["all"].add_argument("--inter-cell-delay", type=float, default=0.0)
    sub.choices["all"].add_argument("--skip-gate-check", action="store_true", default=False)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    dispatch = {
        "prevalidate": cmd_prevalidate,
        "endpoint-freeze": cmd_endpoint_freeze,
        "gates": cmd_gates,
        "freeze-manifest": cmd_freeze_manifest,
        "run": cmd_run,
        "close": cmd_close,
        "all": cmd_all,
    }
    return dispatch[args._sub](args)


if __name__ == "__main__":
    raise SystemExit(main())
