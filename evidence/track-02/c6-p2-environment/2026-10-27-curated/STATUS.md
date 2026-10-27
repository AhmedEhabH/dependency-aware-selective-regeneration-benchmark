# Track02 C6/P2 evidence snapshot — 27 October 2026

**Research status:** C4+C5 frozen 174 candidates; C6 runner v0.4.0 regression suite 90/90 PASS; **candidate C6 runs = 0/174**. P2 environment probes qualified; P2 pilot remains STOP until a scoped runner DB-service adapter is implemented, independently tested, and explicitly authorized by the researcher.

**Git status:** This is an evidence publication on a dedicated branch, not protocol approval or a claim of behavioral qualification. The underlying frozen Saleor history is not copied here. Source versions, receipts, build scripts, and SHA256 manifest provide traceability.

**P2:** Python 3.9.25 compatible substitute (historical runtime requested 3.9.14; NOT identical). Task image sha256:4b41010cadabc8e5b9d09c1207f32ebbc59dbad72662e01c91f415f6a4ee6919; PostgreSQL image sha256:9b4593c6de443299b46098151fc1ec154c882339b77a56334c7ce612c8a7be6a. Both network-isolated; named-volume Unix socket probe PASS.

**Known review finding:** `plans/P2_v050.example.json` in the preserved handoff contains an invalid literal newline in `notes`, so it is not executable JSON as delivered. Any successor plan must correct the JSON, then recompute its SHA256 and secure a NEW per-plan operator authorization. This preserved example is NOT an approved executable plan.

**Runner delta:** `work/p2_env_unblock/C6_P2_RUNNER_DELTA_PROPOSAL.md` is a PROPOSAL only. Do not silently publish baked RSA private keys, put live credentials in plans, or infer DB readiness from socket existence alone. Use authenticated `pg_isready` and bounded cleanup for DB/volume, and ensure DB version/digest are bound to the execution receipt and plan identity.

**Safety:** The scripts under evidence are archival/operator examples only. No pilot was run by this publication. No key, token, wheelhouse binary, Docker image, or protected body cache is committed. `SOURCE_MANIFEST.json` lists exact byte hashes for the text evidence at publication.

**Next gate:** operator approves scoped DB adapter; independent GREEN tests; regenerate/validate plan and protocol bindings; issue explicit P2-only authorization; one serial pilot; publish actual receipts before any expansion.
