# Execution-Agent Provenance — SALEOR_RESERVE_300_RMCSS (2026-09-20)

**Status:** authoring/execution provenance record ONLY. This is NOT a
scientific method change.

## Why this record exists

The pre-unsealing continuation of the SALEOR_RESERVE_300_RMCSS mission was
partly executed by **OpenCode using GLM-5.3-Flash**, although the mission
requested `openrouter/deepseek/deepseek-v4-flash-0731`. Execution returns to
**deepseek-v4-flash-0731** for the remainder. This is recorded transparently;
it does not alter the frozen scientific protocol.

## What was executed under GLM-5.3-Flash (pre-unsealing)

- SIP / RM-CSS terminology freeze (`docs/GLOSSARY.md`);
- T3 impact declaration (`docs/SALEOR_RESERVE_300_RMCSS_IMPACT_DECLARATION_2026-09-20.md`);
- corrected Stage-5 evidence verification (SIP 0.3028/0.2744/0.2857; RM-CSS
  0.3256/0.3524/0.3419; pooled Δ +0.0562 CI [+0.0185, +0.0945]);
- cross-repository transfer diagnostic
  (`scripts/v2_cross_repo_transfer_diagnostic.py`,
  `reports/v2_cross_repo_transfer.json`) — verified against the supplied
  expected numbers (dc→sc DEV Δ +0.0745; dc→sc Stage-5 Δ +0.0776; thr 0.20;
  reverse weak);
- secondary `DJANGO_ONLY_RMCSS_TRANSFER_MODEL`
  (`scripts/saleor_reserve_300_transfer_model.py`,
  `research/saleor-reserve-300-rmcss/django_only_rmcss_transfer_model.json`,
  threshold 0.20, artifact SHA-256 `efb38c07…`);
- exact 300/1086 Saleor RESERVE sample, seed 20260920
  (`scripts/saleor_reserve_300_sample.py`,
  `research/saleor-reserve-300-rmcss/saleor_reserve_300_sample.{json,txt}`,
  manifest SHA-256 `445b5e9d…`);
- label-free preflight 300/300 OK, 0 exclusions
  (`scripts/saleor_reserve_300_preflight.py`);
- temporal descriptor wording B (same/overlapping-period disjoint-commit)
  (`scripts/saleor_reserve_300_temporal.py`);
- 300/300 label-free public-bundle materialization
  (`scripts/saleor_reserve_300_materialize_public.py`): sampled=300 built=300
  skipped=0 failed=0 (0 `hidden/` dirs, 0 `change_statuses` among the 300);
- original preregistration (`reports/SALEOR_RESERVE_300_RMCSS_PREREGISTRATION_2026-09-20.{md,json}`,
  SHA-256 `097b8625…`), committed `04abef5`, pushed, tagged
  `saleor-reserve-300-rmcss-preregistered-2026-09-20` (tag object `6ec7a99f`,
  peel `04abef5`);
- governance P88 (`DECISIONS.md`), PROGRESS / 00_CURRENT_RESEARCH_STATE /
  RESEARCH_JOURNEY updates;
- cost guard: exact label-free projection **$1.650909** vs frozen $1.50 ceiling
  → MANDATORY STOP before any paid call
  (`research/saleor-reserve-300-rmcss/saleor_reserve_300_cost_projection.json`);
  full audit export `project-2026-09-20-1833.zip` (FULL AUDIT EXPORT, ~205 MB).

## Zero-outcome statement

**Zero Saleor RESERVE target outcomes were opened** under GLM-5.3-Flash.
Verification: the 300 materialized bundles contain no `hidden/` directory and
no `change_statuses` in their manifests; no SIP prediction calls were made; no
embedding calls were made; the cost guard stopped before any paid call.

## Validation

All generated scientific artifacts are validated by deterministic
scripts/hashes/tests: sampling determinism re-run (identical manifest SHA),
preflight script (300/300), temporal descriptor (commit metadata), transfer
model artifact SHA-256, cross-repo diagnostic re-run (point estimates exact,
CIs within ~0.001 of the supplied references), preregistration self-hash
recomputed. No GLM-produced artifact is discarded or recomputed merely because
of the authoring-agent switch.

## Execution returns to

`openrouter/deepseek/deepseek-v4-flash-0731` for the remainder of the mission
(SIP execution, embeddings, RM-CSS features, parity gate, evaluation, audits,
reports, tags, exports).