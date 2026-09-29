#!/usr/bin/env python3
"""WP2 M14A Pilot-A readiness + membership (brain-authored corrected kit). ZERO model API.

Implements the FROZEN M13B atomic M14A.S0.A1 for all 26 M13B-eligible ASSAY_HOLDOUT tasks:
  "materialize parent+test patch; gold diff must PASS F2P; empty must FAIL F2P; P2P defined"
using the SAME oracle construction as the Smoke v2.2 evaluator sets:
  1. C4 under Harness V3/V3.1 (changed tests, parent+test patch vs target, x3):
     behavioral F2P = BEHAVIORAL_F2P nodes; P2P-S = P2P_ONLY nodes (3/3 pass both sides).
  2. P2P-U = frozen P2P-U V2/V3 semantics (DECISIONS 2026-09-25 "P2P-U V2 extended
     preservation design freeze"): V3 rediscovery -> outcome-blind proximity-ordered
     cap200 SELECTION -> execute those 200 on parent and target x3 -> keep STABLE_P2P.
     The V1 "execute every candidate, then cap the stable set" rule was STOPPED as
     infeasible (Q7) and replaced by V2. It is NOT used. (132,213 raw candidates for
     these 26 tasks would take ~70 h serial.)
  3. Per-task E2E check: gold non-test diff rebuilds the target tree and PASSES F2P with
     preservation PASS/UNDEFINED; the empty diff FAILS F2P with preservation PASS/UNDEFINED.
  4. ready <=> C4 DONE and F2P non-empty and gold/empty check OK and (P2P-S defined or
     P2P-U200 defined).
Task-specific, deterministic non-readiness (no behavioral F2P, gold diff not applicable,
check failed, lock-exact install blocked twice) is membership evidence. Anything else
(container/WSL/clock/timeout/parse errors) raises -> exit 33 READINESS_ENV_FAIL, writes no
record, and resumes at the same task.

All new evidence goes to research/wp2/pilot_a_v1/readiness/ (closed roots are never written).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import traceback
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
for _p in (PROJECT, PROJECT / "src", PROJECT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

ROOT = PROJECT / "research/wp2/pilot_a_v1"
READINESS = ROOT / "readiness"
DESIGN_ROOT = PROJECT / "research/wp2/pilot_v1_design"
DESIGN = DESIGN_ROOT / "pilot_design_freeze_v1.json"
SELECTION = DESIGN_ROOT / "pilot_selection.json"
POOL = DESIGN_ROOT / "pool_census.json"
M13_FREEZE = DESIGN_ROOT / "m13_freeze.json"
M13_VERIFY = DESIGN_ROOT / "m13_verify.json"
FINAL = ROOT / "pilot_final_membership.json"
EVAL_SETS = ROOT / "evaluator_only/pilot_a_evaluator_sets_v1.json"
EXPECTED = {"design": "c4c28d585bddc1d95051a73a79c13cd3dcf0cbd5c188c2e7d1b19fbc31feb205",
            "selection": "85e238af1897a309b3eaa7b80ff0b7f8d1fb0370779c309739199193473115f9",
            "verify": "2dbc28519342f5a5bfcb9be1790e503a0e21af6dd3aca268a82b1355df2d6cf0"}
N_ELIGIBLE = 26
EXIT_ENV, EXIT_POOL, EXIT_INVARIANT = 33, 31, 78
READINESS_VERSION = "pilot-a-readiness-v2-2026-09-29"


class InfraError(RuntimeError):
    """Environment failure: never membership evidence."""


# ------------------------------------------------------------------ helpers
def load(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def norm_sha(p: Path) -> str:
    d = p.read_bytes()
    if b"\x00" not in d[:8192]:
        d = d.replace(b"\r\n", b"\n")
    return hashlib.sha256(d).hexdigest()


def sha_obj(x: Any) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def self_hash(d: dict) -> dict:
    q = copy.deepcopy(d)
    q["artifact_sha256"] = ""
    d["artifact_sha256"] = sha_obj(q)
    return d


def hash_ok(d: dict) -> bool:
    q = copy.deepcopy(d)
    got = q.get("artifact_sha256", "")
    q["artifact_sha256"] = ""
    return bool(got) and sha_obj(q) == got


def write(p: Path, d: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                 encoding="utf-8", newline="\n")


def require(c: bool, m: str) -> None:
    if not c:
        raise RuntimeError(m)


# ------------------------------------------------------------------ guard
def guard() -> dict:
    for p in (DESIGN, SELECTION, POOL, M13_FREEZE, M13_VERIFY):
        require(p.exists(), f"missing M13B artifact {p.relative_to(PROJECT)}")
    require(load(DESIGN).get("artifact_sha256") == EXPECTED["design"], "design identity drift")
    require(load(SELECTION).get("artifact_sha256") == EXPECTED["selection"],
            "selection identity drift")
    v = load(M13_VERIFY)
    require(v.get("artifact_sha256") == EXPECTED["verify"] and all(v.get("checks", {}).values()),
            "M13 verification not PASS")
    for rel, h in load(M13_FREEZE).get("files", {}).items():
        p = PROJECT / rel
        require(p.exists() and norm_sha(p) == h, f"M13 freeze drift {rel}")
    split = load(PROJECT / "research/wp2/oracle_confirmation_linux_v2_2026-09-23/"
                           "dev_split_v2_2026-09-23.json")["membership"]
    sel = load(SELECTION)
    chosen = set(sel["pilot_a_tasks"]) | set(sel["pilot_b_tasks"]) | set(sel["reserve_order"])
    forb = set(split["DEV_TRAIN_ENG"]) | set(split["DEV_VALIDATION"])
    require(chosen <= set(split["DEV_TRAIN_ASSAY_HOLDOUT"]) and not chosen & forb,
            "protected split violation")
    require(sorted(chosen) == sorted(eligible()) and len(chosen) == N_ELIGIBLE,
            "eligible set != A+B+reserve")
    rec = self_hash({"artifact": "m14a_readiness_guard", "artifact_sha256": "",
                     "design_sha256": EXPECTED["design"], "selection_sha256": EXPECTED["selection"],
                     "n_eligible": N_ELIGIBLE, "readiness_version": READINESS_VERSION,
                     "dev_validation_touched": False, "main_touched": False,
                     "model_api_calls": 0})
    write(ROOT / "m14a_guard.json", rec)
    return rec


def eligible() -> list[str]:
    return [x["task_id"] for x in load(POOL)["tasks"] if x.get("eligible")]


def rec_path(tid: str) -> Path:
    return READINESS / tid / "record.json"


# ------------------------------------------------------------------ harness adapter
class Harness:
    """Thin adapter over the frozen V3/V3.1 harness; replaced by fakes in tests."""

    def __init__(self) -> None:
        import scripts.wp2_m10b_p2pu_v3_eng as pu
        import scripts.wp2_m10b_phase5_c4_v3 as c4
        from benchmark.wp2.p2p_inventory_dev_v1 import P2P_CLASS_STABLE
        self.c4, self.pu, self.STABLE = c4, pu, P2P_CLASS_STABLE

    def redirect(self, out: Path) -> None:
        # Every mutable output of the historical modules goes under the Pilot root.
        self.c4.OUT_ROOT = out
        self.c4.PER_TASK = out / "c4_per_task.jsonl"
        self.c4.PROGRESS_FILE = out / "c4_progress.json"
        self.pu.OUT_ROOT = out

    def c4_run(self, tid: str, td: Path) -> dict:
        return self.c4.run_task(tid, td)

    def p2pu_select(self, tid: str) -> tuple[dict, list[str]]:
        disc = self.pu.rediscover_v3(tid)
        disc["rediscovery_sha256"] = sha_obj(disc)
        if not disc.get("candidate_node_ids"):
            return disc, []
        sel = self.pu.derive_v3_selection(disc)
        return disc, list(sel["cap200_node_ids"])

    def p2pu_execute(self, tid: str, nodes: list[str], disc: dict) -> dict:
        return self.pu.execute_cap(tid, 200, nodes, disc)

    def gold_empty(self, tid: str, sets_path: Path) -> dict:
        from scripts.wp2_m14a_evalcore import gold_empty_canary, point_evaluator
        ev = point_evaluator(sets_path, READINESS)
        return gold_empty_canary(ev, tid, "rd")


# ------------------------------------------------------------------ one task
def classify_task(tid: str, h: Any) -> dict:
    td = READINESS / tid
    td.mkdir(parents=True, exist_ok=True)
    h.redirect(READINESS)
    c4r = h.c4_run(tid, td)
    st = c4r.get("status")
    if st == "ENV_INSTALL_BLOCKED":          # lock-exact install: retry once before accepting
        c4r = h.c4_run(tid, td)
        st = c4r.get("status")
    if st not in ("DONE", "ENV_INSTALL_BLOCKED"):
        raise InfraError(f"C4 status {st} for {tid}")
    recs = c4r.get("node_records", [])
    f2p = sorted(r["node_id"] for r in recs if r.get("v3_class") == "BEHAVIORAL_F2P")
    p2ps = sorted(r["node_id"] for r in recs if r.get("v3_class") == "P2P_ONLY"
                  and all(o == "passed" for o in r.get("target_outcomes", []))
                  and all(o == "passed" for o in r.get("parent_outcomes", [])))
    reasons: list[str] = []
    detail: dict[str, Any] = {"c4_status": st, "c4_evidence_sha256": c4r.get("evidence_sha256")}
    stable: list[str] = []
    selected: list[str] = []
    p2pu_status = "NOT_RUN"
    canary: dict[str, Any] = {}
    if st != "DONE":
        reasons.append("C4_" + str(st))
    elif not f2p:
        reasons.append("NO_BEHAVIORAL_F2P")
    else:
        disc, selected = h.p2pu_select(tid)
        detail["p2pu_rediscovery"] = {k: disc.get(k) for k in (
            "collect_rc", "n_associated_files", "n_collect_files", "rediscovery_sha256",
            "install_mode", "wall_s")}
        detail["p2pu_n_candidates"] = len(disc.get("candidate_node_ids", []))
        if selected:
            res = h.p2pu_execute(tid, selected, disc)
            p2pu_status = res.get("status")
            if p2pu_status != "DONE":
                raise InfraError(f"P2P-U cap200 status {p2pu_status} for {tid}")
            classes = res.get("node_classes", {})
            stable = [n for n in selected if classes.get(n) == h.STABLE]
            detail["p2pu_class_counts"] = res.get("class_counts")
            detail["p2pu_evidence_sha256"] = res.get("evidence_sha256")
        else:
            p2pu_status = "UNDEFINED_NO_CANDIDATES"
        if not p2ps and not stable:
            reasons.append("P2P_UNDEFINED")
        else:
            entry = task_sets_entry(c4r, f2p, p2ps, stable)
            sp = td / "provisional_sets.json"
            from scripts.wp2_m14a_evalcore import sets_artifact
            write(sp, sets_artifact({tid: entry}, READINESS_VERSION + "-provisional"))
            canary = h.gold_empty(tid, sp)
            if not canary.get("ok"):
                reasons.append("GOLD_EMPTY_CHECK_FAILED" if canary.get("gold_applies", True)
                               else "GOLD_DIFF_NOT_APPLICABLE")
    detail.update({"p2pu_status": p2pu_status, "p2pu_selected_cap200": selected,
                   "gold_empty_check": canary})
    write(td / "detail.json", detail)
    rec = self_hash({
        "artifact": "pilot_a_readiness_task", "artifact_sha256": "",
        "readiness_version": READINESS_VERSION, "task_id": tid, "ready": not reasons,
        "reasons": reasons, "era_key": c4r.get("era_key"), "c4_status": st,
        "behavioral_f2p_node_ids": f2p, "p2p_s_node_ids": p2ps,
        "p2p_u_cap200_stable_ids": stable, "p2p_s_defined": bool(p2ps),
        "p2p_u_cap200_defined": bool(stable), "n_p2pu_selected_cap200": len(selected),
        "p2pu_status": p2pu_status, "gold_empty_ok": bool(canary.get("ok")),
        "detail_sha256": norm_sha(td / "detail.json"), "model_api_calls": 0})
    write(rec_path(tid), rec)
    return rec


def task_sets_entry(c4r: dict, f2p: list[str], p2ps: list[str], stable: list[str]) -> dict:
    return {"era_key": c4r.get("era_key"), "target_commit": c4r.get("target_commit"),
            "behavioral_f2p_node_ids": f2p,
            "symbol_f2p_node_ids": sorted(r["node_id"] for r in c4r.get("node_records", [])
                                          if r.get("v3_class") == "SYMBOL_ABSENCE_F2P"),
            "p2p_s_node_ids": p2ps, "p2p_u_cap200_stable_ids": stable,
            "p2p_s_defined": bool(p2ps), "p2p_u_cap200_defined": bool(stable)}


# ------------------------------------------------------------------ commands
def readiness(max_new: int, h: Any = None) -> int:
    guard()
    made = 0
    for tid in eligible():
        p = rec_path(tid)
        if p.exists():
            require(hash_ok(load(p)), f"readiness record corrupt: {tid}")
            continue
        if made >= max_new:
            break
        try:
            h = h or Harness()
            r = classify_task(tid, h)
        except Exception as exc:  # infrastructure or instrument error: STOP, write no record
            err = {"task_id": tid, "error": f"{type(exc).__name__}: {exc}",
                   "traceback": traceback.format_exc()[-8000:]}
            write(READINESS / "unexpected_error.json", err)
            print("READINESS_ENV_FAIL " + json.dumps({k: err[k] for k in ("task_id", "error")}))
            return EXIT_ENV
        print(f"READINESS_TASK {tid} ready={r['ready']} reasons={r['reasons']}", flush=True)
        made += 1
    done = sum(rec_path(t).exists() for t in eligible())
    print(f"READINESS_PROGRESS {done}/{N_ELIGIBLE}")
    return 0


def readiness_check() -> int:
    miss = [t for t in eligible() if not rec_path(t).exists()]
    if miss:
        print("READINESS_INCOMPLETE " + json.dumps(miss[:30]))
        return 1
    bad = [t for t in eligible() if not hash_ok(load(rec_path(t)))
           or norm_sha(READINESS / t / "detail.json") != load(rec_path(t))["detail_sha256"]]
    if bad:
        print("READINESS_CORRUPT " + json.dumps(bad))
        return 1
    print(f"READINESS_COMPLETE n={N_ELIGIBLE}")
    return 0


def build_sets(ids: list[str]) -> dict:
    from scripts.wp2_m14a_evalcore import sets_artifact
    tasks = {}
    for t in ids:
        r = load(rec_path(t))
        tasks[t] = {"era_key": r["era_key"],
                    "behavioral_f2p_node_ids": r["behavioral_f2p_node_ids"],
                    "p2p_s_node_ids": r["p2p_s_node_ids"],
                    "p2p_u_cap200_stable_ids": r["p2p_u_cap200_stable_ids"],
                    "p2p_s_defined": r["p2p_s_defined"],
                    "p2p_u_cap200_defined": r["p2p_u_cap200_defined"]}
    return sets_artifact(tasks, READINESS_VERSION)


def membership() -> int:
    require(readiness_check() == 0, "readiness incomplete or corrupt")
    from scripts.wp2_m13 import finalize_after_readiness  # FROZEN M13B rule, unchanged
    s = load(SELECTION)
    rr = {t: load(rec_path(t)) for t in eligible()}
    ready = {t for t, r in rr.items() if r["ready"]}
    f = finalize_after_readiness(s["pilot_a_tasks"], s["pilot_b_tasks"], s["reserve_order"], ready)
    require(not set(f["A"]) & set(f["B"]) and len(f["A"]) == len(f["B"]), "A/B invariant")
    out = self_hash({"artifact": "pilot_final_membership", "artifact_sha256": "", **f,
                     "n_ready": len(ready), "ready_tasks": sorted(ready),
                     "not_ready": {t: rr[t]["reasons"] for t in sorted(rr) if not rr[t]["ready"]},
                     "readiness_record_sha256": {t: rr[t]["artifact_sha256"] for t in sorted(rr)},
                     "selection_artifact_sha256": s["artifact_sha256"],
                     "rule": "scripts/wp2_m13.py::finalize_after_readiness (M13B frozen)"})
    write(FINAL, out)
    if f["verdict"] == "POOL_INSUFFICIENT":
        print("POOL_INSUFFICIENT " + json.dumps({"A": len(f["A"]), "B": len(f["B"])}))
        return EXIT_POOL
    write(EVAL_SETS, build_sets(sorted(set(f["A"]) | set(f["B"]))))
    print("FINAL_MEMBERSHIP " + json.dumps({"verdict": f["verdict"], "n": len(f["A"]),
                                            "reserve_used": f["reserve_used"]}, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("guard")
    q = sp.add_parser("readiness")
    q.add_argument("--max-new", type=int, default=1)
    sp.add_parser("readiness-check")
    sp.add_parser("membership")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "guard":
            print("M14A_STEP_PASS guard " + guard()["artifact_sha256"][:16])
            return 0
        if a.cmd == "readiness":
            return readiness(a.max_new)
        if a.cmd == "readiness-check":
            return readiness_check()
        return membership()
    except Exception as exc:
        print(f"M14A_READINESS_ERROR {a.cmd} {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return EXIT_INVARIANT


if __name__ == "__main__":
    raise SystemExit(main())
