# Future Fine-Tuning Readiness (research plan only — NOT executed)

**Date:** 2026-09-12
**Status:** PLAN ONLY. No fine-tuning is performed in this task. This note
records the readiness requirements for a future fine-tuning stage so the
evidence corpus is exported in a training-ready schema and held-out cases are
permanently reserved.

## Training-ready export schema (future real-commit corpus)

Any future fine-tuning must export the real-commit corpus in a
training-ready schema with, per example:

| Field | Description |
|---|---|
| `repository` | repository identifier (e.g. djangoCMS 5.0.0) |
| `parent_commit` | the pre-change commit SHA |
| `target_commit` | the post-change commit SHA |
| `requirement_text` | the requirement change text |
| `intent_source` | provenance of the requirement (e.g. issue/PR text, changelog) |
| `candidate universe` | the frozen candidate path set for the repository |
| `dependency graph / features` | the automatic AST dependency-graph features (if used) |
| `observed change-set proxy` | the observed changed-file set used as evaluation proxy |
| `full action labels` | per-candidate full action labels (P/R/V/H) |
| `non-PRESERVE labels` | the sparse non-PRESERVE labels (R/V/H) |
| `change type` | change taxonomy (bugfix/feature/refactor/... ) |
| `provenance hashes` | hashes pinning each input artifact |
| `split` | explicit train/val/test split assignment |

## Held-out reservation (MANDATORY)

- A fixed set of **held-out test cases** must be explicitly reserved and
  **NEVER** used in any future fine-tuning. This preserves an independent
  evaluation set and prevents train/test leakage.

## Guardrails

- No fine-tuning is performed in the current task.
- Any future fine-tuning is a separate, separately-authorized milestone.
- The current six scenarios remain a CURATED DEVELOPMENT / MECHANISM SET and
  are not claimed as an unbiased held-out evaluation set.
