# PILOT-READY-01 - Saleor Scenario-Relevant Test Setup Validated (Not a Blocker)

**Change ID:** PILOT-READY-01-SALEOR-VALIDATION
**Date:** 2026-08-09
**Status:** SALEOR TEST SETUP VERIFIED - scenario-relevant subset passes 49/49 against CI-equivalent service images; repository_versions.yaml updated from `pending` to `verified`

## Truth

```text
saleor version           = 3.23.0 (stable release, tag 3.23.0, commit e11a5557)
python                   = 3.12.13 (uv-managed; pyproject requires-python = ">=3.12,<3.13")
django                   = 5.2.13
infra (CI-equivalent)    = docker postgres:15-alpine  (host port 5433)
                           docker valkey/valkey:8.1-alpine (host port 6380)
scenario-relevant subset = saleor/plugins/user_email/tests/test_plugin.py
                           saleor/plugins/admin_email/tests/test_plugin.py
result                   = 49 passed / 0 failed in 195.53s
env (matches CI)         = DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/saleor
                           CACHE_URL=redis://127.0.0.1:6380/0
                           SECRET_KEY=ci-test
pytest invocation        = uv run --no-sync pytest -m "not e2e" <subset>
```

## Decisions

1. **Saleor is validated, not a blocker.** The DA-01 alternative (STOP + report blocker) was rejected in favor of the verified path: the scenario-relevant subset runs cleanly on the exact CI service images pinned in the project manifest.
2. **Infra pivoted to Docker containers on alternate ports (5433/6380)** because the local native PostgreSQL (17, scram-sha-256, unknown credentials) and the system Redis (6379) could not be used reproducibly. Container images match the saleor CI workflow (`library/postgres:15-alpine`, `valkey/valkey:8.1-alpine`).
3. **Stale manifest corrected:** `python_version` was `">=3.10,<3.13"` but saleor's pyproject requires `">=3.12,<3.13"`; `dependency_file` was `requirements.txt` but saleor 3.23 uses `uv.lock`. Both corrected and `test_setup_verified` set to `verified`.

## Windows-only workarounds (scratch checkout, not pack deliverables)

1. **memray / pytest-memray are win32-incompatible** (build fails at `RuntimeError: memray does not support this platform (win32)`). Workaround: `uv sync --locked --no-install-package memray --no-install-package pytest-memray`, then run with `uv run --no-sync` (uv run lacks `--no-install-package`).
2. **`saleor/core/rlimit.py` unconditionally imports Unix-only `resource`**, and `saleor/settings.py:35` imports it at module load, so the entire pytest suite cannot start on Windows. Workaround: guarded the import (`try: import resource except ImportError`) and made `validate_and_set_rlimit` a no-op when `resource is None`. saleor CI runs Linux only, so this is untested upstream.

## Verification chain

- venv: `uv sync --locked --no-install-package memray --no-install-package pytest-memray` (auto-downloaded CPython 3.12.13)
- smoke: `uv run --no-sync python -c "import django"` -> python 3.12.13, django 5.2.13
- subset: 49 passed, 7 warnings, 195.53s (postgres container confirmed `Up` after run)
- first attempt failed (49 errors) only because the postgres container received an external shutdown mid-run; restart + clean `test_saleor` database -> green
