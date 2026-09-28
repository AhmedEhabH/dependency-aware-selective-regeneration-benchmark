# MISSION-11 — E2E Smoke ENG v1 — STOP REPORT (2026-09-28)

> **ERRATUM 2026-09-28: token corrected to `E2E_SMOKE_INSTRUMENT_INVALID` — see docs/WP2_E2E_SMOKE_ENG_V1_ERRATUM_2026-09-28.md**

Final token: **`E2E_SMOKE_FLOOR_EFFECT`**

## 1. Executive verdict
CLOSED: first WP-2 E2E Smoke on DEV_TRAIN_ENG completed under the frozen
Mission-11 contract. The shared instrument is validated (G-FORMAT 39/39,
G-POS 3/3, G-NEG 3/3, G-LEAK 0, G-BUDGET ok). The frozen generator model
(qwen3-coder) failed the strict SEARCH/REPLACE format on 47/56 episodes
(INVALID_AFTER_REPAIR); only 8 applied. GOLD_HARD RESOLVED = 0/14, so the SG4
floor (≥ 1/14) is not met → `E2E_SMOKE_FLOOR_EFFECT`.

## 2. Scientific question
Does the frozen E2E generation + evaluation pipeline produce resolved
(functionally-correct + preservation-preserving) patches on the 14 ENG
behavioral tasks across the 4 HARD arms?

## 3. Dataset/split and forbidden data
DEV_TRAIN_ENG (14 behavioral tasks). No ASSAY_HOLDOUT / DEV_VALIDATION / MAIN /
INTERNAL_TEST / RESERVE generation. Symbol-only tasks listed, never generated.
Evaluator-only sets never entered generator prompts (G-LEAK 0).

## 4. Validation-gate table
B11 controls PASS (G-FORMAT 39/39 expressible byte-equal; G-POS 3/3 tree==target;
G-NEG 3/3; G-LEAK 0 blocking; G-BUDGET $1.32 ≤ $4.50). INSTRUMENT_READY.
C1 paid preflight PASS (credit $20.44, pricing frozen).
Smoke gates: **SG1 PASS · SG2 PASS · SG3 PASS · SG4 FAIL**.
- SG1 instrument validity: PASS (B11 controls PASS; G-LEAK 0; 0 out-of-scope; evidence hashed).
- SG2 completion: PASS (56/56 episodes terminal: APPLIED 8, INVALID_AFTER_REPAIR 47, NO_SCOPE 1; 0 instrument anomalies).
- SG3 spend: PASS (agent $0.371 ≤ $1.00; smoke $0.257 ≤ $4.50; total $0.628 ≤ $5.50).
- SG4 floor: FAIL (GOLD_HARD RESOLVED = 0/14 < 1/14).
Final token: **E2E_SMOKE_FLOOR_EFFECT**.
No comparative scientific claim between arms (or between RM-CSS and Agent) is supported by this Smoke.

## 5. Main result table
RESOLVED per arm: GOLD 0/14 | RMCSS 0/14 | AGENT 1/14 | PLACEBO 0/14.
F2P pass: GOLD 0, RMCSS 0, AGENT 1, PLACEBO 0. P2P-S pass: 12/13/13/13.
P2P-U200 pass: 14/14/13/14. Added Catch: 0. Spend (authoritative ledger):
agent $0.371 / smoke $0.257 / total $0.628 (ceiling $5.50).

## 6. Development vs confirmatory label
All evidence is DEVELOPMENT (DEV_TRAIN_ENG). No confirmatory claim.

## 7. Fair-comparison warning
No comparative claim between RM-CSS and Agent is made or supported.

## 8. Interpretation
The pipeline is instrument-valid (controls prove the evaluator reproduces
oracle trees). The floor effect is dominated by generator format-adherence:
the model emits preamble prose and non-exact SEARCH blocks, so most episodes
are INVALID_AFTER_REPAIR. The 1 AGENT resolution (e03ee76d2b89) shows the
pipeline CAN resolve when a valid patch is produced.

## 9. What the result does NOT mean
It does NOT validate the generator scientifically; it does NOT support any arm
comparison; it does NOT authorize Stage C / Pilot / holdout / MAIN.

## 10. Competitor/baseline implication
None: no ranking implied.

## 11. Threats/caveats
- Model format adherence to the frozen SEARCH/REPLACE format is low (47/56 invalid).
- n=14, single repository (Saleor), 1 replicate.
- 2d45 RMCSS/PLACEBO shared an identical (empty) final diff (D39 reuse).
- W2 (workers=2) NOT_TESTED.

## 12. Tests/audit
E2E instrument 12/12 unit tests; hardening 16/16; compiler 18/18; ruff clean;
controls all PASS; evidence hashes verified.

## 13. Documentation changed
LIVE_STATUS, PROGRESS, DECISIONS, Smoke draft, this report, freeze + report docs.

## 14. Git branch/commit/main status
branch `main`; result commit `fa7bbdd3`; origin/main equal; tag
`wp2-e2e-smoke-eng-v1-result-2026-09-28` (peels to fa7bbdd3) on origin.

## 15. Merge status
No merge required.

## 16. Tag
`wp2-e2e-smoke-eng-v1-result-2026-09-28` — DEV evidence only.

## 17. Export ZIP + SHA256
See PROJECT_EXPORT_READY / LIGHT_EXPORT_READY blocks (full `project-2026-09-28-0926.zip`,
light `project-LIGHT-2026-09-28-0925.zip`).

## 18. Where we are now
WP-2 E2E Smoke ENG v1 COMPLETE (FLOOR_EFFECT). Mission-11 one-shot fully executed
(A–D). Next: brain/Ahmed review → Pilot design.

## 19. ONE next action
WAIT_FOR_AHMED (Pilot design review). Do NOT start Stage C, Pilot, holdout, or MAIN.