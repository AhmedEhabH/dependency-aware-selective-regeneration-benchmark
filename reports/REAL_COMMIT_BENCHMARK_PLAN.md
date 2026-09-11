# Real-Commit Benchmark Plan

**Date:** 2026-09-11
**Purpose:** reduce author-created requirement/gold bias by proposing an
automated historical-commit benchmark.

---

## 1. Problem being addressed

The current six djangoCMS cases are **author-curated**:
- the researcher authored the requested changes, and
- the gold impacted-file set was also manually defined.

This creates a risk of author-created requirement/gold bias. Five repetitions
of one scenario are **NOT** equivalent to five independent changes.

## 2. Proposed design: automated historical-commit benchmark

For an **eligible upstream commit**:

| Component | Source |
|---|---|
| Parent commit | pre-change repository state |
| Commit message / PR / linked issue | change intent |
| Actual changed production files | **OBSERVED CHANGE-SET PROXY** |

The changed-file set is used as a **proxy** for the impact set. It is NOT
called perfect semantic ground truth — a commit's diff can be incomplete,
over-inclusive, or contain incidental edits. Use the phrase
**OBSERVED CHANGE-SET PROXY** throughout.

### Automated filters (apply before selection)

Exclude commits that are:
- merge commits
- formatting-only changes
- tests-only changes
- migrations-only changes
- generated/vendor files only
- very large sweeping refactors (unbounded diffs)
- commits lacking meaningful natural-language intent (empty / bot-only messages)

Require **production-source changes**. Deduplicate tightly related commits
(e.g., a PR with several commits counts as one change).

## 3. Recommended scope

- **djangoCMS: 20–30 independent real changes** (primary corpus).
- **Todo: retain only as small/component sanity evidence** (its changes are
  too small and component-like to generalize).
- **Possible second project:** 15–30 independent real changes **only if the
  supervisor requires stronger cross-project external validity**.

## 4. Why repetitions are not independent changes

5 repetitions of one scenario measure **within-case model variation** under a
single requirement + single gold. Independent changes measure **cross-case
variation** across different requirements and different observed change-sets.
Only the latter provides evidence that the approach generalizes beyond the
author's curated cases.

---

## D10 — Minimum evidence size guidance

There is **NO universal magic number of changes** that mathematically
guarantees generalization. Distinguish three levels of independence:

1. **model repetitions** — same case, same gold, repeated inference;
2. **independent requirement changes** — different requirements, same repo;
3. **independent repositories** — different codebases.

Pragmatic tiers (study-design guidance, NOT statistical laws):

| Tier | Size | What it supports |
|---|---|---|
| Mechanism demonstration | ~6–10 curated changes | exposes a mechanism or problem; **weak** for broad generalization |
| Stronger single-project evidence | ~20–30 independent real changes | meaningful single-project evidence |
| Broader cross-project evidence | add ≥1 materially different repo with ~15–30 independent real changes | stronger cross-project external validity, if time allows |

Present these as pragmatic guidance, not as a guarantee of generalization.