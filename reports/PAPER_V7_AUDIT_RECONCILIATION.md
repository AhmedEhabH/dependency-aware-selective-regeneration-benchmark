# Paper V7 Audit Reconciliation

**Evidence-backed correction note for manuscript editing.**
Benchmark complete at `v0.11.0-benchmark-complete`; the audited v2 study tag
`stagec-djangocms-impactplan-v2-study-01-audited` is unchanged. No new
scientific call, no frozen artifact modification, no metric change was made by
this note. Every conclusion is recomputed from frozen evidence by
`python scripts/verify_paper_claims.py` (exit 0) and traced in
[`PAPER_CLAIM_EVIDENCE_MAP.md`](PAPER_CLAIM_EVIDENCE_MAP.md).

---

## 1. Token table — Table III is mislabeled

The three manuscript values are **TOTAL tokens (all-cell)**, not completion
tokens:

| Arm | Paper value | Prompt (all-cell) | Completion (all-cell) | Total (all-cell) |
|---|---|---|---|---|
| Agent | 449,792 | 441,348 | 8,444 | **449,792** |
| ImpactPlan-v1 | 184,401 | 87,287 | 97,114 | **184,401** |
| Sparse-v2 | 144,353 | 113,880 | 30,473 | **144,353** |

Source: `run_records.jsonl` `total_tokens` summed over all cells of each arm
(the only aggregation that reproduces these three values exactly).

**Recommended replacement column/caption wording:**

> Total tokens (all-cell) — prompt + completion tokens across all recorded
> cells (Agent 449,792; ImpactPlan-v1 184,401; Sparse-v2 144,353).

Do **not** label any of these "completion tokens" — that field sums to
8,444 / 97,114 / 30,473 respectively.

## 2. v1/v2 confound

v2 changed the representation (sparse, non-PRESERVE-only serialization), the
output schema, and the matching planner instruction **together**. Effects were
**not** independently ablated.

**Recommended manuscript language:**

> Observed v1-to-v2 differences are attributed to the frozen v2 redesign
> package; the isolated causal contribution of sparse encoding alone was not
> measured.

No new ablation is authorized now.

## 3. Uncertainty / confidence intervals

No inferential-significance claim is made. The evidence contains repeated cells
clustered within six scenarios; individual TP/FP/FN decisions are not obviously
independent Bernoulli trials, so a naive Wilson interval would be misleading.
If uncertainty intervals are later desired, they require an explicitly chosen
cluster-aware analysis protocol. **No new statistical headline was generated in
this task.**

## 4. Agent/v1 output-budget confound

Agent-v1 operational-validity differences (25/30 vs 6/30) are **descriptive and
confounded** by structurally different output budgets (Agent 8 × 1024; v1 1 ×
4096). Do not present the comparison as an isolated representation effect.

**Recommended wording:** the 25/30 vs 6/30 valid-cell difference is an
operational/descriptive observation under unequal frozen completion budgets, not
an isolated representation effect.

## 5. 16K diagnostic

State everywhere: **ONE-SCENARIO / ONE-RUN diagnostic** (scenario 004,
`completion 10,650 / 179.172 s / $0.01148`, `CASE_A_TERMINATES`). No
cross-scenario generalization. Source:
`reports/scientific-stagec-djangocms-impactplan-16k-diagnostic-01/diagnostic.json`.

## 6. Graph diagnostic

The graph observation is **POST-HOC, DIAGNOSTIC, NON-CAUSAL**. Do **not** claim
graph predictive value. Because the manuscript is page-constrained, keep the
detailed graph edges/density analysis in the artifact/handoff
(`docs/PAPER_WRITING_HANDOFF.md` §14.3) and reduce the main-paper claim to at
most a cautious Future Work sentence. No new graph experiment was created.

## 7. Failed v2 run — exact verified reason

`stgc-v2-djangocms-external-validity-002-impact_plan_v2-r3` (scenario 002, rep
3) failed with:

```
impact_plan_invariant_failure: v_missing_validation_reason: cms/models/__init__.py
```

The model emitted `cms/models/__init__.py` as **VALIDATE with no cited
supporting evidence**; the frozen semantic invariant failed closed. `cms/api.py`
was nevertheless correctly emitted as REGENERATE. The cell was not salvaged or
rescored. Source: `run_records.jsonl` + raw response
`runs/raw/stgc-v2-djangocms-external-validity-002-impact_plan_v2-r3.txt`.

**Manuscript-safe sentence:**

> The single failed sparse-v2 cell (scenario 002, rep 3) was rejected by the
> frozen semantic invariant: `cms/models/__init__.py` was emitted as VALIDATE
> without cited supporting evidence, so the cell failed closed; it was not
> rescored.

## 8. Scenario-006 table — exact sporadic FP

Gold: `cms/models/pluginmodel.py`, `cms/admin/placeholderadmin.py`,
`cms/utils/plugins.py`.

| File | Gold? | Frequency |
|---|---|---|
| `cms/admin/forms.py` | no | 5/5 |
| `cms/models/pluginmodel.py` | yes | 5/5 |
| `cms/plugin_rendering.py` | no | 5/5 |
| `cms/admin/placeholderadmin.py` | yes | 2/5 |
| `cms/utils/placeholder.py` | no | **1/5** |
| `cms/utils/plugins.py` | yes | 0/5 |

The manuscript's current table lists five visible rows (3 gold + `plugin_rendering`
+ `forms`) that account for **10** false positives. Pooled precision implies
**11** FP. The additional sporadic FP is **`cms/utils/placeholder.py`**
(frequency **1/5**, run `...006-impact_plan_v2-r3`).

**Recommendation:** add the exact row (`cms/utils/placeholder.py`, non-gold,
1/5) if space permits; otherwise state in the caption that the table shows the
persistent/key selections and that one additional sporadic non-gold selection
contributes to the pooled precision.

## 9. 4096 cap provenance

Classification: **B** — the protocol freezes 4096 as the ImpactPlan completion
budget; no stronger documented rationale (e.g., a provider maximum) exists.
Sources: `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md`,
`reports/RESEARCH_DECISION_ARCHIVE.md` (entry 3), and
`src/benchmark/selection/impact_planner.py`
(`IMPACT_PLAN_MAX_COMPLETION_TOKENS = 4096`).

**Safe manuscript wording:**

> 4,096 tokens was the frozen completion budget for the primary structured
> ImpactPlan treatment; it is an experimental budget parameter, not claimed as
> an intrinsic model/provider limit.

## 10. Novelty discipline

**Recommended explicit sentence:**

> Default omission / sparse serialization is not claimed as a novel general
> serialization principle; the contribution is its formulation, diagnosis, and
> audited evaluation for repository-level LLM impact-plan serialization.

Do not claim invention of sparse/default-omission generally.

## 11. Supervisor name

No change made to **Mohammad El-Ramly**. Repository evidence is consistent with
the current spelling; it is changed only if authoritative project or official
evidence contradicts it.

## 12. Style / formatting recommendations

- Remove redundancy: "remains retained" → "is retained".
- Avoid awkward sentence openings while preserving the official product spelling
  **"django CMS"**.
- Every table must be explicitly referenced in body text.
- Use leading zeros consistently (0.646, 0.841, etc.).
- Keep captions concise.
- Follow IEEEtran formatting rather than manually inventing caption styling.

---

**Verification:** `python scripts/verify_paper_claims.py` → exit 0 (all headline
metrics recomputed from frozen evidence and internally consistent).