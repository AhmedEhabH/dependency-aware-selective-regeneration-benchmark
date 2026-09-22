# WP-2 End-to-End Causal Design V1 (2026-09-22)

Status: **DESIGN ONLY — no paid execution in this mission.** This document
freezes the WP-2 causal/interventional E2E experiment design and the assay
sensitivity logic. Final paid authorization and sample sizes are NOT frozen
here.

## 6.1 Core thesis question

> Is a low-cost predicted impact scope functionally sufficient for correct,
> preservation-safe LLM-driven software evolution, and what is the effect of
> enforcing that scope as a hard editing contract?

## 6.2 Do not use cross-task F1→F2P correlation as causal evidence

Cross-task correlation is confounded by task difficulty: hard tasks may
simultaneously have low localization F1 and low generation success. Such
correlation may be reported descriptively, but it cannot establish that scope
quality caused the E2E outcome.

## 6.3 Interventional principle

For causal scope comparison, hold fixed:
- same task;
- same parent repository;
- same task specification;
- same generator/model;
- same temperature/config;
- same repair policy;
- same validator;
- same evaluation oracle;

and change **only the scope contract**.

## 6.4 Arms (designed, not executed)

| Arm | Editable source scope | Gate | Purpose |
|---|---|---|---|
| `GOLD_HARD` | observed target-changed SOURCE files only (tests excluded) | hard: no edits outside scope | feasibility ceiling / scope upper reference (not deployable method) |
| `RMCSS_HARD` | frozen RM-CSS predictions | hard | thesis treatment arm |
| `AGENT_HARD` | frozen protocol-v3 Agent predictions | hard | matched comparator using Agent file selection under the same downstream generator/validator |
| `PLACEBO_HARD` | size-matched random source-file set with exactly \|RMCSS_HARD\| files; fixed seed; from the same eligible parent-only source universe; no test/vendor/generated files; selected without gold/RM-CSS/Agent/E2E outcome | hard | assay sensitivity / location-value negative control |
| `RMCSS_SOFT` | RM-CSS predicted files provided as starting context/hints; editing NOT restricted | soft (same generator/tool budget) | effect of the HARD contract vs soft navigation hint |
| `GOLD_MINUS_ONE` | subset only; tasks with ≥2 and bounded gold source files; remove one gold source file, everything else fixed | hard | causal Critical Omission Risk (not a primary all-task arm; bounded cost/sample plan) |

## 6.5 Core arms vs secondary arms

- Research Run core (cost-controlled): `GOLD_HARD`, `RMCSS_HARD`,
  `AGENT_HARD`, `PLACEBO_HARD`.
- Secondary/ablation: `RMCSS_SOFT`.
- Mechanistic subset: `GOLD_MINUS_ONE`.

Final paid authorization / sample sizes are NOT frozen in this mission.

## 6.6 Assay sensitivity

A future "RM-CSS ≈ Agent functionally" result is interpretable only if the
instrument can show that scope matters. Before Research Run, the Pilot must
demonstrate:
- Gold/meaningful scope is not indistinguishable from random placebo merely
  because the generator has a floor effect;
- the generator can solve a non-trivial fraction of confirmed tasks.

The numeric Pilot threshold is NOT invented here. This mission produces the
data needed to set it before any paid Research Run:
- confirmed oracle yield;
- task strata;
- environment success;
- future Smoke/Pilot runtime;
- zero-API power/sensitivity scenarios.

## 6.7 Specification policy

PRIMARY generator specification:
- existing label-free task intent + parent repository information only;
- no target test content in the prompt;
- no target patch;
- no target file list;
- no target-derived signatures/docstrings;
- tests/evaluator metadata remain hidden.

Why: target-derived signatures can make an under-specified task easier using
privileged future information, changing the question. FEA-Bench legitimately
provides new-component signatures as part of its benchmark contract; our
benchmark has a different task contract.

If Pilot shows a floor caused by under-specification: prepare, but do not
silently activate, a separately labelled `SPEC_AUGMENTED_SENSITIVITY` design.
Any augmentation must be frozen before Research Run and must identify whether
information is parent-available/public vs target-derived/oracle-assisted.

## 6.8 Test hiding

Future generator and repair model must never see:
- target test patch;
- F2P/P2P node IDs;
- target changed-file list;
- target patch;
- test expected outputs beyond what is legitimately present in the task spec.

Evaluator may use them after generation.

## 6.9 Migration policy

Do not solve migration policy by hidden arm-specific post-processing. Design
rule:
- identical deterministic post-processing is allowed only if it is available to
  EVERY arm and its outputs obey that arm's edit-scope contract;
- otherwise migration generation is part of the generator's responsibility.

Record migration-heavy tasks as a stratum. Final policy is frozen before Smoke.

## 6.10 Repetition policy

- TEST ORACLE: 3 runs per parent state and 3 runs per target state for flakiness
  screening.
- LLM GENERATION: do NOT yet force 3 replicates per arm/task. Pilot must
  estimate run-to-run variance and cost first; Research Run replicate count is
  preregistered from Pilot evidence.

## Estimands (planned, not frozen)

For each arm and task:
- functional resolution (F2P pass) rate;
- P2P / preservation violation rate;
- over-edit / out-of-scope edit rate;
- total pipeline cost (selection + generation + validation + repair);
- per-arm pooled and stratified estimates with paired bootstrap CIs across the
  confirmed oracle tasks.