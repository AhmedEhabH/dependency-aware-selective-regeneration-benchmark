# djangoCMS Route-B Confirmatory-Freeze Packet — V2 (supersedes V1)

**Date:** 2026-09-17
**Tier:** T3 scientific documentation — ready-to-approve freeze packet (V2)
**Status:** **FROZEN PACKET V2 (ready for approval). djangoCMS INTERNAL_TEST is
NOT opened in this mission.** No confirmatory inference is run here.
**Supersedes:** `reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_FREEZE_PACKET.md` (V1
remains immutable as a historical record; this V2 supersedes it on every point
listed below).

**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 0. Why V2 exists (changes vs V1, 2026-09-17)

1. **Ranker identity corrected after the ranker-identity audit**
   (`reports/ROUTE_B_RANKER_IDENTITY_AUDIT.md`, zero API). The frozen arm
   historically labelled `Classical-CIA` is exactly
   **normalized BM25 + binary graph-neighbor indicator**; it is NOT classical
   dependency-propagation CIA and it has no association/importance weighting.
   V1's prose overstated the implementation. The truthful name is
   **`BM25+Graph-Neighbor Composite (historical label: CIA)`**. The ranking
   formula itself is UNCHANGED (no silent method change before confirmatory
   testing); only the name and description are corrected.
2. **CIA/Hybrid redundancy confirmed.** The `Hybrid` arm (`0.5·BM25 +
   0.5·graph_neighbor`) is mathematically rank-equivalent to the composite
   (positive scalar multiple), verified at top-B identity on 174 djangoCMS and
   149 Saleor DEVELOPMENT tasks (0 differing task-budget cells at every
   B∈{1,3,5,10}). `Hybrid` is classified a **redundant alias/control**, NOT an
   independent baseline. The confirmatory primary is the composite only; Hybrid
   is retained as a labelled control with identical expected output.
3. **Saleor transfer is now AVAILABLE and classified REPLICATES on
   DEVELOPMENT** (2026-09-17, zero new calls). V1's statement "Saleor Route-B
   replication is NOT available" is REMOVED. Saleor is reported per-repository
   primary; no djangoCMS+Saleor pooling as the headline.
4. **Incremental-evidence ablation added as context**
   (`reports/ROUTE_B_INCREMENTAL_EVIDENCE_ABLATION.md`, zero API): composite
   minus BM25 paired task-level delta + bootstrap CI, graph minus random,
   top-B overlap, and additional-FN recovery on both repositories. This is
   CHARACTERIZATION, not method tuning; the frozen confirmatory method is
   unchanged.

---

## 1. Purpose and confirmatory scope

The Route B V2 DEVELOPMENT robustness closure (174 djangoCMS + 149 Saleor
development tasks; Saleor transfer REPLICATES) PASSED the progression gate:
the frozen composite ranker recovers Sparse-omitted historically-changed files
above the analytic hypergeometric Random control across the full budget curve,
with task-level bootstrap intervals excluding zero at every B>0. This packet
freezes everything needed to run the **confirmatory** djangoCMS
INTERNAL_TEST.

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

**Frozen confirmatory claim (exact):**
> **end-to-end Sparse → frozen omitted-candidate ranker → bounded verifier**
> on djangoCMS INTERNAL_TEST.

---

## 2. Frozen method (exact, pre-result)

### 2.1 Candidate definition
- Candidate per task = files decoded/treated as Sparse PRESERVE / omitted
  candidates = candidate universe minus the Sparse write set.
- Evaluation-only positive = file in the hidden observed-change proxy AND
  Sparse omitted it (Sparse-observed FN at file level).
- Gold/proxy NEVER enters candidate features. Candidate features use only
  parent-visible public inputs.

### 2.2 Frozen ranker formula (truthful name, exact)
- **Name:** `BM25+Graph-Neighbor Composite (historical label: CIA)`.
- **Formula (exact, unchanged from the frozen script):**
  `score(p) = normalized_BM25(p) + graph_neighbor(p)`
  where:
  - `normalized_BM25(p)` = BM25 score of candidate `p` vs the task intent,
    normalized by the max BM25 over the candidate universe (frozen tokenizer +
    BM25 implementation, no tuning);
  - `graph_neighbor(p)` = **binary** indicator (1.0 if `p` is a neighbor of the
    seeds/write-set in the parent-only AST dependency graph, else 0.0).
- **What it is NOT:** it does NOT implement classical dependency propagation
  (seed ∪ dependents closure), association/importance weighting, or a
  path-token-fused score. The separate classical CIA baseline
  (`scripts/classical_cia_baseline_v1.py`, CIA-1H/CIA-2H) exists but is a
  DIFFERENT baseline and is not the frozen Route-B primary.
- **Tie-breaking:** deterministic (stable sort by candidate path after score;
  exact tie-break implemented in the frozen script; no random element).
- **Hybrid (secondary control):** `0.5·BM25 + 0.5·graph_neighbor` —
  predeclared, NOT tuned on outcomes. **Classified REDUNDANT ALIAS/CONTROL**
  (rank-equivalent to the composite; see §0.2). Reported only to document the
  redundancy; the primary scientific comparison uses the composite.

### 2.3 Budget curve
- **B ∈ {0, 1, 3, 5, 10}**; B=0 = Sparse alone (no reconsideration).
- Report **normalized sensitivity** B / |omitted_set| as a secondary view; do
  NOT replace raw B.

### 2.4 Primary endpoint and secondary metrics
- **Primary endpoint:** **False-Negative Recovery Rate / Omission Recovery
  Rate @ B** (per task: recovered Sparse-observed FNs within B / all
  Sparse-observed FNs for that task), presented as recovery effectiveness vs
  added inspection budget.
- **Secondary:** absolute recall gain; FNR reduction; fraction of Oracle@B gap
  closed; candidates inspected per recovered FN; final precision/F1 (safety
  metrics: P, R, F1, FNR of the final selected set); runtime; index/build cost.

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

### 2.7 First-pass repetition aggregation rule (exact)
- The Sparse first pass is run with **3 nested repetitions per task** (frozen
  repetition policy).
- The **one write-set used by Route B per task = the predicted_write_set of the
  FIRST SUCCEEDED repetition in record-file order** (frozen dedupe semantics,
  identical to the Route-B V2 / Saleor transfer implementation:
  `by_case` keeps the first record whose `terminal_status == "succeeded"`).
  It is NOT a majority vote and NOT a union.
- A repetition that is transport-failed, schema-invalid, truncated, or
  otherwise non-succeeded is SKIPPED (not retried; see §2.9).

### 2.8 Exact treatment of failed Sparse reps / tasks
- A failed repetition is recorded as FAILED (no partial credit; the cell's
  metrics contribute fn = proxy_size, recall 0), NEVER silently retried.
- If a task has **no succeeded repetition**, the task is **EXCLUDED** from the
  Route-B analysis (exactly as Saleor `saleor-rc-012472eb8482` was excluded →
  149 tasks). The exclusion is recorded; it is NOT a zero-write-set substitute.

### 2.9 Failure semantics (frozen)
- A cell/record that is schema-invalid, truncated (finish_reason=length), or
  transport-failed is a FAILED cell (fn added, no partial credit), never a
  silent retry; no result-dependent reruns; capability unavailable != numeric
  zero.

### 2.10 Verifier inclusion (frozen; exact semantics)
- **Verifier protocol:** `docs/ROUTE_B_VERIFIER_PILOT_PROTOCOL.md` (30-call
  pilot, ORR 0.86–1.00, dominant loss = first-pass omission).
- **Verifier input (per task, per B):** the intent text; the Sparse write set;
  the top-B composite-ranked omitted candidates (path + one-line module/class
  hint); the candidate universe size. NO hidden proxy, NO gold, NO
  target/future info.
- **Verifier output schema:** JSON array of booleans {reconsider: true/false}
  per candidate presented (B entries), plus an optional one-line rationale per
  entry. Strict JSON-array decode; a non-parseable call is recorded as a
  failure (not retried).
- **Number of verifier calls per task per B: exactly 1 call per (task, B)
  pair**, i.e. for B ∈ {1,3,5,10} → **4 verifier calls per task**;
  **B=0 → NO verifier call** (Sparse alone).
- **Independence across B:** verifier calls at different B are **independent**
  (each call inspects its own top-B candidate set; calls are NOT reused across
  B). A candidate is "recovered" if the verifier approves it AND it is in the
  hidden proxy.
- **Verifier call budget for confirmatory:** frozen separately in
  `reports/DJANGOCMS_CONFIRMATORY_API_BUDGET_FREEZE.md` before any
  confirmatory call. Fail-closed ceilings apply.

### 2.11 Confound checks (frozen)
- Correlations of ranker delta vs omitted-set size and vs universe size must
  NOT be the sole driver (djangoCMS DEV: −0.119 / −0.117; Saleor DEV:
  −0.048 / −0.048, artifact-free).
- Leakage: no gold feature; no future-state/history; hidden proxy separated.
- Repository-id confound for cross-repo: per-repository primary, macro-average
  secondary.

### 2.12 Stop rule (frozen)
- Confirmatory gate mirrors the DEV progression gate: positive direction in
  majority of predeclared folds; materially above analytic Random over a
  nontrivial portion of the B curve; not driven solely by size artifacts;
  leakage-free; practically meaningful recovery. If the gate fails, the negative
  result is frozen and reported — no method change based on confirmatory
  outcomes in the same session.

---

## 3. Exact code / config / commit hashes (frozen)

| Component | Hash / ref |
|---|---|
| Authoring agent | openrouter/deepseek/deepseek-v4-flash-0731 |
| Route B V2 robustness script | `scripts/route_b_v2_robustness.py` (committed) |
| Route B V2 protocol | `docs/ROUTE_B_V2_DEVELOPMENT_PROTOCOL.md` |
| Route B V2 results | `research/transparency/route_b_v2_results.json` |
| Ranker-identity audit | `reports/ROUTE_B_RANKER_IDENTITY_AUDIT.md` + `research/transparency/route_b_ranker_identity_audit.json` |
| Incremental-evidence ablation | `reports/ROUTE_B_INCREMENTAL_EVIDENCE_ABLATION.md` + `research/transparency/route_b_incremental_ablation.json` |
| Saleor transfer results | `reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md` + `research/transparency/saleor_route_b_transfer_results.json` |
| Verifier pilot protocol | `docs/ROUTE_B_VERIFIER_PILOT_PROTOCOL.md` |
| Verifier pilot results | `research/transparency/route_b_verifier_pilot/` |
| Split (djangoCMS V2) | `research/transparency/v2_split_proposal.json` (seed 20260916) |
| V2 dev bundles | `benchmark_data/real_commit_impact_v2/` (INTERNAL_TEST/RESERVE sealed) |
| Confirmatory API budget freeze | `reports/DJANGOCMS_CONFIRMATORY_API_BUDGET_FREEZE.md` |
| Current commit (this packet) | (see final merge hash in the release step) |

---

## 4. DEVELOPMENT results recorded (context, NOT confirmatory)

- djangoCMS n=174 DEVELOPMENT tasks; best arm = composite (BM25+Graph-Neighbor,
  historical label CIA); mean curve delta vs analytic Random +0.118; 5/5 folds
  positive; 4/4 B-points above Random; bootstrap CI at B=5: +0.136
  [+0.092, +0.184]; B=10: +0.194 [+0.147, +0.246]; corr with omitted/universe
  size −0.119/−0.117; **progression gate PASS**.
- Saleor n=149 DEVELOPMENT tasks; transfer REPLICATES; B=5 composite 0.237 vs
  Random 0.006 (delta +0.231, CI [+0.180,+0.287]); 5/5 folds positive; 4/4
  B-points; no size artifact (−0.048).
- Verifier pilot: 30 calls, $0.0023, Oracle-in-top-B = 1.000; verifier ORR
  0.86–1.00; dominant loss = first-pass omission.
- Incremental-evidence ablation (context): composite−BM25 paired deltas are
  small with bootstrap CIs including zero at most B on both repositories
  (djangoCMS B=5 +0.003 [−0.015,+0.019]; Saleor B=5 +0.003 [−0.017,+0.024]);
  the transfer signal is **predominantly lexical (BM25)**, with the graph
  neighbor contributing a small, largely non-significant increment. This is a
  CHARACTERIZATION, NOT a reason to change the frozen confirmatory method.

---

## 5. What is explicitly NOT done / NOT claimed

- djangoCMS INTERNAL_TEST is NOT opened, evaluated, or tuned in this mission.
- NO confirmatory model call is made in this mission (zero API).
- No cross-repository headline claim (per-repository primary only).
- The composite's superiority over Random is NOT claimed to be graph-driven;
  the ablation shows the incremental graph contribution over BM25 is small and
  mostly not significant (predominantly lexical transfer signal).
- P2 adaptive budget remains CONDITIONAL (not complete; not fitted).
- `Classical-CIA` naming is corrected; the formula is unchanged.

---

## 6. Ready-to-approve checklist (for the supervisor)

1. Approve confirmatory choice **B (ranking + actual verifier)** or override to A.
2. Approve the frozen method (candidate def, truthful composite formula, tie-break,
   B curve, endpoint + secondary P/R/F1/FNR, analytic Random, bootstrap, first-pass
   repetition rule, failed-rep/task treatment, verifier semantics, failure semantics,
   confound checks, stop rule).
3. Authorize the confirmatory verifier budget (djangoCMS INTERNAL_TEST) per the
   frozen statement in `reports/DJANGOCMS_CONFIRMATORY_API_BUDGET_FREEZE.md`
   before any confirmatory call.
4. On approval, the executing session opens djangoCMS INTERNAL_TEST ONLY under
   that new authorization and freezes the outcome.