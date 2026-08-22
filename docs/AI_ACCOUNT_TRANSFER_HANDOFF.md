# AI Account-Transfer Handoff — CURRENT v0.9.19 State (2026-08-22)

**Read this file FIRST.** It is the single authoritative snapshot of the
current project state for any AI agent or human resuming on a new account.
Older files contain valuable history, but their "Current" sections may be
superseded — this file wins every contradiction.

---

## 1. Current truth (memorize these facts)

| Fact | Value |
|---|---|
| Accepted release | **`v0.9.19-pilot-exec-ready`** |
| Release tag peel == artifact source commit | **`2305991442a4f965d44bb066bb00c0a459fc395a`** |
| v0.9.19 content | PostgreSQL admin/application bootstrap + partial recovery closure (real Kaggle defect fix) |
| Artifact trust/provenance | **GREEN** — `pilot_deployment_identity.json.source_commit == 2305991…` == immutable tag peel; source-provenance gate PASS; FINAL ARTIFACT TRUST GATE Notebook == Identity == Actual PASS |
| Exact deployment artifact | `dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256` (SHA-256 `f7a168584de3db723acbf9d43f81edd4d0720c2e3850b8017f91eee363928862`) — NEVER manually re-zip |
| Freeze evidence | `reports/pilot_notebook_trust_freeze.json` (status FROZEN) |
| `main` branch state | Post-tag docs/evidence child of the release merge `2305991` (docs commits after the tag are normal and are NOT part of the artifact) |
| OpenCode full-suite evidence | **2330 passed / 34 skipped / 0 failed** |
| Real Pilot status | **NOT STARTED** (accepted for launch, zero real model cells executed) |
| Exact next action | **Fresh Kaggle v0.9.19 target preflight** using the exact v0.9.19 artifact |
| After preflight | If ALL target gates pass → launch the accepted 48-cell Pilot in the SAME session |
| Version discipline | Do NOT open v0.9.20 without real target evidence from the accepted Pilot |

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
| **v0.9.19** | **ACCEPTED — CURRENT** | PostgreSQL admin/application bootstrap + partial recovery closure (real Kaggle defect fix); trust/provenance GREEN |

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

1. Upload the EXACT existing artifact (`dist/pilot-kaggle-upload.zip` +
   `.sha256`, SHA-256 `f7a16858…`) as ONE fresh Kaggle Dataset; attach the
   frozen Pilot notebook (`notebooks/pilot_exec_01.ipynb`) and Qwen 14B input;
   Internet ON; `HF_TOKEN` secret set; confirm mounted model path + HF results
   repo ID.
2. Run the **fresh Kaggle v0.9.19 target preflight** (SHA-256 verify, identity/
   manifest verify, service bootstrap, bundled 48-cell dry-run, model-load
   preflight).
3. If ALL target gates pass → **launch the accepted 48-cell Pilot in the same
   session**. Do not resume/reuse any older experiment namespace.
4. Do NOT open v0.9.20 without real target evidence from the accepted Pilot.

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
