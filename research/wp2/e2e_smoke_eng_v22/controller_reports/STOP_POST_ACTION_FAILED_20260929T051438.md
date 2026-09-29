# Controller STOP — POST_ACTION_FAILED

- plan: WP2_E2E_SMOKE_ENG_V22 (sha ba788149dcc9)
- phase: P05_FREEZE
- utc: 2026-09-29T02:14:38Z
- resumable: False

## Detail

```
{'type': 'tag', 'name': 'wp2-e2e-smoke-eng-v22-freeze-{date}', 'message': 'E2E Smoke ENG v2.2 freeze (controller)'}: push of tag failed
```

## Phase status

- P00_KIT_SELFTEST: PASS
- P01_CLOSE_V21: PASS
- P02_DOCTOR_OFFLINE: PASS
- P03_ENV_CANARY: PASS
- P04_DOCTOR_PAID: PASS
- P05_FREEZE: RUNNING
- P06_GEN_MAIN: PENDING
- P07_GEN_VARIANCE: PENDING
- P08_GENERATION_FREEZE: PENDING
- P09_EVAL_PLAN: PENDING
- P10_EVALUATE: PENDING
- P11_SUMMARY: PENDING
- P12_CLOSE: PENDING

## Next

Not resumable automatically: a human decision is required, recorded with `python scripts/wp2_ctl.py ack-stop --token <TOKEN> --note ...`.
