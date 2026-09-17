# djangoCMS Route-B Confirmatory-Freeze Packet

**Date:** 2026-09-17
**Tier:** T3 scientific documentation — ready-to-approve freeze packet
**Status:** **FROZEN PACKET (ready for approval). djangoCMS INTERNAL_TEST is NOT
opened in this mission.** No confirmatory inference is run here; the packet
freezes the exact method, endpoints, code, and hashes so that the confirmatory
test can be executed later by an authorized session with no researcher degrees
of freedom.

**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 1. Purpose and confirmatory scope

The Route B V2 DEVELOPMENT robustness closure (174 development tasks) PASSED the
progression gate: the frozen Classical-CIA ranker recovers Sparse-omitted
historically-changed files above the analytic hypergeometric Random control
across the full budget curve, with task-level bootstrap intervals excluding zero
at every B>0. This packet freezes everything needed to run the **confirmatory**
djangoCMS INTERNAL_TEST.

**Confirmatory choice (per mission Section E):**
> **B. ranking + actual verifier** — the confirmatory claim is the end-to-end
> conditional-verifier budget curve (ranker produces an ordered candidate list;
> the frozen verifier inspects top-B candidates; recovery is measured against the
> hidden observed-change proxy). Rationale: the DEVELOPMENT result includes the
> Oracle-in-top-B = 1.000 verifier-pilot finding, so a ranking-only confirmatory
> test would under-claim the actual proposal (bounded omission recovery with a
> real verifier). The verifier protocol is already frozen
> (`docs/ROUTE_B_VERIFIER_PILOT_PROTOCOL.md`) and was piloted at 30 calls.

**What is confirmatory (A/B):**
- A. Ranking-only Route B: NOT chosen as the sole claim.
- B. Ranking + actual verifier: **CHOSEN** (end-to-end conditional-verifier
  budget curve on djangoCMS INTERNAL_TEST).

## 2. Frozen method (exact, pre-result)

### 2.1 Candidate definition
- Candidate per task = files decoded/treated as Sparse PRESERVE / omitted
  candidates = candidate universe minus the Sparse write set.
- Evaluation-only positive = file in the hidden observed-change proxy AND
  Sparse omitted it (Sparse-observed FN at file level).
- Gold/proxy NEVER enters candidate features. Candidate features use only
  parent-visible public inputs.

### 2.2 Classical-CIA ranking formula (frozen primary)
- Feature vector per candidate (all parent-visible, deterministic):
  - **BM25** semantic-overlap score vs the task intent (frozen tokenizer + BM25
    implementation, no tuning);
  - **Path-token** overlap of the candidate path with the intent text;
  - **Graph** static/neighbor score from the frozen AST dependency graph
    (parent-only edges);
  - **CIA = Classical-CIA combination** = the frozen composite that fuses
    BM25/graph/path evidence with a classical association/importance weighting
    (exact coefficients frozen in `scripts/route_b_v2_robustness.py`).
- **Tie-breaking:** deterministic (stable sort by candidate path after score;
  exact tie-break implemented in the frozen script; no random element).
- **Hybrid (secondary):** 0.5 BM25 + 0.5 graph neighbor — predeclared, not
  tuned on outcomes.

### 2.3 Budget curve
- **B ∈ {0, 1, 3, 5, 10}**; B=0 = Sparse alone (no reconsideration).
- Report **normalized sensitivity** B / |omitted_set| as a secondary view; do
  NOT replace raw B.

### 2.4 Primary endpoint
- **False-Negative Recovery Rate / Omission Recovery Rate @ B** (per task:
  recovered Sparse-observed FNs within B / all Sparse-observed FNs for that
  task), as recovery effectiveness vs added inspection budget.
- Secondary: absolute recall gain; FNR reduction; fraction of Oracle@B gap
  closed; candidates inspected per recovered FN; final precision/F1 (safety);
  runtime; index/build cost.

### 2.5 Analytic Random control (frozen)
- Task t: N_t omitted candidates, M_t Sparse FNs among them, budget B.
- E[X_t] = B·M_t/N_t (B clipped to N_t); Omission-recovery expectation =
  E[X_t]/M_t = min(B,N_t)/N_t.
- Ranker observed recovery vs analytic expectation, task-level macro mean,
  task-level bootstrap CI for the difference.
- Random repetitions are NEVER independent tasks.

### 2.6 Statistical / bootstrap plan (frozen)
- Task is the independent unit (no candidate-row pseudo-replication).
- Task-level bootstrap (seeded, fixed seed in frozen script) for the delta
  (ranker − analytic Random) at every B.
- Predeclared grouped/task-level K-fold CV (K=5, seeded) + strata: year/time,
  omitted-set size, candidate-universe size, proxy size.
- No feature-weight tuning per fold; no learned model required.

### 2.7 Verifier inclusion (frozen)
- Verifier protocol: `docs/ROUTE_B_VERIFIER_PILOT_PROTOCOL.md` (30-call pilot,
  ORR 0.86–1.00, dominant loss = first-pass omission). In the confirmatory run,
  the verifier inspects top-B candidates per task; a candidate is "recovered"
  if the verifier approves it AND it is in the hidden proxy.
- Verifier call budget for confirmatory: to be set in the authorized execution
  session (not pre-spent here). Fail-closed ceilings apply.

### 2.8 Failure semantics (frozen)
- A cell/record that is schema-invalid, truncated (finish_reason=length), or
  transport-failed is a FAILED cell (fn added, no partial credit), never a
  silent retry; no result-dependent reruns; capability unavailable != numeric
  zero.

### 2.9 Confound checks (frozen)
- Correlations of ranker delta vs omitted-set size and vs universe size must
  NOT be the sole driver (V2 DEV: −0.119 / −0.117, artifact-free).
- Leakage: no gold feature; no future-state/history; hidden proxy separated.
- Repository-id confound for cross-repo: per-repository primary, macro-average
  secondary.

### 2.10 Stop rule (frozen)
- Confirmatory gate mirrors the DEV progression gate: positive direction in
  majority of predeclared folds; materially above analytic Random over a
  nontrivial portion of the B curve; not driven solely by size artifacts;
  leakage-free; practically meaningful recovery. If the gate fails, the negative
  result is frozen and reported — no method change based on confirmatory
  outcomes in the same session.

## 3. Exact code / config / commit hashes (frozen)

| Component | Hash / ref |
|---|---|
| Authoring agent | openrouter/deepseek/deepseek-v4-flash-0731 |
| Route B V2 robustness script | `scripts/route_b_v2_robustness.py` (committed) |
| Route B V2 protocol | `docs/ROUTE_B_V2_DEVELOPMENT_PROTOCOL.md` |
| Route B V2 results | `research/transparency/route_b_v2_results.json` |
| Verifier pilot protocol | `docs/ROUTE_B_VERIFIER_PILOT_PROTOCOL.md` |
| Verifier pilot results | `research/transparency/route_b_verifier_pilot/` |
| Split (djangoCMS V2) | `research/transparency/v2_split_proposal.json` (seed 20260916) |
| V2 dev bundles | `benchmark_data/real_commit_impact_v2/` (INTERNAL_TEST/RESERVE sealed) |
| Current commit (this packet) | `c3b058a` (to be superseded by the final merge hash in the release step) |

## 4. DEVELOPMENT results recorded (context, NOT confirmatory)

- n=174 DEVELOPMENT tasks; best arm CIA; mean curve delta vs analytic Random
  +0.118; 5/5 folds positive; 4/4 B-points above Random; bootstrap CI at
  B=5: +0.136 [+0.092, +0.184]; B=10: +0.194 [+0.147, +0.246]; corr with
  omitted/universe size −0.119/−0.117; **progression gate PASS**.
- Verifier pilot: 30 calls, $0.0023, Oracle-in-top-B = 1.000; verifier ORR
  0.86–1.00; dominant loss = first-pass omission.

## 5. What is explicitly NOT done / NOT claimed

- djangoCMS INTERNAL_TEST is NOT opened, evaluated, or tuned in this mission.
- Saleor Route-B replication is NOT available (Block C budget-blocked).
- No cross-repository headline claim (per-repository primary only).
- P2 adaptive budget remains CONDITIONAL (not complete; not fitted).

## 6. Ready-to-approve checklist (for the supervisor)

1. Approve confirmatory choice **B (ranking + actual verifier)** or override to A.
2. Approve the frozen method (candidate def, CIA formula, tie-break, B curve,
   endpoint, analytic Random, bootstrap, failure semantics, confound checks,
   stop rule).
3. Authorize the confirmatory verifier budget (djangoCMS INTERNAL_TEST) in a
   separate frozen budget statement before any confirmatory call.
4. On approval, the executing session opens djangoCMS INTERNAL_TEST ONLY under
   that new authorization and freezes the outcome.