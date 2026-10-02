"""M16 gates: READY decision, infra/listwise policy, resource projection, tag/push/ancestry, wording."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m16_resource as res  # noqa: E402
from scripts import wp2_m16_run as run  # noqa: E402

OK_NEG = {"strict": {"f2p_task": "FAIL"}, "robust": {"p2p_s_task": "PASS", "p2p_u200_task": "UNDEFINED"}}


def test_design_and_constants_load():
    d = run.design()
    assert d["constants"]["pool_min"] == 40 and d["constants"]["tags"] == run.TAGS
    assert len(run.frame()) == 220


@pytest.mark.parametrize("rec,decision", [
    ({"negative": OK_NEG, "positive": {"scoped_diff_nonempty": True, "robust": {"resolved": True}}}, "READY"),
    ({"negative": {**OK_NEG, "strict": {"f2p_task": "PASS"}}, "positive": {}}, "NOT_READY_NEGATIVE_CONTROL_INVALID"),
    ({"negative": {**OK_NEG, "robust": {"p2p_s_task": "FAIL", "p2p_u200_task": "PASS"}}, "positive": {}},
     "NOT_READY_NEGATIVE_CONTROL_INVALID"),
    ({"negative": OK_NEG, "positive": {"scoped_diff_nonempty": False}}, "NOT_READY_EMPTY_SCOPED_GOLD"),
    ({"negative": OK_NEG, "positive": {"scoped_diff_nonempty": True, "apply_error": "x"}},
     "NOT_READY_SCOPED_GOLD_DOES_NOT_APPLY"),
    ({"negative": OK_NEG, "positive": {"scoped_diff_nonempty": True, "robust": {"resolved": False}}},
     "NOT_READY_SCOPED_GOLD_NOT_RESOLVED"),
    ({"infra_unresolved": True}, "NOT_READY_INFRA_UNRESOLVED")])
def test_decide_ready(rec, decision):
    assert run.decide_ready(rec) == decision


def test_infra_policy_needs_three_attempts_over_two_invocations(tmp_path, monkeypatch):
    led = tmp_path / "a.jsonl"
    calls = {"n": 0}

    def boom():
        calls["n"] += 1
        raise RuntimeError("container did not finish")
    monkeypatch.setattr(run, "INVOCATION", "inv1")
    with pytest.raises(run.Stop) as e:
        run.run_with_attempts("oracle", led, "t1", boom)
    assert e.value.code == run.EXIT_INFRA and calls["n"] == 2          # retried once in-invocation
    monkeypatch.setattr(run, "INVOCATION", "inv2")
    out = run.run_with_attempts("oracle", led, "t1", boom)
    assert out["status"] == "INFRA_UNRESOLVED" and out["attempts"] == 3
    rows = [json.loads(x) for x in led.read_text().splitlines()]
    assert [r["outcome"] for r in rows] == ["INFRA"] * 3 and len({r["invocation"] for r in rows}) == 2


def test_install_fail_needs_two_consecutive_attempts(tmp_path, monkeypatch):
    led = tmp_path / "a.jsonl"
    seq = iter([{"status": "ENV_INSTALL_BLOCKED"}, {"status": "DONE"}])
    assert run.run_with_attempts("oracle", led, "t2", lambda: next(seq))["status"] == "DONE"
    seq2 = iter([{"status": "ENV_INSTALL_BLOCKED"}, {"status": "ENV_INSTALL_BLOCKED"}])
    out = run.run_with_attempts("oracle", led, "t3", lambda: next(seq2))
    assert out["status"] == "ENV_INSTALL_BLOCKED" and "2 consecutive" in out["install_blocked_rule"]


def test_clock_blocked_stops_without_consuming_an_attempt(tmp_path):
    with pytest.raises(run.Stop) as e:
        run.run_with_attempts("oracle", tmp_path / "a.jsonl", "t4", lambda: {"status": "CLOCK_BLOCKED"})
    assert e.value.code == run.EXIT_PREFLIGHT


def test_resource_projection_is_conservative_and_pure():
    rows = [{"use_t_gib": 0.5, "use_p_gib": 0.01, "source": "vhdx_allocated"},
            {"use_t_gib": 0.2, "use_p_gib": 0.02, "source": "vhdx_allocated"}]
    p = res.project(rows, c_free_now_gib=60, n_new_lock_sets=40, evidence_bytes_per_task=2e6)
    assert p["g_cold_gib_per_new_lock_set"] == pytest.approx(0.49)
    assert p["g_warm_gib_per_container"] == pytest.approx(0.02)
    exp = 40 * 0.49 + p["containers_upper_bound"] * 0.02 + 220 * 2e6 / 1024 ** 3 * 4 + 2.0
    assert p["projected_consumption_gib"] == pytest.approx(exp, abs=1e-3)
    assert p["verdict"] == ("PASS" if 60 - exp >= 25 else "S3_REQUIRED")
    assert res.project(rows, c_free_now_gib=20, n_new_lock_sets=0, evidence_bytes_per_task=0)["verdict"] == "S3_REQUIRED"


def test_state_use_prefers_vhdx_and_never_negative():
    a = {"c_free_gib": 50.0, "vhdx": {"allocated_bytes": 10 * 1024 ** 3}}
    b = {"c_free_gib": 49.0, "vhdx": {"allocated_bytes": 11 * 1024 ** 3}}
    assert res.state_use(a, b) == (pytest.approx(1.0), "vhdx_allocated")
    assert res.state_use(b, a)[0] == 0.0
    assert res.state_use({"c_free_gib": 50.0}, {"c_free_gib": 49.5}) == (pytest.approx(0.5), "c_free_drop")


def test_state_use_takes_the_maximum_measure():
    g = 1024 ** 3
    a = {"c_free_gib": 50.0, "vhdx": {"allocated_bytes": 10 * g}, "guest_used_bytes": 5 * g}
    b = {"c_free_gib": 49.8, "vhdx": {"allocated_bytes": 10 * g}, "guest_used_bytes": 7 * g}
    assert res.state_use(a, b) == (pytest.approx(2.0), "guest_used")        # VHDX absorbed it
    b2 = dict(b, c_free_gib=46.0)
    assert res.state_use(a, b2) == (pytest.approx(4.0), "c_free_drop")
    assert res.state_use(a, dict(a))[0] == 0.0


def test_every_snapshot_carries_the_guest_measure(monkeypatch):
    monkeypatch.setattr(res, "c_free_gib", lambda path=None: 40.0)
    monkeypatch.setattr(res, "vhdx_path", lambda: None)
    monkeypatch.setattr(res, "guest_used_bytes", lambda: 7)
    monkeypatch.setattr(res, "uv_cache_bytes", lambda: 1)
    monkeypatch.setattr(res, "docker_df", lambda: [])
    light, heavy = res.snapshot("after_t", heavy=False), res.snapshot("before_t", heavy=True)
    assert light["guest_used_bytes"] == heavy["guest_used_bytes"] == 7 and "uv_cache_bytes" not in light
    b = dict(light, guest_used_bytes=3 * 1024 ** 3, c_free_gib=40.0)
    assert res.state_use(heavy | {"guest_used_bytes": 0}, b)[1] == "guest_used"


def test_no_h2_or_noninferiority_token_is_ever_produced():
    pa = __import__("scripts.wp2_m16_stats", fromlist=["x"]).paired_analysis([(True, False)] * 5 + [(True, True)] * 30)
    assert not any("h2" in k or "inferior" in k for k in pa)
    t = run.tokens_for("M16_OPWS_COMPLETE", pa)
    assert set(t) == {"run_status", "ci_position", "band_position", "method_agreement"}


def test_write_frozen_is_idempotent_and_refuses_different_content(tmp_path):
    p = tmp_path / "f.json"
    assert run.write_frozen(p, run.self_hash({"artifact": "x", "artifact_sha256": "", "v": 1, "utc": "t1"}))
    before = p.read_bytes()
    assert not run.write_frozen(p, run.self_hash({"artifact": "x", "artifact_sha256": "", "v": 1, "utc": "t2"}))
    assert p.read_bytes() == before                                        # resume keeps bytes
    with pytest.raises(run.Stop) as e:
        run.write_frozen(p, run.self_hash({"artifact": "x", "artifact_sha256": "", "v": 2, "utc": "t3"}))
    assert e.value.code == run.EXIT_INVARIANT
    assert run.write_frozen(p, run.self_hash({"artifact": "x", "artifact_sha256": "", "v": 2, "utc": "t3"}),
                            overwrite_if_different=True)


def test_claims_contain_no_winner_or_equivalence_wording():
    base = {"n_analysed": 60, "primary_robust": {"tango_95": [-0.05, 0.12], "delta_hat": 0.03,
                                                 "mcnemar_exact_p": 0.5}}
    for ci in ("DIFFERENCE_CI_INCLUDES_ZERO", "DIFFERENCE_CI_EXCLUDES_ZERO_POSITIVE",
               "DIFFERENCE_CI_EXCLUDES_ZERO_NEGATIVE"):
        for band in ("CI_INSIDE_DESCRIPTIVE_BAND", "CI_CROSSES_BAND_EDGE", "CI_WIDER_THAN_BAND", "CI_OUTSIDE_BAND"):
            a = dict(base, tokens={"run_status": "M16_OPWS_COMPLETE", "ci_position": ci, "band_position": band,
                                   "method_agreement": "DISCORDANT"})
            lines = run.claim_text(a)
            assert run.forbidden_hits(lines) == []
            assert run.SCOPE_CLAUSE in lines[0]
    assert run.forbidden_hits(["RM-CSS is non-inferior to the Agent"]) == ["non-inferior"]
    assert run.forbidden_hits(["the two are equivalent"]) == ["equivalent"]


def test_tokens_not_issued_unless_complete():
    pr = {"n": 30, "ci_position": "DIFFERENCE_CI_INCLUDES_ZERO", "band_position": "CI_WIDER_THAN_BAND",
          "method_agreement": "CONCORDANT"}
    t = run.tokens_for("M16_POOL_INSUFFICIENT_DESCRIPTIVE_ONLY", pr)
    assert t["ci_position"] == t["band_position"] == "NOT_ISSUED"
    assert run.tokens_for("M16_OPWS_COMPLETE", pr)["ci_position"] == "DIFFERENCE_CI_INCLUDES_ZERO"


def _git(cwd: Path, *a: str) -> str:
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout


def test_pushed_tag_requires_unique_pushed_ancestor(tmp_path, monkeypatch):
    repo, origin = tmp_path / "r", tmp_path / "o.git"
    repo.mkdir()
    _git(tmp_path, "init", "-q", "--bare", str(origin))
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@x")
    _git(repo, "config", "user.name", "t")
    (repo / "m.json").write_text("{}\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "c1")
    _git(repo, "remote", "add", "origin", str(origin))
    _git(repo, "push", "-q", "origin", "main")
    monkeypatch.setattr(run, "PROJECT", repo)
    _git(repo, "tag", "-a", "wp2-m16-v1-ready", "-m", "r")
    with pytest.raises(run.Stop) as e:
        run.pushed_tag("wp2-m16-v1-ready", [repo / "m.json"])          # not on origin yet
    assert e.value.code == run.EXIT_TAG
    _git(repo, "push", "-q", "origin", "refs/tags/wp2-m16-v1-ready")
    info = run.pushed_tag("wp2-m16-v1-ready", [repo / "m.json"])
    assert info["commit"] == _git(repo, "rev-parse", "HEAD").strip() and "wp2-m16-v1-ready" in info["ls_remote"]
    _git(repo, "tag", "-a", "wp2-m16-v1-ready-2", "-m", "dup")
    _git(repo, "push", "-q", "origin", "refs/tags/wp2-m16-v1-ready-2")
    with pytest.raises(run.Stop):
        run.pushed_tag("wp2-m16-v1-ready", [repo / "m.json"])          # two READY tags -> refused
    (repo / "m.json").write_text('{"changed": 1}\n')
    _git(repo, "tag", "-d", "wp2-m16-v1-ready-2")
    _git(repo, "push", "-q", "origin", ":refs/tags/wp2-m16-v1-ready-2")
    with pytest.raises(run.Stop):
        run.pushed_tag("wp2-m16-v1-ready", [repo / "m.json"])          # working tree differs from tag
