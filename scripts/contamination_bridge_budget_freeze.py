#!/usr/bin/env python3
# ruff: noqa: E501
"""Writes the Qwen3-embedding bridge budget-freeze report + JSON (NOT EXECUTED)."""
from __future__ import annotations

import json
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_REPORTS = _PROJECT_DIR / "reports"
_TOKEN = json.loads((_PROJECT_DIR / "research" / "contamination-bridge" / "token_estimate.json").read_text(encoding="utf-8"))

BATCH = 64
UNITS = _TOKEN["n_units"]
QUERIES = _TOKEN["n_queries"]
UNIT_TOK = _TOKEN["unit_tokens_total"]
QUERY_TOK = _TOKEN["query_tokens_total"]
TOTAL_TOK = _TOKEN["combined_tokens_total"]
UNIT_REQ = -(-UNITS // BATCH)
QUERY_REQ = -(-QUERIES // BATCH)
REQS = UNIT_REQ + QUERY_REQ

# Sensitivity of USD cost to per-1M-token price (informational; the model is
# not offered so no real price exists).
per_m = {"p05": 0.05, "p10": 0.10, "p15": 0.15, "p20": 0.20, "p25": 0.25}
cost_rows = {k: round(TOTAL_TOK / 1e6 * v, 4) for k, v in per_m.items()}

data = {
    "study_id": "qwen3-embed-contamination-bridge",
    "status": "FROZEN_BUT_NOT_EXECUTED",
    "stop_reason": "model_unavailable_on_openrouter_and_cost_ceiling_infeasible",
    "label": "INFORMATIONAL budget freeze for the DEVELOPMENT-only contamination bridge",
    "frozen_ceilings": {
        "max_scientific_cost_usd": 0.50,
        "max_wall_minutes": 120,
        "max_transport_retries": 3,
        "no_fallback": True,
        "no_result_based_retry": True,
        "batch_size": BATCH,
    },
    "development_population": {"djangocms": 174, "saleor": 149},
    "inputs": {
        "n_unique_code_units": UNITS,
        "n_query_texts": QUERIES,
        "unit_tokens_total": UNIT_TOK,
        "query_tokens_total": QUERY_TOK,
        "combined_tokens_total": TOTAL_TOK,
        "unit_tokens_p50": _TOKEN["unit_tokens_p50"],
        "unit_tokens_p90": _TOKEN["unit_tokens_p90"],
        "unit_tokens_p99": _TOKEN["unit_tokens_p99"],
        "unit_tokens_max": _TOKEN["unit_tokens_max"],
        "tokenizer": _TOKEN["tokenizer"],
    },
    "requests": {
        "unit_requests_at_batch64": UNIT_REQ,
        "query_requests_at_batch64": QUERY_REQ,
        "total_requests": REQS,
    },
    "cost_sensitivity_usd_per_1m_tokens": cost_rows,
    "cost_assessment": (
        "Even at an optimistic $0.05 per 1M tokens the full-corpus run would "
        f"cost ~${cost_rows['p05']:.2f} (> $0.50 ceiling); at typical embedding "
        f"prices ($0.10-$0.25/M) ${cost_rows['p10']:.2f}-${cost_rows['p25']:.2f}. "
        "The model is not offered by OpenRouter, so no real price exists; the "
        "$0.50 ceiling therefore cannot be met for the REQUIRED full population, "
        "and subsampling is forbidden without documented technical/cost "
        "limitation + new authorization."
    ),
    "wall_time_minutes": "UNKNOWN (endpoint unavailable)",
    "max_input_length": {
        "max_unit_tokens": _TOKEN["unit_tokens_max"],
        "model_documented_max_tokens": 32768,
        "would_require_truncation": _TOKEN["unit_tokens_max"] > 32768,
        "note": "re-verify the model's documented max input length at run time if it becomes available",
    },
    "retry_failure_policy": {
        "permitted": ["timeout", "network", "transient 429/5xx"],
        "max_retries": 3,
        "forbidden": ["result-based retry", "provider/model fallback",
                     "batch-size change based on results", "dropping unfavorable tasks"],
    },
    "token_ceiling_frozen": 25_000_000,
    "sealed_data_guard": True,
}

OUT_JSON = _REPORTS / "qwen3_embed_bridge_budget_freeze.json"
OUT_MD = _REPORTS / "QWEN3_EMBED_CONTAMINATION_BRIDGE_BUDGET_FREEZE.md"
OUT_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")

md = [
    "# Qwen3-Embedding Contamination Bridge — Budget Freeze (FROZEN, NOT EXECUTED)",
    "",
    "**Date:** 2026-09-19  **Tier:** T3  **Status:** FROZEN BEFORE CALL 1 — **NOT "
    "EXECUTED** (model unavailable on OpenRouter; cost ceiling infeasible for the "
    "required full population).",
    "",
    "**Hard safety ceilings (frozen):** total OpenRouter scientific cost **<= $0.50**; "
    "wall <= 120 min; max transport retries 3 (timeout/network/transient 5xx only); "
    "no fallback; no result-based retry; no batch-size change based on results; "
    "sealed-data guard ON.",
    "",
    "## 1. DEVELOPMENT inputs (measured with the Qwen3-Embedding-8B tokenizer)",
    "",
    "| Quantity | Value |",
    "|---|---:|",
    f"| Unique DEVELOPMENT code units | {UNITS} |",
    f"| Query texts (174 djangoCMS + 149 Saleor) | {QUERIES} |",
    f"| Unit input tokens (total) | {UNIT_TOK:,} |",
    f"| Unit tokens p50 / p90 / p99 / max | {_TOKEN['unit_tokens_p50']} / {_TOKEN['unit_tokens_p90']} / {_TOKEN['unit_tokens_p99']} / {_TOKEN['unit_tokens_max']} |",
    f"| Query input tokens (total; mean {_TOKEN['query_tokens_mean']}/query) | {QUERY_TOK:,} |",
    f"| Combined input tokens | {TOTAL_TOK:,} |",
    "",
    "## 2. Requests under legal batching (batch = 64)",
    "",
    f"- Unit requests: ceil({UNITS}/64) = **{UNIT_REQ}**",
    f"- Query requests: ceil({QUERIES}/64) = **{QUERY_REQ}**",
    f"- Total embedding requests: **{REQS}**",
    "",
    "## 3. USD cost assessment (informational)",
    "",
    "The model is NOT offered by OpenRouter (verified 2026-09-19), so no real "
    "price exists. A sensitivity analysis over hypothetical per-1M-token prices "
    "shows the REQUIRED full-corpus run cannot fit the $0.50 ceiling:",
    "",
    "| Price per 1M tokens | Projected full-run cost | Within $0.50? |",
    "|---:|---:|:---:|",
    "| $0.05 | " + f"${cost_rows['p05']:.2f}" + " | no |",
    "| $0.10 | " + f"${cost_rows['p10']:.2f}" + " | no |",
    "| $0.15 | " + f"${cost_rows['p15']:.2f}" + " | no |",
    "| $0.20 | " + f"${cost_rows['p20']:.2f}" + " | no |",
    "| $0.25 | " + f"${cost_rows['p25']:.2f}" + " | no |",
    "",
    "**Conclusion:** even at an optimistic $0.05/1M tokens the full-corpus run "
    "would cost ~" + f"${cost_rows['p05']:.2f}" + ", above the frozen $0.50 "
    "ceiling. Subsampling the DEVELOPMENT population is forbidden without a "
    "documented technical/cost limitation AND new authorization. The $0.50 "
    "ceiling therefore cannot be satisfied for the REQUIRED full population, "
    "independently of the model-availability blocker.",
    "",
    "## 4. Max input length",
    "",
    f"- Longest unit: {_TOKEN['unit_tokens_max']} tokens; model documented max: 32,768 "
    "(re-verify at run time if the model becomes available) → no truncation "
    "required at the documented max.",
    "",
    "## 5. Retry / failure policy (frozen)",
    "",
    "- Permitted: deterministic transport retry for timeout / network / transient "
    "429/5xx, max 3 retries.",
    "- Forbidden: result-based retry, provider/model fallback, batch-size change "
    "based on results, dropping unfavorable tasks.",
    "",
    "## 6. STOP conditions actually triggered (2026-09-19)",
    "",
    "1. **Model unavailable**: `qwen/qwen3-embedding-8b` is not in the OpenRouter "
    "catalog (0 embedding models).",
    "2. **Cost ceiling infeasible**: the required full-corpus run is projected "
    "above $0.50 even at optimistic prices; no real price exists to freeze.",
    "",
    "Per the frozen stop policy, **NO scientific call was made** (0 calls, $0.00). "
    "Machine-readable: `reports/qwen3_embed_bridge_budget_freeze.json`.",
]

OUT_MD.write_text("\n".join(md), encoding="utf-8")
print("wrote", OUT_JSON, OUT_MD)
