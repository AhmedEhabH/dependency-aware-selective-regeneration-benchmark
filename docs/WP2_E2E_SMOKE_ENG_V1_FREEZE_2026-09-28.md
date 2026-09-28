# WP-2 E2E Smoke ENG v1 — Freeze (2026-09-28)

Authority: MISSION-11 §3 D30–D64. Tag `wp2-e2e-smoke-eng-v1-freeze-2026-09-28`.
Machine-readable: `research/wp2/e2e_smoke_eng_v1/smoke_freeze.json`.

## Population and arms
- 14 behavioral ENG tasks (DEV_TRAIN_ENG). Symbol-only tasks listed, never generated.
- Arms (all HARD): GOLD_HARD / RMCSS_HARD / AGENT_HARD / PLACEBO_HARD × 1 replicate.
- 56 planned episodes; 1 NO_SCOPE (`39b4138e8550` RMCSS_HARD — empty OOF predictions,
  intention-to-treat per D43/D46); 55 expected initial API calls (D38 reuse may reduce).

## Frozen components (SHA-256 in smoke_freeze.json)
- spec, modules, prompt template, intent source, evaluator sets, Harness V3 identity.
- Scope SHAs per arm:
  - GOLD_HARD `89fd623b…`
  - RMCSS_HARD `657f0c8d…`
  - AGENT_HARD `096a2312…`
  - PLACEBO_HARD `e78cb47a…`

## Budget
- Agent scopes spent $0.348 (ceiling $1.00).
- Smoke worst-case $1.32 (≤ $4.50). Hard total $5.50. Ledger checked before every call.

## Gates
- SG1 instrument validity: B11 controls PASS; 0 leakage blocking hits; 0 out-of-scope edits; evidence 100%.
- SG2 completion ≥ 95% terminal; instrument anomalies ≤ 5%.
- SG3 spend agent ≤ $1.00 / smoke ≤ $4.50 / total ≤ $5.50.
- SG4 floor: GOLD_HARD RESOLVED ≥ 1/14.

## Final tokens
`E2E_SMOKE_PIPELINE_VALID` | `E2E_SMOKE_FLOOR_EFFECT` | `E2E_SMOKE_INSTRUMENT_INVALID`.

## Outcome-blind order
All Smoke generation finishes, is hashed, committed and pushed BEFORE any evaluation (I14).