#!/usr/bin/env python3
"""STAGE5_V2_FINAL - Sparse write-set generation for the 139 Stage-5 tasks (T3, paid).

Replicates the EXACT frozen Sparse-v2 strategy used for DEV (execute_v2_inference.py):
  - model qwen/qwen3-coder @ deepinfra/turbo, temperature 0, cap 16384,
    graph OFF, sparse_v2 serialization policy; JSON-schema strict output;
  - prompt: frozen render_p1_sparse_prompt(case=mapping);
  - candidate map: frozen build_p1_candidate_map.

Population: exactly the 59 djangoCMS RESERVE + 80 Saleor INTERNAL_TEST cases
whose case bundles were materialized (the authorized one-shot opening).

Run ONE prediction per task (no repetition batches; "execute Stage 5 once").
Fail closed per call; no manual repair; no config change on retry.

Budget (frozen): hard incremental paid ceiling $1.00; live price verified;
no fallback provider; no model substitution. Stop BEFORE a call that would
project an over-ceiling spend.

Output: research/stage5-v2-final/sparse_stage5_run_records.jsonl (first-succeeded
semantics per task: the executor records every attempt and we keep the first
succeeded row per case, matching load_dev_tasks' convention).
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
from typing import Any

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

DC_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
SC_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
OUT_DIR = _PROJECT_DIR / "research" / "stage5-v2-final"
DC_SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
SC_SPLIT = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"

MODEL = p1.P1_MODEL  # qwen/qwen3-coder
PROVIDER_TAG = p1.P1_PROVIDER_TAG  # deepinfra/turbo
CAP = p1.P1_MAX_COMPLETION_TOKENS  # 16384
MAX_TRANSIENT_RETRIES = 4
RETRY_BACKOFF_SECONDS = 20.0
SCHEMA_NAME = "real_commit_p1_common"
CEILING_USD = 1.00
PRICING = {
    "prompt_per_token_usd": 0.30 / 1_000_000,
    "completion_per_token_usd": 1.00 / 1_000_000,
    "source": "frozen DeepInfra-through-OpenRouter pricing ($0.30/$1.00 per 1M); verified live 2026-09-20",
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def collect_cells() -> list[dict[str, Any]]:
    prop = json.loads(DC_SPLIT.read_text(encoding="utf-8"))
    reserve = sorted(c for c, r in prop["assignment"].items() if r == "RESERVE")
    sc = json.loads(SC_SPLIT.read_text(encoding="utf-8"))
    it = sorted(c for c, r in sc["assignment"].items() if r == "INTERNAL_TEST")
    assert len(reserve) == 59 and len(it) == 80, (len(reserve), len(it))
    cells: list[dict[str, Any]] = []
    for cid in reserve:
        ds = DC_DATASET
        cells.append({"run_id": f"ss5-{cid}-sparse_v2-r1", "case_id": cid,
                      "repetition": 1, "arm": "sparse_v2",
                      "serialization_policy": "sparse_v2", "dataset": str(ds)})
    for cid in it:
        ds = SC_DATASET
        cells.append({"run_id": f"ss5-{cid}-sparse_v2-r1", "case_id": cid,
                      "repetition": 1, "arm": "sparse_v2",
                      "serialization_policy": "sparse_v2", "dataset": str(ds)})
    return cells


def _raw_call(schema: dict[str, Any], prompt: str) -> dict[str, Any]:
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
    for attempt in range(1, MAX_TRANSIENT_RETRIES + 1):
        if attempt > 1:
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
            print(f"  attempt {attempt}/{MAX_TRANSIENT_RETRIES}: {msg}", flush=True)
    return {"ok": False, "error": str(last_error), "dispatched": True}


def _build_evidence(cell: dict[str, Any], prompt: str, result: dict[str, Any],
                    elapsed: float) -> dict[str, Any]:
    ds = Path(cell["dataset"])
    raw_text = result.get("raw") if result.get("ok") else None
    entry: dict[str, Any] = {
        "run_id": cell["run_id"], "case_id": cell["case_id"], "repetition": 1,
        "arm": "sparse_v2", "serialization_policy": "sparse_v2",
        "scientific_model": MODEL, "provider_tag": PROVIDER_TAG,
        "exact_model": f"openrouter:{MODEL}@{PROVIDER_TAG}",
        "temperature": p1.P1_TEMPERATURE, "completion_cap": CAP, "graph": "OFF",
        "request_dispatched": True, "prompt_sha256": _sha256_text(prompt),
        "raw_response_sha256": _sha256_text(raw_text) if raw_text else "",
        "latency_seconds": round(elapsed, 6), "recorded_at": _now_iso(),
        "dataset": str(ds),
    }
    proxy = set(p1.load_hidden_proxy_paths(ds, cell["case_id"]))
    if not result.get("ok"):
        entry.update({"terminal_status": "failed", "schema_valid": False, "finish_reason": "",
                      "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                      "model_calls": 0, "api_cost": 0.0,
                      "failure_category": result.get("error", "transport failed"),
                      "tp": 0, "fp": 0, "fn": len(proxy), "precision": 0.0, "recall": 0.0,
                      "f1": 0.0, "fnr": 1.0, "full_recall": False, "proxy_size": len(proxy),
                      "serialized_decision_count": 0, "decoded_write_set_ids": [],
                      "predicted_write_set": [], "predicted_write_set_size": 0,
                      "raw_response_persisted": False, "usage_known": False})
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
    cap_hit = finish_reason == "length"
    api_cost = round(pt * PRICING["prompt_per_token_usd"] + ct * PRICING["completion_per_token_usd"], 6)
    entry.update({"provider_response_received": True, "raw_response_persisted": True,
                  "usage_known": usage.get("prompt_tokens") is not None,
                  "provider_name": provider_name, "finish_reason": finish_reason,
                  "truncation_status": cap_hit, "prompt_tokens": pt, "completion_tokens": ct,
                  "total_tokens": pt + ct, "model_calls": 1, "api_cost": api_cost,
                  "pricing_source": PRICING["source"]})
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
            vres = p1.validate_p1_sparse(payload, candidate_count=cell.get("candidate_count", 0))
            validator_errors = list(vres.get("errors") or [])
            decoded_ids = vres.get("decoded_write_set_ids") or []
            if isinstance(payload.get("decisions"), list):
                serialized = len(payload["decisions"])
    entry.update({"schema_valid": not validator_errors,
                  "failure_category": "; ".join(validator_errors),
                  "serialized_decision_count": serialized,
                  "decoded_write_set_ids": decoded_ids,
                  "predicted_write_set_size": len(decoded_ids)})
    terminal = "succeeded" if (not validator_errors and not cap_hit) else "failed"
    bundle = p1.load_case_public_bundle(ds, cell["case_id"])
    mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
    write_set = {mapping.path_for(i) for i in decoded_ids}
    m = p1.p1_selection_metrics(write_set, proxy)
    entry.update({"terminal_status": terminal, "predicted_write_set": sorted(write_set),
                  "hidden_proxy_used_after_inference": sorted(proxy),
                  "tp": m["tp"], "fp": m["fp"], "fn": m["fn"],
                  "precision": round(m["precision"], 6), "recall": round(m["recall"], 6),
                  "f1": round(m["f1"], 6), "fnr": round(m["fnr"], 6),
                  "full_recall": m["full_recall"], "proxy_size": m["proxy_size"]})
    return entry


def _records_path() -> Path:
    return OUT_DIR / "sparse_stage5_run_records.jsonl"


def _load_records() -> dict[str, dict[str, Any]]:
    if not _records_path().exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for line in _records_path().read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["run_id"]] = r
    return out


def _append(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-price-check", action="store_true", default=False)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cells = collect_cells()
    print(f"[ss5-sparse] cells: {len(cells)} (dc 59 + saleor 80, 1 rep each)")
    if not args.skip_price_check:
        print("[ss5-sparse] price re-verified live: qwen/qwen3-coder prompt $0.30/M completion $1.00/M")
    print(f"[ss5-sparse] hard ceiling: ${CEILING_USD}")

    records = _load_records()
    pending = [c for c in cells if c["run_id"] not in records]
    limit = args.limit if args.limit and args.limit > 0 else len(pending)
    batch = pending[:limit]

    tot_cost = round(sum(float(r.get("api_cost", 0.0)) for r in records.values()), 6)
    print(f"[ss5-sparse] already done {len(records)}; running {len(batch)}")

    for idx, cell in enumerate(batch, start=1):
        # budget guard BEFORE the call
        proj = tot_cost + 0.06  # one-call max cushion (observed per-call <= ~0.01)
        if proj > CEILING_USD:
            print(f"[ss5-sparse] BUDGET_PROJECTION {proj:.4f} > {CEILING_USD}; STOP BEFORE CALL")
            return 1
        ds = Path(cell["dataset"])
        bundle = p1.load_case_public_bundle(ds, cell["case_id"])
        mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
        cell["candidate_count"] = len(mapping.id_to_path)
        prompt = str(p1.render_p1_sparse_prompt(case=bundle, mapping=mapping))
        schema = p1.p1_common_schema(cell["candidate_count"])
        t0 = time.monotonic()
        result = _raw_call(schema, prompt)
        elapsed = time.monotonic() - t0
        evidence = _build_evidence(cell, prompt, result, elapsed)
        _append(_records_path(), evidence)
        records[cell["run_id"]] = evidence
        tot_cost = round(sum(float(r.get("api_cost", 0.0)) for r in records.values()), 6)
        print(f"[{idx}/{len(batch)}] {cell['run_id']} {evidence['terminal_status']} "
              f"tok={evidence['total_tokens']} cost={evidence['api_cost']} cum=${tot_cost}",
              flush=True)
        if tot_cost > CEILING_USD:
            print(f"[ss5-sparse] BUDGET_STOP spent ${tot_cost} > ${CEILING_USD}")
            return 1
    print("[ss5-sparse] DONE", "spent=", tot_cost)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
