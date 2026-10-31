# Track 04 — Baseline timing-failure forensic record

Date: 2026-10-31. Status: **Observed native-test nondeterminism; mechanism diagnosed from historical source; no source changes and no model inference.**

## Frozen provenance

- Upstream: `tinylibs/tinybench`, parent `c9816afede719138d581b66bdde1188346010f53`.
- Research branch: `research/track04-typescript-smoke-2026-10-31`.
- Native first run: [41221022535](https://github.com/AhmedEhabH/dependency-aware-selective-regeneration-benchmark/actions/runs/41221022535), 54/54, typecheck/build 0.
- Native second run: [41228941606](https://github.com/AhmedEhabH/dependency-aware-selective-regeneration-benchmark/actions/runs/41228941606), 53/54, typecheck/build 0; artifact `13052404021`, digest `sha256:74022bbc7640a524fa89d1496db23438bc4e6b1e12b2d8026284dc34ef2cd2f9`.
- Failed test: `test/index.test.ts:42`, `hrtimeNow() basic (async)`. Observed `1000.0770493892483` versus target `1000`, difference `0.0770493892482591`, Vitest tolerance `0.05` for `toBeCloseTo(1000,1)`.

## Source-level diagnosis

Historical test `test/index.test.ts` runs an async `Bench` with 16 iterations and checks `throughput.mean * period ~= 1000`. Historical implementation `src/task.ts:402–417` computes `totalTime=sum(latencySamples)`, `latencyStatistics` from latency samples, and `throughputStatistics` from **per-sample reciprocals** `1000/sample`. `period` (line 436) is `totalTime/runs`, while `throughput.mean` is arithmetic mean of reciprocals, not `1000/mean_latency`.

For strictly positive latencies `L_i`, the product equals `1000 * mean(L_i) * mean(1/L_i) >= 1000` by Cauchy–Schwarz/AM-HM, with equality only at constant latency. The test incorrectly expects a near-identity with a tight tolerance; variation from scheduling/timing can push the product across threshold. This **explains** the observed nonrepeatability without demonstrating that the timing environment alone caused it.

## Scientific treatment

- The native reference is not repeatedly all-green; do not report it as such.
- Do not widen upstream assertions, skip the test, or silently retry until green.
- For separate, task-bound F2P/P2P experiments, precommit independent deterministic oracles and report whole-suite reference failures separately.
- Do not score any RM-CSS candidate on an unstable oracle. Any exclusion/triage must be prospective, symmetric across arms, and recorded.
- Source: https://github.com/tinylibs/tinybench/blob/c9816afede719138d581b66bdde1188346010f53/src/task.ts and /test/index.test.ts.
