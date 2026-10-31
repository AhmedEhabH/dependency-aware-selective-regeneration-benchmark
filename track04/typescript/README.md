# Track04 TypeScript Native Readiness

## Repository identity

Research branch: research/track04-typescript-smoke-2026-10-31

Research base SHA: 1661ec215ede6ae96e82735148db4febffb21580

Target project: tinylibs/tinybench

Historical upstream SHA: c9816afede719138d581b66bdde1188346010f53

## Scientific scope

This is a native TypeScript environment smoke test.

It verifies:

1. Historical dependency installation.
2. TypeScript typecheck.
3. Existing Vitest test suite.
4. Existing project build.
5. Reproducible upstream provenance.

## Exclusions

This workflow does not:

- Invoke any LLM.
- Perform RM-CSS inference.
- Generate or modify target project code.
- Run a selected-regeneration experiment.
- Claim F2P or P2P success.
- Modify any frozen research protocol.
- Modify research Tracks 1.1, 1.2, 02, or 03.

## Research interpretation

Passing native tests establishes environment readiness only.

It is not evidence that RM-CSS successfully regenerates TypeScript.

The TypeScript adapter must be implemented and validated separately.

Historical issue and PR references are diagnostic until they pass
the preregistered leakage and behavioral qualification gates.

NestJS remains the previously preregistered cross-language
external-validity candidate.

The tinybench experiment is a separate diagnostic readiness track.