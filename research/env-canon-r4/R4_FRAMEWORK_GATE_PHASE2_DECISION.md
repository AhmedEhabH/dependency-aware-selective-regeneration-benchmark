# R4 Framework-Gate Phase-2 Decision

- **Mission:** `M17_D7_R4_FRAMEWORK_GATE_PHASE2_DECISION`
- **Mission type:** scientific design/decision review only — **NO implementation**
- **Terminal verdict:** `PASS_FRAMEWORK_GATE_DECISION_READY_FOR_PHASE3`
- **Decision UTC:** `2026-10-15T11:13:25.517447Z`

---

## 1. Phase-1 authority (frozen)

| Item | Value |
|---|---|
| Worktree | `D:\WP2\active\r4-framework-semantics-phase2` |
| Required / verified starting HEAD | `e357c7993344e471f1670996df6d7b39603a7ba7` |
| Phase-1 immutable tag | `m17-d7-r4-framework-semantics-audit-r1-2026-10-15` |
| Tag peel | `e357c7993344e471f1670996df6d7b39603a7ba7` |
| Audit verdict | `PASS_FRAMEWORK_SEMANTICS_AUDIT_READY_FOR_PHASE2` |

Verified artifact hashes (recomputed locally, match frozen audit `evidence_files`):

| Artifact | SHA-256 |
|---|---|
| `R4_FRAMEWORK_SEMANTICS_PROBE_219.tsv` | `089fb1990563c719bde0c1d50b3213478667d8005a5536369157e674b567a936` |
| `R4_FRAMEWORK_SEMANTICS_SIGNATURES_144.json` | `a53536d4551088af4f1b9b8a166e4d40eeb5b4af62aee279d102caa25b422a3c` |
| deterministic payload | `61a92159a8eba7c5bcf151011d6baa72548234bf95d9bc0168f04bca58c43c56` |

Frozen audit facts (accepted as-is, not re-derived):

- 144/144 units audited; 219/219 tasks; 219 distinct target commits.
- `CURRENT_GATE_MATCH` = 143 units; `CURRENT_GATE_MISMATCH` = 1 unit (Unit 56); `SEMANTICS_UNRESOLVED` = 0.
- Units 1..55: 0 mismatches. Units 57..144: 0 predicted instances of the same mismatch.
- Two signatures: modern `ce2098d479b46173` (218 commits / 143 units) and legacy `9b783a672de2042b` (commit `8220a53473bb67bbb247490cbd043c56dac4568c` / Unit 56 only).
- `manage.py` default is `saleor.settings` in both signatures; repo pytest settings module is `saleor.tests.settings` (modern) vs `tests.settings` (legacy).

---

## 2. Decision 1 — successor manage-gate settings semantics

**Chosen candidate: C.**

> The manage-gate settings module shall be the exact historical revision's
> repository-authored pytest Django settings module (the settings module the
> repository itself authors for its pytest workload — the repo pytest `--ds`
> / test-settings module), resolved from the exact materialized worktree.
> The manage check command is:
>
> ```
> python manage.py check --settings=<repo-authored pytest settings module>
> ```

For the frozen population this yields exactly:

| Signature | Commits | Repo-authored pytest settings module | Effective manage-gate command |
|---|---|---|---|
| Modern `ce2098d479b46173` | 218 | `saleor.tests.settings` | `python manage.py check --settings=saleor.tests.settings` |
| Legacy `9b783a672de2042b` | 1 (`8220a534…`) | `tests.settings` | `python manage.py check --settings=tests.settings` |

### Why Candidate C is the correct semantic interpretation (not just a Unit-56 fix)

1. **Frozen D7 R3 smoke semantics already target the repository's TEST settings
   module.** The frozen contract
   (`research/env-canon-evidence/d7-r3/harness/D7_R3_HARNESS_CONTRACT.md`,
   section F *Smoke*) preserves the manage smoke gate as
   `manage.py check --settings=saleor.tests.settings`. That module is precisely
   the repository-authored pytest settings module of the modern layout.
   Candidate C is the faithful generalization of that frozen intent to the full
   population: the manage gate validates the framework under the repository's
   authored test settings module, whatever that module is for the exact
   revision.
2. **Repository/semantics-based, not task-specific.** The rule is keyed to the
   per-revision repository-authored pytest settings module — the exact same
   evidence dimension Phase-1 classified deterministically. It contains no
   task-ID / unit-ID / commit-SHA conditionals.
3. **Preserves the existing 143 matching units byte-for-byte.** For all 218
   modern commits the repo-authored pytest settings module *is*
   `saleor.tests.settings`, so the effective command is identical to the
   current gate. No previously-passing unit's effective framework-gate
   command or semantics changes.
4. **Unit 56 is handled by the same general rule.** That revision authors
   `tests.settings` as its pytest settings module; `tests/settings.py` exists
   in its exact tree (probe-verified). No new universal hardcoded module, no
   special case.

### Alternatives rejected

| Candidate | Name | Decision | Evidence |
|---|---|---|---|
| A | Universal hardcoded `--settings=saleor.tests.settings` | **REJECT** | Phase-1 assumption #3 is `HISTORICALLY_FALSE_FOR_SOME_POPULATION`: `saleor/tests/settings.py` exists in 218/219 commits, absent in `8220a534…` (Unit 56). A universal hardcoded module contradicts a frozen revision and is exactly the proven defect. |
| B | Repository manage.py default (`python manage.py check`, default `saleor.settings`) | **REJECT** | Changes the effective framework-gate command for ALL 143 matching units; uses production settings rather than the repository's test settings module; contradicts the frozen R3 smoke semantics which intentionally force the test settings module. |

---

## 3. Decision 2 — TEST settings vs repository manage.py default

**Decision: the manage gate intentionally uses TEST settings (the
repository-authored pytest/test settings module), NOT the repository's normal
manage.py default settings (`saleor.settings`).**

Evidence:

- The frozen D7 R3 harness contract preserves the manage smoke gate as
  `manage.py check --settings=saleor.tests.settings` — i.e., the gate is
  frozen **against the repository's TEST settings module**, not against the
  manage.py default.
- The `manage.py` default is `saleor.settings` in both signatures (Phase-1
  signatures JSON). The audit flagged the override as "a deliberate semantic
  override that Phase 2 should confirm is intended"
  (`R4_FRAMEWORK_SEMANTICS_AUDIT_144.md`, §9). **This decision confirms it is
  intended.**
- The manage gate is a **framework gate**: it verifies the installed
  environment can run Django system checks under the same settings
  configuration the repository's own test suite (pytest) uses. The pytest
  smoke gate already inherits the repo `--ds` config; the manage gate
  validating the same repository-authored test settings module is the
  semantically consistent framework check.
- Candidate B (manage.py default) would change the effective command for all
  143 matching units and would not reflect the settings under which the
  workload's tests actually run.

---

## 4. Manage vs pytest decoupling

**Decision: the manage gate and pytest gate remain intentionally decoupled.**

- The manage gate **forces** the settings module explicitly (`--settings=…`).
- The pytest gate **inherits** the repository-authored config (`--ds`) without
  forcing.
- Under Candidate C both resolve to the **same** repository-authored settings
  module (`saleor.tests.settings` modern / `tests.settings` legacy), so they
  are semantically consistent while remaining mechanically decoupled. Neither
  gate is merged into the other.

---

## 5. Expected effective rules

| Signature | Units | Manage-gate command |
|---|---|---|
| Modern `ce2098d479b46173` (218 commits) | 143 units | `python manage.py check --settings=saleor.tests.settings` |
| Legacy `9b783a672de2042b` (commit `8220a534…`) | Unit 56 | `python manage.py check --settings=tests.settings` |

---

## 6. Impact on Units 1..55

**No effective framework-gate change.** Candidate C resolves to exactly
`python manage.py check --settings=saleor.tests.settings` for every unit
1..55 (all CURRENT_GATE_MATCH, modern signature). Their PASS evidence was
produced under the exact effective command and semantics the corrected
successor rule prescribes for them.

---

## 7. Impact on Unit 56

The effective manage-gate settings module changes from `saleor.tests.settings`
(module absent in that exact tree → `ENV_FRAMEWORK_GATE_FAILURE`) to
`tests.settings` (repository-authored pytest settings module present in that
exact tree). The same general rule handles it; the manage gate is **not
skipped, removed, or weakened**.

---

## 8. Predicted impact on Units 57..144

**0 predicted instances of the same mismatch.** All units 57..144 are
modern-signature (`ce2098d479b46173`); effective manage-gate command remains
`python manage.py check --settings=saleor.tests.settings`.

---

## 9. Evidence-retention decision for Units 1..55

**Decision: RETAIN.**

- The chosen successor (Candidate C) resolves to exactly the same
  `--settings=saleor.tests.settings` for Units 1..55 — no change to their
  effective framework-gate command or semantics.
- Retention is evidence-backed, not "they passed so keep them":
  Phase-1 audit shows 0 mismatches among Units 1..55; all are
  `CURRENT_GATE_MATCH` (the forced settings module exists in each exact tree
  and matches repo-authored semantics); empirically all 55 passed with
  `manage_rc=0` (91 manage-rc=0 markers).
- Their framework-gate evidence is semantically identical to what the
  corrected successor rule prescribes for them → sufficient for scientific
  evidence retention.

---

## 10. Resume-vs-restart decision (Q4)

**Decision: a new corrected-successor run must RESTART FROM UNIT 1.** Resume
from Unit 56 is NOT permitted by the frozen protocol.

Frozen authority:

1. **Contingency matrix**
   (`research/env-canon-r4/R4_FULL144_CONTINGENCY_MATRIX.json`):
   `ENV_FRAMEWORK_GATE_FAILURE` → `automatic_continuation: NO`,
   `no_semantic_retry: true`, `no_scientific_recovery: true`,
   `default: FAIL_CLOSED`.
2. **Pre-execution freeze**
   (`D:\WP2\runs\r4-full-d7-144-successor-2026-10-15\freeze\PRE_EXECUTION_FREEZE.json`):
   `checkpoint_restart_policy` = "intent before start; atomic progress
   checkpoint after PASS; fail closed on progress/evidence mismatch; never
   rerun completed PASS; partial unit -> STOP_OWNER_REVIEW";
   `fail_fast_policy` = "first mandatory unit failure stops the run; no
   skip/reorder/rerun".
3. **Driver** (`src/benchmark/wp2/full144/driver.py`): `run_unit` refuses to
   rerun a completed unit; fail-fast refuses to run later units if a prior
   unit FAILED ("prior unit … FAILED; refusing to run later units");
   `reconcile()` requires `progress.json` and per-unit evidence to agree
   exactly. **No evidence-import / adoption mechanism exists.**

Distinctions:

- **Preserve the old failed run as immutable evidence:** YES — the canonical
  run `D:\WP2\runs\r4-full-d7-144-successor-2026-10-15` remains immutable
  FAIL_CLOSED evidence (`ENV_FRAMEWORK_GATE_FAILURE` at Unit 56; run STOPPED,
  per `logs/launcher.log`).
- **Create a new corrected-successor run:** YES — Phase 3 creates a new
  corrected-successor run under the Candidate C gate rule.
- **Reuse/import Units 1..55 evidence:** NO — the frozen protocol provides no
  evidence-import/adoption mechanism; the contingency matrix marks
  `ENV_FRAMEWORK_GATE_FAILURE` as no-recovery/no-semantic-retry. Importing
  evidence into a new run would be inventing continuation semantics.
- **Actually execute Units 1..55 again:** YES — the new corrected-successor
  run executes from Unit 1 (fresh run root, full 144-unit execution under the
  corrected gate rule).

**Ruling:** Resume-from-56 is not permitted. The canonical failed run is
immutable FAIL_CLOSED evidence. A new corrected-successor run restarts from
Unit 1 and actually executes all 144 units under the corrected general
manage-gate rule. Units 1..55 PASS evidence is retained (Section 9) as valid
scientific evidence but is **not** imported into the new run.

---

## 11. Phase-3 implementation contract (exact, narrow)

1. Change ONLY the manage-gate settings-module resolution in the qualified
   runner (`scripts/r4_behavioral_calibration_n12_r2.py`, manage-gate command
   at line 861) so that `--settings=<module>` is derived from the exact
   revision's repository-authored pytest Django settings module, resolved from
   the exact materialized worktree — NOT from a hardcoded universal module.
2. The rule is general and repository/semantics-based, keyed to the frozen
   per-revision repository-authored pytest settings module. No task-ID /
   unit-ID / commit-SHA-specific conditionals. No new universal hardcoded
   module.
3. The manage gate itself is UNCHANGED in strength: `python manage.py check
   --settings=<repo-authored module>` runs for every unit where `manage.py`
   exists; `rc==0` PASS, `SKIP` only where `manage.py` absent, anything else
   `SMOKE_FAIL`. No gate removal, no skip of the gate, no weakening.
4. If a revision does not author a resolvable pytest/test settings module,
   FAIL CLOSED (never guess, never skip).
5. pytest smoke gate and import smoke remain unchanged (pytest inherits repo
   `--ds`; `import saleor` unchanged).
6. No other runner/driver/providers/population/order/images/network/install
   route semantics change.
7. Create a NEW corrected-successor run root with a fresh
   `PRE_EXECUTION_FREEZE`; restart from Unit 1 (full 144-unit execution). Do
   NOT modify the canonical failed run. Do NOT import/rewrite evidence from
   the canonical run.
8. The legacy signature (Unit 56) is covered by the same general rule:
   `--settings=tests.settings` resolves in its exact tree.

---

## 12. Required-decision-quality checklist

| # | Requirement | Status |
|---|---|---|
| 1 | One general framework-gate rule selected | **PASS** — Candidate C |
| 2 | Rule is repository/semantics-based, not task-specific | **PASS** — keyed to repo-authored pytest settings module per exact revision |
| 3 | Preserves / justifies semantic change for existing 143 matching units | **PASS** — effective command byte-identical for all 143 |
| 4 | Unit 56 handled by the same general rule | **PASS** — `--settings=tests.settings`, repo-authored for that exact revision |
| 5 | No gate removed or weakened | **PASS** — manage check still runs for every unit with `manage.py`; FAIL CLOSED if no repo-authored module |
| 6 | Units 1..55 retention has evidence-backed ruling | **PASS** — 0 mismatches, all CURRENT_GATE_MATCH, identical effective command |
| 7 | Resume-vs-restart has authority-backed ruling | **PASS** — contingency matrix + pre-execution freeze + driver fail-fast/reconcile mandate fresh run from Unit 1 |
| 8 | Phase 3 receives exact narrow implementation contract | **PASS** — 8-item contract in §11 |
| 9 | No scientific execution or repair occurred | **PASS** — no runner/driver edits, no unit execution, no Docker, no new utilities |

**Terminal label:** `PASS_FRAMEWORK_GATE_DECISION_READY_FOR_PHASE3`

---

## 13. Canonical run immutability (cheap verification)

- Run root: `D:\WP2\runs\r4-full-d7-144-successor-2026-10-15`
- `freeze/PRE_EXECUTION_FREEZE.json` present; SHA-256
  `5c3ec3bdec80c2e2bf1e48868aec463ccb2de428c9db50a5956f3d5c749e13a0`
- `progress/progress.json`: 55 PASS + Unit 56
  `ENV_FRAMEWORK_GATE_FAILURE`; `stopped_early: false`; 56 unit dirs present
- `logs/launcher.log` stop line: `FAIL_CLOSED UNIT_FAIL vu-cdcf3222cbb5 ->
  ENV_FRAMEWORK_GATE_FAILURE (evidence persisted; run STOPPED)`
- No modification performed. Verification used existing cheap receipts only;
  the full ~4 GB tree was not rescanned.

## 14. Immutability contracts respected

- Canonical failed run: untouched.
- Predecessor successor refreeze `D:\WP2\active\r4-full144-successor-refreeze`:
  untouched (read-only inspection).
- Phase-1 audit artifacts: untouched (hashes re-verified).

## 15. Unresolved questions

None.