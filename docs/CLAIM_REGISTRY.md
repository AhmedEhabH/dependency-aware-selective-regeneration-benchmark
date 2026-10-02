# CLAIM REGISTRY — Freeze of Supported / Descriptive / Forbidden Claims

**Role:** The binding interpretation of all results. Claims are frozen at
2026-10-02. No executor may change research questions, metrics, thresholds or
claim semantics without a brain-reviewed design amendment. This registry
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
- No claim may present a negative result as a positive one, and no claim may
  pool M16-v1 with any result-bearing experiment.

## Traceability

Every supported/descriptive claim above traces to the numbered rows in
`docs/EXPERIMENT_LEDGER.md` and `docs/RESULTS_SUMMARY.md`; artifact paths are
recorded there.