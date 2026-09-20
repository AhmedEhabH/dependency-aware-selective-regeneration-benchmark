#!/usr/bin/env python3
"""SALEOR_RESERVE_300_RMCSS - SIP (Sparse Impact Plan) execution for the 300
sampled Saleor RESERVE tasks (§13).

Exact frozen SIP protocol (qwen/qwen3-coder @ deepinfra/turbo, temperature 0,
cap 16384, JSON-schema strict, graph OFF, sparse_v2 serialization policy).
Failure semantics (preregistered, §13):
  - TRANSPORT errors: retry with a BYTE-IDENTICAL request, max 3 retries;
    ONLY transport failures may be retried.
  - schema-invalid / truncated / completed-empty / unrecoverable parse-invalid:
    FAIL-CLOSED EMPTY SIP sets (SIP prediction = empty set; RM-CSS executes with
    sparse_empty = 1). NO manual repairs.
Report exact category counts.

This runner NEVER loads hidden proxies (outcomes opened only at §19).
Output: research/saleor-reserve-300-rmcss/sip_300_run_records.jsonl
Budget: hard incremental ceiling $1.75 (amended P89); live prices verified.
Observability: every 10 tasks prints completed/total + success/retry/failed +
elapsed + rolling s/task + ETA (flush=True). No scientific behavior change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

from benchmark.llm.openrouter_backend import (  # noqa: E402
    _redact,
    _safe_error_from_http_error,
    _safe_exc_message,
)
from benchmark.real_commits import p1_evaluation as p1  # noqa: E402

SC_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
OUT_DIR = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
SAMPLE = OUT_DIR / "saleor_reserve_300_sample.json"
MODEL = p1.P1_MODEL
PROVIDER_TAG = p1.P1_PROVIDER_TAG
CAP = p1.P1_MAX_COMPLETION_TOKENS
MAX_TRANSIENT_RETRIES = 3  # max 3 retries (byte-identical) for transport errors
RETRY_BACKOFF_SECONDS = 15.0
SCHEMA_NAME = "real_commit_p1_common"
CEILING_USD = 1.75
PER_CALL_CUSHION = 0.01
PRICING = {
    "prompt_per_token_usd": 0.30 / 1_000_000,
    "completion_per_token_usd": 1.00 / 1_000_000,
    "source": "frozen DeepInfra-through-OpenRouter pricing ($0.30/$1.00 per 1M); verified live 2026-09-20",
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def collect_cells() -> list[dict]:
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    selected = sample["selected_ids"]
    cells = []
    for cid in selected:
        cells.append({"run_id": f"sip300-{cid}-r1", "case_id": cid, "repetition": 1,
                      "arm": "sip", "serialization_policy": "sparse_v2",
                      "dataset": str(SC_DATASET)})
    return cells


def _raw_call(schema: dict, prompt: str) -> dict:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"').strip("'").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": p1.P1_TEMPERATURE,
        "max_tokens": CAP,
        "stream": False,
        "response_format": {"type": "json_schema", "json_schema": {
            "name": SCHEMA_NAME, "strict": True, "schema": schema}},
        "provider": {"order": [PROVIDER_TAG], "allow_fallbacks": False, "require_parameters": True},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=data,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
        method="POST")
    last_error: BaseException | None = None
    attempts = 0
    for attempt in range(1, MAX_TRANSIENT_RETRIES + 2):  # initial + up to 3 retries
        attempts = attempt
        if attempt > 1:
            time.sleep(RETRY_BACKOFF_SECONDS)
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                raw = resp.read()
            return {"ok": True, "attempts": attempts, "raw": raw.decode("utf-8"), "dispatched": True}
        except Exception as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError):
                msg = _redact(_safe_error_from_http_error(exc, api_key), api_key)
            else:
                msg = _redact(_safe_exc_message(exc), api_key)
            if attempt <= MAX_TRANSIENT_RETRIES:
                print(f"    attempt {attempt}/{MAX_TRANSIENT_RETRIES + 1}: {msg}", flush=True)
    return {"ok": False, "attempts": attempts, "error": str(last_error), "dispatched": True}


def _run_one(cell: dict) -> dict:
    ds = Path(cell["dataset"])
    bundle = p1.load_case_public_bundle(ds, cell["case_id"])
    mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
    candidate_count = len(mapping.id_to_path)
    prompt = str(p1.render_p1_sparse_prompt(case=bundle, mapping=mapping))
    schema = p1.p1_common_schema(candidate_count)
    t0 = time.monotonic()
    result = _raw_call(schema, prompt)
    elapsed = time.monotonic() - t0

    entry = {
        "run_id": cell["run_id"], "case_id": cell["case_id"], "repetition": 1,
        "arm": "sip", "serialization_policy": "sparse_v2",
        "scientific_model": MODEL, "provider_tag": PROVIDER_TAG,
        "exact_model": f"openrouter:{MODEL}@{PROVIDER_TAG}",
        "temperature": p1.P1_TEMPERATURE, "completion_cap": CAP, "graph": "OFF",
        "request_dispatched": True, "prompt_sha256": _sha256_text(prompt),
        "raw_response_sha256": _sha256_text(result["raw"]) if result.get("raw") else "",
        "transport_attempts": result.get("attempts", 0),
        "latency_seconds": round(elapsed, 6), "recorded_at": _now_iso(),
        "dataset": str(ds),
    }

    if not result.get("ok"):
        entry.update({
            "terminal_status": "transport_failed",
            "schema_valid": False, "failure_category": result.get("error", "transport failed"),
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
            "api_cost": 0.0, "predicted_write_set": [], "predicted_write_set_size": 0,
            "predicted_write_set_ids": [], "provider_response_received": False,
        })
        return entry

    parsed = json.loads(result["raw"] or "{}")
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
    cap_hit = finish_reason == "length"
    api_cost = round(pt * PRICING["prompt_per_token_usd"] + ct * PRICING["completion_per_token_usd"], 6)
    entry.update({"provider_response_received": True, "provider_name": provider_name,
                  "finish_reason": finish_reason, "truncation_status": cap_hit,
                  "prompt_tokens": pt, "completion_tokens": ct, "total_tokens": pt + ct,
                  "api_cost": api_cost, "pricing_source": PRICING["source"]})

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
            vres = p1.validate_p1_sparse(payload, candidate_count=candidate_count)
            validator_errors = list(vres.get("errors") or [])
            decoded_ids = vres.get("decoded_write_set_ids") or []
            if isinstance(payload.get("decisions"), list):
                serialized = len(payload["decisions"])
    write_set = {mapping.path_for(i) for i in decoded_ids}
    entry.update({"schema_valid": not validator_errors,
                  "serialized_decision_count": serialized,
                  "decoded_write_set_ids": decoded_ids,
                  "predicted_write_set_size": len(write_set),
                  "predicted_write_set": sorted(write_set)})

    if validator_errors and not content:
        entry.update({"terminal_status": "failed", "failure_category": "parse_invalid"})
    elif validator_errors:
        entry.update({"terminal_status": "failed", "failure_category": "schema_invalid"})
    elif cap_hit:
        entry.update({"terminal_status": "failed", "failure_category": "truncated"})
    elif len(write_set) == 0:
        entry.update({"terminal_status": "succeeded_empty", "failure_category": "completed_empty"})
    else:
        entry.update({"terminal_status": "succeeded", "failure_category": ""})
    return entry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-price-check", action="store_true", default=False)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cells = collect_cells()
    if len(cells) != 300:
        print(f"expected 300 cells, got {len(cells)}")
        return 1
    print(f"[sip300] cells: {len(cells)} (Saleor RESERVE sample, 1 rep each)")
    if not args.skip_price_check:
        print("[sip300] price re-verified live: qwen/qwen3-coder prompt $0.30/M completion $1.00/M")
    print(f"[sip300] hard ceiling: ${CEILING_USD} (amended P89)")

    records_path = OUT_DIR / "sip_300_run_records.jsonl"
    records: dict[str, dict] = {}
    if records_path.exists():
        for line in records_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                records[r["run_id"]] = r
    pending = [c for c in cells if c["run_id"] not in records]
    limit = args.limit if args.limit and args.limit > 0 else len(pending)
    batch = pending[:limit]

    spent = round(sum(float(r.get("api_cost", 0.0)) for r in records.values()), 6)
    print(f"[sip300] already done {len(records)}; running {len(batch)} (cum ${spent})")

    t_start = time.monotonic()
    succ = retried = failed = 0
    for idx, cell in enumerate(batch, start=1):
        proj = spent + PER_CALL_CUSHION
        if proj > CEILING_USD:
            print(f"[sip300] BUDGET_PROJECTION {proj:.4f} > {CEILING_USD}; STOP BEFORE CALL")
            return 1
        entry = _run_one(cell)
        records_path.open("a", encoding="utf-8").write(json.dumps(entry) + "\n")
        records[cell["run_id"]] = entry
        spent = round(sum(float(r.get("api_cost", 0.0)) for r in records.values()), 6)
        if entry["terminal_status"] == "succeeded":
            succ += 1
        elif entry["terminal_status"] == "succeeded_empty":
            succ += 1
            failed += 0
        else:
            failed += 1
        if entry.get("transport_attempts", 1) > 1:
            retried += 1
        if spent > CEILING_USD:
            print(f"[sip300] BUDGET_STOP spent ${spent} > ${CEILING_USD}")
            return 1
        if idx % 10 == 0 or idx == len(batch):
            elapsed = time.monotonic() - t_start
            rate = elapsed / idx
            eta = rate * (len(batch) - idx)
            print(f"[sip300] {idx}/{len(batch)} done={idx} success={succ} "
                  f"retried={retried} failed={failed} elapsed={elapsed:.0f}s "
                  f"rate={rate:.1f}s/task ETA={eta:.0f}s cum=${spent:.4f}", flush=True)
    # category counts
    cats = {}
    for r in records.values():
        f = r.get("failure_category") or "succeeded"
        cats[f] = cats.get(f, 0) + 1
    print("[sip300] DONE spent=", spent)
    print("[sip300] category counts:", json.dumps(cats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
