# Scientific Reset Decision — 2026-09-04

**Status:** ACCEPTED / FROZEN (researcher accepted the scientific-management decision).

The researcher has accepted the scientific-management decision. This document
freezes the accepted direction and the preregistration truth BEFORE any new
real API/model call. It is part of the pre-main feasibility /
model-freezing gate. The decision-pack sources are under `_workspace/active/`
and the formal decision-log entries are `D040`–`D045` in `DECISION_LOG.md`.

Related documents:

- `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md` — the compact preregistration
  (thresholds, scenario IDs, 30-run design, GO/NO-GO, anti-cherry-picking,
  graph-eligibility rule).
- `docs/POST_2018_RESEARCH_EVIDENCE_MATRIX.md` — verified evidence matrix
  behind this pivot.

---

## 1. What is decided

1. **Qwen2.5-Coder-14B + Kaggle 2×T4 is RETIRED as the PRIMARY scientific
   inference path.** All previous runs, failures, canaries, candidates, and
   artifacts remain immutable **engineering feasibility evidence**. They are
   preserved; they are not the launch basis.
2. **No old 48-cell Pilot is launched or repaired.** In particular, no
   D14/D15-style time-out / infrastructure / engineering work is opened to
   force the old 48-cell matrix. Do not increase the time-out.
3. The next scientific milestone is a **pre-main Todo correctness-first
   micro-study**, not another release-readiness candidate.
4. **Before the Todo study**:
   a. one non-study **operational model/provider acceptance gate** is executed
      (6 throwaway calls total — 3 per candidate); then
   b. **ONE exact model/provider/settings configuration is frozen**.
5. **No scientific scenario is used to choose between candidate
   models/providers.** The candidates are:
   - Candidate A: **DeepSeek V4 Flash 0731**
   - Candidate B: **Qwen2.5-Coder-32B-Instruct**
   The winner is selected ONLY using the preregistered NON-SCIENTIFIC
   operational criteria. DeepSeek is **not** pre-selected.
6. **Todo micro-study design is frozen:**
   - `todo-smoke-001` (localized)
   - `todo-smoke-002` (moderate)
   - `todo-smoke-003` (cross_cutting)
   - 3 scenarios × 2 strategies × 5 repetitions = **30 attempted runs**.
7. Evaluation reading order is fixed: **correctness first → preservation →
   impact recall → efficiency last (descriptive only)**. Efficiency is
   secondary and never authorizes a claim of significance from n=5.
8. **GO / NO-GO** is computed from the frozen thresholds in
   `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md`.

## 2. Scope guard

- The **permanent final thesis repository scope is NOT decided in this task**.
  Todo is a pre-main scientific go/no-go study.
- **djangoCMS** is conditional on Todo GO **and** a real reproducible
  dependency graph (see the graph-eligibility rule in the preregistration).
- **Saleor is not part of the immediate next task.**
- Any permanent reduction of the final repository count remains a
  supervisor-level scope amendment (see `_workspace/active/05_SUPERVISOR_BRIEF_AR.md`).

## 3. Order of execution (frozen)

```text
preregistration (this commit)
    →
6-call NON-STUDY operational acceptance gate (throwaway tasks only)
    →
freeze ONE exact model/provider/settings
    →
final Todo evaluator/scenario audit
    →
six Pre-Benchmark Validation gates
    →
independent audit
    →
30 real Todo scientific runs
    →
first scientific results table
    →
GO / NO-GO (pre-registered)
    →
STOP
```

## 4. Not-current-target reminder

- NOT a target: Kaggle Qwen14B engineering; the old 48-cell Pilot; Saleor;
  djangoCMS implementation.
- CURRENT SCIENTIFIC TARGET: **SCIENTIFIC-MICROSTUDY-01** (the Todo 30-run
  correctness-first micro-study producing the FIRST SCIENTIFIC RESULTS TABLE).