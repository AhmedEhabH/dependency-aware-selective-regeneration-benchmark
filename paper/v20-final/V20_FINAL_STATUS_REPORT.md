# V20 Final STATUS REPORT

**Date:** 2026-09-15
**Branch:** `paper/v20-final` @ `42755df` (from corrected `main` @ `884ba79`)
**Model (this session):** deepseek/deepseek-v4-flash-0731
**Zero new scientific model calls throughout this closure.**

---

## 1. P5 reporting corrections (C1–C7) — COMPLETE, merged, tagged

New immutable correction tag: **`v0.11.3-p5-reporting-corrections`** @ merge
`884ba7982f283b2e78c48d768d34f2f5a726a862` (pushed).
Historical tag **`v0.11.2-p5-locagent-shared-comparison`** was **NOT moved**
(still peels to `fe4b901d6…`, tag object `4941715155…`).
`main` == `origin/main` == `884ba79`. Working tree clean at closure.

| # | Correction | Before | After (verified) |
|---|---|---|---|
| C1 | Native Acc@K | Acc@1 4/10, Acc@3 8/10, Acc@5 9/10 (item-hit sums) | Official Acc@1 4/10, Acc@3 4/10, Acc@5 2/10; Hit@K 4/10 all |
| C2 | Valid column | 30/30 vs 5/10 ambiguous | Tasks / Runs / Non-empty / Fail-closed explicit |
| C3 | Failure taxonomy | "5 timeouts" (50% timeout) | 2 timeout / 1 context-length / 2 completed-but-empty (50% empty/non-usable) |
| C4 | Provider wording | "pinned DeepInfra" | OpenRouter-routed Qwen3-Coder; provenance disclosed |
| C5 | Efficiency ratios | ~33× tokens / ~160× cost (mixed denominators) | Mean per execution/task: 246× / 100× vs Full; 594× / 478× vs Sparse |
| C6 | README Mermaid | literal `\n` labels (render failure) | Quoted `<br/>` labels |
| C7 | Independent audit | 19 checks | **28 checks**, fails closed on all of the above |

## 2. Strengthened zero-API audit

`python scripts/audit_locagent_p5c.py` → **AUDIT: PASS (28/28)** including:
official Acc@K reproduced from raw evidence; item-hits 4/8/9 audit-only;
empty taxonomy not-all-timeout; ledger provider = openrouter only;
provider-route note present; Venice upstream error logged; efficiency
denominator consistent (245.7× / 593.8×); committed-blob LF check.

## 3. Independent recomputation (from raw evidence, standalone script)

- LocAgent common-set: **TP 10 / FP 13 / FN 27 → P .434783, R .270270,
  F1 .333333, FNR .729730** (matches scorer).
- Official Acc@K: **4/10, 4/10, 2/10**; Hit@K 4/10 at every K.
- P1: Full P .338843 / R .369369 / F1 .353448 / FNR .630631;
  Sparse P .386667 / R .261261 / F1 .311828 / FNR .738739.
- P1 per-task F1 table: 10/10 match frozen metrics.
- Ledger: 402 calls / 32,718,518 + 113,256 = 32,831,774 tokens / $9.928811.
- Mean per task: tokens 3,283,177 (vs Full 13,362 / Sparse 5,530); cost
  $0.99288 (vs Full $0.00992 / Sparse $0.00208) → 245.7× / 100.1× vs Full,
  593.8× / 477.8× vs Sparse.

## 4. Tests / validation

- Targeted regression: **37 passed** (locagent shared comparison incl. official
  Acc@K + item-hit regression, adapter, queue guard, README Mermaid/tables).
- Ruff: clean on all changed Python files. Mypy: clean. Compile: OK.
- README Mermaid structural regression tests added and passing.

## 5. Documentation consistency (zero contradictions)

Updated: README.md, SYSTEM_STATE.md, TODO.md, docs/PAPER_WRITING_HANDOFF.md,
docs/PROJECT_HANDOFF.md, docs/MSC_RESEARCH_ROADMAP_2026_2027.md,
reports/LOCAGENT_P5C_SHARED_COMPARISON.md, LOCAGENT_P5C_HELDOUT_RUN.md,
LOCAGENT_P5C_AUDIT.md, LOCAGENT_P5B_POSIX_VALIDATION_RUN.md,
research/locagent-p5b/shared_comparison.json. Historical P5-B blocker report
left intact with one superseding note. Stale-claim scan: 0 unresolved hits.

## 6. V20 manuscript

- Files: `paper/v20-final/paper_v20_blind.tex/.pdf`,
  `paper_v20_supervisor.tex/.pdf`, `v20_body.tex`, `references.bib` (8 verified
  refs), `V20_CHANGE_LOG.md`, `V20_CLAIMS_EVIDENCE_MATRIX.md` (43/43 PASS),
  `V20_REVIEWER_RISK_AUDIT.md`.
- Page count: **5 pages** (target 6 preferred; 8 hard max). Science identical
  in both variants (shared body).
- Structure: Abstract / Introduction / Related Work / Method (Preserve-by-
  Omission) / Experimental Design / Results (M1, P1, P5) / Discussion /
  Threats to Validity / Conclusion.
- P5 framed as "LocAgent framework baseline using Qwen3-Coder", pinned commit
  stated, NOT a reproduction of the published fine-tuned result; official
  Acc@K only (4/10, 4/10, 2/10); failure taxonomy accurate; provider wording
  accurate; one consistent efficiency denominator.

## 7. Final deliverables

| Item | Path / value |
|---|---|
| Blind TEX/PDF | `paper/v20-final/paper_v20_blind.tex/.pdf` |
| Supervisor TEX/PDF | `paper/v20-final/paper_v20_supervisor.tex/.pdf` |
| References | `paper/v20-final/references.bib` |
| V20 change log | `paper/v20-final/V20_CHANGE_LOG.md` |
| Reviewer-risk audit | `paper/v20-final/V20_REVIEWER_RISK_AUDIT.md` |
| Claims-vs-evidence matrix | `paper/v20-final/V20_CLAIMS_EVIDENCE_MATRIX.md` (43/43 PASS) |
| Submission ZIP | `paper/v20-final/V20_FINAL_SUBMISSION.zip` |
| ZIP SHA-256 | recorded in the authoritative sidecar `V20_FINAL_SUBMISSION.zip.sha256` |
| ZIP integrity | 10/10 entries verified |
| Correction tag | `v0.11.3-p5-reporting-corrections` @ `884ba79` (v0.11.2 untouched) |
| main == origin/main | `884ba79` == `884ba79` ✓ |

## 8. Scientific discipline

- **No new scientific model calls** were made in this closure (correction phase
  zero-API; manuscript from frozen evidence only).
- No LocBench, Saleor, faithful LocAgent replication, new model runs, new graph
  experiments.
- P1/P5 raw evidence was never regenerated; only reporting/scoring code and
  documentation changed.
- High FNR is reported as a weakness motivating selective verification, not as
  a success.

## 9. Blockers / remaining

None. All closure tasks complete.