# Multi-track Git and scientific evidence policy (proposed, NOT active until merged)

## Branch responsibilities

- `main`: conservative, approved project baseline. Never a working experiment branch.
- Track 1.1: OPWS, patch qualification, generated-code F2P/P2P and total costs; maintain original source protocol and append-only failure ledgers.
- Track 1.2: comparator replication, fairness matrices and fair input/cost parity; do not change M02 execution authorization via merges.
- Track 02: full-history census, eligibility, prospective requirement provenance, leakage qualification; keep frozen filters and attribution immutable.
- Track 03: scientific defense, proposal, seminar, claim ledger and limitations; do not certify upstream PASS without verified raw receipts.

Use current owner-named work branches as-is. Do not create or rename canonical track branches without owner confirmation of their local `git remote`, `HEAD`, worktree, and pending changes. The branch names above are logical track identities, NOT an assertion that corresponding Git refs already exist.

## Promotion gates for ALL tracks

1. Trace: what changed and who/which track owns it; base and head commit SHA, affected files, evidence manifest SHA-256, source provenance and frozen protocol version.
2. No scientific upgrade by documentation: distinguish `REPORTED`, `INDEPENDENTLY_AUDITED`, `PROTOCOL_QUALIFIED`, `BEHAVIORAL_PASS`, `GENERATED_E2E_PASS`, `STOP`, `NOT_RUN`. A reference-patch behavioral success must never be labeled generated-code success.
3. Evidence conservation: preserve original model responses, failed outputs, JUnit raw data, expenses, and exclusions; redact credentials/private materials BEFORE publication. SHA-256 of a local file proves identity, not open availability or behavioral correctness.
4. Tests: run tests proportional to touched code and its risk; no automatic costly/long OPWS, model API or full-history runs as routine PR checks.
5. Review: inspect conflicts, contracts, reproducibility, security, temporal leakage, licensing, and failure modes before promotion. STOP and UNKNOWN cannot be silently dropped.
6. Obtain explicit researcher approval for a merge to main. Never force-push, rewrite, auto-merge, or delete branches as part of this governance change.

## Scope of this governance proposal

Documentation-only; intentionally no application-code, frozen-data, CI-workflow, test, deployment, or production changes. The authoritative title/RQs/November registration plan are unchanged.
