# HANDOFF — Interactive MSc Seminar Deck Builder

**Purpose:** give a fresh LLM (or a human designer) everything needed to produce
an interactive MSc seminar deck **without reading the repository**. All numbers
below are frozen, audited facts; the exact claims you may put on a slide are in
the "Claim boundaries" section. Do not invent numbers.

**Date:** 2026-09-17
**Proposal version to present:** `msc_proposal/MSC_PROPOSAL_V1_5.tex` /
`MSC_PROPOSAL_V1_5.pdf` (12 pages) — the current print candidate.
**Model (authoring agent of this file):** openrouter/deepseek/deepseek-v4-flash-0731
**Zero API was used to create this file; none is needed to build slides.**

---

## 1. The one-minute story (say this out loud first)

> Before an LLM can edit a repository it must decide *which files* a requested
> change affects. That decision is expensive: writing out a full file-by-file
> plan costs hundreds of decisions per call, and a second reasoning stage can
> cost orders of magnitude more. This thesis asks whether a **cheap sparse
> first pass** — that only says what to *change* and silently treats everything
> else as *preserve* — can localize most of the affected files, and whether a
> **small, budgeted second look** can then recover the important files the
> first pass omitted. We found the cheap sparse representation cuts serialized
> decisions ~96.6% (4.9 vs 144 records), and — the key result — a frozen
> **BM25+Graph-Neighbor composite ranker** recovers the first pass's missed
> files above a random baseline at every budget point, **confirmed on a held
> internal test** (djangoCMS, 80 tasks, B=5: 0.165 vs 0.028) and **replicated
> in the same direction on a second, larger repository** (Saleor, B=5: 0.237
> vs 0.006, development evidence). The signal is mostly lexical (BM25); we do
> not claim graph novelty. Adaptive budgets are a future program, not a
> completed result.

---

## 2. Slide outline — 20 slides (interactive deck)

Suggested deck structure. Each slide: title / 1-line takeaway / visual /
interaction (poll, click-to-reveal, slider). Keep the deck at 18–24 slides.

1. **Title** — Cost-Aware Repository Change Localization with Sparse Impact
   Planning and Bounded Verification · MSc Research Proposal V1.5 · Ahmed Ehab
   · Supervisor: Mohammad El-Ramly · 2026-09-17. (Visual: title only.)
2. **The problem** — An editing agent must decide which files a change affects,
   and that decision is expensive. (Visual: repo → file list → LLM edit; two
   cost arrows: explicit policy + second stage.)
3. **Why scope matters** — Full explicit file policy serializes ~144 records
   per call at 16K cap; second-stage reasoning can use millions of tokens per
   task. (Visual: bar 144 vs 4.9.)
4. **Key idea: Preserve-by-Omission (Sparse)** — Emit only *non-preserve*
   decisions; everything else is deterministically "preserve". Definition in
   §4. (Visual: before/after output record lists.)
5. **Controlled evidence for Sparse** — 4.9 vs 144 serialized records
   (~96.6% reduction), large completion-token/cost reduction. No
   semantic-superiority claim. (Visual: two-column comparison.)
6. **Real commits, honest proxy** — Real djangoCMS + Saleor commits;
   *parent-only* inputs; the observed diff is a *proxy*, not semantic ground
   truth. (Visual: P → T diff schematic.)
7. **Omissions are the real problem** — Sparse omits files on ~73–80% of
   development tasks; task-level prediction of which tasks will omit is NOT
   reliable (RiskScorer rejected). (Visual: donut/bar of omission prevalence.)
8. **Route B: bounded verification** — Instead of predicting risky *tasks*,
   rank the *omitted candidates* cheaply and verify only the top-B under a
   hard budget. (Visual: pipeline Sparse → omitted set → rank → top-B →
   verifier.)
9. **Terminology slide** — Definitions of Sparse, Route B, B, Random, BM25,
   Composite, Oracle, Verifier (see §4). (Interaction: click each term to
   reveal its definition.)
10. **Toy example — 10-file repository** (see §3). (Interaction: step through
    Sparse output, omitted set, ranking, top-3 budget, recovery.)
11. **Baselines & controls** — Fixed B ∈ {0,1,3,5,10}; analytic Random
    (hypergeometric expectation); BM25; path-token; graph; the frozen
    composite; Oracle (ranking headroom); InspectAll (exhaustive). Ranking ≠
    verification ≠ final localization. (Visual: anchor table.)
12. **Related work — the comparison matrix** — Classical/history CIA,
    Agentless, CodePlan, RepoCoder, LocAgent, GraphLocator, RepoGraph vs this
    proposal across input/output/first pass/second stage/history/graph/budget/
    FN-recovery/real commits/cross-repo. (Visual: the two tables from
    proposal §5; emphasize the "budget-aware + FN-recovery + cross-repo"
    combination.)
13. **Development evidence — djangoCMS** — Composite above analytic Random at
    every B; e.g. B=5 pooled macro recovery 0.163 vs random 0.029
    (CI [+0.09,+0.18]); 5/5 folds positive. (Visual: recovery-vs-B line chart,
    shaded CI.)
14. **Development evidence — Saleor transfer** — 450-cell DEV run (446 valid /
    $2.31); frozen protocol replicates: B=5 0.237 vs 0.006 (Δ+0.231,
    CI [+0.180,+0.287]); *development* evidence only. (Visual: second line
    chart on the same axes.)
15. **CONFIRMATORY result — djangoCMS INTERNAL_TEST** — 80 tasks, 560 calls /
    1.47M tokens / $0.506; composite ORR vs analytic Random: B=1 0.059 vs
    0.006, B=3 0.110 vs 0.017, **B=5 0.165 vs 0.028 (Δ+0.137, CI
    [+0.075,+0.205])**, B=10 0.267 vs 0.055; CIs exclude zero at every B;
    classification **CONFIRMS**. (Visual: confirmatory curve + gate checkmarks.)
16. **End-to-end verifier number** — Verifier-only ORR at B=5 ≈ 0.1007
    (secondary; B≥3 CIs exclude zero; B=1 CI touches zero — documented, not
    the primary claim). (Visual: small inset table or footnote callout.)
17. **Final selected set @ B=5** — P ≈ 0.206 / R ≈ 0.284 / F1 ≈ 0.239 / FNR ≈
    0.716. (Visual: confusion-matrix style P/R/F1/FNR block.)
18. **The signal is mostly lexical** — composite−BM25 deltas are small with CIs
    including zero at most B on both repos; no graph-novelty claim. (Visual:
    ablation delta table with CI whiskers.)
19. **Positioning & boundaries** — What is confirmed (fixed-B Route B on
    djangoCMS INTERNAL_TEST), what is development (Saleor transfer, all P2),
    what is future (adaptive budgets Nov 2026–Mar 2027; NestJS April 2027
    external-validity, conditional). (Visual: confirmed / development / future
    three-column map.)
20. **Q&A + claim boundaries** — Anticipated questions with safe answers
    (§7); the strict claim boundary card (§6).

Optional extra slides (swap in if 24):
21. **Thesis contributions** — representation + dataset/protocol +
    shared-protocol budget-matched comparison + bounded-verification protocol +
    cross-repo evidence; no positive algorithmic result promised.
22. **Timeline 2026-11 → 2027-10** — from proposal §10 (P2 program first five
    months; thesis completion target 2027-07/08; publication buffer after).
23. **Threats & mitigations** — observed proxy ≠ gold; single-family stack so
    far; pre-registration, analytic-Random control, bootstrap CIs, sealed
    tests.
24. **Thank you / contact** — Ahmed Ehab · ahmed.ehab@fci-cu.edu.eg · ORCID
    0000-0002-5076-3829.

---

## 3. Toy example — a 10-file repository

Use this to make the mechanism concrete. **It is illustrative, not data.**

Files: `models.py` · `views.py` · `urls.py` · `admin.py` · `forms.py` ·
`serializers.py` · `signals.py` · `utils.py` · `tests.py` · `migrations.py`
(10 candidate files visible at parent revision).

- **Change request:** "Add a `slug` field to the product model and expose it
  in the admin."
- **Sparse first pass** (preserve-by-omission) emits only the *change*
  decisions: `models.py: modify`, `admin.py: modify`, `views.py: modify`.
  All other 7 files are implicitly "preserve".
- **Observed historical change-set proxy** (evaluation only): the real commit
  changed `models.py`, `admin.py`, `views.py`, **and** `utils.py`.
  ⇒ The sparse first pass **omitted** `utils.py` (a false negative among the 7
  preserved files).
- **Omitted candidate set** (what we may reconsider): the 7 preserved files.
- **Composite ranking** (BM25 + graph-neighbor, parent-visible only) orders the
  7 omitted candidates, e.g.: 1. `utils.py` (imported by `models.py` → graph
  neighbor; BM25 hits "product"/"slug") 2. `signals.py` 3. `serializers.py`
  4. `forms.py` 5. `urls.py` 6. `tests.py` 7. `migrations.py`.
- **Budget B=3:** verify only the top-3 (`utils.py`, `signals.py`,
  `serializers.py`). Verifier accepts `utils.py` (it does need the new field).
  Recovered 1 omitted FN with 3 verification calls. FNR for this task
  improves; that is the "recovery" the thesis measures.
- **Analytic Random control:** with 7 omitted candidates, 1 true FN, B=3,
  E[recovered] = 3 × 1/7 ≈ 0.43 — the composite (1.0 here) beats it.
- **Oracle** would rank `utils.py` first (headroom); **InspectAll** would check
  all 7.

---

## 4. Definitions (exact, slide-safe)

| Term | Definition |
|---|---|
| **Sparse** (preserve-by-omission) | A file-level impact policy that emits only *non-preserve* decisions (modify/add/delete) and reconstructs every unlisted file as "preserve" deterministically. |
| **Route B** | The candidate-level mechanism: rank the *first-pass omitted candidates* with cheap evidence and verify only the top-B, instead of predicting risky tasks. |
| **B** | The per-task verification budget — number of top-ranked omitted candidates admitted to the (LLM) verifier. Primary object is the curve B ∈ {0,1,3,5,10}; B=0 = Sparse alone; B=5 is a reference point, not the single claim. |
| **Random** (analytic) | The control: hypergeometric expectation E[X] = B·M/N (B clipped to N), where N = omitted candidates and M = Sparse-observed FNs in that task. Random repetitions are never independent tasks. |
| **BM25** | A classic lexical ranking of candidates by term overlap with the change request (k1=1.5, b=0.75, frozen stopwords). The strongest cheap lexical signal. |
| **Composite** (BM25+Graph-Neighbor) | The frozen primary ranker = normalized BM25 + binary graph-neighbor indicator. Historical label "Classical-CIA" is kept only as a label; exact formula per the ranker-identity audit. Hybrid (0.5/0.5) is rank-equivalent to the composite (redundant control). |
| **Oracle** | Ranking headroom: the ranker that places the actually-omitted FN files at the top (evaluation-only). Oracle@B ≠ InspectAll. |
| **Verifier** | The second-stage LLM that inspects the top-B ranked candidates and decides whether each is relevant/needs change (1 call per (task,B), B=0 none). |
| **ORR** | Omission/FN Recovery Rate @ B = recovered Sparse-observed FNs within B ÷ all Sparse-observed FNs. Primary endpoint. |
| **Observed change-set proxy** | The real commit's changed production files = evaluation target. Never semantic ground truth. |

---

## 5. Key numbers (frozen — use exactly these)

| Fact | Value | Provenance |
|---|---|---|
| Saleor DEV Sparse run | 450 cells (150×3), **446 valid / 4 failed**, **$2.31**, 7,316,986 tokens, 0 truncations | `reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md` |
| Saleor B=5 transfer (Composite vs Random) | **≈0.237 vs ≈0.006**, Δ+0.231 CI [+0.180,+0.287]; 149 tasks; DEVELOPMENT only | same |
| djangoCMS confirmatory budget | **560 calls / 1.47M tokens / $0.506** (80 tasks; 0 failures; 0 excluded) | `reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md` |
| Confirmatory B=5 Composite ORR vs Random | **≈0.165 vs ≈0.0277**, Δ+0.137 CI [+0.075,+0.205] | same |
| Confirmatory other B | B=1 0.059 vs 0.0055; B=3 0.110 vs 0.0166; B=10 0.267 vs 0.0554; CIs exclude zero at every B | same |
| Verifier B=5 ORR | **≈0.1007** (secondary; B≥3 CIs exclude zero; B=1 CI touches zero — documented) | same |
| Final selected set @ B=5 | **P≈0.206 / R≈0.284 / F1≈0.239 / FNR≈0.716** (TP 71 / FP 274 / FN 179) | same |
| Representation effect | Sparse 4.9 vs Full 144.0 serialized records (~96.6% reduction) | `reports/CONTROLLED_ENCODING_16K_RESULT.md` |
| Cheap-baseline context | BM25@10 pooled F1 ≈ 0.306 on 6 VALIDATION tasks (development, K = operating-point curve, not a final config) | `reports/CHEAP_BASELINES_V1_REPORT.md` |

Present the confirmatory numbers as the strongest result; every Saleor number
as DEVELOPMENT transfer replication; the verifier and final-set numbers as
secondary/context.

---

## 6. Claim boundaries (what a slide may and may NOT claim)

**MAY claim**
- The sparse representation cuts serialized decisions ~96.6% (controlled).
- The composite ranker beats analytic Random on djangoCMS **INTERNAL_TEST
  (confirmatory, CONFIRMS)** and on Saleor **DEV (transfer replication)**.
- The signal is predominantly lexical (BM25); no graph-novelty claim.
- Task-level RiskScorer is not justified on current development evidence.
- P2 (adaptive budgets) is a future development program, not complete.
- NestJS/NextJS is future external-validity work, conditional on a suitability
  gate + TypeScript extractor readiness.
- Ranking ≠ verification ≠ final localization; each stage is reported
  separately.

**MUST NOT claim**
- "First time" / "novel" for any single component (graph, history, selective
  compute alone).
- That Saleor is confirmed (it is development replication only).
- That adaptive budgets work, or that any P2 policy is a contribution.
- That the observed diff equals semantic impact.
- A head-to-head ranking of BM25 vs the LLM planners under a shared fresh
  confirmatory protocol (untested; P1 numbers are directional context only).
- That the verifier "works" from its B=1 CI (touches zero; documented).
- Anything about djangoCMS RESERVE, Saleor INTERNAL_TEST/RESERVE (sealed,
  never opened). The opened djangoCMS INTERNAL_TEST is permanently spent and
  will not be reused for P2 selection.

---

## 7. Likely Q&A with safe answers

1. **"Isn't BM25 enough?"** — It is the strongest cheap signal; the thesis
   combines it with the sparse representation and a *bounded* verifier, and
   evaluates on real commits under matched budgets. We do not claim BM25
   dominates LLM planners under a shared protocol.
2. **"Why is the diff only a proxy?"** — The real commit's changed files are an
   observed consequence, not semantic impact gold; hence claims are scoped to
   historical-file recovery.
3. **"Why not always verify?"** — Always-verify is an arm; the question is the
   correctness–cost Pareto: bounded verification vs always-on and vs random
   matched budget.
4. **"Why does the graph contribute so little?"** — The incremental-evidence
   ablation shows composite−BM25 deltas have CIs including zero at most B;
   the replicated signal is predominantly lexical. This is stated, not hidden.
5. **"What exactly is confirmed?"** — Only the fixed-budget Route-B recovery on
   the authorized djangoCMS INTERNAL_TEST (plus its gate: 5/5 folds, 4/4
   B-points, CIs exclude zero, no size artifact). Everything else is
   development or future.
6. **"What is the actual contribution?"** — The *combination* (sparse explicit
   policy + bounded, budget-matched reconsideration of the rejected residual)
   with reproducible real-commit evidence and honest boundary-keeping; no
   single-component novelty claim.
7. **"Will P2 succeed?"** — Unknown; P2 is a five-month development program
   with pre-registered stopping policies and an honest negative closure; the
   confirmed fixed-B thesis is the fallback.

---

## 8. Build notes for the generating LLM

- Read `msc_proposal/MSC_PROPOSAL_V1_5.tex` for exact wording; reuse the
  proposal's table content for the related-work matrix and timeline slides.
- Suggested interaction model (if the deck is a web/HTML slide deck): sliders
  for B on the recovery curves (re-render the three points B∈{1,3,5,10}),
  click-to-reveal for the definitions slide, and a step-through for the toy
  example.
- Keep every number exactly as §5; put the provenance filename in tiny footer
  text on the corresponding slide.
- Title of the thesis and proposal must stay unchanged.