# WP-2 Linux Oracle V2 + DEV Pool — Mission-07 STOP REPORT (2026-09-25)

Decision token: **`WP2_LINUX_V2_READY_FOR_DEV_SMOKE_DESIGN`**

Mission 07 executed on a Linux substrate (WSL-local Docker engine), replaced the
Windows-limited v1 oracle evidence, and produced a materially larger, temporally
representative oracle pool for MAIN and DEV. Zero model/API/embedding calls.
No generation, repair, Smoke, Pilot, or E2E was executed.

## 1. MAIN V2 pool sizes

- Attempted: **220** (same changed-test MAIN candidates as v1 census).
- Environment/install/task-collection failed: **60** (genuine era attrition).
- Executable: **160**.
- **Primary behavioral eligible: 71** tasks (v1 Windows: 8).
- Symbol-absence eligible: **17** tasks.
- Node totals: BEHAVIORAL_F2P 731, SYMBOL_ABSENCE_F2P 64,
  PARENT_COLLECTION_ERROR 0, FLAKY 1636, TARGET_ORACLE_INVALID 7946,
  P2P_ONLY 10517.

## 2. DEV pool sizes and ENG/HOLDOUT membership

- DEV_TRAIN = 120 (salted split: **DEV_TRAIN_ENG 40** /
  **DEV_TRAIN_ASSAY_HOLDOUT 80**); DEV_VALIDATION = 30 (separate).
- DEV changed-test candidates = 111; oracle-confirmed = **47** (43 primary +
  6 symbol, 2 overlap).
- Oracle-valid by frozen split role: DEV_TRAIN_ENG **9**, ASSAY_HOLDOUT **29**,
  DEV_VALIDATION **9**. Attrition per original split (changed-test subset):
  ENG 9/29, HOLDOUT 29/62, VALIDATION 9/20.
- C4 DEV task-level: 111 attempted → 24 env-failed → 87 executable → 43
  primary eligible. Nodes: BEH 538, SYM 25, PCE 0, FLAKY 510,
  TARGET_INVALID 3727, P2P 5355.

## 3. Temporal / year distribution

- MAIN (C2) per target year: 2020→2026 all represented; yield rates
  0.05–0.77 (2026 highest, 2020 lowest). DEV (C4) per year: 2020 0.20 …
  2026 highest. Full table in
  `research/wp2/oracle_confirmation_linux_v2_2026-09-23/temporal_attrition_final_2026-09-25.json`.

## 4. Windows → Linux recovery

- `?` cassette filenames: BLOCKED on Windows → WORKS on Linux ext4.
- Unix-only `resource` module: BLOCKED on Windows → WORKS on Linux.
- Native libs (gobject/pango): collection recovered with era system superset;
  execution infeasible for one native-lib task (documented).
- Old-era (2020) and 2026-era tasks both yield confirmed BEHAVIORAL_F2P on
  Linux. Main pool grew 8 → 71 primary-eligible.

## 5. C2 PCE / SYMBOL_ABSENCE / BEHAVIORAL counts

- PCE 0, SYMBOL_ABSENCE 64 nodes / 17 tasks, BEHAVIORAL 731 nodes / 71 tasks.

## 6. C4 PCE / SYMBOL_ABSENCE / BEHAVIORAL counts

- PCE 0, SYMBOL_ABSENCE 25 nodes / 6 tasks, BEHAVIORAL 538 nodes / 43 tasks.

## 7. Environment canary outcomes

- Canary semantics implemented (unchanged pre-existing test in touched app,
  parent+target 3/3). B3 dry run recorded CANARY_NONE where no unchanged node
  existed (only changed test files were executed). Full canary execution is a
  defined evaluator-only step for the unchanged-test P2P run (not executed).

## 8. Environment attrition

- MAIN: 60/220 (27%). DEV: 24/111 (22%). Primarily py312 (2026-era resolution
  conflicts) and 2020-era native chains. Reported separately from executable
  tasks; runner DONE ≠ environment success.

## 9. Node-level reclassification examples

- `05bdc7feb9ac` py38: v1 BEHAVIORAL → v2 BEHAVIORAL (eligible, 24+1 nodes).
- `65643ec7c37f` py39: v1 ENV_BROKEN (resource) → v2 2 SYMBOL_ABSENCE + 10 P2P.
- `24f9b244d6bc` py39: v1 ENV_BROKEN (`?` path) → v2 executable (FLAKY node).
- `ab6c29ba265d` py38: v1 ENV_BROKEN (gobject) → v2 collection recovered (276
  nodes) but execution infeasible.
- `3cac33590b90` py312/2026: not-executable v1 → v2 BEHAVIORAL eligible.

## 10. Harness / image / dependency provenance

- Harness version `wp2-linux-harness-v2-2026-09-23`; test-patch rule SHA
  `f64ff583daea4b8bdec7f40293069cb009494a569a75c92d34819cd10030a969`.
- C2 records carry the original freeze hash (b11374fe); executed bundle
  documented in `harness_v2_freeze_2026-09-23_REVISED.json`.
- C4 semantic freeze identity `01c3430f…`; persistence revision
  `c4-persistence-v2-2026-09-23`.
- Era images (frozen, unchanged): py38 `1cc60658b6a2`, py39 `ddc08d7e6855`,
  py312 `0c185699947d`. PostgreSQL `postgres:15-alpine` digest
  `f7d23353…bf81`, container `wp2-pg`, port 5433,
  `fsync=off, synchronous_commit=off, full_page_writes=off`.
- Substrate: WSL Ubuntu-24.04, local dockerd (Root /var/lib/docker, socket
  /var/run/docker.sock); Docker Desktop not used.

## 11. C4 maintenance boundary

- Stopped at 72/111 for storage maintenance; worktrees cleaned; WSL shutdown +
  fstrim + VHDX compact (59.80→52.54 GiB); resumed 72→111; post-maintenance
  tasks marked (cold page cache). C4-specific log `logs/c4_orchestrator.log`.

## 12. P2P candidate inventory status

- V1 association inventory (unchanged test files, same-app, unchanged-by-target)
  covers 297 MAIN tasks (295 with ≥1 candidate). Unchanged-file node-level
  3/3 stability requires an evaluator-only unchanged-test run (NOT executed);
  preservation validation is NOT claimed complete (E2E-G6 remains final).
  C2 P2P_ONLY counts (10,517 nodes / 90 tasks) recorded as contextual signal.

## 13. Metadata reconciliations

- CI width n=8: JSON-exact 0.52–0.57 (doc's ≈0.6 corrected).
- Empty-set: Agent 2/297 vs RM-CSS 29/297 (scope-identical 31/297).
- Env families: 147 (canonical target-state) vs 140 (selection-manifest incl.
  UNKNOWN bucket).
- migration_config_heavy: summary 0 → recomputed 40/297.

## 14. Guards

- **MAIN generation QUARANTINED** (`main_generation_quarantine_2026-09-23.json`,
  297 ids, NO_GENERATION_BEFORE_RESEARCH_FREEZE).
- **INTERNAL_TEST (80) UNTOUCHED** (proof:
  `protected_pools_untouched_proof_2026-09-23.json`).
- **Sealed RESERVE (786) UNTOUCHED**.
- No generation/repair/E2E in Mission 07.

## 15. Git / tag / exports

- Commits: `3b1ead0` (harness/freeze), `c4f5fbb` (evidence/analyses),
  `1db544a` (docs/status).
- HEAD/main: `1db544a85166bee8c5e191114d331577402f4e9c`.
- Tag: `wp2-linux-oracle-dev-v2-complete-2026-09-25` → `1db544a` (pushed).
- Remote: `origin` (github.com/AhmedEhabH/dependency-aware-selective-regeneration-benchmark.git); main + tag pushed OK.
- FULL export: `project-2026-09-25-1302.zip` — 300,225,608 bytes,
  SHA256 `998a9dba8769cda4066aba5da629075f5cedcf210e5901b15af219b21ebaab5c`,
  19,918 entries, verified readable, required members present.
- TRUE LIGHT export: `project-LIGHT-2026-09-25-1304.zip` — 46,483,908 bytes
  (46.48 MB < 50 MB), SHA256
  `2d2111d89a53ec762868ccbb1b677513d34f759b4ad865e55de88a91a7cd0e60`,
  10,193 entries, verified readable.

## 16. Validation

- Full suite once at T3: **3 failed / 3969 passed / 34 skipped** (41.5 min).
  All 3 failures are in the frozen known-failures list
  (`artifacts/known_test_failures_2026-09-21.json`): 1 REAL_DEFECT (github
  boundary, pre-existing outside WP-2) + 2 ENV_OR_DATA_MISSING (pinned
  djangocms source absent). No new node IDs → acceptance rule met.
- Targeted E2 checks (16/16 PASS): JSON/JSONL integrity, uniqueness, orphans,
  duplicates, JUnit manifest, candidate membership, reconciliation, summaries.

## 17. Storage final state

- Windows C: free ≈ 42.9 GiB (used 433 GiB of ~476 GiB).
- ext4: 43G used / 913G available. `/opt/wp2_v2/worktrees` ≈ 0
  (completed C2/C4 worktrees removed evidence-safely after exports); fstrim
  done (957.7 GiB). Era images, `wp2-uv-cache`, Docker volumes preserved.

## 18. Exact next scientific action (NOT executed)

Brain authorization for **DEV Smoke / assay-sensitivity design** over the
oracle-valid DEV tasks (DEV_TRAIN_ASSAY_HOLDOUT 29 + DEV_VALIDATION 9;
DEV_TRAIN_ENG 9 available for harness/generator engineering), per amendment F.
No generation, Gold/Placebo, Gold-minus-one, or selector E2E until a separate
frozen authorization.