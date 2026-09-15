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

## Program overview

| Pillar | Title | Status |
|---|---|---|
| 1 | Sparse impact-policy representation | COMPLETE / AUDITED (M1A + M1B + M1 defensive closure) |
| 2 | Dependency-aware / risk-aware disclosure | COMPLETE / AUDITED (M3 development-set: hints MIXED, gated disclosure NOT PROMISING as implemented) |
| 3 | Real historical-change dataset | **COMPLETE — M4A-1 miner/schema/leakage barrier COMPLETE / AUDITED (2026-09-13; 6 MINER_DEV cases); M4A-2 scientific corpus COMPLETE / AUDITED (2026-09-13; 40 clean cases; split freeze TRAIN 24 / VALIDATION 6 / HELD_OUT_TEST 10; ZERO API calls); M4A-3/P1 real held-out evaluation EXECUTED (2026-09-14; 60/60 cells valid, 0 failures, 0 truncations; cap 16384 both arms; 10 independent tasks; bootstrap over tasks; serialized-record metric corrected 2026-09-14 — see `reports/REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md`); P5-A LocAgent shared-protocol adapter COMPLETE (2026-09-14; ZERO API)** |
| 4 | Cross-repository / cross-model generalization | PARTIAL (cross-model replications closed; cross-repo not) |
| 5 | Learned / fine-tuned impact selection | NOT STARTED |
| 6 | End-to-end selective regeneration and verification | NOT STARTED (selection-only evidence) |

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

**P5 — LocAgent shared-protocol comparison (COMPLETE 2026-09-15).** P5-B real
LocAgent pilot on VALIDATION executed **6/6** on WSL2 Ubuntu (the Windows
`fork` blocker was solved by the POSIX host; the documented compatibility
patch also bounds queue-get deadlocks and BadRequest transport spins — process
/error handling only, no scientific change). P5-C HELD_OUT_TEST executed
**10/10** (5 valid, 5 fail-closed 900 s timeouts). Same 10 P1 held-out tasks,
same frozen proxy, common evaluator. LocAgent micro P/R/F1 0.435/0.270/0.333
(valid 5/10) vs Full-v2 0.339/0.369/0.353 and Sparse-v2 0.387/0.261/0.312;
authoritative ledger 402 calls / 32.8M tokens / $9.9288; native Acc@K
1=4/10, 3=8/10, 5=9/10; paired ΔF1 CIs cross zero. Classified as a
**system-level shared-task comparison** (P1 temp 0 vs LocAgent temp 1), not an
algorithm ablation. Reports: `reports/LOCAGENT_P5C_SHARED_COMPARISON.md`,
`reports/LOCAGENT_P5C_AUDIT.md`.

**Success / failure interpretation.**
- Success: selection accuracy on real commits is comparable to the curated
  scenarios (external validity).
- Failure: real-commit selection is materially worse (curated scenarios were
  unrepresentative; report the gap).

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