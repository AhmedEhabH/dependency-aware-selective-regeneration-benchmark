"""Controller v2.2.3 (copy of the v2.2 suite + v2.2.3 regressions): transitions, STOP mapping, writes, acks, loops, tags, exports."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[4]


def load_ctl():
    spec = importlib.util.spec_from_file_location("ctl", PROJECT / "scripts" / "wp2_ctl_v223.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                          check=True).stdout.strip()


@pytest.fixture()
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "t")
    (root / "README.md").write_text("x\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "init")
    return root


def py(code: str) -> list[str]:
    return ["{python}", "-c", code]


def write_file(rel: str, text: str = "x") -> str:
    return (f"import pathlib; p=pathlib.Path({rel!r}); p.parent.mkdir(parents=True, exist_ok=True); "
            f"p.write_text({text!r})")


def make_plan(root: Path, phases: list[dict], resumable=("OUTAGE",), exports=None) -> Path:
    plan = {"id": "TEST_PLAN",
            "settings": {"state_file": "out/state.json", "report_dir": "out/reports",
                         "stop_flag": "logs/STOP.flag", "git_commit": True, "git_push": False,
                         "stop_commit_prefixes": ["out/"], "resumable_tokens": list(resumable),
                         "exports": exports or {}},
            "phases": phases}
    p = root / "plan.json"
    p.write_text(json.dumps(plan))
    return p


def ctl_for(mod, root, plan, kit_bad=None, clock=None):
    kw = {"kit_check": (lambda: list(kit_bad or []))}
    if clock:
        kw["clock"] = clock
    return mod.Controller(plan, root=root, **kw)


def test_once_phases_pass_commit_and_are_idempotent(repo):
    mod = load_ctl()
    plan = make_plan(repo, [
        {"id": "A", "command": py(write_file("out/a.txt") + "; open('logs_count','a').write('1')"),
         "fail_token": "A_FAIL", "allowed_write_prefixes": ["out/", "logs_count"],
         "pass_checks": [{"type": "file_exists", "path": "out/a.txt"}],
         "commit_message": "a done"},
        {"id": "B", "requires": ["A"], "builtin": "noop", "fail_token": "B_FAIL"}])
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_COMPLETE
    assert "a done" in git(repo, "log", "--oneline")
    assert "out/a.txt" in git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_COMPLETE
    assert (repo / "logs_count").read_text() == "1"  # PASS phases never re-run


def test_exit_code_maps_to_resumable_stop_then_resume(repo):
    mod = load_ctl()
    code = ("import pathlib,sys; f=pathlib.Path('out/fixed'); "
            "sys.exit(0 if f.exists() else 75)")
    plan = make_plan(repo, [{"id": "G", "command": py(code), "fail_token": "G_FAIL",
                             "exit_codes": {"75": "STOP:OUTAGE"},
                             "allowed_write_prefixes": ["out/"]}])
    c = ctl_for(mod, repo, plan)
    assert c.run() == mod.EXIT_STOPPED
    st = json.loads((repo / "out/state.json").read_text())
    assert st["stop"]["token"] == "OUTAGE" and st["stop"]["resumable"] is True
    assert list((repo / "out/reports").glob("STOP_OUTAGE_*.md"))
    assert "controller STOP OUTAGE" in git(repo, "log", "--oneline")
    (repo / "out/fixed").write_text("1")
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_COMPLETE


def test_non_resumable_stop_needs_ack(repo):
    mod = load_ctl()
    code = "import pathlib,sys; sys.exit(0 if pathlib.Path('out/ok').exists() else 1)"
    plan = make_plan(repo, [{"id": "X", "command": py(code), "fail_token": "X_FAIL",
                             "allowed_write_prefixes": ["out/"]}])
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_STOPPED
    (repo / "out/ok").write_text("1")
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_NEEDS_ACK
    c = ctl_for(mod, repo, plan)
    assert c.ack("WRONG", "n") == 1
    assert c.ack("X_FAIL", "human checked and fixed") == 0
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_COMPLETE
    st = json.loads((repo / "out/state.json").read_text())
    assert st["acks"][0]["note"] == "human checked and fixed"


def test_retry_once_then_stop(repo):
    mod = load_ctl()
    code = "open('logs_n','a').write('1'); raise SystemExit(1)"
    plan = make_plan(repo, [{"id": "R", "command": py(code), "fail_token": "R_FAIL",
                             "max_retries": 1, "allowed_write_prefixes": ["logs_n"]}])
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_STOPPED
    assert (repo / "logs_n").read_text() == "11"


def test_unexpected_write_stops(repo):
    mod = load_ctl()
    plan = make_plan(repo, [{"id": "W", "command": py(write_file("src/evil.py")),
                             "fail_token": "W_FAIL", "allowed_write_prefixes": ["out/"]}])
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_STOPPED
    st = json.loads((repo / "out/state.json").read_text())
    assert st["stop"]["token"] == "UNEXPECTED_WRITE" and "src/evil.py" in st["stop"]["detail"]


def test_modifying_a_tracked_file_is_detected(repo):
    mod = load_ctl()
    plan = make_plan(repo, [{"id": "M", "command": py(write_file("README.md", "changed")),
                             "fail_token": "M_FAIL", "allowed_write_prefixes": ["out/"]}])
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_STOPPED
    assert "README.md" in json.loads((repo / "out/state.json").read_text())["stop"]["detail"]


def loop_phase(code: str, target: int = 3, **extra) -> dict:
    ph = {"id": "L", "kind": "loop", "command": py(code), "fail_token": "L_FAIL",
          "max_iterations": 10, "allowed_write_prefixes": ["out/"],
          "done_checks": [{"type": "count_files", "glob": "out/items/*.json",
                           "where": {"status": ["DONE"]}, "op": "==", "value": target}],
          "progress": {"glob": "out/items/*.json", "where": {"status": ["DONE"]}},
          "commit_message": "loop progress"}
    ph.update(extra)
    return ph


ADD_ONE = ("import json,pathlib; d=pathlib.Path('out/items'); d.mkdir(parents=True, exist_ok=True); "
           "n=len(list(d.glob('*.json'))); (d/f'{n}.json').write_text(json.dumps({'status':'DONE'}))")


def test_loop_runs_until_done_and_commits_each_iteration(repo):
    mod = load_ctl()
    plan = make_plan(repo, [loop_phase(ADD_ONE)])
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_COMPLETE
    assert len(list((repo / "out/items").glob("*.json"))) == 3
    assert git(repo, "log", "--oneline").count("loop progress") == 3


def test_loop_without_progress_stops(repo):
    mod = load_ctl()
    plan = make_plan(repo, [loop_phase("pass")])
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_STOPPED
    assert json.loads((repo / "out/state.json").read_text())["stop"]["token"] == "NO_PROGRESS"


def test_loop_yields_on_time_budget_and_resumes(repo):
    mod = load_ctl()
    plan = make_plan(repo, [loop_phase(ADD_ONE)])
    t = {"v": 0.0}

    def clock():
        t["v"] += 100.0
        return t["v"]
    assert ctl_for(mod, repo, plan, clock=clock).run(max_seconds=150) == mod.EXIT_YIELD
    n = len(list((repo / "out/items").glob("*.json")))
    assert 1 <= n < 3
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_COMPLETE


def test_pre_check_failure_uses_its_token(repo):
    mod = load_ctl()
    plan = make_plan(repo, [loop_phase(ADD_ONE, pre_checks=[
        {"type": "command_ok", "command": py("raise SystemExit(1)"), "fail_token": "FREEZE_DRIFT"}])])
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_STOPPED
    assert json.loads((repo / "out/state.json").read_text())["stop"]["token"] == "FREEZE_DRIFT"
    assert not (repo / "out/items").exists()


def test_kit_tamper_blocks_everything(repo):
    mod = load_ctl()
    plan = make_plan(repo, [{"id": "A", "command": py(write_file("out/a")), "fail_token": "F"}])
    assert ctl_for(mod, repo, plan, kit_bad=["modified x.py"]).run() == mod.EXIT_TAMPER
    assert not (repo / "out/a").exists()


def test_plan_change_is_detected(repo):
    mod = load_ctl()
    plan = make_plan(repo, [{"id": "A", "builtin": "noop", "fail_token": "F"}])
    ctl_for(mod, repo, plan).run()
    data = json.loads(plan.read_text())
    data["phases"].append({"id": "B", "builtin": "noop", "fail_token": "F"})
    plan.write_text(json.dumps(data))
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_STOPPED
    assert json.loads((repo / "out/state.json").read_text())["stop"]["token"] == "PLAN_CHANGED"


def test_stop_flag(repo):
    mod = load_ctl()
    plan = make_plan(repo, [{"id": "A", "builtin": "noop", "fail_token": "F"}],
                     resumable=("USER_STOP_FLAG",))
    (repo / "logs").mkdir()
    (repo / "logs/STOP.flag").write_text("1")
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_STOPPED
    (repo / "logs/STOP.flag").unlink()
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_COMPLETE


def test_tags_are_immutable(repo):
    mod = load_ctl()
    git(repo, "tag", "-a", "t-fixed", "-m", "old")
    (repo / "b.txt").write_text("b")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "second")
    plan = make_plan(repo, [{"id": "T", "builtin": "noop", "fail_token": "F",
                             "post_actions": [{"type": "tag", "name": "t-fixed"}]}])
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_STOPPED
    assert json.loads((repo / "out/state.json").read_text())["stop"]["token"] == "POST_ACTION_FAILED"


def test_tag_created_and_idempotent(repo):
    mod = load_ctl()
    plan = make_plan(repo, [{"id": "T", "builtin": "noop", "fail_token": "F",
                             "post_actions": [{"type": "tag", "name": "t-{date}"}]}])
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_COMPLETE
    assert git(repo, "tag").startswith("t-20")


def test_stop_runs_exports(repo):
    mod = load_ctl()
    exports = {"light": py("import sys,pathlib; pathlib.Path('logs').mkdir(exist_ok=True); "
                           "pathlib.Path('logs/export.txt').write_text(sys.argv[1])") + ["{label}"]}
    plan = make_plan(repo, [{"id": "A", "command": py("raise SystemExit(5)"), "fail_token": "A_FAIL"}],
                     exports=exports)
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_STOPPED
    assert (repo / "logs/export.txt").read_text() == "STOP_A_FAIL"
    st = json.loads((repo / "out/state.json").read_text())
    assert st["stop"]["exports"] == {"light": 0}


def test_verify_kit_detects_changes(tmp_path):
    mod = load_ctl()
    (tmp_path / "controller").mkdir()
    f = tmp_path / "a.py"
    f.write_bytes(b"x = 1\r\n")
    man = {"files": {"a.py": mod.norm_sha256(f)}}
    (tmp_path / "controller/KIT_MANIFEST.json").write_text(json.dumps(man))
    assert mod.verify_kit(tmp_path) == []
    f.write_bytes(b"x = 1\n")  # line endings alone are not tampering
    assert mod.verify_kit(tmp_path) == []
    f.write_text("x = 2\n")
    assert mod.verify_kit(tmp_path) == ["modified a.py"]
    f.unlink()
    assert mod.verify_kit(tmp_path) == ["missing a.py"]


def test_real_m13_plan_is_well_formed():
    plan = json.loads((PROJECT / "controller" / "plan_m13_pilot_prep_v1.json").read_text())
    ids = [p["id"] for p in plan["phases"]]
    assert len(ids) == len(set(ids))
    for i, ph in enumerate(plan["phases"]):
        assert ph.get("fail_token")
        assert all(r in ids[:i] for r in ph.get("requires", []))
        assert "command" in ph or ph.get("builtin")
    assert plan["settings"]["kit_manifest"] == "controller/KIT_MANIFEST_M13B.json"
    txt = json.dumps(plan)
    assert "--tags" not in txt and "openrouter" not in txt.lower() and "wsl" not in txt.lower()


# ------------------------------------------------------------ v2.2.3 regressions
def test_tag_push_is_exact_and_ignores_divergent_unrelated_tags(tmp_path):
    mod = load_ctl()
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    work = tmp_path / "w"
    work.mkdir()
    git(work, "init", "-q", "-b", "main")
    git(work, "config", "user.email", "t@example.com")
    git(work, "config", "user.name", "t")
    git(work, "remote", "add", "origin", str(remote))
    (work / "a").write_text("a")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "a")
    git(work, "tag", "old-tag")
    git(work, "push", "-q", "origin", "main", "refs/tags/old-tag")
    (work / "b").write_text("b")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "b")
    git(work, "tag", "-d", "old-tag")
    git(work, "tag", "old-tag")                 # now diverges from origin
    g = mod.Git(work, enabled=True, push=True)
    g.tag("new-tag", "m")
    assert g.push_tag("new-tag") is True
    remote_tags = subprocess.run(["git", "ls-remote", "--tags", str(remote)], capture_output=True,
                                 text=True, check=True).stdout
    assert "refs/tags/new-tag" in remote_tags
    head_a = git(work, "rev-parse", "HEAD~1")
    assert f"{head_a}\trefs/tags/old-tag" in remote_tags   # remote old tag untouched


def test_stop_report_contains_failing_log_tail(repo):
    mod = load_ctl()
    code = "print('first line'); print('THE_REAL_REASON 42'); raise SystemExit(3)"
    plan = make_plan(repo, [{"id": "F", "command": py(code), "fail_token": "F_FAIL"}])
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_STOPPED
    st = json.loads((repo / "out/state.json").read_text())
    assert "THE_REAL_REASON 42" in st["stop"]["detail"]
    rep = next((repo / "out/reports").glob("STOP_F_FAIL_*.md")).read_text()
    assert "THE_REAL_REASON 42" in rep


def test_stop_without_command_has_no_stale_log(repo):
    mod = load_ctl()
    plan = make_plan(repo, [
        {"id": "A", "command": py("print('OLD_LOG_TEXT')"), "fail_token": "A_FAIL"},
        {"id": "B", "builtin": "noop", "fail_token": "B_FAIL",
         "pass_checks": [{"type": "file_exists", "path": "nope"}]}])
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_STOPPED
    st = json.loads((repo / "out/state.json").read_text())
    assert "OLD_LOG_TEXT" not in st["stop"]["detail"]


def test_kit_manifest_path_comes_from_plan(repo):
    mod = load_ctl()
    (repo / "k.py").write_text("x = 1\n")
    man = {"files": {"k.py": mod.norm_sha256(repo / "k.py")}}
    (repo / "controller").mkdir()
    (repo / "controller/KIT_X.json").write_text(json.dumps(man))
    plan = make_plan(repo, [{"id": "A", "builtin": "noop", "fail_token": "F"}])
    data = json.loads(plan.read_text())
    data["settings"]["kit_manifest"] = "controller/KIT_X.json"
    plan.write_text(json.dumps(data))
    c = mod.Controller(plan, root=repo)
    assert c.kit_check() == []
    (repo / "k.py").write_text("x = 2\n")
    assert c.kit_check() == ["modified k.py"]


def test_no_broad_tag_push_in_source():
    txt = (PROJECT / "scripts" / "wp2_ctl_v223.py").read_text()
    assert '"--tags"' not in txt


def test_resumed_tag_one_stop_commit_behind_is_accepted(repo):
    mod = load_ctl()
    plan = make_plan(repo, [{"id": "T", "builtin": "noop", "fail_token": "F",
                             "post_actions": [{"type": "tag", "name": "t-fixed"}]}])
    git(repo, "tag", "-a", "t-fixed", "-m", "m")
    (repo / "out").mkdir()
    (repo / "out/state.json").write_text("{}")
    git(repo, "add", "out/state.json")
    git(repo, "commit", "-q", "-m", "stop bookkeeping")
    (repo / "out/state.json").unlink()
    git(repo, "commit", "-q", "-am", "reset state")
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_COMPLETE


def test_tag_behind_by_real_change_is_refused(repo):
    mod = load_ctl()
    plan = make_plan(repo, [{"id": "T", "builtin": "noop", "fail_token": "F",
                             "post_actions": [{"type": "tag", "name": "t-fixed"}]}])
    git(repo, "tag", "-a", "t-fixed", "-m", "m")
    (repo / "code.py").write_text("x")
    git(repo, "add", "code.py")
    git(repo, "commit", "-q", "-m", "real change")
    assert ctl_for(mod, repo, plan).run() == mod.EXIT_STOPPED
