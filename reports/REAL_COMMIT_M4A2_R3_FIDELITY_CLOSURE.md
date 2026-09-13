# M4A-2 R3 Adjudication-Fidelity Closure

**Date:** 2026-09-14
**Branch:** `research/real-commit-impact-dataset-v2-corpus-01`
**Status:** CLOSED — deterministic, auditable, corpus-invariant
**Frozen corpus:** UNCHANGED (40 scientific cases, split freeze 24/6/10,
`canonical_manifest_sha256` preserved).

---

## 1. The documented issue

The M4A-2 protocol pre-registered R3 as *"adjudicated by inspection (keep the
newest if the messages describe the same change; otherwise both are kept)"*.
The initial implementation in `src/benchmark/real_commits/scientific.py`
applied a **mechanical `exclude_older_keep_newest`** whenever the threshold
(shared proxy path + intent Jaccard ≥ 0.5) fired — the documented
`otherwise both are kept` branch was never implemented, and the report labelled
these as *manual adjudication* although no inspection step existed. The 5 R3
records also claimed a fixed rationale ("messages describe the same/continuation
change") that was fabricated by the code rather than derived from the messages.

## 2. Independent findings (verified against the real git cache)

- **R3 had ZERO effect on the accepted corpus.** Deterministic re-derivation
  with R3 enabled vs. disabled (R1/R2 only) produces the **identical 40-case
  selection** (`diff = []`). Neither the 5 R3 `kept_sha` nor the 5 R3
  `excluded_sha` commits appear in the corpus (they were not year-cap-selected).
- **The accepted corpus contains zero R3-flagable pairs** (no accepted pair
  shares a proxy path AND has intent Jaccard ≥ 0.5), so no related change
  crosses a split.
- **All 5 R3 decisions are correct under the frozen rule.** The 5 flagged pairs
  all describe the same/continuation change, so `exclude_older_keep_newest`
  is the correct decision for every one of them.

## 3. Closure changes

1. `src/benchmark/real_commits/scientific.py`:
   - Added `_messages_describe_same_change` — the deterministic, auditable
     operationalization of the protocol's inspection step (identical /
     token-subset / ≥3-shared-token normalized intents ⇒ same change).
   - R3 now records `decision_source = "deterministic_same_change_predicate"`,
     implements the **keep-both** branch for genuinely different changes, and
     writes a rationale derived from the actual decision.
   - `dedup_summary.after_r1_r2` is now computed from the real R3-excluded set
     (was `len(kept) + #R3-records`, which would be wrong with keep-both).
2. `scripts/build_real_commit_dataset_scientific.py`: report renderer corrected
   to describe the deterministic predicate and keep-both branch truthfully
   (no more "manual/semantic adjudication" wording).
3. Tests (new):
   - `tests/unit/test_real_commit_scientific.py`:
     `test_dedup_r3_suspected_related_different_change_keeps_both` (keep-both
     branch) and `test_messages_describe_same_change_predicate` (all 5 real
     pairs → same change; different-change negatives).
   - `tests/integration/test_real_commit_scientific_pipeline.py`:
     `test_r3_adjudication_is_corpus_invariant` (with/without R3 → identical
     selection).
4. Reports corrected truthfully (unchanged frozen corpus):
   - `reports/REAL_COMMIT_M4A2_ADJUDICATION.md`
   - `reports/real_commit_m4a2_adjudication.json` (R3 records now carry
     `decision_source`)
   - `reports/REAL_COMMIT_M4A2_AUDIT.md` (fidelity-closure note)
   - `reports/REAL_COMMIT_M4A2_PROTOCOL.md` (R3 now "deterministic
     adjudication", not "manual adjudication")

## 4. Verification

- Deterministic rebuild into a temp dataset dir: all 40 case dirs identical;
  canonical per-record hashes recompute to frozen values; the only differences
  are the declared timestamp-only fields (`created_utc`, `generated_utc`).
- `python scripts/verify_real_commit_dataset_scientific.py` → `AUDIT=PASS`
  (610 PASS / 0 FAIL) with the frozen corpus.
- Focused unit + integration suites green.
- No scientific LLM/API calls. The frozen corpus and split freeze are
  untouched.

## 5. Scientific discipline

- The historical diff remains an **OBSERVED CHANGE-SET PROXY**.
- No P/R/V/H gold fabricated from Git diffs.
- R3 now faithfully implements the frozen protocol (keep-both included), is
  deterministic, auditable, and corpus-invariant.