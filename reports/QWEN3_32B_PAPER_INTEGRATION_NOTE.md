# Qwen3-32B Paper Integration Note

**For the manuscript chat (GPT-5.6 SOL / paper phase).** Read this note before
writing any manuscript text about the cross-model robustness replication. Do
NOT edit the manuscript from this note; it only specifies what may and may not
be claimed.

Study: `scientific-stagec-djangocms-qwen3-32b-crossmodel-01`
Label: **POST-HOC CROSS-MODEL ROBUSTNESS REPLICATION**
Status: **COMPLETE + AUDITED** (2026-09-11)

---

## 1. What was run

- Same repositories, cases, treatments, gateway and provider as the frozen
  Qwen3-Coder-480B-A35B-Instruct djangoCMS studies; **only the model changed**
  (`qwen/qwen3-coder` → `qwen/qwen3-32b`), plus an explicit reasoning-mode
  configuration (see §6).
- 60 cells: 6 scenarios × 2 arms (`impact_plan` v1, `impact_plan_v2`) × 5 reps.
- Preregistered before cell 1: `reports/QWEN3_32B_CROSSMODEL_PROTOCOL.md`.

## 2. Exact new results

| Arm | Valid / 30 | Failed | Truncations | P | R | F1 | FNR | Full-recall |
|---|---|---|---|---|---|---|---|---|
| impact_plan (v1) | 2 | 28 | 24 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0/2 |
| impact_plan_v2 | 21 | 9 | 6 | 0.3600 | 0.6207 | 0.4557 | 0.3793 | 5/21 = 0.238 |

- Totals (all 60 cells): 179,641 prompt + 141,611 completion = 321,252 tokens;
  **60 API requests issued** (one per manifest cell), of which **52 are
  usage-bearing** (recorded `model_calls`); **live cost $0.054028** (DeepInfra
  `$0.08/$0.28` per 1M).
- v1 failure taxonomy: 24 truncations at the frozen 4096 cap (verbose
  full-policy serialization does not fit the budget), 4 out-of-universe-path /
  transport failures. Recorded verbatim; **no reruns, no cell 61**.
- v2 failure taxonomy: **6 truncations at the frozen 4096 cap**
  (S004 r1–r5, S008 r2; `finish_reason=length`, unterminated raw JSON ~16 KB)
  + 2 conflicting-decision invariant failures + 1 duplicate-candidate-id
  failure.
- **Accounting correction (2026-09-11):** the originally published "v2
  truncations = 0" was a derived-classification bug — `truncation_status` was
  only set on the success path. Corrected v2 truncations = **6**, total = **30**.
  Valid-run selection metrics (P/R/F1) are **unchanged** (the 6 cells were
  already failed). `model_calls` (52) is usage-bearing only; all 60 cells
  issued exactly one request. 8 failed cells ran before usage capture was
  wired in; 7 have persisted raw responses with **unrecoverable exact provider
  usage** (see §10 and the correction note).

## 3. Allowed claims

- "A post-hoc cross-model robustness replication of the djangoCMS selection
  studies on `qwen/qwen3-32b` (OpenRouter / DeepInfra) was run; 60/60 cells
  recorded; 23 valid / 37 failed / 24 truncations."
- "The sparse v2 representation remained operational on Qwen3-32B (21/30
  valid, 0 truncations), whereas the v1 full-policy serialization truncated at
  the frozen 4096 cap in 24/30 cells."
- "Directionally replicated (descriptive): v2 operational-validity rate (70%)
  exceeded new-v1 (6.7%) and v2 truncation rate (0%) was below new-v1 (80%)."
- "Cross-model Sparse-v2 agreement (descriptive): 102 cross-product Jaccard
  pairs vs historical Qwen3-Coder-480B-A35B-Instruct; mean 0.284, median 0.231, min 0.0,
  max 1.0; per-file selection frequencies in
  `reports/QWEN3_32B_CROSSMODEL_AGREEMENT.{md,csv}`."
- "Reasoning was explicitly disabled (`reasoning.enabled=false`); verified by
  `usage.completion_tokens_details.reasoning_tokens == 0` in the capability
  probes and by absence of a reasoning field in every message."

## 4. Forbidden claims

- **No** model-superiority / inferiority claim between Qwen3-Coder-480B-A35B-Instruct and
  Qwen3-32B.
- **No** "independent confirmation" or "external validation" framing — this is
  post-hoc on the same six cases.
- **No** statistical significance / equivalence / causal claim (Jaccard and
  the directional label are descriptive only).
- **No** claim that truncation rate implies model quality — v1 truncation is
  an output-verbosity vs frozen-cap outcome, not an accuracy measure.
- **No** pooling of denominators across models or arms (each row is its own
  denominator).
- Do NOT label this "Qwen2.5 replication" — the Qwen2.5 route was abandoned
  and the new study ID must stay `scientific-stagec-djangocms-qwen3-32b-crossmodel-01`.

## 5. Directional replication result

**DIRECTIONALLY REPLICATED** (descriptive) — v2 has both (1) a higher
operational-validity rate than new v1 (0.700 vs 0.067) and (2) a lower
truncation rate than new v1 (0.000 vs 0.800). No significance claim.

## 6. Scenario 006 (new Qwen3-32B v2)

- 5/5 valid; pooled P 0.200 / R 0.333 / F1 0.250 / FNR 0.667; full-recall 0/5.
- Gold files for S006: `cms/admin/placeholderadmin.py`,
  `cms/models/pluginmodel.py`, `cms/utils/plugins.py` (per hidden gold).
- Selected-file frequencies (all selections across the 5 valid runs):
  `cms/admin/placeholderadmin.py` 5 (gold), `cms/models/placeholderpluginmodel.py`
  5, `cms/plugin_processors.py` 3, `cms/admin/forms.py` 2,
  `cms/operations/helpers.py` 2, `cms/plugin_rendering.py` 2, plus singletons
  (`cms/management/commands/cms.py`, `cms/templatetags/cms_static.py`,
  `cms/utils/apphook_reload.py`, `cms/utils/page_permissions.py`,
  `cms/utils/placeholder.py`, `cms/wizards/__init__.py`). The gold
  `cms/models/pluginmodel.py` and `cms/utils/plugins.py` were never selected;
  `cms/admin/placeholderadmin.py` was always selected. This is the same
  qualitative S006 weakness observed for Qwen3-Coder-480B-A35B-Instruct (over-selection +
  persistent misses) — consistent, but descriptive only.

## 6a. Scenario 004 (new Qwen3-32B v2, truncated)

- S004 v2 was **5/5 truncated** at the frozen 4096 cap (vs historical
  Qwen3-Coder-480B-A35B-Instruct S004 v2 **5/5 succeeded**, 6–8 explicit decisions each).
- The new model emitted **36–38 explicit decisions before truncation**
  (r1: 37, r2: 36, r3: 36, r4: 36, r5: 38) — roughly **5–6× the historical
  explicit-decision count** (historical mean across all v2 cells: 6.34).
- r1–r4 emit **100% REGENERATE** (broad over-selection); r5 splits
  19 REGENERATE / 19 VALIDATE. The truncated outputs show broad over-selection
  and fail-closed on the truncated JSON. Descriptive only.

## 7. Cross-model Sparse-v2 Jaccard summary

| Scenario | Hist valid | New valid | Pairs | Mean | Median | Min | Max |
|---|---|---|---|---|---|---|---|
| 002 | 4 | 3 | 12 | 0.000 | 0.000 | 0.000 | 0.000 |
| 004 | 5 | 0 | 0 | — | — | — | — |
| 005 | 5 | 5 | 25 | 0.621 | 0.625 | 0.400 | 1.000 |
| 006 | 5 | 5 | 25 | 0.177 | 0.167 | 0.000 | 0.500 |
| 007 | 5 | 4 | 20 | 0.382 | 0.359 | 0.231 | 0.636 |
| 008 | 5 | 4 | 20 | 0.071 | 0.071 | 0.062 | 0.077 |
| Overall | — | — | **102** | **0.284** | **0.231** | **0.000** | **1.000** |

Do NOT interpret Jaccard as internal-reasoning similarity. Pairs are
cross-product (never r1-vs-r1).

## 8. Reasoning-mode setting

`reasoning: {"enabled": false}` sent on every request; verified
`reasoning_tokens == 0`; no reasoning field in any message. This matches the
historical Qwen3-Coder-480B-A35B-Instruct direct/non-thinking contract and prevents an untracked
hidden thinking budget.

## 9. Same serving route

Both models served through the SAME gateway (OpenRouter) and provider
(DeepInfra pinned through OpenRouter; Qwen3-Coder-480B-A35B-Instruct `deepinfra/turbo`,
Qwen3-32B `deepinfra/fp8`), fallback off, `require_parameters` on.

## 10. Remaining limitations (state explicitly)

- Post-hoc (same six cases already informed the primary evidence); survivor
  bias caveats carry over.
- v1 comparison on Qwen3-32B is almost entirely missing-data (2/30 valid);
  no v1 accuracy inference is supported.
- S006 remains the weak case for both models.
- Cost reported at live DeepInfra rates; recorded `api_cost` for early cells
  used the frozen Qwen3-Coder-480B-A35B-Instruct pricing as a conservative bound (the recomputed
  live figure in `final_metrics.json` is authoritative).
- **Accounting correction (2026-09-11):** exact provider usage for 8 failed
  cells (7 with persisted raw responses but run before usage capture; 1
  transport failure with no response) is **unrecoverable** from immutable
  artifacts — only raw text is persisted. Known lower bounds: the 5 S004 v2
  truncations each consumed exactly 4096 completion tokens
  (`finish_reason=length` = cap reached); the 2 S002 v2 conflicting-decision
  cells returned valid JSON (~1.7–1.9 KB raw) but their exact usage is
  unknown; S006 v1 r3 (IncompleteRead) is fully unrecoverable. Do **not**
  report 52 as "total calls" — 60 requests were issued (see
  `ACCOUNTING_CORRECTION_NOTE.md`).

## 11. Evidence to cite

- `reports/scientific-stagec-djangocms-qwen3-32b-crossmodel-01/` (manifest,
  run records, raw + SHA, metrics, agreement, closure gates)
- `reports/QWEN3_32B_CROSSMODEL_PROTOCOL.md` (preregistration)
- `reports/QWEN3_32B_CROSSMODEL_AGREEMENT.{md,csv}`
- `scripts/verify_qwen3_32b_crossmodel_claims.py` (zero-API verifier; exit 0 = PASS)
- `python scripts/verify_paper_claims.py` (historical verifier still PASS)

Do NOT edit the manuscript from this note.