# AI Account-Transfer Handoff — CURRENT v0.9.22 CANDIDATE State (2026-08-24)

**Read this file FIRST.** It is the single authoritative snapshot of the
current project state for any AI agent or human resuming on a new account.
Older files contain valuable history, but their "Current" sections may be
superseded — this file wins every contradiction.

---

## 1. Current truth (memorize these facts)

| Fact | Value |
|---|---|
| Real Kaggle v0.9.21 model preflight result | **FAILED at the long-context probe — CUDA OOM: 12,044 prompt tokens / 64-token output budget / failed allocation 21.62 GiB == exactly `12044*12044*40*4 bytes = 21.6153 GiB`, the full float32 40-head quadratic attention score matrix** after repository preflight / dependencies / Qwen 14B BNB-NF4 load (`qwen_model_load[bnb-nf4]: PASS` — the old 2026-08-05 model-load OOM fix still works) / GPU-only device map / 2x Tesla T4 / per-GPU headroom (min free 7.764 GiB) / short generation probe all PASSED; **v0.9.21 Real Pilot REJECTED BEFORE LAUNCH — no Experiment ID / no RunRecord created; no stable tag moved** |
| Root cause | The effective runtime attention path materialized the math/eager fallback during prompt prefill (offloaded KV cache does not cover prefill attention; `device_map=auto` is not tensor parallelism) |
| Closure branch | `fix/pilot-v0922-long-context-attention-memory-closure` (from clean main `58d1be533c98ca9bafc9a344f2a73f8a140b9540`, v0.9.21 reconciled) |
| Fix set (Tasks A–F) | Task A explicit `attn_implementation="sdpa"` at from_pretrained; Task B fail-closed CUDA generation inside `sdpa_kernel([FLASH_ATTENTION, EFFICIENT_ATTENTION])` (no math/eager fallback; missing torch.nn.attention API on CUDA fails closed); Task C canonical attention evidence (`requested/effective_attn_implementation`, `sdpa_kernel_policy=flash_or_efficient_no_math`) persisted in preflight JSON + rendered in the human table + enforced by the fail-closed `attention_policy` check and pilot launch authorization; Task D corrected OOM diagnosis (long-prompt OOM reports prompt-prefill evidence + free GiB, never advises completion-cap reduction); Tasks E/F regression-guard prior memory fixes and the unchanged 12000/64 gate. RED/GREEN proven: 12 backend + 18 preflight contract tests failed against v0.9.21 code before the fix; full suite **2407 passed / 33 skipped / 0 failed**; dry-run pilot 48/48 (unique IDs, 0 model calls, 0 tokens) |
| Accepted release | `v0.9.21-pilot-exec-ready` @ annotated tag peel == artifact source commit == merge `e308047c9c05f38316d80ce565bac1b51d105bfa`; archive SHA-256 `62e377467e225d336cbcaa70a2c610b5080e329e1a4e6578fbcbdc1af7dbee40`; trust/provenance 0 mismatches; target-shaped Gates 1-3 + full preflight GREEN (runs 32692489617 / 32694137255) — **superseded as launch candidate by the v0.9.22 attention closure; its repository/per-cell fixes remain VALID and are carried forward** |
| v0.9.22 stable tag | **DOES NOT EXIST YET.** Per the one-shot flow: build the exact candidate artifact from the merge commit → run the fresh Kaggle model preflight ONLY (same 12k target, same 64-token probe) → only on PASS create `v0.9.22-pilot-exec-ready`. If the Kaggle proof FAILS, return to the SAME v0.9.22 task (never spawn v0.9.23) |
| Real Pilot status | **NOT STARTED** (no 48-cell launch while untagged) |
| Exact next action | Phase 2 COMPLETE + candidate consistency closure COMPLETE (final merge `ba08392…` on pushed main; anchors frozen at the new merge; candidate artifact `3fd98626…` built; trust/provenance 0 mismatches; exact-artifact dry-run 48/48 with the new source commit in every record) → upload the exact artifact to Kaggle for the model-preflight-only proof (12k probe must PASS) |
| Per-cell validation runtime seam | **CLOSED by v0.9.21 (carried forward).** Generated-workspace validation uses explicit `--validation-python` per-repository interpreters (no sys.executable fallback), carries the frozen repository env into `FunctionalValidator` (parent `os.environ` never mutated), and runs under an explicit bounded `--validation-timeout 1800` on Pilot launch AND resume (separate from the frozen model `--timeout 600`). Target proof: Saleor full primary exit 0 in 941.42s < 1800s (CI run 32692489617) |

Frozen Pilot matrix (unchanged, pre-registered in
`docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md`, DECISION_LOG D025):

- Model: `Qwen/Qwen2.5-Coder-14B-Instruct`, quantization `bnb-nf4`, temperature 0
- Timeout: 600 s uniform per run (do NOT raise), max 3 attempts (initial + 2 repairs),
  max completion 4096 tokens/call, workflow token cap 0 (unlimited)
- 12 scenarios × 2 strategies (`iterative_repository_agent`, `selective`)
  × 2 repetitions = **48 cells**
- Repositories: Todo / django CMS / Saleor at pinned SHAs

## 2. Research goal + frozen protocol

Working paper: *"Don't Regenerate What Hasn't Changed: Selective Regeneration
for Token-Efficient LLM-Driven Software Evolution."* The benchmark measures
whether dependency-aware selective regeneration matches full-scope and agentic
regeneration on correctness while reducing regenerated artifacts, tokens,
calls, and time.

Research Protocol **v1.0 is FROZEN** (`docs/FINAL_RESEARCH_PROTOCOL.md`,
`PROTOCOL_VERSION.md`). No post-hoc scenario/metric changes. Ground Truth is
evaluation-only and post-hoc. Failed runs stay visible. Smoke evidence
(complete/accepted: `exp-20260808-222843` T600 Full-9, 2 successes /
7 scientific failures / 0 engineering blockers) is non-publication evidence.
Pilot findings are descriptive; confirmatory claims require the main study.

## 3. Exact frozen Pilot scenario IDs (12)

| Repository | Scenario IDs |
|---|---|
| todo | `todo-loc-001`, `todo-loc-002`, `todo-mod-004`, `todo-cross-007` |
| djangocms | **`djangocms-mod-005`**, `djangocms-loc-002`, `djangocms-mod-004`, `djangocms-cross-007` |
| saleor | `saleor-loc-001`, `saleor-loc-002`, `saleor-mod-004`, `saleor-cross-007` |

Note: `djangocms-mod-005` replaced `djangocms-loc-001` before any Pilot result
(DA-07 amendment: `djangocms-loc-001` was objectively infeasible at pinned
revision `0f633fc` because `PageContent` already has `meta_description`). The
scenario list lives in `configs/pilot.yaml` and must match
`PROFILES["pilot"]` exactly (parity contract test).

## 4. Release history (chronological, newest last)

| Release | Status | Reason |
|---|---|---|
| v0.9.1–v0.9.10 | historical execution-ready points | superseded as newer Kaggle blockers were closed (service bootstrap, transport encoding, root-safe PostgreSQL, Redis fallback, no-pip envs, release trust gate) |
| v0.9.11 | REJECTED FOR LAUNCH | internally-valid artifact, but the immutable tag did not contain the deployed re-frozen notebook (tag peel `8801304` lacked notebook landed only in post-tag `b87aa49`) |
| v0.9.12 | historical (GOOD) | fail-closed `source_commit` git-tree provenance gate introduced (`validate_source_commit_provenance`) |
| v0.9.13 | stale at upload time | superseded |
| v0.9.14 | REJECTED | artifact notebook provenance did not match immutable tag notebook |
| v0.9.15 | REJECTED FOR ACCEPTED PILOT LAUNCH | release finalization/artifact not completed (dist still v0.9.14; code-manifest SHA stale; single-parent commit) |
| v0.9.16 | RELEASE-ONLY CLOSURE | no production behavior changes; notebook anchors corrected |
| v0.9.17 | REJECTED FOR ACCEPTED PILOT LAUNCH | tag/source-commit provenance mismatch (tag peel `28a18e6…` != artifact source_commit `adf72d4…`); the PGDG bootstrap fix itself was GOOD |
| v0.9.18 | historical (release-only) | provenance/docs correction only; no scientific or production code changes |
| v0.9.19 | REJECTED FOR PILOT LAUNCH | PostgreSQL admin/application bootstrap + partial recovery closure; artifact internally GREEN (trust/provenance 0 mismatches) but the real Kaggle session failed at the Saleor fast capability gate (Pytest exit 5, no tests collected) |
| v0.9.20 | superseded for Real Pilot launch | Saleor preflight root-cause closure (exact fast-gate argv, false-green removal); internally trustworthy and target-shaped no-model preflight GREEN (run 32676588800), but an independent audit found the per-cell validation runtime parity blockers B1/B2/B3 — closed in v0.9.21 |
| v0.9.21 | accepted release — superseded as launch candidate | per-cell validation runtime closure: explicit `--validation-python` interpreter routing (B1), frozen env into `FunctionalValidator` (B2), explicit `--validation-timeout 1800` on launch+resume (B3); target-shaped Gates 1–3 + full no-model preflight GREEN (runs `32692489617` / `32694137255`); trust/provenance 0 mismatches; dry-run 48/48. Real Pilot rejected BEFORE LAUNCH at the real 12k attention-prefill OOM; repository/per-cell fixes remain VALID and are carried forward |
| **v0.9.22 candidate** | **CURRENT — TARGET MEMORY PROOF PENDING, NO TAG YET** | long-context attention memory closure on branch `fix/pilot-v0922-long-context-attention-memory-closure`: Task A `attn_implementation="sdpa"`, Task B fail-closed `sdpa_kernel([FLASH_ATTENTION, EFFICIENT_ATTENTION])`, Task C canonical attention evidence + fail-closed `attention_policy` check + launch authorization enforcement, Task D corrected OOM diagnosis, Tasks E/F regression guards; RED/GREEN proven (12 backend + 18 preflight contract tests failed against v0.9.21); full suite 2407/33/0; dry-run pilot 48/48; stable tag only after the real Kaggle 2x T4 12k probe PASSES |

## 5. Recurring errors → permanent guards

Every guard below exists because a real failure happened. Never remove or
weaken one without an explicit new audit.

1. **Tag/source-commit mismatch** (v0.9.11, v0.9.17 rejected) → create the
   annotated tag ON the accepted artifact source commit; run
   `validate_source_commit_provenance` BEFORE tagging; post-tag docs/evidence
   commits are never tag targets.
2. **Stale "current" docs contradicting reality** → this file is authoritative;
   reconcile all state docs whenever truth moves (see Source-of-truth below).
3. **Workspace contamination across scenarios** (Full-9 `exp-20260807-205422`
   rejected) → exact reset from the immutable snapshot before EVERY matrix run
   (`_reset_workspace_source_from_snapshot`, fixed by `7f2a450`).
4. **Kaggle `venv`+`ensurepip` failure** → repository envs are provisioned
   WITHOUT pip (`--without-pip` + host pip bootstrap; v0.9.9 helper
   `scripts/pilot_kaggle_repo_envs.py`).
5. **Combined apt install abort** (`valkey-server` missing) → probe candidates
   individually via `apt-cache policy`; install EXACTLY ONE package per
   `apt-get install`; fail closed if none works (v0.9.8).
6. **PostgreSQL refuses root** → run the server lifecycle under the unprivileged
   `postgres` OS account when the notebook uid is 0; fail closed if absent;
   never fall back to root (v0.9.7). v0.9.19 additionally removed the implicit
   Saleor DB default from `_psql`, proofs use `db="postgres"`,
   `SHOW data_directory` protects partial recovery, and the Saleor DB is
   created BEFORE any application DB connection.
7. **Dependency drift OOM** (transformers 5.0.0 materialized BF16 before NF4) →
   pin `transformers==4.57.6`; fail-closed version check before load;
   `low_cpu_mem_usage=True`.
8. **GPU0-only VRAM check** → read VRAM on EVERY visible GPU; minimum-free gate
   ≥ 2.0 GiB per GPU (`GpuVramSnapshot`).
9. **CRLF/LF byte drift on Windows checkouts** → `.gitattributes` LF pins +
   LF normalization inside bundle manifests and the provenance gate. Keep it.
10. **Kaggle reserved/unsafe archive names** → `kaggle_transport` reversible
    ZIP encoding + mandatory pre-upload validator (`v0.9.4`/`v0.9.5`).
11. **Saleor `[tool.uv] package=false` import-probe failure** → health probes
    MUST run with `cwd = pristine staged repository root` (v0.9.11 fix; GOOD).

## 6. Git / release invariants

- Immutable tags are NEVER moved, deleted, or recreated.
- Artifact source commit MUST equal the immutable release tag peel.
- Non-fast-forward merges into `main` (no direct pushes of feature work);
  force-push to `main` is prohibited.
- No commit/push/merge/tag/reset/stash unless explicitly requested by the task.
- Stable tags only after successful independent audits.
- Ground Truth stays evaluation-only; no success claims without real execution.
- `dist/pilot-kaggle-upload.zip` (+ `.sha256`) is THE upload artifact — rebuilt
  only by the builder/finalizer from tagged source, never hand-edited.

## 7. OpenCode working rules (summary)

- Validation order: `git diff --check` → Ruff (changed files) → mypy (changed
  production files) → compile check (changed files) → targeted pytest → full
  pytest only at final gates/shared interfaces → bundle rebuilds only when
  production code changed.
- Resources: no pytest-xdist by default; no watch mode/GPU/model downloads/
  clean rebuild; trim logs to first root cause (~120 lines).
- Context discipline: search before reading; do not read whole repo, generated
  code, datasets, or unrelated docs.
- Stop/Blocker Reporting Contract and Project Export Rule in root `AGENTS.md`
  apply to every mandatory stop.

## 8. Exact next action

1. ~~Phase 2 release mechanics (local)~~ **DONE:** non-ff merge → `main` @
   `4827045fce96eb4caa3645e3cf3c8434dca2a1a8` (pushed); notebook/deployment anchors frozen for
   planned `v0.9.22-pilot-exec-ready` via the idempotent two-pass finalizer with
   `--verify-source-provenance` (0 mismatches; freeze evidence `reports/pilot_notebook_trust_freeze.json`);
   exact candidate artifact built from the merge commit: `dist/pilot-kaggle-upload.zip`
   SHA-256 `9182ea2bb091f785ff325a1355caa5bb0f57283764215059092970bbd8014974` (+ sidecar verified);
   exact-artifact dry-run 48/48 succeeded / 48 unique IDs / 0 model calls / 0 tokens.
   **The stable tag still DOES NOT exist — do not create it before step 3 PASSES.**
   **SUPERSEDED by the candidate consistency closure (same day):** branch
   `fix/pilot-v0922-candidate-consistency-closure` non-ff merged → `main` @
   `ba08392552545baa15c10ae5db2e95ce7496a720` (pushed; NO scientific/runtime code delta — four
   stale release-test constants aligned, order-independent missing-SDPA-API test isolation,
   generated dry-run dirs removed, full suite 2407/33/0 with the expanded-artifact simulation
   re-enabled); anchors re-frozen at the new merge via the same finalizer (0 mismatches); exact
   candidate artifact REBUILT: `dist/pilot-kaggle-upload.zip`
   SHA-256 `3fd986262936972a6f12adbae21e844adef488dfd76ef0e4b2e6e434b2aa65b3` (+ sidecar verified);
   exact-artifact dry-run 48/48 succeeded / 48 unique IDs / repos 16/16/16 / strategies 24/24 /
   reps 24/24 / 0 model calls / 0 tokens / new source commit in every record.
2. Upload the EXACT v0.9.22 candidate artifact (`3fd98626…`) as ONE fresh Kaggle Dataset; attach
   the frozen Pilot notebook (`notebooks/pilot_exec_01.ipynb`) and Qwen 14B input; Internet ON;
   `HF_TOKEN` secret set; confirm mounted model path + HF results repo ID.
3. Run the **fresh Kaggle v0.9.22 candidate model preflight ONLY** (SHA-256 verify,
   identity/manifest verify, repository preflight, Qwen 14B BNB-NF4 load PASS, short
   generation probe PASS, **12k long-context probe PASS with attention policy evidence**
   `requested=sdpa effective=sdpa kernel_policy=flash_or_efficient_no_math`). No 48-cell
   launch while untagged.
4. If the 12k probe PASSES → annotate `v0.9.22-pilot-exec-ready` at the tested merge
   commit, push the tag, update docs, then launch the accepted 48-cell Pilot in a fresh
   session. If it FAILS → return to the SAME v0.9.22 task (never spawn v0.9.23).

## 9. Source-of-truth hierarchy

When documents disagree, trust in this order:

1. **This file** (`docs/AI_ACCOUNT_TRANSFER_HANDOFF.md`) — current snapshot.
2. `SYSTEM_STATE.md` → `## Current Truth` (top block only).
3. `AGENTS.md` → `## Release facts`.
4. Machine evidence: `reports/pilot_notebook_trust_freeze.json`,
   `dist/pilot-kaggle-upload/pilot_deployment_identity.json`,
   `configs/pilot.yaml`, `docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md`.
5. Reports (`reports/*.md`) — detailed but partially HISTORICAL.
6. Everything else (README history blockquotes, TODO historical ledger,
   PROJECT_HANDOFF trail, DECISION_LOG entries) — HISTORICAL context.

Anything labeled HISTORICAL / SUPERSEDED anywhere else in the repository must
never be used to override items 1–4.
