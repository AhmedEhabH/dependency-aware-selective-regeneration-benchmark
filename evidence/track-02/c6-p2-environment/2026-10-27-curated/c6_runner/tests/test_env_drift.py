# -*- coding: utf-8 -*-
"""Environment identity drift: identical sources with a different dependency
pin at P yield a different ENVIRONMENT_ID; same pin is stable."""
import json
import os

from c6runner.environment import EnvSnapshot


def test_env_id_stable_for_same_pins():
    a = EnvSnapshot({"requirements.txt": {"content_sha256": "A" * 64, "bytes": 3}},
                    interpreter="cpython-3.11", wheelhouse_id="WH1", image_ref="NONE")
    b = EnvSnapshot({"requirements.txt": {"content_sha256": "A" * 64, "bytes": 3}},
                    interpreter="cpython-3.11", wheelhouse_id="WH1", image_ref="NONE")
    assert a.environment_id() == b.environment_id()


def test_env_id_drifts_on_dep_content():
    a = EnvSnapshot({"requirements.txt": {"content_sha256": "A" * 64, "bytes": 3}},
                    interpreter="cpython-3.11", wheelhouse_id="WH1")
    b = EnvSnapshot({"requirements.txt": {"content_sha256": "B" * 64, "bytes": 3}},
                    interpreter="cpython-3.11", wheelhouse_id="WH1")
    assert a.environment_id() != b.environment_id()


def test_env_id_drifts_on_wheelhouse():
    a = EnvSnapshot({}, interpreter="cpython-3.11", wheelhouse_id="WH1")
    b = EnvSnapshot({}, interpreter="cpython-3.11", wheelhouse_id="WH2")
    assert a.environment_id() != b.environment_id()


def test_env_id_drifts_on_interpreter():
    a = EnvSnapshot({}, interpreter="cpython-3.11", wheelhouse_id="WH1")
    b = EnvSnapshot({}, interpreter="cpython-3.12", wheelhouse_id="WH1")
    assert a.environment_id() != b.environment_id()


def test_runner_env_id_tracks_requirements_change(syn, tmp_path):
    """Mutate requirements content in the synthetic repo at the SAME internal
    env schema level: manifests snapshot differs => ENVIRONMENT_ID differs."""
    from c6runner.runner import C6Runner
    doc = json.load(open(syn["frozen_inputs"], encoding="utf-8"))
    fi = {v["path"]: v["sha256"] for v in doc.values()}
    r = C6Runner(syn["freeze"], syn["auth"], syn["bare"], syn["ledger"],
                 syn["events"], os.path.dirname(syn["body"]),
                 str(tmp_path / "runs"), fi)
    env_a = r._env_snapshot(syn["parent"])
    # different manifest content
    env_a.manifests["requirements.txt"] = {"content_sha256": "C" * 64, "bytes": 4}
    env_b = r._env_snapshot(syn["parent"])
    assert env_a.environment_id() != env_b.environment_id()


def test_env_schema_version_enforced():
    import c6runner
    assert c6runner.ENV_SCHEMA_V1 == "env-v1"