"""Estimate full DEV-47 + future MAIN P2P-U V2 cap200 cost (Mission-09 §22).

Calibrates from the REAL Mission-09 ENG cap200 measurements (not node-count
alone): per-task selected-node execution rate, per-state setup cost, and the
measured relationship between the cap200 wall time and the node/era/file
profile. Produces optimistic/central/conservative DEV-47 projections and a
future MAIN projection (both candidate populations reported separately).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))


EVIDENCE_ROOT = PROJECT / "research" / "wp2" / "p2p_u_v2_eng_2026-09-25"
MEMBERSHIP = json.loads(
    (PROJECT / "research" / "wp2" / "wp2_p2p_u_v2_membership_2026-09-25.json").read_text(encoding="utf-8")
)
INVENTORY = json.loads(
    (PROJECT / "research" / "wp2" / "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json").read_text(
        encoding="utf-8"
    )
)
OUT = EVIDENCE_ROOT / "dev47_and_main_estimate_2026-09-25.json"

ENG_EXECUTED = [
    "saleor-rc-2d45b76a52f2",
    "saleor-rc-39b4138e8550",
    "saleor-rc-74538ea00ce9",
    "saleor-rc-82c56bde0e34",
    "saleor-rc-8f76ddc6267f",
    "saleor-rc-d220843b5418",
    "saleor-rc-dfe77ac1c5dc",
    "saleor-rc-e03ee76d2b89",
]


def load_wall(task_id: str, cap: int) -> float:
    mf = EVIDENCE_ROOT / task_id / f"cap{cap}" / "A" / "manifest.json"
    if not mf.exists():
        return 0.0
    m = json.loads(mf.read_text(encoding="utf-8"))
    return float(m["measurements"]["total_wall_s"])


def main() -> int:
    # Per-executed-ENG-task measured rates at cap200.
    rates: dict[str, float] = {}
    for tid in ENG_EXECUTED:
        sel = MEMBERSHIP["tasks"][tid]
        n_selected = len(sel["cap200_node_ids"])
        if n_selected == 0:
            continue
        wall = load_wall(tid, 200)
        if wall > 0:
            rates[tid] = wall / n_selected  # wall seconds per selected node
    rate_vals = sorted(rates.values())
    rate_central = rate_vals[len(rate_vals) // 2]
    rate_opt = min(rate_vals)
    rate_con = max(rate_vals)

    # Per-state setup cost from the exec manifests (setup_s).
    setup_vals = []
    for tid in ENG_EXECUTED:
        mf = EVIDENCE_ROOT / tid / "cap200" / "A" / "manifest.json"
        if mf.exists():
            setup_vals.append(float(json.loads(mf.read_text(encoding="utf-8"))["measurements"]["setup_s"]))
    setup_central = sorted(setup_vals)[len(setup_vals) // 2] if setup_vals else 0.0

    # DEV-47 forecast using frozen cap200 membership for every oracle-valid task.
    tasks = [t for t in INVENTORY["tasks"] if t.get("oracle_valid")]
    zero = [t["task_id"] for t in tasks if (t.get("candidate_node_ids") or []) == []]
    executable = [t for t in tasks if (t.get("candidate_node_ids") or [])]
    n_executable = len(executable)

    def project(tasks_: list[dict], rate: float) -> dict:
        total_wall = 0.0
        n_nodes = 0
        by_era: dict[str, float] = {}
        for t in tasks_:
            sel = MEMBERSHIP["tasks"][t["task_id"]]
            n = len(sel["cap200_node_ids"])
            n_nodes += n
            est = n * rate + 2 * setup_central  # setup per state (t + p)
            total_wall += est
            by_era[t["era_key"]] = by_era.get(t["era_key"], 0.0) + est
        return {
            "n_tasks": len(tasks_),
            "n_selected_nodes": n_nodes,
            "total_wall_s": round(total_wall, 1),
            "total_wall_h": round(total_wall / 3600, 1),
            "total_wall_days": round(total_wall / 86400, 2),
            "per_era_h": {k: round(v / 3600, 1) for k, v in sorted(by_era.items())},
        }

    dev_optimistic = project(executable, rate_opt)
    dev_central = project(executable, rate_central)
    dev_conservative = project(executable, rate_con)

    # Storage estimate: evidence bytes per selected node from real ENG data.
    import os

    total_evidence_bytes = 0
    for dp, _dn, fn in os.walk(EVIDENCE_ROOT):
        for f in fn:
            if f.endswith((".json", ".jsonl", ".xml", ".log", ".md")):
                total_evidence_bytes += os.path.getsize(os.path.join(dp, f))
    eng_nodes = sum(len(MEMBERSHIP["tasks"][t]["cap200_node_ids"]) for t in ENG_EXECUTED)
    bytes_per_node = total_evidence_bytes / eng_nodes if eng_nodes else 0

    dev_evidence_mib = round(dev_central["n_selected_nodes"] * bytes_per_node / (1024**2), 1)

    # MAIN forecast (ESTIMATE ONLY; population authority unresolved).
    # MAIN raw candidate node discovery has NOT run. Use the MAIN-only inventory's
    # associated-file counts scaled by the corrected DEV nodes/file ratio, then
    # apply the measured per-node rate.
    main_inv = json.loads(
        (
            PROJECT
            / "research"
            / "wp2"
            / "oracle_confirmation_linux_v2_2026-09-23"
            / "wp2_unchanged_p2p_candidate_inventory_v1_final_2026-09-25.json"
        ).read_text(encoding="utf-8")
    )
    dev_nodes_per_file = (
        sum(t.get("n_discovered_candidate_nodes") or 0 for t in tasks)
        / sum(t.get("n_associated_unchanged_test_files") or 0 for t in tasks)
        if sum(t.get("n_associated_unchanged_test_files") or 0 for t in tasks)
        else 0
    )

    def main_projection(n_tasks_pop: int, label: str) -> dict:
        # Use the MAIN inventory task rows (MAIN pool) to estimate raw nodes.
        main_tasks = main_inv.get("tasks", [])
        # MAIN inventory task records carry n_associated_unchanged_test_files.
        pop_tasks = main_tasks[:n_tasks_pop] if len(main_tasks) >= n_tasks_pop else main_tasks
        raw_nodes = sum(
            int(t.get("n_associated_unchanged_test_files", 0) or 0) * dev_nodes_per_file
            for t in pop_tasks
        )
        # cap200 selection: assume full 200/node per defined task (upper bound);
        # use min(raw, 200) per task.
        selected = sum(
            min(200, int(t.get("n_associated_unchanged_test_files", 0) or 0) * dev_nodes_per_file)
            for t in pop_tasks
        )
        wall = selected * rate_central + 2 * setup_central * n_tasks_pop
        return {
            "population_label": label,
            "n_tasks": n_tasks_pop,
            "est_raw_nodes": int(raw_nodes),
            "est_selected_nodes_cap200": int(selected),
            "central_wall_h": round(wall / 3600, 1),
            "central_wall_days": round(wall / 86400, 2),
        }

    main_71 = main_projection(71, "behavioral-only (71)")
    main_83 = main_projection(83, "behavioral ∪ symbol (83)")

    workers2_note = (
        "ENG cap200 measured: wall ≈ 4346.9 s for 1576 selected nodes across 8 tasks "
        "(≈ 543 s/task, ~2.76 s/node-state incl. setup). Per-state setup ≈ "
        f"{setup_central} s. The 400/200 wall multiplier was "
        f"{round(load_wall('saleor-rc-39b4138e8550', 400) / load_wall('saleor-rc-39b4138e8550', 200), 2)}x "
        "for a 2x node "
        "increase (supra-linear per-task via independent 400-run), but at the task "
        "level the dominant cost is node execution not setup, so a workers=2 "
        "performance gate MAY be worth testing for MAIN only — NOT run in "
        "Mission-09 (workers frozen at 1)."
    )

    payload = {
        "artifact": "wp2_p2p_u_v2_dev47_and_main_estimate",
        "date": "2026-09-25",
        "mission": "Mission-09 section 22 (ESTIMATE ONLY - no execution)",
        "calibration": {
            "eng_tasks_measured": len(rates),
            "per_node_wall_s_central": round(rate_central, 3),
            "per_node_wall_s_optimistic": round(rate_opt, 3),
            "per_node_wall_s_conservative": round(rate_con, 3),
            "per_state_setup_s_central": round(setup_central, 1),
            "per_task_rates_s_per_node": {k: round(v, 3) for k, v in rates.items()},
        },
        "dev_47_cap200_estimate": {
            "n_executable_tasks": n_executable,
            "zero_node_tasks": zero,
            "optimistic": dev_optimistic,
            "central": dev_central,
            "conservative": dev_conservative,
            "evidence_growth_mib_est": dev_evidence_mib,
            "min_projected_c_free_gib": 53.0 - dev_evidence_mib / 1024,
            "resource_risk": (
                "low RAM (ENG peak WSL used 1.6 GiB; host headroom verified); "
                "wall-time bound (multi-day serial) is the main constraint; "
                "overnight execution requires checkpointing/resume."
            ),
        },
        "main_future_cap200_estimate": {
            "population_authority_unresolved": True,
            "behavioral_only": main_71,
            "behavioral_union_symbol": main_83,
        },
        "workers2_recommendation": workers2_note,
        "notes": [
            "Estimated from REAL Mission-09 ENG cap200 data (measured per-node wall, "
            "setup cost), not from node count alone (Mission-09 section 22).",
            "C4 historical runtime used only as a covariate check, not as setup time.",
            "MAIN raw candidate discovery has NOT run; MAIN estimate uses the "
            "corrected DEV nodes/file ratio over the MAIN inventory associated-file "
            "counts and must be re-derived once a frozen MAIN population decision exists.",
        ],
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT)
    print("per-node rates s:", {k: round(v, 3) for k, v in rates.items()})
    print("setup central:", setup_central)
    print("DEV-47 central:", json.dumps(dev_central, indent=1))
    print("DEV-47 optimistic:", json.dumps(dev_optimistic, indent=1))
    print("DEV-47 conservative:", json.dumps(dev_conservative, indent=1))
    print("evidence MiB:", dev_evidence_mib)
    print("MAIN 71:", json.dumps(main_71, indent=1))
    print("MAIN 83:", json.dumps(main_83, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
