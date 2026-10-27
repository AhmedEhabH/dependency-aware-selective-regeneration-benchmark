# Main-protection checklist (admin action; NOT automatically applied)

Repository Settings -> Rules -> Rulesets -> New branch ruleset:

- Target `main` only (verify actual repository and branch before saving).
- Block branch deletion and force push.
- Require pull request before merging and disallow direct push, subject to plan-level support and administrator/bypass constraints.
- Keep bypass actors minimal; document any emergency bypass and create an incident/receipt.
- Require conversations resolved where appropriate.
- Optionally require review, but do not require another person if none is available; the researcher must retain a safe, documented authorization workflow.
- Start with checks in evaluate mode or non-required until demonstrated successful on the current `main` and on code/documentation PRs. The existing pilot preflight Action is expensive and narrowly path-triggered; DO NOT mark it required for every PR without examining what happens when it is skipped.
- Do not configure merge queue, automatic branch deletion, or required deployments without separate testing.
- Turn on secret scanning and push protection if available; audit existing public history and any historical credentials separately.
- Validate protection with a harmless test branch and PR. Do not test forbidden direct pushes to `main` against live research source.

**Rollback:** if a ruleset blocks legitimate maintenance, authorized admins can adjust it; keep an offline immutable note of old and new settings. `git revert` may undo an ordinary bad merge but cannot erase public disclosure of a secret. Never use `push --force` as a normal recovery tool.

Settings changes are NOT part of this kit. This document is a checklist, not proof of enabled protection.
