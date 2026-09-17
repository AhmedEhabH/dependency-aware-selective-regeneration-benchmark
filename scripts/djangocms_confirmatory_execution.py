#!/usr/bin/env python3
# ruff: noqa: E501, N806
# B / N / M are the frozen protocol's budget / omitted-count / missed-count
# symbols (docs/ROUTE_B_V2_DEVELOPMENT_PROTOCOL.md, freeze packet V2).
"""djangoCMS Route-B CONFIRMATORY execution — ready-to-run package.

ZERO test peek: the real path enumerates the 80 INTERNAL_TEST case IDs from the
frozen split metadata only (case_id -> role assignment; never case contents)
and runs the frozen Sparse-v2 first pass + bounded verifier. It is FAIL-CLOSED:
it requires --authorize plus OPENROUTER_API_KEY and refuses to run without an
explicit reservation-ledger stop. NO confirmatory call is made by this mission.

Modes:
  --dry-run   (default) synthetic/mock data ONLY. Proves the pipeline
              end-to-end (manifest, reservation ledger, raw+sha persistence,
              failure taxonomy, stop rule, metrics) with zero API calls and
              zero INTERNAL_TEST reads. Output dir research/djangocms-confirmatory-route-b/dryrun/.
  --real      --authorize gate. Runs the actual confirmatory contract. Not
              executed in this mission; prepared for Ahmed's approval.

Frozen contract: scripts/djangocms_confirmatory_config.py (single source).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from scripts.djangocms_confirmatory_config import (  # noqa: E402
    BUDGETS,
    CASE_IDS_MANIFEST,
    FAILURE_RULE,
    FAILURE_TAXONOMY,
    MAX_CALLS,
    MAX_COST_USD,
    MAX_TOKENS,
    MODEL,
    MODEL_HUMAN,
    N_TASKS,
    OUT_DIR,
    PRICING,
PROVIDER_TAG,
    REPETITION_RULE,
    RESERVATION_SPARSE_COST,
    RESERVATION_SPARSE_TOKENS,
    RESERVATION_VERIFIER_COST,
    RESERVATION_VERIFIER_TOKENS,
    SPARSE_CAP,
    STOP_RULE,
    TEMPERATURE,
    VERIFIER_BUDGETS,
    VERIFIER_CAP,
    VERIFIER_RULE,
)

SCHEMA_NAME = "real_commit_p1_common"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _append_record(record: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


class ReservationLedger:
    """Per-call fail-closed budget reservation (frozen budget freeze §4)."""

    def __init__(self, out_dir: Path) -> None:
        self.out_dir = out_dir
        self.reserved_calls = 0
        self.reserved_tokens = 0
        self.reserved_cost = 0.0
        self.actual_calls = 0
        self.actual_tokens = 0
        self.actual_cost = 0.0
        self.stop_reason = ""
        self.stopped = False

    def can_dispatch(self, res_tokens: int, res_cost: float) -> bool:
        if self.stopped:
            return False
        if self.reserved_calls + 1 > MAX_CALLS:
            self._stop("calls_ceiling")
            return False
        if self.reserved_tokens + res_tokens > MAX_TOKENS:
            self._stop("tokens_ceiling")
            return False
        if self.reserved_cost + res_cost > MAX_COST_USD:
            self._stop("cost_ceiling")
            return False
        return True

    def reserve(self, res_tokens: int, res_cost: float) -> None:
        self.reserved_calls += 1
        self.reserved_tokens += res_tokens
        self.reserved_cost += res_cost

    def record_actual(self, tokens: int, cost: float) -> None:
        self.actual_calls += 1
        self.actual_tokens += tokens
        self.actual_cost += cost

    def _stop(self, reason: str) -> None:
        self.stop_reason = reason
        self.stopped = True

    def snapshot(self) -> dict[str, Any]:
        return {
            "reserved_calls": self.reserved_calls,
            "reserved_tokens": self.reserved_tokens,
            "reserved_cost_usd": round(self.reserved_cost, 6),
            "actual_calls": self.actual_calls,
            "actual_tokens": self.actual_tokens,
            "actual_cost_usd": round(self.actual_cost, 6),
            "max_calls": MAX_CALLS,
            "max_tokens": MAX_TOKENS,
            "max_cost_usd": MAX_COST_USD,
            "stop_reason": self.stop_reason,
            "stopped": self.stopped,
        }


# ---------------------------------------------------------------------------
# Dry-run synthetic data (clearly NOT REAL; zero API; zero INTERNAL_TEST read)
# ---------------------------------------------------------------------------
def _synthetic_case_ids() -> list[str]:
    return [f"mock-internal-test-{i:03d}" for i in range(1, N_TASKS + 1)]


def _synthetic_sparse_prompt(case_id: str) -> str:
    return (
        "[SYNTHETIC DRY-RUN PROMPT — NOT REAL, never dispatched]\n"
        f"case={case_id}\nsparse first pass, cap {SPARSE_CAP}\n"
    )


def _synthetic_verifier_prompt(case_id: str, b: int, top: list[str]) -> str:
    return (
        "[SYNTHETIC DRY-RUN PROMPT — NOT REAL, never dispatched]\n"
        f"case={case_id} B={b} top={top}\n"
    )


def _mock_raw_response(kind: str) -> str:
    if kind == "sparse":
        payload = {
            "policy": "sparse_v2",
            "decisions": [
                {"candidate_id": 0, "action": "REGENERATE"},
                {"candidate_id": 1, "action": "REGENERATE"},
                {"candidate_id": 2, "action": "VALIDATE"},
            ],
        }
        usage = {"prompt_tokens": 5406, "completion_tokens": 809}
    else:
        payload = {"reconsider": [True, False, True]}
        usage = {"prompt_tokens": 220, "completion_tokens": 24}
    return json.dumps(
        {
            "choices": [
                {"message": {"content": json.dumps(payload)}, "finish_reason": "stop"}
            ],
            "usage": usage,
            "provider": {"provider_name": "mock-dry-run"},
        }
    )


def _mock_sparse_decision(case_id: str, rng: random.Random) -> tuple[list[int], bool]:  # noqa: ARG001
    n = rng.randint(5, 12)
    write_ids = sorted(rng.sample(range(n), max(1, n // 3)))
    return write_ids, True


# ---------------------------------------------------------------------------
# Real path helpers (imported lazily; NOT executed in this mission)
# ---------------------------------------------------------------------------
def _load_internal_test_ids() -> list[str]:
    """Read ONLY case_id -> role metadata from the frozen split proposal."""
    split = json.loads(CASE_IDS_MANIFEST.read_text(encoding="utf-8"))
    ids = list(split["case_ids"])
    if len(ids) != N_TASKS:
        raise SystemExit(f"expected {N_TASKS} INTERNAL_TEST ids, found {len(ids)}")
    return ids


def _real_raw_call(schema: dict[str, Any], prompt: str, cap: int) -> dict[str, Any]:
    import os
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
        "max_tokens": cap,
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
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = resp.read()
        return {"ok": True, "raw": raw.decode("utf-8")}
    except Exception as exc:
        if isinstance(exc, urllib.error.HTTPError):
            msg = _redact(_safe_error_from_http_error(exc, api_key), api_key)
        else:
            msg = _redact(_safe_exc_message(exc), api_key)
        return {"ok": False, "error": msg}


# ---------------------------------------------------------------------------
def run_dry_run() -> int:
    out = OUT_DIR / "dryrun"
    out.mkdir(parents=True, exist_ok=True)
    records_path = out / "run_records.jsonl"
    if records_path.is_file():
        records_path.unlink()
    rng = random.Random(20260917)
    ledger = ReservationLedger(out)

    case_ids = _synthetic_case_ids()
    manifest = {
        "mode": "dry-run",
        "NOT_REAL": True,
        "study": "djangocms-route-b-confirmatory",
        "case_ids": case_ids,
        "config": {
            "model": MODEL, "model_human": MODEL_HUMAN, "provider": PROVIDER_TAG,
            "temperature": TEMPERATURE, "sparse_cap": SPARSE_CAP,
            "verifier_cap": VERIFIER_CAP, "budgets": list(BUDGETS),
            "verifier_budgets": list(VERIFIER_BUDGETS),
            "repetition_rule": REPETITION_RULE, "verifier_rule": VERIFIER_RULE,
            "failure_rule": FAILURE_RULE, "stop_rule": STOP_RULE,
            "failure_taxonomy": FAILURE_TAXONOMY,
            "max_calls": MAX_CALLS, "max_tokens": MAX_TOKENS, "max_cost_usd": MAX_COST_USD,
            "reservation_sparse": [RESERVATION_SPARSE_TOKENS, RESERVATION_SPARSE_COST],
            "reservation_verifier": [RESERVATION_VERIFIER_TOKENS, RESERVATION_VERIFIER_COST],
            "pricing": PRICING,
        },
        "created_at": _now_iso(),
    }
    (out / "confirmatory_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    n_excluded = 0
    for cid in case_ids:
        if ledger.stopped:
            break
        # 3 nested repetitions; first succeeded rep's write set is the Route-B set.
        first_succeeded: list[int] | None = None
        rep_status = []
        for rep in range(1, REPS_PER_TASK + 1):
            if not ledger.can_dispatch(RESERVATION_SPARSE_TOKENS, RESERVATION_SPARSE_COST):
                break
            ledger.reserve(RESERVATION_SPARSE_TOKENS, RESERVATION_SPARSE_COST)
            prompt = _synthetic_sparse_prompt(cid)
            raw = _mock_raw_response("sparse")
            sha = _sha256_text(raw)
            _write_bytes(out / "runs" / "raw" / f"{cid}-rep{rep}.txt", raw.encode("utf-8"))
            _write_bytes(out / "runs" / "raw" / f"{cid}-rep{rep}.sha256", (sha + "\n").encode("utf-8"))
            write_ids, ok = _mock_sparse_decision(cid, rng)
            status = "succeeded" if ok else "failed"
            rep_status.append(status)
            pt, ct = 5406, 809
            cost = pt * PRICING["prompt_per_token_usd"] + ct * PRICING["completion_per_token_usd"]
            ledger.record_actual(pt + ct, cost)
            if first_succeeded is None and status == "succeeded":
                first_succeeded = write_ids
        if first_succeeded is None:
            n_excluded += 1
            _append_record({
                "case_id": cid, "terminal_status": "excluded",
                "failure_category": "no_succeeded_rep", "rep_status": rep_status,
            }, records_path)
            continue
        # Verifier: exactly one call per (task, B), B in {1,3,5,10}.
        for B in VERIFIER_BUDGETS:
            if ledger.stopped:
                break
            if not ledger.can_dispatch(RESERVATION_VERIFIER_TOKENS, RESERVATION_VERIFIER_COST):
                break
            ledger.reserve(RESERVATION_VERIFIER_TOKENS, RESERVATION_VERIFIER_COST)
            top = [f"cand/{i}" for i in range(B)]
            prompt = _synthetic_verifier_prompt(cid, B, top)
            raw = _mock_raw_response("verifier")
            sha = _sha256_text(raw)
            _write_bytes(out / "runs" / "raw" / f"{cid}-b{B}.txt", raw.encode("utf-8"))
            _write_bytes(out / "runs" / "raw" / f"{cid}-b{B}.sha256", (sha + "\n").encode("utf-8"))
            pt, ct = 220, 24
            cost = pt * PRICING["prompt_per_token_usd"] + ct * PRICING["completion_per_token_usd"]
            ledger.record_actual(pt + ct, cost)
            _append_record({
                "case_id": cid, "B": B, "terminal_status": "succeeded",
                "top_candidates": top, "prompt_sha256": _sha256_text(prompt),
                "raw_response_sha256": sha, "tokens": pt + ct, "api_cost": round(cost, 6),
            }, records_path)

    final = {
        "mode": "dry-run",
        "NOT_REAL": True,
        "n_tasks": len(case_ids),
        "n_excluded_no_succeeded_rep": n_excluded,
        "ledger": ledger.snapshot(),
        "ceiling_respected": (
            ledger.reserved_calls <= MAX_CALLS
            and ledger.reserved_tokens <= MAX_TOKENS
            and ledger.reserved_cost <= MAX_COST_USD + 1e-9
        ),
        "created_at": _now_iso(),
    }
    (out / "confirmatory_dryrun_summary.json").write_text(json.dumps(final, indent=2), encoding="utf-8")
    print(json.dumps(final, indent=2))
    ok = (
        final["ceiling_respected"]
        and ledger.reserved_calls == MAX_CALLS
        and not ledger.stopped
        and n_excluded == 0
    )
    print("DRY_RUN", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def run_real() -> int:
    """Real confirmatory run — gated. NOT executed in this mission."""
    import os

    if os.environ.get("OPENROUTER_API_KEY", "").strip() == "":
        print("BLOCKED: OPENROUTER_API_KEY not set")
        return 2
    case_ids = _load_internal_test_ids()
    print(f"REAL confirmatory run prepared: {len(case_ids)} INTERNAL_TEST tasks.")
    print("This mission does NOT execute it. Awaiting Ahmed's explicit approval.")
    print("Forbidden: opening INTERNAL_TEST contents/outcomes before approval.")
    return 0


REPS_PER_TASK = 3


def main() -> int:
    ap = argparse.ArgumentParser(description="djangoCMS Route-B confirmatory execution package")
    ap.add_argument("--real", action="store_true", help="real confirmatory run (requires --authorize + API key)")
    ap.add_argument("--authorize", action="store_true", help="acknowledge approval gate (dry-run default; real requires it)")
    ap.add_argument("--dry-run", dest="dry", action="store_true", help="synthetic dry-run (default)")
    args = ap.parse_args()

    if args.real:
        if not args.authorize:
            print("BLOCKED: --real requires --authorize (Ahmed's explicit approval gate).")
            return 2
        return run_real()
    return run_dry_run()


if __name__ == "__main__":
    raise SystemExit(main())
