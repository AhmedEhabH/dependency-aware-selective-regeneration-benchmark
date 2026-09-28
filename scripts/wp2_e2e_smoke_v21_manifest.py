"""Mission-12B v2.1 - L2 frozen executable manifest (zero API).

Every code/script/config that can affect:
- provider call
- prompt
- scope
- patch parsing/apply
- caching
- generation
- variance
- evaluation
- summarization/gates

is hashed and recorded. A separate independent verification is performed by
recomputing hashes and comparing (L3).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
V21_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v21"

CATEGORIES = {
    "v21_generation_transport": [
        "src/benchmark/wp2/e2e_v21/transport.py",
        "src/benchmark/wp2/e2e_v21/generate.py",
        "src/benchmark/wp2/e2e_v21/ledger.py",
        "scripts/wp2_e2e_smoke_v21_generate.py",
        "scripts/wp2_e2e_smoke_v21_variance.py",
    ],
    "v21_freeze_eval_summary": [
        "scripts/wp2_e2e_smoke_v21_freeze.py",
        "scripts/wp2_e2e_smoke_v21_evaluate.py",
        "scripts/wp2_e2e_smoke_v21_summary.py",
        "scripts/wp2_e2e_smoke_v21_controls.py",
        "scripts/wp2_e2e_smoke_v21_preflight.py",
    ],
    "frozen_v2_instrument": [
        "src/benchmark/wp2/e2e/generate.py",
        "src/benchmark/wp2/e2e/generate_v2.py",
        "src/benchmark/wp2/e2e/response_cache.py",
        "src/benchmark/wp2/e2e/patch_format.py",
        "src/benchmark/wp2/e2e/prompt.py",
        "src/benchmark/wp2/e2e/llm_client.py",
        "src/benchmark/wp2/e2e/scopes.py",
        "src/benchmark/wp2/e2e/spec.py",
        "src/benchmark/wp2/e2e/task_inputs.py",
        "src/benchmark/wp2/e2e/pycompile.py",
    ],
    "evaluator": [
        "src/benchmark/wp2/e2e/evaluate.py",
        "src/benchmark/wp2/e2e/evaluator_sets.py",
        "research/wp2/harness_v3_2026-09-26/evaluator_only/eng_evaluator_sets_v3.json",
    ],
    "harness": [
        "src/benchmark/wp2/harness_v3.py",
        "research/wp2/harness_v3_2026-09-26/harness_v3_spec.json",
    ],
    "scope_data": [
        "research/wp2/e2e_smoke_eng_v1/scopes/scopes_GOLD_HARD.json",
        "research/wp2/e2e_smoke_eng_v1/scopes/scopes_RMCSS_HARD.json",
        "research/wp2/e2e_smoke_eng_v1/scopes/scopes_AGENT_HARD.json",
        "research/wp2/e2e_smoke_eng_v1/scopes/scopes_PLACEBO_HARD.json",
    ],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = {
        "artifact": "frozen_executable_manifest_v21",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "head": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                               text=True).stdout.strip(),
        "freeze_tag": "wp2-e2e-smoke-eng-v21-freeze-2026-09-29",
        "hold_present_at_manifest_build": (V21_ROOT / "HOLD").exists(),
        "files": {},
    }
    missing = []
    for cat, rels in CATEGORIES.items():
        for rel in rels:
            p = PROJECT / rel
            if not p.exists():
                missing.append(rel)
                continue
            manifest["files"][rel] = {
                "category": cat,
                "sha256": sha256(p),
            }
    if missing:
        print("MANIFEST_MISSING_FILES", json.dumps(missing))
        return 1
    manifest["manifest_sha256"] = hashlib.sha256(
        json.dumps({k: v for k, v in manifest.items() if k != "manifest_sha256"},
                   sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    (V21_ROOT / "frozen_executable_manifest_v21.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("MANIFEST_OK", manifest["manifest_sha256"], "files", len(manifest["files"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
