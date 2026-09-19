# True Polyglot Repository Feasibility — grafana/grafana (Go + TypeScript)

**Date:** 2026-09-19
**Mission:** STRONG LOCALIZATION SIGNAL BRIDGE
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**ZERO API** (public metadata only; no scientific localization run).

## 1. Question

Is `grafana/grafana` a TRUE polyglot single repository — i.e. ONE repository
with substantial production code in multiple languages AND genuine
cross-language change coupling (Go backend + TypeScript frontend modified in
the SAME historical change) — such that a cross-language impact-selection
benchmark is scientifically meaningful?

GitHub's dominant-language heuristic reports TypeScript because the frontend
tree is larger by bytes; the **Go backend is substantial and production** (see
§2), so a byte-count heuristic alone does NOT answer the polyglot question.

## 2. Verified structure (GitHub API, 2026-09-19)

- Root layout confirms BOTH production languages:
  - **Go backend:** `pkg/` (api, apimachinery, apiserver, apis, bus, clientauth,
    components, events, expr, infra, kinds, login, middleware, …) + `kinds/`
    (Go + TS codegen), `cue.mod`.
  - **TypeScript frontend:** `public/` (app, boot, …) + `apps/`, `packages/`,
    `e2e-playwright/` (test).
- Structural cross-language coupling is present by design: backend API
  endpoints in Go ↔ frontend API client / redux slices in TypeScript; the
  project maintains generated API clients (`public/api-merged.json`,
  `openapi3.json`).
- GitHub metadata: `grafana/grafana`, main branch, 76.8k stars, ~2.0 GB repo
  size (clone ≈ 0.5–1.0 GB), active (pushed 2026-09-19), 3.3k open issues —
  issue-link availability is high.

## 3. Frozen minimum eligibility definition (frozen BEFORE any counting)

A historical commit is an eligible **true-polyglot change** ONLY IF it satisfies
ALL of:

1. **Substantial production code on BOTH sides of a language boundary in the
   SAME commit** — e.g. Go + TypeScript — where "production code" means files
   in the per-language production universe (Go: `pkg/`, `cmd/`, `kinds/`
   production `.go`; TS: `public/app/`, `packages/` production `.ts/.tsx`).
2. **Meaningful change size** on both sides: at least one production Go file
   AND at least one production TS file with a real diff (not whitespace-only),
   AND the change is NOT purely generated output (e.g. NOT only
   `public/api-merged.json` / generated codegen artifacts).
3. **Cross-language semantic coupling** is documented or inferable: the Go
   change and the TS change refer to the same feature/endpoint/domain (proxy
   = observed change-set; no target labels).
4. **Exclusions applied**: build scripts / config only (`*.yml`, `Makefile`,
   Dockerfile, CI), vendored code, generated code, tests (`*_test.go`,
   `*.spec.ts`, `e2e`), and trivial config languages (JSON/yaml) do NOT count
   as a meaningful side.
5. **Same proxy/leakage rules** as the frozen protocol (parent-only universe,
   parent-visible intent, observed change-set proxy, no child/target leakage).

## 4. Feasibility assessment

| Requirement | Status |
|---|---|
| Enough historical commits modifying production code across language boundaries (Go+TS in the same change) | **UNVERIFIED ON-REPO — must be counted.** Structurally plausible (backend↔frontend parity changes are a known grafana change pattern) but the exact count requires the repo history. |
| Local clone | Feasible: full clone ≈ 0.5–1.0 GB on 24 GB free disk (tens of minutes). |
| Per-language production universe | Defined above (§3); needs a concrete file-pattern audit against the real tree. |
| Cross-language coupling representation | Two natural options: (a) commit-level strata (mixed-language commits), (b) a typed cross-language edge (backend endpoint ↔ frontend consumer) — graph extractor NOT implemented (Python-only today). |
| `>=60 eligible real commits` target | Predeclared (same as the cross-language rule); to be counted on-repo. |
| Leakage risk | Same parent-only controls; no special risk beyond the standard rules. |

## 5. Recommended next step (NOT executed here)

Freeze the eligibility definition (§3) into a suitability-audit document; then
run a ZERO-API counting probe: clone `grafana/grafana` (shallow optional; full
history preferred), enumerate mixed Go+TS production commits in a frozen
window, and check against the `>=60` rule. If the yield is sufficient, a
per-language universe manifest + split freeze could be prepared in a future
mission. NO localization science runs in this audit.

## 6. Caveats

- "Polyglot" here is about genuine cross-language change coupling in
  PRODUCTION code, not the coexistence of build/config/test languages.
- GitHub's dominant-language metadata is NOT evidence for or against
  eligibility; the on-repo counting probe is the only valid check.
- grafana is a future feasibility candidate ONLY (per P64 roadmap wording);
  nothing in this audit changes that status.