# RealCommitImpactDataset-v1 (M4A-2) — Scientific Corpus Adjudication

**Generated:** 2026-09-13T20:11:09.261278+00:00
**Miner version:** real-commit-miner-v1.0.0
**Window:** newest 6000 ancestors of the frozen anchor

## 1. Commits scanned

- Ancestors scanned (newest-first, window): 6000
- Eligible after frozen eligibility + leakage barrier + MINER_DEV exclusion: 916

## 2. Exclusion counts by reason code

- `diff_too_large`: 14
- `generated_or_vendor_only`: 1553
- `intent_path_leakage`: 92
- `merge_commit`: 1346
- `migrations_only`: 27
- `miner_dev_target`: 6
- `no_meaningful_intent`: 356
- `no_production_source_change`: 901
- `production_add_delete_rename_copy_v1_unsupported`: 41
- `proxy_too_large`: 22
- `tests_only`: 721
- `whitespace_only`: 4

## 3. Duplicate / related-change adjudication (R1/R2/R3)

- Total adjudication records: 587
- `R1_exact_proxy_set`: 582
- `R2_shared_pr_reference`: 0
- `R3_suspected_related`: 5

### R3 suspected-related pairs (overlapping proxy + intent Jaccard ≥ 0.5)

- R3 is adjudicated by a deterministic same-change predicate (`_messages_describe_same_change`): identical / token-subset / ≥3-shared-token intents are treated as the same/continuation change → keep the newest; otherwise BOTH are kept (the frozen protocol's `otherwise both are kept` branch is implemented, never silently dropping a possibly-independent change).
- Adjudication is corpus-invariant by construction and verified: the selected scientific corpus is identical with or without R3 exclusion.

- Kept `967b838d06ec` vs excluded `664426f7e255` (Jaccard 0.5, same change): shared proxy paths and intent Jaccard 0.50 >= 0.5; messages describe the same/continuation change; keep the newest ('Dropped support for Django < 1.11' vs 'Drop support for Django 1.7.')
- Kept `b740724656f0` vs excluded `83ecb2ffcc28` (Jaccard 0.667, same change): shared proxy paths and intent Jaccard 0.67 >= 0.5; messages describe the same/continuation change; keep the newest ('Initial compatibility' vs 'Initial compatibility effort')
- Kept `7c6cfad6fdd4` vs excluded `def08149617f` (Jaccard 0.667, same change): shared proxy paths and intent Jaccard 0.67 >= 0.5; messages describe the same/continuation change; keep the newest ('More fixes' vs 'More context fixes')
- Kept `62f027357194` vs excluded `d99f1cfc3e11` (Jaccard 1.0, same change): shared proxy paths and intent Jaccard 1.00 >= 0.5; messages describe the same/continuation change; keep the newest ('fixes failing tests' vs 'fixes failing tests')
- Kept `0526cdde8118` vs excluded `758da5b98762` (Jaccard 1.0, same change): shared proxy paths and intent Jaccard 1.00 >= 0.5; messages describe the same/continuation change; keep the newest ('fixes issue with page menu missing' vs 'fixes issue with page menu missing')

## 4. Accepted count

- **40** scientific cases accepted

## 5. Proxy-size distribution

- proxy size 1: 13
- proxy size 2: 12
- proxy size 3: 8
- proxy size 5: 3
- proxy size 6: 1
- proxy size 7: 1
- proxy size 9: 1
- proxy size 12: 1

## 6. Change-type distribution (intent-derived conservative taxonomy)

- `bugfix`: 10
- `chore`: 2
- `feature`: 4
- `unknown`: 24

## 7. Temporal distribution (target commit year)

- 2016: 4
- 2017: 5
- 2018: 5
- 2020: 5
- 2021: 1
- 2022: 5
- 2023: 5
- 2024: 5
- 2025: 5

## 8. Intent-source quality notes

- `intent_source` is the normalized commit message only (frozen M4A-1 choice); no PR body / linked-issue mining (would require network/API).
- Scientific cases with `intent_mentions_changed_path=true` are INELIGIBLE (leakage barrier).
- Intent quality is variable by era; the year-capped selection favors recent PR-referenced conventional commits while retaining temporal spread.

## 9. Accepted-case table (parent / target / proxy size)

| case_id | parent | target | year | proxy_size | change_type | split |
|---|---|---|---|---|---|---|
| djangocms-rc-8d50660e7bcf | f26278ceeef5 | 8d50660e7bcf | 2025-04-28 | 5 | bugfix | HELD_OUT_TEST |
| djangocms-rc-2efae8e43bd6 | 71d94bed47b5 | 2efae8e43bd6 | 2025-03-31 | 1 | bugfix | TRAIN |
| djangocms-rc-fdda30c271f0 | c37fa0b7eefd | fdda30c271f0 | 2025-03-27 | 3 | bugfix | HELD_OUT_TEST |
| djangocms-rc-50c3576080be | c30efd44e92e | 50c3576080be | 2025-03-20 | 12 | chore | HELD_OUT_TEST |
| djangocms-rc-ada585d3f358 | 0b775f27300c | ada585d3f358 | 2025-03-13 | 1 | bugfix | TRAIN |
| djangocms-rc-f2c367ddc7b1 | 3f8fcb5fb63b | f2c367ddc7b1 | 2024-12-13 | 1 | bugfix | TRAIN |
| djangocms-rc-3f8fcb5fb63b | 58eb76bb9460 | 3f8fcb5fb63b | 2024-12-09 | 1 | bugfix | TRAIN |
| djangocms-rc-9e33db4f4660 | 47b63015feb1 | 9e33db4f4660 | 2024-12-03 | 2 | bugfix | HELD_OUT_TEST |
| djangocms-rc-47b63015feb1 | c7208ed1b1ad | 47b63015feb1 | 2024-12-01 | 2 | feature | VALIDATION |
| djangocms-rc-1031d20fca28 | 76c5bb05837a | 1031d20fca28 | 2024-11-27 | 9 | bugfix | VALIDATION |
| djangocms-rc-e88032bf704c | b98b0510e44f | e88032bf704c | 2023-12-27 | 2 | chore | TRAIN |
| djangocms-rc-807a87b1de71 | 121acf1cc1cc | 807a87b1de71 | 2023-10-16 | 7 | bugfix | TRAIN |
| djangocms-rc-ac74c212719f | 06ecf3a8e8de | ac74c212719f | 2023-08-23 | 2 | unknown | TRAIN |
| djangocms-rc-06ecf3a8e8de | 369f77689346 | 06ecf3a8e8de | 2023-08-22 | 1 | bugfix | TRAIN |
| djangocms-rc-33fbdb18e5d4 | e703659d3c07 | 33fbdb18e5d4 | 2023-08-08 | 2 | unknown | TRAIN |
| djangocms-rc-b39799f9fc1c | d3615ee27005 | b39799f9fc1c | 2022-12-08 | 5 | feature | HELD_OUT_TEST |
| djangocms-rc-497c3c67e813 | 9945a0f8899d | 497c3c67e813 | 2022-11-25 | 1 | unknown | TRAIN |
| djangocms-rc-5ff38b521274 | 6c64fddb5407 | 5ff38b521274 | 2022-11-11 | 2 | feature | TRAIN |
| djangocms-rc-28ddd6d10308 | 2dbc833bccf1 | 28ddd6d10308 | 2022-10-28 | 3 | unknown | TRAIN |
| djangocms-rc-ff6cb9b5dced | ee89fe4f44fb | ff6cb9b5dced | 2022-08-19 | 3 | feature | TRAIN |
| djangocms-rc-66c70394c9e1 | 29ae26eafa0a | 66c70394c9e1 | 2021-04-10 | 1 | unknown | HELD_OUT_TEST |
| djangocms-rc-d88932559b00 | f30f0204a8c3 | d88932559b00 | 2020-11-05 | 2 | unknown | TRAIN |
| djangocms-rc-c02308fc5261 | 0fec81224889 | c02308fc5261 | 2020-10-29 | 3 | unknown | TRAIN |
| djangocms-rc-0fec81224889 | 68947484a870 | 0fec81224889 | 2020-10-29 | 3 | unknown | VALIDATION |
| djangocms-rc-75978fb1c3ad | f1226a57b767 | 75978fb1c3ad | 2020-07-08 | 1 | unknown | HELD_OUT_TEST |
| djangocms-rc-e429b4584a16 | 5bfb1d144a83 | e429b4584a16 | 2020-02-26 | 2 | unknown | TRAIN |
| djangocms-rc-a1ac04d3f817 | 4e4d1cb1f941 | a1ac04d3f817 | 2018-12-11 | 2 | unknown | TRAIN |
| djangocms-rc-4307e1b8c2e2 | 4dadf9f1e1f2 | 4307e1b8c2e2 | 2018-09-24 | 1 | unknown | HELD_OUT_TEST |
| djangocms-rc-e3a23a7fc757 | 0e885ca9e273 | e3a23a7fc757 | 2018-09-13 | 3 | unknown | VALIDATION |
| djangocms-rc-a7df58dc5ff3 | 085ab6d13e26 | a7df58dc5ff3 | 2018-09-13 | 1 | unknown | TRAIN |
| djangocms-rc-ca16415b1022 | 4981c6229e82 | ca16415b1022 | 2018-09-05 | 2 | unknown | TRAIN |
| djangocms-rc-1ff5bf9149b4 | bd7a63bc6f57 | 1ff5bf9149b4 | 2017-12-27 | 2 | unknown | TRAIN |
| djangocms-rc-0daae01f2f65 | d7ee89da24ee | 0daae01f2f65 | 2017-12-21 | 5 | unknown | VALIDATION |
| djangocms-rc-630a50361ada | e7bba3abaee1 | 630a50361ada | 2017-12-20 | 1 | unknown | HELD_OUT_TEST |
| djangocms-rc-39442083f18a | ba16eb9a1d09 | 39442083f18a | 2017-12-14 | 1 | unknown | TRAIN |
| djangocms-rc-ba16eb9a1d09 | 19804319f83b | ba16eb9a1d09 | 2017-12-13 | 6 | unknown | HELD_OUT_TEST |
| djangocms-rc-9e508ff1c41e | a9efe5e98dba | 9e508ff1c41e | 2016-12-31 | 2 | unknown | TRAIN |
| djangocms-rc-4b8089b8b686 | 5e032e6933e1 | 4b8089b8b686 | 2016-12-27 | 3 | unknown | TRAIN |
| djangocms-rc-a9e2a8d3b7a6 | 78bb22df5c3f | a9e2a8d3b7a6 | 2016-12-23 | 3 | unknown | VALIDATION |
| djangocms-rc-138abbb7e5f4 | ad20bd3eee57 | 138abbb7e5f4 | 2016-12-22 | 1 | unknown | TRAIN |

## 10. R3 adjudication decisions (every decision with rationale)

- R1 (identical proxy set) and R2 (shared PR reference) are deterministic mechanical dedup rules; their per-commit records are persisted in `reports/real_commit_m4a2_adjudication.json`. R3 below applies the frozen deterministic same-change adjudication (identical / token-subset / ≥3-shared-token intents → keep the newest; otherwise BOTH are kept):
- Kept `967b838d06ec` vs excluded `664426f7e255` (Jaccard 0.5, same change): shared proxy paths and intent Jaccard 0.50 >= 0.5; messages describe the same/continuation change; keep the newest ('Dropped support for Django < 1.11' vs 'Drop support for Django 1.7.')
- Kept `b740724656f0` vs excluded `83ecb2ffcc28` (Jaccard 0.667, same change): shared proxy paths and intent Jaccard 0.67 >= 0.5; messages describe the same/continuation change; keep the newest ('Initial compatibility' vs 'Initial compatibility effort')
- Kept `7c6cfad6fdd4` vs excluded `def08149617f` (Jaccard 0.667, same change): shared proxy paths and intent Jaccard 0.67 >= 0.5; messages describe the same/continuation change; keep the newest ('More fixes' vs 'More context fixes')
- Kept `62f027357194` vs excluded `d99f1cfc3e11` (Jaccard 1.0, same change): shared proxy paths and intent Jaccard 1.00 >= 0.5; messages describe the same/continuation change; keep the newest ('fixes failing tests' vs 'fixes failing tests')
- Kept `0526cdde8118` vs excluded `758da5b98762` (Jaccard 1.0, same change): shared proxy paths and intent Jaccard 1.00 >= 0.5; messages describe the same/continuation change; keep the newest ('fixes issue with page menu missing' vs 'fixes issue with page menu missing')

## 11. Scientific discipline

- The historical diff is an **OBSERVED CHANGE-SET PROXY**, never semantic ground truth; no P/R/V/H gold fabricated from Git diffs.
- All six MINER_DEV cases remain permanently excluded from scientific metrics (`miner_dev_target`).
- ZERO scientific LLM/API calls in this milestone.