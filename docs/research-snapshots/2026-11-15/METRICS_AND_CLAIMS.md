# Metrics, denominators, exact provenance and allowed claims

Date: 2026-11-15. Labels `ORIGINAL-REPO`, `DERIVED-OFFLINE`, `HANDOFF-REPORTED`, and `PLANNED` are intentionally distinct.

## A. Original WP1 evidence — `ORIGINAL-REPO`

| Experiment | Denominator/metric | Measured result | Allowed scientific wording | Immutable original |
|---|---|---|---|---|
| Saleor RESERVE-300 | n=300; file-set F1 | RM-CSS `0.3568726356`; SIP `0.2647462277`; paired delta `+0.0921264079`; bootstrap 95% CI `[0.0690794142,0.1156339037]` | RM-CSS improves file-set selection vs SIP on untouched Saleor reserve | [`reports/saleor_reserve_300_rmcss_result.json`](../../../reports/saleor_reserve_300_rmcss_result.json); blob `8e5eb84b9f8eeda8f5e966dcb86ede6807f9374d` |
| Saleor MAIN_297 | n=297; pooled file-set F1 | RM-CSS `0.3568253968` (TP=281, FP=379, FN=634); bounded Agent `0.3630692452` (TP=291, FP=397, FN=624); SIP `0.2651933702` | Selection-only; NI margin 0.05 `SUPPORTED`, margin 0.03 inconclusive, NOT equivalence or downstream superiority | [`reports/wp1b_main297_result.json`](../../../reports/wp1b_main297_result.json); blob `434e894dbcd75602121ec548289d8dad88789e0f` |
| MAIN_297 efficiency | Mean per task, marginal view A | RM-CSS total selection tokens `17011.323232`; Agent `79531.474747` (reduction `78.61%`); calls `2.0` vs `7.282828`; USD `0.00530862` vs `0.02405191` | Marginal **selection-stage** accounting only; not end-to-end token, wall-clock or dollar savings | same MAIN_297 original, `cost_view_A_marginal` |

Note: The 78.61% is `(79531.474747 - 17011.323232)/79531.474747`. The stricter `generative_tokens_only` sensitivity differs (`16969.323232` vs `79531.474747`); never silently swap the denominator or category. The NI verdict does not imply equivalent repair.

## B. Track 1.1 external SWE-bench controls — `DERIVED-OFFLINE`

Identity: SWE-bench Verified, 10 tasks sampled with seed `20261114`; frozen 20 original generation POSTs (10 BM25 + 10 Gold), `max_output_tokens=16384`, route `qwen/qwen3-coder` via `deepinfra/turbo`, `allow_fallbacks=false`. Frozen request-set SHA256: `0fb6780545cf5ecefd38d86cc8f74f20cc989822788f0162d9f4f4c6120728cf` (per supplied report; original workstation not accessed by this sync).

| Metric | C-BM25 | C-GOLD oracle file scope |
|---|---:|---:|
| Original attempts | 10 | 10 |
| Independently evaluated `RESOLVED` | 3/10 | 3/10 |
| HTTP 200 | 10/10 | 10/10 |
| Prompt tokens | 563,602 | 195,990 |
| Completion tokens | 23,010 | 25,769 |
| Total model tokens | 586,612 | 221,759 |
| Model inference USD | 0.1917482 | 0.0833916 |
| Format/application valid PATCH_READY (corrected derived view) | 5/10 | 7/10 |
| Selected file-set micro TP / FP / FN | 5 / 45 / 8 | 13 / 0 / 0 (by construction) |
| File-set micro precision / recall / F1 | .1000 / .384615 / .158730 | 1 / 1 / 1 (oracle by definition) |
| Model-generation latency summed across calls | 424.69 s | 559.16 s |

From C-BM25 to C-GOLD: prompt tokens `65.23%` less, total tokens `62.20%` less and model inference cost `56.51%` lower; completion tokens `11.99%` **more**. These are *not RM-CSS savings*. Per-task elapsed E2E wall-clock, Docker image download time and full grading time: **NOT RECORDED**. File-level accuracy (without a TN universe): **UNDEFINED**.

Source: supplied derived `AGGREGATE_METRICS.json`, corrected-only `T11_SAFE_CORRECTIONS_20261114.zip` (`AGGREGATE_METRICS_CORRECTED.json`, `METRICS_REPORT_CORRECTED.md`, unchanged `PER_TASK_METRICS.csv` and `NEED_FILE_ANALYSIS.csv`). Original `AGGREGATE_METRICS.json` has incorrect negative saving denominators, `successful_http=1` as a boolean, and incorrectly says BM25 `PATCH_READY=7/10`. Do not cite that version for these fields. Full raw workstation evidence was **not** available for independent recheck in this documentation session.

## C. NEED_FILE escalation — `HANDOFF-REPORTED`, not live evaluated

Input historical requests: 7 `NEED_FILE` entries in 4 BM25 tasks, with 5 retrospective Gold-hit entries (=4 unique Gold-hit file paths). The Gold-hit labels are **post hoc evaluation only**, never decision inputs. Under the frozen `NO_EDITS + NEED_FILE` trigger only 3 attempts qualify for inspection:

| Task | Raw requests | Gold-blind outcome | Explanation |
|---|---|---|---|
| `django__django-11119` | `django/template/engine.py` | `ESCALATE` to `engine.py` | Parent blob 6,854 bytes; Handoff file path chosen |
| `matplotlib__matplotlib-14623` | `_base.py` (158,788 B), `scale.py` (24,265 B), `axis.py` (89,364 B) | `ESCALATE` to `lib/matplotlib/scale.py` | 32,768-byte cap skips first-requested `_base.py`, although that is a Gold file; `scale.py` is **not** Gold |
| `sphinx-doc__sphinx-7462` | `sphinx/domains/python.py` twice (52,076 B) | `REJECTED` | Only requested path exceeds 32,768-byte cap |

Reported tests: **26/26 PASS**. Static inspection of uploaded tests: 15 in `test_policy.py`, 7 in `test_escalation.py` (3 integration + 4 spend-guard), 4 in `test_historical.py`. Not 15+4+4+4 (that expression sums to 27). Tests were run on the user's isolated container as reported; **not re-executed** in this documentation session.

Continuation plan: A = same scope and another generation POST, B = scope plus one admitted file and another POST, on the two ESCALATE tasks. 4 POSTs total, estimated cost `$0.101911` **at assumed model price and token estimation**; planned maximum `16384` output tokens per POST. Per-POST spending policy `$0.20`; run hard cap `$1.00`, but **live enforcement is NOT demonstrated**. Original requests and 20 original responses are unchanged. `NEW_QWEN_POSTS=0`, `E2E_RERUNS=0`, `ADDITIONAL_RESOLVED=NOT_MEASURED`.

**Critical live blockers:** Uploaded `need_file_escalate.py` acts as a deterministic planner; no demonstrated binding of `spend_guard.py` to each live provider POST. Crash-safe two-write receipt/ledger durability and replay suppression need a failure-injection audit; a single hour of host stability is not an environment qualification. The quoted `$0.101911` is not a defensible hard upper bound when future prompt tokenization can differ from character-based approximation. Do not authorize live posts on the basis of the plan-only tests.

**Handoff custody:** Nested `CHATGPT_HANDOFF.zip`, byte length **145,710**, SHA256 `0d0d93f6833b131ba36dc1ac982a3fa6856de59b0a395dc63390e93ba71e4984` (independently verified within uploaded outer ZIP). Uploaded outer `T11_ESC_INTEGRATION_20261115.zip`, byte length **283,077**, SHA256 `d8bcdfc6e93fbaa2ae6dbc15a9fbea14dc1a53da9fb4e5423f3dec84a79218a7`. These are different containers; neither replaces the original `D:\WP2\handoffs\T11_ESC_INTEGRATION_20261115` custody without workstation recheck. Frozen policy `policy/need_file_policy.py` SHA256 `eae159a1c6406f46fe06739094d131dc75d6f6005cbdec76841115b2fd369cdd`.

## D. What we CANNOT claim

- Do **not** claim 78.6% or 62.2% E2E savings for RM-CSS; different methods, denominator and stages.
- Do **not** claim RM-CSS repaired 3/10 SWE-bench tasks; those are BM25 / Gold controls.
- Do **not** claim observed success or benefit from NEED_FILE retry: **0** continuation calls so far.
- Do **not** infer that Django/SWE-bench eliminates model pretraining contamination.
- Do **not** claim full time, cost including hardware, or external competitor superiority from unmatched tasks/budgets.
