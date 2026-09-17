# M4A-3 / P1 — REAL-COMMIT FULL-v2 vs SPARSE-v2 ZERO-API Gates + Audit

**Generated:** 2026-09-17T19:25:59.959672+00:00
**Study ID:** real-commit-p1-v1.0.0
**Frozen protocol:** reports/REAL_COMMIT_M4A3_P1_PROTOCOL.md

ZERO scientific LLM/API calls in this milestone. Real held-out inference is NOT executed.

**OVERALL:** PASS

## Gate 1 — Dataset Validation

- [PASS] held_out_membership_exact — ["djangocms-rc-4307e1b8c2e2", "djangocms-rc-50c3576080be", "djangocms-rc-630a50361ada", "djangocms-rc-66c70394c9e1", "djangocms-rc-75978fb1c3ad", "djangocms-rc-8d50660e7bcf", "djangocms-rc-9e33db4f466
- [PASS] held_out_count_10 — 10
- [PASS] public_hidden_separation_djangocms-rc-4307e1b8c2e2 — {"candidate_paths": 140, "records": 140}
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-4307e1b8c2e2 — []
- [PASS] candidate_map_deterministic_djangocms-rc-4307e1b8c2e2 — {"count": 140, "sha256": "68c166b6664bc7af854afa7fe2b473b746067bc86a2592bb7ffccd0378a7a4f7"}
- [PASS] no_hidden_proxy_in_public_bundle_hash_djangocms-rc-4307e1b8c2e2 — "77474ab562d879bf19a2d067932408445f732b0a510630d0dcf40c09d56dd7a2"
- [PASS] public_hidden_separation_djangocms-rc-50c3576080be — {"candidate_paths": 144, "records": 144}
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-50c3576080be — []
- [PASS] candidate_map_deterministic_djangocms-rc-50c3576080be — {"count": 144, "sha256": "9d33e163505722e2cfe602ca165777d3d5accbaf5b9f7a82d1b30068ca9d1ca6"}
- [PASS] no_hidden_proxy_in_public_bundle_hash_djangocms-rc-50c3576080be — "df3f001b70fc3f93f14d5744b13b2975b86696ce6ec5fb90badc163367501ac6"
- [PASS] public_hidden_separation_djangocms-rc-630a50361ada — {"candidate_paths": 152, "records": 152}
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-630a50361ada — []
- [PASS] candidate_map_deterministic_djangocms-rc-630a50361ada — {"count": 152, "sha256": "affe53f09286f00feb14ecdcf43c0750148de3f722fb5133abe47e09ac5744c0"}
- [PASS] no_hidden_proxy_in_public_bundle_hash_djangocms-rc-630a50361ada — "f4ad51527c7978a6e40eab7ed9badd6e6b906a9cf6a58e8b91d8c2f83101244c"
- [PASS] public_hidden_separation_djangocms-rc-66c70394c9e1 — {"candidate_paths": 140, "records": 140}
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-66c70394c9e1 — []
- [PASS] candidate_map_deterministic_djangocms-rc-66c70394c9e1 — {"count": 140, "sha256": "68c166b6664bc7af854afa7fe2b473b746067bc86a2592bb7ffccd0378a7a4f7"}
- [PASS] no_hidden_proxy_in_public_bundle_hash_djangocms-rc-66c70394c9e1 — "403483df371427898dc23f3367741a4787bc4910b75d73e37847d55abba5cbab"
- [PASS] public_hidden_separation_djangocms-rc-75978fb1c3ad — {"candidate_paths": 140, "records": 140}
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-75978fb1c3ad — []
- [PASS] candidate_map_deterministic_djangocms-rc-75978fb1c3ad — {"count": 140, "sha256": "68c166b6664bc7af854afa7fe2b473b746067bc86a2592bb7ffccd0378a7a4f7"}
- [PASS] no_hidden_proxy_in_public_bundle_hash_djangocms-rc-75978fb1c3ad — "101b3ddb82e85b233d016a72fcebb50992df8a1b93a85c8bcb0433fadf1b971a"
- [PASS] public_hidden_separation_djangocms-rc-8d50660e7bcf — {"candidate_paths": 144, "records": 144}
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-8d50660e7bcf — []
- [PASS] candidate_map_deterministic_djangocms-rc-8d50660e7bcf — {"count": 144, "sha256": "9d33e163505722e2cfe602ca165777d3d5accbaf5b9f7a82d1b30068ca9d1ca6"}
- [PASS] no_hidden_proxy_in_public_bundle_hash_djangocms-rc-8d50660e7bcf — "cf29df1c23f066a272f1966a2fcd09a9232462ca7a01961cbcbf4798ab29c770"
- [PASS] public_hidden_separation_djangocms-rc-9e33db4f4660 — {"candidate_paths": 144, "records": 144}
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-9e33db4f4660 — []
- [PASS] candidate_map_deterministic_djangocms-rc-9e33db4f4660 — {"count": 144, "sha256": "9d33e163505722e2cfe602ca165777d3d5accbaf5b9f7a82d1b30068ca9d1ca6"}
- [PASS] no_hidden_proxy_in_public_bundle_hash_djangocms-rc-9e33db4f4660 — "c3c6c08387f77c73223e43531457d070068f2649b883eb1e8bc734b0b2343c36"
- [PASS] public_hidden_separation_djangocms-rc-b39799f9fc1c — {"candidate_paths": 140, "records": 140}
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-b39799f9fc1c — []
- [PASS] candidate_map_deterministic_djangocms-rc-b39799f9fc1c — {"count": 140, "sha256": "0793ce351b34d1854e7559951d2c95751e7ab47b2030c00c9330df81a0020d6b"}
- [PASS] no_hidden_proxy_in_public_bundle_hash_djangocms-rc-b39799f9fc1c — "0482746ddd86291e8240cf153f82c11972db729a98684c4ef04a5425433c80f1"
- [PASS] public_hidden_separation_djangocms-rc-ba16eb9a1d09 — {"candidate_paths": 152, "records": 152}
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-ba16eb9a1d09 — []
- [PASS] candidate_map_deterministic_djangocms-rc-ba16eb9a1d09 — {"count": 152, "sha256": "affe53f09286f00feb14ecdcf43c0750148de3f722fb5133abe47e09ac5744c0"}
- [PASS] no_hidden_proxy_in_public_bundle_hash_djangocms-rc-ba16eb9a1d09 — "e92839cc3ec5dae18c45c95da3010f0d8a8cda3e852c7d594bceb4c57685a3a7"
- [PASS] public_hidden_separation_djangocms-rc-fdda30c271f0 — {"candidate_paths": 144, "records": 144}
- [PASS] proxy_subset_of_parent_universe_djangocms-rc-fdda30c271f0 — []
- [PASS] candidate_map_deterministic_djangocms-rc-fdda30c271f0 — {"count": 144, "sha256": "9d33e163505722e2cfe602ca165777d3d5accbaf5b9f7a82d1b30068ca9d1ca6"}
- [PASS] no_hidden_proxy_in_public_bundle_hash_djangocms-rc-fdda30c271f0 — "5d28724b48b47b0bdd61dd2f28e5b5cb9b62c9fceb75eb791543eedfd52f50aa"

## Gate 2 — Prompt Validation

- [PASS] prompt_control_proof_djangocms-rc-4307e1b8c2e2 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "daf99fcca1fb1a87644f03495135ed949b2b11b763651c2efb7d631c750a38aa", "stripped_sparse_sha256": "daf99fcca1fb1a87644f03495135ed949b2b11b763651c
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-4307e1b8c2e2 — []
- [PASS] intent_present_djangocms-rc-4307e1b8c2e2 — "Use PageContent instance in wizard form instead of Page instance (#6532)"
- [PASS] prompt_control_proof_djangocms-rc-50c3576080be — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "ca107c699e25cb77a65af488ea31197753f14c3e72c9b655934a6973d9d0e5ba", "stripped_sparse_sha256": "ca107c699e25cb77a65af488ea31197753f14c3e72c9b6
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-50c3576080be — []
- [PASS] intent_present_djangocms-rc-50c3576080be — "chore: Minor fixes for django CMS 5.0.0a1 (#8182) * flake8 issues * Capitalize page form titles (#8158) * Add doc'S auto"
- [PASS] prompt_control_proof_djangocms-rc-630a50361ada — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "2b15f3e1893be00b9b00e370c5e76c1c765af454e73ed3e2e4d5e44345c5f674", "stripped_sparse_sha256": "2b15f3e1893be00b9b00e370c5e76c1c765af454e73ed3
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-630a50361ada — []
- [PASS] intent_present_djangocms-rc-630a50361ada — "Fixed #6199 -- Show all languages on language chooser if user is staff (#6200)"
- [PASS] prompt_control_proof_djangocms-rc-66c70394c9e1 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "9d88f18f97498811705ebe647ff8075c9245d0539b460dd6af46649d815e93b9", "stripped_sparse_sha256": "9d88f18f97498811705ebe647ff8075c9245d0539b460d
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-66c70394c9e1 — []
- [PASS] intent_present_djangocms-rc-66c70394c9e1 — "Fix being able to reset the setting PageContent.limit_visibility_in_menu (#7016) * Enable a user to be able to reset a P"
- [PASS] prompt_control_proof_djangocms-rc-75978fb1c3ad — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "5ca3b9739f18f3bc2f0f74969e8f980550351a81e28bc092cef2f0590b892e00", "stripped_sparse_sha256": "5ca3b9739f18f3bc2f0f74969e8f980550351a81e28bc0
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-75978fb1c3ad — []
- [PASS] intent_present_djangocms-rc-75978fb1c3ad — "Ported: Fix 'urls.W001' warning with custom apphook urls (#6874) * Added test to expose the issue * Added fix to the App"
- [PASS] prompt_control_proof_djangocms-rc-8d50660e7bcf — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "e7e689ee6945a937f6e89f14c1267557ecf1d39b0796c71235cf5ced4925277a", "stripped_sparse_sha256": "e7e689ee6945a937f6e89f14c1267557ecf1d39b0796c7
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-8d50660e7bcf — []
- [PASS] intent_present_djangocms-rc-8d50660e7bcf — "fix: Slug uniqueness not checked when moving page (#8185) * fix: Slug uniqueness not checked when moving page * test: ad"
- [PASS] prompt_control_proof_djangocms-rc-9e33db4f4660 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "3fd17123f705c79ba4262fba120b1a6deb4a43dda216e70f2f1b133604882a90", "stripped_sparse_sha256": "3fd17123f705c79ba4262fba120b1a6deb4a43dda216e7
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-9e33db4f4660 — []
- [PASS] intent_present_djangocms-rc-9e33db4f4660 — "fix: Ensure plugin class properties are available to the Django template engine (#8071) * Fix: Ensure plugin class prope"
- [PASS] prompt_control_proof_djangocms-rc-b39799f9fc1c — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "525621e944ea91f0740cad3108c87fe4c98f60725265e54fef8a65fe8e76f671", "stripped_sparse_sha256": "525621e944ea91f0740cad3108c87fe4c98f60725265e5
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-b39799f9fc1c — []
- [PASS] intent_present_djangocms-rc-b39799f9fc1c — "feat: [CMS v4] Reintroduce indicator menus (#7426) * fix target of indicator dropdown menu * Add: draft status indicator"
- [PASS] prompt_control_proof_djangocms-rc-ba16eb9a1d09 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "f56f0dd84114be6c94da0b08a53c35648aafa10df44ac2913e73c1f4a46473b5", "stripped_sparse_sha256": "f56f0dd84114be6c94da0b08a53c35648aafa10df44ac2
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-ba16eb9a1d09 — []
- [PASS] intent_present_djangocms-rc-ba16eb9a1d09 — "Use Django's language override (#6187)"
- [PASS] prompt_control_proof_djangocms-rc-fdda30c271f0 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "301e823ca5c8f544da3502d1ad37ced9cc2e1db88ab35184721fefddd3f9296c", "stripped_sparse_sha256": "301e823ca5c8f544da3502d1ad37ced9cc2e1db88ab351
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-fdda30c271f0 — []
- [PASS] intent_present_djangocms-rc-fdda30c271f0 — "fix: Browser reloaded when clearing placeholder (#8188) * fix: Browser reloaded when clearing placeholder * fix tests * "
- [PASS] zero_scientific_calls_prompt_render — "pure string rendering; no backend constructed"

## Gate 3 — Pipeline Smoke Test

- [PASS] smoke_full_v2_djangocms-rc-4307e1b8c2e2 — {"valid": true, "decoded_candidate_count": 140, "errors": []}
- [PASS] smoke_sparse_v2_djangocms-rc-4307e1b8c2e2 — {"valid": true, "decoded_candidate_count": 140, "errors": []}
- [PASS] smoke_full_v2_djangocms-rc-50c3576080be — {"valid": true, "decoded_candidate_count": 144, "errors": []}
- [PASS] smoke_sparse_v2_djangocms-rc-50c3576080be — {"valid": true, "decoded_candidate_count": 144, "errors": []}
- [PASS] smoke_full_v2_djangocms-rc-630a50361ada — {"valid": true, "decoded_candidate_count": 152, "errors": []}
- [PASS] smoke_sparse_v2_djangocms-rc-630a50361ada — {"valid": true, "decoded_candidate_count": 152, "errors": []}
- [PASS] smoke_full_v2_djangocms-rc-66c70394c9e1 — {"valid": true, "decoded_candidate_count": 140, "errors": []}
- [PASS] smoke_sparse_v2_djangocms-rc-66c70394c9e1 — {"valid": true, "decoded_candidate_count": 140, "errors": []}
- [PASS] smoke_full_v2_djangocms-rc-75978fb1c3ad — {"valid": true, "decoded_candidate_count": 140, "errors": []}
- [PASS] smoke_sparse_v2_djangocms-rc-75978fb1c3ad — {"valid": true, "decoded_candidate_count": 140, "errors": []}
- [PASS] smoke_full_v2_djangocms-rc-8d50660e7bcf — {"valid": true, "decoded_candidate_count": 144, "errors": []}
- [PASS] smoke_sparse_v2_djangocms-rc-8d50660e7bcf — {"valid": true, "decoded_candidate_count": 144, "errors": []}
- [PASS] smoke_full_v2_djangocms-rc-9e33db4f4660 — {"valid": true, "decoded_candidate_count": 144, "errors": []}
- [PASS] smoke_sparse_v2_djangocms-rc-9e33db4f4660 — {"valid": true, "decoded_candidate_count": 144, "errors": []}
- [PASS] smoke_full_v2_djangocms-rc-b39799f9fc1c — {"valid": true, "decoded_candidate_count": 140, "errors": []}
- [PASS] smoke_sparse_v2_djangocms-rc-b39799f9fc1c — {"valid": true, "decoded_candidate_count": 140, "errors": []}
- [PASS] smoke_full_v2_djangocms-rc-ba16eb9a1d09 — {"valid": true, "decoded_candidate_count": 152, "errors": []}
- [PASS] smoke_sparse_v2_djangocms-rc-ba16eb9a1d09 — {"valid": true, "decoded_candidate_count": 152, "errors": []}
- [PASS] smoke_full_v2_djangocms-rc-fdda30c271f0 — {"valid": true, "decoded_candidate_count": 144, "errors": []}
- [PASS] smoke_sparse_v2_djangocms-rc-fdda30c271f0 — {"valid": true, "decoded_candidate_count": 144, "errors": []}
- [PASS] zero_scientific_calls_smoke — "deterministic fixture encode/decode only"

## Gate 4 — Dry Run

- [PASS] manifest_iteration_exactly_60 — 60
- [PASS] run_ids_unique — {"unique": 60}
- [PASS] ten_held_out_cases — ["djangocms-rc-4307e1b8c2e2", "djangocms-rc-50c3576080be", "djangocms-rc-630a50361ada", "djangocms-rc-66c70394c9e1", "djangocms-rc-75978fb1c3ad", "djangocms-rc-8d50660e7bcf", "djangocms-rc-9e33db4f466
- [PASS] two_arms — ["full_v2", "sparse_v2"]
- [PASS] three_reps_per_case_per_arm — "10 cases \u00d7 2 arms \u00d7 3 reps = 60"
- [PASS] frozen_configuration_propagation — "all 60 cells carry frozen model/provider/config"
- [PASS] zero_scientific_calls_and_tokens — "manifest-shape proof only; zero model calls and zero billed tokens"

## Gate 5 — Integration Test

- [PASS] full_v2_decode_djangocms-rc-4307e1b8c2e2 — {"valid": true, "count": 140}
- [PASS] full_v2_proxy_exact_fixture_djangocms-rc-4307e1b8c2e2 — {"predicted": ["cms/forms/wizards.py"], "proxy": ["cms/forms/wizards.py"]}
- [PASS] full_v2_metrics_perfect_fixture_djangocms-rc-4307e1b8c2e2 — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] sparse_v2_decode_djangocms-rc-4307e1b8c2e2 — {"valid": true, "count": 140}
- [PASS] sparse_v2_proxy_exact_fixture_djangocms-rc-4307e1b8c2e2 — {"predicted": ["cms/forms/wizards.py"], "proxy": ["cms/forms/wizards.py"]}
- [PASS] sparse_v2_metrics_perfect_fixture_djangocms-rc-4307e1b8c2e2 — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] full_v2_decode_djangocms-rc-50c3576080be — {"valid": true, "count": 144}
- [PASS] full_v2_proxy_exact_fixture_djangocms-rc-50c3576080be — {"predicted": ["cms/admin/forms.py", "cms/admin/pageadmin.py", "cms/admin/placeholderadmin.py", "cms/admin/utils.py", "cms/cache/page.py", "cms/middleware/language.py", "cms/middleware/toolbar.py", "c
- [PASS] full_v2_metrics_perfect_fixture_djangocms-rc-50c3576080be — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] sparse_v2_decode_djangocms-rc-50c3576080be — {"valid": true, "count": 144}
- [PASS] sparse_v2_proxy_exact_fixture_djangocms-rc-50c3576080be — {"predicted": ["cms/admin/forms.py", "cms/admin/pageadmin.py", "cms/admin/placeholderadmin.py", "cms/admin/utils.py", "cms/cache/page.py", "cms/middleware/language.py", "cms/middleware/toolbar.py", "c
- [PASS] sparse_v2_metrics_perfect_fixture_djangocms-rc-50c3576080be — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] full_v2_decode_djangocms-rc-630a50361ada — {"valid": true, "count": 152}
- [PASS] full_v2_proxy_exact_fixture_djangocms-rc-630a50361ada — {"predicted": ["menus/templatetags/menu_tags.py"], "proxy": ["menus/templatetags/menu_tags.py"]}
- [PASS] full_v2_metrics_perfect_fixture_djangocms-rc-630a50361ada — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] sparse_v2_decode_djangocms-rc-630a50361ada — {"valid": true, "count": 152}
- [PASS] sparse_v2_proxy_exact_fixture_djangocms-rc-630a50361ada — {"predicted": ["menus/templatetags/menu_tags.py"], "proxy": ["menus/templatetags/menu_tags.py"]}
- [PASS] sparse_v2_metrics_perfect_fixture_djangocms-rc-630a50361ada — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] full_v2_decode_djangocms-rc-66c70394c9e1 — {"valid": true, "count": 140}
- [PASS] full_v2_proxy_exact_fixture_djangocms-rc-66c70394c9e1 — {"predicted": ["cms/models/titlemodels.py"], "proxy": ["cms/models/titlemodels.py"]}
- [PASS] full_v2_metrics_perfect_fixture_djangocms-rc-66c70394c9e1 — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] sparse_v2_decode_djangocms-rc-66c70394c9e1 — {"valid": true, "count": 140}
- [PASS] sparse_v2_proxy_exact_fixture_djangocms-rc-66c70394c9e1 — {"predicted": ["cms/models/titlemodels.py"], "proxy": ["cms/models/titlemodels.py"]}
- [PASS] sparse_v2_metrics_perfect_fixture_djangocms-rc-66c70394c9e1 — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] full_v2_decode_djangocms-rc-75978fb1c3ad — {"valid": true, "count": 140}
- [PASS] full_v2_proxy_exact_fixture_djangocms-rc-75978fb1c3ad — {"predicted": ["cms/appresolver.py"], "proxy": ["cms/appresolver.py"]}
- [PASS] full_v2_metrics_perfect_fixture_djangocms-rc-75978fb1c3ad — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] sparse_v2_decode_djangocms-rc-75978fb1c3ad — {"valid": true, "count": 140}
- [PASS] sparse_v2_proxy_exact_fixture_djangocms-rc-75978fb1c3ad — {"predicted": ["cms/appresolver.py"], "proxy": ["cms/appresolver.py"]}
- [PASS] sparse_v2_metrics_perfect_fixture_djangocms-rc-75978fb1c3ad — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] full_v2_decode_djangocms-rc-8d50660e7bcf — {"valid": true, "count": 144}
- [PASS] full_v2_proxy_exact_fixture_djangocms-rc-8d50660e7bcf — {"predicted": ["cms/admin/forms.py", "cms/admin/pageadmin.py", "cms/api.py", "cms/forms/validators.py", "cms/models/pagemodel.py"], "proxy": ["cms/admin/forms.py", "cms/admin/pageadmin.py", "cms/api.p
- [PASS] full_v2_metrics_perfect_fixture_djangocms-rc-8d50660e7bcf — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] sparse_v2_decode_djangocms-rc-8d50660e7bcf — {"valid": true, "count": 144}
- [PASS] sparse_v2_proxy_exact_fixture_djangocms-rc-8d50660e7bcf — {"predicted": ["cms/admin/forms.py", "cms/admin/pageadmin.py", "cms/api.py", "cms/forms/validators.py", "cms/models/pagemodel.py"], "proxy": ["cms/admin/forms.py", "cms/admin/pageadmin.py", "cms/api.p
- [PASS] sparse_v2_metrics_perfect_fixture_djangocms-rc-8d50660e7bcf — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] full_v2_decode_djangocms-rc-9e33db4f4660 — {"valid": true, "count": 144}
- [PASS] full_v2_proxy_exact_fixture_djangocms-rc-9e33db4f4660 — {"predicted": ["cms/plugin_base.py", "cms/utils/compat/__init__.py"], "proxy": ["cms/plugin_base.py", "cms/utils/compat/__init__.py"]}
- [PASS] full_v2_metrics_perfect_fixture_djangocms-rc-9e33db4f4660 — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] sparse_v2_decode_djangocms-rc-9e33db4f4660 — {"valid": true, "count": 144}
- [PASS] sparse_v2_proxy_exact_fixture_djangocms-rc-9e33db4f4660 — {"predicted": ["cms/plugin_base.py", "cms/utils/compat/__init__.py"], "proxy": ["cms/plugin_base.py", "cms/utils/compat/__init__.py"]}
- [PASS] sparse_v2_metrics_perfect_fixture_djangocms-rc-9e33db4f4660 — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] full_v2_decode_djangocms-rc-b39799f9fc1c — {"valid": true, "count": 140}
- [PASS] full_v2_proxy_exact_fixture_djangocms-rc-b39799f9fc1c — {"predicted": ["cms/admin/pageadmin.py", "cms/cms_toolbars.py", "cms/models/contentmodels.py", "cms/models/pagemodel.py", "cms/templatetags/cms_admin.py"], "proxy": ["cms/admin/pageadmin.py", "cms/cms
- [PASS] full_v2_metrics_perfect_fixture_djangocms-rc-b39799f9fc1c — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] sparse_v2_decode_djangocms-rc-b39799f9fc1c — {"valid": true, "count": 140}
- [PASS] sparse_v2_proxy_exact_fixture_djangocms-rc-b39799f9fc1c — {"predicted": ["cms/admin/pageadmin.py", "cms/cms_toolbars.py", "cms/models/contentmodels.py", "cms/models/pagemodel.py", "cms/templatetags/cms_admin.py"], "proxy": ["cms/admin/pageadmin.py", "cms/cms
- [PASS] sparse_v2_metrics_perfect_fixture_djangocms-rc-b39799f9fc1c — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] full_v2_decode_djangocms-rc-ba16eb9a1d09 — {"valid": true, "count": 152}
- [PASS] full_v2_proxy_exact_fixture_djangocms-rc-ba16eb9a1d09 — {"predicted": ["cms/cms_menus.py", "cms/cms_toolbars.py", "cms/models/pagemodel.py", "cms/templatetags/cms_tags.py", "cms/toolbar/toolbar.py", "cms/toolbar/utils.py"], "proxy": ["cms/cms_menus.py", "c
- [PASS] full_v2_metrics_perfect_fixture_djangocms-rc-ba16eb9a1d09 — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] sparse_v2_decode_djangocms-rc-ba16eb9a1d09 — {"valid": true, "count": 152}
- [PASS] sparse_v2_proxy_exact_fixture_djangocms-rc-ba16eb9a1d09 — {"predicted": ["cms/cms_menus.py", "cms/cms_toolbars.py", "cms/models/pagemodel.py", "cms/templatetags/cms_tags.py", "cms/toolbar/toolbar.py", "cms/toolbar/utils.py"], "proxy": ["cms/cms_menus.py", "c
- [PASS] sparse_v2_metrics_perfect_fixture_djangocms-rc-ba16eb9a1d09 — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] full_v2_decode_djangocms-rc-fdda30c271f0 — {"valid": true, "count": 144}
- [PASS] full_v2_proxy_exact_fixture_djangocms-rc-fdda30c271f0 — {"predicted": ["cms/admin/placeholderadmin.py", "cms/middleware/toolbar.py", "cms/plugin_rendering.py"], "proxy": ["cms/admin/placeholderadmin.py", "cms/middleware/toolbar.py", "cms/plugin_rendering.p
- [PASS] full_v2_metrics_perfect_fixture_djangocms-rc-fdda30c271f0 — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] sparse_v2_decode_djangocms-rc-fdda30c271f0 — {"valid": true, "count": 144}
- [PASS] sparse_v2_proxy_exact_fixture_djangocms-rc-fdda30c271f0 — {"predicted": ["cms/admin/placeholderadmin.py", "cms/middleware/toolbar.py", "cms/plugin_rendering.py"], "proxy": ["cms/admin/placeholderadmin.py", "cms/middleware/toolbar.py", "cms/plugin_rendering.p
- [PASS] sparse_v2_metrics_perfect_fixture_djangocms-rc-fdda30c271f0 — {"precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}

## Gate 6 — Metric Verification

- [PASS] micro_precision_recall_f1_recomputed — {"computed": {"tp": 3, "fp": 1, "fn": 0, "precision": 0.75, "recall": 1.0, "f1": 0.8571428571428571, "fnr": 0.0, "full_recall": true, "proxy_size": 3, "predicted_size": 4}, "expected": {"precision": 0
- [PASS] empty_prediction_fail_closed_metrics — {"tp": 0, "fp": 0, "fn": 1, "precision": 0.0, "recall": 0.0, "f1": 0.0, "fnr": 1.0, "full_recall": false, "proxy_size": 1, "predicted_size": 0}
- [PASS] full_incomplete_rejected — "FULL-v2 output missing ids fails closed"
- [PASS] sparse_explicit_preserve_rejected — "SPARSE-v2 must not contain explicit PRESERVE rows"
- [PASS] duplicate_ids_rejected — "duplicate candidate ids fail closed"

## Independent Audit

- [PASS] protocol_frozen_before_result — reports/REAL_COMMIT_M4A3_P1_PROTOCOL.md
- [PASS] study_id_frozen — real-commit-p1-v1.0.0
- [PASS] model_frozen — qwen/qwen3-coder
- [PASS] provider_frozen — deepinfra/turbo
- [PASS] repetitions_3_frozen — 3
- [PASS] temperature_0_frozen — 0.0
- [PASS] cap_16384_frozen — 16384
- [PASS] no_hidden_proxy_in_any_public_bundle — hidden/ never read during prompt render; proxy is evaluation-only
- [PASS] no_scientific_api_artifacts — zero model calls in this milestone

## Scientific discipline

- The historical diff is an **OBSERVED CHANGE-SET PROXY**, never semantic ground truth.
- Independent task = historical change; repeated model calls are nested observations.
- No P/R/V/H gold fabricated from Git diffs; no held-out result exists yet.