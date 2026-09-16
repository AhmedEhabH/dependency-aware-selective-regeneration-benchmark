# Saleor RealCommit Protocol V1

**Date:** 2026-09-16
**Tier:** T3 research-design / ZERO scientific LLM calls
**Status:** PROTOCOL FROZEN (design). Sampling-frame reconstruction BLOCKED
until full Saleor history is cached (see
`reports/SALEOR_REPOSITORY_SUITABILITY_AUDIT.md`).
**Precedence:** this is the Stage-2 cross-repository protocol. It reuses the
frozen M4A-1/M4A-2/M4A-3 machinery without loosening rules.

---

## 1. Purpose

Produce a Saleor real-commit dataset + Sparse impact-plan development evidence
that can confirm (or reject) the djangoCMS findings in a second real system,
under a common file-level protocol.

## 2. Repository identity (frozen)

- repo_url: https://github.com/saleor/saleor
- pinned snapshot: `2c48391b652c26ce4f27a53d6532d4c873306af0`
- profile: `benchmark_data/repository_profiles/saleor.yaml` (version 3.23.0)

## 3. Data rules (identical to the frozen djangoCMS rules; no loosening)

- Window: newest 6000 ancestors of a frozen Saleor anchor (to be pinned after
  full history acquisition; proposed anchor = the pinned snapshot HEAD).
- Eligibility: single-parent; meaningful intent; production Python source
  change only; proxy ≤ 12; total diff ≤ 40; `allow_intent_path_leakage=False`;
  whitespace-only excluded; MINER_DEV-style targets excluded if any.
- Production universe: per `benchmark_data/repository_profiles/saleor.yaml`
  `artifact_universe` (graphql + domain models/services + core + permission +
  plugins + webhook); migrations and tests excluded.
- Dedup: R1 exact-proxy-set / R2 shared-PR-reference / R3 suspected-related
  (same-change predicate) — unchanged.
- Split: metadata-only, deterministic seed, frozen hashes, BEFORE any model
  result.
- Proxy: observed change-set (status M), hidden, evaluation-only.

## 4. Sparse inference configuration (frozen; identical to the registered study)

- model: qwen/qwen3-coder (Qwen3-Coder-480B-A35B-Instruct)
- provider: deepinfra/turbo pinned through OpenRouter (no fallback)
- temperature 0; completion cap 16384; Graph OFF
- protocol real-commit-p1-v1.0.0; serialization SPARSE
- 3 nested reps/task unless the sample-size report says otherwise
- SAME six gates + leakage audit before any call

## 5. Deviations from djangoCMS (documented, pre-registered)

1. Candidate universes are larger (low hundreds to ~1k files) → higher prompt
   tokens per cell; re-budget inference cost from the frame, never assume the
   djangoCMS per-cell cost.
2. Saleor commits are larger → frozen size ceilings exclude a higher share;
   accept a smaller eligible pool rather than loosening rules.
3. History/co-change features require full history (deferred until cached).
4. Cross-repo metrics: per-repository primary; macro-average across repos;
   pooled secondary; repository-ID confound check; no single repo dominating
   the headline.

## 6. Classification (from the suitability audit)

SUITABLE-WITH-DEVIATIONS.

## 7. Gates / audit / release

- Six gates (Dataset / Input / Smoke / Dry Run / Integration / Metric) + independent
  audit, all ZERO-API until the frozen split is audited.
- Then live development inference under a frozen budget (to be set from the
  reconstructed frame; default authorized ceiling pattern: ≤450 new cells,
  ≤2.5M tokens, ≤$1.00, no TEST/RESERVE calls).
- Commit / push / merge main / DEV tag only for genuinely reproducible
  scientific/data milestones.

## 8. Blocker / next action

- Full Saleor history not cached locally. Next action (zero API): acquire full
  history into a pinned cache; run the frozen candidate enumeration
  (`scripts/reconstruct_v2_sampling_frame.py` generalized to Saleor) to
  reconstruct the eligible frame; then freeze the Saleor split and proceed.