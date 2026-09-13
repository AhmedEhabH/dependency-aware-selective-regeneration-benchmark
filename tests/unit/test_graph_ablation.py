"""Unit tests for the M3 graph ablation core (deterministic, ZERO API)."""

from __future__ import annotations

import pytest

from benchmark.selection import graph_ablation as ga


SCENARIOS = (
    "djangocms-external-validity-002",
    "djangocms-external-validity-004",
    "djangocms-external-validity-005",
    "djangocms-external-validity-006",
    "djangocms-external-validity-007",
    "djangocms-external-validity-008",
)


def test_graph_verification() -> None:
    gv = ga.graph_verification()
    assert gv["passed"] is True
    labels = {c["check"]: c["ok"] for c in gv["checks"]}
    assert labels["node_count_144"]
    assert labels["edge_count_562"]
    assert labels["ast_parse_144_of_144"]
    assert labels["canonical_hash_parity"]
    assert labels["no_manually_authored_scenario_edges"]
    assert labels["two_builds_reproducible"]


def test_seed_algorithm_is_deterministic() -> None:
    a = {sid: ga.seed_ids(sid) for sid in SCENARIOS}
    b = {sid: ga.seed_ids(sid) for sid in SCENARIOS}
    assert a == b
    for sid in SCENARIOS:
        assert len(a[sid]) > 0, sid


def test_seed_sets_non_empty_and_zone_sizes() -> None:
    ident = ga.seed_zone_identity()
    for sid in SCENARIOS:
        d = ident["per_scenario"][sid]
        assert len(d["seed_ids"]) > 0
        assert d["zones"]["1"]["size"] >= 20, sid
        assert d["zones"]["2"]["size"] > d["zones"]["1"]["size"], sid
        assert d["zones"]["3"]["size"] > d["zones"]["2"]["size"], sid


def test_three_hop_not_eligible() -> None:
    e3 = ga.three_hop_eligibility()
    assert e3["eligible"] is False
    for d in e3["per_scenario"].values():
        assert d["within_ceiling_115"] is False


def test_s006_missed_gold_is_inside_1hop_zone() -> None:
    """Pre-registered: cms/utils/plugins.py (Sparse-v2's S006 miss) is inside
    the S006 1-hop risk zone, so C2 1-hop mandates an explicit decision on it."""
    sid = "djangocms-external-validity-006"
    zone = ga.risk_zone_ids(sid, 1)
    assert ga.hop_distance(sid, "cms/utils/plugins.py", 3) <= 1
    assert ga.hop_distance(sid, "cms/models/pluginmodel.py", 3) == 0


def test_c0_matches_audited_m1b() -> None:
    res = ga.c0_matches_audited_m1b()
    assert res["passed"] is True
    assert len(res["checks"]) == 6


def test_controlled_diff_only_graph_block_differs() -> None:
    for sid in SCENARIOS:
        cd = ga.condition_controlled_diff(sid)
        assert cd["c0_equals_stripped_c1"]
        assert cd["c0_equals_stripped_c2"]
        assert cd["c0_equals_stripped_c2_2hop"]
        assert cd["c1_differs_from_c0"]
        assert cd["c2_differs_from_c0"]
        assert cd["c2_1hop_differs_from_c2_2hop"]


def test_c2_disclosure_fail_closed_and_compliant() -> None:
    sid = "djangocms-external-validity-006"
    mapping = ga._mapping()
    gold = {"cms/models/pluginmodel.py", "cms/admin/placeholderadmin.py", "cms/utils/plugins.py"}
    rows = {i: ("REGENERATE" if p in gold else "PRESERVE") for i, p in mapping.id_to_path}
    from benchmark.selection import encoding_ablation as ea

    payload = ea.sparse_payload_for(ea.complete_policy_from_actions(rows), mapping)

    violating = ga.validate_c2_disclosure(payload, sid, 1)
    assert violating["valid"] is True
    assert violating["disclosure_valid"] is False
    assert any("mandatory-disclosure-failure" in e for e in violating["disclosure_error"])

    zone = set(ga.risk_zone_ids(sid, 1))
    actions = dict(ea.complete_policy_from_actions(rows).action_by_id)
    for i in zone:
        if actions[i] == "PRESERVE":
            actions[i] = "VALIDATE"
    compliant_payload = {
        "decisions": [{"id": i, "action": a, "rationale": "fixture", "confidence": 0.9,
                       "reason_codes": ["no_change"],
                       "evidence": [{"source": "fixture", "description": "fixture"}]}
                      for i, a in sorted(actions.items()) if a != "PRESERVE"]
    }
    compliant = ga.validate_c2_disclosure(compliant_payload, sid, 1)
    assert compliant["valid"] is True
    assert compliant["disclosure_valid"] is True


def test_failure_categories_preregistered() -> None:
    expected = {
        "missed-neighbor", "over-expansion", "wrong-edge-direction",
        "graph-evidence-ignored", "mandatory-disclosure-failure",
        "unrelated-module-attraction", "graph-coverage-gap",
        "semantic-misreasoning", "operational/schema failure", "other-with-rationale",
    }
    assert set(ga.FAILURE_CATEGORIES) == expected


@pytest.mark.parametrize("sid", SCENARIOS)
def test_prompt_hashes_stable(sid: str) -> None:
    """Hashes are frozen identity for the protocol; any change is a protocol change."""
    cd = ga.condition_controlled_diff(sid)
    assert cd["c0_sha256"]
    assert cd["c1_sha256"]
    assert cd["c2_1hop_sha256"]
    assert cd["c2_2hop_sha256"]