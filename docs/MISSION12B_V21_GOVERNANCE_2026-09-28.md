# MISSION-12B V2.1 — GOVERNANCE RECORD

Date: 2026-09-28
Mission authority: `_workspace/active/MISSION_12B_AUTONOMOUS_UNATTENDED_V21_2026-09-28.md`

## Historical facts (accepted, not re-litigated)

1. **Smoke v1 instrument invalid.** Mission-11 corrected token = `E2E_SMOKE_INSTRUMENT_INVALID`
   (supersedes `E2E_SMOKE_FLOOR_EFFECT`), per `docs/WP2_E2E_SMOKE_ENG_V1_ERRATUM_2026-09-28.md`.
   Defects DF1–DF5.
2. **Mission-12 C22 max-attempt breach acknowledged.** Mission-12B §2.1. A later warm diagnostic
   PASS does not erase the breach. Historical only.
3. **v2 J/K/L phases + paid partial generation = diagnostic/history only.** Not rehabilitated into
   confirmatory evidence.
4. **v2 paid partial run (measured):**
   - episode JSON = 10
   - ledger rows = 11
   - scientific spend = $0.025718400
   - prompt tokens = 64,608
   - completion tokens = 6,384
   - evidence root `research/wp2/e2e_smoke_eng_v2/` (read-only, dirty historical evidence)
5. **Post-freeze generation-driver/client changes** exist in the v2 working tree
   (`scripts/wp2_e2e_smoke_v2_generate.py` modified after freeze). Recorded as diagnostic history only.
6. **v2 HOLD present** at `research/wp2/e2e_smoke_eng_v2/HOLD`.
7. **External pre-hold snapshot** `M12B_PREHOLD_SNAPSHOT_2026-09-28.zip`
   SHA-256 `f89ccd54a3cd6bb3cf5fbe81fb98b6cda318fd74e96275c5e69b97ec2fa18731` (185,486 bytes).

## Prospective decision

- **OPTION A — prospective reset** in a new namespace `research/wp2/e2e_smoke_eng_v21/`.
- **No v2 paid evidence is reused as v21 evidence.**
- Transport policy for v21 = `TRANSPORT_V21` (Mission-12B §2.3), an intentional prospective
  amendment over historical D63 (see `governance/d63_v21_comparison.json`).
- d220 stays in the 14-task primary analysis; a secondary sensitivity table omits d220 and never
  changes the primary Smoke token/NEXT rule.

## Immutability CHECK

- `research/wp2/e2e_smoke_eng_v1/` and `research/wp2/e2e_smoke_eng_v2/` are read-only evidence.
  No v1/v2 evidence bytes are modified by this mission.
- v1 evidence hashes recorded in `governance/history_and_deviations.json` for later verification.
- Historical result/freeze tags are never moved.

## Evidence

- `research/wp2/e2e_smoke_eng_v21/governance/history_and_deviations.json`
- `research/wp2/e2e_smoke_eng_v21/governance/mission11_rule_extracts.json`
- `research/wp2/e2e_smoke_eng_v21/governance/d63_v21_comparison.json`
