# WP-1b One-Page Claim Sheet (2026-09-22)

Immediately usable in paper writing, MSc seminar, supervisor discussion, and
README review. Numbers are quoted from the frozen machine-readable artifacts
(`reports/wp1b_main297_result.json`,
`reports/wp1b_main297_exploratory.json`). No new statistics were computed.

## A. Primary result

- **MAIN_297** (n = 297 tasks, Saleor/Python, protocol-v3 budget-bounded
  iterative repository Agent vs SIP vs RM-CSS): primary verdict =
  `RMCSS_NONINFERIOR_AT_LOWER_COST` (decision rules v2, verdict id 3 =
  `NI_SUPPORTED`).
- Statistic `D = F1_pooled(RM-CSS) − F1_pooled(Agent)`.
- **P (fail-closed, primary):** n = 297, D = **−0.006243848339918201**,
  two-sided 95% CI **[−0.04488048757621672, +0.030762547682913435]**,
  one-sided 95% lower bound **Q5 = −0.0383314093433751**; frozen NI margin
  **Δ = 0.05**; Q5 > −0.05 → NI supported.
- **S (instrument-failure excluded, sensitivity):** n = 295 (2 dropped:
  `saleor-rc-094b1ec0f610`, `saleor-rc-37a3a7bbec31`, both parser failure),
  D = **−0.011504765649930193**, CI **[−0.050202368045461694,
  +0.025468095259528607]**, Q5 = **−0.04336616199062976**.
- **Pooled micro-F1:** Agent **0.363069245165315**, RM-CSS
  **0.3568253968253968**, SIP **0.26519337016574585**.
- **Cost (View A, marginal, ratio RM-CSS/Agent):** model calls **0.275**
  (CI [0.271, 0.279]), total tokens **0.214** (CI [0.210, 0.218]), USD
  **0.221** (CI [0.216, 0.225]) — all upper bounds < 1 → CHEAPER = true.
- **Δ=0.03 sensitivity:** `INCONCLUSIVE_AT_THIS_N`; **Δ=0.10:** `NI_SUPPORTED`.
- **Exploratory macro-F1:** Agent ≈ **0.397082534296782**, RM-CSS ≈
  **0.34269371833245865** (not the primary analysis).
- **EMPTY:** 2/297 (0.67%), both parser failures.

## B. Allowed sentences

- "On the preregistered MAIN_297 pooled file-level F1 analysis, RM-CSS was
  non-inferior to the budget-bounded iterative repository Agent at the
  prespecified Δ=0.05 margin."
- "The Agent had a slightly higher pooled F1 point estimate; the study does not
  establish RM-CSS accuracy superiority."
- "RM-CSS required substantially fewer model calls and tokens under the matched
  selection-stage accounting."
- "The Δ=0.03 sensitivity analysis was inconclusive."
- "Exploratory macro-F1 favored the Agent."
- "No end-to-end code-generation correctness claim follows from WP-1b."
- "MAIN_297 is a selection-stage file-localization result against an observed
  change-set proxy, not semantic gold and not end-to-end patch correctness."

## C. Forbidden sentences

Explicitly forbidden (do not write or say):

- "RM-CSS beats the Agent."
- "RM-CSS is equivalent to the Agent."
- "RM-CSS is universally better/cheaper than agents."
- "RM-CSS beats LocAgent."
- "The Agent is unnecessary."
- "MAIN_297 proves Selective Regeneration works end-to-end."
- "4.5× cheaper" without specifying normalized/list-price accounting.
- "Variance proves the Agent is unstable" without the limited 15-task scope.
- "X3 proves there is no distillation headroom."
- "X6 proves escalation can never work."
- "dominance" (the word is retired for WP-1b).
- Any equivalence claim derived from a CI that crosses zero.

## D. Required caveats

- **Pooled primary vs macro exploratory:** the primary verdict is pooled
  micro-F1; exploratory macro-F1 favored the Agent (0.3971 vs 0.3427) and is
  not hidden.
- **Δ=0.05 vs Δ=0.03:** NI holds at 0.05; 0.03 is `INCONCLUSIVE_AT_THIS_N`.
- **Budget-bounded Agent protocol v3:** 8 calls (call 8 forced final),
  1024-token completion cap, 2000-char observation window, substring search,
  no paging. The claim is against this bounded baseline, not "the best possible
  agent" and not LocAgent/Ripple reproductions.
- **Saleor/Python scope:** single repository (Saleor), single model
  (Qwen3-Coder-480B via DeepInfra), temperature 0.
- **15-task variance subset only:** the 15×3 substudy documents execution
  variability; it is not equivalent to three full MAIN_50 replications and does
  not show a trend.
- **Billed cost affected by provider caching:** list/normalized ledger vs actual
  billed OpenRouter usage differ; never present the billed 4.x ratio as the
  preregistered normalized cost verdict.
- **E2E pending:** WP-2, F2P/P2P oracle, Smoke, Pilot, Research Run have not
  started; no E2E correctness claim follows.
- **Recall/candidate coverage limitation:** RM-CSS cannot select outside its
  candidate pool; the Agent also recovered relatively few outside-pool gold
  files.
- **786 sealed outcomes:** never accessed.

## E. 30-second explanation

WP-1b compared RM-CSS — the frozen, no-generative-call file localizer built
from SIP plus calibrated dense retrieval — against a real, budget-bounded
iterative repository Agent (protocol v3) on 297 Saleor change requests under a
single preregistered protocol. On pooled file-level F1 the Agent had a slightly
higher point estimate (0.363 vs 0.357), but RM-CSS was non-inferior within the
prespecified Δ=0.05 margin (one-sided lower bound −0.038 above −0.05) while
using only about 0.27× the agent's model calls and 0.21× its tokens per task.
This is a selection-stage result only: it says nothing yet about end-to-end
patch correctness, which remains unmeasured (WP-2 / E2E pending), and it holds
for one Python repository, one model, and a specifically bounded agent baseline.