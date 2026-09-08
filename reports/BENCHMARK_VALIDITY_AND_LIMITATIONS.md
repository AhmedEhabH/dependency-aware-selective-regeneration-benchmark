# BENCHMARK VALIDITY AND LIMITATIONS — djangoCMS External-Validity Study

**STUDY_ID:** `scientific-stagec-djangocms-01`
**Generated (UTC):** 2026-09-08T01:49:59.327506+00:00

## 1. What was measured

- Stage-C **selection behavior only**: which repository-relative `.py` paths each arm predicts must change, scored against the source-adjudicated hidden gold.
- Exactly 6 final visible scenarios × 2 arms × 5 repetitions = 60 frozen manifest cells; all 60 recorded.
- Hidden gold (`benchmark_data/external_validity/djangocms_hidden_gold_draft.json`) used AFTER inference only.
- Universe: the frozen 144-path candidate universe (`djangocms_5_0_0_candidate_universe.json`, hash `43f4279b…`).

## 2. Internal validity

- Pre-run: wiring tag `stagec-djangocms-study-wiring-verified-01` verified as ancestor of HEAD; runtime universe == frozen universe (144, identical hashes); missing/extra path sets empty; every gold path ∈ universe; the six final scenario IDs verified; old historical scenarios never model-facing.
- The EXACT six deterministic gates + independent audit PASSED before any scientific call and again after closure (zero scientific calls in both).
- Manifest frozen before the first scientific call; not changed after execution began.
- Raw evidence persisted append-only per cell; a process interruption cannot destroy completed records.
- Scoring is deterministic (TP/FP/FN/P/R/F1/FNR/full-recall); MICRO vs MACRO are reported separately and never mixed.

## 3. Critical validity threats

### 3.1 Severe missing-data asymmetry (PRIMARY LIMITATION)
- Agent: 25/30 valid; ImpactPlan: 6/30 valid.
- 24/30 ImpactPlan cells failed operationally: 20× `finish_reason=length` truncation at the frozen 4096-token cap, 3× fail-closed unknown-path hallucination, 1× provider 429, 1× harness defect. All are recorded failures per the frozen failure policy; no cell was rerun.
- The ImpactPlan MICRO headline therefore rests on 6 survivors and is **not** equal-evidence comparable to Agent's 25-run aggregate. Any arm comparison is provisional and must be re-audited (GPT-5.6 SOL) before any scientific claim.

### 3.2 Provider instability
- DeepInfra upstream rate-limit (`engine_overloaded`) produced 5 infrastructure-failed cells (4 agent + 1 impact) despite the frozen 1-transient-retry policy and operational pacing.
- A brief provider outage at study start was waited out before launching; pacing (15 s inter-cell) is an operational scheduling measure, NOT a scientific-input change.

### 3.3 Cap sensitivity
- ImpactPlan's 4096-completion cap is frozen; the full 144-decision JSON frequently does not fit, so most ImpactPlan cells are cap-truncated failures. The probe (scenario 008) succeeded once at 1817 completion tokens, so the cap is sufficient for compact plans but not for the verbose plans the model emits on the other scenarios.

### 3.4 Cost-accounting gap
- ImpactPlan 007-r1 consumed one model call whose token usage/cost could not be recorded (harness `ValueError` before record construction). True total spend is therefore slightly above the recorded $0.264148 (by ≈ $0.003). Ceiling is $0.50; COST_LOCK stays PASS with wide margin.

### 3.5 External validity
- Single repository (django CMS 5.0.0 pin `0f633fc9…`), single model, single provider session, 6 scenarios × 144-path universe.
- No claim of general large-repository superiority; no end-to-end selective-regeneration claim.

## 4. What is NOT measured
- Regeneration / patching / repair / migration / functional execution correctness. Selection only.
- Cost-probe runs (costprobe-01, costprobe-02) are NON-STUDY diagnostic evidence and are excluded from the 60 scientific results.

## 5. Interpretation rules honored
- Correctness before efficiency; efficiency reported only after correctness.
- No reruns for bad precision/recall/F1/surprising write sets/empty sets/arm losses.
- Raw evidence wins over documentation on any conflict.
