"""Aggregate P2P-U V2 ENG resource samples (Mission-09) - ZERO API.

Builds the per-task/cap and aggregate resource summary (RAM, CPU, disk, time)
from the raw resource_samples.jsonl files persisted by the sampler.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.resource_sampler import aggregate_samples  # noqa: E402

EVIDENCE_ROOT = PROJECT / "research" / "wp2" / "p2p_u_v2_eng_2026-09-25"
OUT = EVIDENCE_ROOT / "resource_summary_2026-09-25.json"

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


def main() -> int:
    per_task: dict = {}
    for tid in ENG_EXECUTED:
        for cap in (200, 400):
            sf = EVIDENCE_ROOT / tid / f"cap{cap}" / "A" / "resource_samples.jsonl"
            agg = aggregate_samples(sf) if sf.exists() else {"n_samples": 0}
            per_task.setdefault(tid, {})[f"cap{cap}"] = agg

    # Aggregate across all executed task/cap runs (pool all raw samples).
    all_paths = [
        EVIDENCE_ROOT / tid / f"cap{cap}" / "A" / "resource_samples.jsonl"
        for tid in ENG_EXECUTED for cap in (200, 400)
    ]
    combined = EVIDENCE_ROOT / "_combined_resource_samples.jsonl"
    with combined.open("w", encoding="utf-8") as out:
        for p in all_paths:
            if p.exists():
                out.write(p.read_text(encoding="utf-8"))
    agg_all = aggregate_samples(combined)
    combined.unlink(missing_ok=True)

    payload = {
        "artifact": "wp2_p2p_u_v2_eng_resource_summary",
        "date": "2026-09-25",
        "mission": "Mission-09 sections 15/16",
        "sampler_version": "wp2-resource-sampler-v1-2026-09-25",
        "sampling_interval_s": 5,
        "per_task_cap": per_task,
        "aggregate_all_runs": agg_all,
        "notes": [
            "host_used_gib = host_total - host_available (never total-as-peak).",
            "wsl_used_gib = MemTotal - MemAvailable; wsl_mem_total_gib is the VM ceiling.",
            "docker cpu_percent is core-normalized by docker (100% = 1 core); not whole-machine.",
            "LIMITATION: during the 16 ENG task/cap executions the resource sampler "
            "queried only wp2-pg for per-container metrics; the active wp2-test-* "
            "test container ran without a stable --name and its per-container RAM "
            "was NOT separately captured. WSL used (MemTotal-MemAvailable, peak "
            f"{agg_all.get('wsl_used_gib', {}).get('max')} GiB) is the conservative "
            "binding upper bound for all WSL-internal consumers (test container + "
            "postgres + docker daemon + fs cache). The sampler now auto-discovers "
            "wp2-test-* containers and the exec runner names the test container, so "
            "future DEV-47 / MAIN runs capture per-test-container RAM directly.",
        ],
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT)
    print("aggregate:", json.dumps(
        {k: v for k, v in agg_all.items() if k != "docker"}, indent=1, sort_keys=True))
    print("docker aggregate:", json.dumps(agg_all.get("docker", {}), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
