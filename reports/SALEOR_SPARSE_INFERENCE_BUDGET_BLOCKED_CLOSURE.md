# Saleor Sparse Inference — Budget-Blocked Closure Report (Block C)

**Date:** 2026-09-17
**Tier:** T3 scientific inference
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Status:** **BLOCKED (BUDGET, FAIL-CLOSED)** — 1/450 cells executed as a live
smoke validation; the full 450-cell Saleor DEVELOPMENT sparse run does NOT fit
the authorized hard ceiling and is NOT run.

---

## 1. Authorization context

- Block B (portability fix + 150/150 bundles) PASSED fully → Block C authorized.
- All 8 pre-call gates PASSED (`reports/saleor_inference_gates.json`):
  dataset validation, input validation, pipeline smoke, dry run, integration,
  metric verification, portability equivalence (98/98), independent audit.
- Freeze before call 1: Sparse-v2 contract (qwen/qwen3-coder @ deepinfra/turbo,
  temp 0, cap 16384, Graph OFF), 3 reps/task, 150 DEV tasks = 450 cells.

## 2. Hard ceiling (mission Section C)

| Ceiling | Authorized | Required (450 cells) | Over |
|---|---|---|---|
| Cells | ≤ 450 | 450 | 0 (OK) |
| Total tokens | ≤ 2.7M | **~6.5–7.4M** | **2.4–2.7×** |
| Cost USD | ≤ $1.00 | **~$2.10–2.23** | **2.1–2.2×** |

## 3. Measured evidence (NOT assumed)

**Live smoke cell** (1/450, first in manifest, run 2026-09-17):

- `saleor-djangocms-rc-012472eb8482-sparse_v2-r1`
- prompt_tokens **14,052**; completion_tokens **508**; total **14,560**
- api_cost **$0.004724**
- terminal_status **succeeded**; schema_valid **True**; raw response + SHA-256 persisted
- candidate count: **671**

**Calibration across 10 candidate-size-stratified dev cases** (prompt char
length → token estimate, ratio 44,195 chars = 14,052 tokens from the smoke call):

| Percentile | est prompt tokens/cell |
|---|---|
| min (403 cand) | ~10,900 |
| median (761 cand) | **~16,050** |
| max (1142 cand) | ~22,150 |

**Projection (450 cells × 3 reps):**

- Median-case: 16,551 tok/cell (incl. ~500 completion) × 450 = **~7.45M tokens**, **~$2.23**
- Smoke-case: 14,560 tok/cell × 450 = **~6.55M tokens**, **~$2.13**

## 4. Decision — FAIL CLOSED (documented)

The mission's hard ceiling is **≤450 cells, ≤2.7M tokens, ≤$1.00, fail closed on
budget**. The measured Saleor per-cell cost is ~2.4–2.7× the token ceiling and
~2.1–2.2× the cost ceiling. Running the full 450-cell development sparse
inference is therefore **NOT authorized** by the mission's own budget rule.

- **What was run:** exactly 1 live smoke cell ($0.0047, 14,560 tokens) to
  validate the live path and measure the true per-cell cost. This is valid
  evidence, persisted, and well within budget.
- **What was NOT run:** the remaining 449 cells. No partial protocol reduction
  (fewer tasks, fewer reps, smaller universe) was silently applied — that would
  be researcher degrees of freedom and would produce a result non-comparable to
  the djangoCMS V2 study.
- **Why not a subset:** the mission specifies "150 tasks" and "3 nested
  reps/task" with the Saleor protocol (§4) frozen at 3 reps. A subset is a
  protocol change requiring explicit authorization, not a routine decision.
- **Cost so far:** $0.004724 (0.47% of the $1.00 ceiling).

## 5. What this means for downstream blocks

- **Block D (Saleor Route-B replication)** requires "Only after Section C
  completes" → **also blocked** (C did not complete). The Route-B transfer test
  CANNOT be computed without Saleor model predictions.
- **Blocks E, F, G (freeze packet, P2 prereg, semantic audit machine-prep) are
  independent** → continue.

## 6. Recommended next step (for a later, explicitly-authorized session)

Options (any ONE requires explicit authorization; none chosen tonight):
1. **Raise the ceiling** for Saleor DEV sparse inference to a measured
   basis: 450 cells ≈ ~7.5M tokens / ~$2.25 (2.8× token, 2.25× cost over the
   current ceiling) — a new frozen budget before any further calls.
2. **Pre-register a documented subset** (e.g., a fixed deterministic subset of
   DEV tasks, or 1 rep/task instead of 3) as a labeled "reduced-budget
   development subset" — explicitly non-comparable to the djangoCMS 3-rep study.
3. **Shrink the Saleor candidate universe** via a documented, pre-registered
   production-scope rule — a protocol change, deferred.

The 1 smoke cell is kept as measured evidence of the true per-cell cost.

## 7. Persisted evidence

- `research/saleor-sparse-inference/saleor_dev_run_records.jsonl` (1 record)
- `research/saleor-sparse-inference/saleor_dev_runs/<run_id>.json` + `raw/<run_id>.txt` + `.sha256`
- `reports/saleor_inference_gates.json` (8 gates PASS before call 1)
- `research/transparency/saleor_portability_fix_evidence.json` (Block B)