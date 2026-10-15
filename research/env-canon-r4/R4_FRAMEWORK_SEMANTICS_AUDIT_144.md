# R4 Framework-Semantics Audit over the frozen Full-D7 population (144 units / 219 tasks)

- **Mission:** `M17_D7_R4_FRAMEWORK_SEMANTICS_AUDIT_144`
- **Mission type:** read-mostly scientific audit, additive evidence only
- **Audit date (UTC):** see `generated_utc` in `R4_FRAMEWORK_SEMANTICS_AUDIT_144.json`
- **Terminal verdict:** `PASS_FRAMEWORK_SEMANTICS_AUDIT_READY_FOR_PHASE2`
- **Repair performed:** **NONE** (explicitly out of scope; Phase 2 only)

---

## 1. Executive verdict

Every exact historical target commit in the frozen Full-D7 population was
audited deterministically against the current hardcoded framework gate
(`python manage.py check --settings=saleor.tests.settings`) using Git-object
evidence from the local WSL Saleor object store.  The audit found:

- **2 distinct historical framework-semantics signatures** across the 219
  distinct target commits.
- **1 commit (8220a53473bb, Unit 56) is the ONLY commit whose repository tree
  lacks `saleor/tests/settings.py`** and instead authors pytest with the
  top-level `tests.settings` module.  This is exactly the Unit-56
  `ENV_FRAMEWORK_GATE_FAILURE` observed in the canonical successor run.
- **143/144 validation units** are `CURRENT_GATE_MATCH` (their commits all
  author `saleor.tests.settings`, and that module exists in each exact tree).
- **Unit 56 only** is `CURRENT_GATE_MISMATCH`.
- **0 units** are `SEMANTICS_UNRESOLVED` (all historical semantics are
  statically resolvable from repository evidence).
- **No unit among 1..55 shares the Unit-56 mismatch.**  Every unit 1..55 that
  passed ran under a gate whose forced settings module exists in its exact
  repository tree; therefore no previously-passed unit was gated on a
  repository semantics that its own revision does not author.
- **No unit among 57..144 is predicted to hit the same mismatch** (they all use
  modern-layout commits).
- The Unit-56 failure is **an isolated, population-wide-unique historical
  layout outlier** — not an era transition and not a widespread signature.

The hardcoded gate command was first introduced into the R4 N12 runner lineage
on 2026-10-12/13 (see §10).  The 12-unit behavioral calibration and all prior
R4-A/B/C/D/E, I5/I6 and N12 gates were executed against calibration
populations that contain **no legacy-layout commit**, which is why the
dimension was not previously detected.

No scientific unit was executed, no Docker was invoked, no network acquisition
occurred, and the canonical failed run was left untouched.

---

## 2. Authorities and frozen inputs

| Authority | Value / path |
|---|---|
| Frozen source HEAD (this worktree) | `def15aefde83ba9d590133b5215413bff183aa11` |
| Worktree branch | `parallel/r4-framework-semantics-audit-2026-10-15` |
| Full144 successor refreeze worktree | `D:\WP2\active\r4-full144-successor-refreeze` (untouched) |
| Canonical failed successor run | `D:\WP2\runs\r4-full-d7-144-successor-2026-10-15` (untouched) |
| Pre-execution freeze | `...\freeze\PRE_EXECUTION_FREEZE.json` |
| Population identity (expected) | `ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac` |
| Ordered membership hash (expected) | `8eb4a7242e12bb03715adac5fffdea2e4340585843fc137ececd38952ad6a19e` |
| Accounting | 144 validation units / 219 member tasks / 219 distinct target commits |
| WSL Saleor object repo | `/opt/wp2_v2/saleor-cache` (Ubuntu-24.04) |
| Current behavioral runner | `scripts/r4_behavioral_calibration_n12_r2.py` |
| Current Full144 driver | `src/benchmark/wp2/full144/driver.py` |
| R4-C tree authority | `src/benchmark/wp2/env_r4/linux_tree_materialize.py` |

All frozen identities were verified in STEP A before any audit work began.

---

## 3. Exact audit method

The audit is fully deterministic and evidence-backed:

1. **Population/order authority** is read from
   `research/env-canon-r4/R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json`
   (same authority the Full144 driver uses).  Identity and ordered-membership
   hashes are recomputed and checked (144 units / 219 tasks / 219 distinct
   commits).
2. **Git-object probe** — for each distinct target commit, a deterministic bash
   probe is run inside WSL against `/opt/wp2_v2/saleor-cache` using only
   `git cat-file -e`, `git show` and `git show -s` (no worktree, no checkout,
   no Docker).  It records, per commit: existence of `manage.py`, `setup.cfg`,
   `pytest.ini`, `pyproject.toml`, `tox.ini`, `saleor/settings.py`,
   `tests/settings.py`, `saleor/tests/settings.py`, `saleor/__init__.py`,
   `tests/__init__.py`, `saleor/tests/__init__.py`, `conftest.py`, the commit
   date, and the raw file contents (base64) of `manage.py`, `setup.cfg`,
   `pytest.ini`, `pyproject.toml` and `tox.ini`.
3. **Semantics extraction** — pure, deterministic Python extracts:
   - manage.py `DJANGO_SETTINGS_MODULE` behavior (setdefault-literal /
     assign-literal / environment-dynamic / none);
   - pytest `--ds=<module>` values from all config files;
   - mypy-django `django_settings_module` references;
   - tox.ini authored manage commands.
4. **Signature classification** — a stable signature is derived from
   evidence-only fields (`manage_py_present`, `manage_default_settings_module`,
   `repo_pytest_settings_module`, `current_forced_manage_settings_exists`,
   `current_manage_semantics_matches_repository`, `settings_layout_family`).
5. **Impact sets** — per unit, the commit-level semantics are aggregated into
   `CURRENT_GATE_MATCH` / `CURRENT_GATE_MISMATCH` / `SEMANTICS_UNRESOLVED`.
6. **Evidence files** are written under `research/env-canon-r4/` (see §12) and
   hashes recorded.

Classification is never inferred from naming: dotted module names are mapped to
exact Git-tree paths and verified with `git cat-file -e`.

### Determinism

Re-running the audit from the frozen probe evidence produces a byte-identical
`deterministic_payload_sha256` (only `generated_utc` is excluded).  Verified:
the payload hash is stable across two consecutive runs
(`61a92159a8eba7c5bcf151011d6baa72548234bf95d9bc0168f04bca58c43c56`).

---

## 4. Population coverage

- 144/144 validation units audited (1..144, exact frozen order).
- 219/219 member tasks accounted for (one distinct target commit per task;
  219 distinct commits total).
- Strata distribution (Full-D7 runtime strata):
  `3.12_poetry=25, 3.12_uv=21, 3.8_poetry=15, 3.9_poetry=83`.
- Every one of the 219 distinct target commits resolves locally in the WSL
  Saleor object store (`git cat-file -e <commit>^{commit}` PASS, 0 missing).
- Every settings-module existence claim is backed by Git-tree evidence.

---

## 5. Historical framework-semantics signatures

Two signatures were found (defined from evidence only):

| Signature | Commits | manage.py default | Repo pytest `--ds` | `saleor/tests/settings.py` in tree | Layout family | Current manage-gate semantics |
|---|---|---|---|---|---|---|
| `ce2098d479b46173` | 218 | `saleor.settings` | `saleor.tests.settings` | present | `SALEOR_PACKAGE_TESTS_SETTINGS` | **MATCH** |
| `9b783a672de2042b` | 1 (`8220a534...`) | `saleor.settings` | `tests.settings` | absent | `TOP_LEVEL_TESTS_SETTINGS` | **MISMATCH** |

### Commit-time range (local Git evidence)

- Signature `ce2098d479b46173`: 218 commits, spanning 2020-06-09 … 2026-08-05
  (the modern layout is present across the entire historical range — this is
  the dominant, universal layout of the population).
- Signature `9b783a672de2042b`: the single commit `8220a53473bb...`
  (author date 2020-05-20).

### Unit/task membership

- `ce2098d479b46173` → **143 units / 218 tasks**.
- `9b783a672de2042b` → **Unit 56 only** (`vu-cdcf3222cbb5`,
  task `saleor-rc-8220a53473bb`).

There is **no era-transition**: the modern `saleor.tests.settings` layout
appears in commits from 2020 through 2026, and the legacy top-level
`tests.settings` layout appears exactly once.  The Unit-56 commit is the sole
outlier of the entire population.

---

## 6. Current harness mismatches

The current framework gate in `scripts/r4_behavioral_calibration_n12_r2.py`
(line 861) runs:

```
python manage.py check --settings=saleor.tests.settings
```

This imposes the assumption that `saleor.tests.settings` is a valid, importable
Django settings module in the materialized worktree.  That assumption:

- **holds** for 218/219 commits (`saleor/tests/settings.py` exists and is the
  repository-authored pytest settings module) → `CURRENT_GATE_MATCH`;
- **does not hold** for 8220a534 (the tree instead authors `tests/settings.py`
  at top level) → `CURRENT_GATE_MISMATCH`, and exactly reproduces the observed
  Unit-56 `ModuleNotFoundError: No module named 'saleor.tests'`.

The pytest smoke gate (`python -m pytest --collect-only -q`, line 868) does
**not** force a settings module; it inherits the repository-authored `--ds`
config, which resolves inside every exact tree — therefore the pytest smoke
semantics agree with repository-authored pytest configuration for **all** 219
commits (confirmed empirically: Unit 56's `pytest_wt0=0`).

The import smoke (`python -c "import saleor"`, line 857) requires the `saleor`
package; `saleor/__init__.py` is present in 219/219 commits → universal.

### Hardcoded-assumption inventory (STEP E)

| # | Assumption (current harness) | Classification | Population evidence |
|---|---|---|---|
| 1 | `import saleor` succeeds (package exists & imports) | HISTORICALLY_UNIVERSAL | `saleor/__init__.py` in 219/219 |
| 2 | `manage.py` exists at repo root (else MANAGE_RC=SKIP) | HISTORICALLY_UNIVERSAL | `manage.py` in 219/219 |
| 3 | Forced manage settings `saleor.tests.settings` is a valid settings module | **HISTORICALLY_FALSE_FOR_SOME_POPULATION** | `saleor/tests/settings.py` in 218/219; absent in 8220a534 (Unit 56) |
| 4 | pytest runs only when `pytest.ini` OR `pyproject.toml` exists | HISTORICALLY_CONDITIONAL | pyproject.toml in 219/219; pytest.ini in 0/219 |
| 5 | pytest `--collect-only` inherits repo-authored `--ds` (no forced module) | HISTORICALLY_UNIVERSAL | repo `--ds` resolves in every exact tree |
| 6 | working directory = each materialized worktree root | HISTORICALLY_UNIVERSAL | manage.py + configs at root of every exact tree |
| 7 | smoke rc parsing maps 1:1 (no silent remap) | HISTORICALLY_UNIVERSAL | markers parsed verbatim per worktree |

**Assumptions requiring Phase-2 review:** #3 (the forced manage settings
module) is the only assumption that is false for part of the population.  #4 is
conditional but currently satisfied by the entire population.

---

## 7. Unit-56 explanation

Unit 56 (`vu-cdcf3222cbb5`, calibration index 56, task
`saleor-rc-8220a53473bb`) targets the single legacy-layout commit
`8220a53473bb67bbb247490cbd043c56dac4568c`.

In that exact revision:

- `manage.py` exists and sets `DJANGO_SETTINGS_MODULE = saleor.settings`
  (setdefault-literal);
- `setup.cfg` configures pytest with `--ds=tests.settings`;
- `saleor/settings.py` exists;
- `tests/settings.py` exists (top-level) — but **`saleor/tests/settings.py`
  does NOT exist** (`saleor/tests/` is not a package in this revision).

The current harness forces `--settings=saleor.tests.settings`, which cannot be
imported in that revision → `ModuleNotFoundError: No module named 'saleor.tests'`
→ `MANAGE_RC_wt0=1` → `ENV_FRAMEWORK_GATE_FAILURE`.  This is a framework-gate
**historical-semantics mismatch**, exactly as the mission hypothesized.

Unit 56 is placed in signature `9b783a672de2042b` (the sole MISMATCH
signature), with evidence-backed confidence.

---

## 8. Effect on units 1..55

**No unit among 1..55 shares the mismatch.**  Every unit 1..55 that passed
contains only modern-layout commits (signature `ce2098d479b46173`, 143 units /
218 tasks), i.e. commits whose tree **does** contain `saleor/tests/settings.py`
and which author pytest with `saleor.tests.settings`.  The framework gate under
which they executed therefore matches their repository-authored semantics at
the settings-module level.

Empirically: all 56 executed units except Unit 56 report `manage_*_rc = 0`
(91 manage-rc=0 markers across the 55 passed units); only Unit 56 reports
`manage_wt0 = 1`.

Whether the previous PASS evidence can be *retained* is a Phase-2 decision;
this audit only supplies the evidence (all 1..55 are CURRENT_GATE_MATCH).

---

## 9. Risk for units 57..144

**No unit among 57..144 is predicted to hit the same mismatch.**  All units
57..144 use only modern-layout commits (signature `ce2098d479b46173`), whose
trees contain `saleor/tests/settings.py` and author pytest with
`saleor.tests.settings`.  Under the current gate these units are
`CURRENT_GATE_MATCH` (143 units total across the population).

Residual Phase-2 review items that are **not** framework-semantics mismatches:
- assumption #4 (pytest trigger on `pytest.ini`/`pyproject.toml`) is currently
  satisfied population-wide but is structurally conditional;
- the manage gate overrides each repository's manage.py default
  (`saleor.settings`) with the test settings module — for 143 units the module
  exists and is authored, so this is semantically valid, but it is a deliberate
  semantic override that Phase 2 should confirm is intended.

---

## 10. Why previous audits missed this dimension

Local Git history evidence:

| Commit | Date | Event |
|---|---|---|
| `b86c7e41` | 2026-09-22 | `saleor.tests.settings` first appears in the WP2 Saleor feasibility census (`--ds=saleor.tests.settings`) |
| `3b1ead02` | 2026-09-25 | linux oracle v2 harness authors `pytest --ds=saleor.tests.settings` |
| `635a59f7` | 2026-10-12 | D7 R3 harness contract preserves `manage.py check --settings=saleor.tests.settings` |
| `bea6fab8` | 2026-10-12 | `sf_calibration12_driver.py` (source-fidelity calibration) uses the same manage-gate command |
| `e8fc6c0f` | 2026-10-13 | the current `r4_behavioral_calibration_n12_r2.py` runner (Attempt-6) inherits the manage-gate command |

**EVIDENCE:** the hardcoded `--settings=saleor.tests.settings` manage-gate
command entered the R4 N12 runner lineage at `e8fc6c0f` (2026-10-13), copied
from `bea6fab8`/`635a59f7` (2026-10-12), which themselves copy the assumption
from the WP2 Saleor oracle lineage (`b86c7e41`, 2026-09-22).  That lineage was
developed and calibrated against modern-layout Saleor revisions.

**EVIDENCE (why N12 could not detect it):** the frozen D7 12-unit calibration
plan (`research/env-canon-evidence/d7-r3/manifests/D7_CALIBRATION_12_PLAN.json`)
contains 12 units whose commits all have `saleor/tests/settings.py` present
(all 18 member commits verified).  None is the legacy commit 8220a534.  The
12-unit behavioral calibration therefore could not observe the Unit-56
signature.

**INFERENCE (clearly separated):** the R4-A/B/C/D/E, I5/I6 and N12 gates were
environment/closure/artifact gates and a 12-unit behavioral calibration, none
of which exercised the manage-gate against the legacy-layout revision 8220a534;
the Full144 successor run was the first to execute that commit under the
manage gate.  The commit history does not state that the authors intended the
gate to apply only to modern layouts; that intent is not claimed here.

---

## 11. Open questions for Phase 2 (design review)

1. Should the manage gate derive the settings module from each repository's own
   authored semantics (manage.py default `saleor.settings`, or the repo's
   pytest `--ds`) instead of a single hardcoded module?
2. Is `saleor.tests.settings` the correct universal manage-gate settings module
   for this population, or should the gate accept the repository-authored
   settings module per revision?
3. Should a legacy-layout revision (`tests.settings` at top level) be treated
   as (a) a supported layout, (b) an explicit skip/UNKNOWN, or (c) an expected
   environment failure with a dedicated classification?
4. Should the manage-gate and pytest gate semantics be decoupled (pytest
   already inherits repo config; the manage gate does not)?
5. Does the override of the repository manage.py default (`saleor.settings`) by
   the test settings module need to be recorded/classified per unit for the
   143 CURRENT_GATE_MATCH units?
6. Retention of previous PASS evidence for units 1..55 (evidence says all are
   CURRENT_GATE_MATCH; owner decision required on retention policy).
7. Whether the Full144 successor run should resume with a corrected gate or
   restart — this is a Phase-2 execution decision, not made here.

---

## 12. Audit artifacts

Written under `research/env-canon-r4/`:

- `R4_FRAMEWORK_SEMANTICS_AUDIT_144.json` — full machine-readable audit
  (per-unit + per-commit records, signatures, assumption inventory, impact
  sets, evidence hashes, deterministic payload hash).
- `R4_FRAMEWORK_SEMANTICS_AUDIT_144.md` — this report.
- `R4_FRAMEWORK_SEMANTICS_SIGNATURES_144.json` — signature definitions and
  membership (commits + unit counts).
- `R4_FRAMEWORK_SEMANTICS_AUDIT_GAP_ANALYSIS.md` — why prior audits missed this
  dimension (evidence vs inference).
- `R4_FRAMEWORK_SEMANTICS_PROBE_219.tsv` — frozen deterministic Git-object
  probe evidence (219 rows) used for reproducible reruns.

Evidence hashes (see audit JSON `evidence_files`):
- `probe_tsv_sha256` = `089fb1990563c719bde0c1d50b3213478667d8005a5536369157e674b567a936`
- `signatures_json_sha256` = `a53536d4551088af4f1b9b8a166e4d40eeb5b4af62aee279d102caa25b422a3c`
- `deterministic_payload_sha256` = `61a92159a8eba7c5bcf151011d6baa72548234bf95d9bc0168f04bca58c43c56`

---

## 13. Explicit statement

**No repair was made in this mission.**  The framework gate, manage-command
semantics, pytest semantics, frozen scientific providers, population/order and
the canonical failed run are all untouched.  This mission produced additive
audit evidence only, for Phase-2 owner/design review.

Terminal label: **`PASS_FRAMEWORK_SEMANTICS_AUDIT_READY_FOR_PHASE2`**
