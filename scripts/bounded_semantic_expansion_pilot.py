#!/usr/bin/env python3
# ruff: noqa: E501, N806
# B is the frozen protocol's budget symbol (docs/BOUNDED_SEMANTIC_RERANK_VERIFY_PROTOCOL_FROZEN.md).
"""BOUNDED SEMANTIC EXPANSION PILOT — Stage 4 (AUTHORIZED 2026-09-18).

Runs the frozen protocol on DEVELOPMENT (djangoCMS DEV + Saleor DEV):

  Arm A — Frozen Route-B verifier (baseline): per task, 1 verifier call per
          (task, B), B in {1,3,5,10} -> 4 calls/task. Top-B = frozen composite
          (BM25 + graph-neighbor). Reuses the EXISTING verifier prompt + schema
          (docs/ROUTE_B_VERIFIER_PILOT_PROTOCOL.md).
  Arm B — Expanded-pool bounded semantic rerank/verify (candidate): per task,
          ONE call over the deterministic expanded pool (Route-B top-10 UNION
          reverse-1hop consumers, dedupe, pre-order desc bm25 then asc path,
          hard cap C=40). The model returns an ORDERED list of the pool
          candidates it would reconsider; the first B of that list is the
          addition at budget B.
  Arm C — Analytic Random (hypergeometric expectation) + Oracle ranking
          references (deterministic, no calls).

Frozen model/route: qwen3-coder (Qwen3-Coder-480B-A35B-Instruct) via OpenRouter,
deepinfra/turbo preferred, fallback OFF, temp 0, completion cap 512.
Strict JSON schema; fail-closed on parse/schema/transport failure (recorded,
never retried); no result-based reruns; no fallback provider.

Budget (frozen): <=300 calls (240 Arm A + 60 Arm B), <=300,000 tokens,
<=USD 0.30, <=60 min wall-clock; cumulative reservation ledger (Arm A reserve
400 tok / $0.00015; Arm B reserve 1500 tok / $0.00040) stops BEFORE any
dispatch that would breach a ceiling.

Resume: a run whose <run_id>.json already exists under runs/ is LOADED from
disk (not re-dispatched). This preserves already-dispatched calls across a
harness restart without re-spending.

Outputs:
- research/bounded-semantic-expansion/pilot_registration_freeze.json (BEFORE calls)
- research/bounded-semantic-expansion/pilot_results.json
- research/bounded-semantic-expansion/ledger.json
- research/bounded-semantic-expansion/runs/<run_id>.json + raw/<run_id>.txt + .sha256
"""
from __future__ import annotations

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

from benchmark.llm.openrouter_backend import (  # noqa: E402
    _redact,
    _safe_error_from_http_error,
    _safe_exc_message,
)
from benchmark.recall.data import load_dev_tasks  # noqa: E402
from benchmark.recall.rankers import rank_composite  # noqa: E402

OUT_DIR = _PROJECT_DIR / "research" / "bounded-semantic-expansion"
RUNS_DIR = OUT_DIR / "runs"
RAW_DIR = RUNS_DIR / "raw"
REG_JSON = OUT_DIR / "pilot_registration_freeze.json"
RESULT_JSON = OUT_DIR / "pilot_results.json"
LEDGER_JSON = OUT_DIR / "ledger.json"

SEED = 20260918
MAX_TASKS_PER_REPO = 30
BUDGETS = (1, 3, 5, 10)
POOL_CAP = 40
B_MAX_ROUTE_B = 10
MODEL = "qwen/qwen3-coder"
PROVIDER_TAG = "deepinfra/turbo"
CAP = 512
PRICING = {"prompt_per_token_usd": 0.30 / 1e6, "completion_per_token_usd": 1.00 / 1e6}
MAX_CALLS = 300
TOKEN_CEILING = 300_000
COST_CEILING = 0.30
WALL_CEILING_S = 60 * 60
RESERVE_A = {"tokens": 400, "cost": 0.00015}
RESERVE_B = {"tokens": 1500, "cost": 0.00040}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def _write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def _raw_openrouter_call(schema: dict, prompt: str) -> dict:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"').strip("'").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": CAP,
        "stream": False,
        "response_format": {"type": "json_schema", "json_schema": {"name": "pilot_output", "strict": True, "schema": schema}},
        "provider": {"order": [PROVIDER_TAG], "allow_fallbacks": False, "require_parameters": True},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    last_error: BaseException | None = None
    for attempt in range(1, 4):  # transport-level retry only; NEVER result-based
        if attempt > 1:
            time.sleep(15)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read()
            return {"ok": True, "attempt": attempt, "raw": raw.decode("utf-8")}
        except Exception as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError):
                msg = _redact(_safe_error_from_http_error(exc, api_key), api_key)
            else:
                msg = _redact(_safe_exc_message(exc), api_key)
            print(f"  attempt {attempt} transport failed: {msg}", flush=True)
    return {"ok": False, "error": str(last_error)}


def build_arm_a_prompt(intent: str, write_set: list[str], top_cands: list[str], universe: int) -> str:
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


def build_arm_b_prompt(intent: str, write_set: list[str], pool: list[str], universe: int) -> str:
    cand_block = "\n".join(f"- {p}" for p in pool)
    ws_block = "\n".join(f"- {p}" for p in write_set[:20]) or "- (none)"
    return (
        "You are an impact-verification assistant for a software repository.\n"
        "A first-pass impact plan selected a set of files to change. We now\n"
        "reconsider a bounded pre-filtered POOL of candidate files the first\n"
        "pass DID NOT select.\n"
        f"\nChange intent:\n{intent}\n"
        f"\nFirst-pass selected files (write set):\n{ws_block}\n"
        f"\nCandidate pool to reconsider (path | module/class hint):\n{cand_block}\n"
        f"\nCandidate universe size: {universe}\n"
        "\nDecide which pool candidates are plausibly affected by the stated\n"
        "change. Return an ORDERED list, most plausibly affected FIRST. Only\n"
        "include candidates you believe are plausibly affected (typically a\n"
        "small subset). Keep each reason to one short phrase.\n"
        'Answer ONLY a JSON object: {"ordered": [{"path": "<exact path from the '
        'pool>", "reason": "<short>"}, ...]}.\n'
    )


def arm_a_schema(n: int) -> dict:
    return {
        "type": "object",
        "properties": {
            "reconsider": {
                "type": "array",
                "items": {"type": "boolean"},
                "minItems": n,
                "maxItems": n,
            }
        },
        "required": ["reconsider"],
        "additionalProperties": False,
    }


def arm_b_schema(max_items: int) -> dict:
    return {
        "type": "object",
        "properties": {
            "ordered": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["path", "reason"],
                    "additionalProperties": False,
                },
                "maxItems": max_items,
            }
        },
        "required": ["ordered"],
        "additionalProperties": False,
    }


def _fn_paths(t) -> set[str]:
    return {c["path"] for c in t.candidates if c["is_missed_positive"]}


def _consumers(t) -> list[str]:
    return sorted(c["path"] for c in t.candidates if c["consumer"])


def build_pool(t) -> list[str]:
    """Frozen pool: Route-B composite top-10 UNION reverse-1hop consumers."""
    base = list(rank_composite(t))[:B_MAX_ROUTE_B]
    union: set[str] = set(base) | set(_consumers(t))
    cand_map = {c["path"]: c for c in t.candidates}
    ordered = sorted(union, key=lambda p: (-float(cand_map[p]["bm25"]), p))
    return ordered[:POOL_CAP]


def stratified_sample(tasks, max_n: int) -> list:
    eligible = sorted([t for t in tasks if t.n_missed >= 1 and t.omitted_size >= 5], key=lambda t: t.case_id)
    total = len(eligible)
    years: dict[str, list] = {}
    for t in eligible:
        years.setdefault(str(t.year or "NA"), []).append(t)
    quota: dict[str, int] = {}
    remaining = max_n
    for y in sorted(years):
        q = min(len(years[y]), round(max_n * len(years[y]) / total))
        quota[y] = q
        remaining -= q
    selected: list = []
    for y in sorted(years):
        grp = sorted(years[y], key=lambda t: (t.universe_size, t.case_id))
        selected.extend(grp[: quota[y]])
    for y in sorted(years):
        if remaining <= 0:
            break
        grp = sorted(years[y], key=lambda t: (t.universe_size, t.case_id))
        for t in grp[quota[y]:]:
            if remaining <= 0:
                break
            selected.append(t)
            remaining -= 1
    return sorted(selected, key=lambda t: t.case_id)


def _parse_usage_and_content(raw_text: str) -> tuple[dict, str]:
    parsed = json.loads(raw_text)
    content = (parsed.get("choices") or [{}])[0].get("message", {}).get("content", "")
    usage = parsed.get("usage") or {}
    return usage, content


def main() -> int:
    t_load0 = time.monotonic()
    tasks = load_dev_tasks()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]
    sample = stratified_sample(dc, MAX_TASKS_PER_REPO) + stratified_sample(sc, MAX_TASKS_PER_REPO)

    registration = {
        "study_id": "bounded-semantic-expansion-pilot",
        "authorization": "2026-09-18 user authorization (<=300 calls / <=300,000 tokens / <=$0.30 / <=60 min)",
        "model": MODEL,
        "provider": PROVIDER_TAG,
        "temperature": 0.0,
        "completion_cap": CAP,
        "pool_cap": POOL_CAP,
        "budgets": list(BUDGETS),
        "seed": SEED,
        "arms": {
            "A": "Route-B verifier baseline, 4 calls/task (B in {1,3,5,10}), frozen composite top-B",
            "B": "expanded-pool bounded semantic rerank/verify, 1 call/task, first-B of ordered list",
            "C": "analytic Random + Oracle ranking references (no calls)",
        },
        "ceilings": {"calls": MAX_CALLS, "tokens": TOKEN_CEILING, "cost_usd": COST_CEILING, "wall_seconds": WALL_CEILING_S},
        "reservations": {"arm_a": RESERVE_A, "arm_b": RESERVE_B},
        "sample": [],
    }
    for t in sample:
        pool = build_pool(t)
        registration["sample"].append({
            "case_id": t.case_id, "repository": t.repository, "role": t.role,
            "year": t.year, "universe_size": t.universe_size, "omitted_size": t.omitted_size,
            "n_missed": t.n_missed, "pool_size": len(pool), "pool": pool,
            "arm_a_tops": {str(B): list(rank_composite(t))[: min(B, t.omitted_size)] for B in BUDGETS},
            "intent_sha256": _sha256_text(t.intent_text),
        })
    REG_JSON.parent.mkdir(parents=True, exist_ok=True)
    _write_text(REG_JSON, json.dumps(registration, indent=2))
    print(f"[registration frozen] tasks={len(sample)} file={REG_JSON}", flush=True)
    print("  repo counts:", {r: sum(1 for s in registration["sample"] if s["repository"] == r) for r in ("djangocms", "saleor")})

    ledger = {
        "study_id": "bounded-semantic-expansion-pilot",
        "reserved_calls": 0, "actual_calls": 0, "reserved_tokens": 0, "actual_tokens": 0,
        "reserved_cost_usd": 0.0, "actual_cost_usd": 0.0, "wall_seconds": 0.0,
        "ceilings": {"calls": MAX_CALLS, "tokens": TOKEN_CEILING, "cost_usd": COST_CEILING, "wall_seconds": WALL_CEILING_S},
        "stop_reason": "",
    }

    def check_and_reserve(arm: str) -> bool:
        reserve = RESERVE_A if arm == "A" else RESERVE_B
        if ledger["actual_calls"] + 1 > MAX_CALLS:
            ledger["stop_reason"] = "CALL_CEILING"
            return False
        if ledger["reserved_tokens"] + reserve["tokens"] > TOKEN_CEILING:
            ledger["stop_reason"] = "TOKEN_CEILING"
            return False
        if ledger["reserved_cost_usd"] + reserve["cost"] > COST_CEILING:
            ledger["stop_reason"] = "COST_CEILING"
            return False
        if time.monotonic() - t_load0 > WALL_CEILING_S:
            ledger["stop_reason"] = "WALL_CEILING"
            return False
        ledger["reserved_calls"] += 1
        ledger["reserved_tokens"] += reserve["tokens"]
        ledger["reserved_cost_usd"] = round(ledger["reserved_cost_usd"] + reserve["cost"], 6)
        return True

    records: list[dict] = []
    resumed = 0

    def record(run_id: str, rec: dict) -> None:
        nonlocal resumed
        rec.pop("_loaded", None)
        if rec.get("_from_disk"):
            rec.pop("_from_disk", None)
            resumed += 1
            records.append(rec)
            return
        records.append(rec)
        _write_text(RUNS_DIR / f"{run_id}.json", json.dumps(rec, indent=2))
        if rec.get("raw_response"):
            _write_text(RAW_DIR / f"{run_id}.txt", rec["raw_response"])
            _write_text(RAW_DIR / f"{run_id}.sha256", _sha256_text(rec["raw_response"]) + "\n")
        if rec["arm"] == "A":
            print(f"[{run_id}] valid={rec['schema_valid']} tok={rec['total_tokens']} cost={rec['api_cost']:.6f} "
                  f"recovered={len(rec['verifier_recovered'])}/{len(rec['true_missed_in_top'])}", flush=True)
        else:
            print(f"[{run_id}] valid={rec['schema_valid']} tok={rec['total_tokens']} cost={rec['api_cost']:.6f} "
                  f"ordered={len(rec['ordered_selected'])} fns_in_pool={rec['n_fns_in_pool']}", flush=True)

    def load_existing(run_id: str) -> dict | None:
        p = RUNS_DIR / f"{run_id}.json"
        if p.is_file():
            rec = json.loads(p.read_text(encoding="utf-8"))
            rec["_from_disk"] = True
            return rec
        return None

    # ---------------- ARM A ----------------
    print("=== ARM A: Route-B verifier (4 calls/task) ===", flush=True)
    for t in sample:
        if ledger["stop_reason"]:
            break
        meta = next(s for s in registration["sample"] if s["case_id"] == t.case_id)
        for B in BUDGETS:
            if ledger["stop_reason"]:
                break
            top = meta["arm_a_tops"][str(B)]
            if not top:
                continue
            prompt = build_arm_a_prompt(t.intent_text, sorted(t.write_set), top, t.universe_size)
            schema = arm_a_schema(len(top))
            run_id = f"armA-{t.case_id}-b{B}"
            existing = load_existing(run_id)
            if existing is not None:
                record(run_id, existing)
                ledger["actual_calls"] += 1
                ledger["actual_tokens"] += existing["total_tokens"]
                ledger["actual_cost_usd"] = round(ledger["actual_cost_usd"] + existing["api_cost"], 6)
                continue
            if not check_and_reserve("A"):
                break
            t0 = time.monotonic()
            result = _raw_openrouter_call(schema, prompt)
            elapsed = time.monotonic() - t0
            raw_text = result.get("raw") if result.get("ok") else None
            decisions = None
            schema_valid = False
            failure = ""
            prompt_tok = compl_tok = 0
            cost = 0.0
            rec_sel: list[str] = []
            if raw_text:
                try:
                    usage, content = _parse_usage_and_content(raw_text)
                    prompt_tok = int(usage.get("prompt_tokens") or 0)
                    compl_tok = int(usage.get("completion_tokens") or 0)
                    cost = round(prompt_tok * PRICING["prompt_per_token_usd"] + compl_tok * PRICING["completion_per_token_usd"], 6)
                    parsed_content = json.loads(content)
                    decisions = parsed_content.get("reconsider")
                    schema_valid = (isinstance(decisions, list) and len(decisions) == len(top)
                                    and all(isinstance(x, bool) for x in decisions))
                    if not schema_valid:
                        failure = "schema/parse mismatch"
                    rec_sel = [p for p, d in zip(top, decisions or [], strict=False) if d]
                except json.JSONDecodeError as e:
                    failure = f"content parse: {e}"
            else:
                failure = result.get("error", "transport failed")
            true_missed = [p for p in top if p in _fn_paths(t)]
            recovered = [p for p in rec_sel if p in _fn_paths(t)]
            ledger["actual_calls"] += 1
            ledger["actual_tokens"] += prompt_tok + compl_tok
            ledger["actual_cost_usd"] = round(ledger["actual_cost_usd"] + cost, 6)
            rec = {
                "run_id": run_id, "case_id": t.case_id, "repository": t.repository,
                "arm": "A", "B": B, "role": t.role,
                "prompt_sha256": _sha256_text(prompt),
                "raw_response": raw_text or "",
                "raw_response_sha256": _sha256_text(raw_text or ""),
                "schema_valid": schema_valid, "failure": failure,
                "top_candidates": top, "verifier_selected": rec_sel,
                "true_missed_in_top": true_missed, "verifier_recovered": recovered,
                "oracle_recovered_in_top": len(true_missed),
                "prompt_tokens": prompt_tok, "completion_tokens": compl_tok,
                "total_tokens": prompt_tok + compl_tok, "api_cost": cost,
                "latency_seconds": round(elapsed, 3), "recorded_at": _now_iso(),
                "terminal_status": "succeeded" if schema_valid else "failed",
            }
            record(run_id, rec)
            if ledger["actual_tokens"] > TOKEN_CEILING or ledger["actual_cost_usd"] > COST_CEILING:
                ledger["stop_reason"] = "ACTUAL_CEILING_BREACH"
                break

    # ---------------- ARM B ----------------
    print("=== ARM B: expanded-pool bounded rerank/verify (1 call/task) ===", flush=True)
    for t in sample:
        if ledger["stop_reason"]:
            break
        meta = next(s for s in registration["sample"] if s["case_id"] == t.case_id)
        pool = meta["pool"]
        if not pool:
            continue
        prompt = build_arm_b_prompt(t.intent_text, sorted(t.write_set), pool, t.universe_size)
        schema = arm_b_schema(len(pool))
        run_id = f"armB-{t.case_id}"
        existing = load_existing(run_id)
        if existing is not None:
            record(run_id, existing)
            ledger["actual_calls"] += 1
            ledger["actual_tokens"] += existing["total_tokens"]
            ledger["actual_cost_usd"] = round(ledger["actual_cost_usd"] + existing["api_cost"], 6)
            continue
        if not check_and_reserve("B"):
            break
        t0 = time.monotonic()
        result = _raw_openrouter_call(schema, prompt)
        elapsed = time.monotonic() - t0
        raw_text = result.get("raw") if result.get("ok") else None
        ordered: list[str] = []
        schema_valid = False
        failure = ""
        prompt_tok = compl_tok = 0
        cost = 0.0
        if raw_text:
            try:
                usage, content = _parse_usage_and_content(raw_text)
                prompt_tok = int(usage.get("prompt_tokens") or 0)
                compl_tok = int(usage.get("completion_tokens") or 0)
                cost = round(prompt_tok * PRICING["prompt_per_token_usd"] + compl_tok * PRICING["completion_per_token_usd"], 6)
                parsed_content = json.loads(content)
                items = parsed_content.get("ordered") or []
                seen: set[str] = set()
                ordered = []
                for it in items:
                    p = it.get("path")
                    if isinstance(p, str) and p in set(pool) and p not in seen:
                        seen.add(p)
                        ordered.append(p)
                schema_valid = len(ordered) == len(items)
                if not schema_valid:
                    failure = "schema/parse mismatch (duplicate or non-pool path)"
            except json.JSONDecodeError as e:
                failure = f"content parse: {e}"
        else:
            failure = result.get("error", "transport failed")
        fn_set = _fn_paths(t)
        true_missed_in_pool = [p for p in pool if p in fn_set]
        per_b = {}
        for B in BUDGETS:
            add = ordered[:B]
            recovered = [p for p in add if p in fn_set]
            per_b[str(B)] = {"additions": add, "recovered": recovered, "oracle_recovered_in_pool_topB": len(true_missed_in_pool[:B])}
        ledger["actual_calls"] += 1
        ledger["actual_tokens"] += prompt_tok + compl_tok
        ledger["actual_cost_usd"] = round(ledger["actual_cost_usd"] + cost, 6)
        rec = {
            "run_id": run_id, "case_id": t.case_id, "repository": t.repository,
            "arm": "B", "role": t.role,
            "prompt_sha256": _sha256_text(prompt),
            "raw_response": raw_text or "",
            "raw_response_sha256": _sha256_text(raw_text or ""),
            "schema_valid": schema_valid, "failure": failure,
            "pool": pool, "ordered_selected": ordered,
            "n_fns_in_pool": len(true_missed_in_pool),
            "prompt_tokens": prompt_tok, "completion_tokens": compl_tok,
            "total_tokens": prompt_tok + compl_tok, "api_cost": cost,
            "latency_seconds": round(elapsed, 3), "recorded_at": _now_iso(),
            "terminal_status": "succeeded" if schema_valid else "failed",
            "per_b": per_b,
        }
        record(run_id, rec)
        if ledger["actual_tokens"] > TOKEN_CEILING or ledger["actual_cost_usd"] > COST_CEILING:
            ledger["stop_reason"] = "ACTUAL_CEILING_BREACH"
            break

    # Reconcile reservations to reflect loaded-from-disk calls too.
    ledger["reserved_calls"] = ledger["actual_calls"]
    ledger["reserved_tokens"] = ledger["actual_tokens"]
    ledger["reserved_cost_usd"] = round(ledger["actual_cost_usd"], 6)
    ledger["wall_seconds"] = round(time.monotonic() - t_load0, 1)
    ledger["budget_respected"] = (
        ledger["actual_calls"] <= MAX_CALLS and ledger["actual_tokens"] <= TOKEN_CEILING
        and ledger["actual_cost_usd"] <= COST_CEILING and ledger["wall_seconds"] <= WALL_CEILING_S
    )
    ledger["resumed_from_disk"] = resumed
    _write_text(LEDGER_JSON, json.dumps(ledger, indent=2))

    result = {"study_id": "bounded-semantic-expansion-pilot",
              "registration": REG_JSON.name, "records": records, "ledger": ledger}
    _write_text(RESULT_JSON, json.dumps(result, indent=2))
    print("calls", ledger["actual_calls"], "tokens", ledger["actual_tokens"],
          "cost", round(ledger["actual_cost_usd"], 4), "wall_s", ledger["wall_seconds"],
          "stop", ledger["stop_reason"], "resumed", resumed)
    print("outputs:", RESULT_JSON, LEDGER_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

