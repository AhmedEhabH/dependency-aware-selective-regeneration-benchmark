# STAGE-C djangoCMS COST PROBE — DECISION (scientific-stagec-djangocms-costprobe-01)

**Date:** 2026-09-08
**Type:** FROZEN NON-STUDY COST PROBE (NOT part of the scientific 60-run result set; MUST NOT be reused as study results).

## Verified frozen prep identity
- `PREP_COMMIT=270089a80d46d1aeac99c94043cf09dc7faf4572` (HEAD)
- `PREP_TAG=stagec-djangocms-prep-verified-01` (peels to the commit above)

## Frozen scientific configuration (as executed)
- Model: `qwen/qwen3-coder`
- Provider: OpenRouter pinned to `deepinfra/turbo` (`provider.order=["deepinfra/turbo"]`, `allow_fallbacks=false`, `require_parameters=true`)
- Fallback: OFF
- Temperature: 0.0
- Scenario: `djangocms-cross-008`
- Arms: `iterative_repository_agent` x1, `impact_plan` x1
- Caps: Agent control 1024; ImpactPlan planner 4096 (frozen constant)
- Scope: SELECTION ONLY (never revise_plan, never regenerate/repair/migrate/evaluate)
- Source: pinned django-cms 5.0.0 commit `0f633fc9fa213357f4202482aab2b0edad680f95` materialized from the verified local cache into `benchmark_data/repositories/djangocms` (git-ignored, uncommitted)

## Result: BOTH PROBE RUNS EXECUTED BUT FAILED (0/2 successful)

The requirement "Scientific calls in this task must equal exactly 2 successful probe runs" was NOT met. Both runs terminated in the fail-closed path. **No valid cost evidence for authorization; no tuning/retry/3rd call performed (forbidden).**

### Run 1 — iterative_repository_agent (FAILED)
- Status: failed — `iterative_agent: no paths selected after exploration`
- 8 model calls, 7 tool calls, 2 files inspected, 17,572 selection tokens (prompt+completion)
- API cost (provider-returned): **$0.005209**
- finish_reason=stop, no truncation
- The agent explored the repo but its final prediction classified every candidate as `preserve` and selected zero regenerate paths. Root-cause driver: the scenario's intended write targets are not representable in the frozen editable/candidate universe (see below).

### Run 2 — impact_plan (FAILED)
- Status: failed — `impact_plan_planner_error: planner produced unknown paths: ['cms/cache/tags.py', 'cms/signals.py']`
- 1 planner model call, 4,345 selection tokens
- API cost (provider-returned): **$0.003497**
- finish_reason=stop, no truncation
- The planner proposed exactly the scenario's gold files but was fail-closed because they are not in the candidate universe.

## Root-cause diagnosis (prep/candidate-universe consistency defect — NOT model quality, NOT cost)
The frozen scenario gold for `djangocms-cross-008` references paths that cannot exist in the materialized source / candidate universe:
1. `cms/cache/tags.py` — a NEW file (expected action `create`). It does not exist in django-cms 5.0.0 and is NOT in the profile `llm_editable`/candidate universe, so no strategy may select it.
2. `cms/signals.py` — the real django-cms 5.0.0 layout is the `cms/signals/` **package** (`cms/signals/__init__.py` etc.); there is no `cms/signals.py` file, so the path is unrepresentable.
Both arms fail closed on this mismatch. This is a scenario/gold/candidate-universe prep defect. Per task rule I did NOT modify scenarios, gold, graph, executor, prompts, caps, or scientific protocol.

## Cost projection (measured from the FAILED runs — INFORMATIONAL ONLY, NOT a valid COST_LOCK basis)
- agent_probe_cost = $0.005209
- impactplan_probe_cost = $0.003497
- raw_projected_60_cost = 30*agent + 30*impactplan = **$0.261189**
- conservative_projected_60_cost = raw * 1.25 = **$0.326486**
- Would-be COST_LOCK if runs had been successful: PASS (<= $0.50)

## Final COST_LOCK
**`COST_LOCK=BLOCKED`** — not PASS, not STOP. The cost would clear the $0.50 gate, but the probe runs were not successful (0/2), so no cost evidence may be used to authorize. The prep defect must be resolved (by the coordinator) and the probe re-run under a fresh authorization.

## Deliverables (raw probe artifacts)
- `reports/scientific-stagec-djangocms-costprobe-01/run_iterative_repository_agent.json`
- `reports/scientific-stagec-djangocms-costprobe-01/run_impact_plan.json`
- `reports/scientific-stagec-djangocms-costprobe-01/cost_probe_report.json`

The final 60-run study was NOT started.