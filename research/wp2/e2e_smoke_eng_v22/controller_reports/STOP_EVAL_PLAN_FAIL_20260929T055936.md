# Controller STOP — EVAL_PLAN_FAIL

- plan: WP2_E2E_SMOKE_ENG_V22 (sha ba788149dcc9)
- phase: P09_EVAL_PLAN
- utc: 2026-09-29T02:59:36Z
- resumable: False

## Detail

```
command failed
```

## Phase status

- P00_KIT_SELFTEST: PASS
- P01_CLOSE_V21: PASS
- P02_DOCTOR_OFFLINE: PASS
- P03_ENV_CANARY: PASS
- P04_DOCTOR_PAID: PASS
- P05_FREEZE: PASS
- P06_GEN_MAIN: PASS
- P07_GEN_VARIANCE: PASS
- P08_GENERATION_FREEZE: PASS
- P09_EVAL_PLAN: RUNNING
- P10_EVALUATE: PENDING
- P11_SUMMARY: PENDING
- P12_CLOSE: PENDING

## Next

Not resumable automatically: a human decision is required, recorded with `python scripts/wp2_ctl.py ack-stop --token <TOKEN> --note ...`.
