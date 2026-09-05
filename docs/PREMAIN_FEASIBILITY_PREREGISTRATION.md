# Pre-Main Feasibility Preregistration

**Status:** FROZEN 2026-09-04 (before any new real model call).
**Companions:** `docs/SCIENTIFIC_RESET_DECISION_2026-09-04.md`,
`docs/POST_2018_RESEARCH_EVIDENCE_MATRIX.md`, `DECISION_LOG.md` D040–D045.

Sources (decision pack, `_workspace/active/`):
`00_DECISION_LOCK.md`, `01_MODEL_PROVIDER_ACCEPTANCE_GATE.md`,
`02_TODO_SCENARIO_PREREGISTRATION.md`, `03_MICROSTUDY_GO_NOGO_RULES.md`,
`06_NEXT_EXECUTION_PLAN.md`, `07_CLAUDE_FEEDBACK_INTEGRATION.md`.

---

## 0. No scientific model call before freeze

No scientific Todo scenario, evaluator, ground truth, or study requirement may
be sent to any model before this preregistration commit is frozen and pushed.
The pre-registered 6-call operational gate uses only throwaway tasks and is not
scientific. Runtime API/model code is not implemented in this freeze task.

---

## 1. Model / provider acceptance gate

Non-study, operational only. It selects a serving configuration; it is NOT a
model benchmark and is NOT used to choose a model by Selective-vs-Agent favor.

**Candidates (blinded order if practical):**
- Candidate A: DeepSeek V4 Flash 0731
- Candidate B: Qwen2.5-Coder-32B-Instruct

**Frozen call settings (where supported equally):** temperature = 0;
non-thinking/direct mode; same exact system/user prompts for equivalent tasks;
same output-token ceiling per task; one fixed provider per candidate during the
gate; no auto-routing/fallback between providers; at most ONE retry for
transport/rate-limit errors (model/content errors are never retried for
acceptance scoring).

**Three throwaway tasks** (MUST NOT be any of the 3 scientific Todo
scenarios):
- T1 exact-patch operational task (small synthetic file, unique target, valid
  SEARCH/REPLACE, patch applies exactly, unrelated bytes preserved);
- T2 agent-control operational task (synthetic repo inventory, frozen
  machine-readable decision/control format, all selected paths from the
  inventory, output parses without repair);
- T3 repair operational task (synthetic faulty patch/validation error, exact
  repair contract obeyed, corrected artifact passes the tiny deterministic
  validation).

**Mandatory eligibility thresholds (ALL must hold):**
1. Task sanity: 3/3 tasks reach their deterministic operational success
   condition.
2. Format compliance: 3/3 first model responses parse under the required
   output contract.
3. Truncation: 0/3 responses finish because of output-length truncation.
4. Transport/provider reliability: ≤1 transient transport/rate-limit event
   across the 3 calls; if one occurs the single allowed retry must succeed.
5. Usage accounting: prompt/input + completion/output tokens returned (or a
   stored equivalent provider usage record) for 3/3 successful calls.
6. Latency: every successful call ≤ 120 s wall-clock; median successful-call
   latency ≤ 60 s.
7. No hidden scientific data: none of the three Todo scientific
   requirements/evaluators/ground truth appear in the acceptance prompts.

**Selection if both eligible** (in order, without looking at scientific
outcomes): 1 higher first-response format-compliance; 2 lower truncation
count; 3 lower median latency; 4 if median latency differs by <20%, lower
observed normalized API cost; 5 still tied → simpler fixed-provider
reproducibility contract, tie documented.

**Failure rule:** exactly one eligible → freeze it; neither eligible → STOP and
diagnose the gate only (no scientific scenarios). No third model is introduced
because outputs are aesthetically unsatisfying — a third candidate requires a
documented amendment before any scientific run.

**Freeze record after selection:** exact model ID/version, exact provider,
endpoint/API mode, temperature, thinking mode, max output tokens per phase,
retry/backoff policy, timeout, structured-output/tool policy, date/time,
pricing snapshot (operational metadata only), API response usage semantics.
Then freeze before the first scientific run.

---

## 2. Frozen Todo scenario IDs + selection rationale

| ID | Blast radius | Existing evaluator asset |
|---|---|---|
| todo-smoke-001 | localized | tests/evaluator_assets/todo_smoke_001_checks.py |
| todo-smoke-002 | moderate | tests/evaluator_assets/todo_smoke_002_checks.py |
| todo-smoke-003 | cross_cutting | tests/evaluator_assets/todo_smoke_003_checks.py |

**Selection rule (mechanical, output-independent):** exactly one pre-existing
Todo scenario per blast-radius class, prioritizing scenarios that (1) existed
before the 2026-09-04 pivot, (2) already have an independent executable
evaluator asset, (3) have explicit expected actions, (4) span
localized/moderate/cross-cutting, (5) are chosen without reference to which
strategy previously looked better. These three are pre-existing Todo smoke
scenarios with evaluators; they are NOT chosen because of the final 1/6 canary
outcome.

**Mandatory pre-run audit (before freezing the dataset):** line-by-line
evaluator-to-visible-contract traceability; no hidden feature surprises; no
leakage of evaluator files/gold expected-actions to either strategy; pinned
Todo base satisfies preconditions; each scenario starts from the SAME pinned
base independently (no sequential contamination unless explicitly designed).

**Replacement rule:** a scenario may be replaced BEFORE any scientific model
call only if the audit identifies contradiction, evaluator leakage,
non-executability, or an invalid pinned-base assumption. Replacement must stay
in the same blast-radius class, follow the same evaluator-readiness rule, be
documented before any scientific call, and never happen because a
strategy/model performs poorly.

---

## 3. Todo 30-run design

```text
3 scenarios × 2 strategies (Agent vs Selective) × 5 independent repetitions
= 30 attempted runs
```

- Both strategies share the same frozen executor/backend/model/provider.
- All failures are retained and classified (attempted-failure retention).

---

## 4. GO / NO-GO thresholds (frozen before model calls)

**Per-scenario Selective gate (5 repetitions):**

- **G1 Changed-requirement correctness:** Selective passes the changed
  requirement executable evaluator in >=4/5 repetitions AND Selective is not
  worse than Agent by more than 1 passing repetition for that scenario
  (examples: Agent 5/5 & Selective 4/5 → clears; Agent 5/5 & Selective 3/5 →
  fails; Agent 4/5 & Selective 4/5 → clears; Agent 3/5 & Selective 4/5 →
  clears Selective gate while the Agent baseline weakness is reported
  separately).
- **G2 Preservation:** in >=4/5 Selective repetitions, zero unintended
  modifications to artifacts labeled preserve AND regression/preservation
  checks pass.
- **G3 Impact recall:** in >=4/5 Selective repetitions, the predicted
  regenerate-set contains every gold artifact labeled regenerate (recall =
  1.0). A run missing a required regenerate artifact is a miss even if the
  executor later happens to pass a limited test.
- **G4 Efficiency (secondary, descriptive only):** computed among
  correctness+preservation-qualified runs: total workflow prompt/input tokens,
  completion/output tokens, total tokens, model calls, selected artifacts,
  regenerated artifacts, wall-clock latency, repair attempts. Medians + raw
  values reported. **No significance claim from n=5.**

**Study-level decision:**
- **GO to conditional djangoCMS extension** only if ALL THREE Todo scenarios
  clear G1 correctness AND G2 preservation AND at least 2/3 scenarios clear G3
  full-impact-recall. Efficiency does NOT have to win statistically to
  authorize the next stage.
- **NO-GO / bounded result:** if the conditions are not met → do not scale to
  djangoCMS; analyze failure modes; preserve the negative/bounded scientific
  result; discuss whether mechanism, ground truth, or executor is limiting,
  without tuning on observed outcomes.

**No post-hoc threshold edits.** Changing any threshold after seeing results
invalidates the study as confirmatory go/no-go evidence and forces explicit
relabeling as exploratory.

---

## 5. Graph eligibility distinction

- **verified-empty graph:** the extractor ran correctly and the scoped case
  genuinely has no dependency edges → may remain a low-information **valid**
  observation.
- **fallback-empty / failed graph:** dependency evidence was not actually
  established → **NOT eligible** for a dependency-aware treatment claim.

Current djangoCMS/Saleor concern is the fallback/construct problem, so the
practical current NO-GO for those repositories stays; Todo has a real graph.

---

## 6. Anti-cherry-picking rules

After this preregistration is committed:
- scenario IDs do NOT change because a strategy/model performs poorly;
- acceptance thresholds do NOT change after the six operational calls;
- model/provider does NOT change after scientific results are seen;
- study failures are retained and classified;
- the winner is selected using operational criteria only (never a scientific
  scenario).

---

## 7. Definition of done for the next feature

The `SCIENTIFIC-MICROSTUDY-01` feature is complete only when either (1) the
30-run scientific results table exists and GO/NO-GO is computed, or (2) a
pre-registered acceptance/validation gate fails and the Stop Report identifies
the exact blocker. Green tests alone do not complete it.

---

# PA-001 — Amendment: SCIENTIFIC-MICROSTUDY-01 implementation clarification

**Date:** 2026-09-05
**Status:** FROZEN (preregistration clarification; discovered by independent
audit BEFORE any new real model call; NOT post-outcome tuning).
**Decision IDs:** D046 (this log); A029 (assumption ledger).
**Audit source:** `_workspace/active/01_INDEPENDENT_AUDIT_FINDINGS.md` (from
exact export `project-2026-09-04-2352.zip`, SHA-256
`9cb351419bc0e96bc848c14cb83317ceac5d53c3ee64656111951e2ed2924a8a`).

## 8.1 Five-file scored source universe (A7)

For this Todo micro-study the strategy-scored source-impact universe is frozen
as EXACTLY:

```text
todo/models.py
todo/serializers.py
todo/views.py
todo/permissions.py
todo/urls.py
```

This matches the existing Todo production dependency graph (5 nodes / 6 edges).

- `gold_regenerate_source_paths` = scenario expected_actions ∩ those 5 files.
- `gold_preserve_source_paths` = the remaining files among those 5.
- Regression test files are VALIDATE-ONLY evidence, not selector regenerate
  targets.
- Generated migration files are SHARED EXECUTOR obligations and are scored
  separately through `migration_generation_passed` / `generated_migration_paths`.
- Migration directories MUST NOT inflate or penalize strategy regenerate
  recall: `post_generation_command` is executed by the matched shared executor,
  not selected by either scope strategy.

## 8.2 Evidence obligations (A5 / A6)

- `predicted_actions: dict[str, str]` is MANDATORY per-run evidence; it must
  contain every final prediction decision path/action. Persisted through
  RunRecord → RunRecordData → JSONL.
- `changed_artifact_paths: list[str]` is MANDATORY per-run evidence; it is
  computed against the frozen active snapshot for the candidate source
  universe (actual unintended changes to preserve artifacts, not merely the
  model predicting `preserve`). Created migrations live in the existing
  `generated_migration_paths` and are excluded from this list.

## 8.3 Fixed provider / no-fallback identity requirement (A2 / A3)

Every OpenRouter generation request for the study MUST carry:

- exactly one pinned provider (no allowlist/order breadth);
- `allow_fallbacks: false`;
- `require_parameters: true` where supported.

`model_identity` shape: `openrouter:<model>@<provider>`. Provider/model/backend
changes MUST alter `config_hash` and Run IDs.

## 8.4 Gold expected-action isolation (A4)

- scientific generation/repair prompts NEVER receive `scenario.expected_actions`
  or `expected_artifact_instructions` sourced from gold labels;
- visible requirement/acceptance criteria and visible architecture constraints
  MAY be shared consistently to both arms;
- the actual edit action for an artifact comes from the strategy-generated
  `RegenerationPlan.actions`, NOT from scenario gold;
- generic Python syntax/module/dependency contract guards remain ACTIVE even
  when gold labels are hidden;
- the new scientific profile is fail-closed against gold leakage; historical
  profiles remain reproducible.

## 8.5 Frozen scientific execution contract

```text
scientific per-run workflow timeout = 900 seconds
source-edit completion cap          = 4096
agent-control completion cap        = 512
max attempts                        = 3
total-workflow token ceiling        = NONE unless the already-frozen pipeline
                                     requires one (no new ceiling invented here)
usage metric of record              = actual provider-reported usage
```

## 8.6 Candidate provider policy (frozen before calls)

Both candidates are served through the existing OpenRouter API backend.

- Candidate A: `deepseek/deepseek-v4-flash-0731` — use the FIRST-PARTY DeepSeek
  provider if it is available for the exact model and required parameters; pin
  ONLY that provider. If the first-party DeepSeek provider is unavailable,
  STOP the acceptance gate and require a preregistration amendment (do NOT
  silently pick a cheaper/faster third party).
- Candidate B: `qwen/qwen-2.5-coder-32b-instruct` — use its single available
  provider. If it is no longer single-provider, STOP and document the change
  before choosing.

Persist the resolved provider slug/name BEFORE the first model call.
---

# PA-002 — Amendment: IMPACTPLAN-WIP-01 (Stage-C R/P/V/H ImpactPlan treatment)

**Date:** 2026-09-05
**Status:** FROZEN (preregistration amendment; before any new model call).
**Decision IDs:** D047; A030 (assumption ledger).
**Supersedes:** Section 8 (PA-001 candidate-provider policy) ONLY for the
scientific model/provider choice; PA-001 evidence/identity/gold-isolation
contracts remain in force and are reused. The old binary R/P micro-study
authorization line `MICROSTUDY_REAL_RUN_AUTHORIZED=YES` is SUPERSEDED: current
authorization is `NO` until the new treatment passes six gates + independent
audit.

## 9.1 New WIP protocol

`label: scientific-wip-impactplan-v1`

## 9.2 Treatment construct — first-class ImpactPlan

The Selective arm (proposed arm) MUST: collect automatic evidence, invoke a
structured Impact Planner, apply a fail-closed invariant gate, and PERSIST the
ImpactPlan BEFORE any source write. The plan classifies every candidate
artifact exactly once as:

- `REGENERATE (R)` — edit justified and permitted.
- `PRESERVE (P)` — no edit justified; writes prohibited.
- `VALIDATE_ONLY (V)` — no edit expected; artifact inside the validation boundary.
- `HUMAN_REVIEW (H)` — evidence insufficient/conflicting or scope unsafe.

The plan also records `write_set`, `preserve_set`, `validate_set`,
`human_review_set`, `context_set` (independent of action sets),
validation/test obligations (separate from actions), architecture checks,
evidence references/rationale, confidence/uncertainty, and versioned
bounded-expansion provenance (parent plan hash, plan version).

## 9.3 Required invariants (fail-closed)

1. every candidate artifact classified exactly once;
2. `write_set == {R}`;
3. P/V/H are NOT writable;
4. action sets pairwise disjoint;
5. `context_set` independent of action sets (may include R/P/V/H);
6. every R cites at least one strategy-visible evidence item;
7. every V cites a validation/test/architecture reason;
8. unknown paths rejected;
9. hidden evaluator/gold artifacts never appear in planner inputs/evidence;
10. plan persisted before the first source write;
11. prohibited write attempts blocked and logged;
12. planner model calls/tokens/latency/cost included in proposed-arm total.

## 9.4 Bounded fallback

- initial plan `v1`;
- at most ONE evidence-driven expansion `v2` (parent hash + newly writable
  artifacts recorded);
- then HUMAN_REVIEW / non-automated outcome.
- Never switch to unrestricted repository writes.

## 9.5 Scientific model and provider (supersedes §8 candidate policy)

- Primary model: `qwen/qwen3-coder` (Qwen3-Coder-480B-A35B-Instruct) through
  the existing OpenRouter backend.
- Provider policy: FIXED COMPATIBLE PROVIDER, no fallback. First-party hosting
  is NOT a scientific requirement.
- Provider order (operationally test, predeclared): 1) DeepInfra (Turbo); 2)
  NovitaAI ONLY if DeepInfra fails the frozen operational contract.
- Freeze the first provider that passes; `allow_fallbacks=false`;
  `require_parameters=true`; persist provider identity in RunRecord/config hash.
- If the primary model fails BOTH providers: STOP; do not model-shop.
- The old first-party-DeepSeek rule and the DeepSeek V4 Flash / Qwen2.5-Coder-32B
  two-candidate gate are historical.

## 9.6 Non-study operational acceptance (three tasks, frozen)

- A1 structured ImpactPlan task (synthetic, not a scientific scenario);
- A2 exact-patch task;
- A3 agent-control/tool task.
Thresholds: 3/3 deterministic success; 3/3 first responses parse; 0
truncations; no provider fallback; usage recorded; every successful call
<= 120 s; median <= 60 s; <= 1 transient retry total (retry must succeed).

## 9.7 Gates before scientific runs

Six Pre-Benchmark gates (Dataset Validation, Prompt Validation, Pipeline Smoke
Test, Dry Run, Integration Test, Metric Verification) MUST reference
`scientific-wip-impactplan-v1`, then the Independent Audit, then full suite
once, then STOP before the 30 scientific cells.

