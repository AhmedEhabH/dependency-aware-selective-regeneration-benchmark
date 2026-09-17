#!/usr/bin/env python3
# ruff: noqa: E501, N803, N806
# B / N / M are the frozen protocol's budget / omitted-count / missed-count symbols.
"""djangoCMS Route-B CONFIRMATORY execution (authorized 2026-09-17).

Runs EXACTLY the frozen V2 confirmatory protocol on the 80 djangoCMS
INTERNAL_TEST tasks (Ahmed-authorized opening ONLY):
- Sparse-v2 first pass, 3 reps/task (qwen/qwen3-coder @ deepinfra/turbo,
  temp 0, cap 16384, Graph OFF) using the frozen p1 sparse prompt + schema;
- first SUCCEEDED rep defines the Route-B write set (NOT majority/union);
- omitted/PRESERVE residual candidates;
- frozen BM25+Graph-Neighbor Composite ranker
  (= normalized_BM25 + binary_graph_neighbor, historical label CIA);
- bounded verifier: 1 call per (task, B) for B in {1,3,5,10}, B=0 none,
  cap 512, independent across B;
- analytic Random control; ORR/FNRR primary; P/R/F1/FNR secondary;
- hard ceilings 560 calls / 2,100,000 tokens / $1.00 with fail-closed
  per-call reservation; no reruns, no method change;
- raw responses + sha256 persisted; frozen failure taxonomy.

Fail-closed: `--real` requires OPENROUTER_API_KEY. Resumable via a persistent
run_records.jsonl (skips already-recorded cells).
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

from benchmark.llm.openrouter_backend import (  # noqa: E402
    _redact,
    _safe_error_from_http_error,
    _safe_exc_message,
)
from benchmark.real_commits import p1_evaluation as p1  # noqa: E402
from scripts.route_b_v2_robustness import (  # noqa: E402
    V2_DATASET,
    build_task,
    load_case,
)

MODEL = "qwen/qwen3-coder"
PROVIDER_TAG = "deepinfra/turbo"
TEMPERATURE = p1.P1_TEMPERATURE
SPARSE_CAP = 16384
VERIFIER_CAP = 512
SPARSE_SCHEMA = "real_commit_p1_common"
VERIFIER_SCHEMA = "reconsider_booleans"

MAX_CALLS = 560
MAX_TOKENS = 2_100_000
MAX_COST_USD = 1.00
RESERVATION_SPARSE_TOKENS = 7_877
RESERVATION_SPARSE_COST = 0.00302
RESERVATION_VERIFIER_TOKENS = 400
RESERVATION_VERIFIER_COST = 0.00015
PRICING = {"prompt_per_token_usd": 0.30 / 1e6, "completion_per_token_usd": 1.00 / 1e6,
           "source": "frozen DeepInfra-through-OpenRouter pricing"}

BUDGETS = (1, 3, 5, 10)
REPS_PER_TASK = 3

DATASET_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
CASE_IDS_MANIFEST = _PROJECT_DIR / "research" / "transparency" / "djangocms_internal_test_case_ids.json"
OUT_DIR = _PROJECT_DIR / "research" / "djangocms-confirmatory-route-b"
RUN_RECORDS = OUT_DIR / "run_records.jsonl"
RAW_DIR = OUT_DIR / "runs" / "raw"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _raw_openrouter_call(schema: dict[str, Any], prompt: str, cap: int, schema_name: str) -> dict[str, Any]:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"').strip("'").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": cap,
        "stream": False,
        "response_format": {"type": "json_schema", "json_schema": {"name": schema_name, "strict": True, "schema": schema}},
        "provider": {"order": [PROVIDER_TAG], "allow_fallbacks": False, "require_parameters": True},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = resp.read()
        return {"ok": True, "raw": raw.decode("utf-8"), "dispatched": True}
    except Exception as exc:
        if isinstance(exc, urllib.error.HTTPError):
            msg = _redact(_safe_error_from_http_error(exc, api_key), api_key)
        else:
            msg = _redact(_safe_exc_message(exc), api_key)
        return {"ok": False, "error": msg, "dispatched": True}


def _load_internal_test_ids() -> list[str]:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    return sorted(c for c, r in split["assignment"].items() if r == "INTERNAL_TEST")


class Ledger:
    def __init__(self) -> None:
        self.reserved_calls = 0
        self.reserved_tokens = 0
        self.reserved_cost = 0.0
        self.actual_calls = 0
        self.actual_tokens = 0
        self.actual_cost = 0.0
        self.stop_reason = ""

    def can_dispatch(self, res_tokens: int, res_cost: float) -> bool:
        if self.reserved_calls + 1 > MAX_CALLS:
            self.stop_reason = "calls_ceiling"
            return False
        if self.reserved_tokens + res_tokens > MAX_TOKENS:
            self.stop_reason = "tokens_ceiling"
            return False
        if self.reserved_cost + res_cost > MAX_COST_USD:
            self.stop_reason = "cost_ceiling"
            return False
        return True

    def reserve(self, res_tokens: int, res_cost: float) -> None:
        self.reserved_calls += 1
        self.reserved_tokens += res_tokens
        self.reserved_cost += res_cost

    def actual(self, tokens: int, cost: float) -> None:
        self.actual_calls += 1
        self.actual_tokens += tokens
        self.actual_cost += cost


def _load_records() -> dict[str, dict[str, Any]]:
    if not RUN_RECORDS.is_file():
        return {}
    out = {}
    for line in RUN_RECORDS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["run_id"]] = r
    return out


def _append_record(record: dict[str, Any]) -> None:
    RUN_RECORDS.parent.mkdir(parents=True, exist_ok=True)
    with RUN_RECORDS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _sparse_cell(cid: str, rep: int) -> dict[str, Any]:
    bundle = p1.load_case_public_bundle(DATASET_DIR, cid)
    mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
    prompt = str(p1.render_p1_sparse_prompt(case=bundle, mapping=mapping))
    schema = p1.p1_common_schema(len(bundle.candidate_paths))
    return {"run_id": f"CONF-{cid}-rep{rep}", "case_id": cid, "rep": rep, "prompt": prompt,
            "schema": schema, "candidate_count": len(bundle.candidate_paths)}


def _build_sparse_record(cell: dict[str, Any], result: dict[str, Any], elapsed: float) -> dict[str, Any]:
    cid, rep = cell["case_id"], cell["rep"]
    raw_text = result.get("raw") if result.get("ok") else None
    proxy = set(p1.load_hidden_proxy_paths(DATASET_DIR, cid))
    base = {
        "run_id": cell["run_id"], "case_id": cid, "rep": rep, "arm": "sparse_v2",
        "scientific_model": MODEL, "provider_tag": PROVIDER_TAG,
        "exact_model": f"openrouter:{MODEL}@{PROVIDER_TAG}",
        "temperature": TEMPERATURE, "completion_cap": SPARSE_CAP, "graph": "OFF",
        "prompt_sha256": _sha256_text(cell["prompt"]),
        "raw_response_sha256": _sha256_text(raw_text) if raw_text is not None else "",
        "latency_seconds": round(elapsed, 6), "recorded_at": _now_iso(),
        "proxy_size": len(proxy),
    }
    if not result.get("ok"):
        base.update({
            "terminal_status": "failed", "schema_valid": False, "finish_reason": "",
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "model_calls": 0,
            "api_cost": 0.0, "failure_category": result.get("error", "transport failed"),
            "tp": 0, "fp": 0, "fn": len(proxy), "precision": 0.0, "recall": 0.0, "f1": 0.0,
            "fnr": 1.0, "full_recall": False, "decoded_write_set_ids": [],
            "predicted_write_set": [], "predicted_write_set_size": 0, "raw_response_persisted": False,
        })
        return base
    parsed = json.loads(raw_text or "{}")
    choice = (parsed.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = message.get("content") or ""
    finish_reason = choice.get("finish_reason", "")
    usage = parsed.get("usage") or {}
    pt = int(usage.get("prompt_tokens") or 0)
    ct = int(usage.get("completion_tokens") or 0)
    usage_known = usage.get("prompt_tokens") is not None and usage.get("completion_tokens") is not None
    cap_hit = finish_reason == "length"
    api_cost = round(pt * PRICING["prompt_per_token_usd"] + ct * PRICING["completion_per_token_usd"], 6)
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
    terminal = "succeeded" if (not validator_errors and not cap_hit) else "failed"
    bundle = p1.load_case_public_bundle(DATASET_DIR, cid)
    mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
    write_set = {mapping.path_for(i) for i in decoded_ids}
    m = p1.p1_selection_metrics(write_set, proxy)
    base.update({
        "terminal_status": terminal, "schema_valid": not validator_errors,
        "failure_category": "; ".join(validator_errors), "finish_reason": finish_reason,
        "truncation_status": cap_hit, "provider_response_received": True,
        "raw_response_persisted": True, "usage_known": usage_known,
        "prompt_tokens": pt, "completion_tokens": ct, "total_tokens": pt + ct, "model_calls": 1,
        "api_cost": api_cost, "serialized_decision_count": serialized,
        "decoded_write_set_ids": decoded_ids, "predicted_write_set": sorted(write_set),
        "predicted_write_set_size": len(decoded_ids),
        "tp": m["tp"], "fp": m["fp"], "fn": m["fn"], "precision": round(m["precision"], 6),
        "recall": round(m["recall"], 6), "f1": round(m["f1"], 6), "fnr": round(m["fnr"], 6),
        "full_recall": m["full_recall"],
    })
    return base


def _verifier_prompt(intent: str, write_set: list[str], top: list[str], universe: int) -> str:
    cand_block = "\n".join(f"- {p}" for p in top)
    ws_block = "\n".join(f"- {p}" for p in write_set[:20]) or "- (none)"
    return (
        "You are an impact-verification assistant for a software repository.\n"
        "A first-pass impact plan selected a set of files to change. We now\n"
        "reconsider a small set of candidate files the first pass DID NOT select.\n"
        f"\nChange intent:\n{intent}\n"
        f"\nFirst-pass selected files (write set):\n{ws_block}\n"
        f"\nCandidate files to reconsider (path | module/class hint):\n{cand_block}\n"
        f"\nCandidate universe size: {universe}\n"
        "\nFor EACH candidate file, decide whether it is plausibly affected by the "
        "stated change (true = reconsider/verify it; false = leave it alone).\n"
        "Answer ONLY a JSON object: {\"reconsider\": [true, false, ...]} with one "
        f"boolean per candidate in the same order ({len(top)} booleans).\n"
    )


def _verifier_schema(n: int) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {"reconsider": {"type": "array", "items": {"type": "boolean"},
                                      "minItems": n, "maxItems": n}},
        "required": ["reconsider"], "additionalProperties": False,
    }


def _build_verifier_record(cid: str, B: int, prompt: str, top: list[str], result: dict[str, Any], elapsed: float) -> dict[str, Any]:
    run_id = f"CONF-{cid}-b{B}"
    raw_text = result.get("raw") if result.get("ok") else None
    base = {
        "run_id": run_id, "case_id": cid, "B": B, "arm": "verifier",
        "scientific_model": MODEL, "provider_tag": PROVIDER_TAG,
        "exact_model": f"openrouter:{MODEL}@{PROVIDER_TAG}",
        "temperature": TEMPERATURE, "completion_cap": VERIFIER_CAP,
        "prompt_sha256": _sha256_text(prompt), "raw_response_sha256": _sha256_text(raw_text) if raw_text is not None else "",
        "latency_seconds": round(elapsed, 6), "recorded_at": _now_iso(), "top_candidates": top,
    }
    if not result.get("ok"):
        base.update({"terminal_status": "failed", "schema_valid": False, "failure_category": result.get("error", "transport failed"),
                     "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "api_cost": 0.0,
                     "verifier_selected": [], "verifier_recovered": [], "true_missed_in_top": [], "raw_response_persisted": False})
        return base
    parsed = json.loads(raw_text or "{}")
    choice = (parsed.get("choices") or [{}])[0]
    content = (choice.get("message") or {}).get("content", "")
    finish_reason = choice.get("finish_reason", "")
    usage = parsed.get("usage") or {}
    pt = int(usage.get("prompt_tokens") or 0)
    ct = int(usage.get("completion_tokens") or 0)
    api_cost = round(pt * PRICING["prompt_per_token_usd"] + ct * PRICING["completion_per_token_usd"], 6)
    decisions = None
    schema_valid = False
    failure = ""
    if content:
        try:
            parsed_content = json.loads(content)
            decisions = parsed_content.get("reconsider")
            schema_valid = isinstance(decisions, list) and len(decisions) == len(top) and all(isinstance(x, bool) for x in decisions)
            if not schema_valid:
                failure = "schema/parse mismatch"
        except json.JSONDecodeError as e:
            failure = f"content parse: {e}"
    base.update({
        "terminal_status": "succeeded" if schema_valid else "failed",
        "schema_valid": schema_valid, "failure_category": failure,
        "finish_reason": finish_reason, "prompt_tokens": pt, "completion_tokens": ct,
        "total_tokens": pt + ct, "api_cost": api_cost, "raw_response_persisted": True,
    })
    return base


def main() -> int:
    ap = argparse.ArgumentParser(description="djangoCMS confirmatory Route-B (authorized)")
    ap.add_argument("--run-sparse", action="store_true", help="run sparse first pass")
    ap.add_argument("--run-verifier", action="store_true", help="run verifier")
    args = ap.parse_args()

    if not os.environ.get("OPENROUTER_API_KEY", "").strip():
        print("BLOCKED: OPENROUTER_API_KEY not set")
        return 2

    internal_ids = _load_internal_test_ids()
    if len(internal_ids) != 80:
        print("EXPECTED_80", len(internal_ids))
        return 2
    records = _load_records()
    ledger = Ledger()
    for r in records.values():
        ledger.actual(r.get("total_tokens", 0), r.get("api_cost", 0.0))
    print(f"INTERNAL_TEST_TASKS={len(internal_ids)} already_recorded={len(records)}")
    print("AUTHORIZED: djangoCMS V2 INTERNAL_TEST only. RESERVE + Saleor sealed.")

    # ---- SPARSE FIRST PASS ----
    if args.run_sparse:
        for cid in internal_ids:
            if ledger.stop_reason:
                break
            for rep in range(1, REPS_PER_TASK + 1):
                run_id = f"CONF-{cid}-rep{rep}"
                if run_id in records:
                    continue
                if not ledger.can_dispatch(RESERVATION_SPARSE_TOKENS, RESERVATION_SPARSE_COST):
                    break
                ledger.reserve(RESERVATION_SPARSE_TOKENS, RESERVATION_SPARSE_COST)
                cell = _sparse_cell(cid, rep)
                t0 = time.monotonic()
                result = _raw_openrouter_call(cell["schema"], cell["prompt"], SPARSE_CAP, SPARSE_SCHEMA)
                elapsed = time.monotonic() - t0
                rec = _build_sparse_record(cell, result, elapsed)
                ledger.actual(rec.get("total_tokens", 0), rec.get("api_cost", 0.0))
                _append_record(rec)
                records[run_id] = rec
                if result.get("ok") and result.get("raw"):
                    _write_bytes(RAW_DIR / f"{run_id}.txt", result["raw"].encode("utf-8"))
                    _write_bytes(RAW_DIR / f"{run_id}.sha256", (rec["raw_response_sha256"] + "\n").encode("utf-8"))
                print(f"[sparse] {run_id} {rec['terminal_status']} tok={rec.get('total_tokens')} cost={rec.get('api_cost')} reserved={ledger.reserved_tokens} ${ledger.reserved_cost:.4f}", flush=True)
                if ledger.stop_reason:
                    break
        print(f"SPARSE_DONE reserved_calls={ledger.reserved_calls} actual_tokens={ledger.actual_tokens} actual_cost={ledger.actual_cost:.4f}")

    # ---- VERIFIER ----
    if args.run_verifier:
        sparse = {cid: [r for r in records.values() if r["case_id"] == cid and r["arm"] == "sparse_v2"]
                  for cid in internal_ids}
        for cid in internal_ids:
            if ledger.stop_reason:
                break
            reps = sparse.get(cid, [])
            succeeded = [r for r in reps if r["terminal_status"] == "succeeded"]
            if not succeeded:
                _append_record({"run_id": f"CONF-{cid}-excluded", "case_id": cid, "arm": "excluded",
                                "terminal_status": "excluded", "failure_category": "no_succeeded_rep",
                                "recorded_at": _now_iso()})
                records[f"CONF-{cid}-excluded"] = {}
                print(f"[excluded] {cid} no succeeded sparse rep", flush=True)
                continue
            first = succeeded[0]
            write_set = set(first.get("predicted_write_set") or [])
            case = load_case(cid, V2_DATASET)
            proxy = set(p1.load_hidden_proxy_paths(DATASET_DIR, cid))
            task = build_task(cid, case, write_set, proxy)
            rank = sorted(task["candidates"].items(), key=lambda kv: (-kv[1]["bm25"] - kv[1]["graph_neighbor"], kv[0]))
            for B in BUDGETS:
                run_id = f"CONF-{cid}-b{B}"
                if run_id in records:
                    continue
                if not ledger.can_dispatch(RESERVATION_VERIFIER_TOKENS, RESERVATION_VERIFIER_COST):
                    break
                ledger.reserve(RESERVATION_VERIFIER_TOKENS, RESERVATION_VERIFIER_COST)
                B_eff = min(B, task["omitted_size"])
                top = [p for p, _ in rank[:B_eff]]
                if not top:
                    continue
                prompt = _verifier_prompt(case["intent_text"], sorted(write_set), top, task["universe_size"])
                schema = _verifier_schema(len(top))
                t0 = time.monotonic()
                result = _raw_openrouter_call(schema, prompt, VERIFIER_CAP, VERIFIER_SCHEMA)
                elapsed = time.monotonic() - t0
                rec = _build_verifier_record(cid, B, prompt, top, result, elapsed)
                # compute recovered
                decisions = None
                if result.get("ok") and result.get("raw"):
                    try:
                        decisions = json.loads(json.loads(result["raw"])["choices"][0]["message"]["content"]).get("reconsider")
                    except Exception:
                        decisions = None
                rec_sel = [p for p, d in zip(top, decisions or [], strict=False) if d]
                true_missed = [p for p in top if task["candidates"][p]["is_missed_positive"]]
                recovered = [p for p in rec_sel if task["candidates"][p]["is_missed_positive"]]
                rec["verifier_selected"] = rec_sel
                rec["true_missed_in_top"] = true_missed
                rec["verifier_recovered"] = recovered
                rec["oracle_recovered_in_top"] = len(true_missed)
                ledger.actual(rec.get("total_tokens", 0), rec.get("api_cost", 0.0))
                _append_record(rec)
                records[run_id] = rec
                if result.get("ok") and result.get("raw"):
                    _write_bytes(RAW_DIR / f"{run_id}.txt", result["raw"].encode("utf-8"))
                    _write_bytes(RAW_DIR / f"{run_id}.sha256", (rec["raw_response_sha256"] + "\n").encode("utf-8"))
                print(f"[verifier] {run_id} {rec['terminal_status']} recovered={len(recovered)}/{len(true_missed)} tok={rec.get('total_tokens')} cost={rec.get('api_cost')}", flush=True)
                if ledger.stop_reason:
                    break
        print(f"VERIFIER_DONE reserved_calls={ledger.reserved_calls} actual_tokens={ledger.actual_tokens} actual_cost={ledger.actual_cost:.4f}")

    summary = {
        "reserved_calls": ledger.reserved_calls, "reserved_tokens": ledger.reserved_tokens,
        "reserved_cost_usd": round(ledger.reserved_cost, 6),
        "actual_calls": ledger.actual_calls, "actual_tokens": ledger.actual_tokens,
        "actual_cost_usd": round(ledger.actual_cost, 6),
        "max_calls": MAX_CALLS, "max_tokens": MAX_TOKENS, "max_cost_usd": MAX_COST_USD,
        "stop_reason": ledger.stop_reason, "recorded": len(records), "ran_at": _now_iso(),
    }
    (OUT_DIR / "confirmatory_ledger.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
