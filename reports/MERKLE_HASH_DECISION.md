# Merkle / Hash Decision

**Date:** 2026-09-11

## 1. What Merkle/content hashing can help with

- snapshot identity (exact state fingerprints)
- detecting actual byte changes
- cache invalidation
- incremental regeneration
- incremental graph rebuilding
- preservation verification
- artifact integrity

## 2. What it does NOT do

Merkle/content hashing does **NOT** by itself infer **semantic impact** from a
new requirement. Hashing tells you *what bytes changed*; it does not tell you
*which files a requirement change affects*. Impact selection remains a model
reasoning task (as evaluated in the completed studies), and dependency
reasoning is a separate graph question.

## 3. What this project already uses

- Git content-addressing (commits/trees/blobs)
- SHA-256 evidence hashing (raw responses, sidecars)
- candidate-universe hashes (144-file universe, canonical hash)
- raw-response hashes (per-run SHA-256)
- graph hashes (canonical graph hash, deterministic rebuild)

## 4. Decision

**MERKLE_RECOMMENDATION: DEFER — NOT A CURRENT IMPACT-SELECTION TREATMENT**

A Merkle subsystem is not needed for the current impact-selection studies. The
existing Git + SHA-256 evidence machinery already provides snapshot identity,
byte-change detection, cache/incremental-rebuild foundations, and artifact
integrity. A Merkle tree would add engineering complexity without changing the
impact-selection treatment. No Merkle subsystem was implemented in this task.