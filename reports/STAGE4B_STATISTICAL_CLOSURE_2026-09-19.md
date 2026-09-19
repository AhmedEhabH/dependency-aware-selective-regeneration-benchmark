# Stage 4b Statistical Closure (POST-HOC DESCRIPTIVE DEVELOPMENT ANALYSIS)

**Date:** 2026-09-19  **Reference budget:** B=5  **Resamples:** 10000 (task-paired, fixed seed 20260919)

**The preregistered Stage-4b verdict is UNCHANGED and immutable: `PRECISION_SAFE_ACCEPTANCE_FAIL` (P67).** This document adds descriptive uncertainty analysis ONLY — it does NOT reopen or reinterpret the frozen gate.

**Metric definitions (used in every relevant report from 2026-09-19 on):**

```
Precision            P  = TP / (TP + FP)
Recall               R  = TP / (TP + FN)
False Negative Rate  FNR = FN / (TP + FN) = 1 - R
F1                   F1 = 2TP / (2TP + FP + FN)
Candidate precision  = correct recovered omitted positives / all accepted recovery candidates
ORR per task i       ORR_i = recovered omitted positives_i / omitted positives_i
                        (0 when the task has no omitted positives — frozen macro convention)
Macro ORR            mean_i(ORR_i)
95% paired bootstrap CI: Delta_b = Metric_B_b - Metric_A_b;
                        CI95 = [quantile_2.5%(Delta), quantile_97.5%(Delta)];
                        bootstrap unit = TASK (never individual files).
```

## djangocms DEV — Stage 4b pilot @B=5 (n = 30 tasks, paired)

### Pooled file-level confusion per arm

| Arm | TP | FP | FN | Precision | Recall | F1 | FNR |
|---|---:|---:|---:|---:|---:|---:|---:|
| A (Route-B verifier) | 21 | 84 | 67 | 0.2000 | 0.2386 | 0.2176 | 0.7614 |
| B (RANK->VERIFY) | 22 | 59 | 66 | 0.2716 | 0.2500 | 0.2604 | 0.7500 |

### Arm B minus Arm A — point estimates and 95% paired-task-bootstrap CIs

| Metric | A | B | delta (abs) | delta (rel) | CI95 lower | CI95 upper | excludes 0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| macro_orr | 0.2225 | 0.1523 | -0.0702 | -31.56% | -0.1958 | 0.0339 | False |
| final_precision | 0.2000 | 0.2716 | +0.0716 | 35.80% | 0.0089 | 0.1514 | True |
| final_recall | 0.2386 | 0.2500 | +0.0114 | 4.76% | -0.0556 | 0.0625 | False |
| final_f1 | 0.2176 | 0.2604 | +0.0427 | 19.64% | -0.0132 | 0.0955 | False |
| final_fnr | 0.7614 | 0.7500 | -0.0114 | -1.49% | -0.0625 | 0.0556 | False |
| candidate_precision | 0.1406 | 0.2500 | +0.1094 | 77.78% | -0.0047 | 0.2474 | False |

## saleor DEV — Stage 4b pilot @B=5 (n = 30 tasks, paired)

### Pooled file-level confusion per arm

| Arm | TP | FP | FN | Precision | Recall | F1 | FNR |
|---|---:|---:|---:|---:|---:|---:|---:|
| A (Route-B verifier) | 17 | 76 | 85 | 0.1828 | 0.1667 | 0.1744 | 0.8333 |
| B (RANK->VERIFY) | 21 | 90 | 81 | 0.1892 | 0.2059 | 0.1972 | 0.7941 |

### Arm B minus Arm A — point estimates and 95% paired-task-bootstrap CIs

| Metric | A | B | delta (abs) | delta (rel) | CI95 lower | CI95 upper | excludes 0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| macro_orr | 0.1278 | 0.2029 | +0.0751 | 58.80% | 0.0037 | 0.1751 | True |
| final_precision | 0.1828 | 0.1892 | +0.0064 | 3.50% | -0.0400 | 0.0573 | False |
| final_recall | 0.1667 | 0.2059 | +0.0392 | 23.53% | 0.0093 | 0.0759 | True |
| final_f1 | 0.1744 | 0.1972 | +0.0228 | 13.09% | -0.0123 | 0.0604 | False |
| final_fnr | 0.8333 | 0.7941 | -0.0392 | -4.71% | -0.0759 | -0.0093 | True |
| candidate_precision | 0.0882 | 0.1163 | +0.0280 | 31.78% | -0.0209 | 0.0851 | False |

## The djangoCMS phenomenon: pooled TP/FP/FN improve while Macro ORR declines — why

**Observed fact (frozen pilot):** on djangoCMS @B=5 the Arm-B final set has *more* TP, *fewer* FP and *fewer* FN than Arm A (pooled P/R/F1/FNR all improve), yet the Arm-B Macro ORR (0.1523) is *below* Arm A (0.2225). Macro ORR and pooled Recall/F1 can move in opposite directions; this is expected under the definitions:

1. **Macro ORR is a per-task ratio averaged over tasks; pooled Recall is a   global ratio over pooled positives.**
   - ORR_i = recovered_i / missed_i. Tasks with a large missed set `missed_i`     contribute little to the macro; tasks with a tiny missed set (e.g. a     single FN, `missed_i = 1`) dominate the macro when the arm recovers     that single FN. Arm A recovered the single FN on **three M=1 tasks**;     Arm B instead approved a *different* non-FN candidate on those tasks,     producing three `delta_i = -1.0` per-task ORR deltas that dominate the     macro average.
   - Pooled Recall pools *all* proxy positives first and divides the pooled     recovered count. A task with a large FN set carries proportionally more     weight there, so recovering a few positives on large-FN tasks moves     pooled Recall even when it does not fix the small-M tasks.
2. **The FP/TP composition differs.** The conservative verifier in Arm B   accepts fewer candidates overall (40 vs 64 selected on djangoCMS @B=5),   cutting the FP tail (candidate precision 0.1406 -> 0.2500) while still   recovering the same net number of FNs (9 -> 10). Fewer FPs and more TPs   at the pooled level directly raise P, R, F1 and lower FNR.
3. **Mechanism verification (from the raw task-level record).** The per-task   deltas at B=5 (djangoCMS) are dominated by the M=1 recovery pattern:

| case_id (M=1) | Arm A recovered | Arm B recovered | Arm A additions | Arm B additions |
|---|---:|---:|---|---|---|
| djangocms-rc-06ecf3a8e8de | 1 | 0 | cms/models/contentmodels.py,cms/utils/helpers.py | cms/models/pagemodel.py |
| djangocms-rc-087fa3ec709a | 0 | 0 | cms/admin/__init__.py,cms/admin/forms.py,cms/admin/pageadmin.py | - |
| djangocms-rc-302c1b5cc51e | 0 | 0 | cms/templatetags/cms_tags.py,cms/utils/i18n.py,menus/templatetags/menu_tags.py | cms/templatetags/cms_tags.py |
| djangocms-rc-3ba27f11960b | 0 | 0 | - | - |
| djangocms-rc-463294977e97 | 0 | 0 | cms/middleware/page.py,cms/page_rendering.py | - |
| djangocms-rc-475120cf18ce | 0 | 0 | cms/admin/change_list.py,cms/admin/forms.py,cms/admin/pageadmin.py,cms/admin/permissionadmin.py | - |
| djangocms-rc-4777a022c421 | 0 | 0 | cms/api.py,cms/extensions/models.py,cms/utils/page.py | cms/models/pagemodel.py |
| djangocms-rc-5ff38b521274 | 1 | 1 | cms/page_rendering.py,cms/templatetags/cms_alias_tags.py,cms/utils/plugins.py,cms/views.py | cms/templatetags/cms_tags.py,cms/utils/plugins.py |
| djangocms-rc-7a6761bfbdf8 | 0 | 0 | cms/utils/compat/dj.py | cms/south_migrations/0025_placeholder_migration.py,cms/south_migrations/0026_finish_placeholder_migration.py |
| djangocms-rc-829f7e224887 | 1 | 0 | cms/cache/page.py,cms/menu_bases.py,menus/models.py | cms/cache/page.py |
| djangocms-rc-9488d4017519 | 1 | 1 | cms/admin/forms.py,cms/utils/page_resolver.py,cms/utils/urlutils.py | cms/utils/urlutils.py |
| djangocms-rc-a7df58dc5ff3 | 1 | 1 | cms/__init__.py,cms/utils/conf.py,cms/utils/request_ip_resolvers.py | cms/utils/conf.py |
| djangocms-rc-f96c80357c71 | 1 | 0 | cms/cms_plugins.py,cms/plugin_base.py,cms/plugin_pool.py | cms/plugin_pool.py |

4. **Conclusion.** The decline in Macro ORR on djangoCMS is a *macro-vs-pooled   weighting artifact of the conservative verifier over-rejecting the easy   single-FN recoveries*, not a sign that the Arm-B final set is worse at the   file level. The preregistered gate (P67) used Macro ORR as a decisive   criterion on BOTH repos, so the pilot correctly FAILED under its own   protocol. This explanation is POST-HOC and descriptive; it does not alter
   `PRECISION_SAFE_ACCEPTANCE_FAIL`.
