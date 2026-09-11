# Qwen3-Coder-30B-A3B-Instruct Cross-Model Agreement (Sparse-v2)

**DESCRIPTIVE ONLY - no equivalence/significance claim.**

Method: for each scenario, ALL valid historical Qwen3-Coder-480B-A35B-Instruct (OpenRouter slug `qwen/qwen3-coder`, OpenRouter / DeepInfra) Sparse-v2 runs x ALL valid new Qwen3-Coder-30B-A3B-Instruct (OpenRouter slug `qwen/qwen3-coder-30b-a3b-instruct`, OpenRouter / SiliconFlow) Sparse-v2 runs, full cross-product Jaccard of selected-file sets. Runs are NOT paired by repetition.

| Scenario | Hist valid | New valid | Pairs | Mean | Median | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| djangocms-external-validity-002 | 4 | 5 | 20 | 0.542 | 0.417 | 0.333 | 1.000 |
| djangocms-external-validity-004 | 5 | 4 | 20 | 0.499 | 0.500 | 0.333 | 0.667 |
| djangocms-external-validity-005 | 5 | 5 | 25 | 0.777 | 0.833 | 0.500 | 1.000 |
| djangocms-external-validity-006 | 5 | 5 | 25 | 0.353 | 0.333 | 0.143 | 0.750 |
| djangocms-external-validity-007 | 5 | 4 | 20 | 0.479 | 0.500 | 0.091 | 0.857 |
| djangocms-external-validity-008 | 5 | 5 | 25 | 0.307 | 0.300 | 0.182 | 0.500 |
| **Overall** | - | - | **135** | **0.491** | **0.429** | **0.091** | **1.000** |

## Per-file selection frequencies

### djangocms-external-validity-002

| File | Hist freq | New freq |
| --- | ---: | ---: |
| `cms/api.py` | 4 | 5 |
| `cms/models/contentmodels.py` | 3 | 0 |
| `cms/utils/page.py` | 2 | 0 |

### djangocms-external-validity-004

| File | Hist freq | New freq |
| --- | ---: | ---: |
| `cms/admin/__init__.py` | 0 | 1 |
| `cms/admin/forms.py` | 2 | 4 |
| `cms/admin/pageadmin.py` | 5 | 4 |
| `cms/api.py` | 5 | 4 |
| `cms/models/contentmodels.py` | 5 | 4 |
| `cms/models/managers.py` | 2 | 0 |
| `cms/templatetags/cms_static.py` | 2 | 0 |
| `cms/utils/urlutils.py` | 0 | 4 |
| `cms/views.py` | 5 | 0 |

### djangocms-external-validity-005

| File | Hist freq | New freq |
| --- | ---: | ---: |
| `cms/admin/pageadmin.py` | 5 | 5 |
| `cms/admin/permissionadmin.py` | 5 | 5 |
| `cms/cms_toolbars.py` | 5 | 4 |
| `cms/models/permissionmodels.py` | 5 | 5 |
| `cms/page_rendering.py` | 0 | 1 |
| `cms/toolbar/toolbar.py` | 0 | 1 |
| `cms/utils/page.py` | 2 | 0 |
| `cms/utils/page_permissions.py` | 4 | 5 |
| `cms/utils/permissions.py` | 1 | 0 |

### djangocms-external-validity-006

| File | Hist freq | New freq |
| --- | ---: | ---: |
| `cms/admin/forms.py` | 5 | 5 |
| `cms/admin/placeholderadmin.py` | 2 | 0 |
| `cms/admin/utils.py` | 0 | 4 |
| `cms/models/permissionmodels.py` | 0 | 2 |
| `cms/models/placeholderpluginmodel.py` | 0 | 4 |
| `cms/models/pluginmodel.py` | 5 | 1 |
| `cms/plugin_rendering.py` | 5 | 3 |
| `cms/utils/placeholder.py` | 1 | 0 |

### djangocms-external-validity-007

| File | Hist freq | New freq |
| --- | ---: | ---: |
| `cms/admin/pageadmin.py` | 5 | 4 |
| `cms/api.py` | 5 | 1 |
| `cms/cms_toolbars.py` | 3 | 3 |
| `cms/constants.py` | 1 | 0 |
| `cms/models/contentmodels.py` | 5 | 3 |
| `cms/models/managers.py` | 0 | 1 |
| `cms/models/permissionmodels.py` | 5 | 2 |
| `cms/plugin_rendering.py` | 0 | 1 |
| `cms/signals/__init__.py` | 5 | 3 |
| `cms/toolbar/toolbar.py` | 2 | 1 |
| `cms/utils/apphook_reload.py` | 0 | 3 |
| `cms/utils/page.py` | 2 | 1 |
| `cms/utils/page_permissions.py` | 1 | 1 |

### djangocms-external-validity-008

| File | Hist freq | New freq |
| --- | ---: | ---: |
| `cms/cache/__init__.py` | 5 | 5 |
| `cms/cache/page.py` | 3 | 0 |
| `cms/cache/permissions.py` | 1 | 0 |
| `cms/cache/placeholder.py` | 2 | 0 |
| `cms/middleware/toolbar.py` | 4 | 5 |
| `cms/models/contentmodels.py` | 0 | 5 |
| `cms/models/pagemodel.py` | 0 | 5 |
| `cms/models/placeholdermodel.py` | 0 | 5 |
| `cms/models/pluginmodel.py` | 0 | 5 |
| `cms/signals/__init__.py` | 5 | 5 |
| `cms/templatetags/cms_static.py` | 0 | 4 |
| `cms/templatetags/cms_tags.py` | 5 | 1 |
