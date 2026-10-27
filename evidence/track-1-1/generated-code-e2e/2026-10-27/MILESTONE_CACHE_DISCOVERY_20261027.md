# Track 1.1 — D2 offline dependency-cache discovery: STOP (2026-10-27)

**Observed gate:** D2 frozen NEG stage **PASS**, host OCI image present, prior isolated PostgreSQL TCP and external-egress checks **PASS**. **Locked offline dependency installation STOP; zero generated-code pytest executions** (0/3 F2P distinct nodes, 0/103 P2P distinct nodes, 0/318 expected invocations). Original A5-R1 model attempt remains **STOP** at `EDIT_2_NOOP_STOP`. D2 is **post-hoc diagnostic**, not an official success.

## Unmodified direct evidence

- Host read-only discovery completed at approximately **2026-10-27 09:33 UTC** (12:33 Cairo); exact timestamp within log not printed. Observed results preserved as `CACHE_DISCOVERY.log` in this folder.
- Original log SHA-256: `edde9441aa24c633541ecac8f37b67de8a646a5bdb599e80a8df957499459ace`.
- Historical reference evidence was reported as 1,078 find-links entries and 237 installed locked packages under R7/R8; do not treat those historical counts as a new D2 pass.
- `/opt/wp2_v2/m17-env/wheelhouse_full` showed **372 top-level files**, including `amqp-5.1.1-py3-none-any.whl`. It did **not** expose a matching `amqp==5.3.1` wheel in the previous V2 four-wheelhouse lookup. Other searched wheelhouses reported 1, 0 and 0 files.
- `amqp==5.3.1` candidate **is present in the historical uv cache as an extracted distribution**, at `/opt/wp2_v2/m17-env/uv-cache/archive-v0/78t-8_kYua-4CL9A/amqp-5.3.1.dist-info` with sibling `amqp/`, plus the index directory `/opt/wp2_v2/m17-env/uv-cache/wheels-v6/pypi/amqp`.
- This establishes an important cache candidate, **not yet verified package metadata/RECORD integrity, uv-cache index accessibility, complete 237-package closure, or a successful isolated container installation**.

## Diagnosis and follow-up

The V2 evaluator searched only four flat archive locations for `amqp==5.3.1`; it did not incorporate the historical `uv-cache` path. **That scope mismatch explains its early pre-Docker STOP**, but it does not yet prove an end-to-end offline installation succeeds using the cache. In particular, a `*.dist-info` directory alone is not a wheel in the flat index and must not be treated as one.

Next **evaluator-only** gate: run `READONLY_UV_CACHE_GATE.sh` via `wsl.exe ... bash -s` to prove package `METADATA` name/version and `RECORD`, cache-index presence and disk usage. Then freeze a new evaluator version that presents an integrity-checked read-only cache source to a new isolated container (copy to a private writable cache if `uv` needs writes); set `UV_CACHE_DIR`, retain offline/no-index constraints, pin image, `uv.lock`, source hashes, fresh PostgreSQL, Docker `--internal` networking and egress checks. **No online pip/uv fallback, no package-version change, no candidate modification.** STOP on cache closure miss. Only after dependency qualification should the 106 frozen tests run with three physical invocations each and fresh JUnit/RC hashes.

No extra model/API requests, Docker mutations, tests, or downloaded dependencies took place in this read-only discovery. Time and disk/network beyond the logs are **NOT_MEASURED**.

Do not upload raw OpenRouter responses or API credentials to this public research repository; preserve separately with raw SHA receipts.
