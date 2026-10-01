# WP2 M15-R V1 - S1 OPWS result (Pilot-B, descriptive)

Token: **M15R_OPWS_COMPLETE**. Members: 10. Primary endpoint: OPWS_ROBUST (strict co-reported).

| Selector | OPWS robust | OPWS strict | empty P_S | NO_SCOPE | mean P | mean R | mean F1 | mean files | mean scope chars | mean G0 prompt chars |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GOLD_HARD | 10/10 | 10/10 | 0 | 0 | 1.0 | 0.908333 | 0.945714 | 2.3 | 63220.6 | 64822.1 |
| RMCSS_HARD | 3/10 | 3/10 | 3 | 0 | 0.255952 | 0.3 | 0.229444 | 4.5 | 75469.1 | 77368.8 |
| AGENT_HARD:r1 | 2/10 | 2/10 | 4 | 1 | 0.37 | 0.225 | 0.267381 | 2.1 | 28812.1 | 30259.1 |
| AGENT_HARD:r2 | 3/10 | 3/10 | 3 | 1 | 0.408333 | 0.308333 | 0.310714 | 2.1 | 34651.5 | 36097.3 |
| AGENT_HARD:r3 | 2/10 | 2/10 | 6 | 0 | 0.316667 | 0.141667 | 0.185714 | 1.9 | 26378.5 | 27936.4 |

Agent replicate agreement on OPWS_ROBUST: 7/10 tasks; mean pairwise Jaccard of Agent editable sets: 0.5.
Paired RM-CSS vs Agent (per task): {"RMCSS_vs_AGENT_HARD:r1": {"rmcss_only": 1, "agent_only": 0, "ties": 9}, "RMCSS_vs_AGENT_HARD:r2": {"rmcss_only": 0, "agent_only": 0, "ties": 10}, "RMCSS_vs_AGENT_HARD:r3": {"rmcss_only": 2, "agent_only": 1, "ties": 7}, "RMCSS_vs_AGENT_MAJORITY": {"rmcss_only": 1, "agent_only": 0, "ties": 9}}.
Strict/robust discordance among evaluated OPWS states: 0/34.

OPWS asks whether the developer's own patch, restricted to the files a selector allowed, still passes the hidden tests. It is independent of any generator, does not penalise over-selection (cost is reported separately), and credits no alternative fix. Gold-changed files follow the frozen GOLD_HARD definition (modified/deleted non-test files; added and renamed files are excluded, as in Smoke, Pilot-A and M14R). n <= 10 Pilot-B tasks: descriptive only, no superiority claim.
