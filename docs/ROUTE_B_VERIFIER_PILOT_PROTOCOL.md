# Route B — Bounded-Verifier Pilot Protocol (conditional; DEVELOPMENT only)

**Date:** 2026-09-17
**Tier:** T3 (live LLM verifier pilot; small, one-shot)
**Status:** FROZEN before call 1 (only triggered because the Route B V2
progression gate PASSED).
**Budget (frozen):** ≤30 independent tasks; 1 verifier call/task; ≤30 outer
calls; ≤300,000 total model tokens; ≤USD 0.30; no result-dependent reruns;
no V2 INTERNAL_TEST; no V2 RESERVE.

---

## 1. Purpose

Decompose the candidate-level omission-recovery pipeline into:
1. **First-pass omission** — files the Sparse first pass did not select;
2. **Ranking failure** — how much of the recoverable headroom Oracle@B shows
   (ranking quality of the frozen CIA ranker);
3. **Verifier failure** — whether a small LLM verifier, given the top-B CIA
   ranked omitted candidates, correctly identifies the true missed files.

This is a DIAGNOSTIC decomposition, not a headline metric.

## 2. Frozen configuration (before call 1)

- **Model:** qwen/qwen3-coder (Qwen3-Coder-480B-A35B-Instruct), identical family
  to the Sparse first-pass work.
- **Provider/route:** OpenRouter (deepinfra/turbo preferred; fallback OFF) — same
  route discipline as the registered djangoCMS study.
- **Temperature:** 0. Completion cap: 512 (small verifier judgment; keeps cost low).
- **Candidate ranker (frozen):** CIA (0.5 normalized BM25 + 0.5 graph neighbor)
  over Sparse-omitted candidates.
- **B operating points:** {1, 3, 5} (5 is the reference point; 1 and 3 for the
  curve).
- **Context payload (per task):** the intent text; the Sparse write set;
  the top-B CIA-ranked omitted candidates (paths + one-line module/class hint);
  the candidate universe size. NO hidden proxy, NO gold, NO target/future info.
- **Output schema:** JSON array of booleans {reconsider: true/false} per
  candidate presented (B entries), plus an optional one-line rationale per entry.
- **Parser:** strict JSON array decode; failure semantics = fail-closed (a
  non-parseable call is recorded as a failure, not retried).
- **Metric:** per-task, the verifier's "reconsider=true" set ∩ true missed
  candidates, compared against the same-budget Oracle and against the CIA
  ranker alone (top-B without the verifier). Decomposition:
  - first-pass omission = Sparse FNs;
  - ranking headroom = Oracle@B recovered FNs;
  - verifier recovery = verifier-selected ∩ true missed at B;
  - InspectAll = all missed recoverable at full reconsideration.

## 3. Selection of the ≤30 tasks

- Deterministic, seeded (20260917): a stratified sample of DEVELOPMENT tasks
  (DEV_TRAIN + DEV_VALIDATION + V1_DEV) that have ≥1 Sparse FN among omitted
  candidates (i.e., the omission-recovery regime is non-trivial). Prefer tasks
  where the CIA ranker has a non-empty omitted set and B=5 < omitted set size.
- INTERNAL_TEST and RESERVE are never touched.

## 4. Budget accounting

- Prompt ≈ 1,200–1,800 tokens; completion cap 512; per-call ≈ 2,000 tokens ≈
  $0.0008–$0.0010 (frozen pricing). 30 calls ≈ $0.025–$0.03, well under $0.30.
- Fail-closed: stop immediately if cumulative tokens > 300,000 or cost > $0.30.

## 5. Decomposition report

- First-pass omission: |Sparse FN set| per task.
- Ranking headroom: Oracle@B recovered FNs (from Route B V2 results).
- Verifier recovery@B: verifier-selected ∩ true missed.
- Verifier vs CIA-alone@B (does the verifier add over the ranker?).
- InspectAll reference.
- tokens / calls / cost / latency / failures.
- Task-level aggregation; repetitions are never independent.

## 6. Outputs

- `reports/ROUTE_B_VERIFIER_PILOT_REPORT.md`
- `research/transparency/route_b_verifier_pilot_results.json`
- raw responses + sha256 sidecars