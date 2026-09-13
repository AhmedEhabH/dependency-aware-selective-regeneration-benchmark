# Future Fine-Tuning Readiness (research plan only — NOT executed)

**Date:** 2026-09-13
**Status:** PLAN ONLY. No fine-tuning is performed in this task. This note
records the readiness requirements for a future fine-tuning stage so the
evidence corpus is designed from the start as **RealCommitImpactDataset-v1**
with explicit TRAIN / VALIDATION / HELD-OUT TEST splits, and held-out test
cases are permanently reserved and **NEVER** enter any future fine-tuning.

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
| `full action labels` | per-candidate full action labels (P/R/V/H) |
| `sparse labels` | the sparse non-PRESERVE labels (R/V/H; PRESERVE-by-omission) |
| `change type` | change taxonomy (bugfix/feature/refactor/... ) |
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
