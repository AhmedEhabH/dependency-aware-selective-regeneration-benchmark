# Track 1.1 — Generated-code E2E evidence and diagnostic

**As of 27 October 2026:** A5-R1 obtained model HTTP 200 but **failed** frozen patch qualification at `EDIT_2_NOOP_STOP`. All generated-code behavioral tests remain **NOT_RUN**. Its D2 derivative removes only a strict no-op in offline post-hoc analysis to permit diagnostic functional study; D2 MUST NOT be counted as an official model/pass@1 success.

- [PROGRESS.md](PROGRESS.md): attempts, 106-node test gates, identities, SHA receipts, measured usage/cost and next milestone.
- [SCIENTIFIC_RISK_REGISTER.md](SCIENTIFIC_RISK_REGISTER.md): novelty, dataset fairness/leakage, behavioral sufficiency, null results and readiness for committee review.
- [D2_DIAGNOSTIC_RECEIPT.json](D2_DIAGNOSTIC_RECEIPT.json): machine-readable derivation and original fingerprints.
- [D2_DIAGNOSTIC_PATCH_LF.diff](D2_DIAGNOSTIC_PATCH_LF.diff): **post-hoc diagnostic, not the frozen A5 candidate**, with exact SHA in receipt.
- [D2_GENERATED_SOURCE_SHA256_LF.json](D2_GENERATED_SOURCE_SHA256_LF.json): expected candidate LF source hashes for evaluator-only staging.
- [D2_GENERATED_SOURCE_SHA256_CRLF.json](D2_GENERATED_SOURCE_SHA256_CRLF.json): separately recorded line-ending variant.

**Original private evidence:** `T11_A5_R1_EVIDENCE_20261027T071318122855Z.zip`, SHA-256 `1ecf859670c7946ed47083422e627febf7cf182d8af61430cec919e38c4a1d2b`. Not uploaded publicly because raw transport metadata can include account identifiers. Preserve locally in an immutable archive. Do not put OpenRouter keys into Git.

Tests must run on the researcher's isolated, qualified Saleor runtime; this GitHub commit only publishes docs and deterministic diagnostic source, and has performed **zero** new 106-node tests.

- [A3_DIAGNOSTIC_REPLAY.py](A3_DIAGNOSTIC_REPLAY.py) and [A3_ORIGINAL_RESULT_RECEIPT.json](A3_ORIGINAL_RESULT_RECEIPT.json): unchanged original A3 retrospective diagnostic program and signed-by-hash receipt, for later Track 3 handoff; program SHA-256 `e611608b8b9c78668ce0a6d91d2878126dde3c61d315452ffad4959aa06c161e`, receipt SHA-256 `81bd8b72bb53249be662974b60ab9b98d8b9700f8a3b57aaf1239f7055b2257d`. Diagnostic replay still needs its original A3 input, and it failed syntax; not a successful attempt.
