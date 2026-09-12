# Paper Writing Handoff

**Purpose:** start the manuscript phase from the frozen benchmark evidence
without reconstructing earlier sessions. The benchmark is **COMPLETE** at
`v0.11.0-benchmark-complete`; current phase is **paper / figures / supervisor
review**; **zero scientific runs remain**.

## 0. Title / claim discipline

**Provisional working title:**

> The Cost of Saying "Unchanged": Sparse Impact Plans for Token-Efficient
> Repository-Level Impact Selection

**Measured-result terminology** (safe to use for what was actually measured):

- impact selection;
- impact planning;
- repository-level change-impact selection;
- selection-stage efficiency.

**Broader motivation** (may be used as motivation only, never as a measured
result):

- selective regeneration;
- LLM-driven software evolution.

**Do NOT claim:**

- dependency-aware measured benefit (graph assistance was not injected);
- end-to-end regeneration success (not measured);
- universal scalability (no scaling experiment was run);
- universal impact-identification correctness (scenario 006).

**Mechanism terminology — Preserve-by-Omission:**

> The sparse representation rule in which explicit non-PRESERVE decisions are
> emitted while omitted candidates deterministically decode to PRESERVE.

## 1. Exact research scope

- **Selection stage only.** What was measured: which repository-relative `.py`
  paths each treatment predicts must change, scored against
  source-adjudicated hidden gold applied after inference.
- **NOT measured in these treatments:** Functional Correctness, Preservation,
  Architecture Compliance, or end-to-end regeneration outcomes. Do not claim
  them.
- Model: `qwen/qwen3-coder` pinned to DeepInfra through OpenRouter
  (`deepinfra/turbo`), fallback OFF, temperature 0.

## 2. Study inventory

| Study | Cells | Status |
|---|---|---|
| Todo Stage-C smoke (`scientific-stagec-selection-01`) | 30 | Frozen, exploratory component study |
| Todo Stage-C held-out (`scientific-stagec-heldout-01`) | 60 | Frozen, follow-up |
| Todo v1.1 end-to-end (`exp-20260906-v11`) | 30 | Frozen, NO-GO (0/30 functional passes) |
| djangoCMS primary (`scientific-stagec-djangocms-01`) | 60 | Frozen, primary selection study |
| djangoCMS ImpactPlan-v2 (`scientific-stagec-djangocms-impactplan-v2-01`) | 30 | Frozen, POST-HOC / EXPLORATORY (audited) |
| **M1A — Controlled 4096-cap feasibility boundary** (`scientific-djangocms-controlled-encoding-ablation-01`) | **0 study cells (2 probes)** | Frozen, POST-HOC / EXPLORATORY capability-feasibility boundary (audited) |

Studies are kept separate; **no 90-cell pooling**. M1A is a
capability/feasibility boundary, **NOT** a completed 60-cell controlled
ablation; it records that the Full-v2 capability probe terminates at the
frozen 4096 completion cap before emitting all 144 required decisions, whereas
the Sparse-v2 probe completes and deterministically reconstructs a valid
144-candidate policy (see
[`reports/CONTROLLED_ENCODING_4096_FEASIBILITY_RESULT.md`](../reports/CONTROLLED_ENCODING_4096_FEASIBILITY_RESULT.md)).
No semantic superiority claim is made. A separately preregistered cap-relaxed
study (M1B, completion cap 16384 for both arms) is planned but NOT run.

## 3. Final frozen metrics

### djangoCMS primary (valid-run micro; severe missing-data asymmetry)

| Arm | Valid / 30 | Precision | Recall | F1 |
|---|---|---|---|---|
| iterative_repository_agent | 25 | 0.6463 | 0.8407 | 0.7308 |
| impact_plan (v1) | 6 | 0.6765 | 0.9200 | 0.7797 |

### djangoCMS ImpactPlan-v2 (30 cells; POST-HOC / EXPLORATORY)

| Metric | Value |
|---|---|
| Recorded / Valid / Failed | 30 / 29 / 1 |
| Truncations | 0 |
| TP / FP / FN | 103 / 36 / 16 |
| Precision / Recall / F1 | 0.741007 / 0.865546 / 0.798450 |
| FNR | 0.134454 |
| Full-recall rate | 18 / 29 = 0.620690 |
| Total tokens / calls / cost | 144,353 / 30 / $0.064634 |
| Latency (all-30) | 391.437 s (mean 13.270 s) |

### Same-cap scenario-004 (cap = 4096)

- Historical ImpactPlan-v1: **5/5 truncated**.
- ImpactPlan-v2: **5/5 completed**, 874–1,525 completion tokens.

### Weakest v2 scenario

- Scenario 006: precision ≈ 0.389, recall ≈ 0.467, full recall 0/5.

## 4. Todo findings / caveats

- Smoke: 30/30 valid, full recall 15/15 per arm, P/R/F1 ceiling.
- Held-out: 60/60 valid, recall 30/30 per arm; precision Agent 0.8778 vs
  ImpactPlan 0.7694; F1 0.9200 vs 0.8540; ImpactPlan tokens −72.98%, calls
  −86.36%, cost −47.51%, total latency −51.81% (median caveat: Agent median
  8.211 s vs ImpactPlan 6.891 s, two large Agent outliers).
- `TODO_SELECTION_SATURATED=NO`: recall saturated on the 5-file universe,
  per-file precision not.
- v1.1 end-to-end Todo study: 0/30 functional passes; first-failure taxonomy
  dominated by downstream exact-patch (C=10) and source-validity (D=8)
  classes, not the impact selector (A=1). Preserved as historical NO-GO.

## 5. djangoCMS primary findings / caveats

- 60/60 cells recorded; 31 valid / 29 failed. Agent 25/30 valid; ImpactPlan-v1
  only 6/30 valid (19 × 4096-cap truncation + 3 unknown-path + 1 provider-429
  + 1 harness defect).
- **Primary v1 valid-run correctness rests on only 6 valid cells.** No
  between-arm accuracy claim is made.
- All-cell operational: Agent 449,792 tokens / 206 calls / $0.140850;
  v1 184,401 tokens / 28 calls / $0.123298 (tokens −59.0%, calls −86.4%,
  cost −12.5%, time +17.4%).
- **The dependency graph was NOT injected** into djangoCMS v1 (or v2). The
  primary study characterizes explicit-plan selection WITHOUT graph assistance.

## 6. v1 diagnostic story

- Full explicit ImpactPlan-v1 serialization over the 144-path universe
  exceeded the frozen 4096 completion cap (minimal 144-path plan ≈ 17,364
  bytes / ~4,341 estimated tokens). 19/30 v1 cells truncated at exactly 4096
  (`finish_reason=length`).
- A one-run 16K diagnostic terminated (10,650 completion tokens, 179.172 s,
  $0.01148) — termination at high serialization cost, no accuracy claim.
- An 8192 ablation probe truncated (not run as a study). Do not claim a
  measured repository-size threshold.

## 7. ImpactPlan-v2 results

- Sparse representation (explicit non-PRESERVE decisions + deterministic
  PRESERVE-by-omission + frozen numeric candidate IDs 1..144) achieved
  29/30 operational validity with 0 truncations in the frozen exploratory
  study (selection-only).
- Valid-only micro: P 0.741007 / R 0.865546 / F1 0.798450 / FNR 0.134454;
  full-recall 18/29.
- **v2 is SELECTION ONLY** and **POST-HOC / EXPLORATORY**; do not present it
  as a preregistered arm or as pooled with the primary study.
- v2 changes schema and planner instruction together — their effects are NOT
  independently isolated.

## 8. Efficiency results (descriptive only)

- v2 vs Agent (all-cell, djangoCMS): tokens −67.91%, calls −85.44%, latency
  −82.72%, recorded cost −54.11% (descriptive; NOT statistically significant;
  no prespecified analysis supports a superiority claim).
- Todo held-out: ImpactPlan tokens −72.98%, calls −86.36%, cost −47.51%,
  latency −51.81% (median caveat).

## 9. Defensible claims

1. Selection-stage evidence is complete, frozen, and audited at
   `v0.11.0-benchmark-complete` and `stagec-djangocms-impactplan-v2-study-01-audited`.
2. At scenario 004 / cap 4096, v1 truncated 5/5 while v2 completed 5/5
   (874–1,525 tokens) — v2 resolves the observed scenario-004
   output-serialization bottleneck (feasibility / mechanism evidence).
3. v2 achieved 29/30 operational validity with zero truncations in the frozen
   30-cell exploratory study, with measurable write-set correctness
   (P 0.741 / R 0.866 / F1 0.798, valid-only micro).
4. ImpactPlan showed strong selection-stage efficiency potential in the small
   (Todo) setting at equal recall, with median-caveated latency.

## 10. Forbidden / unsupported claims

- No end-to-end Functional Correctness, Preservation, or Architecture
  Compliance results (not measured).
- No "v2 statistically beats Agent", "universal superiority", or "no
  trade-off".
- No graph benefit (graph NOT injected into v1 or v2).
- No Saleor results (Saleor was not started).
- No measured repository-size threshold; no claim that v2 solves impact
  identification universally (scenario 006).
- No full R/P/V/H correctness.

## 11. Validity threats (must appear in Limitations / Threats to Validity)

1. Severe missing-data asymmetry in the primary study (Agent 25 vs v1 6 valid).
2. Output-budget asymmetry (Agent 8 × 1024 vs v1 1 × 4096).
3. Provider instability (DeepInfra `engine_overloaded` → 5 infrastructure
   failures).
4. v1/v2 schema+instruction changed together (not isolated).
5. v2 candidate universe still exposed in the prompt — larger-repository input
   scaling remains Future Work.
6. Scenario 006 weakness (P ≈ 0.389, R ≈ 0.467, full recall 0/5).

## 12. Canonical report / evidence paths

| Item | Path |
|---|---|
| Final results | `reports/FINAL_BENCHMARK_RESULTS.{md,csv}` |
| Validity / limitations | `reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md` |
| Reproducibility index | `reports/BENCHMARK_REPRODUCIBILITY_INDEX.md` |
| Cross-repo synthesis | `reports/CROSS_REPO_SYNTHESIS.md` |
| v2 results / design | `reports/DJANGOCMS_IMPACTPLAN_V2_RESULTS.{md,csv}` / `reports/DJANGOCMS_IMPACTPLAN_V2_DESIGN.md` |
| Todo selection | `reports/STAGEC_SELECTION_01_RESULTS.{md,csv}` / `reports/STAGEC_HELDOUT_01_RESULTS.{md,csv}` |
| Todo v1.1 NO-GO | `reports/SCIENTIFIC_MICROSTUDY_V11_RESULTS.{md,csv}` / `reports/V11_ROOT_CAUSE_TAXONOMY.{md,csv}` |
| Primary evidence dir | `reports/scientific-stagec-djangocms-study-01/` |
| v2 evidence dir | `reports/scientific-stagec-djangocms-impactplan-v2-01/` |
| Claim → evidence map | `reports/PAPER_CLAIM_EVIDENCE_MAP.md` |
| V7 audit reconciliation | `reports/PAPER_V7_AUDIT_RECONCILIATION.md` |
| Paper-claim verifier | `scripts/verify_paper_claims.py` |

## 13. Current Git / tag milestones

- Final benchmark tag: `v0.11.0-benchmark-complete` (peels to `5ffc662…`).
- Audited v2 study tag: `stagec-djangocms-impactplan-v2-study-01-audited`
  (peels to `f8e7aa8…`).
- Current branch: `paper/msc-manuscript-01` (paper phase).
- Do not move or recreate either benchmark tag; do not create new benchmark
  treatments.

## 14. POST-HOC DIAGNOSTIC OBSERVATIONS

These are **ZERO-API local diagnostics** recomputed from frozen artifacts only
(`reports/scientific-stagec-djangocms-impactplan-v2-01/run_records.jsonl`,
`benchmark_data/external_validity/djangocms_5_0_0_dependency_graph.json`,
`djangocms_5_0_0_candidate_universe.json`, frozen hidden gold). They are
**POST-HOC / DIAGNOSTIC / NON-CAUSAL** — they are NOT treatment results.

### 14.1 v2 completion-token diagnostic (valid cells)

Across the 29 valid ImpactPlan-v2 cells, completion output ranged from **528 to
1,525 tokens (mean ≈ 1,031)** against the frozen 4,096 completion cap
(valid = 29, min = 528, max = 1525, mean ≈ 1030.83, cap = 4096). **No valid v2
run approached the cap.** Therefore the scenario-006 recall weakness is not
supported as an output-cap/truncation failure; increasing the completion cap is
not motivated by the observed v2 outputs. (This states only that the observed
cap was non-binding; it does not claim that increasing the cap could
mathematically never change model behavior.)

### 14.2 Scenario-006 REGENERATE selection frequencies (5 valid cells)

Gold write set: `cms/models/pluginmodel.py`, `cms/admin/placeholderadmin.py`,
`cms/utils/plugins.py`.

| File | Selection frequency (valid cells) |
|---|---|
| `cms/models/pluginmodel.py` | 5/5 |
| `cms/plugin_rendering.py` | 5/5 |
| `cms/admin/forms.py` | 5/5 |
| `cms/admin/placeholderadmin.py` | 2/5 |
| `cms/utils/plugins.py` | 0/5 |

### 14.3 Post-hoc graph reachability diagnostic (frozen AST graph)

Graph-neighbour definition (analysis-only): **undirected one-hop reachability**
— a candidate is a one-hop neighbour if either `seed -> candidate` or
`candidate -> seed` exists in the frozen directed AST dependency graph
(144 nodes / 562 edges).

Diagnostic seeds (the three 5/5 consistently selected files):
`cms/models/pluginmodel.py`, `cms/plugin_rendering.py`, `cms/admin/forms.py`.

- unique one-hop neighbours **excluding** seed nodes: **41**
- unique one-hop neighbours **including** seed nodes: **44**
- `cms/admin/placeholderadmin.py` reachable: **YES**
- `cms/utils/plugins.py` reachable: **YES**

Exact edges providing reachability (frozen graph):

- `('cms/admin/placeholderadmin.py', 'cms/admin/forms.py')`
- `('cms/admin/placeholderadmin.py', 'cms/models/pluginmodel.py')`
- `('cms/admin/forms.py', 'cms/utils/plugins.py')`
- `('cms/plugin_rendering.py', 'cms/utils/plugins.py')`
- `('cms/utils/plugins.py', 'cms/models/pluginmodel.py')`

**Cautious interpretation (use only this):**

> The post-hoc graph reachability diagnostic shows that the under-recalled
> scenario-006 gold files lie locally adjacent, in the frozen AST dependency
> graph, to files that v2 selected consistently. This motivates evaluating
> dependency evidence as a SOFT signal or re-ranking feature in a future
> treatment.

**Do NOT write:** "the graph would have solved scenario 006"; "graph assistance
improves recall"; "v3 fixes the missed files"; or any causal improvement claim.
No graph-assisted inference was executed.

## 15. Future Work (documentation only; NOT to be implemented here)

### 15.1 Potential v3 (soft dependency evidence)

- Sparse initial ImpactPlan → soft dependency evidence / graph proximity →
  risk-aware re-ranking or second-stage verification → final sparse ImpactPlan.
- Graph evidence should be **SOFT**; do not hard-prune candidates.
- False-negative cost may be weighted above false-positive cost.
- Graph weights / thresholds require a **separate development protocol**.
- The existing six hidden djangoCMS scenarios must **NOT** be used for tuning
  and then re-used as an unbiased test set.

### 15.2 Hash / content-hash clarification

SHA-256 / content hashes are suitable for: evidence integrity, deterministic
cache invalidation, detecting whether a PRESERVE file was modified, and
post-execution preservation verification. They do **not** predict semantic
impact before a requested change is implemented. No hash/Merkle subsystem is
implemented in this task.

### 15.3 Candidate-universe scaling (no claim made)

No universal-scalability claim is made. A controlled candidate-universe scaling
study **could** evaluate serialization growth across increasing universe sizes
while keeping repository / scenario / model / provider fixed. **No such study
is authorized now.**

## 16. Immediate paper tasks

1. Finalize research questions.
2. Freeze contribution claims (use sections 9–10 above).
3. Final Results table (sections 3, 5, 7).
4. Figure 1 (e.g., v1 vs v2 scenario-004 output distribution and the v2
   per-scenario P/R/F1).
5. Related Work (grounded in the selection-only framing above).
6. Limitations / Threats to Validity (section 11).
7. ≤4-page IEEE manuscript refinement.

**Do NOT generate new scientific findings.** Everything must trace to the
frozen evidence paths in section 12.

## 17. V7 reproducibility & audit reconciliation

### 17.1 Recompute command (no API key)

```bash
python scripts/verify_paper_claims.py
```

Recomputes every headline metric from frozen run evidence, verifies the 30/30
sparse raw-response SHA-256 sidecars, and exits 0 only when the evidence is
internally consistent.

- Claim → evidence map: `reports/PAPER_CLAIM_EVIDENCE_MAP.md`
- V7 audit reconciliation: `reports/PAPER_V7_AUDIT_RECONCILIATION.md`

### 17.2 Verified additions

- **Serialized-record reduction (RECORD COUNT, not tokens):** across the 29
  valid v2 cells, total explicit decisions = 184, mean = **6.344828 / 144**
  (= 4.41% of the full-policy 144-file universe emitted), so the serialized
  file-decision record-count reduction is **95.6%**.
- **TOKEN SEMANTICS correction:** the manuscript values 449,792 (Agent) /
  184,401 (v1) / 144,353 (v2) are **TOTAL tokens (all-cell)** —
  prompt+completion across all recorded cells — **not** completion tokens.
  Table III column/caption must say TOTAL TOKENS (all-cell).
- **Failed v2 cell:** scenario 002 rep 3
  (`stgc-v2-...-002-impact_plan_v2-r3`) failed the frozen semantic invariant
  (`v_missing_validation_reason: cms/models/__init__.py` — VALIDATE with no
  cited supporting evidence); not rescored.
- **S006 sporadic FP:** beyond the five persistent table rows, the additional
  sporadic non-gold selection is `cms/utils/placeholder.py` at 1/5 (run
  `...006-impact_plan_v2-r3`), which brings pooled FP to 11.
- **Cap provenance classification B:** 4096 is the frozen protocol budget
  (preregistration + decision archive + `impact_planner.py`); no stronger
  contemporaneous rationale (e.g., provider maximum) is documented.

All claims above stay within frozen evidence and are re-derivable via the
recompute command.

## 18. Qwen3-32B Cross-Model Robustness Replication (POST-HOC)

A separate **POST-HOC CROSS-MODEL ROBUSTNESS REPLICATION** study was
completed and audited (2026-09-11): same repositories, cases, treatments,
gateway and provider, **different Qwen model** (`qwen/qwen3-coder` →
`qwen/qwen3-32b`, OpenRouter / DeepInfra `deepinfra/fp8`, reasoning explicitly
disabled, fallback off, temperature 0, cap 4096, graph OFF). 60 cells
(6 scenarios × 2 arms × 5 reps). Evidence:
`reports/scientific-stagec-djangocms-qwen3-32b-crossmodel-01/`,
`reports/QWEN3_32B_CROSSMODEL_PROTOCOL.md` (preregistered before cell 1),
`reports/QWEN3_32B_CROSSMODEL_AGREEMENT.{md,csv}`,
`reports/QWEN3_32B_PAPER_INTEGRATION_NOTE.md`,
`scripts/verify_qwen3_32b_crossmodel_claims.py` (zero API).

- New v1 (`impact_plan`): 2/30 valid, 24 truncations at the frozen 4096 cap —
  Qwen3-32B's verbose full-policy serialization does not fit the frozen budget;
  recorded verbatim, **no reruns**.
- New v2 (`impact_plan_v2`): 21/30 valid, 0 truncations; pooled P 0.360 /
  R 0.621 / F1 0.456 / FNR 0.379; full-recall 0.238.
- **DIRECTIONALLY REPLICATED** (descriptive): v2 validity rate (70%) > v1
  (6.7%) and v2 truncation rate (0%) < v1 (80%). This is descriptive only —
  no significance or causal claim.
- Cross-model Sparse-v2 Jaccard agreement vs historical Qwen3-Coder-480B-A35B-Instruct:
  102 cross-product pairs, mean 0.284 / median 0.231 / min 0.0 / max 1.0.
  Descriptive only; do **not** interpret as internal-reasoning similarity.
- Denominators are per-row and must **not** be merged with the historical
  rows (historical Qwen3-Coder-480B-A35B-Instruct evidence is unchanged and remains the primary
  evidence).

Recommended manuscript framing: report the new rows in a clearly separate
"cross-model robustness replication" table/section with the explicit
post-hoc label and the descriptive-agreement caveat. See
`reports/QWEN3_32B_PAPER_INTEGRATION_NOTE.md` for exact allowed/forbidden
claims.

## 19. Qwen3-Coder-30B-A3B-Instruct Cross-Model / Cross-Provider Robustness Replication (POST-HOC)

Model: **Qwen3-Coder-30B-A3B-Instruct** (OpenRouter slug
`qwen/qwen3-coder-30b-a3b-instruct`) @ OpenRouter / **SiliconFlow**
(`siliconflow/fp8`), model-native non-thinking, temperature 0, cap 4096,
graph OFF. 60 cells (6 scenarios × 2 arms × 5 reps), executed and audited
2026-09-11. Study id
`scientific-stagec-djangocms-qwen3-coder-30b-a3b-crossmodel-01`.

- **Provider note:** Novita was the task-preferred provider but FAILED the
  capability contract (rejects `response_format=json_schema`); SiliconFlow
  was the predeclared alternative and passed the identical request shape.
  Because the historical model was served via DeepInfra, model and provider
  are **confounded** — always describe this as a cross-model /
  cross-provider descriptive observation.
- v1: 17/30 valid, 13 failed, 11 truncations; v2: **28/30 valid**, 2 failed,
  **0 truncations**.
- v2 pooled P 0.5556 / R 0.6881 / F1 0.6148 / FNR 0.3119; full-recall 10/28.
- **DIRECTIONALLY REPLICATED** (descriptive): v2 validity 0.933 > v1 0.567
  and v2 truncation 0.000 < v1 0.367. This is descriptive only — no
  significance or causal claim.
- Cross-model Sparse-v2 Jaccard agreement vs historical
  Qwen3-Coder-480B-A35B-Instruct: 135 cross-product pairs, mean 0.491 /
  median 0.429 / min 0.091 / max 1.0. Descriptive only; do **not** interpret
  as internal-reasoning similarity.
- Accounting: 60 requests issued, 59 responses, 59 usage-known / 1
  usage-unknown (one transport failure); recorded 301,146 total tokens and
  $0.041518 live cost are **lower bounds**. A recorded-field wiring artifact
  (`request_dispatched` snapshot) is documented in
  `ACCOUNTING_CORRECTION_NOTE.md`; raw evidence, predictions and selection
  metrics unchanged.
- S006 remains the weak case (v2 P 0.053 / R 0.067 / F1 0.059) —
  qualitatively consistent with the historical model; descriptive only.

Recommended manuscript framing: a clearly separate "post-hoc cross-model /
cross-provider robustness replication" section with the provider confound
disclosed and the descriptive-agreement caveat. See
`reports/QWEN3_CODER_30B_A3B_PAPER_INTEGRATION_NOTE.md` for exact
allowed/forbidden claims, and `reports/SUPERVISOR_DECISION_MEMO.md` for the
unified comparison table and supervisor options.
