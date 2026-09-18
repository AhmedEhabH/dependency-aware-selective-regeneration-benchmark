# Precision-Safe Acceptance Pilot — CLOSURE REPORT (DEVELOPMENT, AUTHORIZED)

**Date:** 2026-09-18
**Mission:** authorized execution of
`docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md` under the frozen budget
`reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md`
**Verdict:** **`PRECISION_SAFE_ACCEPTANCE_FAIL`** — the preregistered gate
FAILED (djangoCMS c1 ORR and c2 folds). **The negative is FROZEN; no tuning.**
**Model (pilot inference):** qwen3-coder (Qwen3-Coder-480B-A35B-Instruct) @
OpenRouter deepinfra/turbo, temp 0, cap 512.
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 1. Frozen design (as-registered, BEFORE call 1)

Registration frozen in
`research/precision-safe-acceptance-pilot/pilot_registration_freeze.json`
(60 tasks: 30 djangoCMS + 30 Saleor; pools cap 80 with candidate-ID maps;
K=10; arm-A tops; schemas; ceilings). Sample: seed 20260919, eligibility
`n_missed ≥ 1 AND omitted_size ≥ 5`, **the 60 Stage-4 case_ids excluded**,
stratified by year/universe-size (123 dc + 97 saleor fresh eligible remained).
DEVELOPMENT only; INTERNAL_TEST/RESERVE sealed.

- **Arm A** = frozen Route-B verifier (exact Stage-4 prompt/schema), 4 calls/task.
- **Arm B** = RANK → VERIFY → VARIABLE ACCEPT: 1 semantic-ranking call over the
  pool (candidate-ID enum schema) + 1 strict verification call over the top-K
  (K=10) inspection set (fixed-length boolean vector); accepted = approved
  subset ordered by semantic rank (0..K).
- **Arm C** = analytic references (no calls).

## 2. Budget ledger (actual)

| Quantity | Actual | Ceiling |
|---|---:|---:|
| Dispatched calls | **357** (240 A + 60 rank + 57 verify; 3 fail-closed abstentions) | ≤400 |
| Tokens | **176,060** | ≤300,000 |
| Cost | **$0.0648** | ≤$0.15 |
| Wall | **718.8 s** (655.7 s execution + reload sessions) | ≤3600 s |
| Invalid dispatched calls | **0 / 357** | ≤10% |

Budget respected (`budget_respected: true`); sidecars 357/357 raw + sha256,
0 hash mismatches; resume from disk 357/357 with no double spend. Actual cost
$0.0648 is ~1.2× the ~$0.055 projection (longer rank completions at cap 80),
well inside the safety ceiling.

## 3. Main result (pooled file-level; sparse F1 0.1860 dc / 0.1732 saleor on the sampled tasks)

### djangoCMS DEV @B=5
| Arm | ORR | cand-prec | naive-F1 | final-prec | n-selected | recovered |
|---|---:|---:|---:|---:|---:|---:|
| A Route-B verifier | 0.2225 | 0.1406 | 0.2176 | 0.1032 | 64 | 9 |
| B RANK→VERIFY | 0.1523 | **0.2500** | **0.2604** | **0.1291** | 40 | 10 |

### Saleor DEV @B=5
| Arm | ORR | cand-prec | naive-F1 | final-prec | n-selected | recovered |
|---|---:|---:|---:|---:|---:|---:|
| A Route-B verifier | 0.1278 | 0.0882 | 0.1744 | 0.0593 | 68 | 6 |
| B RANK→VERIFY | **0.2029** | **0.1163** | **0.1972** | **0.0679** | 86 | 10 |

Full curve (B∈{1,3,5,10}) in `reports/PRECISION_SAFE_ACCEPTANCE_PILOT_REPORT.md`.

## 4. Preregistered stop gate (B=5) — FAIL

| Repo | c1 ORR>+0.05 | c2 folds≥3/5 | c3 F1≥−0.05 | c4 prec≥A | c5 leak | c6 schema | c7 cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| djangoCMS | **FAIL (−0.0702)** | **FAIL (2/5)** | PASS (+0.0428) | PASS (+0.1094) | PASS | PASS | PASS |
| Saleor | PASS (+0.0751) | PASS (5/5) | PASS (+0.0228) | PASS (+0.0281) | PASS | PASS | PASS |

Decision: **`PRECISION_SAFE_ACCEPTANCE_FAIL`** — the gate requires material ORR
gain on BOTH repos; djangoCMS ORR fell materially. No prompt/schema/threshold
tuning was performed (frozen protocol §11).

## 5. Interpretation

The RANK → VERIFY → VARIABLE-ACCEPT layer **achieved its precision-safe
objectives on BOTH repositories**:

1. **The Stage-4 failure mode is eliminated.** Stage-4's forbidden "ORR up,
   F1 down" never occurs: naive-union F1 and candidate precision improve on
   BOTH repos at every B (dc F1 0.218→0.260, precision 0.141→0.250; saleor F1
   0.174→0.197, precision 0.088→0.116 @B=5). Variable acceptance (0..K) + the
   strict verifier removed the FP tail the take-first-B design forced in.
2. **Saleor achieves the recovery goal the protocol was motivated by.** ORR
   +0.0751 @B=5 with 5/5 positive folds — the B=10 inspection-depth motivation
   from Stage-4, now realized at B=5 by decoupling inspection (K=10) from
   acceptance (variable).
3. **But djangoCMS trades away material ORR.** The conservative verifier
   over-rejects: 3 single-FN tasks (M=1) where Arm A recovered 1/1 had Arm B
   approve a different, non-FN candidate → three −1.0 per-task deltas that
   dominate the −0.0702 macro. The strict approval criterion is
   anti-calibrated on djangoCMS's easy recoveries. Net absolute recoveries at
   B=5 are comparable (A 9 / B 10), but the macro (task-weighted) ORR falls
   because Arm B's recoveries land on tasks with larger missed sets.
4. **Schema reliability is fixed as engineered:** 0/357 dispatched-call
   schema failures (Stage-4: 6/60 non-pool-path hallucinations); the
   candidate-ID enum + uniqueness enforcement eliminated hallucinated paths;
   3 empty-rank abstentions are genuine conservative decisions (zero additions,
   zero partial credit).

Because the preregistered gate is conjunctive across both repos and requires a
material ORR gain, the outcome is a FAIL and the negative is frozen. This is
NOT a claim that the family is dead — it is a claim that THIS frozen
instantiation (verifier prompt/schema, K=10, cap 80) does not satisfy the
preregistered gate on djangoCMS.

## 6. What this does NOT mean

- NOT a confirmatory result (DEVELOPMENT only; INTERNAL_TEST/RESERVE sealed).
- NOT a license to tune the verifier prompt/schema/thresholds to chase ORR —
  that would be a NEW protocol requiring its own freeze and authorization.
- NOT evidence that the RANK→VERIFY family is useless — it improved F1 and
  precision on both repos and recovered material ORR on Saleor; the failure is
  the djangoCMS recovery trade against the frozen baseline under the
  conjunctive gate.
- NOT a LocAgent comparison; no superiority claim over any planner.

## 7. Tests / audit

- New unit tests `tests/unit/test_precision_safe_acceptance.py` **9/9 PASS**
  (plus the previously green 44/44 affected suites).
- Independent audit recomputes ORR@5, gate decision, schema rate, zero partial
  credit, sealed+disjoint sample, and prompt determinism from raw records
  without importing the analyzer: **11/11 PASS**
  (`reports/precision_safe_acceptance_audit.json`).
- Ruff clean; py_compile clean; `git diff --check` clean.

## 8. Sealed sets

djangoCMS RESERVE, Saleor INTERNAL_TEST + RESERVE never loaded; the 60-task
sample is DEVELOPMENT-only and **disjoint** from the 60 Stage-4 case_ids
(audit A7 PASS). Spent djangoCMS INTERNAL_TEST not touched.

## 9. Raw evidence

- `research/precision-safe-acceptance-pilot/pilot_registration_freeze.json`
- `research/precision-safe-acceptance-pilot/pilot_results.json`
- `research/precision-safe-acceptance-pilot/ledger.json`
- `research/precision-safe-acceptance-pilot/runs/<run_id>.json` + `raw/` (357 txt + sha256)

## 10. ONE next scientific action

Freeze this negative and keep the ladder honest: the precision-safe acceptance
pilot FAILED its preregistered gate (djangoCMS ORR trade). Stage 5
(freeze method + fresh confirmatory) is NOT reached. Any future instrument that
wants to keep the verifier's precision/F1 gains while restoring djangoCMS ORR
would be a NEW protocol (e.g., a calibrated acceptance criterion) requiring its
own freeze, sample discipline, budget, and explicit authorization — and it must
still be gated on BOTH repositories.