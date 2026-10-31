# Track 04 — G2 ofetch #24 Diagnostic Behavioral Oracle (v1)

**Status:** Candidate, NOT YET RUN on historical builds. Public diagnostic oracle, NOT a blinded scientific holdout.

## Frozen historical identity

| Field | Value |
|---|---|
| Repository | `unjs/ofetch` (historical package name `ohmyfetch`) |
| Issue | https://github.com/unjs/ofetch/issues/24 |
| Issue created | 2021-11-08T19:58:07Z |
| Pull request | https://github.com/unjs/ofetch/pull/25 |
| PR created | 2021-11-08T20:10:24Z |
| PR merged | 2021-11-10T12:00:12Z |
| Pinned parent | `a183b02048c5323bcb79f2a03862008466771104` |
| Pinned squash/reference | `7e1b54d1363ba3f5fe57fe8089babab921a8e9ea` |
| Changes in squash | `src/fetch.ts`, `test/index.test.mjs` only |
| Package manager | Historical Yarn Classic lockfile; runner pins Yarn 1.22.22 |
| Runtime | CI Node.js 18.20.8 (diagnostic, not era-authentic) |

## Public issue intent (not hidden)

The reporter describes repeated `baseURL` concatenation when a request retries after a failure. The issue has a minimal reproducer. The current GitHub issue body was retrieved after the fact; **its edit-history / text-as-of-request has not been independently audited**. An Issue-creation timestamp alone does not establish unchanged historical text.

## Oracle (diagnostic only)

- Execute the built `ohmyfetch` library with an in-memory `fetch` transport: first HTTP 503, then HTTP 200. No internet request from the oracle.
- Request string is `404`, base URL `https://oracle.invalid/`, retry=1.
- Classify exact expected first request and duplicated base URL on retry as `RED_DUPLICATED_BASEURL`.
- Classify both request URLs equal to expected as `GREEN_STABLE_BASEURL`.
- Any other behavior, build/import error, missing response, or missing run is `STOP`, not RED.
- Repeat each arm's oracle twice, compare byte-identical evidence.
- Run unchanged historical `yarn test` and `yarn tsc --noEmit` on **both** exact refs to check P2P; require both to succeed.
- Reject dirty historical tracked sources and package lock changes.
- Preserve all raw logs, exit codes and provenance. Do not modify source or test thresholds to pass.

## Gate interpretation

`DIAGNOSTIC_RED_GREEN_AND_NATIVE_P2P_PASS` means this **single public diagnostic** reproduced the known bug on Parent and did not reproduce it on the reference while the historical test suite and tsc checks passed.

This does **NOT** mean: independent hidden F2P, complete P2P characterization, private evaluator custody, parent-time source editing verified, leakage freedom, successful selective regeneration, or fair comparison.

The published workflow and test are visible to anyone who views the research branch. They **must not** be reused as hidden F2P or claimed to be blinded holdout. A separate private evaluator-controlled oracle, as-of request provenance, reproducibility across environment variants and frozen task receipt remain required for scientific task admission.

## Contingencies and stop rules

If the 2021 dependency graph fails under the Node 18 runner, record the exact incompatibility and STOP. Do not silently re-resolve the lockfile, update packages, enable lifecycle scripts, weaken native tests, or retry until success. Such remediation needs an explicitly documented follow-up gate and no alteration to previously frozen records.

This task does not require Docker or model inference. Changes are restricted to the separate Track04 branch; do not merge or edit `main` without approval.
