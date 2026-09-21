# WP-1b Knob Registry v2 — 2026-09-21

**Status:** Versioned supersession of
`docs/WP1B_KNOB_REGISTRY_2026-09-21.md` (v1 kept as history). Amendment
`WP1B_G11_TOOL_BUDGET_2026_09_21` (D2) is the ONLY change: it clarifies that
`MAX_DISTINCT_FILES` applies to explicit `read_file` exposure only, and that
`search_text` backend scanning does NOT consume the distinct-file budget.

**Registry role:** Registry of scientific vs operational knobs for the WP-1b
selection-only experiment (mission section 6). Scientific knobs are frozen and
any change requires a visible prospective amendment BEFORE the first affected
main result. Operational knobs may be repaired without scientific retuning ONLY
if the repair cannot alter which model output is accepted, which files are
selected, or how a prediction is scored.

## SCIENTIFIC KNOBS — FROZEN / AMENDMENT REQUIRED

| Knob | Frozen value | Source |
|------|--------------|--------|
| model identity | `qwen/qwen3-coder` (exact route `openrouter:qwen/qwen3-coder@deepinfra/turbo`) | `research/wp1a/sip_scientific_model_provenance.json` |
| provider identity / routing policy | DeepInfra through OpenRouter (`deepinfra/turbo`) | `sip_scientific_model_provenance.json` |
| temperature | 0.0 | `sip_scientific_model_provenance.json` |
| top_p | unset (not configured) | frozen SIP run records |
| completion-token cap (agent control) | `agent_control_max_completion_tokens` = 1024 (G2 amendment `WP1B_G2_COMPLETION_CAP_2026_09_21` EFFECTIVE; see `docs/WP1B_AGENT_COMPLETION_CAP_PROVENANCE_2026-09-21.md`) | `research/wp1b/wp1b_frozen_agent_protocol_v2.json` |
| MAX_AGENT_CALLS | 8 (calls 1–7 explore, call 8 forced final) | `src/benchmark/strategies/iterative_agent.py`; `wp1a_frozen_agent_protocol.json` |
| tool set | `list_files`, `read_file`, `search_text` | `wp1a_frozen_agent_protocol.json` |
| tool semantics | bounded results (2000 chars/result), traversal/absolute/backslash rejected, repeated identical request rejected | `wp1a_frozen_agent_protocol.json`; `repository_tools.py` |
| **MAX_DISTINCT_FILES (D2 amendment `WP1B_G11_TOOL_BUDGET_2026_09_21`)** | **30 — applies to explicit `read_file` exposure ONLY. `search_text` backend scanning does NOT consume the distinct-file budget.** | `src/benchmark/strategies/repository_tools.py` |
| MAX_SEARCH_RESULTS | 50 — frozen cap; alphabetical first-50 result policy unchanged | `src/benchmark/strategies/repository_tools.py` |
| prompt template | `INITIAL_SYSTEM_PROMPT` + `TOOL_SCHEMA` (per-task intent = byte-identical stored SIP intent) | `wp1a_frozen_agent_protocol.json`; `wp1a_intent_parity.json` |
| final-answer schema | `AGENT_FINAL_SCHEMA` (action=final, selected_paths minItems 1, rationale) | `wp1a_frozen_agent_protocol.json` |
| sample IDs | main-50 (`9b26ad59…`) + calibration-3 (`23f520d8…`), disjoint | `research/wp1a/wp1_main_50_manifest.json`, `wp1_calibration_3_manifest.json` |
| main/calibration membership | first 50 of frozen ordering; deterministic complement draw (seed 20260921) | `wp1_sample_freeze.json` |
| scorer | single shared scorer (TP/FP/FN/P/R/FNR/F1, mean set size, empty rate) | `src/benchmark/wp1a/scorer.py` |
| primary metric | pooled micro F1 | `wp1a_shared_scorer_schema.json` |
| bootstrap method | paired task bootstrap, 10,000 resamples, seed 20260920 | `wp1a_shared_scorer_schema.json` |
| confidence level | 95% percentile CI [Q2.5, Q97.5] | `wp1a_shared_scorer_schema.json` |
| decision rule | G1: CI-based rule, Δ=0.05 (Q5 one-sided), frozen | `research/wp1b/wp1b_ni_margin_frozen.json` |
| NI margin | **Δ = 0.05 pooled micro-F1** (frozen by the WP-1b preflight freeze) | `wp1b_ni_margin_frozen.json` |
| failure semantics | ALL-TASKS / FAIL-CLOSED; EMPTY on no-paths/transport/deadline/malformed | `research/wp1a/wp1a_failure_semantics.json` |
| EMPTY-prediction semantics | fail-closed EMPTY in primary analysis; sensitivity excludes ONLY pre-defined infrastructure failures, reported alongside primary | `wp1a_failure_semantics.json` |
| variance-substudy design | 15-task subset, 3 runs/task (G5 preregistration, `artifacts/wp1b_variance_substudy_preregistration_2026-09-21.json`) | this mission |

## OPERATIONAL KNOBS — MAY BE REPAIRED WITHOUT SCIENTIFIC RETUNING

| Knob | Rule |
|------|------|
| transport retry | max 3 byte-identical retries; ONLY transport failures may be retried |
| rate-limit backoff | allowed, must not change request bytes |
| logging failures | allowed |
| serialization implementation bugs | allowed to fix if output bytes unchanged |
| crash recovery | allowed; never silently discards run records |
| non-semantic path formatting | allowed |
| non-semantic telemetry | allowed (truncation/EMPTY telemetry + A4 tool_ok/tool_error + search telemetry) |
| resume checkpoints | allowed |
| provider metadata lookup | allowed (G6 pricing preflight) |
| **report-only search telemetry** | allowed (G11): `search_files_scanned`, `search_results_returned`, `search_result_cap_hit`, `unique_paths_surfaced`, `tool_duration_seconds` — behavior-preserving, never alter search semantics/ordering/limits |

## Classification rule

If an operational modification could alter which model output is accepted,
which files are selected, or how a prediction is scored, classify it as
SCIENTIFIC instead and handle it as a prospective amendment.

## D2 amendment record

Amendment `WP1B_G11_TOOL_BUDGET_2026_09_21` (approved by Ahmed, 2026-09-21):
`search_text` no longer consumes the distinct-file budget; `read_file` keeps
`MAX_DISTINCT_FILES = 30`. No other agent knob changes. This restores on Saleor
the tool behaviour the v1.1 agent actually had (on Todo the 30-file budget
never bound). See `docs/WP1B_AGENT_TOOL_BUDGET_DEFECT_2026-09-21.md`.

## Authority

Knob values above are drawn from the WP-1a frozen artifacts under
`research/wp1a/`, the frozen protocol set, and the WP-1b preflight freeze. This
registry records current state; it does not amend any frozen value except via
the recorded amendments above.