# Technical Debt Register

> Current register seeded 2026-09-14. Review cadence: before each new scientific
> protocol freeze; at each audited stable tag; weekly while active experimentation
> is ongoing; immediately before a paper/artifact freeze. A debt item must NOT be
> "fixed" if the change would rewrite frozen evidence — in that case implement the
> fix prospectively and preserve backward compatibility.

| ID | Area | Debt / limitation | Evidence | Impact | Category | Severity | Proposed action | Target | Status | Last reviewed |
|---|---|---|---|---|---|---|---|---|---|---|
| TD-001 | README | Current state, historical chronology, and detailed evidence are mixed in one very long page | old README ~505 lines | High reader friction; stale-looking contradictions | docs | High | split reader-first README from historical ledger | docs/model refactor | CLOSED 2026-09-14 | 2026-09-14 |
| TD-002 | Model config | Study scripts duplicate hard-coded model/provider/cap constants | `execute_real_commit_p1.py`, `controlled_encoding_ablation_execute.py` hard-code `qwen/qwen3-coder` + `deepinfra/turbo` | adding a model is slow/error-prone | code | High | immutable `ModelProfile` + resolved config | next infra milestone | OPEN | 2026-09-14 |
| TD-003 | Transport | OpenRouter HTTP/usage/retry logic is duplicated across launchers | `_raw_openrouter_call` repeated | maintenance and accounting drift | code | Medium | reuse one OpenAI-compatible transport boundary | next infra milestone | OPEN | 2026-09-14 |
| TD-004 | LocAgent | upstream agent loop uses POSIX `fork` and was blocked on Windows; upstream `result_queue.get()` can deadlock after an exited worker; upstream `BadRequestError` handler can spin without decrementing the attempt budget | P5-B blocker report; P5-C held-out run | P5 real pilot needed a POSIX host + documented error-handling patch | portability | High | **CLOSED 2026-09-15**: P5-B/P5-C executed on WSL2 Ubuntu; documented compatibility patch (`research/locagent-p5b/upstream_patch_p5_queue_guard.patch`) bounds deadlocks (bounded queue get) and BadRequest transport spins (fail-closed) — process/error handling only, no scientific change | P5-B/P5-C | CLOSED 2026-09-15 | 2026-09-15 |
| TD-005 | Tests | full suite can exceed shell timeouts | 3100+ tests | wastes iteration time | test | Medium | targeted tests during development; deterministic sharded full closure | immediate | MITIGATED | 2026-09-14 |
| TD-006 | Cost fields | historical `api_cost` conflates calculated estimate with potential provider-billed cost | P1 `api_cost` = estimate | ambiguous reporting | research-infra | Medium | new explicit ceiling/estimated/billed fields; backwards-compatible reader (`src/benchmark/model_profiles/cost.py`) | next infra milestone | PARTIAL 2026-09-14 | 2026-09-14 |
| TD-007 | Graph | current source graph is primarily static AST/import structure | M3 graph ablation | misses semantic/runtime relations | research-infra | Medium | evaluate Graph@K + Semantic@K + Hybrid@K before enriching graph | P2 | OPEN | 2026-09-14 |
| TD-008 | Environment | some tests/repos require external materialization/cache state | repository-materialization tests | portability friction | test | Medium | documented acquisition + explicit environment marker | ongoing | PARTIAL | 2026-09-14 |
| TD-009 | Scratch dirs | `demo_runs_v4/` / provider cache artifacts can remain untracked | observed untracked dirs | repository hygiene noise | docs/code | Low | documented scratch policy / `.gitignore` | docs refactor | OPEN | 2026-09-14 |
| TD-010 | Provider routing | provider pin improves reproducibility but can hit shared-pool overload | Qwen3-32B cross-model history | transient blocked probes | research-infra | Medium | classify 429, bounded retry; explicit fallback only outside frozen studies | next infra milestone | OPEN | 2026-09-14 |
| TD-011 | P1 derived metric | P1 `serialized_records` was computed from `len(decoded_write_set_ids)` (REGENERATE write-set size), NOT serialized decision count | `execute_real_commit_p1.py` pre-fix; report showed Full-v2 "Records mean 4.03" (impossible; candidates 140–152) | mislabeled derived metric in a completed study | research-infra | High | **CORRECTED 2026-09-14**: recomputed from persisted raw responses; `serialized_decision_count` + `predicted_write_set_size` persisted by runner; regression tests; correction artifact `reports/REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md` | P1 | CLOSED 2026-09-14 | 2026-09-14 |
| TD-012 | M1B serialized records | M1B sparse `serialized_records` uses the same write-set-size pattern (published 4.9; corrected serialized-decision mean 5.9) | `controlled_encoding_ablation_execute.py` `_serialized_record_count`; raw responses contain VALIDATE rows | mislabeled derived metric in a frozen audited study | research-infra | Medium | runner fixed prospectively (persists `serialized_decision_count`); frozen M1B `final_metrics.json`/reports preserved; decide separately whether to publish a corrected M1B figure | next infra milestone | OPEN | 2026-09-14 |
| TD-013 | M3 serialized records | M3 graph-ablation runner has the same write-set-size pattern for its serialized-record metric | `graph_ablation_execute.py` `_serialized_record_count` | mislabeled derived metric in an exploratory study | research-infra | Medium | runner fixed prospectively; frozen M3 evidence preserved | next infra milestone | OPEN | 2026-09-14 |
| TD-014 | Model profile layer | no unified dynamic model/provider selection for future studies | duplicated constants (TD-002) | future cross-model runs need manual edits | code | Medium | `config/model_profiles.yaml` + `src/benchmark/model_profiles` + `scripts/benchmark_cli.py` | docs/model refactor | PARTIAL 2026-09-14 | 2026-09-14 |
| TD-015 | LocAgent accounting | upstream `util/cost_analysis.py` returns 0 for any model containing `qwen`; `len(raw_output_loc)` is not a model-call count; timeout tasks can make many calls before persisting empty | P5-C usage ledger vs upstream `cost($)='0'` on the smoke run | paid LocAgent run could appear free; timeout-case cost under-reported | research-infra | High | **MITIGATED 2026-09-15**: append-only per-call usage ledger (`research/locagent-p5b/usage_ledger.py`) is the authoritative calls/tokens/cost source; common evaluator estimates cost from frozen P1 pricing; `assert_cost_not_zero_for_paid_usage`; timeout-case cost documented as incomplete/non-authoritative (never zero-with-usage) | P5-B/P5-C | CLOSED 2026-09-15 | 2026-09-15 |

## Review cadence

Review this register:
- before each new scientific protocol freeze;
- at each audited stable tag;
- weekly during active benchmark development;
- immediately before a paper/artifact freeze.

A debt item must not be "fixed" if the change would rewrite frozen evidence. In
that case, implement the fix prospectively and preserve backward compatibility.