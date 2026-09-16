# NestJS RealCommit Protocol V1

**Date:** 2026-09-16
**Tier:** T3 research-design / ZERO scientific LLM calls
**Status:** PROTOCOL FROZEN (design). On-repo verification BLOCKED until a
NestJS anchor cache is pinned and a TypeScript import extractor is implemented
(see `reports/NESTJS_REPOSITORY_SUITABILITY_AUDIT.md`).
**Precedence:** Stage-3 cross-ecosystem protocol. NestJS is preferred but NOT
forced; if a predeclared suitability criterion fails, the backup is a JabRef
suitability protocol.

---

## 1. Purpose

Produce cross-language / cross-framework evidence: does the Sparse impact-plan
representation and the bounded-verification question transfer from Python/Django
(djangoCMS, Saleor) to TypeScript/NestJS?

## 2. Repository identity (frozen)

- repo_url: https://github.com/nestjs/nest
- license: MIT
- anchor: to be pinned after on-repo verification (proposed: the newest stable
  release tag; exact SHA frozen before any model result).

## 3. Data rules (frozen, parameterized for TypeScript)

- Window: newest 6000 ancestors of the frozen anchor.
- Eligibility: single-parent; meaningful intent; production TypeScript source
  change only (`packages/*/src/**/*.ts`, excluding `*.spec.ts`, `e2e/`,
  `test/`, `benchmarks/`, generated files); proxy ≤ 12; total diff ≤ 40;
  `allow_intent_path_leakage=False`; whitespace-only excluded.
- Dedup: R1 exact-proxy-set / R2 shared-PR-reference / R3 suspected-related
  (unchanged).
- Split: metadata-only, deterministic seed, frozen hashes, before any model
  result.
- Proxy: observed change-set (status M), hidden, evaluation-only.

## 4. Sparse inference configuration (frozen; identical to the registered study)

- model qwen/qwen3-coder; provider deepinfra/turbo (OpenRouter, no fallback);
  temperature 0; cap 16384; Graph OFF; protocol real-commit-p1-v1.0.0; SPARSE;
  3 reps/task unless the sample-size report says otherwise; six gates +
  leakage audit before any call.

## 5. Predeclared suitability pass condition (frozen)

After on-repo verification: if the eligible-pool yield after R1/R2/R3 with the
frozen ceilings is < 60 independent cases, NestJS is UNSUITABLE for a
quantitative Stage-3 and the JabRef backup protocol is prepared. This criterion
is set BEFORE any model result; no replacement is chosen because its results
look better.

## 6. Deviations from djangoCMS (documented)

1. TypeScript import/dependency-graph extractor must be implemented (the frozen
   Python graph builder does not parse TS). Graph features are gated on it.
2. Smaller universe/repo → omission-risk regime likely differs; findings are
   ecosystem-comparative.
3. File-extension/path universe filter parameterized for TS.

## 7. Gates / audit / release

Same six gates + independent audit (ZERO-API until split audited), then live
development inference under a frozen budget; commit / push / merge / DEV tag
for reproducible milestones.

## 8. Blocker / next action

- No NestJS cache locally; TS import extractor not implemented. Next actions
  (zero API): pin NestJS anchor cache; verify depth/intent and eligible-pool
  yield; implement TS import extractor; freeze split; then evaluate.