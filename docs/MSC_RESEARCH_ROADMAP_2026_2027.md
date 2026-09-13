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
| 1 | Sparse impact-policy representation | COMPLETE / AUDITED (M1A + M1B) |
| 2 | Dependency-aware / risk-aware disclosure | NOT STARTED (M3 design draft) |
| 3 | Real historical-change dataset | NOT STARTED |
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
  0.5706. Sparse-v2: mean 809 completion tokens, ~4.9 serialized records/run,
  P 0.7211 / R 0.8833 / F1 0.7940. Controlled descriptive reductions: completion
  tokens ≈ −90.35%, serialized records ≈ −96.60%, recorded API cost ≈ −82.54%,
  total latency ≈ −63.29%. Label: **CONTROLLED ENCODING COST EFFECT:
  SUPPORTED** (descriptive). **No universal semantic superiority claim.**
- Independent artifact-level consistency audit PASS (2026-09-08) on the
  selection-stage closure; M1A/M1B zero-API verifiers pass (27/27 and 42/42).

**Missing evidence.** An external, independent representation-equivalence
reproduction; a causal (not descriptive) claim linking sparsity to cost; and
evidence that sparsity effects generalize beyond the six curated development /
mechanism scenarios.

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

**Current evidence.** The completed djangoCMS selection studies explicitly did
**not** inject the dependency graph (graph OFF). A protocol draft exists
(`reports/NEXT_GRAPH_EXPERIMENT_PROTOCOL_DRAFT.md`): C0 Sparse-v2 Graph-OFF vs
C1 Sparse-v2 Graph-Hints, soft evidence only; Graph-Pruned C2 deferred; defined
as POST-HOC EXPLORATORY DEVELOPMENT-SET.

**Missing evidence.** Any executed Graph-OFF vs Graph-Hints comparison.

**Next experiment.** **M3 — Sparse-v2 Graph-OFF vs Graph-Hints** (NOT STARTED;
the next scientific milestone). Follow the existing draft: six development
scenarios, Sparse-v2 arm, temperature 0, frozen provider, graph hints injected
as strategy-visible evidence; soft/exploratory interpretation only; no
unregistered follow-up.

**Success / failure interpretation.**
- Success: a measurable, repeatable change in selection P/R/F1 or cost when
  graph hints are visible.
- Failure: no measurable difference (graph evidence is redundant with the
  requirement text / candidate universe on this scenario set).

**Artifact to be produced.** M3 result report + frozen manifest + zero-API
verifier; a risk-aware disclosure design note if the graph evidence shows
value.

**Major threats to validity.** Same six-scenario development set; graph
construction itself is an extra modeling choice; risk of post-hoc
over-interpretation (pre-register the comparison before running).

---

## Pillar 3 — Real historical-change dataset

**Research question.** Do the selection results transfer from curated
requirement-change scenarios to real historical code changes?

**Current evidence.** Todo + djangoCMS selection studies use curated,
source-adjudicated scenarios. A real-commit benchmark is designed but not
executed (`reports/REAL_COMMIT_BENCHMARK_PLAN.md`; fine-tuning readiness note
in `research/FINE_TUNING_READINESS.md`).

**Missing evidence.** Any real-commit evaluation.

**Next experiment.** Construct **RealCommitImpactDataset-v1** (see
`research/FINE_TUNING_READINESS.md` for the full record schema): real
repository commits paired with change-intent text, candidate universes,
dependency features, observed change-set proxies, action labels, change type,
provenance hashes, and explicit TRAIN / VALIDATION / HELD-OUT TEST splits.
Evaluate Sparse-v2 (and Full-v2 control) selection on the held-out test split.
Held-out test examples must never enter any future fine-tuning.

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
| M2 — Controlled LLM serialization-density characterization | **NOT STARTED** |
| M3 — Sparse-v2 Graph-OFF vs Graph-Hints | **NOT STARTED** |
| Graph-Gated Disclosure | **PROPOSED FOLLOW-UP / NOT EXECUTED** |