# P5 — Independent Audit (P5-A, P5-B, P5-C)

**Date:** 2026-09-15
**Last strengthened audit run:** 2026-09-15 (zero-API correction phase)

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

## P5-C independent audit — PASS (28/28, strengthened 2026-09-15)

`python scripts/audit_locagent_p5c.py`:
1. exact 10 held-out task IDs ✓
2. no hidden-target leakage in inputs ✓
3. candidate/task mapping correct (scored set in-universe) ✓
4. frozen proxy labels across systems ✓
5. each task under frozen protocol (temp 1, num_samples 1, max_attempt_num 1,
   timeout 900, MRR) ✓
6. no poor-result reruns (cases 1-2 preserved; aborted case 3 excluded) ✓
7. empty outcomes retained (5 fail-closed empty) ✓
8. **empty-outcome taxonomy matches raw logs: 2 timeout, 1 context-length
   BadRequest, 2 completed-but-empty — NOT "5 timeouts"** ✓
9. **empty-outcome taxonomy not-all-timeout (exactly 2 timeout cases)** ✓
10. all ledger rows mapped to correct task (0 unknown) ✓
11. total tokens equal summed ledger usage (32,718,518 prompt + 113,256
    completion) ✓
12. model-call count equals ledger count (402) ✓
13. cost uses frozen pricing snapshot ($0.30/$1.00 per 1M) ✓
14. no secrets in evidence ✓
15. raw evidence hashes stable ✓
16. LF line-ending policy preserved (committed blobs LF) ✓
17. no API secrets ✓
18. native ranking preserved (merged MRR order, 10 tasks) ✓
19. P1 evidence reused, not regenerated ✓
20. cost-audit assertion holds (non-zero usage ⇒ non-zero cost) ✓
21. six-gates manifest present ✓
22. **official Acc@K reproduced from raw evidence: Acc@1=4/10, Acc@3=4/10,
    Acc@5=2/10 (task hit iff correct-in-topK == min(len(proxy), K))** ✓
23. **item-hit sums 4/8/9 are audit-only and NOT labelled task accuracy** ✓
24. **ledger provider = openrouter only (gateway), no per-call backend pin** ✓
25. **provider-route note present (OpenRouter-routed Qwen3-Coder)** ✓
26. **provider-route ambiguity logged (Venice upstream error in localize.log)** ✓
27. **efficiency denominator consistent (mean per execution/task: LocAgent/Full
    ≈245.7× tokens, ≈100.1× cost; LocAgent/Sparse ≈593.8× tokens, ≈477.8×
    cost)** ✓
28. no hidden-target leakage (repeat guard) ✓

## Audit conclusions

- All P5 raw evidence (P5-A manifest, P5-B validation, P5-C held-out) is
  internally consistent, leakage-free, and hash-stable.
- The authoritative LocAgent accounting is the per-call usage ledger
  (402 calls / 32.8M tokens / $9.9288 normalized estimate); upstream
  `calc_cost` (returns 0 for qwen) is diagnostic-only.
- P5-C used ONE dedicated Benchmark credential
  (`BENCHMARK_KEY_SOURCE=SEPARATE_PARENT_ENV`), never the OpenCode auth store.
- Negative results (5/10 empty: 2 timeout, 1 context-length BadRequest,
  2 completed-but-empty) and the aborted case-3 attempt are preserved
  verbatim; no scientific history was sanitized.
- **Provider-route limitation (2026-09-15):** the ledger records
  `provider="openrouter"` (the OpenRouter gateway), not the resolved backend;
  raw logs show both DeepInfra and Venice upstream errors, so an unqualified
  per-call DeepInfra pin is NOT supported. P5 wording is corrected to
  "OpenRouter-routed Qwen3-Coder" and the route-provenance limitation is
  disclosed. The $9.9288 cost is a NORMALIZED estimate under the frozen P1
  pricing snapshot, not authoritative provider-billed cost.
- **Native Acc@K correction (2026-09-15):** official Acc@1=4/10, Acc@3=4/10,
  Acc@5=2/10. The historical 4/10, 8/10, 9/10 claims were cross-task sums of
  matching FILE ITEMS and are NOT task accuracy.