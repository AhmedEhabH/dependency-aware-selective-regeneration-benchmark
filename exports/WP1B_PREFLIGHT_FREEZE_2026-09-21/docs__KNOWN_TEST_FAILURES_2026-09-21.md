# Known Test Failures — 2026-09-21

**Mission:** WP1B_PREFLIGHT_FREEZE_2026-09-21 (Phase A2).
**Baseline:** full suite on `main` @ `1ae7058` (clean checkout, branch
`wp1b/preflight-freeze-2026-09-21` created from it).
**Result:** `5 failed / 3700 passed / 35 skipped`.

From now on the full-suite acceptance rule is: **the set of failing node IDs
must equal the list below**. Any new node ID is a failure of the mission. These
failures are pre-existing (they also fail at the pre-WP-1a baseline
`f25950f`). They are unrelated to WP-1a/WP-1b code and are NOT fixed in this
mission (the contract forbids fixing a `REAL_DEFECT` outside WP-1 code; each is
added to `TODO.md`).

## Failing node IDs

| # | Node ID | First error line | Class |
|---|---------|------------------|-------|
| 1 | `tests/integration/test_d96_kaggle_github_boundary.py::test_runtime_launch_resume_path_has_no_github_machinery` | `AssertionError: src\benchmark\issue_grounded\github.py must not contain 'GITHUB_TOKEN'` | `REAL_DEFECT` |
| 2 | `tests/integration/test_stagec_djangocms_runtime_wiring.py::test_all_six_gates_pass` | `FileNotFoundError: [WinError 3] The system cannot find the path specified: '...\project\benchmark_data\repositories\djangocms'` | `ENV_OR_DATA_MISSING` |
| 3 | `tests/integration/test_stagec_djangocms_runtime_wiring.py::test_pinned_source_available` | `assert False` (pinned djangocms source absent) | `ENV_OR_DATA_MISSING` |
| 4 | `tests/unit/test_model_identity_policy.py::test_full_model_name_present_in_current_facing_docs` | `AssertionError: README.md must use the full model name Qwen3-Coder-480B-A35B-Instruct` | `REAL_DEFECT` |
| 5 | `tests/unit/test_readme_markdown_tables.py::TestReadmeSvgFallbacks::test_svg_fallbacks_exist_and_are_embedded` | `AssertionError: README must embed the static SVG fallback for experiment_map` | `REAL_DEFECT` |

## Classification

- **ENV_OR_DATA_MISSING** — the pinned djangocms repository snapshot is not
  present in this checkout (LIGHT export / workstation); the tests require
  `benchmark_data/repositories/djangocms` to exist.
- **REAL_DEFECT** — frozen test/source inconsistencies that pre-date WP-1:
  - (1) `src/benchmark/issue_grounded/github.py` still contains the literal
    `GITHUB_TOKEN` in a docstring, which the D9.6 boundary test forbids.
  - (4) `README.md` documents the current model/provider pass differently from
    the full model name the policy test requires.
  - (5) `README.md` does not embed the static SVG fallback for `experiment_map`.

## Machine-readable list

`artifacts/known_test_failures_2026-09-21.json` (list of node IDs; JSON is the
authoritative set for the acceptance rule).