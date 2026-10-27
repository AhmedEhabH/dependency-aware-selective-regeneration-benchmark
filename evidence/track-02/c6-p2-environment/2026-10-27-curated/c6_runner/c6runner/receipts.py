# -*- coding: utf-8 -*-
"""Complete task receipts (write-then-hash discipline)."""
import hashlib
import json
import os

from . import RECEIPT_SCHEMA_V2


def write_receipt(path: str, payload: dict) -> str:
    """Serialize payload to final bytes, write file, then a <file>.sha256
    sidecar with the digest of the FINAL bytes (write-then-hash)."""
    payload = dict(payload)
    payload["receipt_schema"] = RECEIPT_SCHEMA_V2
    final = json.dumps(payload, indent=1, sort_keys=True) + "\n"
    raw = final.encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest().upper()
    with open(path, "wb") as f:
        f.write(raw)
    with open(path + ".sha256", "w", encoding="utf-8") as f:
        f.write(digest + "  " + os.path.basename(path) + "\n")
    return digest


def load_receipt(path: str):
    with open(path, "rb") as f:
        raw = f.read()
    doc = json.loads(raw.decode("utf-8"))
    digest = hashlib.sha256(raw).hexdigest().upper()
    return doc, digest