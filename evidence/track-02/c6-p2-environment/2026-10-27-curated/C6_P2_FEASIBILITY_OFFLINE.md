# C6_P2_FEASIBILITY_OFFLINE.md — Offline P2 dependency/image feasibility (2026-10-27)

**Pilot P2:** `T=06d25ce29c984d9af0f8759044cd80aa8a835e83` (2022, Old6000),
`P=5b0e5206c5fd30d81438b6489d0441df51038a85`, `runtime.txt=python-3.9.14`,
contract `saleor/graphql/product/tests/test_product.py` (P-available, no
T-only), `oracle_mode=POSITIVE_REFERENCE`.

**Method:** read-only analysis of the frozen bare store (`D:\wp2_env_store\git_cache\saleor.git`)
and the local offline wheelhouse (`D:\wp2_env_store\wheelhouse\py39` +
`D:\wp2_env_store\built_wheelhouse\{canon,canon_r4b}\py39`). **No packages
downloaded; no candidate tests executed; 0 network bytes.**

## 1. Base image — PRESENT, requires extension

| Ref | Digest | Interpreter (probed) | pytest/django/saleor inside |
|---|---|---|---|
| `envcanon/saleor-env-r4b-py39-native:latest` | `sha256:3220486db0d8f7649b29bfe01875a1ef794c860539e2713587d9d32f5bd91b89` | Python 3.9.25 (probe: `--network none`, disposable container) | **absent** (bare base) |

The pinned base exists locally (676 MB) and its interpreter family (~3.9.25)
matches the frozen `runtime.txt` constraint for P2 — but pytest/django must be
baked in for the C6 command to run. This is an operator provisioning step.

## 2. Dependency coverage of the frozen P2 environment (requirements.txt at P)

- **170 pinned entries** (`requirements.txt` at P; identical at T).
- **150/170 (88%) exact-version wheels present** in `wheelhouse/py39` (2,411
  wheels, 2.9 GB).
- 20 non-exact entries: 19 have **zero references in the test contract's
  import closure** (adyen, authorizenet, draftjs-sanitizer, html-to-draftjs,
  jaeger-client, maxminddb, micawber, opentracing, petl, posuto, promise,
  pybars3, pymeta3, python-magic-bin, pyxb, starkbank-ecdsa, threadloop,
  thrift — payment/tracing/template extras, grep of `test_product.py` = 0
  hits) and one patch-compatible pair (`measurement==3.2.0` → 3.2.2 whl
  present). `promise` (2.3 sdist) is a graphene transitive dep with an
  offline sdist present — buildable with the offline `build_toolhouse` (or a
  compatible wheel if graphene's solver accepts it; operator pin decision).

**Test import closure (direct third-party imports of `test_product.py`):**
`before_after`, `django`, `freezegun`, `graphene`, `graphql_relay`,
`measurement`, `prices`, `pytest`, `pytz` — **all covered offline**:

| Package | Local supply (py39) |
|---|---|
| Django | `Django-3.2.11…3.2.25` wheels (era 2022 range) |
| graphene / graphene-django | `graphene-2.1.8/2.1.9`, `graphene_django-2.13.0/2.15.0/2.16.0` |
| graphql-relay | `graphql_relay-2.0.1` wheel |
| pytest (era) | `pytest-6.2.x`, `pytest-7.1.x–7.4.x` wheels |
| before_after | sdist in wheelhouse + **built wheel** `built_wheelhouse/py39/canon/before-after==1.0.1__py39/before_after-1.0.1-py3-none-any.whl` (+ `canon_r4b/py39`) |
| freezegun | `freezegun-0.3.15…1.5.1` wheels |
| prices / measurement | `prices-1.1.0/1.1.1`, `measurement-3.2.2` wheel (3.2.0 sdist) |
| pytz | wheels present |
| psycopg2 (DB driver) | pinned `psycopg2==2.9.4` sdist + **`psycopg2_binary-2.9.3-cp39-cp39-manylinux…whl`** present (patch-compatible selection) and `built_wheelhouse/canon_r4b/py39/psycopg2__2.9.x` build dirs |

## 3. Runtime/service requirements (OPEN items — operator scope)

1. **PostgreSQL**: `test_product.py` uses `transaction`, `Sum`,
   `FlatConcatSearchVector` (Django ORM/Postgres search) → a reachable
   Postgres service + `DATABASE_URL` are required for the plan's environment.
   Presence of a Postgres server/client inside the base image is **UNKNOWN**
   (not probed; not assumed). Marked **operator provisioning**.
2. **Derived image freeze**: extend the pinned base with the era wheelhouse
   subset above (offline `pip install --no-index --find-links <wheelhouse>`)
   and freeze the new `image_digest` in the plan.
3. **promise 2.3**: build from the offline sdist (setuptools present in
   `build_toolhouse/py39`, 33 wheels) or select a compatible wheel; operator
   pin decision; do NOT fetch from the network.

## 4. Cost estimate per task (P2 re-runs)

- Checkouts needed per task: 3 trees = `src` (P), `eval_f2p` (P code + T
  bytes), `eval_work` (T code + T bytes). Measured P2 T-tree tar ≈ **45 MiB**
  → ~**135 MiB** per task on scratch across the 3 trees (plus oracle bytes and
  junit evidence), well under the 5120 MiB scratch cap.
- Command runs per task: **3** (diagnostic + F2P + P2P), each bounded by
  `timeout_s`/`ram_mb`/`disk_mb` from the plan.
- No network at any point (`--network none`); no package download.

## 5. Feasibility verdict

**FEASIBLE-OFFLINE (BLOCKED-ON-OPERATOR-PROVISIONING):** the runtime closure
of P2's C6 contract is fully satisfiable from local cached images + the era
wheelhouse; nothing requires the network. Execution cannot start until the
operator (a) extends+freezes the P2 image digest with the era wheelhouse
subset, (b) provisions a Postgres service + `DATABASE_URL` for the plan, and
(c) freezes a plan with `oracle_mode=POSITIVE_REFERENCE` per
`C6_FINAL_PROTOCOL_V4_ORACLE.md` §9–10. Until then the runner will refuse any
task with `BLOCKED docker_image_not_pinned` (fail-closed by design).

Workspace note: P1 requires a python-3.6-era saleor image + pytest + era
wheels which are NOT present on this host (see `C6_PILOT_PRECHECK_3.csv`);
P3 shares P2's py39 base path but adds the T-only contract file
`saleor/discount/tests/test_utils/test_update_rule_variant_relation.py`.