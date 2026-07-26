---
description: Run the cheapest reliable checks on changed files and directly affected tests
agent: build
---

Load efficient-project-verification. Use Fast mode. Inspect changed files via `git diff --name-only`, `git diff --cached --name-only`, and `git ls-files --others --exclude-standard`. Run `python scripts/check_fast.py`. Summarize exact commands run and their results (exit code, key output). Do not commit, push, merge, or modify unrelated files. Do not run full Pytest unless the script cannot determine a safe affected scope or a shared interface changed.
