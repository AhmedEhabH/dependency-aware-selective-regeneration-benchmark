# Mission-10B — Phase 1 — Full-Text Root-Cause Audit (2026-09-26)

Status: **COMPLETE** (zero-API, deterministic). Fixes the Mission-10A truncated
`raw_error_text` limitation and the merged-repetition node→text map by
re-parsing the FULL `<error>`/`<failure>` element text from C4/C2 Linux V2
JUnit and Mission-09 P2P-U ENG evidence, then attributing root causes at the
node/repetition level with the Mission-10B V3 taxonomy (§7.1–§7.5).

Machine-readable evidence root:
`research/wp2/harness_v3_2026-09-26/`:

- `phase1_c4_node_attribution.json` — per-node attribution + reconciliation +
  materiality (composite keys `task_id::node_id`).
- `phase1_c4_fulltext_records.jsonl` — 10,985 full-text C4 target rep-records.
- `phase1_c2_rescue_attribution.json` / `phase1_c2_fulltext_records.jsonl`.
- `phase1_p2pu_eng_attribution.json`.
- `phase1_hypotheses_verification.json` — independent-review verification.
- `phase1_summary.json`.

Code/tests: `src/benchmark/wp2/m10b_fulltext.py`,
`scripts/wp2_m10b_phase1_audit.py`, `tests/unit/wp2/test_m10b_fulltext.py`
(24 tests PASS).

---

## 1. Reconciliation (7.4) — EXACT

C4 authoritative TARGET_ORACLE_INVALID = **3,727** reconciled exactly
(mismatch **0**):

| bucket | count |
|:---|---:|
| error-bearing (3 target reps = error) | 3,682 |
| failed-only (3 target reps = failed) | 45 |
| STABLE_CAUSE (all 3 target reps, same family) | 2,592 |
| MIXED_CAUSE (reps differ in family) | 1,055 |
| MISSING_EVIDENCE (raw text absent) | 35 |
| FAILED_ONLY | 45 |
| **reconciled total** | **3,727** |

P2P-U ENG cap200 COLLECTION_ERROR = **41 / 41** reconciled exactly (7 tasks,
mismatch 0), all STABLE_CAUSE.

C2 rescue: 159 tasks / 2,994 JUnit files parsed; node-level attribution scoped
honestly to rescue-evidence coverage (8,620 error-bearing nodes; task-level
denominators remain per_task_v2.jsonl authority).

## 2. Full-text taxonomy distribution (rep-level, C4 target)

| taxonomy | rep-records |
|:---|---:|
| INFRA:EMFILE | 9,676 |
| DB:WRONG_CONSTRAINTS | 1,066 |
| MISSING_FIXTURE:count_queries | 237 |
| MISSING_FIXTURE:mocker | 6 |

No DB:OTHER / TIME / INSTALL / COLLECTION records at the C4 target side under
the V3 taxonomy. EMFILE is concentrated in **py38/py39 only** (py39 7,087 /
py38 2,589 rep-records); MISSING_FIXTURE is **py312** (234/237 records).

## 3. Node-level causal attribution (7.3) — NEVER task-level

- **STABLE_CAUSE = 2,592 nodes**, of which **INFRA = 2,511** and
  **MISSING_FIXTURE = 81**.
- **MIXED_CAUSE = 1,055 nodes** — all exactly `2× INFRA:EMFILE + 1×
  DB:WRONG_CONSTRAINTS`, restricted to two tasks
  (`saleor-rc-46a2a565f410`: 569, `saleor-rc-f813a9fd37d3`: 486). This is the
  mechanistically expected **EMFILE → partial DB creation → reuse →
  WRONG_CONSTRAINTS** chain (§1D hypothesis direction, to be tested).
- **MISSING_EVIDENCE = 35 nodes** across 10 tasks (full text not present in
  archived junit for those reps).
- Secondary ≥2/3 majority-cause table (descriptive only, never the gate):
  INFRA 3,578 · MISSING_FIXTURE 81 · DB 1.

## 4. Materiality (14.3, node-level)

| metric | value |
|:---|---:|
| numerator (STABLE_CAUSE in INFRA+DB+MISSING_DECLARED_DEP) | **2,592** |
| by family | INFRA 2,511 · MISSING_FIXTURE 81 |
| denominator (error-bearing TOI) | 3,682 |
| **share of error-bearing** | **70.4%** |
| denominator (sufficient full evidence = 3,682 − 35) | 3,647 |
| **share of sufficient-evidence** | **71.1%** |
| missing-evidence count | 35 |
| mixed-cause count | 1,055 |

Preregistered Phase-4 threshold (≥ 20%) is **far exceeded** under node-level
stable attribution. No task-level co-occurrence is used.

## 5. Independent-review hypothesis verification (7.5)

| hypothesis | reviewed | verified |
|:---|:---|:---|
| EMFILE in 29/46 C4 JUnit-bearing tasks, py38/py39 only | 29 | **29 tasks, py38/py39 only** ✓ |
| ~10,929 parent + 10,853 target EMFILE records | — | **9,676 target rep-records** (parent-side TOI not required by C4 authority) |
| ~3,593/3,727 nodes contain EMFILE | — | **3,587 nodes with ≥1 INFRA rep** (97% match) |
| node-level share attributable to EMFILE | — | **2,511 / 3,682 = 68.2% STABLE-INFRA** |
| C2 rescue EMFILE in 58/159 tasks | 58 | **58 / 159** ✓ |
| ~1,100 WRONG_CONSTRAINTS records | — | **1,066 records / 714 nodes / 2 tasks** |
| 10 ENG candidates EMFILE-affected, none primary-eligible | 10 | **10 ENG EMFILE tasks, all NOT_PRIMARY** ✓ (+1 MISSING_FIXTURE py312 ENG task → 11 materiality-family) |
| largest ENG example saleor-rc-c3b9e396b07d ≈416 TOI | 416 | **416 TOI nodes** ✓ |

## 6. Interpretation

- The dominant node-level cause of C4 TARGET_ORACLE_INVALID is an
  **infrastructure EMFILE defect** during Django test-DB creation/migrations,
  restricted to py38/py39, mechanically attributable at the node level for
  **2,511 nodes (68.2% of error-bearing TOI)** — not a semantic oracle defect.
- DB:WRONG_CONSTRAINTS (1,066 records) only ever appears mixed with EMFILE in
  the same node (2×EMFILE+1×WC), supporting the partial-DB-reuse hypothesis
  direction; never a stable standalone cause.
- Mission-10A's declared-but-not-installed dev/test dependency mechanism is
  reconfirmed at the node level: 81 stable MISSING_FIXTURE nodes (py312 +
  py39), count_queries/mocker only.
- The 45 failed-only nodes are true target-side assertion failures (not infra).
- This is infrastructure recovery, NOT model improvement (§36). V2 remains
  immutable; V3 corrects infrastructure only.

## 7. Validation

- py_compile PASS; ruff PASS; mypy strict PASS (`m10b_fulltext.py`);
  `tests/unit/wp2/test_m10b_fulltext.py` 24 PASS.
- Reconciliation exact (C4 mismatch 0; P2P-U mismatch 0; C2 scoped).
- No model/API call; no frozen artifact mutation.