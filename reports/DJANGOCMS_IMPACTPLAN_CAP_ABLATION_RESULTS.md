# ImpactPlan Completion-Cap Ablation — Results (POST-HOC / EXPLORATORY)

**Status:** POST-HOC EXPLORATORY ABLATION — **NOT PART OF THE PREREGISTERED PRIMARY 60-RUN STUDY** (`scientific-stagec-djangocms-01`). **NOT EXECUTED to completion — STOPPED at the 8192 cost/validity probe.**

**Study ID:** `scientific-stagec-djangocms-impactplan-cap-ablation-01`
**Date (UTC):** 2026-09-08
**Scientific model / provider:** `qwen/qwen3-coder` @ DeepInfra pinned through OpenRouter (`deepinfra/turbo`), fallback OFF, temperature 0, selection-only.

---

## 1. Result headline

```
CAP_8192_PROBE_TRUNCATION
```

The single non-study 8192 cost/validity probe on scenario
`djangocms-external-validity-004` **truncated at exactly 8192 completion tokens**
(`finish_reason=length`, `completion_tokens=8192`). The response was NOT
parseable as schema-valid JSON (unterminated string at char 34816), so the probe
is **INVALID** and the planned 30-run cap-8192 ablation was **NOT launched**.

Per the frozen protocol: **Do NOT jump to 16K automatically.** STOP for
GPT-5.6 Sol review. The 30 ablation cells were never run.

## 2. Probe evidence (non-study, NOT reused as an ablation result)

| Field | Value |
| --- | --- |
| Probe ID | `scientific-stagec-djangocms-impactplan-8192-costprobe-01` |
| Scenario | `djangocms-external-validity-004` (primary ImpactPlan had 0/5 valid here) |
| Arm | `impact_plan` only |
| Completion cap | 8192 (ablation-only configuration; primary remains 4096) |
| Terminal status | failed |
| finish_reason | length |
| truncation_status | true |
| completion_tokens | 8192 (exactly at the 8192 cap) |
| prompt_tokens | 2768 |
| total_tokens | 10960 |
| model_calls | 1 |
| latency_seconds | 202.843 |
| api_cost (USD) | 0.009022 |
| schema/path valid | false (unterminated JSON at char 34816) |
| invalid_selected_paths | [] (none emitted before truncation) |
| predicted_write_set | [] |
| raw_response_sha256 | `c0a4ec2ce0cbd8b8b86ada924d363d5b8ce7b1080040177b15badb2b94bb2863` |
| visible_scenario_sha256 | `0b25d27452ceff3fae08eecd42b15da8d6788c4af162455f71c2db5cf3450430` |
| runtime_universe_hash | `43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410` (144 paths) |

Full probe evidence: `reports/scientific-stagec-djangocms-impactplan-cap-ablation-01/costprobe_8192.json`.

## 3. Cost lock (ablation ceiling $0.25, conservative 25% margin)

| Item | Value |
| --- | --- |
| Probe API cost | $0.009022 |
| Projected 30 runs (probe x 30) | $0.270660 |
| Conservative projected 30-run cost (x 1.25) | **$0.338325** |
| Ablation ceiling | $0.25 |
| COST_LOCK | **FAIL** (projected > ceiling) |

Even if the probe had been valid, the conservative projected 30-run cost
exceeds the hard ablation ceiling of $0.25, so the ablation would have been
stopped by `COST_BUDGET_STOP` regardless.

Full cost evidence: `reports/scientific-stagec-djangocms-impactplan-cap-ablation-01/cost_lock.json`.

## 4. Pre-benchmark validation + gates (PASS, zero scientific calls)

- Ablation pre-run validation PASS (universe == frozen 144, gold evaluation-only,
  six final scenarios, wiring tag ancestor, primary evidence immutable 71/71,
  ablation differs from primary only in ImpactPlan cap 4096 -> 8192, no Agent cells).
- EXACT six deterministic gates + independent audit PASS (Gate 1 Dataset,
  Gate 2 Prompt, Gate 3 Pipeline Smoke, Gate 4 Dry Run, Gate 5 Integration,
  Gate 6 Metric Verification) — zero scientific calls.
- Frozen 30-cell ablation manifest persisted BEFORE any ablation-study call
  (`manifest_30.json`: 6 scenarios x 5 reps x impact_plan only, cap 8192).

## 5. Why the ablation did not run

The probe is the mandatory cost/validity gate before the 30 ablation runs. The
frozen protocol states: *"If the probe itself truncates at 8192: STOP. Do NOT
jump to 16K automatically. Report `CAP_8192_PROBE_TRUNCATION`."*

The probe truncated at 8192, so the ablation (30 cells) was **not executed**.
This means the ablation's primary research question — *whether 8192 materially
reduces truncation and raises operational completion vs the frozen 4096* —
**remains unanswered**: there is no 30-run cap-8192 completion evidence, and
therefore no claim that 8192 improves accuracy or completion.

## 6. Interpretation / recommendation (per frozen interpretation rule)

Because the 8192 single-response cap **still truncates** (it hit exactly 8192
tokens), do NOT immediately run 16K. STOP and recommend one of:

- **A.** a separately authorized 16K diagnostic, or
- **B.** a compact / sparse ImpactPlan-v2 representation.

The choice between A and B must NOT be made without GPT-5.6 Sol review. A
compact future design may classify omitted entries deterministically as PRESERVE
while emitting full evidence only for R/V/H, but that is a NEW treatment and must
NOT be substituted into this ablation.

The primary 4096 result remains **unchanged and immaterially confounded** — no
claim is made that it was caused by output capacity alone; the 8192 probe shows
the full 144-path schema-valid serialization still cannot be emitted within a
single 8192-token response.

## 7. Closure

- Same six closure gates + independent audit PASS; primary 60-run raw evidence
  hashes verified unchanged (71/71).
- Code change: `OpenRouterImpactPlanner` gained an optional
  `max_completion_tokens` parameter (default 4096 — primary reproducibility
  unchanged); the ablation-only runner
  `scripts/stagec_djangocms_ablation_execute.py` implements the cap-8192
  ablation-only configuration.
- Committed + pushed to `research/djangocms-external-validity-prep-01`.
- No main merge. No `v0.11.0-benchmark-complete`.
- **No ablation-completed tag** (`stagec-djangocms-impactplan-cap8192-ablation-01`
  NOT created — the ablation did not complete).
- STOP FOR GPT-5.6 SOL AUDIT.
