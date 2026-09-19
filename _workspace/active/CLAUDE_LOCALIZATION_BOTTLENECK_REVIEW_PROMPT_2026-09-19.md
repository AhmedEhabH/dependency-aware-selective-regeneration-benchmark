# Claude Review Prompt — Localization Bottleneck Review (2026-09-19)

You are reviewing a software-issue-localization research program for an MSc
thesis. Your job is an independent technical review of the CURRENT bottleneck
analysis and the NEW evidence, NOT to re-run or re-derive anything. Read the
listed files and answer the review questions with specific evidence
references. Be skeptical, cite file paths, and do not soften negatives.

## Context (read first)

- `00_CURRENT_RESEARCH_STATE.md` (scientific truth; read the top CURRENT
  TRUTH block and the frozen negatives)
- `DECISIONS.md` P63–P67 (frozen decisions)
- `docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md` (current phase = repository
  change localization / impact selection; primary dims = Impact Correctness +
  Efficiency)
- `reports/GAP_REDUCTION_ROADMAP.md` (the ladder)
- `docs/RESEARCH_JOURNEY.md` (chronology)

## New evidence to review

- `reports/STAGE4B_STATISTICAL_CLOSURE_2026-09-19.md` +
  `reports/stage4b_bootstrap_ci.json` (POST-HOC descriptive closure; verdict
  PRECISION_SAFE_ACCEPTANCE_FAIL unchanged)
- `docs/SWERANK_EMBED_BASELINE_PROTOCOL_FROZEN.md` (frozen protocol)
- `reports/SWERANK_TRAINING_PROVENANCE_AUDIT.md` (verdict C)
- `reports/SWERANK_EMBED_DEVELOPMENT_REPORT.md` +
  `research/strong-localization-signal/swerank/{metrics,gate,efficiency}.json`
- `reports/swerank_independent_audit.json` (independent audit 11/11)
- `reports/STRONG_LOCALIZATION_COMPETITOR_REVIEW_2026-09-19.md`
- `reports/REPOSITORY_MEMORY_FEASIBILITY_2026-09-19.md`
- `reports/CROSS_LANGUAGE_READINESS_2026-09-19.md`
- `reports/POLYGLOT_REPOSITORY_FEASIBILITY_2026-09-19.md`

## Review questions

1. **Bottleneck validity.** Is the "ranking bottleneck" framing (P63/P64)
   still the most defensible reading of the evidence AFTER the SweRank result?
   Could the SweRank result change the interpretation of Stage-4/4b failures?

2. **Stage-4b closure hygiene.** Is the descriptive closure honestly
   separated from the frozen preregistered verdict? Is the djangoCMS
   ORR-down/F1-up explanation (macro-vs-pooled weighting + M=1 verifier
   over-rejection) supported by the raw task-level table?

3. **SweRank gate integrity.** Are the frozen gate conditions (A–E) and the
   pre-specified margins reasonable and non-tuned? Is the K=5/B=5 primary
   operating point defensible? Any sign of post-hoc gate selection?

4. **SweRank result credibility.** Given the training-provenance verdict C
   (contamination not ruled out), is calling the result a PASS on the frozen
   gate scientifically honest, and is the "EXTERNAL PRETRAINED DIAGNOSTIC
   BASELINE" label used consistently everywhere?

5. **Efficiency claim.** Is "0 API calls / $0" accurate? Is the 6.6-hour
   one-time CPU encode honestly represented as amortized index cost?

6. **Next-step selection.** Is choosing option A (embed as replacement
   candidate-ranking signal) over B (SweRankLLM reranker) the right call given
   the evidence and the ZERO-API constraint?

7. **Missed threats.** What threats, caveats, or validity risks in the new
   evidence have I NOT acknowledged?

Deliver a short report (max ~800 words) with numbered answers and file/line
references where possible. Do not fabricate numbers; if a fact is not in the
listed files, say so.