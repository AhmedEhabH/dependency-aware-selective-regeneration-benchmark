# Mission-09 — P2P V2 Gold Freeze + ENG Execution — Impact Declaration (2026-09-25)

Status: **IMPACT DECLARATION.** Declared before any substantive edit, per the
single authoritative OpenCode Execution & Validation Protocol v2 (Tier T3) and
Mission-09 §1–§2.

Authority chain: Mission-09
(`_workspace/active/MISSION_09_P2P_V2_GOLD_FREEZE_ENG_2026-09-25.md`) issued from
the completed Mission-08 checkpoint. All scientific decisions in the mission are
authoritative and frozen; this declaration records execution identity, scope,
non-scope, and verification plan only.

## 1. Execution identity

- Branch: `main`
- HEAD at start: `eb5e21de3def6802b6a05e962d58bea75187c046` == `origin/main`.
- Working tree: Mission-08 checkpoint artifacts present as uncommitted state
  (Mission-08 STOP report, DEV inventory, discovery JSONL, serial pilot
  evidence, Smoke draft, c4_clarification blocks on both MAIN inventories,
  scripts + module + tests). These are the completed Mission-08 outputs we start
  from; Mission-09 extends them without rewriting Mission-07/08 history.
- Mission model/API budget: **$0.00. ZERO LLM/OpenRouter/embedding calls.**
- Tier: **T3** (new evaluation strategy/baseline family). No model/API calls, no
  generation, no repair, no Smoke execution, no assay, no E2E, no HOLDOUT/
  VALIDATION/MAIN outcome execution, no INTERNAL_TEST, no RESERVE access.

## 2. Files and outputs Mission-09 WILL create or change

### 2.1 Mission-08 errata (append-only; no reruns) — M9-1
- `docs/WP2_DEV_P2P_PHASE_A_STOP_REPORT_2026-09-25.md` — append ERRATUM A (RAM
  field: `wsl_mem_before_gib=13.0` was WSL TOTAL, not peak; true peak NOT
  measured; do not claim 13 GiB peak; do not claim workers=2 impossible) and
  ERRATUM B (GraphQL wording: ~92.1% task–test-file association occurrences;
  ~54.7% unique associated test files; do not conflate).
- `docs/WP2_DEV_SMOKE_DESIGN_DRAFT_2026-09-25.md` — ERRATUM C: fix stale DEV
  inventory SHA (`7ac2bd8d…`) to the final Mission-08 SHA
  `0ae5699b890ed3fe7a18cdbfb59bcb53d31d21f091102bef87f15b241ce2bf61`.

### 2.2 P2P-S primary preservation freeze — M9-2
- New artifact (e.g. `research/wp2/wp2_dev_p2p_s_v1_2026-09-25.json`) freezing,
  per oracle-valid DEV task, the P2P_ONLY node IDs extracted from the FINAL
  Mission-07/C4 per-test evidence (`per_test_dev_v2.jsonl`), with defined/sparse/
  evaluator_only/invisible flags and hashes. No new oracle construction
  execution.

### 2.3 P2P-U V2 rule + membership freeze — M9-3
- New rule-freeze artifact (exact scientific rule, salt
  `wp2-p2p-u-v2-2026-09-25`, proximity definition, proximal/distal pools,
  ordering, backfill, caps 200/400, execution semantics, taxonomy, rule SHA).
- New ordered-membership artifact (raw candidates, proximity, proximal/distal,
  cap200/cap400 membership, hashes) frozen BEFORE any V2 outcome execution.

### 2.4 Real resource instrumentation — M9-4
- New resource sampler (separate process; 5 s interval; monotonic timestamps)
  covering Windows host RAM, WSL `/proc/meminfo`, Docker stats (test container +
  PostgreSQL), CPU, disk/IO, time-phase logging. Corrects the Mission-08 gap
  (no `total`-as-`peak` confusion).

### 2.5 P2P-U V2 ENG execution — M9-5/M9-6
- Executes on the 9 oracle-valid ENG tasks only; `saleor-rc-9258154b8a0b` has
  zero unchanged candidate nodes => P2P-U UNDEFINED => no execution (expected
  executed tasks = 8). cap200 independent + cap400 independent, workers=1.
  Evidence persisted under `research/wp2/p2p_u_v2_eng_2026-09-25/`.

### 2.6 Estimates, Smoke draft, reports — M9-7/M9-8/M9-9
- DEV-47 + future MAIN P2P-U cap200 estimates (from real ENG data).
- Updated `docs/WP2_DEV_SMOKE_DESIGN_DRAFT_2026-09-25.md` (draft only).
- STOP report + decision token + FULL/TRUE LIGHT exports + tag.

### 2.7 Documentation / governance touched
- `DECISIONS.md` (append-only).
- `PROGRESS.md` (at final STOP only).
- `docs/LIVE_STATUS.json` via `scripts/render_live_status.py --write` (mission
  outcome block; end of mission).
- `docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md` only if a concrete defect is
  found (no change is currently planned).
- README only if user-facing behavior changes (none expected).

## 3. Explicit non-changes
- No modification of P2P V1 history, no rerun of Mission-07/C4, no rerun of the
  Mission-08 V1 pilot, no new P2P-S oracle construction execution.
- No HOLDOUT/VALIDATION/MAIN P2P-U outcome execution; no cap/salt tuning after
  outcomes; no workers=2; no `.wslconfig` change.
- No evaluator leakage: gold touched paths, P2P-S/P2P-U node IDs, cap memberships,
  proximity, proximal/distal labels, test patch, target diff/outcomes stay
  evaluator-only and invisible to generation/repair.
- No changes to INTERNAL_TEST, RESERVE, or any generation/repair arm.

## 4. Verification plan (targeted; per Protocol v2 §24)
- P2P-S: exact extraction from per_test records; membership; zero/undefined
  handling; SHA repeatability.
- P2P-U V2: no changed test file in pool; no outcome dependence; exact
  deterministic regeneration; rule/ordered-candidate SHA stable; first200 ⊂
  first400 per task; proximal/distal reproducible; UNKNOWN handling; selected
  node IDs ∈ frozen Mission-08 raw inventory.
- Execution: parent includes frozen test patch; target correct; 3+3 reps;
  evidence integrity; JUnit parse integrity; DB/worktree lifecycle; independent
  200/400 runs.
- Resources: sampler validated vs raw sources; `used` ≠ `total`; monotonic
  timestamps.
- Code: py_compile + ruff + mypy (production) + targeted WP2 tests + new unit
  tests (deterministic ordering, pool shortage/backfill, UNKNOWN, zero-node,
  nesting, round-robin, classification precedence). No full historical suite run
  unless a concrete change requires it.

## 5. Scientific guardrails honored
- Ground Truth evaluation-only; zero-node tasks are UNDEFINED, never automatic
  PASS.
- V1 remains immutable historical evidence; V2 is an explicitly versioned
  amendment frozen BEFORE any V2 outcome execution.
- Storage thresholds: WARNING <40 GiB, HARD STOP <32 GiB (PowerShell `/1GB`);
  C: free verified before execution.
- Hard stops of Mission-09 §20 remain active.