# Bundle Build and Deployment Guide

**Purpose:** Document the automated, reproducible process for building Kaggle deployment bundles from canonical sources.

---

## Overview

The Kaggle deployment bundle (`project/kaggle_upload/`) is a **generated derivative** — never edited directly. It is built from canonical sources by the deterministic script `scripts/build_upload_bundle.py`.

**Source-of-truth:** Canonical sources in `project/`  
**Build script:** `scripts/build_upload_bundle.py` (sole producer)  
**Output:** `project/kaggle_upload/` (code/, data/, notebooks/)

---

## Bundle Structure

```
project/kaggle_upload/
├── code/
│   ├── seven_arm_benchmark.py
│   ├── pyproject.toml
│   ├── requirements-kaggle.txt
│   ├── configs/
│   │   ├── smoke.yaml
│   │   ├── pilot.yaml
│   │   └── research.yaml
│   └── src/benchmark/ (14 packages, 66 .py files)
├── data/
│   ├── manifests/
│   │   ├── repositories.yaml
│   │   └── repository_versions.yaml
│   ├── repository_profiles/
│   │   ├── djangocms.yaml
│   │   ├── saleor.yaml
│   │   └── todo.yaml
│   └── scenarios/ (24 YAML files)
└── notebooks/
    └── seven_arm_benchmark.ipynb
```

---

## Building the Bundle

### From Project Root

```bash
cd project
python scripts/build_upload_bundle.py
```

### What the Script Does

1. **Clears** `project/kaggle_upload/` only (never touches canonical sources)
2. **Copies** allowlisted canonical sources:
   - `seven_arm_benchmark.py`
   - `src/benchmark/`
   - `configs/`
   - `requirements-kaggle.txt`
   - `pyproject.toml`
   - `benchmark_data/manifests/`, `repository_profiles/`, `scenarios/`
   - `notebooks/seven_arm_benchmark.ipynb`
3. **Excludes** forbidden patterns:
   - `.git/`, `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`
   - `*.egg-info/`, `*.pyc`, `*.pyo`
   - `runs/`, `reports/`, `tests/`, `inputs/`, `_auto_resume_temp/`
   - `benchmark-results.zip`
4. **Normalizes** text files to LF line endings (.py, .toml, .txt, .yaml, .yml, .md, .cfg, .ini)
5. **Generates** SHA-256 manifests:
   - `code_manifest.json`
   - `data_manifest.json`
   - `notebook_manifest.json`
6. **Verifies** every derivative against canonical source (normalized comparison)
7. **Reports** file counts and sizes
8. **Exits** non-zero on any mismatch

---

## Verification

### Automatic (on build)
```bash
python scripts/build_upload_bundle.py
# Output: "Bundle build complete and verified." (exit 0)
```

### Manual Checksum Verification
```bash
# Example: verify CLI
canon=$(Get-FileHash project/seven_arm_benchmark.py -Algorithm SHA256).Hash
bundle=$(Get-FileHash project/kaggle_upload/code/seven_arm_benchmark.py -Algorithm SHA256).Hash
if ($canon -ne $bundle) { throw "Mismatch" }

# Verify data bundle
$canon = Get-ChildItem project/benchmark_data -Recurse -File | ForEach-Object {
  $h = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
  $rel = $_.FullName.Substring((Get-Item project/benchmark_data).FullName.Length + 1)
  "$rel $h"
}
$bundle = Get-ChildItem project/kaggle_upload/data -Recurse -File | ForEach-Object {
  $h = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
  $rel = $_.FullName.Substring((Get-Item project/kaggle_upload/data).FullName.Length + 1)
  "$rel $h"
}
diff $canon $bundle
```

### Manifest Verification
```bash
# Code manifest has 72 entries
python -c "import json; print(len(json.load(open('project/kaggle_upload/code_manifest.json'))))"

# Data manifest has 29 entries
python -c "import json; print(len(json.load(open('project/kaggle_upload/data_manifest.json'))))"

# Notebook manifest has 1 entry
python -c "import json; print(len(json.load(open('project/kaggle_upload/notebook_manifest.json'))))"
```

---

## Deployment to Kaggle

### Prerequisites
1. Bundle built and verified locally
2. `HF_TOKEN` secret configured in Kaggle (for HuggingFace sync)
3. Qwen2.5-Coder model mounted at `/kaggle/input/qwen2-5-coder`

### Notebook Workflow
1. Open `project/notebooks/seven_arm_benchmark.ipynb` on Kaggle
2. Run cells sequentially:
   - Install dependencies (`requirements-kaggle.txt`)
   - Verify GPU availability
   - Mount Qwen model
   - Clone repository (or use pre-uploaded bundle)
   - Configure credentials
   - Dry-run (`--dry-run --profile smoke`)
   - Real run (`--profile pilot|research`)
   - Resume if needed (`--resume-from-hf`)
   - View results

### Bundle Usage on Kaggle
```bash
# From Kaggle working directory
cd /kaggle/working
# If bundle uploaded as dataset, extract and run
python kaggle_upload/code/seven_arm_benchmark.py --profile smoke --dry-run
```

---

## Selective Regeneration

When canonical sources change, **only affected bundles are regenerated**:

| Canonical Change | Regeneration Command |
|-----------------|---------------------|
| Any source file | `python scripts/build_upload_bundle.py` |
| Single file (if script supported) | Future enhancement |

**Current policy:** Always full rebuild (fast, deterministic, safe).  
**Rationale:** Full rebuild takes <5 seconds; selective adds complexity.

---

## Adding New Canonical Sources

To include a new file/directory in the bundle:

1. Add to `CANONICAL_CODE_SOURCES` or `CANONICAL_DATA_SOURCES` in `scripts/build_upload_bundle.py`
2. Ensure it follows exclusion patterns (no caches, metadata)
3. Rebuild: `python scripts/build_upload_bundle.py`
4. Verify output

---

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| Build fails: "MISSING" | Canonical source deleted; restore or update allowlist |
| Build fails: "MISMATCH" | Canonical source modified after bundle built; rebuild |
| Build fails: "FORBIDDEN" | Cache/metadata leaked into bundle; clean canonical or update exclusion |
| Kaggle notebook fails to import | Verify bundle `code/` has `src/ has `src/benchmark/__init__.py` |
| Data not found on Kaggle | Ensure `--data-dir` points to `kaggle_upload/data/` |
| Line ending issues | Script normalizes to LF; ensure canonical sources use LF or accept normalization |

---

## Security

- **No secrets in bundle:** `.gitignore` excludes `.env`, credentials
- **No `.git/` in bundle:** Excluded by script
- **No caches in bundle:** Excluded by script
- **Model weights:** Not in bundle; mounted at runtime from `/kaggle/input/`
- **HF_TOKEN:** Provided via Kaggle secrets, never in bundle

---

## Maintenance

| Task | Frequency |
|------|-----------|
| Rebuild bundle after any canonical change | Every change |
| Verify manifest counts | Every build |
| Update exclusion patterns if new cache types appear | As needed |
| Review bundle size for Kaggle limits | Before deployment |

---

## Change Record

| Date | Change | Record |
|------|--------|--------|
| 2026-07-24 | Initial automated bundle builder | SU-0001 |