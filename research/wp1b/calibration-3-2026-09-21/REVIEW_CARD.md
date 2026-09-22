# WP-1b Review Card

- records_dir: `research\wp1b\calibration-3-2026-09-21`
- evaluated_utc: 2026-09-22T00:17:19.780772+00:00
- calls: 24 | useful tool calls: 5 | rejected repeats: 7 (29.2% share) | successful reads: 0 | instrument errors: 9

## Per-call table

| task | k | action | arguments | outcome | error text | chars raw/shown | rejected |
|---|---|---|---|---|---|---|---|
| saleor-rc-349d46d906ad | 1 | search_text | query="celery" | ok |  | 485/485 | False |
| saleor-rc-349d46d906ad | 2 | read_file | path="saleor/celeryconf.py" | error | Max distinct files limit (30) reached | 37/37 | False |
| saleor-rc-349d46d906ad | 3 | search_text | query="celery" | ok |  | 485/485 | False |
| saleor-rc-349d46d906ad | 4 |  |  | rejected |  | 0/0 | True |
| saleor-rc-349d46d906ad | 5 |  |  | rejected |  | 0/0 | True |
| saleor-rc-349d46d906ad | 6 |  |  | rejected |  | 0/0 | True |
| saleor-rc-349d46d906ad | 7 |  |  | rejected |  | 0/0 | True |
| saleor-rc-349d46d906ad | 8 | final | path="saleor/celeryconf.py" | final |  | 0/0 | False |
| saleor-rc-b05633dae118 | 1 | search_text | query="external shipping methods" | error | Max distinct files limit (30) reached | 37/37 | False |
| saleor-rc-b05633dae118 | 2 | search_text | query="shipping method currency" | error | Max distinct files limit (30) reached | 37/37 | False |
| saleor-rc-b05633dae118 | 3 |  |  | rejected |  | 0/0 | True |
| saleor-rc-b05633dae118 | 4 | search_text | query="external shipping methods" | error | Max distinct files limit (30) reached | 37/37 | False |
| saleor-rc-b05633dae118 | 5 |  |  | rejected |  | 0/0 | True |
| saleor-rc-b05633dae118 | 6 | list_files | path="saleor/shipping" | ok |  | 195/195 | False |
| saleor-rc-b05633dae118 | 7 | read_file | path="saleor/shipping/interface.py" | error | Max distinct files limit (30) reached | 37/37 | False |
| saleor-rc-b05633dae118 | 8 | final | path="saleor/shipping/interface.py,saleor/shipping/models.py,saleor/shipping/utils.py" | final |  | 0/0 | False |
| saleor-rc-d52a55471bfc | 1 | list_files | path="saleor/shipping" | ok |  | 195/195 | False |
| saleor-rc-d52a55471bfc | 2 | list_files | path="saleor/graphql/shipping/" | ok |  | 495/495 | False |
| saleor-rc-d52a55471bfc | 3 | search_text | query="ShippingMethodTranslationByIdAndLanguageCodeLoader" | error | Max distinct files limit (30) reached | 37/37 | False |
| saleor-rc-d52a55471bfc | 4 |  |  | rejected |  | 0/0 | True |
| saleor-rc-d52a55471bfc | 5 | search_text | query="ShippingMethodTranslation" | error | Max distinct files limit (30) reached | 37/37 | False |
| saleor-rc-d52a55471bfc | 6 | search_text | query="ShippingMethodTranslationByIdAndLanguageCodeLoader" | error | Max distinct files limit (30) reached | 37/37 | False |
| saleor-rc-d52a55471bfc | 7 | search_text | query="ShippingMethodTranslation" | error | Max distinct files limit (30) reached | 37/37 | False |
| saleor-rc-d52a55471bfc | 8 | final | path="saleor/graphql/shipping/dataloaders.py,saleor/graphql/shipping/types.py,saleor/shipping/models.py" | final |  | 0/0 | False |

## Per-task summary

| task | calls | useful | reads | rejects | longest run | instr err | empty | cost ratio | USD |
|---|---|---|---|---|---|---|---|---|---|
| saleor-rc-349d46d906ad | 8 | 2 | 0 | 4 | 4 | 1 | none | 0.636 | 0.033858 |
| saleor-rc-b05633dae118 | 8 | 1 | 0 | 2 | 1 | 4 | none | 0.617 | 0.031420 |
| saleor-rc-d52a55471bfc | 8 | 2 | 0 | 1 | 1 | 4 | none | 0.523 | 0.015865 |

## Anomaly flags

### BLOCKING
- **B1** 9 instrument-class tool errors across the run
- **B2** run(s) of >= 3 consecutive identical rejected requests: {'saleor-rc-349d46d906ad': 4, 'saleor-rc-b05633dae118': 1, 'saleor-rc-d52a55471bfc': 1}
- **B3** zero successful read_file across ALL tasks in the run
- **B5** calibration gate FAIL on check(s): ['CG-10', 'CG-11', 'CG-12']

### INFORMATIONAL
- I1 task saleor-rc-349d46d906ad has 0 read_file calls
- I2 task saleor-rc-349d46d906ad is search/list-only (0 reads, 2 tool calls)
- I1 task saleor-rc-b05633dae118 has 0 read_file calls
- I2 task saleor-rc-b05633dae118 is search/list-only (0 reads, 1 tool calls)
- I1 task saleor-rc-d52a55471bfc has 0 read_file calls
- I2 task saleor-rc-d52a55471bfc is search/list-only (0 reads, 2 tool calls)
- I4 identical normalized tool output/error repeated 9 times: 'max distinct files limit (30) reached'
- I5 task saleor-rc-349d46d906ad: prompt growth < 25 tokens on 4 of 7 consecutive-call deltas
- I5 task saleor-rc-b05633dae118: prompt growth < 25 tokens on 5 of 7 consecutive-call deltas
- I5 task saleor-rc-d52a55471bfc: prompt growth < 25 tokens on 4 of 7 consecutive-call deltas

## Verdict: BLOCKED
