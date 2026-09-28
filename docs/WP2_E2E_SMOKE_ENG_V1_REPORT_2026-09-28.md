# WP-2 E2E Smoke ENG v1 — Report (2026-09-28)

Final token: **`E2E_SMOKE_FLOOR_EFFECT`** (SG1–SG3 PASS, SG4 floor not met).

## Mandatory wording
- Smoke = pipeline validation on DEV_TRAIN_ENG (engineering split). n = 14. No comparative claim between RM-CSS and Agent is made or supported.
- RM-CSS scopes are out-of-fold DEV predictions (realization A); Agent scopes are protocol-v3 selections run on DEV for this Smoke.

## Episode status per arm
| Arm | APPLIED | INVALID_AFTER_REPAIR | NO_SCOPE |
|---|---|---|---|
| GOLD_HARD | 1 | 13 | 0 |
| RMCSS_HARD | 1 (shared diff with PLACEBO for 2d45) | 12 | 1 |
| AGENT_HARD | 3 | 11 | 0 |
| PLACEBO_HARD | 3 | 11 | 0 |

## Five dimensions (descriptive)
1. **Impact correctness** (evaluator-only, descriptive): scope/edited-files P/R/F1 vs GOLD_AT_PARENT not claimed; recorded in evaluations.
2. **Functional**: F2P_TASK pass — GOLD 0/14, RMCSS 0/14, AGENT 1/14, PLACEBO 0/14.
3. **Preservation**: P2P-S pass — GOLD 12, RMCSS 12, AGENT 13, PLACEBO 13; P2P-U200 — GOLD 14, RMCSS 14, AGENT 13, PLACEBO 14. Added Catch: 0 (no P2P-S PASS ∧ P2P-U200 FAIL episodes among defined).
4. **Architecture**: 0 out-of-scope edits; 0 test edits; 0 MODEL_EDIT_NO_MIGRATION.
5. **Efficiency**: Agent scopes $0.348 (16 tasks); Smoke generation $0.257 (56 episodes); evaluation zero-API. API calls: 55 expected; actual initial+repair calls recorded in ledger.

## RESOLVED per arm
GOLD 0/14 | RMCSS 0/14 | AGENT 1/14 | PLACEBO 0/14.

## Paired task × arm matrix (RESOLVED / F2P / P2P-S / P2P-U200)
Only APPLIED episodes have real evaluations; the rest are BY_CONSTRUCTION (F2P FAIL).
- e03ee76d2b89 AGENT_HARD: RESOLVED (PASS/PASS/PASS).
- All other APPLIED episodes: F2P FAIL (model patch did not make behavioral F2P nodes pass).

## Per-task notes
- Most model outputs (47/56) failed the frozen SEARCH/REPLACE validator (preamble prose / non-matching SEARCH) → INVALID_AFTER_REPAIR (no repair succeeded). This is the measured model format-adherence behavior, not an instrument defect (G-POS controls prove the evaluator reproduces target trees).
- 2d45 RMCSS_HARD shares the identical final diff with PLACEBO_HARD (D39 reuse).

## Smoke gates
- SG1 instrument validity: PASS (B11 controls PASS; G-LEAK 0; 0 out-of-scope; evidence hashed).
- SG2 completion: PASS (56/56 terminal; 0 instrument anomalies).
- SG3 spend: PASS (agent $0.348 ≤ $1.00; smoke $0.257 ≤ $4.50; total $0.605 ≤ $5.50).
- SG4 floor: **FAIL** — GOLD_HARD RESOLVED = 0/14 (< 1/14).

## Token
`E2E_SMOKE_FLOOR_EFFECT`.