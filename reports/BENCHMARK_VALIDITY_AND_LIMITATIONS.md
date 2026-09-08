# BENCHMARK VALIDITY AND LIMITATIONS — djangoCMS External-Validity Study

**STUDY_ID:** `scientific-stagec-djangocms-01`
**Report corrected (UTC):** 2026-09-08T03:12:51.922429+00:00

## 1. What was measured

- Stage-C **selection behavior only**: which repository-relative `.py` paths each arm predicts must change, scored against the source-adjudicated hidden gold, applied AFTER inference only.
- Exactly 6 final visible scenarios × 2 arms × 5 repetitions = 60 frozen manifest cells; all 60 recorded.
- Universe: the frozen 144-path candidate universe (hash `43f4279b…`).

## 2. VALID vs FAILED (explicit definition)

- **VALID / SUCCEEDED:** inference reached a terminal selection result that is parseable / schema-valid, with selected paths passing runtime-universe validation, so TP/FP/FN and correctness metrics can be computed. **VALID does NOT mean correct** (a valid run may have precision/recall/F1 = 0).
- **FAILED:** a normal scorable terminal selection was not produced due to an operational failure (completion truncation, provider failure, invalid/non-universe paths, terminal empty selection treated fail-closed, or a harness defect). Failed cells are not converted into synthetic correctness scores.

## 3. Internal validity

- Pre-run: wiring tag `stagec-djangocms-study-wiring-verified-01` verified ancestor of HEAD; runtime universe == frozen universe (144, identical hashes); missing/extra path sets empty; every gold path ∈ universe; six final scenario IDs verified; old historical scenarios never model-facing.
- The EXACT six deterministic gates + independent audit PASSED before the study and again after closure (zero scientific calls in both).
- Manifest frozen before the first scientific call; not changed after execution began.
- Raw evidence persisted append-only per cell; interruption cannot destroy completed records.
- Raw scientific evidence hashes verified unchanged before/after this documentation closure (`raw_evidence_hashes.json`).

## 4. Critical validity threats

### 4.1 Severe missing-data asymmetry (PRIMARY LIMITATION)
- Agent: 25/30 valid; ImpactPlan: 6/30 valid.
- 24/30 ImpactPlan cells failed operationally: **19× completion truncation at the frozen 4096 cap**, 3× fail-closed unknown-path hallucination, 1× provider 429, 1× harness defect. All recorded failures; no cell rerun.
- ImpactPlan MICRO headline rests on 6 survivors and is **not** equal-evidence comparable to Agent's 25-run aggregate. Any arm comparison is provisional and must be re-audited (GPT-5.6 SOL) before any scientific claim.

### 4.2 Output-budget asymmetry (DEDICATED SECTION)

The study arms did NOT have equal completion-token allowance structure. **Do NOT simplify this into “Agent had exactly twice the same output budget.”**

- **Agent:** up to 8 model calls, each max 1024 completion tokens → maximum cumulative per-run completion-token allowance exposure ≈ 8 × 1024 = **8192 tokens across sequential calls**.
- **ImpactPlan:** 1 model call, max 4096 completion tokens → up to **4096 tokens in one structured response**.

The arms have different interaction structures. Agent can distribute output over several calls; ImpactPlan must serialize its plan in a single response. **The frozen 4096 cap may therefore confound representational scalability with completion-budget sufficiency.**

### 4.3 Serialization-size evidence (ZERO API)

- Minimal schema-valid ImpactPlan JSON over the 144-path universe: **17364 bytes / 17364 characters** (exact measurement; empty rationales/evidence).
- Rough token estimate (project heuristic, ESTIMATE ONLY): ~4341 tokens — already on the order of the 4096 cap before any rationale/evidence.
- All 19 truncated responses: `finish_reason=length`, `completion_tokens=4096` (measured). Successful ImpactPlan completions: min 920 / median 2165 / max 3750 tokens.
- The exact qwen/qwen3-coder tokenizer is not locally available and was not downloaded; no API call was made; the token estimate is labeled an estimate.

### 4.4 Provider instability
- DeepInfra upstream rate-limit (`engine_overloaded`) produced 5 infrastructure-failed cells (4 agent + 1 impact) despite the frozen 1-transient-retry policy and operational pacing.
- A brief provider outage at study start was waited out before launching; pacing (15 s inter-cell) is operational scheduling, NOT a scientific-input change.

### 4.5 Cap sensitivity
- ImpactPlan's 4096-completion cap is frozen. The model frequently emits verbose rationales/evidence that exceed 4096 tokens, so most ImpactPlan cells are cap-truncated. Compact outputs (successful cells) fit, so the cap is not inherently impossible — the representation is operationally vulnerable to truncation.

### 4.6 Cost-accounting gap
- ImpactPlan 007-r1 consumed one model call whose token usage/cost could not be recorded (harness `ValueError` before record construction). True spend is slightly above recorded $0.264148 (≈ $0.003). Ceiling is $0.50; COST_LOCK stays PASS with wide margin.

### 4.7 External validity
- Single repository (django CMS 5.0.0 pin `0f633fc9.`), single model, single provider session, 6 scenarios x 144-path universe. No general large-repository superiority claim; no end-to-end claim.

### 4.8 PRIMARY IMPACTPLAN WAS INSTANTIATED WITHOUT THE FROZEN DEPENDENCY GRAPH (documented fact)
- The primary djangoCMS ImpactPlan strategy was instantiated **without** the frozen dependency graph.
- Therefore the primary djangoCMS study (`scientific-stagec-djangocms-01`) characterizes **explicit-plan selection WITHOUT dependency-graph assistance**.
- The frozen 144-node / 562-edge AST graph was **NOT strategy-visible evidence** in the primary ImpactPlan treatment.
- ImpactPlan-v2 likewise does NOT inject graph assistance (graph-assisted planning is a separate possible future treatment).

## 5. What is NOT measured
- Regeneration / patching / repair / migration / functional execution correctness. Selection only.
- Cost-probe runs (costprobe-01, costprobe-02) are NON-STUDY diagnostic evidence and are excluded from the 60 scientific results.
- The 8192-cap ablation (proposal only; NOT run).
- The v2 cost/smoke probe (`scientific-stagec-djangocms-impactplan-v2-costprobe-01`) is a POST-HOC / EXPLORATORY / ONE-SCENARIO treatment; it is excluded from the 60 primary scientific results and does NOT modify the primary study.
- The future 30-run v2 evaluation (NOT executed in this task).

## 6. Interpretation rules honored
- Correctness before efficiency; efficiency reported only after correctness.
- No reruns for bad precision/recall/F1/surprising write sets/empty sets/arm losses.
- Raw evidence wins over documentation on any conflict.

## 7. ImpactPlan-v2 (POST-HOC / EXPLORATORY REDESIGN) validity notes
- v2 changes the output representation contract AND the corresponding planner instruction together; it is treated as ONE representation redesign, NOT a schema-only or prompt-only ablation.
- v2 uses the EXISTING structured-output mechanism (native OpenRouter JSON schema) with a v2-specific sparse schema; structured output already existed in v1.
- v2 emits ONLY non-PRESERVE decisions (REGENERATE / VALIDATE / HUMAN_REVIEW) keyed by deterministic frozen numeric candidate IDs (1..144); every omitted candidate decodes deterministically to PRESERVE, and the decoded policy contains exactly 144 candidate decisions.
- The single 16K observation where the unchanged v1 planner fallback classified the one omitted candidate as PRESERVE and that happened to be correct is an ILLUSTRATIVE empirical observation that deterministic omitted=>P decoding is operationally feasible; it does NOT prove omitted=>P is universally safe.
- Any projected v2 token savings from the 16K response remain PRE-EXPERIMENT ESTIMATES until measured by v2; token-per-entry figures are NOT universal constants.
- The v2 probe is primarily a technical-validity + cost + serialization probe. One-run accuracy differences between v1 and v2 are NOT statistically meaningful.
---

## 8. ImpactPlan-v2 30-CELL STUDY (POST-HOC / EXPLORATORY) validity notes

**STUDY_ID:** `scientific-stagec-djangocms-impactplan-v2-01` — see `reports/DJANGOCMS_IMPACTPLAN_V2_RESULTS.md`.

- v2 is ONE representation redesign (sparse output representation + planner instruction changed TOGETHER); prompt/schema effects are NOT independently isolated.
- v2 uses the EXISTING structured-output mechanism with a v2-specific sparse schema; structured output already existed in v1.
- Operational completeness is much higher than primary v1 ImpactPlan on the same cap: 29/30 valid (0 truncations) vs primary v1 6/30 valid (19x 4096-cap truncations). This is descriptive; the two treatments are separate studies with separate denominators (30 vs 60 cells) and must NOT be pooled.
- Correctness is still survivor-restricted to valid cells; the 1 failed cell (002-r3) is recorded and NOT re-run. Bad outcomes are scientific outcomes.
- The validity of the deterministic omitted=>PRESERVE reconstruction is a REPRESENTATION property (D(E_s(pi)) = pi under the contract), NOT a proof that the LLM identifies every truly impacted candidate.
- Scenario-006 had the weakest correctness (recall 0.4667, full-recall rate 0.0) — a scientific observation, NOT a tuning trigger.
- Prompt-evidence parity (zero scientific calls): scenario-004 v1 and v2 rendered inputs contain the SAME strategy-visible evidence block (32 semantic-seed items); semantic-seed evidence was NOT newly introduced by v2.
- Input-side scalability limitation: v2 removes explicit PRESERVE serialization but still exposes the full candidate universe + evidence in the prompt; a larger repository may face an input-side bottleneck. No threshold is derived from this single repository.
- Related-work note: Aider edit formats, Cheng et al. 2026 (arXiv:2604.27296), Wang et al. 2026 (arXiv:2604.19201), and Yadavally & Nguyen ICSE 2026 (Ripple) document related output-representation and change-impact work; see `reports/DJANGOCMS_IMPACTPLAN_V2_DESIGN.md` section 10.
- Future v3 mathematical note is DESIGN-ONLY: `docs/RISK_AWARE_SPARSE_IMPACT_SELECTION_MODEL.md` (zero scientific calls; does not modify v2).
