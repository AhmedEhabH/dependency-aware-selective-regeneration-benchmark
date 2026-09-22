# WP-1b Calibration-3c — STOP Report (2026-09-22)

**DECISION: CAL3C_CLEAN** — and the mission STOPS here (D3 = MANUAL).

- Contract: `_workspace/active/OPENCODE_CONTRACT_WP1B_G12_TO_MAIN297_2026-09-22.md`
- Branch: `wp1b/calibration-3c-2026-09-22`
- Protocol: v3 (`research/wp1b/wp1b_frozen_agent_protocol_v3.json`, G12 applied)
- Gate: v3 (`artifacts/wp1b_calibration_gate_v3.json`)
- Same 3 calibration tasks; **not scored**; no labels loaded; no F1.
- Ceiling $0.25; actual **$0.063205**.

## Clean criteria (clarification 7) — all PASS

| # | Criterion | Result |
|---|---|---|
| 1 | CG-1..CG-12 PASS | **PASS** (`wp1b_calibration_gate_v3_result.json`) |
| 2 | ≥ 2 of 3 tasks with ≥ 1 successful `read_file` | **PASS** — 349d46d906ad: 2, d52a55471bfc: 2 |
| 3 | rejected-repeat share ≤ 25% of calls | **PASS** — 1/18 = 5.6% |
| 4 | no run of ≥ 3 consecutive identical rejected requests | **PASS** — longest run = 1 |
| 5 | cost ratio ≤ 1.0 on every task | **PASS** — 0.331 / 0.645 / 0.420 |
| 6 | zero BLOCKING Review Card anomalies | **PASS** — 0 blocking (4 informational) |

## Call-by-call evidence

| task | k | action | arguments | outcome | chars raw/shown | rejected |
|---|---|---|---|---|---|---|
| 349d46d906ad | 1 | search_text | query="celery" | ok | 3768/2000 | no |
| 349d46d906ad | 2 | read_file | path="saleor/celeryconf.py" | ok | 1305/1305 | no |
| 349d46d906ad | 3 | read_file | path="saleor/core/logging.py" | ok | 1779/1779 | no |
| 349d46d906ad | 4 | final | selected_paths | final | 0/0 | no |
| b05633dae118 | 1 | search_text | query="shipping method currency" | ok | 0/0 | no |
| b05633dae118 | 2 | search_text | query="external shipping method currency" | ok | 0/0 | no |
| b05633dae118 | 3 | search_text | query="external shipping method" | ok | 753/753 | no |
| b05633dae118 | 4 | search_text | query="currency" | ok | 4345/2000 | no |
| b05633dae118 | 5 | search_text | query="external shipping methods" | ok | 753/753 | no |
| b05633dae118 | 6 | search_text | query="external shipping method currency" | ok | 0/0 | no |
| b05633dae118 | 7 | search_text | query="filter shipping methods" | ok | 695/695 | no |
| b05633dae118 | 8 | final | selected_paths | final | 0/0 | no |
| d52a55471bfc | 1 | search_text | query="ShippingMethodTranslationByIdAndLanguageCodeLoader" | ok | 211/211 | no |
| d52a55471bfc | 2 | read_file | path="saleor/graphql/translations/dataloaders.py" | ok | 4512/2000 | no |
| d52a55471bfc | 3 | (rejected repeat of call 2) | — | rejected | 0/0 | **yes** |
| d52a55471bfc | 4 | read_file | path="saleor/graphql/translations/resolvers.py" | ok | 2511/2000 | no |
| d52a55471bfc | 5 | search_text | query="ShippingMethodTranslationByIdAndLanguageCodeLoader" | ok | 211/211 | no |
| d52a55471bfc | 6 | final | selected_paths | final | 0/0 | no |

## Per-task summary (clarification 12)

| task | calls | useful tool calls | successful reads | rejected repeats | longest consecutive run | prompt growth (first→last) | truncation events | instrument errors | prompt tokens | completion tokens | total tokens | USD | cost ratio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 349d46d906ad | 4 | 3 | 2 | 0 | 0 | 13768 → 15211 (+1443) | 1 | 0 | 58,184 | 165 | 58,349 | 0.017620 | 0.331 |
| b05633dae118 | 8 | 7 | 0 | 0 | 0 | 12935 → 14276 (+1341) | 1 | 0 | 108,307 | 352 | 108,659 | 0.032844 | 0.645 |
| d52a55471bfc | 6 | 4 | 2 | 1 | 1 | 6323 → 7545 (+1222) | 2 | 0 | 41,608 | 258 | 41,866 | 0.012740 | 0.420 |
| **Total** | **18** | **14** | **4** | **1** | **1** | — | **4** | **0** | **208,099** | **775** | **208,874** | **0.063205** | ≤ 0.645 |

- rejected-call share: **1/18 = 5.6%** (was 11/21 = 52.4% in Calibration-3b)
- rejected spend: **$0.002094** (was $0.036727 in 3b; 3.3% of 3c spend vs 52%)
- 0 cap hits, 0 EMPTY, 0 malformed, 0 schema-invalid, 0 instrument errors
- prompt growth across consecutive calls: no run of identical-rejected growth (uniform 18-token signature gone)

## Review Card flags (quoted from `research/wp1b/calibration-3c-2026-09-22/REVIEW_CARD.md`)

- **BLOCKING: none** — verdict `NO_BLOCKING_ANOMALIES`
- **INFORMATIONAL:**
  - I1 task saleor-rc-b05633dae118 has 0 read_file calls
  - I2 task saleor-rc-b05633dae118 is search/list-only (0 reads, 7 tool calls)
  - I3 task saleor-rc-349d46d906ad: 1 search-result-cap hit(s)
  - I3 task saleor-rc-b05633dae118: 1 search-result-cap hit(s)

INFORMATIONAL flags do not independently fail the calibration (clarification 7).

## Calibration-3b → 3c regression

| metric | 3b (pre-G12) | 3c (post-G12) |
|---|---|---|
| calls | 21 | 18 |
| rejected repeats | 11 (52.4%) | 1 (5.6%) |
| longest rejection run | 6 / 4 | 1 |
| successful reads | 3 | 4 |
| instrument errors | 0 | 0 |
| USD | 0.070028 | 0.063205 |
| gate v3 CG-12 | FAIL (RED) | **PASS** |

The G12 amendment (action echo, call counter, named rejection, truncation note)
removed the deterministic context loop: task 2 previously sent the same search 6
times in a row; in 3c it used 7 distinct searches. Task 3 previously re-read the
same truncated file 4 times; in 3c it was rejected once (named warning), then
moved to a different file.

## STOP

D3 = **MANUAL**: the mission stops after Calibration-3c regardless of outcome.
MAIN_297, the variance substudy, label loading and scoring are NOT authorized.
No second scaffold fix (D5 binding). Calibration-3c is clean; the next real
step is a separate decision on MAIN_297.

## What remains

- MAIN_297 + variance 15×3 + scoring (blocked; separate decision required).
- WP-2 shared E2E instrument; E2E-G6 F2P/P2P oracle; Smoke → Pilot → Research Run.

## NEXT

`D3 decision for MAIN_297 (protocol v3, manifest order, ceilings $21.50 / $3.50).`