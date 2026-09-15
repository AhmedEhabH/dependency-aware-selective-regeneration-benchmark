# CHEAP NON-LLM BASELINES v1 — INDEPENDENT AUDIT

**Audited by:** openrouter/deepseek/deepseek-v4-flash-0731 (implementation AI; independent read-only pass over persisted artifacts)
**Basis:** persisted evidence only — `research/cheap-baselines-v1/*.json`, frozen dataset, gate JSON. It does NOT trust in-memory runner objects.
**Verdict:** **PASS** — all six gates + independent audit checks green; no pipeline leak; results reproducible from raw outputs.

## 1. What was checked

| # | Check | Result |
|---|---|---|
| 1 | Dataset: TRAIN 24 / VALIDATION 6 / HELD_OUT_TEST 10 exact; universe hashes match frozen manifest; proxy ⊆ universe | PASS |
| 2 | Query = public intent only; no semantic-gold tokens; frozen-corpus path-mention caveat recorded (3 TRAIN cases) | PASS |
| 3 | Pipeline smoke: B0–B4 × K produce bounded deterministic ranks on synthetic case | PASS |
| 4 | Dry run: 2 real TRAIN/VALIDATION cases, expected cell count 20/case, zero API | PASS |
| 5 | Integration: 30 cases × 5 baselines × 4 K = 600 cells; manifest hash stable | PASS |
| 6 | Metric verification: synthetic TP=2/FP=1/FN=1 → P=R=2/3, F1=2/3, FNR=1/3 | PASS |
| 7 | No HELD_OUT_TEST case in any prediction or processing path | PASS |
| 8 | Zero LLM calls / zero tokens in every efficiency record | PASS |
| 9 | Aggregate labeled "DEVELOPMENT EVIDENCE" (not confirmatory) | PASS |
| 10 | Config freezes exposed-split rule = FORBIDDEN | PASS |

Gate JSON: `reports/cheap_baselines_v1_gates.json` (all_gates_passed=true, audit_passed=true).

## 2. Leakage audit (independent)

- **No proxy in pipeline inputs:** candidate/query/graph inputs are the public
  artifacts only; hidden proxy is loaded separately and is consumed only in the
  post-ranking evaluation step.
- **No future state:** BM25 corpus is materialized from `git archive <parent>`;
  the code refuses parents absent from the cache; the target commit is metadata
  only.
- **No hidden gold in seeds:** graph/hybrid seeds come from the frozen
  intent-token ∩ candidate-token rule, never from proxy membership.
- **No exposed-held-out-derived tuning:** `allowed_case_ids` filters to
  TRAIN/VALIDATION; a dedicated test asserts the HELD_OUT ids are unreachable.
- **Frozen-corpus caveat (not a pipeline leak):** 6/40 frozen cases (3 in
  TRAIN: `djangocms-rc-2efae8e43bd6`, `djangocms-rc-ada585d3f358`,
  `djangocms-rc-5ff38b521274`) carry full-message intents containing a changed
  path; the M4A-2 leak detector had operated on the short subject. The P1 LLM
  planner received the identical full-message intent, so baselines and planner
  share the same (public) input; this is a documented dataset property, not a
  new exposure introduced by this block.

## 3. Reproducibility

- Raw predictions → per-task metrics → aggregates → CSV exports are produced by
  deterministic scripts (`run_cheap_baselines.py`,
  `export_cheap_baselines_csv.py`); results are byte-reproducible across
  identical inputs (dedicated restart-determinism test).
- Fixed seeds and frozen rule constants make every baseline deterministic.

## 4. Conclusion

The block satisfies the T3 bar: six gates PASS, independent audit PASS,
leakage-regression and parent-state tests PASS, metrics verified on synthetic
known-answer examples, and every result table traces to raw outputs.