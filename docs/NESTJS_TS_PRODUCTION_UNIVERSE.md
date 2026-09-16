# NestJS TypeScript Production-Universe Semantics

**Date:** 2026-09-16 evening
**Tier:** T3 design (ZERO scientific LLM calls)
**Purpose:** define the deterministic production-file universe semantics for a
NestJS Stage-3 real-commit dataset, so a future TS import extractor and the
frozen eligibility/dedup/selection rules can be applied without weakening rules.

---

## 1. Repository

- repo_url: https://github.com/nestjs/nest
- license: MIT
- structure: npm-workspaces / lerna-style monorepo under `packages/`
  (`@nestjs/core`, `@nestjs/common`, `@nestjs/platform-express`, etc.).

## 2. Production universe (deterministic)

- **Included:** production TypeScript sources under `packages/*/src/**/*.ts`
  (excluding index/test-only shims that only re-export).
- **Excluded:**
  - `*.spec.ts`, `*.test.ts` (Jest unit tests);
  - `e2e/`, `test/`, `benchmarks/`, `integration/` test directories;
  - generated `dist/`, `node_modules/`, `coverage/`, `lib/` build output;
  - `*.d.ts` declaration shims that duplicate source types;
  - JSON/JS config files (not production source under test).
- **Unit of change:** file path under a production `packages/*/src/` root.

## 3. Import / dependency graph

- ES module and CommonJS imports:
  - relative: `import ... from './foo'` / `'../foo'`;
  - package: `import ... from '@nestjs/core'`.
- A deterministic TS import extractor (regex/AST, zero LLM) is required to map
  package-level and relative imports into a dependency graph. This is an
  implementation requirement; the frozen Python graph builder does NOT parse TS.
- Parent-only inputs (the frozen rule) apply: build the graph from the parent
  revision only.

## 4. Interaction with the frozen rules

- `evaluate_eligibility` / `classify_changed_paths` / R1/R2/R3 / selection /
  split: unchanged. Only the production-root predicate is parameterized
  (`PRODUCTION_ROOT = "packages"` plus `src/**/*.ts` filter) — a config
  adapter, NOT a rule change.

## 5. Candidate scale / expected behavior

- NestJS is much smaller than djangoCMS/Saleor in absolute file count (hundreds
  of production files). Candidate universes per parent are expected in the tens
  to low hundreds. The omission-risk regime likely differs (smaller scope);
  findings are ecosystem-comparative, not pooled-comparable.

## 6. Predeclared yield gate

- If, after applying the frozen eligibility/dedup rules to the reconstructed
  frame, the independent eligible pool is < 60, NestJS is UNSUITABLE for a
  quantitative Stage-3 and the JabRef backup protocol is prepared.
- This gate is set BEFORE any model result; no replacement is chosen because
  its results look better.