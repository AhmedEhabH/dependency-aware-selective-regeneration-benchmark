# Architecture Validation Plan — Phase 4

## Validation Checks

### 1. Import Boundaries
- Use `subprocess` to verify that importing `src.benchmark.strategies` does **not** import `torch`
- Use `ast` module to scan all source files and validate allowed import targets per package

### 2. Circular Imports
- Use stdlib `modulefinder` or `python -c "import src.benchmark; ..."` with `sys.setrecursionlimit`
- Fail on `ImportError` or `RecursionError`
- Automate as a pytest test that imports the full package tree

### 3. Module Layering
- Verify that `src/benchmark/core/` modules import nothing from infrastructure packages
- Scan each module's `ast.Import` / `ast.ImportFrom` nodes and compare against the allowed direction table

### 4. Plugin Contracts
- Instantiate every strategy registered in `strategies/registry.py`
- Verify `isinstance(check, ImpactStrategy)` for each
- Ensure all required protocol methods are implemented

### 5. Package Independence from torch/transformers
- Dedicated test file that imports strategy modules
- Verify `'torch' not in sys.modules` and `'transformers' not in sys.modules` after import
- Run in a subprocess to guarantee clean interpreter state

### 6. No Hidden-Test Imports
- Use `grep` (or `ast` scan) for `private_evaluation` in `src/benchmark/strategies/`
- Fail if any match is found

### 7. No Ground-Truth Imports
- Use `grep` for `ground_truth` in `src/benchmark/execution/`
- Fail if any match is found

### 8. No Notebook-to-Core Dependency
- Notebook files must import from `src.benchmark` only through CLI or public API
- Scan `*.ipynb` for direct imports of internal modules (e.g., `from src.benchmark.strategies import ...`)

### 9. No Repository-Specific Branches in Core
- Search for `if.*repo` patterns in `core/` and `execution/`
- Fail on any match — core logic must be repository-agnostic

### 10. Deterministic Model Serialization
- Serialize and deserialize with a fixed random seed
- Assert the output is byte-identical across runs
- Test all model types in `core/models.py`

### 11. No Import-Time Side Effects
- Import every module in `src/benchmark/` in a clean subprocess
- Verify no files were created, no environment variables changed, no network calls made
- Use `os.listdir()` snapshots before/after import

## Recommended Tools

- `pytest` (already available)
- `ast` (stdlib)
- `subprocess` (stdlib)
- `sys` / `modulefinder` (stdlib)

Do **not** install new tools for validation.
