"""M16 R2 MAIN input adapter: inputs-only, DEV identity, fail-closed closure checks (zero network)."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import benchmark.wp2.e2e.scopes as scopes  # noqa: E402
import benchmark.wp2.harness_v3 as hv3  # noqa: E402
from scripts import wp2_m16_adapter as ad  # noqa: E402

POETRY_PYPROJECT = ("[tool.poetry.dependencies]\npython='~3.9'\n\n"
                    "[tool.poetry.dev-dependencies]\npytest-mock='3.10.0'\n\n[x]\n")
POETRY_LOCK = ('[[package]]\nname = "pytest-mock"\nversion = "3.10.0"\ncategory = "dev"\npython-versions = ">=3.7"\n\n'
               '[[package]]\nname = "django"\nversion = "3.2"\ncategory = "main"\npython-versions = ">=3.6"\n')


@pytest.fixture(scope="module")
def shadow(tmp_path_factory):
    root = tmp_path_factory.mktemp("shadow")
    info = ad.build_shadow(P, root)
    return root, info


def test_frame_and_rows_are_the_frozen_220():
    rows = ad.main_rows(P)
    assert len(rows) == 220 and set(rows) == set(ad.frame_220(P))
    assert all(r["era_key"] in ad.ERAS for r in rows.values())


def test_shadow_keeps_dev_rows_byte_identical(shadow):
    root, info = shadow
    census, inv = ad.load_shadow(root)
    dev_c = json.loads((P / ad.DEV_CENSUS).read_text(encoding="utf-8"))
    dev_i = json.loads((P / ad.DEV_INVENTORY).read_text(encoding="utf-8"))
    assert census["tasks"][:len(dev_c["tasks"])] == dev_c["tasks"]
    assert inv["tasks"][:len(dev_i["tasks"])] == dev_i["tasks"]
    assert info["n_main_census_rows"] == 297 and info["n_main_frame_rows"] == 220


def test_shadow_is_deterministic(tmp_path, shadow):
    _, info = shadow
    assert ad.build_shadow(P, tmp_path)["files"] == info["files"]


def test_main_inputs_patches_and_restores(shadow):
    root, _ = shadow
    t = sorted(ad.main_rows(P))[0]
    before = (scopes.CENSUS, hv3.PROJECT)
    with pytest.raises(KeyError):
        scopes.commits_of(t)
    assert hv3._era_for(t) is None
    with ad.main_inputs(root):
        assert scopes.commits_of(t)[1] == ad.main_rows(P)[t]["target_commit"]
        assert hv3._era_for(t) == ad.main_rows(P)[t]["era_key"]
    assert (scopes.CENSUS, hv3.PROJECT) == before
    assert hv3._era_for(t) is None


def test_dev_closure_identical_through_the_adapter(monkeypatch, shadow):
    root, _ = shadow
    dev = json.loads((P / ad.DEV_CENSUS).read_text(encoding="utf-8"))["tasks"][0]["task_id"]
    monkeypatch.setattr(hv3, "target_manifests", lambda t: {"pyproject.toml": POETRY_PYPROJECT,
                                                            "poetry.lock": POETRY_LOCK})
    ad.clear_closure_cache([dev])
    frozen = copy.deepcopy(hv3.v31_dev_closure(dev))
    ad.clear_closure_cache([dev])
    with ad.main_inputs(root):
        adapted = copy.deepcopy(hv3.v31_dev_closure(dev))
    assert ad.sha_obj(frozen) == ad.sha_obj(adapted)


def test_main_closure_without_adapter_is_silently_none_and_fails_closed(monkeypatch, shadow):
    root, _ = shadow
    t, row = sorted(ad.main_rows(P).items())[0]
    mf = {"pyproject.toml": POETRY_PYPROJECT, "poetry.lock": POETRY_LOCK}
    monkeypatch.setattr(hv3, "target_manifests", lambda tgt: mf)
    ad.clear_closure_cache([t])
    silent = hv3.v31_dev_closure(t)                          # the historical defect for MAIN
    assert silent["mechanism"] == "none" and silent["note"] == "task not in census"
    bad = ad.check_main_closure(t, row["era_key"], mf, silent)
    assert "CLOSURE_NOTE:task not in census" in bad and "DEV_GROUP_DECLARED_BUT_MECHANISM_NONE" in bad
    ad.clear_closure_cache([t])
    with ad.main_inputs(root):
        good = hv3.v31_dev_closure(t)
    assert good["mechanism"] == "poetry" and good["era_key"] == row["era_key"]
    assert ad.check_main_closure(t, row["era_key"], mf, good) == []
    ad.clear_closure_cache([t])


def test_declares_dev_group_predicate():
    assert ad.declares_dev_group({"pyproject.toml": POETRY_PYPROJECT})
    assert ad.declares_dev_group({"requirements_dev.txt": "pytest==7"})
    assert ad.declares_dev_group({"pyproject.toml": "[dependency-groups]\ndev = [\"pytest\"]\n"})
    assert not ad.declares_dev_group({"requirements.txt": "django==3"})


def test_era_mismatch_and_missing_manifests_fail_closed():
    c = {"mechanism": "poetry", "era_key": "py39", "note": ""}
    assert ad.check_main_closure("t", "py312", {"poetry.lock": "x"}, c) == ["ERA_MISMATCH:py39!=py312"]
    assert "NO_TARGET_MANIFESTS" in ad.check_main_closure("t", "py39", {}, c)


def test_ev_proxy_redirects_project_only(tmp_path):
    class M:
        PROJECT = Path("/orig")
        REPS = 3

        @staticmethod
        def f():
            return "frozen"
    p = ad.EvProxy(M, tmp_path)
    assert p.PROJECT == tmp_path and p.REPS == 3 and p.f() == "frozen" and M.PROJECT == Path("/orig")


def test_lock_install_script_is_the_frozen_object():
    src = (P / "src/benchmark/wp2/harness_v3.py").read_bytes().replace(b"\r\n", b"\n")
    design = json.loads((P / "research/wp2/m16_v1/m16_design_freeze_v1.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(src).hexdigest() == design["pins"]["file_norm_sha256"]["src/benchmark/wp2/harness_v3.py"]
    adapter_src = (P / "scripts/wp2_m16_adapter.py").read_text(encoding="utf-8")
    assert "lock_install_script" not in adapter_src and "def v31_dev_closure" not in adapter_src
