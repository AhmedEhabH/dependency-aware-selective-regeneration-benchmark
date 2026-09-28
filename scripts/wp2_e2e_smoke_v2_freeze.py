#!/usr/bin/env python3
"""Mission-12 C2 / wrapper L: build the Smoke v2 freeze artifact.

Mirrors the v1 smoke_freeze.json structure with v2 values:
  - same 14 tasks, same four arms, same v1 scopes (hash-verified)
  - same model/route/temperature/max_tokens (frozen v1 identity)
  - interface wp2-e2e-interface-v2, smoke v2 constants
  - one repair max, full-context repair
  - run-level on-disk response cache (F03)
  - $2.00 ceiling (AU4)
  - generation order: task sorted, arm GOLD,RMCSS,AGENT,PLACEBO
  - variance probe: 3 control tasks x GOLD x 2 extra (var_r1, var_r2), cache bypass
  - gates G1-G4, token rule T, NEXT rule N
  - expressible denominator hash

Persists research/wp2/e2e_smoke_eng_v2/smoke_v2_freeze.json
"""
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
V1_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"


def sha_blob(rel: str) -> str:
    r = subprocess.run(["git", "-C", str(PROJECT), "cat-file", "blob", f"HEAD:{rel}"],
                       capture_output=True)
    return hashlib.sha256(r.stdout).hexdigest()


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    from benchmark.wp2.e2e.generate import _raw_scope
    from benchmark.wp2.e2e.prompt import REPAIR_HINT_ELLIPSIS, REPAIR_TEMPLATE, SYSTEM_PROMPT_V2
    from benchmark.wp2.e2e.response_cache import ResponseCache
    from benchmark.wp2.e2e.scopes import editable_filter
    from benchmark.wp2.e2e.spec import (
        ARMS,
        MAX_TOKENS,
        MODEL,
        SMOKE_TASKS,
        TEMPERATURE,
        TOP_P,
        spec_sha256,
    )

    scopes_per_arm = {}
    planned = []
    n_noscope = 0
    shas: set[str] = set()
    for tid in sorted(SMOKE_TASKS):
        for arm in ARMS:
            scope = editable_filter(tid, _raw_scope(tid, arm))
            planned.append({"task": tid, "arm": arm, "status": "PLANNED",
                            "n_editable": len(scope["editable"])})
            if not scope["editable"]:
                n_noscope += 1
                continue
            scope_hash = sha_blob(f"research/wp2/e2e_smoke_eng_v1/scopes/scopes_{arm}.json")
            scopes_per_arm.setdefault(arm, scope_hash)
            # initial request sha (system v2 + user prompt)
            from benchmark.wp2.e2e.prompt import build_prompt
            from benchmark.wp2.e2e.scopes import commits_of
            from benchmark.wp2.e2e.task_inputs import load_task_input
            ti = load_task_input(tid)
            parent, _ = commits_of(tid)
            import subprocess as sp
            texts = {}
            for p in scope["editable"]:
                r = sp.run(["git", "-C", str(PROJECT / "dist/pilot-repo-cache/saleor"),
                            "show", f"{parent}:{p}"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
                if r.returncode == 0:
                    texts[p] = r.stdout
            sys_p, user, _ = build_prompt(ti, scope["editable"], texts, scope)
            msgs = [{"role": "system", "content": sys_p},
                    {"role": "user", "content": user}]
            shas.add(ResponseCache.request_sha(MODEL,
                                               "openrouter:qwen/qwen3-coder@deepinfra/turbo",
                                               "deepinfra/turbo", TEMPERATURE, TOP_P,
                                               MAX_TOKENS, msgs))

    control_tasks = json.loads((V1_ROOT / "controls" / "control_tasks.json")
                               .read_text(encoding="utf-8"))["chosen"]
    prompt_templates_v2 = "\n".join([SYSTEM_PROMPT_V2, REPAIR_TEMPLATE, REPAIR_HINT_ELLIPSIS])
    prompt_sha_v2 = hashlib.sha256(prompt_templates_v2.encode("utf-8")).hexdigest()

    expr = json.loads((V2_ROOT / "controls" / "expressible_population.json")
                      .read_text(encoding="utf-8"))
    gates = {
        "G1": ("SG1 instrument validity = all B8 controls PASS + 0 replay routes in paid "
           "evidence + G-REPAIR-CONTEXT 100% + evidence integrity 100%"),
        "G2": "SG2 completion >= 95% episodes terminal; instrument anomalies <= 5%",
        "G3": "SG3 spend <= $2.00",
        "G4": "SG4 floor GOLD_HARD RESOLVED >= 1/14",
    }
    token_rule = ("E2E_SMOKE_V2_PIPELINE_VALID (G1-G4 PASS) / "
                  "E2E_SMOKE_V2_FLOOR_EFFECT (G1-G3 PASS, G4 FAIL) / "
                  "E2E_SMOKE_V2_INSTRUMENT_INVALID (G1 or G2 FAIL)")
    next_rule = {
        "N1": "GOLD APPLIED >= 7/14 and GOLD RESOLVED >= 3/14 -> NEXT=PILOT_DESIGN",
        "N2": "GOLD APPLIED >= 7/14 and GOLD RESOLVED <= 2/14 -> NEXT=GENERATOR_COMPETENCE_OR_SPEC_REVIEW",
        "N3": "GOLD APPLIED < 7/14 -> NEXT=INTERFACE_V3_PROBE",
        "N4": "instrument invalid -> NEXT=INSTRUMENT_FIX",
    }

    record = {
        "artifact": "smoke_v2_freeze",
        "smoke_version": "wp2-e2e-smoke-eng-v2",
        "interface_version": "wp2-e2e-interface-v2",
        "created_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "head": subprocess.run(["git", "-C", str(PROJECT), "rev-parse", "HEAD"],
                               capture_output=True, text=True).stdout.strip(),
        "population": SMOKE_TASKS,
        "arms": list(ARMS),
        "n_tasks": len(SMOKE_TASKS),
        "scopes_sha256_per_arm": scopes_per_arm,
        "spec_sha256": spec_sha256(),
        "interface_sha256": sha_blob("src/benchmark/wp2/e2e/spec.py"),
        "module_sha256_v2": {
            "generate_v2.py": sha_blob("src/benchmark/wp2/e2e/generate_v2.py"),
            "response_cache.py": sha_blob("src/benchmark/wp2/e2e/response_cache.py"),
            "patch_format.py": sha_blob("src/benchmark/wp2/e2e/patch_format.py"),
            "prompt.py": sha_blob("src/benchmark/wp2/e2e/prompt.py"),
            "llm_client.py": sha_blob("src/benchmark/wp2/e2e/llm_client.py"),
            "evaluate.py": sha_blob("src/benchmark/wp2/e2e/evaluate.py"),
            "evaluator_sets.py": sha_blob("src/benchmark/wp2/e2e/evaluator_sets.py"),
        },
        "prompt_templates_sha256_v2": prompt_sha_v2,
        "evaluator_sets_sha256": sha_blob("src/benchmark/wp2/e2e/evaluator_sets.py"),
        "harness_v3_identity": {"version": "wp2-harness-v3-2026-09-26",
                                "spec_sha256": None},  # filled below
        "model": MODEL, "route": "openrouter:qwen/qwen3-coder@deepinfra/turbo",
        "provider": "deepinfra/turbo",
        "temperature": TEMPERATURE, "top_p": TOP_P, "max_tokens": MAX_TOKENS,
        "max_repairs": 1,
        "ceilings": {"smoke_v2_usd": 2.00},
        "cache": {"type": "run-level on-disk ResponseCache",
                  "path": "research/wp2/e2e_smoke_eng_v2/cache/responses/<request_sha>.json",
                  "request_sha": "sha256(model|route|provider|temperature|top_p|max_tokens|json(messages))",
                  "repair_own_sha": True},
        "planned_episodes": planned,
        "n_planned": len(planned),
        "n_noscope": n_noscope,
        "expected_initial_request_shas": len(shas),
        "variance_probe": {
            "tasks": control_tasks,
            "arm": "GOLD_HARD",
            "extra_replicates": 2,
            "labels": ["var_r1", "var_r2"],
            "cache_bypass": True,
            "n_episodes": len(control_tasks) * 2,
        },
        "expressible_population": {
            "path": "research/wp2/e2e_smoke_eng_v2/controls/expressible_population.json",
            "hash": sha_file(V2_ROOT / "controls" / "expressible_population.json"),
            "expressible": expr["summary"]["expressible_count"],
        },
        "smoke_gates": gates,
        "token_rule": token_rule,
        "next_rule": next_rule,
        "mandatory_wording": ("Smoke v2 is engineering-split pipeline validation only. n = 14. "
                        "No comparative claim between RM-CSS and Agent is made or supported."),
    }

    # harness v3 spec sha from the module's own constant if available
    import re
    hv = (PROJECT / "src/benchmark/wp2/harness_v3.py").read_text(encoding="utf-8")
    m = re.search(r"HARNESS_V3_SPEC_SHA\s*=\s*[\"']([0-9a-f]{64})[\"']", hv)
    record["harness_v3_identity"]["spec_sha256"] = m.group(1) if m else None

    V2_ROOT.mkdir(parents=True, exist_ok=True)
    out = V2_ROOT / "smoke_v2_freeze.json"
    out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"SMOKE_V2_FREEZE={out}")
    print(f"N_PLANNED={len(planned)} N_NOSCOPE={n_noscope} EXPECTED_INITIAL_SHAS={len(shas)}")
    print(f"PROMPT_SHA_V2={prompt_sha_v2}")
    print(f"HASH={hashlib.sha256(out.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
