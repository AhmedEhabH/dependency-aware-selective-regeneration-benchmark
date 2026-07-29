# R3C Final Freeze Closure

**Date:** 2026-07-30
**Branch:** experiment/three-arm-smoke-v2
**Code commit:** 47e1a05
**Docs commit:** (pending)
**Protocol:** docs/R3C_FREEZE_CLOSURE_AND_DELIVERY_ACCELERATION_PROTOCOL.md

## Evidence gaps closed

1. **TOCTOU tests** — rewritten to validate first, mutate second, then trust-load. Three symlink tests and one frozen-at-trust-time test replace the old pre-mutation approach.
2. **Inode-based test** — deleted; replaced by `test_same_ordinary_path_content_is_frozen_at_trust_time` which proves content is frozen at trust time without inode identity.
3. **Permission-layer proof** — Smoke 003 `_task_create_uses_project_owner` now invokes every configured permission class for owner and non-owner requests via `SimpleNamespace`.
4. **Source-isolation Boolean** — buggy `not exists() or not is_symlink()` replaced with `_assert_workspace_has_no_evaluator_assets` helper using AND logic, rejecting 5 contamination forms.
5. **Lifecycle tests** — 6 fake-Django tests (3 assets × 2 modes: setup failure, setup+teardown failure) persist the setup/teardown JSON contract.
6. **Immutable hash tests** — metadata is required to exist and is never written by the test.
7. **Commit separation** — code commit (47e1a05) contains code/tests only; docs commit follows separately.

## Evidence results

- Unit evaluator: 60 passed, 9 skipped
- Integration evaluator: 51 passed, 1 skipped
- Adjacent R3B + above: 219 passed, 22 skipped
- Full suite: 1424 passed, 32 skipped

## Next

R3D blocked until independent audit accepts this closure.
