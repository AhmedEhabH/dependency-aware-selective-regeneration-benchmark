# PILOT-EXEC-01 — v0.9.20 Root-Cause Closure Report

**Task:** PILOT-EXEC-01-V0920-ROOT-CAUSE-CLOSURE
**Branch:** `fix/pilot-v0920-saleor-preflight-root-closure` (from `origin/main` `aaf80efc34a1c280b3f189d791f8dafb3030383f`)
**Status:** IN PROGRESS — code/test/policy complete; target-shaped CI evidence being collected
**Frozen scientific contract:** UNCHANGED (model `Qwen/Qwen2.5-Coder-14B-Instruct`, bnb-nf4, 12 scenario IDs, strategies, repetitions, 48 cells, prompts, metrics, repository pins, timeout 600 s, max attempts 3, max completion tokens 4096, Ground Truth, regression-obligation scope)

---

## 1. Real Kaggle v0.9.19 failure (target evidence)

The executed v0.9.19 Kaggle notebook passed repository snapshot verification,
PostgreSQL 15 bootstrap, Saleor DB connection probe, Redis service, repository
environment provisioning, Todo validation and django CMS validation — then
failed at the Saleor fast capability gate:

- Saleor gate exit code `5` (Pytest: **no tests collected**);
- services reachable, `failed_count = 0`, `failed_nodeids = []`;
- log contained only the Pytest warning summary;
- Real Pilot never started (cells through execution count 8 only).

## 2. Exact root cause

`scripts/pilot_repo_snapshot.py::run_repo_preflight(...)` built the fast-gate
argv by appending a second `-m pytest ...` vector onto
`command.resolve_interpreter(venv_python)` — which already resolves the ENTIRE
frozen primary command (`<python> -m pytest -m "not e2e" -q -n logical
<5 saleor paths>`). Pytest parsed the second `-m pytest` as a MARKER
EXPRESSION (`-m pytest`), filtering out the single gate nodeid → exit 5.

## 3. Why local validation was false-green

`tests/unit/test_pilot_repo_snapshot.py`'s fake subprocess returned success
whenever `"test_create_checkout"` appeared anywhere in the joined argv. The
malformed command still contained that substring → PASS. It proved substring
presence, not executable-command validity. Introduced in commit
`bbc5b43e76d7524aa6a82a085db2cf34e26bab78`.

## 4. Fix (Tasks A–D)

1. **Exact standalone argv** (`run_repo_preflight`): the gate is now
   `[venv_python, -m, pytest, -n, 0, -x, --tb=line, --no-header, -q,
   <gate nodeid>]`; `resolve_interpreter()` is no longer reused.
2. **Fail-fast invariant** before `_run_command`: `RuntimeError("invalid
   Saleor capability-gate argv")` unless `count("-m") == 1` and
   `argv[1:3] == ["-m", "pytest"]`.
3. **False-green mock removed**: the unit fake now requires the exact full
   argv (first token, exact `python -m pytest`, exact nodeid), rejects a
   duplicate `-m`, rejects inherited primary test paths, and rejects the
   marker expression `pytest`.
4. **Exact-argv contract test**
   (`tests/integration/test_pilot_real_launch_preflight.py::
   TestPreflightRunnerPath.test_saleor_validation_runs_from_staged_root_with_provided_venv_python`)
   asserts the complete gate argv list plus `count("-m") == 1`,
   `argv[2] == "pytest"`, `"not e2e" not in argv`.

### RED/GREEN proof (acceptance §9)

- **RED** — with the v0.9.19 construction restored
  (`git show origin/main:scripts/pilot_repo_snapshot.py`) and the new tests in
  place: `2 failed, 21 passed`
  (`test_saleor_validation_runs_from_staged_root_with_provided_venv_python`
  argv mismatch: left contained the inherited primary paths;
  `test_run_repo_preflight_writes_diagnostics_without_touching_primary_verdict`
  argv mismatch at index 3 `-q != -n` — the malformed concatenation).
- **GREEN** — with the fix restored: `36 passed` (both suites).
- **Target-shaped CI proof** — GitHub run **32650273641** (Linux, real
  subprocesses): `Saleor fast capability gate: PASS`,
  `1 test collected` for
  `saleor/graphql/checkout/tests/benchmark/test_checkout_mutations.py::test_create_checkout`,
  Todo PASS (47 tests), django CMS PASS (382 tests). Evidence tracked at
  `reports/target-evidence/run-32650273641/`.

## 5. Task E — gate nodeid exists in the frozen snapshot

CI run 32650273641 step "Collect exact Saleor capability gate" ran a REAL
`pytest -n 0 --collect-only -q <nodeid>` against the pinned bundled Saleor
snapshot (`e11a5557…`): `1 test collected` +
grep match on the exact nodeid (`saleor-gate-collect.log`).

## 6. Task F — full pristine Saleor baseline: RESOLVED (case 1 — exits 0)

The exact frozen pristine Saleor primary command was executed end-to-end on
target-shaped Linux CI (run **32672656326**, real subprocesses, pinned
snapshot `e11a5557…`, PostgreSQL+Valkey reachable):

```
overall: PASS
  todo:       exit 0 (8.51 s)
  djangocms:  exit 0 (24.32 s)
  saleor:     gate PASS; primary exit 0 (775.71 s); makemigrations --check exit 0
```

Evidence archived at `reports/target-evidence/run-32672656326/`
(`pilot-target-preflight.json`). Per the package rule — "If it exits 0:
record evidence; no extra policy is needed" — the historically documented
nondeterministic order/pricing cluster did NOT appear in the target-shaped
environment, so no baseline-flake profile is required for v0.9.20.

### Baseline-flake policy machinery (implemented, tested, armed-if-evidenced)

Because Gate 9 (`reports/PILOT_EXEC_01_GATE9_ENGINEERING_PREFLIGHT_LEDGER.md`)
recorded 38/33/36 pristine order/pricing failures on other environments, the
evidence-backed classification machinery is implemented exactly per spec and
is exercised by 13 hermetic tests:

- `--emit-baseline-profile PATH` writes the versioned evidence artifact
  (`schema=pilot_saleor_baseline_flaky_profile.v1`; Saleor SHA; frozen
  command; environment versions; full-run exit code/duration; exact failed
  nodeids; per-nodeid serial rerun verdicts; created_utc; source commit;
  platform) — emission NEVER changes any verdict.
- `--baseline-profile PATH` loads + fail-closed-validates the profile
  (schema, Saleor pin SHA, exact frozen command, one serial-PASSING rerun per
  nodeid). A pristine primary failure is classified ONLY when every observed
  nodeid is already in the profile AND still passes a current serial `-n 0`
  rerun. Any new nodeid (`FAILED_UNCLASSIFIED_NODEIDS`), any deterministically
  re-failing nodeid (`FAILED_DETERMINISTIC_SERIAL_FAILURES`), or a missing
  cache (`NOT_CLASSIFIED_NO_LASTFAILED`) fails closed. Raw command truth is
  always preserved (`command_passed=False`, exit codes intact); classification
  is recorded explicitly in `baseline_classification`. Todo/django CMS paths
  untouched; no directory allowlists.
- If a future pristine run exhibits the cluster, the workflow emits
  `fresh-saleor-baseline-profile.json`; committing it as
  `reports/pilot_saleor_baseline_flaky_profile.json` ships it at
  `code/reports/…` and automatically arms the deployed preflight cell. Without
  a committed profile both the CI gate and the deployed cell stay strictly
  fail-closed.

## 7. Target-shaped pre-release CI gate (package file 04)

`.github/workflows/pilot-preflight-target-shape.yml` runs the exact no-model
preflight path on Linux: checkout → deps → PG15+Redis → build exact candidate
artifact → contract tests → repo-env provisioning → real `--collect-only` gate
proof → complete frozen preflight (Todo, django CMS, Saleor fast gate + full
primary) → machine-readable evidence upload. No model download; no 48-cell
benchmark. Per-command timeout 14400 s / job cap 330 min is CI harness headroom
only (the 2-core runner executed only ~36% of the Saleor suite in 3600 s in run
32650273641); the frozen command, paths and the notebook's own budget are
unchanged.

## 8. Verification performed (final release state)

- Full suite: **2346 passed / 33 skipped / 0 failed** (twice: pre-freeze and
  post-freeze states).
- Release-constant suites after finalize: notebook contract + deployment
  bundle + provenance + repo-env provisioning + real-launch preflight +
  snapshot unit = **210 passed**.
- `git diff --check` clean; Ruff clean on changed files; mypy strict clean on
  changed production files; compileall clean.
- Branch freeze at `fdbc79e` (archive `cf57b475…`), then idempotent re-freeze
  AT the merge commit with `--verify-source-provenance`:
  archive **`56b1c2a9019a03892ce627321b9a415795ac95836ac415694bbc0995263c8024`**,
  notebook anchors unchanged (content-derived, as designed).
- Exact-artifact dry run: **48/48 terminal, 48 succeeded, 0 failed, 0 pending,
  48 unique run IDs; todo 16 / djangocms 16 / saleor 16;
  iterative_repository_agent 24 / selective 24; rep1 24 / rep2 24; 0 model
  calls.**
- Trust/provenance on the final artifact: identity source_commit ==
  merge/tag peel `febda79…`; embedded notebook trust validator **0
  mismatches**; source-commit provenance gate **0 mismatches**; archive SHA ==
  sidecar.

## 9. Release state (FINAL)

- **ACCEPTED RELEASE: `v0.9.20-pilot-exec-ready`**
  @ annotated tag peel == artifact source commit == merge
  **`febda7938db1284da4090d35e980db472149c3ad`**; main pushed
  (`a73c952` = post-tag docs/evidence child); tag pushed.
- Archive: `dist/pilot-kaggle-upload.zip` SHA-256
  **`56b1c2a9019a03892ce627321b9a415795ac95836ac415694bbc0995263c8024`**
  (+ `.sha256` sidecar, verified equal).
- Target-shaped no-model preflight evidence:
  - run **32650273641**: fixed fast gate PASS on real Linux (exact nodeid
    collected); exposed the CI-budget issue;
  - run **32672656326**: COMPLETE frozen preflight overall=PASS — pristine
    Saleor primary exit 0 in 775.71 s (Task F case 1);
  - run **32676588800**: fully green preflight on the exact released source
    state (post freeze/constants).
- Real Pilot: **NOT STARTED**. Next action: fresh Kaggle v0.9.20 target
  preflight with this artifact; if all target gates pass, launch the accepted
  48-cell Pilot in the same session.

## 10. Known open items (documented, not opened)

- Per-cell generated-workspace validation resolves the same frozen manifest
  command (`seven_arm_benchmark.py` ~line 2131) with
  `validation_timeout=180`; the full Saleor suite needs far longer, so real
  Pilot Saleor cells would time out at Stage 3 baseline_validation. This is a
  distinct integration seam for the NEXT task (it cannot be closed without
  touching the scientific execution path, which is out of scope here).
