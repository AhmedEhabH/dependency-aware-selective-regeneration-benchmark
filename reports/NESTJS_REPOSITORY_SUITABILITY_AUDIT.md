# NestJS Repository Suitability Audit — Stage 3 generalization

**Date:** 2026-09-16
**Tier:** T3 research-design / ZERO scientific LLM calls
**Repo:** NestJS (`https://github.com/nestjs/nest`)
**Protocol:** `docs/NESTJS_REAL_COMMIT_PROTOCOL_V1.md`
**Classification: SUITABLE-WITH-DEVIATIONS** (see §10). NestJS is the
**preferred** Stage-3 repository but is NOT forced; if a predeclared
suitability criterion fails, the mission's backup is a JabRef suitability
protocol (never choosing a replacement because its results look better).

---

## 1. Scope

NestJS provides cross-language / cross-framework / cross-ecosystem evidence:
TypeScript instead of Python/Django, NestJS DI/controller architecture instead
of Django/Graphene. No scientific LLM inference on NestJS in this mission;
this audit + protocol are design-only.

## 2. Identity / license / anchor

| Item | Value |
|---|---|
| repo_url | https://github.com/nestjs/nest |
| license | MIT |
| language | TypeScript |
| structure | monorepo of `@nestjs/core`, `@nestjs/common`, `@nestjs/platform-express`, etc. (npm workspaces / lerna-style packages under `packages/`) |
| local cache | **absent** — no NestJS cache is currently pinned; audit below is from documented public facts and must be verified on-repo |

## 3. TypeScript production universe

- Production TS sources live under `packages/*/src/` (e.g. `packages/core/src/`,
  `packages/common/src/`, `packages/platform-express/src/`).
- Exclusions for a RealCommit-style universe: `*.spec.ts`, `e2e/`, `test/`,
  `benchmarks/`, generated `dist/`, node_modules, schema/dts shims.
- Universe scale: NestJS is much smaller in absolute file count than djangoCMS
  or Saleor (hundreds of production files, not thousands). This is favorable
  for prompt cost but means candidate universes per parent are small — the
  omission-risk and FNR behavior will differ from large repos.

## 4. Import / dependency-graph feasibility

- ES module / CommonJS imports (`import ... from '@nestjs/core'` and relative
  imports). A TS-aware AST import extractor is required (the frozen
  Python-only `build_parent_universe_and_graph` does NOT parse TS).
- **Deviation:** a TypeScript dependency-graph builder must be implemented
  (zero-LLM, deterministic) or the graph features are unavailable for NestJS.
  This is an implementation requirement, not a rule relaxation.

## 5. Historical commit quality / depth

- NestJS has a long, active public history (GitHub, PR-based, conventional
  commits). Commit volume is high; a 6000-commit window is feasible. Intent
  availability is good (descriptive PR-style messages). To be verified on-repo.

## 6. Parent/target reconstruction + proxy + leakage

- Single-parent diffs, `name-status`, production-only proxy, hidden
  observed-change-set — the frozen machinery applies unchanged.
- `allow_intent_path_leakage=False` unchanged.
- **Deviation:** file extensions and path rules differ (`*.ts` production,
  `*.spec.ts` excluded); the universe filter must be parameterized for TS.

## 7. Duplicates / related changes / candidate scale

- R1/R2/R3 unchanged. NestJS PR-branch merges may produce shared-PR groups
  (R2); the frozen rules handle it.
- Candidate scale: small-to-moderate universes (tens to a few hundred files).

## 8. Test / build metadata

- NestJS ships extensive Jest unit tests + e2e; build tooling (tsc). Tests are
  evaluator assets (read-only), never proxy. Build metadata exists but is not
  needed for the selection-evaluation protocol.

## 9. Expected model context / cost

- Small universes → small prompts → cheap cells (well below the djangoCMS
  per-cell cost). 3-rep development on ~120 tasks (~360 cells) would be well
  under $0.50 at frozen pricing. Re-budget from the actual frame.

## 10. Classification

**SUITABLE-WITH-DEVIATIONS.**

- Suitable because: real third ecosystem (TypeScript), MIT license, active
  PR-era history, well-bounded production universe, favorable cost.
- Deviations (documented):
  1. **TS import extractor required** (the frozen Python graph builder does not
     parse TypeScript) — graph features gated on this implementation.
  2. **Smaller universe/repo** → the omission-risk regime likely differs from
     djangoCMS; findings are ecosystem-comparative, not pooled-comparable.
  3. **No local cache yet** — on-repo verification of depth/intent required
     before freezing an anchor.
- **PREDECLARED suitability pass condition:** if after on-repo verification the
  eligible-pool yield (with frozen ceilings) is too small (e.g. < 60 eligible
  independent cases after R1/R2/R3), NestJS is declared UNSUITABLE for a
  quantitative Stage-3 and the JabRef backup protocol is prepared. This is a
  predeclared criterion, not a results-based choice.

## 11. Role / boundary

- Cross-language / cross-framework / cross-ecosystem evidence.
- Per-repository metrics primary; no pooled djangoCMS/Saleor/NestJS superiority
  claim; repo-ID confound check.
- Do NOT run scientific LLM inference on NestJS in this mission.

## 12. Blocker / next action

- No NestJS cache locally; TS graph extractor not implemented. Next actions
  (zero API, design): pin a NestJS anchor cache; verify commit depth/intent and
  eligible-pool yield; implement the TS import extractor; then freeze the
  NestJS protocol split.
## 13. Readiness status (2026-09-16 evening)

- **Full-history cache:** NOT acquired tonight (secondary priority; the primary
  A/B/C/E blocks are complete). Network is available; git fetch --unshallow
  of https://github.com/nestjs/nest into a pinned cache is the next data step.
- **TS production-universe semantics:** defined in
  docs/NESTJS_TS_PRODUCTION_UNIVERSE.md (packages/*/src/**.ts production,
  excluding *.spec.ts / e2e / test / benchmarks / dist / node_modules).
- **Import extractor:** a deterministic TS import/dependency extractor is
  required (the frozen Python graph builder does not parse TS). NOT implemented
  tonight.
- **Eligible-pool yield gate (predeclared):** >=60 independent eligible cases
  after R1/R2/R3; else NestJS is UNSUITABLE for quantitative Stage-3 and the
  JabRef backup protocol is prepared.
- **Blockers:** (1) no local NestJS cache; (2) TS import extractor not built.
- **Next actions (zero API):** pin NestJS anchor; fetch full history; implement
  TS import extractor + unit tests; estimate eligible pool; then freeze split.
