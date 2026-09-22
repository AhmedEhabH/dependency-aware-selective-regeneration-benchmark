# WP-1b Review Card

- records_dir: `research\wp1b\calibration-3b-2026-09-21`
- evaluated_utc: 2026-09-22T00:16:19.872660+00:00
- calls: 21 | useful tool calls: 7 | rejected repeats: 11 (52.4% share) | successful reads: 3 | instrument errors: 0

## Per-call table

| task | k | action | arguments | outcome | error text | chars raw/shown | rejected |
|---|---|---|---|---|---|---|---|
| saleor-rc-349d46d906ad | 1 | read_file | path="saleor/celeryconf.py" | ok |  | 1305/1305 | False |
| saleor-rc-349d46d906ad | 2 | read_file | path="saleor/core/logging.py" | ok |  | 1779/1779 | False |
| saleor-rc-349d46d906ad | 3 |  |  | rejected |  | 0/0 | True |
| saleor-rc-349d46d906ad | 4 | search_text | query="CELERY_LOGGER_NAME" | ok |  | 134/134 | False |
| saleor-rc-349d46d906ad | 5 | final | path="saleor/celeryconf.py,saleor/core/logging.py" | final |  | 0/0 | False |
| saleor-rc-b05633dae118 | 1 | search_text | query="external shipping methods" | ok |  | 753/753 | False |
| saleor-rc-b05633dae118 | 2 |  |  | rejected |  | 0/0 | True |
| saleor-rc-b05633dae118 | 3 |  |  | rejected |  | 0/0 | True |
| saleor-rc-b05633dae118 | 4 |  |  | rejected |  | 0/0 | True |
| saleor-rc-b05633dae118 | 5 |  |  | rejected |  | 0/0 | True |
| saleor-rc-b05633dae118 | 6 |  |  | rejected |  | 0/0 | True |
| saleor-rc-b05633dae118 | 7 |  |  | rejected |  | 0/0 | True |
| saleor-rc-b05633dae118 | 8 | final | path="saleor/graphql/checkout/types.py,saleor/graphql/webhook/enums.py" | final |  | 0/0 | False |
| saleor-rc-d52a55471bfc | 1 | search_text | query="ShippingMethodTranslation" | ok |  | 824/824 | False |
| saleor-rc-d52a55471bfc | 2 | search_text | query="ShippingMethodTranslationByIdAndLanguageCodeLoader" | ok |  | 211/211 | False |
| saleor-rc-d52a55471bfc | 3 | read_file | path="saleor/graphql/translations/dataloaders.py" | ok |  | 4512/2000 | False |
| saleor-rc-d52a55471bfc | 4 |  |  | rejected |  | 0/0 | True |
| saleor-rc-d52a55471bfc | 5 |  |  | rejected |  | 0/0 | True |
| saleor-rc-d52a55471bfc | 6 |  |  | rejected |  | 0/0 | True |
| saleor-rc-d52a55471bfc | 7 |  |  | rejected |  | 0/0 | True |
| saleor-rc-d52a55471bfc | 8 | final | path="saleor/graphql/translations/dataloaders.py,saleor/graphql/translations/resolvers.py,saleor/shipping/models.py" | final |  | 0/0 | False |

## Per-task summary

| task | calls | useful | reads | rejects | longest run | instr err | empty | cost ratio | USD |
|---|---|---|---|---|---|---|---|---|---|
| saleor-rc-349d46d906ad | 5 | 3 | 2 | 1 | 1 | 0 | none | 0.405 | 0.021543 |
| saleor-rc-b05633dae118 | 8 | 1 | 0 | 6 | 6 | 0 | none | 0.626 | 0.031885 |
| saleor-rc-d52a55471bfc | 8 | 3 | 1 | 4 | 4 | 0 | none | 0.547 | 0.016599 |

## Anomaly flags

### BLOCKING
- **B2** run(s) of >= 3 consecutive identical rejected requests: {'saleor-rc-349d46d906ad': 1, 'saleor-rc-b05633dae118': 6, 'saleor-rc-d52a55471bfc': 4}
- **B5** calibration gate FAIL on check(s): ['CG-12']

### INFORMATIONAL
- I1 task saleor-rc-b05633dae118 has 0 read_file calls
- I2 task saleor-rc-b05633dae118 is search/list-only (0 reads, 1 tool calls)
- I5 task saleor-rc-349d46d906ad: prompt growth < 25 tokens on 1 of 4 consecutive-call deltas
- I5 task saleor-rc-b05633dae118: prompt growth < 25 tokens on 5 of 7 consecutive-call deltas
- I5 task saleor-rc-d52a55471bfc: prompt growth < 25 tokens on 3 of 7 consecutive-call deltas

## Verdict: BLOCKED
