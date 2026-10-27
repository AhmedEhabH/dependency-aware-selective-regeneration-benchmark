# Track 1.1 — D3 test-informed repair control (27 October 2026)

**Status at authoring:** repair implementation and evaluator kit constructed; **actual host Saleor/Docker tests NOT_RUN**. The official A5-R1 is still STOP (`EDIT_2_NOOP_STOP`), and the original D2 post-hoc diagnostic is immutable. This D3 is an **engineering/test-informed repair control**, **not** a fresh model-generated or blind pass@1 patch. It has $0 additional generator API spending. The repairs were designed after researchers saw D2 F2P failures.

## Fixed baseline

- Parent: `798632158394c9f2911e6d36e8e424fd55007dc4`, task `saleor-rc-7e42fc67ce72`, NEG tree `65cd0b6e07e73c102ae600fea0fabea827b7fe29`.
- Historical D2 diagnostic patch SHA-256: `de027cdf63d9badf221fd6ec0807a0425aa54a4e8c5da005629f1c69f396277f`.
- Exact D2 working-tree source hashes are embedded in `T11_D3_CREATE_CONTROL.py` and checked before copying or editing.
- OCI image `sha256:a6e743589b60a4c15676eece07f52ed8347dc501bc782cc53ddffb7200d06c4c`; `uv.lock` SHA-256 `a4c21a2deb52e20e52b691857fd5adae8f130e6844626c18b3aaebc688eb2d66`.
- Hashed offline installation qualified: `PREP_PASS.json` SHA-256 `4094dc06e834daadc309544de1e7fa2baebbc1f35fb8fcd626f6106239a96611`, dated 27 Oct. This preparation included a one-time online public wheel acquisition separate from the offline measurement. The measurement reuses the qualified WSL cache.
- Frozen F2P nodes: R7 SHA-256 `f547b88af226ba8ed0c1745c77bf6b90b1f12f5d2e715013c47234e4fcd98cf9` (3); P2P R8 SHA-256 `d3392709e5b6a62dd885fc9a29845888259285542a622bb78687f9ff4bfea9a0` (103).

## Declared D3 transformation (relative to exact D2)

1. **Token ownership/security:** move default `app.tokens.create(...)` *inside* the `if token_target_url:` block, initialize `token=None` in the missing-target case, and leave the existing send-error compensation / rollback and plugin event behavior otherwise unchanged.
2. **Relative extension validation:** for a relative URL, reject a target other than `app_page` when `appUrl` is absent. `tokenTargetUrl` alone does not justify a non-`app_page` relative URL. Leave D2's other validation logic untouched to minimize uncontrolled changes.

No frozen tests, data, OCI image, lock versions, inputs, developer reference patch or original D2 files are modified. D3 is constructed at runtime **only on a copy** of a hash-verified D2 stage; the exact D3-vs-D2 patch and its SHA-256 are written to fresh evidence.

## Execution plan and STOP rules

1. Validate ZIP and per-file SHA-256, `bash -n`, Python `--selftest`, frozen R7/R8 nodes and exact qualified preparation receipt.
2. Create a fresh private copy of frozen D2; apply *only* the two declared edits using exact, unique source anchors, verify AST and Git whitespace check. If any anchor or SHA differs, STOP without fuzzy patching.
3. Start new internal Docker bridge and PostgreSQL; verify no host-port exposure, two blocked egress probes, fresh DB TCP, lock SHA, **237 Linux** hashed/offline dependency installation and `uv pip check`.
4. Check `ruff check` on the two touched files. Record `ruff format --check` separately (failure is reported, not silently reformatted). **No automatic code repair after pytest**.
5. Run 3 F2P nodes ×3 physical pytest = **9**. Validate exact JUnit names, ledger rows, hashes and PASS. If fewer than 3 distinct stable F2P passes, **STOP without P2P**; retain evidence and record this as D3 functional FAIL.
6. Only on F2P 3/3, run **103 P2P nodes ×3 = 309** physical invocations. Validate all 318 and require stable P2P 103/103; do not count aggregate 312/318 or only pass rate as success.
7. Produce `D3_JUNIT_AUDIT.json`, `D3_QUALITY_REPORT.json`, source SHA receipts and local raw logs, and verify the frozen D2 files still have original hashes; destroy ephemeral Docker DB/network and D3 copy. Preserve qualified private wheel cache unchanged.

`D3_106_HASHED_OFFLINE_E2E=COMPLETE_TEST_INFORMED_REPAIR_CONTROL` is allowed **only after the full 3/3 + 103/103**, exact JUnit integrity, and static lint success. Any failure is preserved as evidence with STOP/FAIL classification and the original A5-R1 unchanged.

## Scientific limits

- A test-informed repair does NOT demonstrate novel selective regeneration effectiveness, generalization, or independent model pass@1. This is one task; evaluating quality versus competitors requires new unseen tasks and controlled equal-budget baselines.
- The three pytest repetitions share a DB/runtime across nodes; they are repeated measurements, not independent samples. A 100% selected P2P rate is not full repository regression safety.
- Code quality is a vector: frozen behavior, targeted regression, Ruff, formatting observation, change size, source identity, and artifact provenance. Coverage, mutation score, security review, and full repository tests remain unqualified until separately measured.
- Raw test output can contain synthetic tokens and transient environment metadata. Keep raw ZIP/local logs private; publish only reviewed sanitized receipts and the incremental patch after review. Do NOT commit credentials, PostgreSQL secrets, or raw logs.

## GitHub policy

Dedicated branch only: `research/track-1-1-generated-e2e-2026-10-27`; latest verified D2 milestone `d2281ef01c07762e827937f5de54d6dd680b8459`. Keep `PROGRESS.md` append-only, never rewrite D2 evidence or merge into main. Pre-test protocol and post-test behavior results should be committed as **separate milestones**, with meaningful SHA references. The connected GitHub integration is read-only for write actions; researcher-host authenticated Git performs pushes.
