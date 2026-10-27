# -*- coding: utf-8 -*-
"""Versioned environment identity for C6.

ENVIRONMENT_ID = SHA-256(ENV_SCHEMA_V1
   | canonical manifest snapshot at P        (path, content_sha256, size)
   | interpreter pin                         (declared or resolved)
   | wheelhouse identity                     (dir id or declared name)
   | runtime base image ref                  (OCI-style ref or NONE))
The formula is versioned (ENV_SCHEMA_V1); any formula change bumps the schema.
"""
import hashlib
import json
import os

from . import ENV_SCHEMA_V1
from .hashes import sha256_hex


class EnvSnapshot:
    def __init__(self, manifests, interpreter=None, wheelhouse_id="NONE",
                 image_ref="NONE", extra=None):
        # manifests: {path: {"content_sha256": str, "bytes": int}}
        self.manifests = dict(manifests)
        self.interpreter = interpreter or "UNRESOLVED"
        self.wheelhouse_id = wheelhouse_id or "NONE"
        self.image_ref = image_ref or "NONE"
        self.extra = extra or {}

    def environment_id(self) -> str:
        parts = {
            "schema": ENV_SCHEMA_V1,
            "manifests": {p: (m["content_sha256"], m.get("bytes"))
                          for p, m in sorted(self.manifests.items())},
            "interpreter": self.interpreter,
            "wheelhouse": self.wheelhouse_id,
            "image": self.image_ref,
            "extra": self.extra,
        }
        data = json.dumps(parts, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True) + "\n"
        return sha256_hex(data.encode("utf-8"))


def wheelhouse_dir_id(wheelhouse_dir: str) -> str:
    """Identity of a wheelhouse by sorted filenames (content not re-hashed here
    unless `deep=True`; deep hashing is caller's choice at protocol freeze)."""
    if not wheelhouse_dir or not os.path.isdir(wheelhouse_dir):
        return "NONE"
    names = sorted(os.listdir(wheelhouse_dir))
    data = json.dumps(names, sort_keys=True, separators=(",", ":")) + "\n"
    return sha256_hex(data.encode("utf-8")).lower()[:16]