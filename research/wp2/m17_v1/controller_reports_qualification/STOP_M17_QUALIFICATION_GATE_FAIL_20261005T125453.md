# Controller STOP — M17_QUALIFICATION_GATE_FAIL

- plan: WP2_M17_V1_QUALIFICATION (sha 01cff0ff8ec7)
- phase: Q05_QUALIFICATION_GATE
- utc: 2026-10-05T09:54:53Z
- resumable: False

## Detail

```
exit mapped to STOP:M17_QUALIFICATION_GATE_FAIL
--- last log: logs/controller/20261005T125452_Q05_QUALIFICATION_GATE.log ---
$ C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_m17_exec.py qualification-gate
M17_QG_FAIL {"done_at_least_10":false,"done_each_represented_era":true,"firewall_clean":true,"infra_unresolved_le_1":true,"no_missing_fixture_or_socket_blocked":true,"projected_c_free_ge_25_gib":false,"r1_triplets_complete":true,"real_executor_only":true,"records_12_of_12":true,"v2_primary_f2p_retention_at_least_half":true}
```

## Phase status

- Q00_KIT_SELFTEST: PASS
- Q01_GUARD: PASS
- Q02_ADAPTER_VERIFY: PASS
- Q03_QUALIFICATION_RUN: PASS
- Q04_QUALIFICATION_REPORT: PASS
- Q05_QUALIFICATION_GATE: RUNNING
- Q06_RESOURCE_PROJECTION: PENDING

## Next

Not resumable automatically: a human decision is required, recorded with `python scripts/wp2_ctl_v224.py ack-stop --plan <PLAN> --token <TOKEN> --note ...`.
