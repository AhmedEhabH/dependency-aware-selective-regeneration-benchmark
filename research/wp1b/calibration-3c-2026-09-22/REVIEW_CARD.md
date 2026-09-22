# WP-1b Review Card

- records_dir: `research\wp1b\calibration-3c-2026-09-22`
- evaluated_utc: 2026-09-22T02:17:49.730919+00:00
- calls: 18 | useful tool calls: 14 | rejected repeats: 1 (5.6% share) | successful reads: 4 | instrument errors: 0

## Per-call table

| task | k | action | arguments | outcome | error text | chars raw/shown | rejected |
|---|---|---|---|---|---|---|---|
| saleor-rc-349d46d906ad | 1 | search_text | query="celery" | ok |  | 3768/2000 | False |
| saleor-rc-349d46d906ad | 2 | read_file | path="saleor/celeryconf.py" | ok |  | 1305/1305 | False |
| saleor-rc-349d46d906ad | 3 | read_file | path="saleor/core/logging.py" | ok |  | 1779/1779 | False |
| saleor-rc-349d46d906ad | 4 | final | path="saleor/celeryconf.py,saleor/core/logging.py" | final |  | 0/0 | False |
| saleor-rc-b05633dae118 | 1 | search_text | query="shipping method currency" | ok |  | 0/0 | False |
| saleor-rc-b05633dae118 | 2 | search_text | query="external shipping method currency" | ok |  | 0/0 | False |
| saleor-rc-b05633dae118 | 3 | search_text | query="external shipping method" | ok |  | 753/753 | False |
| saleor-rc-b05633dae118 | 4 | search_text | query="currency" | ok |  | 4345/2000 | False |
| saleor-rc-b05633dae118 | 5 | search_text | query="external shipping methods" | ok |  | 753/753 | False |
| saleor-rc-b05633dae118 | 6 | search_text | query="external shipping method currency" | ok |  | 0/0 | False |
| saleor-rc-b05633dae118 | 7 | search_text | query="filter shipping methods" | ok |  | 695/695 | False |
| saleor-rc-b05633dae118 | 8 | final | path="saleor/checkout/fetch.py,saleor/graphql/checkout/types.py,saleor/webhook/transport/shipping.py" | final |  | 0/0 | False |
| saleor-rc-d52a55471bfc | 1 | search_text | query="ShippingMethodTranslationByIdAndLanguageCodeLoader" | ok |  | 211/211 | False |
| saleor-rc-d52a55471bfc | 2 | read_file | path="saleor/graphql/translations/dataloaders.py" | ok |  | 4512/2000 | False |
| saleor-rc-d52a55471bfc | 3 |  |  | rejected |  | 0/0 | True |
| saleor-rc-d52a55471bfc | 4 | read_file | path="saleor/graphql/translations/resolvers.py" | ok |  | 2511/2000 | False |
| saleor-rc-d52a55471bfc | 5 | search_text | query="ShippingMethodTranslationByIdAndLanguageCodeLoader" | ok |  | 211/211 | False |
| saleor-rc-d52a55471bfc | 6 | final | path="saleor/graphql/translations/dataloaders.py,saleor/graphql/translations/resolvers.py" | final |  | 0/0 | False |

## Per-task summary

| task | calls | useful | reads | rejects | longest run | instr err | empty | cost ratio | USD |
|---|---|---|---|---|---|---|---|---|---|
| saleor-rc-349d46d906ad | 4 | 3 | 2 | 0 | 0 | 0 | none | 0.331 | 0.017620 |
| saleor-rc-b05633dae118 | 8 | 7 | 0 | 0 | 0 | 0 | none | 0.645 | 0.032844 |
| saleor-rc-d52a55471bfc | 6 | 4 | 2 | 1 | 1 | 0 | none | 0.420 | 0.012740 |

## Anomaly flags

### BLOCKING
- none

### INFORMATIONAL
- I1 task saleor-rc-b05633dae118 has 0 read_file calls
- I2 task saleor-rc-b05633dae118 is search/list-only (0 reads, 7 tool calls)
- I3 task saleor-rc-349d46d906ad: 1 search-result-cap hit(s)
- I3 task saleor-rc-b05633dae118: 1 search-result-cap hit(s)

## Verdict: NO_BLOCKING_ANOMALIES
