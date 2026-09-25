"""Consolidate P2P-U V2 ENG evidence (Mission-09) - ZERO API.

Verifies evidence integrity across all executed task/cap runs, aggregates the
class distributions, computes the 200-vs-400 sensitivity / repeatability
report, and freezes a consolidated results artifact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

EVIDENCE_ROOT = PROJECT / "research" / "wp2" / "p2p_u_v2_eng_2026-09-25"
OUT = EVIDENCE_ROOT / "consolidated_results_2026-09-25.json"

ENG_TASKS = [
    "saleor-rc-2d45b76a52f2",
    "saleor-rc-39b4138e8550",
    "saleor-rc-74538ea00ce9",
    "saleor-rc-82c56bde0e34",
    "saleor-rc-8f76ddc6267f",
    "saleor-rc-9258154b8a0b",  # UNDEFINED
    "saleor-rc-d220843b5418",
    "saleor-rc-dfe77ac1c5dc",
    "saleor-rc-e03ee76d2b89",
]

CLASSES = ("STABLE_P2P", "TARGET_BROKEN", "PARENT_BROKEN", "BOTH_FAIL", "FLAKY", "COLLECTION_ERROR")


def load_manifest(task_id: str, cap: int) -> dict | None:
    mf = EVIDENCE_ROOT / task_id / f"cap{cap}" / "A" / "manifest.json"
    if not mf.exists():
        return None
    return json.loads(mf.read_text(encoding="utf-8"))


def load_outcomes(task_id: str, cap: int) -> dict:
    p = EVIDENCE_ROOT / task_id / f"cap{cap}" / "A" / "node_outcomes.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    per_task: dict = {}
    integrity_failures: list[str] = []
    for tid in ENG_TASKS:
        entry: dict = {"task_id": tid, "undefined": False}
        for cap in (200, 400):
            if tid == "saleor-rc-9258154b8a0b":
                entry["cap200"] = {"undefined": True, "reason": "zero unchanged candidate nodes"}
                entry["cap400"] = {"undefined": True, "reason": "zero unchanged candidate nodes"}
                entry["undefined"] = True
                continue
            m = load_manifest(tid, cap)
            if m is None:
                integrity_failures.append(f"{tid} cap{cap}: NO MANIFEST")
                entry[f"cap{cap}"] = {"error": "NO_MANIFEST"}
                continue
            e = m.get("evidence_integrity", {})
            if not e.get("ok"):
                integrity_failures.append(f"{tid} cap{cap}: integrity={e}")
            entry[f"cap{cap}"] = {
                "n_selected": m["n_selected_nodes"],
                "n_chunks": m["n_chunks"],
                "n_pytest_invocations": m["n_pytest_invocations"],
                "class_counts": m["class_counts"],
                "n_stable": m["n_stable_p2p"],
                "stable_rate": m["stable_over_selected"],
                "preservation_set_sha256": m["preservation_set_sha256"],
                "n_preservation_files": m["n_preservation_files"],
                "composition": m["composition"],
                "integrity": e,
                "measurements": {
                    "total_wall_s": m["measurements"]["total_wall_s"],
                    "setup_s": m["measurements"]["setup_s"],
                    "target_wall_s": m["measurements"]["target_wall_s"],
                    "parent_wall_s": m["measurements"]["parent_wall_s"],
                    "target_per_rep_s": m["measurements"]["target_per_rep_s"],
                    "parent_per_rep_s": m["measurements"]["parent_per_rep_s"],
                    "n_resource_samples": m["measurements"].get("n_resource_samples"),
                },
            }
        per_task[tid] = entry

    # Aggregate class distribution + overlap repeatability over first-200 nodes.
    overlap: dict = {}
    for tid in ENG_TASKS:
        if tid == "saleor-rc-9258154b8a0b":
            continue
        m200 = load_manifest(tid, 200)
        m400 = load_manifest(tid, 400)
        o200 = load_outcomes(tid, 200)
        o400 = load_outcomes(tid, 400)
        if m200 is None or m400 is None:
            continue
        # The overlapping identities are the cap200 selected node set.
        ids200 = list(o200.keys())
        agreement = 0
        stable_agree = 0
        changed = []
        confusion: dict[str, dict[str, int]] = {}
        for nid in ids200:
            c200 = o200[nid]["class"]
            c400 = o400.get(nid, {}).get("class", "MISSING_IN_400")
            confusion.setdefault(c200, {})
            confusion[c200][c400] = confusion[c200].get(c400, 0) + 1
            if c200 == c400:
                agreement += 1
            else:
                changed.append(nid)
            s200 = c200 == "STABLE_P2P"
            s400 = c400 == "STABLE_P2P"
            if s200 == s400:
                stable_agree += 1
        n = len(ids200)
        stable_200 = {nid for nid, rec in o200.items() if rec["class"] == "STABLE_P2P"}
        stable_400 = {nid for nid, rec in o400.items() if nid in set(ids200) and rec["class"] == "STABLE_P2P"}
        inter = len(stable_200 & stable_400)
        union = len(stable_200 | stable_400)
        jaccard = inter / union if union else 1.0
        overlap[tid] = {
            "n_overlap_identities": n,
            "class_agreement_rate": round(agreement / n, 4) if n else 1.0,
            "stable_agreement_rate": round(stable_agree / n, 4) if n else 1.0,
            "n_class_changed": len(changed),
            "confusion": confusion,
            "jaccard_stable_p2p": round(jaccard, 4),
            "stable_set_size_200": len(stable_200),
            "stable_set_size_400_overlap": len(stable_400),
        }

    # Aggregate stable rates.
    agg_rates = {"cap200": {}, "cap400": {}}
    for cap in (200, 400):
        rates = [per_task[t]["cap" + str(cap)]["stable_rate"] for t in ENG_TASKS
                 if t != "saleor-rc-9258154b8a0b" and "stable_rate" in per_task[t]["cap" + str(cap)]]
        agg_rates["cap" + str(cap)] = {
            "n_tasks": len(rates),
            "min": round(min(rates), 4),
            "max": round(max(rates), 4),
            "avg": round(sum(rates) / len(rates), 4) if rates else None,
            "median": round(sorted(rates)[len(rates) // 2], 4) if rates else None,
        }

    total_wall = {200: 0.0, 400: 0.0}
    total_selected = {200: 0, 400: 0}
    total_stable = {200: 0, 400: 0}
    for tid in ENG_TASKS:
        if tid == "saleor-rc-9258154b8a0b":
            continue
        for cap in (200, 400):
            m = per_task[tid]["cap" + str(cap)]
            total_wall[cap] += m["measurements"]["total_wall_s"]
            total_selected[cap] += m["n_selected"]
            total_stable[cap] += m["n_stable"]

    payload = {
        "artifact": "wp2_p2p_u_v2_eng_consolidated",
        "date": "2026-09-25",
        "mission": "Mission-09 sections 13/21",
        "executed_tasks": [t for t in ENG_TASKS if t != "saleor-rc-9258154b8a0b"],
        "undefined_tasks": ["saleor-rc-9258154b8a0b"],
        "per_task": per_task,
        "overlap_repeatability_first200": overlap,
        "aggregate_stable_rates": agg_rates,
        "aggregate_totals": {
            "cap200": {
                "n_tasks": len([t for t in ENG_TASKS if t != "saleor-rc-9258154b8a0b"]),
                "n_selected": total_selected[200],
                "n_stable": total_stable[200],
                "total_wall_s": round(total_wall[200], 1),
                "stable_rate_overall": round(total_stable[200] / total_selected[200], 4),
            },
            "cap400": {
                "n_tasks": len([t for t in ENG_TASKS if t != "saleor-rc-9258154b8a0b"]),
                "n_selected": total_selected[400],
                "n_stable": total_stable[400],
                "total_wall_s": round(total_wall[400], 1),
                "stable_rate_overall": round(total_stable[400] / total_selected[400], 4),
            },
            "runtime_multiplier_400_over_200": round(total_wall[400] / total_wall[200], 2) if total_wall[200] else None,
        },
        "integrity": {
            "all_ok": len(integrity_failures) == 0,
            "failures": integrity_failures,
            "n_executed_task_caps": sum(
                1 for t in ENG_TASKS if t != "saleor-rc-9258154b8a0b"
                for cap in (200, 400) if load_manifest(t, cap) is not None
            ),
        },
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT)
    print("integrity failures:", integrity_failures)
    print("aggregate totals:", json.dumps(payload["aggregate_totals"], indent=1))
    print("overlap repeatability:", json.dumps(
        {k: {kk: vv for kk, vv in v.items() if kk != "confusion"} for k, v in overlap.items()},
        indent=1))
    return 0 if not integrity_failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
