# -*- coding: utf-8 -*-
"""NON-CANDIDATE PostgreSQL connectivity probe v2 (--network none, unix socket).
Exercises: raw psycopg2 over unix socket in shared named volume, SQL semantics,
scratch DB lifecycle, and the EXACT era settings path (DATABASE_URL parsed by
dj_database_url as the runner would inject)."""
import psycopg2, sys, json
out = {"ok": False}
try:
    conn = psycopg2.connect(host="/pg-sock", dbname="c6probe",
                            user="c6probe", password="c6probe", connect_timeout=10)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS probe_t")  # idempotent probe
    cur.execute("SELECT version()")
    out["server"] = cur.fetchone()[0][:80]
    cur.execute("CREATE TABLE probe_t(a int PRIMARY KEY, b text)")
    cur.execute("INSERT INTO probe_t VALUES (1, 'x'), (2, 'y'), (3, 'z')")
    cur.execute("SELECT sum(a) FROM probe_t")
    out["sum"] = cur.fetchone()[0]
    conn.commit()
    cur.execute("SELECT count(*) FROM probe_t")
    out["count"] = cur.fetchone()[0]
    conn.commit()
    conn.autocommit = True
    cur.execute("CREATE DATABASE c6probe_scratch")
    cur.execute("DROP DATABASE c6probe_scratch")
    out["scratch_db_create_drop"] = True
    conn.autocommit = False
    cur.close(); conn.close()
    # era settings path: DATABASE_URL parsed by dj_database_url (unix socket)
    import dj_database_url
    url = "postgres://c6probe:c6probe@/c6probe?host=/pg-sock"
    cfg = dj_database_url.parse(url)
    out["dj_database_url_engine"] = cfg["ENGINE"]
    out["dj_database_url_full"] = cfg
    opts = cfg.get("OPTIONS") or {}
    # Django 4.0 psycopg2 backend merges OPTIONS into connect kwargs; the
    # unix socket dir lands in OPTIONS["host"]. Mirror that exactly.
    host = opts.get("host") or cfg.get("HOST") or "/pg-sock"
    c2 = psycopg2.connect(host=host, dbname=cfg["NAME"],
                          user=cfg["USER"], password=cfg["PASSWORD"],
                          connect_timeout=10)
    cur2 = c2.cursor()
    cur2.execute("SELECT 1")
    out["dj_database_url_connect"] = (cur2.fetchone()[0] == 1)
    out["dj_database_url_host_used"] = host
    c2.close()
    out["ok"] = True
except Exception as e:
    out["error"] = f"{type(e).__name__}: {e}"
print(json.dumps(out, indent=1))
sys.exit(0 if out["ok"] else 2)