#!/usr/bin/env python3
"""WP-2 E2E Smoke v2.2 mechanical summary + gates (brain-authored kit v2.2.1; hash-verified).

Reuses the frozen v2.1 per-arm counting rules and NEXT rule (pointed at the v2.2 root).
Amendment v2.2.1: APPLIED episodes are joined to their evaluation by
(task_id, full diff_sha256). The v2.1 summarizer joined by diff_sha256 alone, which lets
one task borrow another task's score whenever the diffs are identical (e.g. no-op diffs).
It adds the mechanical Smoke gates:

SG1 instrument: generation freeze present AND every planned evaluation record present.
SG2 completion: 56/56 main + 6/6 variance terminal (checked by the generation freeze).
SG3 spend: ledger total <= $2.00.
SG4 floor: GOLD_HARD RESOLVED >= 1/14.
Token: E2E_SMOKE_V22_PIPELINE_VALID | E2E_SMOKE_V22_FLOOR_EFFECT | E2E_SMOKE_V22_INSTRUMENT_INVALID
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.e2e_v22.common import (  # noqa: E402
    SCIENTIFIC_CEILING_USD,
    V22_ROOT,
    VARIANCE_ARM,
    episode_path,
    planned_variance,
)


def load_v21_summary() -> ModuleType:
    path = PROJECT / "scripts" / "wp2_e2e_smoke_v21_summary.py"
    spec = importlib.util.spec_from_file_location("wp2_e2e_smoke_v21_summary_for_v22", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.V21_ROOT = V22_ROOT
    return mod


def _load(p: Path) -> dict[str, Any] | None:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def variance_table() -> list[dict[str, Any]]:
    rows = []
    for task_id, _arm, label in planned_variance():
        main = _load(episode_path(V22_ROOT, "episodes", task_id, VARIANCE_ARM)) or {}
        rep = _load(episode_path(V22_ROOT, "variance", task_id, label)) or {}
        rows.append({"task_id": task_id, "replicate": label,
                     "main_status": main.get("status"), "rep_status": rep.get("status"),
                     "same_status": main.get("status") == rep.get("status"),
                     "same_diff": bool(main.get("diff_sha256"))
                     and main.get("diff_sha256") == rep.get("diff_sha256")})
    return rows


def evals_by_identity(root: Path | None = None) -> dict[tuple[str, str], dict[str, Any]]:
    root = root or V22_ROOT
    out: dict[tuple[str, str], dict[str, Any]] = {}
    d = root / "evaluations" / "unique"
    if not d.exists():
        return out
    for p in d.glob("*/*/evaluation.json"):
        rec = _load(p)
        if not rec:
            continue
        task, sha = p.parent.parent.name, p.parent.name
        if rec.get("task_id") != task or rec.get("diff_sha256") != sha:
            raise RuntimeError(f"evaluation identity mismatch in {p}")
        out[(task, sha)] = rec
    return out


def summarize_v22(mod: ModuleType, tasks: list[str],
                  evals: dict[tuple[str, str], dict[str, Any]] | None = None) -> dict:
    """v2.1 counting rules, with the APPLIED join keyed by (task_id, diff_sha256)."""
    eps = mod._episodes()
    evals = evals_by_identity() if evals is None else evals
    by_cons = mod._by_construction()
    per_arm: dict[str, dict] = {}
    for arm in mod.ARMS:
        first_valid = post_repair = applied = resolved = f2p = p2ps = p2pu = 0
        arch_viol = 0
        missing_eval = 0
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
            for key in ("initial", "repair"):
                for err in ep.get("validation", {}).get(key, []):
                    if err.startswith(("OUT_OF_SCOPE_FILE", "TEST_PATH")):
                        arch_viol += 1
            if ep.get("status") == "APPLIED":
                applied += 1
                if ep.get("repair_used"):
                    post_repair += 1
                else:
                    first_valid += 1
                eval_rec = evals.get((tid, ep.get("diff_sha256", "")), {})
                if not eval_rec:
                    missing_eval += 1
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
            "first_call_valid": first_valid, "post_repair_valid": post_repair,
            "applied": applied, "resolved": resolved, "f2p": f2p, "p2p_s": p2ps,
            "p2p_u200": p2pu, "architecture_scope_violations": arch_viol,
            "applied_without_evaluation": missing_eval,
            "logical_tokens": int(tokens), "billed_tokens": int(tokens),
            "usd": round(usd, 6), "wall_time_s": round(mod._wall_span(wall_times), 1),
        }
    return per_arm


def decide(sg: dict[str, bool]) -> str:
    if not (sg["SG1_instrument"] and sg["SG2_completion"]):
        return "E2E_SMOKE_V22_INSTRUMENT_INVALID"
    if not sg["SG3_spend"]:
        return "E2E_SMOKE_V22_INSTRUMENT_INVALID"
    if not sg["SG4_floor"]:
        return "E2E_SMOKE_V22_FLOOR_EFFECT"
    return "E2E_SMOKE_V22_PIPELINE_VALID"


def main() -> int:
    freeze = _load(V22_ROOT / "smoke_v22_freeze.json")
    gen = _load(V22_ROOT / "generation_freeze_v22.json")
    if not freeze or not gen:
        print("SUMMARY_REFUSED freeze or generation freeze missing")
        return 1
    sys.path.insert(0, str(PROJECT / "scripts"))
    import wp2_e2e_v22_freeze as fz
    eval_ok = fz.eval_complete() == 0
    mod = load_v21_summary()
    pop = freeze["population"]
    evals = evals_by_identity()
    primary = summarize_v22(mod, pop, evals)
    secondary = summarize_v22(mod, [t for t in pop if t != mod.D220], evals)
    next_token, reason = mod._primary_gate(primary)
    from benchmark.wp2.e2e_v21.ledger import LedgerV21
    spend = LedgerV21(V22_ROOT / "ledger" / "spend_ledger_v22.jsonl",
                      {"SMOKE": SCIENTIFIC_CEILING_USD}).total()
    no_orphans = all(r["applied_without_evaluation"] == 0 for r in primary.values())
    sg = {"SG1_instrument": eval_ok and no_orphans,
          "SG2_completion": gen.get("n_episodes") == 62,
          "SG3_spend": spend <= SCIENTIFIC_CEILING_USD,
          "SG4_floor": primary["GOLD_HARD"]["resolved"] >= 1}
    token = decide(sg)
    if token == "E2E_SMOKE_V22_INSTRUMENT_INVALID":
        next_token, reason = "INSTRUMENT_FIX", "SG1/SG2/SG3 failed"
    out = {"artifact": "smoke_v22_summary",
           "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "token": token, "gates": sg, "next": next_token, "next_reason": reason,
           "spend_usd": round(spend, 6),
           "primary": {"n_tasks": len(pop), "per_arm": primary},
           "secondary_d220_omitted": {"per_arm": secondary,
                                      "note": "descriptive only; never changes token/NEXT"},
           "variance": variance_table(),
           "mandatory_wording": "Smoke v2.2 is pipeline validation on the engineering split "
                                "(DEV_TRAIN_ENG), n = 14. No comparative claim between "
                                "RM-CSS and Agent is made or supported."}
    (V22_ROOT / "smoke_v22_summary.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    lines = [f"# WP-2 E2E Smoke ENG v2.2 — Result ({time.strftime('%Y-%m-%d')})", "",
             f"Token: **{token}** — NEXT: **{next_token}** ({reason})", "",
             "| Gate | Result |", "|---|---|"]
    lines += [f"| {k} | {'PASS' if v else 'FAIL'} |" for k, v in sg.items()]
    lines += ["", "| Arm | first-call valid | post-repair valid | APPLIED | RESOLVED | F2P "
                  "| P2P-S | P2P-U200 | USD |", "|---|---|---|---|---|---|---|---|---|"]
    for arm, r in primary.items():
        lines.append(f"| {arm} | {r['first_call_valid']} | {r['post_repair_valid']} | "
                     f"{r['applied']} | {r['resolved']} | {r['f2p']} | {r['p2p_s']} | "
                     f"{r['p2p_u200']} | {r['usd']} |")
    lines += ["", f"Spend: ${spend:.6f} (ceiling ${SCIENTIFIC_CEILING_USD:.2f})", "",
              out["mandatory_wording"], ""]
    report = PROJECT / "docs" / f"WP2_E2E_SMOKE_ENG_V22_REPORT_{time.strftime('%Y-%m-%d')}.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    print("SUMMARY " + json.dumps({"token": token, "next": next_token, "gates": sg},
                                  sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
