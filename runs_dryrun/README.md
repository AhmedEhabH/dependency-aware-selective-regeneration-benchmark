# runs_dryrun/ — frozen HISTORICAL fixture

**WARNING.** This directory is a **frozen historical tracked fixture**, NOT the
current candidate evidence. The name `runs_dryrun/` can be mistaken for the
current D9 48/48 exact-artifact dry-run proof — do NOT make that mistake.

## What this directory actually is

- 7 dry-run run records (`profile=smoke`), generated **2026-07-25**
  (`experiment_id.txt` = `exp-20260725-223726`).
- Source commit `0c831e3` is a **short SHA from that Smoke-era development
  history** — it is NOT `9ea02b35d58a3e4ef2d0d5d980e44fa53d8c079d`
  (the v0.9.22 D9 `D9_SOURCE_COMMIT` / future tag target) and NOT any current
  candidate source.
- Added to the repository at commit `b203b21`, retained ONLY for historical
  reproducibility of the Smoke-era dry-run pipeline.
- Contains 11 tracked files (this README is a 12th, documentation-only, tracked
  file); the original 11 are immutable — their Git blobs must never change.

## Current candidate evidence (authoritative)

The v0.9.22 D9 candidate proof is a **fresh exact-artifact 48/48 dry-run**
generated into a **fresh temporary/output directory** from
`dist/pilot-kaggle-upload.zip` (SHA-256
`913e8065a384effa2cf6b6a69f11e5840506644873fa54764c3cbe8ee5406d48`,
source commit `9ea02b35d58a3e4ef2d0d5d980e44fa53d8c079d`): 48 unique IDs,
repos 16/16/16, strategies 24/24, reps 24/24, 0 model calls / 0 tokens, every
record + `source_identity.json` == `9ea02b3…`, passing the canonical
`validate_pilot_dryrun_evidence`.

## Rules

- MUST NOT be used for Pilot launch authorization.
- MUST NOT be copied, moved, regenerated, deleted, or "refreshed".
- Current truth always lives in AGENTS.md + `docs/AI_ACCOUNT_TRANSFER_HANDOFF.md`.