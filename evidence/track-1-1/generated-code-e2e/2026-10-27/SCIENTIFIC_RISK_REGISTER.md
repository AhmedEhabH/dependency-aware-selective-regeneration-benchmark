# Research and committee-facing risk register (as of 2026-10-27)

This is researcher-directed experimental work with LLMs as tools for code generation and engineering assistance. The researcher/supervisor own scientific decisions. No generated-code task success is claimed.

## Committees: research maturity, not odds of acceptance

**November MSc registration/seminar:** The broad thesis direction "Selective Regeneration for Token-Efficient Software Evolution" is a defensible *research question / work program* if the title, measurable hypotheses, methodology, test plan and negative findings are presented honestly. This is NOT proof of registration approval; institutional approvals and exact seminar date remain outside this experiment. A proposal seminar need not present a completed peer-reviewed result, but should demonstrate a feasible evaluation path, rigorous claims and relevant literature.

**Final defense / contribution claim:** NOT READY. Generated-code functional E2E remains 0/106 evaluated; full dataset fairness, prospective input provenance, temporal leakage prevention, behavioral sufficiency, multiple tasks, strong competitors, uncertainty intervals, cost-vs-correctness tradeoffs and negative-result protocol are still open.

## Risks, current gaps, minimal required evidence

1. **Novelty relative to competitors — OPEN/HIGH.** Ripple (ICSE 2026) uses LLM-guided intent-aware seed-to-scope impact localization. CodeStruct (ACL 2026) uses syntax-validated AST-entity editing for agents and reduces patch-format failures and token use. Their work overlaps localization / structured editing but does not automatically invalidate a token-efficient *selective regeneration* thesis. Need a crisp unique system contribution and matched cost-correctness baseline under the same generator/harness, not paper title differentiation.
2. **Dataset coverage and fairness — OPEN/HIGH.** Explain all sampled commits with time cutoff, full census, filter attrition per reason, frozen random seed and parent-only qualification; evaluate eligible cohorts beyond the 6000-candidate bottleneck before dataset representativeness claims.
3. **Future leakage and proxy intent — OPEN/HIGH.** A5 task text "Make tokenTargetUrl optional in manifest" was reconstructed retrospectively, not proved available at parent cutoff. Model only saw two parent production files; not sufficient for strict historical-grounding claims. Need timestamped issue/PR intent provenance or prospectively sourced tasks.
4. **Behavioral adequacy — OPEN/HIGH.** Gold developer patch overlap, Git apply, AST, and structural edit count do not guarantee intended behavior. Required independently sourced F2P, P2P, adversarial regressions, run logs and reproducible environment.
5. **Failure of hypothesis/eligibility yield — OPEN/HIGH.** Predeclare criteria for null result, inability to qualify tasks, missing tests, high cost, and oracle contamination. Report attrition instead of cherry-picking a successful task.
6. **Protocol drift/attempt multiplicity — OPEN/HIGH.** A2/A3/A4 changed output formats; A5 function-scoped full-line edits then retried transient 429 as A5-R1. No aggregate unbiased pass@1 comparison across these adaptive changes. Preregister a fixed protocol before scaling.

## Notable related work verified in public sources

- Ripple, *From Seed to Scope: Reasoning to Identify Change Impact Sets* (ICSE 2026): https://aashishyadavally.github.io/assets/pdf/pub-icse2026-%282%29.pdf
- CodeStruct, *Code Agents over Structured Action Spaces* (ACL 2026): https://aclanthology.org/2026.acl-long.607/
- PROBE, *Benchmarking code generation in large language models* (published 2026): https://doi.org/10.1007/s10664-026-10904-5 — separates correctness, similarity and quality.
- *Demystifying LLM-Based Software Engineering Agents* (FSE 2025): https://lingming.cs.illinois.edu/publications/fse2025.pdf — reports resolution, dollars, tokens and correct location independently.

## Decision state

- Single-task exploratory D2 functional testing is the operational next milestone; no new API authorization is implied.
- Reserve "generated-code E2E PASS" for qualified prospective frozen outputs executed under true offline OCI/DB controls, and require additional tasks for external validity.
- Preserve meaningful adverse results, including parser errors and transients, in the all-attempt record.
