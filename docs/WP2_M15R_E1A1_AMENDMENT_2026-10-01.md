# WP2 M15-R evaluator amendment E1A1 (2026-10-01)

**Rule:** `M15R_E1A1_GRAPHQL_DUPLICATE_TYPE_STARTUP_V1`

**Code:** `scripts/wp2_m15r_e1a1.py`. It wraps the frozen `evaluate_state_e1`, which itself stays unchanged.

**Record:** `research/wp2/m15r_v1/m15r_e1a1_amendment.json` (self-hashed).

## What happened

The original plan stopped at `Q16_S2_EVALUATE` with a resumable `EVAL_ERROR`. Q00–Q15 had passed. The failing state was task `saleor-rc-0a39d039049d`, identity `u_2d7cf6d90275`: the frozen S2 GOLD G0 patch from replicate r3.

All six active runs (C_0–C_2, U_0–U_2) behaved the same way:
- exit code 1;
- the same log;
- no JUnit written;
- the same final line from Graphene's schema builder:
  `AssertionError: Found different types with the same name in the schema: Date, Date.`

Why it happened:
- The generated patch declares `graphene.Date(...)`.
- The repository already registers its own GraphQL scalar named `Date`.
- So building the schema at import time fails.
- The parent tree starts normally (`parent_starts_ok = true`). The failure is therefore caused by the patch. It is a scientific outcome, a failed patch, not an infrastructure fault.

Why the frozen E1 rule did not catch it: E1 requires the traceback to name an edited file. Here the error is raised inside Graphene's own frames, so E1 classified it as `INFRA_UNCLASSIFIED`.

## Rule

E1A1 applies only when frozen E1 returns `INFRA_UNCLASSIFIED`, and only if all of the following hold:

- **A1.** The frozen E1 diagnostics of this call are valid, with decision `INFRA_UNCLASSIFIED`.
- **A2.** Every active run is missing JUnit.
- **A3.** `parent_starts_ok = true`, and the patch edits at least one file.
- **A4.** Every run has rc 1..127, a log, a traceback and an exception line.
- **A5.** In every run, the last log line is the generic Graphene duplicate-type schema assertion, and the log contains a `graphene/types/` frame. The rule does not special-case any type name, task or scalar.

**If the rule applies:** every node gets `missing` × 3, exactly the frozen E1 `PATCH_STARTUP_FAILURE` outcome.
- The scoring is F2P FAIL, not resolved.
- The taxonomy label is `PATCH_STARTUP_FAILURE`.
- The record carries `e1_decision = PATCH_STARTUP_FAILURE_E1A1` and an `e1a1_decision.json` provenance file.

**Otherwise:** the original error is re-raised, giving a resumable `EVAL_ERROR` for brain review.

## What is not changed

- No generated output, patch, scope, Agent output, episode, plan, ledger, freeze or tag.
- No earlier result (M14A, M14R, Pilot-A, M15-R S0/S1).
- No model or API call.
- The pre-amendment diagnostics stay where they were. E1A1 writes its own diagnostics to `evaluations/diagnostics_e1a1/`.

## Why the two S2 records already written are not re-evaluated

E1A1 returns the frozen E1 result unchanged whenever frozen E1 does not raise. It can only replace an `INFRA_UNCLASSIFIED` stop, and such a stop writes no record.

Every record written before the amendment is therefore exactly what E1A1 would have written:
- the S0 controls;
- 20 S1 unique records;
- the two S2 records, both `ALL_JUNIT_PRESENT`.

Re-running Docker on them would only add new random draws from flaky tests to fixed evidence. A01 checks their hashes.

## Continuation

`controller/plan_m15r_v1_e1a1.json` uses its own state file and the same evidence root:

`A00 tests → A01 verify → A02 S2 evaluate (E1A1) → A03 S2 gate → A04–A07 S3 (only if the gate passes) → A08 summary`

The original plan stays stopped at Q16 as a historical record. It is not resumed.
