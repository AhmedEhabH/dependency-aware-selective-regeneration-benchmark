# ISSUE_GROUNDED_INTENT_HEADROOM - T3 Impact Declaration + Frozen Protocol (2026-09-20)

**Status:** FROZEN BEFORE OUTCOME INSPECTION. This document records the exact
scientific question, paired-population rule, reference-resolution rule,
temporal-validity rule, corpus-freeze rule, ranking arms, metric definitions,
primary gate, and expected artifacts for the ISSUE_GROUNDED_INTENT_HEADROOM
mission BEFORE any issue-ranking outcome is inspected.

**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Mission:** ISSUE_GROUNDED_INTENT_HEADROOM
(does a real pre-change problem description fix the information bottleneck?)
**Tier:** T3 (new signal / intent headroom test; NO new final policy)
**API budget:** HARD ceiling **$0.05** incremental. Only GitHub metadata
retrieval (free) + Qwen QUERY embeddings (issue-title/body) are allowed.
NO corpus re-embed. Verify live price before ANY Qwen call.
**Sealed data:** NOT opened. Stage 5 stays PAUSED and SEALED. No new
final-policy classifier. No V1/V2 tuning. No Sparse change.

---

## 0. Preserved frozen scientific history (NOT rewritten, NOT reinterpreted)

- `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED` - preserved exactly.
- `CALIBRATED_SET_SELECTION_V1_FAIL` - preserved exactly as a frozen negative.
- `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL` - preserved exactly.
- Current final DEVELOPMENT point estimates (unchanged, descriptive):
  djangoCMS Sparse F1 ~= 0.318, V1 ~= 0.334, V2 ~= 0.345 (V2 gate FAIL,
  Delta-F1 CI crosses zero); Saleor Sparse ~= 0.261, V1 ~= 0.336, V2 ~= 0.348
  (V2 PASS on Saleor).
- Stage 5 remains SEALED. This mission does NOT decide the final
  impact-localization policy; it tests whether a richer, temporally valid
  pre-change issue description changes the quality of the localization
  signals themselves.

## 1. Scientific question and scope

Primary question: does replacing the short commit-message intent proxy with a
temporally valid pre-change GitHub issue description materially improve
localization signal on the SAME already-exposed DEVELOPMENT tasks?

This is an INFORMATION HEADROOM test on the DENSE-RANKING / RECOVERY signal.
It is NOT a new final policy, NOT Stage 5, NOT a V1/V2 tune. It tests whether
the commit-message proxy was suppressing useful localization information that a
realistic pre-change issue description would expose.

## 2. Primary alternative intent (issue-grounded)

- ARM I intent = GitHub ISSUE TITLE + "\n" + GitHub ISSUE BODY.
- Forbidden as primary intent: PR diff, PR changed-file list, PR patch, review
  comments, later issue comments, commit diff, target changed paths, generated
  solution summaries, PR body.
- ARM M intent = the existing frozen commit-message intent (unchanged).

## 3. Reference resolution (deterministic, per DEV task)

For every DEVELOPMENT task's commit message:
1. parse `#NNNN`-style references (3-6 digit numbers);
2. resolve the referenced object in the SAME repository (djangocms ->
   `django-cms/django-cms`; saleor -> `saleor/saleor`);
3. distinguish ISSUE vs PULL REQUEST via the GitHub object type;
4. if directly an issue: candidate issue = that issue;
5. if a PR: the PR itself is NOT textual intent. A linked closing issue
   (via GitHub linked-issues, e.g. GraphQL `closingIssuesReferences` or the
   PR body closing-reference) is used ONLY as dataset-construction linkage,
   subject to all temporal rules below.

Record separately per task (mutually exclusive provenance category):
- `DIRECT_ISSUE` - a referenced object is directly an issue;
- `PR_ONE_LINKED` - referenced object(s) are PRs with exactly one linked
  closing issue (total over resolved refs);
- `PR_MULTI_LINKED` - referenced object(s) are PRs with multiple linked issues;
- `PR_NO_LINKED` - referenced object(s) are PRs with no linked issue;
- `UNRESOLVED` - reference could not be resolved (404 / network fail / no match).

For the PRIMARY clean analysis with multiple linked issues: concatenate the
valid issue title/body in deterministic ascending issue-number order and count
this separately. Do not silently choose one.

## 4. Temporal validity (STRICT)

For every candidate issue retrieve: number, created_at, updated_at, title,
body, repository, URL. Define target time from the target commit
(`target_commit_time` in the case manifest).

PRIMARY TEMPORALLY CLEAN requires:
- `issue.created_at < target_commit_time`
- AND `issue.updated_at <= target_commit_time`

If `updated_at > target_commit_time`, the retrieved title/body may contain
post-target edits and cannot be proven to equal the pre-change text ->
`TEMPORALLY_UNCERTAIN`, EXCLUDED from the PRIMARY clean analysis, reported
descriptively only. Issue comments are NOT used in the primary analysis.

## 5. Frozen issue corpus (before ranking evaluation)

Save a compact frozen corpus (JSON) with per-case:
- case_id, repository, provenance category, issue ID(s),
- created_at / updated_at per issue, exact title/body text,
- retrieval timestamp, SHA256 of normalized text, temporal-clean flag,
- target_commit_time (for audit).
NO secrets/tokens in the artifact. Compute a corpus-level SHA256 manifest.

## 6. PRIMARY PAIRED POPULATION

Primary scientific population = DEVELOPMENT tasks with TEMPORALLY CLEAN
issue-grounded intent. The SAME task IDs are used for both arms (paired).

- ARM M: frozen commit-message intent.
- ARM I: issue title + issue body.
Report djangoCMS n and Saleor n, plus the fraction of each full DEV repository
covered by the clean issue-grounded population.

## 7. Dense-ranking arms (frozen, NO ranking-method changes)

Reuse the existing frozen Qwen3-Embedding-8B corpus/code-unit embeddings. Do
NOT re-embed the code corpus.

- ARM M: reuse the existing frozen original-message rankings (the frozen
  full-file-score dense ranks per task per realization).
- ARM I: compute ONLY the new issue-query embedding (title+body) per clean
  task, against the SAME frozen code-unit embeddings, SAME file-MAX
  aggregation, SAME file filters, SAME similarity (cosine), SAME tie-break,
  SAME full-universe dense ranking.

If A/B corpus realizations exist, evaluate issue-query robustness against BOTH
existing realizations without redesign.

## 8. DENSE HEADROOM METRICS (frozen)

For ARM M and ARM I on the SAME clean paired tasks:
- target-file Recall@1 / @3 / @5 / @10 / @20
  Recall@K = (# proxy-changed target files ranked within top K) / (# proxy
  changed target files)
- task-level target coverage@K (fraction of tasks with >=1 proxy target in
  top K)
- median target-file rank; mean reciprocal rank where well-defined
- rank distribution; top-K candidate precision
- exact rank movement per target file
Task-paired bootstrap >=10,000 resamples for primary deltas (seed 20260920).

## 9. DEEP-DENSE-MISS RESCUE (frozen definition)

Use the existing frozen V1/V2 deep-dense-miss definition:
`DEEP_DENSE_MISS` = historical-proxy positive file that remains a V1 false
negative AND is outside the V1 frozen candidate universe (Sparse UNION dense
top-20). For deep misses belonging to the PRIMARY paired population, report:
- original-message dense rank;
- issue-intent dense rank;
- number entering top1 / top3 / top5 / top10 / top20.
`IssueDeepFNRescue@20` = (# previously deep dense misses moved into top20 by
issue intent) / (# eligible deep dense misses).

## 10. HISTORICAL EPISODE RETRIEVAL ARM (frozen)

Reuse the frozen parent-only historical episode corpus and BM25 method. Do NOT
change history window, BM25 implementation, or top-K.
- ARM M: commit-message query (frozen).
- ARM I: issue-title/body query.
Measure: historical episode retrieval relevance to proxy target files,
DeepFNRecovery via retrieved historical episodes, number of useful historical
files introduced, candidate precision. NO model fitting.

## 11. PATH-MENTION SENSITIVITY (descriptive only, pre-registered)

For each clean issue text detect literal mentions of:
- exact file paths; basenames; module/class/function identifiers where
  deterministically detectable.
Report separately:
- A: issue texts containing an exact/basename target-file mention;
- B: issue texts without target-file path mentions.
Do NOT delete path-mentioned tasks from the primary result.

## 12. INTENT-LENGTH ANALYSIS (descriptive only)

Use the already-frozen buckets <=6 / 7-15 / >15 words for commit-message
intents; also report issue-text token/word lengths. Do NOT use intent length
as a feature or gate. Evaluate descriptively whether short-message tasks
receive larger rank improvements from issue grounding.

## 13. PRIMARY HEADROOM GATE (frozen BEFORE outcome inspection)

Primary metric: target-file Recall@20.

`ISSUE_GROUNDED_INTENT_SIGNAL_SUPPORTED` requires, on BOTH repositories in the
temporally-clean paired population:
- A. Recall@20(issue) > Recall@20(message)
- B. task-paired 95% CI lower bound for Delta Recall@20 > 0
- C. median target-file rank improves or stays equal
- D. no leakage / temporal-validity violation.

If only one repo passes -> `ISSUE_GROUNDED_INTENT_SIGNAL_MIXED`.
If neither passes -> `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED`.
No post-hoc K choice. No gate redefinition after results.

## 14. Forbidden (expensive / irreversible)

NO opening sealed outcomes; NO Stage 5; NO new final-policy classifier; NO
V1/V2 feature changes; NO code-unit re-embedding; NO SweRank / LocAgent /
Agentless / JEPA / energy-model training; NO cloning new large repositories.
Stop before any paid call if projected cost > $0.05.

## 15. Validation

Targeted pytest for: reference parsing, repo-local resolution, temporal-clean
rule, updated_at guard, no PR text, no comments, no diff, corpus hashing,
paired task identity, frozen-corpus embedding reuse, unchanged ranking
aggregation, Recall@K formulas, task-paired bootstrap, path-mention detection,
sealed-data guard. Independent audit must NOT import the main analyzer.
Run ruff, py_compile, git diff --check on changed files.

## 16. Expected artifacts

- research/issue-grounded-intent-headroom/* (corpus, ranks, metrics, JSON)
- reports/ISSUE_GROUNDED_INTENT_HEADROOM_2026-09-20.md
- reports/LOCALIZATION_COMPARABILITY_MAP_2026-09-20.md
- reports/issue_grounded_intent_freeze.json + audit.json
- src/benchmark/issue_grounded/ + tests/unit/test_issue_grounded_*.py
- governance: 00_CURRENT_RESEARCH_STATE.md, PROGRESS.md, DECISIONS.md,
  docs/RESEARCH_JOURNEY.md, roadmap, literature ledger.

## 17. Future roadmap notes (document only, NOT executed)

- ENERGY_BASED_CHANGE_SET_COMPLETION: score complete predicted file SETS
  (E(q,S) = -sum unary -sum pairwise + size penalty), ref LeCun et al. EBL.
  Pairwise evidence: parent-visible co-change, parent dependency adjacency,
  negative historical association. NO novelty claim; dedicated literature
  review required before execution.
- JEPA / world model: supervisor-discussion direction only; current
  highest-value question is information quality, not model capacity.
