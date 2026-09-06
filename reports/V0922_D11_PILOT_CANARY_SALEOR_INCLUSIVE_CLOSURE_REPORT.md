IMPLEMENTATION_MODEL_USED=opencode/big-pickle

# v0.9.22 D11 — PILOT-CANARY SALEOR-INCLUSIVE PRE-PILOT VIABILITY GATE CLOSURE REPORT (PILOT-EXEC-01)

**Report Date:** 2026-09-01
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`
**Task Pack:** `_workspace/active/00_EXECUTE_D11.md`
**Builds:** `b07da1a` (code) → `c1c892b` (notebook anchor refresh + freeze report) → `224c5a9` (provenance-verified freeze report)

---

## 1. Executive summary

The D11 pre-pilot viability gate corrects the pilot-canary **operational
topology** so the canary genuinely represents ALL THREE Pilot repositories
(Todo / django CMS / Saleor) as a 6-cell matrix — three canary scenarios,
two strategies, one repetition — instead of the D10 1-repo / 1-cell default
path and the contradictory `blast_radii` filter that silently dropped
`djangocms-cross-007` (cross_cutting) and made the canary uncallable.

The closure also separates Pilot protocol 1.1 from every other profile
(profile-derived `--protocol-version` default), restores validation-manifest
protocol parity with `configs/pilot.yaml`, and adds executable integration
coverage that proves the six-cell saleor-inclusive canary topology through the
actual CLI.

**Scientific inputs are UNCHANGED:** model Qwen2.5-Coder-14B-Instruct (BNB-NF4,
SDPA, kernel policy `flash_or_efficient_no_math`, GQA compat `repeat_kv_sm75`),
12 scenarios, 3 repo pins (Todo / django CMS / Saleor), 2 strategies (selective,
iterative_repository_agent), 2 repetitions = 48 cells, prompts, Ground Truth,
metrics, max attempts 3, completion cap 4096, the 12000/64 long-context gate,
Pilot timeout 1200. **The operational canary becoming 6 cells is not a scientific
matrix change.**

**No stable-tag move and no real Pilot launch happens in this closure.** The
D11 candidate artifact `v0.9.22-d11-candidate` is **built + provenance-verified
FROZEN** (0 mismatches) but is **NOT a launch basis**: the next real Pilot
launch requires a real pilot-canary pass on this (or a fresh exact) candidate
with its own tag decision.

---

## 2. B1–B4 blockers, tests-first evidence

```
BLOCKER=B1 (canary topology lost Saleor + dropped djangocms-cross-007)
RED_TEST=tests/unit/test_pilot_canary_viability.py test_validate_pilot_canary_evidence_defaults_three_repos (expected 6 cells with 2/2/2 repos; observed 1 repo / 1 cell on the D10 default path) + test for the blast_radii filter callability
RED_RESULT=FAIL (canary resolvable=0 cells; djangocms-cross-007 unreachable under blast_radii=localized; canary profile produced 0 scenario ids)
FIX=B1 pilot-canary profile: scenario_count=3, repository_names=[todo,djangocms,saleor], blast_radii=[localized,cross_cutting], scenario_ids=[todo-loc-001,djangocms-cross-007,saleor-loc-001]; validate_pilot_canary_evidence defaults expected_repositories=(todo,djangocms,saleor), expected_cells=6
GREEN_TEST=test_validate_pilot_canary_evidence_defaults_three_repos + tests/integration/test_pilot_canary_execution_path.py (executable CLI dry-run 6 cells)
GREEN_RESULT=PASS
EDGE_CASES=repo_counts mismatch error repaired (indented message); repetition 1 only for canary (rep1=6); strategies 3/3

BLOCKER=B2 (CLI --protocol-version default 1.1 leaked into dry-run and other profiles)
RED_TEST=tests/unit/test_cli.py test_protocol_default_profile_derivation (new)
RED_RESULT=FAIL (default forced 1.1 for smoke/research profiles)
FIX=B2 --protocol-version default None + resolve_profile_protocol(profile_name, explicit) = pilot/pilot-canary->1.1, smoke/research/scientific-smoke-v1/v2->1.0, explicit always overrides
GREEN_TEST=test_protocol_default_profile_derivation + override both directions
GREEN_RESULT=PASS
EDGE_CASES=explicit -p default None; explicit 1.0 on pilot profile; explicit 1.1 on smoke profile; unknown profile defaults 1.0

BLOCKER=B3 (validation-manifest protocol 1.0 vs configs/pilot.yaml 1.1 parity)
RED_TEST=tests/integration/test_pilot_notebook_contract.py TestPilotManifestProtocolParity
RED_RESULT=FAIL (manifest 1.0, config 1.1)
FIX=B3 benchmark_data/manifests/pilot_validation_commands.yaml protocol_version 1.0 -> 1.1
GREEN_TEST=TestPilotManifestProtocolParity
GREEN_RESULT=PASS
EDGE_CASES=exact YAML field read and cross-checked against configs/pilot.yaml

BLOCKER=B4 (no executable canary integration coverage)
RED_TEST=absent (no executable canary path test), new tests/integration/test_pilot_canary_execution_path.py
RED_RESULT=N/A (coverage missing)
FIX=B4 new executable integration test invokes the actual CLI in dry-run mode against canonical scenario data and proves the six-cell saleor-inclusive canary topology (repo counts 2/2/2, strategies 3/3, rep1=6, 6 unique ids, 0 model calls/tokens)
GREEN_TEST=test_pilot_canary_execution_path.py (4 tests)
GREEN_RESULT=PASS
EDGE_CASES=also assert pilot 48-cell matrix unchanged; protocol 1.1 in canary source_identity
```

**Additional production fix while aligning defaults:** the
`validate_pilot_canary_evidence` repo-count error message was reformatted
(inner lines wrongly indented inside the f-string expression — cosmetic, no
behavior change, verified by `ast.parse` and compile check).

---

## 3. Exact change-impact table

| File | Before | After | Why | Dependencies affected | Tests proving it | Scientific impact |
|---|---|---|---|---|---|---|
| `seven_arm_benchmark.py` | `pilot-canary` profile = todo/djangocms, blast_radii=[localized], no saleor; `--protocol-version` default hardcoded `"1.1"` | `pilot-canary` = 3 scenarios/3 repos (todo-loc-001, djangocms-cross-007, saleor-loc-001), blast_radii=[localized,cross_cutting]; `--protocol-version` default `None`, resolved by new `resolve_profile_protocol` before the timeout block | B1/B2 — canary must represent all three repos and protocol must not leak | every profile path and every canary launch/validator path | `test_pilot_canary_viability.py`, `test_cli.py`, `test_pilot_readiness.py` | None (48-cell pilot unchanged) |
| `src/benchmark/execution/preflight.py` | `validate_pilot_canary_evidence` defaults internally 1 repo / 1 cell; repo-count error message mis-indented | defaults `expected_repositories=("todo","djangocms","saleor")`, `expected_cells=6`; message strings dedented | B1 — fail-closed canary evidence defaults must match the saleor-inclusive topology | canary validator callers (unit + notebook canary gate) | `test_pilot_canary_viability.py`, `test_pilot_readiness.py` | None |
| `benchmark_data/manifests/pilot_validation_commands.yaml` | `protocol_version: "1.0"` | `protocol_version: "1.1"` | B3 — parity with `configs/pilot.yaml` | validation-manifest consumers (launch/resume argv) | `TestPilotManifestProtocolParity` (notebook contract) | None |
| `notebooks/pilot_exec_01.ipynb` | canary cell passed validation-python for todo/djangocms only; header/nav said D10.3 + 6-cell markdown stale | canary cell adds `--validation-python "saleor="+SALEOR_PYTHON` (+ todo/djangocms), `PILOT-EXEC-01 D11` headers, `D11 FAIL-CLOSED` message; step-07 markdown heading `Pilot-Canary — Real End-to-End Gate (D11, Saleor-inclusive)` describing the 3-repo/6-cell matrix | B1/B4 — the bundled canary must exercise Saleor validation and the runbook must describe the saleor-inclusive canary | notebook contract + deployment bundle tests | `test_pilot_notebook_contract.py` (heading + D11 canary-cell validation-commands test), `test_pilot_deployment_bundle.py` | None |
| `tests/unit/test_cli.py`, `test_pilot_readiness.py`, `test_pilot_canary_viability.py` | old 1.1-default and 1-repo expectations | profile-derived protocol default matrix + 3-repo/6-cell canary evidence expectations | B1/B2 regression guards | — | themselves | None |
| `tests/integration/test_pilot_notebook_contract.py`, `test_pilot_deployment_bundle.py` | D10.3 heading/old validation commands; TARGET tag constants d10 | D11 heading + `test_d11_canary_cell_saleor_inclusive_validation_commands`; PILOT_SOURCE_TAG / EXPECTED_FROZEN_SOURCE_TAG -> v0.9.22-d11-candidate | B3/B4 + release provenance alignment | notebook contract + bundle tests | themselves | None |
| `tests/integration/test_pilot_canary_execution_path.py` (NEW) | — | 4 integration tests: runs the real CLI dry-run for canary, asserts 6 cells / 2-2-2 repos / 3-3 strategies / rep1=6 / 6 unique ids / 0 calls / 0 tokens / protocol 1.1 | B4 — executable canary coverage | runtime CLI | itself | None |

---

## 4. B1 canary audit

```
BEFORE repos=todo,djangocms
BEFORE scenarios=todo-loc-001,djangocms-cross-007
BEFORE blast_radii=localized
BEFORE executable topology=FAIL (blast_radii filter dropped djangocms-cross-007 (cross_cutting); canary uncallable)

AFTER repos=todo,djangocms,saleor
AFTER scenarios=todo-loc-001,djangocms-cross-007,saleor-loc-001
AFTER blast_radii=localized,cross_cutting
AFTER cells=6
AFTER repo counts=2/2/2
AFTER topology dry-run=PASS
```

```
FULL_PILOT_REPOS=todo,djangocms,saleor
FULL_PILOT_CELLS=48
FULL_PILOT_CHANGED=NO
```

---

## 5. Protocol evaluation

| Profile | Resolved default protocol |
|---|---|
| smoke | 1.0 |
| research | 1.0 |
| scientific-smoke-v1 | 1.0 |
| scientific-smoke-v2 | 1.0 |
| pilot | 1.1 |
| pilot-canary | 1.1 |

Explicit override wins in both directions (proven in `test_cli.py`):
`--protocol-version 1.0` on `pilot` → 1.0; `--protocol-version 1.1` on `smoke`
→ 1.1. Dry-run now emits protocol 1.0 (pre-D11 bug emitted 1.1).

---

## 6. Scientific drift audit — nothing scientific changed

- 12 full-Pilot scenario IDs: **unchanged** (27 total scenario files; pilot profile still resolves exactly the 12 full-pilot scenarios).
- Todo / django CMS / Saleor repository pins: **unchanged** (`benchmark_data/repository_profiles/` and snapshot pins).
- Full Pilot strategies (selective, iterative_repository_agent): **unchanged**.
- Full Pilot repetitions (2): **unchanged** → 48 cells.
- Prompts: **unchanged** (`src/benchmark/prompts/` untouched).
- Ground Truth: **unchanged** (evaluation-only; not touched).
- Metrics: **unchanged**.
- Model Qwen2.5-Coder-14B-Instruct: **unchanged**.
- BNB-NF4 quantization: **unchanged**.
- SDPA/GQA policy (`flash_or_efficient_no_math`, `repeat_kv_sm75`): **unchanged**.
- max attempts 3: **unchanged**.
- completion cap 4096: **unchanged**.
- 12000/64 long-context gate: **unchanged**.
- Pilot timeout 1200 (both strategies): **unchanged** (still 1200 from D10).
- `configs/pilot.yaml`: **unchanged** (already protocol 1.1).

D10.2's canary profile resolution in `seven_arm_benchmark.py` now creates a
`pilot-canary` profile that represents 3 repos; the 48-cell Pilot profile is
bit-identical to D10.

---

## 7. Last-real-run comparison (historical evidence, carried, NOT accepted)

From `05_LAST_KAGGLE_EVIDENCE.md` and the D10 closure:

```
experiment=exp-20260830-134232
source=478261ff595d3d64ed9d5bab32d1cc90d7dabd77
protocol=1.0
timeout=600
planned=48
terminal=48
succeeded=0
failed=48
Todo cells=16
djangoCMS cells=16
Saleor cells=16
Saleor budget-censored=15/16
```

**Why the new canary includes Saleor:**
- The D9.6 exact-artifact real preflight PASSED the Saleor repository preflight.
- Saleor participated in 16 real Pilot cells.
- **15/16 Saleor cells were 600-second budget-censored** in the rejected real Pilot.
- Therefore the corrected (protocol 1.1 / timeout 1200) pilot-canary MUST
  exercise a Saleor local scenario against the real backend before any further
  48-cell GPU spend — Saleor is the most at-risk repository and can no longer
  be represented by a 1-repo todo-only canary.

This rejected run is NEVER reported as accepted benchmark evidence.

---

## 8. Gate results (source-level)

| Gate | Result | Count | Notes |
|---|---|---|---:|---|
| Gate 1 — Dataset Validation | PASS | 152 passed / 4 skipped | plus direct check: 27 total scenarios unique/no dupes; pilot=12 scenarios ×2 strategies ×2 reps=48; canary ids resolve to correct repo/blast |
| Gate 2 — Prompt Validation | PASS | 85 passed | contract + normalization + strategies |
| Gate 3 — Pipeline Smoke | PASS | 289 passed / 1 skipped | |
| Gate 4A — 48-cell pilot dry-run | PASS | 48/48 | fresh dir; 48 unique IDs; repos 16/16/16; strategies 24/24; reps {1:24,2:24}; 0 calls/0 tokens; protocol 1.1; `validate_pilot_dryrun_evidence` PASS |
| Gate 4B — canary dry-run | PASS | 6/6 | repos 2/2/2; strategies 3/3; rep 1:6; 0 calls/0 tokens; protocol 1.1 |
| Gate 4C — exact-artifact pilot dry-run | PASS | 48/48 | bundled exact code/data/notebook from `v0.9.22-d11-candidate`; 0 calls/0 tokens; protocol 1.1 |
| Gate 4D — exact-artifact canary dry-run | PASS | 6/6 | bundled exact; repos 2/2/2; strategies 3/3; rep 1:6; protocol 1.1 |
| Gate 5 — Integration | PASS | canary 4 + notebook contract 104 + deployment bundle 66 + real-launch preflight 14 + d96 boundary 6 + multi-repo production 12 + v0921 validation 24 + repo-env provisioning 28 | `test_pilot_release_provenance.py` runs in the post-alignment phase |
| Gate 6 — Metric Verification | PASS | 254 passed / 9 skipped | |

Re-running a pilot dry-run into the SAME output dir fails closed with
`RunRecordIntegrityError` (expected; first run's records intact).

---

## 9. Full test suite

```
passed=2585
skipped=33
failed=0
duration=~1160 s
```

---

## 10. Candidate artifact audit

```
candidate name=v0.9.22-d11-candidate
code commit=b07da1ae9f8c9b06c532cece81de83681fb79844
anchor-refresh commit=c1c892bb6c11c7cc399dee8e6631ea73a33d61a6
freeze-report commit=224c5a9
source commit (final)=c1c892bb6c11c7cc399dee8e6631ea73a33d61a6
build id=c1c892b
artifact path=dist/pilot-kaggle-upload.zip
artifact SHA-256=4554dced6a438893ed01cbdbce9756613c0b0951459a43eb9a4a467edee4cb8a
sidecar SHA-256=4554dced6a438893ed01cbdbce9756613c0b0951459a43eb9a4a467edee4cb8a
hash match=YES
provenance mismatches=0
exact artifact full dry-run=48/48
exact artifact canary dry-run=6/6
forbidden-content leak count=0
```

D10 candidate `v0.9.22-d10-candidate` (archive `d468ee63...`) is SUPERSEDED
by this D11 candidate. No stable tag created or moved; the retired
`v0.9.22-pilot-exec-ready` tag is untouched.

---

## 11. Independent self-audit

- over-engineering found? **NO** (no new framework, no unrelated refactor/
  rename, no historical docs rewrite, no matrix redesign, no new dependency).
- scientific drift? **NO** (48-cell matrix, prompts, GT, metrics, model,
  quantization, SDPA/GQA policy unchanged).
- stale current-state docs? **NO** — AGENTS.md / SYSTEM_STATE.md / TODO.md /
  README.md / START_HERE.md / PROJECT_HANDOFF.md / MASTER_IMPLEMENTATION_PLAN.md
  / PILOT_KAGGLE_RUNBOOK.md / PROJECT_HEALTH_REPORT.md / latest_phase_report.md
  current-state capsules updated to D11; one concise current truth + link to
  this report.
- protocol leakage? **NO** — profile-derived defaults; explicit override wins.
- canary executable? **YES** — executable integration test + exact-artifact
  canary dry-run both 6/6.
- Saleor represented? **YES** — saleor-loc-001 in the canary matrix.
- exact artifact equivalent to source? **YES** — provenance-verified, 0
  mismatches, sidecar matches.

---

## 12. Truthful release status

- The stable tag `v0.9.22-pilot-exec-ready` is NOT moved/re-created; it still
  peels to `478261ff...` and remains retired as a launch candidate.
- `exp-20260830-134232` is REJECTED and never resumed or counted.
- `exp-20260828-151335` has zero accepted RunRecords and must never be resumed.
- Scientific version remains **v0.9.22** (never v0.9.23).
- The D11 candidate is **NOT a launch basis** — the next real Pilot launch
  needs its own real pilot-canary pass and its own tag decision.

---

## 13. What remains

1. Push all D11 commits (code `b07da1a`, anchor refresh `c1c892b`, freeze
   report `224c5a9`, release-tag alignment, doc/closure commits) to origin and
   verify HEAD/origin parity.
2. Export the `project-YYYY-MM-DD-HHmm.zip` audit ZIP outside the project
   folder and verify its contents/SHA.
3. (External) upload the exact `v0.9.22-d11-candidate` artifact to Kaggle;
   run the required real preflight (repo preflight, SDPA/GQA microprobe,
   generation-deadline canary, short + 12k probes).
4. (External) run the **6-cell real pilot-canary only** (`pilot-canary-cell`).
5. Validate the real canary evidence with the canonical fail-closed gate.
6. Only on PASS, make the candidate's own stable-tag decision.
7. Then launch the 48-cell Pilot.

---

## 14. Files

- Freeze: `reports/pilot_notebook_trust_freeze.json` (source
  `c1c892b…`, `v0.9.22-d11-candidate`, archive `4554dced…`).
- This report: `reports/V0922_D11_PILOT_CANARY_SALEOR_INCLUSIVE_CLOSURE_REPORT.md`.