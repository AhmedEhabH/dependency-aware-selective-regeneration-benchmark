"""Mission-12B v2.1 - variance runner (T3).

3 frozen GOLD control tasks x 2 replicates (var_r1, var_r2). Each replicate:
- has a DISTINCT evidence path including the replicate label
  (variance/<task>/var_r1, variance/<task>/var_r2);
- gets its own cache namespace so an identical request between r1/r2 still
  invokes the provider twice (no response reuse);
- writes its own terminal record; r1 can never overwrite r2;
- merges spend into the same v21 ledger.

Descriptive only; no CI / population variance estimate / causal statement.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

V21_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v21"
HOLD = V21_ROOT / "HOLD"

from benchmark.wp2.e2e.response_cache import ResponseCache  # noqa: E402
from benchmark.wp2.e2e_v21.generate import E2E_ROOT_V21, run_episode_v21  # noqa: E402
from benchmark.wp2.e2e_v21.ledger import LedgerV21  # noqa: E402
from benchmark.wp2.e2e_v21.transport import V21HttpClient  # noqa: E402

SCIENTIFIC_CEILING_USD = 2.00

VARIANCE_TASKS = [
    "saleor-rc-644f33094857",
    "saleor-rc-2d45b76a52f2",
    "saleor-rc-d220843b5418",
]
VARIANCE_ARM = "GOLD_HARD"
REPLICATES = ("var_r1", "var_r2")


def run_variance(client: V21HttpClient | None = None,
                 ledger: LedgerV21 | None = None,
                 root: Path = E2E_ROOT_V21,
                 cache_namespace: str = "cache_variance") -> list[dict]:
    """Run six fresh variance replicates (3 tasks x 2 reps).

    Each replicate uses its own on-disk cache namespace (``<root>/<ns>/<label>``)
    so identical request bytes across r1/r2 still cause a fresh provider call.
    Returns the list of summary records.
    """
    if client is None:
        client = V21HttpClient(hold_file=HOLD)
    if ledger is None:
        ledger = LedgerV21(V21_ROOT / "ledger" / "spend_ledger_v21.jsonl",
                           {"SMOKE": SCIENTIFIC_CEILING_USD})
    recs: list[dict] = []
    for tid in sorted(VARIANCE_TASKS):
        for label in REPLICATES:
            cache = ResponseCache(root / cache_namespace / label)
            rec = run_episode_v21(tid, VARIANCE_ARM, client, ledger, cache, root,
                                  subdir="variance", label=label)
            recs.append({"label": label, "task_id": tid, "status": rec["status"],
                         "diff_sha256": rec["diff_sha256"],
                         "repair_used": rec.get("repair_used", False),
                         "request_sha_initial": rec.get("request_sha_initial", ""),
                         "actual_cost": rec.get("_actual_cost", 0.0),
                         "provider_calls": rec.get("_provider_calls", 0)})
    return recs


def main() -> int:
    recs = run_variance()
    out = {"artifact": "variance_v21", "tasks": VARIANCE_TASKS,
           "arm": VARIANCE_ARM, "replicates": list(REPLICATES),
           "episodes": recs,
           "note": "descriptive only; no CI / population variance estimate / causal statement"}
    (V21_ROOT / "variance").mkdir(parents=True, exist_ok=True)
    (V21_ROOT / "variance" / "variance_v21.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    ledger = LedgerV21(V21_ROOT / "ledger" / "spend_ledger_v21.jsonl",
                       {"SMOKE": SCIENTIFIC_CEILING_USD})
    print(f"[variance] episodes={len(recs)}; ledger total=${ledger.total():.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
