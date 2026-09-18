# AI-Blinded Semantic Audit Package (ai_blinded_v1)

**Created:** 2026-09-18
**Purpose:** independent AI-assisted semantic-plausibility audit of 25
DEVELOPMENT-only real-commit cases, fully blinded (no method/arm/ranking
leakage).
**ZERO scientific model/API calls were used to build this package.**
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

## What this is

Two assistants (ChatGPT, Claude) independently judge, per file, whether each
file is semantically plausible for the stated change (1_required /
2_related_optional / 3_incidental_tangled / 4_not_determinable) plus three
case-level summaries. This is an **independent AI-assisted semantic plausibility
audit** — it does NOT replace human semantic gold.

## Layout

```
ai_blinded_v1/
  AI_ASSISTED_SEMANTIC_AUDIT_PROMPT_2026-09-18.md  controlling audit prompt
  AI_AUDIT_OUTPUT_SCHEMA.json                      strict JSON output schema
  preparation_manifest.json                        seeds + per-batch hashes
  sealed_mapping.json                              PRIVATE mapping (never sent)
  cases/AI-CASE-001..025.json                      neutral evidence (25 cases)
  chatgpt/chatgpt_batch_01..05/                    5 fresh-chat batches
  claude/claude_batch_01..05/                      5 fresh-chat batches
  human_spotcheck_form.csv                         placeholder (generator fills)
```

## Blinding

Hidden from raters: method/arm name, Route B, BM25/Graph/Composite/Random/
Oracle labels, rank position, top-ranked vs matched-random wording, thesis
outcomes, any aggregate metric. Raters see only neutral IDs and the semantic
role: `historical_changed_file` / `omitted_candidate_file`.

## Exact next action (for Ahmed)

1. Run each of the 10 batches in a **separate fresh chat** (5 ChatGPT + 5
   Claude) using the batch folder as the only input. — **DONE (2026-09-18)**;
   frozen outputs returned.
2. Save the ten JSON outputs exactly as:
   `chatgpt_batch_01.json` … `chatgpt_batch_05.json`,
   `claude_batch_01.json` … `claude_batch_05.json` into one directory. —
   **DONE:** received under `rater_outputs/` (2 syntax-only normalized copies).
3. Ingest + agreement:
   `python scripts/semantic_ai_audit_agreement.py <outputs_dir> sealed_mapping.json`
   — **DONE:** exact 0.6981 / κ 0.5579 (see report).
4. Human spot-check:
   `python scripts/semantic_ai_audit_human_spotcheck.py reports/ai_semantic_audit_agreement_result.json`
   — **DONE:** 119-row form generated (109 disagreements + 10 agreement rows).

## Status (2026-09-18)

**ANALYSIS COMPLETE.** 10 frozen outputs validated (2 syntax-only repairs),
ingested, agreement + post-hoc sensitivity + human minimal spot-check
delivered (ZERO API). This is an **independent AI-assisted semantic-plausibility
audit / model-based semantic sensitivity analysis**, NOT human semantic gold.
See `reports/AI_SEMANTIC_AUDIT_AGREEMENT_REPORT.md`.

See `reports/AI_SEMANTIC_AUDIT_ANALYSIS_PROTOCOL.md` for the full runbook.