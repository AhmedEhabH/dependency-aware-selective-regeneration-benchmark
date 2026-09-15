# DECISIONS.md — Append-Only Decision Record

**Role:** Append-only record of implementation/research decisions made during
execution. Entries are never edited after append; corrections are new entries.

---

## Decision P1 — Governance hierarchy (2026-09-15)

- **Status:** ADOPTED (permanent)
- **Context:** Post-ICCI experimental block start; ambiguity between
  `00_CURRENT_RESEARCH_STATE.md`, `SYSTEM_STATE.md`, `TODO.md` as sources of truth.
- **Decision:** Permanent hierarchy:
  1. `00_CURRENT_RESEARCH_STATE.md` = scientific source of truth (frozen
     evidence, datasets/splits, exposed test sets, tags/SHAs, supported claims,
     research direction);
  2. `PROGRESS.md` = execution source of truth (current execution, last task,
     next step, blockers);
  3. `DECISIONS.md` = append-only decision record.
  No new competing current-state handoff will be created.
- **Rationale:** One scientific truth + one execution truth + append-only
  decisions; avoids handoff drift.
- **Impact:** All future state updates target exactly these three files.

## Decision P2 — Protocol CURRENT PHASE (2026-09-15)

- **Status:** ADOPTED
- **Context:** Execution & Validation Protocol v2 must name the current phase.
- **Decision:** CURRENT PHASE = **Repository change localization / impact
  selection**. Evaluation dimensions for this phase:
  - PRIMARY: 1. Impact Correctness (Precision, Recall, F1, FNR); 2. Efficiency
    (runtime, computational cost, retrieval/query cost; LLM calls/tokens/cost
    only when an LLM is actually used).
  - CONDITIONAL: 3. Architecture / protocol compliance.
  - DEFERRED (until downstream code regeneration): 4. Functional Correctness;
    5. Preservation / regression correctness.
- **Rationale:** Localization-only experiments must not be forced to claim
  downstream-regeneration dimensions.
- **Impact:** Baselines and future localization work report only applicable
  dimensions.

## Decision P3 — Protocol A scope (2026-09-15)

- **Status:** ADOPTED (this task)
- **Context:** Executing the only scientific experiment of this block.
- **Decision:** Implement B0 Random@K (seeded), B1 BM25@K, B2 path/identifier
  token@K, B3 Graph@K (frozen per-case parent-only dependency graph, seed =
  intent-term hits against candidate metadata; if no defensible seed exists,
  stop and document), B4 Hybrid@K (frozen pre-validation combination rule).
  Evaluate K in {1,3,5,10}. TRAIN 24 + VALIDATION 6 only; HELD_OUT_TEST 10 is
  PERMANENTLY EXCLUDED from all tuning/selection.
- **Rationale:** Zero-LLM-cost baseline family; matched K; matched-cardinality
  view kept separate if scientifically useful.
- **Impact:** Smallest defensible baseline family; zero API cost.

## Decision P4 — STRICT DATA RULE (2026-09-15)

- **Status:** ADOPTED (permanent)
- **Context:** The 10 HELD_OUT_TEST tasks are permanently exposed (P1 M4A-3 +
  P5 ran them).
- **Decision:** Use ONLY TRAIN (24) + VALIDATION (6). Never use HELD_OUT_TEST
  for tuning, threshold selection, method choice, K selection, feature design,
  or error-driven revisions. Report any aggregate on TRAIN/VALIDATION as
  development evidence only (not confirmatory/generalizable).
- **Rationale:** Exposed test set must not inform any new-method decision.
- **Impact:** Violations are audited fail-closed.

## Decision P5 — Frozen P1/P5 evidence immutability (2026-09-15)

- **Status:** ADOPTED (permanent)
- **Context:** Post-ICCI experimental block.
- **Decision:** Do NOT rerun or modify frozen ICCI/P1/P5 scientific evidence.
  All baseline analysis is run-fresh on TRAIN/VALIDATION; no frozen run_records
  are altered.
- **Rationale:** Immutable submitted science.
- **Impact:** Baseline output dirs are new; existing evidence untouched.

## Decision P6 — Frozen-corpus path-mention caveat classification (2026-09-16)

- **Status:** ADOPTED (documented, not a pipeline defect)
- **Context:** Gate2 flagged 6 frozen cases whose full-message public intent
  literally contains a changed path while the recorded
  `intent_mentions_changed_path` flag is False (M4A-2 leak detector ran on the
  short subject; persisted intent is the full message).
- **Decision:** Classify as a **frozen-corpus property** shared identically by
  the P1 LLM planner and the baselines (same public query). Do NOT modify the
  frozen corpus; record the 3 TRAIN cases
  (`djangocms-rc-2efae8e43bd6`, `ada585d3f358`, `5ff38b521274`) as a caveat in
  gates/audit/report, and treat it as a data-construction lesson for the
  future Saleor minining (test the SAME string that is persisted).
- **Rationale:** The baselines receive no new exposure beyond the public input
  the planner also sees; altering frozen data would corrupt frozen evidence.
- **Impact:** Gate2/audit now pass with the caveat recorded; no result change.

## Decision P7 — Protocol A frozen configuration (2026-09-16)

- **Status:** ADOPTED (frozen before validation)
- **Decision:** K ∈ {1,3,5,10}; seed rule = intent-token ∩ candidate-token;
  Hybrid = 0.5·Nm(BM25) + 0.5·Ng(graph) with seedless→pure-BM25; tie-break by
  (-score, path); BM25 k1=1.5, b=0.75; frozen stopword set; per-case random
  seed `20260915:case_id`. No threshold/method/K change allowed from validation
  results.
- **Rationale:** smallest defensible baseline family, preregistered.
- **Impact:** freeze point for the cheap-baseline arm of the MSc proposal
  (pending Ahmed's review).

## Decision P8 — Matched-cardinality view NOT reported (2026-09-16)

- **Status:** ADOPTED
- **Context:** The prompt allows a separate matched-cardinality view "if
  scientifically useful".
- **Decision:** Do not report a matched-cardinality view: Full/Sparse predicted
  write-set sizes exist only on the exposed HELD_OUT_TEST ten, and matching K to
  the observed proxy cardinality would leak the reference into the method.
  Fixed-K tables are the honest default.
- **Rationale:** preserving the strict data rule and the exposed split.
- **Impact:** documented in `reports/CHEAP_BASELINES_V1_REPORT.md` §7.