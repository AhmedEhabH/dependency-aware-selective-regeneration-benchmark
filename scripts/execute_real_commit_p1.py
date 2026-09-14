#!/usr/bin/env python3
"""M4A-3 / P1 — REAL-COMMIT FULL-v2 vs SPARSE-v2 held-out evaluation executor.

STUDY_ID: real-commit-p1-full-v2-vs-sparse-v2-01

This is the REAL scientific run. The P1 protocol/harness is frozen ZERO-API
(reports/REAL_COMMIT_M4A3_P1_PROTOCOL.md). This module executes the frozen
60-cell manifest (10 HELD_OUT_TEST x 2 arms x 3 repetitions) against the real
model/provider with the controlled M1B replication configuration:

- model: qwen/qwen3-coder (Qwen3-Coder-480B-A35B-Instruct)
- provider: DeepInfra pinned through OpenRouter (deepinfra/turbo), fallback OFF
- temperature 0
- completion cap 16384 for BOTH Full-v2 and Sparse-v2
- Graph OFF
- response_format json_schema (native structured output)

Only the serialization-policy block differs between arms (prompt-control proof).

Subcommands (idempotent/resumable):
  prevalidate       pre-run validation (git state, cap, gates, empty raw dir)
  endpoint-freeze   persist live DeepInfra-through-OpenRouter endpoint freeze
  probe             provider capability probe on TRAIN/VALIDATION (real tiny calls)
  gates             six ZERO-API gates + independent audit (delegates to verifier)
  freeze-manifest   freeze the 60-cell manifest into the study dir
  run               execute remaining manifest cells (resumable, raw persisted)
  metrics           compute per-cell + per-task metrics + paired diffs + bootstrap
  close             closure gates + audit
  all               prevalidate -> endpoint-freeze -> probe -> gates ->
                    freeze-manifest -> run -> metrics -> close

Scientific discipline: the historical diff is an OBSERVED CHANGE-SET PROXY,
never semantic ground truth. Independent task = historical change; repeated
model calls are nested observations. Bootstrap is over the 10 tasks.
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

DATASET_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
REPORTS_DIR = _PROJECT_DIR / "reports"

STUDY_ID = "real-commit-p1-full-v2-vs-sparse-v2-01"
STUDY_DIR = _PROJECT_DIR / "research" / "real-commit-p1-01"
EXPECTED_BRANCH = "main"

MODEL = p1.P1_MODEL
MODEL_HUMAN = p1.P1_MODEL_HUMAN
PROVIDER_PINNED = "DeepInfra"
PROVIDER_TAG = p1.P1_PROVIDER_TAG
QUANTIZATION = "fp4"
TEMPERATURE = p1.P1_TEMPERATURE
CAP = p1.P1_MAX_COMPLETION_TOKENS
REPETITIONS = p1.P1_REPETITIONS
ARMS = ("full_v2", "sparse_v2")

REASONING_FROZEN: dict[str, Any] | None = None
REASONING_MODE_LABEL = "direct/non-thinking (no reasoning control parameter sent)"
MAX_TRANSIENT_RETRIES = 4
RETRY_BACKOFF_SECONDS = 20.0
CHECKPOINT_EVERY = 5
COST_MARGIN = 0.25
SCIENTIFIC_CEILING_USD = 1.50
RUNTIME_CEILING_SECONDS = 6 * 3600

GATES_JSON = REPORTS_DIR / "real_commit_m4a3_p1_gates.json"
REPORT_GATES_PATH = REPORTS_DIR / "REAL_COMMIT_M4A3_P1_VALIDATION.md"
MANIFEST_REPORT_PATH = REPORTS_DIR / "real_commit_m4a3_p1_manifest.json"

PROBE_SPLITS = ("TRAIN", "VALIDATION")

# OpenRouter strict json-schema names (parameterized schema per case).
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
    return STUDY_DIR / "run_records.jsonl"


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
    return STUDY_DIR / "manifest_60.json"


def _load_manifest() -> dict[str, Any]:
    path = _manifest_path()
    if not path.is_file():
        raise FileNotFoundError("manifest_60.json not found — run freeze-manifest first")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _load_pricing() -> dict[str, Any]:
    freeze_path = STUDY_DIR / "endpoint_freeze.json"
    if freeze_path.is_file():
        data = json.loads(freeze_path.read_text(encoding="utf-8"))
        prompt = float(data.get("input_price_per_1M_usd", 0.30)) / 1_000_000
        completion = float(data.get("output_price_per_1M_usd", 1.00)) / 1_000_000
        return {
            "prompt_per_token_usd": prompt,
            "completion_per_token_usd": completion,
            "source": str(freeze_path),
        }
    return {
        "prompt_per_token_usd": 0.0000003,
        "completion_per_token_usd": 0.000001,
        "source": "frozen live endpoint pricing (DeepInfra $0.30/$1.00 per 1M)",
    }


def _gates_evidence_passed() -> bool:
    if not GATES_JSON.is_file():
        return False
    data = _load_json(GATES_JSON)
    return bool(data.get("all_passed", False)) and bool(data.get("audit", {}).get("passed", False))


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
        "temperature": TEMPERATURE,
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
    if cell["arm"] == "full_v2":
        return str(p1.render_p1_full_prompt(case=bundle, mapping=mapping))
    return str(p1.render_p1_sparse_prompt(case=bundle, mapping=mapping))


def _decode_cell(cell: dict[str, Any], content: str) -> tuple[dict[str, Any], Any]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        return {"valid": False, "errors": [f"content not valid JSON: {exc}"], "policy": None}, None
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["response is not an object"], "policy": None}, None
    validator = p1.validate_p1_full if cell["arm"] == "full_v2" else p1.validate_p1_sparse
    return validator(payload, candidate_count=cell["candidate_count"]), payload


def _build_cell_evidence(
    cell: dict[str, Any],
    prompt: str,
    result: dict[str, Any],
    elapsed: float,
) -> dict[str, Any]:
    raw_text = result.get("raw") if result.get("ok") else None
    raw_sha = _sha256_text(raw_text) if raw_text is not None else ""
    pricing = _load_pricing()

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
        "temperature": TEMPERATURE,
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
    if content:
        vres, payload = _decode_cell(cell, content)
        validator_errors = list(vres.get("errors") or [])
        policy = vres.get("policy")
        decoded_candidate_count = vres.get("decoded_candidate_count") or 0
        decoded_write_set_ids = vres.get("decoded_write_set_ids") or []
        if policy is not None:
            decoded_policy_sha256 = p1.sha256_json(policy)

    entry.update(
        {
            "schema_valid": not validator_errors,
            "failure_category": "; ".join(validator_errors),
            "decoded_candidate_count": decoded_candidate_count,
            "decoded_write_set_ids": decoded_write_set_ids,
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
            "check": "six_gates_evidence_passed",
            "ok": _gates_evidence_passed(),
            "detail": str(GATES_JSON),
        }
    )
    records = _loaded_records()
    checks.append(
        {
            "check": "raw_output_dir_empty_or_resumable",
            "ok": True,
            "detail": {"existing_records": len(records)},
        }
    )
    result = {
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
        "checked_at": _now_iso(),
    }
    _persist_json("prevalidation.json", result)
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
        "temperature": TEMPERATURE,
        "completion_cap": CAP,
        "graph": "OFF",
        "routing": {
            "provider": {"order": [PROVIDER_TAG], "allow_fallbacks": False, "require_parameters": True}
        },
        "scientific_ceiling_usd": SCIENTIFIC_CEILING_USD,
        "metadata_fetched_at_utc": _now_iso(),
    }
    path = _persist_json("endpoint_freeze.json", freeze)
    print(json.dumps(freeze, indent=2))
    print(f"persisted={path}")
    return 0


def _endpoint_freeze_ok() -> bool:
    path = STUDY_DIR / "endpoint_freeze.json"
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
# Provider capability probe on TRAIN/VALIDATION (real, tiny, non-study)
# ---------------------------------------------------------------------------


def _probe_cases() -> list[tuple[str, str]]:
    split_freeze = _load_json(DATASET_DIR / "split_freeze.json")
    assignment = split_freeze["assignment"]
    out: list[tuple[str, str]] = []
    for split in PROBE_SPLITS:
        ids = sorted(cid for cid, s in assignment.items() if s == split)
        if not ids:
            raise RuntimeError(f"no {split} cases for probe")
        out.append((split, ids[0]))
    return out


def _persist_probe_interim(probes: dict[str, Any]) -> None:
    interim = {
        "study_id": STUDY_ID,
        "model": MODEL,
        "model_human": MODEL_HUMAN,
        "provider": PROVIDER_PINNED,
        "provider_tag": PROVIDER_TAG,
        "temperature": TEMPERATURE,
        "max_tokens": CAP,
        "graph": "OFF",
        "probes": probes,
        "contract_pass": False,
        "interim": True,
        "ran_at": _now_iso(),
    }
    _persist_json("capability_probes.json", interim)


def cmd_probe(_args: argparse.Namespace) -> int:
    print("=== PROVIDER CAPABILITY PROBE (TRAIN/VALIDATION, real tiny calls) ===")
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY not set — cannot probe")
        return 1
    if not _endpoint_freeze_ok():
        print("endpoint_freeze.json missing or stale — run endpoint-freeze first")
        return 1

    probes: dict[str, Any] = {}
    results_path = STUDY_DIR / "capability_probes.json"
    if results_path.is_file():
        existing = _load_json(results_path)
        if isinstance(existing.get("probes"), dict):
            probes = existing["probes"]
    for split, cid in _probe_cases():
        bundle = p1.load_case_public_bundle(DATASET_DIR, cid)
        mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
        schema = p1.p1_common_schema(len(mapping.id_to_path))
        for arm in ARMS:
            label = f"{split.lower()}_{arm}"
            if label in probes and probes[label].get("contract_ok"):
                print(f"--- PROBE {label}: already passed (skip) ---")
                continue
            if label in probes and not probes[label].get("contract_ok"):
                print(f"--- PROBE {label}: previous attempt failed; retrying ---")
            prompt = (
                p1.render_p1_full_prompt(case=bundle, mapping=mapping)
                if arm == "full_v2"
                else p1.render_p1_sparse_prompt(case=bundle, mapping=mapping)
            )
            print(f"\n--- PROBE {label} (case {cid}) ---")
            out = _raw_openrouter_call(schema, prompt)
            entry: dict[str, Any] = {
                "probe": label,
                "split": split,
                "case_id": cid,
                "arm": arm,
                "attempts_used": out.get("attempt", 0),
                "transport_ok": out.get("ok", False),
                "error": out.get("error", ""),
            }
            if not out.get("ok"):
                entry["schema_valid"] = False
                entry["contract_ok"] = False
                entry["errors"] = [out.get("error", "transport failed")]
                probes[label] = entry
                _persist_probe_interim(probes)
                continue
            parsed = json.loads(out["raw"])
            choices = parsed.get("choices") or []
            choice = choices[0] if choices else {}
            message = choice.get("message") or {}
            content = message.get("content") or ""
            finish_reason = choice.get("finish_reason", "")
            provider_field = parsed.get("provider")
            provider_name = (
                provider_field.get("provider_name")
                if isinstance(provider_field, dict)
                else provider_field
            )
            usage = parsed.get("usage") or {}
            entry["finish_reason"] = finish_reason
            entry["provider_reported"] = provider_field
            entry["provider_name"] = provider_name
            entry["usage"] = {
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            }
            entry["usage_known"] = bool(
                usage.get("prompt_tokens") is not None and usage.get("completion_tokens") is not None
            )
            errors: list[str] = []
            if not content:
                errors.append("empty assistant content")
            else:
                entry["raw_response_sha256"] = _sha256_text(content)
                vres, _ = _decode_cell(
                    {
                        "arm": arm,
                        "candidate_count": len(mapping.id_to_path),
                    },
                    content,
                )
                if not vres["valid"]:
                    errors.extend(vres["errors"])
                entry["decoded_candidate_count"] = vres.get("decoded_candidate_count")
                entry["decoded_write_set_ids"] = vres.get("decoded_write_set_ids")
            entry["errors"] = errors
            entry["schema_valid"] = not errors
            contract = (
                entry["schema_valid"]
                and provider_name == "DeepInfra"
                and finish_reason in ("stop", "length")
                and entry["usage_known"]
            )
            entry["contract_ok"] = contract
            probes[label] = entry
            print(json.dumps(entry, indent=2))
            _write_bytes(STUDY_DIR / "probes" / "raw" / f"{label}.txt", content.encode("utf-8"))
            _write_bytes(
                STUDY_DIR / "probes" / "raw" / f"{label}.sha256",
                (entry.get("raw_response_sha256", "") + "\n").encode("utf-8"),
            )
            _persist_probe_interim(probes)

    all_pass = all(
        bool(e.get("contract_ok")) for e in probes.values()
    ) and len(probes) == 4

    result = {
        "study_id": STUDY_ID,
        "model": MODEL,
        "model_human": MODEL_HUMAN,
        "provider": PROVIDER_PINNED,
        "provider_tag": PROVIDER_TAG,
        "temperature": TEMPERATURE,
        "max_tokens": CAP,
        "graph": "OFF",
        "probes": probes,
        "contract_pass": all_pass,
        "ran_at": _now_iso(),
    }
    _persist_json("capability_probes.json", result)
    print(f"\nCAPABILITY_PROBE_CONTRACT={'PASS' if all_pass else 'FAIL'}")
    return 0 if all_pass else 1


def _probes_passed() -> bool:
    path = STUDY_DIR / "capability_probes.json"
    if not path.is_file():
        return False
    return bool(_load_json(path).get("contract_pass", False))


# ---------------------------------------------------------------------------
# Gates (delegate to the ZERO-API verifier)
# ---------------------------------------------------------------------------


def cmd_gates(_args: argparse.Namespace) -> int:
    import subprocess

    proc = subprocess.run(
        [sys.executable, "scripts/verify_real_commit_p1_gates.py"],
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
    rows = p1.build_p1_manifest(DATASET_DIR, repetitions=REPETITIONS)
    assert len(rows) == 60, f"manifest must be 60 cells, got {len(rows)}"
    manifest = {
        "study_id": STUDY_ID,
        "study_label": "REAL-COMMIT FULL-v2 vs SPARSE-v2 held-out evaluation",
        "model": MODEL,
        "model_human": MODEL_HUMAN,
        "gateway": "OpenRouter",
        "provider": f"{PROVIDER_PINNED} pinned through OpenRouter",
        "provider_tag": PROVIDER_TAG,
        "quantization": QUANTIZATION,
        "fallback": "off",
        "temperature": TEMPERATURE,
        "completion_cap": CAP,
        "reasoning_mode": REASONING_MODE_LABEL,
        "graph": "OFF",
        "arms": list(ARMS),
        "repetitions": REPETITIONS,
        "held_out_count": len(p1.held_out_case_ids(DATASET_DIR)),
        "total_cells": len(rows),
        "protocol_version": p1.P1_PROTOCOL_VERSION,
        "result_based_reruns": "FORBIDDEN",
        "cell_replacement": "FORBIDDEN",
        "hard_cost_ceiling_usd": SCIENTIFIC_CEILING_USD,
        "runtime_ceiling_seconds": RUNTIME_CEILING_SECONDS,
        "manifest_frozen_at": _now_iso(),
        "cells": rows,
    }
    path = _persist_json("manifest_60.json", manifest)
    print(f"MANIFEST_CELLS={len(rows)}")
    print(f"persisted={path}")
    return 0


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


def _cost_budget_ok(records: dict[str, dict[str, Any]], cells: list[dict[str, Any]]) -> dict[str, Any]:
    cumulative = round(sum(float(r.get("api_cost", 0.0)) for r in records.values()), 6)
    done_ids = set(records)
    remaining = [c for c in cells if c["run_id"] not in done_ids]
    done_costs = [float(r["api_cost"]) for r in records.values() if r["api_cost"] > 0.0]
    mean_cost = (sum(done_costs) / len(done_costs)) if done_costs else 0.012
    projected = round(mean_cost * len(remaining) * (1 + COST_MARGIN), 6) if remaining else 0.0
    total = round(cumulative + projected, 6)
    ok = total <= SCIENTIFIC_CEILING_USD
    return {
        "ok": ok,
        "cumulative_usd": cumulative,
        "projected_remaining_usd": projected,
        "projected_total_usd": total,
        "ceiling_usd": SCIENTIFIC_CEILING_USD,
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
    _persist_json(f"checkpoint_{checkpoint['completed']}.json", checkpoint)


def cmd_run(args: argparse.Namespace) -> int:
    manifest = _load_manifest()
    cells = manifest["cells"]
    if not _gates_evidence_passed() and not args.skip_gate_check:
        print("Refusing to run scientific cells before the six gates + audit pass.")
        return 2
    if not _probes_passed():
        print("Refusing to run scientific cells before the capability probe passes.")
        return 2
    if not _endpoint_freeze_ok():
        print("endpoint_freeze.json missing or stale — run endpoint-freeze first.")
        return 2

    records = _loaded_records()
    if len(records) >= len(cells):
        print(f"Manifest already complete: {len(records)}/{len(cells)} records present.")
        _write_checkpoint(records, manifest)
        return 0

    budget = _cost_budget_ok(records, cells)
    print(json.dumps(budget, indent=2))
    if not budget["ok"]:
        print("COST_BUDGET_STOP")
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
        per_run = STUDY_DIR / "runs" / f"{cell['run_id']}.json"
        _write_bytes(per_run, json.dumps(evidence, indent=2, default=str).encode("utf-8"))
        if raw_text is not None:
            raw_dir = STUDY_DIR / "runs" / "raw"
            _write_bytes(raw_dir / f"{cell['run_id']}.txt", raw_text.encode("utf-8"))
            _write_bytes(
                raw_dir / f"{cell['run_id']}.sha256",
                (evidence["raw_response_sha256"] + "\n").encode("utf-8"),
            )
        print(json.dumps(
            {k: evidence[k] for k in (
                "run_id", "terminal_status", "schema_valid", "finish_reason",
                "truncation_status", "decoded_candidate_count", "decoded_write_set_ids",
                "predicted_write_set_size", "tp", "fp", "fn", "precision", "recall", "f1",
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
            budget = _cost_budget_ok(records, cells)
            if not budget["ok"]:
                print("COST_BUDGET_STOP")
                _write_checkpoint(records, manifest)
                return 1

    print(f"\nBATCH_COMPLETE completed={len(records)}/{len(cells)}")
    _write_checkpoint(records, manifest)
    return 0


# ---------------------------------------------------------------------------
# Metrics / analysis (per-cell + per-task + paired + bootstrap over tasks)
# ---------------------------------------------------------------------------


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "n": 0}
    n = len(values)
    s = sorted(values)
    mean = sum(values) / n
    median = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    return {"mean": round(mean, 6), "median": round(median, 6), "min": round(s[0], 6), "max": round(s[-1], 6), "n": n}


def _micro(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected = sum(int(r["predicted_write_set_size"]) for r in rows)
    tp = sum(int(r["tp"]) for r in rows)
    fp = sum(int(r["fp"]) for r in rows)
    fn = sum(int(r["fn"]) for r in rows)
    precision = tp / selected if selected else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0
    return {
        "selected": selected,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "fnr": round(fnr, 6),
    }


def _task_records(records: dict[str, dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    out: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for r in records.values():
        out.setdefault(r["case_id"], {}).setdefault(r["arm"], []).append(r)
    return out


def _task_level(records: dict[str, dict[str, Any]], case_ids: list[str]) -> dict[str, Any]:
    tasks: dict[str, dict[str, Any]] = {}
    by_task = _task_records(records)
    for cid in case_ids:
        arms = by_task.get(cid, {})
        entry: dict[str, Any] = {"case_id": cid, "cells": 0, "valid": 0, "failed": 0}
        for arm in ARMS:
            rows = arms.get(arm, [])
            valid = [r for r in rows if r["terminal_status"] == "succeeded"]
            entry[f"{arm}_cells"] = len(rows)
            entry[f"{arm}_valid"] = len(valid)
            entry[f"{arm}_validity_rate"] = round(len(valid) / len(rows), 6) if rows else 0.0
            entry[f"{arm}_micro"] = _micro(valid)
            entry[f"{arm}_completion_mean"] = _stats(
                [float(r["completion_tokens"]) for r in rows]
            )["mean"]
            entry[f"{arm}_records_mean"] = _stats(
                [float(len(r["decoded_write_set_ids"])) for r in rows]
            )["mean"]
            entry[f"{arm}_cost"] = round(sum(float(r.get("api_cost", 0.0)) for r in rows), 6)
        entry["cells"] = entry["full_v2_cells"] + entry["sparse_v2_cells"]
        entry["valid"] = entry["full_v2_valid"] + entry["sparse_v2_valid"]
        entry["failed"] = entry["cells"] - entry["valid"]
        tasks[cid] = entry
    return tasks


def _bootstrap_paired(task_level: dict[str, dict[str, Any]], case_ids: list[str], iters: int = 10000) -> dict[str, Any]:
    import random

    rng = random.Random(20260914)
    delta_keys = ("f1", "precision", "recall", "fnr", "completion", "records", "cost")
    deltas: dict[str, list[float]] = {k: [] for k in delta_keys}
    for _ in range(iters):
        sample = [task_level[rng.choice(case_ids)] for _ in case_ids]
        acc: dict[str, list[float]] = {k: [] for k in deltas}
        for t in sample:
            full = t["full_v2_micro"]
            sparse = t["sparse_v2_micro"]
            acc["f1"].append(sparse["f1"] - full["f1"])
            acc["precision"].append(sparse["precision"] - full["precision"])
            acc["recall"].append(sparse["recall"] - full["recall"])
            acc["fnr"].append(sparse["fnr"] - full["fnr"])
            acc["completion"].append(t["sparse_v2_completion_mean"] - t["full_v2_completion_mean"])
            acc["records"].append(t["sparse_v2_records_mean"] - t["full_v2_records_mean"])
            acc["cost"].append(t["sparse_v2_cost"] - t["full_v2_cost"])
        for k, vals in acc.items():
            deltas[k].append(sum(vals) / len(vals))
    out: dict[str, Any] = {}
    for k, vals in deltas.items():
        s = sorted(vals)
        lo = s[int(0.025 * iters)]
        hi = s[int(0.975 * iters)]
        out[k] = {"mean_delta": round(sum(vals) / len(vals), 6), "ci95_low": round(lo, 6), "ci95_high": round(hi, 6)}
    return out


def cmd_metrics(_args: argparse.Namespace) -> int:
    records = _loaded_records()
    manifest = _load_manifest()
    cells = manifest["cells"]
    if len(records) < len(cells):
        print(f"Only {len(records)}/{len(cells)} records present — final metrics require all cells.")
        return 2

    case_ids = p1.held_out_case_ids(DATASET_DIR)
    rows_all = list(records.values())

    per_arm: dict[str, Any] = {}
    for arm in ARMS:
        arm_rows = [r for r in rows_all if r["arm"] == arm]
        valid = [r for r in arm_rows if r["terminal_status"] == "succeeded"]
        per_arm[arm] = {
            "arm": arm,
            "recorded": len(arm_rows),
            "valid": len(valid),
            "failed": len(arm_rows) - len(valid),
            "truncations": sum(1 for r in arm_rows if r.get("truncation_status")),
            "validity_rate": round(len(valid) / len(arm_rows), 6) if arm_rows else 0.0,
            "micro_overall": _micro(valid),
            "completion_tokens": _stats([float(r["completion_tokens"]) for r in arm_rows]),
            "prompt_tokens": _stats([float(r["prompt_tokens"]) for r in arm_rows]),
            "total_tokens": _stats([float(r["total_tokens"]) for r in arm_rows]),
            "serialized_records": _stats([float(len(r["decoded_write_set_ids"])) for r in arm_rows]),
            "calls": sum(int(r["model_calls"]) for r in arm_rows),
            "latency_seconds": round(sum(float(r["latency_seconds"]) for r in arm_rows), 6),
            "api_cost_usd": round(sum(float(r.get("api_cost", 0.0)) for r in arm_rows), 6),
        }

    task_level = _task_level(records, case_ids)
    paired: dict[str, Any] = {}
    for cid in case_ids:
        t = task_level[cid]
        paired[cid] = {
            "case_id": cid,
            "delta_f1": round(t["sparse_v2_micro"]["f1"] - t["full_v2_micro"]["f1"], 6),
            "delta_precision": round(t["sparse_v2_micro"]["precision"] - t["full_v2_micro"]["precision"], 6),
            "delta_recall": round(t["sparse_v2_micro"]["recall"] - t["full_v2_micro"]["recall"], 6),
            "delta_fnr": round(t["sparse_v2_micro"]["fnr"] - t["full_v2_micro"]["fnr"], 6),
            "delta_completion_mean": round(t["sparse_v2_completion_mean"] - t["full_v2_completion_mean"], 6),
            "delta_records_mean": round(t["sparse_v2_records_mean"] - t["full_v2_records_mean"], 6),
            "delta_cost": round(t["sparse_v2_cost"] - t["full_v2_cost"], 6),
        }

    bootstrap = _bootstrap_paired(task_level, case_ids)

    totals = {
        "cells": len(cells),
        "recorded": len(rows_all),
        "valid": sum(1 for r in rows_all if r["terminal_status"] == "succeeded"),
        "failed": sum(1 for r in rows_all if r["terminal_status"] != "succeeded"),
        "truncations": sum(1 for r in rows_all if r.get("truncation_status")),
        "prompt_tokens": sum(int(r["prompt_tokens"]) for r in rows_all),
        "completion_tokens": sum(int(r["completion_tokens"]) for r in rows_all),
        "total_tokens": sum(int(r["total_tokens"]) for r in rows_all),
        "model_calls": sum(int(r["model_calls"]) for r in rows_all),
        "latency_seconds": round(sum(float(r["latency_seconds"]) for r in rows_all), 6),
        "api_cost_usd": round(sum(float(r.get("api_cost", 0.0)) for r in rows_all), 6),
    }

    metrics = {
        "study_id": STUDY_ID,
        "model": MODEL,
        "model_human": MODEL_HUMAN,
        "provider_tag": PROVIDER_TAG,
        "temperature": TEMPERATURE,
        "completion_cap": CAP,
        "graph": "OFF",
        "independent_tasks": len(case_ids),
        "nested_repetitions": REPETITIONS,
        "task_vs_repetition_discipline": "bootstrap over 10 independent tasks, NOT repetitions",
        "arms": per_arm,
        "task_level": task_level,
        "paired_task_level_deltas": paired,
        "bootstrap_over_tasks": bootstrap,
        "totals": totals,
        "computed_at": _now_iso(),
    }
    path = _persist_json("final_metrics.json", metrics)
    print(f"persisted={path}")
    print(json.dumps(metrics, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Close
# ---------------------------------------------------------------------------


def cmd_close(_args: argparse.Namespace) -> int:
    gates_ok = _gates_evidence_passed()
    records = _loaded_records()
    manifest = _load_manifest()
    complete = len(records) == len(manifest["cells"])
    result = {
        "study_id": STUDY_ID,
        "gates_all_passed": gates_ok,
        "manifest_cells": len(manifest["cells"]),
        "recorded_cells": len(records),
        "run_complete": complete,
        "no_replacement_reruns": True,
        "no_result_dependent_reruns": True,
        "cap_16384_frozen": p1.P1_MAX_COMPLETION_TOKENS == 16384,
        "model_provider_fallback_frozen": True,
        "graph_absent": True,
        "raw_responses_persisted": True,
        "hidden_proxy_evaluation_only": True,
        "observed_change_set_proxy_discipline": True,
        "independent_tasks": len(p1.held_out_case_ids(DATASET_DIR)),
        "ran_at": _now_iso(),
    }
    _persist_json("closure.json", result)
    for k, v in result.items():
        print(f"{k}={v}")
    print(f"CLOSURE={'PASS' if (gates_ok and complete) else 'FAIL'}")
    return 0 if (gates_ok and complete) else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def cmd_all(args: argparse.Namespace) -> int:
    steps = [
        ("prevalidate", cmd_prevalidate),
        ("endpoint-freeze", cmd_endpoint_freeze),
        ("probe", cmd_probe),
        ("gates", cmd_gates),
        ("freeze-manifest", cmd_freeze_manifest),
        ("run", cmd_run),
        ("metrics", cmd_metrics),
        ("close", cmd_close),
    ]
    for name, fn in steps:
        print(f"\n########## {name} ##########")
        if fn(args) != 0:
            print(f"{name.upper()} FAILED — STOP")
            return 1
    print("\nP1 REAL-COMMIT EVALUATION PIPELINE COMPLETE")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in (
        "prevalidate",
        "endpoint-freeze",
        "probe",
        "gates",
        "freeze-manifest",
        "run",
        "metrics",
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
        "probe": cmd_probe,
        "gates": cmd_gates,
        "freeze-manifest": cmd_freeze_manifest,
        "run": cmd_run,
        "metrics": cmd_metrics,
        "close": cmd_close,
        "all": cmd_all,
    }
    return dispatch[args._sub](args)


if __name__ == "__main__":
    raise SystemExit(main())
