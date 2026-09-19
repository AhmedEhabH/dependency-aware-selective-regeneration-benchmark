# Cross-Language Readiness (TypeScript / Java / Go) — 2026-09-19

**Date:** 2026-09-19
**Mission:** STRONG LOCALIZATION SIGNAL BRIDGE
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**ZERO API** (only public repo metadata; no inference, no tuning).

Purpose: prepare — but NOT run — dataset readiness for one TypeScript, one
Java and one Go repository, so Stage-7 cross-language generalization is
pre-planned. These datasets must NOT affect Python-method tuning (they are
readiness only).

## Summary table

| Criterion | TypeScript | Java | Go |
|---|---|---|---|
| Candidate | `nestjs/nest` (roadmap) | `JabRef/jabref` (roadmap backup) | `prometheus/prometheus` (new) |
| Dominant language | TypeScript | Java | Go |
| GitHub metadata (2026-09-19) | 76.7k stars, active, master | 4.7k stars, active, main | 66k stars, active, main |
| Commit availability | full history available on GitHub; local cache ABSENT | full history on GitHub; local cache ABSENT | full history on GitHub; local cache ABSENT |
| Issue-link availability | PRs link issues (GitHub) | issues + PRs (GitHub) | issues + PRs (GitHub) |
| Parent-only universe feasibility | YES (protocol V1 frozen) | YES (same miner) | YES (same miner) |
| Production-file rules | `packages/*/src` production TS, exclude `*.spec.ts`/`e2e`/`test`/`benchmarks`/generated | `src/main/java`/`jabgui`/`jablib` etc. production Java, exclude test/generated | `pkg/`, `cmd/`, `promql/`, `scrape/`, `storage/`, `web/` production Go, exclude `_test.go`/vendor/generated |
| Generated/vendor/test exclusions | TS: `*.spec.ts`, `e2e`, `test`, `benchmarks`, `node_modules` | Java: `src/test`, `build/`, generated | Go: `*_test.go`, `vendor/`, `embedded/` |
| Approx eligible real commits | >=60 rule frozen (unverified on-repo) | >=60 rule (to be verified on-repo) | >=60 rule (to be verified on-repo) |
| Mining feasibility | HIGH (same deterministic miner; TS import extractor MISSING — blocker) | HIGH (same miner; Java parser = `javalang`-style or regex) | HIGH (same miner; Go parser = `tree-sitter-go` or stdlib `go/parser`) |
| Leakage risk | same parent-only rules; TS/Java/Go all use observed-change-set proxy | same | same |
| Storage/build complexity | clone ~200-500 MB; TS extractor needed for graph features | clone ~200 MB; Java build (Gradle) heavy but mining does not need a build | clone ~300 MB; no build needed for mining |

## TypeScript — nestjs/nest (carried forward from 2026-09-18 readiness)

- Frozen suitability protocol + `>=60` rule already exist
  (`docs/NESTJS_REAL_COMMIT_PROTOCOL_V1.md`,
  `reports/NESTJS_REPOSITORY_SUITABILITY_AUDIT.md`).
- **Blockers (unchanged):** (1) no local NestJS cache — full-history fetch +
  pin needed; (2) **TypeScript import/dependency extractor NOT implemented**
  (the frozen graph builder parses Python only) — graph features for NestJS are
  gated on a new extractor + tests; (3) anchor SHA not yet pinned; (4)
  eligible-pool yield not yet counted on-repo.
- **This mission's addendum:** GitHub metadata re-verified reachable and
  active. NestJS remains the preferred TS candidate; the JabRef backup is the
  Java line (below).

## Java — JabRef/jabref (roadmap backup candidate, now primary Java)

- GitHub: `JabRef/jabref`, main branch, 4.7k stars, active (pushed 2026-09-19).
- Dominant language Java (Gradle multi-module: `jabgui`, `jablib`, `jabls`,
  `jabsrv`, `jabkit`, etc.).
- Production Java universe: module `src/main/java` trees; exclude `src/test`,
  `src/testFixtures`, `build/`, generated sources.
- Mining: same deterministic parent-only miner (intent text from linked
  issues; observed change-set proxy). Java dependency graph would need a Java
  import extractor (e.g. `javalang`-based) — a NEW engineering component.
- Leakage: identical parent-only rules.
- Approx eligible real commits: to be counted on-repo against the `>=60` rule
  (predeclared); likely sufficient given an active issue-driven project.

## Go — prometheus/prometheus (new candidate, proposed)

- GitHub: `prometheus/prometheus`, main branch, 66k stars, active (pushed
  2026-09-19).
- Pure-Go structure: `cmd/`, `pkg/`, `promql/`, `rules/`, `scrape/`,
  `storage/`, `tsdb/`, `web/` — production Go, issue-driven development with
  high issue-link availability.
- Production universe: production `.go` files; exclude `*_test.go`,
  `vendor/`, `embedded/`, generated protobuf (`prompb/` generated?), build
  artifacts.
- Mining: same miner; Go import graph via stdlib `go/parser` or
  `tree-sitter-go` (new extractor component).
- Approx eligible real commits: to be counted on-repo; the project's history
  is large (10k+ commits), so `>=60` is likely satisfied.

## Common engineering gaps (all three, ZERO-API blockers)

1. **Non-Python import/dependency extractors are not implemented** (TS, Java,
   Go). The graph features used by Route-B are Python-only. For the 
   embedding-only SweRank-style evaluation the graph is NOT needed, so a
   cross-language first experiment could proceed WITHOUT the graph (Sparse +
   embedding additions); graph features would be added later.
2. **Local caches absent** for all three (full-history clone required;
   ~200-500 MB each, tractable on this machine's 24 GB free disk).
3. **Eligible-pool yields unverified on-repo** — must be counted before any
   protocol activation (predeclared `>=60` rule).

## Recommendation

TypeScript (NestJS) and Java (JabRef) are pre-planned in the roadmap. Go
(`prometheus/prometheus`) is proposed here as a concrete pure-Go candidate.
Readiness is at the "documented + verified metadata" level; actual mining
requires (a) local clones, (b) a per-language universe filter, and (c)
optional per-language import extractors. None of this affects Python-method
tuning, and none is executed in this mission.