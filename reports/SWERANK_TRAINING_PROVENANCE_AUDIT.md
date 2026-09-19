# SweRank Training-Contamination / Provenance Audit

**Date:** 2026-09-19
**Mission:** STRONG LOCALIZATION SIGNAL BRIDGE
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**ZERO API** (only public primary sources + local artifacts were inspected).

## Verdict

**`TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP`**

The SweRank/SweLoc training corpus *cannot* be proven disjoint from
djangoCMS/Saleor from the publicly released artifacts. Consequently,
`Salesforce/SweRankEmbed-Small` is evaluated ONLY as an **EXTERNAL PRETRAINED
DIAGNOSTIC BASELINE**; its results are NOT clean unseen generalization. This
verdict applies to the entire DEV study and every downstream comparison.

## 1. Method

We inspected, from primary sources only:

1. The official model card
   (`https://huggingface.co/Salesforce/SweRankEmbed-Small`).
2. The official SweRank repository
   (`https://github.com/gangiswag/SweRank`, cloned at `main` and inspected
   read-only) — data-collection pipeline under `src/collect/`.
3. The primary paper: *SweRank: Software Issue Localization with Code Ranking*
   (Reddy et al., ICLR 2026, arXiv:2505.07849) — full text extracted and
   searched.
4. Hugging Face dataset search (`SweLoc`, `SweRank`) — no public SweLoc
   dataset release was found.

## 2. What the primary sources establish

- The model is trained on **large-scale issue localization data collected from
  public Python GitHub repositories** (model card).
- SweLoc construction (paper §3.1): select repositories associated with the
  **top 11,000 PyPI packages** on GitHub; require ≥80% Python code; **exclude
  repositories already present in SWE-Bench and LocBench**; deduplicate by
  source-code overlap → **3,387 curated repositories**; 67,341 initial
  (PR, codebase) pairs; functions modified in a PR = positives, unmodified
  functions = negatives.
- The reproduction pipeline (`get_top_pypi.py`) scrapes the
  `hugovk.github.io/top-pypi-packages` ranking (top PyPI packages by monthly
  downloads).
- **The released artifacts do NOT include the 3,387-repo manifest** (the
  `repo_contrastive_mined_filtered.jsonl` training file is produced by the
  pipeline, not released; no SweLoc HF dataset exists).

## 3. Target-repo relevance

- **django-cms** and **saleor** are real PyPI packages (Django CMS is a
  widely-installed CMS; Saleor is a Django e-commerce platform). Their presence
  in the *top 11,000 PyPI packages by monthly downloads* at the 2025 collection
  time **cannot be ruled out** from released artifacts (a direct PyPI download-
  rank check was attempted but the PyPI JSON API was unreachable from the local
  network at audit time — recorded, not fabricated).
- The exclusion set covers only SWE-Bench and LocBench repos. **djangoCMS and
  Saleor are NOT in SWE-Bench's 12-repo set and are NOT in LocBench's repo set**
  (LocBench repos are the SWE-Bench family + a small known set), so the
  published exclusions do NOT protect djangoCMS/Saleor.
- A full-text search of the paper PDF for "django", "saleor", "Django CMS"
  returned **zero hits** — the paper does not enumerate the 3,387 repos, so
  absence of a mention is NOT evidence of absence from the corpus.
- The published figure (paper Fig. 3) reports only aggregate statistics; no
  per-repo breakdown is released.

## 4. Conclusion

Because the repo manifest and the training data are not public, we **cannot
determine** whether djangoCMS, Saleor, their forks, their target commits, or
closely related issue/PR examples appear in the SweLoc training corpus. The
honest verdict is `TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP`.

**Consequence (applied to this entire mission):**
- SweRankEmbed-Small = **EXTERNAL PRETRAINED DIAGNOSTIC BASELINE**.
- All SweRank results in this mission are labeled with the contamination /
  pretraining threat.
- SweRank results are NOT called clean unseen generalization.
- The PASS/FAIL gate result is interpreted as *"this external pretrained
  diagnostic signal transfers to our parent-only protocol on DEVELOPMENT"*,
  NOT as *"SweRank cleanly generalizes to djangoCMS/Saleor"*.

## 5. Mitigations already in place

- The DEV evaluation ran under strict parent-only leakage rules (query =
  parent-visible intent; code = parent revision only; no target patch / changed
  paths / proxy in inputs) — so the *protocol* is leak-free regardless of the
  pretraining question.
- Frozen adapter, pinned revision, deterministic ranking, independent audit.
- The result is DEVELOPMENT evidence only; sealed sets untouched.

## 6. How to upgrade this verdict later

1. Release of the SweLoc 3,387-repo manifest (or the
   `repo_contrastive_mined_filtered.jsonl` training file) → re-run the repo
   membership check → verdict A (`NO_KNOWN_TARGET_REPO_OVERLAP`) or B
   (`TARGET_REPO_OVERLAP_FOUND`).
2. Query the maintainers for a repo manifest.
3. Until then, any downstream use of the SweRank result MUST carry the
   diagnostic-baseline label.