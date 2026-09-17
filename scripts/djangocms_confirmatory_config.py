#!/usr/bin/env python3
"""djangoCMS Route-B confirmatory execution — FROZEN CONFIG SNAPSHOT.

ZERO test peek: this module contains NO INTERNAL_TEST contents, prompts, gold,
labels, or outcomes. It only codifies the frozen execution contract from:
- reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_FREEZE_PACKET_V2.md
- reports/DJANGOCMS_CONFIRMATORY_API_BUDGET_FREEZE.md

The INTERNAL_TEST case IDs are read from the frozen split metadata at real-run
time (research/transparency/v2_split_proposal.json), which contains only
case_id -> role assignment (metadata), never case contents.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

# --- Frozen scientific contract (freeze packet V2) ---------------------------
N_TASKS = 80
REPS = 3
BUDGETS = (0, 1, 3, 5, 10)
VERIFIER_BUDGETS = (1, 3, 5, 10)  # B=0 -> NO verifier call
MODEL = "qwen/qwen3-coder"
MODEL_HUMAN = "Qwen3-Coder-480B-A35B-Instruct"
PROVIDER_TAG = "deepinfra/turbo"
TEMPERATURE = 0.0
SPARSE_CAP = 16384
VERIFIER_CAP = 512
PRICING = {
    "prompt_per_token_usd": 0.30 / 1e6,
    "completion_per_token_usd": 1.00 / 1e6,
    "source": "frozen DeepInfra-through-OpenRouter pricing (budget freeze 2026-09-17)",
}

# --- Frozen hard ceilings (API budget freeze) --------------------------------
MAX_CALLS = 560                      # 240 sparse + 320 verifier, deterministic
MAX_TOKENS = 2_100_000
MAX_COST_USD = 1.00

# --- Per-call reservation rule (fail-closed) ---------------------------------
# Incremented BEFORE dispatch; the run stops fail-closed if cumulative reserved
# + next reservation would breach a ceiling. No call is dispatched that would
# breach the ceiling (material overshoot impossible by construction).
RESERVATION_SPARSE_TOKENS = 7_877    # p99 observed DEV sparse cell
RESERVATION_SPARSE_COST = 0.00302
RESERVATION_VERIFIER_TOKENS = 400    # B=10-safe
RESERVATION_VERIFIER_COST = 0.00015

# --- Frozen aggregation / semantics (freeze packet V2) -----------------------
# Repetition aggregation: the one write-set used by Route B per task = the
# predicted_write_set of the FIRST SUCCEEDED repetition in record-file order.
# NOT a majority vote, NOT a union.
REPETITION_RULE = "first_succeeded_rep"
# Failed reps are skipped (NOT retried); a task with no succeeded rep is
# EXCLUDED from the Route-B analysis (recorded, not a zero-write-set substitute).
FAILED_REP_RULE = "skip_recorded"
NO_SUCCEEDED_REP_TASK_RULE = "excluded_recorded"
# Verifier: exactly 1 call per (task, B), independent across B (each inspects
# its own top-B candidate set); B=0 -> no call.
VERIFIER_RULE = "one_call_per_task_b_independent"
# Failure semantics: a schema-invalid / truncated / transport-failed call is
# recorded as FAILED (fn added, no partial credit), NEVER retried; no
# result-dependent reruns.
FAILURE_RULE = "recorded_failed_no_retry_no_rerun"

# --- Failure taxonomy (exact) -------------------------------------------------
FAILURE_TAXONOMY = [
    "transport_failed",      # HTTP / network / timeout before a response
    "http_error",            # provider returned an error status
    "content_parse_failed",  # response content not valid JSON
    "schema_invalid",        # JSON decodes but fails the frozen schema
    "truncated",             # finish_reason == "length"
    "usage_unknown",         # usage counters missing
    "budget_stop",           # fail-closed ceiling breach (no dispatch)
    "no_succeeded_rep",      # task excluded from Route-B analysis
]

# --- Stop rule (frozen) -------------------------------------------------------
# 1. Fail-closed: stop BEFORE dispatching any call whose reservation would
#    breach MAX_CALLS / MAX_TOKENS / MAX_COST_USD.
# 2. The actual cumulative usage must also never exceed the hard ceilings
#    (any overshoot is reported fail-closed, never silently absorbed).
# 3. Confirmatory gate mirrors the DEV progression gate: positive direction in
#    the majority of predeclared folds; materially above analytic Random over a
#    nontrivial portion of the B curve; not driven solely by size artifacts;
#    leakage-free; practically meaningful recovery. If the gate fails, the
#    negative result is frozen and reported — no method change based on
#    confirmatory outcomes in the same session.
STOP_RULE = "fail_closed_reservation_and_actual_no_rerun"

# --- Paths --------------------------------------------------------------------
SPLIT = PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
CASE_IDS_MANIFEST = PROJECT_DIR / "research" / "transparency" / "djangocms_internal_test_case_ids.json"
DATASET_DIR = PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
OUT_DIR = PROJECT_DIR / "research" / "djangocms-confirmatory-route-b"
RUN_RECORDS = OUT_DIR / "run_records.jsonl"
RAW_DIR = OUT_DIR / "runs" / "raw"
METRICS_JSON = OUT_DIR / "confirmatory_metrics.json"
METRICS_MD = PROJECT_DIR / "reports" / "DJANGOCMS_CONFIRMATORY_ROUTE_B_RESULT.md"
