# P5-C — LocAgent HELD_OUT shared-protocol run (COMPLETE 10/10)

**Date:** 2026-09-15
**Host:** WSL2 Ubuntu-24.04
**Classification:** SYSTEM-LEVEL SHARED-PROTOCOL COMPARISON (P1 temperature 0
vs LocAgent upstream temperature 1) — not a pure algorithm ablation.

## Frozen P5-C protocol (as executed)

- upstream SHA: `4935b557326c154bad8e8dcf3747cc8d32d1f387`
- queue-guard compatibility patch: `37756801ddfeb864ec021c8e6cb87f8bf36883f79749bace63cd3122299e1061`
  (process-failure + transport-error handling only; includes bounded
  BadRequestError handler that fail-closes within the frozen attempt policy)
- compatibility wrapper: `locagent-compat-launch-layer-1.2`
- model/provider: `openrouter/qwen/qwen3-coder` — **OpenRouter-routed** Qwen3-Coder.
  NOTE (corrected 2026-09-15): the per-call ledger records `provider="openrouter"`
  (the gateway), not the resolved backend; raw logs show BOTH DeepInfra and
  Venice upstream errors, so an unqualified "pinned DeepInfra" claim per call
  is NOT supported. Fallback OFF.
- temperature: 1 (upstream hard-coded), num_samples=1, max_attempt_num=1
- timeout: 900 s, ranking: MRR
- dataset: 10 P1 HELD_OUT_TEST tasks (leakage-free, patch="")
- file-set conversion: exact emitted merged file set (frozen)
- cost: real token usage × frozen P1 pricing (`$0.30/$1.00 per 1M`), computed
  by the common evaluator — a NORMALIZED estimate, not authoritative
  provider-billed cost; upstream `calc_cost` diagnostic-only
- model-call count: from the per-call usage ledger (authoritative)
- credential: ONE dedicated Benchmark key (parent env `OPENROUTER_API_KEY`,
  `BENCHMARK_KEY_SOURCE=SEPARATE_PARENT_ENV`), bridged via WSLENV, no key
  switching during P5-C

## 1. Held-out outcomes (10/10)

| Case | found_files | Outcome | Raw-log failure evidence |
|---|---|---|---|
| djangocms-rc-4307e1b8c2e2 | 0 | fail-closed empty (timeout) | `execution flow reconstruction exceeded timeout. Terminating.` |
| djangocms-rc-50c3576080be | 11 | valid | — |
| djangocms-rc-630a50361ada | 1 | valid | — |
| djangocms-rc-66c70394c9e1 | 0 | fail-closed empty (context-length) | `OpenrouterException - Upstream error from Venice: ... maximum context length ... 198248 input tokens` |
| djangocms-rc-75978fb1c3ad | 1 | valid | — |
| djangocms-rc-8d50660e7bcf | 4 (3 in-universe) | valid | — |
| djangocms-rc-9e33db4f4660 | 0 | completed-but-empty | `localizing ... succeed, process multiple loc outputs` with empty `found_files` |
| djangocms-rc-b39799f9fc1c | 0 | completed-but-empty | `localizing ... succeed, process multiple loc outputs` with empty `found_files` |
| djangocms-rc-ba16eb9a1d09 | 7 | valid | — |
| djangocms-rc-fdda30c271f0 | 0 | fail-closed empty (timeout) | `execution flow reconstruction exceeded timeout. Terminating.` |

**Failure taxonomy (corrected 2026-09-15):** 5 valid / 5 empty. The 5 empty
outcomes are **NOT all timeouts**: 2 timeout (4307e1b8c2e2, fdda30c271f0),
1 context-length `BadRequestError` (66c70394c9e1), and 2 completed-but-empty
(9e33db4f4660, b39799f9fc1c — the upstream flow logged "succeed" but yielded
no parseable file set). The prior "50% timeout rate" wording is NOT supported.

## 2. Infrastructure repair note (held-out execution)

The first P5-C attempt on case 3 (`630a50361ada`) exposed an upstream
transport-handling defect: an upstream backend rejected the agent's oversized
context (~197k prompt tokens near the 262k limit) with `BadRequestError`, and
the upstream handler did `continue` WITHOUT decrementing `max_attempt_num`, so
with `max_attempt_num=1` the attempt re-entered forever and the 900 s timeout
never persisted a fail-closed result. Fixed in the compatibility patch (bounded
BadRequestError handler → fail-closed within the frozen attempt policy). This
is an execution infrastructure repair, NOT a scientific tuning change.
Aborted case-3 partial usage (170 ledger rows) was EXCLUDED from the final
aggregate; cases 1-2 were preserved verbatim and NOT rerun.

## 3. Authoritative accounting (per-call usage ledger)

- Authoritative LLM calls: **402** (cases 1-2 from preserved evidence + 3-10
  from the resumed run; aborted case-3 rows excluded)
- Prompt tokens: 32,718,518
- Completion tokens: 113,256
- Total tokens: 32,831,774
- Estimated API cost (frozen pricing snapshot): **$9.928811** (a NORMALIZED
  estimate under the frozen pricing snapshot, not authoritative
  provider-billed cost)
- Latency (summed per-call): ~4,026 s of LLM call time

Per-call ledger fields: case_id, call_index, resolved model, resolved provider,
status, prompt/completion tokens, latency, estimated cost. No prompts,
responses, secrets, or hidden targets persisted.

## 4. Shared-protocol comparison (same 10 held-out tasks)

Execution/validity denominators are explicit (independent tasks / runs-cells /
non-empty-parseable / fail-closed-empty):

| System | Tasks | Runs/cells | Non-empty/parseable | Fail-closed/empty | P | R | F1 | FNR | comp_tok | calls | cost | lat |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Full-v2 | 10 | 30 | 30 | 0 | 0.339 | 0.369 | 0.353 | 0.631 | 8,445.8 | 30 | $0.2976 | 1,715.7s |
| Sparse-v2 | 10 | 30 | 30 | 0 | 0.387 | 0.261 | 0.312 | 0.739 | 599.0 | 30 | $0.0623 | 200.4s |
| LocAgent | 10 | 10 | 5 | 5 | 0.435 | 0.270 | 0.333 | 0.730 | 11,325.6 | 402 | $9.9288 | 4,025.9s |

Macro means (task-level): Full-v2 F1 0.387, Sparse-v2 0.379, LocAgent 0.318.

Paired task-level F1 deltas (bootstrap over 10 independent tasks):
- LocAgent − Full: −0.0684 [CI95 −0.2496, 0.1702]
- LocAgent − Sparse: −0.0607 [CI95 −0.3057, 0.2409]

LocAgent-native metrics (from original ranked order, separate from F1,
corrected 2026-09-15):
- Official Acc@K (task hit iff #correct in top-K == min(proxy, K)): Acc@1
  4/10; Acc@3 4/10; Acc@5 2/10.
- Simple task-level Hit@K (>=1 proxy file in top-K): 4/10 at every K.
- Item-hit sums (audit-only, NOT task accuracy): 4/8/9 — the historical
  4/10, 8/10, 9/10 claims were these item-hit sums and are NOT Acc@K / Hit@K.

## 5. Independent audit

PASS (see `reports/LOCAGENT_P5C_AUDIT.md`; corrected audit adds assertions for
native Acc@K semantics, failure taxonomy, provider-route provenance, and
consistent efficiency denominators).

## 6. Evidence

- `research/locagent-p5b/out_c/` — raw outputs, merged ranked outputs,
  trajs, log, args, wrapper manifest, merged authoritative ledger
- `research/locagent-p5b/shared_comparison.json` — machine-readable table
- `scripts/locagent_shared_comparison.py` — tracked scorer
- `scripts/audit_locagent_p5c.py` — tracked independent audit
- `reports/LOCAGENT_P5B_POSIX_VALIDATION_RUN.md` — P5-B validation