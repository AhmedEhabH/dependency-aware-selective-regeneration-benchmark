#!/usr/bin/env python3
# ruff: noqa: E501, N806
# B and K are the frozen protocol's budget/inspection symbols
# (docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md).
"""PRECISION-SAFE ACCEPTANCE PILOT — RANK → VERIFY → VARIABLE ACCEPT (AUTHORIZED 2026-09-18).

Executes the frozen protocol on a fresh disjoint DEVELOPMENT sample
(seed 20260919; the 60 Stage-4 case_ids are excluded):

  Arm A — frozen Route-B verifier (baseline): 1 call per (task, B), B in
          {1,3,5,10} -> 4 calls/task; top-B = frozen composite
          (BM25 + graph-neighbor). REUSES the EXACT Stage-4 Arm-A verifier
          prompt + schema (scripts/bounded_semantic_expansion_pilot.py).
  Arm B — RANK → VERIFY → VARIABLE ACCEPT (candidate): stage 1 = one bounded
          semantic-ranking call over the deterministic expanded pool
          (Route-B top-10 UNION reverse-1hop consumers, dedupe, pre-order desc
          bm25 then asc path, hard cap C=80), candidate-ID enum schema;
          stage 2 = one strict verification call over the top-K inspection set
          (K=10), fixed-length boolean vector. Accepted additions = the
          verifier-approved subset ordered by semantic rank (VARIABLE 0..K).
  Arm C — Analytic Random (hypergeometric expectation) + Oracle ranking
          references (deterministic, no calls).

Frozen model/route: qwen3-coder (Qwen3-Coder-480B-A35B-Instruct) via OpenRouter,
deepinfra/turbo, fallback OFF, temp 0, completion cap 512. Strict JSON schema
(candidate-ID enum + uniqueness; fixed-length boolean vector). Fail-closed with
NO partial credit: any schema-invalid call contributes zero accepted additions
for its task; recorded, never retried. No result-based retries; no fallback
provider; no prompt tuning.

Budget (frozen, reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md):
<=400 calls, <=300,000 tokens, <=USD 0.15, <=60 min wall; cumulative
reservation ledger (Arm A 300 tok / $0.00010; Arm B rank 1500 tok / $0.00060;
Arm B verify 400 tok / $0.00015) stops BEFORE any dispatch that would breach a
ceiling.

Resume: a run whose <run_id>.json already exists under runs/ is LOADED from disk
(not re-dispatched), so a harness restart never re-spends.

Outputs:
- research/precision-safe-acceptance-pilot/pilot_registration_freeze.json (BEFORE calls)
- research/precision-safe-acceptance-pilot/pilot_results.json
- research/precision-safe-acceptance-pilot/ledger.json
- research/precision-safe-acceptance-pilot/runs/<run_id>.json + raw/<run_id>.txt + .sha256
"""
from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.recall.data import load_dev_tasks  # noqa: E402
from benchmark.recall.rankers import rank_composite  # noqa: E402
from scripts.bounded_semantic_expansion_pilot import (  # noqa: E402
    _raw_openrouter_call,
    _sha256_text,
    _write_text,
    arm_a_schema,
    build_arm_a_prompt,
    stratified_sample,
)

OUT_DIR = _PROJECT_DIR / "research" / "precision-safe-acceptance-pilot"
RUNS_DIR = OUT_DIR / "runs"
RAW_DIR = RUNS_DIR / "raw"
REG_JSON = OUT_DIR / "pilot_registration_freeze.json"
RESULT_JSON = OUT_DIR / "pilot_results.json"
LEDGER_JSON = OUT_DIR / "ledger.json"

STAGE4_REG = _PROJECT_DIR / "research" / "bounded-semantic-expansion" / "pilot_registration_freeze.json"

SEED = 20260919
MAX_TASKS_PER_REPO = 30
BUDGETS = (1, 3, 5, 10)
POOL_CAP = 80
K_INSPECT = 10
B_MAX_ROUTE_B = 10
MODEL = "qwen/qwen3-coder"
PROVIDER_TAG = "deepinfra/turbo"
CAP = 512
PRICING = {"prompt_per_token_usd": 0.30 / 1e6, "completion_per_token_usd": 1.00 / 1e6}
MAX_CALLS = 400
TOKEN_CEILING = 300_000
COST_CEILING = 0.15
WALL_CEILING_S = 60 * 60
RESERVE_A = {"tokens": 300, "cost": 0.00010}
RESERVE_RANK = {"tokens": 1500, "cost": 0.00060}
RESERVE_VERIFY = {"tokens": 400, "cost": 0.00015}


def _fn_paths(t) -> set[str]:
    return {c["path"] for c in t.candidates if c["is_missed_positive"]}


def _consumers(t) -> list[str]:
    return sorted(c["path"] for c in t.candidates if c["consumer"])


def build_pool(t, cap: int = POOL_CAP) -> list[str]:
    """Frozen pool: Route-B composite top-10 UNION reverse-1hop consumers,
    dedupe, pre-order desc bm25 then asc path, hard cap `cap`."""
    base = list(rank_composite(t))[:B_MAX_ROUTE_B]
    union: set[str] = set(base) | set(_consumers(t))
    cand_map = {c["path"]: c for c in t.candidates}
    ordered = sorted(union, key=lambda p: (-float(cand_map[p]["bm25"]), p))
    return ordered[:cap]


def pool_ids(pool: list[str]) -> dict[str, str]:
    return {p: f"C{i:02d}" for i, p in enumerate(pool, start=1)}


def build_rank_prompt(intent: str, write_set: list[str], pool: list[str], id_map: dict[str, str],
                      universe: int, cand_map: dict[str, dict]) -> str:
    lines = "\n".join(
        f"- {id_map[p]}: {p} | {cand_map[p].get('module', '')}" for p in pool
    )
    ws_block = "\n".join(f"- {p}" for p in write_set[:20]) or "- (none)"
    return (
        "You are an impact-verification assistant for a software repository.\n"
        "A first-pass impact plan selected a set of files to change. We now\n"
        "reconsider a bounded pre-filtered POOL of candidate files the first\n"
        "pass DID NOT select.\n"
        f"\nChange intent:\n{intent}\n"
        f"\nFirst-pass selected files (write set):\n{ws_block}\n"
        f"\nCandidate pool to reconsider (candidate_id: path | module/class hint):\n{lines}\n"
        f"\nCandidate universe size: {universe}\n"
        "\nRank the pool candidates that are plausibly affected by the stated\n"
        "change, MOST plausibly affected FIRST. Only include candidates you\n"
        "genuinely believe are plausibly affected (typically a small subset).\n"
        "Reference candidates ONLY by their candidate_id. Keep each reason to\n"
        "one short phrase.\n"
        'Answer ONLY a JSON object: {"ranked": [{"candidate_id": "C03", '
        '"reason": "<short>"}, ...]}.\n'
    )


def build_verify_prompt(intent: str, write_set: list[str], inspection: list[tuple[str, str]],
                        universe: int) -> str:
    lines = "\n".join(f"- {cid}: {path}" for cid, path in inspection)
    ws_block = "\n".join(f"- {p}" for p in write_set[:20]) or "- (none)"
    return (
        "You are a conservative impact-approval assistant for a software\n"
        "repository. A semantic ranker has proposed a small inspection set of\n"
        "candidate files for a stated change. Your job is to approve a file\n"
        "ONLY if it is DIRECTLY implicated by the change and should be added\n"
        "to the change set. Be conservative: leave a file unapproved unless\n"
        "you are genuinely confident it must change.\n"
        f"\nChange intent:\n{intent}\n"
        f"\nFirst-pass selected files (write set):\n{ws_block}\n"
        f"\nInspection set (candidate_id: path):\n{lines}\n"
        f"\nCandidate universe size: {universe}\n"
        "\nReturn exactly one boolean per candidate in the SAME order as the\n"
        "inspection set (true = approve/add to the change set; false = leave\n"
        "it alone).\n"
        'Answer ONLY a JSON object: {"approve": [true, false, ...]}.\n'
    )


def rank_schema(ids: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "ranked": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "candidate_id": {"type": "string", "enum": ids},
                        "reason": {"type": "string"},
                    },
                    "required": ["candidate_id", "reason"],
                    "additionalProperties": False,
                },
                "maxItems": len(ids),
            }
        },
        "required": ["ranked"],
        "additionalProperties": False,
    }


def verify_schema(n: int) -> dict:
    return {
        "type": "object",
        "properties": {
            "approve": {
                "type": "array",
                "items": {"type": "boolean"},
                "minItems": n,
                "maxItems": n,
            }
        },
        "required": ["approve"],
        "additionalProperties": False,
    }


def _parse_usage_and_content(raw_text: str) -> tuple[dict, str]:
    parsed = json.loads(raw_text)
    content = (parsed.get("choices") or [{}])[0].get("message", {}).get("content", "")
    usage = parsed.get("usage") or {}
    return usage, content


def _content_json(rec: dict) -> dict | None:
    """Extract the assistant content JSON from a record's raw_response."""
    raw = rec.get("raw_response") or ""
    if not raw:
        return None
    try:
        _, content = _parse_usage_and_content(raw)
        return json.loads(content)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def _apply_parsed(rec: dict) -> dict:
    if "parsed_content" not in rec:
        rec["parsed_content"] = _content_json(rec)
    return rec


def main() -> int:
    t_load0 = time.monotonic()
    stage4_reg = json.loads(STAGE4_REG.read_text(encoding="utf-8"))
    stage4_ids = {s["case_id"] for s in stage4_reg["sample"]}
    tasks = load_dev_tasks()
    dc = [t for t in tasks if t.repository == "djangocms" and t.case_id not in stage4_ids]
    sc = [t for t in tasks if t.repository == "saleor" and t.case_id not in stage4_ids]
    sample = stratified_sample(dc, MAX_TASKS_PER_REPO) + stratified_sample(sc, MAX_TASKS_PER_REPO)

    registration = {
        "study_id": "precision-safe-acceptance-pilot",
        "authorization": "2026-09-18 user authorization (<=400 calls / <=300,000 tokens / <=$0.15 / <=60 min; frozen protocol docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md)",
        "model": MODEL,
        "provider": PROVIDER_TAG,
        "temperature": 0.0,
        "completion_cap": CAP,
        "pool_cap": POOL_CAP,
        "inspection_k": K_INSPECT,
        "budgets": list(BUDGETS),
        "seed": SEED,
        "excluded_stage4_case_ids": sorted(stage4_ids),
        "arms": {
            "A": "frozen Route-B verifier baseline, 4 calls/task (B in {1,3,5,10}), frozen composite top-B (exact Stage-4 Arm-A prompt/schema)",
            "B": "RANK -> VERIFY -> VARIABLE ACCEPT, 2 calls/task (1 semantic rank over pool cap 80; 1 strict verify over top-K=10); accepted = verifier-approved subset ordered by semantic rank (0..K)",
            "C": "analytic Random + Oracle ranking references (no calls)",
        },
        "ceilings": {"calls": MAX_CALLS, "tokens": TOKEN_CEILING, "cost_usd": COST_CEILING, "wall_seconds": WALL_CEILING_S},
        "reservations": {"arm_a": RESERVE_A, "arm_b_rank": RESERVE_RANK, "arm_b_verify": RESERVE_VERIFY},
        "sample": [],
    }
    for t in sample:
        pool = build_pool(t, POOL_CAP)
        id_map = pool_ids(pool)
        cand_map = {c["path"]: c for c in t.candidates}
        registration["sample"].append({
            "case_id": t.case_id, "repository": t.repository, "role": t.role,
            "year": t.year, "universe_size": t.universe_size, "omitted_size": t.omitted_size,
            "n_missed": t.n_missed, "pool_size": len(pool), "pool": pool,
            "pool_id_map": id_map,
            "arm_a_tops": {str(B): list(rank_composite(t))[: min(B, t.omitted_size)] for B in BUDGETS},
            "intent_sha256": _sha256_text(t.intent_text),
        })
    REG_JSON.parent.mkdir(parents=True, exist_ok=True)
    _write_text(REG_JSON, json.dumps(registration, indent=2))
    print(f"[registration frozen] tasks={len(sample)} file={REG_JSON}", flush=True)
    print("  repo counts:", {r: sum(1 for s in registration["sample"] if s["repository"] == r) for r in ("djangocms", "saleor")})
    assert all(s["pool_size"] <= POOL_CAP for s in registration["sample"])

    ledger = {
        "study_id": "precision-safe-acceptance-pilot",
        "reserved_calls": 0, "actual_calls": 0, "reserved_tokens": 0, "actual_tokens": 0,
        "reserved_cost_usd": 0.0, "actual_cost_usd": 0.0, "wall_seconds": 0.0,
        "ceilings": {"calls": MAX_CALLS, "tokens": TOKEN_CEILING, "cost_usd": COST_CEILING, "wall_seconds": WALL_CEILING_S},
        "stop_reason": "",
    }
    # Wall time accumulates across resume sessions so the ledger reports the
    # TOTAL elapsed wall-clock of the pilot (not just the latest session).
    _prev_wall = 0.0
    if LEDGER_JSON.is_file():
        try:
            _prev_wall = float(json.loads(LEDGER_JSON.read_text(encoding="utf-8")).get("wall_seconds", 0.0))
        except Exception:
            _prev_wall = 0.0

    def check_and_reserve(arm: str) -> bool:
        reserve = {"A": RESERVE_A, "RANK": RESERVE_RANK, "VERIFY": RESERVE_VERIFY}[arm]
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
        print(f"[{run_id}] valid={rec['schema_valid']} tok={rec['total_tokens']} cost={rec['api_cost']:.6f} "
              f"stage={rec['stage']} {rec.get('summary','')}", flush=True)

    def load_existing(run_id: str) -> dict | None:
        p = RUNS_DIR / f"{run_id}.json"
        if p.is_file():
            rec = json.loads(p.read_text(encoding="utf-8"))
            rec["_from_disk"] = True
            return rec
        return None

    def dispatch(run_id: str, schema: dict, prompt: str, arm: str, stage: str, t) -> dict | None:
        """Dispatch one call; returns None if the reservation is refused."""
        if not check_and_reserve(arm):
            return None
        t0 = time.monotonic()
        result = _raw_openrouter_call(schema, prompt)
        elapsed = time.monotonic() - t0
        raw_text = result.get("raw") if result.get("ok") else None
        schema_valid = False
        failure = ""
        prompt_tok = compl_tok = 0
        cost = 0.0
        parsed_content = None
        if raw_text:
            try:
                usage, content = _parse_usage_and_content(raw_text)
                prompt_tok = int(usage.get("prompt_tokens") or 0)
                compl_tok = int(usage.get("completion_tokens") or 0)
                cost = round(prompt_tok * PRICING["prompt_per_token_usd"] + compl_tok * PRICING["completion_per_token_usd"], 6)
                parsed_content = json.loads(content)
                schema_valid = True
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                failure = f"content parse: {e}"
        else:
            failure = result.get("error", "transport failed")
        ledger["actual_calls"] += 1
        ledger["actual_tokens"] += prompt_tok + compl_tok
        ledger["actual_cost_usd"] = round(ledger["actual_cost_usd"] + cost, 6)
        rec = {
            "run_id": run_id, "case_id": t.case_id, "repository": t.repository,
            "arm": arm, "stage": stage, "role": t.role,
            "prompt_sha256": _sha256_text(prompt),
            "raw_response": raw_text or "",
            "raw_response_sha256": _sha256_text(raw_text or ""),
            "schema_valid": schema_valid, "failure": failure,
            "parsed_content": parsed_content,
            "prompt_tokens": prompt_tok, "completion_tokens": compl_tok,
            "total_tokens": prompt_tok + compl_tok, "api_cost": cost,
            "latency_seconds": round(elapsed, 3), "recorded_at": datetime.now(UTC).isoformat(),
            "terminal_status": "succeeded" if schema_valid else "failed",
        }
        record(run_id, rec)
        return rec

    def apply_cost(rec: dict) -> None:
        ledger["actual_calls"] += 1
        ledger["actual_tokens"] += rec["total_tokens"]
        ledger["actual_cost_usd"] = round(ledger["actual_cost_usd"] + rec["api_cost"], 6)

    # ---------------- ARM A ----------------
    print("=== ARM A: frozen Route-B verifier (4 calls/task) ===", flush=True)
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
                _apply_parsed(existing)
                record(run_id, existing)
                apply_cost(existing)
                rec = existing
            else:
                rec = dispatch(run_id, schema, prompt, "A", "arm_a_verifier", t)
                if rec is None:
                    break
                if ledger["actual_tokens"] > TOKEN_CEILING or ledger["actual_cost_usd"] > COST_CEILING:
                    ledger["stop_reason"] = "ACTUAL_CEILING_BREACH"
                    break
            # Derive the frozen verifier decision fields from the parsed content.
            decisions = (rec.get("parsed_content") or {}).get("reconsider")
            if isinstance(decisions, list) and len(decisions) == len(top) \
                    and all(isinstance(x, bool) for x in decisions):
                sel = [p for p, d in zip(top, decisions, strict=False) if d]
            else:
                rec["schema_valid"] = False
                rec["failure"] = rec["failure"] or "arm_a reconsider vector mismatch"
                rec["terminal_status"] = "failed"
                sel = []
            true_missed = [p for p in top if p in _fn_paths(t)]
            rec["B"] = B
            rec["top_candidates"] = top
            rec["verifier_selected"] = sel
            rec["true_missed_in_top"] = true_missed
            rec["verifier_recovered"] = [p for p in sel if p in _fn_paths(t)]
            rec["oracle_recovered_in_top"] = len(true_missed)
            _write_text(RUNS_DIR / f"{run_id}.json", json.dumps(rec, indent=2))

    # ---------------- ARM B ----------------
    print("=== ARM B: RANK -> VERIFY -> VARIABLE ACCEPT (2 calls/task) ===", flush=True)
    rank_transport_abort = 0
    for t in sample:
        if ledger["stop_reason"]:
            break
        meta = next(s for s in registration["sample"] if s["case_id"] == t.case_id)
        pool = meta["pool"]
        if not pool:
            continue
        id_map = meta["pool_id_map"]
        cand_map = {c["path"]: c for c in t.candidates}
        ids_by_id = {v: k for k, v in id_map.items()}

        # --- stage 1: semantic rank ---
        rank_run_id = f"armB-rank-{t.case_id}"
        rank_existing = load_existing(rank_run_id)
        if rank_existing is not None:
            _apply_parsed(rank_existing)
            record(rank_run_id, rank_existing)
            apply_cost(rank_existing)
            rank_rec = rank_existing
        else:
            prompt = build_rank_prompt(t.intent_text, sorted(t.write_set), pool, id_map,
                                       t.universe_size, cand_map)
            schema = rank_schema(list(id_map.values()))
            rank_rec = dispatch(rank_run_id, schema, prompt, "RANK", "rank", t)
            if rank_rec is None:
                break
            if "transport failed" in (rank_rec["failure"] or ""):
                rank_transport_abort += 1
                if rank_transport_abort >= 3:
                    ledger["stop_reason"] = "RANK_TRANSPORT_ABORT"
                    break
            if ledger["actual_tokens"] > TOKEN_CEILING or ledger["actual_cost_usd"] > COST_CEILING:
                ledger["stop_reason"] = "ACTUAL_CEILING_BREACH"
                break

        # Parse stage-1 output: ordered candidate_ids (enum + uniqueness enforced).
        ranked_ids: list[str] = []
        rank_failure = ""
        if rank_rec["schema_valid"]:
            try:
                items = (rank_rec.get("parsed_content") or {}).get("ranked") or []
                seen: set[str] = set()
                for it in items:
                    cid = it.get("candidate_id")
                    if isinstance(cid, str) and cid in id_map.values() and cid not in seen:
                        seen.add(cid)
                        ranked_ids.append(cid)
                if len(ranked_ids) != len(items):
                    rank_failure = "rank stage: duplicate or non-enum candidate_id"
                    ranked_ids = []
            except Exception as e:
                rank_failure = f"rank stage parse: {e}"
                ranked_ids = []
        else:
            rank_failure = rank_rec["failure"] or "rank stage failed"

        # --- stage 2: strict verify over the top-K inspection set ---
        inspection_ids = ranked_ids[:K_INSPECT]
        verify_rec: dict | None = None
        verify_run_id = f"armB-verify-{t.case_id}"
        if not inspection_ids:
            # No inspection set -> fail-closed, zero additions, no dependent call.
            verify_rec = {
                "run_id": verify_run_id, "case_id": t.case_id, "repository": t.repository,
                "arm": "VERIFY", "stage": "verify", "role": t.role,
                "prompt_sha256": "", "raw_response": "", "raw_response_sha256": "",
                "schema_valid": False, "failure": f"skipped: no inspection set ({rank_failure or 'empty rank output'})",
                "parsed_content": None,
                "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "api_cost": 0.0,
                "latency_seconds": 0.0, "recorded_at": datetime.now(UTC).isoformat(),
                "terminal_status": "failed", "skipped": True,
            }
            record(verify_run_id, verify_rec)
        else:
            existing_verify = load_existing(verify_run_id)
            inspection = [(cid, ids_by_id[cid]) for cid in inspection_ids]
            if existing_verify is not None:
                _apply_parsed(existing_verify)
                record(verify_run_id, existing_verify)
                apply_cost(existing_verify)
                verify_rec = existing_verify
            else:
                prompt = build_verify_prompt(t.intent_text, sorted(t.write_set), inspection,
                                             t.universe_size)
                schema = verify_schema(len(inspection_ids))
                verify_rec = dispatch(verify_run_id, schema, prompt, "VERIFY", "verify", t)
                if verify_rec is None:
                    break
                if ledger["actual_tokens"] > TOKEN_CEILING or ledger["actual_cost_usd"] > COST_CEILING:
                    ledger["stop_reason"] = "ACTUAL_CEILING_BREACH"
                    break

        # --- accepted additions: approved subset ordered by semantic rank ---
        approved: list[str] = []
        if rank_rec["schema_valid"] and ranked_ids and verify_rec and verify_rec["schema_valid"]:
            try:
                flags = (verify_rec.get("parsed_content") or {}).get("approve")
                if isinstance(flags, list) and len(flags) == len(inspection_ids) \
                        and all(isinstance(x, bool) for x in flags):
                    approved = [ids_by_id[cid] for cid, ok in zip(inspection_ids, flags, strict=True) if ok]
                else:
                    verify_rec["schema_valid"] = False
                    verify_rec["failure"] = "verify stage: boolean-vector length/type mismatch"
                    verify_rec["terminal_status"] = "failed"
            except Exception as e:
                verify_rec["schema_valid"] = False
                verify_rec["failure"] = f"verify stage parse: {e}"
                verify_rec["terminal_status"] = "failed"
        fn_set = _fn_paths(t)
        per_b = {}
        for B in BUDGETS:
            add = approved[:B]
            recovered = [p for p in add if p in fn_set]
            per_b[str(B)] = {"additions": add, "recovered": recovered,
                             "oracle_recovered_in_pool_topB": len([p for p in fn_set if p in set(pool)][:B])}
        summary = f"ranked={len(ranked_ids)} approved={len(approved)}"
        for rec in (rank_rec, verify_rec):
            if rec is None:
                continue
            rec["per_b"] = per_b
            rec["approved_sorted"] = approved
            rec["summary"] = summary
            _write_text(RUNS_DIR / f"{rec['run_id']}.json", json.dumps(rec, indent=2))

    # Reconcile reservations to reflect loaded-from-disk calls too.
    ledger["reserved_calls"] = ledger["actual_calls"]
    ledger["reserved_tokens"] = ledger["actual_tokens"]
    ledger["reserved_cost_usd"] = round(ledger["actual_cost_usd"], 6)
    ledger["wall_seconds"] = round(_prev_wall + (time.monotonic() - t_load0), 1)
    ledger["budget_respected"] = (
        ledger["actual_calls"] <= MAX_CALLS and ledger["actual_tokens"] <= TOKEN_CEILING
        and ledger["actual_cost_usd"] <= COST_CEILING and ledger["wall_seconds"] <= WALL_CEILING_S
    )
    ledger["resumed_from_disk"] = resumed
    _write_text(LEDGER_JSON, json.dumps(ledger, indent=2))

    result = {"study_id": "precision-safe-acceptance-pilot",
              "registration": REG_JSON.name, "records": records, "ledger": ledger}
    _write_text(RESULT_JSON, json.dumps(result, indent=2))
    print("calls", ledger["actual_calls"], "tokens", ledger["actual_tokens"],
          "cost", round(ledger["actual_cost_usd"], 4), "wall_s", ledger["wall_seconds"],
          "stop", ledger["stop_reason"], "resumed", resumed)
    print("outputs:", RESULT_JSON, LEDGER_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
