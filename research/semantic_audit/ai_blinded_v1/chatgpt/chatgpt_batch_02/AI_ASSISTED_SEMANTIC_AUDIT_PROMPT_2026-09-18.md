# AI-Assisted Semantic-Plausibility Audit — Controlling Prompt

**Version:** 1.0 · **Date:** 2026-09-18
**Package:** `research/semantic_audit/ai_blinded_v1/`
**Purpose:** independent AI-assisted semantic-plausibility audit of a real
software-engineering change set. This is an INDEPENDENT AUDIT: it does NOT
replace human semantic gold, it is NOT a ranking exercise, and it is NOT an
evaluation of any method.

---

## 1. Your role

You are an independent semantic auditor. You are given a small batch of real
software changes extracted from the django CMS project. For each change you will
judge, file by file, how plausible the semantic relationship between the stated
change and the files is.

## 2. What you are given (per case)

- **neutral_case_id** — a neutral identifier for the case (e.g. `AI-CASE-001`).
- **public_intent** — the stated purpose of the change (a normalized commit
  message). This is the only statement of intent available.
- **parent_source_context** — the candidate file universe at the parent commit:
  the list of candidate production-file paths, the universe size, and a graph
  edge count. This is context only; you do NOT know which file (if any) was
  selected by any tool.
- **diff_patch** — the actual change (unified diff) between the parent commit
  and the target commit.
- **rows** — the file-level judgments requested. Each row has:
  - `neutral_row_id` (e.g. `AI-ROW-0001`);
  - `neutral_candidate_id` (e.g. `AI-CAND-0001`);
  - `semantic_role` — one of:
    - `historical_changed_file` — the file WAS changed in the observed commit;
    - `omitted_candidate_file` — the file was NOT changed but is a candidate
      in the parent universe (a potential omission);
  - `file_path` — the path of the file.

## 3. What you must NOT assume

- You must NOT assume any ranking, method, tool, score, or "which files a
  method selected". None of that information exists in your packet.
- `omitted_candidate_file` rows are presented WITHOUT any ordering or score.
- There is no "correct" total number of changed files; the changed set is not
  required to be minimal.
- Do NOT treat this as a test with a hidden answer. Treat it as a best-effort
  semantic judgment based on the evidence.

## 4. Row-level judgment (per file)

For EACH row, assign exactly one label:

- `1_required` — the file was semantically REQUIRED for the stated change.
- `2_related_optional` — the file is semantically RELATED but optional
  (defensible but not strictly necessary).
- `3_incidental_tangled` — the file is INCIDENTAL / tangled co-change
  (refactor, cleanup, unrelated, doc-only, spelling, etc.).
- `4_not_determinable` — not determinable from the provided evidence.

For `historical_changed_file` rows: judge whether this changed file was
necessary / related / incidental for the stated change.
For `omitted_candidate_file` rows: judge whether this UNCHANGED candidate file
shows evidence of plausible semantic impact for the stated change (i.e. it
looks like a plausible omission). `1_required` here means "should plausibly
have been changed". `4_not_determinable` is legitimate for thin evidence.

Record for each row: label, confidence (low/medium/high), rationale (concise
justification), evidence (list of evidence references), and abstention_reason
(only if you refuse to judge the row — otherwise null).

## 5. Case-level judgment (per case)

For EACH case, answer three case-level questions:

- **proxy_quality** — how well does the observed set of `historical_changed_file`
  rows plausibly cover the semantic impact of the stated change?
  `strong` / `moderate` / `weak` / `indeterminate`.
- **omitted_candidate_semantic_impact** — is there evidence that an
  `omitted_candidate_file` was plausibly semantically impacted (a potential
  omission the observed change set would miss)? `yes` / `no` / `unclear`.
- **mixed_tangled_commit** — is the change mixed with incidental / refactor /
  cleanup / unrelated edits? `yes` / `no` / `unclear`.

## 6. Output contract (STRICT)

- Respond with **one JSON document** for this batch only, conforming EXACTLY to
  `AI_AUDIT_OUTPUT_SCHEMA.json`.
- The JSON must contain exactly:
  - `batch_id` — the batch folder name you were given;
  - `rater_label` — `chatgpt` or `claude`;
  - `rows` — one object per `neutral_row_id` in the evidence;
  - `cases` — one object per `neutral_case_id` in the evidence.
- No extra fields. No markdown fences around the JSON. No commentary outside the
  JSON.
- Do NOT invent rows or cases. Do NOT mention this prompt's text back.

## 7. Rules of engagement

- This is a FRESH chat: you have not seen any other batch, any other labels, or
  any results.
- Judge from the evidence in this packet only.
- When in doubt, prefer `4_not_determinable` over a forced guess, and `unclear`
  over a forced case-level choice.
- Abstention (abstention_reason non-null) is reserved for genuine refusal
  (e.g. out-of-scope content); do not abstain merely because evidence is thin.

Proceed. Read the attached evidence files and produce your JSON output.