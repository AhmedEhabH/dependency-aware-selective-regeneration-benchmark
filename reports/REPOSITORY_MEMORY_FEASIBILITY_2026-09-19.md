# Repository-Memory Localization — Feasibility Study (ZERO API, 2026-09-19)

**Date:** 2026-09-19
**Mission:** STRONG LOCALIZATION SIGNAL BRIDGE
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**ZERO API.** No model/LLM calls. Only local git history + released artifacts.

## 1. Question

Can a parent-visible **repository-memory** signal (the mechanism of
"Improving Code Localization with Repository Memory", arXiv 2510.01003) be
reproduced under our parent-only real-commit protocol, and is it worth building?
The literature shows commit-history memory (recent commits + linked issues +
functionality summaries of actively evolving parts) materially improves agentic
localization on SWE-bench; our P63/P64 finding says the ranking bottleneck is
the dominant loss, and repository history is a fundamentally DIFFERENT signal
family we have not yet tested.

## 2. Resolved blocker: "Saleor parent-visible history cache absent"

The documented blocker (PROGRESS.md / AGENTS.md) is that
`dist/real-commit-cache/saleor` is absent. **This mission resolves it:**

- A **full local Saleor git repository IS available** at
  `dist/pilot-repo-cache/saleor`:
  - origin = `https://github.com/saleor/saleor.git`;
  - HEAD = `2c48391b652c26ce4f27a53d6532d4c873306af0` — **identical to the
    frozen dataset anchor commit** in
    `benchmark_data/real_commit_impact_saleor/saleor_development_manifest.json`;
  - full history, **22,615 commits**, not shallow (`rev-parse --is-shallow-repository`
    = false);
  - parent commits of the Saleor DEV tasks resolve (`git cat-file -t` PASS,
    e.g. `11c15f1af…`).
- The `dist/real-commit-cache/saleor` path is simply the *standard* cache path
  that was never materialized; the git data is present at the pilot-repo-cache
  path. **A Saleor parent-visible history cache can therefore be built
  deterministically** from this repo (see §5).
- djangoCMS history cache already exists (`dist/real-commit-cache/djangocms`),
  and the co-change cache
  (`research/first-pass-recall-bottleneck/cochange_cache.json`, 174 tasks)
  already holds parent-visible co-change counts for djangoCMS.

## 3. The mechanism (from arXiv 2510.01003)

The paper augments an agent with a **non-parametric memory** built from:
1. recent historical commits (parent-only) — retrieved as textual memory;
2. linked issues for those commits (issue ↔ commit linkage);
3. functionality summaries of actively evolving modules, identified via commit
   patterns (frequency/evolution information).

All are parent-visible (the history strictly precedes the target commit). This
is exactly the signal family our protocol permits (it never needs the target
patch or child revision).

## 4. What a faithful reproduction requires (minimum viable probe)

| Component | Requirement | Local availability |
|---|---|---|
| Parent-only commit history | `git log <parent>` ancestors per task | djangoCMS: YES; Saleor: YES (pilot-repo-cache) |
| File-level co-change counts | deterministic `git log --name-status` scan | djangoCMS: already cached; Saleor: buildable |
| Linked issues | issue ↔ commit linkage (PR/issue numbers from commit messages) | partially in commit messages; needs a mapping audit |
| Module/function summaries | LLM-generated (paper) OR deterministic (regex/structural) | deterministic variant feasible ZERO-API; LLM variant needs budget |
| Evolution frequency | per-file commit frequency/recency before parent | YES (git log --follow / rev-list) |
| Leakage controls | strictly exclude the target commit and any descendant | trivially enforced (history = ancestors of parent only) |

## 5. Deterministic build procedure (frozen proposal, ZERO API)

1. **Corpus**: for each task, collect ancestor commits of `parent_commit`
   (e.g. `git -C <repo> rev-list <parent>` capped at a window, say the most
   recent 2,000 ancestors — the same window already used for the djangoCMS
   co-change cache).
2. **Co-change table**: `git log --name-status -n <window> <parent>` → for each
   seed/write-set path, count files changed together (already implemented for
   djangoCMS in `src/benchmark/recall/data.py::_files_changed_with`).
3. **Evolution features**: per universe file — commit count in window, last
   touched recency, distinct contributor count (optional).
4. **Linked issue text**: parse `(#NNNN)` / `Fixes #NNNN` from ancestor commit
   messages → map to issue numbers (no network needed if issue text is not
   fetched; a network-free variant uses only the commit messages themselves).
5. **Score**: define ONE deterministic memory ranker (e.g. co-change count with
   recency decay) over the omitted-candidate pool; evaluate with the SAME
   metrics/gate machinery as the SweRank study (paired bootstrap, B=5 primary).

**Disk/time estimate**: Saleor `git log --name-status` for ~149 tasks × 2,000
ancestors ≈ sub-10-minute wall on the local repo (single machine); the
djangoCMS cache took minutes. Disk: negligible (JSON caches). No model/LLM
required for the deterministic variant.

## 6. Minimum useful feasibility probe

Do NOT build the full system. Probe = build the Saleor co-change + evolution
table for the 149 DEV tasks (and confirm the 174-task djangoCMS table), then
test ONE deterministic memory ranker (co-change count desc, recency-decay
tie-break) against Route-B under the frozen progression gate shape. If the
probe fails the gate (like the earlier binary-flag ADD queues), freeze the
negative; if it passes, expand to linked-issue text memory.

## 7. Leakage tests required before any run

- Assert every candidate memory entry's commit is an ancestor of `parent`
  (never the target/child commit, never a descendant).
- Assert no target patch paths / proxy positives enter the memory.
- Assert determinism (same input → same memory → same ranking).

## 8. Recommendation

**Feasible, cheap, and scientifically motivated.** The history signal is a
fundamentally different family from the (now positive) embedding signal; the
two could later be fused. The deterministic co-change/evolution probe can be
executed entirely ZERO-API and should be the next repository-memory experiment
if a future mission is authorized. This mission only records feasibility; it
does NOT build the probe (scope: statistics + SweRank + readiness).