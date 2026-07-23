# Results and Evidence Policy

**Date:** 2026-07-23
**Status:** Ratified

---

## 1. Result Storage

### 1.1 Run Records
- Each benchmark run produces a `RunRecord` frozen dataclass
- Stored as JSON in `runs/YYYYMMDD_HHMMSS_<run_id>/run_record.json`
- Contains: strategy, repository, scenario, status, duration, token usage, artifacts

### 1.2 Aggregated Results
- `runs/benchmark_summary.json` — Per-arm success/failure/timeout counts
- `runs/benchmark_results.json` — Full evaluation results (pilot/research only)
- `runs/publication_tables/` — LaTeX, CSV, Markdown tables (research only)

### 1.3 Directory Structure
```
runs/
  benchmark_summary.json         # Top-level summary
  YYYYMMDD_HHMMSS_<run_id>/
    run_record.json              # Individual run
    benchmark_result.json        # Evaluation result
    logs/                        # Execution logs
  publication_tables/            # Research profile only
    strategy_comparison.csv
    strategy_comparison.md
    strategy_comparison.tex
    repository_summary.csv
```

---

## 2. Output Classification

Every run carries a `publication_evidence` boolean:

| Value | Meaning |
|-------|---------|
| `false` | Smoke/pilot — engineering validation, not for publication |
| `true` | Research profile — publication-quality evidence |

Run metadata also includes:
- `label`: profile label (`orchestration-smoke`, `protocol-pilot`, `protocol-research`)
- `timestamp`: ISO 8601 UTC
- `environment`: Python version, platform, dependency versions
- `protocol_version`: Frozen protocol version used
- `config_hash`: SHA-256 of execution config

---

## 3. Versioning and Audit Trail

### 3.1 Result Tagging
- Every result set is tagged with the Git commit SHA of the code that produced it
- Results directory is labeled with timestamp + run ID for traceability

### 3.2 Checksums
- All scenario YAMLs, configs, and run records have SHA-256 checksums
- Frozen protocol documents have checksums recorded in `SYSTEM_STATE.md`
- On any protocol amendment, checksums are recomputed and the change logged

### 3.3 Commit Before Execution
- Before any publication-profile run, commit all code changes to a named branch
- Tag the commit with `results/<profile>/<date>` for traceability
- Do not modify code between execution and analysis

---

## 4. Evidence Chain

```
Source material (paper) 
  → Research Protocol v1.0 (frozen)
    → Protocol companion docs (7 files)
      → Implementation (Phase 4A–4F)
        → Benchmark execution (Kaggle)
          → RunRecords (raw data)
            → EvaluationResults (metrics)
              → Aggregated results (statistics)
                → Publication tables (reporting)
```

Each link in the chain is versioned and traceable.

---

## 5. Reproducibility Requirements

Per the Reproducibility Protocol (`docs/REPRODUCIBILITY_PROTOCOL.md`):

1. **Deterministic strategies:** Monolithic, compiled_ai, incr_rtl must produce identical outputs given identical inputs
2. **Non-deterministic strategies:** LLM-dependent strategies (agent, selective, delta_mcp, code_plan) report seed and temperature; results may vary
3. **Seed recording:** Each RunRecord records the seed used
4. **Environment snapshot:** Python version, package versions, platform recorded in run metadata
5. **Kaggle environment:** Session ID, GPU type, Kaggle platform version noted in logs

---

## 6. Publication Criteria

Research profile runs may be cited in publication only if:

1. Protocol v1.0 (or an approved amendment) governs the run
2. All quality gates passed at the tagged commit
3. The run completed without manual intervention
4. Run records include the full evidence chain
5. The `publication_evidence` flag is `true`
6. Results are independently reproducible (per reproducibility protocol)

---

## 7. Amendment Handling

If results from an earlier protocol version are superseded by an amendment:

1. Keep original results (do not delete)
2. Tag with `superseded-by: <amendment-id>`
3. New results use the amended protocol
4. Both are preserved for audit
5. Amendment record explains why earlier results are superseded
