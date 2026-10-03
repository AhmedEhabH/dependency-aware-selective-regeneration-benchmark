"""M17 P06/P08 - zero-Docker controller simulation (state machine, no Docker/WSL/API).

Simulates the qualification controller phases as a pure state machine over the
controller plan: normal run, resumable infra stop, resource-review state,
collision/restart, and the selector-blind ordering guarantee (Q08 scopes only
after the pushed READY freeze).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

QUAL_PLAN = P / "controller/plan_m17_v1_qualification.json"
MAIN_PLAN = P / "controller/plan_m17_v1_main.json"

DONE = "DONE"
PENDING = "PENDING"
STOPPED = "STOPPED"


class SimController:
    """Minimal deterministic controller state machine over a plan."""

    def __init__(self, plan: dict, resumable: bool = True) -> None:
        self.phases = [ph["id"] for ph in plan["phases"]]
        self.req = {ph["id"]: ph.get("requires", []) for ph in plan["phases"]}
        self.status = {ph_id: PENDING for ph_id in self.phases}
        self.resumable = resumable

    def run(self, stop_at: str | None = None) -> tuple[dict, str | None]:
        """Run until completion or a STOP. Returns (status, stop_phase)."""
        for ph_id in self.phases:
            deps = self.req[ph_id]
            if any(self.status[d] != DONE for d in deps):
                self.status[ph_id] = STOPPED
                return self.status, ph_id
            self.status[ph_id] = DONE
            if ph_id == stop_at:
                self.status[ph_id] = STOPPED
                return self.status, ph_id
        return self.status, None

    def resume(self, from_phase: str) -> tuple[dict, str | None]:
        """Resume after a resumable stop: re-enter the stopped phase."""
        if not self.resumable:
            raise AssertionError("non-resumable stop cannot resume")
        self.status[from_phase] = PENDING
        for ph_id in self.phases:
            if self.status[ph_id] == PENDING and ph_id >= from_phase:
                deps = self.req[ph_id]
                if any(self.status[d] != DONE for d in deps):
                    continue
                self.status[ph_id] = DONE
        return self.status, None


def test_qualification_plan_phases_sequential():
    plan = json.loads(QUAL_PLAN.read_text(encoding="utf-8"))
    ids = [ph["id"] for ph in plan["phases"]]
    assert ids == ["Q00_KIT_SELFTEST", "Q01_GUARD", "Q02_ADAPTER_VERIFY",
                   "Q03_QUALIFICATION_RUN", "Q04_QUALIFICATION_REPORT", "Q05_RESOURCE_PROJECTION"]
    for ph in plan["phases"]:
        assert ph["id"] not in ("Q08_SCOPES", "Q09_OPWS")  # qualification never materializes scopes


def test_qualification_normal_run():
    plan = json.loads(QUAL_PLAN.read_text(encoding="utf-8"))
    sim = SimController(plan)
    status, stop = sim.run()
    assert stop is None
    assert all(v == DONE for v in status.values())


def test_qualification_resumable_infra_stop():
    plan = json.loads(QUAL_PLAN.read_text(encoding="utf-8"))
    sim = SimController(plan, resumable=True)
    status, stop = sim.run(stop_at="Q03_QUALIFICATION_RUN")
    assert stop == "Q03_QUALIFICATION_RUN"
    assert status["Q03_QUALIFICATION_RUN"] == STOPPED
    status2, stop2 = sim.resume("Q03_QUALIFICATION_RUN")
    assert stop2 is None
    assert all(v == DONE for v in status2.values())


def test_qualification_non_resumable_stop():
    plan = json.loads(QUAL_PLAN.read_text(encoding="utf-8"))
    sim = SimController(plan, resumable=False)
    _, stop = sim.run(stop_at="Q02_ADAPTER_VERIFY")
    assert stop == "Q02_ADAPTER_VERIFY"
    with pytest.raises(AssertionError):
        sim.resume("Q02_ADAPTER_VERIFY")


def test_resource_review_state_maps_to_m17_resume_token():
    plan = json.loads(QUAL_PLAN.read_text(encoding="utf-8"))
    q05 = [ph for ph in plan["phases"] if ph["id"] == "Q05_RESOURCE_PROJECTION"][0]
    assert q05["fail_token"] == "M17_RESOURCE_REVIEW"
    assert "M17_RESOURCE_GATE" in plan["settings"]["resumable_tokens"]


def test_main_plan_scopes_only_after_ready_freeze():
    plan = json.loads(MAIN_PLAN.read_text(encoding="utf-8"))
    ids = [ph["id"] for ph in plan["phases"]]
    assert "Q07_READY_FREEZE" in ids and "Q08_SCOPES" in ids and "Q09_OPWS" in ids
    q08 = [ph for ph in plan["phases"] if ph["id"] == "Q08_SCOPES"][0]
    assert "Q07_READY_FREEZE" in q08["requires"]
    assert "Q09_OPWS" not in q08["requires"]
    # selector-blind ordering: OPWS depends on scopes; scopes depend on READY freeze
    q09 = [ph for ph in plan["phases"] if ph["id"] == "Q09_OPWS"][0]
    assert "Q08_SCOPES" in q09["requires"]


def test_main_plan_has_no_early_stop():
    plan = json.loads(MAIN_PLAN.read_text(encoding="utf-8"))
    assert plan["status"] == "DESIGN_ONLY_NOT_AUTHORIZED"


def test_collision_restart_same_state_is_deterministic():
    plan = json.loads(QUAL_PLAN.read_text(encoding="utf-8"))
    s1 = SimController(plan).run(stop_at="Q03_QUALIFICATION_RUN")[0]
    s2 = SimController(plan).run(stop_at="Q03_QUALIFICATION_RUN")[0]
    assert s1 == s2


def test_no_selector_file_opened_before_q08(tmp_path):
    # The plans' allowed write prefixes never touch scopes/opws before Q08 in MAIN;
    # in qualification they never appear at all.
    qplan = json.loads(QUAL_PLAN.read_text(encoding="utf-8"))
    for ph in qplan["phases"]:
        assert not any("scopes" in w or "opws" in w for w in ph.get("allowed_write_prefixes", []))
    mplan = json.loads(MAIN_PLAN.read_text(encoding="utf-8"))
    for ph in mplan["phases"]:
        writes = ph.get("allowed_write_prefixes", [])
        if ph["id"] not in ("Q08_SCOPES", "Q09_OPWS"):
            assert not any("scopes" in w or "opws" in w for w in writes)
