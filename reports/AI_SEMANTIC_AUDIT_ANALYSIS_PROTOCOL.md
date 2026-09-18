# AI-Assisted Semantic Audit — Analysis Protocol

**Date:** 2026-09-18
**Package:** `research/semantic_audit/ai_blinded_v1/`
**Tier:** T0/T3 data-quality (ZERO API, ZERO model calls)
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Status:** ANALYSIS COMPLETE (2026-09-18) — 10 frozen outputs validated
(2 syntax-only repairs), ingested, agreement + post-hoc sensitivity run, human
minimal spot-check generated. See
`reports/AI_SEMANTIC_AUDIT_AGREEMENT_REPORT.md`.

This document is the analysis protocol for the **independent AI-assisted
semantic plausibility audit**. It defines what the audit is, how the blinded
packages were built, how the ten rater outputs are ingested, what agreement
statistics are computed, and how the human minimal-spot-check is generated.

---

## 1. What this audit is (and is NOT)

- **IS:** an independent AI-assisted semantic-plausibility audit. Two different
  assistants (ChatGPT, Claude) independently judge, file by file, whether each
  file's relationship to the stated change is plausible (required / related /
  incidental / not determinable), plus three case-level summaries.
- **IS NOT:** human semantic gold. It does NOT replace the human audit
  (`research/semantic_audit/rater_form_A/B.csv`), it is NOT expert
  adjudication, and it is NOT a ranking or method evaluation.
- **Agreement meaning:** inter-model agreement between ChatGPT and Claude is
  descriptive evidence about assistant reliability on this task. It is NEVER
  called human agreement.

## 2. Inputs and blinding

The source data are the 25 frozen DEVELOPMENT-only human evidence packets
(`research/semantic_audit/djangocms-rc-*/`), derived from the frozen rater
form A. **None of the original packets/manifests/forms were modified.**

### 2.1 What is hidden from the raters

- method/arm name and `Route B`;
- `BM25` / `Graph` / `Composite` / `Random` / `Oracle` labels;
- candidate rank position and `top-ranked` vs `matched-random` wording;
- thesis outcomes / results and any aggregate performance metric.

### 2.2 What the raters MAY see

Only the semantic role required for interpretation:

- `historical_changed_file` — was changed in the observed commit;
- `omitted_candidate_file` — not changed, candidate in the parent universe
  (potential omission).

Plus the public intent, the parent source context (candidate universe count +
paths + parent-context edge count), and the P→T diff patch.

### 2.3 Neutral identity

- neutral case IDs: `AI-CASE-001` … `AI-CASE-025`;
- neutral row IDs: `AI-ROW-0001` … `AI-ROW-0361` (361 file-level rows:
  111 `historical_changed_file` + 250 `omitted_candidate_file`);
- neutral candidate IDs: `AI-CAND-0001` … `AI-CAND-0361`.

### 2.4 Sealed private mapping

`research/semantic_audit/ai_blinded_v1/sealed_mapping.json` maps, privately:
neutral row ID → original row ID, original arm/source, case ID, file path,
semantic role; neutral case ID → original case ID. **This file is NEVER
included in any rater package.** It is used only after both raters are frozen,
by the agreement script and the human spot-check generator.

## 3. Batches (fresh-chat isolation)

- 25 cases → 5 batches of 5 cases each per rater.
- ChatGPT: `research/semantic_audit/ai_blinded_v1/chatgpt/chatgpt_batch_01..05`.
- Claude: `research/semantic_audit/ai_blinded_v1/claude/claude_batch_01..05`.
- Different fixed seeds per rater (persisted in `preparation_manifest.json`):
  `chatgpt` seed 20260919, `claude` seed 20260920 (neutral-case/row seeds
  20260918).
- Each batch is self-contained: controlling prompt + output schema + its 5 case
  evidence files + neutral IDs only. No other batch labels/results.

## 4. Rater workflow (exact)

1. Ahmed (or an operator) opens **one fresh chat** per batch — 10 chats total
   (5 ChatGPT + 5 Claude).
2. The rater reads the batch's `AI_ASSISTED_SEMANTIC_AUDIT_PROMPT_2026-09-18.md`
   and the 5 case files under `cases/`.
3. The rater returns **one JSON document** conforming exactly to
   `AI_AUDIT_OUTPUT_SCHEMA.json` (rows + cases arrays).
4. Save the ten outputs with the exact names:
   `chatgpt_batch_01.json` … `chatgpt_batch_05.json`,
   `claude_batch_01.json` … `claude_batch_05.json`, into one directory
   (e.g. `research/semantic_audit/ai_blinded_v1/rater_outputs/`).
5. Neither rater may see the other rater's labels before freeze; the sealed
   mapping is never sent.

## 5. Ingest + agreement

```bash
python scripts/semantic_ai_audit_agreement.py <outputs_dir> \
    research/semantic_audit/ai_blinded_v1/sealed_mapping.json \
    --out reports/ai_semantic_audit_agreement_result.json
```

The script validates all 10 files against the strict schema and the expected
neutral IDs (25 cases, 361 rows), reassembles each rater's 25-case audit, then
computes:

1. exact row-level agreement (4-category nominal; no collapsing);
2. Cohen's kappa (nominal / unweighted);
3. confusion matrix;
4. agreement by label;
5. abstention rate (per rater);
6. agreement separately for `historical_changed_file` vs
   `omitted_candidate_file` rows;
7. case-level agreement for `proxy_quality`,
   `omitted_candidate_semantic_impact`, `mixed_tangled_commit`;
8. a disagreement list (for human spot-check);
9. a deterministic random sample of 10 agreement rows (seed 20260918).

### Integrity rules (fail-closed)

- exactly 10 files with the exact expected names;
- every file conforms to the schema;
- per-rater reassembly covers the expected 25 cases / 361 rows exactly once;
- no label alteration, no category collapsing, no thesis results used.

## 6. Human minimal-spot-check

After the agreement analysis exists:

```bash
python scripts/semantic_ai_audit_human_spotcheck.py \
    reports/ai_semantic_audit_agreement_result.json
```

This (re)generates `research/semantic_audit/ai_blinded_v1/human_spotcheck_form.csv`
containing all inter-model disagreements plus the deterministic 10-row
agreement sample. A human reviewer records whether the packet evidence supports
either / both / neither model label. **This is NOT expert adjudication unless
the reviewer is documented as an expert.**

## 7. Reporting rules (do NOT)

- Do NOT alter labels to increase agreement.
- Do NOT collapse categories before reporting.
- Do NOT call inter-model agreement human agreement.
- Do NOT use thesis performance results in the analysis.

## 8. Status

- Original human packets untouched: YES.
- Scientific model/API calls: ZERO.
- Packages: READY. Analysis script + tests: 19/19 PASS (16 original + 3 post-hoc).
- **Analysis (2026-09-18):** the 10 frozen rater outputs were validated exactly
  as received (`chatgpt_batch_02`/`chatgpt_batch_04` received syntax-only
  normalized copies for unescaped quotes in evidence strings; originals
  untouched); agreement run (exact 0.6981, κ 0.5579, 109 disagreements,
  deterministic 10-row agreement sample seed 20260918); POST-HOC sensitivity
  (`scripts/semantic_ai_audit_posthoc.py`) separating
  `sparse_omitted_and_historical_changed` (n=15, κ 0.17) from
  `sparse_omitted_and_outside_historical_diff` (n=235, κ 0.26); descriptive
  top-ranked-vs-random relevance per rater (ChatGPT 0.193 vs 0.099; Claude
  0.053 vs 0.008), never pooled as gold; 119-row human minimal spot-check form
  generated (109 disagreements + 10 deterministic agreement rows). Explicitly
  an **independent AI-assisted semantic-plausibility audit / model-based
  semantic sensitivity analysis**, NOT human semantic gold.
- Remaining: human review of the 119-row spot-check form; the human two-rater +
  adjudicator audit remains AWAITING_HUMAN_RATINGS.