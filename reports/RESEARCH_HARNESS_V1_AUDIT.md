# RESEARCH HARNESS V1 — INDEPENDENT AUDIT

**Audited by:** openrouter/deepseek/deepseek-v4-flash-0731 (implementation AI;
independent read-only pass over persisted artifacts + code).
**Basis:** persisted evidence only — `reports/research_harness_v1_gates.json`,
`research/harness-protocol-a-equivalence/raw_predictions_via_harness_v1.json`,
frozen `research/cheap-baselines-v1/*.json`, frozen dataset. It does NOT trust
in-memory runner objects.
**Verdict:** **PASS** — six T3 gates + interface/leakage/determinism/budget/
config-reproducibility/isolation checks green; Protocol-A outputs reproduced
byte-for-byte through the compatibility layer; frozen evidence unchanged.

## 1. What was checked

| # | Check | Result |
|---|---|---|
| 1 | Gate 1 Dataset Validation: adapter split counts 24/6/10, case-count 40, proxy ⊆ universe | PASS |
| 2 | Gate 2 Input/Query Validation: public intent only; no semantic-gold markers in 6 sampled cases | PASS |
| 3 | Gate 3 Pipeline Smoke Test: all 5 frozen rankers through the harness on a synthetic case; bounded top-K; ZERO LLM | PASS |
| 4 | Gate 4 Dry Run: metadata-mode 2-case slice → 2 cases × 20 rows; zero LLM | PASS |
| 5 | Gate 5 Integration Test: registry resolves all concrete seams; interface-only RiskScorer/Verifier abstract; config SHA-256 reproducible | PASS |
| 6 | Gate 6 Metric Verification: synthetic TP=2/FP=1/FN=1 → P=R=2/3, F1=2/3, FNR=1/3 | PASS |
| 7 | Hidden-gold access: public case has no proxy field; held-out split fails closed; ranker never receives proxy | PASS |
| 8 | Deterministic ranking: identical inputs + frozen seed → identical ranked paths (restart determinism) | PASS |
| 9 | Budget enforcement: zero-LLM spec fails on any model call; call/token/wallclock bounds raise; budget persisted in spec | PASS |
| 10 | Dataset-adapter isolation: rankings identical across adapter implementations; ranker sees only `PublicCase` | PASS |
| 11 | Config reproducibility: identical config → identical spec SHA-256; JSON round-trip preserves hash | PASS |
| 12 | RiskScorer/Verifier interface-only: no concrete registration; cannot be instantiated | PASS |
| 13 | Saleor seam fails closed: instantiation raises NotImplementedError | PASS |
| 14 | Protocol-A equivalence: full 30-case × 5-method × 4-K = 600-row scientific projection byte-identical to frozen evidence; per_task + aggregates identical | PASS |
| 15 | Frozen evidence untouched: git status shows no modifications to `research/cheap-baselines-v1/`, `benchmark_data/`, frozen P1/P5, paper | PASS |

Gate JSON: `reports/research_harness_v1_gates.json` (all_gates_passed=true).

## 2. Leakage audit (independent)

- **No proxy in method code:** `Ranker`/`Planner` receive only the public case
  bundle; `load_hidden_proxy_paths` is called only in the runner's scoring
  step and by the dataset adapter's own fail-closed guard.
- **Split policy:** HELD_OUT_TEST fails closed both in the adapter and in the
  runner split check.
- **No future state:** snapshots are parent-commit-only (metadata or
  `git archive <parent>`); target commit is metadata only.
- **No semantic gold:** intent is the frozen public full message (same input
  the P1 planner saw); frozen-corpus path-mention caveat applies unchanged.
- **ZERO new API:** every harness backend is `none` (fail-closed on call) or
  `mock` (test-only); the equivalence run made zero model calls.

## 3. Reproducibility

- `scripts/verify_research_harness_v1.py` regenerates
  `reports/research_harness_v1_gates.json` deterministically (ZERO API).
- `scripts/run_harness_protocol_a_equivalence.py` regenerates the equivalence
  evidence and asserts byte-identical scientific output against the frozen
  persisted evidence.
- `tests/integration/test_harness_protocol_a_equivalence.py` runs the same
  equivalence for a 2-case slice inside pytest (git cache required, else
  skipped — same policy as the cheap-baselines gate 5).
- `tests/unit/test_harness_*.py` cover interfaces, config reproducibility,
  hidden-gold, budget, determinism, isolation, and interface-only seams.

## 4. Independent recomputation

The audit independently recomputed TRAIN/VALIDATION/TRAIN_VALIDATION micro
aggregates from the frozen per-task rows for the equivalence compared cases
and matched the harness aggregate view (test
`test_aggregate_view_matches_frozen_micro_for_compared_cases`).

## 5. Caveats

- Literature rows other than LocAgent are SEEDED (status column) and must be
  verified against primary sources before any thesis claim.
- Timing fields are excluded from equivalence (non-deterministic by nature).
- The harness is V1 architecture; the Omission-Risk Feature Study v1 is the
  next scientific step and is NOT started by this milestone.