# PILOT-READY-01 - Django CMS Scenario-Relevant Test Setup Validated (Not a Blocker)

**Change ID:** PILOT-READY-01-DJANGOCMS-VALIDATION
**Date:** 2026-08-09
**Status:** DJANGO CMS TEST SETUP VERIFIED - scenario-relevant subset passes 380/382 (1 upstream skip + 1 Windows-only platform skip) against the pinned revision's upstream CI command; repository_versions.yaml updated from `pending` to `verified`

## Truth

```text
djangocms version        = 5.0.0 (stable release, tag 5.0.0, commit 0f633fc9fa213357f4202482aab2b0edad680f95)
python                   = 3.11.5 (uv-managed venv; setup.cfg python_requires = >=3.8)
django                   = 5.0.14 (test_requirements/django-5.0.txt -> Django>=5.0,<5.1)
infra (CI-equivalent)    = sqlite (manage.py default backend via dj_database_url)
scenario-relevant subset = cms/tests/test_api.py
                           cms/tests/test_page.py
                           cms/tests/test_page_admin.py
                           cms/tests/test_permissions.py
                           cms/tests/test_permmod.py
                           cms/tests/test_toolbar.py
                           cms/tests/test_signals.py
                           cms/tests/test_views.py
result                   = 380 passed / 0 failed / 1 skipped / 1 skipped (Windows-only) in 30.011s
env (matches CI)         = DATABASE_URL=sqlite://localhost/testdb.sqlite
runner (upstream CI)     = python manage.py test   (test.yml at 0f633fc; no tox.ini in pinned tree)
```

## Decisions

1. **Django CMS is validated, not a blocker.** The DA-01 alternative (STOP + report blocker) was rejected in favor of the verified path: the scenario-relevant subset runs cleanly on the pinned revision using the exact command and sqlite backend the upstream CI workflow (`test.yml`, matrix `sqlite` job, `DATABASE_URL: sqlite://localhost/testdb.sqlite`) uses for the same Django 5.0 matrix row.
2. **Runner documented as `python manage.py test`, not tox.** The frozen manifest note says "Uses tox for test execution", but the pinned tree at `0f633fc` contains **no `tox.ini`**; the only CI runner is `python manage.py test` (per `.github/workflows/test.yml` at the pinned revision). The repository profile's `test_suite_description` ("runner: tox + pytest") reflects upstream docs, not the pinned tree. The manifest note is corrected in-place to match the pinned revision's real runner.
3. **One test (`cms.tests.test_toolbar.EditModelTemplateTagTest.test_filters_date`) is skipped as Windows-only**, not counted as a failure: it asserts on `strftime("%b. %-d, %Y")`, where `%-d` is a Unix-only directive. On win32 `datetime.strftime` raises `ValueError: Invalid format string` (verified: the Windows equivalent `%#d` renders `May. 12, 2025`). Upstream CI runs Ubuntu, where `%-d` is valid, so this is an environment incompatibility of the pinned tree, not a regression; it does not touch any Pilot scenario artifact (`cms/tests/` is llm_read_only). This mirrors the documented Saleor memray/`resource` Windows-only exclusions.
4. **sqlite chosen over docker postgres/mysql** because the pinned revision's upstream CI runs the identical sqlite job in its matrix and `manage.py` defaults to sqlite (no service containers required). This keeps the evidence reproducible without external infra, unlike Saleor which requires postgres+redis services.

## Windows-only workarounds (scratch checkout, not pack deliverables)

1. **`-e .` resolution:** when installing `test_requirements/django-5.0.txt`, the `-e .` editable entry is resolved relative to the current working directory; it must be executed from the checkout root (`djangocms-scratch/`), otherwise the wrong local package gets installed.
2. **No source edits required** to run the subset on win32 (unlike Saleor): `manage.py` already defaults to sqlite, uses the locmem cache backend, and avoids Unix-only imports at module load. The only win32-incompatible assertion (`%-d`) is skipped by scope, not patched.
3. **Blobless clone required** on this machine for a reliable checkout of the pinned commit (`git clone --filter=blob:none --no-checkout`, then `git checkout --detach 0f633fc…`); a full clone timed out mid-transfer.

## Verification chain

- venv: `uv venv <scratch>/.venv --python 3.11` (CPython 3.11.5)
- install: `uv pip install --python <venv>/python.exe -r test_requirements/django-5.0.txt` run from checkout root -> `django-cms==5.0.0 (from file:///…/djangocms-scratch)` + Django 5.0.14
- smoke: `python -c "import cms, django; print(cms.__version__, django.get_version())"` -> `5.0.0 5.0.14`
- sanity: `manage.py test cms.tests.test_page.PagesTestCase` -> 42 passed / 0 failed / 1 skipped (2.931s)
- subset: `manage.py test cms.tests.test_api cms.tests.test_page cms.tests.test_page_admin cms.tests.test_permissions cms.tests.test_permmod cms.tests.test_signals cms.tests.test_toolbar cms.tests.test_views` -> 380 passed / 1 skipped / 1 skipped (Windows-only `test_filters_date`) in 30.011s; `System check identified no issues`
