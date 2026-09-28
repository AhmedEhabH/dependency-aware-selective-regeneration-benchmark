#!/usr/bin/env python3
"""Mission-12B v2.1 - Q mechanical summarizer/gates (T6).

Inputs ONLY: frozen generation/evaluation evidence under the v21 root.
No model/API. No outcome repair.

Primary table per arm (x/14): first-call valid, post-repair valid, APPLIED,
RESOLVED, F2P, P2P-S, P2P-U200, architecture/scope violations, logical tokens,
billed tokens, USD, wall time.

Primary gate (frozen):
- instrument invalid -> NEXT=INSTRUMENT_FIX
- GOLD APPLIED < 7/14   -> NEXT=INTERFACE_V3_PROBE
- GOLD APPLIED >= 7 and GOLD RESOLVED <= 2 -> NEXT=GENERATOR_COMPETENCE_OR_SPEC_REVIEW
- GOLD APPLIED >= 7 and GOLD RESOLVED >= 3 -> NEXT=PILOT_DESIGN

Secondary: same descriptive table excluding d220. NEVER changes the primary
token or NEXT.

Usage:
  python scripts/wp2_e2e_smoke_v21_summary.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

V21_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v21"
ARMS = ("GOLD_HARD", "RMCSS_HARD", "AGENT_HARD", "PLACEBO_HARD")
D220 = "saleor-rc-d220843b5418"


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _episodes() -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    for sub in ("episodes", "variance"):
        d = V21_ROOT / sub
        if not d.exists():
            continue
        for ep in d.rglob("episode.json"):
            rec = _load(ep)
            if not rec:
                continue
            key = (rec["task_id"], ep.parent.name)
            rec["_subdir"] = sub
            out[key] = rec
    return out


def _evals_by_diff() -> dict[str, dict]:
    out = {}
    d = V21_ROOT / "evaluations" / "unique"
    if not d.exists():
        return out
    for ep in d.rglob("evaluation.json"):
        rec = _load(ep)
        if rec and rec.get("diff_sha256"):
            out[rec["diff_sha256"]] = rec
    return out


def _by_construction() -> dict[tuple[str, str], dict]:
    out = {}
    for sub in ("episodes", "variance"):
        d = V21_ROOT / "evaluations" / sub
        if not d.exists():
            continue
        for ep in d.rglob("evaluation.json"):
            rec = _load(ep)
            if rec and rec.get("status") == "BY_CONSTRUCTION":
                out[(rec["task_id"], rec["label"])] = rec
    return out


def _wall_span(times: list[str]) -> float:
    parsed = []
    for t in times:
        try:
            parsed.append(datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").timestamp())
        except (ValueError, TypeError):
            continue
    if len(parsed) < 2:
        return 0.0
    return max(parsed) - min(parsed)


def summarize(tasks: list[str]) -> dict:
    eps = _episodes()
    evals = _evals_by_diff()
    by_cons = _by_construction()
    per_arm: dict[str, dict] = {}
    for arm in ARMS:
        first_valid = post_repair = applied = resolved = f2p = p2ps = p2pu = 0
        arch_viol = 0
        tokens = usd = 0.0
        wall_times: list[str] = []
        for tid in tasks:
            ep = eps.get((tid, arm))
            if not ep:
                continue
            if ep.get("created_utc"):
                wall_times.append(ep["created_utc"])
            for c in ep.get("calls", []):
                tokens += c.get("prompt_tokens", 0) + c.get("completion_tokens", 0)
                usd += c.get("cost_usd_actual", 0.0)
            for err in ep.get("validation", {}).get("initial", []):
                if err.startswith(("OUT_OF_SCOPE_FILE", "TEST_PATH")):
                    arch_viol += 1
            for err in ep.get("validation", {}).get("repair", []):
                if err.startswith(("OUT_OF_SCOPE_FILE", "TEST_PATH")):
                    arch_viol += 1
            status = ep.get("status")
            if status == "APPLIED":
                applied += 1
                if ep.get("repair_used"):
                    post_repair += 1
                else:
                    first_valid += 1
                eval_rec = evals.get(ep.get("diff_sha256", ""), {})
            else:
                eval_rec = by_cons.get((tid, arm), {})
            if eval_rec:
                if eval_rec.get("f2p_task") == "PASS":
                    f2p += 1
                if eval_rec.get("p2p_s_task") in ("PASS", "PASS_BY_CONSTRUCTION"):
                    p2ps += 1
                if eval_rec.get("p2p_u200_task") in ("PASS", "PASS_BY_CONSTRUCTION"):
                    p2pu += 1
                if eval_rec.get("resolved"):
                    resolved += 1
        per_arm[arm] = {
            "first_call_valid": first_valid,
            "post_repair_valid": post_repair,
            "applied": applied,
            "resolved": resolved,
            "f2p": f2p,
            "p2p_s": p2ps,
            "p2p_u200": p2pu,
            "architecture_scope_violations": arch_viol,
            "logical_tokens": int(tokens),
            "billed_tokens": int(tokens),
            "usd": round(usd, 6),
            "wall_time_s": round(_wall_span(wall_times), 1),
        }
    return per_arm


def _primary_gate(per_arm: dict) -> tuple[str, str]:
    gold = per_arm["GOLD_HARD"]
    applied = gold["applied"]
    resolved = gold["resolved"]
    if applied < 7:
        return "INTERFACE_V3_PROBE", f"GOLD APPLIED {applied}/14 < 7/14"
    if resolved <= 2:
        reason = (f"GOLD APPLIED {applied}/14 >= 7/14 and "
                  f"RESOLVED {resolved}/14 <= 2/14")
        return "GENERATOR_COMPETENCE_OR_SPEC_REVIEW", reason
    reason = (f"GOLD APPLIED {applied}/14 >= 7/14 and "
              f"RESOLVED {resolved}/14 >= 3/14")
    return "PILOT_DESIGN", reason


def main() -> int:
    all_tasks = _load(V21_ROOT / "smoke_v21_freeze.json").get("population", []) if _load(
        V21_ROOT / "smoke_v21_freeze.json") else []
    if not all_tasks:
        raise RuntimeError("smoke_v21_freeze.json missing or empty population")

    primary = summarize(all_tasks)
    secondary_tasks = [t for t in all_tasks if t != D220]
    secondary = summarize(secondary_tasks)

    next_token, gate_reason = _primary_gate(primary)
    out = {
        "artifact": "smoke_v21_summary",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "primary": {"n_tasks": len(all_tasks), "per_arm": primary,
                    "token": "PIPELINE_DESCRIPTIVE"},
        "secondary_d220_omitted": {"n_tasks": len(secondary_tasks),
                                   "per_arm": secondary,
                                   "note": "descriptive sensitivity only; never changes primary token/NEXT"},
        "gate": {"next": next_token, "reason": gate_reason},
        "mandatory_wording": "Smoke v2.1 is engineering-split pipeline validation only. "
                             "n = 14. No comparative claim between RM-CSS and Agent is made or supported.",
    }
    (V21_ROOT / "smoke_v21_summary.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"next": next_token, "reason": gate_reason}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
