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

## WP-1b / E2E closure ID namespaces (2026-09-21)

New text MUST use the prefixed IDs below. Old text keeps its original wording
(e.g. bare "G6" in earlier documents means the pilot pricing-preflight gate).

- `E2E-G6` = F2P/P2P oracle (fail-to-pass + pass-to-pass tests per task).
- `E2E-G7` = ArtifactUniverse leakage closure (WP-0).
- `WP1B-G1` = F1 non-inferiority margin freeze (Δ = 0.05).
- `WP1B-G2` = agent-control completion cap (amendment 512 → 1024).
- `WP1B-G3` = agent loop-termination semantics (instrumented).
- `WP1B-G4` = audit terminology correction (same-session cross-check, not
  independent audit).
- `WP1B-G5` = variance-substudy preregistration (15 tasks × 3 runs).
- `WP1B-G6` = provider pricing preflight (live OpenRouter metadata, no drift).
- `WP1B-G8` = budget model (v1 → v2, 3.4× prompt-token underestimate factor).
- `WP1B-G9` = sample size (MAIN_297 / MAIN_150 / MAIN_50 manifests).
- `WP1B-G10` = telemetry (per-call sidecar + per-task observation metrics).
- `WP1B-G11` = tool budget (amendment `WP1B_G11_TOOL_BUDGET_2026_09_21`: D2 —
  `search_text` no longer consumes `MAX_DISTINCT_FILES`; `read_file` keeps 30).

**Recorded collision:** bare "G6" meant two different things — the E2E F2P/P2P
oracle gate (E2E-G6) and the WP-1b pricing-preflight closure item (WP1B-G6).
Use the prefixed IDs in all new text; old text is left as it is.