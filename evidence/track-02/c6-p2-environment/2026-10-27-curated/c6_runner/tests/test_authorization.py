# -*- coding: utf-8 -*-
"""Authorization and missing/invalid approval tests (fail-closed)."""
import json
import os

import pytest

from c6runner.authorization import AuthorizationReceipt, FrozenProtocol
from c6runner.errors import MissingApproval, NotAuthorized
from conftest import _make_auth


@pytest.fixture(scope="module")
def freezer(syn):
    return FrozenProtocol(syn["freeze"])


def test_missing_freeze_file(syn, tmp_path):
    from c6runner.errors import C6Stop
    with pytest.raises(C6Stop):
        FrozenProtocol(str(tmp_path / "nope.json"))


def test_missing_authorization_file(syn, tmp_path):
    from c6runner.errors import C6Stop
    with pytest.raises(C6Stop):
        AuthorizationReceipt(str(tmp_path / "nope_auth.json"))


def test_authorization_wrong_protocol(syn):
    # auth bound to a DIFFERENT protocol sha must fail closed
    auth = _make_auth(syn["data_dir"], "0" * 64)
    with pytest.raises(NotAuthorized):
        AuthorizationReceipt(auth).authorize(FrozenProtocol(syn["freeze"]))


def test_authorization_scope_excludes_task(syn):
    auth = _make_auth(syn["data_dir"], syn["proto_sha"], scope=["TASK:" + "f" * 40])
    with pytest.raises(NotAuthorized):
        AuthorizationReceipt(auth).authorize(FrozenProtocol(syn["freeze"]),
                                             task_sha=syn["target"])


def test_authorization_all_scope_ok(syn, freezer):
    auth = _make_auth(syn["data_dir"], syn["proto_sha"], scope="ALL")
    assert AuthorizationReceipt(auth).authorize(freezer, task_sha=syn["target"]) is True


def test_authorization_self_hash_mismatch_detected(syn, tmp_path):
    # tamper with the receipt bytes without touching authorization_sha256
    auth = _make_auth(str(tmp_path), syn["proto_sha"], scope="ALL")
    raw = open(auth, "rb").read()
    tampered = raw.replace(b'"operator": "synthetic-test"',
                           b'"operator": "synthetic-tamper"')
    assert tampered != raw
    tampered_path = os.path.join(str(tmp_path), "tampered_auth.json")
    with open(tampered_path, "wb") as f:
        f.write(tampered)
    with pytest.raises(NotAuthorized):
        AuthorizationReceipt(tampered_path).authorize(FrozenProtocol(syn["freeze"]))