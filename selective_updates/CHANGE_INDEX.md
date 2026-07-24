# Change Index

Compact table of all selective updates. Sorted by date (newest first).

| ID | Date | Requirement | Status | Canonical Artifacts Affected | Derivatives Regenerated | Branch | Commit | Validation | Time | Agent Tokens | Quality Result | Record Link |
|----|------|-------------|--------|------------------------------|-------------------------|--------|--------|------------|------|--------------|----------------|-------------|
| SU-0006 | 2026-07-25 | Fix HF recovery activation path for auto-resume | MERGED | src/benchmark/checkpoint/hf_sync.py | kaggle_upload/code/src/benchmark/checkpoint/hf_sync.py, code_manifest.json | fix/su-0006-recovery-activation-path | 2e4c7bb | pytest (648 pass, 2 skip), mypy strict, ruff, bundle verified | null | null | preserved | records/SU-0006-recovery-activation-path.md |
| SU-0005 | 2026-07-25 | Fix explicit HF resume identity, canonical Run IDs, and idempotent persistence | MERGED | src/benchmark/checkpoint/checkpoint.py, hf_sync.py, persistence.py, seven_arm_benchmark.py, notebooks/seven_arm_benchmark.ipynb | kaggle_upload/code/ | fix/su-0005-explicit-resume-identity | 8b65c7b | pytest (636 pass), mypy strict (SU-0005 files clean), bundle verified | null | null | preserved | records/SU-0005-explicit-resume-identity.md |
| SU-0004 | 2026-07-25 | HF candidate rejection diagnosis | MERGED | src/benchmark/checkpoint/hf_sync.py, seven_arm_benchmark.py, notebooks/seven_arm_benchmark.ipynb, tests/unit/test_hf_sync.py | kaggle_upload/code/seven_arm_benchmark.py, kaggle_upload/code/src/benchmark/checkpoint/hf_sync.py | diagnose/su-0004-hf-candidate-rejection | 2892761 | pytest, ruff, mypy, pip check, bundle | null | null | preserved | records/SU-0004-hf-candidate-rejection-diagnosis.md |
| SU-0003 | 2026-07-24 | HF auto-resume discovery and Run-ID consistency | MERGED | src/benchmark/checkpoint/hf_sync.py, persistence.py, checkpoint.py, resume.py, seven_arm_benchmark.py, tests/unit/test_checkpoint.py | kaggle_upload/code/seven_arm_benchmark.py, kaggle_upload/code/src/benchmark/checkpoint/ | fix/su-0003-hf-auto-resume-discovery | 8bf54ec | Bundle verification, pytest, ruff, mypy, pip check | null | null | preserved | records/SU-0003-hf-auto-resume-discovery.md |
| SU-0001 | 2026-07-24 | Canonical structure remediation | MERGED | scripts/build_upload_bundle.py, .gitignore, docs/*.md, SYSTEM_STATE.md, TODO.md, DECISION_LOG.md | kaggle_upload/code/, kaggle_upload/data/, kaggle_upload/notebooks/ | chore/canonical-project-remediation | 16a993e | Bundle verification, pytest, ruff, mypy, pip check | null | null | preserved | records/SU-0001-canonical-structure-remediation.md |

## Status Legend

- `PLANNED` — Not started
- `IN_PROGRESS` — Work in progress
- `VALIDATED` — Quality gates passed, ready to merge
- `MERGED` — On main
- `DEPLOYED` — On Kaggle
- `ROLLED_BACK` — Reverted
- `BLOCKED` — Cannot proceed