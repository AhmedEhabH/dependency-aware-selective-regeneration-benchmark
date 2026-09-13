# Future Fine-Tuning Readiness (research plan only — NOT executed)

**Date:** 2026-09-13
**Status:** PLAN ONLY. No fine-tuning is performed in this task. This note
records the readiness requirements for a future fine-tuning stage so the
evidence corpus is designed from the start as **RealCommitImpactDataset-v1**
with explicit TRAIN / VALIDATION / HELD-OUT TEST splits, and held-out test
cases are permanently reserved and **NEVER** enter any future fine-tuning.

> **M4A-1 status update (2026-09-13):** the deterministic
> **RealCommitImpactDataset-v1 miner** is now implemented and frozen (branch
> `research/real-commit-impact-dataset-v1-miner-01`): versioned record
> schema, v1 eligibility/exclusion rules, parent-commit candidate universe +
> dependency graph, physical public/hidden separation, and the
> `intent_mentions_changed_path` leakage detector. **6 MINER_DEV cases** are
> materialized and permanently excluded from all final metrics.
>
> **M4A-2 status (2026-09-13): the scientific corpus + split freeze are now
> COMPLETE / AUDITED.** **40 clean scientific djangoCMS cases** were mined with
> the frozen M4A-1 miner/schema/leakage barrier (ZERO LLM/API calls), and the
> split assignment (TRAIN 24 / VALIDATION 6 / HELD_OUT_TEST 10, seed
> `20260913`, metadata-only) was frozen **before** any model results. Held-out
> evaluation is M4A-3 under a separately frozen protocol. Legacy frozen
> benchmark runs remaining: ZERO; new RealCommitImpactDataset scientific
> evaluation: PENDING.

## IMPORTANT: two label kinds must NOT be conflated

M4A-1 stores the **automatically mined observed change-set proxy** — the set
of production files whose content differs between the parent and target
commits. This is an **OBSERVED CHANGE-SET PROXY**, never a semantic gold
label. The miner does **NOT** fabricate P/R/V/H (PRESERVE / REGENERATE /
VALIDATE / HUMAN_REVIEW) action labels from the Git diff: a historical diff
does not prove the semantic action per file. **Optional later human semantic
action adjudication** (per-file P/R/V/H labels) is a separate, future step and
must be recorded as such. The table below marks `full action labels` /
`sparse labels` as future adjudication fields, NOT as outputs of the miner.

## Dataset: RealCommitImpactDataset-v1 (design target)

The future corpus must be designed from the start as a single versioned
dataset, **RealCommitImpactDataset-v1**, with explicit, frozen splits:

| Split | Purpose | Constraint |
|---|---|---|
| **TRAIN** | fine-tuning | the only split any future training procedure may read |
| **VALIDATION** | early stopping / hyperparameter selection | may be read by training loops, never for final metrics |
| **HELD-OUT TEST** | final evaluation only | **NEVER** used in any future fine-tuning; reserved and immutable before training begins |

Held-out test examples must be assigned at dataset construction time (recorded
in the `split` field), not selected after training. No example moves between
splits after `RealCommitImpactDataset-v1` is frozen.

## Target record schema (per example)

| Field | Description |
|---|---|
| `repository` | repository identifier (e.g. djangoCMS 5.0.0) |
| `parent_commit` | the pre-change commit SHA |
| `target_commit` | the post-change commit SHA |
| `requirement/change-intent text` | the requirement change text (as a natural-language intent) |
| `intent source` | provenance of the requirement (e.g. issue/PR text, changelog) |
| `candidate universe` | the frozen candidate path set for the repository |
| `dependency features` | automatic AST dependency-graph features (if used) |
| `observed change-set proxy` | the observed changed-file set used as evaluation proxy |
| `full action labels` | **FUTURE adjudication** — per-candidate full action labels (P/R/V/H); NOT mined from Git diff |
| `sparse labels` | **FUTURE adjudication** — the sparse non-PRESERVE labels (R/V/H; PRESERVE-by-omission) |
| `change type` | change taxonomy (bugfix/feature/refactor/... ) — conservative intent-derived, UNKNOWN allowed |
| `provenance hashes` | hashes pinning each input artifact |
| `split` | explicit `TRAIN` / `VALIDATION` / `HELD-OUT TEST` assignment |

## Split hygiene (MANDATORY)

- The **HELD-OUT TEST** split is reserved at dataset construction and is
  immutable.
- Held-out test examples must **NEVER** be used in any future fine-tuning,
  including pre-training, continued pre-training, or instruction tuning of the
  same model family.
- Evaluation against the HELD-OUT TEST split happens exactly once per model
  configuration, at the end.

## Guardrails

- No fine-tuning is performed in the current task.
- Any future fine-tuning is a separate, separately-authorized milestone
  (Pillar 5 of `../docs/MSC_RESEARCH_ROADMAP_2026_2027.md`).
- The current six scenarios remain a CURATED DEVELOPMENT / MECHANISM SET and
  are not claimed as an unbiased held-out evaluation set.
- The dataset construction (Pillar 3) must precede any fine-tuning; fine-tuning
  without a frozen split assignment is prohibited.
