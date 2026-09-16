# Semantic-Proxy Audit Protocol

**Date:** 2026-09-16 evening
**Tier:** T2/T3 data-quality
**Purpose:** quantify how far the OBSERVED CHANGE-SET PROXY is from semantic
impact gold, via later HUMAN adjudication of a stratified DEVELOPMENT-only
sample. AI/machine preparation is allowed for evidence packets; it is NEVER
called semantic gold.

**Status:** PROTOCOL FROZEN. Evidence-packet preparation for a development-only
sample is implemented in `scripts/prepare_semantic_audit_packets.py`.

---

## 1. Why

All localization claims in the thesis are scoped to historical-file recovery
(P→T changed production files) because the observed diff is a proxy, not
semantic impact gold. This protocol prepares the evidence needed to later
quantify:
- what fraction of changed production files were SEMANTICALLY NECESSARY for the
  stated change;
- whether semantically impacted-but-unchanged production files exist;
- whether the commit is mixed with incidental refactor/cleanup.

## 2. Sample (stratified DEVELOPMENT-only)

- Stratify the V2 DEV_TRAIN development cases by proxy-size bucket and year,
  and select a deterministic sample of **20–30 tasks** (seed 20260916).
- FORBIDDEN: V2 INTERNAL_TEST, V2 RESERVE, and any HELD_OUT_TEST case.
- Sample selection is deterministic and reproducible from the split proposal.

## 3. Evidence packet per case

Each packet contains (parent-visible public + the P→T diff for adjudication only):
- public intent (normalized commit message);
- parent source context (candidate universe metadata);
- the P→T diff (name-status + patch) — used for adjudication, never as model
  input for the localization method;
- changed production files (the observed proxy);
- candidate-universe metadata (count, paths, graph edges).

## 4. Human questions

For each changed production file:
1. Was this file SEMANTICALLY NECESSARY for the stated change?
2. Is there evidence of a semantically impacted but UNCHANGED production file
   (a potential true omission the proxy would miss)?
3. Is the commit mixed with incidental refactor / cleanup / unrelated change?

## 5. Annotation form + schema

- Form fields: case_id, file, question_1..3, evidence refs, reviewer id,
  confidence, notes.
- Adjudication schema (JSON): per-file verdicts + a per-case summary.
- Reviewer instructions: focus on the stated change; do not require the
  changed-file set to be the smallest possible; flag ambiguity.

## 6. Inter-rater plan (future)

- Two independent reviewers on a 10-task subset; Cohen's kappa.
- Disagreements resolved by discussion; unresolved marked.

## 7. Machine preparation (allowed, NOT gold)

- Evidence packets are prepared deterministically (no LLM).
- A preliminary machine-assisted note may flag apparent refactor/cleanup signals
  from the diff (e.g., whitespace, renames, doc-only lines) but MUST be labeled
  as a machine note and never treated as semantic gold.

## 8. Outputs

- `research/semantic_audit/` — evidence packets (one dir per case) + manifest.
- `research/semantic_audit/annotation_form.csv` — blank form.
- `research/semantic_audit/reviewer_instructions.md`.
- `research/semantic_audit/adjudication_schema.json`.
- `research/semantic_audit/sample_manifest.json` — selected cases.