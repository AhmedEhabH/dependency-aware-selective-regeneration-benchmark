"""M14R kit: behavioral, adversarial, zero-network tests (no Docker/WSL/API)."""
from __future__ import annotations

import copy
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

from scripts import wp2_m14r_core as core  # noqa: E402


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


T = {"behavioral_f2p_node_ids": ["t.py::f1", "t.py::f2"], "p2p_s_node_ids": ["t.py::s1"],
     "p2p_u_cap200_stable_ids": ["u.py::u1", "u.py::u2"]}
OK3 = ["passed"] * 3


def groups(f1=OK3, f2=OK3, s1=OK3, u1=OK3, u2=OK3):
    return {"C": {"t.py::f1": f1, "t.py::f2": f2, "t.py::s1": s1},
            "U": {"u.py::u1": u1, "u.py::u2": u2}}


# ================================================================ scoring
def test_strict_matches_frozen_score_on_synthetic_and_pilot_a(monkeypatch):
    from benchmark.wp2.e2e import evaluate as fev
    monkeypatch.setattr(fev, "load_evaluator_sets", lambda: {"tasks": {"x": T}})
    cases = [groups(), groups(f1=["failed"] * 3), groups(s1=["passed", "failed", "passed"]),
             groups(u2=["missing"] * 3), {"C": {}, "U": {}}, groups(f2=["passed", "passed"])]
    for g in cases:
        a = fev.score("x", "l", g)
        b = core.score_strict(T, g)
        assert (a["f2p_task"], a["p2p_s_task"], a["p2p_u200_task"], a["resolved"]) == \
            (b["f2p_task"], b["p2p_s_task"], b["p2p_u200_task"], b["resolved"])
    root = P / "research/wp2/pilot_a_v1"
    if not (root / "evaluations/unique").exists():
        pytest.skip("Pilot-A evidence not present in this checkout")
    sets = json.loads((root / "evaluator_only/pilot_a_evaluator_sets_v1.json").read_text())["tasks"]
    n = 0
    for f in root.glob("evaluations/unique/*/*/evaluation.json"):
        e = json.loads(f.read_text())
        s = core.score_strict(sets[e["task_id"]], e["groups"])
        assert (s["f2p_task"], s["p2p_s_task"], s["p2p_u200_task"], s["resolved"]) == \
            (e["f2p_task"], e["p2p_s_task"], e["p2p_u200_task"], e["resolved"])
        n += 1
    assert n == 29


def test_robust_rule_only_forgives_single_repetition_preservation_failures():
    one = ["passed", "failed", "passed"]
    two = ["failed", "passed", "failed"]
    assert core.score_robust(T, groups(s1=one, u1=one))["resolved"] is True
    assert core.score_strict(T, groups(s1=one))["resolved"] is False
    assert core.score_robust(T, groups(s1=two))["resolved"] is False
    assert core.score_robust(T, groups(u2=["missing"] * 3))["resolved"] is False
    assert core.score_robust(T, groups(f1=one))["f2p_task"] == "FAIL"      # F2P stays 3/3
    r = core.node_report(T, groups(f1=["failed"] * 3, f2=one, s1=two, u1=["missing"] * 3))
    assert (r["f2p_pass3"], r["f2p_intermittent"], r["s_intermittent"], r["u_missing"]) == (0, 1, 1, 1)


def test_taxonomy_precedence_is_exclusive():
    st = core.score_strict
    assert core.classify_episode("INVALID_AFTER_REPAIR", False, None, None, None, None)["label"] \
        == "FORMAT_INVALID"
    assert core.classify_episode("APPLIED", True, None, T, groups(), st(T, groups()))["label"] == "NO_OP"
    miss = {"C": {k: ["missing"] * 3 for k in groups()["C"]}, "U": {k: ["missing"] * 3 for k in groups()["U"]}}
    assert core.classify_episode("APPLIED", False, None, T, miss, st(T, miss))["label"] == \
        "PATCH_STARTUP_FAILURE"
    assert core.classify_episode("APPLIED", False, None, T, groups(), st(T, groups()))["label"] == "RESOLVED"
    g = groups(s1=["passed", "failed", "passed"])
    c = core.classify_episode("APPLIED", False, None, T, g, st(T, g))
    assert c == {"label": "F2P_PASS_PRESERVATION_FAIL", "detail": "PRESERVATION_INTERMITTENT_ONLY"}
    g = groups(f2=["failed"] * 3, u1=["failed"] * 3)
    c = core.classify_episode("APPLIED", False, None, T, g, st(T, g))
    assert c == {"label": "PARTIAL_F2P_PROGRESS", "detail": "+DETERMINISTIC_PRESERVATION_BREAK"}
    g = groups(f1=["failed"] * 3, f2=["failed"] * 3)
    assert core.classify_episode("APPLIED", False, None, T, g, st(T, g))["label"] == "ZERO_F2P_PROGRESS"


# ================================================================ static check
PARENT = "import os\n\n\ndef f():\n    return DYNAMIC\n"


def test_static_reports_only_new_undefined_names():
    pytest.importorskip("pyflakes")
    gen = "import os\n\n\ndef f():\n    return DYNAMIC + TranslationProxy()\n"
    r = core.new_static_findings({"a.py": PARENT}, {"a.py": gen}, ["a.py"])
    assert [(d["cls"], d["args"]) for d in r["new"]] == [("UndefinedName", ["TranslationProxy"])]
    assert core.new_static_findings({"a.py": PARENT}, {"a.py": PARENT}, ["a.py"])["new"] == []
    r = core.new_static_findings({"a.py": PARENT}, {"a.py": "def f(:\n"}, ["a.py"])
    assert r["new"] == [] and r["parse_skipped"] == ["a.py"]
    msg = core.static_repair_text(core.new_static_findings(
        {"a.py": PARENT}, {"a.py": gen}, ["a.py"])["new"])
    assert "TranslationProxy" in msg and "a.py: line 5" in msg and "test" not in msg.lower()


def test_real_pilot_a_b14def_patches_are_caught_by_static_check():
    pytest.importorskip("pyflakes")
    root = P / "research/wp2/pilot_a_v1/episodes/saleor-rc-b14def73518c"
    if not root.exists():
        pytest.skip("Pilot-A evidence not present in this checkout")
    for lab in ("GOLD_HARD__r1", "GOLD_HARD__r2"):
        f = root / lab / "final_files/saleor/product/models.py"
        found = core.undefined_findings("saleor/product/models.py", f.read_text())
        assert any(d["args"] == ["TranslationProxy"] for d in found)


# ================================================================ read-only context
REPO = {
    "pkg/__init__.py": "",
    "pkg/a/__init__.py": "",
    "pkg/a/edit.py": ("from ..models import Product, helper\nfrom . import sibling\n"
                      "import pkg.util\nfrom pkg.tests.fixtures import fx\n"
                      "from ..migrations import m0001\nimport json\n"),
    "pkg/a/sibling.py": "def public(x):\n    return x\n\n\ndef _private():\n    pass\n",
    "pkg/models.py": ("class Product(Base):\n    \"\"\"Doc.\"\"\"\n    name = CharField()\n"
                      "    available_for_purchase = DateField(\n        null=True)\n\n"
                      "    class Meta:\n        ordering = ('name',)\n\n"
                      "    @property\n    def price(self) -> int:\n        return 1\n\n"
                      "def helper(a,\n           b):\n    return a\n\n\ndef other():\n    pass\n"),
    "pkg/util.py": "CONST = 1\n_HIDDEN = 2\n",
    "pkg/tests/fixtures.py": "fx = 1\n",
    "pkg/migrations/m0001.py": "X = 1\n",
}


def ctx(editable=("pkg/a/edit.py",)):
    return core.build_readonly_context(list(editable), REPO.get, set(REPO),
                                       lambda p: "/tests/" in p)


def test_outline_is_one_hop_verbatim_and_excludes_tests_migrations_editable():
    c = ctx()
    t = c["text"]
    assert "available_for_purchase = DateField(" in t and "def price(self) -> int:" in t
    assert "def helper(a," in t and "           b):" in t and "def other" not in t
    assert "def public(x):" in t and "_private" not in t and "CONST = 1" in t and "_HIDDEN" not in t
    assert "fixtures" not in t and "migrations" not in t and "return 1" not in t
    assert "OUTLINE: pkg/a/edit.py" not in t
    assert core.verbatim_audit(t, REPO.get) == []
    assert core.verbatim_audit(t.replace("CONST = 1", "CONST = 2"), REPO.get)
    assert ctx() == c                                            # deterministic
    assert ctx(("pkg/a/edit.py", "pkg/models.py"))["text"].count("OUTLINE: pkg/models.py") == 0


def test_outline_caps(monkeypatch):
    big = {f"m{i}.py": "".join(f"def f{j}_{i}(x):\n    pass\n" for j in range(900))
           for i in range(20)}
    repo = {"e.py": "".join(f"import m{i}\n" for i in range(20)), **big}
    c = core.build_readonly_context(["e.py"], repo.get, set(repo), lambda p: False)
    assert c["chars"] <= core.OUTLINE_TOTAL_CAP + 200
    assert any(m["status"] == "TOTAL_CAP_REACHED" for m in c["modules"])
    assert "# [outline truncated]" in c["text"]
    assert core.verbatim_audit(c["text"], repo.get) == []


# ================================================================ decision
def metrics(g0=5, g1=5, g2=5, g3=5, inv=(3, 3, 3, 3), pl=(0, 0, 0, 0), tasks_any=(5, 5, 5, 5),
            tok=(100, 100, 100, 100)):
    vals = dict(zip(core.VARIANT_ORDER, (g0, g1, g2, g3), strict=True))
    return {v: {"gold_robust": vals[v], "gold_invalid": inv[k], "placebo_robust": pl[k],
                "tasks_any": tasks_any[k], "gold_mean_tokens": tok[k]}
            for k, v in enumerate(core.VARIANT_ORDER)}


def per_task(counts: dict[str, list[int]]):
    return {v: {f"t{i}": c for i, c in enumerate(counts[v])} for v in counts}


def test_decision_rule_truth_table():
    base = [1] * 5 + [0] * 9
    flat = per_task({v: base for v in core.VARIANT_ORDER})
    assert core.decide(metrics(), flat, 14, False)["token"] == "M14R_INSTRUMENT_FIX"
    assert core.decide(metrics(pl=(0, 0, 2, 0)), flat, 14, True)["token"] == \
        "M14R_PLACEBO_LEAK_REVIEW"
    d = core.decide(metrics(g0=5, g2=8), per_task({"G0": base, "G1": base, "G2": [1] * 8 + [0] * 6,
                                                   "G3": base}), 14, True)
    assert d["winner"] == "G2" and d["token"] == "M14R_FLOOR_NOT_MET"         # 8 < ceil(0.2*42)=9
    d = core.decide(metrics(g0=6, g1=9, g3=9, tok=(100, 90, 100, 80)),
                    per_task({"G0": [1] * 6 + [0] * 8, "G1": [1] * 9 + [0] * 5,
                              "G2": [1] * 6 + [0] * 8, "G3": [1] * 9 + [0] * 5}), 14, True)
    assert d["winner"] == "G3" and d["token"] == "M14R_FLOOR_MET"            # tokens tie-break
    d = core.decide(metrics(g0=6, g1=9, inv=(3, 7, 3, 3)),
                    per_task({"G0": [1] * 6 + [0] * 8, "G1": [1] * 9 + [0] * 5,
                              "G2": [1] * 6 + [0] * 8, "G3": [1] * 6 + [0] * 8}), 14, True)
    assert d["winner"] == "G0" and d["checks"]["G1"]["invalid"] is False
    d = core.decide(metrics(g0=6, g1=9), per_task({"G0": [0, 0, 0, 3, 3] + [0] * 9,
                                                   "G1": [3, 3, 3, 0, 0] + [0] * 9,
                                                   "G2": [0] * 14, "G3": [0] * 14}), 14, True)
    assert d["checks"]["G1"]["direction"] is True
    assert core.thresholds(10)["floor_resolved_min"] == 6 and core.thresholds(10)["floor_tasks_min"] == 4


def test_frozen_design_binds_core_constants_and_engine():
    d = json.loads((P / "research/wp2/m14r_v1/m14r_design_freeze_v1.json").read_text())
    q = copy.deepcopy(d)
    q["artifact_sha256"] = ""
    assert core.sha_obj(q) == d["artifact_sha256"]
    assert d["core_constants_sha256"] == core.sha_obj(core.design_constants())
    eng = (P / "scripts/wp2_m14r_run.py").read_text()
    assert f'DESIGN_SHA = "{d["artifact_sha256"]}"' in eng
    assert d["population"]["candidate_tasks"] == sorted(d["population"]["candidate_tasks"])
    sel = P / "research/wp2/pilot_v1_design/pilot_selection.json"
    if sel.exists():
        s = json.loads(sel.read_text())
        prot = set(s["pilot_a_tasks"]) | set(s["pilot_b_tasks"]) | set(s.get("reserve_order", []))
        assert not prot & set(d["population"]["candidate_tasks"])


# ================================================================ engine fixtures
@pytest.fixture()
def eng(tmp_path, monkeypatch):
    m = load("m14r_run", "scripts/wp2_m14r_run.py")
    root = tmp_path / "m14r"
    for k, v in {"ROOT": root, "READY": root / "readiness", "MEMBERSHIP": root / "m.json",
                 "AUTH": root / "auth.json", "FREEZE": root / "f.json", "SCOPES": root / "s.json",
                 "CTX_DIR": root / "ctx", "GEN_PLAN": root / "gp.json",
                 "STATIC_PLAN": root / "sp.json", "GEN_FREEZE": root / "gf.json",
                 "EVAL_PLAN": root / "evaluations/plan.json", "SUMMARY": root / "sum.json",
                 "REPORT": tmp_path / "r.md", "LEDGER": root / "ledger/x.jsonl",
                 "STOP_FLAG": tmp_path / "STOP.flag"}.items():
        monkeypatch.setattr(m, k, v)
    return m


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
UNDEF = ("FILE: saleor/a.py\n<<<<<<< SEARCH\n    return 1\n=======\n    return Missing()\n"
         ">>>>>>> REPLACE\n")


@pytest.fixture()
def fake_gen(monkeypatch):
    import benchmark.wp2.e2e.generate as g
    import benchmark.wp2.e2e.generate_v2 as g2
    import benchmark.wp2.e2e.scopes as sc
    import benchmark.wp2.e2e.task_inputs as ti
    import benchmark.wp2.e2e_v21.generate as v21
    scope = {"editable": sorted(PARENTS), "excluded_large": [], "excluded_budget": [],
             "raw": sorted(PARENTS)}
    tin = types.SimpleNamespace(task_id="saleor-rc-x", era_key="py39",
                                python_requirement="Python >= 3.9",
                                developer_change_description_rendered="Do it")
    for mod in (g, v21):
        monkeypatch.setattr(mod, "_raw_scope", lambda t, a: sorted(PARENTS), raising=False)
        monkeypatch.setattr(mod, "_parent_texts", lambda t, ps: {p: PARENTS[p] for p in ps},
                            raising=False)
    for mod in (sc, v21):
        monkeypatch.setattr(mod, "editable_filter", lambda t, raw: dict(scope), raising=False)
    for mod in (ti, v21):
        monkeypatch.setattr(mod, "load_task_input", lambda t: tin, raising=False)
    monkeypatch.setattr(g2, "py_compile_in_era", lambda era, files: {p: "ok" for p in files})
    return scope


def test_g0_requests_and_outcome_equal_frozen_v21(eng, fake_gen, tmp_path):
    from benchmark.wp2.e2e.response_cache import ResponseCache
    from benchmark.wp2.e2e_v21.generate import run_episode_v21
    for texts in ([GOOD], [BAD, GOOD], [BAD, BAD]):
        c1, c2 = FakeClient(texts), FakeClient(texts)
        r1 = run_episode_v21("saleor-rc-x", "GOLD_HARD", c1, FakeLedger(),
                             ResponseCache(tmp_path / f"a{len(texts)}{texts[-1][:3]}"),
                             tmp_path / "v21", label="L")
        item = {"task_id": "saleor-rc-x", "arm": "GOLD_HARD", "context": "C0", "replicate": "r1",
                "label": f"GOLD_HARD__C0__r{len(texts)}{texts[-1][:1]}"}
        r2 = eng.run_base_episode(item, c2, FakeLedger(),
                                  ResponseCache(tmp_path / f"b{len(texts)}{texts[-1][:3]}"))
        assert c1.seen == c2.seen                                  # identical requests
        assert r1["status"] == r2["status"]
        if r1["status"] == "APPLIED":
            assert r1["diff_sha256"] == r2["diff_sha256"]
            assert r1["prompt_sha256"] == r2["prompt_sha256"]


def test_c2_adds_readonly_context_and_keeps_scope_hard(eng, fake_gen, tmp_path):
    from benchmark.wp2.e2e.response_cache import ResponseCache
    txt = ("READ-ONLY CONTEXT (NOT EDITABLE): outlines\n===== OUTLINE: saleor/m.py (read-only) "
           "=====\nY = 1\n===== END OUTLINE: saleor/m.py =====")
    p = eng.ctx_path("saleor-rc-x", "GOLD_HARD")
    p.parent.mkdir(parents=True)
    p.write_text(txt)
    (eng.ROOT / "readonly_context").mkdir(parents=True, exist_ok=True)
    (eng.ROOT / "readonly_context/context_meta.json").write_text(json.dumps({"contexts": {
        "saleor-rc-x/GOLD_HARD": {"sha256": hashlib.sha256(txt.encode()).hexdigest()}}}))
    out_of_scope = "FILE: saleor/m.py\n<<<<<<< SEARCH\nY = 1\n=======\nY = 2\n>>>>>>> REPLACE\n"
    c = FakeClient([out_of_scope, out_of_scope])
    item = {"task_id": "saleor-rc-x", "arm": "GOLD_HARD", "context": "C2", "replicate": "r1",
            "label": "GOLD_HARD__C2__r1"}
    r = eng.run_base_episode(item, c, FakeLedger(), ResponseCache(tmp_path / "c2"))
    assert r["status"] == "INVALID_AFTER_REPAIR"
    assert any("OUT_OF_SCOPE_FILE:saleor/m.py" in e for e in r["validation"]["initial"])
    assert txt in c.seen[0][1]["content"] and core.SYSTEM_PROMPT_C2_INSERT in c.seen[0][0]["content"]
    p.write_text(txt + "tampered")
    with pytest.raises(eng.Stop):
        eng.run_base_episode(dict(item, label="GOLD_HARD__C2__r2"), FakeClient([GOOD]),
                             FakeLedger(), ResponseCache(tmp_path / "c2b"))


def _base_then_static(eng, tmp_path, base_texts, static_texts):
    from benchmark.wp2.e2e.response_cache import ResponseCache
    item = {"task_id": "saleor-rc-x", "arm": "GOLD_HARD", "context": "C0", "replicate": "r1",
            "label": "GOLD_HARD__C0__r1"}
    b = eng.run_base_episode(item, FakeClient(base_texts), FakeLedger(),
                             ResponseCache(tmp_path / "base"))
    sitem = {**item, "static": True, "base_label": item["label"], "label": "GOLD_HARD__C0S__r1"}
    c = FakeClient(static_texts)
    led = FakeLedger()
    s = eng.run_static_episode(sitem, c, led, ResponseCache(tmp_path / "st"))
    return b, s, c, led


def test_static_clean_makes_no_call_and_keeps_diff(eng, fake_gen, tmp_path):
    pytest.importorskip("pyflakes")
    b, s, c, led = _base_then_static(eng, tmp_path, [GOOD], [])
    assert c.seen == [] and led.rows == [] and s["diff_sha256"] == b["diff_sha256"]
    assert s["static"]["reason"] == "CLEAN" and s["variant"] == "G1"


def test_static_repair_adopted_or_base_kept(eng, fake_gen, tmp_path):
    pytest.importorskip("pyflakes")
    b, s, c, led = _base_then_static(eng, tmp_path, [UNDEF], [GOOD])
    assert len(c.seen) == 1 and len(c.seen[0]) == 4 and "Missing" in c.seen[0][3]["content"]
    assert c.seen[0][2]["content"] == UNDEF                       # candidate that was applied
    assert s["static"]["repair_status"] == "ADOPTED" and s["diff_sha256"] != b["diff_sha256"]
    assert s["static"]["remaining_new_findings"] == 0 and led.rows[0]["kind"] == "static_repair"


def test_static_invalid_repair_never_lowers_applied(eng, fake_gen, tmp_path):
    pytest.importorskip("pyflakes")
    b, s, c, led = _base_then_static(eng, tmp_path / "x", [UNDEF], [BAD])
    assert s["status"] == "APPLIED" and s["diff_sha256"] == b["diff_sha256"]
    assert s["static"]["repair_status"] == "INVALID_KEPT_BASE"


def test_static_refuses_tampered_base(eng, fake_gen, tmp_path):
    pytest.importorskip("pyflakes")
    from benchmark.wp2.e2e.response_cache import ResponseCache
    item = {"task_id": "saleor-rc-x", "arm": "GOLD_HARD", "context": "C0", "replicate": "r1",
            "label": "GOLD_HARD__C0__r1"}
    eng.run_base_episode(item, FakeClient([UNDEF]), FakeLedger(), ResponseCache(tmp_path / "b"))
    (eng.ep_dir(item) / "final_diff.patch").write_text("x")
    with pytest.raises(eng.Stop):
        eng.run_static_episode({**item, "base_label": item["label"], "label": "GOLD_HARD__C0S__r1"},
                               FakeClient([GOOD]), FakeLedger(), ResponseCache(tmp_path / "s"))


def test_driver_outage_writes_no_outcome(eng, fake_gen, tmp_path):
    from benchmark.wp2.e2e_v22.transport import ProviderUnavailable

    class Br:
        def on_start(self):
            pass

        def on_unavailable(self, _r):
            return types.SimpleNamespace(action="STOP", reason="down", seconds=0)

        def on_success(self):
            pass

    def runner(_i):
        raise ProviderUnavailable("down", [])
    items = eng.base_items(["saleor-rc-x"])[:1]
    code, info = eng.drive(items, runner, FakeClient([]), FakeLedger(), Br(),
                           lambda i: sorted(PARENTS), 8, 100)
    assert code == eng.EXIT_OUTAGE and eng.ep_status(items[0]) is None


def test_plans_and_variants():
    items = core.CONTEXTS
    assert items == ("C0", "C2")
    m = load("m14r_run2", "scripts/wp2_m14r_run.py")
    b = m.base_items(["t1", "t2"])
    assert len(b) == 2 * 2 * 3 + 2 * 2 * 1
    assert {m.variant_of(i["label"]) for i in b} == {"G0", "G2"}
    s = m.static_items(["t1", "t2"])
    assert {m.variant_of(i["label"]) for i in s} == {"G1", "G3"}
    assert all(i["base_label"].replace("__C0__", "__C0S__").replace("__C2__", "__C2S__")
               == i["label"] for i in s)


# ================================================================ readiness / evaluation
def test_readiness_decisions(eng, monkeypatch):
    sets = {"saleor-rc-x": T}
    monkeypatch.setattr(eng, "eng_sets", lambda: sets)
    import benchmark.wp2.e2e.scopes as sc
    monkeypatch.setattr(sc, "build_arm_scopes", lambda t, a: {"editable": ["saleor/a.py"],
                                                              "excluded_large": [],
                                                              "excluded_budget": []})
    import scripts.wp2_m14a_evalcore as ec
    import scripts.wp2_m14a_evalcore_e1 as e1

    def run(neg, pos, diff="diff --git a/saleor/a.py b/saleor/a.py\n"):
        monkeypatch.setattr(eng, "scoped_gold_diff", lambda t, ed: diff)
        monkeypatch.setattr(ec, "evaluate_state_safe", lambda ev, t, lb, w: {"groups": neg,
                                                                             "junit_files": {}})
        monkeypatch.setattr(e1, "evaluate_state_e1", lambda ev, t, lb, w, **k: {
            "groups": pos, "e1_decision": "ALL_JUNIT_PRESENT"})
        ev = types.SimpleNamespace(materialize=lambda t, lb, d: ("/wt", "tree"))
        return eng.readiness_task("saleor-rc-x", ev)["decision"]
    fail = groups(f1=["failed"] * 3, f2=["failed"] * 3)
    assert run(fail, groups()) == "READY"
    assert run(fail, groups(u1=["passed", "failed", "passed"])) == "READY"
    assert run(groups(), groups()) == "NOT_READY_NEGATIVE_CONTROL_INVALID"
    assert run(fail, groups(), diff="") == "NOT_READY_EMPTY_SCOPED_GOLD"
    assert run(fail, fail) == "NOT_READY_SCOPED_GOLD_NOT_RESOLVED"


def test_readiness_infra_failure_is_resumable_stop(eng, monkeypatch):
    monkeypatch.setattr(eng, "design", lambda: {"population": {"candidate_tasks": ["saleor-rc-x"]}})
    eng.GUARD = eng.ROOT / "g.json"
    eng.write(eng.GUARD, eng.self_hash({"artifact_sha256": ""}))
    from scripts.wp2_m14a_evalcore import EvalInfraError

    def boom(_t):
        raise EvalInfraError("docker down")
    with pytest.raises(eng.Stop) as ei:
        eng.readiness(1, boom)
    assert ei.value.code == eng.EXIT_PREFLIGHT
    assert not (eng.READY / "saleor-rc-x" / "record.json").exists()


def _setup_eval(eng, monkeypatch, tmp_path):
    monkeypatch.setattr(eng, "verify_generation_freeze", lambda: [])
    monkeypatch.setattr(eng, "eng_sets", lambda: {"saleor-rc-x": T})
    rd = eng.READY / "saleor-rc-x"
    eng.write(rd / "record.json", eng.self_hash({"decision": "READY", "artifact_sha256": ""}))
    eng.write(rd / "negative_groups.json", eng.self_hash({
        "groups": groups(f1=["failed"] * 3, f2=["failed"] * 3, s1=["passed", "failed", "passed"]),
        "tree_sha": "t0", "artifact_sha256": ""}))
    src = eng.ROOT / "episodes/saleor-rc-x/GOLD_HARD__C0__r1"
    src.mkdir(parents=True)
    (src / "final_diff.patch").write_text("diff --git a/saleor/a.py b/saleor/a.py\n")
    items = [{"task_id": "saleor-rc-x", "diff_sha256": eng.EMPTY_DIFF_SHA,
              "source": "episodes/saleor-rc-x/GOLD_HARD__C0__r1/episode.json",
              "labels": ["PLACEBO_HARD__C0__r1"], "sources": ["s"]},
             {"task_id": "saleor-rc-x", "diff_sha256": "a" * 64,
              "source": "episodes/saleor-rc-x/GOLD_HARD__C0__r1/episode.json",
              "labels": ["GOLD_HARD__C0__r1"], "sources": ["s"]}]
    eng.write(eng.EVAL_PLAN, {"items": items, "n_unique_identities": 2})
    return items


def test_evaluate_empty_identity_uses_negative_control_and_robust_scoring(eng, monkeypatch, tmp_path):
    _setup_eval(eng, monkeypatch, tmp_path)
    seen = []
    eng.evaluate(4, evaluate_fn=lambda t, lb, w, d: seen.append(lb) or
                 {"groups": groups(), "e1_decision": "ALL_JUNIT_PRESENT"},
                 materialize_fn=lambda t, lb, d: ("/wt", "tree"))
    e0 = json.loads(eng.unique_path("saleor-rc-x", eng.EMPTY_DIFF_SHA).read_text())
    assert e0["evaluation_source"] == "READINESS_NEGATIVE_CONTROL"
    assert e0["strict"]["p2p_s_task"] == "FAIL" and e0["robust"]["p2p_s_task"] == "PASS"
    e1 = json.loads(eng.unique_path("saleor-rc-x", "a" * 64).read_text())
    assert e1["robust"]["resolved"] and seen == ["u_aaaaaaaaaaaa"] and eng.eval_complete() == 0


def test_evaluate_infra_and_apply_failures_are_distinct_stops(eng, monkeypatch, tmp_path):
    _setup_eval(eng, monkeypatch, tmp_path)
    from scripts.wp2_m14a_evalcore import EvalInfraError

    def infra(*_a):
        raise EvalInfraError("x")
    with pytest.raises(eng.Stop) as ei:
        eng.evaluate(4, evaluate_fn=infra, materialize_fn=lambda t, lb, d: ("/wt", "tree"))
    assert ei.value.code == eng.EXIT_EVAL_INFRA

    def noapply(*_a):
        raise ValueError("does not apply")
    with pytest.raises(eng.Stop) as ei:
        eng.evaluate(4, evaluate_fn=infra, materialize_fn=noapply)
    assert ei.value.code == eng.EXIT_INVARIANT


# ================================================================ plan / kit
PLAN = json.loads((P / "controller/plan_m14r_v1.json").read_text())


def test_plan_order_paid_boundary_and_isolation():
    ids = [p["id"] for p in PLAN["phases"]]
    assert ids == ["R00_KIT_SELFTEST", "R01_GUARD", "R02_PILOT_A_TAXONOMY", "R03_READINESS",
                   "R04_MEMBERSHIP", "R05_AUTH", "R06_DOCTOR_OFFLINE", "R07_DOCTOR_PAID",
                   "R08_FREEZE", "R09_GENERATE", "R10_STATIC", "R11_GENERATION_FREEZE",
                   "R12_EVAL_PLAN", "R13_EVALUATE", "R14_SUMMARY"]
    paid = [p["id"] for p in PLAN["phases"] if re.search(r"\b(generate|static)\b",
                                                          " ".join(p.get("command", [])))]
    assert paid == ["R09_GENERATE", "R10_STATIC"]
    assert ids.index("R05_AUTH") < ids.index("R08_FREEZE") < ids.index("R09_GENERATE")
    txt = json.dumps(PLAN)
    for bad in ("--tags", "pilot_a_v1/", "RMCSS_HARD", "AGENT_HARD", "M15"):
        assert bad not in txt
    for p in PLAN["phases"]:
        for pre in p.get("allowed_write_prefixes", []):
            assert pre.startswith(("research/wp2/m14r_v1/", "docs/WP2_M14R"))
        if p.get("kind") == "loop":
            assert isinstance(p["progress"], dict) and p["done_checks"]
    s = PLAN["settings"]
    assert s["state_file"] == "research/wp2/m14r_v1/controller_state.json"
    assert "EVAL_ERROR" in s["resumable_tokens"] and "M14R_INVARIANT" not in s["resumable_tokens"]


def test_zero_api_outside_generate_and_static():
    src = (P / "scripts/wp2_m14r_run.py").read_text()
    assert src.count("client.generate_messages(") == 1
    assert src.count("= _paid_setup()") == 2
    for fn in ("def readiness_task", "def evaluate(", "def summary", "def build_freeze"):
        body = src.split(fn, 1)[1].split("\ndef ", 1)[0]
        assert "generate_messages" not in body and "_paid_setup" not in body
    core_src = (P / "scripts/wp2_m14r_core.py").read_text()
    assert "import requests" not in core_src and "urllib" not in core_src
    assert "subprocess" not in core_src


def test_authorize_helper_refusals(tmp_path, monkeypatch):
    au = load("m14r_auth", "scripts/wp2_m14r_authorize.py")
    monkeypatch.setattr(au, "M", tmp_path / "m.json")
    monkeypatch.setattr(au, "D", tmp_path / "d.json")
    (tmp_path / "d.json").write_text(json.dumps({"artifact_sha256": "d" * 64}))
    (tmp_path / "m.json").write_text(json.dumps({"verdict": "POOL_INSUFFICIENT",
                                                 "artifact_sha256": "m"}))
    with pytest.raises(SystemExit):
        au.build("A", 1.0, "t")
    (tmp_path / "m.json").write_text(json.dumps({"verdict": "OK", "artifact_sha256": "m"}))
    with pytest.raises(SystemExit):
        au.build("A", 3.5, "t")
    r = au.build("A", 3.0, "t")
    q = dict(r, artifact_sha256="")
    assert r["artifact_sha256"] == au.sha_obj(q) and r["design_artifact_sha256"] == "d" * 64
