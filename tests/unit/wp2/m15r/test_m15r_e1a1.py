"""M15-R E1A1 evaluator amendment: zero-network regression tests (no Docker/WSL/API)."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import socket
import sys
import types
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src", P / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m14r_core as core  # noqa: E402
from scripts.wp2_m14a_evalcore import EvalInfraError  # noqa: E402
from scripts.wp2_m14a_evalcore_e1 import decide, write_diagnostics  # noqa: E402

REAL = P / "research/wp2/m15r_v1/evaluations/diagnostics/saleor-rc-0a39d039049d/u_2d7cf6d90275/e1_diagnostics.json"
SIG = "AssertionError: Found different types with the same name in the schema: Date, Date."
KEYS = ["C_0", "C_1", "C_2", "U_0", "U_1", "U_2"]


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
def am():
    return load("m15r_e1a1", "scripts/wp2_m15r_e1a1.py")


def run(last=SIG, rc=1, tb=True, frame=True):
    tail = ["Traceback (most recent call last):"] if tb else []
    tail += ['  File "/opt/venv/lib/python3.9/site-packages/graphene/types/typemap.py", line 97'] if frame else []
    tail += ["    assert _type.graphene_type == type, (", last]
    return {"rc": rc, "log_present": True, "rc_in_range": 1 <= rc <= 127, "traceback": tb,
            "exception_line": True, "edited_files_in_log": [], "startup_failure_signature": False,
            "log_tail_redacted": tail}


def diag(tmp: Path, *, per=None, parent=True, edited=("saleor/x.py",), missing=KEYS, decision=None) -> dict:
    per = per or {k: run() for k in KEYS}
    p = tmp / "d.json"
    write_diagnostics(p, {"rule_id": "M14A_E1_PATCH_STARTUP_FAILURE_V1", "rule_constants_sha256": "x",
                          "task_id": "saleor-rc-x", "label": "u_x", "decision": decision or decide(
                              KEYS, list(missing), per, parent),
                          "active_runs": KEYS, "missing_runs": list(missing), "container_rc": 0,
                          "rcs": {}, "edited_paths": list(edited), "parent_starts_ok": parent,
                          "per_run": per})
    return json.loads(p.read_text())


# ================================================================ pure rule
def test_observed_stop_record_is_rescued(am):
    if not REAL.exists():
        pytest.skip("observed diagnostics not in this checkout")
    d = json.loads(REAL.read_text(encoding="utf-8"))
    assert d["decision"] == "INFRA_UNCLASSIFIED" and am.diag_hash_ok(d)
    assert am.decide_e1a1(d) == (am.DECISION, [])


def test_synthetic_signature_rescued_and_safeguards_hold(am, tmp_path):
    d = diag(tmp_path)
    assert d["decision"] == "INFRA_UNCLASSIFIED" and am.decide_e1a1(d) == (am.DECISION, [])
    # A3: parent never started in this environment -> not a patch failure
    d = diag(tmp_path, parent=False)
    assert am.decide_e1a1(d)[0] == "NOT_APPLICABLE" and "A3" in am.decide_e1a1(d)[1]
    # A3: no edited file
    assert am.decide_e1a1(diag(tmp_path, edited=()))[0] == "NOT_APPLICABLE"
    # A2: partial missing stays infrastructure (frozen E1 already says INFRA_PARTIAL_MISSING)
    d = diag(tmp_path, missing=KEYS[:3])
    assert d["decision"] == "INFRA_PARTIAL_MISSING" and am.decide_e1a1(d)[0] == "NOT_APPLICABLE"
    # A1: tampered diagnostics
    d = diag(tmp_path)
    d["parent_starts_ok"] = True
    d["per_run"]["C_0"]["rc"] = 2
    assert am.decide_e1a1(d)[1][0] == "A1"


@pytest.mark.parametrize("last", [
    "django.db.utils.OperationalError: could not connect to server: Connection refused",
    "psycopg2.OperationalError: FATAL:  database does not exist",
    "OSError: [Errno 28] No space left on device",
    "MemoryError",
    "AssertionError: something else",
    "docker: Error response from daemon: OCI runtime create failed",
])
def test_genuine_infrastructure_and_other_errors_stay_infrastructure(am, tmp_path, last):
    per = {k: run(last=last) for k in KEYS}
    d = diag(tmp_path, per=per)
    assert d["decision"] == "INFRA_UNCLASSIFIED"
    dec, failed = am.decide_e1a1(d)
    assert dec == "NOT_APPLICABLE" and all(f.startswith("A5") for f in failed)


def test_signature_must_hold_in_every_run_with_a_graphene_frame(am, tmp_path):
    per = {k: run() for k in KEYS}
    per["U_2"] = run(last="psycopg2.OperationalError: server closed the connection unexpectedly")
    assert am.decide_e1a1(diag(tmp_path, per=per)) == ("NOT_APPLICABLE", ["A5:U_2"])
    per = {k: run(frame=False) for k in KEYS}
    assert am.decide_e1a1(diag(tmp_path, per=per))[0] == "NOT_APPLICABLE"
    per = {k: run(rc=137) for k in KEYS}                     # killed process: not a startup failure
    assert am.decide_e1a1(diag(tmp_path, per=per))[0] == "NOT_APPLICABLE"
    per = {k: run(tb=False) for k in KEYS}
    assert am.decide_e1a1(diag(tmp_path, per=per))[0] == "NOT_APPLICABLE"


def test_rule_is_generic_not_task_or_scalar_specific(am, tmp_path):
    other = "AssertionError: Found different types with the same name in the schema: Money, Money."
    assert am.decide_e1a1(diag(tmp_path, per={k: run(last=other) for k in KEYS}))[0] == am.DECISION
    src = (P / "scripts/wp2_m15r_e1a1.py").read_text()
    code = src.split('"""', 2)[2]                            # everything after the module docstring
    assert "0a39d039049d" not in code and '"Date' not in code and "Date," not in code


# ================================================================ wrapper semantics
class EV:
    REPS = 3

    def load_evaluator_sets(self):
        return {"tasks": {"saleor-rc-x": {"behavioral_f2p_node_ids": ["t::f"], "p2p_s_node_ids": ["t::s"],
                                          "p2p_u_cap200_stable_ids": ["u::1"]}}}


def test_wrapper_passthrough_rescue_reraise_and_stale_diag(am, tmp_path):
    dp = tmp_path / "diag/e1_diagnostics.json"
    sentinel = {"groups": {"C": {}, "U": {}}, "e1_decision": "ALL_JUNIT_PRESENT"}
    assert am.evaluate_state_e1a1(EV(), "saleor-rc-x", "u_x", "/wt", diff_text="d", diag_path=dp,
                                  parent_starts_ok=True, e1_fn=lambda *a, **k: sentinel) is sentinel

    def failing(per, parent=True):
        def fn(ev, t, lb, wt, *, diff_text, diag_path, parent_starts_ok):
            write_diagnostics(diag_path, {"rule_id": "M14A_E1_PATCH_STARTUP_FAILURE_V1", "task_id": t,
                                          "label": lb, "decision": decide(KEYS, KEYS, per, parent_starts_ok),
                                          "active_runs": KEYS, "missing_runs": KEYS, "container_rc": 0,
                                          "edited_paths": ["saleor/x.py"], "parent_starts_ok": parent_starts_ok,
                                          "per_run": per})
            raise EvalInfraError("JUnit missing")
        return fn
    r = am.evaluate_state_e1a1(EV(), "saleor-rc-x", "u_x", "/wt", diff_text="d", diag_path=dp,
                               parent_starts_ok=True, e1_fn=failing({k: run() for k in KEYS}))
    assert r["e1_decision"] == am.DECISION and r["junit_files"] == {}
    assert r["groups"] == {"C": {"t::f": ["missing"] * 3, "t::s": ["missing"] * 3}, "U": {"u::1": ["missing"] * 3}}
    rec = json.loads((dp.parent / "e1a1_decision.json").read_text())
    assert rec["decision"] == am.DECISION and rec["model_api_calls"] == 0
    with pytest.raises(EvalInfraError):                       # parent unverified: original error re-raised
        am.evaluate_state_e1a1(EV(), "saleor-rc-x", "u_x", "/wt", diff_text="d", diag_path=dp,
                               parent_starts_ok=False, e1_fn=failing({k: run() for k in KEYS}))

    def no_diag(*_a, **_k):                                   # container never finished: no diagnostics
        raise EvalInfraError("evaluation container did not finish")
    with pytest.raises(EvalInfraError):                       # the stale record above is never reused
        am.evaluate_state_e1a1(EV(), "saleor-rc-x", "u_x", "/wt", diff_text="d", diag_path=dp,
                               parent_starts_ok=True, e1_fn=no_diag)
    assert not dp.exists()


def test_scoring_and_taxonomy_of_a_rescued_state(am):
    t = EV().load_evaluator_sets()["tasks"]["saleor-rc-x"]
    g = {"C": {"t::f": ["missing"] * 3, "t::s": ["missing"] * 3}, "U": {"u::1": ["missing"] * 3}}
    st, rb = core.score_strict(t, g), core.score_robust(t, g)
    assert st["f2p_task"] == "FAIL" and not st["resolved"] and not rb["resolved"]
    lab = core.classify_episode("APPLIED", False, am.DECISION, t, g, st)
    assert lab["label"] == "PATCH_STARTUP_FAILURE"


def test_engine_evaluate_with_amended_fns_records_failure(am, tmp_path, monkeypatch):
    m = am.m15r
    root = tmp_path / "m15r"
    for k, v in {"ROOT": root, "READY": root / "readiness"}.items():
        monkeypatch.setattr(m, k, v)
    monkeypatch.setattr(m, "EVAL_PLAN", {"s2": root / "evaluations/p2.json", "s3": root / "evaluations/p3.json"})
    monkeypatch.setattr(m, "verify_generation_freeze", lambda st: [])
    t = EV().load_evaluator_sets()["tasks"]
    monkeypatch.setattr(m, "pilot_sets", lambda: t)
    m.write(m.READY / "saleor-rc-x/record.json", m.self_hash({"decision": "READY", "artifact_sha256": ""}))
    diff = "diff --git a/saleor/x.py b/saleor/x.py\n"
    ident = m.core_diff_sha(diff)
    src = root / "episodes/saleor-rc-x/GOLD_HARD__C0__r1"
    src.mkdir(parents=True)
    (src / "final_diff.patch").write_text(diff)
    m.write(m.EVAL_PLAN["s2"], {"items": [{"task_id": "saleor-rc-x", "diff_sha256": ident,
                                           "source": "episodes/saleor-rc-x/GOLD_HARD__C0__r1/episode.json",
                                           "labels": ["GOLD_HARD__C0__r1"], "sources": ["s"]}],
                                "n_unique_identities": 1})
    monkeypatch.setattr(am, "DIAG_DIR", root / "evaluations/diagnostics_e1a1")
    import scripts.wp2_m14a_evalcore_e1 as e1mod

    def fake_e1(ev, tk, lb, wt, *, diff_text, diag_path, parent_starts_ok):
        per = {k: run() for k in KEYS}
        write_diagnostics(diag_path, {"rule_id": "M14A_E1_PATCH_STARTUP_FAILURE_V1", "task_id": tk, "label": lb,
                                      "decision": decide(KEYS, KEYS, per, parent_starts_ok), "active_runs": KEYS,
                                      "missing_runs": KEYS, "container_rc": 0, "edited_paths": ["saleor/x.py"],
                                      "parent_starts_ok": parent_starts_ok, "per_run": per})
        raise EvalInfraError("JUnit missing")
    monkeypatch.setattr(e1mod, "evaluate_state_e1", fake_e1)
    fns = am.amended_fns()
    fns.materialize_fn = lambda tk, lb, d: ("/wt", "tree")
    fns.ev = EV()
    assert m.evaluate("s2", 4, fns) == 0 and m.eval_complete("s2") == 0
    rec = json.loads(m.unique_path("saleor-rc-x", ident).read_text())
    assert rec["e1_decision"] == am.DECISION and not rec["robust"]["resolved"] and not rec["strict"]["resolved"]
    assert (root / "evaluations/diagnostics_e1a1/saleor-rc-x" / ("u_" + ident[:12]) / "e1a1_decision.json").exists()


# ================================================================ kit / provenance
def test_frozen_modules_untouched_and_amendment_record_binds_rule(am):
    man = json.loads((P / "controller/KIT_MANIFEST_M15R.json").read_text())
    def norm(p):
        d = (P / p).read_bytes().replace(b"\r\n", b"\n")
        return hashlib.sha256(d).hexdigest()
    for r in ("scripts/wp2_m14a_evalcore_e1.py", "scripts/wp2_m15r_run.py", "controller/plan_m15r_v1.json"):
        assert norm(r) == man["files"][r], r
    a = json.loads(am.AMENDMENT.read_text())
    q = copy.deepcopy(a)
    q["artifact_sha256"] = ""
    assert am._sha_obj(q) == a["artifact_sha256"]
    assert a["rule_id"] == am.RULE_ID and a["rule_constants_sha256"] == am.rule_constants_sha()
    assert a["model_api_calls"] == 0 and a["reevaluate_existing_records"] is False
    for r, h in a["frozen_files_unchanged"].items():
        assert norm(r) == h, r


def test_continuation_plan_is_evaluation_only_until_the_gate():
    plan = json.loads((P / "controller/plan_m15r_v1_e1a1.json").read_text())
    ids = [p["id"] for p in plan["phases"]]
    assert ids == ["A00_KIT_SELFTEST", "A01_E1A1_VERIFY", "A02_S2_EVALUATE", "A03_S2_GATE", "A04_S3_GENERATE",
                   "A05_S3_GENERATION_FREEZE", "A06_S3_EVAL_PLAN", "A07_S3_EVALUATE", "A08_SUMMARY"]
    ph = {p["id"]: p for p in plan["phases"]}
    assert "scripts/wp2_m15r_e1a1.py" in ph["A02_S2_EVALUATE"]["command"]
    assert "scripts/wp2_m15r_e1a1.py" in ph["A07_S3_EVALUATE"]["command"]
    paid = [p["id"] for p in plan["phases"] if {"agent", "generate"} & set(p.get("command", []))]
    assert paid == ["A04_S3_GENERATE"]
    s = plan["settings"]
    assert s["state_file"] == "research/wp2/m15r_v1/controller_state_e1a1.json"
    assert s["kit_manifest"] == "controller/KIT_MANIFEST_M15R_E1A1.json"
    txt = json.dumps(plan)
    for bad in ("--tags", "opws-evaluate", "Q16_S2_EVALUATE\"", "generate\", \"--stage\", \"s2"):
        assert bad not in txt
    for p in plan["phases"]:
        for pre in p.get("allowed_write_prefixes", []):
            assert pre.startswith(("research/wp2/m15r_v1/", "docs/WP2_M15R")), pre
    _ = types  # keep import used
