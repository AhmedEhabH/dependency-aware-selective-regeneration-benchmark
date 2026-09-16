# Route B — Bounded-Verifier Pilot (DEVELOPMENT only)

**Date:** 2026-09-17  **Calls:** 30/30  **Valid:** 30
**Tokens:** 6748  **Cost:** $0.0023
Frozen: qwen3-coder @ deepinfra/turbo, temp 0, cap 512, CIA ranker.

| run_id | B | valid | recovered/top-missed | tokens | cost |
|---|---|---|---:|---:|---:|
| vp-djangocms-rc-890451d3f92e-b1 | 1 | True | 0/0 | 176 | 0.0001 |
| vp-djangocms-rc-890451d3f92e-b3 | 3 | True | 1/1 | 194 | 0.0001 |
| vp-djangocms-rc-890451d3f92e-b5 | 5 | True | 1/1 | 212 | 0.0001 |
| vp-djangocms-rc-7fbb344766d9-b1 | 1 | True | 0/0 | 199 | 0.0001 |
| vp-djangocms-rc-7fbb344766d9-b3 | 3 | True | 0/0 | 216 | 0.0001 |
| vp-djangocms-rc-7fbb344766d9-b5 | 5 | True | 0/0 | 235 | 0.0001 |
| vp-djangocms-rc-241d1cbe47a6-b1 | 1 | True | 0/0 | 210 | 0.0001 |
| vp-djangocms-rc-241d1cbe47a6-b3 | 3 | True | 0/1 | 226 | 0.0001 |
| vp-djangocms-rc-241d1cbe47a6-b5 | 5 | True | 0/1 | 245 | 0.0001 |
| vp-djangocms-rc-f509572a260c-b1 | 1 | True | 0/0 | 165 | 0.0001 |
| vp-djangocms-rc-f509572a260c-b3 | 3 | True | 0/0 | 184 | 0.0001 |
| vp-djangocms-rc-f509572a260c-b5 | 5 | True | 0/0 | 204 | 0.0001 |
| vp-djangocms-rc-9488d4017519-b1 | 1 | True | 0/0 | 189 | 0.0001 |
| vp-djangocms-rc-9488d4017519-b3 | 3 | True | 1/1 | 207 | 0.0001 |
| vp-djangocms-rc-9488d4017519-b5 | 5 | True | 1/1 | 224 | 0.0001 |
| vp-djangocms-rc-3981f92d5c6d-b1 | 1 | True | 1/1 | 296 | 0.0001 |
| vp-djangocms-rc-3981f92d5c6d-b3 | 3 | True | 1/1 | 315 | 0.0001 |
| vp-djangocms-rc-3981f92d5c6d-b5 | 5 | True | 1/1 | 333 | 0.0001 |
| vp-djangocms-rc-3a358b840d10-b1 | 1 | True | 1/1 | 174 | 0.0001 |
| vp-djangocms-rc-3a358b840d10-b3 | 3 | True | 2/2 | 189 | 0.0001 |
| vp-djangocms-rc-3a358b840d10-b5 | 5 | True | 2/2 | 206 | 0.0001 |
| vp-djangocms-rc-16e3bbecb7c9-b1 | 1 | True | 1/1 | 182 | 0.0001 |
| vp-djangocms-rc-16e3bbecb7c9-b3 | 3 | True | 1/1 | 198 | 0.0001 |
| vp-djangocms-rc-16e3bbecb7c9-b5 | 5 | True | 2/2 | 216 | 0.0001 |
| vp-djangocms-rc-7bb471c8e1e4-b1 | 1 | True | 0/0 | 262 | 0.0001 |
| vp-djangocms-rc-7bb471c8e1e4-b3 | 3 | True | 0/0 | 281 | 0.0001 |
| vp-djangocms-rc-7bb471c8e1e4-b5 | 5 | True | 0/0 | 304 | 0.0001 |
| vp-djangocms-rc-733c377ab37e-b1 | 1 | True | 0/0 | 212 | 0.0001 |
| vp-djangocms-rc-733c377ab37e-b3 | 3 | True | 0/0 | 236 | 0.0001 |
| vp-djangocms-rc-733c377ab37e-b5 | 5 | True | 0/0 | 258 | 0.0001 |

## Decomposition

- First-pass omission: Sparse FNs (per task in results JSON).
- Ranking headroom: Oracle@B recovered FNs (Route B V2).
- Verifier recovery@B: verifier-selected ∩ true missed.
- Verifier vs CIA-alone@B: does the verifier add over the ranker?
- InspectAll: all missed at full reconsideration.

Full machine-readable results: research/transparency/route_b_verifier_pilot/

## Decomposition summary (aggregate, task-level)

| B | tasks with >=1 missed in top-B | verifier recovered | missed in top-B | verifier ORR | Oracle-in-top-B ORR |
|---|---:|---:|---:|---:|---:|
| 1 | 3 | 3 | 3 | 1.000 | 1.000 |
| 3 | 6 | 6 | 7 | 0.857 | 1.000 |
| 5 | 6 | 7 | 8 | 0.875 | 1.000 |
