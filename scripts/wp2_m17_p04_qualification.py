#!/usr/bin/env python3
"""M17 P04 - qualification membership freeze (12 tasks), instrument qualification only.

Deterministic, selector-blind:
1. Strata use ONLY era x install-mechanism x historical-schema signature (P01 fields).
2. Nonempty strata are sorted by canonical tuple.
3. Within each stratum, task IDs are ranked by sha256("m17-qualification-2026-10-02|<task_id>").
4. One task per stratum until all strata represented or 12 are selected.
5. Remaining slots (if fewer than 12) are filled globally by the same hash ranking
   from unselected tasks.
6. (No more than 12 strata exist in this frame, so the 12-strata-cap rule is unused.)

Writes research/wp2/m17_v1/m17_qualification_membership.json with the frozen IDs,
the derivation transcript and a membership sha256. No selector outcome is read.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
AUDIT = PROJECT / "research/wp2/m17_v1/m17_main_frame_audit.json"
OUT = PROJECT / "research/wp2/m17_v1/m17_qualification_membership.json"

SALT = "m17-qualification-2026-10-02"
N_TARGET = 12


def _env_path(name: str, default: Path) -> Path:
    import os

    override = os.environ.get(name)
    return Path(override) if override else default


def h(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def canonical_stratum(era: str, mechanism: str, schema: str) -> tuple[str, str, str]:
    return (era, mechanism, schema)


def main() -> int:
    audit_path = _env_path("M17_AUDIT_OVERRIDE", AUDIT)
    out_path = _env_path("M17_OUT_OVERRIDE", OUT)
    import os

    allow_synthetic = os.environ.get("M17_ALLOW_SYNTHETIC_FRAME") == "1"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    tasks = audit["tasks"]
    if not allow_synthetic and (len(tasks) != 220 or audit["frame"]["n_unique_ids"] != 220):
        print("FATAL: census audit is not the frozen 220 frame", file=sys.stderr)
        return 2

    strata: dict[tuple[str, str, str], list[str]] = {}
    for t in tasks:
        key = canonical_stratum(
            t["era_key"],
            t["historical_install_mode"]["manifest_mechanism_derived"],
            t["historical_schema_signature"]["schema"],
        )
        strata.setdefault(key, []).append(t["task_id"])

    for key in strata:
        strata[key].sort(key=lambda tid: h(f"{SALT}|{tid}"))

    ordered_strata = sorted(strata.keys())
    transcript: list[dict] = []
    selected: list[str] = []
    stratum_pick: dict[tuple[str, str, str], str] = {}

    for key in ordered_strata:
        if len(selected) >= N_TARGET:
            break
        tid = strata[key][0]
        selected.append(tid)
        stratum_pick[key] = tid
        transcript.append(
            {"step": "per_stratum", "stratum": list(key), "n_in_stratum": len(strata[key]),
             "chosen": tid, "hash": h(f"{SALT}|{tid}")}
        )

    if len(selected) < N_TARGET:
        remaining = [tid for key in ordered_strata for tid in strata[key] if tid not in selected]
        remaining.sort(key=lambda tid: h(f"{SALT}|{tid}"))
        for tid in remaining:
            if len(selected) >= N_TARGET:
                break
            selected.append(tid)
            transcript.append(
                {"step": "global_backfill", "chosen": tid, "hash": h(f"{SALT}|{tid}")}
            )

    selected_sorted = sorted(selected)
    if len(selected) != N_TARGET or len(set(selected)) != N_TARGET:
        print(f"FATAL: membership not exactly {N_TARGET} unique (got {len(selected)})", file=sys.stderr)
        return 2

    membership = {
        "artifact": "m17_qualification_membership",
        "mission": "M17_P04",
        "date": "2026-10-02",
        "rule": (
            "Instrument qualification only, NOT a scientific sample. Strata = "
            "era x install-mechanism x historical-schema-signature (P01 fields). "
            "One task per stratum by sha256(salt|task_id), then global backfill by "
            "the same ranking. Qualification results never determine READY membership "
            "or scientific thresholds."
        ),
        "salt": SALT,
        "n_target": N_TARGET,
        "n_strata": len(ordered_strata),
        "strata": {",".join(k): {"count": len(strata[k]), "ids": strata[k]} for k in ordered_strata},
        "stratum_selection": {",".join(k): v for k, v in stratum_pick.items()},
        "membership": selected_sorted,
        "membership_sha256": h(json.dumps(selected_sorted, sort_keys=True)),
        "derivation_transcript": transcript,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(membership, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"M17_P04_QUAL_MEMBERSHIP_PASS n={len(selected_sorted)} strata={len(ordered_strata)} "
          f"sha={membership['membership_sha256']}")
    print("MEMBERS:", " ".join(selected_sorted))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
