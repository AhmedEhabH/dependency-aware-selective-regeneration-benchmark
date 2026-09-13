# M1 Threats-to-Validity Matrix

**Milestone:** M1 defensive closure (M1A + M1B evidence)
**Date:** 2026-09-13
**Classification:** defensive scientific-claims documentation; zero scientific API calls
**Status:** frozen input evidence unchanged; this document is a claims-risk audit only.

This matrix enumerates the threats to the validity of every M1A/M1B-derived
claim, the existing control, the remaining risk, the concrete evidence, the
claim affected, and the mitigation / next experiment for each threat.

The M1 evidence base is:

- **M1A** — Controlled 4096-cap feasibility boundary
  (`research/controlled-encoding-ablation-01/`, probes only; no 60-cell study).
- **M1B** — Controlled 16K cap-relaxed encoding ablation
  (`research/controlled-encoding-ablation-16k-01/`, 60/60 cells, Full-v2 vs
  Sparse-v2, 6 scenarios x 2 arms x 5 repetitions).

Statistical convention used throughout (see
[`reports/M1_STATISTICAL_ANALYSIS.md`](M1_STATISTICAL_ANALYSIS.md)): **6
scenarios are the independent task units (n = 6); 5 repetitions are nested
repeated observations within scenario.** No claim, table, or test in this
closure treats the 30 repetitions per arm as 30 independent tasks.

---

## Threat 1 — Construct validity

- **Threat.** The selection metric (micro-averaged precision / recall / F1 over
  the 144-candidate write set vs hidden gold) may not measure the construct
  that matters downstream ("did the model choose the right files to
  regenerate"), or the write-set-only view may miss that VALIDATE /
  HUMAN_REVIEW decisions carry scope information.
- **Why it matters.** If the metric does not track the construct, every
  downstream claim (encoding cost effect, graph benefit) is about a proxy.
- **Existing control.** Hidden gold is evaluation-only and is a source-graph
  adjudicated write set (adjudication file
  `benchmark_data/external_validity/djangocms_hidden_gold_adjudication.json`,
  schema/2, decision = INCLUDE only when the visible requirement necessarily
  requires writing the file). Metrics P/R/F1/FNR are computed against that gold
  after inference. Both arms decode into the SAME canonical 144-candidate
  policy, so the metric compares the same construct across arms.
- **Remaining risk.** The gold is an adjudicated judgment (8-record audit);
  "necessarily requires writing" is a human-settable criterion. VALIDATE /
  HUMAN_REVIEW actions are not part of the write-set construct, so scope
  signaling is unmeasured.
- **Evidence.** `research/controlled-encoding-ablation-16k-01/final_metrics.json`
  (pooled micro per scenario/arm); adjudication JSON; gate 6 metric
  verification (deterministic recomputation).
- **Claim affected.** All M1A/M1B semantic claims; M3's ΔFN/ΔRecall/ΔPrecision
  analyses.
- **Mitigation / next experiment.** Real historical changes with
  development/validation/held-out separation (RealCommitImpactDataset-v1);
  secondary metrics that treat VALIDATE/HUMAN_REVIEW zones as partial scope;
  multi-annotator gold with agreement reporting.

## Threat 2 — Internal validity

- **Threat.** Observed Full-v2 vs Sparse-v2 differences might be caused by
  something other than the serialization-policy block (schema, prompt text,
  candidate order, model, provider, cap, temperature, evidence, scoring).
- **Why it matters.** Internal validity is the precondition for ANY causal
  attribution to the encoding.
- **Existing control.** A single common JSON schema and a single common prompt
  template for BOTH arms; the ONLY intended difference is the
  `[[SERIALIZATION_POLICY]]` block. Prompt-control proof (`prompt_control.json`):
  after stripping the policy block, FULL and SPARSE prompts are byte-identical
  for all six scenarios (`PROMPT_CONTROLLED_DIFF == "PASS"`). Frozen identity
  hashes (common schema / template / policy / reason codes / candidate map /
  universe) are validated by prevalidation + gates. FROZEN_M1A_PARITY proves
  the only M1A->M1B study-level change is the completion cap 4096->16384.
- **Remaining risk.** The treatment necessarily changes OUTPUT length
  (144 rows vs ~5 rows); "policy block" and "output length / decoding
  semantics" are entangled by design. A model that behaves differently when
  asked to be terse is not distinguishable from an encoding effect at the
  prompt level alone.
- **Evidence.** `prompt_control.json`, `FROZEN_M1A_PARITY.json`,
  `prevalidation.json`, `prestudy_gates.json`.
- **Claim affected.** "Sparse encoding reduces serialization cost" (the
  encoding-attribution half of M1B).
- **Mitigation / next experiment.** M2 serialization-density study (same
  content, different density) to separate policy content from density; M3
  graph treatment keeps everything else fixed so graph attribution has the
  same internal-validity discipline.

## Threat 3 — External validity

- **Threat.** Results on six curated djangoCMS scenarios may not generalize to
  other repositories, change types, or real historical changes.
- **Why it matters.** The thesis proposes a general mechanism
  (sparse representation), so generalizability is the point.
- **Existing control.** The six scenarios span the external-validity audit
  (002 loc, 004 mod, 005 perm/admin, 006 mod/cross-entity, 007 cross-cutting,
  008 cache/signal/toolbar); scenarios are drawn from a pinned upstream
  repository with a real source-derived candidate universe; claims are labeled
  POST-HOC EXPLORATORY DEVELOPMENT-SET, never confirmatory. Two cross-model
  replications (Qwen3-32B, Qwen3-Coder-30B-A3B) closed for model generality.
- **Remaining risk.** One repository (djangoCMS 5.0.0) only. Repository
  topology, import density, and scenario difficulty all interact with encoding
  cost. No held-out real-change evaluation exists yet.
- **Evidence.** Scenario taxonomy, visible drafts
  (`benchmark_data/external_validity/visible_drafts/`), universe artifact,
  cross-model replication reports in `reports/scientific-stagec-*`.
- **Claim affected.** Any generalization beyond djangoCMS / beyond the six
  scenarios.
- **Mitigation / next experiment.** RealCommitImpactDataset-v1 (30-40
  high-quality historical changes) with strict
  development/validation/held-out separation; cross-repository replication
  (Todo, Saleor are already wired for the closed benchmark infrastructure).

## Threat 4 — Conclusion validity

- **Threat.** Statistical conclusions drawn from the data may be wrong (e.g.,
  treating 30 repetitions as independent, over-interpreting a small n, or
  using significance tests the design cannot support).
- **Why it matters.** A wrong inference is a direct scientific error.
- **Existing control.** The analysis explicitly treats 6 scenarios as units and
  5 repetitions as nested observations; it does NOT claim n=30; bootstrap (when
  used) resamples scenarios (n=6) and states the limitation; no significance
  test pretends repetitions are independent. M1B's label is descriptive
  ("CONTROLLED ENCODING COST EFFECT: SUPPORTED (descriptive)"), not causal.
- **Remaining risk.** n=6 is small; bootstrap CIs over 6 units are wide and
  sensitive to the resampling unit; sign consistency is mixed for semantic
  metrics (see the statistics report). No inferential claim is made stronger
  than the design supports.
- **Evidence.** `reports/M1_STATISTICAL_ANALYSIS.md`,
  `reports/m1_defensive_closure_stats.json` (computed zero-API).
- **Claim affected.** The strength (descriptive vs causal) of every M1B claim.
- **Mitigation / next experiment.** Increase the number of independent task
  units via RealCommitImpactDataset-v1; preregister inferential claims before
  running.

## Threat 5 — Curated-scenario bias

- **Threat.** The six scenarios are curated development/mechanism cases; the
  model may perform better (or worse) here than on representative changes, and
  the difficulty distribution is author-chosen.
- **Why it matters.** Curated scenarios can create or hide effects; recall is
  high partly because the scenarios were designed to be solvable.
- **Existing control.** Explicitly classified as CURATED DEVELOPMENT /
  MECHANISM SET, NOT held-out confirmation; reports state this everywhere;
  the M1B label is descriptive; scenario difficulty varies (F1 ranges from
  0.278 to 1.0 across scenario/arm cells).
- **Remaining risk.** No unbiased sample of real changes; the risk is
  irreducible in the current evidence.
- **Evidence.** Scenario classification language in
  `reports/CONTROLLED_ENCODING_16K_RESULT.md` and the roadmap.
- **Claim affected.** Absolute performance levels (R ~0.88, F1 ~0.79 for
  Sparse-v2), NOT the relative within-study encoding comparison.
- **Mitigation / next experiment.** RealCommitImpactDataset-v1 with strict
  development/validation/held-out separation.

## Threat 6 — Repetition dependence

- **Threat.** The 5 repetitions may be dependent draws (same prompts, same
  model, temperature 0) so within-scenario "n=5" may overstate independent
  information, OR provider-side nondeterminism may make them noisier than
  expected.
- **Why it matters.** Both directions corrupt variance estimates: treating
  dependent repeats as independent inflates n; ignoring real nondeterminism
  underestimates noise.
- **Existing control.** The analysis treats repetitions as NESTED observations,
  computes within-scenario distributions (min/median/max/sd over 5), and does
  not add them to the scenario-level n. Empirically the 5 reps per
  scenario/arm are NOT byte-identical (decoded policies and token counts
  differ), so within-scenario variance is real and is used descriptively.
- **Remaining risk.** With 5 repeats per scenario we cannot reliably separate
  repeat-level noise from scenario-level effects; the paired design mitigates
  but does not eliminate this.
- **Evidence.** `run_records.jsonl` (per-rep decoded_policy_sha256,
  completion_tokens differ across r1..r5); statistics JSON (within-scenario
  sd).
- **Claim affected.** Variance/CI statements; effect sizes.
- **Mitigation / next experiment.** More independent units (real changes),
  each with a small number of repetitions; explicit repeat-level variance
  decomposition once n_units grows.

## Threat 7 — Prompt sensitivity

- **Threat.** Results may be brittle to prompt wording (instructions, policy
  block phrasing, evidence formatting), so the encoding effect could be an
  artifact of a specific prompt.
- **Why it matters.** The paper's claims should survive reasonable prompt
  variants, not just one frozen template.
- **Existing control.** The prompt template is frozen and byte-controlled
  (prompt-control proof); the policy block is the only difference between arms;
  the same template is used across M1A/M1B and (by reuse) C0 of M3.
- **Remaining risk.** No prompt-sensitivity sweep has been run; a different
  template could plausibly shift absolute levels (and possibly the relative
  effect).
- **Evidence.** `prompt_control.json`; common template identity hash.
- **Claim affected.** Robustness of the encoding-cost direction.
- **Mitigation / next experiment.** A preregistered prompt-sensitivity
  micro-study (2-3 wording variants) as part of M2 or a follow-up; report
  stability of Δtokens and ΔF1 across variants.

## Threat 8 — Schema choice

- **Threat.** The specific common JSON schema (fields, required keys,
  `additionalProperties: false`, variable-length `decisions` array) may drive
  the effect: Full-v2 may be costly mainly because the schema forces verbose
  rows for all 144 candidates.
- **Why it matters.** If the schema itself causes the cost gap, the claim is
  about THIS schema, not about sparsity per se.
- **Existing control.** Both arms use the SAME schema; representation
  equivalence holds (decode(encode(pi)) == pi) on the frozen candidate map; the
  cost difference is reported as schema-relative, and the paper phrasing
  attributes the cost effect to the serialization policy under a fixed common
  schema.
- **Remaining risk.** A leaner full schema (e.g., no per-row evidence) could
  shrink the Full-v2 cost; the magnitude (but likely not the direction) of the
  cost effect is schema-dependent.
- **Evidence.** `COMMON_ABLATION_SCHEMA` (frozen hash), representation
  equivalence checks (14/14), `FROZEN_M1A_PARITY.json`.
- **Claim affected.** Magnitude of the completion-token/cost reduction
  (~-90%/-82%).
- **Mitigation / next experiment.** M2 serialization-density stress (schema
  with same content at different densities); report Δ across schemas.

## Threat 9 — Completion-cap choice

- **Threat.** The completion cap determines where truncation happens; the
  4096 boundary made Full-v2 invalid while 16384 made both arms valid, so the
  "cost effect" could be an artifact of cap placement.
- **Why it matters.** A cap-related censoring artifact would invalidate the
  cost comparison (survivor bias, Threat 13).
- **Existing control.** M1A is explicitly a 4096-cap feasibility boundary (NOT
  a semantic comparison); M1B relaxes the cap to 16384 for BOTH arms (the ONLY
  study-level change) and achieves 60/60 valid, 0 truncations, so the M1B
  semantic comparison is NOT censored by the cap. Parity artifact proves only
  the cap changed.
- **Remaining risk.** 16384 is still a finite cap; extremely verbose Full-v2
  outputs could theoretically truncate on other scenarios/repos. Completion
  cap choice also bounds M3 (the mission fixes one cap for all conditions).
- **Evidence.** M1A `capability_probes.json` (Full-v2 truncated at id 76 /
  4096 tokens; Sparse-v2 419 tokens), M1B `FROZEN_M1A_PARITY.json`,
  `final_metrics.json` (0 truncations).
- **Claim affected.** The validity/truncation claims and the M1B semantic
  comparison.
- **Mitigation / next experiment.** Keep the non-binding 16384 cap for all M3
  conditions (mission requirement); report cap headroom per arm; re-audit if
  any M3 condition hits the cap.

## Threat 10 — Model/provider dependence

- **Threat.** All M1 evidence is from one model
  (Qwen3-Coder-480B-A35B-Instruct) through one provider route
  (DeepInfra `deepinfra/turbo`, fp4), so the effect may not reproduce with
  another model or provider.
- **Why it matters.** The mechanism claim should be model-robust; the paper
  must not overclaim from one route.
- **Existing control.** Provider pinned with fallback OFF and `require_parameters`
  (no silent reroute); endpoint freeze; two cross-model replications
  (Qwen3-32B and Qwen3-Coder-30B-A3B) closed for model generality of the
  selection task; M1B itself is a 60-cell replication of M1A's design at a
  different cap.
- **Remaining risk.** The encoding cost effect has NOT been replicated across
  providers for the same model, nor across a second large model family at this
  exact design; provider-side nondeterminism at temperature 0 is observed
  (repetitions differ).
- **Evidence.** `endpoint_freeze.json` (both studies), `run_records.jsonl`
  (`exact_model`, `provider_tag`, `provider_reported`), cross-model reports.
- **Claim affected.** Generalization of the cost effect and of semantic
  levels.
- **Mitigation / next experiment.** A provider-route replication arm; keep
  M3 on the same frozen provider route as M1B (mission requirement) so C0 reuse
  is valid.

## Threat 11 — Closed-world candidate universe

- **Threat.** The candidate universe is a closed set of 144 files derived from
  the pinned source; the model can never select an out-of-universe file, so
  recall is bounded by universe construction and misses repository files that
  fall outside it (migrations, tests, non-.py, etc. are excluded by design).
- **Why it matters.** Selection "correctness" is only measurable within the
  closed universe; a real engineer could edit files outside it.
- **Existing control.** Universe is derived deterministically from the pinned
  source (production `cms/**` and `menus/**`, excluding tests/migrations);
  gold is required to be a subset of the universe (gate 1); the universe is
  frozen and hash-verified; the closed-world status is stated.
- **Remaining risk.** Universe boundary is a modeling choice; two different
  boundaries could change P/R/F1 levels and even relative arm ordering.
- **Evidence.** `djangocms_5_0_0_candidate_universe.json` (144 paths, frozen
  hash), gate 1 checks, source-graph eligibility.
- **Claim affected.** Absolute recall/F1; the universe-relative nature of every
  semantic number.
- **Mitigation / next experiment.** Sensitivity to universe construction on
  real historical changes; report universe-coverage statistics (what fraction
  of real change targets fall inside vs outside the universe).

## Threat 12 — Gold / expected-impact validity

- **Threat.** The hidden gold (expected write set) may be wrong: adjudication
  is judgment-based, gold paths may miss files the change truly requires, or
  include files that do not need editing.
- **Why it matters.** All TP/FP/FN/P/R/F1 numbers inherit gold errors.
- **Existing control.** Gold is source-adjudicated: INCLUDE only when the final
  visible requirement NECESSARILY requires writing the file (exact symbol
  location verified in the pinned source); historical expected_actions are
  LEADS ONLY; the adjudication file records per-file rationale; gold is
  evaluation-only and never enters prompts (leak scan + gate 1).
- **Remaining risk.** Adjudication remains human judgment; a second annotator
  has not been used; borderline files (e.g., files that "should" change but are
  not strictly necessary) are excluded by the strict criterion, which can
  inflate FP if the model reasonably selects them.
- **Evidence.** `djangocms_hidden_gold_adjudication.json` (schema/2, per-file
  rationale), `djangocms_hidden_gold_draft.json`, leak-scan results.
- **Claim affected.** Every semantic number; S006's diagnosis (Threat-relevant
  because S006's gold includes `cms/utils/plugins.py`, a file Sparse-v2
  systematically misses).
- **Mitigation / next experiment.** Independent second adjudicator + agreement
  (kappa) on RealCommitImpactDataset-v1; sensitivity of conclusions to
  alternative gold boundaries.

## Threat 13 — Survivor bias

- **Threat.** Comparing arms on VALID outputs only can bias conclusions when
  validity differs by arm (an arm that fails more often is judged only on its
  surviving runs).
- **Why it matters.** This is the sharpest threat to the M1 story: at 4096,
  Full-v2 produced ZERO valid outputs while Sparse-v2 produced one, so any
  semantic comparison at 4096 would be purely survivor-biased toward Sparse-v2.
- **Existing control.** M1A is reported as a feasibility/capability boundary,
  NOT a semantic comparison. M1B relaxes the cap so BOTH arms survive (30/30
  valid each, 0 truncations), making the M1B semantic comparison uncensored.
  The statistics report performs an explicit sensitivity analysis:
  operational metrics (validity/truncation) vs valid-output semantic metrics
  (P/R/F1), so the funnel is quantified rather than hidden. Within M1B, failed
  runs would have been counted as recall-0/FNR-1 (fail-closed) rather than
  dropped silently.
- **Remaining risk.** The funnel still exists at the 4096 boundary; if any M3
  condition starts failing at the 16384 cap, the same survivor-bias discipline
  must be re-applied.
- **Evidence.** `reports/M1_STATISTICAL_ANALYSIS.md` (sensitivity section),
  M1A probes, M1B records (all succeeded).
- **Claim affected.** The M1B cost-effect comparison (protected by cap
  relaxation) and any M1A-derived semantic reading (none is made).
- **Mitigation / next experiment.** Keep cap non-binding for all M3 conditions;
  report validity and semantic metrics side by side in every table; fail-closed
  scoring for invalid runs.

## Threat 14 — Token / cost accounting

- **Threat.** Token and cost numbers may be mis-accounted (usage missing,
  pricing source drift, cost lock misuse), inflating or deflating the
  cost-effect claim.
- **Why it matters.** The headline M1B contribution is a cost effect
  (-82.54% recorded API cost); accounting errors would change the headline.
- **Existing control.** Corrected accounting semantics (C4): request_attempted /
  request_dispatched / provider_response_received / raw_response_persisted /
  usage_known / finish_reason / truncation_status / transport_failure recorded
  per cell; usage captured BEFORE downstream validation; cost recomputed from
  usage at live pinned pricing; cost lock with conservative projected
  completion; zero-API verifiers recompute totals (42/42 checks).
- **Remaining risk.** Prices are provider-reported and can drift (Threat 15);
  usage_unknown cells are possible on transport failure; latency includes
  scheduling overhead.
- **Evidence.** `run_records.jsonl` per-cell `usage`, `api_cost`,
  `latency_seconds`; `endpoint_freeze.json` pricing; `verify_controlled_encoding_16k_claims.py`.
- **Claim affected.** Completion-token mean (8,383 vs 809), total cost
  ($0.275 vs $0.048), latency (1,659 s vs 609 s), and the -90.35% / -82.54% /
  -63.29% controlled reductions.
- **Mitigation / next experiment.** Re-fetch pricing at freeze time and again
  at closure; report both recorded-cost and usage-recomputed cost; apply the
  same accounting to M3 and its zero-API verifier.

## Threat 15 — Temporal / provider drift

- **Threat.** The provider route (DeepInfra `deepinfra/turbo`, fp4) may change
  behavior, pricing, quantization, or hardware over time, so numbers captured
  in September 2026 may not reproduce later.
- **Why it matters.** Reproducibility and honest longitudinal claims.
- **Existing control.** Endpoint freeze persists provider tag, quantization,
  context, max completion, pricing, and routing at study time; fallback OFF;
  provider reported per record; historical endpoint freeze retained; two
  independent builds of the graph plus canonical hashes protect the static
  inputs; cross-model replications partially bound drift.
- **Remaining risk.** No longitudinal re-run exists; provider-side
  nondeterminism is already visible at temperature 0; pricing can drift
  between freeze and any future re-run.
- **Evidence.** `endpoint_freeze.json` (M1A and M1B), per-record
  `provider_reported`, `exact_model`, `pricing_source`.
- **Claim affected.** Reproducibility of absolute token/cost numbers and
  semantic levels.
- **Mitigation / next experiment.** Re-freeze the endpoint immediately before
  M3 calls (mission requirement: same frozen provider route as M1 if
  available); document any pricing/route change; run a small same-batch
  repeatability probe (already evidenced by the 5-repetition within-scenario
  spread).

---

## Summary of risk posture

| # | Threat | Direction of residual risk | Primary control | Next experiment |
|---|---|---|---|---|
| 1 | Construct validity | Metric-gold judgment | Source-adjudicated gold, evaluation-only | RealChangeDataset + agreement |
| 2 | Internal validity | Encoding vs output-length entanglement | Prompt-control proof; parity artifact | M2 density separation |
| 3 | External validity | One repo, six curated scenarios | Explicit development-set labeling | RealCommitImpactDataset-v1 |
| 4 | Conclusion validity | n=6 units; descriptive claims only | Scenario-level analysis; no n=30 | More independent units |
| 5 | Curated-scenario bias | Difficulty author-chosen | Explicit NOT held-out language | Held-out real changes |
| 6 | Repetition dependence | 5 nested repeats, real nondeterminism | Nested treatment; within-scenario sd | More units + repeat decomposition |
| 7 | Prompt sensitivity | Single frozen template | Byte-controlled prompt control | Prompt-variant sweep |
| 8 | Schema choice | Schema drives magnitude | Same schema both arms; equivalence | M2 density stress |
| 9 | Completion-cap choice | Cap placement shapes censoring | 4096=feasibility only; 16384 non-binding | Keep non-binding in M3 |
| 10 | Model/provider dependence | One model, one provider route | Pinned route; two cross-model reps | Provider-route replication |
| 11 | Closed-world universe | Universe boundary is a choice | Frozen 144-path universe; gold subset | Universe sensitivity |
| 12 | Gold validity | Single-annotator adjudication | Source-verified rationale per file | Second annotator / agreement |
| 13 | Survivor bias | 4096 funnel; fail-closed otherwise | Sensitivity analysis; cap relaxation | Keep validity+semantic side-by-side |
| 14 | Token/cost accounting | Pricing drift; usage edge cases | Per-cell usage + recompute; verifiers | Re-freeze pricing at closure |
| 15 | Temporal/provider drift | Provider route may shift | Endpoint freeze; fallback OFF | Re-freeze before M3; repeatability probe |

**Bottom line.** The M1B descriptive cost effect (completion tokens, records,
cost, latency all reduced in all six scenarios; -90.35% / -96.60% / -82.54% /
-63.29%) is internally well controlled and is reported as descriptive. The
semantic direction of the encoding is NOT uniform across scenarios (see
`M1_SCENARIO_LEVEL_ANALYSIS.md`: S006 is a counterexample), which is exactly
why no universal semantic-superiority claim is made. The dominant remaining
risks are external validity (one repo, six curated scenarios), conclusion
validity (n=6), and gold validity — all addressed by
RealCommitImpactDataset-v1 and the M3 development-set design.