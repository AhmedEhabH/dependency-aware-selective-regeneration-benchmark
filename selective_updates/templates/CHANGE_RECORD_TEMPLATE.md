# Change Record Template

Copy this template to `records/SU-XXXX-short-description.md` and fill in all fields.

---

Change ID: SU-XXXX
Title: [Short descriptive title]
Date: YYYY-MM-DD
Requirement or defect: [Link to requirement, issue, or defect description]
Reason for change: [Why this change is needed]
Research/protocol impact: [Does this affect the frozen protocol? If yes, describe]
Canonical artifacts affected: [List exact canonical file paths]
Canonical artifacts explicitly unaffected: [List artifact groups confirmed unchanged]
Generated derivatives affected: [List derivative paths that will be regenerated]
Runtime artifacts affected: [List runtime outputs that may change]
Pre-change evidence: [Test results, benchmarks, observations before change]
Impact analysis: [What could break? What dependencies exist?]
Planned minimal diff: [Summary of intended changes]
Actual files changed: [Filled after implementation]
Actual lines added/deleted: [Filled after implementation]
Targeted tests: [Specific test modules run]
Full quality gates: [ruff, mypy, pytest, pip check results]
Bundle synchronization: [scripts/build_upload_bundle.py run result]
Source-to-derivative checksum result: [All match? Any mismatches?]
Engineering elapsed time: [HH:MM or seconds, or null]
OpenCode/model used: [Model name if AI-assisted]
Agent token usage: [Tokens if available, else null]
Defects detected: [Count and description]
Defects introduced: [Count and description, 0 if none]
Quality outcome: [preserved|improved|degraded|unknown]
Git branch: [branch name]
Branch commit: [commit hash]
Merge commit: [commit hash after --no-ff merge]
Final main commit: [commit hash on main]
Deployment status: [not_deployed|deployed_to_kaggle|rolled_back]
Rollback plan: [How to revert if needed]
Residual risks: [Known issues or limitations remaining]
Next exact task: [SU-XXXX+1 description or "none"]