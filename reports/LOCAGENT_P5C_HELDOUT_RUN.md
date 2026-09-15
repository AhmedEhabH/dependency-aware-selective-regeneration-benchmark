# P5-C — LocAgent HELD_OUT shared-protocol run (in progress)

**Date:** 2026-09-15
**Host:** WSL2 Ubuntu-24.04
**Classification:** SYSTEM-LEVEL SHARED-PROTOCOL COMPARISON (P1 temperature 0
vs LocAgent upstream temperature 1) — not a pure algorithm ablation.

## Frozen P5-C protocol (before call #1)

- upstream SHA: `4935b557326c154bad8e8dcf3747cc8d32d1f387`
- queue-guard compatibility patch: `c2fa932f…` (process-failure handling only)
- compatibility wrapper: `locagent-compat-launch-layer-1.2`
- model/provider: `openrouter/qwen/qwen3-coder` via OpenRouter→DeepInfra
  (`deepinfra/turbo`), fallback OFF
- temperature: 1 (upstream hard-coded), num_samples=1, max_attempt_num=1
- timeout: 900 s, ranking: MRR
- dataset: 10 P1 HELD_OUT_TEST tasks (leakage-free, patch="")
- file-set conversion: exact emitted merged file set (frozen)
- cost: real token usage × frozen P1 pricing (`$0.30/$1.00 per 1M`), computed
  by the common evaluator; upstream `calc_cost` diagnostic-only
- model-call count: from the per-call usage ledger (authoritative)
- credential: ONE dedicated Benchmark key (parent env `OPENROUTER_API_KEY`,
  `BENCHMARK_KEY_SOURCE=SEPARATE_PARENT_ENV`), bridged via WSLENV, no key
  switching during P5-C

## Pre-launch verification (2026-09-15)

- `OPENROUTER_API_KEY=SET` in parent env; `BENCHMARK_KEY_SOURCE=SEPARATE_PARENT_ENV`
- non-held-out auth/capability probe PASS: expected Qwen/OpenRouter route,
  `finish_reason=stop`, usage metadata present
- OpenRouter daily credit: limit $7.00, used $4.36, remaining $2.64
- P5-C estimated budget: ≤ $1.50 (frozen ceiling, same as P1)

*This report will be updated with the 10/10 HELD_OUT metrics, the shared
Full/Sparse/LocAgent comparison, paired bootstrap, and audit results.*