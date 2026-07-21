# Local Environment Report

## Environment Name
`selective-regen-benchmark`

## Python Version
3.11.15 (packaged by Anaconda, Inc. — MSC v.1942 64 bit AMD64)

## Conda Implementation
- **Conda version:** 23.10.0
- **Conda location:** `C:\Users\Ahmed\AppData\Local\anaconda3`
- **Mamba/Micromamba:** Not available
- **Platform:** Windows (win-64)

## Package Resolver Used
`conda` 23.10.0 with `defaults` channel for core compiled dependencies, followed by `pip` 26.1.2 for development packages.

## Installation Commands

```bash
# Step 1: Create environment with core dependencies
conda env create -f environment.yml

# Step 2: Install missing pip packages (conda env pip timed out)
conda run -n selective-regen-benchmark python -m pip install pyyaml click pydantic jsonschema
conda run -n selective-regen-benchmark python -m pip install "pytest>=8.0,<9" "pytest-cov>=5.0,<6" "ruff>=0.4,<1" "mypy>=1.8,<2" "types-pyyaml>=6.0,<7"
conda run -n selective-regen-benchmark python -m pip install "nbformat>=5.0,<6" "nbconvert>=7.0,<8"
conda run -n selective-regen-benchmark python -m pip install "pre-commit>=3.0,<4"
```

## Installed Package Versions

See `requirements-lock.txt` for the complete frozen list.

**Key packages:**
| Package | Version |
|---------|---------|
| python | 3.11.15 |
| numpy | 2.4.6 |
| pandas | 3.0.3 |
| pytest | 8.4.2 |
| pytest-cov | 5.0.0 |
| ruff | 0.15.22 |
| mypy | 1.20.2 |
| pydantic | 2.13.4 |
| jsonschema | 4.26.0 |
| pyyaml | 6.0.3 |
| click | 8.4.2 |
| nbformat | 5.10.4 |
| nbconvert | 7.17.1 |
| pre-commit | 3.8.0 |

## Dependency Conflicts Found
- **None.** `python -m pip check` reports: "No broken requirements found."

## How Conflicts Were Resolved
- An initially installed `pytest 9.1.1` (from earlier `--no-deps` install) was replaced with `pytest 8.4.2` when the full dependency-aware install completed.
- No other conflicts were encountered.

## Remaining Warnings
- Several pip "not on PATH" warnings are expected when using the full Python path to invoke environment tools. These are benign when the environment is properly activated.
- Full `jupyter` metapackage was not installed (timed out due to large size of jupyterlab/notebook on slow connection). The core notebook-validation packages `nbformat`, `nbconvert`, `jupyter_core`, and `jupyter_client` are installed and functional.

## Activation Command
```bash
conda activate selective-regen-benchmark
```

If `conda activate` is not working (requires initialization):
```powershell
# PowerShell
& "C:\Users\Ahmed\AppData\Local\anaconda3\shell\condabin\conda-hook.ps1"
conda activate selective-regen-benchmark

# Or use the conda init path directly:
C:\Users\Ahmed\AppData\Local\anaconda3\Scripts\conda.exe activate selective-regen-benchmark
```

## Deactivation Command
```bash
conda deactivate
```

## Environment Removal Command
```bash
conda env remove -n selective-regen-benchmark
```

## Local Tests Executed
- `python -m pip check` — PASSED (no broken requirements)
- Import smoke tests — PASSED (pytest, pydantic, jsonschema, yaml, click, numpy, pandas, nbformat, nbconvert, mypy)
- `ruff check src/ tests/` — PASSED (all checks passed)
- `mypy src/ tests/` — PASSED (no issues found)
- `pytest --version` — PASSED (pytest 8.4.2)

## Kaggle-Only Checks Not Executed
- Real model loading or inference
- Qwen model discovery
- Kaggle environment variables or secrets
- GPU availability
- `torch` / `transformers` installation
- Real benchmark runs
- Runtime token counts or model latency
