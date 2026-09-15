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

## 1. Held-out outcomes (10/10)

| Case | found_files | Valid |
|---|---|---|
| djangocms-rc-4307e1b8c2e2 | 0 | fail-closed (timeout) |
| djangocms-rc-50c3576080be | 11 | valid |
| djangocms-rc-630a50361ada | 1 | valid |
| djangocms-rc-66c70394c9e1 | 0 | fail-closed (timeout) |
| djangocms-rc-75978fb1c3ad | 1 | valid |
| djangocms-rc-8d50660e7bcf | 4 (3 in-universe) | valid |
| djangocms-rc-9e33db4f4660 | 0 | fail-closed (timeout) |
| djangocms-rc-b39799f9fc1c | 0 | fail-closed (timeout) |
| djangocms-rc-ba16eb9a1d09 | 7 | valid |
| djangocms-rc-fdda30c271f0 | 0 | fail-closed (timeout) |

5 valid / 5 fail-closed empty (900 s per-attempt timeouts, persisted fail-closed).

## 2. Infrastructure repair note (held-out execution)

The first P5-C attempt on case 3 (`630a50361ada`) exposed an upstream
transport-handling defect: DeepInfra rejected the agent's oversized context
(~197k prompt tokens near the 262k limit) with `BadRequestError`, and the
upstream handler did `continue` WITHOUT decrementing `max_attempt_num`, so with
`max_attempt_num=1` the attempt re-entered forever and the 900 s timeout never
persisted a fail-closed result. Fixed in the compatibility patch (bounded
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
- Estimated API cost (frozen pricing): **$9.928811**
- Latency (summed per-call): ~4,026 s of LLM call time

Per-call ledger fields: case_id, call_index, resolved model, resolved provider,
status, prompt/completion tokens, latency, estimated cost. No prompts,
responses, secrets, or hidden targets persisted.

## 4. Shared-protocol comparison (same 10 held-out tasks)

| System | Valid | P | R | F1 | FNR | comp_tok | calls | cost | lat |
|---|---|---|---|---|---|---|---|---|---|
| Full-v2 | 30/30 | 0.339 | 0.369 | 0.353 | 0.631 | 8,445.8 | 30 | $0.2976 | 1,715.7s |
| Sparse-v2 | 30/30 | 0.387 | 0.261 | 0.312 | 0.739 | 599.0 | 30 | $0.0623 | 200.4s |
| LocAgent | 5/10 | 0.435 | 0.270 | 0.333 | 0.730 | 11,325.6 | 402 | $9.9288 | 4,025.9s |

Macro means (task-level): Full-v2 F1 0.387, Sparse-v2 0.379, LocAgent 0.318.

Paired task-level F1 deltas (bootstrap over 10 independent tasks):
- LocAgent − Full: −0.0684 [CI95 −0.2496, 0.1702]
- LocAgent − Sparse: −0.0607 [CI95 −0.3057, 0.2409]

LocAgent-native Acc@K (from original ranked order, separate from F1):
- Acc@1: 4/10; Acc@3: 8/10; Acc@5: 9/10

## 5. Independent audit

PASS (19/19): exact 10 held-out IDs; no hidden leakage; candidate mapping
correct; frozen proxy labels; frozen protocol (temp 1, num_samples 1,
max_attempt_num 1, timeout 900, MRR); no poor-result reruns (cases 1-2
preserved, aborted case 3 excluded); timeout results retained; ledger mapped
to tasks; total tokens = summed ledger; model-call count = ledger count; cost
uses frozen pricing; no secrets in evidence; evidence hashes stable; LF
line-endings preserved; native ranking preserved; P1 evidence reused (not
regenerated); six gates manifest present; cost-audit assertion holds.

## 6. Evidence

- `research/locagent-p5b/out_c/` — raw outputs, merged ranked outputs,
  trajs, log, args, wrapper manifest, merged authoritative ledger
- `research/locagent-p5b/shared_comparison.json` — machine-readable table
- `scripts/locagent_shared_comparison.py` — tracked scorer
- `scripts/audit_locagent_p5c.py` — tracked independent audit
- `reports/LOCAGENT_P5B_POSIX_VALIDATION_RUN.md` — P5-B validation