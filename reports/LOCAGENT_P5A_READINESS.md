# P5-A — LocAgent Shared-Protocol Adapter Readiness (ZERO API)

**Generated:** 2026-09-14T04:21:05.287305+00:00
**Upstream:** https://github.com/gersteinlab/LocAgent @ `4935b557326c154bad8e8dcf3747cc8d32d1f387` (2026-08-12, Apache-2.0)
**Adapter version:** locagent-shared-protocol-adapter-1

ZERO scientific LLM/API calls. HELD_OUT_TEST is never used for adapter development or validation (frozen P0_TO_P5 §P5-B rule).

## 1. Upstream pin check

- **pinned_commit:** 4935b557326c154bad8e8dcf3747cc8d32d1f387
- **pinned_date:** 2026-08-12
- **license:** Apache-2.0
- **no_vendoring:** True
- **input_fields:** ['instance_id', 'repo', 'base_commit', 'problem_statement', 'patch']

## 2. Dry-run manifest (36 allowed cases)

| case_id | split | base_commit | problem_statement_chars | patch_chars | candidate_count | input_sha256 |
|---|---|---|---|---|---|---|
| djangocms-rc-06ecf3a8e8de | TRAIN | 369f776893 | 164 | 0 | 140 | dc67cbe6a30e9cfc |
| djangocms-rc-0daae01f2f65 | VALIDATION | d7ee89da24 | 97 | 0 | 152 | 86e9b8675e6f7a04 |
| djangocms-rc-0fec81224889 | VALIDATION | 68947484a8 | 114 | 0 | 140 | 62538795a10fc0df |
| djangocms-rc-1031d20fca28 | VALIDATION | 76c5bb0583 | 371 | 0 | 144 | 4e487be34b9bcdf9 |
| djangocms-rc-110d4c740927 | MINER_DEV | 50c3576080 | 189 | 0 | 144 | 7b774b3fd5d770dc |
| djangocms-rc-138abbb7e5f4 | TRAIN | ad20bd3eee | 65 | 0 | 148 | 4a619f55adc2c6a9 |
| djangocms-rc-1ff5bf9149b4 | TRAIN | bd7a63bc6f | 87 | 0 | 152 | b1e69543154a2773 |
| djangocms-rc-28ddd6d10308 | TRAIN | 2dbc833bcc | 657 | 0 | 140 | 1595948eb05090ea |
| djangocms-rc-2efae8e43bd6 | TRAIN | 71d94bed47 | 1012 | 0 | 144 | b8e1396b54899f1e |
| djangocms-rc-33fbdb18e5d4 | TRAIN | e703659d3c | 8 | 0 | 140 | bb0be68f5d885f5c |
| djangocms-rc-39442083f18a | TRAIN | ba16eb9a1d | 98 | 0 | 152 | 207dd1be572bc8db |
| djangocms-rc-3f8fcb5fb63b | TRAIN | 58eb76bb94 | 229 | 0 | 144 | 8e63776c0a2acf3e |
| djangocms-rc-47040a2887ca | MINER_DEV | 8f9ed64184 | 581 | 0 | 144 | e6297156f0559c04 |
| djangocms-rc-47b63015feb1 | VALIDATION | c7208ed1b1 | 270 | 0 | 144 | 6cb47437320248d5 |
| djangocms-rc-497c3c67e813 | TRAIN | 9945a0f889 | 247 | 0 | 140 | 1054a701b0a15b7e |
| djangocms-rc-4b8089b8b686 | TRAIN | 5e032e6933 | 68 | 0 | 148 | 3c682841454d33e1 |
| djangocms-rc-5ff38b521274 | TRAIN | 6c64fddb54 | 259 | 0 | 140 | ea2baae46f103a3d |
| djangocms-rc-807a87b1de71 | TRAIN | 121acf1cc1 | 204 | 0 | 140 | d9f9ef50a33ccf12 |
| djangocms-rc-888ee6eeef91 | MINER_DEV | ada585d3f3 | 314 | 0 | 144 | a130dec274c96c72 |
| djangocms-rc-9e508ff1c41e | TRAIN | a9efe5e98d | 369 | 0 | 148 | a522627efee89df0 |
| djangocms-rc-a1ac04d3f817 | TRAIN | 4e4d1cb1f9 | 40 | 0 | 140 | 91312bb2739e53ce |
| djangocms-rc-a7df58dc5ff3 | TRAIN | 085ab6d13e | 28 | 0 | 140 | 4985988d5d45e9a8 |
| djangocms-rc-a9e2a8d3b7a6 | VALIDATION | 78bb22df5c | 50 | 0 | 148 | 3dd096fa881c1356 |
| djangocms-rc-ac74c212719f | TRAIN | 06ecf3a8e8 | 70 | 0 | 140 | 91a3ea9a243de42f |
| djangocms-rc-ada585d3f358 | TRAIN | 0b775f2730 | 185 | 0 | 144 | d7ee2b95c5fafb0f |
| djangocms-rc-c02308fc5261 | TRAIN | 0fec812248 | 144 | 0 | 140 | 3267bd8175875c35 |
| djangocms-rc-c30efd44e92e | MINER_DEV | 888ee6eeef | 241 | 0 | 144 | e6e40dbdf1485a42 |
| djangocms-rc-ca16415b1022 | TRAIN | 4981c6229e | 45 | 0 | 140 | 2e77668235053dbf |
| djangocms-rc-d88932559b00 | TRAIN | f30f0204a8 | 139 | 0 | 140 | 17fab5615ed7579a |
| djangocms-rc-e008ff4b5c21 | MINER_DEV | 8d50660e7b | 366 | 0 | 144 | 81206cb2860147f5 |
| djangocms-rc-e3a23a7fc757 | VALIDATION | 0e885ca9e2 | 20 | 0 | 140 | 8f8561bd54bdc98c |
| djangocms-rc-e429b4584a16 | TRAIN | 5bfb1d144a | 343 | 0 | 140 | 9ff4b57ea1918754 |
| djangocms-rc-e88032bf704c | TRAIN | b98b0510e4 | 520 | 0 | 143 | b9de23eb46f5e733 |
| djangocms-rc-f2c367ddc7b1 | TRAIN | 3f8fcb5fb6 | 252 | 0 | 144 | b6e497abedd28979 |
| djangocms-rc-fd608e896daf | MINER_DEV | 23824547e0 | 186 | 0 | 144 | 6828d03bcf50ddb7 |
| djangocms-rc-ff6cb9b5dced | TRAIN | ee89fe4f44 | 70 | 0 | 140 | 70f348359dd8e974 |

## 3. Common-evaluator checks (deterministic, ZERO API)

- [PASS] locagent_output_parser_valid — ['cms/admin/forms.py', 'cms/models/pagemodel.py', 'cms/api.py']
- [PASS] common_evaluator_metrics — {'precision': 1.0, 'recall': 0.6666666666666666, 'f1': 0.8, 'fnr': 0.3333333333333333}
- [PASS] adapter_patch_empty_all_cases — patch field EMPTY/non-informative for every allowed case
- [PASS] no_held_out_in_dryrun — splits used: MINER_DEV,TRAIN,VALIDATION
- [PASS] upstream_pin_frozen — 4935b557326c154bad8e8dcf3747cc8d32d1f387

## 4. Scientific discipline

- Adapter inputs are PARENT-ONLY: repo identity, base commit, visible intent; the `patch` field is EMPTY (never the hidden target patch).
- The hidden observed-change proxy / target diff / gold labels never appear in any LocAgent input (leakage barrier enforced fail-closed).
- LocAgent native `Acc@K` is reported separately and is never mixed with the common F1 in one performance column.