# M1 Statistical Analysis

**Milestone:** M1 defensive closure (M1A + M1B evidence)
**Date:** 2026-09-13
**Evidence:** audited M1B controlled 16K encoding ablation (60 cells) + M1A 4096 probes
**Computation:** zero scientific API calls; `scripts/m1_defensive_closure_stats.py` -> `reports/m1_defensive_closure_stats.json`

---

## 1. Design and unit structure (frozen)

- **6 scenarios = the independent task units (n = 6).**
- **5 repetitions = repeated observations NESTED within scenario** (r1..r5 per
  scenario per arm).
- **This analysis does NOT claim n = 30 independent tasks.**
- **No significance test in this document pretends the 30 repetitions per arm
  are independent.** All cross-scenario statements use the 6 scenario-level
  summaries as the effective sample.
- Paired differences are **Sparse-v2 minus Full-v2** computed within the SAME
  repetition index of the SAME scenario (r1 vs r1, ..., r5 vs r5).
- Empirically the five repetitions within a scenario/arm are **not**
  byte-identical even at temperature 0 (decoded policies and token counts
  differ across r1..r5 — provider-side nondeterminism), so nested
  within-scenario variance is real and is used descriptively.

The arms are **Full-v2** (explicit decision for all 144 candidates, including
explicit PRESERVE rows) and **Sparse-v2** (non-PRESERVE rows only; omitted ids
deterministically reconstruct as PRESERVE). Both arms share the same schema,
prompt template (only the `[[SERIALIZATION_POLICY]]` block differs), model
(`qwen/qwen3-coder` @ `deepinfra/turbo`, fp4), temperature 0, cap 16384, and
scorer.

## 2. Scenario-level paired summaries (mean paired difference, Sparse - Full)

| Scenario | ΔF1 | ΔRecall | ΔPrecision | ΔFNR | ΔFN (abs) | Δcompletion | Δcost USD | Δlatency s | Δrecords |
|---|---|---|---|---|---|---|---|---|---|
| 002 | -0.0667 | 0.0000 | -0.1000 | 0.0000 | 0.0 | -7,379 | -0.007374 | -33.9 | -142.8 |
| 004 | +0.1844 | +0.1500 | +0.1933 | -0.1500 | -0.6 | -7,433 | -0.007429 | -42.0 | -139.0 |
| 005 | +0.3532 | +0.2000 | +0.4222 | -0.2000 | -1.0 | -7,563 | -0.007559 | -33.0 | -138.4 |
| 006 | **-0.1760** | **-0.4667** | -0.0912 | **+0.4667** | +1.4 | -7,638 | -0.007634 | -14.9 | -139.8 |
| 007 | +0.3342 | +0.2000 | +0.4095 | -0.2000 | -1.4 | -7,593 | -0.007589 | -21.5 | -137.4 |
| 008 | +0.2188 | +0.2500 | +0.1734 | -0.2500 | -1.0 | -7,836 | -0.007832 | -64.7 | -137.2 |

Per-scenario per-repetition distributions (min / median / max / sd over the 5
nested repeats) are in `reports/m1_defensive_closure_stats.json`
(`per_scenario[*].arm_distributions` and `.paired_summary`).

## 3. Mean and median paired effects across scenarios (n = 6)

Using each scenario's mean paired difference as one observation (n = 6):

| Metric | mean of scenario means | median of scenario means | sd | Cohen's d (across scenarios) | sign consistency |
|---|---|---|---|---|---|
| ΔF1 | +0.1413 | +0.2016 | 0.1975 | +0.72 | 4 positive / 2 negative (mixed) |
| ΔRecall | +0.0556 | +0.1750 | 0.2464 | +0.23 | 4 pos / 1 neg / 1 zero (mixed) |
| ΔPrecision | +0.1679 | +0.1834 | 0.2092 | +0.80 | 4 pos / 2 neg (mixed) |
| ΔFNR | -0.0556 | -0.1750 | 0.2464 | -0.23 | 1 pos / 4 neg / 1 zero (mixed) |
| Δcompletion tokens | -7,573.9 | -7,578.1 | 147.7 | -51.3 | 6 / 6 negative (uniform) |
| Δrecords | -139.1 | -138.7 | 1.9 | -74.0 | 6 / 6 negative (uniform) |
| Δapi cost USD | -0.007569 | -0.007574 | 0.00015 | -51.1 | 6 / 6 negative (uniform) |
| Δlatency s | -35.0 | -33.4 | 15.9 | -2.2 | 6 / 6 negative (uniform) |

**Reading.** The **cost-side** paired effects are directionally uniform across
all six scenarios and large (completion tokens, serialized records, API cost,
latency all decrease in every scenario). The **semantic-side** paired effects
are mixed in direction at the scenario level: F1 improves in 4 of 6 scenarios
and degrades in 2 (002, 006). The aggregate +0.141 ΔF1 is therefore NOT a
uniform semantic effect — it is a central-tendency summary over a mixed sign
pattern driven by 004/005/007/008 and opposed by 002/006.

## 4. Effect sizes

- **Cohen's d (across scenarios, n = 6), for the mean paired difference:**
  ΔF1 d = +0.72, ΔPrecision d = +0.80, ΔRecall d = +0.23 — moderate to large
  central-tendency effects but with **mixed signs** (d is only meaningful as a
  descriptive magnitude given the sign inconsistency; see Section 3).
- **Cost side:** completion tokens d = -51.3, cost d = -51.1, records d = -74.0
  — enormous and uniform; these are descriptive magnitudes of a near-mechanical
  reduction (144 explicit rows vs ~4.9 omitted-rows).
- **Within-scenario effect sizes** (d over the 5 paired diffs of that
  scenario) are in the stats JSON. S006 shows within-scenario d(F1) = -4.35,
  d(recall) = -2.86 — the strongest negative encoding effect in the study.
- **Caution:** with n = 6 units, Cohen's d is noisy; it is reported as a
  descriptive standardized difference, not an inferential claim.

## 5. Per-scenario distributions (valid-output semantic + operational)

The per-scenario per-arm distributions over the 5 nested repetitions
(min/median/max/sd) are persisted in the stats JSON. The pooled-micro
scenario-level semantic numbers (used by the scenario report) are:

| Scenario | Arm | P | R | F1 | FNR | full-recall runs |
|---|---|---|---|---|---|---|
| 002 | Full / Sparse | 1.000 / 0.833 | 1.000 / 1.000 | 1.000 / 0.909 | 0.000 / 0.000 | 5 / 5 |
| 004 | Full / Sparse | 0.607 / 0.800 | 0.850 / 1.000 | 0.708 / 0.889 | 0.150 / 0.000 | 0 / 5 |
| 005 | Full / Sparse | 0.465 / 0.893 | 0.800 / 1.000 | 0.588 / 0.943 | 0.200 / 0.000 | 0 / 5 |
| 006 | Full / Sparse | 0.308 / 0.238 | 0.800 / 0.333 | 0.444 / 0.278 | 0.200 / 0.667 | 0 / 0 |
| 007 | Full / Sparse | 0.471 / 0.939 | 0.686 / 0.886 | 0.558 / 0.912 | 0.314 / 0.114 | 0 / 1 |
| 008 | Full / Sparse | 0.375 / 0.588 | 0.750 / 1.000 | 0.500 / 0.741 | 0.250 / 0.000 | 0 / 5 |

## 6. Bootstrap confidence intervals — over SCENARIOS, not runs

Bootstrap resamples the **6 scenario-level mean paired differences with
replacement** (10,000 iterations). The repetitions are never resampled as
independent units. The CI therefore reflects between-scenario uncertainty only.

| Metric | bootstrap mean | 95% CI (scenario-level) |
|---|---|---|
| ΔF1 | +0.1397 | [-0.0220, +0.2932] |
| ΔRecall | +0.0545 | [-0.1667, +0.2083] |
| ΔPrecision | +0.1691 | [-0.0030, +0.3383] |
| ΔFNR | -0.0549 | [-0.2083, +0.1667] |
| Δcompletion tokens | -7,574.7 | [-7,695.4, -7,462.2] |
| Δapi cost USD | -0.007569 | [-0.007690, -0.007457] |

**Explicit n = 6 limitation.** The F1/Recall/Precision CIs all include zero or
come close to it (ΔF1 lower bound -0.022; ΔRecall lower bound -0.167). This is
the honest picture of a 6-unit study with a mixed sign pattern: the semantic
direction is NOT statistically established at the scenario level. The
completion-token and cost CIs are far from zero (uniform sign across all 6
scenarios), which is why the **cost effect** is the defensible claim and the
**semantic direction** is not.

## 7. Sensitivity analysis: operational metrics vs valid-output semantic metrics (survivor bias explicit)

The M1 evidence contains an explicit survivor-bias funnel at the 4096-cap
boundary:

- **M1A @ 4096:** Full-v2 probe = operationally INVALID (terminated at the
  completion cap, JSON unterminated after candidate id 76; 0 valid semantic
  observations). Sparse-v2 probe = operationally VALID (419 completion tokens,
  decodes the full 144-candidate policy; 1 semantic observation).
- **M1B @ 16384:** BOTH arms survive (30/30 valid each, 0 truncations,
  30 semantic observations per arm).

**Sensitivity statement.** If one compared "valid-output semantic metrics" at
the 4096 boundary, Full-v2 would contribute zero observations and every
comparison would be survivor-biased toward Sparse-v2. M1B removes the cap as a
censoring mechanism (both arms produce valid outputs), so the M1B semantic
comparison is NOT cap-censored. The operational metric (validity rate) at 4096
(0.0 vs 1.0) and the valid-output semantic metric at 16384 coexist in this
closure and must not be conflated:

- Operational claim (M1A): under a 4096 cap, Sparse-v2 completes and Full-v2
  truncates — a capability/feasibility fact.
- Semantic claim (M1B): under a non-binding 16384 cap, Sparse-v2's valid
  outputs are not uniformly semantically better (mixed signs; S006 worse).

Within M1B there is NO additional survivor bias because every run is valid; the
fail-closed scoring rule (invalid runs would count as recall 0 / FNR 1, never
be dropped) is the standing control for any future study (including M3).

## 8. What can and cannot be concluded

**Supported (descriptive, all 6 scenarios, uniform direction):**
- Under a fixed common schema/prompt/model/provider/cap, the Sparse-v2
  representation is far cheaper to produce than Full-v2 (mean completion
  tokens 809 vs 8,383; ~4.9 vs 144 serialized records; recorded API cost
  $0.048 vs $0.275; latency 609 s vs 1,659 s). Bootstrap CIs over scenarios
  are far from zero.

**NOT established (mixed signs, 6-unit sample):**
- That Sparse-v2 universally improves semantic selection (F1/Recall/Precision
  improve in 4/6 scenarios, degrade in 2). The scenario-level CIs straddle
  zero. S006 is a strong, reproducible counterexample (see the scenario
  report).

**Convention preserved throughout:** 6 independent task units; 5 nested
repetitions; no n=30 claim; no independence-faking significance test.

---

Companion documents: `reports/M1_THREATS_TO_VALIDITY_MATRIX.md` (risk audit),
`reports/M1_SCENARIO_LEVEL_ANALYSIS.md` (per-scenario tables + S006),
`reports/m1_defensive_closure_stats.json` (full persisted numbers).