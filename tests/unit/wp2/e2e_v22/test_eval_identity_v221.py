"""Amendment v2.2.1: evaluation identity = (task_id, full diff_sha256). Zero API."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import socket
import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT / "scripts"))

NOOP = hashlib.sha256(b"no-op diff identity").hexdigest()
SEVEN = [f"saleor-rc-{i:012x}" for i in range(7)]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, PROJECT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(socket.socket, "connect", boom)


@pytest.fixture()
def env(tmp_path, monkeypatch):
    root = tmp_path / "v22"
    ev = load("wp2_e2e_v22_evaluate")
    fz = load("wp2_e2e_v22_freeze")
    sm = load("wp2_e2e_v22_summary")
    for m in (ev, fz, sm):
        monkeypatch.setattr(m, "V22_ROOT", root)
    monkeypatch.setattr(fz, "GEN_FREEZE_FILE", root / "generation_freeze_v22.json")
    monkeypatch.setattr(fz, "AMENDMENT_FILE", root / "evaluation_instrument_amendment_v221.json")
    v21 = ev.load_v21_evaluate()
    v21.V21_ROOT = root
    return root, ev, fz, sm, v21


def episode(root: Path, sub: str, task: str, label: str, arm: str, sha: str,
            status: str = "APPLIED", diff: str = "\n") -> Path:
    d = root / sub / task / label
    d.mkdir(parents=True, exist_ok=True)
    rec = {"task_id": task, "arm": arm, "status": status, "diff_sha256": sha, "calls": []}
    (d / "episode.json").write_text(json.dumps(rec))
    (d / "final_diff.patch").write_text(diff, newline="")
    return d


class FakeEvaluator:
    """Stands in for materialize/evaluate_state/score; outcome depends on the task."""

    def __init__(self, passing: set[str]) -> None:
        self.passing = passing
        self.calls: list[tuple[str, str, str]] = []

    def materialize(self, task, label, diff):
        self.calls.append((task, label, diff))
        return f"/wt/{task}_{label}", f"tree-{task}"

    def evaluate_state(self, task, label, wt):
        assert wt == f"/wt/{task}_{label}"
        return {"groups": {"f2p": task}}

    def score(self, task, label, groups):
        assert groups["f2p"] == task
        ok = task in self.passing
        return {"f2p_task": "PASS" if ok else "FAIL", "p2p_s_task": "PASS",
                "p2p_u200_task": "PASS", "resolved": ok, "flaky_under_patch": []}

    def run(self, ev, plan, n=0):
        return ev.run_eval(plan, n, self.materialize, self.evaluate_state, self.score)


def test_seven_tasks_same_noop_diff_are_seven_independent_evaluations(env):
    root, ev, fz, _sm, v21 = env
    for t in SEVEN:
        episode(root, "episodes", t, "PLACEBO_HARD", "PLACEBO_HARD", NOOP)
    plan = v21.build_plan()
    assert plan["n_unique_diffs"] == 7
    assert ev.identity_problems(plan) == []
    assert ev.cross_task_groups(plan) == {NOOP: sorted(SEVEN)}
    fake = FakeEvaluator(passing={SEVEN[0]})
    assert fake.run(ev, plan) == 7
    assert sorted(c[0] for c in fake.calls) == sorted(SEVEN)
    paths = {fz.unique_eval_path(root, t, NOOP) for t in SEVEN}
    assert len(paths) == 7 and all(p.exists() for p in paths)
    for t in SEVEN:
        rec = json.loads(fz.unique_eval_path(root, t, NOOP).read_text())
        assert rec["task_id"] == t and rec["diff_sha256"] == NOOP
        assert rec["resolved"] is (t == SEVEN[0])
    assert fake.run(ev, plan) == 0  # idempotent


def test_same_task_same_diff_across_arms_and_variance_is_evaluated_once(env):
    root, ev, fz, _sm, v21 = env
    sha = "a" * 64
    episode(root, "episodes", "t1", "GOLD_HARD", "GOLD_HARD", sha, diff="x\n")
    episode(root, "episodes", "t1", "RMCSS_HARD", "RMCSS_HARD", sha, diff="x\n")
    episode(root, "variance", "t1", "var_r1", "GOLD_HARD", sha, diff="x\n")
    plan = v21.build_plan()
    assert plan["n_unique_diffs"] == 1
    item = plan["items"][0]
    assert len(item.get("also_sources", [])) == 2
    fake = FakeEvaluator(passing={"t1"})
    assert fake.run(ev, plan) == 1 and len(fake.calls) == 1
    rec = json.loads(fz.unique_eval_path(root, "t1", sha).read_text())
    assert len(rec["sources"]) == 3


def test_same_task_hashes_sharing_sha8_do_not_collide(env):
    root, ev, fz, _sm, v21 = env
    h1, h2 = "deadbeef" + "0" * 56, "deadbeef" + "1" * 56
    episode(root, "episodes", "t1", "GOLD_HARD", "GOLD_HARD", h1, diff="a\n")
    episode(root, "episodes", "t1", "RMCSS_HARD", "RMCSS_HARD", h2, diff="b\n")
    plan = v21.build_plan()
    assert plan["n_unique_diffs"] == 2 and ev.identity_problems(plan) == []
    fake = FakeEvaluator(passing=set())
    assert fake.run(ev, plan) == 2
    assert fz.unique_eval_path(root, "t1", h1) != fz.unique_eval_path(root, "t1", h2)
    assert {c[2] for c in fake.calls} == {"a\n", "b\n"}  # each identity got its own diff


def test_identity_problems_reject_short_hash_and_duplicates(env):
    _root, ev, _fz, _sm, _v21 = env
    assert ev.identity_problems({"items": [{"task_id": "t", "diff_sha256": "abc"}]})
    dup = {"items": [{"task_id": "t", "diff_sha256": "a" * 64}] * 2}
    assert ev.identity_problems(dup)
    with pytest.raises(ValueError):
        _fz = load("wp2_e2e_v22_freeze")
        _fz.unique_eval_path(Path("."), "t", "abc")


def test_summary_never_borrows_another_tasks_score(env):
    root, ev, _fz, sm, v21 = env
    episode(root, "episodes", SEVEN[0], "PLACEBO_HARD", "PLACEBO_HARD", NOOP)
    episode(root, "episodes", SEVEN[1], "PLACEBO_HARD", "PLACEBO_HARD", NOOP)
    plan = v21.build_plan()
    FakeEvaluator(passing={SEVEN[0]}).run(ev, {"items": plan["items"][:1]})
    ran = plan["items"][0]["task_id"]
    s21 = load("wp2_e2e_smoke_v21_summary")
    s21.V21_ROOT = root
    per = sm.summarize_v22(s21, [SEVEN[0], SEVEN[1]])
    pl = per["PLACEBO_HARD"]
    assert pl["applied"] == 2
    assert pl["applied_without_evaluation"] == 1   # the other task is NOT filled in
    assert pl["resolved"] == (1 if ran == SEVEN[0] else 0)


def test_summary_rejects_misfiled_evaluation(env):
    root, _ev, fz, sm, _v21 = env
    p = fz.unique_eval_path(root, "t1", NOOP)
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"task_id": "t2", "diff_sha256": NOOP}))
    with pytest.raises(RuntimeError):
        sm.evals_by_identity(root)


def test_eval_complete_requires_all_seven(env, monkeypatch):
    root, ev, fz, _sm, v21 = env
    monkeypatch.setattr(fz, "planned_main", lambda: [(t, "PLACEBO_HARD", "PLACEBO_HARD")
                                                     for t in SEVEN])
    monkeypatch.setattr(fz, "planned_variance", lambda: [])
    for t in SEVEN:
        episode(root, "episodes", t, "PLACEBO_HARD", "PLACEBO_HARD", NOOP)
    plan = v21.persist_plan()
    FakeEvaluator(set()).run(ev, plan, n=6)
    assert fz.eval_complete() == 1
    FakeEvaluator(set()).run(ev, plan)
    assert fz.eval_complete() == 0


# ------------------------------------------------------------ amendment verification
def make_amendment(fz, root: Path, freeze_sha: str, gen_sha: str, changed: dict) -> dict:
    body = {"artifact": "evaluation_instrument_amendment_v221", "base_freeze_sha256": freeze_sha,
            "generation_freeze_sha256": gen_sha, "changed_files": changed}
    am = dict(body, amendment_sha256=fz.json_sha256(body))
    (root / "evaluation_instrument_amendment_v221.json").write_text(json.dumps(am))
    return am


def make_gen_freeze(fz, root: Path) -> str:
    d = episode(root, "episodes", "t1", "GOLD_HARD", "GOLD_HARD", NOOP)
    rel = (d / "episode.json").relative_to(root).as_posix()
    body = {"artifact": "generation_freeze_v22", "n_episodes": 1,
            "episodes": {rel: {"episode_file_sha256": fz.norm_sha256(d / "episode.json")}}}
    body["generation_freeze_sha256"] = fz.json_sha256(body)
    (root / "generation_freeze_v22.json").write_text(json.dumps(body))
    return body["generation_freeze_sha256"]


FREEZE = {"freeze_sha256": "F" * 64,
          "code_sha256": {"scripts/wp2_e2e_v22_evaluate.py": "old-eval",
                          "scripts/wp2_e2e_v22_generate.py": "old-gen"}}


def test_amendment_valid(env):
    root, _ev, fz, _sm, _v21 = env
    gen = make_gen_freeze(fz, root)
    make_amendment(fz, root, FREEZE["freeze_sha256"], gen,
                   {"scripts/wp2_e2e_v22_evaluate.py": {"old": "old-eval", "new": "new-eval"}})
    changed, reasons = fz.load_amendment(FREEZE)
    assert reasons == [] and changed["scripts/wp2_e2e_v22_evaluate.py"]["new"] == "new-eval"


@pytest.mark.parametrize("case,token", [
    ("non_amendable", "AMENDMENT_TOUCHES_NON_AMENDABLE"),
    ("old_mismatch", "AMENDMENT_OLD_HASH_MISMATCH"),
    ("other_freeze", "AMENDMENT_BOUND_TO_OTHER_FREEZE"),
    ("other_gen", "AMENDMENT_BOUND_TO_OTHER_GENERATION_FREEZE"),
    ("tampered", "AMENDMENT_SELF_HASH_MISMATCH"),
    ("episode_changed", "GENERATION_EVIDENCE_CHANGED"),
])
def test_amendment_fails_closed(env, case, token):
    root, _ev, fz, _sm, _v21 = env
    gen = make_gen_freeze(fz, root)
    changed = {"scripts/wp2_e2e_v22_evaluate.py": {"old": "old-eval", "new": "new-eval"}}
    freeze_sha, gen_sha = FREEZE["freeze_sha256"], gen
    if case == "non_amendable":
        changed = {"scripts/wp2_e2e_v22_generate.py": {"old": "old-gen", "new": "x"}}
    if case == "old_mismatch":
        changed = {"scripts/wp2_e2e_v22_evaluate.py": {"old": "zzz", "new": "new-eval"}}
    if case == "other_freeze":
        freeze_sha = "E" * 64
    if case == "other_gen":
        gen_sha = "0" * 64
    make_amendment(fz, root, freeze_sha, gen_sha, changed)
    if case == "tampered":
        p = root / "evaluation_instrument_amendment_v221.json"
        am = json.loads(p.read_text())
        am["changed_files"]["scripts/wp2_e2e_v22_evaluate.py"]["new"] = "evil"
        p.write_text(json.dumps(am))
    if case == "episode_changed":
        p = root / "episodes/t1/GOLD_HARD/episode.json"
        p.write_text(p.read_text().replace("APPLIED", "NO_SCOPE"))
    _changed, reasons = fz.load_amendment(FREEZE)
    assert any(r.startswith(token) for r in reasons), reasons


def test_verify_accepts_only_amended_new_hashes(env, monkeypatch, capsys, tmp_path):
    root, _ev, fz, _sm, _v21 = env
    sets = tmp_path / "sets.json"
    sets.write_text("{}")
    freeze = dict(FREEZE, scopes_semantic_sha256={}, evaluator_sets_sha256=fz.norm_sha256(sets),
                  policy={"p": 1}, env_identity={"era_images": {}, "postgres": {"image_id": "pg"}})
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(fz, "FREEZE_FILE", root / "smoke_v22_freeze.json")
    (root / "smoke_v22_freeze.json").write_text(json.dumps(freeze))
    monkeypatch.setattr(fz, "EVALUATOR_SETS", sets)
    monkeypatch.setattr(fz, "scope_hashes", lambda: ({}, []))
    monkeypatch.setattr(fz, "policy", lambda: {"p": 1})
    monkeypatch.setattr(fz, "env_identity", lambda *a: {"errors": [], "era_images": {},
                                                        "postgres": {"image_id": "pg"}})
    now = {"scripts/wp2_e2e_v22_evaluate.py": "new-eval", "scripts/wp2_e2e_v22_generate.py": "old-gen"}
    monkeypatch.setattr(fz, "code_hashes", lambda: dict(now))
    assert fz.verify() == 1  # no amendment yet -> drift
    gen = make_gen_freeze(fz, root)
    make_amendment(fz, root, FREEZE["freeze_sha256"], gen,
                   {"scripts/wp2_e2e_v22_evaluate.py": {"old": "old-eval", "new": "new-eval"}})
    assert fz.verify() == 0
    assert "amendment v2.2.1" in capsys.readouterr().out
    now["scripts/wp2_e2e_v22_generate.py"] = "changed-gen"  # a non-amended file drifts
    assert fz.verify() == 1
    now["scripts/wp2_e2e_v22_generate.py"] = "old-gen"
    now["scripts/wp2_e2e_v22_evaluate.py"] = "some-other-edit"  # amended file edited again
    assert fz.verify() == 1


def test_summary_v22_equals_v21_rules_when_diffs_are_task_unique(env):
    root, ev, _fz, sm, v21 = env
    episode(root, "episodes", "t1", "GOLD_HARD", "GOLD_HARD", "1" * 64, diff="a\n")
    episode(root, "episodes", "t2", "GOLD_HARD", "GOLD_HARD", "2" * 64, diff="b\n")
    episode(root, "episodes", "t2", "RMCSS_HARD", "RMCSS_HARD", "", status="NO_SCOPE")
    plan = v21.build_plan()
    FakeEvaluator(passing={"t2"}).run(ev, plan)
    s21 = load("wp2_e2e_smoke_v21_summary")
    s21.V21_ROOT = root
    old = s21.summarize(["t1", "t2"])
    new = sm.summarize_v22(s21, ["t1", "t2"])
    for arm in old:
        extra = new[arm].pop("applied_without_evaluation")
        assert extra == 0
        assert new[arm] == old[arm]
