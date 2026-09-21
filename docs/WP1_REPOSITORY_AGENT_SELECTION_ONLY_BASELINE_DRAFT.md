# WP-1 — Repository-Agent Selection-Only Baseline (DRAFT)

**STATUS: DRAFT — AWAITING AHMED AUTHORIZATION — DO NOT EXECUTE**

**WP-1a preparation (2026-09-21): COMPLETE on branch
`feat/wp1a-selection-baseline-preparation`. Model-parity correction below
REPLACES the earlier DeepSeek claim; the WP-1a artifacts under
`research/wp1a/` freeze model/provider provenance, label-free prediction
schemas, deterministic per-task re-derivation, main-50/calibration-3 sample
freeze, intent parity, the repository-agent protocol, failure semantics,
shared scorer, accounting, budget model, and outcome categories. This document
remains a DRAFT and remains DO_NOT_EXECUTE.

This document is a specification DRAFT only. It defines a future work
package. It does NOT authorize or perform any execution: no API calls, no
agent execution, no predictions, no scoring, and no newly accessed target
outcomes.

Related: `docs/END_TO_END_MEASUREMENT_BOUNDARY.md`,
`docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md`.

---

## 10.1 Research Question

**Primary question:** Under the same task population, model, repository
snapshots, candidate universes, scorer, and machine, what cost-quality
operating point does frozen RM-CSS provide relative to the existing iterative
repository agent for FILE-SET SELECTION ONLY?

This is NOT end-to-end regeneration. This is NOT a Ripple/LocAgent
head-to-head experiment.

## 10.2 Fixed Population

Use ONLY tasks from the already-opened Saleor RESERVE-300 population. No new
Saleor RESERVE outcomes are accessed.

- Frozen sample manifest seed: `20260920`.
- Proposed WP-1 subset: the first `n = 50` tasks in the existing deterministic
  frozen sample ordering.

The exact 50 IDs MUST be persisted and frozen BEFORE execution authorization.
Do NOT select tasks based on labels or difficulty. The existing frozen sample
manifest (`research/saleor-reserve-300-rmcss/saleor_reserve_300_sample.json`)
is the deterministic ordering source; do not reorder it.

## 10.3 Held-Constant Invariants

All arms MUST use:

- the exact same 50 task IDs;
- the same parent repository snapshots;
- the same candidate universe per task;
- the same intent input;
- the same scoring implementation;
- the same execution machine;
- the same model for every generative selection arm;
- temperature = 0;
- the same timeout/error accounting rules.

Model: `openrouter/deepseek/deepseek-v4-flash-0731`. **CORRECTED BY WP-1a
(2026-09-21):** the frozen Saleor-300 SIP run was mechanically verified to use
**`qwen/qwen3-coder` @ `deepinfra/turbo` (exact route
`openrouter:qwen/qwen3-coder@deepinfra/turbo`), temperature 0.0, completion cap
16384, 300/300 consistent** — see
`research/wp1a/sip_scientific_model_provenance.json`. The future repository-agent
generative arm MUST use the SAME scientific model identity (Qwen3-Coder) as the
frozen SIP predictions to avoid model mismatch. The OpenCode coding model is NOT
the scientific arm model. Do NOT hard-code either claim; recover it from the
frozen run records.

SIP and RM-CSS use their ALREADY-STORED predictions for those 50 tasks. Do
NOT call the LLM again for SIP or RM-CSS.

Repository Agent is the ONLY live generative arm.

## 10.4 Repository-Agent Baseline

Baseline implementation: the existing
`src/benchmark/strategies/iterative_agent.py` (or the currently authoritative
repository-agent implementation).

Before future execution, the WP MUST record EXACTLY:

- initial prompt;
- available tools;
- tool schemas;
- parent-snapshot access;
- candidate-universe boundary;
- file-reading policy;
- search policy;
- context retention/truncation policy;
- round definition;
- stopping rule;
- timeout rule;
- retry rule;
- malformed-output rule;
- empty-output rule.

Proposed hard round cap: **10 tool/model rounds per task**.

The agent may inspect ONLY information available at the PARENT state. It MUST
NOT access:

- target diff;
- target changed-file labels;
- hidden proxy;
- `expected_affected_artifacts`;
- target outcome;
- future repository state.

`allow_ground_truth_universe` MUST remain `False`. The RunRecord must make
this auditable.

## 10.5 Prediction Freeze Before Scoring

Although the 50 tasks come from an already-opened population, preserve
procedural blinding. For all 50 tasks:

1. produce repository-agent selection predictions;
2. persist raw transcripts/predictions;
3. freeze IDs and prediction hashes;
4. only THEN load existing stored outcome labels for scoring.

The prediction process must never access the labels.

## 10.6 Arms

Exactly:

1. `repository_agent`
2. `SIP`
3. `RM-CSS`

No fourth method. No V3. No tuning. No new localization features.

## 10.7 Metrics

For each arm report:

**Impact Correctness:**

- TP
- FP
- FN
- Precision
- Recall
- FNR
- F1
- mean predicted set size
- empty-set rate

**Efficiency:**

- total prompt tokens
- total completion tokens
- total tokens
- total model calls
- mean model calls/task
- total wall time
- mean latency/task
- total USD cost
- mean USD/task

For deterministic non-generative RM-CSS components, additionally report their
already-established incremental embedding/memory/classifier costs where
applicable, without double counting.

Use one shared scorer for all arms. Assert task-ID sets are exactly identical.

## 10.8 Cost-Quality Hypothesis

The hypothesis must be stated narrowly:

**`H_WP1`:** Frozen RM-CSS provides a lower-cost FILE-SELECTION operating
point than the iterative repository agent without lower file-set F1 on the
same 50 tasks.

Pre-register outcome categories BEFORE execution.

**A. `RM_CSS_COST_QUALITY_DOMINANCE`** — only if RM-CSS F1 >= repository-agent
F1 AND RM-CSS uses fewer total tokens, fewer model calls, and lower total USD
cost. Latency is reported but is not by itself a hard dominance criterion
(wall-clock is more environment-sensitive).

**B. `COST_QUALITY_TRADEOFF`** — if RM-CSS is cheaper on the core efficiency
metrics but RM-CSS F1 < repository-agent F1. Do NOT call this superiority;
report the frontier/trade-off.

**C. `NO_RM_CSS_EFFICIENCY_ADVANTAGE`** — if RM-CSS does not reduce the core
efficiency metrics relative to the repository agent.

**D. `RM_CSS_EFFICIENCY_HYPOTHESIS_FALSIFIED`** — the narrow hypothesis
"lower cost without lower F1" is falsified on this WP sample if RM-CSS F1 <
repository-agent F1 OR RM-CSS fails to reduce one or more of the
pre-registered core efficiency dimensions (total tokens, total model calls,
USD cost).

Do NOT move the goalposts after seeing results. This n=50 study remains a
same-protocol measured baseline and must not be silently upgraded to a
universal / SOTA claim.

## 10.9 Statistical Reporting

Use paired task-level bootstrap:

- 10,000 resamples;
- seed: `20260920`.

Report Delta F1 (RM-CSS - repository_agent) with a 95% percentile CI. Also
report descriptive paired differences for tokens/task, calls/task,
latency/task, and USD/task.

Do NOT invent a non-inferiority margin unless an already-authoritative
source-of-truth document defines one for THIS selection-only experiment. If no
such margin exists, do NOT silently choose one; use the categorical
cost-quality rules above.

## 10.10 Budget

Proposed hard scientific API ceiling: **$2.50 total**. This ceiling applies
only when Ahmed explicitly authorizes WP-1 execution.

Before any future paid call: run a label-free cost projection. If projected
total > $2.50, STOP before paid calls.

During execution: log cumulative cost after every task. If actual cumulative
cost reaches the hard ceiling, abort before the next paid request.

## 10.11 Failure Semantics

The future WP-1 protocol MUST define:

- transport retry count;
- malformed-response handling;
- empty-response handling;
- timeout handling;
- whether a failed task becomes an EMPTY prediction or is excluded.

Do NOT silently exclude hard tasks. Any pre-label infrastructure exclusion
must be logged and must not be replaced after label access. The final protocol
MUST freeze these semantics BEFORE execution.

## 10.12 Acceptance Criteria

Draft ACs:

- **AC-1.1 — Population identity:** all three arms use exactly the same 50
  task IDs. Mechanical assertion: byte-identical sorted task-ID manifests.
- **AC-1.2 — Leakage fence:** repository agent reads only parent-state/public
  information. `allow_ground_truth_universe=False`. No target diff / hidden
  proxy / expected affected artifacts. Independent audit PASS.
- **AC-1.3 — Prediction freeze:** all repository-agent predictions and hashes
  persisted before the scorer loads outcomes.
- **AC-1.4 — Shared scorer:** all three arms scored by the same scorer
  implementation. Independent audit re-derives every
  TP/FP/FN/P/R/FNR/F1.
- **AC-1.5 — Efficiency accounting:** tokens/calls/latency/USD recorded
  mechanically from raw run artifacts. Accounting identity passes.
- **AC-1.6 — Budget:** total scientific API cost <= $2.50.
- **AC-1.7 — Reproducible agent protocol:** loop, tools, round cap, stop
  rules, context policy and failure semantics frozen before the first paid
  call.
- **AC-1.8 — Statistical output:** 10,000-task-level paired bootstrap with
  seed 20260920 reproduces from raw per-task records.
- **AC-1.9 — Independent audit:** an independent script recomputes all
  headline values.
- **AC-1.10 — Claim boundary:** final report explicitly states
  "same-protocol n=50 selection-only comparison; not E2E; not universal
  state-of-the-art evidence."

## 10.13 Proposed Selective Update Record

Future execution, if authorized, MUST create:
`selective_updates/records/SU-0013-repository-agent-selection-baseline.md`

SU-0013 is not currently allocated in authoritative project history (verified
at draft time). If SU-0013 is already allocated by authoritative project
history before execution, do NOT silently reuse it. Record the conflict in
the DRAFT and leave the final SU identifier as `TO_BE_ASSIGNED_AT_AUTHORIZATION`.
Do not renumber existing records.

## 10.14 Status

`AWAITING_AHMED_AUTHORIZATION`

`DO_NOT_EXECUTE`

### WP-1a preparation status (2026-09-21)

- **WP-1a artifacts:** `research/wp1a/` (model provenance, label-free schema,
  per-task predictions + SHA-256 manifest, re-derivation verification, main-50
  and calibration-3 manifests, intent parity, frozen agent protocol, failure
  semantics, shared scorer schema, accounting schema, budget model,
  cost-quality categories, independent audit, acceptance report).
- **AC-1A.1..AC-1A.12:** all PASS (see `research/wp1a/wp1a_acceptance_report.json`).
- **WP-1b:** NOT executed; remains `WP-1b Calibration + Main n=50 Selection
  Run — AWAITING AHMED AUTHORIZATION`.
