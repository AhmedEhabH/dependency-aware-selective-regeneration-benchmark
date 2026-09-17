# djangoCMS Confirmatory API Budget Freeze

**Date:** 2026-09-17
**Tier:** T3 scientific documentation — frozen pre-authorization budget
**Status:** **FROZEN (zero test peek).** Derived ONLY from DEVELOPMENT
distributions/maxima (djangoCMS DEV sparse first-pass cells + the 30-call
verifier pilot). djangoCMS INTERNAL_TEST prompts, gold, labels, and outcomes are
NOT inspected. **No API call is made in this mission.**

**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 1. Planned confirmatory run (frozen scope)

- **80 independent djangoCMS INTERNAL_TEST tasks.**
- **Sparse-v2 first pass** using the already-frozen repetition policy:
  **3 nested reps per task → the FIRST SUCCEEDED rep's `predicted_write_set`
  is the one write-set used by Route B** (frozen dedupe semantics; not a
  majority vote, not a union). Failed reps are skipped (not retried); a task
  with no succeeded rep is excluded.
- **Bounded verifier** at **B = {1,3,5,10}** (B=0 → NO verifier call).
  Exactly **1 verifier call per (task, B)** pair; calls at different B are
  **independent** (each inspects its own top-B candidate set; NOT reused).

## 2. Basis: DEVELOPMENT evidence only (frozen)

### 2.1 Sparse first-pass per-cell distribution (djangoCMS DEV, N=520 succeeded cells)
| Stat | total_tokens | api_cost (USD) |
|---|---:|---:|
| mean | 5,714 | 0.00200 |
| p50 | 5,406 | 0.00198 |
| p90 | 7,033 | 0.00226 |
| p95 | 7,141 | 0.00254 |
| p99 | 7,877 | 0.00302 |
| max | 19,461 | 0.01604 |

### 2.2 Verifier per-call distribution (30-call pilot, djangoCMS DEV)
| Stat | total_tokens | api_cost (USD) |
|---|---:|---:|
| B=1 mean | 206 | 0.000064 |
| B=3 mean | 225 | 0.000070 |
| B=5 mean | 244 (max 333) | 0.000079 (max 0.000111) |
| B=10 estimated mean | ~291 (extrapolated: prompt ~ +7.5 tok/candidate, completion ~ +2/candidate) | ~0.000094 |

## 3. Frozen budget (from the distributions above, ZERO test peek)

### 3.1 Calls
| Line | Cells/calls | Formula |
|---|---:|---:|
| Sparse first pass | 80 × 3 = **240 cells** | one model call per cell |
| Verifier | 80 × 4 = **320 calls** | one call per (task, B), B∈{1,3,5,10} |
| **Expected calls** | **560** | 240 + 320 |
| **Worst/upper-bound calls** | **560** | deterministic; NO retries, NO result-dependent reruns, B=0 has no call |

### 3.2 Tokens
| Line | Expected | Conservative ceiling basis |
|---|---:|---:|
| Sparse first pass | 240 × 5,714 ≈ **1,371,416** | per-cell reservation at **p99 = 7,877** → 240 × 7,877 = 1,890,480 |
| Verifier | 320 × ~225 ≈ **71,979** | per-call reservation at **400** (covers B=10 max with headroom) → 320 × 400 = 128,000 |
| **Expected total tokens** | **~1,443,395** | — |
| **Conservative hard token ceiling** | **2,100,000** | 1,890,480 + 128,000 = 2,018,480, rounded up to the next 100k |

### 3.3 USD cost (frozen DeepInfra-through-OpenRouter pricing: $0.30/$1.00 per 1M prompt/completion)
| Line | Expected | Conservative ceiling basis |
|---|---:|---:|
| Sparse first pass | 240 × 0.00200 ≈ **$0.48** | per-cell reservation at p99 = $0.00302 → 240 × 0.00302 = $0.7241 |
| Verifier | 320 × 0.000076 ≈ **$0.024** | per-call reservation at $0.00015 → 320 × 0.00015 = $0.0480 |
| **Expected USD** | **~$0.50** | — |
| **Conservative hard USD ceiling** | **$1.00** | 0.7241 + 0.0480 = $0.7721, rounded up to $1.00 |

## 4. Per-call reservation rule (fail-closed; cumulative budget cannot overshoot materially)

- Maintain **cumulative_reserved_tokens** and **cumulative_reserved_cost**, each
  incremented by the per-call reservation BEFORE the call is dispatched:
  - sparse cell reservation = **7,877 tokens / $0.00302** (p99 observed);
  - verifier call reservation = **400 tokens / $0.00015** (B=10-safe).
- **Stop condition:** if `cumulative_reserved + next_reservation` would exceed
  the hard ceiling (**2,100,000 tokens** OR **$1.00**), the run STOPS fail-closed
  BEFORE dispatching the next call. No call is dispatched that would breach the
  ceiling; the ledger makes a material overshoot impossible by construction.
- **Tracked in addition:** actual per-call usage (tokens/cost) recorded after
  each call; the actual cumulative must also never exceed the hard ceilings
  (any overshoot is fail-closed engineering, reported, and never silently
  absorbed).
- **Failure semantics:** a failed/truncated/schema-invalid call is recorded
  (fn added, no partial credit), NEVER retried, NEVER re-dispatched; excluded
  tasks (no succeeded rep) do not add verifier calls.

## 5. Hard limits summary (frozen)

| Quantity | Expected | Hard ceiling |
|---|---:|---:|
| Calls | 560 | 560 (no retries) |
| Tokens | ~1,443,395 | **2,100,000** |
| USD | ~$0.50 | **$1.00** |
| B curve | {0,1,3,5,10} | B=0 no verifier call |

## 6. Constraints

- **No confirmatory model call is made in this mission** (this document is
  prepared from DEVELOPMENT evidence only).
- INTERNAL_TEST prompts, gold, labels, and outcomes are NOT inspected.
- Any confirmatory execution requires Ahmed's explicit approval of this frozen
  budget together with the confirmatory freeze packet V2
  (`reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_FREEZE_PACKET_V2.md`).