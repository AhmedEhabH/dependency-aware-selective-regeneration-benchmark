# Precision-Safe Acceptance — Feasibility Analysis + Protocol Freeze (2026-09-18)

**Mission:** PRECISION-SAFE ACCEPTANCE FEASIBILITY + PROTOCOL FREEZE
**Tier:** T3 (new acceptance/evaluation strategy; DEVELOPMENT analysis; ZERO API — no
model/API call is made by this mission)
**Inputs:** the frozen Stage-4 300-call record
(`research/bounded-semantic-expansion/pilot_results.json`, `pilot_registration_freeze.json`)
+ frozen DEV task features (`benchmark.recall.data.load_dev_tasks`).
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Stage-4 verdict:** `BOUNDED_SEMANTIC_NEGATIVE_FROZEN` — **UNCHANGED, NOT reinterpreted.**

---

## A. IMPACT DECLARATION (written first, before any modification)

This mission is classified under the **current repository protocol**
(`docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md`), whose CURRENT PHASE is
**Repository change localization / impact selection**. The mission does NOT fall
under an older generic five-dimension localization protocol.

Primary evaluation dimensions for this mission:

1. **Impact Correctness** — candidate acceptance precision, final file-level
   P/R/F1/FNR, omission recovery (ORR), fold/task stability.
2. **Efficiency** — ZERO API by mandate; all analysis is deterministic
   recomputation over already-recorded evidence; the future-pilot cost model is
   estimated from the frozen Stage-4 ledger.

Conditional dimension:

3. **Architecture / protocol compliance** — the proposed RANK → VERIFY →
   VARIABLE-ACCEPT architecture is assessed for protocol compliance
   (inspection depth K conceptually separated from the number of accepted
   additions).

Deferred until downstream regeneration (NOT claimed here):

4. **Functional Correctness**.
5. **Preservation / regression correctness**.

Scientific discipline (frozen): the Stage-4 negative is immutable; every new
finding is **POST-HOC DEVELOPMENT analysis** and is NOT retroactively inserted
into the preregistered Stage-4 hypothesis. No sealed set is opened.

---

## B. Stage-4 negative verified from raw records

| Quantity | Value | Frozen source |
|---|---:|---|
| Calls | 300 (Arm A 240 + Arm B 60) | ledger |
| Tokens | 106,325 | ledger |
| Cost | $0.0444 | ledger |
| Wall | 553.6 s | ledger |
| Arm A valid | 240 / 240 | records |
| Arm B valid | 54 / 60 (6 schema-invalid, fail-closed, no retries) | records |
| Recomputed ORR@5 djangoCMS | Arm A 0.1111 / Arm B 0.2500 | raw records |
| Recomputed ORR@5 Saleor | Arm A 0.3344 / Arm B 0.3574 | raw records |

The recomputed ORR@5 values match the frozen Stage-4 metrics JSON exactly
(budget ceilings respected, `budget_respected == true`). The verdict
`BOUNDED_SEMANTIC_NEGATIVE_FROZEN` remains immutable. No Stage-4 file was
modified.

---

## C. Failure anatomy — ZERO API, from the 300 recorded calls

All numbers below are deterministic recomputations from the frozen records
(machine-readable: `reports/precision_safe_feasibility_metrics.json`).

### C.1 Arm-B candidate precision by semantic rank position (cumulative)

The model's ordered (accepted) list is NOT strongly precision-sorted. On the
valid Arm-B calls:

| Rank | djangoCMS cum-prec | Saleor cum-prec | djangoCMS cum FN | Saleor cum FN |
|---:|---:|---:|---:|---:|
| 1 | 0.125 | 0.346 | 3 | 9 |
| 2 | 0.125 | 0.212 | 6 | 11 |
| 3 | 0.111 | 0.218 | 8 | 17 |
| 4 | 0.083 | 0.202 | 8 | 21 |
| 5 | 0.093 | 0.177 | 11 | 23 |
| 10 | 0.093 | 0.153 | 15 | 31 |

Saleor's rank-1 precision is respectable (0.346) and decays monotonically;
djangoCMS precision is flat-low throughout. The semantic order carries FNs
marginally higher but never precision-sorts the list.

### C.2 Cumulative ORR and candidate precision at frozen B (pooled over all 30 records)

| Repo | B | Arm A ORR | Arm B ORR | Arm A cand-prec | Arm B cand-prec |
|---|---:|---:|---:|---:|---:|
| djangoCMS | 1 | 0.022 | 0.082 | 0.167 | 0.185 |
| djangoCMS | 3 | 0.022 | 0.164 | 0.051 | 0.124 |
| djangoCMS | 5 | 0.111 | **0.250** | 0.143 | **0.105** |
| djangoCMS | 10 | 0.139 | 0.290 | 0.086 | 0.098 |
| Saleor | 1 | 0.135 | 0.185 | 0.368 | 0.310 |
| Saleor | 3 | 0.229 | 0.295 | 0.263 | 0.230 |
| Saleor | 5 | 0.334 | **0.357** | 0.256 | **0.179** |
| Saleor | 10 | 0.341 | 0.487 | 0.141 | 0.152 |

Macro ORR reproduces the frozen metrics exactly at every B (verification flag
`macro_orr all match frozen: True`).

### C.3 FN recovery vs FP additions by rank (at B=5, pooled additions)

| Repo | Arm | FN added | FP added | accepted | cand-prec |
|---|---:|---:|---:|---:|---:|
| djangoCMS | A | 7 | 42 | 49 | 0.143 |
| djangoCMS | B | 14 | **119** | 133 | 0.105 |
| Saleor | A | 22 | 64 | 86 | 0.256 |
| Saleor | B | 26 | **119** | 145 | 0.179 |

Arm B approximately doubles FN recovery on djangoCMS (7→14) and slightly on
Saleor (22→26) but adds ~2.8× (dc) / ~1.9× (saleor) the false positives of
Arm A. The FP tail is the dominant Stage-4 failure.

### C.4/C.5/C.6 Source split — Route-B top-10 overlap vs reverse-1hop-only

At B=5, on the **27 valid Arm-B tasks** per repo:

| Repo | FN from top-10 | FN consumer-only | FP from top-10 | FP consumer-only |
|---|---:|---:|---:|---:|
| djangoCMS | 7 | 4 | 62 | 45 |
| Saleor | 19 | 4 | 66 | 41 |

- **Useful recovered FNs come from BOTH sources** (djangoCMS is balanced; Saleor
  FN recovery is dominated by the Route-B top-10 overlap).
- **The FP tail also comes from BOTH sources** (roughly 55–60% top-10, 40–45%
  consumer-only). No single pool source is the FP problem — the *acceptance
  layer* is.
- On Saleor, 19 of 26 recovered FNs sit inside the Route-B top-10 (where the
  frozen verifier decisions exist); the consumer-only source contributes
  little FN recovery there.

### C.7 Pool-size distribution

| Repo | min | max | at cap 40 | distribution |
|---|---:|---:|---:|---|
| djangoCMS | 10 | 40 | 21/30 | {10:6, 13:1, 25:2, 40:21} |
| Saleor | 36 | 40 | 29/30 | {36:1, 40:29} |

### C.8 Saleor pool-cap saturation at C=40

Saleor is essentially fully saturated: **29/30 tasks sit at the cap**. The full
(uncapped) Route-B-top-10 ∪ consumer union on the sampled tasks has
`mean ≈ 313, max ≈ 671` candidates — the cap was cost-necessary but is binding
on almost every Saleor task.

### C.9 FNs lost by the cap

| Repo | total FN (sampled) | FN in capped pool | FN in full union | FN lost by cap |
|---|---:|---:|---:|---:|
| djangoCMS | 61 | 32 | 42 | **10** |
| Saleor | 85 | 46 | 75 | **29** |

Cap-coverage curve (fraction of sampled FNs reachable in the pre-order):

| Cap | djangoCMS | Saleor |
|---|---:|---:|
| 40 | 0.525 | 0.541 |
| 80 | 0.656 | 0.600 |
| 120 | 0.689 | 0.694 |

The cap C=40 excludes **10 (djangoCMS) + 29 (Saleor)** FNs from the pool —
mechanism evidence that a larger pool cap is a real recovery lever.

### C.10/C.11 Valid vs schema-invalid output + failure taxonomy

- 240/240 Arm-A calls valid; **6/60 Arm-B calls schema-invalid** (3 djangoCMS +
  3 Saleor), recorded fail-closed with no retries.
- Failure taxonomy (all 6): **non-pool path** — the model emitted plausible
  paths that are NOT members of the presented pool (e.g.
  `cms/plugin_rendering.py`, `saleor/order/utils.py`). Zero content-parse
  failures, zero duplicates, zero transport failures; `finish_reason == stop`
  on all 6.
- **Important frozen-analyzer subtlety:** the Stage-4 pilot retains the
  pool-member *subset* of an invalid list in `per_b`, so the frozen metrics give
  schema-invalid calls **partial credit** in pooled candidate precision and
  naive-union F1. This muddies fail-closed semantics and is an engineering
  defect the future schema must eliminate.

### C.12 Task-level heterogeneity and frozen-fold direction (B=5)

Per-task ORR delta (Arm B − Arm A) at B=5:

| Repo | tasks | B>A | B<A | B=A | mean delta |
|---|---:|---:|---:|---:|---:|
| djangoCMS | 30 | 8 | 1 | 21 | +0.139 |
| Saleor | 30 | 7 | 3 | 20 | +0.023 |

Seeded 5-fold direction (frozen seed 20260918):

| Repo | fold fractions | positive folds |
|---|---:|---:|
| djangoCMS | [1.0, 1.0, 0.5, 1.0, 1.0] | 5/5 |
| Saleor | [1.0, 0.0, 0.5, 1.0, 0.0] | 3/5 |

Most tasks have zero recovery in both arms (the B=A mass is mostly 0-vs-0);
where Arm B differs it is usually positive.

### C.13 B=10 Saleor consistency (DEVELOPMENT motivation ONLY)

| Repo | Arm A ORR@10 | Arm B ORR@10 | Arm A prec | Arm B prec | folds positive |
|---|---:|---:|---:|---:|---:|
| djangoCMS | 0.139 | 0.290 | 0.086 | 0.098 | 5/5 |
| Saleor | 0.341 | **0.487** | 0.141 | 0.152 | **5/5** |

Saleor B=10: mean per-task delta **+0.146**, 10/30 tasks strictly positive,
0 fold-level regressions, 5/5 positive folds. This is **consistent recovery
growth** — and it is exactly the *inspection-depth* signal the mission asks
about: recovery keeps growing to B=10 while acceptance precision is already
poor at B=5. Conclusion for C.13: the B=10 observation **is consistent enough
to motivate a larger inspection depth K**, but NOT as a Stage-4 success and
NOT as a retroactive endpoint. It is labeled DEVELOPMENT motivation only.

---

## D. Decoupling inspection from acceptance

Stage-4's weakness was the forced identity:

```
semantic ranking → first B candidates → B additions   (accept exactly B)
```

The next protocol investigates:

```
expanded deterministic pool → semantic ranking → inspect bounded top-K
→ conservative verifier → ADD only verifier-approved candidates (0..K)
```

Two quantitative facts from the anatomy make this decoupling concrete:

1. **Recovery keeps growing to rank 10 while acceptance precision collapses**
   (C.1, C.13): Saleor cumulative FNs 9→31 from rank 1→10 (precision 0.35→0.15).
   Forcing acceptance at B=5 truncates useful recovery; forcing B=10 adds a
   huge FP tail. K must be allowed to exceed the accepted count.
2. **The accepted count must be allowed to be < K** (C.3): 87–91% of Arm-B
   accepted additions are FPs at B=5. A precision-safe layer that accepts only
   verifier-approved candidates naturally produces a variable accepted set.

**Definition (frozen for the next protocol):** K = inspection budget (the number
of semantically-ranked candidates the verifier may consider) is conceptually
separate from the number of accepted additions (0..K). A future method MUST be
allowed to inspect K candidates and add 0..K. Exactly-K acceptance is rejected
by design.

---

## E. Precision-safe acceptance feasibility — POST-HOC, ZERO API

**Label (frozen):** *POST-HOC DEVELOPMENT FEASIBILITY — NOT CONFIRMATORY
EVIDENCE.* Every number below is a mechanism diagnosis over the already-recorded
300 calls. No threshold was swept; exactly ONE principled rule family was
evaluated.

### E.1 The one principled family evaluated

**RANK → VERIFY → VARIABLE ACCEPT**, instantiated as: *accept candidate c iff c
is in the semantic top-K (Arm B ordered list) AND c is verifier-approved*. The
only verifier signal in the frozen record is the **Arm A B=10 `reconsider`
decision, which exists ONLY for the Route-B top-10 subset of each pool** — the
semantic rank covers the whole pool, the frozen verifier covers only 10 of up
to 40 pool candidates.

### E.2 Results at K ∈ {5, 10} (pooled over the 27 valid Arm-B tasks per repo)

| Repo | Rule K | cand-prec | macro ORR | naive F1 | accepted (mean/task) |
|---|---:|---:|---:|---:|---:|
| djangoCMS | 5 | 0.146 | 0.130 | 0.407 | 1.8 |
| djangoCMS | 10 | 0.143 | 0.148 | 0.400 | 2.1 |
| Saleor | 5 | 0.222 | 0.219 | 0.263 | 2.7 |
| Saleor | 10 | 0.213 | 0.274 | 0.273 | 3.5 |

### E.3 Matched-subset comparison (same 27 valid tasks; sparse / Arm A@5 / Arm B@5 / rule)

| Repo | sparse | Arm A@5 | Arm B@5 (take-first-5) | rule K=5 | rule K=10 |
|---|---:|---:|---:|---:|---:|
| djangoCMS | 0.450 | 0.414 | 0.324 | 0.407 | 0.400 |
| Saleor | 0.159 | 0.287 | 0.258 | 0.263 | 0.273 |

### E.4 Frozen-verifier strength (why AND-ing it is not enough)

| Repo | approved@10 | FN among approved | approval precision | FN-recovery among top-10 |
|---|---:|---:|---:|---:|
| djangoCMS | 105 | 9 | 0.086 | 0.643 (9/14) |
| Saleor | 170 | 24 | 0.141 | 0.800 (24/30) |

### E.5 Feasibility verdict

**Directional support (mechanism):** the conservative AND-rule (a) improves
candidate precision over Arm B take-first-5 on both repos (dc 0.105→0.146,
saleor 0.179→0.222), (b) recovers most of Arm B's F1 loss on djangoCMS
(0.324→0.407) and slightly improves Saleor's (0.258→0.263–0.273), and (c)
reduces the accepted FP tail sharply (dc 133→48 at K=5). **The family is
directionally justified: a precision-safe acceptance layer is the correct next
mechanism, and the K-vs-acceptance decoupling is the right container.**

**Why the SPECIFIC frozen instantiation is NOT justified:** the frozen verifier
approves ~everything it sees (8.6–14% approval precision; 80% of Route-B-top-10
FNs recovered only at the price of ~5.7× FPs). AND-ing it with the semantic rank
therefore *removes FNs along with FPs*: the rule's ORR falls below the frozen
Route-B verifier on Saleor (0.219 vs 0.334) and its F1 does NOT beat Arm A on
either repo (dc 0.407 vs 0.414; saleor 0.263 vs 0.287). **The frozen Stage-4
verifier is a "reconsider" judge with no acceptance calibration, not a
precision-safe acceptance layer.**

**Explicit insufficiency (stated, not papered over):** the frozen verifier only
decided on Route-B top-10 candidates. **Existing frozen records CANNOT assess a
verifier on reverse-1hop-only candidates — no such evidence exists in the
300-call record.** Any claim that a future verifier will reject consumer-only
FPs while keeping consumer-only FNs is UNTESTED by the frozen data and must be
measured prospectively.

**Conclusion:** the mechanism hypothesis — *a precision-safe acceptance layer
between semantic ranking and the final file set can retain useful FN recovery
while rejecting enough FPs to preserve final F1* — is **coherent, and the
Stage-4 failure modes are identified with fixable root causes** (FP tail from
both sources; weak uncalibrated verifier; cap loss; partial credit). The frozen
records justify freezing **exactly ONE next DEVELOPMENT pilot** that tests a
**NEW, strictly-constrained second-stage verifier** (Section F schema) inside
the RANK → VERIFY → VARIABLE-ACCEPT family. The records do NOT confirm that
new verifier will work — the pilot is a prospective test with a preregistered
gate.

---

## F. Schema reliability (design for a FUTURE protocol — not executed)

Stage-4 had 6/60 Arm-B schema-invalid outputs; the taxonomy is 6/6
**non-pool-path hallucinations**, and the frozen analyzer granted invalid calls
partial credit. The future protocol's schema (frozen in
`docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md`) is machine-constrained:

1. **Candidate IDs instead of free-form paths.** Every pool candidate is given a
   stable ID `C01..C<cap>`; the model references IDs only. The JSON Schema
   declares the candidate-ID **enum** server-side (OpenRouter
   `response_format.json_schema`, `strict: true`), and the fail-closed parser
   ALSO validates every emitted ID against the pool enum — two independent
   layers, so a hallucinated path cannot even be expressed.
2. **Uniqueness enforcement** (parser-level, fail-closed): an ID may appear at
   most once in a ranking; duplicate → whole call invalid.
3. **Fixed-length boolean verification vector** for the second stage: exactly
   K booleans (`minItems == maxItems == K`) in the presented candidate-ID order
   — one boolean per inspected candidate; no free text.
4. **Strict fail-closed semantics with NO partial credit:** any invalid call
   contributes zero accepted additions for its task (fixes the Stage-4
   partial-credit defect), recorded, never retried.

The goal is engineering validity (fewer invalid outputs, unambiguous fail-closed
behavior), NOT outcome tuning.

---

## G. Exactly ONE next protocol

**Justified: YES** (Section E.5). Exactly ONE candidate protocol is frozen:
`docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md` — the **RANK → VERIFY →
VARIABLE-ACCEPT** protocol:

`Sparse first pass → deterministic expanded pool (cap 80) → bounded semantic
ranking (1 call/task) → top-K inspection set (K=10) → strict second-stage
verifier (1 call/task, fixed boolean vector) → variable accepted additions
(0..K) → final file set`

- Pool construction, inspection K=10, and pool cap C=80 are **explicitly
  DEVELOPMENT-derived method design** (labels in the protocol): K from C.1/C.13
  (recovery grows to rank 10), cap from C.9 (cap-40 loses 10+29 FNs; cap-80
  covers 66%/60% at ~2× ranking cost; cap-120 gains only +3%/+9%).
- Baseline: the frozen Route-B verifier (Arm A) at B∈{1,3,5,10} on the same
  fresh sample.
- Comparison semantics are fully matched to Stage-4: the candidate's
  verifier-approved-and-semantically-ranked additions form its ORR/F1 curve at
  B∈{1,3,5,10}, with the ability to add fewer than B when fewer are approved.

The protocol freezes, BEFORE any future call: candidate pool construction,
inspection K and its DEV-derived rationale, acceptance semantics, schema,
fail-closed behavior, provider/model, temperature/cap, comparison baseline, task
sampling, metrics, cost accounting, leak guard, stop gate, audit, and the
no-result-based-retry rule.

---

## H. Future sample discipline

For the future DEVELOPMENT pilot, the frozen sample-selection algorithm (seed
**20260919**) draws **≤30 fresh tasks per repo** from the DEV eligibility
predicate `n_missed ≥ 1 AND omitted_size ≥ 5`, stratified by year/universe-size
EXACTLY as Stage-4, with the **hard exclusion of all 60 Stage-4 sampled
case_ids**. Availability verified from frozen records: **123 djangoCMS + 97
Saleor fresh eligible tasks remain** (A11 PASS). The algorithm is frozen before
calls and is never executed against sealed data. Forbidden: djangoCMS RESERVE,
Saleor INTERNAL_TEST, Saleor RESERVE, and the spent djangoCMS INTERNAL_TEST.

---

## I. Success gate for the future pilot

Frozen in `docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md` (all thresholds
predeclared; none chosen by sweeping). Summary at the reference point B=5,
BOTH repos required:

| Gate | Requirement | Rationale |
|---|---|---|
| c1 ORR | candidate macro ORR > Arm A ORR + **0.05** | same materiality as Stage-4; blocks marginal +0.02 claims |
| c2 folds | ≥3/5 seeded folds positive direction | stability, not single-fold luck |
| c3 F1 | candidate naive F1 ≥ Arm A F1 − **0.05** | forbids the "ORR up, F1 down" outcome |
| c4 precision | candidate acceptance precision ≥ Arm A candidate precision | the precision-safe claim is measured, not asserted |
| c5 leak | leak-free (audited) | no hidden target/gold in any prompt |
| c6 schema | ≥90% valid, zero partial credit | engineering reliability gate |
| c7 cost | within ceilings; marginal cost justified | cost minimization is first-class |
| c8 | per-task delta distribution reported (descriptive) | heterogeneity transparency |

The gate requires evidence on BOTH repositories; it is impossible to claim
"ORR up" without the F1 and precision guards.

---

## J. Cost freeze — estimated, NOT executed

`reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md` freezes the
smallest justified budget:

- **Expected:** 360 calls (240 Arm A baseline + 60 semantic ranking + 60 strict
  verification) ≈ **130,000–170,000 tokens ≈ $0.05–0.06 ≈ < 30 min**.
- **Hard ceilings (safety limits, not targets):** 400 calls / 300,000 tokens /
  $0.15 / 60 min.
- Per-call reservation ledger (fail-closed) sized from measured Stage-4
  distributions (Arm A mean 248–252 tok; rank stage 658–884 tok at cap 40 →
  reserved for cap 80; verify stage ≈ 300 tok).
- **No API call is authorized by this mission.**

---

## K. Required outputs (this mission)

| Output | Location |
|---|---|
| Feasibility report | `reports/PRECISION_SAFE_ACCEPTANCE_FEASIBILITY_2026-09-18.md` (this file) |
| Machine-readable feasibility metrics | `reports/precision_safe_feasibility_metrics.json` |
| Independent audit report/JSON | `reports/PRECISION_SAFE_ACCEPTANCE_AUDIT.md` + `reports/precision_safe_feasibility_audit.json` (11/11 PASS) |
| Exactly one frozen protocol | `docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md` |
| Future API budget freeze draft | `reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md` |
| Roadmap update | `reports/GAP_REDUCTION_ROADMAP.md` |
| Current-state update | `00_CURRENT_RESEARCH_STATE.md` |
| Execution update | `PROGRESS.md` |
| Decision record (append after P65) | `DECISIONS.md` — Decision P66 |
| Research journey update | `docs/RESEARCH_JOURNEY.md` |
| Deterministic analysis code | `scripts/precision_safe_feasibility_anatomy.py`, `scripts/precision_safe_feasibility_audit.py` |
| Tests | `tests/unit/test_precision_safe_feasibility.py` (13/13 PASS) |

Stage-4 closure artifacts were NOT overwritten.

---

## L. Validation / audit (per `docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md`)

T3 discipline for this new acceptance-strategy analysis:

- Deterministic recomputation: audit recomputes all headline numbers from raw
  records without importing the analyzer — **11/11 PASS**
  (`reports/precision_safe_feasibility_audit.json`).
- Leakage guard: prompts rebuilt from parent-visible inputs for a deterministic
  10-record sample, prompt SHA-256 matches (A10); pool construction verified
  parent-visible (test `test_no_hidden_proxy_in_pool_construction`).
- Metric verification: macro ORR matches frozen Stage-4 metrics at every B.
- Affected tests: `tests/unit/test_precision_safe_feasibility.py` **13/13 PASS**
  (plus the previously green 31/31 Stage-4 suites).
- Ruff clean; `py_compile` clean; `git diff --check` clean.
- No hidden target/gold use: no prompt in the frozen protocol contains proxy
  paths, gold sets, or future information (Section 8 of the protocol).

---

## M. Final report — the ten mandated answers

1. **Where exactly did Stage-4 false positives come from?**
   From the acceptance layer, in BOTH pool sources. At B=5 Arm B added 119 FPs
   (djangoCMS) / 119 FPs (Saleor) against 14/26 FNs; the FP tail is split
   ~55–60% Route-B top-10 and ~40–45% reverse-1hop-only. No single source is
   responsible; the semantic rank is not precision-sorted (C.1) and Arm B was
   forced to accept exactly B additions. Schema-invalid calls also leaked
   partial credit into the pooled counts.

2. **Is semantic ranking itself still worth keeping?**
   **Yes.** It is the first instrument that realizes real FN recovery:
   djangoCMS ORR 0.111→0.250 at B=5 (2×), both repos 5/5 positive folds at
   B=10, recovery growing through rank 10, and oracle-reviewer F1 rising on
   both repos (frozen Stage-4 result). The ranking is NOT the failure; naive
   acceptance is.

3. **Can inspection depth and acceptance count be safely decoupled?**
   **Yes, and the decoupling is supported by the anatomy:** recovery grows to
   rank 10 (Saleor cumulative FNs 9→31) while acceptance precision is already
   poor at rank 5; C=40 loses 10+29 FNs; the POST-HOC AND-rule already produces
   a variable accepted set (mean 1.8–3.5/task, range 0..K).

4. **Is a rank-then-verify protocol scientifically justified?**
   **Yes — the FAMILY is justified (RANK → VERIFY → VARIABLE ACCEPT), with an
   explicit caveat:** the frozen verifier is too weak (8.6–14% approval
   precision) and was never assessed on reverse-1hop-only candidates (explicit
   insufficiency). The justified protocol therefore specifies a NEW, strictly
   constrained second-stage verifier whose performance is UNTESTED by frozen
   data and must be measured under the preregistered gate.

5. **What EXACTLY is the one frozen next protocol?**
   `docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md` — Sparse first pass →
   deterministic expanded pool (Route-B top-10 ∪ reverse-1hop consumers, cap
   C=80, DEV-derived) → bounded semantic ranking (1 call/task) → top-K
   inspection set (K=10, DEV-derived) → strict fixed-length boolean-vector
   verifier (1 call/task, candidate-ID enum schema, no partial credit) →
   variable accepted additions (0..K) → final file set; compared against the
   frozen Route-B verifier (Arm A) at B∈{1,3,5,10}; 30 fresh DEV tasks/repo,
   seed 20260919, Stage-4 sample excluded.

6. **What would constitute PASS/FAIL?**
   PASS = the preregistered gate (§I) holds on BOTH repos: material ORR gain
   (+0.05), ≥3/5 positive folds, no material F1 regression (−0.05), acceptance
   precision ≥ Arm A, leak-free, ≥90% schema-valid, within budget. FAIL =
   any single gate condition fails on either repo → freeze the negative, do NOT
   tune.

7. **What is the expected and maximum cost?**
   Expected ≈ 360 calls / 130–170k tokens / $0.05–0.06 / <30 min. Hard ceilings
   (safety limits): 400 calls / 300,000 tokens / $0.15 / 60 min.

8. **Which datasets remain sealed?**
   djangoCMS RESERVE, Saleor INTERNAL_TEST, Saleor RESERVE, and the spent
   djangoCMS INTERNAL_TEST (never reused as a fresh test). The future pilot uses
   fresh DEVELOPMENT tasks only.

9. **What explicit authorization sentence would be required before any new API
   spend?**
   The exact sentence in `reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md`
   §7. No variant is treated as authorization; only that sentence authorizes
   calls.

10. **What is the ONE next action?**
    Await the user's review of this feasibility report, the frozen protocol, and
    the budget draft. This mission is COMPLETE (ZERO API); the next action is
    authorization (or rejection) of the frozen DEVELOPMENT pilot. If rejected,
    the feasibility conclusion (positive-direction family, negative specific
    frozen instantiation) is itself frozen as development evidence.

---

## N. Boundary held

- ZERO model/API calls in this mission (no OpenRouter call, no fallback, no
  hidden provider, no spend).
- Stage-4 verdict `BOUNDED_SEMANTIC_NEGATIVE_FROZEN` and P65 immutable.
- No sealed set opened; spent djangoCMS INTERNAL_TEST not touched.
- No threshold swept; exactly one principled rule family evaluated; all
  DEV-derived parameters labeled.
- `CHEAP_RANKING_CLOSED_FOR_NOW` remains frozen.