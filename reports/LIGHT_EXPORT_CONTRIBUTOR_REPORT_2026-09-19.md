# TRUE LIGHT EXPORT — Contributor-Size Report (2026-09-19)

**Purpose:** document why the light export exceeds the 50 MB target and what
was excluded, per the mission rule "if still >50MB: produce a contributor-size
report and remove only reproducible, non-authoritative build artifacts."

## 1. What was excluded (all applied)

| Category | Excluded items | Size |
|---|---:|---:|
| `.git/` | git metadata (verified `HEAD == origin/main == 2053df5d…`) | ~35 MB |
| `pilot-kaggle-upload.zip` (+ `.sha256`) | MOVED to external historical archive `…\_historical_archive\` (SHA `65269528…` matches the documented v0.9.22-d13r2 candidate archive; NOT added to git) | 37.1 MB |
| `dist/*.zip` + nested ZIPs | all tracked `*.zip` (incl. `paper/v20-final/V20_FINAL_SUBMISSION.zip` historical submission) | 1.5 MB |
| Derived/reproducible | `research/strong-localization-signal/swerank/unit_manifest.json` (regenerable from cached blob texts + frozen `code_units.extract_code_units`) | 21.0 MB |
| Verbose agent logs | `research/locagent-p5b/**/localize.log`, `research/locagent-p5r1/**/localize.log`, `loc_trajs.jsonl` (P5 raw agent runs; the authoritative P5 numbers live in `research/locagent-p5b/locagent_two_way.json` + reports) | 15.1 MB |
| Caches/venvs/HF/embedding caches/build caches/`__pycache__` | not tracked → absent by construction (git archive) | 0 |
| Temp stdout/stderr logs | not tracked | 0 |

Total excluded: **~38.8 MB** (tracked-tree items) + `.git` + pilot zip.

## 2. Remaining content (187.7 MB raw) — by top-level directory

| Directory | MB | Why it must stay |
|---|---:|---|
| `benchmark_data/` | 132.6 | The frozen real-commit DATASET (djangoCMS + Saleor case bundles: candidate universes, dependency graphs, intents, hidden proxies) — required to reproduce every published number |
| `research/` | 47.4* | Raw evidence: run records, results, ledgers, registration freezes, transparency, contamination-bridge evidence, task rankings, metrics, gate, budgets (*after exclusions) |
| `reports/` | 11.6 | All authoritative experiment reports + JSONs |
| `tests/` + `scripts/` + `src/` + `docs/` + `msc_proposal/` + `paper/` + `kaggle_upload/` + root | ~14.5 | Source, tests, docs, proposal/paper, historical pilot-upload code |

## 3. Verdict

**The compressed TRUE LIGHT export is 35,398,954 bytes (35.4 MB) — WITHIN the
50 MB target.** The uncompressed tree is 187.75 MB (dominated by the 132.6 MB
authoritative dataset + 47 MB raw evidence), but JSON/text compresses ~5:1, so
the delivered export meets the size requirement WITHOUT deleting any
authoritative scientific evidence. The pilot `pilot-kaggle-upload.zip`
(37.1 MB) was moved to the external historical archive, `.git/` was omitted
(verified facts in §4), and the derived/verbose artifacts in §1 were excluded.

**If an even smaller transfer is ever required**, the only compliant options
are (a) a curated read-only summary pack (human-readable docs + cheatsheet +
key JSONs only, not a reproduction bundle), or (b) an authorized dataset
download/regeneration path for the receiver. Neither is implemented in this
mission.

## 4. Verified git facts (recorded before omitting `.git`)

- `HEAD == origin/main == 2053df5d602fd5df1ca1b1c4beadc8aee9fd3526`
- remote URL: `https://github.com/AhmedEhabD/dependency-aware-selective-regeneration-benchmark.git`
- scientific tags and peeled SHAs:
  - `strong-localization-signal-2026-09-19` → `0c12223b15de4fa704dd2200ccae15b088ce23be`
  - `qwen3-embed-contamination-bridge-2026-09-19` → `44866fcff5e06bfe1598902300ba593a438b905c`
  - `oracle-gap-bidirectional-repair-2026-09-18` → `8b2d1b6785b6bf9275d06f84eb992d8cb80789c2`

## 5. UPDATE — QWEN3 two-realization replication closure (2026-09-20 01:57)

TRUE LIGHT export re-built at the new scientific closure
(`qwen3-two-realization-replication-2026-09-19` tag, merge `083a1b2…`,
HEAD == origin/main == `083a1b2…`, clean tree):

- **Project export: `project-2026-09-20-0157.zip`**
  - **38,560,221 bytes (38.6 MB) ≤ 50 MB** (was 35.4 MB; +3.2 MB = the new
    two-realization artifacts: full-file-score Parquet ×2, task_rankings ×2,
    two_realization_metrics.json, reports, docs, tests).
  - SHA-256 `334aaba7e475529e1c4096133a9b9124c34a1eb5c218a7da93e40bb14d22e5bf`
  - 7,676 entries; git archive (no `.git`); same exclusions as §1
    (pilot zip, tracked `*.zip`, `unit_manifest.json`, locagent verbose logs).
  - Verified members: `00_CURRENT_RESEARCH_STATE.md`, `DECISIONS.md`,
    `reports/QWEN3_TWO_REALIZATION_REPLICATION_REPORT_2026-09-19.md`,
    `research/contamination-bridge/qwen_embed/realization_{A,B}/{full_file_scores.parquet,task_rankings.json}`.
- Updated git facts at this closure: HEAD == origin/main ==
  `083a1b2e9a14e484e166a58f729559070a3cf479`; new DEV-evidence tag
  `qwen3-two-realization-replication-2026-09-19` peels to `083a1b2…`.
- Budget: cumulative Qwen bridge spend ≈ **$0.439 ≤ $0.50** (A $0.1971 +
  B $0.2188 + ~$0.023 probes).