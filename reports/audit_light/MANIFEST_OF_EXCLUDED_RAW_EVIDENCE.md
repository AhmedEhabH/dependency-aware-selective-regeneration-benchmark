# Manifest of Excluded Raw Evidence

Package: `audit_light_m1a_m1b_final.zip`

Total excluded raw files: **0**

All M1A/M1B raw-response evidence is INCLUDED in this archive (including research/controlled-encoding-ablation-16k-01/runs/raw/*.txt, which exists only in the working tree and is not committed to git). Nothing is excluded, so no raw file needs to be fetched from a tag. The prior Stage-C manifest content (commit 0f81843) remains in git history.

This archive embeds every M1A/M1B raw provider response body and its SHA-256
sidecar, so an auditor can recompute all claims and verify all raw hashes from
the archive alone. No raw file is excluded, and therefore no raw file needs to
be fetched from an immutable tag for this package.

The immutable study tags still hold the complete snapshots for independent
verification:

- `controlled-encoding-4096-feasibility-boundary-01` (M1A)
- `paper-replication-artifact-controlled-encoding-4096-boundary-01` (M1A snapshot)
- `controlled-encoding-ablation-16k-wiring-verified-01` (M1B wiring)
- `controlled-encoding-ablation-16k-study-01-audited` (M1B study)
- `paper-replication-artifact-controlled-encoding-ablation-16k-01` (M1B snapshot)
