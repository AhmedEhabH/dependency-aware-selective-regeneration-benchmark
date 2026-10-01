"""M15-R end-to-end pipeline on SYNTHETIC tasks with fakes (zero network, no Docker/WSL/API).

The engine file is copied into a temporary project so that every evidence path points there;
no Pilot-B task, evaluator set or outcome is read. Both S2 gate branches are exercised.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import socket
import sys
import types
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src", P / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import benchmark.wp2.e2e.generate  # noqa: E402,F401  (cache the real packages before the copy loads)
import scripts.wp2_m14a_evalcore  # noqa: E402
import scripts.wp2_m14r_run  # noqa: E402,F401
from benchmark.wp1b import main_runner  # noqa: E402,F401

TASKS = [f"saleor-rc-x{i}" for i in range(1, 8)]          # x7 will be NOT_READY
T = {"behavioral_f2p_node_ids": ["t.py::f1"], "p2p_s_node_ids": ["t.py::s1"],
     "p2p_u_cap200_stable_ids": ["u.py::u1"]}
OK3, FAIL3 = ["passed"] * 3, ["failed"] * 3
PARENTS = {"saleor/a.py": "def f():\n    return 1\n", "saleor/b.py": "X = 1\n", "saleor/c.py": "Y = 1\n"}
GOLD = ["saleor/a.py", "saleor/b.py"]
GOOD = "FILE: saleor/a.py\n<<<<<<< SEARCH\n    return 1\n=======\n    return 2\n>>>>>>> REPLACE\n"


def grp(ok: bool) -> dict:
    return {"C": {"t.py::f1": OK3 if ok else FAIL3, "t.py::s1": OK3}, "U": {"u.py::u1": OK3}}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(socket.socket, "connect", boom)


def make_project(tmp: Path) -> types.ModuleType:
    design = json.loads((P / "research/wp2/m15r_v1/m15r_design_freeze_v1.json").read_text())
    eng_src = load_real()
    files = set(design["pins"]["m14r_g0_source_norm_sha256"]) | set(eng_src.KIT) | set(eng_src.AGENT_CODE_FILES)
    files |= {"research/wp2/m15r_v1/m15r_design_freeze_v1.json", "research/wp1b/wp1b_frozen_agent_protocol_v3.json",
              "research/memory-rescue-v2/final_oof_predictions_A.json"}
    for r in sorted(files):
        (tmp / r).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(P / r, tmp / r)
    for t in TASKS:
        d = tmp / "benchmark_data/real_commit_impact_saleor/scientific" / t / "public"
        d.mkdir(parents=True)
        (d / "intent.json").write_text(json.dumps({"intent_text": "Do it"}))
    spec = importlib.util.spec_from_file_location("m15r_pipeline_engine", tmp / "scripts/wp2_m15r_run.py")
    mod = importlib.util.module_from_spec(spec)
    saved = list(sys.path)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = saved
    assert tmp == mod.PROJECT and tmp / "research/wp2/m15r_v1" == mod.ROOT
    return mod


def load_real():
    spec = importlib.util.spec_from_file_location("m15r_real_for_lists", P / "scripts/wp2_m15r_run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeCall:
    def __init__(self, text):
        self.text, self.finish_reason = text, "stop"
        self.prompt_tokens, self.completion_tokens, self.cost_usd = 100, 10, 0.001
        self.route, self.provider, self.latency_s, self.request_id = "r", "p", 0.0, "id"


class FakeClient:
    def __init__(self):
        self.seen, self.network_attempts = [], 0

    def generate_messages(self, messages):
        self.seen.append(messages)
        self.network_attempts += 1
        return FakeCall(GOOD)

    def set_context(self, **_):
        pass

    def check_hold(self):
        pass


class Br:
    def on_start(self):
        pass

    def on_success(self):
        pass


@pytest.mark.parametrize("solvable,expect_gate", [(["saleor-rc-x1", "saleor-rc-x2", "saleor-rc-x3"], "PASS"),
                                                   (["saleor-rc-x1"], "FAIL")])
def test_full_pipeline_with_fakes(tmp_path, monkeypatch, solvable, expect_gate):
    m = make_project(tmp_path)
    import benchmark.wp2.e2e.generate as g
    import benchmark.wp2.e2e.generate_v2 as g2
    import benchmark.wp2.e2e.scopes as sc
    import benchmark.wp2.e2e.task_inputs as ti
    from benchmark.wp1b import main_runner as mr
    tin = types.SimpleNamespace(task_id="x", era_key="py39", python_requirement="Python >= 3.9",
                                developer_change_description_rendered="Do it")
    monkeypatch.setattr(g, "_parent_texts", lambda t, ps: {p: PARENTS[p] for p in ps})
    monkeypatch.setattr(sc, "editable_filter", lambda t, raw: {
        "editable": sorted(p for p in raw if p in PARENTS), "raw": sorted(raw), "excluded_large": [],
        "excluded_budget": []})
    monkeypatch.setattr(ti, "load_task_input", lambda t: tin)
    monkeypatch.setattr(g2, "py_compile_in_era", lambda era, files: {p: "ok" for p in files})
    monkeypatch.setattr(m, "population", lambda: TASKS)
    monkeypatch.setattr(m, "pilot_sets", lambda: {t: T for t in TASKS})
    monkeypatch.setattr(m, "worst_case", lambda t: {"worst_case_usd": 0.04})
    monkeypatch.setattr(m, "bundle_meta", lambda t: {"synthetic": True})
    monkeypatch.setattr(m, "freeze_pushed", lambda: "wp2-m15r-v1-freeze-synthetic")

    # ---- S0 readiness + membership
    m.write(m.GUARD, m.self_hash({"artifact_sha256": ""}))

    def task_fn(t):
        m.write(m.READY / t / "negative_groups.json", m.self_hash({"groups": grp(False), "tree_sha": "n",
                                                                   "artifact_sha256": ""}))
        m.write(m.READY / t / "positive_groups.json", m.self_hash({
            "groups": grp(True), "tree_sha": "p", "e1_decision": "ALL_JUNIT_PRESENT",
            "scoped_diff_sha256": m.text_sha("POS:" + t), "artifact_sha256": ""}))
        return {"task_id": t, "decision": "READY" if t != "saleor-rc-x7" else "NOT_READY_SCOPED_GOLD_NOT_RESOLVED",
                "positive": {"editable": GOLD, "scoped_diff_sha256": m.text_sha("POS:" + t)}}
    while m.readiness_check():
        m.readiness(3, task_fn)
    assert m.membership() == 0
    members = m.members()
    assert members == TASKS[:6]

    # ---- authorization (git check replaced) + doctors
    auth = m.self_hash({"approval_token": m.APPROVAL_TOKEN, "max_total_spend_usd": 2.0, "artifact_sha256": ""})
    m.write(m.AUTH, auth)
    monkeypatch.setattr(m, "validate_auth", lambda: m.load(m.AUTH))
    for mode in ("offline", "paid"):
        m.write(m.ROOT / f"doctor/doctor_{mode}.json", {"pass": True})

    # ---- Agent prefreeze + localization (fake runner writes frozen-format records)
    assert m.agent_prefreeze() == 0
    pre = m.load(m.AGENT_PRE)
    assert pre["agent_ceiling_usd"] == 1.25 and len(pre["items"]) == 18

    def sel(key):
        t, rep = key.split("#")
        return {"r1": GOLD, "r2": ["saleor/a.py"], "r3": [] if t == "saleor-rc-x2" else ["saleor/a.py",
                                                                                           "saleor/c.py"]}[rep]

    class Runner:
        def __init__(self, cfg):
            self.cfg = cfg

        def run(self):
            done = {r["work_key"] for r in mr.read_jsonl_tolerant(self.cfg.out_dir / mr.RECORDS_FILE)[0]}
            todo = [i for i in self.cfg.items if i.key not in done][:self.cfg.limit]
            self.cfg.out_dir.mkdir(parents=True, exist_ok=True)
            with (self.cfg.out_dir / mr.RECORDS_FILE).open("a") as f:
                for it in todo:
                    s = sel(it.key)
                    f.write(json.dumps({"work_key": it.key, "selected_paths": s, "prediction_empty": not s,
                                        "empty_reason": "none" if s else "no_paths", "infra_failure": False,
                                        "token_usage": {}, "model_calls": 4}) + "\n")
            return mr.RunOutcome(0, "CHUNK_DONE", "", len(done) + len(todo), len(self.cfg.items), 0.0)
    while m.agent_complete():
        assert m.agent(7, runner_factory=Runner) == 0
    assert len(list(m.AGENT_ITEMS.glob("*.json"))) == 18

    # ---- freeze (scopes from the frozen raw selections; real D35 replaced by the fake filter)
    def build_scopes(tasks, agent_raw):
        out = {}
        for t in tasks:
            raws = {"GOLD_HARD": GOLD, "RMCSS_HARD": ["saleor/a.py", "saleor/c.py"]}
            raws.update({f"AGENT_HARD:{r}": agent_raw[(t, r)] for r in m.REPS})
            out[t] = {k: sc.editable_filter(t, v) for k, v in raws.items()}
        return out
    monkeypatch.setattr(m, "build_scopes", build_scopes)
    monkeypatch.setattr(m, "g0_prompt_meta", lambda t, k, s, st: {"no_scope": not s["editable"],
                                                                  "prompt_chars": 10 * len(s["editable"]),
                                                                  "scope_chars": len(s["editable"]),
                                                                  "leakage_hits": 0})
    assert m.freeze() == 0 and m.freeze_verify() == 0
    fr = m.load(m.FREEZE)
    assert fr["agent_empty"]["saleor-rc-x2#r3"] and not fr["agent_empty"]["saleor-rc-x1#r3"]
    tamper = m.SCOPES.read_text()
    m.SCOPES.write_text(tamper.replace("saleor/c.py", "saleor/b.py", 1))
    assert m.freeze_verify() == 1
    m.SCOPES.write_text(tamper)

    # ---- S1 OPWS
    def diff_fn(t, ps):
        return ("POS:" + t) if ps == GOLD else f"D:{t}:" + ",".join(ps) + "\n"
    with pytest.raises(m.Stop):
        m.generate("s2", 1, 1, setup=lambda: (_ for _ in ()).throw(AssertionError("paid before S1")))
    m.opws_plan(diff_fn)
    calls = []

    def ev_fn(t, lb, wt, d):
        calls.append(d)
        return {"groups": grp(all(f in d for f in GOLD)), "e1_decision": "ALL_JUNIT_PRESENT"}
    fns = m.EvalFns(ev_fn, lambda t, lb, d: ("/wt", "tree"))
    while m.opws_complete():
        m.opws_evaluate(2, fns)
    assert len(set(calls)) == len(calls) == 6               # each unique (task, P_S) evaluated once
    m.opws_summary()
    s1 = m.load(m.OPWS_SUMMARY)
    ps = s1["per_selector"]
    assert s1["token"] == "M15R_OPWS_COMPLETE" and ps["GOLD_HARD"]["opws_robust"] == 6
    assert ps["AGENT_HARD:r1"]["opws_robust"] == 6 and ps["RMCSS_HARD"]["opws_robust"] == 0
    assert ps["AGENT_HARD:r3"]["empty_by_construction"] == 1 and ps["AGENT_HARD:r3"]["no_scope"] == 1
    assert s1["paired_rmcss_vs_agent"]["RMCSS_vs_AGENT_HARD:r1"]["agent_only"] == 6
    assert m.OPWS_REPORT.exists()

    # ---- S2 (G0 via the frozen M14R driver)
    led = m.Ledger(m.LEDGER, 3.0, m.agent_spend_usd())
    client = FakeClient()
    while m.generation_complete("s2"):
        assert m.generate("s2", 5, 100, setup=lambda: (led, client, Br())) == 0
    assert len(client.seen) == 18
    m.generation_freeze("s2")
    m.eval_plan("s2")

    def gen_eval(t, lb, wt, d):
        return {"groups": grp(t in solvable), "e1_decision": "ALL_JUNIT_PRESENT"}
    fns2 = m.EvalFns(gen_eval, lambda t, lb, d: ("/wt", "tree"))
    while m.eval_complete("s2"):
        m.evaluate("s2", 4, fns2)
    m.s2_gate()
    gate = m.load(m.S2_GATE)
    assert gate["verdict"] == expect_gate

    # ---- S3 (or recorded no-op) + summary
    n_before = len(client.seen)
    while m.generation_complete("s3"):
        assert m.generate("s3", 7, 100, setup=lambda: (led, client, Br())) == 0
    m.generation_freeze("s3")
    m.eval_plan("s3")
    while m.eval_complete("s3"):
        m.evaluate("s3", 4, fns2)
    assert not m.verify_generation_freeze("s2")             # S2 freeze survives S3 ledger appends
    m.summary()
    s = m.load(m.SUMMARY)
    assert s["winner_tokens"] == [] and s["tokens"][0] == "M15R_OPWS_COMPLETE"
    if expect_gate == "PASS":
        assert s["tokens"][1] == "M15R_COMPLETE_DESCRIPTIVE" and s["s3_executed"]
        assert len(client.seen) - n_before == 35             # 36 S3 episodes, one NO_SCOPE (x2 r3)
        assert s["per_arm_replicate"]["AGENT_HARD:r3"]["no_scope"] == 1
        assert s["per_arm_replicate"]["RMCSS_HARD:r1"]["robust_analysis_set"] == 3
        assert s["analysis_set"] == solvable
    else:
        assert s["tokens"][1] == "M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM" and not s["s3_executed"]
        assert len(client.seen) == n_before and "RMCSS_HARD:r1" not in s["per_arm_replicate"]
    assert s["per_arm_replicate"]["GOLD_HARD:r1"]["robust_all"] == len(solvable)
    assert s["cost"]["generation_provider_reported_usd"] == pytest.approx(0.001 * len(client.seen))
    assert s["cost"]["agent_localization"]["runs"] == 18 and s["cost"]["agent_localization"]["empty_predictions"] == 1
    assert s["per_arm_replicate"]["GOLD_HARD:r1"]["f2p_node_progress"] == f"{len(solvable)}/6"
    assert m.REPORT.exists()
    q = copy.deepcopy(s)
    q["artifact_sha256"] = ""
    assert m.sha_obj(q) == s["artifact_sha256"]
