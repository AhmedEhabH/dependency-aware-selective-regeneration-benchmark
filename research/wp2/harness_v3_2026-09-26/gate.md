# Mission-10B Phase-4 Mechanical Gate

TOKEN = **HARNESS_V3_RECOMMENDED**
AUTO-CONTINUE to Phase 5 = **True**

| criterion | PASS | detail |
|:---|:---|:---|
| MATERIALITY | True | 2592/3647 = 71.1% (>= 20%) |
| RECOVERY | True | 667 V2-invalid nodes recovered to valid oracle class |
| FIX_EFFICACY | True | 0 EMFILE hits across all V3 probe junit files (66 files, 4 tasks) - EMFILE fully eliminated; Phase-1C controlled repro: A reproduces EMFILE at nofile=1024, B eliminates at 65536 (EFFICACY TRUE) |
| SAFETY | True | new-infra 0, clock-blocked 0, integrity True, regressions 0, fix-efficacy True |
| REGRESSIONS (S2') | True | count = 0 |
| INTEGRITY | True | {'saleor-rc-c3b9e396b07d': True, 'saleor-rc-e25cf9b4a837': True, 'saleor-rc-74538ea00ce9': True, 'saleor-rc-8f76ddc6267f': True} |

V2_DEFECT_CORRECTIONS = 1
