"""M14A-E1 evaluator amendment: zero-network tests (no Docker/WSL/API)."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import socket
import sys
import types
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src", P / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

TASK = "saleor-rc-b14def73518c"
LABEL = "u_073711c62862"
DIFF = ("diff --git a/saleor/core/utils/translations.py b/saleor/core/utils/translations.py\n"
        "--- a/saleor/core/utils/translations.py\n+++ b/saleor/core/utils/translations.py\n"
        "@@ -1 +1 @@\n-x\n+y\n"
        "diff --git a/saleor/product/models.py b/saleor/product/models.py\n"
        "--- a/saleor/product/models.py\n+++ b/saleor/product/models.py\n@@ -1 +1 @@\n-a\n+b\n")
NAME_ERROR_LOG = (
    "Traceback (most recent call last):\n"
    '  File "/opt/venv/lib/python3.9/site-packages/pytest_django/plugin.py", line 180, in _setup_django\n'
    "    django.setup()\n"
    '  File "/workspace/wt/saleor/product/models.py", line 716, in ProductVariant\n'
    "    translated = TranslationProxy()\n"
    "NameError: name 'TranslationProxy' is not defined\n"
    "DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/db\n")


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, P / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(socket.socket, "connect", boom)


@pytest.fixture()
def e1():
    return load("e1core", "scripts/wp2_m14a_evalcore_e1.py")


# ================================================================ pure rule
def test_edited_paths_and_rcs(e1):
    assert e1.edited_paths(DIFF) == ["saleor/core/utils/translations.py",
                                     "saleor/product/models.py"]
    assert e1.edited_paths("") == []
    assert e1.parse_rcs("x\nRC_C_0=1\nRC_U_2=137\nE2E_DONE\n") == {"C_0": 1, "U_2": 137}


def test_classify_positive_signature(e1):
    c = e1.classify_run(1, NAME_ERROR_LOG, e1.edited_paths(DIFF))
    assert c["startup_failure_signature"] is True
    assert c["edited_files_in_log"] == ["saleor/product/models.py"]


@pytest.mark.parametrize("rc,log,why", [
    (0, NAME_ERROR_LOG, "rc 0"),
    (137, NAME_ERROR_LOG, "killed"),
    (None, NAME_ERROR_LOG, "no rc"),
    (1, None, "no log"),
    (1, "some output\nNameError: x\n", "no traceback"),
    (1, "Traceback (most recent call last):\n  File \"/x/other.py\"\nNameError: y\n", "no edited file"),
    (4, "Traceback (most recent call last):\n  saleor/product/models.py\n", "no exception line"),
])
def test_classify_negative(e1, rc, log, why):
    assert e1.classify_run(rc, log, e1.edited_paths(DIFF))["startup_failure_signature"] is False, why


def test_decide_truth_table(e1):
    ok = {"startup_failure_signature": True}
    bad = {"startup_failure_signature": False}
    keys = ["C_0", "C_1", "U_0"]
    assert e1.decide(keys, [], {}, True) == e1.ALL_JUNIT_PRESENT
    assert e1.decide(keys, ["C_0"], {"C_0": ok}, True) == e1.INFRA_PARTIAL_MISSING
    assert e1.decide(keys, keys, {k: ok for k in keys} | {"U_0": bad}, True) == e1.INFRA_UNCLASSIFIED
    assert e1.decide(keys, keys, {k: ok for k in keys}, False) == e1.INFRA_PARENT_UNVERIFIED
    assert e1.decide(keys, keys, {k: ok for k in keys}, True) == e1.PATCH_STARTUP_FAILURE


def test_redaction(e1):
    tail = "\n".join(e1.redact_tail(NAME_ERROR_LOG))
    assert "saleor:saleor" not in tail and "postgres://<redacted>" in tail


# ================================================================ evaluator (faked WSL/Docker)
GROUPS = {"behavioral_f2p_node_ids": ["t::f"], "p2p_s_node_ids": ["t::s"],
          "p2p_u_cap200_stable_ids": ["u::a", "u::b"]}


def _fakes(monkeypatch, mod, tmp_path, files: dict[str, str], rc_lines: str, done=True):
    import benchmark.wp2.e2e.scopes as sc
    import benchmark.wp2.harness_v3 as hv
    import benchmark.wp2.oracle_confirmation as oc
    monkeypatch.setattr(hv, "target_manifests", lambda t: [], raising=False)
    monkeypatch.setattr(hv, "lock_install_script", lambda w, m: ("i", "m", None), raising=False)
    monkeypatch.setattr(hv, "locked_dev_install", lambda t: "d", raising=False)
    monkeypatch.setattr(oc, "parse_junit_with_failures",
                        lambda x: ({n: ("passed" if "PASS" in x else "failed")
                                    for n in ("t::f", "t::s", "u::a", "u::b")}, {}),
                        raising=False)
    monkeypatch.setattr(sc, "commits_of", lambda t: ("p", "t"))
    scripts, removed = [], []

    def fake_run(args, **kw):
        scripts.append((tuple(args), kw.get("input", b"")))
        out = (rc_lines + "E2E_DONE") if done else "INSTALL_DEV_FAIL"
        return types.SimpleNamespace(returncode=0, stdout=out, stderr="")
    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    def wsl(s, *a, **k):
        if "worktree remove" in s:
            removed.append(s)
            return types.SimpleNamespace(stdout="")
        for name, content in files.items():
            if f"/{name} " in s:
                return types.SimpleNamespace(stdout=content)
        return types.SimpleNamespace(stdout="__NO_FILE__\n")
    ev = types.SimpleNamespace(
        PROJECT=P, DISTRO="d", REPS=3, NOFILE_HARD=1, STATE_TIMEOUT_S=10, WSL_CACHE="/c",
        E2E_ROOT=tmp_path, fresh_db_name=lambda a, b: "db", ensure_postgres_running=lambda: None,
        ensure_fresh_db=lambda db: None, drop_db=lambda db: None,
        load_evaluator_sets=lambda: {"tasks": {TASK: GROUPS}}, wsl=wsl)
    inv = json.loads((P / "research/wp2/wp2_dev_unchanged_p2p_candidate_inventory_v1"
                      "_2026-09-25.json").read_text(encoding="utf-8"))
    if not any(r["task_id"] == TASK for r in inv["tasks"]):
        pytest.skip("inventory lacks the task in this checkout")
    return ev, scripts, removed


def _xml(content: str) -> dict[str, str]:
    return {f"{TASK[:12]}_{LABEL[:4]}_{g}_r{r}.xml": content for g in "CU" for r in range(3)}


def test_all_junit_present_is_identical_to_frozen_evaluator(e1, monkeypatch, tmp_path):
    ec = sys.modules.get("scripts.wp2_m14a_evalcore") or load("ec", "scripts/wp2_m14a_evalcore.py")
    files = _xml("<testsuite>PASS</testsuite>")
    ev, s1, _ = _fakes(monkeypatch, ec, tmp_path / "a", files, "RC_C_0=0\n")
    ev.E2E_ROOT = tmp_path / "a"
    frozen = ec.evaluate_state_safe(ev, TASK, LABEL, "/wt/x")
    ev2, s2, rm = _fakes(monkeypatch, e1, tmp_path / "b", files, "RC_C_0=0\n")
    ev2.E2E_ROOT = tmp_path / "b"
    diag = tmp_path / "diag.json"
    out = e1.evaluate_state_e1(ev2, TASK, LABEL, "/wt/x", diff_text=DIFF, diag_path=diag,
                               parent_starts_ok=True)
    assert out["groups"] == frozen["groups"] and out["junit_files"] == frozen["junit_files"]
    assert out["e1_decision"] == e1.ALL_JUNIT_PRESENT and not diag.exists() and rm
    assert s1 == s2                                   # identical WSL/Docker commands and scripts


def test_patch_startup_failure_scores_missing(e1, monkeypatch, tmp_path):
    files = {f"run_{g}_{r}.log": NAME_ERROR_LOG for g in "CU" for r in range(3)}
    rcs = "".join(f"RC_{g}_{r}=1\n" for g in "CU" for r in range(3))
    ev, _, rm = _fakes(monkeypatch, e1, tmp_path, files, rcs)
    diag = tmp_path / "d" / "e1_diagnostics.json"
    out = e1.evaluate_state_e1(ev, TASK, LABEL, "/wt/x", diff_text=DIFF, diag_path=diag,
                               parent_starts_ok=True)
    assert out["e1_decision"] == e1.PATCH_STARTUP_FAILURE
    assert out["groups"]["C"] == {"t::f": ["missing"] * 3, "t::s": ["missing"] * 3}
    assert out["groups"]["U"] == {"u::a": ["missing"] * 3, "u::b": ["missing"] * 3}
    d = json.loads(diag.read_text())
    assert d["decision"] == e1.PATCH_STARTUP_FAILURE and len(d["missing_runs"]) == 6
    assert "saleor:saleor" not in diag.read_text() and rm       # redacted; worktree removed
    from benchmark.wp2.e2e import evaluate as fev
    monkeypatch.setattr(fev, "load_evaluator_sets", lambda: {"tasks": {TASK: {
        **GROUPS, "p2p_u_cap200_stable_ids": ["u::a", "u::b"]}}})
    sc = fev.score(TASK, LABEL, out["groups"])
    assert (sc["f2p_task"], sc["p2p_s_task"], sc["p2p_u200_task"], sc["resolved"]) == \
        ("FAIL", "FAIL", "FAIL", False)


@pytest.mark.parametrize("case", ["partial", "unclassified", "parent", "container"])
def test_everything_else_stays_an_infra_stop(e1, monkeypatch, tmp_path, case):
    logs = {f"run_{g}_{r}.log": NAME_ERROR_LOG for g in "CU" for r in range(3)}
    rcs = "".join(f"RC_{g}_{r}=1\n" for g in "CU" for r in range(3))
    files, parent, done = dict(logs), True, True
    if case == "partial":
        files.update({f"{TASK[:12]}_{LABEL[:4]}_U_r{r}.xml": "<t>PASS</t>" for r in range(3)})
    elif case == "unclassified":
        files["run_U_2.log"] = "Killed\n"
    elif case == "parent":
        parent = False
    else:
        done = False
    ev, _, rm = _fakes(monkeypatch, e1, tmp_path, files, rcs, done=done)
    diag = tmp_path / "e1_diagnostics.json"
    ec = sys.modules["scripts.wp2_m14a_evalcore"]
    with pytest.raises(ec.EvalInfraError):
        e1.evaluate_state_e1(ev, TASK, LABEL, "/wt/x", diff_text=DIFF, diag_path=diag,
                             parent_starts_ok=parent)
    assert rm                                           # worktree always removed
    if case != "container":
        assert json.loads(diag.read_text())["decision"].startswith("INFRA_")


def test_frozen_command_text_is_unchanged(e1):
    def block(rel):
        s = (P / rel).read_text(encoding="utf-8")
        return s[s.index("runs.append("):s.index('"echo E2E_DONE")')]
    assert block("scripts/wp2_m14a_evalcore.py") == block("scripts/wp2_m14a_evalcore_e1.py")


# ================================================================ driver / plan / amendment
def test_plan_e1_is_zero_api_and_reuses_frozen_engine():
    plan = json.loads((P / "controller/plan_m14a_pilot_a_v1_e1.json").read_text())
    cmds = [" ".join(p["command"]) for p in plan["phases"]]
    assert [p["id"] for p in plan["phases"]] == ["E00_KIT_SELFTEST", "E01_VERIFY", "E02_EVALUATE",
                                                "E03_SUMMARY", "E04_ADDENDUM"]
    assert not any(re.search(r"\b(generate|doctor-paid|authorize|canary|freeze)\b", c)
                   for c in cmds)
    ev = plan["phases"][2]
    assert ev["command"][1:] == ["scripts/wp2_m14a_e1.py", "evaluate", "--max-evals", "4"]
    assert ev["exit_codes"]["79"] == "STOP:EVAL_ERROR"
    assert set(ev["allowed_write_prefixes"]) == {"research/wp2/pilot_a_v1/evaluations/",
                                                 "research/wp2/pilot_a_v1/junit/"}
    assert plan["settings"]["state_file"].endswith("controller_state_e1.json")
    orig = json.loads((P / "controller/plan_m14a_pilot_a_v1.json").read_text())
    assert plan["settings"]["state_file"] != orig["settings"]["state_file"]


def test_driver_evaluate_injects_e1_into_frozen_run(monkeypatch):
    drv = load("e1drv", "scripts/wp2_m14a_e1.py")
    seen = {}
    monkeypatch.setattr(drv, "verify_problems", lambda: [])
    monkeypatch.setattr(drv.run, "evaluate",
                        lambda n, evaluate_fn=None: seen.update(n=n, fn=evaluate_fn) or 0)
    assert drv.evaluate(4, evaluate_fn=lambda *a: {}) == 0 and seen["n"] == 4 and seen["fn"]
    monkeypatch.setattr(drv, "verify_problems", lambda: ["drift"])
    with pytest.raises(drv.run.Stop):
        drv.evaluate(4, evaluate_fn=lambda *a: {})


def test_readiness_ok_requires_self_hashed_gold_empty(monkeypatch, tmp_path):
    drv = load("e1drv2", "scripts/wp2_m14a_e1.py")
    monkeypatch.setattr(drv.run, "ROOT", tmp_path)
    p = tmp_path / "readiness" / TASK / "record.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(drv.run.self_hash({"gold_empty_ok": True, "artifact_sha256": ""})))
    assert drv.readiness_ok(TASK) is True
    d = json.loads(p.read_text())
    d["gold_empty_ok"] = False
    p.write_text(json.dumps(d))
    assert drv.readiness_ok(TASK) is False
    assert drv.readiness_ok("saleor-rc-none") is False


def test_amendment_artifact_binds_files_and_rule(e1):
    a = json.loads((P / "research/wp2/pilot_a_v1/m14a_e1_amendment.json").read_text())
    run = load("runmod", "scripts/wp2_m14a_run.py")
    assert run.hash_ok(a) and a["rule_constants_sha256"] == e1.rule_constants_sha()
    for rel, h in a["e1_file_hashes"].items():
        assert run.norm_sha(P / rel) == h, rel
    assert "scripts/wp2_m14a_evalcore.py" in a["frozen_files_unchanged"]
    assert a["trigger"]["identity"].startswith(TASK)
