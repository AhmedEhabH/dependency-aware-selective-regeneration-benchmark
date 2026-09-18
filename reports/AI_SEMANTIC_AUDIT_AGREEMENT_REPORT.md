# Independent AI-Assisted Semantic-Plausibility Audit — Agreement & Sensitivity Report

**Date:** 2026-09-18
**Package:** `research/semantic_audit/ai_blinded_v1/`
**Tier:** T0/T3 data-quality (ZERO API, ZERO model calls in this analysis)
**Authoring model (analysis):** openrouter/deepseek/deepseek-v4-flash-0731
**Raters:** ChatGPT and Claude (external assistants; frozen outputs ingested)
**Status:** AGREEMENT + POST-HOC SENSITIVITY + HUMAN SPOT-CHECK ARTIFACT COMPLETE

> **What this is:** an independent **AI-assisted semantic-plausibility audit** and
> **model-based semantic sensitivity analysis**. It is **NOT human semantic
> gold**, is **NOT expert adjudication**, and is **NOT a ranking or method
> evaluation**. All 10 rater outputs were treated as **frozen**; no label,
> confidence, rationale, evidence, or case judgment was altered, relabeled,
> reconciled, or exposed to the other rater.

---

## 1. Exact model

| Role | Model |
|---|---|
| Analysis authoring agent | `openrouter/deepseek/deepseek-v4-flash-0731` |
| Rater A (5 fresh-chat batches) | ChatGPT (external, batch outputs frozen) |
| Rater B (5 fresh-chat batches) | Claude (external, batch outputs frozen) |

The analysis itself performed **ZERO model/API calls**. All computations are
deterministic Python against the frozen JSON outputs and the sealed mapping.

## 2. JSON validity status for the 10 inputs (validated exactly as received)

Originals preserved untouched at
`C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\inputs\semantic\results\`.
Files were validated byte-exactly as received. Two files had **syntax-only**
defects (unescaped inner double quotes inside `evidence` string values); a
normalized copy with syntax-only repair was created alongside each and the
analysis ingested the normalized copy. No semantic content changed (verified by
full tolerant-parse round-trip equality).

| File (as received) | JSON status | Repair |
|---|---|---|
| `chatgpt_batch_01_result.json` | VALID_JSON_AS_RECEIVED | none |
| `chatgpt_batch_02_result.json` | REPAIRED_SYNTAX_ONLY | unescaped quotes in 7 evidence strings |
| `chatgpt_batch_03_result.json` | VALID_JSON_AS_RECEIVED | none |
| `chatgpt_batch_04_result.json` | REPAIRED_SYNTAX_ONLY | unescaped quotes in 2 evidence strings |
| `chatgpt_batch_05_result.json` | VALID_JSON_AS_RECEIVED | none |
| `claude_batch_01_result.json` | VALID_JSON_AS_RECEIVED | none |
| `claude_batch_02_result.json` | VALID_JSON_AS_RECEIVED | none |
| `claude_batch_03_result.json` | VALID_JSON_AS_RECEIVED | none |
| `claude_batch_04_result.json` | VALID_JSON_AS_RECEIVED | none |
| `claude_batch_05_result.json` | VALID_JSON_AS_RECEIVED | none |

Machine-readable: `reports/ai_semantic_audit_json_validation.json` (with original
SHA-256 per file). Original SHA-256s: chatgpt_01 `5cc7c3a4…`, chatgpt_02
`08cbff50…`, chatgpt_03 `90812839…`, chatgpt_04 `a76f1b67…`, chatgpt_05
`d5aeb9e7…`, claude_01 `2aca6240…`, claude_02 `15ebf124…`, claude_03
`696a6802…`, claude_04 `c3736eb1…`, claude_05 `2e9ed52d…`.

The two normalized copies were ingested under the protocol's expected names into
`research/semantic_audit/ai_blinded_v1/rater_outputs/`
(`chatgpt_batch_01..05.json`, `claude_batch_01..05.json`).

## 3. Row/case coverage

- **25 cases** (AI-CASE-001..025) per rater, reassembled from 5 batches × 5.
- **361 file-level rows** per rater (AI-ROW-0001..0361), each rated exactly once:
  - 111 `historical_changed_file` rows;
  - 250 `omitted_candidate_file` rows.
- Coverage validated **fail-closed** for both raters (missing/extra rows → error).
- **n_rated_both = 361/361** (no abstentions from either rater).

## 4. Exact agreement and Cohen's kappa (row level, 4-category nominal)

- **Exact row agreement: 0.6981** (252/361).
- **Cohen's kappa (nominal, unweighted): 0.5579** (sklearn `cohen_kappa_score`,
  independently recomputed and matching the report exactly).
- Interpretation (descriptive): **moderate** inter-model agreement; NOT human
  agreement and NOT a reliability claim for any method.

## 5. Confusion matrix and label distributions

Confusion matrix (rows = ChatGPT, columns = Claude; labels
`1_required, 2_related_optional, 3_incidental_tangled, 4_not_determinable`):

| ChatGPT \ Claude | 1_req | 2_rel | 3_inc | 4_not |
|---|---|---|---|---|
| **1_required** | 88 | 5 | 0 | 1 |
| **2_related_optional** | 0 | 8 | 22 | 8 |
| **3_incidental_tangled** | 0 | 0 | 127 | 11 |
| **4_not_determinable** | 12 | 5 | 45 | 29 |

Label distributions (marginal):

| Label | ChatGPT | Claude |
|---|---|---|
| `1_required` | 94 | 100 |
| `2_related_optional` | 38 | 18 |
| `3_incidental_tangled` | 138 | 194 |
| `4_not_determinable` | 91 | 49 |

Agreement by label (`both` / `either` / pct):

| Label | both | either | pct_both_of_either |
|---|---|---|---|
| `1_required` | 88 | 106 | 0.8302 |
| `2_related_optional` | 8 | 48 | 0.1667 |
| `3_incidental_tangled` | 127 | 205 | 0.6195 |
| `4_not_determinable` | 29 | 111 | 0.2613 |

Claude is systematically more conservative (more `3_incidental_tangled`), while
ChatGPT uses `2_related_optional` and `4_not_determinable` more. The largest
disagreement cell is ChatGPT `4_not_determinable` → Claude `3_incidental_tangled`
(45 rows).

## 6. Historical-changed vs omitted-candidate agreement

| Role | n | exact | kappa |
|---|---|---|---|
| `historical_changed_file` | 111 | **0.8468** | 0.5007 |
| `omitted_candidate_file` | 250 | **0.6320** | 0.3124 |
| Overall | 361 | 0.6981 | 0.5579 |

Agreement is **markedly higher on historical-changed rows** (files actually in
the observed diff) than on omitted-candidate rows.

## 7. Case-level agreement

| Case field | n | exact | kappa |
|---|---|---|---|
| `proxy_quality` | 25 | **0.56** | 0.2075 |
| `omitted_candidate_semantic_impact` | 25 | **0.48** | 0.1096 |
| `mixed_tangled_commit` | 25 | **0.68** | 0.4536 |

Case-level agreement is weak-to-moderate; the `omitted_candidate_semantic_impact`
judgment has the lowest agreement (0.48 exact, kappa 0.11).

## 8. POST-HOC sensitivity: omitted-role interpretation (frozen labels NOT altered)

Some rater rationales interpret "omitted" as "absent from the historical diff"
(e.g. "the row is marked omitted, but the supplied diff contains a change to this
same file"). The 250 `omitted_candidate_file` rows were therefore partitioned by
whether the **same file also appears in that case's historical changed set**:

| Partition | n | exact | kappa |
|---|---|---|---|
| `sparse_omitted_and_historical_changed` (file also in historical diff) | 15 | 0.6000 | 0.1667 |
| `sparse_omitted_and_outside_historical_diff` (file not in historical diff) | 235 | 0.6340 | 0.2605 |

The 15 ambiguous rows (whose file IS in the historical diff) show the *lowest*
kappa (0.17) — consistent with raters applying inconsistent "omitted"
interpretations on exactly those rows. Frozen labels were **not** altered for
this analysis; the partitions are reported as a clearly labeled post-hoc
sensitivity check. Machine-readable:
`reports/ai_semantic_audit_posthoc_result.json`.

## 9. Top-ranked vs matched-random semantic enrichment (descriptive, per rater)

**Definition (no gold claimed):** among `omitted_candidate_file` rows OUTSIDE the
historical diff (n=235), "AI-rated semantic relevance" = label
`1_required` or `2_related_optional`. ChatGPT and Claude are reported separately;
they are **never pooled** into human ground truth.

| Rater | Arm | n | relevant | rate_relevant |
|---|---|---|---|---|
| ChatGPT | `matched_random_omitted` | 121 | 12 | **0.0992** |
| ChatGPT | `top_ranked_omitted` | 114 | 22 | **0.1930** |
| Claude | `matched_random_omitted` | 121 | 1 | **0.0083** |
| Claude | `top_ranked_omitted` | 114 | 6 | **0.0526** |

**Descriptive direction (both raters, same sign):** top-ranked omitted candidates
outside the historical diff carry a **higher** AI-rated relevance rate than
matched-random omitted candidates (ChatGPT 0.193 vs 0.099; Claude 0.053 vs
0.008). Absolute rates are low and the signal is descriptive only; this is a
**model-based semantic sensitivity observation**, NOT human gold and NOT a
method-evaluation claim.

## 10. Human minimal-spot-check workload

Generated artifact:
`research/semantic_audit/ai_blinded_v1/human_spotcheck_form.csv` (119 rows):

- **109 inter-model disagreements** (all rows where labels differ; none were
  abstentions) — the complete disagreement list.
- **10 deterministic agreement-sample rows** (seed `20260918`), labels blanked
  for the human reviewer.

The 10 deterministic agreement rows:

| neutral_row_id | role | agreed label |
|---|---|---|
| AI-ROW-0333 | historical_changed_file | 1_required |
| AI-ROW-0110 | omitted_candidate_file | 3_incidental_tangled |
| AI-ROW-0328 | omitted_candidate_file | 4_not_determinable |
| AI-ROW-0055 | historical_changed_file | 2_related_optional |
| AI-ROW-0212 | omitted_candidate_file | 4_not_determinable |
| AI-ROW-0018 | historical_changed_file | 3_incidental_tangled |
| AI-ROW-0209 | historical_changed_file | 1_required |
| AI-ROW-0342 | omitted_candidate_file | 3_incidental_tangled |
| AI-ROW-0150 | omitted_candidate_file | 3_incidental_tangled |
| AI-ROW-0123 | omitted_candidate_file | 3_incidental_tangled |

This is a **minimal human spot-check**, not expert adjudication. No human
judgments were fabricated in this closure.

## 11. Limitations and permitted scientific wording

**Limitations:**
- Inter-model agreement is **NOT** human agreement; it is descriptive evidence
  about assistant reliability on this task.
- ChatGPT/Claude outputs are AI judgments, not semantic gold; they do not
  replace the human two-rater + adjudicator audit (`rater_form_A/B_filled.csv`),
  which remains **AWAITING_HUMAN_RATINGS**.
- The two syntax repairs changed only JSON delimiters (unescaped quotes); labels
  and rationales are unaltered, but files were not byte-identical to the frozen
  originals at the evidence-string level (verified content-preserving).
- Post-hoc partitions (Section 8) and relevance rates (Section 9) are
  **post-hoc and descriptive**, not preregistered; small partition sizes
  (n=15) limit precision.
- No inference about the thesis methods/arms follows from any number here.

**Permitted wording:** "Inter-model agreement (ChatGPT vs Claude) was 0.698
exact / κ=0.56 on 361 blinded file-level judgments; agreement was higher on
historical-changed rows (0.847) than omitted-candidate rows (0.632); a post-hoc
omitted-role sensitivity check and a descriptive top-ranked-vs-random
semantic-relevance observation were reported per rater. These are AI-assisted
descriptive results, not human semantic gold."

**Forbidden wording:** claiming human agreement, gold, expert adjudication,
method/arm ranking, or any causal validity for the model-based rates.

## 12. Tests and independent audit

- **19/19 unit tests PASS** (`tests/unit/test_semantic_ai_audit.py`): 16
  pre-existing prepare/agreement/spot-check tests + 3 new post-hoc tests
  (partition, relevance split, main-writes-result).
- **Independent statistical audit:** exact agreement, kappa, confusion matrix,
  label marginals, disagreement count, and the deterministic 10-row sample were
  recomputed independently (sklearn) and match the report exactly
  (`n_rated_both=361`, kappa `0.557906…`, CM identical, sample identical).
- **Second independent audit (pure-stdlib, no sklearn):** all statistics
  recomputed from the raw frozen outputs + sealed mapping using only the
  standard library — row-level, case-level, role split, post-hoc partitions and
  relevance rates all match the report; artifact
  `reports/ai_semantic_audit_independent_audit.json` (PASS_ALL_CHECKS).
- Deterministic spot-check seed fixed (`20260918`); reproducible.
- Ruff clean on changed Python files; mypy strict clean on the new post-hoc
  script; py_compile clean.

## 13. Git / tag / export

See final closure report fields (branch, merge, tag, LIGHT export) in
`PROGRESS.md` / the closure report generated at the end of this mission.

## 14. ONE next scientific action

Deliver the 119-row minimal human spot-check form (Section 10) to the human
reviewer as the *first* bounded check of inter-model disagreement, alongside the
still-required human two-rater + adjudicator semantic audit (which remains the
gold and remains **AWAITING_HUMAN_RATINGS**).