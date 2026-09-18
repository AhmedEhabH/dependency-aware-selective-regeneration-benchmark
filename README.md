# Repository-Level LLM Impact Selection Benchmark

**Exact model for this documentation pass:** openrouter/deepseek/deepseek-v4-flash-0731
**Last scientific tag:** `oracle-gap-bidirectional-repair-2026-09-18` (peel == scientific closure commit, see [Governance](#8-reproducibility--governance))

> **Start here.** This README is a ~5-minute entry point. Detailed scientific
> truth lives in
> [`00_CURRENT_RESEARCH_STATE.md`](00_CURRENT_RESEARCH_STATE.md), the
> chronological record of what was tried / learned / ruled out is in
> [`docs/RESEARCH_JOURNEY.md`](docs/RESEARCH_JOURNEY.md), and every experiment's
> evidence is in [`reports/`](reports/).

---

## 1. One-sentence problem

Repository-level LLMs must decide which files a requested change may affect;
exhaustive reasoning over every candidate is costly, while sparse localization
risks missing files the change actually touches.

## 2. Current research idea

```
Change request
  → Sparse first-pass impact plan (preserve-by-omission)
  → omitted-candidate recovery / bounded verification
  → final affected-file set
```

- **Preserve-by-Omission is representation/cost, not semantic correctness.** It
  emits only non-`PRESERVE` decisions and reconstructs the rest; this cuts
  serialization/output cost but does not by itself improve impact accuracy.
- **Fixed Route-B omission recovery is CONFIRMED** under the frozen djangoCMS
  protocol (composite beats analytic Random at every budget; gate PASS).
- **Current unsolved bottleneck = first-pass recall** (75–79% of proxy
  positives missed on DEVELOPMENT; the fixed next task).
- **The AI-assisted semantic audit is DESCRIPTIVE only** — inter-model
  agreement (0.698 / κ 0.558) is not human semantic gold.

## 3. Current scientific status — at a glance

| Milestone | Status | Main result | Scientific meaning | Evidence |
|---|---|:---|:---|:---|
| Preserve-by-Omission controlled study (M1A/M1B) | CONFIRMED (development/controlled) | Full-v2 F1 0.571 vs Sparse-v2 F1 0.794; ~90% lower completion output | Representation/cost advantage, not semantic superiority | [M1B](reports/CONTROLLED_ENCODING_16K_RESULT.md) · [M1B JSON](research/controlled-encoding-ablation-16k-01/final_metrics.json) |
| real-commit Full-vs-Sparse (M4A-3 / P1) | CONFIRMED (held-out 10) | ΔF1 (Sparse−Full) −0.009 CI [−0.130, +0.119]; Δcost/task −$0.0235 (CI excludes 0) | Cost effect transfers; semantic superiority does not | [P1 correction](reports/REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md) |
| LocAgent shared-protocol study (P5) | CONFIRMED (shared protocol) | LocAgent F1 0.333 (5/10 non-empty) vs Full 0.353 / Sparse 0.312; CIs cross zero | Comparable-or-lower F1 at far higher cost; 50% empty rate; NOT a faithful published-config reproduction | [P5C shared comparison](reports/LOCAGENT_P5C_SHARED_COMPARISON.md) |
| Route-B candidate-level recovery | DEVELOPMENT (djangoCMS DEV + Saleor DEV) | CIA/Hybrid beat analytic Random at every B; Oracle headroom large | Cheap evidence can rank some omitted positives above Random | [Route-B V2](reports/ROUTE_B_V2_ROBUSTNESS_REPORT.md) |
| Saleor DEVELOPMENT transfer | DEVELOPMENT | CIA B=5 macro ORR 0.237 vs random 0.006; **REPLICATES** | Cross-repository transfer on DEVELOPMENT | [Saleor transfer](reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md) |
| djangoCMS fixed Route-B confirmatory | CONFIRMED (spent INTERNAL_TEST) | Composite ORR B=5 0.165 vs random 0.028; gate PASS 5/5 folds, 4/4 B-points | Fixed Route-B omission recovery confirmed | [Confirmatory](reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md) |
| P2 adaptive-budget Phase 1 | NEGATIVE (frozen) | All four policies fail the strong-method gate on both repos | Choosing budget B is not the main bottleneck | [P2 final](reports/P2_PHASE1_FINAL_REPORT.md) |
| AI-assisted semantic plausibility audit | DESCRIPTIVE (NOT gold) | Exact agreement 0.698 / κ 0.558; historical-changed 0.847 vs omitted 0.632 | Descriptive assistant reliability; human gold still AWAITING | [AI audit](reports/AI_SEMANTIC_AUDIT_AGREEMENT_REPORT.md) |
| Oracle-gap / bidirectional repair exploration | POST-HOC (DEVELOPMENT) | Oracle-Add ALL F1 0.867/0.829; F1 0.85 NOT add-only-reachable on Saleor | First-pass recall is dominant; simple BBSR negative | [Oracle-gap](reports/ORACLE_GAP_BIDIRECTIONAL_REPAIR_FINAL_REPORT.md) |
| **Next task: First-Pass Recall Bottleneck** | FUTURE (not started) | — | FN anatomy → source-specific ceilings → ADD queues → matched-budget DEV comparison → gate | [Oracle-gap §17](reports/ORACLE_GAP_BIDIRECTIONAL_REPAIR_FINAL_REPORT.md) |

Labels: **CONFIRMED** = frozen confirmatory evidence · **DEVELOPMENT** = TRAIN/VALIDATION-only design evidence · **NEGATIVE** = valid empirical boundary · **DESCRIPTIVE** = not human gold · **POST-HOC** = labelled characterization · **FUTURE** = not started.

## 4. What we have learned

Each lesson: **Observation → Evidence → Consequence.**

1. **Sparse representation greatly reduces output/serialization burden, but sparse encoding is not semantic correctness.** M1B: ~90% lower completion output; P1: ΔF1 CI crosses zero. → Report representation cost separately from impact accuracy; never conflate the two.
2. **Real historical evidence did not show universal Sparse semantic superiority.** P1 ΔF1 (Sparse−Full) −0.009, CI [−0.130, +0.119]. → Claim cost/representation effects only; semantic effects are task-heterogeneous.
3. **LocAgent shared-protocol execution was very expensive/fragile in our setup; not a faithful published-config reproduction.** P5: 402 calls, ~32.8M prompt tokens, ~$9.93 normalized, 50% empty/non-usable rate, 900 s timeouts. → Use LocAgent numbers only under a shared protocol with explicit denominators; do not compare to its published headline.
4. **Cheap candidate-level evidence can rank some omitted positives above Random; Route-B transferred on Saleor DEVELOPMENT and confirmed on djangoCMS INTERNAL_TEST.** Route-B V2 + transfer + confirmatory all PASS their gates. → The fixed-B omission-recovery line is the solid anchor.
5. **Current graph-neighbor increment is small; most ranking signal is lexical/BM25.** Graph@K ≈ path_token@K; BM25@K is the strongest cheap baseline. → Do not assume graph evidence is the lever.
6. **Simple adaptive-budget P2 policies failed; choosing B is not the main bottleneck.** P2 Phase-1 NEGATIVE on both repos (strong-method gate FALSE). → Budget adaptation was ruled out as the primary fix.
7. **Add-only Route-B can improve omission recovery while lowering final file-level F1 because of false-positive additions.** Route-B add-only lowers F1 (djangoCMS B=5: 0.226 vs Sparse 0.318). → ORR and file-level F1 are different targets; FP additions must be controlled.
8. **Oracle analysis shows first-pass recall is dominant: 75–79% of proxy positives missed on DEVELOPMENT; Oracle-Add headroom ~+0.55–0.57 F1.** Oracle-gap decomposition. → The next task is FN anatomy / first-pass recall recovery, ZERO-API first.
9. **Cheap DROP/FP-pruning signal is too weak; simple BBSR failed despite oracle headroom.** FP-pruning flagged precision ≈ random; heuristic BBSR fails the progression gate on both repos. → A DROP queue is not yet viable with cheap observable signals.
10. **Therefore next task = FN anatomy / first-pass recall recovery, ZERO-API first.** Oracle-Add ALL F1 0.867/0.829 vs Sparse 0.318/0.261. → Concentrate on the ADD side, not the DROP side.

**Why negatives are kept:** every negative above (P2, RiskScorer, graph, BBSR,
LocAgent fragility) is a **search-space reduction under this protocol** — it
saves future researchers/engineers time, API cost, and effort by ruling out an
approach that was already tested. Negatives are empirical boundaries, not
thesis failures. Full per-milestone detail and revisit triggers:
[`docs/RESEARCH_JOURNEY.md`](docs/RESEARCH_JOURNEY.md).

## 5. Current key numbers

Only current headline numbers, each linked to its authoritative report:

- **Sparse representation cost/serialization:** M1B Sparse-v2 vs Full-v2: mean
  completion 809 vs 8,383 tokens; mean serialized records 5.9 vs 144.0; ~90%
  lower completion output
  ([M1B report](reports/CONTROLLED_ENCODING_16K_RESULT.md) · [correction note](reports/REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md)).
- **Fixed Route-B confirmatory (djangoCMS INTERNAL_TEST, spent):** composite ORR
  B=5 0.165 vs analytic Random 0.028; final selected set F1 0.239 (TP 71 /
  FP 274 / FN 179)
  ([confirmatory](reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md)).
- **Saleor DEVELOPMENT transfer:** CIA macro ORR B=5 0.237 vs random 0.006 —
  **REPLICATES**
  ([transfer](reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md)).
- **Oracle-gap DEVELOPMENT:** Sparse F1 0.318 (djangoCMS) / 0.261 (Saleor);
  Oracle-Add ALL 0.867 / 0.829; F1 0.85 NOT add-only-reachable on Saleor
  ([Oracle-gap](reports/ORACLE_GAP_BIDIRECTIONAL_REPAIR_FINAL_REPORT.md) ·
  [surfaces](reports/oracle_f1_ceiling_and_budget_surface.json)).
- **AI semantic-audit agreement (descriptive):** exact 0.698 / κ 0.558;
  historical-changed 0.847 vs omitted 0.632
  ([agreement](reports/AI_SEMANTIC_AUDIT_AGREEMENT_REPORT.md) ·
  [result JSON](reports/ai_semantic_audit_agreement_result.json)).

## 6. Current bottleneck and next experiment

**Bottleneck:** first-pass recall — 75–79% of proxy positives are missed before
any correction; Oracle-Add headroom is ~+0.55–0.57 F1, the largest single lever.

**Next experiment (fixed, NOT started):**
```
FN taxonomy → source-specific recovery ceilings → complementary ADD queues
→ matched-budget DEVELOPMENT comparison → progression gate
```
- **ZERO-API first** (deterministic analysis over existing DEVELOPMENT evidence).
- **Sealed sets remain sealed:** djangoCMS RESERVE, Saleor INTERNAL_TEST +
  RESERVE are never opened; the spent djangoCMS INTERNAL_TEST is used only as
  labelled POST-HOC sanity.
- Detail: [`reports/ORACLE_GAP_BIDIRECTIONAL_REPAIR_FINAL_REPORT.md`](reports/ORACLE_GAP_BIDIRECTIONAL_REPAIR_FINAL_REPORT.md) §17.

## 7. Evaluation and datasets

| Repository | DEV (design evidence) | Confirmatory | Sealed |
|---|---|---|---|
| djangoCMS | 174 tasks (V1 30 + V2 DEV_TRAIN 117 + DEV_VALIDATION 27) | INTERNAL_TEST 80 — **spent** (Route-B confirmatory) | RESERVE 59 — sealed |
| Saleor | 149 tasks | — | INTERNAL_TEST 80 + RESERVE 1086 — sealed |

- **Observed change-set proxy:** the parent→target changed production-file set
  is an **OBSERVED CHANGE-SET PROXY, not semantic gold**; no P/R/V/H gold is
  fabricated from diffs.
- **Public/hidden boundary:** inference uses parent commit only; target/hidden
  data never enters prompts.
- **HELD_OUT_TEST (10):** permanently exposed after P1/P5 — never tune on it.
- **Semantic audit:** the AI-assisted audit is descriptive; human two-rater +
  adjudicator ratings remain **AWAITING_HUMAN_RATINGS**.
- Definitions: [`reports/DATASET_OPERATIONAL_DEFINITIONS.md`](reports/DATASET_OPERATIONAL_DEFINITIONS.md).

## 8. Reproducibility / governance

- **Scientific truth:** [`00_CURRENT_RESEARCH_STATE.md`](00_CURRENT_RESEARCH_STATE.md)
- **Execution truth:** [`PROGRESS.md`](PROGRESS.md)
- **Append-only decisions:** [`DECISIONS.md`](DECISIONS.md)
- **Protocol v2:** [`docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md`](docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md)
- **Chronological research history:** [`docs/RESEARCH_JOURNEY.md`](docs/RESEARCH_JOURNEY.md)
- **Experiment evidence:** [`reports/`](reports/)
- **Tags:** scientific milestones are DEV-evidence tags (e.g.
  `oracle-gap-bidirectional-repair-2026-09-18`), NOT stable-tag moves.

**Traceability schema:** scientific closure commit and tag peel are **immutable
scientific facts** embedded in `GIT_STATE.txt`
(`scientific_closure_commit`, `scientific_closure_tag_peel`); **live
HEAD/origin-main are runtime git facts** and are queried with
`git rev-parse HEAD` / `git rev-parse origin/main` — a tracked file cannot
embed its own final live HEAD SHA.

## 9. Repository map

```
benchmark_data/      frozen datasets (real-commit V1/V2, Saleor)
src/benchmark/       source (loaders, execution, impact strategies, evaluation)
scripts/             reproducible experiment launchers + verification
research/            per-milestone evidence (run records, manifests, raw responses)
reports/             authoritative experiment reports + machine-readable JSON
docs/                protocols, runbook, research journey, roadmap, handoffs
msc_proposal/        proposal documents (V1.5 current)
dist/                release/upload bundles
```

Full map: [`docs/PROJECT_STRUCTURE_MAP.md`](docs/PROJECT_STRUCTURE_MAP.md).

## 10. Reproduce / test

```bash
# Deterministic smoke-profile dry run (mock backend — zero model calls)
python seven_arm_benchmark.py --dry-run --profile smoke

# Recompute every headline manuscript metric from frozen evidence
python scripts/verify_paper_claims.py

# Run the test suite
python -m pytest tests/unit tests/integration
```

Detailed: [`docs/BENCHMARK_RUNBOOK.md`](docs/BENCHMARK_RUNBOOK.md),
[`docs/REPRODUCIBILITY_PROTOCOL.md`](docs/REPRODUCIBILITY_PROTOCOL.md).

## 11. Citation / claim status

| Label | Meaning |
|---|---|
| **CONFIRMED** | frozen confirmatory evidence (e.g. djangoCMS INTERNAL_TEST) |
| **DEVELOPMENT** | TRAIN/VALIDATION-only design evidence (not confirmatory) |
| **NEGATIVE** | valid empirical boundary / search-space reduction |
| **POST-HOC** | labelled characterization of frozen evidence (not preregistered) |
| **DESCRIPTIVE** | e.g. AI-assisted semantic audit — NOT human semantic gold |
| **FUTURE** | not started (e.g. First-Pass Recall Bottleneck) |

Citation metadata: [`CITATION.cff`](CITATION.cff). License: MIT
([`LICENSE`](LICENSE)).

---

**Author:** Ahmed Ehab — [AhmedEhabH](https://github.com/AhmedEhabH)