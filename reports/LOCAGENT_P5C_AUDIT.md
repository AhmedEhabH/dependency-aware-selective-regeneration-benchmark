# P5 — Independent Audit (P5-A, P5-B, P5-C)

**Date:** 2026-09-15

## P5-A (adapter readiness, ZERO API) — PASS

`python scripts/verify_locagent_p5a_readiness.py` → OVERALL PASS:
- locagent_output_parser_valid
- common_evaluator_metrics
- adapter_patch_empty_all_cases
- no_held_out_in_dryrun (36 allowed cases only)
- upstream_pin_frozen (4935b557326c154bad8e8dcf3747cc8d32d1f387)

## P5-B six Pre-Benchmark Validation gates — PASS (6/6)

`python scripts/validate_locagent_p5b_gates.py` → 6/6 PASS:
1. Dataset Validation
2. Prompt/Input Validation
3. Pipeline Smoke Test
4. Dry Run (6 VALIDATION cases, 0 model calls)
5. Integration Test
6. Metric Verification

## P5-B independent audit — PASS (12/12)

`python scripts/audit_locagent_p5b.py`:
- upstream pin 4935b557… ✓
- wrapper SHA + invokes upstream (no algorithm edit) ✓
- raw smoke evidence hashes ✓
- common-evaluator cost non-zero with tokens ✓
- no HELD_OUT in P5-B inputs ✓
- token usage captured ✓

## P5-C independent audit — PASS (19/19)

`python scripts/audit_locagent_p5c.py`:
1. exact 10 held-out task IDs ✓
2. no hidden-target leakage in inputs ✓
3. candidate/task mapping correct (scored set in-universe) ✓
4. frozen proxy labels across systems ✓
5. each task under frozen protocol (temp 1, num_samples 1, max_attempt_num 1,
   timeout 900, MRR) ✓
6. no poor-result reruns (cases 1-2 preserved; aborted case 3 excluded) ✓
7. timeout results retained (5 fail-closed empty) ✓
8. all ledger rows mapped to correct task (0 unknown) ✓
9. total tokens equal summed ledger usage (32,718,518 prompt + 113,256
   completion) ✓
10. model-call count equals ledger count (402) ✓
11. cost uses frozen pricing snapshot ($0.30/$1.00 per 1M) ✓
12. no secrets in evidence ✓
13. raw evidence hashes stable ✓
14. LF line-ending policy preserved ✓
15. no API secrets ✓
16. native ranking preserved (merged MRR order, 10 tasks) ✓
17. P1 evidence reused, not regenerated ✓
18. cost-audit assertion holds (non-zero usage ⇒ non-zero cost) ✓
19. six-gates manifest present ✓

## Audit conclusions

- All P5 raw evidence (P5-A manifest, P5-B validation, P5-C held-out) is
  internally consistent, leakage-free, and hash-stable.
- The authoritative LocAgent accounting is the per-call usage ledger
  (402 calls / 32.8M tokens / $9.9288); upstream `calc_cost` (returns 0 for
  qwen) is diagnostic-only.
- P5-C used ONE dedicated Benchmark credential
  (`BENCHMARK_KEY_SOURCE=SEPARATE_PARENT_ENV`), never the OpenCode auth store.
- Negative results (5/10 timeout) and the aborted case-3 attempt are preserved
  verbatim; no scientific history was sanitized.