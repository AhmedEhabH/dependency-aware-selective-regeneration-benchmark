# C6_P2_PYTHON_COMPAT.md — Python 3.9.25 vs declared 3.9.14 (evidence)

Mission TRACK02-C6-P2-ENV-UNBLOCK · 2026-10-27Z · NON-CANDIDATE, offline.

## Question
P2's frozen manifest declares `runtime.txt = python-3.9.14` (verified at commit
P=`5b0e5206…8a85` and identical at T=`06d25ce2…5e83` — requirement files and
runtime.txt are byte-identical between P and T). The only locally available
python-3.9 base image (`envcanon/saleor-env-r4b-py39-native`,
`sha256:3220486db0…b89`, verified on-disk) contains **CPython 3.9.25**
(`PYTHON_VERSION` env + `python --version` probe). The protocol forbids
claiming exact equivalence without evidence.

## What is NOT claimed
- 3.9.25 and 3.9.14 are NOT the same interpreter (patch levels differ).
- No claim that ANY 3.9.14 behavior is absent from 3.9.25 or vice versa at a
  patch level; no claim on CPython-internal differences.

## Evidence for functional equivalence on THIS contract
1. **Same python minor family (3.9.x = bugfix-only line).** CPython policy
   states that within a minor version (3.9.z), release series ship bugfixes,
   security fixes and documentation; the public C API and the stable ABI do
   not change within the minor. All artifact wheels in the era wheelhouse are
   tagged `cp39` (CPython 3.9 series, patch-agnostic) or `py3-none-any`
   (pure Python) — none are patch-level artifacts.
2. **No bytecode dependence.** The runner sets `PYTHONDONTWRITEBYTECODE=1`;
   no `.pyc` artifacts are read or shipped, so patch-level bytecode-format
   differences (none exist within 3.9 anyway) are irrelevant.
3. **Exact era wheels installed on 3.9.25 (offline, hash-pinned):**
   - django==4.0.8, graphene==2.1.9, graphene-django==2.15.0,
     graphql-relay==2.0.1, pytest==7.1.3, pytest-django==4.5.2,
     psycopg2==2.9.4 (local prebuilt cp39 wheel, EXACT pin), promise==2.3
     (sdist built offline with setuptools), before-after==1.0.1 (local wheel),
     freezegun==1.2.2, measurement==3.2.2 (wheel; pin 3.2.0 sdist) —
     see `work/p2_env_unblock/build_img/Dockerfile(.r3)` +
     `offwh/SHA256SUMS.txt`.
4. **Empirical closure gate (r3 image, P tree mounted read-only, --network
   none):** `django.setup()` with `saleor.settings` → **OK**; contract test
   MODULE import (`saleor.graphql.product.tests.test_product`) → **OK**;
   `saleor.graphql.product.filters` → **OK**; plugin app.ready() for all
   `saleor.plugins.*` → **OK** (this is what demanded petl/jaeger/tracing
   closure).
5. **Full-stack DB integration on 3.9.25:** Django ORM `SELECT`, searchvector
   cast, dj_database_url unix-socket config — **PASS** (see
   `C6_P2_ENV_QUALIFICATION.md` probe receipts).

## Verdict
- **Compatibility: EMPIRICALLY VERIFIED for the P2 contract closure** on
  CPython 3.9.25 with the exact era pins.
- **Exact patch identity (3.9.14 == 3.9.25): NOT claimed.**
- `plan.interpreter_version` is frozen to the CONCRETE probed value
  **3.9.25** so ENVIRONMENT_ID always reflects the executed interpreter
  (never a silent alias of the declared 3.9.14).
- Residual risk is patch-level (bugfix differences), documented in the plan
  notes; no scientific claim depends on the patch delta.