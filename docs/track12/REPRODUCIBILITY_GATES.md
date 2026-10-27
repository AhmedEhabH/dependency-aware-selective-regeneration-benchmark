# Reproducibility and STOP gates

1. Preserve frozen plan SHA256, original R7/R8 drivers, exact source/image/tree identity.
2. For a separate authorized controls-only attempt, set the stage-root import path
   in the PROCESS environment, without changing frozen harness/driver sources.
3. Proposed Windows process PYTHONPATH = `<STAGE_ROOT>`
   followed, if required, by `<STAGE_ROOT>\src`.
   First verify import resolution independently. This is a proposal, NOT qualification.
4. Use original `--audit-root <AUDIT_ROOT>` path, not a nested run directory.
5. Require a certified exclusive execution slot, PostgreSQL ownership, memory/disk
   admission, frozen controls and event-level receipts. Do not run on snapshot alone.
6. Expected controls: NEG 9 FAIL_ASSERTION; FULL_REFERENCE 9 PASS; RM_CSS 9 according
   to its frozen contract; report actual JUnit XML and SHA256, never just expectations.
7. No auto-retry, patching, comparator expansion, new paid scientific API calls,
   or cross-arm result reuse after a scientific STOP.
8. Option B is sealed; M02-E comparator execution needs its own authorization.
9. Prespecify fair comparison classes, input rights, selection metrics and costs
   before running new outcomes. External/seed-edit methods are contextual if unmatched.

