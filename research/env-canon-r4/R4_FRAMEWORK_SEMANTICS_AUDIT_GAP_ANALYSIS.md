# R4 Framework-Semantics Audit — Gap Analysis

- **Mission:** `M17_D7_R4_FRAMEWORK_SEMANTICS_AUDIT_144`
- **Companion:** `R4_FRAMEWORK_SEMANTICS_AUDIT_144.json` / `.md`
- **Scope:** why the current framework-gate semantics dimension was not detected
  by prior R4 gates (A/B/C/D/E, I5/I6, N12) and by the 12-unit behavioral
  calibration.
- **Statement:** no intent is invented.  Where Git history does not state
  intent, it is explicitly labelled INFERENCE.

---

## 1. Provenance of the hardcoded manage-gate command (EVIDENCE)

The command `python manage.py check --settings=saleor.tests.settings` is
present in the current runner `scripts/r4_behavioral_calibration_n12_r2.py`
(line 861).  Local Git history traces its introduction:

1. **2026-09-22 `b86c7e41`** — the string `saleor.tests.settings` first enters
   the repository in the WP2 Saleor zero-container feasibility census
   (`research/wp2/wp2_saleor_environment_feasibility_2026-09-22.json`:
   `--ds=saleor.tests.settings`, `saleor/tests/settings.py` described as the
   pytest settings module) and in `research/wp2/wp2_saleor_main297_census_...`.
2. **2026-09-25 `3b1ead02`** — the linux oracle v2 harness authors
   `pytest --ds=saleor.tests.settings` for the Saleor workload.
3. **2026-10-12 `635a59f7`** — the D7 R3 harness contract preserves
   `manage.py check --settings=saleor.tests.settings` as the D7 smoke semantics.
4. **2026-10-12 `bea6fab8`** — `sf_calibration12_driver.py`
   (source-fidelity calibration 12) is created with the same manage-gate
   command (`git blame` line 441).
5. **2026-10-13 `e8fc6c0f`** — the current qualified Attempt-6 runner
   `r4_behavioral_calibration_n12_r2.py` is created; `git blame` attributes
   line 861 to this commit.  This is the runner reused by the Full144 driver.

EVIDENCE conclusion: the hardcoded manage-gate command is inherited from the
WP2 Saleor oracle lineage (2026-09-22) through the R3/R4 env-canon lineage
(2026-10-12/13).  The command predates the Full144 population assembly and was
not derived from a per-revision census of the Full-D7 target commits.

---

## 2. Was the introduction justified by a specific calibration population / repository layout? (INFERENCE)

The WP2 Saleor oracle lineage was built against modern-layout Saleor revisions
in which `saleor/tests/settings.py` exists and pytest is configured with
`--ds=saleor.tests.settings`.  The Git history does not state that the authors
audited whether **every** Full-D7 target commit uses that layout.

INFERENCE (clearly separated): the manage-gate assumption was almost certainly
copied from the modern Saleor layout (the layout of the WP2 oracle revisions)
and carried into the R4 env-canon lineage without a population-wide layout
census.  The repository history contains no statement of intent that the gate
must apply to every historical revision.

---

## 3. Could a prior 12-unit behavioral calibration have detected the Unit-56 signature? (EVIDENCE)

No.

The frozen 12-unit calibration plan
(`research/env-canon-evidence/d7-r3/manifests/D7_CALIBRATION_12_PLAN.json`,
12 units) was extracted and every member commit was probed against the WSL
object store for this audit:

- all 12 planned units are modern-layout (signature `ce2098d479b46173`);
- all 18 member commits have `saleor/tests/settings.py` present;
- **none** of the calibration commits is `8220a53473bb...`.

EVIDENCE conclusion: the 12-unit behavioral calibration population does not
contain the legacy-layout commit, so it could not detect the Unit-56
framework-semantics signature.  A calibration of size 12 drawn from the Full-D7
population has, a priori, ~8.9% chance of including the single legacy commit
(12/219*100 ≈ 5.5% expected; observed 0).

---

## 4. Why previous R4-A/B/C/D/E, I5/I6 and N12 gates did not cover this dimension (EVIDENCE + INFERENCE)

The earlier R4 gates were read-only environment/closure/artifact gates:

- **R4-A** wheel-tag / artifact composition;
- **R4-B** uv adapter + integrated lock parser;
- **R4-C** Linux tree-fidelity materialization;
- **R4-D** calibration coverage report;
- **R4-E1/E2/E3** pylint recovery + affected revalidation;
- **R4-I5** zero-container smoke (N12) — environment smoke, not framework-gate
  semantics per revision;
- **R4-I6** corrected zero-container census (metadata/artifact readiness);
- **N12** behavioral calibration — 12 units, none containing the legacy commit.

None of these gates executed `manage.py check --settings=saleor.tests.settings`
against the legacy revision 8220a534.  The Full144 successor run was the first
execution to reach that commit under the manage gate.

INFERENCE: prior gates were population/env/closure audits and a small
behavioral calibration whose sample did not include the sole legacy-layout
revision; the framework-semantics dimension (whether the gate's forced settings
module exists in the exact historical tree) was therefore never exercised
population-wide before the Full144 successor run.

---

## 5. Why the Full144 successor run detected it (EVIDENCE)

The Full144 driver executes all 144 units in frozen order.  Unit 56 targets the
only legacy-layout commit in the entire population.  The observed
`ENV_FRAMEWORK_GATE_FAILURE` (`ModuleNotFoundError: No module named
'saleor.tests'`) is the deterministic consequence of forcing
`saleor.tests.settings` in a revision that authors `tests.settings` instead.

This is not a scientific failure of the unit or its environment; it is a
framework-gate historical-semantics mismatch — the audit's exact subject.

---

## 6. Evidence vs inference boundary

EVIDENCE (Git objects / Git history / probe):

- the exact file-existence facts per commit (probe TSV);
- the manage-gate command and its line in the runner;
- the introduction lineage of the command (commits listed in §1);
- the 12-unit calibration membership (plan JSON + probe);
- Unit-56 raw evidence (`manage_wt0.log`, `result.json` classification).

INFERENCE (explicitly not evidence):

- why the command was originally chosen (modern-layout copy hypothesis);
- whether prior gates "should" have detected this;
- Phase-2 repair/design decisions.

These are never mixed in the audit payload; the JSON marks per-commit facts as
evidence-only and the gap analysis keeps INFERENCE labels.
