# Controller STOP — M16_ADAPTER_FAIL

- plan: WP2_M16_V1_DRYRUN_R2A (sha d188d989df64)
- phase: R02_ADAPTER_VERIFY
- utc: 2026-10-02T13:06:19Z
- resumable: False

## Detail

```
exit mapped to STOP:M16_ADAPTER_FAIL
--- last log: logs/controller/20261002T155557_R02_ADAPTER_VERIFY.log ---
$ C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_m16_run.py adapter-verify
M16_ADAPTER_FAIL R2 fail-closed: 4 violation(s): ['ENG_IDENTITY:saleor-rc-939093a9c65c:INSTALL_MODE_DIFFERS_FROM_RECORD', 'ENG_IDENTITY:saleor-rc-a8e6a4dd55fe:INSTALL_MODE_DIFFERS_FROM_RECORD', 'ENG_IDENTITY:saleor-rc-f73c4e95c828:INSTALL_MODE_DIFFERS_FROM_RECORD']
```

## Phase status

- R00_KIT_SELFTEST: PASS
- R01_GUARD: PASS
- R02_ADAPTER_VERIFY: RUNNING
- R03_DRYRUN_SELECT: PENDING
- R04_DRYRUN_EXECUTE: PENDING
- R05_RESOURCE_GATE: PENDING

## Next

Not resumable automatically: a human decision is required, recorded with `python scripts/wp2_ctl_v224.py ack-stop --plan <PLAN> --token <TOKEN> --note ...`.
