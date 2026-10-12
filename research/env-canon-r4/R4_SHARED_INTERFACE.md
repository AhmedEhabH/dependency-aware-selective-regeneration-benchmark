# R4 Shared Interface — frozen contract

**Mission:** `M17_D7_R4_SHARED_INTERFACE_FREEZE`
**Date frozen:** 2026-10-13
**Machine encoding:** `src/benchmark/wp2/env_r4/contracts.py`
**Public package:** `src/benchmark/wp2/env_r4/__init__.py`
**Contract tests:** `tests/contract/test_env_r4_contract.py`

## Scope

This is the minimal shared interface that the four R4 tracks need so that they
can work **independently without inventing incompatible APIs**.  It is a
freeze; it is not a design, a full environment canon, or a lock-format parser.

Explicitly OUT of scope: Full-D7 execution, Docker execution, network access,
OPWS, artifact acquisition, and any redesign beyond this interface.

## Track ownership (frozen)

- **Track A / Track B** may implement the `LockParser` interface *behind*
  `env_r4.contracts` and bind it via `bind_lock_parser(...)`.  They MUST NOT
  modify `env_r4` or `contracts.py`.
- **Track C / Track D** may consume the frozen data types and the
  `parse_lock` / `wheel_compatible` entry points.  They MUST NOT modify
  `env_r4` or `contracts.py`.

Changing any type, field, signature, or rule below requires a NEW mission and a
successor schema; it is never done in place.

## Frozen common types

### `RuntimeTarget`

| field | type | example | meaning |
|---|---|---|---|
| `python_version` | `str` | `"3.12"` | target `MAJOR.MINOR` (malformed version fails closed) |
| `implementation` | `str` | `"cpython"` | Python implementation |
| `platform` | `str` | `"linux"` | OS platform |
| `architecture` | `str` | `"x86_64"` | CPU architecture |

### `SourceType` (enum, exactly four members)

| member | token(s) recognized by `from_token` |
|---|---|
| `REGISTRY` | `NULL` (no source table), `registry` |
| `DIRECTORY` | `directory` |
| `PATH` | `path` |
| `EDITABLE_SELF` | `virtual` (uv root project), `editable_self`, `editable` |

Any other source token raises `LockParseError` (**fail closed**); callers never
guess a semantic.

### `NormalizedRequirement`

| field | type | meaning |
|---|---|---|
| `normalized_name` | `str` | PEP 503 normalized distribution name (must equal `normalize_name(...)`, else fail closed) |
| `version` | `str` | locked version |
| `source_type` | `SourceType` | REGISTRY / DIRECTORY / PATH / EDITABLE_SELF |
| `source_reference` | `str \| None` | lock source reference (e.g. path); `None` for implicit registry |
| `marker` | `str \| None` | raw environment marker string |
| `marker_applies` | `bool` | whether `marker` was evaluated true for the target |
| `editable_self` | `bool` | True ONLY for the editable/virtual root project representation |

### `LockClosure`

| field | type | meaning |
|---|---|---|
| `lock_format` | `str` | lock format identifier (non-empty, else fail closed) |
| `target` | `RuntimeTarget` | target the closure was resolved for |
| `requirements` | `tuple[NormalizedRequirement, ...]` | applicable third-party wheel requirements, deterministic order; NEVER contains an editable-self entry |
| `editable_self` | `NormalizedRequirement \| None` | the explicit editable/virtual root project, or `None` |
| `exclusions` | `tuple[NormalizedRequirement, ...]` | requirements excluded because they do not apply to the target (e.g. `marker_applies` is False); visible so nothing is silently skipped |
| `fail_closed_reasons` | `tuple[str, ...]` | non-empty ⇒ the closure is INVALID and MUST NOT be consumed |

`is_valid` is `False` exactly when `fail_closed_reasons` is non-empty.
`to_canonical_dict()` and `freeze_sha256()` are the deterministic,
order-independent serialization and closure identity.

## Required interfaces

```python
parse_lock(
    lock_path: Path,
    target: RuntimeTarget,
    pyproject_path: Path | None = None,
) -> LockClosure

wheel_compatible(wheel_filename: str, target: RuntimeTarget) -> bool
```

`parse_lock` resolves a lock file for a target into a `LockClosure`; structural
failures and unknown semantics fail closed (exception or `fail_closed_reasons`).
`wheel_compatible` reports whether a wheel is usable on the target.  With no
parser bound, both entry points raise `LockParseError` (fail closed).

### `wheel_compatible` behavioural contract (for A/B implementations)

True cases (P2P):

- filename parses under the PEP 427 wheel tag grammar
  `{distribution}-{version}(-{build})?-{pytag}-{abitag}-{plattag}.whl` and
  every tag is satisfied by `target` (`pytag` admits `target.python_version`,
  `abitag` is `none`/`abiN`/`cpN` matching the target, `plattag` admits
  `target.platform` + `target.architecture`).

False cases (F2P):

- filename does not end in `.whl`;
- any tag cannot be evaluated for `target`;
- any tag is definitively incompatible with `target`;
- `wheel_filename` is empty/whitespace.

The check never depends on a task/unit identifier.

## Frozen rules

1. The editable/virtual root project is represented **explicitly** by
   `LockClosure.editable_self` and is **NOT** emitted as a third-party wheel
   requirement in `LockClosure.requirements`.  A `requirements` entry with
   `editable_self=True` fails closed at construction.
2. Source types distinguish exactly REGISTRY / DIRECTORY / PATH /
   EDITABLE_SELF (enum `SourceType`).
3. Unknown semantics fail closed: unknown source tokens raise
   `LockParseError`; a `LockClosure` with non-empty `fail_closed_reasons` is
   invalid and must never be used.  No silent skips: excluded requirements are
   carried in `exclusions`.
4. No task-ID special cases: `normalize_name`, `from_token`, deterministic
   ordering and serialization are case- and label-agnostic generic rules.
5. Deterministic ordering and serialization: `requirements` and `exclusions`
   are sorted at construction (independent of input order) and serialize
   byte-for-byte identically for semantically equal closures
   (`freeze_sha256` is the closure identity).

## Validation (targeted only)

The mission runs ONLY targeted contract validation:

1. `git diff --check`
2. Ruff on changed Python files
3. Mypy (strict) on changed production Python files
4. `py_compile` on changed Python files
5. Targeted `pytest tests/contract/test_env_r4_contract.py`

No full-suite run.

## Deliverables

| path | role |
|---|---|
| `research/env-canon-r4/R4_SHARED_INTERFACE.md` | this specification |
| `src/benchmark/wp2/env_r4/__init__.py` | public package surface |
| `src/benchmark/wp2/env_r4/contracts.py` | frozen machine encoding |
| `tests/contract/test_env_r4_contract.py` | minimal contract tests |

**Status:** `M17_D7_R4_SHARED_INTERFACE_FROZEN`