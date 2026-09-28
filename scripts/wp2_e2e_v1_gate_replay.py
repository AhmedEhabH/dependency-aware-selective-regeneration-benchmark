#!/usr/bin/env python3
"""Mission-12 C1: mechanical replay of the preregistered Smoke-v1 SG gates.

Loads the frozen gate rules from smoke_freeze.json and the frozen numbers from
smoke_summary.json, applies the gates WITHOUT interpretation, then folds in the
reproduced instrument defects (instrument_defects_v1.json) to derive the
corrected v1 token. Read-only against v1 except the erratum output dir.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
V1 = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"
ERRATUM = V1 / "erratum"


def load(name: str) -> dict:
    return json.loads((V1 / name).read_text(encoding="utf-8"))


def main() -> None:
    freeze = load("smoke_freeze.json")
    summary = load("smoke_summary.json")
    defects = json.loads((ERRATUM / "instrument_defects_v1.json").read_text(encoding="utf-8"))

    gates = freeze["smoke_gates"]
    original_gates = summary["gates"]
    resolved = {k: v["resolved"] for k, v in summary["per_arm"].items()}
    spend = summary["spend_usd"]

    df_reproduced = {k: defects["defects"][k]["reproduced"] for k in ("df1", "df2", "df3", "df4", "df5")}

    # Mechanical application of the frozen rules.
    sg1_original = original_gates.get("SG1")
    sg2_original = original_gates.get("SG2")
    sg3_original = original_gates.get("SG3")
    sg4_original = original_gates.get("SG4")

    # DF1 violates SG1 evidence integrity (a replay test fixture sits in the real
    # paid evidence root). DF2 violates SG1 instrument validity (repair request
    # deviates from the preregistered Appendix P2 four-message structure).
    sg1_corrected = "FAIL" if (df_reproduced["df1"] or df_reproduced["df2"]) else sg1_original
    sg2_corrected = sg2_original
    sg3_corrected = sg3_original
    sg4_corrected = sg4_original

    original_token = summary["final_token"]
    allowed_tokens = freeze["final_tokens"]
    if sg1_corrected == "FAIL" or sg2_corrected == "FAIL":
        corrected_token = "E2E_SMOKE_INSTRUMENT_INVALID"
    elif sg3_corrected == "FAIL":
        corrected_token = "E2E_SMOKE_INSTRUMENT_INVALID"
    elif sg4_corrected == "FAIL":
        corrected_token = "E2E_SMOKE_FLOOR_EFFECT"
    else:
        corrected_token = "E2E_SMOKE_PIPELINE_VALID"
    assert corrected_token in allowed_tokens, f"{corrected_token} not in frozen token set"

    record = {
        "artifact": "v1_gate_replay",
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frozen_rules": gates,
        "original_result": {
            "gates": original_gates,
            "final_token": original_token,
        },
        "df_reproduced": df_reproduced,
        "sg1_corrected_basis": {
            "DF1_replay_fixture_in_evidence_root": df_reproduced["df1"],
            "DF2_blind_repair_instrument_deviation": df_reproduced["df2"],
        },
        "corrected": {
            "SG1": sg1_corrected,
            "SG2": sg2_corrected,
            "SG3": sg3_corrected,
            "SG4": sg4_corrected,
        },
        "resolved_per_arm": resolved,
        "spend_usd": spend,
        "original_token": original_token,
        "corrected_token": corrected_token,
        "token_rule": "SG1 or SG2 FAIL -> INSTRUMENT_INVALID; SG3 FAIL -> INSTRUMENT_INVALID; SG4 FAIL -> FLOOR_EFFECT; else PIPELINE_VALID",
        "supersedes": "The previous token E2E_SMOKE_FLOOR_EFFECT is superseded by the erratum (not deleted).",
    }
    out = ERRATUM / "v1_gate_replay.json"
    out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    json.loads(out.read_text(encoding="utf-8"))  # integrity: JSON round-trip
    print(f"GATE_REPLAY={out}")
    print(f"ORIGINAL_TOKEN={original_token}")
    print(f"CORRECTED_TOKEN={corrected_token}")
    print(f"GATES_CORRECTED={record['corrected']}")
    print("CHECK=OK")


if __name__ == "__main__":
    main()