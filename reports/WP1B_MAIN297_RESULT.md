# WP-1b PRIMARY_MAIN_297 - result (frozen decision rules v2)

**Final category:** `RMCSS_NONINFERIOR_AT_LOWER_COST`  
**Quality verdict:** `NI_SUPPORTED` (row 3 of 7)  
**Cost verdict (View A):** CHEAPER = `True`  
**n:** 297 tasks · labels: opened RESERVE-300 proxies only; 786 sealed outcomes untouched  
**Prediction freeze:** tag `wp1b-main297-predictions-frozen-2026-09-22` · sha256 `c78968ef3fc83af4c067958a529df3b49752ab176d6b2c5f1919962958afd99c`

## 1. Per-arm metrics (pooled micro over identical task IDs)

| Arm | TP | FP | FN | Precision | Recall | F1 | F2 | FNR | mean set size | EMPTY rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SIP | 192 | 341 | 723 | 0.3602 | 0.2098 | **0.2652** | 0.2290 | 0.7902 | 1.79 | 0.239 |
| RM-CSS | 281 | 379 | 634 | 0.4258 | 0.3071 | **0.3568** | 0.3252 | 0.6929 | 2.22 | 0.098 |
| Agent | 291 | 397 | 624 | 0.4230 | 0.3180 | **0.3631** | 0.3346 | 0.6820 | 2.32 | 0.007 |

## 2. Primary comparison D = F1(RM-CSS) − F1(Agent)

| Analysis | n | D point [Q2.5, Q97.5]; Q5 | NI (Q5 > −0.05) |
|---|---:|---|:---:|
| P (fail-closed, primary) | 297 | -0.0062 [-0.0449, +0.0308]; Q5 -0.0383 | True |
| S (drop truncation/parser/infra; dropped 2) | 295 | -0.0115 [-0.0502, +0.0255]; Q5 -0.0434 | True |

Sensitivity margins (reported, not decisive): Δ=0.03: `INCONCLUSIVE_AT_THIS_N`, Δ=0.10: `NI_SUPPORTED`

## 3. Cost (View A, marginal per change) — ratio RM-CSS / Agent of per-task means

| Dimension | RM-CSS mean | Agent mean | ratio [95% CI] | upper < 1 |
|---|---:|---:|---|:---:|
| total_tokens | 17011.3232 | 79531.4747 | 0.214 [0.210, 0.218] | True |
| model_calls | 2.0000 | 7.2828 | 0.275 [0.271, 0.279] | True |
| usd | 0.0053 | 0.0241 | 0.221 [0.216, 0.225] | True |

View B (setup amortized over n): +$0.000087/task → RM-CSS $0.005396/task.  
RM-CSS calls/task in View A = 2 (1 SIP coder call + 1 query-embedding request; preregistered).

## 4. Agent failure modes (fail-closed EMPTY by reason)

`parser_failure`: 2

## 5. Descriptive (not part of the verdict)

- SIP − Agent: -0.0979 [-0.1350, -0.0618]; Q5 -0.1289
- RM-CSS − SIP on this subset: +0.0916 [+0.0690, +0.1153]; Q5 +0.0725

## 6. Run accounting

- ledger USD (frozen list price): $7.147415 of $21.50
- logical calls 2164 · HTTP attempts 2178 · failed calls 1

## 7. What this result does NOT mean

- It is a SELECTION-ONLY file-localization result against an observed change-set proxy, not semantic gold and not end-to-end patch correctness (WP-2 / E2E-G6 not started).
- The competitor is a budget-bounded iterative repository agent (8 calls, 1024-token control cap, 2000-char observation window, substring search), not the strongest possible agent and not a reproduction of LocAgent / Ripple / other published systems.
- Single repository (Saleor), single model (Qwen3-Coder-480B via DeepInfra), temperature 0.
- The word 'dominance' is retired for WP-1b; no equivalence claim is made from a CI that crosses zero.
