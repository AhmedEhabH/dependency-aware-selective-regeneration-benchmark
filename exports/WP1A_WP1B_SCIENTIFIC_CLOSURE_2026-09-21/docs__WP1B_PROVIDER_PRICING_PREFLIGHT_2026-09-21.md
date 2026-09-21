# WP-1b Provider/Pricing Preflight + Cost Estimate (G6)

**Date:** 2026-09-21
**Status:** PREFLIGHT COMPLETE (zero paid inference). Live provider metadata
fetched at execution time from the OpenRouter public metadata API.

## 1. Live metadata captured (execution time)

Timestamp (UTC): `2026-09-21T02:59:03.138248+00:00`

| Field | Value |
|-------|-------|
| Model ID | `qwen/qwen3-coder` (Qwen3-Coder-480B-A35B-Instruct) |
| Provider / router | OpenRouter → DeepInfra |
| Provider route | `deepinfra/turbo` |
| Quantization | fp4 |
| Input price (prompt) | $0.30 / 1M tokens (per-token 0.0000003) |
| Output price (completion) | $1.00 / 1M tokens (per-token 0.000001) |
| Cache read price | $0.10 / 1M tokens (input_cache_read) |
| Context limit | 262,144 tokens |
| Completion limit (route max) | 65,536 tokens |
| Structured output support | YES (`structured_outputs`, `response_format`) |
| Tool support | YES (`tools`, `tool_choice`) |
| Route status | available (status 0; uptime 1d 97.98%) |

Machine-readable: `artifacts/wp1b_provider_pricing_preflight_2026-09-21.json`.

## 2. Frozen-protocol match

[VERIFIED] The live model, route, and prices match the frozen WP-1a protocol:
- model `qwen/qwen3-coder` == frozen model;
- route `deepinfra/turbo` == frozen route `openrouter:qwen/qwen3-coder@deepinfra/turbo`;
- prompt $0.30/1M and completion $1.00/1M == the frozen pricing verified
  2026-09-20 in `research/wp1a/wp1a_budget_model.json`.

**No model/route/pricing drift detected.** The configured model/route still
matches the frozen experiment, so no STOP per mission section 21.

## 3. Cost estimate (label-free projection from frozen token evidence)

Source: `research/wp1a/wp1a_budget_model.json`
(main_n=50, calibration_n=3, max_calls_per_task=8, completion_cap=512;
projected prompt 1,729,114 tokens, completion 217,088 tokens; base USD
0.735822; safety-factor-1.5 USD 1.103733).

All values are ESTIMATES. `upper-bound` and `actual` are labelled explicitly.

| Component | Estimated (base) USD | Estimated (with 1.5× safety) USD | Notes |
|-----------|----------------------|-----------------------------------|-------|
| Calibration-3 | 0.0417 | 0.0625 | 3/53 of the frozen projection |
| Main-50 | 0.6942 | 1.0413 | 50/53 of the frozen projection |
| Variance substudy (additional 30 executions = 15 tasks × 2 extra) | 0.4165 | 0.6248 | per-task projected (0.735822/53) × 30 |
| Expected total | 1.1524 | **1.7285** | calibration + main + substudy |
| Upper bound (worst completion-cap exposure) | — | 1.4580 | prompt 1.5× = 0.7781 + completion worst-case (all calls at 1024 cap): 679,936 tokens = 0.6799 |

Definitions:
- **estimated** = projection from the frozen budget model's token evidence.
- **upper-bound** = worst reasonable completion-cap exposure assuming the G2
  1024-cap amendment (all control calls hit the cap).
- **actual** = $0.00 — this mission made NO paid scientific call.

## 4. Conservative ceiling

- Calibration + Main-50 combined ceiling (frozen budget model): **$1.10**
  (recommended for Ahmed review; NOT auto-accepted).
- If the variance substudy additional repeats are authorized, a conservative
  ceiling for the whole program (calibration + main + substudy) is ~**$2.00**
  (label-free projection; separate authorization decision required).

## 5. Budget guard (unchanged)

- Cumulative USD guard checked before each paid request.
- Main-run ceiling frozen before main task 1.
- Hitting the ceiling mid-main-run = `BUDGET_ABORT_INVALID_FOR_PRIMARY_COMPARISON`
  (no ordered partial n<50 primary table).

## 6. Falsifiers

- This preflight is wrong if the live OpenRouter metadata changes price/route
  before the WP-1b paid run (re-run the preflight immediately before any paid
  call).
- The cost estimate is wrong if the actual token usage deviates materially
  from the frozen projection (the cumulative USD guard and abort rule are the
  control).
- The "no drift" verdict is wrong if the paid run is routed to a provider
  other than `deepinfra/turbo`.