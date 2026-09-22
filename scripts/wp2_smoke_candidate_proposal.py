#!/usr/bin/env python3
"""Deterministic WP-2 Smoke candidate proposal (ZERO API, outcome-blind).

Reads the WP-2 MAIN_297 census and proposes 5-10 Smoke candidates using only
transparent deterministic rules (changed-file structure; never RM-CSS/Agent
success, never E2E outcome). Group A favored, changed-file count diversity,
tie-break by SHA-256 of a fixed salt + task_id.

Usage:
  python scripts/wp2_smoke_candidate_proposal.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
CENSUS = (
    _PROJECT_DIR
    / "research"
    / "wp2"
    / "wp2_saleor_main297_census_2026-09-22.json"
)
OUT = _PROJECT_DIR / "research" / "wp2" / "wp2_smoke_candidate_proposal_2026-09-22.json"

SALT = "wp2-smoke-proposal-v1-2026-09-22"
GROUP_A_CAP = 6
GROUP_B_CAP = 1
GROUP_C_CAP = 1
TOTAL_CAP = 8


def tie_key(task_id: str) -> str:
    return hashlib.sha256(f"{SALT}+{task_id}".encode()).hexdigest()


def main() -> int:
    data = json.loads(CENSUS.read_text(encoding="utf-8"))
    tasks = [t for t in data["tasks"] if t["status"] == "OK"]

    def group_of(t: dict) -> str:
        f2p = t["f2p_candidacy"]
        heavy = t["n_migration"] > 0 or t["n_config_or_infra"] > 0
        if f2p in ("STRONG_F2P_CANDIDATE", "MODIFIED_TEST_CANDIDATE") and not heavy:
            return "A"
        if f2p in ("STRONG_F2P_CANDIDATE", "MODIFIED_TEST_CANDIDATE") and heavy:
            return "B"
        if f2p == "NO_CHANGED_TEST_EVIDENCE":
            return "C"
        return "D"

    groups: dict[str, list[dict]] = {"A": [], "B": [], "C": [], "D": []}
    for t in tasks:
        groups[group_of(t)].append(t)

    counts = {k: len(v) for k, v in groups.items()}

    def pick(group: list[dict], cap: int) -> list[dict]:
        ordered = sorted(group, key=lambda t: tie_key(t["task_id"]))
        return ordered[:cap]

    a = pick(groups["A"], GROUP_A_CAP)
    b = pick(groups["B"], GROUP_B_CAP)
    c = pick(groups["C"], GROUP_C_CAP)

    # Deterministic Group-A favoritism: if the group-A pool contains at least one
    # STRONG_F2P_CANDIDATE, always include the top STRONG candidate (by tie-key)
    # in the proposal so the Smoke set is not all-MODIFIED_TEST_CANDIDATE.
    strong_a = [t for t in groups["A"] if t["f2p_candidacy"] == "STRONG_F2P_CANDIDATE"]
    if strong_a and all(t["f2p_candidacy"] != "STRONG_F2P_CANDIDATE" for t in a):
        top_strong = min(strong_a, key=lambda t: tie_key(t["task_id"]))
        # replace the last (lowest tie-key) group-A pick deterministically
        a_sorted = sorted(a, key=lambda t: tie_key(t["task_id"]))
        a_sorted[-1] = top_strong
        a = a_sorted

    # change-count diversity guard for Group A: if the first picks are all in the
    # same n_changed band, swap in a higher-variance pick deterministically.
    def diversity_swap(chosen: list[dict], pool: list[dict], n_changed_target: int) -> list[dict]:
        chosen_ids = {t["task_id"] for t in chosen}
        rest = [t for t in pool if t["task_id"] not in chosen_ids]
        if not rest:
            return chosen
        rest_sorted = sorted(rest, key=lambda t: tie_key(t["task_id"]))
        for t in rest_sorted:
            if t["n_changed"] >= n_changed_target:
                chosen[0] = t
                break
        return chosen

    if a and len(groups["A"]) > GROUP_A_CAP and max(t["n_changed"] for t in a) <= 2:
        a = diversity_swap(a, groups["A"], n_changed_target=4)

    candidates = sorted(a + b + c, key=lambda t: tie_key(t["task_id"]))[:TOTAL_CAP]

    payload = {
        "artifact": "wp2_smoke_candidate_proposal",
        "date": "2026-09-22",
        "status": "SMOKE_CANDIDATE_PROPOSAL_ONLY",
        "not_a_frozen_scientific_sample": True,
        "requires_brain_ahmed_review": True,
        "method": {
            "source": "research/wp2/wp2_saleor_main297_census_2026-09-22.json",
            "rules": [
                "Group A: added/modified target tests, no migration/config-heavy marker",
                "Group B: changed tests + migration/config-heavy",
                "Group C: no changed test evidence",
                "Group D: metadata/materialization problem (if any)",
                "selection favors Group A; includes diversity in changed-file count; "
                "never selects by RM-CSS/Agent success/failure; never selects by E2E outcome "
                "(none exist); tie-break by SHA-256 of fixed salt + task_id; if any Group-A "
                "STRONG_F2P_CANDIDATE exists, the top one (by tie-key) is always included",
            ],
            "tie_break_salt": SALT,
            "candidate_count": TOTAL_CAP,
            "group_a_cap": GROUP_A_CAP,
            "group_b_cap": GROUP_B_CAP,
            "group_c_cap": GROUP_C_CAP,
        },
        "groups": {
            "A": {
                "rule": "f2p_candidacy in {STRONG_F2P_CANDIDATE, MODIFIED_TEST_CANDIDATE} "
                "and n_migration == 0 and n_config_or_infra == 0",
                "n": counts["A"],
            },
            "B": {
                "rule": "f2p_candidacy in {STRONG_F2P_CANDIDATE, MODIFIED_TEST_CANDIDATE} "
                "and (n_migration > 0 or n_config_or_infra > 0)",
                "n": counts["B"],
            },
            "C": {
                "rule": "f2p_candidacy == NO_CHANGED_TEST_EVIDENCE",
                "n": counts["C"],
            },
            "D": {
                "rule": "status != OK (metadata/materialization problem), if any",
                "n": counts["D"],
            },
        },
        "proposed_candidates": [
            {
                "task_id": t["task_id"],
                "group": group_of(t),
                "f2p_candidacy": t["f2p_candidacy"],
                "n_changed": t["n_changed"],
                "n_test_added": t["n_test_added"],
                "n_test_modified": t["n_test_modified"],
                "n_migration": t["n_migration"],
                "n_config_or_infra": t["n_config_or_infra"],
                "tie_key": tie_key(t["task_id"]),
                "rationale": "deterministic structural selection; outcome-blind",
            }
            for t in candidates
        ],
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[wp2] proposal written with {len(candidates)} candidates")
    for t in candidates:
        print(
            f"  {t['task_id']} group={group_of(t)} f2p={t['f2p_candidacy']} "
            f"n_changed={t['n_changed']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
