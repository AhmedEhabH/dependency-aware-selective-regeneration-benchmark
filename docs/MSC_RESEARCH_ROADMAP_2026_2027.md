# MSC Research Roadmap — 2026–2027

**Dependency-Aware Selective Regeneration Benchmark**

This roadmap defines the long-term research program that builds on the closed
selection-stage benchmark (`v0.11.0-benchmark-complete`). It is scientific and
tool-neutral: development-assistant tooling is not part of the experimental
method and is not referenced here.

Status legend:

- **CLOSED** — evidence produced, audited, frozen.
- **COMPLETE / AUDITED** — study executed and independently audited.
- **NOT STARTED** — no scientific runs; design/pre-registration only.
- **PROPOSED FOLLOW-UP / NOT EXECUTED** — design proposal, no runs.

## Overall research position (2026-09-16, after the Sparse omission-risk study)

```text
ICCI / Preserve-by-Omission
        ↓
Real-commit dataset + P1/P5
        ↓
Cheap baselines
        ↓
Pluggable harness
        ↓
Sparse omission-risk study
        ↓
RESULT: task-level cheap RiskScorer not justified on n=30
        ↓
NEXT: enlarge development evidence + protect untouched confirmation
        ↓
djangoCMS V2-LARGE
        ↓
classical CIA + stronger history/static evidence
        ↓
conditional risk-routing OR candidate-level bounded verification
        ↓
Saleor external confirmation
        ↓
NestJS cross-ecosystem confirmation
        ↓
selective / bounded verification system
        ↓
final correctness–cost Pareto evidence
```

The thesis does NOT depend on RiskScorer success. Two contingency routes are
pre-registered (see the proposal and the V2 protocol):

### Route A — task-level selective routing
Use only if a larger development set establishes a reliable, stable risk signal.

### Route B — candidate-level bounded verification
If task-level risk remains unseparable: use cheap first-pass candidate
evidence, identify suspicious omitted candidates using independent
structural/history evidence, verify only those candidates under a hard budget,
and compare with always-verify and random matched-budget verification.

> **Route B V2 status (2026-09-17, PRE-CONFIRMATORY HARDENING V14):**
> DEVELOPMENT robustness closure COMPLETE (174 tasks; budget curve
> B∈{0,1,3,5,10}; analytic hypergeometric Random; frozen primary =
> **`BM25+Graph-Neighbor Composite (historical label: Classical-CIA)`**
> = normalized BM25 + binary graph-neighbor; Hybrid = rank-equivalent redundant
> control; 5/5 folds positive; 4/4 B-points above Random; bootstrap CIs exclude
> zero; gate PASS). Incremental-evidence ablation: the replicated cross-repo
> signal is **predominantly lexical (BM25)**; graph increment small and largely
> non-significant; no graph novelty claim. Bounded verifier pilot EXECUTED (30
> calls, $0.0023, Oracle-in-top-B = 1.000, diagnostic). **Confirmatory-freeze
> packet V2 ready-to-approve** (`reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_FREEZE_PACKET_V2.md`,
> choice B = ranking + actual verifier; djangoCMS INTERNAL_TEST sealed).
> **Saleor Route-B transfer REPLICATES on DEVELOPMENT** (2026-09-17; 149 tasks;
> B=5 composite 0.237 vs analytic Random 0.006, delta +0.231 CI
> [+0.180,+0.287]; DEVELOPMENT transfer replication, NOT confirmatory;
> `reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md`).

The thesis question remains:

> When is additional repository reasoning worth its inference cost, and how can
> bounded verification reduce missed-impact risk without paying the full
> always-on cost?

No claim is made in advance that Route A or Route B will win.

## Program overview

| Pillar | Title | Status |
|---|---|---|
| 1 | Sparse impact-policy representation | COMPLETE / AUDITED (M1A + M1B + M1 defensive closure) |
| 2 | Dependency-aware / risk-aware disclosure | COMPLETE / AUDITED (M3 development-set: hints MIXED, gated disclosure NOT PROMISING as implemented) |
| 3 | Real historical-change dataset | **COMPLETE — M4A-1 miner/schema/leakage barrier COMPLETE / AUDITED (2026-09-13; 6 MINER_DEV cases); M4A-2 scientific corpus COMPLETE / AUDITED (2026-09-13; 40 clean cases; split freeze TRAIN 24 / VALIDATION 6 / HELD_OUT_TEST 10; ZERO API calls); M4A-3/P1 real held-out evaluation EXECUTED (2026-09-14; 60/60 cells valid, 0 failures, 0 truncations; cap 16384 both arms; 10 independent tasks; bootstrap over tasks; serialized-record metric corrected 2026-09-14 — see `reports/REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md`); P5-A LocAgent shared-protocol adapter COMPLETE (2026-09-14; ZERO API)** |
| 4 | Cross-repository / cross-model generalization | PARTIAL (cross-model replications closed; cross-repo not) |
| 5 | Learned / fine-tuned impact selection | NOT STARTED |
| 6 | End-to-end selective regeneration and verification | NOT STARTED (selection-only evidence) |
| 7 | **Cross-repository confirmation — SALEOR (confirmed future pillar)** | SUITABLE-WITH-DEVIATIONS AUDIT DONE (2026-09-16); protocol frozen (`docs/SALEOR_REAL_COMMIT_PROTOCOL_V1.md`); **DEVELOPMENT DATASET READY + CLEAN 150×3 DEV SPARSE RUN EXECUTED (2026-09-17)** — identity/provenance migration `djangocms-rc-*` → `saleor-rc-*` (150/150 equivalence PASS; `reports/SALEOR_IDENTITY_MIGRATION_REPORT.md`), 446 valid / 4 failed / 7,316,986 tokens / $2.31 / 0 truncations (`reports/SALEOR_PORTABILITY_FIX_AND_150_BUILD_REPORT.md`, `reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md`); **frozen Route-B transfer REPLICATES on DEVELOPMENT (149 tasks; B=5 0.237 vs 0.006, Δ+0.231 CI [+0.180,+0.287]); INTERNAL_TEST/RESERVE sealed** |
| 8 | **Omission-risk detection — THESIS CORE (confirmed future pillar)** | DEVELOPMENT-EVIDENCE COMPLETE — task-level RiskScorer NOT justified on n=30 (Sparse-v2 development inference 2026-09-16); V2 design + sample-size analysis in `docs/REAL_COMMIT_DATASET_V2_PROTOCOL.md` |

> **Confirmed future pillars (2026-09-15).** Both pillars are authoritative
> parts of the MSc roadmap: SALEOR as the second-repository confirmatory line
> and Omission-risk detection as the thesis-core mechanism. Neither is executed
> in the cheap-non-LLM-baselines block; each requires its own freeze conditions
> before its first scientific result.

> **Reusable experiment architecture (2026-09-16, T3).** The
> **PLUGGABLE_RESEARCH_HARNESS_V1** (`src/benchmark/harness/`) + **LIVING
> SYSTEMATIC REVIEW V1** (`docs/LIVING_SYSTEMATIC_REVIEW.md`,
> `research/literature/`) are COMPLETE / AUDITED (ZERO API). The harness
> generalizes the research machinery through seams (DatasetAdapter,
> SnapshotProvider, Ranker, Planner, ModelBackend, RiskScorer/Verifier
> interface-only, BudgetPolicy, common Evaluator, versioned ExperimentSpec)
> and reproduces the frozen Protocol-A outputs byte-for-byte. This feeds
> Pillar 8 (omission-risk) as the execution substrate for the next scientific
> step **OMISSION_RISK_FEATURE_STUDY_V1**.
>
> **Omission-Risk Feature Study V1 (2026-09-16, T3; ZERO new LLM/API calls).**
> Phase-B preflight A–G + six gates + independent audit PASS. The
> deterministic-first-pass (metadata-corpus BM25@K) development analysis found
> **no reliable omission-risk signal at n=30** (only 1–2/83 features above the
> random AUROC band, all anti-correlated with the pre-registered direction;
> adaptive-K no better than fixed K=10; always-escalate dominates the cost
> analysis). The registered Sparse-v2-label study was initially DEFERRED
> (TRAIN/VALIDATION had no Sparse-v2 predictions); a frozen approval-gated
> **DEVELOPMENT-INFERENCE protocol** (90-cell Sparse-v2, ~$0.19) was produced
> (`docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md`).
>
> **Sparse-v2-label development-inference EXECUTED 2026-09-16 (approved).**
> 90-cell Sparse-v2 run on TRAIN/VALIDATION: **90/90 valid, 490,747 tokens /
> $0.184** (frozen 600,000-token AND $0.30 hard-stop respected), raw responses +
> sha256 sidecars persisted, six gates + leakage audit PASS pre-call. Task-level
> Sparse-v2 `has_fn` prevalence **26/30 = 86.7%** (26 positive / 4 negative);
> **class-balance gate FAILED (neg < 10)** → no multivariable RiskScorer;
> descriptive/single-feature only. Rerun on the real Sparse-v2 label: only
> **3/97 features above the random band** (4.85 expected by chance — a
> retrieval-peakiness cluster now direction-consistent), Sparse–BM25
> disagreement anti-predictive (0.303), graph inside band, adaptive-K no help,
> always-escalate still dominates. **A RiskScorer v1 is NOT statistically
> justified.** Report `reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md`;
> audit PASS. This bounds Pillar 8: the omission-risk detector is NOT yet
> validated and must not be frozen.

---

## POST-ICCI MSc PROPOSAL FOCUS (2026-09-16; proposal V1 draft in `msc_proposal/`)

Thesis direction: **Repository Change Localization Under Limited Inference
Budgets**. Working title (does not assume graph or RiskScorer success):
**Cost-Aware Repository Change Localization with Sparse Impact Planning and
Bounded Verification** (alternative: Repository Change Localization Under
Limited Inference Budgets). "Graph" is only one optional verifier, never a
required success. Everything below separates evidence by status:

### Proposal deadline schedule
- 2026-09-16/17: Proposal V1 supervisor-ready draft.
- by 2026-09-22: supervisor-feedback integration target.
- by 2026-09-25: scientific content freeze target.
- by 2026-09-27: print-layout freeze.
- by 2026-09-29: physical print ready.
- 2026-09-30: safety buffer.
- before 2026-10-01: submission-ready printed proposal.
- seminar presentation may continue improving afterward.

### A. Completed ICCI evidence (frozen, submitted)
- M1A / M1B / M1 defensive closure, M3 graph ablation (development-set),
  M4A-1/M4A-2 dataset + split freeze, M4A-3/P1 real held-out evaluation, P5
  LocAgent shared-protocol comparison + C1–C7 reporting corrections. Manuscript
  submitted (repo artifact `paper/v20-final/V20_FINAL_SUBMISSION.zip`; record
  `paper/v20-final/ICCI_SUBMISSION_RECORD_2026-09-15.json`).
- No arm-superiority claim from P1 (paired ΔF1 CIs cross zero); the cost
  effect (Sparse cheaper) is supported descriptively.

### B. Preliminary / descriptive P5 evidence (report but do not over-claim)
- LocAgent on the same 10 tasks: headline fail-closed F1 0.333 (TP10/FP13/FN27),
  usable-5 survivor-conditioned F1 0.417 (diagnostic only), 50% empty
  localization rate (2 timeout / 1 context-length / 2 completed-but-empty),
  402 calls / 32.8M tokens / $9.93 normalized estimate. OpenRouter-routed
  (backend not pinned per call). Classification: SYSTEM-LEVEL shared-task
  comparison, NOT an algorithm ablation and NOT a reproduction of the
  published fine-tuned result.

### C. Proposed selective-escalation work (NOT validated, NOT started)
- Pipeline: `Sparse first pass → omission-risk detection → selective
  graph-guided escalation → bounded false-negative verification`.
- The exposed ten-task HELD_OUT_TEST split is **PERMANENTLY EXPOSED** — no
  tuning, no confirmatory calls on it. All decision rules are selected on
  TRAIN/VALIDATION; fresh confirmatory evidence requires a fresh split or a
  second repository.
- Drafted (NOT executed) protocols:
  `docs/POST_ICCI_NEXT_EXPERIMENTS_DRAFT.md` (A cheap non-LLM baseline; B
  faithful LocAgent replication; C fresh second-repository / fresh-held-out
  confirmatory).
- Claim discipline: selective escalation is a PROPOSAL. It will be claimed as
  validated only after a preregistered fresh-split experiment with its own
  frozen budget.

---

## Pillar 1 — Sparse impact-policy representation

**Research question.** Can a sparse output representation (explicit
non-PRESERVE decisions with deterministic PRESERVE-by-omission reconstruction)
encode a complete repository-wide impact policy at a fraction of the
serialization cost of a full explicit plan, without sacrificing validity?

**Current evidence (CLOSED).**
- **M1A — Controlled 4096-cap feasibility boundary** (`COMPLETE / AUDITED`):
  under the frozen 4096 completion cap, the Full-v2 explicit-PRESERVE probe
  terminated at the cap (truncated at decision 76) while the Sparse-v2 probe
  completed (419 completion tokens, 144-candidate deterministic
  reconstruction). Zero 60-cell study cells executed; no semantic superiority
  claim.
- **M1B — Controlled 16K cap-relaxed encoding ablation** (`COMPLETE /
  AUDITED`): with a non-binding 16384 cap on **both** arms (the only study-level
  change from M1A), 60/60 cells valid, 0 truncations. Full-v2: mean 8,383
  completion tokens, 144 serialized records/run, P 0.4515 / R 0.7750 / F1
  0.5706. Sparse-v2: mean 809 completion tokens, ~4.9 serialized records/run as
  published (mean 5.9 corrected serialized-decision count per the 2026-09-14
  audit — frozen M1B evidence unchanged; see
  `reports/REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md` §9),
  P 0.7211 / R 0.8833 / F1 0.7940. Controlled descriptive reductions: completion
  tokens ≈ −90.35%, serialized records ≈ −95.9% corrected, recorded API cost
  ≈ −82.54%, total latency ≈ −63.29%. Label: **CONTROLLED ENCODING COST EFFECT:
  SUPPORTED** (descriptive). **No universal semantic superiority claim.**
- Independent artifact-level consistency audit PASS (2026-09-08) on the
  selection-stage closure; M1A/M1B zero-API verifiers pass (27/27 and 42/42).
- **M1 defensive closure** (`COMPLETE`, 2026-09-13; zero API calls; raw M1
  evidence unchanged): threat-to-validity matrix (15 threats,
  `reports/M1_THREATS_TO_VALIDITY_MATRIX.md`); scenario-level statistical
  analysis (`reports/M1_STATISTICAL_ANALYSIS.md` +
  `reports/m1_defensive_closure_stats.json`) treating **6 scenarios as the
  independent task units and 5 repetitions as nested observations** (no n=30
  claim; bootstrap over scenarios with n=6 stated; mean paired ΔF1 +0.1413,
  Δcompletion tokens −7,573.9 uniform across all 6 scenarios);
  per-scenario analysis (`reports/M1_SCENARIO_LEVEL_ANALYSIS.md`) incl. the
  **S006 counterexample** to any universal Sparse semantic claim.

**Missing evidence.** An external, independent representation-equivalence
reproduction; a causal (not descriptive) claim linking sparsity to cost; and
evidence that sparsity effects generalize beyond the six curated development /
mechanism scenarios. The M1 defensive closure makes the **mixed semantic sign
pattern explicit**: Sparse-v2 improves F1 in 4/6 scenarios (004/005/007/008)
and degrades in 2 (002/006), so the semantic direction is NOT statistically
established at the scenario level while the cost direction is uniform.

**Next experiment.** M2 — Controlled LLM serialization-density characterization
(see Pillar-2 note on M2/M3 ordering). M2 isolates how LLM behavior responds to
increasing serialization density under identical semantics.

**Success / failure interpretation.**
- Success: Sparse-v2 cost advantage replicates under tighter controls while
  validity is preserved at 100%.
- Failure: sparsity gains reverse on some scenario class, or a denser policy
  matches Sparse-v2 validity at comparable cost (representation is not the
  binding factor).

**Artifact to be produced.** A controlled density-stress result report with a
frozen manifest, raw responses + SHA sidecars, and a zero-API verifier.

**Major threats to validity.** Six development scenarios only (curated, not an
unbiased sample); single model (Qwen3-Coder-480B-A35B-Instruct); single
provider; no statistical significance testing; descriptive labels only.

---

## Pillar 2 — Dependency-aware / risk-aware disclosure

**Research question.** Does making the dependency graph and risk/impact
evidence visible to the selector change selection quality or cost, and can the
disclosure policy be made risk-aware?

**Current evidence.** **M3 — Graph ablation C0/C1/C2** is now COMPLETE /
AUDITED (2026-09-13; POST-HOC EXPLORATORY DEVELOPMENT-SET; 90 new cells + 30
reused C0; see `reports/M3_GRAPH_PROTOCOL.md` and `reports/M3_GRAPH_RESULTS.md`):

- C0 (Graph OFF) = audited M1B Sparse-v2 reuse: P 0.7211 / R 0.8833 / F1
  0.7940 / FN 14 / FP 41.
- C1 (Graph Hints, full 562-edge AST graph as soft evidence): P 0.8136 / R
  0.8000 / F1 0.8067 / FN 24 / FP 22 — **precision +9.2pp, FP −19, but
  recall −8.3pp, FN +10, tokens ×2.6** (the graph acted as a pruning signal,
  not a recall amplifier).
- C2 (Graph-Gated Disclosure): mandatory-zone compliance **2/30 (1-hop) →
  0/30 (2-hop)**; all 58 failures were `mandatory-disclosure-failure` (the
  sparse schema's natural output length is far below the 25–41 / 111–119
  in-zone mandate).
- S006: C1 F1 0.278 → 0.414 (precision-driven; the structural miss
  `cms/utils/plugins.py` persists under soft evidence). 3-hop pre-registered
  NOT eligible (zones 129–130/144).
- **GRAPH HINT SIGNAL: MIXED. GRAPH-GATED DISCLOSURE: NOT PROMISING (as
  implemented).** No universal graph claim.

**Missing evidence.** A held-out graph evaluation (development-set only so
far); a disclosure design that matches the sparse output capacity (e.g.,
smaller zones or an explicit in-zone serialization policy); cross-repository
graph evidence.

**Next experiment.** A **held-out graph evaluation** is NOT authorized on the
six curated scenarios (they are exhausted as a mechanism set). The next
graph-related milestone is a held-out arm of RealCommitImpactDataset-v1
(development/validation/held-out separation), or a redesigned disclosure
variant that caps the mandate at the model's demonstrated sparse output
capacity — both only after supervisor direction.

**Success / failure interpretation.**
- Success (hints): recall improves or FP falls without a recall tax.
- Failure (hints): FN rises (observed in M3: FN 14 → 24) — the hint signal
  is then only a precision/FP intervention.
- Success (disclosure): compliance ≥ 50% with in-zone FN recovered.
- Failure (disclosure): compliance collapse (observed: 2/30 → 0/30).

**Artifact to be produced.** (M3 artifacts produced: protocol, results,
taxonomy, hop sensitivity, cost-recall trade-off, zero-API verifier 40/40.)

**Major threats to validity.** Same six-scenario development set; graph
construction is an extra modeling choice; compliance collapse is schema/
zone-capacity specific and must not be over-generalized; no held-out
confirmation.

---

## Pillar 3 — Real historical-change dataset

**Research question.** Do the selection results transfer from curated
requirement-change scenarios to real historical code changes?

**Current evidence.** Todo + djangoCMS selection studies use curated,
source-adjudicated scenarios. **M4A-1 (2026-09-13) implemented and froze the
RealCommitImpactDataset-v1 miner infrastructure** (branch
`research/real-commit-impact-dataset-v1-miner-01`): deterministic miner over
real djangoCMS history (ancestors of the frozen 5.0.0 anchor), versioned
record schema, frozen v1 eligibility/exclusion rules, candidate universe +
dependency graph built from the parent commit only, physical `public/` vs
`hidden/` separation, `intent_mentions_changed_path` leakage detector, and
**6 MINER_DEV cases** permanently marked non-held-out (ZERO API calls; six
Pre-Benchmark gates + independent audit PASS). See
`reports/REAL_COMMIT_M4A1_PROTOCOL.md`, `reports/REAL_COMMIT_M4A1_VALIDATION.md`,
`reports/REAL_COMMIT_M4A1_AUDIT.md`, `reports/REAL_COMMIT_BENCHMARK_PLAN.md`;
fine-tuning readiness note in `research/FINE_TUNING_READINESS.md`.
**M4A-2 (2026-09-13) completed the scientific corpus + split freeze** on
branch `research/real-commit-impact-dataset-v2-corpus-01` (ZERO API calls):
40 clean scientific cases mined from the newest 6000 ancestors of the frozen
anchor (≈2016–2025) with the frozen M4A-1 rules + leakage barrier
(`allow_intent_path_leakage=False`, 92 leaked ineligible), R1/R2/R3
related/duplicate removal (582 exact-set, 0 shared-PR, 5 suspected-related
adjudicated), and a deterministic metadata-only split freeze (seed
`20260913`) before any model result: TRAIN 24 / VALIDATION 6 /
HELD_OUT_TEST 10. The historical diff is an **OBSERVED CHANGE-SET PROXY**,
never semantic ground truth. Six scientific gates + independent audit PASS
(610 checks). Reports: `reports/REAL_COMMIT_M4A2_PROTOCOL.md`,
`reports/REAL_COMMIT_M4A2_ADJUDICATION.md`,
`reports/REAL_COMMIT_M4A2_VALIDATION.md`, `reports/REAL_COMMIT_M4A2_AUDIT.md`,
`benchmark_data/real_commit_impact_v1/scientific_manifest.json`,
`benchmark_data/real_commit_impact_v1/split_freeze.json`.

**Missing evidence.** Any real-commit **scientific** model result beyond
M4A-3/P1 (the 40-case corpus + split freeze are COMPLETE / AUDITED 2026-09-13;
the M4A-3/P1 held-out evaluation is **EXECUTED** 2026-09-14 — 60/60 cells
valid, 0 failures, 0 truncations, cap 16384 both arms, 10 independent tasks,
bootstrap over tasks; P5-A LocAgent shared-protocol adapter COMPLETE
2026-09-14, ZERO API, MINER_DEV/TRAIN/VALIDATION only).

**P5 — LocAgent shared-protocol comparison (COMPLETE 2026-09-15; reporting
corrections applied 2026-09-15, zero-API).** P5-B real LocAgent pilot on
VALIDATION executed **6/6** on WSL2 Ubuntu (the Windows
`fork` blocker was solved by the POSIX host; the documented compatibility
patch also bounds queue-get deadlocks and BadRequest transport spins — process
/error handling only, no scientific change). P5-C HELD_OUT_TEST executed
**10/10** (5 non-empty localizations / 5 fail-closed empty). Same 10 P1 held-out tasks,
same frozen proxy, common evaluator. LocAgent micro P/R/F1 0.435/0.270/0.333
(5/10 non-empty) vs Full-v2 0.339/0.369/0.353 and Sparse-v2 0.387/0.261/0.312;
authoritative ledger 402 calls / 32.8M tokens / $9.9288 (frozen pricing
snapshot, normalized estimate); official native Acc@K (task hit iff
correct-in-topK == min(proxy, K)) Acc@1 4/10, Acc@3 4/10, Acc@5 2/10 (the
historical 4/10/8/10/9/10 were item-hit sums); paired ΔF1 CIs cross zero. The
5 empty outcomes are 2 timeout, 1 context-length BadRequest, 2
completed-but-empty (50% empty/non-usable, NOT 50% timeout). Provider wording
is **OpenRouter-routed Qwen3-Coder** (ledger records the OpenRouter gateway;
logs show both DeepInfra and Venice upstream errors). Classified as a
**system-level shared-task comparison** (P1 temp 0 vs LocAgent temp 1), not an
algorithm ablation. Reports: `reports/LOCAGENT_P5C_SHARED_COMPARISON.md`,
`reports/LOCAGENT_P5C_AUDIT.md`.
**Artifact to be produced.** RealCommitImpactDataset-v1 (splits + schema +
hashes) and a real-commit evaluation report.

**Major threats to validity.** Data curation bias (which commits are sampled),
intent-text quality, change-set proxy noise, repository/source drift, licensing
of third-party repos.

---

## Pillar 4 — Cross-repository / cross-model generalization

**Research question.** Do selection quality and the sparse-representation
cost effect generalize across repositories and models?

**Current evidence (PARTIAL).** Cross-model replications are **COMPLETE /
AUDITED**: Qwen3-32B (DeepInfra) and Qwen3-Coder-30B-A3B-Instruct (SiliconFlow)
both directionally replicate the Sparse-v2 advantage (v2 validity > v1,
v2 truncation < v1, descriptive only). Saleor is explicitly **not executed**
(defined but FUTURE WORK).

**Missing evidence.** A second, larger repository actually executed; a
third-party replication on independent infrastructure; any claim beyond
"directional".

**Next experiment.** A single pinned Saleor selection probe set (or an
equivalent large-repository scenario set) with the frozen protocol, gated by
cost bounds — not a full 48-cell Pilot.

**Success / failure interpretation.**
- Success: Sparse-v2 remains operational and cost-advantaged on a larger
  repository.
- Failure: Sparse-v2 validity collapses or the candidate universe becomes the
  dominant cost factor (scaling limit found and reported).

**Artifact to be produced.** A large-repository selection report + frozen
manifest + zero-API verifier.

**Major threats to validity.** Repository-size confounds, provider/model
interaction, cost ceilings censoring runs, and no statistical power in
one-off probes.

---

## Pillar 5 — Learned / fine-tuned impact selection

**Research question.** Can a fine-tuned model learn the sparse impact-policy
representation and improve selection accuracy over in-context prompting?

**Current evidence.** PLAN ONLY. `research/FINE_TUNING_READINESS.md` records
the training-ready export requirements. No fine-tuning has been performed.

**Missing evidence.** A training corpus with proper splits; any trained
checkpoint; any evaluation.

**Next experiment.** Build **RealCommitImpactDataset-v1** with explicit
TRAIN / VALIDATION / HELD-OUT TEST splits (Pillar 3); fine-tune a coder model
on the TRAIN split only; evaluate on the HELD-OUT TEST split (never seen in
training); compare against the in-context Sparse-v2 baseline. This is a
separate, separately-authorized milestone.

**Success / failure interpretation.**
- Success: fine-tuned model improves held-out P/R/F1 over in-context baseline
  at comparable or lower cost.
- Failure: no improvement (in-context prompting already captures the
  representation) — report and do not over-claim.

**Artifact to be produced.** Fine-tuned checkpoint metadata + split indices +
evaluation report + reproduction script.

**Major threats to validity.** Data leakage across splits, evaluation on the
training distribution, catastrophic forgetting, compute/cost limits, and
confusing "fine-tuning works" with "fine-tuning is necessary".

---

## Pillar 6 — End-to-end selective regeneration and verification

**Research question.** Does selecting a sparse set of files and regenerating
only those files preserve functional correctness and reduce cost end-to-end?

**Current evidence.** Selection-stage benchmark only. The completed studies
measure selection (which paths the model predicts must change) scored against
hidden gold — **not** functional correctness, preservation, architecture
compliance, or end-to-end regeneration correctness. The historical v1.1
end-to-end Todo study was NO-GO (0/30 functional passes) and is preserved as
historical evidence.

**Missing evidence.** Any accepted end-to-end regeneration success; any
measured preservation / functional-correctness result on the frozen scenario
set.

**Next experiment.** A bounded end-to-end regeneration study (select →
regenerate → repair → validate) on the Todo/djangoCMS development set with a
strict functional-validation gate and a hard cost ceiling. Not authorized for
this thesis cycle unless the supervisor directs it.

**Success / failure interpretation.**
- Success: selected-file regeneration passes functional validation at a cost
  below full-file regeneration.
- Failure: correctness cannot be preserved (report the failure taxonomy; the
  selection result still stands as a separate contribution).

**Artifact to be produced.** End-to-end results + validator + cost report.

**Major threats to validity.** Repair/validation machinery confounds the
selection contribution; timeouts censor runs; evaluator coverage limits
correctness claims.

---

## Pillar 7 — Cross-repository confirmation — SALEOR (confirmed future pillar)

**Status: READY-TO-RUN (2026-09-16 evening).** Full Saleor history cached
(22,615 commits, non-shallow); sampling frame reconstructed
(6000 → 2409 → 1352 → **1316** independent eligible); split proposal frozen
(seed 20260916; DEV_TRAIN 120 / DEV_VALIDATION 30 / INTERNAL_TEST 80 /
RESERVE 1086; all-pool SHA `6be5c994…`); sample-size analysis done; protocol in
`docs/SALEOR_REAL_COMMIT_PROTOCOL_V1.md`; suitability
`reports/SALEOR_REPOSITORY_SUITABILITY_AUDIT.md`; gates
`reports/SALEOR_PRE_INFERENCE_GATE_REPORT.md`. **Saleor DEVELOPMENT DATASET READY
(2026-09-17):** identity/provenance correction (case IDs `saleor-rc-<sha>`,
repository identity, 150/150 scientific-payload equivalence PASS;
`reports/SALEOR_PORTABILITY_FIX_AND_150_BUILD_REPORT.md`,
`reports/SALEOR_IDENTITY_MIGRATION_REPORT.md`); frozen DEV manifest; a clean
150×3 DEVELOPMENT sparse run is the next scientific step under the frozen
budget (450 cells / 9M tokens / $3.00; INTERNAL_TEST/RESERVE sealed).

**Role in the thesis.** Saleor is the second-repository candidate
(subject to the frozen protocol-fit audit):
- whether Preserve-by-Omission savings transfer beyond djangoCMS;
- semantic fidelity under a materially different repository (e-commerce
  modular monolith vs CMS plugin architecture);
- candidate-universe scale/density behavior;
- and to provide untouched confirmatory evidence.

**Required preconditions before any Saleor scientific result:**
1. audit repository suitability (DONE — SUITABLE-WITH-DEVIATIONS);
2. define candidate-universe semantics (DONE in the frozen profile);
3. define historical-change mining rules (DONE — frozen M4A-2 rules);
4. define proxy/adjudication protocol (DONE — frozen R1/R2/R3);
5. freeze TRAIN/VALIDATION/HELD_OUT_TEST (PENDING frame reconstruction);
6. freeze baselines and metrics (frozen study contract);
7. ensure TEST remains untouched until final confirmation.

**Current project threat note.** Saleor costs a real model budget; the v0.9.x
Kaggle pilot evidence (saleor scenarios) is legacy/engineering only and is not
confirmatory scientific evidence for this proposal line.

**Generalization ladder (frozen, 2026-09-16; terminology corrected 2026-09-18):**
- Stage 1 — djangoCMS V2-LARGE: within-repo large evidence + untouched internal test.
- Stage 2 — Saleor: cross-repository evidence in a different real system
  (Python/Django; SUITABLE-WITH-DEVIATIONS).
- Stage 3 — NestJS: **cross-language / cross-framework** evidence
  (TypeScript; `reports/NESTJS_REPOSITORY_SUITABILITY_AUDIT.md`,
  `docs/NESTJS_REAL_COMMIT_PROTOCOL_V1.md`; SUITABLE-WITH-DEVIATIONS;
  preferred but NOT forced — predeclared yield criterion, JabRef backup).
- **Stage 7 (future) — polyglot SINGLE-REPOSITORY generalization (added
  2026-09-18):** a FUTURE feasibility candidate is `grafana/grafana`, because
  the same repository contains a Go backend and a TypeScript frontend with
  documented backend/frontend parity paths. NOT scientifically accepted yet —
  requires a repository feasibility audit, per-language production-source
  universe definition, cross-language dependency/coupling representation,
  ≥60 eligible real commits target if feasible, explicit mixed-language
  commit strata, no generated/vendor/test leakage, and the same
  proxy/leakage rules. Terminology rule (2026-09-18): **"multi-language"
  future work has TWO distinct meanings that must not be conflated** — (A)
  CROSS-LANGUAGE / CROSS-REPOSITORY (different repos from different
  ecosystems: Python, TypeScript, Java, Go) vs (B) POLYGLOT
  SINGLE-REPOSITORY (one repository containing substantial production code
  in multiple languages with real cross-language change coupling). Ambiguous
  roadmap wording is renamed to
  `cross-language + polyglot-repository generalization`.
- **P2 adaptive-budget / adaptive-k status (gated, not deleted;
  2026-09-18):** P2 Phase-1 is COMPLETE, NEGATIVE, and frozen; adaptive
  budget is NOT the current bottleneck and is NOT active work. The
  Shichao-Zhang / adaptive-k / demand-driven-k line remains FUTURE WORK and
  is gated: revisit ONLY after a stable ranking/recovery signal exists,
  because choosing k cannot rescue a poorly ordered candidate list.

---

## Pillar 8 — Omission-risk detection — THESIS CORE (confirmed future pillar)

**Status: DEVELOPMENT-EVIDENCE COMPLETE — task-level RiskScorer NOT justified
on n=30; the mechanism pivots to Route A/B (see the overall research position
above) and a V2 development program (`docs/REAL_COMMIT_DATASET_V2_PROTOCOL.md`).**

**Omission-Risk Feature Study V1 (2026-09-16, T3):**
Phase-B preflight A–G + six gates + independent audit PASS. Deterministic-
first-pass (metadata-corpus BM25@K) development analysis: **no reliable
omission-risk signal at n=30** — only 1–2 of 83 features exceed the random
AUROC 95% band (expected ~12 by chance), all anti-correlated with the
pre-registered direction (peaked/confident retrieval → more omissions,
hypothesis-generating only); adaptive-K does not beat fixed K=10; the
cost-sensitive decision analysis shows **always-escalate dominates** at any
C_FN/C_VERIFY ratio because the first pass omits files on ~73–80% of tasks.
The **registered Sparse-v2-label study is EXECUTED 2026-09-16** via the approved
90-cell development-inference protocol (TRAIN/VALIDATION only): 90/90 valid,
490,747 tokens / $0.184 within the 600k/$0.30 hard stop; Sparse-v2 `has_fn`
prevalence **86.7% (26/30; 4 negatives)**; **class-balance gate FAILED** → no
multivariable RiskScorer, descriptive/single-feature only; only **3/97 features
above the random band** (4.85 expected by chance — retrieval-peakiness cluster,
now direction-consistent); Sparse–BM25 disagreement anti-predictive; graph
inside band; adaptive-K no help; **always-escalate still dominates; a
RiskScorer v1 is NOT statistically justified** (report
`reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md`, audit PASS).

**Why it is central.** P1 false-negative diagnostics show that action labels
alone cannot identify most omissions:

- Full-v2 FN 70: PRESERVE 70 / VALIDATE 0 / HUMAN_REVIEW 0.
- Sparse-v2 FN 82: PRESERVE 74 / VALIDATE 8 / HUMAN_REVIEW 0.

Most missed affected files are **silent PRESERVE decisions**, so an independent
omission-risk signal is required.

**Planned mechanism (design only):**

```
Sparse first-pass impact plan
    ↓
Omission-risk estimation
    ↓
low risk → accept
high risk → bounded graph/agent verification
    ↓
revised impact scope
```

**Rules:** risk detection is developed using TRAIN/VALIDATION only; NEVER tuned
on the exposed ten-task HELD_OUT_TEST; not implemented in the cheap-baselines
block; preserved as the core thesis mechanism after baseline establishment.

**Route A (task-level selective routing) vs Route B (candidate-level bounded
verification):** both are pre-registered in the V2 protocol
(`docs/REAL_COMMIT_DATASET_V2_PROTOCOL.md`). Route A is used only if a larger
development set establishes a reliable, stable risk signal; otherwise Route B
verifies only suspicious omitted candidates under a hard budget and is compared
with always-verify and random matched-budget verification.

**Frozen comparison plan for the thesis (subject to feasibility):**
Random/cheap control, BM25, adaptive cheap retrieval (if justified),
classical/static CIA, Sparse planner, Full planner, faithful LocAgent/reference
agent (when reproducible), Sparse+Always Verify, Sparse+Random Verify (matched
budget), Sparse+Selective/Bounded Verify, Oracle routing upper bound. If
task-level routing is unsupported, arm 10 becomes candidate-level bounded
verification. Metrics: P/R/F1/FNR, FN recovery, selected candidate count,
escalation/verification rate, calls, tokens, cost, latency, failures,
graph/index build cost separated from query cost, correctness–cost Pareto
frontier. Per-repository metrics primary; macro-average across repos; pooled
secondary; repository-ID confound check; no single large repo dominates the
headline.

---

## Protocol A — Cheap non-LLM baseline block (2026-09-16; ZERO API; CLOSED + DEV tag)

**Status:** COMPLETE / AUDITED (development evidence; merged to `main`; DEV tag
`cheap-baselines-v1-dev-2026-09-16` — audited DEVELOPMENT evidence, NOT
confirmatory).

**Purpose.** Establish the cheapest defensible file-selection reference family
for the selective-escalation pipeline: B0 Random@K, B1 BM25@K, B2 path-token@K,
B3 Graph@K (lexical/path-token seeds), B4 Hybrid@K (frozen 0.5/0.5) over
TRAIN 24 + VALIDATION 6 only (HELD_OUT_TEST ten permanently excluded; ZERO
LLM/API).

**Findings (development evidence):**
- **BM25@K is the strongest cheap lexical baseline.** VALIDATION primary
  development-decision table: BM25@3 P 0.333/R 0.240/F1 0.279 (precision
  operating point), BM25@10 P 0.217/R 0.520/F1 0.306/FNR 0.480 (recall
  operating point, highest VALIDATION F1). **K is an operating-point curve, NOT
  a final configuration** — the primary selection objective of a future frozen
  protocol fixes K.
- **Graph@K ≈ path_token@K**; because Graph@K seeds are lexical/path-token
  derived, this shows the cheap lexical-seeded expansion adds little over the
  seed signal — **no general negative graph claim**.
- **Hybrid@K ≈ BM25@K** (frozen 0.5/0.5 does not materially improve) →
  motivates bounded/selective graph verification later, not score fusion.
- **Fair-comparison boundary:** BM25 provides a meaningful zero-LLM
  localization signal on development data; whether it matches/underperforms
  LLM planners is **untested under a shared fresh confirmatory protocol**
  (P1 Full/Sparse numbers are directional context only — different exposed
  split).
- **Efficiency:** ~403 s BM25 wall dominated by parent git-archive
  materialization (index-build cost); query/ranking ~1.3 s total — BM25 is not
  "403-second inference"; caching/pre-indexing is an engineering optimization.
- **Path-mention sensitivity (ZERO API):** excluding the 3 TRAIN full-intent
  path-mention cases, BM25@3 F1 0.283 → 0.262 (TRAIN) / 0.282 → 0.267 (pooled);
  material qualitative ordering unchanged; frozen dataset untouched.
- Six gates + independent audit PASS; report
  `reports/CHEAP_BASELINES_V1_REPORT.md`; diagnostic
  `research/cheap-baselines-v1/path_mention_sensitivity_v1.json`.

**Relationship to the pillars.** This block feeds Pillar 8 (omission-risk) as
the cheap first-pass baseline whose FNR is the target of omission-risk
detection, and it arms the fair-comparison boundary for Pillar 7 (Saleor) and
the faithful LocAgent line (Pillar 4-adjacent): a future LLM-vs-BM25 comparison
must run on a fresh shared confirmatory split.

---

## Cross-cutting governance

- **Scientific runs.** Zero new scientific API calls until a next milestone is
  explicitly authorized. Each milestone pre-registers its comparison, frozen
  manifest, and cost ceiling before cell 1.
- **Evidence rules.** Ground truth is evaluation-only. Raw responses are
  persisted append-only with SHA-256 sidecars. No claim of statistical
  significance without a registered analysis.
- **Verification.** Every closed study ships a zero-API verifier and an
  independent audit.
- **No unsupported novelty claims.** Every label above is descriptive and
  scoped to its evidence.

## Study status summary (explicit)

| Study | Status |
|---|---|
| M1A — Controlled 4096-cap feasibility boundary | **COMPLETE / AUDITED** |
| M1B — Controlled 16K cap-relaxed encoding ablation | **COMPLETE / AUDITED** |
| M1 defensive closure (threat matrix + statistics + per-scenario) | **COMPLETE** (2026-09-13) |
| M2 — Controlled LLM serialization-density characterization | **NOT STARTED** |
| M3 — Graph ablation C0/C1/C2 (hints + gated disclosure) | **COMPLETE / AUDITED** (2026-09-13; POST-HOC EXPLORATORY DEVELOPMENT-SET; hints MIXED, gated NOT PROMISING as implemented) |
| Graph-Gated Disclosure | **EXECUTED / NOT PROMISING as implemented** |
| Protocol A — Cheap non-LLM baselines v1 | **COMPLETE / AUDITED** (2026-09-16; DEVELOPMENT evidence; DEV tag `cheap-baselines-v1-dev-2026-09-16`; BM25 strongest cheap lexical; K = operating-point curve; no LLM-vs-BM25 claim) |
| Pluggable Research Harness V1 + Living Systematic Review V1 | **COMPLETE / AUDITED** (2026-09-16; T3 reusable experiment architecture; ZERO API; DEV tag `research-harness-v1-dev-2026-09-16`; Protocol-A outputs reproduced byte-for-byte) |
| Omission-Risk Feature Study V1 | **COMPLETE / AUDITED in two stages** (2026-09-16). Stage 1 deterministic-first-pass development analysis (T3; ZERO LLM; Phase-B A–G + six gates + audit PASS; DEV tag `omission-risk-feature-study-v1-dev-2026-09-16`). Stage 2 **Sparse-v2-label development-inference EXECUTED** (approved 90-cell run, TRAIN/VALIDATION only; 90/90 valid; 490,747 tokens / $0.184 within the 600k/$0.30 hard stop; Sparse-v2 `has_fn` prevalence 86.7% (26/30, 4 negatives); class-balance gate FAILED → descriptive/single-feature only, NO multivariable RiskScorer; no signal survives the random band; report `reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md`; audit PASS) |
| RealCommitImpactDataset-v2 design + sampling frame + sample size | **COMPLETE / AUDITABLE** (2026-09-16; T3 ZERO API; funnel 6000->916->334->329->40; 289 untouched beyond exposed v1; N=120-150 recommended from frame, not round; split proposal seed 20260916 + hashes; 150 V2 dev case bundles built; INTERNAL_TEST 80 + RESERVE 59 untouched) |
| V2 Sparse development inference + omission-risk analysis | **EXECUTED** (2026-09-16; 431/450 cells, fail-closed token-ceiling stop at 2.5M tokens / \.873; 144 new V2 tasks; merged 174 tasks 155 pos / 19 neg; C4 signal gates FAIL - v1 peakiness signal does not replicate in V2 (universe-size artifact); NO multivariable RiskScorer; Route B pivot) |
| Classical/static CIA baseline V1 | **IMPLEMENTED** (2026-09-16; T3 ZERO LLM; 150 V2 dev cases; BM25/GRAPH@K strongest; closure arms weaker; development evidence) |
| Saleor / NestJS suitability + protocols | **SUITABLE-WITH-DEVIATIONS** (2026-09-16; T3 ZERO API; protocols frozen; frames blocked on full-history caches) |
| MSc Proposal V1 + seminar outline | **DRAFT COMPLETE** (2026-09-16; msc_proposal/; 6-page PDF; deadline-critical path to print before 2026-10-01) |
| Proposal V1.2 + BibTeX triage + traceability ledgers | **COMPLETE** (2026-09-16 evening; msc_proposal/MSC_PROPOSAL_V1_2.pdf 7 pages; 13 .bib exports triaged, 10 high-priority verified from primary sources; 6 ledgers: decision/problem/experiment/baseline/literature) |
| LocAgent P5R forensics + rescue pilot | **EXECUTED** (2026-09-16 evening; 0/5 usable; wrapper timeout ineffective against upstream 900 s hard-coded deadline; full 10-task rerun NOT triggered; P5 immutable; reports/LOCAGENT_P5R1_PILOT_REPORT.md) |
| Route B candidate-level omission recovery V1 | **EXECUTED** (2026-09-16 evening; zero-LLM; R4 Classical CIA beats Random at B=5: DEV_VALIDATION 0.180 vs 0.037, CI [-0.003,+0.285]; no universe-size artifact corr 0.105; first positive candidate-level signal; reports/ROUTE_B_OMISSION_RECOVERY_V1_REPORT.md) |
| **djangoCMS Route-B CONFIRMATORY (djangoCMS INTERNAL_TEST, 2026-09-17)** | **EXECUTED + CONFIRMS** (Ahmed-authorized; 80 tasks; 560 calls / 1,470,174 tokens / $0.505917; 0 failures; composite ORR vs analytic Random B=5 0.165 vs 0.028, Δ+0.137 CI [+0.075,+0.205]; CIs exclude zero at every B; no size artifact; reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md) |
| **P2 adaptive-budget algorithm program** | **ADOPTED — DEVELOPMENT-only, Nov 2026–Mar 2027** (Shichao-Zhang-inspired policies + systematic landscape 24 entries; common evaluation contract; Saleor INTERNAL_TEST sealed as possible P2 confirmation set; docs/P2_IMPLEMENTATION_ROADMAP_2026_2027.md) |
| Saleor Stage-2 READY-TO-RUN | **READY-TO-RUN** (2026-09-16 evening; full history 22,615 commits; frame 6000->2409->1352->1316; split proposal seed 20260916 DEV_TRAIN 120 / DEV_VALIDATION 30 / INTERNAL_TEST 80 / RESERVE 1086; pre-inference gates PASS; no inference tonight) |
| Semantic-proxy audit protocol + packets | **PREPARED** (2026-09-16 evening; docs/SEMANTIC_PROXY_AUDIT_PROTOCOL.md; 25 DEVELOPMENT-only evidence packets; human audit required; AI notes not gold) |

## 2026-09-17 update — PRE-CONFIRMATORY HARDENING V14 (ZERO API)

- **Ranker identity audit:** the frozen Route-B V2 primary is exactly
  **`BM25+Graph-Neighbor Composite (historical label: Classical-CIA)`** =
  normalized BM25 + binary graph-neighbor; Hybrid is a redundant
  rank-equivalent alias (0 differing task-budget cells, 174 djangoCMS + 149
  Saleor DEV). Terminology corrected; formula unchanged.
- **Incremental-evidence ablation:** cross-repo signal predominantly lexical
  (BM25); composite−BM25 paired deltas small with CIs including zero at most B
  on both repos; Saleor graph arm ≈ binary-neighbor floor; history available
  only for djangoCMS (94 tasks). No new ranker selected.
- **Confirmatory freeze packet V2** supersedes V1 (truthful name; Saleor
  transfer AVAILABLE + REPLICATES; exact repetition/failure/verifier
  semantics; frozen claim = end-to-end Sparse → frozen ranker → bounded
  verifier on djangoCMS INTERNAL_TEST).
- **Confirmatory API budget frozen:** 560 calls / ≤2,100,000 tokens / ≤$1.00
  with per-call reservation rule; DEVELOPMENT distributions only.
- **Proposal V1.4** created — Saleor DEV transfer replication is a
  material scientific change; V1.3 immutable. **V1.4 print addendum
  (2026-09-17):** Experimental Design table rebuilt (no overlap), bibliography
  rendered in the PDF (21 verified entries), timeline replaced with
  **2026-11 → 2027-10** (substantive completion 2027-07/08; 09/10 = publication
  buffer); 10 pages; SHA-256
  `50957a2525f7430de47fd9306895d2b4c80b30c358d3cafe6798a0a27b0525b1`.
- **V1.4 final document-consistency audit** (`reports/V14_FINAL_DOCUMENT_CONSISTENCY_AUDIT.md`):
  PASS — exact ranker wording, no graph/quality-parity claims, DEVELOPMENT-only
  cross-repo claims, task counts 174/149 consistent, bibliography renders.
- **Confirmatory execution package** (`reports/DJANGOCMS_CONFIRMATORY_EXECUTION_READINESS.md`):
  **READY_FOR_AHMED_APPROVAL** (ZERO test peek; 560 calls / 2,100,000 tokens /
  $1.00; fail-closed reservation ledger; dry-run PASS; real run gated on
  Ahmed's approval).
- **P2 adaptive budget** (`docs/ADAPTIVE_BUDGET_P2_PRE_REGISTRATION_NOTE.md`):
  **CONDITIONAL — AFTER FIXED ROUTE-B CONFIRMATION** (observable features,
  dev-only evaluation, stop/fail criteria, and ACTIVE/negative-close evidence
  now specified; NO learned policy fitted).
- **Semantic human audit readiness** (`reports/SEMANTIC_AUDIT_HUMAN_EXECUTION_READINESS.md`):
  **READY_FOR_HUMAN_EXECUTION** (blinded manifest, Rater A/B + adjudicator
  forms, one-page instructions, kappa/sensitivity scripts, checklist, exact
  save locations, one synthetic dry-run clearly NOT_REAL; integrity + dry-run
  PASS).
- INTERNAL_TEST/RESERVE remain SEALED (both repos). Next external step:
  Ahmed approves/rejects opening djangoCMS INTERNAL_TEST under the frozen V2
  packet and budget.

## 2026-09-17 update — DJANGOCMS CONFIRMATORY RUN (AUTHORIZED, EXECUTED, CONFIRMS) + P2 PROGRAM

- **CONFIRMATORY djangoCMS INTERNAL_TEST EXECUTED** (Ahmed-authorized 2026-09-17;
  ONLY djangoCMS V2 INTERNAL_TEST = 80 tasks; RESERVE + Saleor sealed).
  Exact frozen V2 protocol + budget: **560 calls / 1,470,174 tokens /
  $0.505917** (ceilings 560 / 2,100,000 / $1.00), 0 failures, 0 excluded,
  raw+sha 560/560 verified.
  **Composite ORR vs analytic Random:** B=1 0.0591 vs 0.0055 (Δ +0.0522, CI
  [0.0163,0.0957]); B=3 0.1098 vs 0.0166; B=5 0.165 vs 0.0277 (Δ +0.1367, CI
  [0.0746,0.2046]); B=10 0.2669 vs 0.0554. CIs exclude zero at every B; 5/5
  folds positive; 4/4 B-points; no size artifact. **Classification: CONFIRMS.
  Fixed Route B is now scientifically confirmed on djangoCMS INTERNAL_TEST.**
  Reports: `reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md`,
  `reports/DJANGOCMS_CONFIRMATORY_AUDIT.md`,
  `research/djangocms-confirmatory-route-b/`.
- **FROZEN BOUNDARIES.** The opened djangoCMS INTERNAL_TEST is permanently used
  as the confirmatory test; it will NEVER be reused as a fresh test for P2
  algorithm selection. P2/adaptive work uses DEVELOPMENT only (djangoCMS DEV +
  Saleor DEV). No method change based on outcomes.
- **P2 FIVE-MONTH ALGORITHM PROGRAM ADOPTED (Nov 2026 - Mar 2027; DEVELOPMENT
  only).** Reproduce Shichao-Zhang-inspired adaptive-budget ideas (Learning-k,
  cost-sensitive KNN, one-step computation, demand-driven kNN,
  adaptive-neighborhood) and systematically discover/classify competing
  algorithms (adaptive/conditional computation, selective prediction/
  abstention/learning-to-defer, cascaded inference, optimal stopping, budgeted
  retrieval, active search, contextual bandits where mechanistically
  relevant). Classify each as DIRECT_COMPETITOR / CLOSE_ANALOGUE /
  ALGORITHMIC_INSPIRATION / BACKGROUND_ONLY / REJECT_IRRELEVANT. Common
  zero-LLM/low-cost harness vs fixed B={1,3,5,10}, Analytic Random, BM25-only,
  frozen composite, Oracle, InspectAll. Select ≤1-2 justified P2 candidates on
  DEVELOPMENT only; use still-sealed Saleor INTERNAL_TEST for P2 confirmation
  only if justified; otherwise close P2 negative with the fixed-B thesis
  intact.
- **Sealed now:** djangoCMS RESERVE, Saleor INTERNAL_TEST, Saleor RESERVE.

## 2026-09-18 update — P2 PHASE-1 EXECUTED (NEGATIVE) + semantic AI-audit packages

- **P2 Phase-1 WAS EXECUTED (2026-09-18; DEVELOPMENT; ZERO API).** The Nov 2026
  window was brought forward: the common adaptive-budget harness
  (`src/benchmark/p2/`) + four pre-registered interpretable policies
  (P2-P1..P2-P4) were evaluated on djangoCMS DEV (174) + Saleor DEV (149).
  **Result: all four NEGATIVE** (P2-P3 REJECTED_BY_DESIGN as a size/repo
  artifact); strong-method gate FALSE; stronger methods NOT run. **P2 Phase-1 =
  NEGATIVE (frozen).** Phase-2 candidates: NONE yet. The expanded landscape
  (P2-025..P2-039) remains the Phase-2 candidate pool. The broader P2 program
  remains OPEN for possible Phase-2 candidates. Fixed-B thesis (CONFIRMED)
  intact. (`reports/P2_PHASE1_FINAL_REPORT.md`, tag
  `p2-phase1-negative-closure-2026-09-18`.)
- **Semantic-proxy human audit** remains **AWAITING_HUMAN_RATINGS**
  (human-work blocker; machine prep complete and verified).
- **Independent AI-assisted semantic-plausibility audit packages PREPARED
  (2026-09-18; ZERO API):** fully blinded two-assistant audit batch packages
  under `research/semantic_audit/ai_blinded_v1/` (five fresh-chat batches per
  assistant, neutral IDs, sealed private mapping, strict JSON output schema,
  agreement script + tests, human minimal-spot-check generator). Inter-model
  agreement is NOT human agreement; the human audit remains the gold.
- **Sealed now (unchanged):** djangoCMS RESERVE, Saleor INTERNAL_TEST, Saleor
  RESERVE.
