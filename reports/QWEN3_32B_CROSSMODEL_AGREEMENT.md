# Qwen3-32B Cross-Model Agreement (Sparse-v2)

**DESCRIPTIVE ONLY - no equivalence/significance claim.**

Method: for each scenario, ALL valid historical Qwen3-Coder-480B-A35B-Instruct Sparse-v2 runs x ALL valid new Qwen3-32B Sparse-v2 runs, full cross-product Jaccard of selected-file sets. Runs are NOT paired by repetition.

| Scenario | Hist valid | New valid | Pairs | Mean | Median | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| djangocms-external-validity-002 | 4 | 3 | 12 | 0.000 | 0.000 | 0.000 | 0.000 |
| djangocms-external-validity-004 | 5 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 |
| djangocms-external-validity-005 | 5 | 5 | 25 | 0.621 | 0.625 | 0.400 | 1.000 |
| djangocms-external-validity-006 | 5 | 5 | 25 | 0.177 | 0.167 | 0.000 | 0.500 |
| djangocms-external-validity-007 | 5 | 4 | 20 | 0.382 | 0.359 | 0.231 | 0.636 |
| djangocms-external-validity-008 | 5 | 4 | 20 | 0.071 | 0.071 | 0.062 | 0.077 |
| **Overall** | - | - | **102** | **0.284** | **0.231** | **0.000** | **1.000** |

## Per-file selection frequencies

### djangocms-external-validity-002
| File | Hist freq | New freq |
| --- | ---: | ---: |
| cms/__init__.py | 0 | 1 |
| cms/api.py | 4 | 0 |
| cms/models/contentmodels.py | 3 | 0 |
| cms/utils/__init__.py | 0 | 3 |
| cms/utils/page.py | 2 | 0 |

### djangocms-external-validity-004
| File | Hist freq | New freq |
| --- | ---: | ---: |
| cms/admin/forms.py | 2 | 0 |
| cms/admin/pageadmin.py | 5 | 0 |
| cms/api.py | 5 | 0 |
| cms/models/contentmodels.py | 5 | 0 |
| cms/models/managers.py | 2 | 0 |
| cms/templatetags/cms_static.py | 2 | 0 |
| cms/views.py | 5 | 0 |

### djangocms-external-validity-005
| File | Hist freq | New freq |
| --- | ---: | ---: |
| cms/admin/pageadmin.py | 5 | 5 |
| cms/admin/permissionadmin.py | 5 | 5 |
| cms/cms_toolbars.py | 5 | 5 |
| cms/models/pagemodel.py | 0 | 3 |
| cms/models/permissionmodels.py | 5 | 5 |
| cms/templatetags/__init__.py | 0 | 2 |
| cms/utils/admin.py | 0 | 2 |
| cms/utils/page.py | 2 | 0 |
| cms/utils/page_permissions.py | 4 | 5 |
| cms/utils/permissions.py | 1 | 5 |
| cms/utils/urlutils.py | 0 | 1 |
| cms/wizards/forms.py | 0 | 2 |

### djangocms-external-validity-006
| File | Hist freq | New freq |
| --- | ---: | ---: |
| cms/admin/forms.py | 5 | 2 |
| cms/admin/placeholderadmin.py | 2 | 5 |
| cms/management/commands/cms.py | 0 | 1 |
| cms/models/placeholderpluginmodel.py | 0 | 5 |
| cms/models/pluginmodel.py | 5 | 0 |
| cms/operations/helpers.py | 0 | 2 |
| cms/plugin_processors.py | 0 | 3 |
| cms/plugin_rendering.py | 5 | 2 |
| cms/templatetags/cms_static.py | 0 | 1 |
| cms/utils/apphook_reload.py | 0 | 1 |
| cms/utils/page_permissions.py | 0 | 1 |
| cms/utils/placeholder.py | 1 | 1 |
| cms/wizards/__init__.py | 0 | 1 |

### djangocms-external-validity-007
| File | Hist freq | New freq |
| --- | ---: | ---: |
| cms/admin/forms.py | 0 | 1 |
| cms/admin/pageadmin.py | 5 | 4 |
| cms/api.py | 5 | 4 |
| cms/cms_toolbars.py | 3 | 4 |
| cms/constants.py | 1 | 0 |
| cms/models/aliaspluginmodel.py | 0 | 4 |
| cms/models/contentmodels.py | 5 | 0 |
| cms/models/permissionmodels.py | 5 | 2 |
| cms/operations/helpers.py | 0 | 1 |
| cms/signals/__init__.py | 5 | 4 |
| cms/templatetags/__init__.py | 0 | 1 |
| cms/templatetags/cms_static.py | 0 | 1 |
| cms/toolbar/toolbar.py | 2 | 0 |
| cms/utils/admin.py | 0 | 2 |
| cms/utils/encoder.py | 0 | 1 |
| cms/utils/mail.py | 0 | 2 |
| cms/utils/page.py | 2 | 4 |
| cms/utils/page_permissions.py | 1 | 2 |
| cms/utils/permissions.py | 0 | 1 |
| cms/utils/setup.py | 0 | 2 |

### djangocms-external-validity-008
| File | Hist freq | New freq |
| --- | ---: | ---: |
| cms/cache/__init__.py | 5 | 4 |
| cms/cache/page.py | 3 | 0 |
| cms/cache/permissions.py | 1 | 0 |
| cms/cache/placeholder.py | 2 | 0 |
| cms/management/commands/subcommands/check.py | 0 | 4 |
| cms/middleware/language.py | 0 | 4 |
| cms/middleware/toolbar.py | 4 | 0 |
| cms/models/managers.py | 0 | 3 |
| cms/models/permissionmodels.py | 0 | 3 |
| cms/models/placeholderpluginmodel.py | 0 | 3 |
| cms/plugin_rendering.py | 0 | 1 |
| cms/signals/__init__.py | 5 | 0 |
| cms/signals/apphook.py | 0 | 1 |
| cms/templatetags/cms_static.py | 0 | 4 |
| cms/templatetags/cms_tags.py | 5 | 0 |
| cms/toolbar/toolbar.py | 0 | 1 |
| cms/urls.py | 0 | 1 |
| cms/utils/compat/warnings.py | 0 | 3 |
| cms/utils/encoder.py | 0 | 1 |
| cms/utils/page_permissions.py | 0 | 1 |
| cms/utils/permissions.py | 0 | 3 |
| cms/utils/placeholder.py | 0 | 3 |
| cms/wizards/forms.py | 0 | 1 |

Raw pairwise rows: 102 rows in QWEN3_32B_CROSSMODEL_AGREEMENT.csv