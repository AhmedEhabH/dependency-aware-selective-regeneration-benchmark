# -*- coding: utf-8 -*-
"""Hash primitives. json_blob follows the frozen WP-B convention
(SHA-256 over compact JSON + newline, uppercase)."""
import hashlib
import json

HEX = "0123456789ABCDEF"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def sha256_bytes_upper(data: bytes) -> str:
    return sha256_hex(data)


def json_blob(items) -> str:
    """Frozen WP-B json_blob: SHA-256(compact_json(items)+'\\n'), uppercase."""
    raw = json.dumps(sorted(set(items)), separators=(",", ":"), ensure_ascii=True) + "\n"
    return sha256_hex(raw.encode("utf-8"))


def digest_sorted_records(records) -> str:
    """SHA-256 over a stable canonical encoding of a dict/list of str/int records."""
    data = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    return sha256_hex(data.encode("utf-8"))