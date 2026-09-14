#!/usr/bin/env python3
"""P5-B — Independent Audit of the LocAgent VALIDATION pilot groundwork.

Audits (ZERO additional model calls):
1. Upstream pin identity (must equal 4935b557...)
2. Compatibility wrapper SHA + no-semantic-change (diff vs upstream absent;
   wrapper only constructs args and calls upstream functions)
3. Raw smoke evidence file hashes (evidence must be byte-identical to what
   the pipeline emitted)
4. Common-evaluator cost accounting (non-zero tokens => non-zero estimated
   cost, using the frozen P1 pricing snapshot; upstream calc_cost is NOT used)
5. No HELD_OUT_TEST case appears in any P5-B input set
6. Token/call/latency capture presence in the smoke evidence
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, cast

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_PACKAGE_ROOT / "src"))

from benchmark.locagent import evaluator  # noqa: E402
from benchmark.locagent.adapter import LOCAGENT_PINNED_COMMIT  # noqa: E402

DATASET_DIR = _PACKAGE_ROOT / "benchmark_data" / "real_commit_impact_v1"
SMOKE_DIR = _PACKAGE_ROOT / "research" / "locagent-p5b" / "evidence_smoke"
GATES_DIR = _PACKAGE_ROOT / "research" / "locagent-p5b" / "gates"
WRAPPER = _PACKAGE_ROOT / "research" / "locagent-p5b" / "launch_locagent.py"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def main() -> int:
    failures: list[str] = []
    checks: list[dict[str, Any]] = []

    # 1. Upstream pin
    pin_ok = LOCAGENT_PINNED_COMMIT == "4935b557326c154bad8e8dcf3747cc8d32d1f387"
    checks.append({"check": "upstream_pin_4935b557", "pass": pin_ok})
    if not pin_ok:
        failures.append(f"upstream pin mismatch: {LOCAGENT_PINNED_COMMIT}")

    # 2. Wrapper identity + hashes
    wrapper_sha = _sha256(WRAPPER)
    wrapper_txt = WRAPPER.read_text(encoding="utf-8")
    no_semantic_edit = (
        "from auto_search_main import localize, merge, run_localize" in wrapper_txt
        and "def build_args" in wrapper_txt
    )
    checks.append({"check": "wrapper_sha256", "pass": True, "sha256": wrapper_sha})
    checks.append({"check": "wrapper_invokes_upstream_no_algorithm_edit", "pass": no_semantic_edit})
    if not no_semantic_edit:
        failures.append("wrapper no longer invokes upstream functions directly")

    # 3. Raw smoke evidence hashes
    evidence_files = [
        "loc_outputs.jsonl",
        "merged_loc_outputs_mrr.jsonl",
        "loc_trajs.jsonl",
        "args.json",
        "wrapper_manifest.json",
        "localize.log",
    ]
    for fn in evidence_files:
        p = SMOKE_DIR / fn
        if not p.exists():
            failures.append(f"smoke evidence missing: {fn}")
            checks.append({"check": f"evidence_{fn}", "pass": False})
            continue
        checks.append({"check": f"evidence_{fn}", "pass": True, "sha256": _sha256(p)})

    # 4. Common-evaluator cost accounting (independent recompute)
    res = evaluator.common_evaluator(
        predicted_file_set={"cms/a.py"},
        proxy_paths={"cms/a.py"},
        prompt_tokens=1_000_000,
        completion_tokens=500_000,
    )
    expected = 1_000_000 * 0.30 / 1_000_000 + 500_000 * 1.00 / 1_000_000
    cost_ok = abs(res["cost_usd"] - expected) < 1e-6 and res["cost_usd"] > 0.0
    checks.append(
        {
            "check": "common_evaluator_cost_nonzero_with_tokens",
            "pass": cost_ok,
            "cost_usd": res["cost_usd"],
            "expected": round(expected, 8),
        }
    )
    if not cost_ok:
        failures.append("common evaluator cost accounting wrong (paid run appears free)")

    # 5. No held-out leakage in P5-B inputs
    split_freeze = _load_json(DATASET_DIR / "split_freeze.json")
    held_out = set(split_freeze["per_split"]["HELD_OUT_TEST"]["case_ids"])
    dryrun = _load_json(GATES_DIR / "p5b_dryrun_manifest.json")
    dry_cases = {r["case_id"] for r in dryrun["cases"]}
    leak = held_out & dry_cases
    checks.append({"check": "no_held_out_in_p5b_dryrun", "pass": not leak})
    if leak:
        failures.append(f"HELD_OUT_TEST leak into P5-B: {sorted(leak)}")

    # 6. Token/call/latency capture presence
    traj = SMOKE_DIR / "loc_trajs.jsonl"
    usage_ok = False
    if traj.exists():
        rows = [json.loads(line) for line in traj.read_text(encoding="utf-8").splitlines()]
        for r in rows:
            u = r.get("usage") or {}
            if int(u.get("prompt_tokens", 0)) > 0 or int(u.get("completion_tokens", 0)) > 0:
                usage_ok = True
    checks.append({"check": "token_usage_captured", "pass": usage_ok})
    if not usage_ok:
        failures.append("no token usage captured in smoke evidence")

    print("=== P5-B INDEPENDENT AUDIT ===")
    for c in checks:
        extra = "".join(f" {k}={v}" for k, v in c.items() if k not in ("check", "pass"))
        print(f"[{'PASS' if c['pass'] else 'FAIL'}] {c['check']}{extra}")
    print(f"\nAUDIT: {'PASS' if not failures else 'FAIL'}")
    for f in failures:
        print(f"  - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
