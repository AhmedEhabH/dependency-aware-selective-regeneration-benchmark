---
name: efficient-project-verification
description: Run low-cost changed-file diagnostics, targeted tests, and final verification for this Python benchmark while minimizing context and machine usage.
compatibility: opencode
metadata:
  project: dependency-aware-selective-regeneration-benchmark
  workflow: verification
---

## Fast mode

1. Inspect `git diff` (staged, unstaged, untracked).
2. Determine changed Python files.
3. Run Ruff only on changed Python files.
4. Run Mypy only on changed production Python files.
5. Compile-check changed Python files (`python -m py_compile`).
6. Select directly affected tests via path mapping.
7. Run targeted Pytest (`-q`, no xdist).
8. Stop at first root-cause failure.
9. Do not run full suite or bundle unless justified.

## Final mode

1. `git diff --check`
2. Full Ruff (`ruff check src tests scripts`)
3. Full Mypy (`mypy --strict src tests scripts`)
4. Full Pytest (`python -m pytest -q`)
5. Bundle rebuild and verification only when canonical production code, configs, Kaggle requirements, or the entry point changed (`python scripts/build_upload_bundle.py`). Do not run for documentation/tooling-only changes.
6. Documentation consistency check
7. Report exact totals

## Rules

- Do not reread unchanged files.
- Do not repeat successful checks when inputs did not change.
- Do not send entire logs to the model—trim to root cause and relevant tail.
- Do not install tools.
- Do not change source code unless the user requested a fix.
- Do not call the full suite in Fast mode.
