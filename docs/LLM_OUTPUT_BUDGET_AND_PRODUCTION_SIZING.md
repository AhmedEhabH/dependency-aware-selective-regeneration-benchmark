# LLM Output Budget and Production Sizing

## Frozen Todo scientific budgets

For `scientific-wip-impactplan-v1.1`, maximum completion tokens are frozen
before outcomes:

| Role | Maximum | Payload |
|---|---:|---|
| Agent control/tool action | 1024 | One structured tool action or final path selection |
| ImpactPlan | 4096 | Compact R/P/V/H plan with evidence references and provenance |
| Initial PatchEnvelope | 8192 | Ordered exact-literal search/replace patches |
| Repair PatchEnvelope | 8192 | The same bounded structured patch representation |

These are ceilings, not targets. Actual provider-reported completion usage is
the billed and recorded value. A `finish_reason=length` is persisted as a
truncation/failure; the attempted run remains evidence and is not retried with
a larger ceiling. Todo never uses 16384 or 65536 and no budget is raised after
observing scientific outcomes.

The model's maximum completion capacity is not an operational default. A large
open ceiling increases worst-case latency, cost, runaway/repetition exposure,
provider variance, and accidental verbose JSON/code output. The Todo candidate
universe is five source artifacts, so role-sized ceilings provide ample
headroom while preserving reproducibility.

## Stable production interfaces

Impact planning accepts requirement deltas, visible constraints, candidate
metadata, and automatic evidence references. It returns a compact structured
ImpactPlan without copying repository contents. `context_set` remains
independent of the action sets, so preserved artifacts may be read without
becoming writable.

Editing uses a JSON-schema PatchEnvelope. Every non-empty `search` must match
exactly one literal substring when applied; patches apply in order; fuzzy
matching and generic whitespace correction are prohibited. Historical marker
parsing remains available only to older protocols.

Repair retains the current R write-set; only the existing bounded ImpactPlan
v2 expansion may widen it. ImpactPlan and planner provenance survive all
repair/failure paths. Agent control is structured: calls 1-7 may explore and
call 8 is forced final in the Todo protocol.

Persist per call: model, provider, role, prompt/completion/total tokens,
configured cap, finish reason, truncation, latency, retry count, schema status,
and cost when available. Persist per run: plan/version/hash, candidate-universe
hash, context/write sets, validation obligations, changed/prohibited paths,
validation results, and final result.

## Production sizing policy — documentation only

Dynamic production sizing is not implemented in the Todo study.

### Tier S — small change or bounded subsystem

Typical size is at most 25 candidate artifacts. Start with Agent 1024,
ImpactPlan 4096, patch 8192, and repair 8192. This is the active Todo policy.

### Tier M — medium subsystem

Typical size is 26-100 candidates. A future preregistered production policy may
use Agent 1024 (2048 only if a measured final path list cannot fit), ImpactPlan
8192, and patch/repair 8192 per artifact or 16384 for a deliberately bounded
small batch. Prefer artifact/batch splitting to a whole-subsystem response.

### Tier L — large heterogeneous repository

For more than 100 candidates, partition evidence and planning by subsystem,
emit compact summaries and evidence references, compose a deterministic
top-level plan, and generate patches per artifact or bounded batch. Suggested
future starting ceilings are control 2048 only when required, plan shards
8192, top-level plan 4096-8192, and patch/repair batches 8192-16384.

16384 is allowed only after pre-run sizing proves a legitimate structured
payload need. 65536 is never a normal default and requires a separately frozen
workload that cannot safely be chunked. Large context capacity never justifies
serializing the whole repository; collect only strategy-visible evidence and
required code context, and keep input budgeting separate from output headroom.

## Promotion rule

Larger tiers may activate only before a future repository experiment or
production deployment, based on pre-run artifact/output sizing and before any
scientific outcome. D051/A032 keep Tier M/L inactive for Todo v1.1.
