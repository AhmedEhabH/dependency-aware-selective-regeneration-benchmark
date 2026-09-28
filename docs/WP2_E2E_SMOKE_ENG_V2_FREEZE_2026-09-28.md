# WP-2 E2E Smoke ENG v2 - Freeze (2026-09-28)

Authority: MISSION-12 §2.4-2.5 + wrapper L. Tag `wp2-e2e-smoke-eng-v2-freeze-2026-09-28`.
Machine-readable: `research/wp2/e2e_smoke_eng_v2/smoke_v2_freeze.json`.

## Population and arms
- Same 14 behavioral ENG tasks as v1 (DEV_TRAIN_ENG; v1 scope files reused as-is,
  hash-verified byte-identical to v1 immutability record).
- Arms (all HARD): GOLD_HARD / RMCSS_HARD / AGENT_HARD / PLACEBO_HARD x 1 replicate.
- 56 planned episodes; 1 NO_SCOPE (`39b4138e8550` RMCSS_HARD - empty OOF predictions,
  intention-to-treat, same as v1); 52 unique initial request shas (identical-prompt
  pairs deduplicated by the run-level cache).

## Frozen instrument v2 (fixes F01-F05)
- DF1 replay guard: a replay route cannot be persisted into a paid episodes root
  (controls live under `controls/`).
- DF2 full-context repair: messages `[system, original_user, previous_assistant_output,
  repair_instruction]`.
- DF3 run-level on-disk response cache keyed by canonical request_sha; repair carries
  its own request_sha and never overwrites the initial.
- DF4 real provider `finish_reason` propagated; `length` -> TRUNCATED (consumes repair).
- DF5 raw response text persisted immediately under `episodes/<task>/<arm>/calls/*.txt`
  + sha256 + byte count.

## Interface v2
- Envelope extraction (I01): drop pre-first-FILE preamble, fences/interstitial prose
  outside SEARCH/REPLACE bodies, prose after the final REPLACE; body bytes never altered.
- SEARCH matching ladder (I02): exact unique -> PASS; else right-strip both sides ->
  unique tolerant -> PASS + WHITESPACE_TOLERANT; else FAIL/AMBIGUOUS.
- SEARCH_ELLIPSIS (I03) named error.
- Prompt I04/I05 (formatting-only additions).
- `INTERFACE_VERSION = wp2-e2e-interface-v2`, `SMOKE_VERSION_V2 = wp2-e2e-smoke-eng-v2`.

## Frozen components (SHA-256 in smoke_v2_freeze.json)
- spec (unchanged v1 hash), interface, modules (generate_v2, response_cache,
  patch_format, prompt, llm_client), prompt templates v2, evaluator sets, Harness V3
  identity, expressible denominator.

## Budget
- AU4 ceiling **$2.00**. G-BUDGET worst case $1.41 (<= $2.00). Ledger checked before
  every call. Variance probe (6 episodes, cache bypass) included in the $2 ceiling.

## Gates (mechanical)
- G1 SG1 instrument validity: all zero-API controls v2 PASS + 0 replay routes in paid
  evidence + G-REPAIR-CONTEXT 100% + evidence integrity 100%.
- G2 SG2 completion >= 95% episodes terminal; instrument anomalies <= 5%.
- G3 SG3 spend <= $2.00.
- G4 SG4 floor GOLD_HARD RESOLVED >= 1/14.

## Token rule (T)
`E2E_SMOKE_V2_PIPELINE_VALID` (G1-G4 PASS) | `E2E_SMOKE_V2_FLOOR_EFFECT` (G1-G3 PASS,
G4 FAIL) | `E2E_SMOKE_V2_INSTRUMENT_INVALID` (G1 or G2 FAIL).

## NEXT rule (N, written not executed)
N1 GOLD APPLIED >= 7/14 and GOLD RESOLVED >= 3/14 -> NEXT=PILOT_DESIGN.
N2 GOLD APPLIED >= 7/14 and GOLD RESOLVED <= 2/14 -> NEXT=GENERATOR_COMPETENCE_OR_SPEC_REVIEW.
N3 GOLD APPLIED < 7/14 -> NEXT=INTERFACE_V3_PROBE.
N4 instrument invalid -> NEXT=INSTRUMENT_FIX.

## Variance probe (descriptive only)
3 v1 control tasks x GOLD_HARD x 2 extra replicates (var_r1, var_r2), cache bypassed.
Reported separately; never in the main table. No CI / population variance estimate.

## Outcome-blind order
All Smoke v2 generation (main + variance) finishes, is hashed, committed and pushed
BEFORE any evaluation (generation_freeze_v2 on origin/main).

## Mandatory wording
Smoke v2 is engineering-split pipeline validation only. n = 14. No comparative claim
between RM-CSS and Agent is made or supported.
