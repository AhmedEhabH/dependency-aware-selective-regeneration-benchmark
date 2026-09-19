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

# ---- live pricing (2026-09-19; pinned provider DeepInfra @ $0.01/M) ----
PINNED_PROVIDER = "DeepInfra"
PRICE_PER_1M = 0.01
EXPECTED_COST = round(TOTAL_TOK / 1e6 * PRICE_PER_1M, 4)

data = {
    "study_id": "qwen3-embed-contamination-bridge",
    "status": "FROZEN_WITH_LIVE_PRICING; TECHNICAL PROBES EXECUTED; FULL RUN STOPPED (DETERMINISM)",
    "label": "Budget freeze for the DEVELOPMENT-only contamination bridge (corrected availability probe; live provider pricing; stopped before full run on determinism)",
    "frozen_ceilings": {
        "max_scientific_cost_usd": 0.50,
        "max_wall_minutes": 180,
        "max_transport_retries": 3,
        "no_fallback": True,
        "no_result_based_retry": True,
        "batch_size": BATCH,
    },
    "provider_pin": {
        "model": "qwen/qwen3-embedding-8b",
        "provider": PINNED_PROVIDER,
        "price_per_1m_tokens_usd": PRICE_PER_1M,
        "context_length": 32768,
        "fallback_disabled": True,
        "providers_at_0_01_per_m": ["DeepInfra", "Nebius"],
        "provider_selection_basis": "availability, documented pricing, API compatibility, reproducibility (frozen before target-aware results)",
    },
    "cost_arithmetic": {
        "total_estimated_tokens": TOTAL_TOK,
        "price_per_1m_tokens_usd": PRICE_PER_1M,
        "expected_cost_usd": EXPECTED_COST,
        "formula": "total_estimated_tokens / 1_000_000 * price_per_1m_tokens_usd",
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
        "LIVE pinned-provider price (DeepInfra) is $0.01 per 1M tokens; expected "
        f"full-run input cost = {TOTAL_TOK} / 1,000,000 x $0.01 = ${EXPECTED_COST:.4f}, "
        "well inside the $0.50 hard ceiling. The earlier $1.09-$5.47 projection used "
        "stale assumed prices and is superseded."
    ),
    "wall_time_minutes": "180 (documented before call 1; ~783 batched requests x provider latency)",
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
    "# Qwen3-Embedding Contamination Bridge — Budget Freeze (v2, live pricing)",
    "",
    "**Date:** 2026-09-19  **Tier:** T3  **Status:** FROZEN BEFORE CALL 1 with "
    "corrected availability probe + live provider pricing. Technical probes "
    "EXECUTED; the FULL scientific run was STOPPED on material embedding "
    "nondeterminism (see `reports/QWEN3_EMBED_DEVELOPMENT_REPORT_2026-09-19.md`).",
    "",
    "**Hard safety ceilings (frozen):** total OpenRouter scientific cost **<= $0.50**; "
    "wall <= 180 min (documented before call 1: ~783 batched requests x provider "
    "latency); max transport retries 3 (timeout/network/transient 5xx only); "
    "no fallback; no result-based retry; no batch-size change based on results; "
    "sealed-data guard ON.",
    "",
    "**Provider pin (frozen before call 1):** **DeepInfra** for "
    "`qwen/qwen3-embedding-8b` at the documented **$0.01 / 1M tokens** (context "
    "32,768; 100% 5-min uptime); routing pinned and fallbacks disabled per "
    "request. Nebius also serves $0.01/M (recorded alternative).",
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
    "## 3. Expected cost (explicit arithmetic, live pinned-provider price)",
    "",
    "`expected_cost = total_estimated_tokens / 1_000_000 * price_per_1m`",
    "",
    f"`= {TOTAL_TOK} / 1_000_000 * $0.01 = ${EXPECTED_COST:.4f}`",
    "",
    f"**Expected full-run input cost: ${EXPECTED_COST:.4f}** (hard ceiling $0.50). "
    "The earlier $1.09-$5.47 projection used stale assumed prices and is "
    "superseded by the live $0.01/M provider price.",
    "",
    "## 4. Max input length",
    "",
    f"- Longest unit: {_TOKEN['unit_tokens_max']} tokens; DeepInfra context "
    f"32,768 → no truncation required at the documented max.",
    "",
    "## 5. Retry / failure policy (frozen)",
    "",
    "- Permitted: deterministic transport retry for timeout / network / transient "
    "429/5xx, max 3 retries.",
    "- Forbidden: result-based retry, provider/model fallback, batch-size change "
    "based on results, dropping unfavorable tasks.",
    "",
    "## 6. Availability correction (2026-09-19)",
    "",
    "The dedicated embeddings catalog `GET /api/v1/embeddings/models` lists 33 "
    "embedding models including `qwen/qwen3-embedding-8b` (context 32,768). The "
    "prior probe used the GENERATION catalog (0 embedding models) and was "
    "defective (P72: QWEN3_EMBED_AVAILABILITY_PROBE_DEFECT_CONFIRMED). The bridge "
    "therefore RESUMES under the frozen protocol.",
    "",
    "Machine-readable: `reports/qwen3_embed_bridge_budget_freeze.json`.",
]

OUT_MD.write_text("\n".join(md), encoding="utf-8")
print("wrote", OUT_JSON, OUT_MD)
