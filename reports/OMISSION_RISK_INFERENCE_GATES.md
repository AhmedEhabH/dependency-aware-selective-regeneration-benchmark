# Omission-Risk Development Inference — ZERO-API Gates + Leakage Audit

**Generated:** 2026-09-16T05:30:29.814337+00:00
**Study ID:** omission-risk-development-inference-v1
**Frozen protocol:** docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md

ZERO scientific LLM/API calls in this milestone. No model call is made before these gates pass.

**OVERALL:** PASS

## Gate 1 — Dataset Validation

- [PASS] split_count_TRAIN — 24
- [PASS] split_count_VALIDATION — 6
- [PASS] split_count_HELD_OUT_TEST — 10
- [PASS] adapter_case_ids_only_train_validation — {"n": 30, "splits": ["TRAIN", "VALIDATION"]}
- [PASS] adapter_excludes_held_out — "no HELD_OUT_TEST case exposed by the adapter"
- [PASS] heldout_proxy_fails_closed — "blocked"
- [PASS] proxy_subset_universe_djangocms-rc-a7df58dc5ff3 — []
- [PASS] proxy_subset_universe_djangocms-rc-0daae01f2f65 — []
- [PASS] proxy_subset_universe_djangocms-rc-ada585d3f358 — []
- [PASS] proxy_subset_universe_djangocms-rc-1031d20fca28 — []
- [PASS] proxy_subset_universe_djangocms-rc-2efae8e43bd6 — []
- [PASS] proxy_subset_universe_djangocms-rc-ca16415b1022 — []
- [PASS] proxy_subset_universe_djangocms-rc-ff6cb9b5dced — []
- [PASS] proxy_subset_universe_djangocms-rc-497c3c67e813 — []
- [PASS] proxy_subset_universe_djangocms-rc-06ecf3a8e8de — []
- [PASS] proxy_subset_universe_djangocms-rc-c02308fc5261 — []
- [PASS] proxy_subset_universe_djangocms-rc-3f8fcb5fb63b — []
- [PASS] proxy_subset_universe_djangocms-rc-d88932559b00 — []
- [PASS] proxy_subset_universe_djangocms-rc-138abbb7e5f4 — []
- [PASS] proxy_subset_universe_djangocms-rc-ac74c212719f — []
- [PASS] proxy_subset_universe_djangocms-rc-1ff5bf9149b4 — []
- [PASS] proxy_subset_universe_djangocms-rc-e429b4584a16 — []
- [PASS] proxy_subset_universe_djangocms-rc-a1ac04d3f817 — []
- [PASS] proxy_subset_universe_djangocms-rc-807a87b1de71 — []
- [PASS] proxy_subset_universe_djangocms-rc-47b63015feb1 — []
- [PASS] proxy_subset_universe_djangocms-rc-9e508ff1c41e — []
- [PASS] proxy_subset_universe_djangocms-rc-28ddd6d10308 — []
- [PASS] proxy_subset_universe_djangocms-rc-33fbdb18e5d4 — []
- [PASS] proxy_subset_universe_djangocms-rc-e88032bf704c — []
- [PASS] proxy_subset_universe_djangocms-rc-f2c367ddc7b1 — []
- [PASS] proxy_subset_universe_djangocms-rc-4b8089b8b686 — []
- [PASS] proxy_subset_universe_djangocms-rc-e3a23a7fc757 — []
- [PASS] proxy_subset_universe_djangocms-rc-a9e2a8d3b7a6 — []
- [PASS] proxy_subset_universe_djangocms-rc-0fec81224889 — []
- [PASS] proxy_subset_universe_djangocms-rc-39442083f18a — []
- [PASS] proxy_subset_universe_djangocms-rc-5ff38b521274 — []

## Gate 2 — Prompt/Input Validation

- [PASS] prompt_control_proof_djangocms-rc-06ecf3a8e8de — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "b6855b9095fd54e6d8013b2e0ccb908b6f6319083421f18d36fc8e4a40a4a579", "stripped_sparse_sha256": "b6855b9095fd54e6d8013b2e0ccb908b6f6319083421f1
- [PASS] sparse_policy_block_djangocms-rc-06ecf3a8e8de — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-06ecf3a8e8de — []
- [PASS] intent_present_djangocms-rc-06ecf3a8e8de — "fix: Update transifex source file (#7629) * Fix css glitch * Update translations"
- [PASS] candidate_ids_1_n_djangocms-rc-06ecf3a8e8de — 140
- [PASS] prompt_control_proof_djangocms-rc-0daae01f2f65 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "ef021c734542d6d25849f10413ccf8a287459f0df5b4933e6dd818337ca3cb23", "stripped_sparse_sha256": "ef021c734542d6d25849f10413ccf8a287459f0df5b493
- [PASS] sparse_policy_block_djangocms-rc-0daae01f2f65 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-0daae01f2f65 — []
- [PASS] intent_present_djangocms-rc-0daae01f2f65 — "Fixed #6201 -- Don't allow users to paste a page if it doesn't have translations"
- [PASS] candidate_ids_1_n_djangocms-rc-0daae01f2f65 — 152
- [PASS] prompt_control_proof_djangocms-rc-0fec81224889 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "007982d20781a75fce75999661499b15ac1f18d0b1d58e00d09da33dc03b2b5f", "stripped_sparse_sha256": "007982d20781a75fce75999661499b15ac1f18d0b1d58e
- [PASS] sparse_policy_block_djangocms-rc-0fec81224889 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-0fec81224889 — []
- [PASS] intent_present_djangocms-rc-0fec81224889 — "Deprecate the core Alias plugin (#6918) * Add a deprecation comment in the Alias"
- [PASS] candidate_ids_1_n_djangocms-rc-0fec81224889 — 140
- [PASS] prompt_control_proof_djangocms-rc-1031d20fca28 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "e78b5c8f547129ce96061fa4f75e34451cdca879695d9cc7e8b20a711799e0a0", "stripped_sparse_sha256": "e78b5c8f547129ce96061fa4f75e34451cdca879695d9c
- [PASS] sparse_policy_block_djangocms-rc-1031d20fca28 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-1031d20fca28 — []
- [PASS] intent_present_djangocms-rc-1031d20fca28 — "fix: Replaced `languages` field from `Page` which used to become inconsistent (#"
- [PASS] candidate_ids_1_n_djangocms-rc-1031d20fca28 — 144
- [PASS] prompt_control_proof_djangocms-rc-138abbb7e5f4 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "8a7d121700679d5544e5bed46acb1ca72ea737b3c65d19121d876909ad7014bf", "stripped_sparse_sha256": "8a7d121700679d5544e5bed46acb1ca72ea737b3c65d19
- [PASS] sparse_policy_block_djangocms-rc-138abbb7e5f4 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-138abbb7e5f4 — []
- [PASS] intent_present_djangocms-rc-138abbb7e5f4 — "More efficient implementation of get_text_enabled_plugins (#5816)"
- [PASS] candidate_ids_1_n_djangocms-rc-138abbb7e5f4 — 148
- [PASS] prompt_control_proof_djangocms-rc-1ff5bf9149b4 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "bd9223835ccdef8e254e6a48a59f580ff7445480c2c506134124912efad9a587", "stripped_sparse_sha256": "bd9223835ccdef8e254e6a48a59f580ff7445480c2c506
- [PASS] sparse_policy_block_djangocms-rc-1ff5bf9149b4 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-1ff5bf9149b4 — []
- [PASS] intent_present_djangocms-rc-1ff5bf9149b4 — "Fixed #6205 -- Require \"Change advanced settings\" permission to change template "
- [PASS] candidate_ids_1_n_djangocms-rc-1ff5bf9149b4 — 152
- [PASS] prompt_control_proof_djangocms-rc-28ddd6d10308 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "efe88ae36258aa9fe213d0a2837ca48209240d895f43889bf94e2add8a44267c", "stripped_sparse_sha256": "efe88ae36258aa9fe213d0a2837ca48209240d895f4388
- [PASS] sparse_policy_block_djangocms-rc-28ddd6d10308 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-28ddd6d10308 — []
- [PASS] intent_present_djangocms-rc-28ddd6d10308 — "Fix page tree w/ empty page contents and language-aware adding of new page conte"
- [PASS] candidate_ids_1_n_djangocms-rc-28ddd6d10308 — 140
- [PASS] prompt_control_proof_djangocms-rc-2efae8e43bd6 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "69fe0a38da64b60b3043fe4868833d883c139034fc613ac51f08c862f0fdb2f6", "stripped_sparse_sha256": "69fe0a38da64b60b3043fe4868833d883c139034fc613a
- [PASS] sparse_policy_block_djangocms-rc-2efae8e43bd6 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-2efae8e43bd6 — []
- [PASS] intent_present_djangocms-rc-2efae8e43bd6 — "fix: Grouper models w/o must not assume language grouper (#8194) * fix: Grouper "
- [PASS] candidate_ids_1_n_djangocms-rc-2efae8e43bd6 — 144
- [PASS] prompt_control_proof_djangocms-rc-33fbdb18e5d4 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "d413e5401f5c03bd9316bc9f6ae893c5110b5eb8541fc89a316bbcb20aeb6e90", "stripped_sparse_sha256": "d413e5401f5c03bd9316bc9f6ae893c5110b5eb8541fc8
- [PASS] sparse_policy_block_djangocms-rc-33fbdb18e5d4 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-33fbdb18e5d4 — []
- [PASS] intent_present_djangocms-rc-33fbdb18e5d4 — "fix ruff"
- [PASS] candidate_ids_1_n_djangocms-rc-33fbdb18e5d4 — 140
- [PASS] prompt_control_proof_djangocms-rc-39442083f18a — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "0831611c8ca5e9d9750c3fbc7895db219085d5e661cab018d18ac4fd99657887", "stripped_sparse_sha256": "0831611c8ca5e9d9750c3fbc7895db219085d5e661cab0
- [PASS] sparse_policy_block_djangocms-rc-39442083f18a — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-39442083f18a — []
- [PASS] intent_present_djangocms-rc-39442083f18a — "Fixes #6189 -- Use only published languages when rendering LanguageChanger for p"
- [PASS] candidate_ids_1_n_djangocms-rc-39442083f18a — 152
- [PASS] prompt_control_proof_djangocms-rc-3f8fcb5fb63b — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "6ac9b3b1c46c71325a8c267466815079777c928aa0a879f098e3ced733c72d34", "stripped_sparse_sha256": "6ac9b3b1c46c71325a8c267466815079777c928aa0a879
- [PASS] sparse_policy_block_djangocms-rc-3f8fcb5fb63b — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-3f8fcb5fb63b — []
- [PASS] intent_present_djangocms-rc-3f8fcb5fb63b — "fix: Correct ContentRenderer logic for toolbar and page content handling (#8092)"
- [PASS] candidate_ids_1_n_djangocms-rc-3f8fcb5fb63b — 144
- [PASS] prompt_control_proof_djangocms-rc-47b63015feb1 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "72bba093e107c3327a3a8002dffc93be3272600e0441d8eca4a1b076393975ed", "stripped_sparse_sha256": "72bba093e107c3327a3a8002dffc93be3272600e0441d8
- [PASS] sparse_policy_block_djangocms-rc-47b63015feb1 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-47b63015feb1 — []
- [PASS] intent_present_djangocms-rc-47b63015feb1 — "feat: Improved delete page confirmation message (#8070) * first stab at delete c"
- [PASS] candidate_ids_1_n_djangocms-rc-47b63015feb1 — 144
- [PASS] prompt_control_proof_djangocms-rc-497c3c67e813 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "5a8b398fbca5513c4c578cf17121dc53f3260e4e4fd4e29c601720ab795ed2b8", "stripped_sparse_sha256": "5a8b398fbca5513c4c578cf17121dc53f3260e4e4fd4e2
- [PASS] sparse_policy_block_djangocms-rc-497c3c67e813 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-497c3c67e813 — []
- [PASS] intent_present_djangocms-rc-497c3c67e813 — "Optimize populating title cache for Page model. (#7177) * Optimize populating ti"
- [PASS] candidate_ids_1_n_djangocms-rc-497c3c67e813 — 140
- [PASS] prompt_control_proof_djangocms-rc-4b8089b8b686 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "36280155d8a5c25d521dfc2db7e17307a2d80fa4d75afdcc8256db2c4d039787", "stripped_sparse_sha256": "36280155d8a5c25d521dfc2db7e17307a2d80fa4d75afd
- [PASS] sparse_policy_block_djangocms-rc-4b8089b8b686 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-4b8089b8b686 — []
- [PASS] intent_present_djangocms-rc-4b8089b8b686 — "Fixed #5752 -- Move pages relative to left or right siblings (#5770)"
- [PASS] candidate_ids_1_n_djangocms-rc-4b8089b8b686 — 148
- [PASS] prompt_control_proof_djangocms-rc-5ff38b521274 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "38495a04f3f23c28cca59ede09d50e45ca6880ba7a513e2ce92cc3c91ea05b5a", "stripped_sparse_sha256": "38495a04f3f23c28cca59ede09d50e45ca6880ba7a513e
- [PASS] sparse_policy_block_djangocms-rc-5ff38b521274 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-5ff38b521274 — []
- [PASS] intent_present_djangocms-rc-5ff38b521274 — "feat: graceful plugin exceptions (#7423) * Fix: Catch exceptions caused by missi"
- [PASS] candidate_ids_1_n_djangocms-rc-5ff38b521274 — 140
- [PASS] prompt_control_proof_djangocms-rc-807a87b1de71 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "e32defa2463fb6b7db170be555accf1c09f6f2cb06d50ebaece9ededdfb79414", "stripped_sparse_sha256": "e32defa2463fb6b7db170be555accf1c09f6f2cb06d50e
- [PASS] sparse_policy_block_djangocms-rc-807a87b1de71 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-807a87b1de71 — []
- [PASS] intent_present_djangocms-rc-807a87b1de71 — "fix: Remove `can_publish` permission from django CMS 4 core (#7635) * Fix css gl"
- [PASS] candidate_ids_1_n_djangocms-rc-807a87b1de71 — 140
- [PASS] prompt_control_proof_djangocms-rc-9e508ff1c41e — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "6710374e2f3bcd22635aafc3f65b3aceaaa6900790c066810d9fe73a4d3573ab", "stripped_sparse_sha256": "6710374e2f3bcd22635aafc3f65b3aceaaa6900790c066
- [PASS] sparse_policy_block_djangocms-rc-9e508ff1c41e — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-9e508ff1c41e — []
- [PASS] intent_present_djangocms-rc-9e508ff1c41e — "Deprecated CMSPluginBase attribute; removed deprecated CMSPlugin methods (#5829)"
- [PASS] candidate_ids_1_n_djangocms-rc-9e508ff1c41e — 148
- [PASS] prompt_control_proof_djangocms-rc-a1ac04d3f817 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "4f86689218187d6ff89c813311e9bef5f2cf02e33cbc3aff29621e3f2adf681b", "stripped_sparse_sha256": "4f86689218187d6ff89c813311e9bef5f2cf02e33cbc3a
- [PASS] sparse_policy_block_djangocms-rc-a1ac04d3f817 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-a1ac04d3f817 — []
- [PASS] intent_present_djangocms-rc-a1ac04d3f817 — "Optionally disable the sideframe (#6553)"
- [PASS] candidate_ids_1_n_djangocms-rc-a1ac04d3f817 — 140
- [PASS] prompt_control_proof_djangocms-rc-a7df58dc5ff3 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "679c4ff12ce2940207c4191238e311bb3ec68a74f7089c59892a91ca41643999", "stripped_sparse_sha256": "679c4ff12ce2940207c4191238e311bb3ec68a74f7089c
- [PASS] sparse_policy_block_djangocms-rc-a7df58dc5ff3 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-a7df58dc5ff3 — []
- [PASS] intent_present_djangocms-rc-a7df58dc5ff3 — "Rename default persist param"
- [PASS] candidate_ids_1_n_djangocms-rc-a7df58dc5ff3 — 140
- [PASS] prompt_control_proof_djangocms-rc-a9e2a8d3b7a6 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "498fbdb4b0f4c432b255230dacd53e82f10376a061daa0cc505708d6943c97b4", "stripped_sparse_sha256": "498fbdb4b0f4c432b255230dacd53e82f10376a061daa0
- [PASS] sparse_policy_block_djangocms-rc-a9e2a8d3b7a6 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-a9e2a8d3b7a6 — []
- [PASS] intent_present_djangocms-rc-a9e2a8d3b7a6 — "Mark CMSPlugin.render_plugin as PendingDeprecation"
- [PASS] candidate_ids_1_n_djangocms-rc-a9e2a8d3b7a6 — 148
- [PASS] prompt_control_proof_djangocms-rc-ac74c212719f — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "5f203ccee49f9354ecc7c7c0d20a1fb52c456009d20ea65f34995051adf1925a", "stripped_sparse_sha256": "5f203ccee49f9354ecc7c7c0d20a1fb52c456009d20ea6
- [PASS] sparse_policy_block_djangocms-rc-ac74c212719f — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-ac74c212719f — []
- [PASS] intent_present_djangocms-rc-ac74c212719f — "Fix: Open new plugin window in language of toolbar not of page (#7632)"
- [PASS] candidate_ids_1_n_djangocms-rc-ac74c212719f — 140
- [PASS] prompt_control_proof_djangocms-rc-ada585d3f358 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "4d878907655904b80f714df3f876a85d9ad4b28e149dcb4da27eb362514e4e72", "stripped_sparse_sha256": "4d878907655904b80f714df3f876a85d9ad4b28e149dcb
- [PASS] sparse_policy_block_djangocms-rc-ada585d3f358 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-ada585d3f358 — []
- [PASS] intent_present_djangocms-rc-ada585d3f358 — "fix: Complete #8176 (#8178) * fix: Show toolbar on v4 endpoints even if `CMS_HID"
- [PASS] candidate_ids_1_n_djangocms-rc-ada585d3f358 — 144
- [PASS] prompt_control_proof_djangocms-rc-c02308fc5261 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "0dd1380e9fba8bb2941d3d377c7faa4ccbd663ee7ecd33e0bdfc3fa96173739e", "stripped_sparse_sha256": "0dd1380e9fba8bb2941d3d377c7faa4ccbd663ee7ecd33
- [PASS] sparse_policy_block_djangocms-rc-c02308fc5261 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-c02308fc5261 — []
- [PASS] intent_present_djangocms-rc-c02308fc5261 — "Add CMSAppExtension.ready which is called after all cms app configs are loaded ("
- [PASS] candidate_ids_1_n_djangocms-rc-c02308fc5261 — 140
- [PASS] prompt_control_proof_djangocms-rc-ca16415b1022 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "e445e957e386bc14ed07c3886418aa4e9a2dfb1a090f1a027f89e82c4c5c0229", "stripped_sparse_sha256": "e445e957e386bc14ed07c3886418aa4e9a2dfb1a090f1a
- [PASS] sparse_policy_block_djangocms-rc-ca16415b1022 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-ca16415b1022 — []
- [PASS] intent_present_djangocms-rc-ca16415b1022 — "Added language to Page translation operations"
- [PASS] candidate_ids_1_n_djangocms-rc-ca16415b1022 — 140
- [PASS] prompt_control_proof_djangocms-rc-d88932559b00 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "bda89559fed1954dcd812c2f5ae2d069aa244f6b9b8ec71a8eb9eeee5f28fa69", "stripped_sparse_sha256": "bda89559fed1954dcd812c2f5ae2d069aa244f6b9b8ec7
- [PASS] sparse_policy_block_djangocms-rc-d88932559b00 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-d88932559b00 — []
- [PASS] intent_present_djangocms-rc-d88932559b00 — "Patch defects (#6930) Co-authored-by: Adam Murray <adam@Adams-MacBook-Pro-2.loca"
- [PASS] candidate_ids_1_n_djangocms-rc-d88932559b00 — 140
- [PASS] prompt_control_proof_djangocms-rc-e3a23a7fc757 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "79c7d11dab14342301f04317db9f487d9b853efdf2b1d306d55720ec09d2c3cd", "stripped_sparse_sha256": "79c7d11dab14342301f04317db9f487d9b853efdf2b1d3
- [PASS] sparse_policy_block_djangocms-rc-e3a23a7fc757 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-e3a23a7fc757 — []
- [PASS] intent_present_djangocms-rc-e3a23a7fc757 — "Removed resolve view"
- [PASS] candidate_ids_1_n_djangocms-rc-e3a23a7fc757 — 140
- [PASS] prompt_control_proof_djangocms-rc-e429b4584a16 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "8c7e8d1f9c5ec9599812fc833a9bd5559453c01e51239d1de34ebadd62dc987d", "stripped_sparse_sha256": "8c7e8d1f9c5ec9599812fc833a9bd5559453c01e51239d
- [PASS] sparse_policy_block_djangocms-rc-e429b4584a16 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-e429b4584a16 — []
- [PASS] intent_present_djangocms-rc-e429b4584a16 — "Provide a general get method that can be monkeypatched (#6806) * Provide a gener"
- [PASS] candidate_ids_1_n_djangocms-rc-e429b4584a16 — 140
- [PASS] prompt_control_proof_djangocms-rc-e88032bf704c — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "6c6d40076c016869f4acde1028be91354113ebaa78bb083c1d051fc0e93d1843", "stripped_sparse_sha256": "6c6d40076c016869f4acde1028be91354113ebaa78bb08
- [PASS] sparse_policy_block_djangocms-rc-e88032bf704c — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-e88032bf704c — []
- [PASS] intent_present_djangocms-rc-e88032bf704c — "chore: Merge `release/build` into `release/4.1.x` (#7729) * [4.1.0 release proce"
- [PASS] candidate_ids_1_n_djangocms-rc-e88032bf704c — 143
- [PASS] prompt_control_proof_djangocms-rc-f2c367ddc7b1 — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "a5c6ae312fb0eac2f994305a5a9b76f5c65f20982bb571f55d52a27d134cab39", "stripped_sparse_sha256": "a5c6ae312fb0eac2f994305a5a9b76f5c65f20982bb571
- [PASS] sparse_policy_block_djangocms-rc-f2c367ddc7b1 — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-f2c367ddc7b1 — []
- [PASS] intent_present_djangocms-rc-f2c367ddc7b1 — "fix: Adjust tests for updated django 5.2 admin templates (#8095) * fix: Adjust t"
- [PASS] candidate_ids_1_n_djangocms-rc-f2c367ddc7b1 — 144
- [PASS] prompt_control_proof_djangocms-rc-ff6cb9b5dced — {"PROMPT_CONTROLLED_DIFF": "PASS", "stripped_full_sha256": "abb963521ab76199bd9fe2d062137ee94aca03005357ab9c2115b753a9b730ef", "stripped_sparse_sha256": "abb963521ab76199bd9fe2d062137ee94aca03005357ab
- [PASS] sparse_policy_block_djangocms-rc-ff6cb9b5dced — "SPARSE policy block present"
- [PASS] no_hidden_proxy_marker_in_prompt_djangocms-rc-ff6cb9b5dced — []
- [PASS] intent_present_djangocms-rc-ff6cb9b5dced — "feat: Added pre-migrate hook to check version 4 is intentional (#7249)"
- [PASS] candidate_ids_1_n_djangocms-rc-ff6cb9b5dced — 140
- [PASS] zero_model_calls_prompt_render — "pure string rendering; no backend constructed"

## Gate 3 — Pipeline Smoke Test

- [PASS] prompt_renders — {"prompt_len": 16366}
- [PASS] mock_sparse_decode_valid — {"valid": true, "count": 140}
- [PASS] mock_metrics_exact_fixture — {"tp": 1, "fp": 0, "fn": 0, "precision": 1.0, "recall": 1.0, "f1": 1.0, "fnr": 0.0}
- [PASS] zero_model_calls_smoke — "fixture encode/decode only"

## Gate 4 — Dry Run

- [PASS] slice_cell_count_6 — 6
- [PASS] slice_run_ids_unique — 6
- [PASS] row_shape_contract — "13 fields"
- [PASS] frozen_config_slice — "sparse_v2 / qwen3-coder / deepinfra-turbo / temp0 / cap16384"
- [PASS] zero_model_calls_dry_run — "manifest-shape proof only"

## Gate 5 — Integration Test

- [PASS] manifest_exactly_90 — 90
- [PASS] manifest_30_unique_cases — 30
- [PASS] manifest_three_reps_each — "30 cases x 3 reps = 90"
- [PASS] manifest_sparse_only — ["sparse_v2"]
- [PASS] manifest_protocol_frozen — "real-commit-p1-v1.0.0"
- [PASS] run_records_schema_fields — {"missing": [], "n_fields": 60}
- [PASS] raw_sha256_sidecar_contract — {"raw_bytes": 42, "sha256": "529d33075bfbefc1cffb60b5ee3f750eecb924625522eb9396a800c7a918da28"}
- [PASS] zero_model_calls_integration — "schema + manifest proof only"

## Gate 6 — Metric Verification

- [PASS] micro_precision_recall_f1_recomputed — {"computed": {"tp": 3, "fp": 1, "fn": 0, "precision": 0.75, "recall": 1.0, "f1": 0.8571428571428571, "fnr": 0.0, "full_recall": true, "proxy_size": 3, "predicted_size": 4}, "expected": {"precision": 0
- [PASS] empty_prediction_fail_closed_metrics — {"tp": 0, "fp": 0, "fn": 1, "precision": 0.0, "recall": 0.0, "f1": 0.0, "fnr": 1.0, "full_recall": false, "proxy_size": 1, "predicted_size": 0}
- [PASS] sparse_explicit_preserve_rejected — "SPARSE-v2 must not contain explicit PRESERVE rows"

## Independent Audit (pre-run preconditions)

- [PASS] features_no_proxy_loader — extractor is proxy-free by construction
- [PASS] heldout_never_in_manifest — no HELD_OUT_TEST case in any of the 90 cells
- [PASS] feature_extraction_deterministic — byte-identical feature dicts
- [PASS] task_level_unit_30_tasks — N=30 independent tasks; 3 nested repetitions per task
- [PASS] phase_b_gate_a_precondition — TRAIN/VALIDATION Sparse-v2 predictions absent before this run

## Scientific discipline

- Historical diff is an OBSERVED CHANGE-SET PROXY, never semantic ground truth.
- Independent task = historical change; repeated model calls are nested observations.
- HELD_OUT_TEST is never used for any decision in this run.