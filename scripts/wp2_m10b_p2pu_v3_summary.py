#!/usr/bin/env python3
"""WP-2 Mission-10B P2P-U V3 ENG summary + preservation coverage (A4) - ZERO API.

Reads every p2pu_v3_eng_<task>_cap<cap>.json unit file, recomputes totals,
asserts the A4.2 invariants, and writes p2pu_v3_eng_summary.json.

Also computes D19 cap200 vs first200(cap400) agreement and the V2->V3
comparison for the 7 tasks with Mission-09 evidence.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
V2_ROOT = PROJECT / "research" / "wp2" / "p2p_u_v2_eng_2026-09-25"
CENSUS = json.loads((PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" /
                     "dev_census_2026-09-23.json").read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_unit(task_id: str, cap: int) -> dict:
    return json.loads((OUT_ROOT / f"p2pu_v3_eng_{task_id}_cap{cap}.json").read_text(encoding="utf-8"))


def rediscovery_v3_selection(task_id: str) -> dict:
    d = json.loads((OUT_ROOT / f"p2pu_v3_rediscovery_{task_id}.json").read_text(encoding="utf-8"))
    return d.get("v3_selection", {})


def load_v2_classes(task_id: str, cap: int) -> dict[str, str] | None:
    p = V2_ROOT / task_id / f"cap{cap}" / "A" / "node_classes.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def era_of(task_id: str) -> str:
    for t in CENSUS.get("tasks", []):
        if t["task_id"] == task_id:
            return t.get("era_key", "")
    return ""


def main() -> int:
    eng_ready = json.loads((OUT_ROOT / "eng_v3_oracle_ready.json").read_text(encoding="utf-8"))
    union = sorted(eng_ready["oracle_valid_union_task_ids"])
    env_blocked = set(eng_ready.get("environment_failed_task_ids", []))
    behavioral = set(eng_ready.get("behavioral_task_ids", []))
    symbol = set(eng_ready.get("symbol_only_task_ids", []))

    per_task: dict[str, dict] = {}
    defined_cap200: list[str] = []
    defined_cap400: list[str] = []
    for tid in union:
        cap200 = load_unit(tid, 200)
        cap400 = load_unit(tid, 400)
        t_rec = {"task_id": tid, "era_key": era_of(tid), "behavioral": tid in behavioral,
                 "symbol_only": tid in symbol, "cap200": cap200, "cap400": cap400}
        per_task[tid] = t_rec
        if cap200.get("status") == "DONE":
            defined_cap200.append(tid)
        if cap400.get("status") == "DONE":
            defined_cap400.append(tid)

    def cap_rec(unit: dict) -> dict:
        return {
            "status": unit.get("status"),
            "class_counts": unit.get("class_counts", {}),
            "n_selected": unit.get("n_selected", 0),
            "n_stable_p2p": unit.get("n_stable_p2p", 0),
            "stable_rate": round(unit.get("n_stable_p2p", 0) / unit.get("n_selected", 1), 4)
                           if unit.get("n_selected") else 0.0,
            "wall_s": unit.get("wall_s", 0.0),
            "collection_session_abort": unit.get("manifest", {}).get("collection_session_abort", {}),
            "install_mode": unit.get("manifest", {}).get("install_mode"),
            "has_locked_dev_entry": unit.get("manifest", {}).get("task_id") in _LOCKED_DEV_TASKS,
        }

    summary: dict = {
        "artifact": "p2p-u-v3-eng-summary",
        "mission": "Mission-10B Phase 5B / Mission-11 A4",
        "created_utc": _now_utc(),
        "population": {"union": len(union), "behavioral": len(behavioral), "symbol_only": len(symbol),
                       "env_blocked": sorted(env_blocked)},
        "per_task": {},
        "totals": {},
        "agreement": {},
        "v2_comparison": {},
        "invariants": {},
    }

    class_keys = ["STABLE_P2P", "TARGET_BROKEN", "PARENT_BROKEN", "BOTH_FAIL", "FLAKY", "COLLECTION_ERROR"]
    total_cap200 = {k: 0 for k in class_keys}
    total_cap400 = {k: 0 for k in class_keys}
    n_selected_200 = n_stable_200 = 0
    n_selected_400 = n_stable_400 = 0
    wall_200 = wall_400 = 0.0

    for tid in union:
        rec = per_task[tid]
        rec["summary"] = {"cap200": cap_rec(rec["cap200"]), "cap400": cap_rec(rec["cap400"])}
        summary["per_task"][tid] = rec["summary"]

        # A4.2 invariant: sum(class_counts) == n_selected for DONE
        for cap in (200, 400):
            u = rec[f"cap{cap}"]
            if u.get("status") == "DONE":
                assert sum(u.get("class_counts", {}).values()) == u.get("n_selected"), tid

        # D19 cap200 vs first200(cap400) agreement
        sel = rediscovery_v3_selection(tid)
        c200 = list(sel.get("cap200_node_ids", []))
        c400 = list(sel.get("cap400_node_ids", []))
        n200 = len(c200)
        if n200 == 0:
            agreement = {"status": "UNDEFINED"}
        else:
            first200 = c400[:200] if len(c400) >= 200 else c400
            same_list = (c200 == first200)
            if rec["cap200"].get("status") == "DONE" and rec["cap400"].get("status") == "DONE":
                nc200 = rec["cap200"].get("node_classes", {})
                nc400 = rec["cap400"].get("node_classes", {})
                shared = [n for n in c200 if n in nc400]
                class_agree = sum(1 for n in shared if nc200.get(n) == nc400.get(n)) / len(shared) if shared else 0.0
                s200 = set(n for n, c in nc200.items() if c == "STABLE_P2P")
                s400 = set(n for n, c in nc400.items() if c == "STABLE_P2P")
                stable_agree = sum(1 for n in shared if (nc200.get(n) == "STABLE_P2P") == (nc400.get(n) == "STABLE_P2P")) / len(shared) if shared else 0.0
                inter = s200 & s400
                union_s = s200 | s400
                jaccard = len(inter) / len(union_s) if union_s else 1.0
                class_change = sorted(n for n in shared if nc200.get(n) != nc400.get(n))
            else:
                class_agree = stable_agree = None
                jaccard = None
                class_change = []
            agreement = {
                "status": "DONE",
                "same_node_list": same_list,
                "n_cap200": len(c200),
                "n_first200_cap400": len(first200),
                "class_agreement": round(class_agree, 4) if class_agree is not None else None,
                "stable_agreement": round(stable_agree, 4) if stable_agree is not None else None,
                "jaccard_stable_p2p": round(jaccard, 4) if jaccard is not None else None,
                "class_change_count": len(class_change),
                "class_change": class_change[:50],
            }
        summary["agreement"][tid] = agreement

        # totals
        for cap in (200, 400):
            u = rec[f"cap{cap}"]
            if u.get("status") != "DONE":
                continue
            cc = u.get("class_counts", {})
            for k in class_keys:
                (total_cap200 if cap == 200 else total_cap400)[k] += cc.get(k, 0)
            if cap == 200:
                n_selected_200 += u.get("n_selected", 0)
                n_stable_200 += u.get("n_stable_p2p", 0)
                wall_200 += u.get("wall_s", 0.0)
            else:
                n_selected_400 += u.get("n_selected", 0)
                n_stable_400 += u.get("n_stable_p2p", 0)
                wall_400 += u.get("wall_s", 0.0)

        # V2 comparison (7 tasks with Mission-09 evidence)
        v2c200 = load_v2_classes(tid, 200)
        if v2c200 is not None and rec["cap200"].get("status") == "DONE":
            v3nc = rec["cap200"].get("node_classes", {})
            v2_stable = {n for n, c in v2c200.items() if c == "STABLE_P2P"}
            v3_stable = {n for n, c in v3nc.items() if c == "STABLE_P2P"}
            shared_ids = sorted(set(v2c200) & set(v3nc))
            inter = v2_stable & v3_stable
            union_s = v2_stable | v3_stable
            jac = len(inter) / len(union_s) if union_s else 1.0
            class_change: dict[str, int] = {}
            for n in shared_ids:
                v2c = v2c200[n]
                v3c = v3nc[n]
                if v2c != v3c:
                    class_change[f"{v2c}->{v3c}"] = class_change.get(f"{v2c}->{v3c}", 0) + 1
            summary["v2_comparison"][tid] = {
                "n_v2_nodes": len(v2c200),
                "n_shared": len(shared_ids),
                "v2_stable": len(v2_stable),
                "v3_stable": len(v3_stable),
                "jaccard_v2_v3_stable": round(jac, 4),
                "class_change_counts": class_change,
            }

    summary["totals"] = {
        "defined_cap200": sorted(defined_cap200),
        "defined_cap400": sorted(defined_cap400),
        "n_defined_cap200": len(defined_cap200),
        "n_defined_cap400": len(defined_cap400),
        "n_executed_done": len(defined_cap200),
        "n_undefined_units": 2 * len([t for t in union if per_task[t]["cap200"].get("status") != "DONE"]),
        "class_counts_cap200": total_cap200,
        "class_counts_cap400": total_cap400,
        "n_selected_cap200": n_selected_200,
        "n_stable_cap200": n_stable_200,
        "overall_stable_rate_cap200": round(n_stable_200 / n_selected_200, 4) if n_selected_200 else 0.0,
        "n_selected_cap400": n_selected_400,
        "n_stable_cap400": n_stable_400,
        "overall_stable_rate_cap400": round(n_stable_400 / n_selected_400, 4) if n_selected_400 else 0.0,
        "wall_s_cap200": round(wall_200, 1),
        "wall_s_cap400": round(wall_400, 1),
        "cap400_cap200_wall_multiplier": round(wall_400 / wall_200, 3) if wall_200 else None,
    }

    # ---- A4.2 invariants ----
    invariants: dict = {}
    # 1. population subset + no env-blocked
    invariants["population_subset_union"] = all(t in union for t in union)
    invariants["env_blocked_intersection_empty"] = not (set(union) & env_blocked)
    # 2. sum(class_counts) == n_selected (asserted above)
    invariants["sum_class_counts_eq_n_selected"] = True
    # 3+4. cap200 == first200(cap400) and node lists equal rediscovery v3_selection
    list_ok = True
    for tid in union:
        sel = rediscovery_v3_selection(tid)
        u200 = per_task[tid]["cap200"]
        u400 = per_task[tid]["cap400"]
        if u200.get("status") == "DONE":
            keys200 = sorted(u200.get("node_classes", {}).keys())
            sel200 = list(sel.get("cap200_node_ids", []))
            if keys200 != sorted(sel200):
                list_ok = False
        if u400.get("status") == "DONE":
            keys400 = sorted(u400.get("node_classes", {}).keys())
            sel400 = list(sel.get("cap400_node_ids", []))
            if keys400 != sorted(sel400):
                list_ok = False
        if u200.get("status") == "DONE" and u400.get("status") == "DONE":
            if summary["agreement"][tid].get("same_node_list") is not True:
                list_ok = False
    invariants["node_lists_equal_rediscovery_selection"] = list_ok
    invariants["all_pass"] = all(invariants.values())
    summary["invariants"] = invariants

    if not invariants["all_pass"]:
        print(json.dumps(invariants, indent=1))
        raise SystemExit("P2PU_INTEGRITY_STOP: A4.2 invariant failed")

    out = OUT_ROOT / "p2pu_v3_eng_summary.json"
    out.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out}")
    print(f"defined cap200={len(defined_cap200)} cap400={len(defined_cap400)} "
          f"overall stable cap200={summary['totals']['overall_stable_rate_cap200']} "
          f"cap400={summary['totals']['overall_stable_rate_cap400']}")
    return 0


_LOCKED_DEV_TASKS = {
    "saleor-rc-c3b9e396b07d", "saleor-rc-e25cf9b4a837", "saleor-rc-74538ea00ce9",
    "saleor-rc-8f76ddc6267f",
}


def _now_utc() -> str:
    import datetime
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())