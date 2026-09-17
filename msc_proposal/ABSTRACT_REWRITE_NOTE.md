# ABSTRACT REWRITE NOTE — V1.4 → V1.5

**Date:** 2026-09-17
**Scope:** Abstract only (`msc_proposal/MSC_PROPOSAL_V1_5.tex`).
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**ZERO API; no scientific input changed; V1.4 immutable.**

---

## 1. Why the Abstract was rewritten

The V1.4 abstract was result-dense and violated the doctor-guide order in two
places: it opened with the cost context and then jumped straight into
preliminary development results (including the Saleor transfer) before stating
the precise gap, and it carried two unsafe phrasings ("for the first time at
candidate level", an unscoped "robust recovery signal") that the supervisor
review line asks to avoid. V1.5 restructures the Abstract to the mandated
order and demotes secondary results to the body.

## 2. Old → New mapping (structure)

| # | V1.4 element | V1.5 replacement | Rationale |
|---|---|---|---|
| 1 | Problem/context (cost of explicit file policy + second-stage reasoning) | Kept, sharpened: "serializes hundreds of decisions per call" (was "spends hundreds of serialized records per call"). | Clearer cost framing; no metric change. |
| 2 | Limitation of current approaches | **NEW paragraph 2:** existing methods "emit one affected-file set and stop"; they neither expose the first-pass residual as a first-class object nor reason about second-look cost. | Explicit "limitation of current approaches" step the guide requires. |
| 3 | Precise gap | **NEW:** "absence of an explicit, budget-controlled treatment of the first-pass residual: which omitted files deserve a second look, and at what cost." | Precise-gap step; replaces the implicit gap. |
| 4 | Central-identity quote | Kept verbatim. | Unchanged thesis identity. |
| 5 | Proposed approach | **NEW compact paragraph:** two-stage design (sparse preserve-by-omission first pass; bounded top-`B` omission recovery) + experimental setting (real commits, two Python/Django repos, parent-only inputs, analytic-Random control, task-level bootstrap, observed proxy). | "Proposed approach" + "experimental setting" steps; no miniature methods section. |
| 6 | Strongest result | **Only** the confirmatory djangoCMS result (B=5 0.165 vs 0.028, delta +0.137, CI excludes zero) + one-line Saleor DEV replication (0.237 vs 0.006, development evidence only). | "Strongest result only" + "confirmatory status"; Saleor moved from abstract headline to development-transfer sentence. |
| 7 | Confirmatory status | Explicit: fixed-budget signal "scientifically confirmed on that test"; adaptive budget (P2) is future, not complete. | Boundary DEVELOPMENT vs CONFIRMATORY vs FUTURE kept explicit. |
| 8 | One scope limitation | **NEW final sentence:** "localization is evaluated against the observed historical diff as a proxy for impact, never against semantic ground truth." | Mandated one scope limitation. |
| 9 | Secondary details REMOVED from Abstract | Representation effect (4.9/144 records), verifier pilot, identity audit / incremental-ablation detail, task-level RiskScorer rejection. | Demoted to Results/Preliminary Evidence (Sections 6/9) where they already exist; keeps the abstract short. |
| 10 | "for the first time at candidate level" | **Removed.** | Unsafe novelty phrasing. |
| 11 | "a robust recovery signal" | Replaced by "recovers ... above the analytic-Random baseline at every budget point ... interval excluding zero". | Avoids unscoped "robust"; claims only what the statistics support. |
| 12 | "missed files" (abstract) | "missed files in the observed historical change-set proxy". | Proxy-bound claim safety. |

## 3. What did NOT change

- The thesis title, central identity, and all body sections (except the
  terminology pass and the added comparison matrix documented in
  `PROPOSAL_V1_5_CHANGELOG.md`).
- No number changed; every number quoted in the new Abstract maps to an audited
  artifact (`reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md`,
  `reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md`).
- DEVELOPMENT vs CONFIRMATORY vs FUTURE boundaries are preserved and restated.

## 4. Word-count / readability

The V1.5 Abstract is approximately the same length as V1.4 (one additional
sentence for the gap/limitation), while carrying strictly less result detail;
the removed detail already lives in Section 9 (Preliminary evidence).