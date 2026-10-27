# Track 1.1 — Generated-code E2E progress (2026-10-27)

Status: **STOP / NO GENERATED-CODE E2E CLAIM**. Research task: `saleor-rc-7e42fc67ce72`; parent `798632158394c9f2911e6d36e8e424fd55007dc4`; NEG tree `65cd0b6e07e73c102ae600fea0fabea827b7fe29`. A retrospective proxy task description was used; parent-cutoff availability is unproven. This branch contains observational reporting, NOT the frozen A1–A5 scientific evidence, and DOES NOT amend earlier receipts.

## Attempts and attrition

| Attempt | Transport | Primary STOP | Model response | Generated F2P/P2P |
| --- | --- | --- | --- | --- |
| A1 | 429 | upstream rate limitation | none | NOT_RUN |
| A2 | 200 | invalid unified diff | yes | NOT_RUN |
| A3 | 200 | non-unique edit locator | yes | NOT_RUN |
| A3-D1 (post hoc) | offline | Python syntax failed | modified diagnostic | NOT_RUN |
| A4 | 200 | `NOOP_EDIT_STOP` | yes; wrong-file edit found secondarily | NOT_RUN |
| A5 | 429 | DeepInfra `engine_overloaded`; shared upstream pool | none | NOT_RUN |
| A5-R1 | 200, 1 new POST | `EDIT_2_NOOP_STOP` | yes, 4 edits | NOT_RUN |
| A5-R1-D2 (post hoc) | offline | preliminary Git-LF apply and AST PASS; functional test NOT_RUN | 3 original non-no-op edits only | NOT_RUN |

**Interpretation:** A5-R1 is a qualification failure even though the strict-text content includes 3 substantive edits and 1 identical no-op. D2 is a derived diagnostic; it is not a new independent model response and must NEVER improve the official success rate. The 75% figure (3/4) counts non-no-op edits, **not functional accuracy**. Raw original model output is retained separately as immutable evidence with its hash; avoid copying token-bearing HTTP metadata into a public repository.

## A5-R1 machine receipts

- Original ZIP SHA-256: `1ecf859670c7946ed47083422e627febf7cf182d8af61430cec919e38c4a1d2b` (kept by researcher; not uploaded into public git).
- Model response exact UTF-8 SHA-256: `014a73dab35cd32d13fab3195fa0440568c9b82bab6c13c9ccee53efb91c7ee6`.
- Raw HTTP response SHA-256: `0b77850846906e121e26f68e1f32f3ae64b2780afa92b32a62e4959a93cee4ed`.
- Frozen A5 request SHA-256: `7877cebcd0718216c71f9b29014f65835fabade605711d4abd3b98003a79b1c9`.
- Frozen A5 protocol SHA-256: `762085cdf267b8c078c933f1881d911a3ebabd7d38947dd14b766e80dbf224ff`.
- Frozen A5 engine SHA-256: `a4af386e28af1d88ca6c26328b385fac0afe7602de1d29212f621fc1ed18015d`.
- A5-R1 prompt tokens: **5,306**; completion tokens: **1,135**; total **6,441**; charged **$0.0027268**. Earlier A2+A3+A4 known charges: **$0.0068680**. Thus total of **documented paid 200-response costs** is **$0.0095948**, excluding A1, A5 429 and any unrelated key usage, all unverified. A5-R1 key cap $0.25 cumulative, pre-run balance $0.243132.
- A5-R1 HTTP interval in evidence: 2026-10-27T07:13:18.327092+00:00 to 2026-10-27T07:13:27.510996+00:00; exact wall-clock of future functional tests not measured.
- A5-R1 response `4` structured edits; only `3` non-no-op (75% structural share). `EDIT_2_NOOP_STOP` is authoritative. No patch qualified by official protocol.

## D2 diagnostic (non-benchmark)

`D2_DIAGNOSTIC_PATCH_LF.diff` is reproducibly derived by removing only the third JSON edit, because its `old_lines` and `new_lines` are **identical**. All other code edits are exactly model-authored. The frozen A5 engine's Git LF synthetic applicability + AST checks passed post hoc. The candidate likely implements 2 requested high-level changes (optional required manifest field; conditional token POST), but its `_clean_extension_url` rewrite may reject previously allowed absolute extension URLs when both `appUrl` and `tokenTargetUrl` are absent. Behavior and regression status are **UNKNOWN** pending real tests. Not 75% correctness, not reference-validated, not independently prospective.

- D2 diff SHA-256: `de027cdf63d9badf221fd6ec0807a0425aa54a4e8c5da005629f1c69f396277f`.
- D2 Linux LF source SHA-256: installation_utils `f2bc364b2dde5ba64b0020a89be7a845321fa552e0685ec2174f66817c370224`, manifest_validations `7b442c57b450f9c968b0ddd912d163dd374c882fce9dd847ab3d277660374042`.
- Frozen F2P: **3 distinct test nodes** x 3 invocations = **9**, F2P **NOT_RUN**.
- Frozen P2P: **103 distinct test nodes** x 3 invocations = **309**, P2P **NOT_RUN**.
- 106 distinct nodes, 318 expected invocations. References R7/R8 verified separately and are NOT model-generated code.

## Operational next gate

1. Preserve A1–A5 receipts and one batch lock; no re-execution merely to change labels.
2. Stage D2 on a fresh frozen NEG Git tree, with patch SHA + clean-parent original Git LF SHA + generated LF source hashes. **Never edit the candidate by hand**. This is a diagnostic track, not official pass.
3. Verify pinned OCI image digest, isolated DB provenance, blocked egress, resource and disk headroom, and fresh run folder. STOP on missing proof; don't invent image names/commands.
4. Run F2P first, then P2P if infrastructure is valid, each exactly three physical invocations per frozen node, retaining fresh JUnit XML and nonzero return codes (assertion failures are legitimate measurements). Run auditable aggregate counts. Do not treat three runs sharing a DB as independent statistical replicates.
5. Report functional counts as e.g. `F2P passing distinct /3`, `P2P passing distinct /103`, plus fail/skip/error categories. If D2 passes, label "post-hoc derived diagnostic succeeded" only. Reserve prospective claim for a separately preregistered protocol not tuned on these outputs.
6. Qualify additional parent-cutoff task inputs, dataset-wide attrition and competitors before generalization. At least one task is not a general scientific result.

## Resource/accounting controls

No new paid calls or OCI/test runs were executed while preparing this GitHub report. D2 derivation requires negligible local disk; actual Docker/test data usage, egress, execution time and DB cleanup remain **NOT_MEASURED** and must be reported from user's host only. API key, private raw HTTP metadata, owner identifiers, and tokens must not be committed. Change-scope coverage is not demonstrated by syntactic match alone.

Original A3 diagnostic replay program and original A3 result receipt are preserved unchanged in this package with exact SHA-256 listed in README. The A3 post-hoc D1 AST result is FAIL; not rerun here. No independent contemporaneous researcher GO is claimed for A3 (NOT_CAPTURED).
