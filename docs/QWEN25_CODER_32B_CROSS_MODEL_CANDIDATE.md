# Qwen2.5-Coder-32B-Instruct — Cross-Model Robustness Candidate Note

> **STATUS UPDATE (2026-09-11): EXECUTION ABANDONED — REPLACED BY QWEN3-32B.**
> The planned Qwen2.5-Coder-32B cross-model robustness replication was **NOT
> run** and is **ABANDONED** due to provider-contract unavailability: the only
> OpenRouter endpoint for `qwen/qwen-2.5-coder-32b-instruct` was **Cloudflare**
> (no DeepInfra, `response_format` not supported — a forbidden route); the
> direct DeepInfra model is **deprecated and replaced by `Qwen/Qwen3-32B`**;
> the Hugging Face / Nscale route was unavailable (expired OAuth token). This
> investigation is preserved as historical provider-selection evidence
> (`reports/qwen25-coder32b-crossmodel-01/` on branch
> `research/qwen25-coder32b-crossmodel-01`; **zero scientific cells executed**).
> The authorized replacement study is the **Qwen3-32B cross-model robustness
> replication** (`scientific-stagec-djangocms-qwen3-32b-crossmodel-01`,
> `qwen/qwen3-32b` @ OpenRouter / DeepInfra), which is COMPLETE + AUDITED.
> Do NOT reuse the Qwen2.5 study ID or names for the new study.

> **STATUS: CANDIDATE DESIGN NOTE ONLY — NOT AUTHORIZED TO RUN IN THIS TASK.**
> This document preregisters a *possible future* cross-model robustness
> replication. It is **not** an experiment authorization and **no scientific
> model call was made** to produce it. It changes no frozen evidence, metric,
> prompt, schema, or tag.

## 1. Model

- **Model:** `Qwen2.5-Coder-32B-Instruct`

## 2. Motivation

- **Motivation:** future **cross-model robustness** replication of the frozen
  djangoCMS selection-stage studies under a second, independent, openly
  documented coding model.
- **NOT motivation:** "it is definitively better than Qwen3-Coder". No such
  claim is made anywhere in this repository, and no between-model superiority
  claim may be derived from this note or from any future run.

## 3. Verified literature benchmark figures (read-only)

Target model `Qwen2.5-Coder-32B-Instruct` vs Claude 3.5 Sonnet on HumanEval and
EvalPlus Average. Source classification per metric:

| Metric | Qwen value | Claude 3.5 Sonnet value | Source | PRIMARY/SECONDARY | Vendor-reported |
|---|---|---|---|---|---|
| HumanEval | 92.7 | 92.1 | Qwen2.5-Coder Technical Report, arXiv:2409.12186, Table 16 (Qwen2.5-Coder-32B-Instruct row: 92.7; `Claude-3.5-Sonnet-20241022`: 92.1) | **PRIMARY-SOURCE VERIFIED** | YES |
| EvalPlus Average | 86.3 | 85.9 | arXiv:2503.22732 ("Reasoning Beyond Limits") Table III + prose: "outperforming Claude Sonnet 3.5 on HumanEval (92.7 vs. 92.1) and EvalPlus (86.3 vs. 85.9)"; values also derivable from the four EvalPlus sub-scores in the Qwen technical report Table 16 (HE/HE+/MBPP/MBPP+ = 92.7/87.2/90.2/75.1 → mean 86.3; Claude 92.1/86.0/91.0/74.6 → mean 85.9) | **SECONDARY-SOURCE VERIFIED** (table + prose); primary-source sub-scores internally consistent with the derived averages | YES |

Notes:

- **HumanEval 92.7 / 92.1** appear **verbatim** in the primary source
  (Qwen2.5-Coder Technical Report, Table 16).
- **EvalPlus Average 86.3 / 85.9** are **not printed verbatim** as an "average"
  column in the Qwen technical report (which reports only HE / HE+ / MBPP /
  MBPP+). They appear verbatim in the secondary survey
  (arXiv:2503.22732) and are exactly reproducible as the mean of the four
  EvalPlus sub-scores in the primary report.
- These are **VENDOR / DEVELOPER-REPORTED BENCHMARK RESULTS** (Qwen team's own
  evaluation; the survey's citation [57] is the QwenLM blog post
  "Qwen2.5 coder family", 2024). They are **not** independent evaluation and
  must not be labeled as such.
- HumanEval / EvalPlus measure **function-level code generation pass@1**; they
  do **not** measure repository-level impact selection. **No repository-level
  impact-selection ability is inferred from these figures.**
- Do **not** state that Qwen2.5-Coder-32B is universally better than Claude 3.5
  Sonnet (differences are task-specific, small, and developer-reported).

## 4. Proposed FUTURE design (design-only, not run)

A future cross-model robustness replication, **if separately authorized**, would
use the **same frozen scientific inputs** as the current djangoCMS studies with
only the model/backend swapped:

- Same **6 frozen djangoCMS cases** (djangocms-external-validity-002/004/005/
  006/007/008).
- Arms: **ImpactPlan-v1 and ImpactPlan-v2 only** (no Agent arm).
- **5 repetitions** per case per arm → 6 × 2 × 5 = **60 cells**.
- **Completion cap 4096** (unchanged frozen budget).
- **Temperature 0**, **graph OFF** (dependency graph NOT injected),
  **fallback OFF**.
- **No result-based reruns**; no cell salvaging.

## 5. Post-hoc status

Because the same six cases have already informed the current paper's primary
and Sparse-v2 evidence, such a run would be a **POST-HOC CROSS-MODEL
ROBUSTNESS REPLICATION**, not an independent confirmatory study, and would be
presented as such (survivor-bias caveats for primary v1 carry over).

## 6. Cross-model agreement metric (prerecorded design)

If the future run is authorized, the **preferred descriptive agreement metric**
is per-scenario **cross-model set Jaccard**:

- Do **NOT** pair repetition r1 of model A with repetition r1 of model B.
- For each scenario: all 5 Qwen3 runs × all 5 Qwen2.5 runs = **25 cross-model
  set comparisons**.
- For each pair compute Jaccard `J(A, B) = |A ∩ B| / |A ∪ B|` on the selected
  file sets.
- Report per scenario: **mean, median, min, max** of the 25 Jaccard values.
- Retain **per-file selection frequencies** per model.
- This metric is **DESCRIPTIVE**. No equivalence threshold is defined after
  seeing results; no overlapping-confidence-interval → model-equivalence claim
  is made.

## 7. Inferential-statistics boundary

No new inference statistics are added by this note or by any future run without
a separately justified, pre-frozen protocol. No naive Wilson intervals on
pooled file decisions, no Wald intervals, no significance tests comparing v1
and v2, no TOST, no cluster-bootstrap headlines, no model-equivalence claims.
Rationale: five repetitions nested within only six fixed cases; primary v1 has
severe survivor bias (6/30 valid).