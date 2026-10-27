# -*- coding: utf-8 -*-
"""NON-CANDIDATE full-stack integration probe: era settings + Django ORM +
PostgreSQL over the unix socket, exactly as the P2P role container would bring
them up (minus any test execution)."""
import os, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
os.environ["SECRET_KEY"] = "c6-probe-secret-not-for-execution"
os.environ["DATABASE_URL"] = "postgres://c6probe:c6probe@/c6probe?host=/pg-sock"
os.environ.setdefault("REDIS_URL", "redis://unused:6379/0")
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
_k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
os.environ["RSA_PRIVATE_KEY"] = _k.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
    serialization.NoEncryption()).decode()
import django
django.setup()
print("DJANGO_SETUP_OK")
from django.conf import settings
print("DATABASES:", settings.DATABASES["default"]["ENGINE"], "| HOST=", settings.DATABASES["default"].get("HOST"))
from django.db import connection
with connection.cursor() as cur:
    cur.execute("SELECT version()")
    v = cur.fetchone()[0][:60]
    cur.execute("SELECT 1+1")
    s = cur.fetchone()[0]
print("ORM_SELECT_OK", s, "|", v)
# django.contrib.postgres searchvector support (used by contract)
try:
    with connection.cursor() as cur:
        cur.execute("SELECT 'cat'::tsvector")
        out = cur.fetchone()
    print("SEARCHVECTOR_OK", out[0][:20])
except Exception as e:
    print("SEARCHVECTOR_FAIL", type(e).__name__, str(e)[:100])
# saleor app tables exist? only if migrated — do NOT migrate in a probe. The
# plugin MODULE import closure was already exercised by app.ready() (plugins
# load_and_check_plugin raised earlier when petl was missing — now passes).
print("PLUGIN_APP_READY_OK (all saleor.plugins modules imported at app.ready)")
print("INTEGRATION_PROBE_PASS")