IMPLEMENTATION_MODEL_USED=opencode/big-pickle

# v0.9.22 D12 — NOTEBOOK ORCHESTRATION FIX CLOSURE REPORT (PILOT-EXEC-01)

**Report Date:** 2026-09-01
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`
**Task Pack:** `_workspace/active/00_EXECUTE_D12_NOTEBOOK_ORCHESTRATION_FIX.md`
**Builds:** `83d15dd` (code + RED regression test) → `84acb8b` (notebook anchor refresh + freeze report) → `f960abe` (provenance-verified freeze report) → `fb84073` (release-tag constants)

---

## 1. Executive summary

D12 fixes the verified in-flight notebook-orchestration blocker that would have
prevented the pilot-canary from running as an independent notebook stage:
`pilot-canary-cell` (cell **20**) reads `SCRIPT_PATH` but only `dryrun-cell`
(cell **22**) defined it, so any notebook execution that started at the canary
cell (after the archive-verify cell provisions code + data, before the full
48-cell launch) raised **`NameError: name 'SCRIPT_PATH' is not defined`**.

The single canonical
```python
SCRIPT_PATH = CODE_DIR / "seven_arm_benchmark.py"
```
plus the multiline `FileNotFoundError("seven_arm_benchmark.py missing after
provisioning: ...")` guard now lives in `pilot-archive-verify-cell` (cell **4**),
after the `CODE_DIR` existence checks and **before ANY use**. The duplicate
definition/guard in the dry-run cell was **deleted** so there is exactly **one**
definition cell — enforced by new integration tests
(`TestD12ScriptPathOrchestration`, 4 tests).

**Scientific inputs are UNCHANGED:** model Qwen2.5-Coder-14B-Instruct (BNB-NF4,
SDPA, kernel policy `flash_or_efficient_no_math`, GQA compat `repeat_kv_sm75`),
12 scenarios, 3 repo pins (Todo / django CMS / Saleor), 2 strategies (selective,
iterative_repository_agent), 2 repetitions = 48 cells, prompts, Ground Truth,
metrics, max attempts 3, completion cap 4096, the 12000/64 long-context gate,
Pilot timeout 1200, protocol 1.1.

**No stable-tag move and no real Pilot launch happens in this closure.** The
D12 candidate artifact `v0.9.22-d12-candidate` is **built + provenance-verified
FROZEN** (0 mismatches) but is **NOT a launch basis**: the next real Pilot
launch requires a real pilot-canary pass on this (or a fresh exact) candidate
with its own tag decision. The D11 candidate (`v0.9.22-d11-candidate`, archive
`4554dced…`) is **SUPERSEDED** by this D12 candidate.

---

## 2. The blocker, RED then GREEN evidence

```
BLOCKER=D12 (SCRIPT_PATH undefined before first canary use)
RED_TEST=tests/integration/test_pilot_notebook_contract.py::TestD12ScriptPathOrchestration (4 tests)
RED_RESULT=FAIL on the D11 baseline:
  1) SCRIPT_PATH first defined in cell 22 (dryrun-cell) but used in cell 20 (pilot-canary-cell)
  2) pre-definition code references pre-defined SCRIPT_PATH use in cell 20
  3) pilot-archive-verify-cell (cell 4) missing the canonical SCRIPT_PATH def + FileNotFoundError guard
  4) ast.parse of all code cells succeeded (the notebook is syntactically VALID, so the NameError
     only fires at execution time — a semantically-hidden orchestration defect)
  observed: 3 FAIL / 1 PASS
FIX=D12 move the single canonical SCRIPT_PATH def + FileNotFoundError guard into pilot-archive-verify-cell
  (cell 4, after CODE_DIR existence checks, before ANY use); DELETE the duplicate def/guard from dryrun-cell
  (cell 22); exactly-one definition cell.
GREEN_TEST=TestD12ScriptPathOrchestration (4 tests) after the fix
GREEN_RESULT=PASS 4/4
EDGE_CASES=notebook remains valid JSON; cell ids unchanged; all 17 code cells ast.parse clean;
  the canary can now run as an independent stage immediately following the archive-verify cell
```

---

## 3. Validation gates (all PASS)

| Gate | Scope | Result |
|------|-------|--------|
| G1 | Dataset validation | **267 passed / 4 skipped** |
| G2 | Prompt validation | **101 passed / 4 skipped** |
| G3 | Pipeline smoke | **722 passed / 14 skipped** |
| G4 | Dry-runs | source pilot **48/48** + source canary **6/6** + exact-artifact pilot **48/48** + exact-artifact canary **6/6**; protocol 1.1, 0 model calls, 0 tokens; canonical `validate_pilot_dryrun_evidence` PASS |
| G5 | Integration | **258 passed** |
| G6 | Metrics | **329 passed / 10 skipped** |

### G4 exact-artifact dry-runs (`--source-commit 84acb8b… --source-tag v0.9.22-d12-candidate --deployed-build-id 84acb8b`)

- **Pilot 48/48:** repos `{djangocms:16, saleor:16, todo:16}`, strategies
  `{iterative_repository_agent:24, selective:24}`, reps `{1:24, 2:24}`,
  0 calls / 0 tokens; every record + `source_identity.json` == `84acb8b…` +
  `v0.9.22-d12-candidate` + build `84acb8b`; canonical
  `validate_pilot_dryrun_evidence(... expected_deployed_build_id='84acb8b')` PASS.
- **pilot-canary 6/6:** repos `{todo:2, djangocms:2, saleor:2}`, strategies
  `{iterative_repository_agent:3, selective:3}`, reps `{1:6}`, 0 calls / 0
  tokens, protocol 1.1, model `dry-run:mock`.

---

## 4. Freeze / provenance

Two-pass finalizer (`scripts/finalize_pilot_notebook_trust.py`) with
`--verify-source-provenance`:

- Pass 1 (source `83d15dd`): wrote notebook `FROZEN_SOURCE_TAG =
  "v0.9.22-d12-candidate"` and the freeze report; committed `84acb8b`.
- Pass 2 (source `84acb8b`, created-utc `2026-09-01T18:40:35+00:00`):
  **0 mismatches**, final archive **`812d37555a42f8fbdfbbb2e5441c814fb733cfd424ca75c810ead96a0bc4346a`**
  (+ sidecar verified).

- **Candidate tag:** `v0.9.22-d12-candidate`
- **Frozen source commit:** `84acb8bb01bbae28d6bab260d029af539c80a229`
- **Deployed build id:** `84acb8b`
- **Created-utc:** `2026-09-01T18:40:35+00:00`
- **Archive SHA-256:** `812d37555a42f8fbdfbbb2e5441c814fb733cfd424ca75c810ead96a0bc4346a`
- **Freeze report:** `reports/pilot_notebook_trust_freeze.json` (status FROZEN)

Release-tag constants aligned to `v0.9.22-d12-candidate` in six test files
(canary_viability 9, notebook_contract 2, deployment_bundle 2, d96 1,
release_provenance 1, repo_env 1) at commit `fb84073`.

---

## 5. Full test suite

```
2589 passed / 33 skipped / 0 failed
```

D11 was `2585 passed / 33 skipped / 0 failed`; the **+4** is exactly the new
`TestD12ScriptPathOrchestration` regression. Nothing else changed.

---

## 6. Required truthful status

- This candidate is **NOT a launch basis**: the next REAL Pilot launch requires
  a real pilot-canary pass on this or a fresh exact candidate with its own tag
  decision.
- The retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff…`) and the
  `edae1b7e…8c4a` artifact are NOT reused.
- The D11 candidate (`v0.9.22-d11-candidate`, archive `4554dced…`) is
  **SUPERSEDED** by this D12 candidate.
- Never resume `exp-20260828-151335` (zero accepted RunRecords);
  `exp-20260830-134232` remains REJECTED (48/48 terminal failures).
- Scientific version stays **v0.9.22** (never v0.9.23); scientific inputs
  unchanged.

---

## 7. Decision log

Appended **Decision D036** (`DECISION_LOG.md`).
