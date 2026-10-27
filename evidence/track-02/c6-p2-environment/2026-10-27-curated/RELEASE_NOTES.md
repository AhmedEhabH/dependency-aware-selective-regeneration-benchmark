# Track 02 — C6 Historical Environment Qualification

Published engineering evidence, 27 October 2026.

- Frozen population: 22,699 Saleor commits inspected; 174 C4+C5 candidates, not 22,699 runnable tests.
- C6 v0.4 regression suite: 90/90 PASS; evidence is engineering verification, not candidate behavioral results.
- P2 historical-environment probes: PASS with a pinned Python 3.9.25 substitute (historical declaration Python 3.9.14) and a PostgreSQL Unix-socket sidecar.
- Candidate C6 execution: 0/174. C7 generated-code evaluation: NOT RUN.
- Remaining gate: implement and test a narrowly scoped database-service adapter in the runner, validate the corrected P2 plan and its hash, then obtain prospective operator authorization for one P2 pilot.
- The previously drafted v0.5 example contained invalid JSON and was intentionally excluded pending regeneration and validation.
- The original operational handoff archives remain local. This public snapshot normalizes documentation transfer labels; the publication manifest records both local-source and published-file SHA-256 values. No scientific outcomes or executable oracle implementation have been rewritten.
- Never interpret readiness, a prepared plan, or offline dependency probes as successful behavioral qualification.