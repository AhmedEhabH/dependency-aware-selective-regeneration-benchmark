# Track 04 — TypeScript Parent-Graph G1

**Status: Engineering Gate Candidate. Not an RM-CSS result.**

## Inputs

- Historical `tinylibs/tinybench` parent commit `c9816afede719138d581b66bdde1188346010f53`.
- TypeScript and dependency versions from the parent `pnpm-lock.yaml` via pnpm 9.15.4.
- Production universe for tinybench: `src/**/*.{ts,tsx,mts,cts}` excluding tests/specs/benchmarks/`.d.ts`/generated outputs.
- Historical NestJS production universe: `packages/*/src/**/*.{ts,tsx,mts,cts}`, same exclusions. This mode is not an amendment of its pre-registered scientific protocol.

## Guarantees tested

1. `git rev-parse HEAD` matches the specified parent SHA, or STOP.
2. Any tracked OR untracked source/config changes from HEAD trigger STOP (including staged edits).
3. Symlink paths are not traversed; import edges point only to files inside the frozen production universe.
4. TypeScript compiler AST parses import and export clauses, literal `require()` and literal dynamic `import()` without executing source.
5. Static top-level functions, class/method spans and arrow-function declarations are recorded with content SHA256 and line spans.
6. TS parse errors STOP. Zero eligible source files STOP.
7. Repeated identical parent analyses must be byte-identical. Graph includes parent SHA and TS version.
8. The evaluator and model are not involved; no child commit, patch, changed-path ground truth or hidden test is provided.
9. Pinned tinybench parent must have exactly seven production TypeScript files (`bench`, `constants`, `event`, `index`, `task`, `types`, `utils`).
10. Independent audit compares each source SHA-256 against `git show P:path`, checks all graph edges target frozen production files and matches per-file imports.

## Not yet supported or qualified

- Full RM-CSS TypeScript execution, code regeneration, or model inference.
- Independently validated TypeScript dependency graph recall (including complex `tsconfig` aliases, dynamic variable imports, runtime reflection, decorators).
- Behavioral F2P/P2P qualification, hidden tests, or selection methodology.
- Representative cross-project statistics / external-validity claims.
- NestJS scientific suitability gate (>=60 deduplicated qualified cases under the already frozen protocol).

## Paper-safe interpretation

`G1 PASS` demonstrates that a zero-inference, parent-only TypeScript inventory can be deterministically constructed at a pinned historical revision; it **does not** demonstrate that RM-CSS can localize changes, generate compilable code, pass tests, or save tokens.
