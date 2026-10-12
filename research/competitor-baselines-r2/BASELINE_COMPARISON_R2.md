# M17 — Cheap Zero-Paid-API Same-Protocol Baselines on MAIN_297 (R2)

**Mission:** `M17_COMP_BASELINES_R2_FINAL_CHEAP_SAME_PROTOCOL`
**Branch:** `parallel/competitor-baselines-2026-10-12` · **HEAD:** `1661ec215ede6ae96e82735148db4febffb21580`
**Freeze:** `research/competitor-baselines-r2/BASELINE_PROTOCOL_FREEZE_R2.json` SHA256 `881237ddef31efd66d1f437e861b6d8de9af296dc5ede0eef742b8df9ec1cef9`
**Population:** MAIN_297 (297 tasks = RESERVE-300 minus 3 Calibration-3)
**Evaluator:** the exact evaluator used for RM-CSS / SIP / Agent MAIN_297 results
(`benchmark.wp1a.scorer` micro pooling + per-task confusion).

## 1. Frozen protocol and population identity

- Manifest: `research/wp1b/wp1b_main_297_manifest.json` (`manifest_sha256 6bc5980f…fccde`; `task_ids_sha256 1678dbaa…ccbceb`).
- Gold: `research/saleor-reserve-300-rmcss/saleor_reserve_300_proxies.json` (opened-once observed change-set proxy; all proxy paths inside the frozen candidate universe).
- Candidate universe: per-task `public/candidate_universe.json` (no added exclusions; 0 predictions outside universe).
- Input to methods: exact developer change description (`intent_text`) + repository snapshot at the parent commit; no gold-derived information.
- All parameter decisions (BM25 k1=1.2/b=0.75, DENSE frozen artifact, K ∈ {1,3,5,10}, SIZE_MATCHED rule, oracle seed rule, bootstrap seed 20261012) frozen BEFORE any baseline outcome.

## 2. Direct same-protocol results (micro, pooled over 297 tasks)

| Arm | Evaluation label | P | R | F1 | FNR | macro F1 | size mean (min..max) |
|---|---:|---:|---:|---:|---:|---:|---:|
| RM-CSS | FROZEN_MAIN297_ARM | 0.4258 | 0.3071 | 0.3568 | 0.6929 | 0.3427 | 2.22 (0..10) |
| SIP | FROZEN_MAIN297_ARM | 0.3602 | 0.2098 | 0.2652 | 0.7902 | 0.2562 | 1.79 (0..21) |
| AGENT | FROZEN_MAIN297_ARM | 0.4230 | 0.3180 | 0.3631 | 0.6820 | 0.3971 | 2.32 (0..17) |
| BM25@1 | DIRECT_SAME_PROTOCOL | 0.3502 | 0.1137 | 0.1716 | 0.8863 | 0.2042 | 1.00 (1..1) |
| BM25@3 | DIRECT_SAME_PROTOCOL | 0.2368 | 0.2306 | 0.2337 | 0.7694 | 0.2345 | 3.00 (3..3) |
| BM25@5 | DIRECT_SAME_PROTOCOL | 0.1946 | 0.3158 | 0.2408 | 0.6842 | 0.2318 | 5.00 (5..5) |
| BM25@10 | DIRECT_SAME_PROTOCOL | 0.1394 | 0.4525 | 0.2131 | 0.5475 | 0.2001 | 10.00 (10..10) |
| BM25_SIZE_MATCHED | SIZE_MATCHED_CONTROL | 0.2818 | 0.2033 | 0.2362 | 0.7967 | 0.2238 | 2.22 (0..10) |
| DENSE@1 | DIRECT_SAME_PROTOCOL | 0.3973 | 0.1290 | 0.1947 | 0.8710 | 0.2239 | 1.00 (1..1) |
| DENSE@3 | DIRECT_SAME_PROTOCOL | 0.2783 | 0.2710 | 0.2746 | 0.7290 | 0.2782 | 3.00 (3..3) |
| DENSE@5 | DIRECT_SAME_PROTOCOL | 0.2168 | 0.3519 | 0.2683 | 0.6481 | 0.2600 | 5.00 (5..5) |
| DENSE@10 | DIRECT_SAME_PROTOCOL | 0.1471 | 0.4776 | 0.2250 | 0.5224 | 0.2136 | 10.00 (10..10) |
| DENSE_SIZE_MATCHED | SIZE_MATCHED_CONTROL | 0.3318 | 0.2393 | 0.2781 | 0.7607 | 0.2617 | 2.22 (0..10) |
| BM25_TO_CIA_1HOP | DIRECT_SAME_PROTOCOL | 0.0457 | 0.3781 | 0.0816 | 0.6219 | 0.1062 | 25.48 (1..276) |
| BM25_TO_CIA_2HOP | DIRECT_SAME_PROTOCOL | 0.0074 | 0.8044 | 0.0146 | 0.1956 | 0.0245 | 336.93 (1..833) |
| C_ORACLE_1HOP | UPPER_BOUND_ONLY | 0.0707 | 0.6262 | 0.1271 | 0.3738 | 0.1914 | 27.28 (1..197) |
| C_ORACLE_2HOP | UPPER_BOUND_ONLY | 0.0077 | 0.9333 | 0.0153 | 0.0667 | 0.0311 | 373.08 (1..843) |

> DENSE rows additionally carry **DENSE_ONLY_ABLATION** (the frozen RM-CSS classifier consumes exactly this dense representation; ranking quality isolated from the calibrated head).

## 3. Size-matched controls

- `BM25_SIZE_MATCHED`, `DENSE_SIZE_MATCHED`: k_t = number of files selected by the frozen RM-CSS prediction for task t (RM-CSS **output size only**; never reads gold).
- Purpose: separate ranking quality from selection-budget differences. Not presented as independent published competitor implementations.

## 4. Parameter-grid results (pre-specified; no K selected after outcomes)

- BM25@1/3/5/10: F1 0.172 / 0.234 / 0.241 / 0.213 (FNR 0.886 / 0.769 / 0.684 / 0.548).
- DENSE@1/3/5/10: F1 0.195 / 0.275 / 0.268 / 0.225 (FNR 0.871 / 0.729 / 0.648 / 0.522).
- Best direct baseline F1 (0.275 @ DENSE@3) < RM-CSS F1 (0.357).

## 5. Gold-seeded upper bounds (diagnostic)

- `C_ORACLE_1HOP` F1 0.127, `C_ORACLE_2HOP` F1 0.015 (UPPER_BOUND_ONLY / GOLD_SEEDED).
- Reverse-dependency closure is recall-hungry and precision-poor on Saleor (mean set 27 / 373 files); these are **diagnostic** and never enter the headline comparison. They form the bridge to seeded methods such as RIPPLE / From Seed to Scope (also GOLD_SEEDED by definition).

## 6. Paired bootstrap CIs (RM-CSS − baseline; 10,000 resamples over tasks, seed 20261012)

| Comparison | Label | ΔF1 point | ΔF1 95% CI | ΔRecall point | ΔRecall 95% CI |
|---|---:|---:|---:|---:|---:|
| RM-CSS − BM25@1 | DIRECT_SAME_PROTOCOL | +0.1852 | [+0.1455, +0.2231] | +0.1934 | [+0.1588, +0.2278] |
| RM-CSS − BM25@3 | DIRECT_SAME_PROTOCOL | +0.1232 | [+0.0847, +0.1608] | +0.0765 | [+0.0394, +0.1136] |
| RM-CSS − BM25@5 | DIRECT_SAME_PROTOCOL | +0.1160 | [+0.0803, +0.1513] | -0.0087 | [-0.0475, +0.0296] |
| RM-CSS − BM25@10 | DIRECT_SAME_PROTOCOL | +0.1437 | [+0.1082, +0.1784] | -0.1454 | [-0.1886, -0.1032] |
| RM-CSS − DENSE@1 | DIRECT_SAME_PROTOCOL | +0.1621 | [+0.1301, +0.1937] | +0.1781 | [+0.1486, +0.2081] |
| RM-CSS − DENSE@3 | DIRECT_SAME_PROTOCOL | +0.0822 | [+0.0563, +0.1086] | +0.0361 | [+0.0095, +0.0625] |
| RM-CSS − DENSE@5 | DIRECT_SAME_PROTOCOL | +0.0885 | [+0.0634, +0.1137] | -0.0448 | [-0.0716, -0.0191] |
| RM-CSS − DENSE@10 | DIRECT_SAME_PROTOCOL | +0.1319 | [+0.1033, +0.1602] | -0.1705 | [-0.1995, -0.1415] |
| RM-CSS − BM25_SIZE_MATCHED | SIZE_MATCHED_CONTROL | +0.1206 | [+0.0848, +0.1567] | +0.1038 | [+0.0728, +0.1357] |
| RM-CSS − DENSE_SIZE_MATCHED | SIZE_MATCHED_CONTROL | +0.0787 | [+0.0546, +0.1034] | +0.0678 | [+0.0466, +0.0899] |

RM-CSS micro-F1 is above **every** direct variant and both size-matched controls with 95% CIs entirely above zero. ΔRecall is positive vs small-K baselines and negative vs K=10 (large set sizes), i.e. the RM-CSS advantage is precision-and-set-size driven.

## 7. Efficiency

- Zero-API arms: **0 new LLM calls, $0.00 new API cost** (all arms). Computational cost is not zero: BM25 full run wall ≈ 250 s (index 42.6 s + query 207.6 s over 297 tasks, local CPU); Phase 2 total wall ≈ 277 s.
- DENSE: frozen-artifact reuse (no new calls; historical materialization $0.026035 for 300 tasks recorded as informational, not this mission's spend).
- Reused frozen arms: SIP (1 call/task, ~5.00M prompt tokens, $1.593 total), RM-CSS, bounded Agent (protocol v3) — evidence frozen, not rerun.

## 8. Agentless-style estimate

See `AGENTLESS_STYLE_EXECUTION_ESTIMATE.md` (official repo `https://github.com/OpenAutoCoder/Agentless` @ `5ce5888b`; prompt source `agentless/fl/FL.py`; offline prompt-size stats; ~$0.7–$1.7 localization-only cost band with the frozen qwen3-coder@deepinfra/turbo price; planned run class = **AGENTLESS_STYLE_ADAPTATION**).

## 9. Blocked / ambiguous arms

- `SweRankEmbed-Small` dense path: **BLOCKED_DOWNLOAD** (model not cached locally; 273 MiB download > 100 MiB prohibited). Mission continued with the frozen qwen dense artifact (zero new download, zero new API call) — see execution JSON.
- No other arm blocked; no BASELINE_PROTOCOL_AMBIGUITY / MISSING_ARTIFACT / EVALUATOR_MISMATCH / NOT_REPRODUCIBLE_WITHOUT_NEW_PROTOCOL.

## 10. Interpretation (no scientific claim change)

- On the frozen MAIN_297 population and the frozen file-level evaluator, the pre-specified cheap zero-API baselines (BM25, dense retrieval, static CIA closure, gold-seeded CIA) do not match RM-CSS micro-F1; the RM-CSS advantage is statistically supported at the 95% level against every direct variant.
- Static reverse-dependency closure (even gold-seeded) performs poorly as a set-selection method here — recall is easy, precision collapses.
- Published Acc@K / Hit@K / MRR / MAP / function-level accuracy / resolve rates from competitor papers are **PUBLISHED_CONTEXT_ONLY** and must never be numerically compared with these micro-F1 numbers (see `research/competitors/COMPETITOR_MATRIX_R1.md` §4).
- RIPPLE / From Seed to Scope is **not run**; any future comparison to it requires a separately frozen seed-generation protocol (e.g., BM25 top-1) and would otherwise be GOLD_SEEDED / UPPER_BOUND_ONLY.
