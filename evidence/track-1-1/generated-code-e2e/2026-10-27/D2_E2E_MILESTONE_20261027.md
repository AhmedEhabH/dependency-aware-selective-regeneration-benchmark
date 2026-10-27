# Track 1.1 — Generated-code D2 exploratory E2E (27 October 2026)

**Decision:** E2E measurement pipeline **PASS**, diagnostic D2 repair adequacy **FAIL**. Frozen A5-R1 official candidate remains **STOP** (`EDIT_2_NOOP_STOP`) and is NOT a successful model generation attempt.

## Behavioral findings (independently checked from original user-host ZIP)

| Endpoint | Distinct tests stable-pass in all 3 repeats | Physical pass / total | Interpretation |
| --- | --- | --- | --- |
| F2P — tests of required change | **1 / 3 (33.3%)** | 3 / 9 | Two required behaviors remain broken |
| P2P — frozen regression guard | **103 / 103 (100%)** | 309 / 309 | No regression detected in this selected subset |
| Combined | **104 / 106** | **312 / 318** | Overall aggregate pass rate is NOT a valid substitute for F2P |

All **318** physical invocations have JUnit XML and a matching command-ledger entry; all **648** hashed evidence files in original ZIP match SHA-256. There were **6 F2P failures**, no JUnit error/skip, and no mixed outcomes across the three repeats for any node.

## Two concrete F2P failures (3 failures each)

1. `saleor/app/tests/test_app_commands.py::test_creates_app_from_manifest_skips_sending_token_when_target_url_not_provided`: the test observes `app.tokens.count() == 1` while expected 0. The D2 code creates a default token unconditionally **before** its `if token_target_url:` guard. Not sending the HTTP POST does not meet the tested no-token semantics.
2. `saleor/app/tests/test_validators.py::test_new_tab_relative_url_without_app_url`: the test expected a `ValidationError` for a relative `new_tab` extension URL when `appUrl` is absent, but the D2 validation admitted it. Validation semantics remain incomplete.

**F2P pass:** `saleor/app/tests/test_installation_utils.py::test_install_app_manifest_data_without_token_target_url` passed in all 3 runs.

The above diagnoses are supported by JUnit failures and by the model-authored D2 patch already in this branch; they are NOT instructions to change the frozen candidate retrospectively. Future implementations must be **new, prospectively declared attempts** with no relabeling of the original attempt.

## Reproducibility / provenance

- Task: `saleor-rc-7e42fc67ce72`; frozen parent `798632158394c9f2911e6d36e8e424fd55007dc4`; NEG tree `65cd0b6e07e73c102ae600fea0fabea827b7fe29`.
- Model-authored D2 post-hoc diff SHA-256: `de027cdf63d9badf221fd6ec0807a0425aa54a4e8c5da005629f1c69f396277f`.
- OCI image: `sha256:a6e743589b60a4c15676eece07f52ed8347dc501bc782cc53ddffb7200d06c4c`.
- Lockfile SHA-256: `a4c21a2deb52e20e52b691857fd5adae8f130e6844626c18b3aaebc688eb2d66`.
- Preparation receipt SHA-256: `4094dc06e834daadc309544de1e7fa2baebbc1f35fb8fcd626f6106239a96611`; offline hashed dependencies PASS, fresh DB and blocked egress confirmed in original run evidence.
- Original raw evidence ZIP retained by researcher: `T11_D2_RESUME_E2E_20261027T183920378Z.zip` SHA-256 `b3327793e5c926d6621bbb694fa231fb5a35f535e62d89112b5bf832f472463a`.
- Original `D2_JUNIT_AUDIT.json` SHA-256 `02b1779cb21bc10d659d77fc06a82b1e03ad7a5ec6b1ac9e08aea34175ba02c7`.
- Independent read-only auditor: `VERIFY_D2_RAW_ZIP.py`; publication: `D2_E2E_SANITIZED_AUDIT.json` and `D2_E2E_NODE_OUTCOMES.csv`.
- No additional model API calls during evaluation. Measurement runtime reported **5,584 seconds (1h 33m 4s)**. **Caution:** cumulative per-invocation timing fields sum to a greater value than whole-run elapsed; timing needs reconciliation before any efficiency comparison.

## Scientific boundaries and next gate

This is **one task**, one **post-hoc derivative** candidate; three repeats used the same DB/runtime, so are not independent experimental replicates. The 103 P2P nodes only represent the frozen regression subset. The total 312/318 passing invocations is dominated by P2P, so it is scientifically wrong to report 98.1% as regeneration correctness.

**Next gate:** Freeze this D2 evidence, write a prospective pre-declared protocol for the next genuinely model-generated patch and ensure it addresses complete F2P semantics without hand-repairing D2. No new model calls without explicit authorization. Temporal availability of the proxy description and dataset representativeness remain open research issues.

**Data handling:** Original per-test stdout/stderr contains a synthetic authentication token; do not upload raw original ZIP, container logs, or test traces to the public repository. This milestone publishes aggregate outcomes and immutable SHA fingerprints only.
