# -*- coding: utf-8 -*-
"""Protocol freeze + operator authorization binding (fail-closed).

Authorization model (Track02 pattern, mirrors H1/H2 approval receipts):
  - The operator freezes an accepted protocol document: sha256 of final bytes.
    `C6_PROTOCOL_FREEZE.json` records {protocol_sha256, utc, operator,
    protocol_document_path}.
  - The operator then issues a SEPARATE CLI authorization receipt, a JSON file
    bound to the freeze hash: {authorization_sha256 (write-then-hash), utc,
    operator, protocol_sha256, scope: ["TASK:<sha>", ...] | "ALL",
    resource_caps, notes}.
  - The runner requires BOTH files. If either is absent, malformed, or the
    bindings don't match the on-disk bytes, authorization never unlocks.
"""
import json
import os

from .errors import FrozenInputDrift, MissingApproval, NotAuthorized
from .hashes import sha256_file


class FrozenProtocol:
    def __init__(self, freeze_path: str):
        self.freeze_path = freeze_path
        if not os.path.exists(freeze_path):
            raise MissingApproval("protocol freeze file not found", freeze_path)
        try:
            self.doc = json.load(open(freeze_path, encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise MissingApproval("protocol freeze file malformed", str(e)) from e
        req = ("protocol_sha256", "utc", "operator", "protocol_document_path")
        missing = [k for k in req if not self.doc.get(k)]
        if missing:
            raise MissingApproval("freeze schema incomplete", f"missing={missing}")
        self.protocol_sha256 = str(self.doc["protocol_sha256"]).upper()
        self.protocol_document_path = self.doc["protocol_document_path"]
        if not os.path.exists(self.protocol_document_path):
            raise FrozenInputDrift("protocol document missing", self.protocol_document_path)
        self._doc_sha = sha256_file(self.protocol_document_path)
        if self._doc_sha != self.protocol_sha256:
            raise FrozenInputDrift(
                "protocol document hash drift",
                f"file={self._doc_sha} declared={self.protocol_sha256}")


class AuthorizationReceipt:
    SCHEMA_KEYS = ("authorization_sha256", "utc", "operator",
                   "protocol_sha256", "scope")

    def __init__(self, auth_path: str):
        self.auth_path = auth_path
        if not os.path.exists(auth_path):
            raise MissingApproval("authorization receipt not found", auth_path)
        with open(auth_path, "rb") as f:
            self._bytes = f.read()
        try:
            self.doc = json.loads(self._bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise MissingApproval("authorization file malformed", str(e)) from e
        missing = [k for k in self.SCHEMA_KEYS if k not in self.doc]
        if missing:
            raise MissingApproval("authorization schema incomplete", f"missing={missing}")
        self.authorization_sha256 = str(self.doc["authorization_sha256"]).upper()
        self.protocol_sha256 = str(self.doc["protocol_sha256"]).upper()
        self.scope = self.doc["scope"]
        self.task_bindings = self.doc.get("task_bindings") or {}
        self.resource_caps = self.doc.get("resource_caps") or {}

    def verify_self_hash(self) -> bool:
        """Documented convention: authorization_sha256 is the SHA-256 over the
        canonical serialization of the document WITHOUT the self-field. This is
        deterministic and tamper-evident (any mutation changes recomputation)."""
        import hashlib
        stripped = {k: v for k, v in self.doc.items() if k != "authorization_sha256"}
        canonical = json.dumps(stripped, indent=1, sort_keys=True) + "\n"
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper() == self.authorization_sha256

    def authorize(self, protocol: FrozenProtocol, task_sha: str = None):
        if not self.verify_self_hash():
            raise NotAuthorized("authorization self-hash mismatch", self.auth_path)
        if self.protocol_sha256 != protocol.protocol_sha256:
            raise NotAuthorized(
                "authorization not bound to this protocol freeze",
                f"auth={self.protocol_sha256} freeze={protocol.protocol_sha256}")
        if self.scope != "ALL":
            key = f"TASK:{task_sha}"
            if task_sha is None or key not in self.scope:
                raise NotAuthorized("task outside authorization scope", key)
        if task_sha is not None and self.task_bindings:
            if task_sha not in self.task_bindings:
                raise NotAuthorized(
                    "no task binding in authorization receipt", f"TASK:{task_sha}")
        if task_sha is not None and self.task_bindings:
            return self.task_bindings[task_sha]
        return True

    def binding_for(self, task_sha: str) -> dict:
        """Return the operator-frozen per-task binding (plan constants)."""
        if not self.task_bindings or task_sha not in self.task_bindings:
            raise NotAuthorized("task binding absent", f"TASK:{task_sha}")
        return self.task_bindings[task_sha]