"""M14A corrected kit: behavioral, adversarial, zero-network tests (no Docker/WSL/API)."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import socket
import subprocess
import sys
import types
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src", P / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


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


def git(root: Path, *a: str) -> str:
    return subprocess.run(["git", *a], cwd=root, capture_output=True, text=True,
                          check=True).stdout.strip()


def init_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "t")
    (root / "README").write_text("x")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "init")
    return root


PLAN = json.loads((P / "controller/plan_m14a_pilot_a_v1.json").read_text())


# ================================================================ plan / controller
def test_plan_loop_phases_have_dict_progress_and_done_checks():
    for ph in PLAN["phases"]:
        if ph.get("kind") == "loop":
            assert isinstance(ph["progress"], dict) and "glob" in ph["progress"], ph["id"]
            assert ph["done_checks"]


def test_plan_paid_boundary_and_isolation():
    ids = [p["id"] for p in PLAN["phases"]]
    assert ids.index("P03_MEMBERSHIP") < ids.index("P04_AUTH") < ids.index("P08_FREEZE") \
        < ids.index("P09_GENERATE") < ids.index("P10_GENERATION_FREEZE") < ids.index("P11_EVAL_PLAN")
    txt = json.dumps(PLAN)
    for bad in ("--tags", "RMCSS_HARD", "AGENT_HARD", "M15", "M14R"):
        assert bad not in txt
    res = set(PLAN["settings"]["resumable_tokens"])
    assert {"READINESS_ENV_FAIL", "E2E_PROVIDER_OUTAGE", "EVAL_ERROR", "NOT_AUTHORIZED"} <= res
    assert "M14A_INVARIANT" not in res and "POOL_INSUFFICIENT" not in res
    gen = next(p for p in PLAN["phases"] if p["id"] == "P09_GENERATE")
    assert gen["exit_codes"]["75"] == "STOP:E2E_PROVIDER_OUTAGE"
    for p in PLAN["phases"]:
        for w in p.get("allowed_write_prefixes", []):
            assert w.startswith("research/wp2/pilot_a_v1/") or w == "docs/WP2_PILOT_A_V1_RESULT.md"


def ctl_repo(tmp_path, phases, final_actions=None, exports=None):
    root = init_repo(tmp_path / "r")
    plan = {"id": "T", "settings": {"state_file": "out/state.json", "report_dir": "out/reports",
                                    "git_commit": True, "git_push": False,
                                    "stop_commit_prefixes": ["out/"], "resumable_tokens": [],
                                    "exports": exports or {},
                                    "final_actions": final_actions or []},
            "phases": phases}
    (root / "plan.json").write_text(json.dumps(plan))
    ctl = load("ctl224", "scripts/wp2_ctl_v224.py")
    return root, ctl, ctl.Controller(root / "plan.json", root=root, kit_check=lambda: [])


def test_controller_runs_loop_with_plan_progress_format(tmp_path):
    prog = PLAN["phases"][2]["progress"]                     # P02 format, re-rooted
    add = ("import pathlib;d=pathlib.Path('out/x');d.mkdir(parents=True,exist_ok=True);"
           "(d/f'{len(list(d.glob(\"*.json\")))}.json').write_text('{}')")
    phases = [{"id": "L", "kind": "loop", "command": ["{python}", "-c", add], "fail_token": "F",
               "done_checks": [{"type": "count_files", "glob": "out/x/*.json", "op": ">=",
                                "value": 3}],
               "progress": {"glob": "out/x/*.json"}, "allowed_write_prefixes": ["out/"],
               "commit_message": "p"}]
    assert set(prog) == {"glob"}
    root, ctl, c = ctl_repo(tmp_path, phases)
    assert c.run() == ctl.EXIT_COMPLETE


def test_terminal_state_persisted_before_final_light(tmp_path):
    snap = ("import sys,json,shutil,pathlib;pathlib.Path('logs').mkdir(exist_ok=True);"
            "shutil.copy('out/state.json','logs/light_state.json')")
    phases = [{"id": "A", "builtin": "noop", "fail_token": "F"}]
    fa = [{"type": "commit", "prefixes": ["out/"], "message": "close"},
          {"type": "tag", "name": "t-result"}, {"type": "exports", "label": "R",
                                                "required": ["light"]}]
    root, ctl, c = ctl_repo(tmp_path, phases, fa, {"light": ["{python}", "-c", snap]})
    assert c.run() == ctl.EXIT_COMPLETE
    assert json.loads((root / "logs/light_state.json").read_text())["complete"] is True
    assert "t-result" in git(root, "tag")


def test_exact_tag_push_survives_divergent_unrelated_tag(tmp_path):
    ctl = load("ctl224b", "scripts/wp2_ctl_v224.py")
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    w = init_repo(tmp_path / "w")
    git(w, "remote", "add", "origin", str(remote))
    git(w, "tag", "old")
    git(w, "push", "-q", "origin", "main", "refs/tags/old")
    (w / "b").write_text("b")
    git(w, "add", "-A")
    git(w, "commit", "-q", "-m", "b")
    git(w, "tag", "-d", "old")
    git(w, "tag", "old")
    g = ctl.Git(w, enabled=True, push=True)
    g.tag("new", "m")
    assert g.push_tag("new") is True
    assert "refs/tags/new" in subprocess.run(["git", "ls-remote", "--tags", str(remote)],
                                             capture_output=True, text=True).stdout


def test_push_failure_after_commit_is_recoverable(tmp_path):
    phases = [{"id": "A", "builtin": "noop", "fail_token": "F",
               "post_actions": [{"type": "tag", "name": "t1"}, {"type": "push"}]}]
    root, ctl, c = ctl_repo(tmp_path, phases)
    data = json.loads((root / "plan.json").read_text())
    data["settings"]["git_push"] = True
    data["settings"]["resumable_tokens"] = ["POST_ACTION_FAILED"]
    (root / "plan.json").write_text(json.dumps(data))
    c = ctl.Controller(root / "plan.json", root=root, kit_check=lambda: [])
    c.git.push = lambda: False                                 # remote unreachable
    c.git.push_tag = lambda name: True
    assert c.run() == ctl.EXIT_STOPPED
    c2 = ctl.Controller(root / "plan.json", root=root, kit_check=lambda: [])
    c2.git.push = lambda: True
    c2.git.push_tag = lambda name: True
    assert c2.run() == ctl.EXIT_COMPLETE                        # tag one STOP-commit behind: ok


# ================================================================ readiness
class FakeHarness:
    STABLE = "STABLE_P2P"

    def __init__(self, *, c4=("DONE",), f2p=("t::f",), p2ps=("t::s",), candidates=5000,
                 p2pu_status="DONE", unstable=(), canary_ok=True, gold_applies=True):
        self.c4_statuses = list(c4)
        self.f2p, self.p2ps = list(f2p), list(p2ps)
        self.candidates = [f"u::n{i:05d}" for i in range(candidates)]
        self.p2pu_status, self.unstable = p2pu_status, set(unstable)
        self.canary = {"ok": canary_ok, "gold_applies": gold_applies}
        self.executed: list[list[str]] = []
        self.redirected = None
        self.gold_calls = 0

    def redirect(self, out):
        self.redirected = out

    def c4_run(self, tid, td):
        st = self.c4_statuses.pop(0) if len(self.c4_statuses) > 1 else self.c4_statuses[0]
        recs = [{"node_id": n, "v3_class": "BEHAVIORAL_F2P"} for n in self.f2p]
        recs += [{"node_id": n, "v3_class": "P2P_ONLY", "target_outcomes": ["passed"] * 3,
                  "parent_outcomes": ["passed"] * 3} for n in self.p2ps]
        return {"status": st, "era_key": "py39", "target_commit": "abc", "node_records": recs,
                "evidence_sha256": "e"}

    def p2pu_select(self, tid):
        disc = {"candidate_node_ids": self.candidates, "collect_rc": 0}
        return disc, self.candidates[:200]          # frozen V2/V3: outcome-blind cap200 SELECTION

    def p2pu_execute(self, tid, nodes, disc):
        self.executed.append(list(nodes))
        return {"status": self.p2pu_status, "class_counts": {},
                "node_classes": {n: ("FLAKY" if n in self.unstable else "STABLE_P2P")
                                 for n in nodes}}

    def gold_empty(self, tid, sets_path):
        self.gold_calls += 1
        sets = json.loads(Path(sets_path).read_text())
        assert tid in sets["tasks"]
        return dict(self.canary)


@pytest.fixture()
def rd(tmp_path, monkeypatch):
    m = load("rd", "scripts/wp2_m14a_readiness.py")
    root = tmp_path / "pilot"
    for k, v in {"ROOT": root, "READINESS": root / "readiness",
                 "FINAL": root / "pilot_final_membership.json",
                 "EVAL_SETS": root / "evaluator_only/sets.json"}.items():
        monkeypatch.setattr(m, k, v)
    return m


def test_readiness_ready_uses_cap200_selection_then_stability(rd):
    h = FakeHarness(candidates=5000, unstable={"u::n00003"})
    r = rd.classify_task("saleor-rc-x", h)
    assert r["ready"] and r["reasons"] == []
    assert len(h.executed) == 1 and len(h.executed[0]) == 200      # never the full 5000
    assert "u::n00003" not in r["p2p_u_cap200_stable_ids"]
    assert len(r["p2p_u_cap200_stable_ids"]) == 199
    assert set(r["p2p_u_cap200_stable_ids"]) <= set(h.executed[0])
    assert h.redirected == rd.READINESS and h.gold_calls == 1
    assert rd.hash_ok(json.loads(rd.rec_path("saleor-rc-x").read_text()))


@pytest.mark.parametrize("kw,reason,gold_calls", [
    ({"f2p": ()}, "NO_BEHAVIORAL_F2P", 0),
    ({"p2ps": (), "candidates": 0}, "P2P_UNDEFINED", 0),
    ({"canary_ok": False}, "GOLD_EMPTY_CHECK_FAILED", 1),
    ({"canary_ok": False, "gold_applies": False}, "GOLD_DIFF_NOT_APPLICABLE", 1),
    ({"c4": ("ENV_INSTALL_BLOCKED",)}, "C4_ENV_INSTALL_BLOCKED", 0),
])
def test_readiness_task_specific_non_readiness(rd, kw, reason, gold_calls):
    h = FakeHarness(**kw)
    r = rd.classify_task("saleor-rc-x", h)
    assert not r["ready"] and r["reasons"] == [reason] and h.gold_calls == gold_calls


def test_install_blocked_is_retried_once(rd):
    r = rd.classify_task("saleor-rc-x", FakeHarness(c4=("ENV_INSTALL_BLOCKED", "DONE")))
    assert r["ready"]


def test_p2pu_defined_by_selection_only_when_s_missing(rd):
    r = rd.classify_task("saleor-rc-x", FakeHarness(p2ps=()))
    assert r["ready"] and not r["p2p_s_defined"] and r["p2p_u_cap200_defined"]


@pytest.mark.parametrize("kw", [{"c4": ("ERROR",)}, {"c4": ("CLOCK_BLOCKED",)},
                                {"p2pu_status": "ENV_FAIL_P2PU"},
                                {"p2pu_status": "CLOCK_BLOCKED"}])
def test_infrastructure_failure_stops_and_writes_no_record(rd, monkeypatch, kw):
    monkeypatch.setattr(rd, "guard", lambda: {})
    monkeypatch.setattr(rd, "eligible", lambda: ["saleor-rc-x"])
    assert rd.readiness(1, FakeHarness(**kw)) == rd.EXIT_ENV
    assert not rd.rec_path("saleor-rc-x").exists()
    assert (rd.READINESS / "unexpected_error.json").exists()


def test_harness_redirect_never_targets_closed_roots(rd):
    h = rd.Harness.__new__(rd.Harness)
    h.c4 = types.SimpleNamespace(OUT_ROOT=Path("research/wp2/harness_v3_2026-09-26"),
                                 PER_TASK=None, PROGRESS_FILE=None)
    h.pu = types.SimpleNamespace(OUT_ROOT=Path("research/wp2/harness_v3_2026-09-26"))
    h.redirect(rd.READINESS)
    for p in (h.c4.OUT_ROOT, h.c4.PER_TASK, h.c4.PROGRESS_FILE, h.pu.OUT_ROOT):
        assert rd.READINESS in (p, *p.parents)


def test_corrupt_readiness_record_is_detected(rd, monkeypatch):
    rd.classify_task("saleor-rc-x", FakeHarness())
    monkeypatch.setattr(rd, "eligible", lambda: ["saleor-rc-x"])
    assert rd.readiness_check() == 0
    p = rd.rec_path("saleor-rc-x")
    d = json.loads(p.read_text())
    d["ready"] = False
    p.write_text(json.dumps(d))
    assert rd.readiness_check() == 1


def membership_env(rd, monkeypatch, tmp_path, not_ready):
    sel = json.loads((P / "research/wp2/pilot_v1_design/pilot_selection.json").read_text())
    ids = sel["pilot_a_tasks"] + sel["pilot_b_tasks"] + sel["reserve_order"]
    monkeypatch.setattr(rd, "eligible", lambda: ids)
    for t in ids:
        rd.classify_task(t, FakeHarness(f2p=() if t in not_ready else ("t::f",)))
    return sel


def test_membership_full_with_reserve_replacement(rd, monkeypatch, tmp_path):
    sel0 = json.loads((P / "research/wp2/pilot_v1_design/pilot_selection.json").read_text())
    drop = {sel0["pilot_a_tasks"][2]}
    sel = membership_env(rd, monkeypatch, tmp_path, drop)
    assert rd.membership() == 0
    f = json.loads(rd.FINAL.read_text())
    assert f["verdict"] == "FULL" and f["reserve_used"] == [sel["reserve_order"][0]]
    assert not set(f["A"]) & set(f["B"]) and len(f["A"]) == len(f["B"]) == 12
    sets = json.loads(rd.EVAL_SETS.read_text())
    assert set(sets["tasks"]) == set(f["A"]) | set(f["B"])


def test_membership_pool_insufficient_holds(rd, monkeypatch, tmp_path):
    sel0 = json.loads((P / "research/wp2/pilot_v1_design/pilot_selection.json").read_text())
    membership_env(rd, monkeypatch, tmp_path, set(sel0["pilot_a_tasks"][:5]))
    assert rd.membership() == rd.EXIT_POOL
    assert not rd.EVAL_SETS.exists()


# ================================================================ authorization
@pytest.fixture()
def run_env(tmp_path, monkeypatch):
    m = load("run", "scripts/wp2_m14a_run.py")
    proj = init_repo(tmp_path / "proj")
    design = json.loads((P / "research/wp2/pilot_v1_design/pilot_design_freeze_v1.json").read_text())
    tmpl = json.loads((P / "research/wp2/pilot_v1_design/PILOT_A_HUMAN_AUTH_TEMPLATE.json").read_text())
    dd = proj / "research/wp2/pilot_v1_design"
    dd.mkdir(parents=True)
    (dd / "pilot_design_freeze_v1.json").write_text(json.dumps(design))
    (dd / "PILOT_A_HUMAN_AUTH_TEMPLATE.json").write_text(json.dumps(tmpl))
    root = proj / "research/wp2/pilot_a_v1"
    mem = m.self_hash({"artifact": "pilot_final_membership", "artifact_sha256": "",
                       "verdict": "FULL", "A": [f"t{i}" for i in range(12)],
                       "B": [f"b{i}" for i in range(12)]})
    root.mkdir(parents=True)
    (root / "pilot_final_membership.json").write_text(json.dumps(mem))
    for k, v in {"PROJECT": proj, "ROOT": root, "DESIGN": dd / "pilot_design_freeze_v1.json",
                 "AUTH_TEMPLATE": dd / "PILOT_A_HUMAN_AUTH_TEMPLATE.json",
                 "FINAL": root / "pilot_final_membership.json",
                 "AUTH": root / "human_authorization.json",
                 "LEDGER": root / "ledger/pilot_a_spend.jsonl",
                 "STOP_FLAG": proj / "logs/STOP.flag"}.items():
        monkeypatch.setattr(m, k, v)
    au = load("auth", "scripts/wp2_m14a_authorize.py")
    for k, v in {"P": proj, "R": root, "D": dd / "pilot_design_freeze_v1.json",
                 "T": dd / "PILOT_A_HUMAN_AUTH_TEMPLATE.json",
                 "M": root / "pilot_final_membership.json",
                 "OUT": root / "human_authorization.json"}.items():
        monkeypatch.setattr(au, k, v)
    git(proj, "add", "-A")
    git(proj, "commit", "-q", "-m", "membership")
    return m, au, proj, root


def write_auth(m, au, proj, mutate=None, commit=True):
    a = au.build("Ahmed", 1.0, "2026-09-29T00:00:00Z")
    if mutate:
        mutate(a)
        a["artifact_sha256"] = ""
        a["artifact_sha256"] = au.sha_obj(copy.deepcopy(a))
    m.AUTH.write_text(json.dumps(a))
    if commit:
        git(proj, "add", "-A")
        git(proj, "commit", "-q", "-m", "auth")


def test_auth_valid_passes(run_env):
    m, au, proj, _ = run_env
    write_auth(m, au, proj)
    assert m.validate_auth()["authorized_by"] == "Ahmed"


@pytest.mark.parametrize("mutate,commit", [
    (None, False),                                                     # uncommitted
    (lambda a: a.update(max_generation_spend_usd=1.5), True),          # cap > $1
    (lambda a: a.update(provider="other/route"), True),                # wrong provider
    (lambda a: a.update(allow_fallbacks=True), True),
    (lambda a: a.update(design_artifact_sha256="0" * 64), True),       # wrong design
    (lambda a: a.update(membership_artifact_sha256="0" * 64), True),   # wrong membership
    (lambda a: a.update(m13_auth_template_sha256="0" * 64), True),     # not bound to template
    (lambda a: a.update(approval_token="yes"), True),
])
def test_auth_refusals(run_env, mutate, commit):
    m, au, proj, _ = run_env
    write_auth(m, au, proj, mutate, commit)
    with pytest.raises(m.Stop) as ei:
        m.validate_auth()
    assert ei.value.code == m.EXIT_AUTH


def test_auth_missing_and_tampered(run_env):
    m, au, proj, _ = run_env
    with pytest.raises(m.Stop):
        m.validate_auth()
    write_auth(m, au, proj)
    d = json.loads(m.AUTH.read_text())
    d["max_generation_spend_usd"] = 0.5                                # edit without re-hash
    m.AUTH.write_text(json.dumps(d))
    git(proj, "commit", "-qam", "tamper")
    with pytest.raises(m.Stop):
        m.validate_auth()


def test_authorize_helper_refuses_bad_cap(run_env):
    _m, au, _proj, _ = run_env
    with pytest.raises(SystemExit):
        au.build("x", 1.01, "u")
    with pytest.raises(SystemExit):
        au.build("x", 0.0, "u")


# ================================================================ generation driver
class FakeClient:
    def __init__(self):
        self.network_attempts = 0
        self.ctx = {}

    def set_context(self, **kw):
        self.ctx = kw

    def check_hold(self):
        pass


class Breaker:
    def __init__(self, stop_after=10):
        self.n, self.stop_after = 0, stop_after

    def on_start(self):
        pass

    def on_success(self):
        self.n = 0

    def on_unavailable(self, _msg):
        self.n += 1
        return types.SimpleNamespace(action="STOP" if self.n > self.stop_after else "COOLDOWN",
                                     seconds=900, reason="outage")


def gen_setup(m, tmp_path, n_tasks=2):
    items = m.generation_items([f"saleor-rc-{i:012d}" for i in range(n_tasks)])
    ledger = m.Ledger(m.LEDGER, 1.0)
    return items, ledger


def make_episode_fn(m, script):
    """script: {(task,label): [exc | 'PAY_THEN_OUTAGE' | status]}"""
    from benchmark.wp2.e2e_v22.transport import ProviderUnavailable

    def fn(task_id, arm, client, ledger, cache, root, subdir="episodes", label=None):
        seq = script.get((task_id, label), [])
        act = seq.pop(0) if seq else "APPLIED"
        cfile = cache / "initial.json"
        if act == "PAY_THEN_OUTAGE":
            if not cfile.exists():                                   # first attempt pays
                ledger.record({"arm": arm, "cost_usd": 0.004, "prompt_tokens": 100,
                               "completion_tokens": 10})
                cache.mkdir(parents=True, exist_ok=True)
                cfile.write_text("{}")
            raise ProviderUnavailable("429 on repair", [])
        if isinstance(act, Exception):
            raise act
        if not cfile.exists():
            ledger.record({"arm": arm, "cost_usd": 0.004, "prompt_tokens": 100,
                           "completion_tokens": 10})
        p = root / subdir / task_id / label / "episode.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"task_id": task_id, "arm": arm, "status": act,
                                 "editable_set": ["a.py"], "calls": []}))
        return {"status": act, "editable_set": ["a.py"]}
    return fn


def run_drive(m, items, ledger, fn, breaker=None, scope=lambda i: ["a.py"], cur=None, max_new=99):
    sleeps = []
    code, info = m.drive(items, FakeClient(), ledger, breaker or Breaker(), fn,
                         lambda i: m.cache_dir(i), scope, cur or scope, max_new, 1e9,
                         clock=lambda: 0.0, sleep=sleeps.append)
    return code, info, sleeps


def test_outage_after_paid_initial_resumes_without_double_billing(run_env, tmp_path):
    m, _au, _proj, _ = run_env
    items, ledger = gen_setup(m, tmp_path, 1)
    first = items[0]
    fn = make_episode_fn(m, {(first["task_id"], first["label"]): ["PAY_THEN_OUTAGE",
                                                                  "PAY_THEN_OUTAGE"]})
    code, info, sleeps = run_drive(m, items, ledger, fn)
    assert code == 0 and info["terminal"] == len(items)
    rows = [json.loads(x) for x in m.LEDGER.read_text().splitlines()]
    assert len(rows) == len(items)                     # the interrupted episode billed once
    assert sum(sleeps) == 1800
    assert all(json.loads(m.ep_path(i).read_text())["status"] != "GENERATION_FAIL" for i in items)


def test_persistent_outage_writes_pending_not_outcome(run_env, tmp_path):
    from benchmark.wp2.e2e_v22.transport import ProviderUnavailable
    m, _au, _proj, _ = run_env
    items, ledger = gen_setup(m, tmp_path, 1)
    first = items[0]
    fn = make_episode_fn(m, {(first["task_id"], first["label"]):
                             [ProviderUnavailable("x", [])] * 9})
    code, _info, _ = run_drive(m, items, ledger, fn, Breaker(stop_after=3))
    assert code == m.EXIT_OUTAGE and not m.ep_path(first).exists()
    assert (m.ROOT / "transport/pending.json").exists()


def test_cache_namespace_never_crosses_task_arm_replicate(run_env, tmp_path):
    m, _au, _proj, _ = run_env
    items, _ = gen_setup(m, tmp_path, 12)
    dirs = {m.cache_dir(i) for i in items}
    assert len(items) == 48 and len(dirs) == 48
    assert all(i["task_id"] in str(m.cache_dir(i)) and i["label"] in str(m.cache_dir(i))
               for i in items)


@pytest.mark.parametrize("exc_name,code", [("HoldActiveV22", 3), ("RequestRejected", 76),
                                           ("RuntimeError", 78)])
def test_other_failures_never_create_episodes(run_env, tmp_path, exc_name, code):
    import benchmark.wp2.e2e_v22.transport as tr
    m, _au, _proj, _ = run_env
    items, ledger = gen_setup(m, tmp_path, 1)
    first = items[0]
    exc = {"HoldActiveV22": tr.HoldActiveV22("h"), "RequestRejected": tr.RequestRejected("402"),
           "RuntimeError": RuntimeError("docker")}[exc_name]
    fn = make_episode_fn(m, {(first["task_id"], first["label"]): [exc]})
    c, _i, _ = run_drive(m, items, ledger, fn)
    assert c == code and not m.ep_path(first).exists()


def test_budget_cap_and_scope_drift_and_forbidden(run_env, tmp_path):
    m, _au, _proj, _ = run_env
    items, _ = gen_setup(m, tmp_path, 1)
    led = m.Ledger(m.LEDGER, 0.05)
    c, _i, _ = run_drive(m, items, led, make_episode_fn(m, {}))
    assert c == m.EXIT_BUDGET
    led = m.Ledger(m.LEDGER, 1.0)
    c, _i, _ = run_drive(m, items, led, make_episode_fn(m, {}), cur=lambda i: ["b.py"])
    assert c == m.EXIT_INVARIANT
    p = m.ep_path(items[1])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"status": "GENERATION_FAIL"}))
    c, _i, _ = run_drive(m, items, led, make_episode_fn(m, {}))
    assert c == m.EXIT_INVARIANT


# ================================================================ evaluation identity
def put_ep(m, item, status, diff="d"):
    p = m.ep_path(item)
    p.parent.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(diff.encode()).hexdigest()
    p.write_text(json.dumps({"task_id": item["task_id"], "arm": item["arm"], "status": status,
                             "diff_sha256": sha if status == "APPLIED" else "",
                             "editable_set": ["a.py"], "edited_files": ["a.py"], "calls": []}))
    (p.parent / "final_diff.patch").write_text(diff)
    return sha


def test_eval_plan_identity(run_env, tmp_path, monkeypatch):
    m, _au, _proj, _ = run_env
    items = m.generation_items(["saleor-rc-a", "saleor-rc-b"])
    monkeypatch.setattr(m, "load", lambda p: {"items": items} if p == m.GEN_PLAN
                        else json.loads(Path(p).read_text()))
    for i in items:
        put_ep(m, i, "APPLIED", "\n")                  # identical no-op diff everywhere
    plan = m.build_eval_plan()
    assert len(plan) == 2                              # one per task, never shared across tasks
    assert all(len(x["also_sources"]) == 3 for x in plan)
    assert m.unique_path("saleor-rc-a", plan[0]["diff_sha256"]) != \
        m.unique_path("saleor-rc-b", plan[0]["diff_sha256"])
    with pytest.raises(m.Stop):
        m.unique_path("saleor-rc-a", "abc")


def test_corrupt_evaluation_record_stops(run_env):
    m, _au, _proj, _ = run_env
    p = m.unique_path("saleor-rc-a", "a" * 64)
    p.parent.mkdir(parents=True, exist_ok=True)
    rec = m.self_hash({"task_id": "saleor-rc-a", "diff_sha256": "a" * 64, "resolved": False,
                       "evaluation_sha256": ""}, "evaluation_sha256")
    p.write_text(json.dumps(rec))
    assert m.record_state(p) == "VALID"
    rec["resolved"] = True
    p.write_text(json.dumps(rec))
    assert m.record_state(p) == "CORRUPT"


# ================================================================ summary / gates
def test_summary_gates_direction_and_ledger_tokens(run_env, tmp_path, monkeypatch):
    m, _au, _proj, _ = run_env
    tasks = [f"saleor-rc-{i:012d}" for i in range(12)]
    items = m.generation_items(tasks)
    fin = json.loads(m.FINAL.read_text())
    fin["A"] = tasks
    m.FINAL.write_text(json.dumps(fin))
    monkeypatch.setattr(m, "load", lambda p: {"items": items} if p == m.GEN_PLAN
                        else json.loads(Path(p).read_text()))
    monkeypatch.setattr(m, "verify_generation_freeze", lambda: [])
    monkeypatch.setattr(m, "eval_complete", lambda: 0)
    gold_resolved = {(tasks[0], "r1"), (tasks[1], "r1"), (tasks[2], "r2")}
    for i in items:
        sha = put_ep(m, i, "APPLIED", f"{i['task_id']}{i['label']}")
        res = i["arm"] == "GOLD_HARD" and (i["task_id"], i["replicate"]) in gold_resolved
        p = m.unique_path(i["task_id"], sha)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(m.self_hash({"task_id": i["task_id"], "diff_sha256": sha,
                                             "f2p_task": "PASS" if res else "FAIL",
                                             "p2p_s_task": "PASS", "p2p_u200_task": "PASS",
                                             "resolved": res, "evaluation_sha256": ""},
                                            "evaluation_sha256")))
    m.LEDGER.parent.mkdir(parents=True, exist_ok=True)
    m.LEDGER.write_text("\n".join(json.dumps({"arm": a, "cost_usd": 0.01, "prompt_tokens": 7,
                                              "completion_tokens": 3})
                                  for a in ("GOLD_HARD", "PLACEBO_HARD")) + "\n")
    s = m.compute_summary()
    assert s["per_arm"]["GOLD_HARD"]["resolved"] == 3
    assert s["task_direction"] == {"gold_gt_placebo": 3, "placebo_gt_gold": 0, "ties": 9}
    assert s["gates"]["A5_separation"] and s["token"] == "PILOT_A_PASS"
    assert s["per_arm"]["GOLD_HARD"]["provider_reported_tokens"] == 10
    assert s["auto_execution_of_M14R_or_M15"] is False
    assert "not an RM-CSS-vs-Agent" in s["mandatory_wording"]
    # an out-of-scope edit is an instrument failure
    e = json.loads(m.ep_path(items[0]).read_text())
    e["edited_files"] = ["evil.py"]
    m.ep_path(items[0]).write_text(json.dumps(e))
    s2 = m.compute_summary()
    assert s2["token"] == "PILOT_A_INSTRUMENT_FIX"


# ================================================================ evaluator core
def fake_ev(tmp_path, groups, xml_present=True, done=True):
    calls = []
    ev = types.SimpleNamespace(
        PROJECT=P, DISTRO="d", REPS=3, NOFILE_HARD=1, STATE_TIMEOUT_S=10, WSL_CACHE="/c",
        E2E_ROOT=tmp_path, fresh_db_name=lambda a, b: "db", ensure_postgres_running=lambda: None,
        ensure_fresh_db=lambda db: None, drop_db=lambda db: None,
        load_evaluator_sets=lambda: {"tasks": {"saleor-rc-012472eb8482": groups}},
        wsl=lambda s, *a, **k: types.SimpleNamespace(
            stdout="<testsuite/>" if (xml_present and "cat" in s) else "__NO_FILE__"))
    return ev, calls


def test_evalcore_skips_empty_group_and_raises_on_missing_junit(tmp_path, monkeypatch):
    ec = load("ec", "scripts/wp2_m14a_evalcore.py")
    import benchmark.wp2.harness_v3 as hv
    import benchmark.wp2.oracle_confirmation as oc
    monkeypatch.setattr(hv, "target_manifests", lambda t: [], raising=False)
    monkeypatch.setattr(hv, "lock_install_script", lambda w, m: ("i", "m", None), raising=False)
    monkeypatch.setattr(hv, "locked_dev_install", lambda t: "d", raising=False)
    monkeypatch.setattr(oc, "parse_junit_with_failures", lambda x: ({}, {}), raising=False)
    import benchmark.wp2.e2e.scopes as sc
    monkeypatch.setattr(sc, "commits_of", lambda t: ("p", "t"))
    scripts = []

    def fake_run(args, **kw):
        scripts.append((args, kw.get("input", b"")))
        return types.SimpleNamespace(returncode=0, stdout="E2E_DONE", stderr="")
    monkeypatch.setattr(ec.subprocess, "run", fake_run)
    groups = {"behavioral_f2p_node_ids": ["t::f"], "p2p_s_node_ids": [],
              "p2p_u_cap200_stable_ids": []}
    ev, _ = fake_ev(tmp_path, groups)
    out = ec.evaluate_state_safe(ev, "saleor-rc-012472eb8482", "u_abc", "/wt/x")
    assert out["skipped_empty_groups"] == ["U"]
    runs = [inp for a, inp in scripts if a[-1].endswith(".m14a_runs.sh")]
    assert runs and b"_U_" not in runs[0] and b"_C_" in runs[0]
    ev2, _ = fake_ev(tmp_path, groups, xml_present=False)
    with pytest.raises(ec.EvalInfraError):
        ec.evaluate_state_safe(ev2, "saleor-rc-012472eb8482", "u_abc", "/wt/x")


def test_canary_ok_truth_table():
    ec = load("ec2", "scripts/wp2_m14a_evalcore.py")
    pos = {"tree_matches": True, "f2p_task": "PASS", "p2p_s_task": "PASS", "p2p_u200_task": "UNDEFINED"}
    neg = {"f2p_task": "FAIL", "p2p_s_task": "PASS", "p2p_u200_task": "PASS"}
    assert ec.canary_ok(pos, neg)
    assert not ec.canary_ok(dict(pos, tree_matches=False), neg)
    assert not ec.canary_ok(dict(pos, p2p_s_task="FAIL"), neg)
    assert not ec.canary_ok(pos, dict(neg, f2p_task="PASS"))
    assert not ec.canary_ok(pos, dict(neg, p2p_u200_task="FAIL"))


def test_sets_artifact_verifies_with_frozen_loader(tmp_path, monkeypatch):
    ec = load("ec3", "scripts/wp2_m14a_evalcore.py")
    import benchmark.wp2.e2e.evaluator_sets as es
    p = tmp_path / "s.json"
    p.write_text(json.dumps(ec.sets_artifact({"t": {"behavioral_f2p_node_ids": []}}, "v")))
    monkeypatch.setattr(es, "EVAL_PATH", p)
    monkeypatch.setattr(es, "_CACHE", None)
    assert "t" in es.load_evaluator_sets()["tasks"]


# ================================================================ LIGHT profile
def test_light_profile_puts_result_first_and_excludes_bulk():
    prof = json.loads((P / "controller/light_profile_m14a.json").read_text())
    assert prof["include"][0] == "docs/WP2_PILOT_A_V1_RESULT.md"
    assert prof["include"].index("research/wp2/pilot_a_v1/controller_state.json") < 3
    for ex in ("*/junit/*", "*/p2pu_v3_junit/*", "*/cache_namespaces/*"):
        assert ex in prof["exclude"]


def test_kit_is_zero_api_except_generate_and_read_only_doctor():
    for f in ("scripts/wp2_m14a_readiness.py", "scripts/wp2_m14a_evalcore.py",
              "scripts/wp2_m14a_authorize.py"):
        t = (P / f).read_text().lower()
        assert "openrouter.ai" not in t and "urllib.request" not in t and "run_episode" not in t
