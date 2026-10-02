"""M16 R1 (repetition retention): identity with the frozen phase5/run_state_v3 path, FLAKY reachability.

Zero network, zero Docker/WSL: the frozen functions run for real; only their lowest-level IO
(wsl / wsl_docker / subprocess.run / DB helpers / git) is replaced by an in-memory fake.
"""
from __future__ import annotations

import copy
import json
import sys
import types
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import benchmark.wp2.harness_v3 as hv3  # noqa: E402
import scripts.wp2_m10b_phase5_c4_v3 as ph5  # noqa: E402
from benchmark.wp2.oracle_confirmation import parse_junit_with_failures  # noqa: E402
from benchmark.wp2.oracle_semantics_v2 import classify_node_v2, task_eligibility_v2  # noqa: E402
from scripts import wp2_m16_r1 as r1  # noqa: E402

FILES = ["saleor/a/tests/test_x.py", "saleor/b/tests/test_y.py"]


def xml(cases: dict[str, str]) -> str:
    out = ['<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite name="pytest">']
    for node, outcome in cases.items():
        f, name = node.split("::")
        cls = f[:-3].replace("/", ".")
        body = {"passed": "", "failed": '<failure message="AssertionError: x">assert 1 == 2</failure>',
                "error": '<error message="E">boom</error>', "skipped": '<skipped message="s"/>'}[outcome]
        out.append(f'<testcase classname="{cls}" name="{name}" file="{f}">{body}</testcase>')
    out.append("</testsuite></testsuites>")
    return "".join(out)


class FakeIO:
    """In-memory replacement for the frozen run_state_v3's wsl/docker/subprocess/DB calls."""

    def __init__(self, per_state: dict[str, list[dict[int, dict[str, str]] | None]]) -> None:
        self.per_state = per_state           # state -> [rep -> {file_idx -> {node: outcome}}]
        self.fs: dict[str, str] = {}

    def install(self, mp, tid: str, files: list[str]) -> None:
        def fake_docker(args, timeout_s=0):
            wt = next(a for a in args if ":/workspace/" in a).split(":")[0]
            state = wt.rsplit("_", 1)[-1]
            for rep, reps in enumerate(self.per_state[state]):
                if reps is None:
                    continue
                for idx, _tf in enumerate(files):
                    cases = reps.get(idx)
                    if cases is not None:
                        self.fs[f"{wt}/{tid}_{state}_r{rep}_f{idx}.xml"] = xml(cases)
            return types.SimpleNamespace(returncode=0, stdout="RUN_0_RC=0\nALL_RUNS_DONE\n", stderr="")

        def fake_wsl(script, timeout_s=120):
            if script.startswith("cat "):
                path = script.split()[1]
                return types.SimpleNamespace(returncode=0, stdout=self.fs.get(path, "__NO_FILE__\n"), stderr="")
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")

        def fake_run(*a, **k):
            return types.SimpleNamespace(returncode=0, stdout=b"", stderr=b"")
        mp.setattr(hv3, "wsl_docker", fake_docker)
        mp.setattr(hv3, "wsl", fake_wsl)
        mp.setattr(hv3, "subprocess", types.SimpleNamespace(run=fake_run))
        for name in ("ensure_postgres_running", "drop_db"):
            mp.setattr(hv3, name, lambda *a, **k: None)
        mp.setattr(hv3, "ensure_fresh_db", lambda *a, **k: {"created": True})


def triple(target: list[dict[str, str]], parent: list[dict[str, str]]) -> dict:
    """Build per-state repetitions: each element is {node: outcome} for that repetition."""
    def by_file(cases: dict[str, str]) -> dict[int, dict[str, str]]:
        out: dict[int, dict[str, str]] = {}
        for node, o in cases.items():
            out.setdefault(FILES.index(node.split("::")[0]), {})[node] = o
        return out
    return {"t": [by_file(c) for c in target], "p": [by_file(c) for c in parent]}


def frozen_and_r1(mp, tmp_path, per_state: dict) -> tuple[dict, dict]:
    """Run the REAL frozen phase5.run_task and the R1 oracle_task on the same fake world."""
    io = FakeIO(per_state)
    task, tid = "saleor-rc-0123456789ab", "0123456789ab"
    io.install(mp, tid, FILES)
    wts = {"t": f"/opt/wt/{tid}_v3_t", "p": f"/opt/wt/{tid}_v3_p"}
    mp.setattr(ph5, "task_commits", lambda t: ("P" * 40, "T" * 40))
    mp.setattr(ph5, "load_v2_tasks", lambda: {task: {"era_key": "py39"}})
    mp.setattr(ph5, "changed_test_files", lambda p, t: list(FILES))
    clock = {"verdict": "PASS", "pre": {"median_skew_s": 0.01}}
    mp.setattr(ph5, "clock_preflight", lambda *a, **k: clock)
    mp.setattr(ph5, "target_manifests", lambda t: {"pyproject.toml": "x"})
    mp.setattr(ph5, "ensure_worktrees_v3", lambda *a: dict(wts))
    mp.setattr(ph5, "lock_install_script", lambda wt, m: ("echo install", "LOCK_EXACT_MAIN_PLUS_DEV", {}))
    mp.setattr(ph5, "locked_dev_install", lambda t: "echo NO_LOCKED_DEV_GROUP")
    mp.setattr(ph5, "base_image_id", lambda e: "sha256:img")
    mp.setattr(ph5, "v31_dev_closure", lambda t: {"mechanism": "poetry", "pins": [], "unsupported": []})
    mp.setattr(ph5, "remove_worktrees_v3", lambda t: None)
    mp.setattr(ph5, "lockfile_sha256", lambda m: "lock")
    mp.setattr(ph5, "git_local", lambda *a: types.SimpleNamespace(stdout="HEAD\n"))
    mp.setattr(ph5, "PER_TASK", tmp_path / "per_task.jsonl")
    frozen = ph5.run_task(task, tmp_path)
    deps = {"changed_test_files": lambda p, t: list(FILES), "clock_preflight": lambda *a, **k: clock,
            "target_manifests": lambda t: {"pyproject.toml": "x"}, "ensure_worktrees_v3": lambda *a: dict(wts),
            "lock_install_script": lambda wt, m: ("echo install", "LOCK_EXACT_MAIN_PLUS_DEV", {}),
            "locked_dev_install": lambda t: "echo NO_LOCKED_DEV_GROUP", "base_image_id": lambda e: "sha256:img",
            "run_state_v3": hv3.run_state_v3, "parse_junit_with_failures": parse_junit_with_failures,
            "classify_node_v2": classify_node_v2, "task_eligibility_v2": task_eligibility_v2,
            "remove_worktrees_v3": lambda t: None,
            "v31_dev_closure": lambda t: {"mechanism": "poetry", "pins": [], "unsupported": []},
            "lockfile_sha256": lambda m: "lock"}
    io.fs.clear()
    rec = r1.oracle_task(task, parent="P" * 40, target="T" * 40, era_key="py39", raw_root=tmp_path / "raw",
                         deps=deps)
    return frozen, rec


N1, N2, N3 = "saleor/a/tests/test_x.py::test_one", "saleor/a/tests/test_x.py::test_two", \
    "saleor/b/tests/test_y.py::test_three"


def test_identical_triples_reproduce_the_frozen_classification(monkeypatch, tmp_path):
    t = {N1: "passed", N2: "passed", N3: "passed"}
    p = {N1: "failed", N2: "passed", N3: "error"}
    frozen, rec = frozen_and_r1(monkeypatch, tmp_path, triple([t] * 3, [p] * 3))
    assert rec["status"] == "DONE" and frozen["status"] == "DONE"
    assert rec["node_records"] == frozen["node_records"]
    assert rec["counts"] == frozen["counts"] and rec["eligibility"] == frozen["eligibility"]
    assert rec["classification"] == frozen["classification"] == "BEHAVIORAL_F2P"


@pytest.mark.parametrize("seq", [["passed", "passed", "failed"], ["passed", "failed", "passed"],
                                 ["failed", "passed", "passed"]])
@pytest.mark.parametrize("side", ["target", "parent"])
def test_unstable_triples_reach_flaky_only_under_r1(monkeypatch, tmp_path, seq, side):
    stable_t, stable_p = {N1: "passed"}, {N1: "failed"}
    t = [dict(stable_t) for _ in range(3)]
    p = [dict(stable_p) for _ in range(3)]
    for i, o in enumerate(seq):
        (t if side == "target" else p)[i][N1] = o if side == "target" else ("passed" if o == "failed" else "failed")
    frozen, rec = frozen_and_r1(monkeypatch, tmp_path, triple(t, p))
    r_cls = {nr["node_id"]: nr["v3_class"] for nr in rec["node_records"]}
    f_cls = {nr["node_id"]: nr["v3_class"] for nr in frozen["node_records"]}
    assert r_cls[N1] == "FLAKY"
    last = frozen["node_records"][0]["target_outcomes" if side == "target" else "parent_outcomes"]
    assert len(set(last)) == 1                                  # frozen path saw [last]*3
    assert f_cls[N1] != "FLAKY" or len(set(seq)) == 1


def test_classifier_semantics_for_unstable_triples_are_the_frozen_ones():
    for seq in (["passed", "passed", "failed"], ["passed", "failed", "passed"], ["failed", "passed", "passed"]):
        assert classify_node_v2(target_outcomes=seq, parent_outcomes=["failed"] * 3, parent_failure_text="x",
                                parent_collects_node=True) == "FLAKY"
        assert classify_node_v2(target_outcomes=["passed"] * 3, parent_outcomes=seq, parent_failure_text="x",
                                parent_collects_node=True) == "FLAKY"


def test_missing_rep_file_keeps_frozen_pseudo_node_semantics(monkeypatch, tmp_path):
    t = {N1: "passed", N3: "passed"}
    p = {N1: "failed", N3: "failed"}
    per_state = triple([t] * 3, [p] * 3)
    per_state["p"][2] = {0: per_state["p"][2][0]}            # file 1 missing in parent repetition 2
    frozen, rec = frozen_and_r1(monkeypatch, tmp_path, per_state)
    assert set(nr["node_id"] for nr in rec["node_records"]) == set(nr["node_id"] for nr in frozen["node_records"])
    pseudo = next(nr for nr in rec["node_records"] if nr["node_id"] == FILES[1])
    assert pseudo["parent_outcomes"] == ["missing", "missing", "error"]
    n3 = next(nr for nr in rec["node_records"] if nr["node_id"] == N3)
    assert n3["parent_outcomes"] == ["failed", "failed", "missing"] and n3["v3_class"] == "FLAKY"


def test_container_incomplete_is_infrastructure_not_a_classification(tmp_path):
    def run_state(**k):
        return {"error": None, "returncode": 125, "junit": {}, "junit_failures": {}, "stdout_tail": "docker: error"}
    out = r1.run_state_r1(run_state=run_state, parse=parse_junit_with_failures, raw_dir=tmp_path / "r",
                          era_key="py39", worktree_linux="/w/x_t", tid="x", state="t", test_files=FILES,
                          install_fragment="", locked_dev_fragment="")
    assert out["infra_reason"].startswith("CONTAINER_INCOMPLETE")


def test_install_fail_is_frozen_env_install_blocked_candidate():
    assert r1.frozen_status({"error": "INSTALL_FAIL"}, {"error": None}) == "ENV_INSTALL_BLOCKED"
    assert r1.frozen_status({"error": None}, {"error": None}) == "DONE"


def test_pack_raw_is_deterministic(tmp_path):
    for i in range(2):
        d = tmp_path / f"raw{i}"
        (d / "t").mkdir(parents=True)
        (d / "t" / "a.xml").write_text("<x/>", encoding="utf-8")
        (d / "p").mkdir()
        (d / "p" / "b.xml").write_text("<y/>", encoding="utf-8")
    h1 = r1.pack_raw(tmp_path / "raw0", tmp_path / "a.tar.gz")
    h2 = r1.pack_raw(tmp_path / "raw1", tmp_path / "b.tar.gz")
    assert h1 == h2 and not (tmp_path / "raw0").exists()


def test_r1_module_never_writes_historical_roots():
    src = (P / "scripts/wp2_m16_r1.py").read_text(encoding="utf-8")
    for root in ("harness_v3_2026-09-26", "m15r_v1", "m14r_v1", "pilot_a_v1", "oracle_confirmation_linux_v2"):
        assert root not in src
    assert json.loads(json.dumps(r1.RULE_CONSTANTS)) == copy.deepcopy(r1.RULE_CONSTANTS)
