# SweRank Training-Provenance Audit V2 (2026-09-19)

**Date:** 2026-09-19
**Mission:** DEVELOPMENT-only contamination-robustness bridge (scope change).
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**ZERO paid API** (only free public metadata + the frozen local artifacts).
**Verdict V1 (unchanged):** `TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP` (C).
**V2 strengthens the evidence base; the verdict is NOT upgraded to A or B.**

---

## 1. What V2 added (deeper, targeted checks)

### 1a. PyPI download-rank evidence (the exact SweLoc source population)

SweLoc selects repositories of the **top 11,000 PyPI packages by monthly
downloads** (paper §3.1; pipeline `src/collect/get_top_pypi.py` scrapes
`hugovk.github.io/top-pypi-packages`).

We fetched the current dump
(`https://hugovk.github.io/top-pypi-packages/top-pypi-packages.json`,
last_update **2026-09-01**, 15,000 rows) and looked up the target packages:

| Package | Rank in 2026-09 dump | In top-11k? |
|---|---:|---:|
| `django` | 537 | yes (but this is the framework, not django-cms) |
| `django-cms` | **11,118** | **NO — just outside the top-11,000 cutoff (by 118 positions)** |
| `saleor` | not in top 15,000 | no |
| `saleor-core` | not in top 15,000 | no |

**Interpretation (careful):**
- This dump is **2026-09**, while SweLoc was collected around **May 2025**;
  rank positions drift. `django-cms` at 11,118 *now* means it plausibly sat in
  the ~10k–12k band in 2025 — **straddling the 11,000 cutoff**. We therefore
  **cannot rule out** that django-cms was inside the top-11k at collection time.
- `saleor` is absent from the current top-15k, making it **unlikely** (not
  impossible) it was in the top-11k in May 2025.
- Even within the top-11k, membership also required: a GitHub repo (both
  `django-cms/django-cms` and `saleor/saleor` exist ✓), ≥80% Python (both are
  Python ✓), NOT in SWE-Bench/LocBench (neither ✓), and source-overlap
  deduplication.

### 1b. Released corpus artifacts — none found (re-confirmed, deepened)

- The official SweRank repo (`github.com/gangiswag/SweRank`, **full 18-commit
  history fetched**): **no** `valid_top_pypi_gitrepos.jsonl`,
  `pypi_rankings.jsonl`, `repo_contrastive_mined_filtered.jsonl`, `tasks/`,
  `prs/` or any corpus/repo-list artifact was ever committed.
- Hugging Face dataset search: **no SweLoc dataset** exists (V1 re-confirmed).
- The paper full text (arXiv:2505.07849) does not enumerate the 3,387 repos and
  contains no "django"/"saleor" mention (V1 re-confirmed).
- GitHub code-search for the artifact filenames requires authentication (401
  unauthenticated) — recorded as a limitation, not a negative result.

### 1c. Forks / mirrors (indirect-overlap analysis)

- The corpus applied "deduplication based on source-code overlap to remove
  near-identical repositories". This **mitigates** the direct-fork risk
  (a near-identical mirror of django-cms would be deduped).
- A **modified** fork (below the overlap threshold) or a repackaged/mirrored
  copy that still qualifies as a distinct repo is **not excluded** by the
  published pipeline description.
- Neither django-cms nor saleor appears in SWE-Bench/LocBench exclusion sets.

## 2. Verdict

**`TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP` (C) — UNCHANGED.**

Rationale for NOT upgrading to A:
- `django-cms` is borderline for the top-11k membership condition (rank
  11,118 in 2026-09; 2025 rank unverifiable).
- Absence of exact target commit hashes in released materials is **not
  sufficient evidence** (the training manifest is not public).
- Modified-fork indirect overlap is not excluded by the published pipeline.

Rationale for NOT downgrading to B:
- No released artifact positively establishes that django-cms or saleor
  (or a fork, or their commits/PRs/issues) is in the SweLoc corpus.
- `saleor` appears very unlikely to have met the top-11k membership condition.

## 3. Consequences (unchanged, restated)

- SweRankEmbed-Small remains an **EXTERNAL PRETRAINED DIAGNOSTIC BASELINE**.
- `SWERANK_EMBED_PASS` is NOT clean unseen generalization; a clean-generalization
  claim is forbidden.
- Stage-5 confirmatory execution remains PAUSED and SEALED.

## 4. How to upgrade this verdict later

1. Release of the SweLoc 3,387-repo manifest or
   `repo_contrastive_mined_filtered.jsonl` → direct membership check →
   verdict A or B.
2. A May-2025 top-PyPI rank snapshot for `django-cms`/`saleor` (the site keeps
   historical dumps) could tighten the membership condition; not required to
   change the current verdict.
3. Until then, every downstream use of the SweRank result must carry the
   diagnostic-baseline label.