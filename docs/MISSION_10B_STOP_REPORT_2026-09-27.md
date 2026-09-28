# MISSION-10B — HARNESS V3 + ENG ORACLE — STOP REPORT (2026-09-27)

Decision token: **`HARNESS_V3_RECOMMENDED`** / **`PHASE_REACHED = 5-ENG`** / **`ENG_SMOKE_READY = YES`**

Mission-10B validated the Harness V3 infrastructure candidate and closed the
ENG oracle + P2P-S/P2P-U evidence. The follow-on WP-2 Environment Closure V3.1
(Mission-11 authorization, 2026-09-27) installed the historically-declared
DEV/TEST dependencies by rule and re-ran the affected ENG evidence under the
corrected environment. ZERO LLM/API calls; total paid spend $0.00.

---

## 1. Executive verdict

**CLOSED WITH CORRECTION.** Harness V3 is RECOMMENDED (infrastructure fix for
FD headroom / DB lifecycle / lock-exact install / clock preflight). The ENG
oracle is READY for Smoke: 14 behavioral / 2 symbol-only / oracle-valid union
16, unchanged by the environment closure. The P2P-U V3 evidence was re-run
under the corrected environment (MISSING_FIXTURE 164→0, SOCKET_BLOCKED
132→0, overall stable rate 0.956→0.996, compliance FAIL→PASS).

## 2. Scientific question

Does the Harness V3 infrastructure candidate (nofile, DB lifecycle,
lock-exact dependency install, clock preflight, richer manifests) provide a
valid foundation for the WP-2 ENG oracle and downstream Smoke, without changing
oracle scientific semantics?

## 3. Dataset/split and forbidden data

Development evidence only: DEV_TRAIN_ENG (29 candidates). No generation on
ASSAY_HOLDOUT, DEV_VALIDATION, MAIN, INTERNAL_TEST, or RESERVE. No Stage C.
No model/API calls. Frozen oracle semantics, P2P-U rule/salt/caps, splits, and
workers=1 unchanged.

## 4. Validation-gate table

| Gate | Verdict | Evidence |
|---|---|---|
| Harness V3 freeze (Phase 2) | PASS | research/wp2/harness_v3_2026-09-26/harness_v3_spec.json |
| Phase-4 mechanical gate | PASS | …/gate.json |
| W1_RERUN_REPRODUCIBILITY | PASS | …/phase5_c4_v3_progress.json |
| W2_EQUIVALENCE | NOT_TESTED | C4 ran at effective workers=1 (validated Phase-3 regime); no w2 run |
| ENG C4 terminal | PASS 29/29 | …/phase5_c4_v3_progress.json |
| REGRESSIONS = 0 | PASS | …/eng_v3_oracle_ready.json |
| ENG_V3_ORACLE_READY | PASS (v2) | …/eng_v3_oracle_ready.json |
| P2P-S V3 invariants | PASS | …/p2p_s_v3_eng.json |
| P2P-U V3 execution + verify_unit | PASS 32/32 | …/p2pu_v3_eng_*.json |
| D19 cap agreement ≥ 0.95 | PASS | …/p2pu_v3_eng_summary.json |
| V3.1 env closure preflight | PASS | …/env_closure_v31_preflight_summary.json |
| ENG_SMOKE_READY | YES | …/eng_smoke_ready.json |

## 5. Main result table

- Oracle-valid union = 16 (behavioral 14, symbol-only 2, overlap 0).
- P2P-S: 14 defined / 2 undefined (39b4138e8550, 823b899757ab), 1791 nodes.
- P2P-U: 32/32 units DONE + verified; cap200/cap400 defined 16/16
  (9258154b8a0b recovered); overall stable rate cap200 0.9961 / cap400 0.9973.
- Corrected C4 node-level changes vs pre-closure (recorded, e.g.
  82c56bde0e34 BEHAVIORAL_F2P 11→12; 74538ea00ce9 TARGET_ORACLE_INVALID 0→1);
  task-level membership sets unchanged.

## 6. Development vs confirmatory label

All evidence is DEVELOPMENT (DEV_TRAIN_ENG). No confirmatory claim is made.
The Smoke (next phase) is pipeline validation on DEV_TRAIN_ENG.

## 7. Fair-comparison warning

No method comparison is made in this closure. Any future arm comparison in the
Smoke is descriptive-only; no cross-split head-to-head ranking is authorized.

## 8. Interpretation

The corrected P2P-U stable rates (0.996) confirm that the earlier non-stable
losses were overwhelmingly environment defects (missing declared dev/test deps),
not real test behavior. The remaining 28 non-stable nodes (20 FLAKY, 8
assertions) are genuine behavior.

## 9. What the result does NOT mean

It does NOT validate the Smoke generator/evaluator (built next, zero-API). It
does NOT authorize Stage C, MAIN, holdout, or any paid call. It does NOT make a
comparative claim between RM-CSS and Agent.

## 10. Competitor/baseline implication

The corrected environment provides the faithful baseline for the Smoke arms
(GOLD/RMCSS/AGENT/PLACEBO). No arm ranking is implied.

## 11. Threats/caveats

- Single repository (Saleor) ENG split; n=16 union.
- W2 (workers=2) equivalence NOT_TESTED; all runs at effective workers=1.
- A small number of dev/test exact pins are ENV_INSTALL_BLOCKED
  (codecov versions removed from PyPI, python-magic-bin no Linux wheel,
  pywin32 Windows-only) — none required by the preflight (fixtures/collection
  pass).
- 5 tasks gained P2P-U candidates under the corrected env (supersets).

## 12. Tests/audit

Dependency-compiler unit tests 18/18 PASS; Harness hardening 16/16 PASS;
verify_unit 32/32; ruff clean; py_compile clean; git diff --check clean.
Gate JSONs and audits referenced in section 4.

## 13. Documentation changed

PROGRESS.md, DECISIONS.md (authorization), docs/WP2_DEV_SMOKE_DESIGN_DRAFT_2026-09-25.md,
docs/LIVE_STATUS.json (+ rendered blocks), this report,
docs/MISSION_11_STOP_HARNESS_V3_DEV_DEPS_GAP_2026-09-27-0145.md (resolved by closure).

## 14. Git branch/commit/main status

Branch `main`; HEAD = origin/main (see A6.4 for tag/export blocks).

## 15. Merge status

No merge required (work executed directly on `main`; no feature branch).

## 16. Tag

`wp2-harness-v3-eng-smoke-ready-2026-09-27` — created on the ENG_SMOKE_READY
commit (Mission-10B scientific artifact; DEV evidence only).

## 17. Export ZIP + SHA256

See the PROJECT_EXPORT_READY / LIGHT_EXPORT_READY blocks in A6.4 of the
Mission-11 log and the export scripts.

## 18. Where we are now

Mission-10B CLOSED (ENG_SMOKE_READY). Mission-11 continues at B1
(E2E instrument build, zero-API) under the original authorization.

## 19. ONE next action

Proceed to Mission-11 Part B: build the WP-2 shared E2E instrument (zero API).