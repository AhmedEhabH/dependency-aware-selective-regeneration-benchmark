# V1.5 Supervisor Patch List

**Date:** 2026-09-18
**Purpose:** record the remaining supervisor-review issues for the proposal V1.5
**Status:** V1.5 REMAINS the supervisor review candidate. **No V1.6 is created**
for minor wording; **no PPTX is touched** (slide revision belongs to the
presentation workflow).
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## Remaining issues (for the next MATERIAL revision, not for minor polish)

1. **Abstract length:** the abstract can still be shortened further if the
   supervisor requests it. No action taken now (no material content change).
2. **Defensive phrasing:** remove defensive phrases such as "No positive
   algorithmic result is promised" in the next material revision. Keep the
   factual boundaries; only the phrasing is scheduled for change.
3. **"Meaningful intent" operational definition:** the dataset operational
   definition of "meaningful intent" is now documented in
   `reports/DATASET_OPERATIONAL_DEFINITIONS.md` (non-empty, >=5 chars,
   not bot/release/changelog dominated). The proposal can point to this
   operational rule in a future revision.
4. **Curve-level statistics are post-hoc, not preregistered:** the AURC,
   simultaneous bootstrap band, per-task recovery distributions and zero-FN
   handling are added in
   `reports/ROUTE_B_CURVE_LEVEL_POSTHOC_CHARACTERIZATION.md` and are explicitly
   labelled POST-HOC. The proposal must NOT present them as preregistered; if
   quoted, they carry the post-hoc label.
5. **Semantic audit pending:** the semantic-proxy audit is
   **AWAITING_HUMAN_RATINGS** (`reports/SEMANTIC_AUDIT_ACTION_REQUIRED_FROM_HUMANS.md`).
   The proposal must not claim semantic-audit completion until human ratings
   exist.
6. **P2 status update (NEW, 2026-09-18):** P2 Phase 1 is now a **NEGATIVE
   closure** on DEVELOPMENT (no adaptive-budget policy beats fixed-B on both
   repositories; see `reports/P2_PHASE1_DECISION_GATE.md`). The proposal's
   adaptive-budget future-work paragraph should be updated in the next material
   revision to reflect this negative development result honestly (fixed-B
   remains the CONFIRMED thesis).

## Explicitly NOT done

- No `V1.6` created.
- No PPTX/slide file touched.
- No scientific input change.
- No sealed set opened; ZERO API.