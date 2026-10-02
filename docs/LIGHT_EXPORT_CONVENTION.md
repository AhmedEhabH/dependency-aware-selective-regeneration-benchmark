# LIGHT Export Convention (effective 2026-10-02, future exports only)

**Filename convention:** `project-light-YYYY-MM-DD-HHMM.zip`

Examples:
- `project-light-2026-10-02-1855.zip`
- `project-light-2026-10-03-0000.zip`

## Rules

1. **Lowercase prefix:** filename starts with `project-light` (lowercase).
2. **Timezone-aware local timestamp only in the filename:** the only variable
   part is the machine's local creation time `YYYY-MM-DD-HHMM` at **minute**
   precision (no seconds, no timezone offset, no suffix).
3. **No result/STOP/experiment token in the filename:** a plan id, STOP token,
   phase, experiment name or result claim never appears in the filename.
4. **Internal manifest records identity fields.** `LIGHT_MANIFEST.json` inside
   the zip records:
   - `plan_id`;
   - `stop_or_completion_token` / `label`;
   - `phase`;
   - `git_commit` and `git_tag` (best-effort, when the export runs inside a git
     working tree);
   - `sha256` (per-file and the zip digest printed in the LIGHT_EXPORT block);
   - `export_timestamp_utc` / `created_utc` (UTC ISO-8601);
   - `created_local` (timezone-aware local creation time, ISO-8601 with
     offset) and `local_offset`;
   - `source_run_identifiers` (from the profile, when provided).
5. **Collision fails closed:** if a file with the exact minute-resolution name
   already exists, the exporter refuses to overwrite it. It prints
   `LIGHT_EXPORT_COLLISION` and returns a non-zero exit code. Re-running is safe
   only after the colliding file is moved/removed or after a later minute.
   No suffix is ever invented.
6. **Historical LIGHT filenames are never renamed** in-place, because their
   hashes/paths are already cited (e.g. the M16 STOP LIGHT
   `project-LIGHT-STOP_M16_ADAPTER_FAIL-2026-10-02-1606.zip` stays as-is).
   This convention applies only to future exports.

## Why

Stable sortable filenames, no result leakage in the name, simpler archival
automation, and an unambiguous, reviewer-friendly local timestamp.

## Implementation

`scripts/wp2_export_light.py` produces the new-convention name by default
(`future_name()`), keeps the profile's include/exclude/cap semantics unchanged,
and fails closed on collision. The profile fields `plan_id`, `phase` and
`source_run_identifiers` are optional manifest metadata; when absent they are
recorded as `null` / `[]`.

## Acceptance

- a future export filename matches `^project-light-\d{4}-\d{2}-\d{2}-\d{4}\.zip$`;
- a same-minute collision fails closed (no overwrite, no suffix);
- the manifest records a timezone-aware local creation timestamp plus UTC;
- historical exports are untouched;
- exporter unit tests pass (`tests/unit/wp2/e2e_v22/test_export_light_v22.py`).