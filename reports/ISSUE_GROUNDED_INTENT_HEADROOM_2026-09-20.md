# ISSUE-GROUNDED INTENT HEADROOM - Human-Readable Report (2026-09-20)

**Mission:** ISSUE_GROUNDED_INTENT_HEADROOM
**Verdict:** `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED` (frozen negative)
**Tier:** T3 (information-headroom test; no new final policy, no Stage 5)
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Frozen protocol:** `docs/ISSUE_GROUNDED_INTENT_HEADROOM_IMPACT_DECLARATION_2026-09-20.md`
**Freeze JSON:** `reports/issue_grounded_intent_freeze.json`
**Artifacts:** `research/issue-grounded-intent-headroom/*`

---

## 1. Plain-language answers

**1. Is the commit-message proxy information-poor?**
Yes in a descriptive sense: commit messages are post-implementation summaries
(~median 11 words; 22 mean). But this mission could not demonstrate that a
real pre-change issue description materially improves the dense localization
signal on the PRIMARY clean paired population. On the 12 evaluated djangoCMS
tasks, Recall@20 point-rises (0.6875 -> 0.7188) but the paired 95% CI crosses
zero and median rank worsens. On Saleor the temporally-clean population is
EMPTY (0 tasks), so no paired evaluation is possible there.

**2. How many DEV tasks have resolvable issues?**
From 174 djangocms + 149 Saleor DEV tasks:
- djangocms: 99/174 commit messages contain `#NNNN` references (verified by
  recomputation; equals the prior descriptive claim).
- Saleor: 112/149 contain references (recomputed; equals the prior claim).
- References resolved to: DIRECT_ISSUE 28 (djangocms 27 / saleor 1),
  PR_ONE_LINKED 30 (16/14), PR_MULTI_LINKED 8 (5/3), PR_NO_LINKED 145 (51/94),
  NO_REFERENCE 112 (75/37). Rows with a resolvable issue-grounded candidate:
  djangocms 48 tasks, saleor 18 tasks.

**3. How many are temporally clean?**
Under the strict rule (created_at < target AND updated_at <= target):
- djangoCMS: **12 tasks** (15 clean issues across them) out of 174 (6.9%).
- Saleor: **0 tasks** out of 149 (0%).
The dominant exclusion is `updated_at > target_commit_time` (GitHub issues are
frequently edited/touched later; many are closed/updated a few seconds after
the merge commit). 36 djangocms + 18 saleor tasks had candidates but NONE clean.

**4. How much longer/richer are issues than commit messages?**
Vastly: issue-text median 174 words (mean 209.6) vs commit-message median 11
words (mean 22.0). Issue-text length buckets: >15 words 11/12, 7-15 words 1/12.
Issues are ~16x longer than the messages that reference them.

**5. Does issue text move true files upward?**
On the 12-task clean djangocms population: mixed. Target-file rank movement per
file: 13 improved / 15 worsened / 4 unchanged (realization A). Mean change -4.6
(better) but median change 0.0. Deep dense misses (message rank >= 40) moved
up: e.g. ranks 135->64, 128->65, 92->51, 38->11.

**6. Recall@1/3/5/10/20 before vs after (djangoCMS clean paired n=12, pooled):**
| K | Message (ARM M) | Issue (ARM I) | Delta |
|---|---|---|---|
| 1 | 0.1875 | 0.1875 | 0.0000 |
| 3 | 0.3438 | 0.3438 | 0.0000 |
| 5 | 0.4688 | 0.4688 | 0.0000 |
| 10 | 0.5938 | 0.5625 | -0.0312 |
| 20 | 0.6875 | 0.7188 | **+0.0312** |
Task-paired bootstrap (10,000 resamples, seed 20260920) for Delta Recall@20:
point **+0.0201**, 95% CI **[-0.0875, +0.1375]** -> crosses zero.
Identical in realization A and B.

**7. How many deep dense misses enter top20?**
Deep dense misses (frozen V1 definition) in the PRIMARY clean population:
djangoCMS 7 eligible (Saleor 0). Issue intent moved **1/7 (0.143) into top20**
(`IssueDeepFNRescue@20 = 0.143`); none entered top1/3/5/10. On the message arm
the same deep misses sat at ranks 38-135; issue intent reduced several to 11-71
but only one crossed the top-20 line.

**8. Does history retrieval also improve?**
NO. The historical-episode BM25 arm (frozen top-10, parent-only history):
- djangocms clean tasks: ARM M candidate precision **0.0885** (113 episode
  files), ARM I candidate precision **0.0431** (116 files).
Issue queries retrieve more episode files but with HALF the proxy precision vs
commit messages on this small sample. Saleor clean population empty -> n/a.

**9. How much gain comes from explicit path mentions?**
Descriptive split (clean djangocms tasks):
- With an exact/basename target-file mention in the issue text (4 tasks):
  Recall@20 message 0.5833 -> issue 0.5833 (no change).
- Without mention (8 tasks): Recall@20 message 0.7500 -> issue 0.8000 (+0.05).
So the observed Recall@20 rise is NOT explained by trivial explicit path
disclosure; the small gain lives in the without-mention group. 4/12 clean issue
texts contain at least one exact/basename target-file mention.

**10. Is the signal consistent across djangoCMS and Saleor?**
NO. djangoCMS has a usable (12-task) clean population with a point Rise@20 but a
statistically null CI; Saleor has a ZERO-task clean population, so no paired
comparison at all. The gate requires BOTH repositories.

**11. Does this justify a full issue-grounded pipeline?**
NO under the frozen gate. Verdict = `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED`.
Reason (djangoCMS): criterion A passes (Recall@20 issue 0.7188 > message
0.6875), criterion B FAILS (CI lower -0.0875 <= 0), criterion C FAILS (pooled
median target rank 6.0 -> 7.5, i.e. worsened), criterion D passes (temporally
clean by construction; no PR text/comments/diffs used). Saleor has no clean
population -> cannot demonstrate support. The commit-message proxy was NOT
demonstrated to be suppressing useful localization information that a real
pre-change issue description would expose.

**12. What does this NOT prove?**
- It does NOT prove issues are useless for localization generally.
- It does NOT prove the commit-message proxy is information-rich.
- It does NOT say issue text helps no task: 5/12 djangocms clean tasks improved
  their median rank, and the only top-20 rescue came from issue text.
- It does NOT claim any comparison with LocAgent/ROSE/Agentless headliners
  (see comparability map).
- It does NOT open sealed sets, run Stage 5, or fit a new policy.
- It does NOT claim the strict `updated_at` rule is the only sensible temporal
  rule; it is the frozen rule and its consequence is a small clean population.

---

## 2. Detailed results

### 2.1 Reference verification (recomputed, not copied)
| Repo | DEV tasks | tasks with `#NNNN` | refs total | direct issue | PR-1-link | PR-multi | PR-no-link | no ref |
|---|---|---|---|---|---|---|---|---|
| djangocms | 174 | 99 (0.569) | 138 | 27 | 16 | 5 | 51 | 75 |
| saleor | 149 | 112 (0.752) | 124 | 1 | 14 | 3 | 94 | 37 |
| total | 323 | 211 | 262 | 28 | 30 | 8 | 145 | 112 |

The prior descriptive claim (99/174, 112/149) is reproduced exactly. 257
distinct repository-local issue/PR objects were resolved through the GitHub
API; none of the referenced PR texts became intent (linked-closing-issue
retrieval only).

### 2.2 Temporally clean population
| Repo | tasks with >=1 candidate | tasks with >=1 CLEAN issue | clean issues |
|---|---|---|---|
| djangocms | 48 | **12** | 15 |
| saleor | 18 | **0** | 0 |

Primary paired population = **djangocms 12**, **saleor 0** (fraction covered:
djangocms 12/174 = 0.069, saleor 0/149 = 0.000).

### 2.3 Dense ranking arms (frozen Qwen3-Embedding-8B corpus; ARM M frozen,
ARM I = new issue-query embeddings only, $0.000057)

djangoCMS clean paired (n=12), pooled Recall@K:

| K | ARM M | ARM I | macro M | macro I |
|---|---|---|---|---|
| 1 | 0.1875 | 0.1875 | 0.2146 | 0.2771 |
| 3 | 0.3438 | 0.3438 | 0.3771 | 0.3729 |
| 5 | 0.4688 | 0.4688 | 0.5194 | 0.4979 |
| 10 | 0.5938 | 0.5625 | 0.6097 | 0.5528 |
| 20 | 0.6875 | 0.7188 | 0.6889 | 0.7090 |

Coverage@20 (tasks with >=1 proxy in top20): M 0.8333, I 0.8333.
MRR: M 0.3510, I 0.3750. Per-task mean median rank: M 21.54, I 18.92
(improving) BUT the gated pooled median rank: M 6.0 -> I 7.5 (worsening).

### 2.4 Primary gate (frozen, djangocms clean n=12)
| Criterion | Value | Pass? |
|---|---|---|
| A Recall@20(I) > Recall@20(M) | 0.7188 > 0.6875 | YES |
| B paired 95% CI lower > 0 | -0.0875 | NO |
| C median target-file rank improves/equal | 6.0 -> 7.5 | NO |
| D no leakage / temporal-validity | clean-by-construction | YES |
djangoCMS REPO_FAIL. Saleor: no clean population -> cannot pass.

**Overall verdict: `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED`** (identical
in realizations A and B).

### 2.5 Deep-dense-miss rescue
| Repo | deep misses (frozen) | in primary population | rescue@20 |
|---|---|---|---|
| djangocms | 199 | 7 | 0.1429 (1/7) |
| saleor | 177 | 0 | n/a |

Moved examples: `cms/menu_bases.py` 38->11, `cms/middleware/page.py` 92->51,
`cms/management/commands/subcommands/base.py` 135->64.

### 2.6 Historical episode retrieval arm (frozen BM25 top-10, parent-only)
| Repo | arm | episode files | proxy hits | candidate precision |
|---|---|---|---|---|
| djangocms (clean 12) | M | 113 | 10 | 0.0885 |
| djangocms (clean 12) | I | 116 | 5 | 0.0431 |

Issue queries lower episodic candidate precision on this sample.

### 2.7 Path-mention sensitivity (descriptive)
- 4/12 clean issue texts contain an exact/basename target-file mention.
- With mention: Recall@20 M 0.5833 / I 0.5833.
- Without mention: Recall@20 M 0.7500 / I 0.8000.

### 2.8 A/B corpus-realization robustness (ARM I)
Exact proxy-rank agreement between realization A and B = 0.9062 (29/32 proxy
files). Headroom gate identical in A and B.

### 2.9 Cost / reversibility
- GitHub API calls (REST + GraphQL, cached): ~260+ objects resolved; free.
- Qwen query tokens: 5,662 prompt tokens ($0.01/M verified live on 2026-09-20).
- Qwen query cost: **$0.000057** (hard ceiling $0.05; projected $0.00004).
- Wall time: resolution ~30 min (flaky network retries), ARM I ~4 s.
- Frozen issue-corpus size: 323 records, 56.6 KB JSON; SHA-256
  `d43987b4f9f75ace3c26597002526d0f6579c9554cc3229425648d37ad135d0f`.
- No corpus re-embed, no model download, no sealed evidence.

---

## 3. Governance

- **Verdict:** `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED` (frozen negative).
- Preserved exactly: `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`,
  `CALIBRATED_SET_SELECTION_V1_FAIL`, `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`.
- Stage 5 stays PAUSED/SEALED; no new final policy; V1/V2/Sparse untouched.
- Next scientific action (documented, NOT executed): should a future mission
  revisit issue grounding, it must (a) decide the temporal rule deliberately
  (the strict `updated_at` rule produces a near-empty Saleor population),
  (b) evaluate on a larger pre-registered clean corpus, and (c) keep the
  comparability-map discipline. No full issue-grounded pipeline is justified
  by this evidence.

## 4. Validation
- 27/27 new unit tests PASS (`tests/unit/test_issue_grounded.py`).
- Independent audit **12/12 PASS** (`reports/issue_grounded_audit.json`);
  recomputes every claim WITHOUT importing the analyzer.
- ruff clean; py_compile clean; `git diff --check` clean on changed files.