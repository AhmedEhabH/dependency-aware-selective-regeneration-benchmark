# REPRO AUDIT — 2026-10-02

**Role:** Independent reproducibility audit of the 2026-10-02 closure
documentation. Zero model API; every check is deterministic filesystem/git/hash
verification. The audit verifies that (1) documentation links resolve, (2)
hashes and tags resolve to real artifacts, and (3) README claims match the
canonical registry.

Audit scope: files written/updated by the closure phase (README, docs/*) plus
the frozen evidence they cite. All checks performed on commit
`3280a658ac488dc64f44fef050c1f8ea993a58c9` (branch `main`).

---

## 1. Link resolution

Checked every local Markdown link in the closure-facing documents, resolved
relative to the referencing file's directory:

| File | Missing links |
|---|---|
| README.md | 0 |
| docs/EXPERIMENT_LEDGER.md | 0 |
| docs/RESULTS_SUMMARY.md | 0 |
| docs/CLAIM_REGISTRY.md | 0 |
| docs/RESEARCH_STATUS_2026-10-02.md | 0 |
| docs/METHODS_OVERVIEW.md | 0 |
| docs/THREATS_TO_VALIDITY.md | 0 |
| docs/LIGHT_EXPORT_CONVENTION.md | 0 |
| docs/M16_V1_CLOSURE_2026-10-02.md | 0 |

**Verdict:** no broken paths. **PASS**

## 2. Hash and tag resolution

### 2.1 M16 STOP LIGHT hash

| File | Expected SHA256 | Actual (source + cold copy) |
|---|---|---|
| `project-LIGHT-STOP_M16_ADAPTER_FAIL-2026-10-02-1606.zip` | `32465cf2…c1f08f` | MATCH (source `..` and `D:/wp2_cold/`) |

### 2.2 Frozen tags

| Tag | Present |
|---|---|
| `wp2-m16-v1-kit-2026-10-02` | FOUND |
| `wp2-m16-v1-r2a-2026-10-02` | FOUND |
| `wp2-m15r-v1-opws-2026-10-01` | FOUND |
| `wp2-m15r-v1-result-2026-10-01` | FOUND |
| `wp2-m14r-v1-result-2026-10-01` | FOUND |
| `wp2-pilot-a-v1-e1-result-2026-09-30` | FOUND |
| `wp1b-main297-result-2026-09-22` | FOUND |
| `saleor-reserve-300-rmcss-final-replication-2026-09-20` | FOUND |

**Verdict:** hashes/tags resolve. **PASS**

## 3. README claims match the registry

Cross-checked the README landing page against
`docs/RESULTS_SUMMARY.md` / `docs/CLAIM_REGISTRY.md` / `docs/EXPERIMENT_LEDGER.md`:

| Check | Result |
|---|---|
| README RESERVE-300 F1 (.3569 / .2647) | PASS |
| README MAIN_297 arms (.3631 / .3568 / .2652) | PASS |
| RESULTS_SUMMARY RESERVE-300 delta + CI (.0921 [.0691, .1156]) | PASS |
| RESULTS_SUMMARY MAIN_297 NI (NI_SUPPORTED, margin 0.05) | PASS |
| CLAIM_REGISTRY forbids "RM-CSS is E2E-superior to the Agent" | PASS |
| CLAIM_REGISTRY forbids "RM-CSS and the Agent are equivalent" | PASS |
| CLAIM_REGISTRY forbids "M16-v1 provides MAIN OPWS results" | PASS |
| EXPERIMENT_LEDGER traces numbers to artifact paths | PASS |

**Verdict:** README claims match registry. **PASS**

## 4. Reproduction commands

### 4.1 `python scripts/verify_paper_claims.py`

Result: `RESULT: PASS — all headline manuscript results recomputed from frozen
evidence and internally consistent.` (raw SHA 30/30 PASS). **PASS**

**Finding (verifier side effect, must be disclosed):** this command rewrites
the `ran_at` / `created_at` timestamp fields **in place** in four tracked
evidence artifacts when it recomputes them:
`reports/REAL_COMMIT_M4A3_P1_VALIDATION.md`,
`reports/real_commit_m4a3_p1_gates.json`,
`research/djangocms-confirmatory-route-b/dryrun/confirmatory_dryrun_summary.json`,
`research/djangocms-confirmatory-route-b/dryrun/confirmatory_manifest.json`.
Running it during this audit rewrote those timestamps to the run date; the four
files were restored byte-for-byte to HEAD (`git checkout HEAD -- <paths>`). The
check is that the verifier should be treated as read-only on frozen evidence;
any future run must restore or discard the rewritten timestamps. No scientific
content changed.

### 4.2 `python seven_arm_benchmark.py --dry-run --profile smoke`

Verified against a **fresh** output directory
(`--output-dir <temp>`): 9/9 runs succeeded, exit 0. **PASS when run from a
clean output directory.**

**Environmental note (not a documentation defect):** the command's default
output directory is `runs/`, which currently contains untracked
`run_records.jsonl` records from an earlier real run. `rebuild_experiment_reports`
fails closed with `ReportRebuildError: Unexpected Run IDs in records` when
re-executed against that stale state (it validates that persisted records
exactly match the current plan). This is pre-existing local workspace state;
the documented command is correct and reproducible from a clean output
directory. No audit action taken (out of audit scope to delete workspace
state).

## 5. Exporter / LIGHT convention

- `scripts/wp2_export_light.py` produces the new-convention name
  `project-light-YYYY-MM-DD-HHMM.zip` (verified live: matched
  `^project-light-\d{4}-\d{2}-\d{2}-\d{4}\.zip$`).
- Collision fail-closed verified (no overwrite, non-zero exit).
- Exporter tests: `tests/unit/wp2/e2e_v22/test_export_light_v22.py` 8/8 PASS
  (superseded 4/4 set from the closure phase).
- M16 kit tests (which import the exporter): 102/102 PASS.
- LIVE STATUS block in README remains byte-for-byte in sync with
  `docs/LIVE_STATUS.json` (`tests/unit/test_live_status_blocks.py` 3/3 PASS).

## 6. Verdict

| Acceptance | Result |
|---|---|
| no broken paths | PASS |
| hashes/tags resolve | PASS |
| README claims match registry | PASS |

**Overall: PASS.** The only finding is the pre-existing stale `runs/` state
noted in §4.2, which is environmental and not a defect of the closure
documentation.

---

## 7. Addendum (2026-10-02, T2 baseline finalization)

After the closure audit above, the T2 finalization task corrected the future
LIGHT naming convention and brought the live status current:

- **Naming correction:** the future LIGHT filename convention changed from
  `project-light-YYYYMMDDTHHMMSSZ.zip` to
  `project-light-YYYY-MM-DD-HHMM.zip` (timezone-aware local creation time,
  minute precision; same-minute collision fails closed; no suffix). Historical
  LIGHT artifacts were not renamed. Exporter tests
  (`tests/unit/wp2/e2e_v22/test_export_light_v22.py`) re-verified at 8/8 PASS.
- **LIVE status:** `docs/LIVE_STATUS.json` updated to the true 2026-10-02 state
  (C0→C6 done, G0_BRAIN_REVIEW done, M16-v1 closed pre-experiment, WP1
  primary / WP2 supporting) and re-rendered byte-for-byte into the four
  current-facing targets; `tests/unit/test_live_status_blocks.py` PASS.
- **No scientific change:** no metric, threshold, selector, dataset, RQ, or
  claim was modified by this addendum; this is durability/documentation only.
  The 2026-10-02 baseline is committed, pushed, and tagged
  `msc-research-baseline-2026-10-02`.