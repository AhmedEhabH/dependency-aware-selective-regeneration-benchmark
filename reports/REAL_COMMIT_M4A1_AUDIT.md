# M4A-1 Independent Audit — RealCommitImpactDataset-v1 Miner

**Date:** 2026-09-13
**Milestone:** M4A-1 — RealCommitImpactDataset-v1 miner + 6 MINER_DEV cases
**Branch:** `research/real-commit-impact-dataset-v1-miner-01`
**Audit path:** `scripts/verify_real_commit_dataset.py` (reads persisted
artifacts only; does NOT trust the builder's in-memory objects).
**Result:** **AUDIT=PASS** (all checks PASS).

## Checks performed (79 PASS / 0 FAIL)

### Dataset-level
- dataset manifest exists; exactly **6 dev cases** (within [4, 6]);
- all cases `split == MINER_DEV`; no `HELD_OUT_TEST` assigned;
- anchor SHA matches project truth
  (`0f633fc9fa213357f4202482aab2b0edad680f95`).

### Per-case (× 6 cases)
- **Git parent relation** independently re-derived from the cache
  (`git log`/`rev-parse`): every target's single parent equals the recorded
  `parent_commit`;
- **public/hidden physical separation**: `public/` + `hidden/` both exist and
  the hidden proxy file is present;
- **hashes recompute**: candidate universe hash, dependency graph hash,
  observed-change proxy hash, intent hash, and canonical record hash all
  recompute to the recorded values;
- **candidate/proxy constraints**: proxy ⊆ parent universe; all proxy statuses
  are ordinary `M`; proxy size in [1, 12];
- **leakage barrier**: public bundle contains no hidden proxy filename / field
  names / status marker rows / target diff text / embedded proxy payload /
  semantic gold tokens;
- **no scientific API artifacts** created inside any case
  (no `run_records.jsonl`, `manifest_90.json`, `raw_response`).

### Frozen-regression identities (M1/M3 evidence unchanged)
- candidate universe count **144**, canonical hash **`43f4279bdf...`** — PASS;
- graph edge count **562**, canonical hash **`0a6bf0f7...`** (node count 144) — PASS.

### Docs state
- README / SYSTEM_STATE / TODO record M4A-1 COMPLETE and MINER_DEV cases — PASS.

## Verifier usage

```powershell
python scripts/verify_real_commit_dataset.py
# prints AUDIT=PASS and one line per check; exit code 0.
```

## Frozen regression identity values (spec section 8)

| Identity | Expected | Verified |
|---|---|---|
| Candidate universe count | 144 | PASS |
| Candidate universe canonical hash | `43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410` | PASS |
| Graph edge count | 562 | PASS |
| Graph canonical hash | `0a6bf0f758c9cd7de79adb72138c549a2b0aee3cfd62841496cb455d1ce7cd58` | PASS |

## Scientific discipline

- No hidden proxy in any public bundle.
- No scientific LLM/API calls (all gates + audit deterministic).
- Changed files are recorded as **OBSERVED CHANGE-SET PROXY**, never semantic
  gold.
- No P/R/V/H gold fabricated from Git diffs.
- M1/M3 frozen evidence unchanged.