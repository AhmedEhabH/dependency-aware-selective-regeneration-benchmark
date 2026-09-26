# WP-2 Harness V3 Freeze (2026-09-26) — Mission-10B Phase 2

Status: **FROZEN** before any Phase-3 probe execution. Harness V3 changes ONLY
infrastructure/runtime; oracle scientific semantics are UNCHANGED.

Authority: Mission-10B `_workspace/active/MISSION_10B_HARNESS_V3_GOLD_2026-09-26.md`
sections 13-14. ZERO API; no new Docker image build/tag.

---

## 1. Scope and boundary

- Task population authority, split, test-patch semantics
  (parent = parent + frozen test patch; `TEST_PATCH_APPLIED_ON_PARENT=true`),
  target = target commit, exact 3+3 stability policy, F2P/P2P classifications,
  test-selection rules, P2P-U rule/salt/caps, architecture metrics, and the
  generation-leakage firewall are UNCHANGED from V2.
- V3 corrects infrastructure only: FD headroom, DB lifecycle, lock-exact
  dependency install, clock preflight, and richer manifests.

## 2. FROZEN V3 CANDIDATE (13.A–13.E)

### A. NOFILE
Every test container runs with:
`--ulimit nofile=65536:65536`.

### B. DB LIFECYCLE
Per (task, state):
- unique DB name: `saleor_v3_<task12>_<state>`;
- created FRESH at state start (DROP-then-CREATE, never reuse a partially
  created DB);
- if creation fails: DROP + recreate once only;
- DROP at task completion.
- Within repetitions of ONE successfully-initialized state, `--reuse-db` is
  retained because it matches existing C4 semantics and never crosses
  parent/target state boundaries (per-mission findings: WRONG_CONSTRAINTS
  arises ONLY when a partially-created DB is reused across EMFILE-failed
  creation; fresh per-state DB removes that chain).

### C. DEPENDENCIES
- LOCKFILE-FIRST: exact historical lock/pin; historical constraint; range only
  when NO lock/pin exists. Never unconstrained latest.
- Preferred INSTALL_MODE = `LOCK_EXACT_MAIN_PLUS_DEV`:
  - uv-era: `uv sync --frozen --group dev` / `uv export --frozen --group dev`
    into the ephemeral venv (project-supporting).
  - poetry-era: historical `poetry.lock` main+dev exact set (no re-resolve of
    ranges against today's index).
- Fallback (only if full project lock install is technically impossible):
  `V2_MAIN_PLUS_EXACT_LOCKED_DEV` (frozen V2 main + exact locked dev/test
  versions).
- Harness-only tooling retained at frozen V2 versions.
- Every task records INSTALL_MODE; if no historically faithful mode is
  producible: `ENV_INSTALL_BLOCKED` (rule not weakened).

### D. CLOCK PREFLIGHT
Before every V3 task, measure median host↔WSL skew (midpoint, >=3 samples):
- <=0.5 s: PASS;
- >0.5 s: attempt ONE recorded safe WSL resync;
- after resync: <=1.0 s continue (record pre/post); >1.0 s CLOCK_BLOCKED
  (task not executed). Never silently change Windows host time.

### E. MANIFEST (every task manifest)
task_id · target commit · era · frozen base image ID · harness_v3 spec SHA ·
runner/orchestrator SHA · lockfile path/hash · INSTALL_MODE · `pip freeze`
hash · pytest version · pytest plugin list · fixtures of relevant plugins ·
ulimit soft/hard · host↔WSL skew pre/post · DB names · worker count ·
resource sampler version.

## 3. Freeze hashes (Phase 2)

Machine-readable spec: `research/wp2/harness_v3_2026-09-26/harness_v3_spec.json`
(spec SHA256 `4b9edda4184dcf97a1dc94d16ba8c28ba8abeed683842139daf89a50139b63d7`).

| artifact | SHA256 |
|:---|:---|
| V3 spec (`harness_v3_spec.json`) | `4b9edda4184dcf97a1dc94d16ba8c28ba8abeed683842139daf89a50139b63d7` |
| runner (`src/benchmark/wp2/harness_v3.py`) | `54d76b5be11207ef06b11920e1d090587d4008cbc76f8ba48d61a4381be3ea08` |
| orchestrator (`scripts/wp2_m10b_phase3_probe.py`) | `71d630f3641d4076ebb1480da436b102f53bcebfb88d01b199bc2763f0de4b7a` |
| error taxonomy (`src/benchmark/wp2/m10b_fulltext.py`) | `209384052ea82d6662d04fc7ab2dbce0979971e73bfbeb3b9f1ab184a0dcb151` |
| resource sampler (Mission-09, reused) | `wp2-resource-sampler-v1-2026-09-25` |
| git HEAD at freeze | `26cfbbae` (probe evidence commits follow as descendants) |

## 4. Explicitly unchanged

- task population authority; split; test patch semantics; parent = parent +
  frozen test patch; target = target commit;
  `TEST_PATCH_APPLIED_ON_PARENT=true`; exact 3+3 stability policy;
  F2P/P2P classifications; test selection rules; P2P-U rule/salt/caps;
  architecture metrics; generation leakage firewall.

## 5. Preregistered V3 decision rules (14) — written BEFORE Phase 3

### 14.1 Clean V2 evidence
A previously valid V2 node is CLEAN only if none of its available
parent/target reps contains: INFRA:*; DB:* infrastructure/setup defect; TIME:*;
MISSING_FIXTURE:*; MODULE_NOT_FOUND caused by a missing declared dependency;
known truncated/missing raw evidence that prevents checking these classes. A
legitimate target-change semantic error (e.g. parent-side import of a
target-only symbol) is NOT automatically dirty.

### 14.2 S2' non-regression
For V2 nodes classified BEHAVIORAL_F2P / SYMBOL_ABSENCE_F2P / P2P_ONLY:
- IF V2 evidence CLEAN and class changes under V3 → REGRESSION_CANDIDATE;
  if no legitimate existing semantic explanation → **REGRESSION**.
- IF V2 evidence DEFECTIVE → V2_DEFECT_CORRECTION (not a V3 regression).
- Mechanical gate: **REGRESSIONS must equal 0**.

### 14.3 Materiality
Primary criterion: among authoritative C4 TARGET_ORACLE_INVALID nodes with
sufficient full evidence, the percentage with STABLE_CAUSE in
INFRA + DB-infrastructure + MISSING_DECLARED_DEP must be **>= 20%**.
Report numerator/denominator/percentage/missing-evidence/mixed-cause counts.
Task-level co-occurrence is NEVER used for the gate.

### 14.4 Recovery
RECOVERY = PASS iff the Phase-3 probe converts at least ONE V2-invalid node
into a valid existing oracle class under unchanged scientific semantics
(BEHAVIORAL_F2P / SYMBOL_ABSENCE_F2P / P2P_ONLY / other valid class).

### 14.5 Root-cause fix efficacy
- EMFILE contributing to materiality: controlled probe/V3 run must show EMFILE
  eliminated on affected probe tasks.
- Missing declared deps contributing: package/plugin/fixture available in V3
  and corresponding missing-fixture probe errors disappear.
- DB policy claimed as repair: controlled evidence must support its effect.
- Otherwise FIX_EFFICACY = FAIL.

### 14.6 Safety
SAFETY PASS requires: zero NEW infrastructure error categories under V3 probe;
zero CLOCK_BLOCKED probe tasks; integrity PASS for all probe tasks;
REGRESSIONS = 0 under S2'; no scientific rule drift; FIX_EFFICACY PASS for the
material causes V3 claims to fix.

## 6. Gate (16)

AUTO-CONTINUE to Phase 5 iff ALL:
MATERIALITY = PASS · RECOVERY = PASS · FIX_EFFICACY = PASS · SAFETY = PASS ·
REGRESSIONS = 0 · all 4 probe task integrity = PASS. No subjective override.
Tokens: HARNESS_V3_RECOMMENDED (all pass) / ENV_V2_ADEQUATE (MATERIALITY FAIL
and RECOVERY FAIL, no other major defect) / HARNESS_AUDIT_INCONCLUSIVE
(otherwise).