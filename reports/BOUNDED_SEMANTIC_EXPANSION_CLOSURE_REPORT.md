# Bounded Semantic Expansion Pilot — CLOSURE REPORT (DEVELOPMENT, AUTHORIZED)

**Date:** 2026-09-18
**Mission:** authorized Stage-4 execution of
`docs/BOUNDED_SEMANTIC_RERANK_VERIFY_PROTOCOL_FROZEN.md` under the frozen budget
`reports/BOUNDED_SEMANTIC_EXPANSION_BUDGET_FREEZE_DRAFT.md`
**Verdict:** **BOUNDED_SEMANTIC_NEGATIVE_FROZEN** — the expanded-pool bounded
semantic rerank/verify (Arm B) does NOT pass the preregistered gate vs the
frozen Route-B verifier (Arm A). Real pilot executed (300 calls, DEVELOPMENT).
**Model (pilot inference):** qwen3-coder (Qwen3-Coder-480B-A35B-Instruct) @
OpenRouter deepinfra/turbo, temp 0, cap 512.
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 1. Frozen design (as-registered, BEFORE call 1)

- Registration frozen in `research/bounded-semantic-expansion/pilot_registration_freeze.json`
  (60 tasks: 30 djangoCMS + 30 Saleor; pools, arm-A tops, schemas, ceilings).
- Sample: seeded 20260918, stratified by repo + year/universe-size, ≥1 Sparse FN
  and omitted ≥5, DEVELOPMENT only; INTERNAL_TEST/RESERVE sealed.
- Pool (Arm B): Route-B composite top-10 ∪ reverse-1hop consumers, dedupe,
  pre-order desc bm25 then asc path, hard cap C=40 (verified ≤40 everywhere).
- Arms: A = frozen Route-B verifier (4 calls/task), B = expanded-pool bounded
  rerank/verify (1 call/task, first-B of ordered list), C = analytic references.

## 2. Budget ledger (actual)

| Quantity | Actual | Ceiling |
|---|---:|---:|
| Calls | **300** (240 A + 60 B) | ≤300 |
| Tokens | **106,325** | ≤300,000 |
| Cost | **$0.0444** | ≤$0.30 |
| Wall | **553.6 s** | ≤3600 s |
| Failures (fail-closed) | Arm B 6 schema-invalid (no retries) | ≤10% |

Budget respected; cost is near the frozen projection (~$0.035) and far below the
safety ceiling. Sidecars: 300/300 raw + sha256, 0 hash mismatches.

## 3. Main result (pooled file-level; sparse F1 0.4324 / 0.1854 on sampled)

### djangoCMS DEV @B=5
| Arm | ORR | cand-prec | naive-F1 | oracleRev-F1 | OracleAdd-gap |
|---|---:|---:|---:|---:|---:|
| A Route-B verifier | 0.111 | 0.143 | 0.396 | 0.503 | 0.155 |
| B expanded rerank | **0.250** | 0.105 | 0.327 | **0.568** | 0.296 |

### Saleor DEV @B=5
| Arm | ORR | cand-prec | naive-F1 | oracleRev-F1 | OracleAdd-gap |
|---|---:|---:|---:|---:|---:|
| A Route-B verifier | 0.334 | 0.256 | 0.304 | 0.416 | 0.380 |
| B expanded rerank | 0.357 | 0.179 | 0.270 | **0.452** | 0.439 |

Full curve (B∈{1,3,5,10}) in `reports/BOUNDED_SEMANTIC_EXPANSION_PILOT_REPORT.md`.

## 4. Preregistered stop gate (B=5) — FAIL

| Repo | c1 ORR>+0.05 | c2 folds≥3/5 | c3 naive-F1 | c4 leak | c5 cost |
|---|---:|---:|---:|---:|---:|
| djangoCMS | PASS (+0.139) | PASS | **FAIL (−0.069)** | PASS | PASS |
| Saleor | **FAIL (+0.023)** | PASS | PASS | PASS | PASS |

**Decision: `BOUNDED_SEMANTIC_NEGATIVE_FROZEN`.** Arm B raises ORR but NOT
materially on Saleor, and on djangoCMS it materially lowers naive final F1
(−0.069) — exactly the "ORR rises but final F1 falls materially" failure the
protocol explicitly forbids claiming as success. No prompt/schema tuning was
performed after outcomes (frozen protocol §9).

## 5. Interpretation

- The expanded pool gives the semantic layer more candidates to reorder, which
  improves recovery quality (oracle-reviewer F1 up on both repos; ORR up on
  djangoCMS) — but the accepted additions also carry more FPs, so the naive
  union final F1 falls where the gain concentrates (djangoCMS). On Saleor the
  pool is at cap-40 for almost every task (mean 39.9) and the ORR gain is not
  material.
- This is a bounded DEVELOPMENT pilot; it is NOT a claim about any confirmatory
  set. It confirms that the measured ranking headroom requires something the
  bounded semantic layer did not deliver at this budget: a precision-safe way to
  accept the recovered FNs without the FP tail.

## 6. What this does NOT mean

- Not a LocAgent comparison; no superiority claim over any planner.
- Not a confirmation on INTERNAL_TEST/RESERVE (sealed).
- Not evidence that unbounded/semantic-richer reasoning cannot help — only that
  THIS frozen bounded protocol at THIS budget does not pass the preregistered
  gate on DEVELOPMENT.
- The quantitative-structural cheap-ranking negative and this semantic pilot
  negative are BOTH frozen; the gap-reduction ladder Stage 4 is now closed
  (negative) and Stage 5 (freeze method + fresh confirmatory) is NOT reached.

## 7. Tests / audit

- Affected suites: `test_recall_bottleneck.py` 19/19 + `test_quant_ranking_bridge.py`
  12/12 = **31/31 PASS**.
- Independent audit recomputes headline metrics from raw per-run records without
  importing the analyzer: **8/8 PASS**
  (`reports/bounded_semantic_expansion_audit.json`).
- Ruff clean; py_compile clean; `git diff --check` clean.

## 8. Sealed sets

djangoCMS RESERVE, Saleor INTERNAL_TEST + RESERVE never loaded. Sample = DEV
only (audit A7 PASS). Spent djangoCMS INTERNAL_TEST not touched.

## 9. Raw evidence

- `research/bounded-semantic-expansion/pilot_registration_freeze.json`
- `research/bounded-semantic-expansion/pilot_results.json`
- `research/bounded-semantic-expansion/ledger.json`
- `research/bounded-semantic-expansion/runs/<run_id>.json` + `raw/` (300 txt + sha256)

## 10. ONE next scientific action

Freeze this negative and keep the ladder honest: Stage 4 is closed NEGATIVE;
any future semantic instrument must be pre-registered with a precision-safe
acceptance rule (e.g., verifier-approved AND ranked-gated) before further API
spend, and still requires the same explicit user authorization for any new
budget.