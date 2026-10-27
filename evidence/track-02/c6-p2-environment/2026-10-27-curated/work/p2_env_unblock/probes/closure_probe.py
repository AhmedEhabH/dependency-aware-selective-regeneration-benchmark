# -*- coding: utf-8 -*-
"""NON-CANDIDATE environment closure probe (TRACK02-C6-P2-ENV-UNBLOCK).
Imports django settings at P and the C6 contract test MODULE (imports only;
ZERO candidate tests are executed). Rootfs is read-only, network none."""
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
os.environ.setdefault("SECRET_KEY", "c6-probe-secret-not-for-execution")
os.environ.setdefault("DATABASE_URL", "postgres://c6probe:c6probe@unused/c6probe")
os.environ.setdefault("REDIS_URL", "redis://unused:6379/0")
import django
print("django", django.get_version())
# RSA_PRIVATE_KEY: DEBUG-mode saleor writes a temporary .jwt_key.pem into the
# (read-only) cwd at startup; a real key in env skips that write (era behavior).
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
_k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
os.environ.setdefault(
    "RSA_PRIVATE_KEY",
    _k.private_bytes(serialization.Encoding.PEM,
                     serialization.PrivateFormat.TraditionalOpenSSL,
                     serialization.NoEncryption()).decode())
django.setup()
print("DJANGO_SETUP_OK")
import saleor.graphql.product.tests.test_product as tp  # imports only
print("test_product module IMPORT_OK")
from saleor.graphql.product import filters  # T-changed module content (P rev)
print("filters import OK")
import pkg_resources
print("pkg_resources OK")
try:
    from django.core.management import call_command  # noqa: F401
    from django.test.utils import setup_test_environment  # noqa: F401
    print("test-infra imports OK")
except Exception as e:  # pragma: no cover
    print("test-infra FAIL", type(e).__name__, e)