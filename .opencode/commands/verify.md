---
description: Run the final pre-commit or pre-merge verification gate
agent: build
---

Load efficient-project-verification. Use Final mode. Run final validation exactly once. Stop on the first root-cause failure. After success report exact:
- Ruff result
- Mypy result
- Pytest collected/passed/skipped/failed
- Bundle result
- Changed files
- Documentation status

Do not commit, push, merge, or tag.
