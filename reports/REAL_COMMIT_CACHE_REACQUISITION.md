# RealCommitImpactDataset-v1 — Fresh-Machine Cache Reacquisition (djangoCMS)

**Date:** 2026-09-13
**Milestone:** M4A-1 closure / M4A-2 corpus (RealCommitImpactDataset-v1)
**Purpose:** reproduce every RealCommitImpactDataset-v1 gate, audit, and parent
relation check on a **new device WITHOUT copying Ahmed's local cache**
(`dist/real-commit-cache/djangocms`). The upstream djangoCMS history is
public; the cache is re-derived deterministically from source.

---

## 1. What the cache is

`dist/real-commit-cache/djangocms` is an **ignored, full bare-tip clone** of
`https://github.com/django-cms/django-cms` created with:

```powershell
git clone --no-checkout https://github.com/django-cms/django-cms dist/real-commit-cache/djangocms
```

- **No working tree is required.** All miners/verifiers use read-only plumbing
  commands (`rev-parse`, `cat-file`, `log`, `diff-tree`, `diff --quiet -w`)
  against the object database.
- **No GitPython.** The miner invokes the system `git` CLI via `subprocess`
  and **fails closed on SHA mismatch** (see
  `src/benchmark/real_commits/miner.py::acquire_cache` / `verify_commit_sha`).
- The clone is shallow-free (full history) so every ancestor of the frozen
  anchor `0f633fc9fa213357f4202482aab2b0edad680f95` (tag `5.0.0`) is present.

## 2. Step-by-step reacquisition on a fresh machine

```powershell
# 1) Create the parent directory (project/dist may already exist; it is gitignored).
New-Item -ItemType Directory -Force -Path dist\real-commit-cache

# 2) Clone the full upstream repository WITHOUT checkout into the exact cache path.
git clone --no-checkout https://github.com/django-cms/django-cms dist/real-commit-cache/djangocms

# 3) Verify the frozen anchor resolves to the exact expected commit.
git -C dist/real-commit-cache/djangocms rev-parse --verify 0f633fc9fa213357f4202482aab2b0edad680f95^{commit}
#    EXPECTED OUTPUT (must be byte-identical):
#    0f633fc9fa213357f4202482aab2b0edad680f95

# 4) Confirm the anchor object type is a commit (not a tag/blob).
git -C dist/real-commit-cache/djangocms cat-file -t 0f633fc9fa213357f4202482aab2b0edad680f95
#    EXPECTED: commit
```

If `git clone` is slow or interrupted, delete the partial directory and retry;
the miner also re-clones automatically when it detects a corrupt/partial cache
(`acquire_cache` removes and re-clones on mismatch).

## 3. Verification that the cache is authoritative

The independent verifier re-derives every recorded parent relation and every
artifact hash **from the cache only** (never from the builder's memory):

```powershell
python scripts/verify_real_commit_dataset.py
# AUDIT=PASS, exit code 0  →  every parent/target/universal/graph/proxy hash
# recomputes from the fresh clone and matches the frozen manifests.
```

The six Pre-Benchmark gates perform the same parent-relation re-derivation
(`parent_relation_verified_*` checks):

```powershell
# (six gates: dataset / prompt / pipeline smoke / dry run / integration /
#  metric — see reports/REAL_COMMIT_M4A1_VALIDATION.md for the mechanism)
```

## 4. Network / environment notes

- Requires network access to `github.com` on the fresh machine.
- The system `git` must be on `PATH` (the miner does **not** bundle git).
- No HF_TOKEN, no API keys, no LLM provider credentials are needed for any
  dataset gate, audit, or the M4A-2 corpus build: everything is deterministic
  local git + AST. **ZERO scientific LLM/API calls.**
- Cache size is the full djangoCMS history (~a few hundred MiB object DB);
  disk space must accommodate it plus the extraction objects.

## 5. What is NOT reproduced by re-cloning

The clone reproduces only the **upstream history**. It does not contain any
project-side artifact. Dataset artifacts (universe / graph / proxy / intents /
manifests) live in tracked `benchmark_data/real_commit_impact_v1/` and must be
checked out from the project repository normally. After a fresh clone, run the
verifier + six gates to prove the local clone + tracked dataset agree.

## 6. Frozen identity reference

| Item | Value |
|---|---|
| Repository URL | `https://github.com/django-cms/django-cms` |
| Anchor commit | `0f633fc9fa213357f4202482aab2b0edad680f95` (tag `5.0.0`) |
| Candidate universe count / hash | 144 / `43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410` |
| Dependency graph edges / hash | 562 / `0a6bf0f758c9cd7de79adb72138c549a2b0aee3cfd62841496cb455d1ce7cd58` |
| License manifest | `benchmark_data/manifests/repositories.yaml#djangocms` (BSD-3-Clause) |