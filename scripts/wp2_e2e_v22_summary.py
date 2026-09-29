#!/usr/bin/env python3
"""WP-2 E2E Smoke v2.2 mechanical summary + gates (brain-authored kit; hash-verified).

Reuses the frozen v2.1 per-arm summarizer and NEXT rule unchanged (pointed at the v2.2
root) and adds the mechanical Smoke gates:

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
    primary = mod.summarize(pop)
    secondary = mod.summarize([t for t in pop if t != mod.D220])
    next_token, reason = mod._primary_gate(primary)
    from benchmark.wp2.e2e_v21.ledger import LedgerV21
    spend = LedgerV21(V22_ROOT / "ledger" / "spend_ledger_v22.jsonl",
                      {"SMOKE": SCIENTIFIC_CEILING_USD}).total()
    sg = {"SG1_instrument": eval_ok,
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
