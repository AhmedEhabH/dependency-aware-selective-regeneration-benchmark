# CLAIM REGISTRY — Freeze of Supported / Descriptive / Forbidden Claims

**Role:** The binding interpretation of all results. Claims are frozen at
2026-10-02. No executor may change research questions, metrics, thresholds or
claim semantics without a review-approved design amendment. This registry
mirrors the claim freeze in the control pack
(`03_RESEARCH_QUESTIONS_AND_CLAIMS.md`).

---

## Supported claims

1. **Sparse representation solves output-feasibility/truncation.** The sparse
   impact-plan representation greatly improves plan validity under output
   constraints (valid 29/30 vs explicit 6/30 with 19 truncations).
2. **RM-CSS improves over SIP on the clean Saleor reserve.** RM-CSS F1 .3569 vs
   SIP .2647, delta +.0921, 95% CI [.0691, .1156] on the untouched
   RESERVE-300 sample.
3. **On MAIN_297, RM-CSS is close to the bounded Agent in file-level F1** and
   uses far fewer calls/tokens (≈0.2746× calls, ≈0.2134× generation tokens).
4. **Selection-only non-inferiority at the preregistered 0.05 margin is
   supported** (NI_SUPPORTED); margin 0.03 is inconclusive at this n.

## Supporting / descriptive claims

1. OPWS Pilot-B (n=10) indicates limited reference-patch sufficiency for both
   RM-CSS (3/10) and Agent (2/10–3/10) scopes on a small sample; descriptive
   only, no superiority claim.
2. E2E pipeline execution is feasible as an engineering pipeline (Smoke v2.2).
3. Generator capability is a separate downstream bottleneck (Pilot-A, M14R,
   M15-R generation all negative/floor-not-met).

## RQ2 — Agentless-style localization comparator (2026-10-12)

**EMPIRICAL — Agentless-style MAIN_297 scores (frozen):** the pre-registered
`AGENTLESS_STYLE_ADAPTATION` file-level localization comparator scored micro
F1 0.2736 (P 0.2786 / R 0.2689; TP 246 / FP 637 / FN 669; FNR 0.7311) on the
frozen MAIN_297 population with the same file-level evaluator as RM-CSS/SIP/
Agent. Experimental API cost $2.002373 (297 calls; 6,555,810 prompt / 35,628
completion tokens).

**EMPIRICAL — paired bootstrap (10,000 resamples, seed 20261012):**
- RM-CSS minus Agentless: ΔF1 +0.0832, 95% CI [+0.0511, +0.1148] (excludes
  zero; RM-CSS higher).
- Agent minus Agentless: ΔF1 +0.0894, 95% CI [+0.0552, +0.1260] (excludes
  zero; Agent higher).
- Agentless minus SIP: ΔF1 +0.0084, 95% CI [−0.0204, +0.0377] (crosses zero).

**INTERPRETIVE:** the Agentless-style adaptation supplies a stronger
literature-inspired localization comparator than simple retrieval alone
(BM25 / DENSE@K / size-matched controls). DENSE@3 point estimate 0.2746 is
close to/slightly above Agentless-style 0.2736; no statistical separation is
claimed between them.

**FORBIDDEN:** "exact Agentless reproduction"; "RM-CSS beats official
Agentless"; "RM-CSS is best overall"; "Agentless-style significantly beats SIP
in F1" (paired CI crosses zero); "the $2 fail-closed budget was not crossed"
(the final task crossed it; cumulative cost $2.002373).

## Unsupported / forbidden claims

1. **RM-CSS is E2E-superior to the Agent.** Forbidden. MAIN_297 is
   selection-only; E2E is not established.
2. **RM-CSS and the Agent are equivalent.** Forbidden. NI at 0.05 is
   non-inferiority, not equivalence.
3. **M15-R proves general repository repair quality.** Forbidden. Pilot-B n=10
   is descriptive; generation S2 gate failed.
4. **M16-v1 provides MAIN OPWS results.** Forbidden. M16-v1 closed as a
   pre-experiment adapter failure; no MAIN OPWS outcome exists.
5. **The current implementation is language-agnostic.** Forbidden. No polyglot
   study has been run.
6. **Generator correctness is solved.** Forbidden. Every generator probe
   (Pilot-A, M14R, M15-R) failed to clear the floor.

## Fixed wording rules (binding)

- MAIN_297 statements must carry "selection-only" and may not imply end-to-end
  correctness.
- M15-R statements must carry "descriptive" and "Pilot-B n=10".
- M16-v1 statements must state "pre-experiment adapter failure, no MAIN outcome".
- Any graph-ablation statement must carry "may improve precision at material
  token cost; no universal graph claim".
- Agentless statements must name the adaptation exactly `AGENTLESS_STYLE_ADAPTATION`
  (never `EXACT_AGENTLESS` / `OFFICIAL_AGENTLESS` / `AGENTLESS_REPRODUCTION`)
  and must carry "file-level localization comparator; not an exact
  published-Agentless reproduction".
- Cost statements about the Agentless adaptation must state that the frozen $2
  fail-closed threshold was crossed by the final task (cumulative experimental
  API cost $2.002373) with execution stopping immediately afterward; never
  write "cost stayed under $2" or "actual cost <= $2".
- Repository-wide non-green suite results on the Agentless branch snapshot must
  be described as integration-validation debt (environment / missing-fixture /
  unrelated cross-domain branch-state failures), never as Agentless experiment
  failures and never as a passing regression suite.
- No claim may present a negative result as a positive one, and no claim may
  pool M16-v1 with any result-bearing experiment.

## Traceability

Every supported/descriptive claim above traces to the numbered rows in
`docs/EXPERIMENT_LEDGER.md` and `docs/RESULTS_SUMMARY.md`; artifact paths are
recorded there.