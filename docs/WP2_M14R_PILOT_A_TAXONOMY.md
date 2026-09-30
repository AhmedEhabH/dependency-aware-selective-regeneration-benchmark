# Pilot-A failure taxonomy (descriptive; changes no Pilot-A gate)

Precedence: FORMAT_INVALID > NO_SCOPE > NO_OP > PATCH_STARTUP_FAILURE > RESOLVED > F2P_PASS_PRESERVATION_FAIL > PARTIAL_F2P_PROGRESS > ZERO_F2P_PROGRESS

| Task | Arm | Rep | Label | Detail | F2P nodes 3/3 | S det/int | U det/int |
|---|---|---|---|---|---|---|---|
| saleor-rc-012472eb8482 | GOLD_HARD | r1 | FORMAT_INVALID | INVALID_AFTER_REPAIR | - | - | - |
| saleor-rc-012472eb8482 | GOLD_HARD | r2 | ZERO_F2P_PROGRESS |  | 0/5 | 0/0 | 0/0 |
| saleor-rc-5b0e5206c5fd | GOLD_HARD | r1 | PARTIAL_F2P_PROGRESS | +DETERMINISTIC_PRESERVATION_BREAK | 3/8 | 2/0 | 0/0 |
| saleor-rc-5b0e5206c5fd | GOLD_HARD | r2 | ZERO_F2P_PROGRESS |  | 0/8 | 0/0 | 0/0 |
| saleor-rc-6459dd2d9135 | GOLD_HARD | r1 | PARTIAL_F2P_PROGRESS |  | 1/2 | 0/0 | 0/0 |
| saleor-rc-6459dd2d9135 | GOLD_HARD | r2 | PARTIAL_F2P_PROGRESS |  | 1/2 | 0/0 | 0/0 |
| saleor-rc-6f37bd256e12 | GOLD_HARD | r1 | PARTIAL_F2P_PROGRESS | +DETERMINISTIC_PRESERVATION_BREAK | 61/62 | 0/0 | 1/0 |
| saleor-rc-6f37bd256e12 | GOLD_HARD | r2 | PARTIAL_F2P_PROGRESS |  | 61/62 | 0/0 | 0/0 |
| saleor-rc-a3c478408852 | GOLD_HARD | r1 | ZERO_F2P_PROGRESS |  | 0/2 | 0/0 | 0/0 |
| saleor-rc-a3c478408852 | GOLD_HARD | r2 | ZERO_F2P_PROGRESS |  | 0/2 | 0/0 | 0/0 |
| saleor-rc-a91ea48a60a7 | GOLD_HARD | r1 | FORMAT_INVALID | INVALID_AFTER_REPAIR | - | - | - |
| saleor-rc-a91ea48a60a7 | GOLD_HARD | r2 | FORMAT_INVALID | INVALID_AFTER_REPAIR | - | - | - |
| saleor-rc-b14def73518c | GOLD_HARD | r1 | PATCH_STARTUP_FAILURE |  | 0/1 | 92/0 | 200/0 |
| saleor-rc-b14def73518c | GOLD_HARD | r2 | PATCH_STARTUP_FAILURE |  | 0/1 | 92/0 | 200/0 |
| saleor-rc-b497f8d82426 | GOLD_HARD | r1 | FORMAT_INVALID | INVALID_AFTER_REPAIR | - | - | - |
| saleor-rc-b497f8d82426 | GOLD_HARD | r2 | ZERO_F2P_PROGRESS |  | 0/1 | 0/0 | 0/0 |
| saleor-rc-bbba01a02725 | GOLD_HARD | r1 | ZERO_F2P_PROGRESS | +DETERMINISTIC_PRESERVATION_BREAK | 0/101 | 6/0 | 1/0 |
| saleor-rc-bbba01a02725 | GOLD_HARD | r2 | FORMAT_INVALID | INVALID_AFTER_REPAIR | - | - | - |
| saleor-rc-d3847fa5f518 | GOLD_HARD | r1 | F2P_PASS_PRESERVATION_FAIL | PRESERVATION_INTERMITTENT_ONLY | 1/1 | 0/1 | 0/1 |
| saleor-rc-d3847fa5f518 | GOLD_HARD | r2 | F2P_PASS_PRESERVATION_FAIL | PRESERVATION_INTERMITTENT_ONLY | 1/1 | 0/1 | 0/0 |
| saleor-rc-012472eb8482 | PLACEBO_HARD | r1 | ZERO_F2P_PROGRESS |  | 0/5 | 0/0 | 0/0 |
| saleor-rc-012472eb8482 | PLACEBO_HARD | r2 | NO_OP |  | 0/5 | 0/0 | 0/0 |
| saleor-rc-5b0e5206c5fd | PLACEBO_HARD | r1 | NO_OP |  | 0/8 | 0/0 | 0/0 |
| saleor-rc-5b0e5206c5fd | PLACEBO_HARD | r2 | NO_OP |  | 0/8 | 0/0 | 0/0 |
| saleor-rc-6459dd2d9135 | PLACEBO_HARD | r1 | NO_OP |  | 0/2 | 0/0 | 0/0 |
| saleor-rc-6459dd2d9135 | PLACEBO_HARD | r2 | ZERO_F2P_PROGRESS |  | 0/2 | 0/0 | 0/0 |
| saleor-rc-6f37bd256e12 | PLACEBO_HARD | r1 | FORMAT_INVALID | INVALID_AFTER_REPAIR | - | - | - |
| saleor-rc-6f37bd256e12 | PLACEBO_HARD | r2 | FORMAT_INVALID | INVALID_AFTER_REPAIR | - | - | - |
| saleor-rc-a3c478408852 | PLACEBO_HARD | r1 | ZERO_F2P_PROGRESS |  | 0/2 | 0/0 | 0/0 |
| saleor-rc-a3c478408852 | PLACEBO_HARD | r2 | ZERO_F2P_PROGRESS |  | 0/2 | 0/0 | 0/0 |
| saleor-rc-a91ea48a60a7 | PLACEBO_HARD | r1 | FORMAT_INVALID | INVALID_AFTER_REPAIR | - | - | - |
| saleor-rc-a91ea48a60a7 | PLACEBO_HARD | r2 | NO_OP |  | 0/2 | 0/0 | 0/0 |
| saleor-rc-b14def73518c | PLACEBO_HARD | r1 | NO_OP |  | 0/1 | 0/1 | 0/0 |
| saleor-rc-b14def73518c | PLACEBO_HARD | r2 | NO_OP |  | 0/1 | 0/1 | 0/0 |
| saleor-rc-b497f8d82426 | PLACEBO_HARD | r1 | NO_OP |  | 0/1 | 0/0 | 0/0 |
| saleor-rc-b497f8d82426 | PLACEBO_HARD | r2 | NO_OP |  | 0/1 | 0/0 | 0/0 |
| saleor-rc-bbba01a02725 | PLACEBO_HARD | r1 | ZERO_F2P_PROGRESS |  | 0/101 | 0/0 | 0/0 |
| saleor-rc-bbba01a02725 | PLACEBO_HARD | r2 | ZERO_F2P_PROGRESS |  | 0/101 | 0/0 | 0/0 |
| saleor-rc-d3847fa5f518 | PLACEBO_HARD | r1 | NO_OP |  | 0/1 | 0/0 | 0/1 |
| saleor-rc-d3847fa5f518 | PLACEBO_HARD | r2 | ZERO_F2P_PROGRESS |  | 0/1 | 0/0 | 0/0 |

Aggregate: {"GOLD_HARD": {"F2P_PASS_PRESERVATION_FAIL": 2, "FORMAT_INVALID": 5, "PARTIAL_F2P_PROGRESS": 5, "PATCH_STARTUP_FAILURE": 2, "ZERO_F2P_PROGRESS": 6}, "PLACEBO_HARD": {"FORMAT_INVALID": 3, "NO_OP": 10, "ZERO_F2P_PROGRESS": 7}}
Descriptive robust-preservation RESOLVED: {"GOLD_HARD": 2, "PLACEBO_HARD": 0}
