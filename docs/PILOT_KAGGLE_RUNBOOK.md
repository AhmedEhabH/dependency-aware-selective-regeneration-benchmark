# PILOT KAGGLE RUNBOOK — PILOT-EXEC-01

**Status:** READY FOR USE — CURRENT RELEASE `v0.9.21-pilot-exec-ready`
(per-cell validation runtime closure merged + tagged; bundle frozen from the
exact release source). Pilot NOT started.

> **HISTORICAL NOTE:** earlier versions of this runbook targeted
> `v0.9.9-pilot-exec-ready` (and were never updated through v0.9.19/v0.9.20).
> That content is SUPERSEDED — do not follow it. This page is the only current
> runbook. Authoritative snapshot: `docs/AI_ACCOUNT_TRANSFER_HANDOFF.md`.

**Release identity (exact, verify before launch):**

| Item | Value |
|---|---|
| Source tag | `v0.9.21-pilot-exec-ready` |
| Source commit (= tag peel) | `e308047c9c05f38316d80ce565bac1b51d105bfa` |
| Artifact SHA-256 | `62e377467e225d336cbcaa70a2c610b5080e329e1a4e6578fbcbdc1af7dbee40` |
| Sidecar | `dist/pilot-kaggle-upload.zip.sha256` (must equal the archive hash) |
| Trust / provenance | 0 mismatches |
| Exact artifact dry-run | 48/48 succeeded, 48 unique IDs, 0 model calls |

**Execution contract:** `docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md` (frozen
before any real Pilot model result).
**Bundle:** `dist/pilot-kaggle-upload/` + `dist/pilot-kaggle-upload.zip` +
`.sha256`; built by the builder/finalizer from the TAGGED SOURCE
`v0.9.21-pilot-exec-ready` (real repo cache: djangocms/saleor at pinned SHAs,
todo embedded). NEVER hand-re-zip the folder — the zip + sidecar are ONE
frozen unit.

## Canonical Gate C deployment shape

- ONE Kaggle Dataset containing exactly `pilot-kaggle-upload.zip` +
  `pilot-kaggle-upload.zip.sha256`.
- Extract root `/kaggle/working/pilot_bundle`; `/kaggle/input` is never mutated.
- Notebook-frozen anchors (`FROZEN_SOURCE_TAG`, `FROZEN_DEPLOYMENT`, four
  stable `FROZEN_MANIFEST_HASHES`) are verified against the extracted tree at
  runtime; the ZIP member names are Kaggle-safe via `kaggle_transport`
  encoding, restored by the `transport-restore-cell` before any verification.

## Freeze procedure (how the notebook's trust anchors are finalized)

The two-pass finalizer (`scripts/finalize_pilot_notebook_trust.py`) runs a
discovery build (trust gate off), writes the anchors
(`source_commit` — which MUST equal the final tag peel — the archive SHA-256,
and the deployed-notebook SHA), then a validation-enabled rebuild whose gates
include `validate_bundled_notebook_trust` and
`validate_source_commit_provenance`. For v0.9.21 this ran at merge
`e308047c9c05f38316d80ce565bac1b51d105bfa` with 0 mismatches; freeze evidence:
`reports/pilot_notebook_trust_freeze.json`.

## 1. Before launching (all must be done first)

1. Confirm `main` is at/after the release merge `e308047…` and the local tag
   dereferences to it; verify `dist/pilot-kaggle-upload.zip` SHA-256 equals the
   sidecar AND the table above.
2. Upload the zip + sidecar as ONE fresh Kaggle Dataset; attach the frozen
   Pilot notebook (`notebooks/pilot_exec_01.ipynb`) and the Qwen 14B model
   input; Internet ON; `HF_TOKEN` secret set.
3. Confirm the mounted model path and the exact HF results repo ID.

## 2. Notebook cells (first launch)

0. The notebook runs its `service-bootstrap-cell` after dataset/repo snapshot
   verification and BEFORE the repo-specific preflight / any repository
   validation / any model load. It provisions PostgreSQL `127.0.0.1:5433`
   (role/db `saleor/saleor@saleor`) and Valkey/Redis `127.0.0.1:6379`
   (persistence disabled) idempotently, installing OS packages via apt-get
   when the services are absent. **Redis package fallback:** the two
   Redis-compatible candidates `valkey-server` / `redis-server` are
   ALTERNATIVES, so the cell NEVER installs both in one apt transaction (the
   real Kaggle runtime exposes `redis-server` but NOT `valkey-server`, and a
   combined install aborts the whole transaction). It resolves an already
   installed binary first, refreshes apt metadata at most once, probes each
   candidate via `apt-cache policy <name>`, installs EXACTLY ONE package per
   `apt-get install`, and fails closed with distro/runtime diagnostics when
   neither candidate can be installed — no pip client package, no in-process
   fake server. **Root handling:** the Kaggle notebook process runs as root
   while PostgreSQL `initdb`/`pg_ctl` refuse root, so when the notebook
   effective uid is 0 the PostgreSQL server lifecycle (initdb, pg_ctl and the
   postgres server it launches) runs under the package-native unprivileged
   `postgres` OS account; the cell FAILS CLOSED before initdb if that account
   is missing and never falls back to root. Non-root notebook processes keep
   the direct path. This requires **Internet ENABLED** (the cell fails loudly,
   never silently, if an OS install is needed while offline). Model loading
   itself remains offline. Prints
   `SALEOR VALIDATION SERVICE BOOTSTRAP: PASSED` on success.
1. Resolve the attached dataset mount. The setup cell discovers EXACTLY ONE
   input shape and fails closed on ambiguity:
   - **Mode A:** `pilot-kaggle-upload.zip` — the ZIP SHA-256 must equal its
     sidecar, then the tree is verified against the frozen anchors.
   - **Mode B:** `pilot-kaggle-upload/` auto-expanded directory — the sidecar
     is required as provenance metadata only; the tree is trusted ONLY against
     the frozen `FROZEN_SOURCE_TAG` / `FROZEN_DEPLOYMENT` / four stable
     `FROZEN_MANIFEST_HASHES` anchors plus self-consistent notebook-manifest
     verification, then copied to `/kaggle/working/pilot_bundle`.
     `/kaggle/input` is never mutated.
2. Provision `/kaggle/working/pilot_bundle` (extract for Mode A, copy for
   Mode B). The extract root must be empty or absent; a non-empty root fails
   closed. Both modes verify the tree against the frozen anchors before
   proceeding. For v0.9.21 the identity must report source tag
   `v0.9.21-pilot-exec-ready`.
3. Run the notebook's `transport-restore-cell`: verifies
   `kaggle_transport_path_map.json` SHA-256 against the identity and restores
   every transport-encoded canonical repository filename from
   `kaggle_transport/files/` back to its EXACT original path (rejecting
   traversal/drive/`..` destinations, collisions, missing blobs, and leftover
   blobs), then removes `kaggle_transport/`. This happens BEFORE any manifest
   or repository verification.
4. Verify `pilot_deployment_identity.json`: task `PILOT-EXEC-01`, source tag
   `v0.9.21-pilot-exec-ready`, source commit
   `e308047c9c05f38316d80ce565bac1b51d105bfa`; the identity-verify cell anchors
   `source_tag` and the full `FROZEN_DEPLOYMENT` to the frozen constants in
   BOTH modes.
5. Verify the code/data manifests against the freeze report.
6. Bundled paths:
   ```python
   PILOT_CODE = "/kaggle/working/pilot_bundle/code"
   PILOT_DATA = "/kaggle/working/pilot_bundle/data"
   ```
7. Install the pinned runtime lock, then GPU/model-mount checks.
8. Bundled dry-run (mock, 48 expected cells) before any real call:
   ```bash
   python /kaggle/working/pilot_bundle/code/seven_arm_benchmark.py \
       --dry-run \
       --profile pilot \
       --data-dir /kaggle/working/pilot_bundle/data \
       --qwen-quantization bnb-nf4
   ```
9. Model-load preflight (loads model with `--qwen-quantization bnb-nf4`, no
   scientific cells).

### Repository environment provisioning + preflight (no model call)

The `pilot-repo-preflight-cell` first asserts the two service ports
(PostgreSQL `127.0.0.1:5433`, Valkey/Redis `127.0.0.1:6379`), then loads the
bundled `scripts/pilot_kaggle_repo_envs.py` helper and calls
`provision_repository_envs(...)` to build ISOLATED environments under
`/kaggle/working/pilot_envs`:

- `tools/` — no-pip venv; `uv` installed by HOST pip via `--python <target>`.
  NEVER runs the failing `ensurepip` path and NEVER touches the
  benchmark/model interpreter.
- `djangocms/` — no-pip venv; pinned `test_requirements/django-5.0.txt`
  installed with `uv pip install --python <venv>` from the frozen snapshot
  root.
- `saleor/` — exact copy of the pinned snapshot, then `uv venv .venv --python
  <existing 3.12>` with `UV_PYTHON_DOWNLOADS=never` and `uv sync --locked`.
- Upstream OS prerequisites `gettext`, `gcc`, `libpq-dev` in ONE apt
  transaction (fail closed listing ALL missing).
- Completion markers (`.pilot_env_ready.json`, schema
  `pilot_repo_environment.v1`) + health probes decide reuse; only the specific
  invalid private env dir is rebuilt.
- Provisioning log at `preflight/environment_provisioning.log`
  (`PROVISIONING: PASSED`); heartbeats every 30 s; no secret values recorded.

The provisioned interpreters are exposed by the cell as:

```python
TODO_PYTHON   # the notebook/benchmark interpreter (sys.executable)
DJANGO_PYTHON # /kaggle/working/pilot_envs/djangocms/bin/python
SALEOR_PYTHON # /kaggle/working/pilot_envs/saleor/.venv/bin/python
```

They drive the shared `scripts/pilot_repo_snapshot.py preflight` runner
(frozen per-repo commands from
`benchmark_data/manifests/pilot_validation_commands.yaml`; fails closed unless
`overall == PASS`) — and the SAME three values MUST be passed to the real
launch/resume commands as `--validation-python` mappings (per-cell validation
runtime parity, v0.9.21).

## 3. Real Pilot launch (frozen flags)

These mirror the canonical `pilot-launch-cell` exactly. `<TODO_PYTHON>`,
`<DJANGO_PYTHON>` and `<SALEOR_PYTHON>` are the preflight-provisioned
interpreter paths above (copy them verbatim from the cell output; do NOT
substitute other Pythons):

```bash
python /kaggle/working/pilot_bundle/code/seven_arm_benchmark.py \
    --backend kaggle-qwen \
    --profile pilot \
    --qwen-quantization bnb-nf4 \
    --max-attempts 3 \
    --protocol-version 1.0 \
    --max-completion-tokens-per-call 4096 \
    --max-total-workflow-tokens 0 \
    --timeout 600 \
    --validation-python todo=<TODO_PYTHON> \
    --validation-python djangocms=<DJANGO_PYTHON> \
    --validation-python saleor=<SALEOR_PYTHON> \
    --validation-timeout 1800 \
    --source-commit e308047c9c05f38316d80ce565bac1b51d105bfa \
    --source-tag v0.9.21-pilot-exec-ready \
    --data-dir /kaggle/working/pilot_bundle/data \
    --model-path /kaggle/input/<pilot-model-slug> \
    --output-dir /kaggle/working/runs/<experiment-dir> \
    --hf-sync \
    --hf-repo-id <exact HF results repo id> \
    --new-experiment \
    --require-launch-authorization \
    --repo-preflight-json <PREFLIGHT_JSON> \
    --model-preflight-json <MODEL_PREFLIGHT_JSON> \
    --launch-auth-dryrun-dir <DRYRUN_DIR> \
    --expected-model-identity <EXPECTED_MODEL_IDENTITY>
```

Notes:

- One continuous 48-cell session. No `--max-runs` subsetting for the Pilot.
- `--timeout 600` is the cooperative workflow/model-call deadline (frozen);
  `--validation-timeout 1800` is the separate bounded per-cell validation
  subprocess budget. Validation may finish after the 600s deadline elapses;
  no new model/repair call starts once the cooperative deadline has elapsed.
  Both budgets are existing/frozen semantics.
- Every real/resume invocation MUST pass `--qwen-quantization bnb-nf4`
  explicitly (generic CLI default is `bnb-int8`).

## 4. Resume (external interruption only)

Same flags INCLUDING all three `--validation-python` mappings and
`--validation-timeout 1800`, WITHOUT `--new-experiment`, adding
`--resume-from-hf`; identical experiment id / output-dir / model /
source commit / quantization. Never `--new-experiment` on resume.

```bash
python /kaggle/working/pilot_bundle/code/seven_arm_benchmark.py \
    --backend kaggle-qwen \
    --profile pilot \
    --qwen-quantization bnb-nf4 \
    --max-attempts 3 \
    --protocol-version 1.0 \
    --max-completion-tokens-per-call 4096 \
    --max-total-workflow-tokens 0 \
    --timeout 600 \
    --validation-python todo=<TODO_PYTHON> \
    --validation-python djangocms=<DJANGO_PYTHON> \
    --validation-python saleor=<SALEOR_PYTHON> \
    --validation-timeout 1800 \
    --source-commit e308047c9c05f38316d80ce565bac1b51d105bfa \
    --source-tag v0.9.21-pilot-exec-ready \
    --data-dir /kaggle/working/pilot_bundle/data \
    --model-path /kaggle/input/<pilot-model-slug> \
    --output-dir /kaggle/working/runs/<same-experiment-dir> \
    --hf-sync \
    --hf-repo-id <exact HF results repo id> \
    --resume-from-hf
```

## 5. Completion

- All 48 scientific cells must be terminal before Pilot success is claimed.
- Download the full `runs/` artifact (run_records.jsonl, checkpoint,
  benchmark_summary.json, COMPLETED marker, benchmark-results.zip,
  remote_sync.json) and move under `reports/results/` in the repo.
- Then freeze the Main-study per-run budgets from measured Pilot
  distributions (never before the Pilot results audit).
