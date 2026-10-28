# D3 test-informed repair control — research milestone

- **State:** `D3_COMPLETE_CONTROL_PASS`
- **Official A5-R1:** `STOP` (unchanged)
- **D2 baseline:** 1/3 F2P, 103/103 selected P2P, 318 JUnit invocations
- **D3 intervention:** move default token creation inside tokenTargetUrl guard; reject non-APP_PAGE relative extension without appUrl
- **D3 F2P stable:** `3/3`
- **D3 P2P stable:** `103/103`
- **Verified physical invocations:** `318`
- **D3 over D2 SHA-256:** `01cd8d20d8efe3810022d6b8b04e0775145bed188faa4861f7715094f8e9df6f`

## Scientific limits
- This was engineered *after inspecting frozen F2P failures*; it is not blind model pass@1, independent regeneration evidence, or a competitor comparison.
- The 3 repeated pytest invocations per node shared DB/runtime. Results do not prove independent replicates, complete code quality, mutation score, or security.
- Raw execution logs and test XML remain local; no logs, tokens, environment variables or DB identifiers are embedded in this public report.
