# Artifact Drift Audit

**Audit Date:** 2026-07-24
**Methodology:** SHA-256 comparison of canonical files vs bundled copies, with normalization to detect line-ending-only differences.
**Branch:** `audit/canonical-project-architecture`

---

## 1. Canonical seven_arm_benchmark.py vs Bundled Copies

| Comparison | Raw SHA-256 | Normalized SHA-256 | Result |
|-----------|-------------|-------------------|--------|
| Canonical | `D28E2D9DFB4E3067418017303DAF813483F94CDC45849F5168E3470B0D0828DA` | (base) | — |
| Inner bundle `project/kaggle_upload/code/` | `D28E2D9DFB4E3067418017303DAF813483F94CDC45849F5168E3470B0D0828DA` | MATCH | **Exact match** |
| Outer bundle `<parent>/kaggle_upload/code/` | `E8A004A86CD69EAC0F63276F611131CAE099611840B6B034C5B142068B1AE84A` | DIFFERS | **Content mismatch** |

**Verdict:** Inner bundle is current. Outer bundle is stale — contains a different version of the script.

---

## 2. Canonical src/benchmark/ Package vs Bundled Copies

| Metric | Inner bundle | Outer bundle |
|--------|-------------|-------------|
| Source files compared | 66 | 66 |
| Exact match | 66 | 62 |
| Line-ending only diff | 0 | 3 |
| **Content mismatch** | **0** | **1** |
| Missing files | 0 | 0 |

**Content mismatch in outer bundle:**
- `src/benchmark/checkpoint/hf_sync.py` — canonical 30052 bytes vs outer 28790 bytes. Genuinely different content.

**Line-ending-only differences in outer bundle:**
- `src/benchmark/core/models.py`
- `src/benchmark/llm/kaggle_qwen_backend.py`
- `src/benchmark/strategies/agent.py`

**Verdict:** Inner bundle is synchronized. Outer bundle is stale for `hf_sync.py`.

---

## 3. Canonical Configs vs Bundled Configs

| Config | Canonical SHA-256 | Inner bundle SHA-256 | Normalized | Result |
|--------|------------------|---------------------|------------|--------|
| `smoke.yaml` | `BDDF78C1BCF128209F8D2FAF5A7518DD56C552E638441AE3F71DE4189CF6AFF5` | `5BCDC7EB6FFD9B22D45860FB96C79B718592F18685BB2EF4B41C93F4DECC2E19` | MATCH | **Line-ending only** |
| `pilot.yaml` | `490ABAC1C97B7FD7EC7D71A40CE5F9A70494A17FDC09922629FA25B2AE91B982` | `E764B23BDBD9CCD31EDD23C8A351BCA8DEA2FBD013593E992BA4D6D6237FA9A0` | MATCH | **Line-ending only** |
| `research.yaml` | `0E4BAC11BD3830DF5BF82E6853F55F8E257D2A732EC361B73DDBF07CD78E85D4` | `F46FAA60DDEE2B0405E88DD739CAC5D90C22114075C08B839957E1B1161E2217` | MATCH | **Line-ending only** |

**Verdict:** Content matches after LF normalization. CRLF in canonical, LF in bundles.

---

## 4. Canonical Notebook vs Bundled Copies

| Comparison | Raw SHA-256 | Normalized | Result |
|-----------|-------------|------------|--------|
| Canonical `project/notebooks/` | `A153DE855B0B071B7359D007C9FC4AC3757AA1731A24155409203AA86EBDF0B8` | (base) | — |
| Inner bundle `project/kaggle_upload/notebooks/` | `A153DE855B0B071B7359D007C9FC4AC3757AA1731A24155409203AA86EBDF0B8` | MATCH | **Exact match** |
| Outer bundle `<parent>/kaggle_upload/notebooks/` | `5AFF3A08B272EC6FBFF34D550114B68C4293C2127F23B0122A0A86F76CD97777` | MATCH | **Line-ending only** |

**Verdict:** Inner bundle exact match. Outer bundle has only CRLF differences (but notebook JSON lines re-encoded). Content equivalent.

---

## 5. Canonical Benchmark Data vs Data Bundle

Comparison of all 29 data files (24 scenarios + 2 manifests + 3 profiles) between canonical and outer data bundle:

| File Group | Files Checked | Matches | Mismatches |
|-----------|--------------|---------|-----------|
| Scenarios | 24 | 24 | 0 |
| Manifests | 2 | 2 | 0 |
| Profiles | 3 | 3 | 0 |

**Verdict:** Outer data bundle EXACTLY matches canonical benchmark_data/. Data is correct but stored in the wrong location (outside Git).

---

## 6. Inner Bundle vs Outer Bundle

| Comparison | Status |
|-----------|--------|
| `seven_arm_benchmark.py` | **DIFFER** (content) |
| `notebooks/seven_arm_benchmark.ipynb` | **DIFFER** (raw hash, normalized match) |
| Source files (66) | 1 content diff (`hf_sync.py`), 3 line-ending only |
| Configs | Line-ending only |
| Data bundle | Inner empty, outer populated |
| `.git/` dir | Present in inner, absent in outer |
| Caches | Present in inner, absent in outer |

---

## 7. Git-Tracked Files vs Untracked Duplicates

| Tracked (Canonical) | Untracked Duplicate | Status |
|--------------------|--------------------|--------|
| `project/seven_arm_benchmark.py` | `<parent>/kaggle_upload/code/seven_arm_benchmark.py` | **Stale** — content differs |
| `project/notebooks/seven_arm_benchmark.ipynb` | `<parent>/kaggle_upload/notebooks/seven_arm_benchmark.ipynb` | **Stale** — hash differs |
| `project/benchmark_data/**` | `<parent>/kaggle_upload/data/**` | **Exact match** (but untracked) |
| `project/kaggle_upload/code/` | `<parent>/kaggle_upload/code/` | **Differ** — see above |
| `project/kaggle_upload/data/` (empty) | `<parent>/kaggle_upload/data/` (populated) | **Inverse sync failure** |
| `project/benchmark-results.zip` | (none) | Untracked, unknown origin |

---

## 8. Summary

| Category | Exact Match | Line-Ending Only | Content Diff | Missing |
|----------|------------|-----------------|-------------|---------|
| Inner bundle code vs canonical | 66/66 | 0 | 0 | 0 |
| Outer bundle code vs canonical | 62/66 | 3 | 1 (hf_sync.py) | 0 |
| Outer data bundle vs canonical | 29/29 | 0 | 0 | 0 |
| Inner bundle notebook vs canonical | 1/1 | 0 | 0 | 0 |
| Outer bundle notebook vs canonical | 0/1 | 1 | 0 | 0 |
| Inner bundle configs vs canonical | 0/3 | 3 | 0 | 0 |
| Inner vs outer bundle (code) | N/A | N/A | 1 content + 3 CRLF | 0 |
| Inner data bundle | N/A | N/A | N/A | **ENTIRELY EMPTY** |

**Critical observation:** The inner `project/kaggle_upload/data/` directory is empty. The only populated data bundle is the outer one at `<parent>/kaggle_upload/data/`. This means any Kaggle deployment using the inner bundle will fail to find scenario YAMLs, manifests, or repository profiles.
