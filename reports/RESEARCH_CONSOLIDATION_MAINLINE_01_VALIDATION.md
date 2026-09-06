# RESEARCH-CONSOLIDATION-MAINLINE-01 — Six Validation Items + Independent Audit

Date: 2026-09-07. Consolidation branch `research/stagec-consolidation-01`.
No model/API calls were made. The six Pre-Benchmark-style reporting categories
are retained; this is NOT a new benchmark run.

## 1. Dataset Validation — PASS
Raw source evidence files are byte-unchanged vs `main`:
`reports/scientific_microstudy_v11/run_records.jsonl`,
`reports/scientific_stagec_selection_01/run_records.jsonl`,
`reports/scientific_stagec_heldout_01/run_records.jsonl`,
`reports/STAGEC_SELECTION_01_RESULTS.csv`,
`reports/STAGEC_HELDOUT_01_RESULTS.csv`,
`reports/SCIENTIFIC_MICROSTUDY_V11_DECISION.md` all `git diff HEAD` empty.
30/30 + 30/30 + 60/60 raw records present and readable.

## 2. Prompt Validation — PASS (N/A for model generation)
No model call and no prompt modification in this task. No LLM was invoked;
the analysis is purely deterministic over persisted records.

## 3. Pipeline Smoke Test — PASS
Both analysis scripts run end-to-end on the live historical records and produce
their CSV/MD reports (verified by `TestScriptsRunEndToEnd`, 2 tests, plus direct
runs). 21 focused tests pass.

## 4. Dry Run — PASS
Report outputs (`reports/V11_ROOT_CAUSE_TAXONOMY.{csv,md}`,
`reports/STAGEC_LATENCY_DECOMPOSITION.{csv,md}`,
`reports/RESEARCH_TRUTH_MATRIX.md`, `docs/STAGEC_FORMAL_MODEL.md`) were generated
without mutating any source evidence (verified by `TestRawEvidenceUntouchedByGit`).

## 5. Integration Test — PASS
Both scripts consume the live historical evidence (`scientific_microstudy_v11`,
`scientific_stagec_selection_01`, `scientific_stagec_heldout_01`) and produce
reports; classifier + latency aggregation are exercised over the real records
(`TestReproducedV11Counts`, `TestLatencyAggregation`).

## 6. Metric Verification — PASS
Reproduced frozen counts exactly:
- v1.1 overall: A=1,B=0,C=10,D=8,E=4,F=7,G=0,H=0,I=0 (30 total)
- v1.1 by arm: Agent C=5,D=4,E=3,F=3; ImpactPlan A=1,C=5,D=4,E=1,F=4
- v1.1 by scenario: smoke-001 C=3,D=7; smoke-002 A=1,C=2,F=7; smoke-003 C=5,D=1,E=4
- Latency: smoke Agent 147.644s/89 calls/98,512 tokens/median 10.281s; smoke IP
  252.094s/15 calls/34,084 tokens/median 13.531s; held-out Agent 490.108s/220
  calls/210,883 tokens/median 8.211s (outliers 149.468s + 111.406s); held-out IP
  236.162s/30 calls/56,971 tokens/median 6.891s.

All match the frozen GPT-5.6 Sol precheck exactly.

## Independent Audit

| # | Item | Verdict | Evidence |
|---|------|---------|----------|
| 1 | Objective unchanged (consolidation, not new science) | PASS | pack 00_READ_FIRST; no scientific/model design change |
| 2 | No model/API calls | PASS | no LLM backend invoked; scripts read records only |
| 3 | All raw scientific records preserved | PASS | git diff empty for all evidence files; hashes stable |
| 4 | Existing evidence tags not moved | PASS | `stagec-heldout-selection-01` (peel `3e4224a`) and `stagec-selection-exploratory-01` unchanged |
| 5 | No rebase/squash of evidence history | PASS | `main` merged via `--no-ff` (merge `42509b5`), parents `6909b5d`+`3e4224a`; branch ancestry intact |
| 6 | v1.1 taxonomy reproduced deterministically | PASS | frozen counts reproduced exactly (see Metric Verification) |
| 7 | Latency decomposition incl. medians/outliers | PASS | total + median + p90 + outliers reported; caveat stated |
| 8 | Formal model frozen without Agent O(2^n) claim | PASS | `docs/STAGEC_FORMAL_MODEL.md` §5 explicitly forbids O(2^n) claim |
| 9 | Truth Matrix created with exact numbers | PASS | `reports/RESEARCH_TRUTH_MATRIX.md`; numbers verified by test |
| 10 | Archive appended, never rewritten | PASS | `RESEARCH_DECISION_ARCHIVE.md` Entry 10 appended only |
| 11 | No executor/regeneration/patch redesign | PASS | only analysis scripts + docs + reports + tests |
| 12 | main parity after merge | PASS | `main` HEAD == `origin/main` == `42509b5` |

**AUDIT = PASS**
