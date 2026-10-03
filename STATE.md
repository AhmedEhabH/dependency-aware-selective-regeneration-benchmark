# STATE.md - Current Project State

**Role:** Append-only governance record of the current project state. Entries
are appended; corrections are new entries.

---

## STATE 2026-10-03 - M17 Phase0B-v2 executable qualification kit frozen

- **Head:** `f7412ec0031a4585df9c4102a9e18607cf2d7db8` (branch `main`) pre-freeze; this
  mission stages the M17 kit for the exact-path freeze commit
  `feat(wp2): freeze M17 executable qualification kit` + annotated tag
  `wp2-m17-v1-kit-2026-10-02`.
- **M17 Phase0B-v2:** built and validated the REAL zero-Docker M17 executable
  qualification kit: adapter rebuilt from frozen harness semantics
  (`scripts/wp2_m17_adapter.py`), real runner (`scripts/wp2_m17_run.py`),
  F2P/P2P contract module (`scripts/wp2_m17_contract.py`), kit manifest
  (`controller/KIT_MANIFEST_M17.json`), real-controller fake-world integration
  (8 scenarios PASS), P2P/F2P contract + failure-injection suite PASS, 109 M17
  unit tests PASS. ZERO Docker / WSL / API; qualification NOT run; MAIN NOT run.
- **Qualification membership (brain-approved 2026-10-03):** corrected 12-task
  membership in `m17_qualification_membership_v2_approved.json`; the old
  Phase-0 membership and the v2 candidate are both preserved for auditability.
  `saleor-rc-f76d0093b450` is recorded ADAPTER_UNRESOLVED
  (DEV_GROUP_DECLARED_BUT_MECHANISM_NONE) and kept in the 220-frame ledger.
- **M16-v1:** remains CLOSED pre-experiment (no MAIN outcome). M15-R immutable.
- **Next:** STOP at `M17_QUALIFICATION_READY_REVIEW`; await ChatGPT brain review
  before the REAL 12-task qualification. No scientific run until approved.

---

## STATE 2026-10-02 - M16-v1 closed; documentation/research closure phase

- **Head:** `3280a658ac488dc64f44fef050c1f8ea993a58c9` (branch `main`)
- **Phase:** Next-phase closure: archive M16-v1, consolidate evidence, update
  README/docs, freeze claims, produce seminar/proposal material. No new
  science; no M16-v2; no polyglot study until a brain decision after review.
- **M16-v1:** CLOSED as pre-experiment adapter/instrument failure. Final STOP
  `M16_ADAPTER_FAIL` at R02_ADAPTER_VERIFY (resumable=False), 4 violations:
  3 ENG install-mode mismatches + 1 MAIN declared-dev-group-but-mechanism-none.
  No R03/R04/R05, no MAIN, no OPWS outcome, no R2B/R2C. Final LIGHT
  `project-LIGHT-STOP_M16_ADAPTER_FAIL-2026-10-02-1606.zip` sha256
  `32465cf2f07fca11dd7f276695036779d08e36719cb85fd7a3d13e11e6c1f08f` archived to
  `D:\wp2_cold\`. Closure record: `docs/M16_V1_CLOSURE_2026-10-02.md`.
- **WP1 evidence (frozen, unchanged):** Saleor RESERVE-300 primary (RM-CSS
  F1 0.3569 vs SIP 0.2647, delta +0.0921 CI [0.0691, 0.1156]); MAIN_297
  selection-only (Agent 0.3631 / RM-CSS 0.3568 / SIP 0.2652) with NI at 0.05
  supported; efficiency (RM-CSS ~0.2746x calls, ~0.2134x generation tokens).
- **WP2 evidence (frozen, unchanged):** Smoke v2.2 supporting; Pilot-A
  generator floor; M14R floor not met; M15-R OPWS Pilot-B descriptive.
- **Next actions:** C1..C6 per task_graph.json (evidence registry, LIGHT
  naming convention + tests, README landing page, repro audit, closure LIGHT),
  then STOP for brain review at G0_BRAIN_REVIEW.

---

## STATE 2026-10-02 (T2) - Research baseline finalization (durability/documentation only)

- **Head:** branch `main`; pre-mission HEAD/origin main
  `3280a658ac488dc64f44fef050c1f8ea993a58c9`; C0→C6 changes were uncommitted.
- **C0→C6 closure:** complete; G0_BRAIN_REVIEW completed by ChatGPT with
  decision to finalize a durable research baseline before any new science.
- **LIVE status:** `docs/LIVE_STATUS.json` brought current to 2026-10-02 and
  re-rendered into the four current-facing targets (README.md, PROGRESS.md,
  START_HERE_CURRENT_2026-09-21b.md, 00_CURRENT_RESEARCH_STATE.md).
- **Future LIGHT naming (corrected):** `project-light-YYYY-MM-DD-HHMM.zip`
  (timezone-aware local creation time, minute precision; same-minute collision
  fails closed). Historical LIGHTs immutable; none renamed.
- **M16-v1:** remains CLOSED pre-experiment; no MAIN outcome; no M16-v2.
- **Scientific state:** unchanged — WP1 primary (selection correctness/
  efficiency), WP2 supporting/downstream; no metric, threshold, selector,
  dataset, RQ, or claim changed; no new experiment run.
- **Next:** commit + push the durable baseline, freeze tag
  `msc-research-baseline-2026-10-02`, produce a fresh corrected-convention
  LIGHT, then STOP at `G1_SCIENCE_DECISION` for the brain call:
  seminar/proposal first vs exactly one optional targeted external-validity
  pilot.