# R4-D Calibration Coverage Report

**Status:** `DRAFT_PENDING_R4_INTEGRATION` — NOT FINAL. This mission inspects frozen population/environment metadata only; it does NOT execute calibration or Full D7.

## Population

- N_VALIDATION_UNITS = **144** (expected exactly 144).
- N_MAPPED_TASKS = **219** (expected exactly 219).
- Population identity SHA-256: `ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac`

## Exact strata counts

| Python + lock | count |
|---|---|
| Python 3.12 + Poetry | 25 |
| Python 3.12 + uv     | 21 |
| Python 3.9  + Poetry | 83 |
| Python 3.8  + Poetry | 15 |

## Unique environment dimensions

- Unique Docker profiles: **4** (dk-py312-bookworm, dk-py38-bullseye, dk-py39-bookworm, dk-py39-bullseye)
- Unique native profiles: **10** (nat-02b9bb45ba01, nat-0728db662cde, nat-34c1a3756742, nat-591718dce38a, nat-62bc3631c27d, nat-a39687f3d19c, nat-cc2f641e9e04, nat-d35546f097f4, nat-d7d5ae76a87f, nat-f65b9bf250fd)
- Unique install routes: **4** (LOCK_FRAGMENT_MAIN_PLUS_DEV, REQ_MAIN_PLUS_LOCK_DEV, UV_EXPORT, V2_EDITABLE_PLUS_LOCK_DEV)
- Unique wheelhouse eras: **3** (py312, py38, py39)
- Unique lock adapter paths: **2** (poetry, uv)
- Unique environment paths (full signature): **13**

## Source-fidelity paths

| unit | member task | DIRECTORY sources | overlay state |
|---|---|---|---|
| vu-692af9112c6d | saleor-rc-19bb9b070965 | PyXB 1.2.5, authorizenet 1.1.4 | PRESENT_PREEXISTING (frozen source-fidelity-r1 wheels) |
| vu-b9808f19ace4 | saleor-rc-e6198146186d | PyXB 1.2.5, authorizenet 1.1.4 | PRESENT_PREEXISTING (frozen source-fidelity-r1 wheels) |

## Proposed calibration

- N_CALIBRATION = **12** (deterministic, metadata-only selection).
- Plan SHA-256: `8ec20f360f62c7f4d072ad03bb5fe042c85fa98bad64757715227b5c88de687d`
- Selection rule: walk frozen unit order; force both source-fidelity units; select a unit iff it covers at least one still-uncovered required category; never uses FIRST_N and never consults outcomes.

Selected units (plan order):

```
1. vu-b9808f19ace4 (3.12 poetry V2_EDITABLE_PLUS_LOCK_DEV dk-py312-bookworm nat-34c1a3756742)
2. vu-692af9112c6d (3.12 poetry V2_EDITABLE_PLUS_LOCK_DEV dk-py312-bookworm nat-f65b9bf250fd)
3. vu-e4998719ee01 (3.12 poetry LOCK_FRAGMENT_MAIN_PLUS_DEV dk-py312-bookworm nat-34c1a3756742)
4. vu-db74b3640c98 (3.12 poetry LOCK_FRAGMENT_MAIN_PLUS_DEV dk-py312-bookworm nat-a39687f3d19c)
5. vu-422bca69f329 (3.12 poetry LOCK_FRAGMENT_MAIN_PLUS_DEV dk-py312-bookworm nat-cc2f641e9e04)
6. vu-13c1de1de71e (3.12 uv UV_EXPORT dk-py312-bookworm nat-02b9bb45ba01)
7. vu-b78ebcf3e530 (3.12 uv UV_EXPORT dk-py312-bookworm nat-591718dce38a)
8. vu-bfe987de6e53 (3.12 uv UV_EXPORT dk-py312-bookworm nat-0728db662cde)
9. vu-eda4e9f82401 (3.8 poetry REQ_MAIN_PLUS_LOCK_DEV dk-py38-bullseye nat-62bc3631c27d)
10. vu-457f26c93ff1 (3.9 poetry REQ_MAIN_PLUS_LOCK_DEV dk-py39-bullseye nat-d35546f097f4)
11. vu-ffe68ddec229 (3.9 poetry V2_EDITABLE_PLUS_LOCK_DEV dk-py39-bookworm nat-f65b9bf250fd)
12. vu-0e0ef31c7634 (3.9 poetry REQ_MAIN_PLUS_LOCK_DEV dk-py39-bullseye nat-d7d5ae76a87f)
```

## Coverage achieved

- Required categories: 27
- Covered categories: 27
- Uncovered categories: **0**
- overall_pass = **true**

## Missing local Docker images

- All expected images present locally: **true** (14/14).
- Absent images: none
- Registry digests are NOT frozen (ENV_CANON_GATE `all_image_digests_frozen` = false); images are local sha256-identifiable but not digest-pinned.

## Unresolved metadata ambiguity

- None: every unit maps to an explicit python version, lock type, install route, Docker profile and native profile in the frozen matrix.
- Note (not blocking): unit `vu-692af9112c6d` carries native profile `nat-f65b9bf250fd` (a bookworm-era profile) on the `dk-py312-bookworm` Docker base per the frozen matrix; recorded as-is, no reinterpretation.

## Dependencies on R4-A / R4-B / R4-C

- **R4-A / R4-B:** `poetry_lock_parser`, `uv_lock_parser`, `wheel_tag_parser` are PENDING_R4_A (Track A or Track B, per frozen interface neither is assigned per format).
- **R4-C:** `linux_materialization` is PENDING_R4_C (Linux-side worktree/materialization).
- `source_fidelity_overlay`, `docker_images`, `network_disabled_install` are PRESENT_PREEXISTING (frozen pre-R4 baseline).

## Plan label

**`DRAFT_PENDING_R4_INTEGRATION`** — do NOT label FINAL until R4-A/B/C integration is real.
