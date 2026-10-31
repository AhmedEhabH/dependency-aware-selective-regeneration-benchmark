# G1.1 — Engineering-only gate

G1 v1 is immutable; this is a separate v2 schema for TypeScript declaration coverage. Unit tests include 11 prior synthetic fixtures, one new UTF-16 source-span/hash test, and one empty-file edge-case test. The G1.1 workflow requires the pinned historical parent, two identical outputs, no file/import edge drift versus v1, nonzero units in all seven files, and SHA verification of every real-parent unit against Git blobs.

This is not a graph-recall benchmark: TypeScript alias resolution, decorators, conditional imports, reflection, runtime-only dependencies and unknown module forms require additional adversarial tests. No F2P/P2P, no regeneration, no inference.

Task-admission status: `0` qualified cases. Diagnostic lead tinybench #54 / PR #55 still has `ISSUE_BODY_AS_OF_UNVERIFIED`, parent P2P and independent red/green oracle unproven.
