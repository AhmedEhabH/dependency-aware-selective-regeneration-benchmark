# STAGE-C-SELECTION-01 DECISION (EXPLORATORY COMPONENT STUDY)

- **Label:** EXPLORATORY COMPONENT STUDY
- **Protocol:** `scientific-stagec-selection-01`
- **Status:** COMPLETE - 30/30 real selection runs, all terminal, all valid finals.

## Result

| Arm | n | valid finals | full recall | precision | recall | F1 | FNR | write-set | cost (USD) |
|-----|---:|-------------:|------------:|----------:|-------:|----:|----:|----------:|-----------:|
| iterative_repository_agent | 15 | 15 | 15/15 | 1.000 | 1.000 | 1.000 | 0.000 | 3.0 | 0.0318 |
| impact_plan | 15 | 15 | 15/15 | 1.000 | 1.000 | 1.000 | 0.000 | 3.0 | 0.0209 |

- Exact API cost (both arms, 30 runs): **$0.052696** (estimated $0.032; actual higher because the Agent arm uses several control calls per run).
- Per scenario/arm, all 5/5 runs have full source-recall of the hidden gold regenerate set, precision 1.0, FNR 0.0.
- ImpactPlan descriptive: 45 R / 21 P / 9 V / 0 H across 15 runs; validate-only rate mean 0.12, human-review rate 0.00.
- Agent descriptive: finalization rate 1.000; 89 control calls, 74 tool calls, 48 inspected files across 15 runs.

## Interpretation (EXPLORATORY)

- This is **component evidence about the Stage-C impact-selection boundary only**.
- On the same three Todo smoke scenarios that produced the v1.1 end-to-end
  NO-GO (0/30 functional passes), BOTH arms' **INITIAL selection** perfectly
  identifies the hidden gold source set (15/15 full recall each).
- This strongly suggests the v1.1 end-to-end failures are NOT caused by initial
  impact selection; they are downstream in the code-generation / exact-patch /
  revision / validation path.
- **No claim is made** about functional correctness, code-generation
  reliability, or end-to-end token efficiency. This study never regenerates,
  repairs, migrates, or evaluates.

## Decision

- STUDY_CLASS = EXPLORATORY_COMPONENT
- NEXT_ACTION = document and archive evidence (no executor change in this study);
  a future held-out/multi-repo preregistered study may revisit selection
  confidence and precision beyond these three smoke scenarios.