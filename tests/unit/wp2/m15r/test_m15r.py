"""M15-R kit: behavioral, adversarial, zero-network tests (no Docker/WSL/API, no Pilot-B outcome)."""
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

ENGINE = "scripts/wp2_m15r_run.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, P / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def norm(p: Path) -> str:
    d = p.read_bytes()
    if b"\x00" not in d[:8192]:
        d = d.replace(b"\r\n", b"\n")
    return hashlib.sha256(d).hexdigest()


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(socket.socket, "connect", boom)


T = {"behavioral_f2p_node_ids": ["t.py::f1"], "p2p_s_node_ids": ["t.py::s1"],
     "p2p_u_cap200_stable_ids": ["u.py::u1"]}
OK3 = ["passed"] * 3
FAIL3 = ["failed"] * 3


def groups(f1=OK3, s1=OK3, u1=OK3):
    return {"C": {"t.py::f1": f1, "t.py::s1": s1}, "U": {"u.py::u1": u1}}


DESIGN = json.loads((P / "research/wp2/m15r_v1/m15r_design_freeze_v1.json").read_text())
PLAN = json.loads((P / "controller/plan_m15r_v1.json").read_text())


# ================================================================ design / pins
def test_design_binds_engine_review_and_pilot_b():
    q = copy.deepcopy(DESIGN)
    q["artifact_sha256"] = ""
    assert core.sha_obj(q) == DESIGN["artifact_sha256"]
    assert DESIGN["core_constants_sha256"] == core.sha_obj(core.design_constants())
    src = (P / ENGINE).read_text()
    assert f'DESIGN_SHA = "{DESIGN["artifact_sha256"]}"' in src
    b = DESIGN["population"]["pilot_b_tasks"]
    assert len(b) == len(set(b)) == 10 and DESIGN["population"]["min_members"] == 6
    fm = P / "research/wp2/pilot_a_v1/pilot_final_membership.json"
    if fm.exists():
        f = json.loads(fm.read_text())
        assert f["B"] == b and f["artifact_sha256"] == DESIGN["pins"]["pilot_final_membership_artifact_sha256"]
        assert not set(b) & set(f["A"])
    m14 = P / "research/wp2/m14r_v1/m14r_design_freeze_v1.json"
    if m14.exists():
        assert not set(b) & set(json.loads(m14.read_text())["population"]["candidate_tasks"])
    for r, h in DESIGN["pins"]["file_norm_sha256"].items():
        if (P / r).exists():
            assert norm(P / r) == h, r
    assert "docs/WP2_RESHAPE_INDEPENDENT_REVIEW_2026-10-01.md" in DESIGN["pins"]["file_norm_sha256"]
    assert DESIGN["tokens"]["winner_tokens"] == [] and "stronger-model" in json.dumps(DESIGN["arms"]["excluded"])
    assert len(DESIGN["source_review"]["wording_errata"]) == 2


def test_g0_sources_are_the_m14r_sources_and_unchanged():
    pins = DESIGN["pins"]["m14r_g0_source_norm_sha256"]
    assert {"scripts/wp2_m14r_run.py", "scripts/wp2_m14r_core.py"} <= set(pins)
    m14 = load("m14r_for_pins", "scripts/wp2_m14r_run.py")
    assert set(m14.BORROWED) <= set(pins)
    for r, h in pins.items():
        assert norm(P / r) == h, r
    fr = P / "research/wp2/m14r_v1/m14r_freeze.json"
    if fr.exists():                       # the exact code that produced M14R G0
        sh = json.loads(fr.read_text())["source_hashes"]
        for r in pins:
            assert sh[r] == pins[r], r


# ================================================================ engine fixture
@pytest.fixture()
def eng(tmp_path, monkeypatch):
    m = load("m15r_run", ENGINE)
    root = tmp_path / "m15r"
    paths = {"ROOT": root, "GUARD": root / "g.json", "READY": root / "readiness",
             "MEMBERSHIP": root / "m.json", "AUTH": root / "auth.json", "AGENT_PRE": root / "pre.json",
             "AGENT_DIR": root / "agent", "AGENT_ITEMS": root / "agent/items", "FREEZE": root / "f.json",
             "SCOPES": root / "s.json", "PROMPT_META": root / "pm.json", "OPWS_DIR": root / "opws",
             "OPWS_PLAN": root / "opws/plan.json", "OPWS_SUMMARY": root / "os.json",
             "S2_GATE": root / "gate.json", "SUMMARY": root / "sum.json", "OPWS_REPORT": tmp_path / "o.md",
             "REPORT": tmp_path / "r.md", "LEDGER": root / "ledger/x.jsonl",
             "STOP_FLAG": tmp_path / "STOP.flag"}
    for k, v in paths.items():
        monkeypatch.setattr(m, k, v)
    monkeypatch.setattr(m, "PLANS", {"s2": root / "p2.json", "s3": root / "p3.json"})
    monkeypatch.setattr(m, "GEN_FREEZE", {"s2": root / "gf2.json", "s3": root / "gf3.json"})
    monkeypatch.setattr(m, "EVAL_PLAN", {"s2": root / "evaluations/p2.json", "s3": root / "evaluations/p3.json"})
    monkeypatch.setattr(m, "pilot_sets", lambda: {"saleor-rc-x": T, "saleor-rc-y": T})
    root.mkdir(parents=True)
    return m


def ready(eng, t="saleor-rc-x", pos_diff="POSDIFF"):
    rd = eng.READY / t
    eng.write(rd / "record.json", eng.self_hash({
        "decision": "READY", "artifact_sha256": "",
        "positive": {"editable": ["saleor/a.py", "saleor/b.py"], "scoped_diff_sha256": eng.text_sha(pos_diff)}}))
    eng.write(rd / "negative_groups.json", eng.self_hash({
        "groups": groups(f1=FAIL3, s1=["passed", "failed", "passed"]), "tree_sha": "t0", "artifact_sha256": ""}))
    eng.write(rd / "positive_groups.json", eng.self_hash({
        "groups": groups(), "tree_sha": "t1", "e1_decision": "ALL_JUNIT_PRESENT",
        "scoped_diff_sha256": eng.text_sha(pos_diff), "artifact_sha256": ""}))


def scope(ed, raw=None):
    return {"editable": sorted(ed), "raw": sorted(raw if raw is not None else ed), "excluded_large": [],
            "excluded_budget": []}


SC = {"GOLD_HARD": scope(["saleor/a.py", "saleor/b.py"]),
      "RMCSS_HARD": scope(["saleor/a.py", "saleor/c.py"]),
      "AGENT_HARD:r1": scope(["saleor/a.py", "saleor/b.py", "saleor/z.py"]),
      "AGENT_HARD:r2": scope(["saleor/z.py"]),
      "AGENT_HARD:r3": scope([])}


# ================================================================ S1 OPWS
def test_opws_restriction_and_file_prf(eng):
    assert eng.opws_paths(SC, "RMCSS_HARD") == ["saleor/a.py"]
    assert eng.opws_paths(SC, "AGENT_HARD:r1") == ["saleor/a.py", "saleor/b.py"]
    assert eng.opws_paths(SC, "AGENT_HARD:r2") == [] and eng.opws_paths(SC, "AGENT_HARD:r3") == []
    gold_only_raw = dict(SC, GOLD_HARD=scope(["saleor/a.py"], raw=["saleor/a.py", "saleor/big.py"]),
                         RMCSS_HARD=scope(["saleor/big.py"]))
    # a gold file excluded from GOLD editable (budget) still counts when the selector allowed it
    assert eng.opws_paths(gold_only_raw, "RMCSS_HARD") == ["saleor/big.py"]
    r = eng.prf(SC["RMCSS_HARD"]["editable"], SC["GOLD_HARD"]["raw"])
    assert (r["precision"], r["recall"], r["f1"]) == (0.5, 0.5, 0.5)
    assert eng.prf([], ["a"]) == {"precision": 0.0, "recall": 0.0, "f1": 0.0, "tp": 0, "n_editable": 0,
                                  "n_gold": 1}


def _opws_setup(eng, monkeypatch):
    monkeypatch.setattr(eng, "verify_freeze", lambda: [])
    monkeypatch.setattr(eng, "members", lambda: ["saleor-rc-x"])
    monkeypatch.setattr(eng, "PROJECT", eng.ROOT.parent)
    monkeypatch.setattr(eng, "freeze_pushed", lambda: "wp2-m15r-v1-freeze-test")
    ready(eng)
    eng.write(eng.SCOPES, {"tasks": {"saleor-rc-x": SC}})

    def diff_fn(_t, ps):
        return "POSDIFF" if ps == ["saleor/a.py", "saleor/b.py"] else "D:" + ",".join(ps) + "\n"
    return diff_fn


def test_opws_plan_kinds_and_determinism(eng, monkeypatch):
    diff_fn = _opws_setup(eng, monkeypatch)

    def unpushed():
        raise eng.Stop("no pushed freeze tag")
    with pytest.raises(eng.Stop):                           # S1 never starts from an unpushed freeze
        eng.opws_plan(diff_fn, pushed_fn=unpushed)
    assert not eng.OPWS_PLAN.exists()
    assert eng.opws_plan(diff_fn) == 0
    kinds = {i["selector"]: i["kind"] for i in eng.load(eng.OPWS_PLAN)["items"]}
    assert kinds == {"GOLD_HARD": "REUSE_SCOPED_GOLD", "RMCSS_HARD": "EVALUATE",
                     "AGENT_HARD:r1": "REUSE_SCOPED_GOLD", "AGENT_HARD:r2": "EMPTY_BY_CONSTRUCTION",
                     "AGENT_HARD:r3": "EMPTY_BY_CONSTRUCTION"}
    assert eng.opws_plan(diff_fn) == 0                      # deterministic re-run accepted
    with pytest.raises(eng.Stop):
        eng.opws_plan(lambda t, ps: "OTHER\n")              # a different plan is refused
    from scripts.wp2_m14a_evalcore import EvalInfraError

    def infra(*_a):
        raise EvalInfraError("wsl down")
    eng.OPWS_PLAN.unlink()
    with pytest.raises(eng.Stop) as ei:
        eng.opws_plan(infra)
    assert ei.value.code == eng.EXIT_EVAL_INFRA
    with pytest.raises(eng.Stop):                           # GOLD must reproduce the S0 diff
        eng.opws_plan(lambda t, ps: "NOT_THE_POSITIVE\n")


def test_opws_evaluate_reuse_dedupe_budget_and_scoring(eng, monkeypatch):
    diff_fn = _opws_setup(eng, monkeypatch)
    eng.opws_plan(diff_fn)
    seen = []
    fns = eng.EvalFns(evaluate_fn=lambda t, lb, wt, d: seen.append(d) or {
        "groups": groups(s1=["passed", "failed", "passed"]), "e1_decision": "ALL_JUNIT_PRESENT"},
        materialize_fn=lambda t, lb, d: ("/wt", "tree"))
    assert eng.opws_evaluate(0, fns) == 0                   # budget 0: no real evaluation
    assert seen == [] and eng.opws_complete() == 1
    eng.opws_evaluate(5, fns)
    assert seen == ["D:saleor/a.py\n"] and eng.opws_complete() == 0
    res = {s: eng.load(eng.opws_record_path("saleor-rc-x", s)) for s in
           ("GOLD_HARD", "RMCSS_HARD", "AGENT_HARD:r1", "AGENT_HARD:r2")}
    assert res["GOLD_HARD"]["opws_robust"] and res["AGENT_HARD:r1"]["evaluation_source"] == \
        "READINESS_POSITIVE_CONTROL"
    assert res["RMCSS_HARD"]["opws_robust"] and not res["RMCSS_HARD"]["opws_strict"]   # 1-of-3 forgiven
    assert res["AGENT_HARD:r2"]["evaluation_source"] == "EMPTY_BY_CONSTRUCTION"
    assert not res["AGENT_HARD:r2"]["opws_robust"] and not res["AGENT_HARD:r2"]["opws_strict"]
    p = eng.opws_record_path("saleor-rc-x", "RMCSS_HARD")
    p.write_text(p.read_text().replace('"opws_robust": true', '"opws_robust": false'))
    with pytest.raises(eng.Stop):
        eng.opws_evaluate(5, fns)                           # tampered record is never replaced


def test_opws_infra_and_apply_failures_are_distinct_stops(eng, monkeypatch):
    eng.opws_plan(_opws_setup(eng, monkeypatch))
    from scripts.wp2_m14a_evalcore import EvalInfraError

    def infra(*_a):
        raise EvalInfraError("docker down")

    def noapply(*_a):
        raise ValueError("does not apply")
    with pytest.raises(eng.Stop) as ei:
        eng.opws_evaluate(5, eng.EvalFns(infra, lambda t, lb, d: ("/wt", "t")))
    assert ei.value.code == eng.EXIT_EVAL_INFRA
    with pytest.raises(eng.Stop) as ei:
        eng.opws_evaluate(5, eng.EvalFns(infra, noapply))
    assert ei.value.code == eng.EXIT_INVARIANT


def test_opws_summary_agreement_and_paired_contrast(eng, monkeypatch):
    eng.opws_plan(_opws_setup(eng, monkeypatch))
    eng.opws_evaluate(5, eng.EvalFns(lambda t, lb, wt, d: {"groups": groups(f1=FAIL3)},
                                     lambda t, lb, d: ("/wt", "t")))
    meta = {k: {"prompt_chars": 100, "scope_chars": 10} for k in SC}
    eng.write(eng.PROMPT_META, {"tasks": {"saleor-rc-x": meta}})
    s = eng.compute_opws_summary()
    ps = s["per_selector"]
    assert ps["GOLD_HARD"]["opws_robust"] == 1 and ps["RMCSS_HARD"]["opws_robust"] == 0
    assert ps["AGENT_HARD:r1"]["opws_robust"] == 1 and ps["AGENT_HARD:r3"]["no_scope"] == 1
    assert s["agent_replicate_agreement_tasks"] == 0      # r1 True, r2/r3 False
    assert s["paired_rmcss_vs_agent"]["RMCSS_vs_AGENT_HARD:r1"] == {"rmcss_only": 0, "agent_only": 1,
                                                                    "ties": 0}
    assert s["paired_rmcss_vs_agent"]["RMCSS_vs_AGENT_MAJORITY"]["ties"] == 1
    assert s["token"] == "M15R_OPWS_COMPLETE" and s["instrument_valid"]
    assert "winner" not in json.dumps({k: v for k, v in s.items() if k != "mandatory_wording"})


# ================================================================ G0 identity
class FakeCall:
    def __init__(self, text, finish="stop"):
        self.text, self.finish_reason = text, finish
        self.prompt_tokens, self.completion_tokens, self.cost_usd = 100, 10, 0.001
        self.route, self.provider, self.latency_s, self.request_id = "r", "p", 0.0, "id"


class FakeClient:
    def __init__(self, texts):
        self.texts, self.seen, self.network_attempts = list(texts), [], 0

    def generate_messages(self, messages):
        self.seen.append(copy.deepcopy(messages))
        self.network_attempts += 1
        return FakeCall(self.texts.pop(0))

    def set_context(self, **_):
        pass

    def check_hold(self):
        pass


class FakeLedger:
    def __init__(self):
        self.rows, self.context = [], {}

    def record(self, r):
        self.rows.append(r)

    def can_spend(self, _w):
        return True

    def total(self):
        return 0.0


PARENTS = {"saleor/a.py": "def f():\n    return 1\n", "saleor/b.py": "X = 1\n"}
GOOD = "FILE: saleor/a.py\n<<<<<<< SEARCH\n    return 1\n=======\n    return 2\n>>>>>>> REPLACE\n"
BAD = "Looking at this...\n"


@pytest.fixture()
def fake_gen(monkeypatch):
    import benchmark.wp2.e2e.generate as g
    import benchmark.wp2.e2e.generate_v2 as g2
    import benchmark.wp2.e2e.scopes as sc
    import benchmark.wp2.e2e.task_inputs as ti
    import benchmark.wp2.e2e_v21.generate as v21
    tin = types.SimpleNamespace(task_id="saleor-rc-x", era_key="py39", python_requirement="Python >= 3.9",
                                developer_change_description_rendered="Do it")
    for mod in (g, v21):
        monkeypatch.setattr(mod, "_raw_scope", lambda t, a: sorted(PARENTS), raising=False)
        monkeypatch.setattr(mod, "_parent_texts", lambda t, ps: {p: PARENTS[p] for p in ps}, raising=False)
    for mod in (sc, v21):
        monkeypatch.setattr(mod, "editable_filter", lambda t, raw: scope([p for p in raw if p in PARENTS],
                                                                          raw), raising=False)
    for mod in (ti, v21):
        monkeypatch.setattr(mod, "load_task_input", lambda t: tin, raising=False)
    monkeypatch.setattr(g2, "py_compile_in_era", lambda era, files: {p: "ok" for p in files})
    return g


def test_g0_requests_equal_frozen_v21_and_m14r_and_restore_globals(eng, fake_gen, tmp_path):
    from benchmark.wp2.e2e.response_cache import ResponseCache
    from benchmark.wp2.e2e_v21.generate import run_episode_v21
    m14 = eng.m14r()
    real_root, real_raw = m14.ROOT, fake_gen._raw_scope
    scopes = {"saleor-rc-x": {"GOLD_HARD": scope(sorted(PARENTS))}}
    for n, texts in enumerate(([GOOD], [BAD, GOOD], [BAD, BAD])):
        c1, c2, c3 = FakeClient(texts), FakeClient(texts), FakeClient(texts)
        r1 = run_episode_v21("saleor-rc-x", "GOLD_HARD", c1, FakeLedger(), ResponseCache(tmp_path / f"a{n}"),
                             tmp_path / "v21", label="L")
        item = {"task_id": "saleor-rc-x", "arm": "GOLD_HARD", "context": "C0", "replicate": "r1",
                "label": f"GOLD_HARD__C0__r{n + 1}", "stage": "s2", "scope_key": "GOLD_HARD"}
        with eng.g0_redirect(scopes) as st:
            r2 = eng.g0_episode(item, c2, FakeLedger(), ResponseCache(tmp_path / f"b{n}"), st)
        monkey_root = tmp_path / f"m14root{n}"
        old = m14.ROOT
        m14.ROOT = monkey_root
        try:
            r3 = m14.run_base_episode({k: item[k] for k in ("task_id", "arm", "context", "replicate", "label")},
                                      c3, FakeLedger(), ResponseCache(tmp_path / f"c{n}"))
        finally:
            m14.ROOT = old
        assert c1.seen == c2.seen == c3.seen
        assert r1["status"] == r2["status"] == r3["status"]
        if r2["status"] == "APPLIED":
            assert r1["diff_sha256"] == r2["diff_sha256"] == r3["diff_sha256"]
            assert r2["variant"] == "G0"
        assert (eng.ROOT / "episodes/saleor-rc-x" / item["label"] / "episode.json").exists()
        assert real_root == m14.ROOT and fake_gen._raw_scope is real_raw      # globals restored


def test_g0_injects_frozen_per_replicate_agent_scope(eng, fake_gen, tmp_path):
    from benchmark.wp2.e2e.response_cache import ResponseCache
    scopes = {"saleor-rc-x": {"AGENT_HARD:r1": scope(["saleor/a.py"]), "AGENT_HARD:r2": scope(["saleor/b.py"]),
                              "AGENT_HARD:r3": scope([])}}
    seen = {}
    for rep in ("r1", "r2", "r3"):
        item = {"task_id": "saleor-rc-x", "arm": "AGENT_HARD", "context": "C0", "replicate": rep,
                "label": f"AGENT_HARD__C0__{rep}", "stage": "s3", "scope_key": f"AGENT_HARD:{rep}"}
        c = FakeClient([GOOD, GOOD])
        with eng.g0_redirect(scopes) as st:
            r = eng.g0_episode(item, c, FakeLedger(), ResponseCache(tmp_path / rep), st)
        seen[rep] = (r, c)
        assert r["editable_set"] == scopes["saleor-rc-x"][f"AGENT_HARD:{rep}"]["editable"]
    assert "saleor/a.py" in seen["r1"][1].seen[0][1]["content"]
    assert "saleor/a.py" not in seen["r2"][1].seen[0][1]["content"]
    assert seen["r3"][0]["status"] == "NO_SCOPE" and seen["r3"][1].seen == []       # no call
    with eng.g0_redirect(scopes) as st:                     # resolver refuses a foreign item
        st["item"] = {"task_id": "saleor-rc-x", "arm": "RMCSS_HARD", "scope_key": "RMCSS_HARD"}
        import benchmark.wp2.e2e.generate as g
        with pytest.raises(eng.Stop):
            g._raw_scope("saleor-rc-x", "AGENT_HARD")


def test_generate_drives_m14r_driver_with_combined_cap(eng, fake_gen, monkeypatch, tmp_path):
    from benchmark.wp2.e2e.response_cache import ResponseCache
    monkeypatch.setattr(eng, "verify_freeze", lambda: [])
    eng.write(eng.OPWS_SUMMARY, eng.self_hash({"artifact_sha256": ""}))
    sc2 = {"saleor-rc-x": {"GOLD_HARD": scope(sorted(PARENTS))}}
    eng.write(eng.SCOPES, {"tasks": sc2})
    items = eng.gen_items("s2", ["saleor-rc-x"])
    eng.write(eng.PLANS["s2"], {"items": items})
    led = eng.Ledger(eng.LEDGER, 3.0, offset=2.95)           # Agent already spent 2.95 of 3.00

    class Br:
        def on_start(self):
            pass

        def on_success(self):
            pass
    c = FakeClient([GOOD] * 6)
    code = eng.generate("s2", 10, 100, setup=lambda: (led, c, Br()),
                        cache_fn=lambda i: ResponseCache(tmp_path / "cache" / i["label"]))
    assert code == eng.EXIT_BUDGET and c.seen == []          # 2.95 + 0.12 reserve > 3.00
    led2 = eng.Ledger(eng.LEDGER, 3.0, offset=0.5)
    code = eng.generate("s2", 10, 100, setup=lambda: (led2, c, Br()),
                        cache_fn=lambda i: ResponseCache(tmp_path / "cache" / i["label"]))
    assert code == 0 and eng.generation_complete("s2") == 0 and len(c.seen) == 3
    assert all(r["stage"] == "M15R" and r["variant"] == "G0" for r in
               (json.loads(x) for x in eng.LEDGER.read_text().splitlines()))
    assert eng.Ledger(eng.LEDGER, 3.0, 0.5).total() == pytest.approx(0.5 + 3 * 0.001)


def test_s1_must_close_before_s2(eng, monkeypatch):
    monkeypatch.setattr(eng, "verify_freeze", lambda: [])
    with pytest.raises(eng.Stop):
        eng.generate("s2", 1, 1, setup=lambda: (_ for _ in ()).throw(AssertionError("paid setup reached")))


# ================================================================ S2 gate / S3 skip
def test_gate_thresholds_scale():
    m = load("m15r_th", ENGINE)
    assert m.gate_thresholds(10) == {"min_solvable_tasks": 4, "min_robust_episodes": 6, "n_tasks": 10,
                                     "n_episodes": 30}
    assert m.gate_thresholds(6) == {"min_solvable_tasks": 3, "min_robust_episodes": 4, "n_tasks": 6,
                                    "n_episodes": 18}
    for n in range(1, 40):                                  # exact ceil, never float-rounded upward
        th = m.gate_thresholds(n)
        assert th["min_solvable_tasks"] * 10 >= 4 * n > (th["min_solvable_tasks"] - 1) * 10
        assert th["min_robust_episodes"] * 10 >= 6 * n > (th["min_robust_episodes"] - 1) * 10


def _gate_with(eng, monkeypatch, per_task):
    rows = [{"task_id": t, "robust_resolved": i < k, "strict_resolved": False, "unevaluated": False,
             "scope_violation": False} for t, k in per_task.items() for i in range(3)]
    monkeypatch.setattr(eng, "eval_complete", lambda st: 0)
    monkeypatch.setattr(eng, "verify_generation_freeze", lambda st: [])
    monkeypatch.setattr(eng, "episode_rows", lambda st: rows)
    monkeypatch.setattr(eng, "members", lambda: sorted(per_task))
    if eng.S2_GATE.exists():
        eng.S2_GATE.unlink()
    eng.s2_gate()
    return eng.load(eng.S2_GATE)


def test_s2_gate_truth_table(eng, monkeypatch):
    six = {f"t{i}": 0 for i in range(6)}
    g = _gate_with(eng, monkeypatch, dict(six, t0=2, t1=1, t2=1))          # 3 tasks, 4 episodes
    assert g["verdict"] == "PASS" and g["analysis_set_for_s3"] == ["t0", "t1", "t2"]
    g = _gate_with(eng, monkeypatch, dict(six, t0=3, t1=1))                # 2 tasks only
    assert g["verdict"] == "FAIL" and g["token"] == "M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM"
    assert g["analysis_set_for_s3"] == []
    g = _gate_with(eng, monkeypatch, dict(six, t0=1, t1=1, t2=1))          # 3 tasks, 3 episodes
    assert g["verdict"] == "FAIL"


def test_s3_is_a_recorded_no_op_when_the_gate_fails(eng, monkeypatch):
    monkeypatch.setattr(eng, "verify_freeze", lambda: [])
    eng.write(eng.OPWS_SUMMARY, eng.self_hash({"artifact_sha256": ""}))
    eng.write(eng.S2_GATE, eng.self_hash({"verdict": "FAIL", "token": "M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM",
                                          "artifact_sha256": ""}))
    assert eng.generate("s3", 5, 5, setup=lambda: (_ for _ in ()).throw(AssertionError("paid"))) == 0
    assert eng.generation_complete("s3") == 0
    eng.generation_freeze("s3")
    gf = eng.load(eng.GEN_FREEZE["s3"])
    assert gf["skipped"] and gf["n_episodes"] == 0 and eng.verify_generation_freeze("s3") == []
    eng.eval_plan("s3")
    assert eng.load(eng.EVAL_PLAN["s3"])["items"] == [] and eng.eval_complete("s3") == 0


def test_append_only_prefix_check(eng, tmp_path):
    p = tmp_path / "l.jsonl"
    p.write_text('{"a": 1}\n{"b": 2}\n')
    rec = eng._prefix_record(p)
    p.write_text('{"a": 1}\n{"b": 2}\n{"c": 3}\n')
    assert eng._prefix_ok(p, rec)
    p.write_text('{"a": 1}\n{"b": 9}\n{"c": 3}\n')
    assert not eng._prefix_ok(p, rec)


# ================================================================ S0 readiness / membership
def test_readiness_decisions(eng, monkeypatch):
    import benchmark.wp2.e2e.scopes as sc
    monkeypatch.setattr(sc, "build_arm_scopes", lambda t, a: {"editable": ["saleor/a.py"], "excluded_large": [],
                                                              "excluded_budget": []})
    import scripts.wp2_m14a_evalcore as ec
    import scripts.wp2_m14a_evalcore_e1 as e1
    m14 = eng.m14r()

    def run(neg, pos, diff="diff --git a/saleor/a.py b/saleor/a.py\n"):
        monkeypatch.setattr(m14, "scoped_gold_diff", lambda t, ed: diff)
        monkeypatch.setattr(ec, "evaluate_state_safe", lambda ev, t, lb, w: {"groups": neg, "junit_files": {}})
        monkeypatch.setattr(e1, "evaluate_state_e1", lambda ev, t, lb, w, **k: {
            "groups": pos, "e1_decision": "ALL_JUNIT_PRESENT"})
        ev = types.SimpleNamespace(materialize=lambda t, lb, d: ("/wt", "tree"))
        return eng.readiness_task("saleor-rc-x", ev)
    fail = groups(f1=FAIL3)
    r = run(fail, groups())
    assert r["decision"] == "READY" and r["positive"]["scoped_diff_identity"] == eng.core_diff_sha(
        "diff --git a/saleor/a.py b/saleor/a.py\n")
    assert eng.hash_ok(eng.load(eng.READY / "saleor-rc-x/positive_groups.json"))
    assert run(fail, groups(u1=["passed", "failed", "passed"]))["decision"] == "READY"
    assert run(groups(), groups())["decision"] == "NOT_READY_NEGATIVE_CONTROL_INVALID"
    assert run(fail, groups(), diff="")["decision"] == "NOT_READY_EMPTY_SCOPED_GOLD"
    assert run(fail, fail)["decision"] == "NOT_READY_SCOPED_GOLD_NOT_RESOLVED"


def test_readiness_infra_is_resumable_and_membership_floor(eng, monkeypatch):
    monkeypatch.setattr(eng, "design", lambda: {})
    monkeypatch.setattr(eng, "population", lambda: [f"t{i}" for i in range(10)])
    eng.write(eng.GUARD, eng.self_hash({"artifact_sha256": ""}))
    from scripts.wp2_m14a_evalcore import EvalInfraError

    def boom(_t):
        raise EvalInfraError("docker down")
    with pytest.raises(eng.Stop) as ei:
        eng.readiness(1, boom)
    assert ei.value.code == eng.EXIT_PREFLIGHT and not (eng.READY / "t0/record.json").exists()

    def nowsl(_t):
        raise FileNotFoundError("wsl")
    with pytest.raises(eng.Stop) as ei:
        eng.readiness(1, nowsl)
    assert ei.value.code == eng.EXIT_PREFLIGHT

    def bug(_t):
        raise KeyError("engine bug")
    with pytest.raises(KeyError):                           # a code defect is never "environment"
        eng.readiness(1, bug)
    for n_ready, code in ((6, 0), (5, eng.EXIT_POOL)):
        for i in range(10):
            eng.write(eng.READY / f"t{i}/record.json", eng.self_hash({
                "decision": "READY" if i < n_ready else "NOT_READY_X", "artifact_sha256": ""}))
        assert eng.membership() == code
        m = eng.load(eng.MEMBERSHIP)
        assert (m["verdict"] == "OK") == (code == 0)
        assert m["terminal_token"] == ("" if code == 0 else "M15R_POOL_INSUFFICIENT")


# ================================================================ Agent localization wrapper
def test_agent_wrapper_manifest_ceiling_mirror_and_exit_mapping(eng, monkeypatch):
    from benchmark.wp1b import main_runner as mr
    tasks = ["saleor-rc-x", "saleor-rc-y"]
    pre = {"items": eng.agent_items(tasks), "items_sha256": "s", "agent_ceiling_usd": 1.25,
           "worst_case_per_task": {t: {"worst_case_usd": 0.04} for t in tasks}}
    assert [i["key"] for i in pre["items"]][:3] == ["saleor-rc-x#r1", "saleor-rc-y#r1", "saleor-rc-x#r2"]
    monkeypatch.setattr(eng, "agent_prefreeze_record", lambda: pre)
    monkeypatch.setattr(eng, "validate_auth", lambda: {"max_total_spend_usd": 3.0})
    eng.write(eng.AGENT_PRE, pre)
    got = {}

    class Runner:
        def __init__(self, cfg):
            got["cfg"] = cfg

        def run(self):
            cfg = got["cfg"]
            cfg.out_dir.mkdir(parents=True, exist_ok=True)
            with (cfg.out_dir / mr.RECORDS_FILE).open("a") as f:
                for it in cfg.items[:cfg.limit]:
                    f.write(json.dumps({"work_key": it.key, "selected_paths": ["saleor/a.py"],
                                        "prediction_empty": False, "empty_reason": "none",
                                        "infra_failure": False, "token_usage": {}, "model_calls": 3}) + "\n")
            return mr.RunOutcome(got.get("code", 0), got.get("status", "CHUNK_DONE"), "d", cfg.limit, 6, 0.1)
    assert eng.agent(4, runner_factory=Runner) == 0
    cfg = got["cfg"]
    assert cfg.ceiling_usd == 1.25 and cfg.limit == 4 and cfg.kind == "m15r_agent_scope"
    assert [i.replicate for i in cfg.items] == [1, 1, 2, 2, 3, 3] and cfg.stop_file == eng.STOP_FLAG
    assert len(list(eng.AGENT_ITEMS.glob("*.json"))) == 4 and eng.agent_complete() == 1
    for code, status, want in ((mr.EXIT_INFRA_HALT, "PROVIDER_OUTAGE_HALT", eng.EXIT_OUTAGE),
                               (mr.EXIT_INFRA_HALT, "OPERATOR_STOP", eng.EXIT_STOP),
                               (mr.EXIT_BUDGET_ABORT, "H1_BUDGET_ABORT", eng.EXIT_BUDGET),
                               (mr.EXIT_INSTRUMENT_HALT, "H7_TOOLS_BLIND", eng.EXIT_INVARIANT),
                               (mr.EXIT_CONFIG_ERROR, "ACCOUNT_OR_CONFIG_HALT", eng.EXIT_PREFLIGHT)):
        assert eng.translate_agent_exit(code, status) == want
    got.update(code=mr.EXIT_INFRA_HALT, status="PROVIDER_OUTAGE_HALT")
    (eng.AGENT_DIR / mr.RECORDS_FILE).unlink()
    assert eng.agent(1, runner_factory=Runner) == eng.EXIT_OUTAGE


def test_agent_guard_paths_and_tag_scope():
    m = load("m15r_paths", ENGINE)
    for p in ("research/wp2/pilot_a_v1/evaluator_only/", "research/wp2/m15r_v1/readiness/",
              "research/wp2/m15r_v1/opws/", "research/wp2/m15r_v1/evaluations/"):
        assert p in m.AGENT_FORBIDDEN
    for p in ("research/wp2/m15r_v1/agent_prefreeze.json", "research/wp2/m15r_v1/m15r_design_freeze_v1.json",
              "research/wp1b/wp1b_frozen_agent_protocol_v3.json", "src/benchmark",
              "research/wp2/pilot_a_v1/evaluator_only/"):
        assert p in m.AGENT_PATHSPECS
    assert not any(p.startswith("research/wp2/m15r_v1/agent/") for p in m.AGENT_PATHSPECS)
    assert m.AGENT_CEILING_USD <= m.MAX_USD == 3.0
    from benchmark.wp1b import label_guard as lg
    saved = lg._FORBIDDEN_PREFIXES
    try:
        lg._FORBIDDEN_PREFIXES = saved + m.AGENT_FORBIDDEN
        assert lg.is_forbidden_relative("research/wp2/m15r_v1/readiness/saleor-rc-x/record.json")
        assert lg.is_forbidden_relative("research/wp2/pilot_a_v1/evaluator_only/pilot_a_evaluator_sets_v1.json")
        assert not lg.is_forbidden_relative("benchmark_data/real_commit_impact_saleor/scientific/t/public/intent.json")
    finally:
        lg._FORBIDDEN_PREFIXES = saved


# ================================================================ guard helpers
def test_prior_output_scan_and_protected_ids(eng, monkeypatch, tmp_path):
    proj = tmp_path / "proj"
    (proj / "research/wp2/pilot_a_v1/episodes/saleor-rc-a1").mkdir(parents=True)
    (proj / "research/wp2/other/evaluations/unique/saleor-rc-b1/x").mkdir(parents=True)
    (proj / "research/wp2/m15r_v1/episodes/saleor-rc-b2").mkdir(parents=True)
    monkeypatch.setattr(eng, "PROJECT", proj)
    assert eng.prior_outputs(["saleor-rc-b1", "saleor-rc-b2"]) == [
        "research/wp2/other/evaluations/unique/saleor-rc-b1"]
    assert eng.prior_outputs(["saleor-rc-zz"]) == []


# ================================================================ plan / kit
def test_plan_order_paid_boundary_tags_and_isolation():
    ids = [p["id"] for p in PLAN["phases"]]
    assert ids[:13] == ["Q00_KIT_SELFTEST", "Q01_GUARD", "Q02_READINESS", "Q03_MEMBERSHIP", "Q04_AUTH",
                        "Q05_DOCTOR_OFFLINE", "Q06_DOCTOR_PAID", "Q07_AGENT_PREFREEZE", "Q08_AGENT", "Q09_FREEZE",
                        "Q10_OPWS_PLAN", "Q11_OPWS_EVALUATE", "Q12_OPWS_SUMMARY"]
    assert ids[-1] == "Q22_SUMMARY" and ids.index("Q17_S2_GATE") < ids.index("Q18_S3_GENERATE")
    paid = [p["id"] for p in PLAN["phases"] if {"agent", "generate"} & set(p.get("command", []))]
    assert paid == ["Q08_AGENT", "Q13_S2_GENERATE", "Q18_S3_GENERATE"]
    assert ids.index("Q04_AUTH") < ids.index("Q07_AGENT_PREFREEZE") < ids.index("Q08_AGENT")
    assert ids.index("Q09_FREEZE") < ids.index("Q10_OPWS_PLAN")
    ph = {p["id"]: p for p in PLAN["phases"]}
    assert [a["type"] for a in ph["Q07_AGENT_PREFREEZE"]["post_actions"]] == ["commit", "tag", "push"]
    assert ph["Q07_AGENT_PREFREEZE"]["post_actions"][1]["name"].startswith("wp2-m15r-v1-agent-freeze-")
    assert [a["type"] for a in ph["Q09_FREEZE"]["post_actions"]] == ["commit", "tag", "push"]
    assert ph["Q03_MEMBERSHIP"]["exit_codes"]["31"] == "STOP:M15R_POOL_INSUFFICIENT"
    txt = json.dumps(PLAN)
    for bad in ("--tags", "PLACEBO", "deepseek", "m14r_v1/", "pilot_a_v1/"):
        assert bad not in txt
    for p in PLAN["phases"]:
        for pre in p.get("allowed_write_prefixes", []):
            assert pre.startswith(("research/wp2/m15r_v1/", "docs/WP2_M15R")), pre
        if p.get("kind") == "loop":
            assert isinstance(p["progress"], dict) and p["done_checks"]
    s = PLAN["settings"]
    assert s["state_file"] == "research/wp2/m15r_v1/controller_state.json"
    assert "EVAL_ERROR" in s["resumable_tokens"] and "M15R_INVARIANT" not in s["resumable_tokens"]
    assert "E2E_BUDGET_STOP" not in s["resumable_tokens"] and "M15R_POOL_INSUFFICIENT" not in s["resumable_tokens"]


def test_zero_api_outside_paid_paths():
    src = (P / ENGINE).read_text()
    assert "generate_messages(" not in src                         # G0 is the M14R function
    assert src.count("_paid_setup)()") == 1 and src.count("_real_agent_runner)(") == 1
    for fn in ("def readiness_task", "def opws_plan", "def opws_evaluate", "def evaluate(", "def summary",
               "def build_freeze", "def s2_gate", "def guard"):
        body = src.split(fn, 1)[1].split("\ndef ", 1)[0]
        for bad in ("_paid_setup", "OpenRouterBackend", "_real_agent_runner", "generate_messages"):
            assert bad not in body, (fn, bad)
    assert "import requests" not in src and "urllib" not in src
    m14 = (P / "scripts/wp2_m14r_run.py").read_text()
    assert "def run_base_episode" in m14 and "def drive" in m14


def test_kit_manifest_matches_files():
    man = json.loads((P / "controller/KIT_MANIFEST_M15R.json").read_text())
    assert man["design_artifact_sha256"] == DESIGN["artifact_sha256"]
    for r, h in man["files"].items():
        assert norm(P / r) == h, r


def test_authorize_helper_refusals(tmp_path, monkeypatch):
    au = load("m15r_auth", "scripts/wp2_m15r_authorize.py")
    monkeypatch.setattr(au, "M", tmp_path / "m.json")
    monkeypatch.setattr(au, "D", tmp_path / "d.json")
    (tmp_path / "d.json").write_text(json.dumps({"artifact_sha256": "d" * 64}))
    (tmp_path / "m.json").write_text(json.dumps({"verdict": "POOL_INSUFFICIENT", "artifact_sha256": "m"}))
    with pytest.raises(SystemExit):
        au.build("A", 1.0, "t")
    (tmp_path / "m.json").write_text(json.dumps({"verdict": "OK", "artifact_sha256": "m"}))
    with pytest.raises(SystemExit):
        au.build("A", 3.5, "t")
    r = au.build("A", 3.0, "t")
    assert r["artifact_sha256"] == au.sha_obj(dict(r, artifact_sha256=""))
    assert r["max_total_spend_usd"] == 3.0 and r["agent_protocol"] == "wp1b_frozen_agent_protocol_v3"
    with pytest.raises(SystemExit):
        au.build("A", 1.9, "t")                             # below the $2.00 floor
    m = load("m15r_auth_eng", ENGINE)
    assert au.TOKEN == m.APPROVAL_TOKEN and au.MAX_USD == m.MAX_USD


# ================================================================ review fixes (caps, binding, pricing)
def test_authorization_cap_floor_and_agent_worst_case(eng, monkeypatch):
    eng.write(eng.MEMBERSHIP, eng.self_hash({"verdict": "OK", "members": ["saleor-rc-x"], "artifact_sha256": ""}))
    base = {"authorized": True, "approval_token": eng.APPROVAL_TOKEN, "design_artifact_sha256": eng.DESIGN_SHA,
            "membership_artifact_sha256": eng.load(eng.MEMBERSHIP)["artifact_sha256"], "model": eng.MODEL,
            "provider": eng.PROVIDER, "allow_fallbacks": False, "agent_protocol": "wp1b_frozen_agent_protocol_v3",
            "artifact_sha256": ""}
    for cap in (1.5, 3.5):
        eng.write(eng.AUTH, eng.self_hash(dict(base, max_total_spend_usd=cap)))
        with pytest.raises(eng.Stop) as ei:
            eng.validate_auth()
        assert ei.value.code == eng.EXIT_AUTH and "max spend" in str(ei.value)
    monkeypatch.setattr(eng, "validate_auth", lambda: {"max_total_spend_usd": 2.0, "artifact_sha256": "a"})
    monkeypatch.setattr(eng, "members", lambda: ["saleor-rc-x", "saleor-rc-y"])
    monkeypatch.setattr(eng, "bundle_meta", lambda t: {})
    monkeypatch.setattr(eng, "worst_case", lambda t: {"worst_case_usd": 0.25})     # 1.50 > 1.25 ceiling
    with pytest.raises(eng.Stop) as ei:
        eng.build_agent_prefreeze()
    assert ei.value.code == eng.EXIT_AUTH
    monkeypatch.setattr(eng, "worst_case", lambda t: {"worst_case_usd": 0.2})      # 1.20: 2.0-1.2 >= 0.75
    assert eng.build_agent_prefreeze()["worst_case_total_usd"] == pytest.approx(1.2)
    monkeypatch.setattr(eng, "worst_case", lambda t: {"worst_case_usd": 0.21})     # 1.26 > 1.25 ceiling
    with pytest.raises(eng.Stop):
        eng.build_agent_prefreeze()


def test_prefreeze_is_bound_to_the_current_authorization(eng, monkeypatch):
    monkeypatch.setattr(eng, "validate_auth", lambda: {"max_total_spend_usd": 3.0, "artifact_sha256": "a" * 64})
    monkeypatch.setattr(eng, "members", lambda: ["saleor-rc-x"])
    monkeypatch.setattr(eng, "bundle_meta", lambda t: {})
    monkeypatch.setattr(eng, "worst_case", lambda t: {"worst_case_usd": 0.04})
    eng.write(eng.MEMBERSHIP, eng.self_hash({"verdict": "OK", "members": ["saleor-rc-x"], "artifact_sha256": ""}))
    assert eng.agent_prefreeze() == 0
    assert eng.agent_prefreeze_record()["auth_artifact_sha256"] == "a" * 64
    monkeypatch.setattr(eng, "validate_auth", lambda: {"max_total_spend_usd": 2.0, "artifact_sha256": "b" * 64})
    with pytest.raises(eng.Stop) as ei:
        eng.agent_prefreeze_record()
    assert ei.value.code == eng.EXIT_AUTH


def test_generation_checks_live_pricing_before_paid_setup(eng, monkeypatch):
    monkeypatch.setattr(eng, "verify_freeze", lambda: [])
    eng.write(eng.OPWS_SUMMARY, eng.self_hash({"artifact_sha256": ""}))
    import scripts.wp2_e2e_v22_doctor as doc
    monkeypatch.setattr(doc, "live_pricing", lambda: {"ok": False, "value": "drift"})
    monkeypatch.setattr(eng, "_paid_setup", lambda: (_ for _ in ()).throw(AssertionError("paid setup")))
    with pytest.raises(eng.Stop) as ei:
        eng.generate("s2", 1, 1)
    assert ei.value.code == eng.EXIT_PREFLIGHT


def test_materialization_halt_is_resumable_environment():
    m = load("m15r_exit", ENGINE)
    from benchmark.wp1b import main_runner as mr
    assert m.translate_agent_exit(mr.EXIT_INFRA_HALT, "MATERIALIZATION_HALT") == m.EXIT_PREFLIGHT
