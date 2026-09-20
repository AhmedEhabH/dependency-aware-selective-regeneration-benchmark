# PROVENANCE-BY-CONSTRUCTION — Strategic Direction Note (2026-09-20)

**Status:** SUPERVISOR-FACING STRATEGIC NOTE ONLY. **NOT implemented. NOT a
scope change in this mission.** `SUPERVISOR_DISCUSSION_REQUIRED_BEFORE_EXECUTION`.

**Mission context:** PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 (T3, ZERO API).
This note is created per mission §28 and does NOT alter the active thesis
scope.

---

## 1. The concept

During LLM generation/regeneration, persist **trace links** as they are
created:

```
requirement / DSL element  ->  files  ->  symbols  ->  tests
```

Future impact analysis could then use:

```
trace lookup  +  dependency closure  +  repository memory
```

instead of rediscovering all impact solely from ambiguous natural-language
intent. This is a MAJOR potential scope change (a new pipeline stage / new
artifact family), NOT a small addition to the current calibrated
set-selection line.

## 2. Why now

The V2 result (frozen negative `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`)
confirms the current bottleneck is not basic dense ranking (independently
replicated) but the **semantic gap between the frozen parent-visible intent
text and the impacted file set**: 156/129 deep dense misses remain
"not-generated" even by history memory, and intent-length stratification
(descriptive) shows short intents are hardest. Trace links generated AT
construction time bypass the ambiguous-intent rediscovery step entirely.

## 3. What it is NOT

- NOT a claim that trace links exist today in the benchmark;
- NOT a new scientific experiment in this mission;
- NOT executed; NOT part of the V2 feature set;
- NOT a novelty claim.

## 4. Scoped literature check (per mission §28)

Prior-art families recorded in the literature ledger (primary sources):

- **Requirements-to-code traceability** (classical + modern ML-based):
  Cleland-Huang et al. traceability recovery survey line; deep-learning
  traceability (e.g., Guo et al., "Recovering Traceability Links with Neural
  Networks"); T-Recs / online-learning traceability.
- **Model-driven trace links:** MDE / model-to-code generation traceability;
  incremental transformation traceability (e.g., synchronizing models and
  generated code).
- **Recent LLM traceability systems:** LLM-based issue-to-commit linking and
  requirement traceability recovery; repository-level code generation agents
  that emit per-file/per-symbol edit provenance.

The full verified entries are recorded in
`reports/LITERATURE_DECISION_LEDGER.md` (2026-09-20 addendum) and
`research/literature/` (bibtex triage + review matrix). The active thesis does
NOT claim novelty for traceability.

## 5. Decision needed from supervisor

- Whether provenance-by-construction should become a thesis direction;
- if so, under a NEW mission with its own frozen hypothesis, budget, and
  authorization;
- the current mission does NOT execute it.

**`SUPERVISOR_DISCUSSION_REQUIRED_BEFORE_EXECUTION`.**