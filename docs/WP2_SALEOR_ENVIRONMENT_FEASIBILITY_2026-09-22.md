# WP-2 Saleor Environment Feasibility (2026-09-22)

Zero-API, non-destructive inspection. Nothing was installed, started, or
downloaded; no Saleor test was run; no runtime is claimed. Evidence comes from
the local Saleor cache (`dist/pilot-repo-cache/saleor`, HEAD) and non-destructive
local machine probes. Status codes: **AVAILABLE / NOT_AVAILABLE / UNKNOWN**.

| Item | Status | Evidence |
|---|---|---|
| Supported Python / tooling | AVAILABLE | `pyproject.toml`: `requires-python = ">=3.12,<3.13"`, hatchling. Local interpreter is Python 3.11.5 — below the Saleor HEAD range; a suitable interpreter/venv is needed at execution time. |
| Test runner / framework | AVAILABLE | `setup.cfg [tool:pytest]`: `testpaths = saleor`, `addopts = -n auto --record-mode=none --ds=saleor.tests.settings --disable-socket --allow-hosts 127.0.0.1,::1`. Django TestCase via `saleor.tests.settings`. `pytest` installed in the current interpreter. |
| Database requirements | AVAILABLE | `saleor/settings.py` `DATABASES` default `postgres://saleor:saleor@localhost:5432/saleor`. PostgreSQL 17 service **Running** locally. Port probe not conclusive in this session; connectivity not verified (nothing started). |
| Redis / cache requirements | AVAILABLE | `saleor/settings.py` `CACHES = django_cache_url.config()`, `REDIS_URL` fallback, webhook circuit-breaker RedisStorage. Redis service **Running** locally. `redis` module not installed in the current interpreter. |
| Celery / background worker | AVAILABLE | Celery + django-celery-beat in settings; **`saleor/tests/settings.py` sets `CELERY_TASK_ALWAYS_EAGER = True`** → most tests run eager, no worker needed. `celery` not installed in the current interpreter. |
| Env vars / settings for tests | AVAILABLE | `.env.example` at root (DATABASE_URL / CACHE_URL style). `saleor/tests/settings.py` hard-codes `SECRET_KEY`, `PUBLIC_URL`, locmem email, `POPULATE_DEFAULTS = False`. `--ds=saleor.tests.settings` and `--disable-socket` make the default posture offline. |
| Docker / container support | AVAILABLE | `Dockerfile` at root; `docker` CLI present; no docker-compose at HEAD root (`deployment/elasticbeanstalk` present). Docker not used in this census. |
| PostgreSQL available locally | AVAILABLE | `Get-Service postgresql-x64-17` → Running. |
| Redis available locally | AVAILABLE | `Get-Service Redis` → Running; `redis-cli.exe` present. |
| Required Python deps installed | UNKNOWN | Current interpreter: django/pytest installed; celery/redis/psycopg2/graphql not installed. Saleor `.venv` exists in cache but version completeness not verified. Exact Saleor dependency set = UNKNOWN until a non-destructive check at execution time. |
| No-network local test feasible | AVAILABLE_WITH_SETUP | `setup.cfg` already ships `--disable-socket --allow-hosts 127.0.0.1,::1`; local Postgres + Redis are running. Feasibility is structural, NOT a measured runtime: a real run would need the Saleor dependency set in a suitable interpreter plus a provisioned test database — both deliberately out of scope here. |

## What this means for WP-2

- The repository is Python 3.12+ (HEAD); the local interpreter is 3.11.5. A
  WP-2 executor must pin a compatible interpreter/venv for the target commit's
  era (many MAIN_297 targets predate 3.12 requirements).
- The designed test posture is already offline (`--disable-socket`), and the
  local machine has Postgres + Redis running, so a loopback no-network run is
  structurally feasible.
- Real runtime (setup time, per-test wall time, migration cost) is **NOT
  measured here** and must not be claimed before a WP-2 executor measures it.