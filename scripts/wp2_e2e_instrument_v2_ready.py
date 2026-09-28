#!/usr/bin/env python3
"""Mission-12 J10: build instrument_v2_ready.json from the persisted control evidence."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))
V2_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v2"


def load(name: str) -> dict:
    return json.loads((V2_ROOT / "controls" / name).read_text(encoding="utf-8"))


def main() -> int:
    fmt = load("g_format_v2.json")
    noisy = load("g_format_noisy_v2.json")
    pos = load("g_pos_v2.json")
    neg = load("g_neg_v2.json")
    ctx = load("g_repair_context_v2.json")
    cache = load("g_cache_v2.json")
    leak = load("g_leak_v2.json")
    replay = load("g_replay_v2.json")
    budget = load("g_budget_v2.json")
    expr = load("expressible_population.json")

    def sha(path: str) -> str:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    gates = {
        "G_FORMAT_CLEAN": {"pass": fmt["summary"]["expected_100pct"],
                           "detail": fmt["summary"]},
        "G_FORMAT_NOISY": {"pass": noisy["summary"]["expected_100pct"],
                           "detail": noisy["summary"]},
        "G_POS": {"pass": pos["summary"]["tree_matches"] == "3/3"
                           and pos["summary"]["f2p_pass"] == 3,
                  "detail": pos["summary"]},
        "G_NEG": {"pass": neg["summary"]["f2p_fail"] == 3
                         and neg["summary"]["resolved_false"] == 3,
                  "detail": neg["summary"]},
        "G_REPAIR_CONTEXT": {"pass": ctx["summary"]["expected_3_3"],
                             "detail": ctx["summary"]},
        "G_CACHE": {"pass": cache["match"], "detail": {
            "logical_requests": cache["logical_requests"],
            "unique_request_shas": cache["unique_request_shas"],
            "client_invocations": cache["client_invocations"]}},
        "G_LEAK": {"pass": leak["expected_0_blocking"],
                   "detail": {"blocking_total": leak["blocking_total"]}},
        "G_REPLAY": {"pass": replay["expected_0"],
                     "detail": {"replay_routes": replay["replay_routes_in_paid_episodes"]}},
        "G_BUDGET": {"pass": budget["within_ceiling"],
                     "detail": {"worst_case_usd": budget["worst_case_smoke_usd"],
                                "ceiling_usd": budget["ceiling_smoke_v2_usd"]}},
    }
    all_pass = all(g["pass"] for g in gates.values())

    record = {
        "artifact": "instrument_v2_ready",
        "created_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "head": subprocess.run(["git", "-C", str(PROJECT), "rev-parse", "HEAD"],
                               capture_output=True, text=True).stdout.strip(),
        "interface_version": "wp2-e2e-interface-v2",
        "smoke_version_v2": "wp2-e2e-smoke-eng-v2",
        "expressible_population": {
            "path": "research/wp2/e2e_smoke_eng_v2/controls/expressible_population.json",
            "expressible": expr["summary"]["expressible_count"],
            "modified_non_test": expr["summary"]["modified_non_test_count"],
            "hash": sha(str(V2_ROOT / "controls" / "expressible_population.json")),
        },
        "gates": gates,
        "all_gates_pass": all_pass,
        "module_shas": {
            "spec.py": sha("src/benchmark/wp2/e2e/spec.py"),
            "llm_client.py": sha("src/benchmark/wp2/e2e/llm_client.py"),
            "prompt.py": sha("src/benchmark/wp2/e2e/prompt.py"),
            "patch_format.py": sha("src/benchmark/wp2/e2e/patch_format.py"),
            "generate.py": sha("src/benchmark/wp2/e2e/generate.py"),
            "generate_v2.py": sha("src/benchmark/wp2/e2e/generate_v2.py"),
            "response_cache.py": sha("src/benchmark/wp2/e2e/response_cache.py"),
            "evaluate.py": sha("src/benchmark/wp2/e2e/evaluate.py"),
            "evaluator_sets.py": sha("src/benchmark/wp2/e2e/evaluator_sets.py"),
        },
        "unit_test_counts": {"instrument_v2": 27, "instrument_v1": 12},
    }
    dest = V2_ROOT / "instrument_v2_ready.json"
    dest.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"INSTRUMENT_V2_READY={dest}")
    print(f"ALL_GATES_PASS={all_pass}")
    print(f"HASH={hashlib.sha256(dest.read_bytes()).hexdigest()}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
