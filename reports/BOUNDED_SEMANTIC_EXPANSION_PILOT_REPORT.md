# Bounded Semantic Expansion Pilot (DEVELOPMENT, AUTHORIZED 2026-09-18)

**Calls:** 300/300  **Tokens:** 106325  **Cost:** $0.0444  **Wall:** 553.6s  **Stop:** none

Arms: A = frozen Route-B verifier (4 calls/task), B = expanded-pool bounded rerank/verify (1 call/task), C = analytic references.

## djangocms DEV (sparse F1 0.4324)

| B | Arm | ORR | cand-prec | naive-F1 | oracleRev-F1 | OracleAdd-gap | valid/tasks |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | A | 0.022 | 0.167 | 0.425 | 0.453 | 0.079 | 30/30 |
| 1 | B | 0.072 | 0.185 | 0.423 | 0.484 | 0.194 | 27/30 |
| 3 | A | 0.022 | 0.051 | 0.364 | 0.453 | 0.047 | 30/30 |
| 3 | B | 0.183 | 0.123 | 0.367 | 0.532 | 0.225 | 27/30 |
| 5 | A | 0.111 | 0.143 | 0.396 | 0.503 | 0.155 | 30/30 |
| 5 | B | 0.250 | 0.105 | 0.327 | 0.568 | 0.296 | 27/30 |
| 10 | A | 0.139 | 0.086 | 0.324 | 0.522 | 0.197 | 30/30 |
| 10 | B | 0.290 | 0.098 | 0.302 | 0.602 | 0.371 | 27/30 |

## saleor DEV (sparse F1 0.1854)

| B | Arm | ORR | cand-prec | naive-F1 | oracleRev-F1 | OracleAdd-gap | valid/tasks |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | A | 0.135 | 0.368 | 0.247 | 0.266 | 0.267 | 30/30 |
| 1 | B | 0.185 | 0.310 | 0.256 | 0.287 | 0.339 | 27/30 |
| 3 | A | 0.229 | 0.263 | 0.279 | 0.349 | 0.314 | 30/30 |
| 3 | B | 0.295 | 0.230 | 0.286 | 0.398 | 0.407 | 27/30 |
| 5 | A | 0.334 | 0.256 | 0.304 | 0.416 | 0.380 | 30/30 |
| 5 | B | 0.357 | 0.179 | 0.270 | 0.452 | 0.439 | 27/30 |
| 10 | A | 0.341 | 0.141 | 0.237 | 0.434 | 0.384 | 30/30 |
| 10 | B | 0.487 | 0.152 | 0.256 | 0.519 | 0.514 | 27/30 |

## Preregistered stop gate (B=5)

**Decision: BOUNDED_SEMANTIC_NEGATIVE_FROZEN**

| Repo | c1 ORR>+0.05 | fold+ (>=3/5) | c3 naive-F1 | c4 leak | c5 cost |
|---|---:|---:|---:|---:|---:|
| djangocms | True (d +0.139) | True [1.0, 1.0, 0.5, 1.0, 1.0] | False | True | True |
| saleor | False (d +0.023) | True [1.0, 0.0, 0.5, 1.0, 0.0] | True | True | True |

Machine-readable: reports/bounded_semantic_expansion_metrics.json, reports/bounded_semantic_expansion_gate.json
Raw calls: research/bounded-semantic-expansion/runs/