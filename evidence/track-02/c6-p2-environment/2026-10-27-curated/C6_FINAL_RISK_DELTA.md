# C6_FINAL_RISK_DELTA.md — residual-risk delta vs the V2 register (2026-10-27)

Scope: delta *from* `TRACK02_SCIENTIFIC_RISK_REGISTER.md` (V2) introduced in
this blocker-repair mission. Ratings: REMOVED / REDUCED / NEW (post-repair).

## Removed / reduced

| Risk (V2) | Delta | Why |
|---|---|---|
| T-only evaluator crash (F1) | **REMOVED** | plan now flows through `run_limited` → `docker_run`; regression-tested (RED→GREEN) |
| PASS recorded despite evaluator_error (F2) | **REMOVED** | verdict is computed strictly AFTER the reference evaluation; error → BLOCKED |
| Forged/trivial oracle accepted via stdout (F3) | **REMOVED** | behavioral oracle = injectable junit-xml inside the sandbox only; identity/count/exit consistency binding |
| Runtime identity incomplete: UNRESOLVED interpreter / NONE image / `:latest` tags (F4) | **REDUCED** | resolved interpreter@version + wheelhouse + immutable digest in ENVIRONMENT_ID; ENV_DRIFT stops execution. Residual: interpreter probe depends on local image availability; declared pins are authoritative |
| Host-PID `docker kill` + orphan risk (F5) | **REMOVED** | cidfile identity + label + forced cleanup + sweep; REAL probe 0/0/0 orphans; residual risk: minimal (daemon unavailable → BLOCKED) |
| CLI source substitution with `inputs_verified=True` (F6) | **REMOVED** | frozen roles manifest + INPUT_BINDING_MISMATCH GLOBAL STOP; residual: operator could author a fraudulent manifest — outside runner threat model (authorization binding covers plan/protocol, not the manifest's contents at authoring time) |
| Inference of reference behavior at T from P tests / no T-contract evaluation (F7) | **REDUCED** | full M/A T contract evaluated in a separate reference tree; P tests alone never PASS. Residual: node-level semantics of individual test nodes remain the operator's command decision (files are the frozen identity unit) |

## New (post-repair, documented)

| Risk | Level | Mitigation |
|---|---|---|
| junitxml path inside the sandbox could be masked by a hostile pytest config (e.g. addopts writing elsewhere) | Low | runner injects `--junitxml` REJECTED duplicates: plan validation forbids a pre-existing `--junitxml` in the command; evidence file must sit under the scratch bind and is byte-hashed |
| Interpreter probe runs one probe container per digest (cached) | Negligible | cached by (image, interpreter); offline, `--network none`, ~1 s |
| `--cidfile` fallback to label query on very fast timeouts | Low | 3 s bounded read loop, then label query; both proven in the unit mock and the real probe |

## Unchanged residual risks (from the V2 register, still OPEN)

- No operator freeze/authorization → execution remains BLOCKED (`NOT_AUTHORIZED`).
- Historical dependency closure: images with era pytest + wheels are NOT yet
  provisioned (P1 python-3.6.x image missing entirely; P2/P3 base existing but
  without pytest/django) — per-task `image_digest` must be operator-frozen or
  the task BLOCKs (fail-closed, no silent fallback).
- 67 changed_test/TEST_CHANGE discrepancy rows: 0 inside the 174 cohort
  (unchanged).

## Bottom line

All seven execution-blockers that produced the V2 STOP are repaired and
regression-locked (74/74 + real docker probe + 174 read-only verify). The
remaining risks are operator-side (freeze/authorization/image provisioning),
not runner-side defects.