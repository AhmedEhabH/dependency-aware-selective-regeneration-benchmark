# Full-D7 Zero-Container Scope Census (owner decision)

Mission: `M17_ENV_CANON_SOURCE_FIDELITY_R1_FULL_D7` — T3 real full-D7 environment
qualification.  Phase: **SCOPE_CENSUS_ZERO_CONTAINER**.

No Docker.  No Full-D7 unit/container execution.  No git freeze/push.

## Decision the owner must make

The frozen R3 resolver, used exactly as frozen, is **py312-only in its wheel-tag
gate** (`d7_r3_wheeltags.TARGET_PYVER = (3, 12)`) and its closure derivation does
**not** exclude the uv.lock editable-self (`saleor==X`, `source = virtual`).
Applied faithfully over the whole 144-unit population, only the **py312 + poetry
stratum (25 units)** passes the frozen resolution dry-run.  All other strata are
**OUT_OF_VALIDATED_SCOPE** in this census — never classified as environment
failure, never labelled NOT_READY here.

## Population (144 units / 219 tasks)

| era × lock | units | frozen dry-run (RESOLVE_OK) |
|---|---|---|
| 3.12 \| poetry | 25 | 25 ✓ |
| 3.12 \| uv | 21 | 0 (missing `saleor==X` editable-self, `python-magic-bin`) |
| 3.9 \| poetry | 83 | 0 (65 missing + 18 incompatible under py312 gate) |
| 3.8 \| poetry | 15 | 0 (missing + incompatible under py312 gate) |

**Validated domain** = Calibration-12 stratum (py312 ∧ poetry): 25 units in the
population, 12 of which Calibration-12 executed with 12/12 PASS under
`source_fidelity_r1`.

## Worktrees (evidence, no full byte-verification)

- 219/219 member-task worktree directories exist under
  `D:\wp2_sf_full_d7_r1_store\worktrees` (fresh output root; store untouched).
- **18/18 Calibration-overlap worktrees byte-identical** to the frozen store
  worktrees (`SCOPE_WORKTREE_PARITY18.json`).
- **NTFS-invalid skipped paths:** 38 tasks / 190 files (`SCOPE_NTFS.json`) —
  VCR test cassettes only (never closure/smoke inputs); all 38 tasks are members
  of py39-poetry units (OUT_OF_VALIDATED_SCOPE).
- **Missing worktree ⇒ FAIL-CLOSED, never silent skip** (frozen closure needs
  member pyproject.toml for the win32 `python-magic-bin` exclusion; smoke needs
  the mounted worktree).

## Frozen-resolver limitations (frozen-authority facts, not defects)

1. **py312-only wheel-tag gate:** py38/py39 era wheels (cp38/cp39 non-abi3) are
   rejected by the frozen resolver; those strata cannot pass it as frozen.
2. **uv editable-self / markers:** the frozen R3 closure path does not exclude
   the uv root-project editable-self and does not apply uv marker semantics.
3. Both are FROZEN-AUTHORITY LIMITATIONS.  Adapting the rule is out of scope for
   this census and would need owner authorization.

## Evidence files (research/source-fidelity-full-d7-r1/)

- `FULL_D7_SCOPE_CENSUS.json` — consolidated census
- `SCOPE_ERA_LOCK_DRYRUN.json` — per-unit frozen resolution dry-run (144 units)
- `SCOPE_WORKTREE_PARITY18.json` — 18-worktree parity evidence
- `SCOPE_NTFS.json` — NTFS-invalid skipped-path counts
- `FULL_D7_POPULATION_MANIFEST.json` — frozen 144/219 population
- `FULL_D7_SOURCE_AWARE_CLOSURE_IMPACT.json` — 142 unchanged / 2 changed (F3)
- `FULL_D7_INPUT_IMMUTABILITY_AUDIT.json` — F1 byte-exact freeze audit
- `FULL_D7_DRIVER_DESIGN_FACTS.md` — frozen driver design facts

## What happens next (NOT performed)

F4 driver freeze, F5/F6 P2P-F2P tests, F7 execution, F9–F17 classification,
eligibility, freeze, LIGHT — all deferred pending owner decision.