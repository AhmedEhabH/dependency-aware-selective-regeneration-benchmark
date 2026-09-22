# WP-2 Smoke Proposal Review (2026-09-22)

Review of `research/wp2/wp2_smoke_candidate_proposal_2026-09-22.json` (the
previous 8-task proposal). This review is recorded; the old proposal is NOT
deleted and NOT called wrong.

## What the old proposal was

- Status: `SMOKE_CANDIDATE_PROPOSAL_ONLY`.
- Engineering planning proposal, **not** a scientific sample.
- Outcome-blind: selection used changed-file structure only (Group A/B/C,
  changed-file count diversity, SHA-256 salt tie-break) and never RM-CSS/Agent
  success, localization F1, or E2E outcome.
- It contained only **one** `STRONG_F2P_CANDIDATE` (the rest were
  `MODIFIED_TEST_CANDIDATE` or `NO_CHANGED_TEST_EVIDENCE`).

## Assessment

- **Strength:** outcome-blindness. The selection did not leak selector or
  generator performance into the Smoke set.
- **Limitation:** it was created before any executable Oracle Confirmation. A
  Smoke run must exercise the full F2P/P2P chain, which requires
  **evaluator-valid** tasks; structural candidacy alone is not enough.

## Policy going forward

- After Oracle Confirmation, the final Smoke set should **preferentially contain
  confirmed evaluator-valid F2P tasks** (i.e., `PRIMARY_BEHAVIORAL_F2P_ELIGIBLE`
  where available).
- Keep at least one **migration/config-heavy** case for environment stress if it
  is executable and environment-valid.
- Keep at least one **P2P-only / no-changed-test** case only if useful for
  harness negative-control coverage; it must not dilute the F2P feasibility
  check.
- The final Smoke set is frozen **only after** this mission's oracle evidence
  (proposal v2 in `research/wp2/wp2_smoke_candidate_proposal_v2_2026-09-22.json`
  and `docs/WP2_SMOKE_SELECTION_V2_2026-09-22.md`).

## Recommendation

Replace the Smoke selection basis from structural candidacy to
oracle-confirmed evaluator validity once Wave A/B evidence is available,
keeping the outcome-blind determinism that made the original proposal sound.