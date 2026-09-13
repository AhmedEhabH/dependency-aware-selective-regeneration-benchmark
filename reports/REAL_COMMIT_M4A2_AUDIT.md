# M4A-2 Independent Audit — RealCommitImpactDataset-v1 Scientific Corpus

**Date:** 2026-09-13
**Milestone:** M4A-2 — 40-case scientific real-commit corpus + split freeze
**Branch:** `research/real-commit-impact-dataset-v2-corpus-01`
**Audit path:** `scripts/verify_real_commit_dataset_scientific.py` (reads
persisted artifacts only; never trusts the builder's in-memory objects).
**Result:** **AUDIT=PASS** (610 PASS / 0 FAIL, exit code 0).

---

## Checks performed

### Dataset-level
- scientific manifest exists; **40 cases** (within [30, 40]);
- anchor matches project truth
  (`0f633fc9fa213357f4202482aab2b0edad680f95`).

### Per-case (× 40 cases)
- **Git parent relation** independently re-derived from the cache: every
  target's single parent equals the recorded `parent_commit`;
- **public/hidden physical separation**: `public/` + `hidden/` exist and the
  hidden proxy file is present;
- **hashes recompute**: candidate universe, dependency graph, observed-change
  proxy, intent, and canonical record hashes all recompute to recorded values;
- **candidate/proxy constraints**: proxy ⊆ parent universe; all statuses are
  ordinary `M`; proxy size in [1, 12];
- **leakage barrier**: public bundle contains no hidden proxy filename / field
  names / status marker rows / target diff text / embedded proxy payload /
  semantic gold tokens;
- **scientific strictness**: every split ∈ {TRAIN, VALIDATION, HELD_OUT_TEST},
  `partition_role == SCIENTIFIC`, target is NOT a MINER_DEV target,
  `intent_mentions_changed_path == False`;
- **no scientific API artifacts** created inside any case.

### Split freeze
- per-split counts match (`TRAIN 24 / VALIDATION 6 / HELD_OUT_TEST 10`);
- per-split SHA-256 recomputes;
- split membership == scientific manifest case ids (40/40);
- MINER_DEV disjoint from scientific (no shared case id).

### Frozen M1/M3 regression (unchanged)
- candidate universe count **144**, hash **`43f4279bdf...`** — PASS;
- graph edge count **562**, hash **`0a6bf0f7...`** (node count 144) — PASS.

### Docs state
- README / SYSTEM_STATE / TODO record M4A-2 — PASS.

## Key corpus identities

| Identity | Value |
|---|---|
| Scientific manifest SHA-256 | `9a9e0728f4293d1c4a43a3ec1a5669704e0bc61da2cfdf59e83bcd89c7ac06be` |
| Split freeze canonical SHA-256 | `6a487b926ec4e59f3b1cff30182ebfe0c033fb0e0634a108b57653b84bd0d9b2` |
| TRAIN | 24 cases · SHA-256 `8a0a244d…` |
| VALIDATION | 6 cases · SHA-256 `75a464c2…` |
| HELD_OUT_TEST | 10 cases · SHA-256 `7cd2a609…` |
| Temporal range | 2016 – 2025 (9 years) |

## Scientific discipline

- The historical diff is recorded as **OBSERVED CHANGE-SET PROXY**, never
  semantic ground truth; no P/R/V/H gold fabricated from Git diffs.
- Scientific cases with `intent_path_leakage=true` are INELIGIBLE (92 excluded
  in the scan window).
- The 6 MINER_DEV cases are permanently excluded (`miner_dev_target` = 6).
- No scientific LLM/API calls (all gates + audit deterministic).
- Related/duplicate historical changes do not appear as independent examples
  (R1 exact-set 582, R2 shared-PR 0, R3 suspected-related 5 adjudicated).
- **R3 adjudication-fidelity closure:** R3 is adjudicated by the frozen
  deterministic same-change predicate (`_messages_describe_same_change`);
  the frozen `otherwise both are kept` protocol branch is implemented and
  verified. The 5 flagged R3 pairs all describe the same/continuation change,
  so all decisions are `exclude_older_keep_newest`; the accepted corpus is
  proven **invariant to R3** (identical 40-case selection with or without R3
  exclusion), and the committed adjudication records carry
  `decision_source=deterministic_same_change_predicate`.
- M1/M3 frozen evidence unchanged.

## Usage

```powershell
python scripts/verify_real_commit_dataset_scientific.py
# prints AUDIT=PASS and one line per check; exit code 0.
python scripts/build_real_commit_dataset_scientific.py
# deterministic rebuild; identical manifests when inputs unchanged.
```