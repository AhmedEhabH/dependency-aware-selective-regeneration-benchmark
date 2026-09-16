#!/usr/bin/env python3
# ruff: noqa: E501, N806
# B is the frozen protocol's budget symbol (docs/ROUTE_B_VERIFIER_PILOT_PROTOCOL.md).
"""Route B — small real bounded-verifier pilot (Block 4, DEVELOPMENT only).

Frozen protocol: docs/ROUTE_B_VERIFIER_PILOT_PROTOCOL.md.
- <=30 independent dev tasks; 1 verifier call/task; <=30 calls;
  <=300,000 total tokens; <=USD 0.30; fail-closed; no reruns.
- Candidate ranker: CIA (0.5 BM25 + 0.5 graph neighbor) over Sparse-omitted.
- B in {1,3,5}; model qwen3-coder @ deepinfra/turbo (OpenRouter), temp 0,
  cap 512; JSON boolean array output; strict parser; fail-closed on parse error.

Outputs:
- research/transparency/route_b_verifier_pilot_results.json
- research/transparency/route_b_verifier_pilot/runs/<run_id>.json
- research/transparency/route_b_verifier_pilot/runs/raw/<run_id>.txt + .sha256
- reports/ROUTE_B_VERIFIER_PILOT_REPORT.md
"""

from __future__ import annotations

import hashlib
import json
import os
import random
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
from scripts.route_b_v2_robustness import (  # noqa: E402
    V1_DATASET,
    V1_RECORDS,
    V2_DATASET,
    V2_RECORDS,
    _load_run,
    build_task,
    load_case,
)

SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
OUT_DIR = _PROJECT_DIR / "research" / "transparency" / "route_b_verifier_pilot"
OUT_JSON = OUT_DIR / "route_b_verifier_pilot_results.json"
OUT_MD = _PROJECT_DIR / "reports" / "ROUTE_B_VERIFIER_PILOT_REPORT.md"

SEED = 20260917
MAX_TASKS = 30
MAX_CALLS = 30
TOKEN_CEILING = 300_000
COST_CEILING = 0.30
BUDGETS = (1, 3, 5)
MODEL = "qwen/qwen3-coder"
PROVIDER_TAG = "deepinfra/turbo"
CAP = 512
PRICING = {"prompt_per_token_usd": 0.30 / 1e6, "completion_per_token_usd": 1.00 / 1e6}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def _write_bytes(p: Path, b: bytes) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b)


def _raw_openrouter_call(schema: dict[str, Any], prompt: str) -> dict[str, Any]:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"').strip("'").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": CAP,
        "stream": False,
        "response_format": {"type": "json_schema", "json_schema": {"name": "reconsider_booleans", "strict": True, "schema": schema}},
        "provider": {"order": [PROVIDER_TAG], "allow_fallbacks": False, "require_parameters": True},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    last_error: BaseException | None = None
    for attempt in range(1, 4):
        if attempt > 1:
            time.sleep(15)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read()
            return {"ok": True, "attempt": attempt, "raw": raw.decode("utf-8"), "dispatched": True}
        except Exception as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError):
                msg = _redact(_safe_error_from_http_error(exc, api_key), api_key)
            else:
                msg = _redact(_safe_exc_message(exc), api_key)
            print(f"  attempt {attempt} failed: {msg}")
    return {"ok": False, "error": str(last_error), "dispatched": True}


def build_verifier_prompt(intent: str, write_set: list[str], top_cands: list[str], universe: int) -> str:
    cand_block = "\n".join(f"- {p}" for p in top_cands)
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
        f"boolean per candidate in the same order ({len(top_cands)} booleans).\n"
    )


def main() -> int:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    assign = split["assignment"]
    v1_recs = _load_run(V1_RECORDS)
    v2_recs = _load_run(V2_RECORDS)
    v1_case_ids = {r["case_id"] for r in v1_recs}

    by_case: dict[str, dict[str, Any]] = {}
    rep_meta = {}
    for rec in v1_recs + v2_recs:
        if rec["terminal_status"] != "succeeded":
            continue
        cid = rec["case_id"]
        if cid in by_case:
            continue
        dataset = V1_DATASET if cid in v1_case_ids else V2_DATASET
        case = load_case(cid, dataset)
        proxy = set(rec["hidden_proxy_used_after_inference"])
        write_set = set(rec.get("predicted_write_set") or [])
        task = build_task(cid, case, write_set, proxy)
        task["role"] = assign.get(cid, "V1_DEV")
        by_case[cid] = task
        rep_meta[cid] = {"dataset": dataset, "write_set": write_set, "case": case}

    # Tasks with >=1 Sparse FN among omitted (non-trivial omission recovery).
    candidates = [t for t in by_case.values() if t["n_missed"] >= 1]
    # Deterministic stratified sample to <=30.
    rng = random.Random(SEED)
    rng.shuffle(candidates)
    selected = candidates[:MAX_TASKS]

    # CIA ranking (0.5 BM25 + 0.5 graph neighbor) over omitted candidates.
    def cia_rank(cands):
        return sorted(cands.items(), key=lambda kv: (-kv[1]["bm25"] - kv[1]["graph_neighbor"], kv[0]))

    calls = 0
    total_tokens = 0
    total_cost = 0.0
    records = []
    for t in selected:
        if calls >= MAX_CALLS:
            break
        cid = t["case_id"]
        rank = cia_rank(t["candidates"])
        for B in BUDGETS:
            if calls >= MAX_CALLS:
                break
            B_eff = min(B, t["omitted_size"])
            top = [p for p, _ in rank[:B_eff]]
            if not top:
                continue
            meta = rep_meta[cid]
            prompt = build_verifier_prompt(
                meta["case"]["intent_text"], sorted(meta["write_set"]), top, t["universe_size"]
            )
            schema = {
                "type": "object",
                "properties": {
                    "reconsider": {
                        "type": "array",
                        "items": {"type": "boolean"},
                        "minItems": len(top),
                        "maxItems": len(top),
                    }
                },
                "required": ["reconsider"],
                "additionalProperties": False,
            }
            run_id = f"vp-{cid}-b{B}"
            t0 = time.monotonic()
            result = _raw_openrouter_call(schema, prompt)
            elapsed = time.monotonic() - t0
            raw_text = result.get("raw") if result.get("ok") else None
            parsed_content = None
            decisions = None
            schema_valid = False
            failure = ""
            if raw_text:
                try:
                    parsed = json.loads(raw_text)
                    content = (parsed.get("choices") or [{}])[0].get("message", {}).get("content", "")
                    usage = parsed.get("usage") or {}
                    prompt_tok = int(usage.get("prompt_tokens") or 0)
                    compl_tok = int(usage.get("completion_tokens") or 0)
                    cost = round(prompt_tok * PRICING["prompt_per_token_usd"] + compl_tok * PRICING["completion_per_token_usd"], 6)
                    parsed_content = json.loads(content)
                    decisions = parsed_content.get("reconsider")
                    schema_valid = isinstance(decisions, list) and len(decisions) == len(top) and all(isinstance(x, bool) for x in decisions)
                    if not schema_valid:
                        failure = "schema/parse mismatch"
                    # compute recovery vs proxy (evaluation-only)
                    rec_sel = [p for p, d in zip(top, decisions or [], strict=False) if d]
                    true_missed = [p for p in top if t["candidates"][p]["is_missed_positive"]]
                    recovered = [p for p in rec_sel if t["candidates"][p]["is_missed_positive"]]
                    record = {
                        "run_id": run_id, "case_id": cid, "B": B, "role": t["role"],
                        "prompt_sha256": _sha256_text(prompt), "raw_response_sha256": _sha256_text(raw_text),
                        "schema_valid": schema_valid, "failure": failure,
                        "top_candidates": top, "verifier_selected": rec_sel,
                        "true_missed_in_top": true_missed, "verifier_recovered": recovered,
                        "oracle_recovered_in_top": len(true_missed),
                        "prompt_tokens": prompt_tok, "completion_tokens": compl_tok,
                        "total_tokens": prompt_tok + compl_tok, "api_cost": cost,
                        "latency_seconds": round(elapsed, 3), "recorded_at": _now_iso(),
                        "terminal_status": "succeeded" if schema_valid else "failed",
                    }
                    calls += 1
                    total_tokens += record["total_tokens"]
                    total_cost += cost
                    records.append(record)
                    OUT_DIR.mkdir(parents=True, exist_ok=True)
                    _write_bytes(OUT_DIR / "runs" / f"{run_id}.json", json.dumps(record, indent=2).encode("utf-8"))
                    _write_bytes(OUT_DIR / "runs" / "raw" / f"{run_id}.txt", raw_text.encode("utf-8"))
                    _write_bytes(OUT_DIR / "runs" / "raw" / f"{run_id}.sha256", (_sha256_text(raw_text) + "\n").encode("utf-8"))
                    print(f"[{run_id}] valid={schema_valid} tok={record['total_tokens']} cost={cost} recovered={len(recovered)}/{len(true_missed)}", flush=True)
                    if total_tokens > TOKEN_CEILING or total_cost > COST_CEILING:
                        print("VERIFIER_BUDGET_STOP")
                        break
                except json.JSONDecodeError as e:
                    failure = f"content parse: {e}"
                    print(f"[{run_id}] PARSE_FAIL {failure}", flush=True)
            else:
                failure = result.get("error", "transport failed")
                print(f"[{run_id}] TRANSPORT_FAIL {failure}", flush=True)
        if total_tokens > TOKEN_CEILING or total_cost > COST_CEILING:
            break

    result = {
        "study_id": "route-b-verifier-pilot",
        "n_tasks_selected": len(selected),
        "n_calls_made": calls,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "token_ceiling": TOKEN_CEILING,
        "cost_ceiling": COST_CEILING,
        "budget_respected": total_tokens <= TOKEN_CEILING and total_cost <= COST_CEILING,
        "records": records,
    }
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # Report
    valid = [r for r in records if r["schema_valid"]]
    md = [
        "# Route B — Bounded-Verifier Pilot (DEVELOPMENT only)",
        "",
        f"**Date:** 2026-09-17  **Calls:** {calls}/{MAX_CALLS}  **Valid:** {len(valid)}",
        f"**Tokens:** {total_tokens}  **Cost:** ${total_cost:.4f}",
        "Frozen: qwen3-coder @ deepinfra/turbo, temp 0, cap 512, CIA ranker.",
        "",
        "| run_id | B | valid | recovered/top-missed | tokens | cost |",
        "|---|---|---|---:|---:|---:|",
    ]
    for r in records:
        md.append(
            f"| {r['run_id']} | {r['B']} | {r['schema_valid']} | "
            f"{len(r['verifier_recovered'])}/{len(r['true_missed_in_top'])} | "
            f"{r['total_tokens']} | {r['api_cost']:.4f} |"
        )
    md += [
        "",
        "## Decomposition",
        "",
        "- First-pass omission: Sparse FNs (per task in results JSON).",
        "- Ranking headroom: Oracle@B recovered FNs (Route B V2).",
        "- Verifier recovery@B: verifier-selected ∩ true missed.",
        "- Verifier vs CIA-alone@B: does the verifier add over the ranker?",
        "- InspectAll: all missed at full reconsideration.",
        "",
        "Full machine-readable results: research/transparency/route_b_verifier_pilot/",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print("calls", calls, "tokens", total_tokens, "cost", round(total_cost, 4))
    print("outputs:", OUT_JSON, OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
