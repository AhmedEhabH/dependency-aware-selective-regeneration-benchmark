# C6_P2_RUNNER_DELTA_PROPOSAL.md — the single operator decision
(TRACK02-C6-P2-ENV-UNBLOCK · 2026-10-27Z · mission blocking item, NOT executed)

## Summary
The P2 historical environment is provisioned and qualified (image r3,
`sha256:4b41010c…ee6919`, closure + Postgres integration PASS). One tooling
gap remains before the first real C6 pilot can execute: **c6runner v0.4.0
cannot reach a database** — its task container has a fixed env block and a
fixed mount list, and cannot start/inspect a service container. P2's
contract is DB-backed (Django ORM, `transaction`, `Sum`,
`FlatConcatSearchVector`), and a live PostgreSQL is provably required
(`django.setup()` passes without it but pytest-django table setup and the
contract queries will not). FROZEN STATE says runner v0.4.0 = 90/90 PASS;
changing the runner is therefore **not done here (no self-authorization)**.
Ratification of this delta is the single next operator decision.

## The proven facts (this mission, non-candidate probes)
1. `--network none` containers keep a working loopback (`127.0.0.1`); local
   TCP works, **all external network is enforced-blocked** (verified).
2. Docker Desktop's Windows bind mounts (drvfs) cannot carry unix domain
   sockets; **named docker volumes carry sockets** (verified: server socket
   reachable by a second `--network none` container through a shared volume).
3. `postgres:15-alpine` (immutable local digest
   `sha256:9b4593c6de44…`) runs headless with `--network none`, listens on a
   unix socket at `/var/run/postgresql`, and satisfies the era
   `dj_database_url` config via `DATABASE_URL='postgres://u:p@/db?host=/pg-sock'`
   (engine `django.db.backends.postgresql`, connect verified).
4. No offline Debian/glibc PostgreSQL server binaries exist on this host
   (no apt cache, no store artifacts, musl Alpine image cannot host the
   glibc manylinux python stack) → **the same-container approach is not
   feasible offline**; the sidecar+unix-socket design is the only offline
   path.

## Minimal delta spec (proposed: c6runner v0.4.0 → v0.5.0)
Scope is deliberately narrow; no oracle/eligibility/verdict semantics change.

1. `taskplan.py`
   - `TaskPlan.__init__/canonical/from_dict/to_dict` gain two optional fields:
     - `env: dict[str,str]` (sorted keys in canonical)
     - `postgres: None | {image, image_digest, database, user, password}`
   - Both default to absent; existing v1 plan files (e.g. `plans/P2.json`)
     keep parsing; canonical SHA changes ONLY when one of the fields is
     present (absent fields render identically to today's canonical — verify
     by unit test).
   - New `TASK_PLAN_SCHEMA_V2 = "c6-task-plan-v2"` constant; schema string
     advances only when `postgres`/`env` are used (plans with neither keep
     `c6-task-plan-v1`), so the READ-ONLY plan-sha binding helper stays
     behavior-identical for the frozen v1 path.
2. `isolation.py` — `docker_run()` service orchestration (docker docker
   backend only; fail-closed everywhere):
   a. If `plan.postgres`: resolve the service image digest OFFLINE
      (`docker image inspect`, no pull) and require byte-equality with the
      frozen `postgres.image_digest` → else `Blocked(docker_image_not_pinned)`.
   b. Start: `docker run -d --rm --network none --name c6.<task12>.pg
      --label c6.pg=<task12> -e POSTGRES_USER=<user> -e POSTGRES_PASSWORD=<pwd>
      -e POSTGRES_DB=<db> -v <named-volume c6.<task12>.pg>:/var/run/postgresql
      <service-image>@<digest>` (named volume avoids drvfs socket loss).
   c. Readiness: bounded poll (≤60 s) `docker exec c6.<task12>.pg
      test -S /var/run/postgresql/.s.PGSQL.5432`; timeout → kill/rm + Blocked.
   d. Task container: add `--mount type=volume,src=c6.<task12>.pg,dst=/pg-sock`
      and `--env DATABASE_URL=postgres://<user>:<pwd>@/<db>?host=/pg-sock`.
   e. `env_block` also merges `plan.env` (explicit plan values win; still zero
      network; values sha-signed by the plan SHA).
   f. Teardown (always, incl. Blocked paths): `docker rm -f c6.<task12>.pg`,
      `docker volume rm c6.<task12>.pg`, then the existing label sweep;
      receipt gains `postgres_service:{container_id, socket_ready,
      clean_removed, volume_removed}`.
   g. RSA key: bake a `sitecustomize.py` into the r3 image that injects an
      ephemeral RSA_PRIVATE_KEY default (DEBUG-mode saleor writes
      `.jwt_key.pem` into the read-only /work otherwise — verified FAIL).
      Explicit runner env wins over the baked default.
3. `version` → `RUNNER_VERSION = "0.5.0"`.
4. New tests `tests/test_postgres_service.py` (mocked subprocess, same
   pattern as existing) covering: no-postgres plan → unchanged; digest
   drift; readiness timeout; cleanup-on-Blocked; env merge. Existing 90
   tests untouched (no assertion changes); the suite is re-run once as
   delta-integrity evidence (the only suite run this mission).
5. Reproducibility: delta only adds a service around the existing plan;
   `ENVIRONMENT_ID` continues to bind the task image digest (the DB service
   digest is recorded in the receipt's `environment.extra`).

## What does NOT change (fail-closed by design, per protocol V4 §2/§8)
- 174-candidate census, eligibility rules, frozen hashes, oracle
  validity rules, POSITIVE_REFERENCE semantics, STOP taxonomy, no-PASS
  degeneracies, cleanup contract, offline/0-network, image digest binding,
  interpreter probe, plan-SHA authorization binding.

## Decision requested (single)
**APPROVE / REJECT**: authorize c6runner v0.4.0 → v0.5.0 exactly as scoped
above (new plan fields env+postgres, docker service orchestration, new
tests, one suite re-run). The alternative is a hard `STOP` blocker:
`runner_db_service_capability_absent` — the first real C6 pilot cannot
connect its mandated PostgreSQL under the frozen v0.4.0.

## Exact next executable action if approved
```
pwsh -ExecutionPolicy Bypass -File P2_OPERATOR_FREEZE_AND_EXEC.ps1
```
(script accompanies this package; section 5B runs the DB service + P2 plan;
a `C6_STOP:` prints trigger + LAST_STEP as today).