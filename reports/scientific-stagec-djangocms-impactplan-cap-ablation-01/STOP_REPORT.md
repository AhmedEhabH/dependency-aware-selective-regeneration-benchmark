# STOP REPORT — djangoCMS ImpactPlan 8192-cap ABLATION (POST-HOC / EXPLORATORY)

**STUDY_ID:** `scientific-stagec-djangocms-impactplan-cap-ablation-01`
**Date (UTC):** 2026-09-08
**Type:** POST-HOC EXPLORATORY ABLATION — **STOPPED at the 8192 cost/validity probe** (NOT executed to completion).
**Closure type:** REPORTING / EVIDENCE / DOCUMENTATION closure. ONE scientific probe call; ZERO ablation-study cells.

---

## 1. Execution Identity

- Implementation/OpenCode model: `openrouter/deepseek/deepseek-v4-flash-0731` (DEFAULT variant).
- Scientific model: `qwen/qwen3-coder`
- Scientific provider: DeepInfra pinned through OpenRouter (`deepinfra/turbo`), fallback OFF, temperature 0, selection-only.
- Branch: `research/djangocms-external-validity-prep-01`
- HEAD (full): `bc05722d89fbf35b813b1dcf4e72618ef30e2b8e` at closure start (post durability-fix)
- Remote HEAD: `bc05722d89fbf35b813b1dcf4e72618ef30e2b8e` (parity YES)
- Tree state: CLEAN at closure start
- Primary study tag (created this task): `stagec-djangocms-study-01-audited` @ `2c217d7a3f6311567540a2cc48b096338065ffcf` (annotated; primary tags NOT moved)

## 2. Why I Am Stopping

**STOP FOR GPT-5.6 SOL INDEPENDENT AUDIT — `CAP_8192_PROBE_TRUNCATION`.**

The mandatory non-study 8192 cost/validity probe truncated at exactly 8192
completion tokens (`finish_reason=length`, unterminated JSON). Per the frozen
ablation protocol, the 30-run ablation must NOT proceed, and 16K must NOT be
jumped to automatically. The 30 ablation cells were never run.

## 3. Primary study immutability

- Primary 60-run evidence (`scientific-stagec-djangocms-01`) recomputed and
  verified identical: **71/71 hashes unchanged** (raw_evidence_hashes.json).

## 4. Pre-benchmark validation + gates (PASS, zero scientific calls)

- Ablation pre-run validation PASS (universe == frozen 144, canonical hash
  `43f4279b...`; gold evaluation-only; six final scenarios; wiring tag
  `stagec-djangocms-study-wiring-verified-01` ancestor; ablation vs primary
  differs ONLY in ImpactPlan cap 4096 -> 8192; no Agent cells; primary immutable).
- EXACT six deterministic gates + independent audit PASS
  (`reports/scientific-stagec-djangocms-impactplan-cap-ablation-01/ablation_gates.json`).
- Frozen 30-cell manifest persisted BEFORE any ablation-study call
  (`manifest_30.json`: 6 scenarios x 5 reps x impact_plan only, cap 8192).

## 5. Cost/validity probe result (one non-study call)

See `reports/DJANGOCMS_IMPACTPLAN_CAP_ABLATION_RESULTS.md` and
`reports/scientific-stagec-djangocms-impactplan-cap-ablation-01/costprobe_8192.json`.

- Probe ID: `scientific-stagec-djangocms-impactplan-8192-costprobe-01`
- Scenario: `djangocms-external-validity-004`, arm impact_plan, cap 8192
- Result: FAILED (truncated at exactly 8192 completion tokens; not parseable JSON)
- tokens: 2768 prompt / 8192 completion / 10960 total; calls 1; latency 202.843 s; cost $0.009022
- Conservative projected 30-run cost (x 1.25) = **$0.338325 > $0.25 ceiling** (COST_LOCK=FAIL)

## 6. Ablation execution status

- Planned: 30 cells (6 scenarios x 5 reps x impact_plan only, cap 8192).
- **Executed: 0 / 30 ablation-study cells.** The probe gate stopped execution.
- No run 1..30. No replacement cells. The probe is NON-STUDY and not reused.

## 7. Decision metrics

Not computed — no 30-run ablation evidence exists. No valid/failed/truncation
counts, correctness table, or efficiency table for the ablation (only the single
probe). The primary 4096 ImpactPlan numbers (valid 6/30 = 20.0%, truncation
19/30 = 63.33%) are UNCHANGED and are NOT mixed with any ablation result.

## 8. Interpretation

The 8192 single-response cap STILL truncates on the full 144-path schema-valid
serialization, so this ablation does NOT support a claim that raising the cap
materially removes truncation. Per the frozen interpretation rule, STOP and
recommend (A) a separately authorized 16K diagnostic, or (B) a compact/sparse
ImpactPlan-v2 representation — not chosen without GPT-5.6 Sol review. No claim
of improved accuracy/completion at 8192 is made.

## 9. Deliverables

- Evidence dir: `reports/scientific-stagec-djangocms-impactplan-cap-ablation-01/`
  (prevalidation.json, ablation_gates.json, manifest_30.json, costprobe_8192.json,
  cost_lock.json, closure_gates.json, STOP_REPORT.md)
- Results report: `reports/DJANGOCMS_IMPACTPLAN_CAP_ABLATION_RESULTS.md`
- Code: `scripts/stagec_djangocms_ablation_execute.py` (new, ablation-only);
  `src/benchmark/selection/impact_planner.py` (configurable cap, default 4096 unchanged)

## 10. Git state

- Committed + pushed to `research/djangocms-external-validity-prep-01`.
- No main merge. No `v0.11.0-benchmark-complete`.
- Primary tag `stagec-djangocms-study-01-audited` created (not moved).
- Ablation-completed tag `stagec-djangocms-impactplan-cap8192-ablation-01` **NOT** created (ablation did not complete).

**STOP FOR GPT-5.6 SOL AUDIT.**
