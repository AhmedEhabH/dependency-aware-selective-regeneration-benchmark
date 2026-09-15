# V20 Reviewer-Risk Audit

**Branch:** `paper/v20-final`
**Date:** 2026-09-15
**Scope:** adversarial review of the V20 manuscript against the frozen
evidence, supervisor guidance, and reporting corrections. Zero-API.

## 1. Risks identified and mitigation

### R1 — LocAgent comparison overreach
- **Risk:** a reviewer reads P5 as a LocAgent reproduction and compares its
  published Acc@5 (0.90) with our F1.
- **Mitigation in V20:** P5 is explicitly labelled a *framework baseline*,
  not a reproduction of the published fine-tuned configuration; the pinned
  upstream commit hash is stated; native Acc@K (official 4/10, 4/10, 2/10)
  is reported in a separate sentence with "not comparable to our F1"; the
  published 92.7% figure appears only in Related Work with its own-benchmark
  caveat.

### R2 — Denominator / validity confusion
- **Risk:** "30/30 vs 5/10" appears as one validity column.
- **Mitigation:** the V20 P5 table separates Tasks / Runs / Non-empty / Empty;
  the efficiency table states one denominator (mean per execution/task) in the
  caption; §Results never mixes the two.

### R3 — Failure-taxonomy mislabel
- **Risk:** a reviewer notices the logs and challenges "50% timeout".
- **Mitigation:** V20 states 2 timeouts / 1 context-length BadRequest /
  2 completed-but-empty and gives the raw-log evidence table; "50%
  empty/non-usable" is the only aggregate phrase used.

### R4 — Provider provenance
- **Risk:** a reviewer challenges "pinned DeepInfra" for every P5 call.
- **Mitigation:** V20 uses "OpenRouter-routed Qwen3-Coder"; the Threats section
  discloses that the backend was not proven per call and cost is a normalized
  estimate. No DeepInfra claim appears in P5.

### R5 — Item-hit counts as Acc@K
- **Risk:** the historical 4/10/8/10/9/10 reappears.
- **Mitigation:** corrected official Acc@K only (4/10, 4/10, 2/10); the
  strengthened audit fails closed on item-hit-as-task-accuracy.

### R6 — Survivor bias at 4096 cap
- **Risk:** a reviewer sees M1A and thinks the semantic comparison used the
  4096 cap.
- **Mitigation:** M1A is described as a feasibility boundary only; all semantic
  comparisons use the non-binding 16K cap; the threat is in §Threats (7).

### R7 — Observed proxy misread as gold
- **Risk:** a reviewer treats the historical diff as perfect ground truth.
- **Mitigation:** the proxy caveat appears in the Abstract method sentence and
  the Experimental Design opening; Threats (1) repeats it.

### R8 — n=30 independence claim
- **Risk:** repetitions treated as independent examples.
- **Mitigation:** the design section states 6 independent units / 5 nested
  repetitions and 10 independent tasks / 3 nested reps; bootstrap is over the
  10 tasks only.

### R9 — High FNR framed as success
- **Risk:** omission risk presented as a strength.
- **Mitigation:** Threats (8) and Discussion explicitly call high FNR a
  weakness and the motivation for future selective verification.

## 2. Positive reviewer expectations (met)

- Reproducibility: frozen raw evidence + hash-pinned raw responses + six gates
  + 28-check audit, all referenced.
- Honest uncertainty: CIs crossing zero stated as "no clear detected
  difference, not equivalence".
- Consolidated caveats: repeated limitations are gathered in Threats.

## 3. Remaining residual risks (accepted, evidence-bound)

- Single repository (django CMS) for held-out data — disclosed.
- P5 backend-route unproven per call — disclosed, wording downgraded.
- 10-task sample size — stated as the inferential unit; no over-claim.

## 4. Verdict

The manuscript is claim-safe against the frozen evidence. Every numeric value
in the paper is covered by the claims-vs-evidence matrix (43/43 PASS). No
scientific blocker found; no additional model call is required.