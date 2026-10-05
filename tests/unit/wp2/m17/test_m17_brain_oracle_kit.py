from __future__ import annotations

import json
from pathlib import Path


def test_oracle_authorized_plan_stops_at_eligibility():
    plan = json.loads(
        Path("controller/plan_m17_v1_oracle_authorized.json").read_text(encoding="utf-8")
    )
    ids = [phase["id"] for phase in plan["phases"]]
    assert ids == [
        "Q00_KIT_SELFTEST",
        "Q01_GUARD",
        "Q02_ADAPTER_VERIFY",
        "Q03_ORACLE",
        "Q04_ELIGIBILITY_FREEZE",
    ]
    blocked = ["wp1a/sip_rmcss", "agent_run_records", "opws-evaluate", "scopes"]
    assert not any(token in json.dumps(plan).lower() for token in blocked)


def test_qualification_plan_is_loop_and_has_gate():
    plan = json.loads(
        Path("controller/plan_m17_v1_qualification.json").read_text(encoding="utf-8")
    )
    by_id = {phase["id"]: phase for phase in plan["phases"]}
    assert by_id["Q03_QUALIFICATION_RUN"]["kind"] == "loop"
    assert by_id["Q03_QUALIFICATION_RUN"]["done_checks"]
    assert "Q05_QUALIFICATION_GATE" in by_id
    assert by_id["Q05_QUALIFICATION_GATE"]["command"][-1] == "qualification-gate"


def test_exec_script_has_hard_no_selector_commands():
    source = Path("scripts/wp2_m17_exec.py").read_text(encoding="utf-8")
    for token in ("opws-evaluate", "scopes", "analyze", "summary"):
        assert token not in source
    assert "REAL_EXECUTOR_ID" in source
    assert "qualification_gate" in source
