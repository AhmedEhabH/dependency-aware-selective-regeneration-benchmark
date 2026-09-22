# WP-2 Census, Task, Candidate, and Selection Rationale (2026-09-22)

This document fixes the exact meaning of the WP-2 planning vocabulary and
records every inclusion / exclusion / attrition rule. It is the authoritative
interpretation of the previous 20/200/77 census counts.

## 3.1 Census

**Census** = exhaustive structural inspection of the entire currently opened
WP-2 planning population, **not** a statistical sample.

Here the population is exactly the **297 MAIN_297 task IDs** already used in the
matched WP-1b comparison.

The census:
- checks every one of the 297;
- uses parent/target repository state and diffs;
- uses zero model calls;
- does **not** score RM-CSS or Agent success to select tasks;
- does **not** itself prove F2P/P2P.

Why this mattered:
1. it converts an assumed WP-2 data supply into **measured counts**;
2. it finds environment/oracle bottlenecks **before** expensive generation;
3. it makes later Smoke selection **auditable**;
4. it protects against cherry-picking by separating **structural eligibility**
   from selector/generator outcomes.

## 3.2 Task

A WP-2 **task** = one real Saleor change instance with:
- task/case ID;
- change intent;
- parent commit;
- target commit;
- parent repository state;
- observed target diff used only where allowed by evaluator/dataset construction;
- candidate source-file universe;
- eventual evaluator-only test oracle.

A task is **not** a file.

## 3.3 Three different meanings of "candidate"

These three objects MUST never be called simply "candidate" in scientific docs
without the qualifier:

A. **impact candidate** — a FILE considered by SIP/RM-CSS during localization.

B. **F2P candidate** — a TASK whose commit history exposes test-change evidence
   that may permit construction of a fail-to-pass oracle.

C. **Smoke candidate** — a TASK proposed for a small engineering feasibility run.

## 3.4 Census F2P candidacy labels

**`STRONG_F2P_CANDIDATE`**
- target diff ADDS ≥1 test file.
- Why "strong": a newly added target test provides a direct candidate evaluator
  that can be injected into the parent state and checked before vs after.
- Why NOT "confirmed": it can still be flaky, environment-broken, pass on
  parent, fail for infrastructure reasons, or encode target-specific
  implementation details.

**`MODIFIED_TEST_CANDIDATE`**
- target modifies ≥1 test file and adds no test file.
- This is weaker evidence, NOT bad evidence.
- It can still yield valid F2P tests when changed test nodes fail on
  parent+test-patch and pass on target.
- Do NOT describe all 200 as "F2P" before execution.

**`NO_CHANGED_TEST_EVIDENCE`**
- no test path changed in target diff.
- The historical commit does not directly supply an automatic test patch for
  F2P extraction.
- It does NOT mean the change is untestable.
- It does NOT mean the task is scientifically worthless.
- It may support later manually constructed/independent oracle work,
  architecture checks, preservation checks, or external tests.
- It is excluded only from the **automatic changed-test Oracle Confirmation
  path** in this mission.

## 3.5 What was actually excluded and why

1. **The 3 calibration tasks:** excluded from MAIN_297 by frozen design because
   they were used to validate the Agent instrument. Keeping them out prevents
   calibration/evaluation overlap.
2. **The 786 sealed Saleor RESERVE outcomes:** excluded and UNOPENED to
   preserve the untouched reserve for future confirmation/generalization. They
   are not a convenient source of extra WP-2 examples.
3. **The 77 no-changed-test-evidence tasks:** NOT deleted from the study. They
   are merely outside this automated F2P-oracle extraction path.
4. **Migration/config-heavy tasks:** NOT excluded. They are a complexity stratum
   because environment/setup and architecture behavior may differ.
5. **Future Oracle Confirmation attrition:** tasks can leave the PRIMARY
   executable F2P corpus only for predeclared instrument/oracle reasons:
   - environment cannot be reproduced;
   - target evaluator test does not pass stably;
   - parent and target both pass (P2P-only);
   - test patch cannot be applied to parent;
   - non-deterministic/flaky status;
   - failure is unrelated to requested behavior/environment corruption.
   Every attrition reason remains counted and published.

**No task may be excluded because:**
- RM-CSS selected the wrong files;
- Agent selected the wrong files;
- a generator later failed;
- the result is inconvenient.

## Literature basis

Verified references and relevance are recorded in
`research/wp2/wp2_design_reference_manifest_2026-09-22.json` and the BibTeX in
`research/literature/wp2_verified_references_2026-09-22.bib`. Summary:

1. **SWE-bench** (Jimenez et al., ICLR 2024, arXiv:2310.06770): real
   issue/repository evaluation; F2P and P2P are separate evaluation sets; a task
   is resolved only when both pass; test patches belong to the evaluator, not
   the generation prompt.
2. **FEA-Bench** (Li et al., ACL 2025, DOI 10.18653/v1/2025.acl-long.839):
   incremental feature implementation; tasks collected from changes involving
   tests; test patch run before and after the gold patch; explicitly does NOT
   auto-reject ImportError/AttributeError before the gold patch; provides
   new-component signatures as metadata (our primary protocol deliberately does
   not import target-derived signatures); oracle context beats BM25 only
   modestly, motivating direct functional evaluation.
3. **Loc2Repair** (Al Awad & Ivanov, arXiv:2606.30963): isolates localization as
   an upstream variable under a shared repair runtime; pooled resolved rates
   44.7% (no loc) / 48.9-49.1% (predicted) / 52.4% (gold); even gold
   localization leaves downstream failures, so WP-2 must prove assay
   discrimination rather than read "no difference" as equivalence.
4. **Cost-Effective Repository Exploration for Agentic Issue Localization**
   (arXiv:2608.29675): distinguishes recoverable ranking/coverage handoffs from
   restrictive file gates; "restrictive gate" is not our novelty — our question
   is the downstream functional/preservation/cost effect of the hard-vs-soft
   contract.
5. **Agentless** (Xia et al., arXiv:2407.01489): localization → repair →
   validation predates WP-2; do not claim it as new by itself.
6. **RIPPLE** (Yadavally & Nguyen, ICSE 2026, DOI 10.1145/3744916.3773265):
   intent-aware change impact analysis with dependency/evolutionary coupling is
   prior art; graph/impact-set prediction alone is not the new contribution.
7. **Placebo-controlled localization study** (Jha, arXiv:2609.00854): random-span
   placebo matched to edit size; supports a size-matched random-scope placebo in
   WP-2.
8. **FastContext (arXiv:2606.14066):** current arXiv v4 is **withdrawn**; do not
   use as positive evidence without an explicit withdrawal note; recorded for
   literature hygiene only.