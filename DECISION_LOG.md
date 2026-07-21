# Decision Log

## Decision D001 — Bootstrap Phase
- **Date:** 2026-07-22
- **Decision ID:** D001
- **Status:** IMPLEMENTED
- **Category:** Engineering
- **Description:** Execute Phase 0 (Bootstrap and Environment) as the initial project phase.
- **Rationale:** The working directory is empty (except for `docs/OPENCODE_EXECUTION_GUIDE.md`). Per the guide, Phase 0 must be executed first.
- **Alternatives considered:** None — Phase 0 is the required first phase.
- **Impact:** Establishes project structure, Conda environment, state files, and Git baseline.
- **Evidence:** Successful directory creation, environment creation, and Git initialization.

---

## Decision D002 — Conda as Package Resolver
- **Date:** 2026-07-22
- **Decision ID:** D002
- **Status:** IMPLEMENTED
- **Category:** Engineering
- **Description:** Use `conda` (not mamba/micromamba) as the package resolver.
- **Rationale:** `conda` 23.10.0 is available. `mamba` and `micromamba` are not installed.
- **Alternatives considered:** 
  - Install mamba in base → rejected (forbidden by Section 3.2: "install packages into the base Conda environment")
  - Install mamba inside the project env → would complicate bootstrap (chicken-and-egg)
- **Impact:** Slower dependency resolution; no functional difference.

---

## Decision D003 — Environment Package Selection
- **Date:** 2026-07-22
- **Decision ID:** D003
- **Status:** IMPLEMENTED
- **Category:** Engineering
- **Description:** Define environment.yml with core Python 3.11 + numpy + pandas via Conda channels, and development/testing/linting packages via pip from requirements-dev.txt.
- **Rationale:** Conda provides pre-compiled binaries for numpy/pandas (no local build toolchain required). Pip is the standard for pure-Python dev tools. This hybrid approach follows Section 4.2 guidelines.
- **Alternatives considered:** 
  - All conda → some dev packages missing from conda-forge on Windows
  - All pip → would lose compiled-dependency optimization
- **Impact:** Faster installation, smaller environment file.

---

## Decision D004 — Kaggle Requirements Not Installed Locally
- **Date:** 2026-07-22
- **Decision ID:** D004
- **Status:** IMPLEMENTED
- **Category:** Engineering
- **Description:** Do not install `requirements-kaggle.txt` contents (torch, transformers, datasets, kagglehub) in the local environment.
- **Rationale:** Section 3.2 forbids downloading model weights or running LLM inference locally. torch would pull CUDA runtime; transformers would pull tokenizer files. These are Kaggle-only dependencies.
- **Alternatives considered:** Install torch CPU-only → still triggers 2+ GB download, against the spirit of "no local model"
- **Impact:** Local environment is ~500 MB instead of ~5 GB. All Kaggle-only dependencies must be validated on Kaggle.
