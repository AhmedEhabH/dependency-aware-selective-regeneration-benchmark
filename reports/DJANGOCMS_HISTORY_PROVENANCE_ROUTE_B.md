# djangoCMS Parent-Visible History — Provenance Record (Route B history arm)

**Date:** 2026-09-17
**Tier:** T3 data (ZERO scientific model calls)
**Purpose:** enable the Route B **history/co-change arm** using parent-visible
djangoCMS history. The protocol requires that ONLY history at/before a task's
parent commit P is used; NEVER commits after P (no future-state leakage).

---

## 1. Cache provenance

- **Cache path:** `dist/real-commit-cache/djangocms`
- **State:** non-shallow; **16,602 commits**; full modern PR-era history.
- **Anchor:** `0f633fc9fa213357f4202482aab2b0edad680f95` (tag 5.0.0) — present.
- **Verification:** `git rev-parse --is-shallow-repository` = `false`;
  `git rev-list --count HEAD` = 16602.
- **Note:** the documented "missing pinned git cache"
  (`benchmark_data/repositories/djangocms`) is a DIFFERENT path used by the
  frozen parent-commit corpus (Protocol-A). The full-history cache at
  `dist/real-commit-cache/djangocms` is available and is the authoritative
  source for parent-visible co-change features.

## 2. Parent-visible rule (frozen)

For a task with parent commit P and candidate file f:
- co-change evidence for f uses ONLY commits reachable from P (i.e., history
  with commit time <= time(P) and reachable as an ancestor of P).
- NEVER use commits after P (target T or later).
- Implementation: `git log --ancestry-path P` / `git log P` (all ancestors of
  P) to collect files that changed together with f before P.

## 3. Feature definition (frozen, before result inspection)

For each Sparse-omitted candidate f and the task's Sparse write set W:
- **co_change_history(f)** = count of commits in history(P) that changed both f
  and any file in W (within a window), normalized by the max over candidates.
- **history_rank_pct(f)** = percentile rank of f by co-change count among
  omitted candidates (1 = most co-changed).
- If history(P) is unavailable for a task, the feature is marked UNAVAILABLE
  (not numeric zero).

## 4. Cache-fetch evidence

- Anchor verified; 6/6 sampled task parents present as commits.
- Exact per-task history availability is computed at feature-extraction time.

## 5. No future-state leakage

- The route-b feature extractor only runs `git log P` (ancestors of P) and
  `git show P:file` (parent content). Target/future commits are never accessed.
- Provenance SHA-256 of this record is recorded in the export.