# Assumption, Decision, Obstacle, and Lesson Evolution

**Project:** Dependency-Aware Selective Regeneration Benchmark  
**Scientific version:** v0.9.22 (current)  
**Purpose:** Preserve the reasoning history behind the benchmark so a future maintainer or AI can understand not only *what* the project does, but *why* each major choice was made, what evidence invalidated earlier assumptions, and why the replacement decision is better.

> This file is an **assumption/decision learning ledger**, not a replacement for `DECISION_LOG.md`.
> `DECISION_LOG.md` records formal decisions. This file connects those decisions causally:
>
> `Assumption → Why it seemed reasonable → Obstacle/evidence → Revised decision → Lesson`.

---

## 1. Long-term and near-term goal

### Long-term scientific goal

Produce scientifically usable evidence comparing:

- a representative **iterative repository-agent workflow**, and
- the proposed **dependency-aware hybrid selective regeneration workflow**

under matched:

- repository state,
- requirement change,
- LLM,
- generation parameters,
- repair policy,
- validation policy,
- quality criteria,
- and end-to-end measurement boundary.

The intended result is not merely “fewer tokens”. Efficiency claims are valid only when correctness and quality are comparable.

### Current near-term goal

**CHANGED on 2026-09-04 by the SCIENTIFIC RESET DECISION (D040–D045).** The
old immediate goal (real 2×T4 preflight → 6-cell canary → stable tag → full
48-cell Pilot) is **PRIOR / SUPERSEDED**: Qwen2.5-Coder-14B + Kaggle 2×T4 is
RETIRED as the primary scientific inference path and the old 48-cell Pilot is
NOT launched or repaired. The current near-term goal is **SCIENTIFIC-MICROSTUDY-01**:

1. free the frozen preregistration (docs + DECISION_LOG D040–D045) — DONE 2026-09-04;
2. implement the minimal API seam + the 6-call NON-STUDY operational
   acceptance gate on two candidates (DeepSeek V4 Flash 0731, Qwen2.5-Coder-32B-Instruct);
3. freeze the ONE model/provider/settings chosen only by operational criteria;
4. frozen Todo evaluator/scenario audit (`todo-smoke-001/002/003`);
5. six Pre-Benchmark Validation gates;
6. independent Audit;
7. 30 real Todo runs (3 scenarios × 2 strategies × 5 reps) → first scientific
   results table → pre-registered GO/NO-GO → STOP.

NOT current targets: Kaggle Qwen14B engineering, the old 48-cell Pilot, Saleor,
djangoCMS implementation.

---

# 2. Scientific invariants that must not drift silently

Current full Pilot:

```text
repositories = todo, djangocms, saleor
scenarios = 12
strategies = iterative_repository_agent, selective
repetitions = 2
cells = 48
model = Qwen2.5-Coder-14B-Instruct
quantization = BNB-NF4
attention = SDPA, no math/eager fallback
GQA compatibility = repeat_kv_sm75
max attempts = 3
max completion tokens/call = 4096
Pilot workflow timeout = 1200 s
```

The 6-cell canary is an **operational gate**, not a scientific-matrix change.

---

# 3. Material assumption and decision evolution

The entries below cover the material assumptions that changed architecture, experiment design, deployment, release policy, or interpretation. Trivial implementation assumptions are intentionally excluded.

---

## A001 — The paper and frozen protocol should be the source of truth

### Initial assumption
The project should not be implemented ad hoc from code ideas. The research paper/protocol must define the experiment first.

### Why it was reasonable
Without a pre-registered protocol, implementation outcomes could influence experimental design and create post-hoc tuning.

### Obstacle
The original protocol draft contained contradictions in formulas, repair budgets, failure handling, determinism claims, monetary-cost reporting, and timing/cutoff rules.

### Revised decision
Freeze Protocol v1.0 only after researcher-approved decisions and explicit corrections (D006-D007).

### Lesson
**Freeze the scientific question before optimizing the software that answers it.**

Status: **KEPT, with corrections before freeze.**

---

## A002 — Local development and Kaggle execution should be intentionally separated

### Initial assumption
The local machine should implement/test the benchmark without installing the heavy Kaggle model stack or running local LLM inference.

### Why it was reasonable
Local CUDA/model downloads were expensive and unnecessary; real target behavior belongs on Kaggle.

### Obstacle
Local tests cannot prove:
- Kaggle GPU behavior,
- model loading,
- long-context attention behavior,
- real repository environment behavior,
- or service provisioning.

### Revised decision
Keep the local/Kaggle separation, but require target-shaped Kaggle/CI gates before launch readiness (D004, D020, D027+).

### Lesson
**Environment isolation is good, but local green is never evidence for target-runtime behavior.**

Status: **KEPT, strengthened with target proof.**

---

## A003 — Three repositories give a useful spectrum of repository complexity

### Initial assumption
Use:
1. controlled Django Todo,
2. django CMS,
3. a larger production repository.

ERPNext was considered for the third repository.

### Why it was reasonable
The experiment needed controlled, medium, and larger real-world repositories.

### Obstacle
ERPNext did not fit the intended architectural-boundary design as well as alternatives.

### Revised decision
Replace ERPNext with **Saleor Core**, and freeze:
- Todo,
- django CMS 5.0.0,
- Saleor Core 3.23.0.

This became 24 prepared scenarios initially, with the confirmatory Pilot using a frozen 12-scenario subset.

### Lesson
**Repository selection must serve the research construct, not merely maximize repository size.**

Status: **CHANGED: ERPNext → Saleor.**

---

## A004 — A single canonical project root is necessary

### Initial assumption
Existing directory copies could coexist during development.

### Why it seemed harmless
Early work was documentation-heavy and duplicate directories did not immediately break code.

### Obstacle
Phase 3.5 found stale duplicate `docs/` and `benchmark_data/` trees outside the Git repository.

### Revised decision
`project/` became the canonical source of truth; stale outer copies were removed or migrated (D009-D010).

### Lesson
**Multiple writable sources of truth create silent experimental drift.**

Status: **CHANGED to single canonical root.**

---

## A005 — Layered implementation before execution is worth the upfront structure

### Initial assumption
Domain models, loaders, backends, execution, evaluation, and statistics should be built in dependency order.

### Why it was reasonable
The benchmark has scientific contracts that are easier to test when the architecture separates them.

### Obstacle
This added planning/documentation overhead.

### Revised decision
Keep the layered architecture, but later adopt bounded feature closures instead of repeatedly expanding architecture work.

### Lesson
**Architecture is useful when it protects scientific contracts; architecture work becomes over-engineering when it no longer removes a concrete blocker.**

Status: **KEPT with stricter scope control.**

---

## A006 — The original “agent” arm was an adequate repository-agent baseline

### Initial assumption
The existing LLM “agent” strategy could serve as the main baseline for token-efficiency comparison.

### Why it seemed reasonable
It used an LLM to choose impact scope and was labeled as an agent.

### Obstacle
The arm-to-protocol audit showed:
- it was effectively single-shot scope prediction,
- several arms had LLM-design/wiring mismatches,
- and the measurement boundary excluded regeneration/repair.

This made the original token-efficiency comparison scientifically invalid.

### Revised decision
Research Design V2 (D023):
- main baseline = **iterative repository agent**,
- treatment = **hybrid selective**,
- matched shared regeneration executor,
- end-to-end accounting includes selection + regeneration + repair + validation,
- efficiency claims require comparable correctness/quality.

### Lesson
**A name is not an experimental construct. Audit what the code actually does.**

Status: **CHANGED materially.**

---

## A007 — One dependency graph could represent a mixed-repository Pilot plan

### Initial assumption
A graph built for the plan could be reused while executing multiple repositories.

### Why it seemed reasonable
The execution plan was treated as one benchmark batch.

### Obstacle
Pilot readiness dry-runs proved that a graph from one repository could not represent another repository's editable universe correctly.

### Revised decision
Build and select **one dependency graph per repository**; fail closed on mixed-repository misuse (D024).

### Lesson
**Repository identity is part of the dependency universe. Never share repository-local graph state across repos.**

Status: **CHANGED.**

---

## A008 — Dry-run/mock success was sufficient evidence that the execution path was wired correctly

### Initial assumption
A deterministic dry-run proving planned cells, IDs, strategy counts, and zero model calls was a strong readiness signal.

### Why it was reasonable
Dry-run catches matrix, configuration, identity, serialization, and many path errors cheaply.

### Obstacle
Real Kaggle execution repeatedly exposed failures impossible for a mock to prove:
- real Qwen failure propagation,
- graph/backend wiring,
- repository environments,
- GPU memory,
- target subprocess argv,
- services,
- and notebook runtime state.

### Revised decision
Dry-run remains mandatory, but is only one gate among:
- Dataset Validation,
- Prompt Validation,
- Pipeline Smoke,
- Dry Run,
- Integration,
- Metric Verification,
- target preflight,
- real canary.

### Lesson
**Dry-run proves topology, not viability.**

Status: **KEPT but demoted from “readiness proof” to one gate.**

---

## A009 — Component-mocked local tests were enough for Saleor preflight command correctness

### Initial assumption
Mocks that recognized expected command fragments adequately tested the Saleor preflight command.

### Why it seemed reasonable
The component under test appeared to be argument construction, not pytest itself.

### Obstacle
Real Kaggle v0.9.19 failed with pytest exit 5 because a second `-m pytest` was appended.  
The local fake runner was **false-green** because it matched substrings rather than exact argv.

### Revised decision
D027:
- exact command-vector contracts,
- exact node IDs,
- fail-closed duplicated `-m` detection,
- target-shaped Linux preflight before an `exec-ready` tag.

### Lesson
**Mocks must validate semantics, not merely recognize substrings.**

Status: **CHANGED testing policy.**

---

## A010 — The benchmark/model Python interpreter could validate all generated repositories

### Initial assumption
Using `sys.executable` for per-cell validation was sufficient.

### Why it seemed reasonable
Todo validation worked and using one interpreter simplified execution.

### Obstacle
Saleor and django CMS dependencies were intentionally isolated in repository-specific environments. Saleor also required frozen environment variables and its real validation runtime was far longer than 180 seconds.

### Revised decision
D028:
- explicit `--validation-python repo=path`,
- per-repository validation environments,
- `--validation-timeout 1800`,
- parent environment remains unmodified.

### Lesson
**Execution-runtime parity must include interpreter, environment, services, and time budget.**

Status: **CHANGED.**

---

## A011 — Successful model load + short generation was enough GPU proof

### Initial assumption
If Qwen 14B BNB-NF4 loaded on 2x T4 and generated a short probe, the model runtime was viable.

### Why it seemed reasonable
Load and short inference are the usual first memory checks.

### Obstacle
v0.9.21 failed on the 12,044-token long-context probe with an allocation matching the full quadratic float32 attention matrix.

### Revised decision
D029-D030:
- explicit `attn_implementation="sdpa"`,
- no math/eager fallback,
- attention-policy evidence,
- GQA T4 microprobe,
- `repeat_kv_sm75`,
- keep the real long-context probe.

### Lesson
**Short-context viability does not imply long-context viability. Test the actual scientific context regime.**

Status: **CHANGED runtime policy.**

---

## A012 — Passing real target preflight plus a 48-cell dry-run implied the Pilot was viable

### Initial assumption
After:
- all repository preflights PASS,
- model preflight PASS,
- long-context PASS,
- exact artifact dry-run 48/48,
- stable tag creation,

the real Pilot should be safe to launch.

### Why it was reasonable
Every known static/environment/runtime gate had passed.

### Obstacle
The 2026-08-30 real Pilot (`exp-20260830-134232`) produced:

```text
48 terminal
0 succeeded
48 failed
33 scientific_budget_exhausted
8 model_output
7 build
```

33 runs hit the 600-second workflow deadline. Resume also had a standalone `NameError`.

### Revised decision
D034:
- reject the run as scientific evidence,
- preserve it verbatim,
- retire (do not move/delete) the old stable tag as a launch candidate,
- separate terminality from viability,
- increase Pilot workflow timeout 600 → 1200,
- require a small **real canary before another 48-cell spend**.

### Lesson
**Preflight proves environment readiness; it does not prove end-to-end workflow viability.**

Status: **CHANGED strongly.**

---

## A013 — The 600-second Pilot timeout was adequate because it was pre-registered

### Initial assumption
Uniform 600 s per run was a reasonable preregistered Pilot workflow timeout.

### Why it was reasonable
A bounded uniform timeout avoids performance-driven tuning.

### Obstacle
The real Pilot showed 33/48 deadline-censored runs. Saleor alone had 15/16 budget-censored cells.

### Revised decision
Use 1200 s for the internal Pilot runtime contract while preserving the scientific version at v0.9.22 and documenting why the old run is rejected.

### Why changing it is scientifically defensible
The previous timeout prevented observing the workflow outcome at all; it acted as an engineering censoring defect rather than a meaningful experimental condition.

### Lesson
**Pre-registration protects against outcome-driven tuning, but a demonstrably censoring infrastructure limit must be corrected transparently, not worshipped.**

Status: **CHANGED 600 → 1200 with explicit provenance.**

---

## A014 — A two-repository canary was sufficient

### Initial assumption
A small canary using Todo + django CMS could cheaply exercise both strategies.

### Why it seemed reasonable
The canary was intended as a reduced operational sub-matrix, not a mini benchmark.

### Obstacle
Historical real evidence showed Saleor was the most timeout-sensitive repository: **15/16 cells budget-censored**.

The first D10 canary also contained an internal contradiction:
- `blast_radii=["localized"]`,
- while `djangocms-cross-007` is `cross_cutting`,
so the scenario was filtered out before execution.

### Revised decision
D035:
- include **all three repos**,
- one canonical scenario per repo,
- both strategies,
- one repetition,
- total = **6 cells**,
- blast radii include localized + cross-cutting.

### Lesson
**A viability canary must represent the highest-risk production path, not only the cheapest paths.**

Status: **CHANGED 2 repos/4 cells → 3 repos/6 cells.**

---

## A015 — Setting CLI default protocol to 1.1 was a safe way to update the Pilot

### Initial assumption
Changing the global CLI protocol default to 1.1 would naturally move the Pilot to the corrected runtime contract.

### Why it seemed reasonable
Pilot and canary were the active execution targets.

### Obstacle
The default leaked into smoke/research profiles whose protocol remained 1.0.

### Revised decision
D035:
- protocol is profile-derived:
  - pilot / pilot-canary → 1.1,
  - smoke / research / scientific-smoke-v1/v2 → 1.0,
- explicit CLI override always wins.

### Lesson
**A local contract change must not silently become a global default.**

Status: **CHANGED.**

---

## A016 — A CLI-level executable canary integration test was enough to prove the Kaggle canary path

### Initial assumption
If an integration test invokes the real benchmark CLI with `--profile pilot-canary` and gets the correct 6-cell topology, then the canary is executable.

### Why it seemed reasonable
This fixed the D10 failure where profile configuration itself could not resolve the requested scenarios.

### Obstacle
The 2026-09-01 Kaggle run proved a different layer could still fail:

```text
NameError: name 'SCRIPT_PATH' is not defined
```

All of these had already passed:
- artifact verification,
- repository snapshots,
- Saleor PostgreSQL/Redis bootstrap,
- Todo/django CMS/Saleor repo preflight,
- T4 GQA microprobe,
- Qwen 14B BNB-NF4 load,
- long-context probe,
- generation-deadline probe,
- HF secret retrieval.

The failure occurred while *constructing* `canary_cmd`, before the canary subprocess or first canary model call.

### Root cause
D10 inserted `pilot-canary-cell` **before** the existing `dryrun-cell`.

The new cell used:

```python
str(SCRIPT_PATH)
```

but the definition remained downstream inside `dryrun-cell`:

```python
SCRIPT_PATH = CODE_DIR / "seven_arm_benchmark.py"
```

So the notebook had a hidden **execution-order dependency**.

### Why 2585 tests did not catch it
The test suite checked different layers separately:

1. notebook code cells compile with `ast.parse`;
2. expected notebook cell order exists;
3. canary cell contains the expected argv/validator markers;
4. the benchmark CLI itself can execute a dry-run canary.

None of those tests executed or modeled the **state produced by earlier notebook cells before entering `pilot-canary-cell`**.

Thus:
- CLI integration = green,
- notebook syntax = green,
- notebook structure = green,
- real notebook orchestration = broken.

### Revised decision (required D12)
Critical operational notebook cells must not depend on variables first defined in later cells.

For this bug, define/validate the benchmark script path **before the canary** (single canonical definition), and add a regression test proving the definition occurs before first canary use.

Do **not** redesign the notebook framework.

### Lesson
**Integration tests must cover the orchestration layer, not only the executable being orchestrated.**

Status: **INVALIDATED on 2026-09-01; D12 blocker.**

---

## A017 — Complete-file regeneration is sufficient for large generated files

### Initial assumption
The regeneration strategy could always rewrite an entire generated file, matching the monolithic arm's output semantics while preserving the selective budget.

### Why it seemed reasonable
Iterative regeneration had always produced complete files in local/dry-run tests, and exact-match editing was seen as unnecessary complexity.

### Obstacle
The 2026-09-02 real canary showed a 56k-char djangoCMS file consumed ~1154 s to emit only 1839 completion tokens; complete-file regeneration is O(file) in prompt/attention cost and blew the per-cell deadline and token budget. djangocms-cross-007 was deadline-censored.

### Revised decision (required D13 B1)
Introduce an exact-patch source editor (`<<<<<<< SEARCH … ======= … >>>>>>> REPLACE`, multi-block, fail-closed, exact string match, no regex/fuzzy) shared by BOTH strategies via `ExecutorConfig.exact_patch`. Both strategies now emit targeted patches, not wholesale file rewrites, so large files no longer dominate the prompt.

### Lesson
**Complete-file edit cost grows with file size; exact-patch editing makes cost proportional to the change, not the file.**

Status: **CHANGED on 2026-09-02; D13 B1 (done).**

---

## A018 — The iterative agent may plan its own source edits under the same token cap

### Initial assumption
One completion-token allowance per call (the source-edit cap) is enough to bound an agent's control-plane reasoning and its actual code edits together.

### Why it seemed reasonable
The plan/analysis text and the emitted code share one model call, so a single cap seemed natural.

### Obstacle
On the 2026-09-02 canary, the agent's control-plane reasoning (impact analysis, plan revision) consumed completion budget that large-file regeneration then lacked, contributing to censored/under-length outputs.

### Revised decision (required D13 B2)
Separate the **agent-control-plane** output cap (`AGENT_CONTROL_MAX_COMPLETION_TOKENS = 512`) from the **source-edit** cap. `control_cap = min(max_completion_tokens_per_call, AGENT_CONTROL_MAX_COMPLETION_TOKENS)` is applied to `analyze_impact` and `revise_plan`; the source-edit allowance is unchanged.

### Lesson
**Control-plane reasoning and production code edits need independent token budgets, or reasoning starves the edit.**

Status: **CHANGED on 2026-09-02; D13 B2 (done).**

---

## A019 — Migration execution is environment-agnostic

### Initial assumption
A migration directory JSON field and environment-agnostic command targeting were enough; the executor did not need to know which repository a migration belongs to.

### Why it seemed reasonable
The Todo/django CMS/Saleor repos share a Django-style migration layout.

### Obstacle
Migrations must run inside the correct repository working tree against the correct `validation_python`; environment-agnostic targeting risks running an interpreter/env that does not match the repository.

### Revised decision (required D13 B3)
Add `migration_directory: str = "todo/migrations"` to `Scenario` and thread it through `run_post_generation_command`. The per-repo `validation_python` binding (repository-aware interpreter resolution) is a follow-up, deferred within this closure.

### Lesson
**Command execution must be repository-aware; a shared default directory is a stopgap, not the full binding.**

Status: **PARTIALLY CHANGED on 2026-09-02; D13 B3 (core field + threading done, per-repo interpreter binding deferred).**

---

## A020 — All 12 Pilot scenarios are semantically executable on the pinned base repos

### Initial assumption
The pinned base repositories already satisfy every hidden capability a Pilot scenario needs to run, so a fail-closed executability gate was unnecessary.

### Why it seemed reasonable
Local and dry-run execution never exercised a real failure of a hidden assertion against the frozen base.

### Obstacle
B4 analysis found scenarios that cannot run on the pinned base as-is: todo-loc-001's hidden priority-filter test needs an amended/validated expectation, saleor-loc-002 requires `is_featured` absent from the pinned base (must fail closed), and saleor-cross-007 needs a create capability. Untested, these scenarios silently produce no-path-selection or false-terminal outcomes.

### Revised decision (required D13 B4)
A fail-closed semantic-executability gate across all 12 Pilot scenarios (B4.1 todo-loc-001 hidden test, B4.2 saleor-loc-002 `is_featured`, B4.3 create capability). **Not implemented in this D13 closure; recorded as a deferred known-incomplete with explicit rationale** to keep the artifact/closure unambiguous about what is and is not proven.

### Lesson
**Scenario coverage must include a fail-closed executability check against the exact pinned base, or hidden missing-capability scenarios silently fail.**

Status: **KNOWN-INCOMPLETE / deferred on 2026-09-02; D13 B4 not implemented (see WORK STATE).**

---

## A021 — Protocol 1.1 remains the correct Pilot runtime contract after the canary failure

### Initial assumption
After the 2026-09-02 canary exposed production-scale execution defects (deadline censoring, oversized-file regeneration, build-in-completion failures), the Pilot runtime protocol 1.1 was still correct.

### Why it seemed reasonable
The canary failures looked like per-scenario execution defects, not a systemic contract problem.

### Obstacle
The defects (deadline censoring, token-budget starvation, complete-file O(file) cost) indicate the Pilot runtime contract should be tightened to a corrected protocol to reflect the production-grade execution semantics (exact-patch editing, separated budgets, repository-aware migrations).

### Revised decision (required D13 protocol bump)
Advance **Pilot-only** protocol 1.1 → 1.2: `resolve_profile_protocol` returns 1.2 for `pilot`/`pilot-canary`; preflight validators (preflight.py:1243 and 1711), `configs/pilot.yaml`, `pilot_validation_commands.yaml`, and the canary contract are bumped. Non-Pilot profiles stay 1.0; generic "1.1" source defaults not Pilot-coupled are left intact.

### Lesson
**A changed runtime contract must be versioned explicitly for the profile it governs, and preflight validators must be moved in lockstep.**

Status: **CHANGED on 2026-09-02; D13 protocol 1.1→1.2 (Pilot-only).**

---

## A022 — Long-context attention memory PASS implies scientific throughput viability

### Initial assumption
Passing the real 2×T4 12k long-context probe (Qwen 14B, SDPA no-math, 12044 tokens in ~29 s with the 64-token probe) meant the Qwen14B/T4 path could deliver scientific results within a usable wall-clock and budget envelope.

### Why it seemed reasonable
The memory closure (D013-D013R2 line) proved the 12k prompt could be processed without the CUDA OOM; the engineering blockers looked closed.

### Obstacle
The real 48-cell Pilot (`exp-20260830-134232`) still finished 48/48 terminal failures in ~23,610 s with 293 model calls and 820,631 tokens: 33 runs were killed at the deadline and the iterative agent repeatedly ran out to "no paths selected". Memory viability ≠ throughput/cost viability; the 29 s prefill is a small part of sustained multi-turn generation against large test repos.

### Revised decision (required D040)
Retire Qwen2.5-Coder-14B + Kaggle 2×T4 as the primary scientific inference path; all Qwen14B/T4 results are **engineering feasibility evidence**, not scientific evidence. Move the first scientific milestone to a Todo-only correctness-first micro-study on a frozen, operationally accepted path.

### Lesson
**A memory-prefill PASS is a necessary condition, not a scientifically sufficient one; throughput, budget and failure rate are viability properties.**

Status: **CHANGED on 2026-09-04; D040 (insight feeds D041/D042).**

---

## A023 — Exact-patch source editing alone solves the large-repo runtime problem

### Initial assumption
The D13 B1 exact-patch SEARCH/REPLACE editing fix (which removed complete-file O(file) regeneration) would make the Qwen14B/2×T4 path fast enough on large repositories.

### Why it seemed reasonable
The 2026-09-02 canary showed complete-file regeneration consuming ~1154 s for one django CMS file; exact-patch removes that specific cost.

### Obstacle
Exact-patch is an editing-format fix; it does not change the model's sustained generation speed, the agent's multi-turn search, or the per-turn latency on two T4s. The old 48-cell evidence still showed deadline-censored runs and path-explosion even before/independent of file-size per call.

### Revised decision (required D041, D042)
Do not attempt to force the old large-repo matrix onto the 14B/2×T4 track. The scientific micro-study runs on a Todo-only, correctness-first design on an operationally accepted path; the large-repo runtime question is deferred, not solved by a format change.

### Lesson
**A single-mechanic fix is not a runtime fix; production-scale runtime is a whole-path property (model, latency, search behavior, repo size).**

Status: **CHANGED on 2026-09-04; D042.**

---

## A024 — Repository profile and presence in the Pilot imply a meaningful dependency graph

### Initial assumption
Because django CMS and Saleor were pinned repositories in the Pilot, their strategy-visible dependency graphs were usable evidence for a dependency-aware treatment claim.

### Why it seemed reasonable
Repository complexity (three repos) was treated as a proxy for graph richness.

### Obstacle
The executed runs produced empty/fallback dependency-graph observations in the large repos — the extractor did not actually establish dependency edges in those cases. An empty graph produced by a failed/degraded extraction is NOT equivalent to a verified empty graph; claiming dependency-aware behavior on fallback-empty evidence would be invalid.

### Revised decision (required D045)
**verified-empty** (extractor ran, genuinely no edges) ≠ **fallback-empty** (extraction did not run / degraded). Only verified-empty may remain as a possible low-information observation; fallback-empty is NOT eligible for a dependency-aware treatment claim. Todo (real graph with edges) is the scientific venue for now; djangoCMS participation is conditional on a real reproducible graph.

### Lesson
**A repository's presence is not a dependency-graph fact; graph eligibility must be proven by the extractor ran correctly, not inferred from the repo roster.**

Status: **CHANGED on 2026-09-04; D045.**

---

## A025 — Engineering execution (preflight/canary/dry-run mechanics) implies scientific correctness

### Initial assumption
Once the exact artifact passed repo preflight, dry-runs 48/48, and the mechanics kept running, a real execution would produce evaluator-passed scientific results.

### Why it seemed reasonable
Every engineering gate (G1-G6) was green and the pipeline "ran".

### Obstacle
The only fully permitted real 48-cell Pilot completed 48/48 with **0 succeeded / 0 evaluator-passed**, and the real canary 6/6 also failed. Operational completion (pipeline runs to a terminal state) is not scientific validity (the requirement-change was not correctly handled).

### Revised decision (required D040, D043)
Separate terminality from viability (D10 already did this in the validator); the scientific evaluation is correctness-first with pre-registered thresholds (D043). Engineering gate success must never be reported as scientific success.

### Lesson
**Operational completion and scientific correctness are different observables; only the evaluator-passed rate answers the scientific question.**

Status: **CHANGED on 2026-09-04; D043.**

---

## A026 — Free Kaggle GPUs mean the lowest effective cost for the primary path

### Initial assumption
Running on free Kaggle 2×T4 hardware made the Qwen14B track the cheapest provider option, so cost favored keeping that path.

### Why it seemed reasonable
The GPU is free; the alternative pays per token/call.

### Obstacle
Free GPU cost is offset by wall-clock, reproducibility risk, session/timebox fragility, engineering overhead per launch, and the observed 100% failure cost of the old matrix. A per-run cost comparison must include the full operational cost (launch, retries, failures, wall-clock), not the sticker GPU price.

### Revised decision (required D041)
The model/provider gate scores **normalized cost per candidate** among its operational criteria — including reproducibility and failure overhead, not just sticker price — and the chosen path is frozen. no a priori model/preset decision.

### Lesson
**Cost is an expected operational cost, not a sticker price; free hardware can be the expensive path when failures dominate.**

Status: **CHANGED on 2026-09-04; D041.**

---

## A027 — temperature=0 makes the runs deterministic, so few repetitions suffice

### Initial assumption
Because earlier scientific settings froze temperature=0, a single or double repetition would be enough to claim reproducibility.

### Why it seemed reasonable
Temperature=0 is widely treated as deterministic sampling.

### Obstacle
Real runs still vary materially (ordering, tokenization, non-deterministic kernels, multi-turn search, repair decisions). The old double-repetition 48-cell plan was not rejected for determinism; and the new study's thresholds (`>=4/5`) explicitly require five independent repetitions even at temperature=0.

### Revised decision (required D042, D043)
Freeze **5 independent repetitions per cell** regardless of temperature=0; efficiency and correctness are reported across the 5 reps with medians and raw values, and thresholds are stated on the pass counts.

### Lesson
**temperature=0 is not a determinism guarantee; repetition is a preregistered design property, not a knob to save cost.**

Status: **CHANGED on 2026-09-04; D042.**

---

## A028 — Model/provider may be chosen from within the scientific study as it runs

### Initial assumption
Picking the best-working model from among available options during (or just after) a few scientific runs is acceptable tuning.

### Why it seemed reasonable
Running pilots and keeping what works is a common empirical workflow.

### Obstacle
Selecting the model after seeing scientific outcomes lets model choice be tuned on the target data and turns confirmatory go/no-go claims into exploratory ones (anti-cherry-picking violation; Door 1 of the Go/No-Go doctrine).

### Revised decision (required D041)
The model/provider/settings are chosen ONLY by a **NON-STUDY operational acceptance gate** (6 throwaway non-scientific calls on two candidates) using pre-registered operational criteria; the winner is frozen before the first scientific call. Scientific scenario data never feeds model selection.

### Lesson
**Model selection must be operationally determined before scientific outcomes exist, or the study is no longer confirmatory.**

Status: **CHANGED on 2026-09-04; D041.**

---

## A029 — The regeneration executor may read scenario gold expected-actions, and counts suffice for preservation

### Initial assumption
Threading `scenario.expected_actions` into the regeneration scenario context
(as `Expected action for this file` in the generation/repair prompt) and
scoring preservation/predicted-impact from persisted counts alone is an
acceptable measurement design.

### Why it seemed reasonable
The executor previously used gold expected-actions to drive exact-patch mode and
scope checks, and the RunRecord had no per-path evidence fields.

### Obstacle
The independent audit (exact export `project-2026-09-04-2352.zip`) verified this
is gold-label leakage for a scientific study: the post-selection executor can
receive gold expected-action information from the scenario YAML. Persisted
counts cannot reconstruct impact recall or preservation: they do not record the
actual predicted path/action map nor the actual changed source paths.

### Revised decision (required D046 / PA-001)
Scientific prompts never receive `scenario.expected_actions` or
`expected_artifact_instructions`; edit-action semantics come from
`RegenerationPlan.actions`; generic Python contract guards stay active without
gold context. Per-run evidence is mandatory: `predicted_actions: dict[str,str]`
and `changed_artifact_paths: list[str]` survive RunRecord → RunRecordData →
JSONL. Migrations are shared-executor obligations scored separately. The
five-file Todo universe is the clean scoring set.

### Lesson
**Evidence produced by the study must be exactly reconstructable from the
persisted record; gold labels can never reach the executor. "Preserve" is an
actual-behavior claim, not a model's word.**

Status: **CHANGED on 2026-09-05; D046.**

---

# 4. Latest real Kaggle attempt — 2026-09-01

## What passed

Real target evidence from the uploaded run:

```text
Repository preflight: PASS
  Todo: PASS
  django CMS: PASS
  Saleor: PASS

Saleor PostgreSQL: PASS
Saleor Redis-compatible service: PASS

T4 SDPA GQA microprobe: PASS on both GPUs

Qwen 14B BNB-NF4 model load: PASS
device_map GPU-only: PASS
short generation probe: PASS
generation-deadline probe: PASS
long-context probe:
  prompt_tokens=12044
  elapsed=29.182s
  PASS

HF_TOKEN retrieval: PASS
```

## What failed

The first real canary notebook cell:

```text
NameError: name 'SCRIPT_PATH' is not defined
```

## Scientific contamination

None.

The error occurred before `_run_live(canary_cmd, ...)`.

Therefore:

```text
real canary model calls = 0
real canary RunRecords = 0
real canary scientific result = NOT STARTED
```

This is an engineering orchestration failure, not a failed scientific canary.

---

# 4b. Latest real Kaggle attempt — 2026-09-02 (pilot-canary)

## What happened

A real Pilot canary was launched on 2026-09-02 from the D12 candidate
(`v0.9.22-d12-candidate`, source `84acb8bb`, profile `pilot-canary`,
protocol 1.1, model `qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`,
hardware 2× Tesla T4).

```text
planned = 6, completed = 6, failed = 6, succeeded = 0
wall time ≈ 5525 s
```

Breakdown:
- 4 deadline-censored (killed at the workflow deadline),
- 2 Todo build-in-completion failures,
- 0 evaluator-passed.

## Root-cause blockers exposed (closed/flagged in D13)

| Blocker | Evidence | D13 closure |
|---|---|---|
| Complete-file regeneration | djangoCMS used a 56k-char file consuming ~1154 s to emit only 1839 completion tokens | B1 exact-patch source editing (done) |
| Agent control-plane token starvation | completion budgets consumed by plan/analysis, starving the source edit | B2 `AGENT_CONTROL_MAX_COMPLETION_TOKENS = 512` (done) |
| Environment-agnostic migrations | migrations not bound to the correct repo/interpreter | B3 `migration_directory` field + threading (core done; per-repo interpreter binding deferred) |
| Missing scenario executability | scenarios can't run on the pinned base (hidden missing capability) | B4 fail-closed executability gate (deferred, known-incomplete) |
| Stale Pilot runtime contract | deadline censoring + oversized-file + build-in-completion indicate contract gap | Pilot protocol 1.1→1.2 (done) |

## Scientific contamination

None. No scientific claim is changed by this closure; v0.9.22 scientific inputs
are unchanged. The canary itself did not pass, so **no 48-cell Pilot launch and
no stable release tag** is authorized by this closure.

---

# 5. Obstacle → correction summary

| Obstacle | Incorrect/insufficient assumption | Correction |
|---|---|---|
| Duplicate project trees | Multiple copies can coexist | Single canonical Git root |
| Original agent not true iterative baseline | Label implies construct | RD-V2 iterative repository-agent baseline |
| Measurement excluded regen/repair | Scope-selection tokens enough | End-to-end measurement boundary |
| One graph for mixed repos | Plan-level graph is reusable | Per-repository dependency graphs |
| Real Qwen wiring failures | Mock smoke enough | Real Kaggle smoke |
| Saleor pytest exit 5 | Substring mock validates argv | Exact argv + target-shaped gate |
| Wrong per-cell interpreter/env | `sys.executable` enough | Per-repo interpreters/env |
| Saleor >180s validation | Generic validation timeout enough | Explicit 1800s validation budget |
| 12k prompt CUDA OOM | Short generation implies memory viability | Explicit SDPA no-math + long-context gate |
| T4 GQA concerns | Generic SDPA proof enough | Real per-GPU GQA microprobe |
| 48/48 real Pilot failed | Preflight + dry-run imply viability | Real canary before full Pilot |
| 600s censored 33/48 | Pre-registered timeout must never change | Transparent 1200s internal correction |
| Canary omitted Saleor | Reduced matrix need not include all repos | 6-cell all-repo canary |
| Canary blast radius contradiction | Profile unit assertions enough | Executable CLI topology test |
| Protocol 1.1 leaked globally | Global default is harmless | Profile-derived protocol |
| `SCRIPT_PATH` NameError | CLI integration proves notebook path | Notebook execution-order regression test |
| Complete-file regeneration violates deadline/budget | Whole-file edit is always safe | Exact-patch SEARCH/REPLACE editing (B1) |
| Agent reasoning starves the edit | One token cap is enough | Separate 512 control-plane cap (B2) |
| Migrations environment-agnostic | Shared default dir is enough | Repository-aware `migration_directory` (B3) |
| Scenarios silently unexecutable on pinned base | Coverage implies executability | Fail-closed executability gate (B4, deferred) |
| Pilot runtime contract stale after canary | 1.1 still correct | Pilot-only protocol 1.1→1.2 |
| No scientific result after 48/48 + 6/6 failures | Engineering execution implies scientific correctness (A025) | Retire Qwen14B/T4 track; correctness-first micro-study (D040) |
| Model choice could tune on outcomes (A028) | Model picked within the study is acceptable | 6-call NON-STUDY operational acceptance gate before any scientific run (D041) |
| Large-repo throughput threats (A023) | Single-mechanic fix solves runtime | Todo-only correctness-first 30-run study; large-repo deferred (D042) |
| Post-hoc thresholds | Thresholds may follow observed results | GO/NO-GO thresholds frozen BEFORE model calls (D043) |
| Scenario IDs chosen after outcomes | Outcome-based scenario selection is fine | `todo-smoke-001/002/003` pre-registered by blast-radius class (D044) |
| fallback-empty graph treated as empty (A024) | Repo presence implies a meaningful graph | verified-empty ≠ fallback-empty; graph eligibility proven (D045) |

---

# 6. Testing doctrine learned from the project

A high test count is useful but not sufficient.

Every launch-critical feature should have four layers:

```text
1. Unit contract
2. Executable component integration
3. Orchestration/integration in the exact deployment surface
4. Real target canary when the target cannot be reproduced locally
```

For notebooks specifically:

```text
Syntax-valid cell
    !=
Correct notebook execution state
```

A new operational cell must either:
- be self-contained for critical paths, or
- have an explicit tested upstream-variable contract.

---

# 7. Anti-over-engineering rule

A new task is justified only if it does one of the following:

1. removes a demonstrated blocker;
2. protects scientific validity;
3. makes exact target execution reproducible;
4. fixes evidence/provenance integrity.

Do **not** open a new phase merely to:
- rename,
- refactor unrelated code,
- increase test count,
- rewrite historical documentation,
- generalize a one-line notebook dependency into a new framework.

For the current `SCRIPT_PATH` bug, the correct fix is a **small notebook orchestration correction + regression test + truth-only documentation update**.

---

# 8. Current Go/No-Go state

**CHANGED on 2026-09-04 by the SCIENTIFIC RESET DECISION (D040-D045).**

```text
Scientific reset decision (D040-D045):     FROZEN (2026-09-04)
Qwen2.5-Coder-14B + Kaggle 2x T4 primary path: RETIRED (engineering evidence only)
Old 48-cell Pilot authorization:           NO-GO (not launched, not repaired)
Model/provider selection gate:             PENDING (6-call NON-STUDY gate, 0 calls made)
Frozen model/provider:                     NONE YET (must be operationally chosen + frozen)
Pre-Benchmark Validation gates (new path): PENDING (not yet run for the new scientific path)
Todo evaluator/scenario audit:             PENDING (mandatory before scientific runs)
SCIENTIFIC-MICROSTUDY-01 runs:             PENDING (0 real scientific calls)
First scientific results table:            PENDING
Study GO/NO-GO:                            PENDING (thresholds frozen in D043)
```

Required next action:

```text
preregistration froze + pushed (this closure)
-> minimal API seam (NON-STUDY only, no scientific data)
-> 6-call operational acceptance gate (2 candidates, operational criteria only)
-> freeze ONE exact model/provider/settings
-> Todo evaluator/scenario audit
-> six Pre-Benchmark Validation gates
-> independent Audit
-> 30 real Todo runs (3 scenarios x 2 strategies x 5 reps)
-> first scientific results table + pre-registered GO/NO-GO
-> STOP
```

PRIOR (2026-09-01/09-03, superseded by the 2026-09-04 decision):

```text
D11 code/config scientific contract:     PASS
D11 exact artifact topology:             PASS
Real target repository/model preflight:  PASS
D12 notebook orchestration fix:          PASS
Real pilot-canary execution (2026-09-02):FAILED 6/6 (deadline + build-in-completion)
Cause:                                    production-scale execution defects (B1-B4)
D13 closures (B1 exact-patch, B2 caps, B3 migrations):  DONE
D13 protocol 1.1 -> 1.2 (Pilot-only):    DONE
D13 B4 semantic executability gate:      DEFERRED (known-incomplete)
D13R1/R2 canary readiness + hotfixes:    DONE (H1-H4; CANARY_LAUNCH_BASIS=YES)
Scientific canary evidence:              NONE (canary did not pass)
Full 48-cell Pilot authorization:        NO-GO (superseded entirely by the 2026-09-04 decision)
```

Do not launch the 48-cell Pilot (it is retired and NOT a launch basis); do
not reopen D14/D15 timeout/infrastructure work; do not run any scientific
model call until the model/provider gate has selected and frozen a path.

---

# 9. Formal decision-log mapping

This learning ledger is grounded in the project's formal decisions:

- D001-D005: bootstrap/environment/input truth
- D006-D007: protocol draft/freeze
- D008: repository and scenario selection
- D009-D010: architecture and canonical structure
- D011-D019: benchmark core/evaluation implementation
- D020: real Kaggle smoke
- D021-D022: canonical bundle + early CLI NameError lesson
- D023: Research Design V2
- D024: multi-repository Pilot readiness
- D025: Pilot execution preregistration
- D027: Saleor exact-argv/target-preflight lesson
- D028: per-cell validation runtime parity
- D029-D030: long-context SDPA/GQA runtime closure
- D031-D033: Kaggle/GitHub boundary, notebook navigation, real T4 preflight and old stable tag
- D034: all-failed real Pilot rejection and viability correction
- D035: Saleor-inclusive 6-cell canary + protocol correction
- D036: notebook execution-order failure and D12 correction (SCRIPT_PATH defined once)
- D13 (this closure): 2026-09-02 canary production-scale execution defects — exact-patch editing (B1), separate agent-control cap (B2), repository-aware migration directory (B3), Pilot-only protocol 1.1→1.2, `v0.9.22-d13-candidate` supersedes D12; B4 executability gate deferred (known-incomplete).
- D13r1: canary launch-readiness finalizer — F1 semantic-executability gate WIRED into the real pilot/pilot-canary PRE-MODEL launch path (full 48-cell Pilot is NOT a launch basis while any scenario is semantically unexecutable; canary is a launch basis after a real target pass); F2 migration metadata ONLY on the 3 canary scenarios; F3 migration execution decoupled from `evaluator_asset`; F4 exact-patch repair-prompt contradiction removed; F5 `exact_patch` + `agent_control_max_completion_tokens` in frozen config/provenance identity. `v0.9.22-d13r1-candidate` (archive `9f120412…`, source `6bc946a`) supersedes `v0.9.22-d13-candidate`; CANARY_LAUNCH_BASIS=YES, FULL_48_LAUNCH_BASIS=NO.
- D13R2 (last canary hotfix, same D13 line, no D14): H1-H4 audited canary defects closed — the 3 canary scenarios now carry COMPLETE executable migration metadata (`post_generation_command` `python manage.py makemigrations todo|cms|product --noinput` + `require_new_migration: true`; was empty/False); the semantic gate PROVES migration executability via the frozen `_CANARY_MIGRATION_FIXTURES` map (fail-closed on any mismatch); migration generation receives the frozen `validation_env` (FunctionalValidator merge semantics, parent `os.environ` never mutated); `_compute_config_hash` now includes `exact_patch` + `agent_control_max_completion_tokens`. `v0.9.22-d13r2-candidate` (archive `65269528…`, source `fc1c7c8`) supersedes `v0.9.22-d13r1-candidate`; CANARY_LAUNCH_BASIS=YES, FULL_48_LAUNCH_BASIS=NO.
- D040 (2026-09-04, SCIENTIFIC RESET): retire Qwen2.5-Coder-14B + Kaggle 2×T4 as the primary scientific inference path; old 48-cell Pilot not launched/repaired; all D01–D13R2 evidence stays immutable engineering feasibility evidence (A022-A025).
- D041 (2026-09-04): mandatory 6-call NON-STUDY operational acceptance gate (DeepSeek V4 Flash 0731 vs Qwen2.5-Coder-32B-Instruct, neither pre-selected; operational criteria only) then freeze ONE exact model/provider/settings before scientific runs (A026-A028).
- D042 (2026-09-04): freeze the scientific micro-study design — `todo-smoke-001/002/003` × 2 strategies × 5 reps = 30 attempted runs; correctness → preservation → impact recall → efficiency (descriptive only).
- D043 (2026-09-04): freeze GO/NO-GO thresholds BEFORE model calls (G1 correctness ≥4/5 and not worse than Agent by >1 pass; G2 preservation ≥4/5; G3 impact recall ≥4/5; study GO = all 3 clear G1 + G2 + ≥2/3 clear G3).
- D044 (2026-09-04): freeze scenario IDs `todo-smoke-001` (localized) / `todo-smoke-002` (moderate) / `todo-smoke-003` (cross_cutting) before scientific inference, with mandatory pre-run evaluator audit.
- D045 (2026-09-04): graph eligibility rule — verified-empty ≠ fallback-empty; only verified-empty may be a low-information observation; fallback-empty is NOT eligible for a dependency-aware treatment claim.
- D046 (2026-09-05): freeze PA-001 implementation clarification — five-file Todo source universe; migrations as shared-executor obligations scored separately; mandatory `predicted_actions` + `changed_artifact_paths` per-run evidence; fixed-provider/no-fallback identity (`openrouter:<model>@<provider>` reconfigures config_hash/Run IDs); gold expected-actions isolated from scientific prompts with `RegenerationPlan.actions` driving edit semantics; workflow timeout 900 s / source cap 4096 / agent cap 512 / max attempts 3 / no new token ceiling / provider-reported usage is the metric of record; first-party DeepSeek provider mandatory for candidate A (A029).

---

# 10. Maintenance rule for future AI/operators

Whenever an assumption is invalidated, do not only patch code.

Update this file with:

```text
Assumption:
Why it was reasonable:
Evidence that broke it:
Old decision:
New decision:
Why the new decision is better:
Scientific impact:
Regression test added:
Evidence required before closure:
```

That makes project history reusable knowledge instead of a sequence of unexplained patches.
