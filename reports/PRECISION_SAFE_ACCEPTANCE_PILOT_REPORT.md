# Precision-Safe Acceptance Pilot (DEVELOPMENT, AUTHORIZED 2026-09-18)

**Calls:** 357/357  **Tokens:** 176060  **Cost:** $0.0648  **Wall:** 718.8s  **Stop:** none

Arms: A = frozen Route-B verifier (4 calls/task), B = RANK->VERIFY->VARIABLE ACCEPT (2 calls/task), C = analytic references.

## djangocms DEV (sparse F1 0.186)

| B | Arm | ORR | cand-prec | naive-F1 | oracleRev-F1 | OracleAdd-gap | valid/tasks |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | A | 0.071 | 0.375 | 0.219 | 0.227 | 0.121 | 30/30 |
| 1 | B | 0.143 | 0.348 | 0.263 | 0.292 | 0.310 | 30/30 |
| 3 | A | 0.122 | 0.158 | 0.216 | 0.267 | 0.143 | 30/30 |
| 3 | B | 0.147 | 0.257 | 0.256 | 0.304 | 0.210 | 30/30 |
| 5 | A | 0.223 | 0.141 | 0.218 | 0.304 | 0.189 | 30/30 |
| 5 | B | 0.152 | 0.250 | 0.260 | 0.317 | 0.208 | 30/30 |
| 10 | A | 0.284 | 0.132 | 0.221 | 0.364 | 0.264 | 30/30 |
| 10 | B | 0.157 | 0.239 | 0.263 | 0.329 | 0.212 | 30/30 |

## saleor DEV (sparse F1 0.1732)

| B | Arm | ORR | cand-prec | naive-F1 | oracleRev-F1 | OracleAdd-gap | valid/tasks |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | A | 0.028 | 0.182 | 0.188 | 0.202 | 0.081 | 30/30 |
| 1 | B | 0.132 | 0.269 | 0.235 | 0.269 | 0.274 | 30/30 |
| 3 | A | 0.100 | 0.125 | 0.194 | 0.256 | 0.138 | 30/30 |
| 3 | B | 0.170 | 0.141 | 0.209 | 0.294 | 0.202 | 30/30 |
| 5 | A | 0.128 | 0.088 | 0.174 | 0.256 | 0.117 | 30/30 |
| 5 | B | 0.203 | 0.116 | 0.197 | 0.307 | 0.189 | 30/30 |
| 10 | A | 0.140 | 0.069 | 0.155 | 0.294 | 0.159 | 30/30 |
| 10 | B | 0.203 | 0.103 | 0.188 | 0.307 | 0.175 | 30/30 |

## Preregistered stop gate (B=5)

**Decision: PRECISION_SAFE_ACCEPTANCE_FAIL**

| Repo | c1 ORR>+0.05 | fold+ (>=3/5) | c3 naive-F1 | c4 cand-prec | c5 leak | c6 schema | c7 cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| djangocms | False (d -0.070) | False [0.0, 1.0, 1.0, 0.0, 0.0] | True (+0.043) | True (+0.109) | True | True | True |
| saleor | True (d +0.075) | True [0.5, 1.0, 0.5, 1.0, 1.0] | True (+0.023) | True (+0.028) | True | True | True |

Schema rate (dispatched calls): 1.0 (0 invalid / 357); zero partial credit: True; Arm B calls/task: 2.0

Machine-readable: reports/precision_safe_acceptance_metrics.json, reports/precision_safe_acceptance_gate.json
Raw calls: research/precision-safe-acceptance-pilot/runs/