"""M13B atomic engine: selection, replacement rule, gates, task map (zero network, no repo data)."""
from __future__ import annotations

import importlib.util
import json
import socket
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[4]


def load():
    spec = importlib.util.spec_from_file_location("m13", PROJECT / "scripts" / "wp2_m13.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(socket.socket, "connect", boom)


def fake_pool(n_by_era: dict[str, int]) -> list[dict]:
    out = []
    for era, n in n_by_era.items():
        for i in range(n):
            out.append({"task_id": f"saleor-rc-{era}{i:08d}", "era_key": era})
    return out


def test_quota_sums_and_respects_caps():
    m = load()
    q = m.largest_remainder_quota({"py39": 17, "py312": 7, "py38": 2}, 24)
    assert sum(q.values()) == 24 and all(q[k] <= v for k, v in {"py39": 17, "py312": 7,
                                                                  "py38": 2}.items())
    with pytest.raises(m.Stop):
        m.largest_remainder_quota({"py39": 5}, 24)


def test_select_is_deterministic_disjoint_and_sized():
    m = load()
    pool = fake_pool({"py39": 17, "py312": 7, "py38": 2})
    s1, s2 = m.select_from(pool), m.select_from(list(reversed(pool)))
    assert s1 == s2
    assert len(s1["A"]) == len(s1["B"]) == 12 and not set(s1["A"]) & set(s1["B"])
    assert len(s1["reserve"]) == 2
    assert set(s1["A"]) | set(s1["B"]) | set(s1["reserve"]) == {x["task_id"] for x in pool}


def test_replacement_rule_all_cases():
    m = load()
    a = [f"a{i}" for i in range(12)]
    b = [f"b{i}" for i in range(12)]
    r = ["r0", "r1"]
    everyone = set(a) | set(b) | set(r)
    full = m.finalize_after_readiness(a, b, r, everyone)
    assert full["verdict"] == "FULL" and full["A"] == a and full["reserve_used"] == []
    one = m.finalize_after_readiness(a, b, r, everyone - {"a3"})
    assert one["verdict"] == "FULL" and one["A"][-1] == "r0" and "a3" not in one["A"]
    two = m.finalize_after_readiness(a, b, r, everyone - {"a3", "b5"})
    assert two["verdict"] == "FULL" and two["reserve_used"] == ["r0", "r1"]
    assert "r0" in two["A"] and "r1" in two["B"]
    three = m.finalize_after_readiness(a, b, r, everyone - {"a1", "a2", "b0"})
    assert three["verdict"] == "REDUCED_11"
    assert len(three["A"]) == len(three["B"]) == 11 and three["dropped"] == ["r1"]
    bad = m.finalize_after_readiness(a, b, r, everyone - {f"a{i}" for i in range(5)})
    assert bad["verdict"] == "POOL_INSUFFICIENT"
    # never uses a not-ready reserve task
    nr = m.finalize_after_readiness(a, b, r, everyone - {"a0", "r0"})
    assert "r0" not in nr["A"] + nr["B"] and nr["verdict"] == "FULL"


def test_replacement_never_reorders_selected_tasks():
    m = load()
    a = [f"a{i}" for i in range(12)]
    b = [f"b{i}" for i in range(12)]
    out = m.finalize_after_readiness(a, b, ["r0", "r1"], (set(a) | set(b) | {"r0", "r1"}) - {"a4"})
    assert out["A"][:11] == [t for t in a if t != "a4"]


def test_gates_scale_and_calibration():
    m = load()
    g = m.gates_for(12)
    assert g == {"episodes_per_arm": 24, "A2_gold_applied_min": 14, "A3_gold_resolved_min": 3,
                 "A4_placebo_resolved_max": 1, "A5_gold_minus_placebo_min": 2}
    g10 = m.gates_for(10)
    assert g10["episodes_per_arm"] == 20 and g10["A3_gold_resolved_min"] == 3
    cal = m.gate_pass_probabilities(12)
    assert cal["P(A3 pass | gold_rate=0.2)"] > cal["reference_old_gate_P(>=4/24 | 0.20)"]
    assert cal["P(A3 pass | gold_rate=0.2)"] >= 0.85


def test_binomial_helpers():
    m = load()
    assert abs(m.binom_tail_ge(10, 0.5, 0) - 1.0) < 1e-12
    assert abs(m.binom_cdf_le(10, 0.5, 10) - 1.0) < 1e-12
    assert abs(m.binom_tail_ge(24, 0.2, 4) - 0.736) < 0.001


def test_real_task_map_is_valid_and_matches_plan():
    m = load()
    tm = json.loads((PROJECT / "controller" / "task_map_m13_m16_v1.json").read_text())
    plan = json.loads((PROJECT / "controller" / "plan_m13_pilot_prep_v1.json").read_text())
    assert m.validate_task_map(tm, plan) == []
    ids = [a["id"] for t in tm["tasks"] for s in t["subtasks"] for a in s["atomics"]]
    assert "P09_VERIFY" in ids and "M14A.S0.A2" in ids and "M15.S0.A2" in ids
    md = m.map_md(tm)
    assert "| P05_SELECT |" in md


def test_task_map_validator_catches_defects():
    m = load()
    tm = json.loads((PROJECT / "controller" / "task_map_m13_m16_v1.json").read_text())
    a = tm["tasks"][0]["subtasks"][1]["atomics"][0]
    a["on_pass"] = "NOWHERE"
    del a["checks"]
    bad = m.validate_task_map(tm)
    assert any("unknown NOWHERE" in x for x in bad) and any("missing checks" in x for x in bad)


def test_json_sha_and_norm_sha(tmp_path):
    m = load()
    p = tmp_path / "x.txt"
    p.write_bytes(b"a\r\nb\r\n")
    q = tmp_path / "y.txt"
    q.write_bytes(b"a\nb\n")
    assert m.norm_sha(p) == m.norm_sha(q)
    assert m.json_sha({"b": 1, "a": 2}) == m.json_sha({"a": 2, "b": 1})


def test_engine_is_zero_api_by_construction():
    txt = (PROJECT / "scripts" / "wp2_m13.py").read_text()
    for needle in ("openrouter", "urllib.request", "requests.", "wsl", "docker"):
        assert needle not in txt.lower().replace("zero docker/wsl", "")
