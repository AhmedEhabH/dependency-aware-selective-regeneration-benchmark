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

**The 50 MB target is NOT reachable without deleting authoritative scientific
evidence** (the 132 MB dataset + 47 MB raw evidence). The mission explicitly
forbids deleting "raw scientific evidence required to reproduce published
numbers merely to hit the size target". Therefore the TRUE LIGHT export is the
maximum-lightweight authoritative tree above (~188 MB raw; compressed size
reported at build time), and the 50 MB target is documented as unreachable
under the constraint that reproducibility of the published numbers is
preserved.

**If a smaller transfer is ever required**, the only compliant options are:
(a) a curated *read-only summary pack* (human-readable docs + cheatsheet +
key JSONs only, not a reproduction bundle), or (b) an authorized dataset
download/regeneration path for the receiver. Neither is implemented in this
mission.

## 4. Verified git facts (recorded before omitting `.git`)

- `HEAD == origin/main == 2053df5d602fd5df1ca1b1c4beadc8aee9fd3526`
- remote URL: `https://github.com/AhmedEhabH/dependency-aware-selective-regeneration-benchmark.git`
- scientific tags and peeled SHAs:
  - `strong-localization-signal-2026-09-19` → `0c12223b15de4fa704dd2200ccae15b088ce23be`
  - `qwen3-embed-contamination-bridge-2026-09-19` → `44866fcff5e06bfe1598902300ba593a438b905c`
  - `oracle-gap-bidirectional-repair-2026-09-18` → `8b2d1b6785b6bf9275d06f84eb992d8cb80789c2`