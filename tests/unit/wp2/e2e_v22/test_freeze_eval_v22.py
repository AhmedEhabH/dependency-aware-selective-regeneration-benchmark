"""v2.2 freeze gates, evaluation wrapper paths/collisions, summary decision (all zero-API)."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[4]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, PROJECT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MAIN = [("t1", "GOLD_HARD", "GOLD_HARD"), ("t1", "RMCSS_HARD", "RMCSS_HARD"),
        ("t2", "GOLD_HARD", "GOLD_HARD")]
VAR = [("t1", "GOLD_HARD", "var_r1")]


@pytest.fixture()
def fz(tmp_path, monkeypatch):
    mod = load("wp2_e2e_v22_freeze")
    root = tmp_path / "v22"
    monkeypatch.setattr(mod, "V22_ROOT", root)
    monkeypatch.setattr(mod, "GEN_FREEZE_FILE", root / "generation_freeze_v22.json")
    monkeypatch.setattr(mod, "planned_main", lambda: list(MAIN))
    monkeypatch.setattr(mod, "planned_variance", lambda: list(VAR))
    mod._root = root
    return mod


def put_episode(root: Path, subdir: str, task: str, label: str, status: str = "APPLIED",
                raw: str | None = "RAW", route: str = "deepinfra/turbo", diff: str = "d1") -> Path:
    d = root / subdir / task / label
    (d / "calls").mkdir(parents=True, exist_ok=True)
    calls = []
    if raw is not None:
        (d / "calls" / "1_initial.txt").write_text(raw, newline="")
        calls.append({"kind": "initial", "index": 1, "route": route,
                      "raw_sha256": hashlib.sha256(b"RAW").hexdigest()})
    rec = {"task_id": task, "arm": "GOLD_HARD", "status": status, "diff_sha256": diff,
           "calls": calls}
    (d / "episode.json").write_text(json.dumps(rec))
    return d


def fill_all(root: Path) -> None:
    for t, _a, lab in MAIN:
        put_episode(root, "episodes", t, lab, diff=f"{t}{lab}")
    for t, _a, lab in VAR:
        put_episode(root, "variance", t, lab, diff=f"{t}{lab}")


def test_generation_freeze_pass_and_idempotent(fz, capsys):
    fill_all(fz._root)
    assert fz.generation_freeze() == 0
    out = json.loads((fz._root / "generation_freeze_v22.json").read_text())
    assert out["n_episodes"] == 4 and out["spend_usd"] == 0
    assert fz.generation_freeze() == 0  # same evidence -> same hash


def test_generation_freeze_detects_changed_evidence(fz):
    fill_all(fz._root)
    assert fz.generation_freeze() == 0
    put_episode(fz._root, "episodes", "t2", "GOLD_HARD", diff="changed")
    assert fz.generation_freeze() == 1


def test_generation_freeze_requires_every_planned_episode(fz, capsys):
    fill_all(fz._root)
    (fz._root / "variance" / "t1" / "var_r1" / "episode.json").unlink()
    assert fz.generation_freeze() == 1
    assert "not terminal: variance/t1/var_r1" in capsys.readouterr().out


def test_generation_freeze_rejects_forbidden_replay_and_raw_mismatch(fz, capsys):
    fill_all(fz._root)
    put_episode(fz._root, "episodes", "t9", "GOLD_HARD", status="GENERATION_FAIL")
    put_episode(fz._root, "episodes", "t1", "RMCSS_HARD", route="replay")
    put_episode(fz._root, "episodes", "t2", "GOLD_HARD", raw="TAMPERED")
    assert fz.generation_freeze() == 1
    out = capsys.readouterr().out
    assert "forbidden status" in out and "replay route" in out and "hash mismatch" in out


def test_generation_freeze_rejects_overspend(fz, capsys):
    fill_all(fz._root)
    led = fz._root / "ledger" / "spend_ledger_v22.jsonl"
    led.parent.mkdir(parents=True)
    led.write_text(json.dumps({"phase": "SMOKE", "cost_usd": 2.5, "cost_usd_actual": 2.5}) + "\n")
    assert fz.generation_freeze() == 1
    assert "ceiling" in capsys.readouterr().out


def test_eval_complete_uses_task_scoped_paths(fz, capsys):
    root = fz._root
    for t, _a, lab in MAIN:
        put_episode(root, "episodes", t, lab, status="NO_SCOPE")
    for t, _a, lab in VAR:
        put_episode(root, "variance", t, lab, status="APPLIED", diff="ab" * 32)
    (root / "evaluations").mkdir(parents=True)
    plan = {"items": [{"task_id": "t1", "diff_sha256": "ab" * 32}], "n_unique_diffs": 1}
    (root / "evaluations" / "plan.json").write_text(json.dumps(plan))
    assert fz.eval_complete() == 1
    up = fz.unique_eval_path(root, "t1", "ab" * 32)
    up.parent.mkdir(parents=True)
    up.write_text(json.dumps({"task_id": "t2", "diff_sha256": "ab" * 32}))  # wrong owner
    for t, lab in (("t1", "GOLD_HARD"), ("t1", "RMCSS_HARD"), ("t2", "GOLD_HARD")):
        p = root / "evaluations/episodes" / t / lab / "evaluation.json"
        p.parent.mkdir(parents=True)
        p.write_text("{}")
    assert fz.eval_complete() == 1
    assert "identity mismatch" in capsys.readouterr().out
    up.write_text(json.dumps({"task_id": "t1", "diff_sha256": "ab" * 32}))
    assert fz.eval_complete() == 0
    (root / "evaluations/episodes/t2/GOLD_HARD/evaluation.json").unlink()
    assert fz.eval_complete() == 1
    assert "episodes/t2/GOLD_HARD" in capsys.readouterr().out


def test_code_hash_is_line_ending_invariant(tmp_path, monkeypatch):
    mod = load("wp2_e2e_v22_freeze")
    monkeypatch.setattr(mod, "CODE_GLOBS", ("scripts/*.py",))
    (tmp_path / "scripts").mkdir()
    f = tmp_path / "scripts" / "a.py"
    f.write_bytes(b"x = 1\r\n")
    h1 = mod.code_hashes(tmp_path)
    f.write_bytes(b"x = 1\n")
    assert mod.code_hashes(tmp_path) == h1
    f.write_bytes(b"x = 2\n")
    assert mod.code_hashes(tmp_path) != h1


def test_policy_declares_provider_failures_non_scientific():
    mod = load("wp2_e2e_v22_freeze")
    pol = mod.policy()
    assert pol["provider_failures_are_scientific_outcomes"] is False
    assert pol["allow_fallbacks"] is False and pol["workers"] == 1
    assert "GENERATION_FAIL" not in pol["terminal_statuses"]


# ------------------------------------------------------------ evaluation wrapper
class FakeV21:
    def __init__(self, items):
        self.items = items

    def _collect_by_construction(self):
        return self.items


def test_by_construction_records_are_task_scoped(tmp_path, monkeypatch):
    ev = load("wp2_e2e_v22_evaluate")
    monkeypatch.setattr(ev, "V22_ROOT", tmp_path)
    items = [{"task_id": t, "arm": "GOLD_HARD", "label": "GOLD_HARD", "status": "NO_SCOPE",
              "diff_sha256": "", "source": f"episodes/{t}/GOLD_HARD/episode.json",
              "subdir": "episodes"} for t in ("t1", "t2")]
    sets = {"tasks": {"t1": {"behavioral_f2p_node_ids": ["a"], "p2p_s_defined": True,
                             "p2p_u_cap200_defined": False},
                      "t2": {"behavioral_f2p_node_ids": [], "p2p_s_defined": False,
                             "p2p_u_cap200_defined": True}}}
    assert ev.by_construction_records(FakeV21(items), sets) == 2
    r1 = json.loads((tmp_path / "evaluations/episodes/t1/GOLD_HARD/evaluation.json").read_text())
    r2 = json.loads((tmp_path / "evaluations/episodes/t2/GOLD_HARD/evaluation.json").read_text())
    assert (r1["task_id"], r1["f2p_task"], r1["p2p_u200_task"]) == ("t1", "FAIL", "UNDEFINED")
    assert (r2["task_id"], r2["f2p_task"], r2["p2p_s_task"]) == ("t2", "UNDEFINED", "UNDEFINED")
    assert ev.by_construction_records(FakeV21(items), sets) == 0  # idempotent


def test_evaluator_is_pointed_at_v22_root():
    ev = load("wp2_e2e_v22_evaluate")
    ev.point_evaluator_at_v22()
    from benchmark.wp2.e2e import evaluate as core
    assert core.E2E_ROOT == ev.V22_ROOT


# ------------------------------------------------------------ summary decision
@pytest.mark.parametrize("gates,token", [
    ((True, True, True, True), "E2E_SMOKE_V22_PIPELINE_VALID"),
    ((True, True, True, False), "E2E_SMOKE_V22_FLOOR_EFFECT"),
    ((False, True, True, True), "E2E_SMOKE_V22_INSTRUMENT_INVALID"),
    ((True, False, True, True), "E2E_SMOKE_V22_INSTRUMENT_INVALID"),
    ((True, True, False, True), "E2E_SMOKE_V22_INSTRUMENT_INVALID"),
])
def test_summary_decision_table(gates, token):
    sm = load("wp2_e2e_v22_summary")
    keys = ("SG1_instrument", "SG2_completion", "SG3_spend", "SG4_floor")
    assert sm.decide(dict(zip(keys, gates, strict=True))) == token
