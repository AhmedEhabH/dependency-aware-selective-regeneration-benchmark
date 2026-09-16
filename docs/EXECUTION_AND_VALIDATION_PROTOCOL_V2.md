# OpenCode Execution & Validation Protocol v2

**Version:** 2.0 · **Status:** ACTIVE (supersedes execution-guide phase framing for scientific-work governance)
**Root files:** `docs/OPENCODE_EXECUTION_GUIDE.md` (v1.0.0), `docs/ONE_PASS_PHASE_EXECUTION_PROTOCOL.md` (phase lifecycle). This v2 protocol aligns project governance on top of them.

---

## 1. CURRENT PHASE (authoritative)

```
CURRENT PHASE: Repository change localization / impact selection
```

The active scientific phase evaluates **which files an impact-selection method
would mark for change** (the predicted write/selected set) against the observed
change-set proxy, within the frozen candidate universe at the parent revision.
Selection happens BEFORE downstream regeneration.

## 2. Governance hierarchy (permanent)

1. `00_CURRENT_RESEARCH_STATE.md` — **scientific source of truth**: frozen
   evidence, datasets/splits, exposed test sets, tags/SHAs, supported claims,
   current research direction.
2. `PROGRESS.md` — **execution source of truth**: what is being executed now,
   last completed task, immediate next step, blockers.
3. `DECISIONS.md` — **append-only** record of implementation/research decisions.

No competing current-state handoff is created. Historical handoffs
(`SYSTEM_STATE.md`, `TODO.md`, `docs/PROJECT_HANDOFF.md`) remain as historical
records.

## 3. Evaluation dimensions for the current phase

PRIMARY:
1. **Impact Correctness** — Precision, Recall, F1, FNR (micro and
   task-level/macro where meaningful).
2. **Efficiency** — wall-clock runtime; index/build time separated from query
   time; computational cost; retrieval/query cost; memory if trivial to
   measure; LLM calls/tokens/cost ONLY when an LLM is actually used
   (zero for non-LLM baselines).

CONDITIONAL:
3. **Architecture / protocol compliance** (only when the method defines an
   architecture/protocol contract).

DEFERRED until downstream code regeneration:
4. **Functional Correctness**.
5. **Preservation / regression correctness**.

Rule: Do NOT force non-applicable dimensions into localization-only
experiments.

## 4. Task classification

- **T0** — documentation / reporting / governance.
- **T1** — infrastructure/engineering change with no new scientific evaluation.
- **T2** — new scientific run reusing an existing evaluation strategy.
- **T3** — new evaluation strategy / baseline family (requires all six
  pre-benchmark gates + independent audit, leakage tests, and deterministic
  reproducibility).

Protocol A of the post-ICCI block (cheap-nonllm-baselines-v1) is classified
**T3**.

## 5. Validation gates (T3)

1. Dataset Validation
2. Prompt/Input Validation (for non-LLM: visible-intent/query construction)
3. Pipeline Smoke Test
4. Dry Run
5. Integration Test
6. Metric Verification (synthetic examples with manually known TP/FP/FN/P/R/F1/FNR)

Plus: independent audit; leakage regression tests; historical-parent-state
indexing tests; deterministic-seed tests.

## 6. Data discipline

- TRAIN and VALIDATION are **development evidence** only (not confirmatory,
  not final, not statistically generalizable).
- Use VALIDATION to select/confirm the frozen candidate method; freeze
  implementation, K/config, metric code, and candidate-universe rules BEFORE
  any new confirmatory dataset is evaluated.
- The HELD_OUT_TEST ten are PERMANENTLY EXPOSED (P1 + P5 ran them). Never use
  them for tuning/threshold/K/feature selection or error-driven revision.

## 7. Cost discipline

This phase is ZERO-API for non-LLM baselines. Any future LLM use requires its
own frozen budget before cell 1. No new scientific model/API call without
explicit authorization.

## 8. Relationship to prior protocol docs

- Execution mechanics/branching from `docs/OPENCODE_EXECUTION_GUIDE.md`.
- Phase lifecycle/one-pass discipline from `docs/ONE_PASS_PHASE_EXECUTION_PROTOCOL.md`.
- Scientific protocol from `docs/FINAL_RESEARCH_PROTOCOL.md` (frozen v1.0) and
  its companion docs. This v2 doc adds the current-phase naming and the
  governance hierarchy only; it does not amend the frozen scientific protocol.

## 9. Progress response format (normal vs closure)

### 9.1 Normal progress responses

Normal incremental progress responses may remain **one line** (e.g., "step X of
Y complete: <one-line status>"). The one-line rule is the default for
non-boundary progress.

### 9.2 Detailed closure report exception (T2/T3 MANDATORY STOP or scientific milestone closure)

**This detailed closure report is NOT prohibited by the normal one-line progress
rule.** For a **T2/T3 MANDATORY STOP** or a **scientific milestone closure**, the
final report MUST be detailed and MUST contain ALL of the following sections:

1. **Executive verdict** — one-paragraph outcome (PASS / FAIL / PARTIAL / closed
   with correction), not a bare number.
2. **Scientific question** — the exact question the milestone answers.
3. **Dataset/split and forbidden data** — which split(s) were used (development
   vs confirmatory label on each), which data was forbidden and stayed unused.
4. **Validation-gate table** — every applicable gate with PASS/FAIL and the
   evidence location.
5. **Main result table** — the headline numbers, with denominators and the
   metric definition (TP/FP/FN/P/R/F1/FNR).
6. **Development vs confirmatory label** — explicit statement that the evidence
   is development (TRAIN/VALIDATION) or confirmatory; never blurred.
7. **Fair-comparison warning** — when comparing methods across different
   splits/protocols, an explicit warning that cross-split head-to-head ranking
   is prohibited or only directional context.
8. **Interpretation** — what the numbers mean, not merely re-printing them.
9. **What the result does NOT mean** — explicit negative-space: over-strong
   claims that the result does NOT support.
10. **Competitor/baseline implication** — what the result implies for the LLM
    planner line / alternative methods, stated within the fair-comparison
    boundary.
11. **Threats/caveats** — every threat, caveat, and shortcut (e.g., frozen-corpus
    path mentions, small n, single repository).
12. **Tests/audit** — test counts, audit verdict, gate JSON locations.
13. **Documentation changed** — per-file list of docs synchronized.
14. **Git branch/commit/main status** — branch, HEAD, main, origin/main equality.
15. **Merge status** — merged or not, merge commit.
16. **Tag** — tag name and its exact meaning (e.g., DEV evidence only), or
    explicit "no tag" statement.
17. **Export ZIP + SHA256** — the light export name, path, size, SHA-256, and the
    `PROJECT_EXPORT_READY` block.
18. **Where we are now** — exact position in the research pipeline.
19. **ONE next action** — a single recommended next step (not started).

This exception exists so that milestone closures and mandatory stops leave a
durable, auditable record without weakening the one-line rule for normal
progress.