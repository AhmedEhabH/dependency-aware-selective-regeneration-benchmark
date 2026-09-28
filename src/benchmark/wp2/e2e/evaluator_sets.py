"""WP-2 Mission-11 E2E Smoke - evaluator-only sets loader (B3).

Reads eng_evaluator_sets_v3.json (protected), verifies artifact_sha256, and
exposes per-task sets. Raises if called from a generator-side module
(benchmark.wp2.e2e.prompt / generate / validator / patch_format / pycompile /
llm_client / task_inputs).
"""
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4]
EVAL_PATH = PROJECT / "research/wp2/harness_v3_2026-09-26/evaluator_only/eng_evaluator_sets_v3.json"

GENERATOR_SIDE_MODULES = {
    "benchmark.wp2.e2e.prompt",
    "benchmark.wp2.e2e.generate",
    "benchmark.wp2.e2e.validator",
    "benchmark.wp2.e2e.patch_format",
    "benchmark.wp2.e2e.pycompile",
    "benchmark.wp2.e2e.llm_client",
    "benchmark.wp2.e2e.task_inputs",
}

_CACHE: dict | None = None


def _caller_is_generator() -> bool:
    for frame_info in inspect.stack():
        name = frame_info.frame.f_globals.get("__name__", "")
        if name in GENERATOR_SIDE_MODULES:
            return True
        if name.startswith("benchmark.wp2.e2e.") and name not in (
                "benchmark.wp2.e2e.scopes", "benchmark.wp2.e2e.evaluate",
                "benchmark.wp2.e2e.summary", "benchmark.wp2.e2e.evaluator_sets"):
            return True
    return False


def load_evaluator_sets() -> dict:
    global _CACHE
    if _caller_is_generator():
        raise RuntimeError("evaluator_only data accessed from a generator-side module")
    if _CACHE is not None:
        return _CACHE
    data = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    import copy
    check = copy.deepcopy(data)
    check.setdefault("hashes", {})["artifact_sha256"] = ""
    computed = hashlib.sha256(
        json.dumps(check, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    expected = data.get("hashes", {}).get("artifact_sha256")
    if expected is None or computed != expected:
        raise RuntimeError("evaluator sets artifact_sha256 mismatch")
    _CACHE = data
    return data
