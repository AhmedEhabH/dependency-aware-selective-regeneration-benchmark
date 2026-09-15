# V20 Change Log

**Branch:** `paper/v20-final` (created from corrected `main` @ `884ba79`)
**Date:** 2026-09-15

## Prior manuscript base

No prior V19 LaTeX manuscript exists in the repository; V20 is the first
full LaTeX manuscript written from the frozen evidence. It replaces the
provisional working titles in `docs/PAPER_WRITING_HANDOFF.md` with a final
title grounded in the actual evidence.

## Scientific / reporting changes vs the pre-correction P5 evidence state

1. **Native LocAgent Acc@K corrected.** The historical 4/10, 8/10, 9/10 claims
   were cross-task sums of matching FILE ITEMS. V20 reports only the official
   LocAgent metric (task hit iff correct-in-top-K == min(proxy, K)):
   Acc@1 4/10, Acc@3 4/10, Acc@5 2/10, plus simple Hit@K 4/10 at every K.
2. **Validity denominators separated.** The ambiguous single `Valid` column
   (30/30 vs 5/10) is replaced by explicit Tasks / Runs / Non-empty / Empty
   columns and a consistent per-execution/task efficiency table.
3. **P5 failure taxonomy corrected.** The five empty LocAgent outcomes are
   2 genuine 900 s timeouts, 1 context-length BadRequest, 2
   completed-but-empty. V20 states a 50% empty/non-usable rate, NOT a 50%
   timeout rate, with raw-log evidence.
4. **Provider wording downgraded.** "OpenRouter → pinned DeepInfra" is replaced
   by "OpenRouter-routed Qwen3-Coder"; the backend-route provenance limitation
   is disclosed and cost is described as a normalized estimate under a frozen
   pricing snapshot.
5. **Efficiency ratios use one denominator.** Mean per execution/task:
   LocAgent ≈ 246× mean tokens / 100× mean cost vs Full; ≈ 594× / 478× vs
   Sparse (replacing the mixed 33×/160× wording).
6. **P5 framed as framework baseline, not fine-tuned reproduction.** Pinned
   upstream commit `4935b557326c154bad8e8dcf3747cc8d32d1f387` is stated; no
   numeric comparison with published LocAgent Acc@5.

## Scientific content carried forward (unchanged)

- M1 controlled 16K encoding ablation (60 cells; completion 8,383→809;
  records 144.0→5.9; cost $0.275→$0.048).
- P1 real-commit held-out replication (60 cells; P/R/F1/FNR unchanged from
  frozen P1 metrics; serialized-record correction 144.0 / 4.07).
- M4A corpus construction and split freeze (40 cases; 24/6/10).
- Scenario-006 counterexample and heterogeneous-fidelity framing.

## Paper structure (per supervisor guidance)

Abstract → Introduction → Related Work → Method (Preserve-by-Omission) →
Experimental Design → Results (M1 / P1 / P5) → Discussion → Threats to Validity
→ Conclusion. Related Work precedes detailed Method; prose follows each major
heading; present tense for current work, past tense for prior work.

## Compiled deliverables

- `paper_v20_blind.tex/.pdf` — anonymous review variant (shared body).
- `paper_v20_supervisor.tex/.pdf` — supervisor variant with author identity
  (placeholder affiliation; science identical to blind).
- `references.bib` + inline `thebibliography` (8 verified references).
- `V20_CLAIMS_EVIDENCE_MATRIX.md` — 43/43 PASS.
- `V20_REVIEWER_RISK_AUDIT.md` — risk mitigation record.

## Page count

- Blind: 5 pages; Supervisor: 5 pages (target 6 preferred, 8 hard maximum).