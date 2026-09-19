# STRONG LOCALIZATION SIGNAL BRIDGE — Final STOP Report (2026-09-19)

**Mission:** Statistical closure of Stage 4b + cross-language readiness + a
fundamentally different localization signal (`Salesforce/SweRankEmbed-Small`).
**Tier:** T3 (new evaluation-strategy / baseline family).
**Scientific spend:** ZERO paid LLM/API calls. API calls = 0, API cost = $0.
Local CPU inference on a pinned CC-BY-NC-4.0 model only.

---

## 0. Executive verdict

**COMPLETE — all zero-API mission work done.** The bounded cheap-semantic
family is closed FOR NOW with descriptive statistical closure of Stage 4b; a
specialized issue-localization embedding signal was evaluated on the FULL legal
DEVELOPMENT populations and **PASSED its frozen progression gate on both
repositories** (every metric improves at every B; all paired-bootstrap 95% CIs
@B=5 exclude zero on both repos; 0 API calls / $0). The result is honestly
labeled as an EXTERNAL PRETRAINED DIAGNOSTIC BASELINE (SweLoc training
provenance could not rule out overlap — verdict C). Repository-memory,
cross-language and polyglot readiness audits were completed; the documented
Saleor history blocker was independently resolved (full history exists locally
at `dist/pilot-repo-cache/saleor`).

---

## 1. Execution identity

- Provider/model (authoring agent): openrouter/deepseek/deepseek-v4-flash-0731.
- Branch: `main` (mission branch
  `research/strong-localization-signal-2026-09-19` merged).
- HEAD: `0c12223b15de4fa704dd2200ccae15b088ce23be`.
- origin/main: `0c12223b15de4fa704dd2200ccae15b088ce23be` (== HEAD).
- Tree state: clean (0 modified/untracked).

## 2. Why I am stopping — **COMPLETE**

Every actionable item of the mission is executed and verified: P0 (Stage-4b
statistical closure, SweRank provenance audit, protocol freeze, full DEV eval,
metrics+CIs, independent audit, PASS/FAIL decision) and P1 (competitor review,
repository-memory feasibility, TS/Java/Go readiness, grafana/polyglot audit,
SweRank+ readiness). No remaining zero-API work is scientifically safe to do
beyond this mission's scope.

## 3. What I completed (per-file table)

### Scientific evidence / reports (new)
| File | Content |
|---|---|
| `reports/STAGE4B_STATISTICAL_CLOSURE_2026-09-19.md` | POST-HOC descriptive closure; definitions; per-repo pooled TP/FP/FN; point estimates + 95% paired CIs; djangoCMS phenomenon explained |
| `reports/stage4b_bootstrap_ci.json` | machine-readable closure CIs (10,000 resamples, seed 20260919) |
| `reports/swerank_bootstrap_ci.json` | machine-readable SweRank CIs @B=5 |
| `reports/SWERANK_EMBED_DEVELOPMENT_REPORT.md` | full DEV evaluation (methods × B curves, gate, CIs, efficiency, interpretation, next step) |
| `reports/SWERANK_TRAINING_PROVENANCE_AUDIT.md` | verdict **C** (insufficient to rule out overlap) |
| `reports/SWERANK_INDEPENDENT_AUDIT.md` + `.json` | independent audit 11/11 PASS |
| `reports/STRONG_LOCALIZATION_COMPETITOR_REVIEW_2026-09-19.md` | SweRank/LocAgent/RepoGraph/OrcaLoca/Agentless/CoSIL/repo-memory/SweRank+ |
| `reports/REPOSITORY_MEMORY_FEASIBILITY_2026-09-19.md` | Saleor history blocker resolved; deterministic probe plan |
| `reports/CROSS_LANGUAGE_READINESS_2026-09-19.md` | TS (nestjs) / Java (JabRef) / Go (prometheus) |
| `reports/POLYGLOT_REPOSITORY_FEASIBILITY_2026-09-19.md` | grafana Go+TS eligibility definition frozen |
| `docs/SWERANK_EMBED_BASELINE_PROTOCOL_FROZEN.md` | frozen protocol + comparator/K clarification + temporal-guard record |
| `docs/STRONG_LOCALIZATION_SIGNAL_IMPACT_DECLARATION_2026-09-19.md` | T3 impact declaration |
| `_workspace/active/CLAUDE_LOCALIZATION_BOTTLENECK_REVIEW_PROMPT_2026-09-19.md` | reviewer prompt |

### Raw evidence (new)
| File | Content |
|---|---|
| `research/strong-localization-signal/stage4b/task_level.json` | per-task Arm A/B contributions @B=5 |
| `research/strong-localization-signal/swerank/{metrics,gate,efficiency,model_pin,task_rankings,blob_manifest,unit_manifest}.json` | full DEV evaluation machine artifacts |

### Implementation (new)
| File | Content |
|---|---|
| `src/benchmark/signal/{__init__,metrics,code_units,swrank_adapter,swerank_model}.py` | metrics/bootstrap, unit extraction, frozen adapter, pinned model loader |
| `scripts/stage4b_statistical_closure.py` | closure reproducer |
| `scripts/swerank_dev_eval.py` | DEV evaluation pipeline |
| `scripts/swerank_write_report.py` | report writer |
| `scripts/swerank_independent_audit.py` | independent audit (no analyzer imports) |

### Tests (new) — `tests/unit/`
| File | Count | Coverage |
|---|---|---|
| `test_signal_metrics.py` | 13 | TP/FP/FN→P/R/F1/FNR, ORR, candidate precision, paired bootstrap (point/delta/CI, determinism, task unit) |
| `test_signal_adapter.py` | 13 | unit extraction + fallback, MAX aggregation, cosine, deterministic ranking, tie-break, no-target-label |
| `test_signal_leakage.py` | 7 | pinned revision, query=intent hash, parent-only indexing, unit-manifest integrity, files-exist |
| `test_stage4b_closure.py` | 5 | closure point estimates == frozen metrics, determinism, verdict unchanged |

### Documentation updated
`00_CURRENT_RESEARCH_STATE.md`, `PROGRESS.md`, `DECISIONS.md` (P68–P70
append), `docs/RESEARCH_JOURNEY.md` (rows), `reports/GAP_REDUCTION_ROADMAP.md`
(stale Stage-4b wording fixed + addendum), `research/literature/idea_ledger.md`
+ `review_matrix.csv` (+7 verified entries), `.gitignore` (un-ignore new
mission reports).

## 4. Verification performed

- **ruff**: clean on all changed/new Python.
- **py_compile**: clean on all new modules/scripts/tests.
- **git diff --check**: clean.
- **Tests**: 53/53 prior affected suites +
  **38 new unit tests PASS** (35 in one run + closure re-run 5/5; leakage
  suite 7/7). Full suite not re-run for this T3 patch (project protocol: run
  affected; 2 known pre-existing environmental failures on a clean base).
- **Independent audit**: `scripts/swerank_independent_audit.py` 11/11 PASS
  (formulas, macro ORR, pooled P/R/F1/FNR, gate A–E, folds, bootstrap CI
  determinism, leakage surface, pinned model, efficiency, Stage-4b closure vs
  frozen pilot, verdict unchanged) — recomputed from raw JSONs WITHOUT
  importing the analyzer.

## 5. Pre-benchmark validation (T3 gates)

1. Dataset validation — DEV populations frozen; counts verified (174 + 149);
   sealed sets untouched.
2. Prompt/query validation — parent-visible intent only; SHA-256 per task;
   audit S6 verified == sha256(intent_text).
3. Pipeline smoke — 4-task smoke runs completed exit 0 (artifacts deleted
   before the full run; temporal-guard recorded).
4. Dry run — deterministic, cache-backed; full population run.
5. Integration — Route-B composite macro ORR reproduced EXACTLY on both full
   DEV populations (0.0464/0.1177/0.1633/0.2512 and
   0.0775/0.1576/0.2369/0.3173).
6. Metric verification — synthetic TP/FP/FN tests; point estimates reproduce
   frozen metrics within 1e-4.

## 6. Main results

### 6a. Stage-4b statistical closure @B=5 (POST-HOC; frozen verdict UNCHANGED: `PRECISION_SAFE_ACCEPTANCE_FAIL`)

| Repo (n=30 paired) | Metric | Arm A | Arm B | Δ | 95% CI (10k bootstrap) | excludes 0 |
|---|---|---:|---:|---:|---:|:--:|
| djangoCMS | macro ORR | 0.2225 | 0.1523 | −0.0702 | [−0.196, +0.034] | no |
| djangoCMS | final Precision | 0.2000 | 0.2716 | +0.0716 | [+0.009, +0.151] | yes |
| djangoCMS | final Recall | 0.2386 | 0.2500 | +0.0114 | [−0.056, +0.063] | no |
| djangoCMS | final F1 | 0.2176 | 0.2604 | +0.0427 | [−0.013, +0.096] | no |
| djangoCMS | final FNR | 0.7614 | 0.7500 | −0.0114 | [−0.063, +0.056] | no |
| djangoCMS | cand-prec | 0.1406 | 0.2500 | +0.1094 | [−0.005, +0.247] | no |
| Saleor | macro ORR | 0.1278 | 0.2029 | +0.0751 | [+0.004, +0.175] | yes |
| Saleor | final Precision | 0.1828 | 0.1892 | +0.0064 | [−0.040, +0.057] | no |
| Saleor | final Recall | 0.1667 | 0.2059 | +0.0392 | [+0.009, +0.076] | yes |
| Saleor | final F1 | 0.1744 | 0.1972 | +0.0228 | [−0.012, +0.060] | no |
| Saleor | final FNR | 0.8333 | 0.7941 | −0.0392 | [−0.076, −0.009] | yes |
| Saleor | cand-prec | 0.0882 | 0.1163 | +0.0280 | [−0.021, +0.085] | no |

Pooled confusion: djangoCMS A (TP21/FP84/FN67) vs B (TP22/FP59/FN66); Saleor A
(TP17/FP76/FN85) vs B (TP21/FP90/FN81).

**djangoCMS phenomenon (verified from raw task data):** macro ORR is a
per-task-ratio mean; Arm B's conservative verifier over-rejects the three M=1
easy recoveries (case_ids `06ecf3a8e8de`, `829f7e224887`, `f96c80357c71` —
Arm A recovered 1/1, Arm B approved a different non-FN candidate), producing
three Δ=−1.0 task deltas that dominate the macro, while pooled TP/FP/FN and
P/R/F1/FNR still improve because Arm B cuts the FP tail (40 vs 64 selected)
with the same net FN recovery (9 vs 10).

### 6b. SweRankEmbed-Small (EXTERNAL PRETRAINED DIAGNOSTIC BASELINE) @B=5 vs frozen Route-B

| Repo (n) | Metric | Route-B | SweRank | Δ | CI95 (10k) | excl0 |
|---|---|---:|---:|---:|---:|:--:|
| djangoCMS (174) | macro ORR | 0.1633 | 0.2908 | +0.1274 | [+0.068, +0.188] | yes |
| djangoCMS | final P | 0.1626 | 0.2017 | +0.0391 | [+0.020, +0.059] | yes |
| djangoCMS | final R | 0.3688 | 0.4576 | +0.0888 | [+0.046, +0.133] | yes |
| djangoCMS | final F1 | 0.2257 | 0.2800 | +0.0543 | [+0.028, +0.081] | yes |
| djangoCMS | final FNR | 0.6312 | 0.5424 | −0.0888 | [−0.133, −0.046] | yes |
| djangoCMS | cand-prec | 0.0713 | 0.1230 | +0.0517 | [+0.026, +0.077] | yes |
| Saleor (149) | macro ORR | 0.2369 | 0.3266 | +0.0897 | [+0.024, +0.158] | yes |
| Saleor | final P | 0.1716 | 0.2093 | +0.0376 | [+0.017, +0.059] | yes |
| Saleor | final R | 0.3803 | 0.4637 | +0.0833 | [+0.040, +0.126] | yes |
| Saleor | final F1 | 0.2365 | 0.2884 | +0.0518 | [+0.024, +0.080] | yes |
| Saleor | final FNR | 0.6197 | 0.5363 | −0.0833 | [−0.126, −0.040] | yes |
| Saleor | cand-prec | 0.1060 | 0.1584 | +0.0523 | [+0.024, +0.082] | yes |

Frozen gate A–E: **PASS on both repos** (djangocms F1 Δ+0.054, R Δ+0.089, FNR
Δ−0.089, P Δ+0.039, folds 4/5; Saleor F1 Δ+0.052, R Δ+0.083, FNR Δ−0.083, P
Δ+0.038, folds 3/5). **Decision: `SWERANK_EMBED_PASS`.**

Efficiency: 0 API calls, $0; one-time corpus encode (49,705 distinct units,
14,807 blobs) ≈ 6.6 h CPU; marginal per-task scoring ≈ 0.1 s after indexing.

## 7. Decision summary (append-only, frozen negatives preserved)

- Preserved: `CHEAP_RANKING_CLOSED_FOR_NOW`, `BOUNDED_SEMANTIC_NEGATIVE_FROZEN`,
  `PRECISION_SAFE_ACCEPTANCE_FAIL` — all unreinterpreted.
- **P68 `BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW`** (narrowly scoped).
- **P69 SweRank provenance verdict C
  `TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP`.**
- **P70 `SWERANK_EMBED_PASS`** (frozen method as candidate-ranking signal;
  next step A chosen; option B budget-planned, not executed).

## 8. Competitor / landscape implications

SweRankEmbed-Small is the first signal in this line to realize the measured
ranking/recall headroom with a deterministic zero-API mechanism; it is
competitive at file level with the agentic/reranker families listed in
`reports/STRONG_LOCALIZATION_COMPETITOR_REVIEW_2026-09-19.md` (external numbers
are literature context only; protocol-matched comparison required for any
head-to-head). Repository-memory localization (arXiv 2510.01003) is the most
scientifically promising NEXT fundamentally-different family given the now
full local history availability.

## 9. Tests / audit

- 53/53 prior affected suites PASS; 38 new unit tests PASS.
- Independent audit 11/11 PASS (`reports/swerank_independent_audit.json`).
- Ruff / py_compile / git diff --check clean.

## 10. Sealed sets

djangoCMS RESERVE, Saleor INTERNAL_TEST, Saleor RESERVE untouched; spent
djangoCMS INTERNAL_TEST unused; the DEV evaluation used only the legal
DEVELOPMENT populations.

## 11. Branch / commit / tag / export / SHA256

- Branch: `research/strong-localization-signal-2026-09-19` (merged to main).
- Feature commit: `9f043c6ed189f3d8a0d1d862545cfa92068abc6c`.
- Merge commit (main): `0c12223b15de4fa704dd2200ccae15b088ce23be`.
- DEV-evidence tag: `strong-localization-signal-2026-09-19` (annotated;
  peel `0c12223b15de4fa704dd2200ccae15b088ce23be` == main == origin/main;
  NOT a stable-tag move).
- LIGHT export: `project-2026-09-19-1056.zip`
  (122,151,655 bytes; `.git/HEAD` + `dist/pilot-kaggle-upload.zip` + `.sha256`
  verified inside).

```
PROJECT_EXPORT_READY
PROJECT_EXPORT_NAME=project-2026-09-19-1056.zip
PROJECT_EXPORT_PATH=C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project-2026-09-19-1056.zip
PROJECT_EXPORT_SIZE_BYTES=122151655
PROJECT_EXPORT_SHA256=f50178dd19b9eba43fb35d5c9d5f24a608519a1f358805966aae2d3675e8da8a
UPLOAD_THIS_FILE=project-2026-09-19-1056.zip
```

## 12. Where we are now

Stage 4b is closed with descriptive statistics (verdict unchanged).
`BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW`. A new external-pretrained embedding
signal PASSES its frozen gate on DEVELOPMENT and is frozen as the candidate
ranking signal. Stage 5 confirmatory NOT reached.

## 13. ONE next scientific action

Freeze a **confirmatory protocol** for the embed method (replacement
candidate-ranking signal = Sparse write set + SweRankEmbed-ranked additions)
under a fresh, explicitly authorized protocol with its own sample discipline
and sealed-set policy — or, alternatively, an authorized budgeted experiment
with the official SweRankLLM listwise reranker (option B, cost/compute plan in
the competitor review §10).

## 14. What I need from user

`Nothing — I can continue automatically.` (awaiting normal review of the
closed mission.)

## 15. Independent self-audit

- Objective unchanged: statistical closure + strong-signal pivot; adhered.
- Plan adherence: P0 → P1 order respected; comparator/K frozen before result
  inspection; temporal-guard recorded; no result-driven tuning.
- Over-engineering: none — files/steps scoped to the mission.
- Debt: SweRank venv + HF cache live outside the repo (versions recorded);
  embeddings regenerable deterministically; unit/blob manifests committed.
- Durability: all required durable outputs exist; governance docs updated;
  exports verified.
- Tag state: DEV-evidence tag created on the accepted merge; no stable tag
  moved; release-provenance invariant honored.