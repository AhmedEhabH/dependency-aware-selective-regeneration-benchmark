# Change Index

Compact table of all selective updates. Sorted by date (newest first).

| ID | Date | Requirement | Status | Canonical Artifacts Affected | Derivatives Regenerated | Branch | Commit | Validation | Time | Agent Tokens | Quality Result | Record Link |
|----|------|-------------|--------|------------------------------|-------------------------|--------|--------|------------|------|--------------|----------------|-------------|
| SU-0002 | 2026-07-24 | runs_dir NameError fix | VALIDATED | seven_arm_benchmark.py, tests/unit/test_cli.py | kaggle_upload/code/seven_arm_benchmark.py | fix/su-0002-runs-dir-nameerror | pending | pytest 613 pass, ruff/mypy/pip check clean, bundle verified | null | null | preserved | records/SU-0002-runs-dir-nameerror-fix.md |
| SU-0001 | 2026-07-24 | Canonical structure remediation | MERGED | scripts/build_upload_bundle.py, .gitignore, docs/*.md, SYSTEM_STATE.md, TODO.md, DECISION_LOG.md | kaggle_upload/code/, kaggle_upload/data/, kaggle_upload/notebooks/ | chore/canonical-project-remediation | 16a993e | Bundle verification, pytest, ruff, mypy, pip check | null | null | preserved | records/SU-0001-canonical-structure-remediation.md |

## Status Legend

- `PLANNED` — Not started
- `IN_PROGRESS` — Work in progress
- `VALIDATED` — Quality gates passed, ready to merge
- `MERGED` — On main
- `DEPLOYED` — On Kaggle
- `ROLLED_BACK` — Reverted
- `BLOCKED` — Cannot proceed