# STOP REPORT — djangoCMS ImpactPlan FULL-PLAN 16K OUTPUT-SCALABILITY DIAGNOSTIC

**DIAGNOSTIC_ID:** `scientific-stagec-djangocms-impactplan-16k-diagnostic-01`
**Date (UTC):** 2026-09-08
**Type:** POST-HOC / EXPLORATORY / ONE-SCENARIO DIAGNOSTIC — **exactly ONE scientific run.**
**Closure type:** REPORTING / EVIDENCE / DOCUMENTATION closure. ONE scientific diagnostic call; ZERO study cells; primary and 8192 evidence unchanged.

---

## 1. Execution Identity

- Implementation/OpenCode model: `openrouter/deepseek/deepseek-v4-flash-0731` (DEFAULT variant).
- Scientific model: `qwen/qwen3-coder`
- Scientific provider: DeepInfra pinned through OpenRouter (`deepinfra/turbo`), fallback OFF, temperature 0, selection-only.
- Branch: `research/djangocms-external-validity-prep-01`
- HEAD (full): `79165e450d634e63f728bbece7c63d28cec64169` at closure start
- Remote HEAD: `79165e450d634e63f728bbece7c63d28cec64169` (parity YES)
- Tree state: CLEAN at closure start

## 2. Why I Am Stopping

**STOP FOR GPT-5.6 SOL REVIEW — `FULL_PLAN_16K_DIAGNOSTIC=TERMINATES` (CASE A).**

The single 16K diagnostic on `djangocms-external-validity-004` TERMINATED
successfully before the 16384 cap (`finish_reason=stop`, `completion_tokens=
10650`), parsed as schema-valid JSON, with valid candidate paths only. Per the
decision rule, this is **CASE A — TERMINATES**: do NOT launch a 16K 30-run
ablation, and interpret the full explicit 144-node representation's
serialization requirement as a scalability/efficiency concern. Recommend next
step: Compact/Sparse ImpactPlan-v2. STOP FOR GPT-5.6 SOL.

## 3. Primary study immutability

- Primary 60-run evidence (`scientific-stagec-djangocms-01`) recomputed and
  verified identical: **71/71 hashes unchanged** (raw_evidence_hashes.json).
- Previous 8192 probe evidence (`costprobe_8192.json`) verified unchanged vs
  HEAD (`git diff --quiet` PASS).

## 4. Pre-benchmark validation + gates (PASS, zero scientific calls)

- Diagnostic pre-run validation PASS (universe == frozen 144, canonical hash
  `43f4279b...`; gold evaluation-only; scenario 004 model-facing from
  `visible_drafts/`; old historical scenario never loaded; ONLY treatment
  difference = ImpactPlan cap 8192 -> 16384; model/provider/temp/fallback
  unchanged; planner prompt+schema identical to HEAD; primary immutable;
  8192 evidence unchanged).
- EXACT six deterministic gates + independent audit PASS
  (`reports/scientific-stagec-djangocms-impactplan-16k-diagnostic-01/diagnostic_gates.json`).

## 5. Diagnostic result (ONE scientific call)

Full evidence: `reports/scientific-stagec-djangocms-impactplan-16k-diagnostic-01/diagnostic.json`,
`raw_response.txt`, `raw_response.sha256`, `response_size_analysis.json`.

- Scenario: `djangocms-external-validity-004`, arm impact_plan, cap 16384
- **completion_tokens: 10650 (TERMINATED BEFORE 16384)**
- finish_reason: `stop`; terminal_status: `succeeded`; schema-valid: true
- prompt_tokens 2768 / completion 10650 / total 13418; model_calls 1;
  latency 179.172 s; api_cost $0.01148
- invalid_paths: [] ; predicted_write_set: 9 paths; no truncation
- Selection metrics (normal scoring valid): TP 4 / FP 5 / FN 0,
  precision 0.444444, recall 1.0, F1 0.615385, FNR 0.0, full_recall true
- Full raw response persisted: 42,773 bytes / 42,773 chars / 1,314 lines,
  SHA-256 `5f66423ef5c5dd0e1d89848ec4e5621e7381672a6735d0f36eb1f7428bda3e0e`
- emitted_entry_count (deterministic, valid-JSON path): **143** — the model
  emitted 143 of the 144 path decision objects; `cms/toolbar/utils.py` was
  omitted from the response and defaults to PRESERVE via the unchanged planner
  fallback, so all 144 candidate paths remain classified exactly once.

## 6. Decision case

**CASE A — TERMINATES.** `FULL_PLAN_16K_DIAGNOSTIC=TERMINATES`.

The current full explicit 144-path ImpactPlan representation CAN terminate
within a single 16384-completion-token response on this previously
truncation-prone scenario (finish_reason=stop at 10650 tokens, schema-valid,
no invalid paths). Best observed empirical lower bound for THIS scenario's
full-plan serialization: **10,650 completion tokens**.

## 7. Interpretation (frozen rule)

- No claim that 16K fixes ImpactPlan generally (one scenario only).
- No claim that ImpactPlan is more accurate.
- The primary 4096 study is NOT invalidated and is unchanged (71/71).
- The 8192 probe evidence is NOT modified.
- Line count alone does NOT prove percentage completion — emitted_entry_count
  was derived deterministically from the raw response (valid-JSON parse).
- This diagnostic is NOT confirmatory evidence.
- Allowed interpretation: the full explicit plan representation CAN serialize
  a 144-path plan within a larger single-response budget on one previously
  truncation-prone scenario; its serialization requirement remains a
  scalability/efficiency concern → recommend Compact/Sparse ImpactPlan-v2 next.

## 8. Deliverables

- Evidence dir: `reports/scientific-stagec-djangocms-impactplan-16k-diagnostic-01/`
  (prevalidation.json, diagnostic_gates.json, diagnostic.json,
  raw_response.txt, raw_response.sha256, response_size_analysis.json,
  closure_gates.json, STOP_REPORT.md)
- Code: `scripts/stagec_djangocms_16k_diagnostic_execute.py` (new, diagnostic-only;
  cap 16384; full raw-response durability; deterministic response-size analysis)
- Report: `reports/DJANGOCMS_IMPACTPLAN_CAP_ABLATION_RESULTS.md`
  (new section "FULL-PLAN OUTPUT-SCALABILITY DIAGNOSTIC")

## 9. Git state

- Committed + pushed to `research/djangocms-external-validity-prep-01`.
- No main merge. No `v0.11.0-benchmark-complete`.
- **No 16K study tag** (one diagnostic only; not a multi-run study).

**STOP FOR GPT-5.6 SOL REVIEW. DO NOT RUN 32K. DO NOT RUN A MULTI-RUN 16K ABLATION. DO NOT START COMPACT V2 WITHOUT REVIEW.**