# WP-2 C4 Provenance Hardening (2026-09-23)

## 1. Resolution of the bundle-hash issue

`b5074bff...` is a **WHOLE-RUNNER hash**: it was computed over the full
`HARNESS_FILES` list (classifier modules + era resolver + dry-run runner +
MAIN/DEV sweep runners + orchestrator). It therefore changes whenever any
persistence/orchestration file changes (e.g. the orchestrator spike-fix or the
new C4 JUnit-archiving lines), even though classification semantics are
unchanged.

Per the requested A/B determination: **B — obsolete whole-runner hash that must
be separated.**

## 2. Split identities (no C2 rewrite, no retroactive re-attribution)

- **C2_FREEZE_IDENTITY**: the 220 C2 records keep the identity they recorded
  (`classifier_bundle_sha256 = b11374fe…`), which is the original
  pre-optimization whole-runner freeze. The bundle actually executed at C2 run
  time is documented in the REVISED freeze (current whole-runner hash
  `7bdbf714…`). C2 is NOT rewritten and NOT re-attributed.
- **C4_SEMANTIC_FREEZE_IDENTITY** (new, stable):
  SHA-256 over the semantic classifier files only
  (`oracle_semantics_v2.py`, `oracle_confirmation.py`):
  `01c3430f221e70fb75ff4dbf1c0e5093a3c1305f2c870e1b20e2b6c4b64dd337`.
  This hash is **independent of persistence/orchestration changes** and is the
  authoritative "classifier bundle" identity for C4.
- **C4_PERSISTENCE_REVISION** (new):
  `c4-persistence-v2-2026-09-23` — bumped when persistence/provenance code
  changes (current: JUnit copy-only archiving added; whole-runner hash
  `7bdbf714…`).
- The 4 existing C4 records recorded the whole-runner hash `b5074bff…`; they
  remain valid because their semantic classifier identity
  (`01c3430f…`) is unchanged. New C4 records will record the semantic identity
  + persistence revision.

## 3. Provenance note

- No C2 result is attributed to any C4 revision.
- The whole-runner hash remains informational; the semantic classifier hash is
  the scientific identity.

## 4. C4_PROVENANCE_HASH_STATUS = REPAIRED (semantic identity defined and
stable; self-referential whole-runner hardcode superseded)