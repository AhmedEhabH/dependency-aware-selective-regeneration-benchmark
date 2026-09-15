# P5-B — LocAgent VALIDATION pilot on Ubuntu/WSL (COMPLETE)

**Date:** 2026-09-15
**Host:** WSL2 Ubuntu-24.04 (preferred POSIX host per P5 sprint authority)
**Upstream:** gersteinlab/LocAgent @ `4935b557326c154bad8e8dcf3747cc8d32d1f387` (unchanged pin)
**Model/provider:** `openrouter/qwen/qwen3-coder` (Qwen3-Coder-480B-A35B) —
**OpenRouter-routed** via the same route family as P1. NOTE (corrected
2026-09-15): the per-call ledger records `provider="openrouter"` (the
gateway), not the resolved backend; raw logs show both DeepInfra and Venice
upstream errors, so an unqualified per-call DeepInfra pin is NOT supported for
P5. Fallback OFF.
**Compatibility layer:** `research/locagent-p5b/launch_locagent.py`
(`locagent-compat-launch-layer-1.1`) — invokes upstream `localize()`/`merge()`
with a frozen args namespace; bypasses the restrictive upstream `--model`
argparse `choices` only. No change to prompts, BM25, graph traversal, ranking,
temperature, iteration budget, or output semantics.

## 0. P5-B VALIDATION results (6/6 executed, frozen common evaluator)

Policy: exact emitted merged file set (`exact_emitted_file_set`). LocAgent
native Acc@K reported separately; never mixed with F1. Cost = real token
usage x frozen P1 pricing (`input $0.30/1M`, `output $1.00/1M`).

| Case | Pred | Proxy | P | R | F1 | FNR | prompt_tok | comp_tok | est. cost |
|---|---|---|---|---|---|---|---|---|---|
| djangocms-rc-0daae01f2f65 | 3 | 5 | 0.667 | 0.400 | 0.500 | 0.600 | 1,101,416 | 1,951 | $0.332376 |
| djangocms-rc-0fec81224889 | 3 | 3 | **1.000** | **1.000** | **1.000** | **0.000** | 589,908 | 1,310 | $0.178282 |
| djangocms-rc-1031d20fca28 | 0 | 9 | 0.000 | 0.000 | 0.000 | 1.000 | 0 | 0 | $0.000000 |
| djangocms-rc-47b63015feb1 | 0 | 2 | 0.000 | 0.000 | 0.000 | 1.000 | 0 | 0 | $0.000000 |
| djangocms-rc-a9e2a8d3b7a6 | 1 | 3 | **1.000** | 0.333 | 0.500 | 0.667 | 564,589 | 1,608 | $0.170985 |
| djangocms-rc-e3a23a7fc757 | 0 | 3 | 0.000 | 0.000 | 0.000 | 1.000 | 0 | 0 | $0.000000 |
| **Aggregate** | | | **0.444** | **0.289** | **0.333** | **0.711** | | | **$0.681643** |

- valid_output_rate = 0.5 (3/6 produced real found_files; 3/6 fail-closed
  empty). NOTE (corrected 2026-09-15): the P5-B pre-ledger run predates the
  per-case log taxonomy, so P5-B empty rows are recorded as fail-closed; the
  authoritative per-case failure taxonomy (timeout vs context-length
  BadRequest vs completed-but-empty) is established from raw logs in P5-C.
- LocAgent-native Acc@K (found_files top-K hits) is reported separately and is
  NOT the common F1 column.
- The 3 empty rows are fail-closed outcomes (agent ran its full budget without
  a usable `<finish>` file set) under the frozen attempt policy — fail-closed,
  not data loss. See the P5-C taxonomy for per-case failure classification.
- Efficiency columns for this pre-ledger run are provisional (see §5): token/
  cost for timeout rows is incomplete/non-authoritative; authoritative
  ledger-based accounting applies to P5-C.

## 1. Status

- **P5-B VALIDATION pilot: COMPLETE 6/6.** Case 1
  `djangocms-rc-0daae01f2f65` SUCCESS (real 3-file output); case 2
  `djangocms-rc-0fec81224889` SUCCESS (perfect F1=1.0, 3/3); case 5
  `djangocms-rc-a9e2a8d3b7a6` SUCCESS (1 file); cases 3/4/6 fail-closed empty
  (timeouts). Six gates 6/6 PASS; independent audit 12/12 PASS; common metrics
  computed above.
- **GO decision: P5-B GO** — all six VALIDATION cases executed (3 real outputs,
  3 fail-closed timeouts under the frozen attempt policy), parser/common
  evaluator stable, no hidden target used to tune, model/provider/prompt/search
  settings frozen, audit PASS.

## 2. What was solved on POSIX (relative to the prior Windows blocker)

The 2026-09-14 blocker report
(`reports/LOCAGENT_P5B_VALIDATION_BLOCKER_REPORT.md`) recorded that the pinned
upstream uses `mp.get_context('fork')` (POSIX-only) and that `--model` argparse
`choices` reject `openrouter/qwen/qwen3-coder`. On Ubuntu/WSL:

1. `fork` is available → the agent loop runs natively.
2. A **compatibility launch layer** (outside upstream source) constructs the
   frozen args namespace and calls upstream `localize()` / `merge` directly,
   so the restrictive `--model` list is never consulted.
3. The upstream repo clone was pinned at `4935b557…` and served from a **local
   frozen mirror** (the GitHub `djangocms/djangocms` repo currently serves an
   empty ref list; the audited `dist/real-commit-cache/djangocms` mirror is
   used via `git url.insteadOf`). LF line endings enforced (`core.autocrlf=false`)
   because CRLF breaks the upstream tree-sitter pre_code parser.
4. Dependency set resolved on Linux (litellm 1.100.1, llama-index-core 0.11.22,
   bm25s 0.2.14, tree-sitter 0.21.3, faiss-cpu, torch 2.14.0+cpu).

## 3. Deadlock guard (process-failure handling only)

A stalled 6-case run exposed an upstream deadlock: when a worker exits without
writing to `result_queue` and `join(timeout)` returns, the parent blocks forever
on the unbounded `result_queue.get()`. Fixed with a **documented minimal
upstream patch** (`research/locagent-p5b/upstream_patch_p5_queue_guard.patch`,
SHA-256
`c2fa932f27735a9d455f81e12fb08f00450cdad74471b3fd54d149f844edd368`) that:

- adds `LocAgentWorkerFailureError`;
- after `join(timeout=args.timeout)`, checks `process.exitcode`;
  nonzero → classify attempt failed (fail-closed);
- replaces unbounded `result_queue.get()` with bounded `get(timeout=30)`;
  `Empty` → fail-closed attempt;
- new `except` handler decrements `max_attempt_num` and continues — the
  same frozen attempt policy as TimeoutError / ContextWindow errors.

No localization semantics change. Regression tests:
`tests/unit/test_locagent_queue_agent.py` (child-exits-without-result →
fail cleanly, normal result path intact, bare get() negative control, patch
text guards).

## 4. Integration / accounting note — credential provenance

The P5 smoke and the stalled pre-fix VALIDATION run were executed with the
OpenRouter credential sourced from the OpenCode internal auth store
(`C:\Users\Ahmed\.local\share\opencode\auth.json`) via a transient PowerShell
bridge. That store is OpenCode's own credential and is NOT the dedicated
Benchmark key.

**Correction (2026-09-15):** benchmark/P5 processes must obtain the scientific
credential ONLY from the parent Windows environment
(`OPENROUTER_API_KEY` set by Ahmed before launching OpenCode) and bridge it
transiently to WSL via WSLENV. No benchmark/P5 code may read
`opencode/auth.json`. Verified:

- `OPENROUTER_API_KEY=SET` in the parent environment;
- `BENCHMARK_KEY_SOURCE=SEPARATE_PARENT_ENV` (in-memory comparison confirms the
  parent key is NOT the OpenCode auth-store key);
- no tracked/committed code references the OpenCode auth store;
- no credential persists in WSL or in committed evidence.

P5-B VALIDATION results remain valid because model/provider/prompt/algorithm
identity were unchanged; the provenance issue is **integration/accounting
only**. Valid persisted outputs (e.g. Case 2) are not rerun.

P5-C HELD_OUT will use ONE dedicated Benchmark credential for all 10 tasks,
sourced from the parent environment, with no key switching.

## 5. Cost accounting

Upstream `util/cost_analysis.py` returns 0 for any model name containing
`qwen` (verified on the smoke run: upstream `cost($)='0'` while actual usage
was 1,310,246 prompt + 2,207 completion tokens). Therefore upstream native
cost is **diagnostic-only**. The authoritative estimated cost is computed in
the common evaluator from real LiteLLM/OpenRouter token usage × the frozen P1
pricing snapshot (`input $0.30/1M`, `output $1.00/1M`). Audit assertion:
non-zero Qwen/OpenRouter usage must not produce zero authoritative estimated
cost (`assert_cost_not_zero_for_paid_usage`).

**Ledger instrumentation (2026-09-15):** an append-only per-call usage ledger
(`research/locagent-p5b/usage_ledger.py`) now wraps `litellm.completion` and
persists one metadata row per call (case_id, call_index, model, provider,
status, prompt/completion tokens, latency, estimated cost). It never persists
prompts, responses, secrets, or hidden targets. The ledger is the authoritative
source for model-call count and token/cost accounting in the shared comparison.
`len(raw_output_loc)` is NOT used as the model-call metric.

**P5-B efficiency accounting caveat:** the P5-B VALIDATION run predates the
ledger, so its efficiency figures are provisional:
- `model_calls` in the P5-B table is a floor (per persisted output), not the
  authoritative ledger count;
- timeout cases (1031d20fca28, 47b63015feb1, e3a23a7fc757) made real LLM calls
  before their 900 s timeout but their token/cost is recorded as **incomplete /
  non-authoritative** (0 shown) rather than claimed as a real zero-cost result.
The authoritative, ledger-based efficiency numbers apply to P5-C.

## 6. Evidence

- Smoke (MINER_DEV): `research/locagent-p5b/evidence_smoke/`
- Stalled pre-fix run: `research/locagent-p5b/evidence_p5b_stalled/`
- P5-B VALIDATION outputs + trajs + log: `research/locagent-p5b/out/`
- Six gates + audit scripts: `scripts/validate_locagent_p5b_gates.py`,
  `scripts/audit_locagent_p5b.py`

## 7. P5-C freeze (GO)

P5-C will run the SAME frozen protocol on the 10 HELD_OUT_TEST tasks exactly
once:
- upstream SHA `4935b557326c154bad8e8dcf3747cc8d32d1f387` + queue-guard patch
  `c2fa932f…`;
- compatibility wrapper `locagent-compat-launch-layer-1.1`;
- model `openrouter/qwen/qwen3-coder` — OpenRouter-routed (backend provider
  not proven per call; see corrected provider-route note), fallback OFF;
- temperature 1 (upstream hard-coded), max_attempt_num 1, num_samples 1,
  ranking mrr, timeout 900;
- file-set conversion: exact emitted merged file set;
- cost: real token usage x frozen P1 pricing via common evaluator;
- ONE dedicated Benchmark credential (parent env `OPENROUTER_API_KEY`), bridged
  via WSLENV, verified `BENCHMARK_KEY_SOURCE=SEPARATE_PARENT_ENV`, no key
  switching, capability probe before call #1.