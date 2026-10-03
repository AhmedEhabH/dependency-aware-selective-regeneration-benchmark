# Controller STOP — M17_QUAL_STRATA_CHANGED

- mission: M17_PHASE0B_V2 (K03)
- utc: 2026-10-03
- resumable: False (requires ChatGPT brain approval before freeze)

## Summary

The qualification strata and the exact 12-task membership **changed** after
recomputing with corrected frozen-harness-derived adapter values. Per mission
K03 the membership is NOT silently overwritten; this STOP report is produced
and the candidate file is written to:

`research/wp2/m17_v1/m17_qualification_membership_v2_candidate.json`

ChatGPT must approve the changed membership before the kit can be frozen (K10).

## Old strata (Phase-0 P01/P04, hand-written manifest_mechanism_derived)

| stratum | count |
|---|---|
| py312,poetry,oracle_harness_schema_v2 | 42 |
| py312,uv,oracle_harness_schema_v2 | 35 |
| py38,poetry,oracle_harness_schema_v2 | 22 |
| py39,poetry,oracle_harness_schema_v2 | 120 |
| py39,requirements,oracle_harness_schema_v2 | 1 |

n_strata = 5

## New strata (K02 frozen-harness closure mechanism, resolved tasks only)

| stratum | count |
|---|---|
| py312,poetry,oracle_harness_schema_v2 | 42 |
| py312,uv,oracle_harness_schema_v2 | 35 |
| py38,poetry,oracle_harness_schema_v2 | 22 |
| py39,poetry,oracle_harness_schema_v2 | 120 |

n_strata = 4

Dropped stratum: `py39,requirements,oracle_harness_schema_v2` (1 task:
`saleor-rc-f76d0093b450`).

## Old 12 (Phase-0 membership)

```
saleor-rc-14a682044ca4 saleor-rc-663543eaf563 saleor-rc-7b1e8cee95d5
saleor-rc-7e42fc67ce72 saleor-rc-8220a53473bb saleor-rc-9b88221ba8c2
saleor-rc-a9e79dac40a2 saleor-rc-ba4ff17faab4 saleor-rc-d361479ab7da
saleor-rc-e0890780bf56 saleor-rc-e28ca6ad6442 saleor-rc-f76d0093b450
```
membership_sha256 = `3effa42878ed63ad3f89ca4492618cb3e04a8f6d53f4726ffa12722ac5d56a14`

## New candidate 12 (K02 frozen-harness derived)

```
saleor-rc-14a682044ca4 saleor-rc-663543eaf563 saleor-rc-7b1e8cee95d5
saleor-rc-7e42fc67ce72 saleor-rc-8220a53473bb saleor-rc-9b88221ba8c2
saleor-rc-a9e79dac40a2 saleor-rc-ba4ff17faab4 saleor-rc-bcd9f60d2aef
saleor-rc-d361479ab7da saleor-rc-e0890780bf56 saleor-rc-e28ca6ad6442
```
membership_sha256 = `75c13be8b44080407944291db8d7c2809e2ddd0fff8cc03ca6e80cfb9ded6cee`

## Exact cause of change

1. The only task in stratum `py39,requirements` (`saleor-rc-f76d0093b450`) is
   classified **ADAPTER_UNRESOLVED** by the K02 frozen-harness-derived adapter:
   its target manifests declare a dev/test group
   (`benchmark.wp2.dep_compiler.pyproject_dev_group_names` returns 29 names)
   while the frozen closure mechanism is `none`
   (`benchmark.wp2.dep_compiler.derive_dev_test_closure` on its target
   manifests: `pyproject.toml` + `requirements.txt` + `requirements_dev.txt`,
   no lock file, `_pins_from_req_files` collects no exact pins because
   `parse_requirements` strips the `==` operator before
   `_pins_from_req_files` tests `ver.startswith("==")`).
   This is the exact M16 R2A fail-closed class
   `DEV_GROUP_DECLARED_BUT_MECHANISM_NONE` (`saleor-rc-f76d0093b450`), now
   detected by the frozen harness path instead of a hand-written rule.
2. Because the task is unresolved it is excluded from the resolvable pool,
   so the `py39,requirements` stratum disappears and the 12-task selection
   (per-stratum min-sha then global backfill) replaces
   `saleor-rc-f76d0093b450` with `saleor-rc-bcd9f60d2aef`.

## Is the change purely a correction of an invalid Phase-0 derived field?

YES for the *stratification mechanism axis*: the Phase-0 P01 audit derived
`manifest_mechanism_derived` by hand-written lockfile-presence heuristics
(uv if uv.lock, poetry if poetry.lock, requirements if any req file, else
none) and the P04 membership consumed that field. The corrected adapter
derives the mechanism from the frozen harness closure
(`derive_dev_test_closure`) for every task, which is the same semantic
definition the frozen harness actually uses.

The membership *membership-set* change additionally excludes one
ADAPTER_UNRESOLVED task (the exact M16 fail-closed class). This is a
fail-closed correction: a task whose declared dev/test group cannot be
materialized by the frozen harness must not be silently qualified.

No dataset rule, readiness semantic, selector, metric, threshold, NI margin,
M15-R, or M16 artifact was changed.

## Files produced

- `research/wp2/m17_v1/m17_m16_root_cause_map.json` (K01)
- `research/wp2/m17_v1/adapter/adapter_report.json` (K02)
- `scripts/wp2_m17_adapter.py` (K02 rebuild)
- `tests/unit/wp2/m17/test_m17_adapter.py`, `test_m17_schema_mutation.py` (K02)
- `research/wp2/m17_v1/m17_qualification_membership_v2_candidate.json` (K03)

## Next

ChatGPT must approve the changed membership. Only after approval may the
mission continue to K04-K10 (runner, manifest, controller integration,
contract tests, validation, review package, freeze).