# M17 runtime failure owner review — progress

TODO_UI_UNAVAILABLE — native todowrite is not exposed.

- [x] R0.1 Verify branch/base/clean tree.
- [x] R0.2 Verify receipt counts, first failure, and frozen contract.
- [x] R1.1 Hash evidence and preserve a path-only inventory.
- [x] R1.2 Recheck harness hashes against freeze.
- [x] R2.1 Read target commit date, Python declarations, Docker and CI.
- [x] R2.2 Trace frozen runtime assignment to its source authority.
- [x] R2.3 Count per-commit and per-unit Python compatibility across 144.
- [x] R3.1 Compare original lock and frozen lock source identities.
- [x] R3.2 Trace installed wheels and compare vendored source bytes.
- [x] R4.1 Hash and inspect local PyXB/PyXB-X wheels without importing them.
- [x] R4.2 Check prior compatibility amendment scope.
- [x] R5.1 Produce reproducible 144-row blast-radius CSV.
- [x] R5.2 Conservatively assess other source/compatibility risks.
- [x] R6.1 Select primary classification from evidence.
- [x] R7.1 Evaluate all five options and evidence-led next action.
- [x] R8.1 Run audit-only positive and negative policy checks.
- [x] R8.2 Verify input immutability.
- [x] R9.1 Write MD/JSON owner packet and stop report.
- [x] R9.2 Update live status and verify synchronization.
- [x] R10.1 Create LIGHT <=50 MiB; verify members and hash.
- [x] R10.2 Report exact final state and stop without remediation.

Population scan estimate: 219 small pyproject Git reads plus selected vendored blobs,
144 local lock reads, no task imports, no network, no Docker; expected minutes.
The mission-specific LIGHT-only contents supersede the generic full-repository export.




