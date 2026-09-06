# SCIENTIFIC-WIP-IMPACTPLAN-V1.1 — INDEPENDENT AUDIT (D051)

Audit performed immediately before the one authorized full-suite run and the
real v1.1 30-run study. Every item below is a code/evidence check, not a claim
of scientific success.

## 1. Gold leakage

- Planner prompt template contains no `expected_actions`, no `GOLD_SENTINEL`,
  no evaluator asset names (verified by G2 gate + source grep).
- Executor prompt contains no evaluator asset names and no gold sentinel
  (verified by G1/G2 gates).
- `todo_smoke_*_checks` markers appear in neither `impact_planner.py` nor
  `regeneration.py` (verified by G1 gate).
- Acceptance probe uses a synthetic non-study scenario with its own
  deterministic validator; no study gold involved.
- Result: PASS.

## 2. Context/action separation

- `ImpactPlan.context_set` is an independent set; orthogonality invariant is
  enforced in `gate_plan` (`context_set` need not equal any action set;
  `src/benchmark/selection/impact_planner.py:243-245`).
- A PRESERVE artifact may be context without being writable.
- Result: PASS.

## 3. Write guard

- `SharedRegenerationExecutor` tracks `prohibited_write_attempts`; writes
  outside the executable plan's write-set are blocked and counted
  (`src/benchmark/execution/regeneration.py:569-603`).
- `write_set == {R}` for the impact-plan arm (`plan_from_impact_plan`); P/V/H
  writes are not in the executable plan.
- Final RunRecord carries `prohibited_write_attempts`
  (`src/benchmark/execution/runner.py:1487`).
- Result: PASS.

## 4. Bounded expansion

- Impact-plan arm allows exactly ONE bounded v1->v2 expansion
  (`src/benchmark/execution/runner.py:1308-1400`; gated on
  `impact_plan.plan_version == "v1"`).
- Expansion is evidence-driven (failure summary fed to `expand_plan`), parent
  hash/version recorded; after expansion failure the run escalates to
  HUMAN_REVIEW (no further widening).
- `impact_expansion_count` persisted on the record.
- Result: PASS.

## 5. Repair provenance

- Repair path is `_run_regeneration_repair_flow` for the impact-plan arm; the
  first record's impact-plan evidence is preserved and the final record keeps
  `impact_plan` dict, `impact_plan_hash`, `impact_plan_version`,
  `impact_plan_parent_hash`, `planner_*` metrics
  (`src/benchmark/execution/runner.py:1475-1489`).
- Planner prompt/completion/total tokens, calls and latency persist (verified
  by `test_scientific_evidence_persistence.py`, G5).
- Result: PASS.

## 6. Cap freeze

- Frozen caps verified in freeze artifact
  `reports/SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json`:
  `agent_control_cap=1024`, `impact_plan_cap=4096`, `source_edit_cap=8192`,
  `repair_patch_cap=8192`.
- No Todo scientific call uses 16384/65536 (transport asserts role caps).
- `finish_reason=length` is persisted as truncation/failure; caps are not
  auto-raised (tested in `test_agent_control_cap.py`, `test_exact_patch_executor.py`).
- Result: PASS.

## 7. Provider pin

- Model `qwen/qwen3-coder`; provider `DeepInfra` via OpenRouter; fallback OFF
  (`allow_fallbacks=False`, `require_parameters=True` in backend).
- NovitaAI not used (DeepInfra accepted JSON Schema at capability probe).
- Result: PASS.

## 8. Historical-run preservation

- `reports/scientific_microstudy/run_records.jsonl` (exp-20260905-225518)
  preserved byte-for-byte: 136621 bytes, SHA-256
  `222A63E91F91369F38A201A4F3ED00A6EF2FF39FC7BF52E7A9262F32F9AA5871`
  (recomputed and matched at handoff and again at final stop).
- Results builder rejects mixed historical protocols.
- Result: PASS.

## 9. Over-engineering check

- Four authorized interface fixes only: JSON-schema PatchEnvelope, structured
  Agent control, file/directory `search_text`, ImpactPlan provenance.
- No new model, repository, metric, gate, graph/retrieval/agent framework,
  parser heuristic, or cap escalation.
- Production Tier M/L sizing is documentation only (not implemented).
- Two narrow demonstrated-defect fixes during execution, both re-verified:
  1. Acceptance-gate capability probe awaited the async `generate_structured`
     correctly (asyncio.run) — real runtime defect, no scope added.
  2. `agent_final` JSON schema dropped `uniqueItems` because DeepInfra's strict
     JSON-schema grammar rejects it (`Unimplemented keys: ["uniqueItems"]`).
     Uniqueness of `selected_paths` was already enforced deterministically in
     the agent control loop (`iterative_agent.py` duplicate check), so no
     semantic guarantee was lost. Acceptance gate re-passed after the fix
     (2/2 E2E reach and pass functional validation; 0 truncations).
- Result: PASS.

## Audit summary

```
SCIENTIFIC_WIP_V11_AUDIT=PASS
GOLD_LEAKAGE=PASS
CONTEXT_ACTION_SEPARATION=PASS
WRITE_GUARD=PASS
BOUNDED_EXPANSION=PASS
REPAIR_PROVENANCE=PASS
CAP_FREEZE=PASS
PROVIDER_PIN=PASS
HISTORICAL_RUN_PRESERVATION=PASS
OVER_ENGINEERING_CHECK=PASS
```