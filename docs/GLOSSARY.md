# Project Glossary (2026-09-20)

**Status:** Live glossary of thesis-facing terminology. Terminology changes
are report/glossary-facing only; historical code identifiers, commits, tags and
artifact paths are NOT renamed.

---

## SIP — Sparse Impact Plan

The Sparse baseline. This is the frozen Sparse write set produced by the
frozen Sparse (qwen3-coder) strategy. It is the primary comparator in the final
untouched RM-CSS replication.

- Old/ambiguous thesis-facing names (superseded for NEW reports): "Sparse-v2",
  "sparse impact plan", bare "Sparse" in final-policy contexts (historical
  reports keep their original wording).
- Historical code identifiers (NOT renamed): `sparse_stage5_run_records.jsonl`,
  `predicted_write_set`, Sparse-v2 strategy, `Sparse` baseline in old reports.

## RM-CSS — Repository-Memory Calibrated Set Selection

The current frozen method. It consists of:

```
RM-CSS = SIP
       + Qwen dense ranking          (qwen/qwen3-embedding-8b @ DeepInfra, realization A)
       + parent-only Repository Memory (structural top-10 + episodic top-10)
       + calibrated ADD / KEEP / DROP set selection (L2-LR, 11 features, threshold 0.20)
```

- Old/ambiguous thesis-facing name (superseded for NEW reports): "V2" (in the
  sense of Repository-Memory Calibrated Set Selection), "Repository Memory
  Rescue V2", "PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2".
- Historical code identifiers (NOT renamed): `deployment_artifact.json`,
  `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`,
  `STAGE5_CORRECTED_REEXECUTION_POSITIVE`, `candidate_rows_stage5_corrected.parquet`,
  `benchmark.memory_rescue.candidates`.

## Guidance

- Avoid ambiguous bare wording such as "V2 beats V2".
- Use SIP and RM-CSS in NEW thesis-facing/report text.
- When quoting old artifacts/reports, preserve their original "V2"/"Sparse"
  wording and add a clarification pointer to this glossary.

## Other core terms (unchanged)

| Term | Meaning |
|---|---|
| Qwen dense ranking | file score = MAX cosine over code units of `qwen/qwen3-embedding-8b` (realization A) against the task intent embedding |
| Parent-only Repository Memory | deterministic co-change (Jaccard, support >= 2) + episodic BM25 features computed ONLY from parent-visible history |
| Calibrated set selection | 11-feature L2-LR (C=1.0, liblinear, seed 0) with StandardScaler; threshold 0.20 (frozen) |
| DEV | development evidence (djangoCMS DEV 174 + Saleor DEV 149) — selection evidence only |
| Stage-5 | the previously-exposed 139-task confirmatory population (dc RESERVE 59 + saleor INTERNAL_TEST 80); NOT untouched |
| Saleor RESERVE | the only untouched sealed population (1,086 tasks); this mission samples 300 |
| Embedding-coverage correction | P86 fix: never use finite sentinels for missing embeddings; NaN for no-unit files; embed missing units |
| `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED` | permanent: no new localization method will be designed/tuned for the current thesis |