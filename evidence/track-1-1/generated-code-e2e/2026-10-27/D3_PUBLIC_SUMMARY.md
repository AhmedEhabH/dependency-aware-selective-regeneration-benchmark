# D3 test-informed repair control — research milestone

- **State:** `INFRASTRUCTURE_STOP_BEFORE_REPAIR`
- **Official A5-R1:** `STOP` (unchanged)
- **D2 baseline:** 1/3 F2P, 103/103 selected P2P, 318 JUnit invocations
- **D3 intervention:** move default token creation inside tokenTargetUrl guard; reject non-APP_PAGE relative extension without appUrl
- **D3 F2P:** not qualified
- **D3 P2P:** not run or not qualified
- **Complete JUnit audit:** not qualified
- **D3 patch SHA:** no qualified repair receipt

## Scientific limits
- This was engineered *after inspecting frozen F2P failures*; it is not blind model pass@1, independent regeneration evidence, or a competitor comparison.
- The 3 repeated pytest invocations per node shared DB/runtime. Results do not prove independent replicates, complete code quality, mutation score, or security.
- Raw execution logs and test XML remain local; no logs, tokens, environment variables or DB identifiers are embedded in this public report.
