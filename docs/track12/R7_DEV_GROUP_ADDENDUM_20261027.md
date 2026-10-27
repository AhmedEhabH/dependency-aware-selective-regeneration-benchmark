# Track 1.2 — R7 dev-group provenance addendum (2026-10-27)

**Disposition: LOG_MARKER_CONTRADICTION_EXPLAINED; FULL_ENVIRONMENT_PARITY_NOT_YET_CERTIFIED.**

This note supplements `docs/track12/R7_SCOPED_F2P_GATE_20261027.md`. It does **not** modify the frozen R7 experiment, retrospectively change classifications, assert broad M02-Q qualification, or authorize M02-E.

## Exact read-only evidence reviewed

Source: `M19B_R7_F2P_PILOT_20261027T082605801327Z_f32b72b6.zip`, with report/manifest/JUnit integrity established in the preceding R7 scoped gate.

| State | `.install.sh` SHA-256 | `install.log` SHA-256 |
|---|---|---|
| NEG | `814b8f9aa4262a691838655c176df92fc6564ec95f0362dee7b679dc36399e29` | `448042491dde17a8d0628368c40752d92616159ba95ce552a361de585ea98ac1` |
| FULL_REFERENCE | `21b38603b65fa5d9a5b457eb4a6a49efaa2f36bb271a8dc968ceccb943baa48a` | `3b38be525792f9121496a430aaf6766e3b44974540f195ed2786b0fa77e9f0b4` |
| RM_CSS | `1b12b7a83c3284892051e90ce03861e32f6a64af410c2562fb9bd6c533e9c525` | `802d995a0a66f3a8b22935d2b64e11784f474141ee806098f0658f3815e99c52` |

In all three **recorded** state-run scripts, the following command appears:

```sh
uv export --frozen --group dev | uv pip install -r - --python /opt/venv/bin/python
```

Immediately afterward, each script separately prints these literal markers:

```sh
echo UV_EXPORT_FROZEN_GROUP_DEV
echo NO_LOCKED_DEV_GROUP
```

Consequently, `NO_LOCKED_DEV_GROUP` is an **unconditional, misleading literal log line**, **not** an observed test that the dev group was absent. All three install logs record 237 installed packages, including `pytest-django-queries==1.2.0` and `pytest-mock==3.15.1`. All three container output logs include `OFFLINE_DEP_INSTALL_PASS` and the 27 scoped JUnit outcomes were verified separately.

## Remaining qualification limitation

The recorded scripts use `set -e` but **not `set -o pipefail`** around the export-to-install pipeline. As a result, a successful piped installer exit does not by itself demonstrate the upstream `uv export` exit status. Frozen-lock consistency, precise cache provenance, and cross-arm environment parity should be independently attested prospectively. **Do not rewrite the original logs, the frozen runner, or this result to hide the limitation.** A subsequent runner amendment, if needed, is prospective and requires its own qualification.

## Scientific status retained

- R7 scoped F2P: 27/27 expected state-node classifications, within **one Saleor task** and three distinct nodes repeated three times per state. PASS as a **scoped** gate.
- Fresh P2P: **NOT_RUN**; earlier historical R8 P2P observations are not interchangeable with the fresh R7 state and cannot be relabeled as fresh M02-Q qualification.
- M02-E comparators: **0/13** prospective arm evaluations, **NOT_RUN**. No superiority/non-inferiority or generated-code E2E claim follows.
- Frozen Option B: `REUSE_NOT_PERMITTED`; no cross-arm result reuse even where trees coincide.
- Canonical project branch: `docs/track12-m01d-m02q-evidence-20261027`; Draft PR #1; do not merge until reviewed.

## Next execution gate

1. Read-only environment attestation for the exact R7 state, including source SHA/OID, dev-group dependency inventory, runner image/config fingerprints, PG isolation and actual host resource ownership. Reuse frozen evidence instead of rerunning the 27 passing F2P observations.
2. Decide/pin uniform P2P policy (103 nodes × 3 per eligible arm where required) **before** looking at comparator outcomes. Treat missing P2P as `NOT_RUN` and restrict claims accordingly.
3. Freeze an isolated first batch with the original outcome-blind order `SIP → DENSE_K3 → DENSE_K10 → BM25_K10`, equal budgets and unmodified tree/scope/test identities, with independent physical runs per Option B. The named arm `AGENTLESS_STYLE_ADAPTATION` is not a reproduction of original Agentless.
4. Admit M02-E only after G-M02-A route proof, environment/ownership qualification, frozen comparator CLI readiness, and **separate bounded researcher execution authorization**. Default offline reference-patch evaluation has benchmark generation API cost $0; any actual Qwen generation requires distinct authorization and an explicit USD/token cap.
5. Preserve full run receipts, wall/resource/net measurements, JUnit SHA-256, raw STOPs and claim limits. Publish only reviewed documentation into the canonical project branch; no raw logs/private data into the public repository.

**Gate statement:** `R7_DEV_GROUP_LOG_MARKER_EXPLAINED`; next: `G_M02_A5_READ_ONLY_ENV_AND_P2P_AUDIT`. M02-E remains STOP/NOT_RUN.
