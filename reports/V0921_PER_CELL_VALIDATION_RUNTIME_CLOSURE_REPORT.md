# PILOT-EXEC-01 — v0.9.21 Per-Cell Validation Runtime Closure Report

**Task:** PILOT-EXEC-01-V0921-PER-CELL-VALIDATION-RUNTIME-CLOSURE
**Branch:** `fix/pilot-v0921-per-cell-validation-runtime-closure` (from `origin/main` `ade4995557fa97c8efd39cf4a9afc8c89c55fdea`)
**Status:** COMPLETE — RELEASED as `v0.9.21-pilot-exec-ready`
**Frozen scientific contract:** UNCHANGED (model `Qwen/Qwen2.5-Coder-14B-Instruct`, bnb-nf4, 12 scenario IDs, strategies, repetitions, 48 cells, prompts, metrics, repository pins, frozen validation command paths/scope, model/request timeout 600 s, max attempts 3, completion cap 4096, Ground Truth)

---

## 1. Blockers and closures

### B1 — Wrong per-cell validation interpreter routing — CLOSED

The v0.9.20 scientific runner resolved every frozen validation command with
`frozen.resolve_interpreter(sys.executable)`, while the notebook preflight
provisions Todo=benchmark interpreter, django CMS=
`pilot_envs/djangocms/bin/python`, Saleor=`pilot_envs/saleor/.venv/bin/python`.
Saleor dependencies are deliberately isolated from the benchmark/model
interpreter.

Fix: repeatable `--validation-python repo_id=path` CLI flag
(`parse_validation_python_args`: duplicates/malformed fail closed;
non-dry-run interpreters must exist) +
`resolve_frozen_validation_runtime()` which fails closed on missing mappings,
rejects non-existent interpreters, asserts the resolved argv starts with the
provided interpreter, and returns the frozen env verbatim. Resolution happens
in `main()` before execution-plan creation / model initialization.

### B2 — Frozen validation env discarded — CLOSED

`FunctionalValidator.validate(...)` now accepts optional `env` overrides and
executes with `os.environ.copy()` + overrides (parent `os.environ` never
mutated). `PipelineConfig.validation_env` → `RunnerConfig.validation_env` →
Stage 3 pass the per-repository `frozen.env_dict()`: Todo `{}`, django CMS
`{"DATABASE_URL": "sqlite://localhost/testdb.sqlite"}`, Saleor the exact four
frozen values (`DATABASE_URL`, `CACHE_URL`, `SECRET_KEY`, `TZ`).

### B3 — Validation timeout below measured target runtime — CLOSED

New `--validation-timeout` (positive integer enforced in argparse gate,
`PipelineConfig.__post_init__`, `RunnerConfig.__post_init__`; legacy default
180 preserved for non-Pilot compatibility). The frozen Pilot notebook launch
AND resume cells pass `--validation-timeout 1800` plus all three
`--validation-python` mappings; the dry-run cell intentionally does not.
Target evidence: full pristine Saleor primary ran **941.42 s** on target-shaped
Linux CI (< 1800 s budget, >2x margin over the 180 s legacy cap). The
scientific model/request `--timeout 600` is untouched.

## 2. RED/GREEN evidence

- **RED (B2):** with the v0.9.20 `FunctionalValidator` restored, all four
  env-propagation tests fail (no `env` parameter; overrides never reach the
  subprocess): `4 failed in 0.33s`.
- **RED (B1):** precondition recorded inside
  `test_missing_mapping_fails_closed_no_sys_executable_fallback` — the old
  path resolves `argv[0] == sys.executable` silently; the new helper raises.
- **GREEN:** 24/24 new regression tests pass; full suite
  **2370 passed / 33 skipped / 0 failed**.

## 3. Target-shaped CI Gates (real Linux, real subprocesses)

Run **32692489617** (branch code state) and **32694137255** (final released
source state) — both SUCCESS:

- **Gate 1 PASS** — production `FunctionalValidator` on real staged targets
  with provisioned interpreters + exact frozen env: Todo test file exit 0;
  django CMS `cms.tests.test_api` exit 0 (2.40 s); Saleor capability nodeid
  exit 0.
- **Gate 3 PASS** — actual `resolve_frozen_validation_runtime` contract:
  commands begin with provisioned interpreters and carry the frozen env (no
  substring mocks).
- **Gate 2 PASS** — full pristine Saleor primary from the existing complete
  no-model preflight: exit 0, duration **941.42 s < 1800 s**.
- Complete frozen no-model preflight: overall=PASS.

Evidence artifacts uploaded per run (`per-cell-validation-parity.json`,
`pilot-target-preflight.json`).

## 4. Release identity

- Accepted release: **`v0.9.21-pilot-exec-ready`**
  @ annotated tag peel == artifact source commit == merge
  **`e308047c9c05f38316d80ce565bac1b51d105bfa`** (tag pushed).
- Archive: `dist/pilot-kaggle-upload.zip` SHA-256
  **`62e377467e225d336cbcaa70a2c610b5080e329e1a4e6578fbcbdc1af7dbee40`**
  (+ `.sha256` sidecar verified equal).
- Trust validator: **0 mismatches**; source-commit provenance gate:
  **0 mismatches** (run with `--verify-source-provenance`).
- Exact-artifact dry run: **48/48 terminal / 48 succeeded / 0 failed /
  48 unique IDs; todo 16 / djangocms 16 / saleor 16;
  iterative_repository_agent 24 / selective 24; rep1 24 / rep2 24; 0 model
  calls / 0 tokens.**
- Full suite at freeze states: **2370 passed / 33 skipped / 0 failed**.
- Branch freeze `b6837d06…`; idempotent re-freeze at the merge produced the
  released archive above (anchors content-derived, unchanged).

## 5. v0.9.20 status correction

`v0.9.20-pilot-exec-ready` remains internally trustworthy with a GREEN
no-model target-shaped preflight, but it was **never accepted for Real Pilot
launch**: the independent audit found exactly this per-cell validation runtime
parity seam (B1/B2/B3). v0.9.21 supersedes it as the launch candidate.

## 6. Known open items

- None blocking launch. The next task is the real Kaggle v0.9.21 session:
  fresh target preflight, then the accepted 48-cell Pilot in the same session
  if every target gate passes.
