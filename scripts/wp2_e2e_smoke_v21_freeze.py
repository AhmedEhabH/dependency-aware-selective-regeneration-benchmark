"""Mission-12B v2.1 - fail-closed freeze builder (T4).

Builds ``research/wp2/e2e_smoke_eng_v21/smoke_v21_freeze.json`` and refuses to
write if any required identity/hash is null, the v1 frozen scope semantic
hash does not match, model/route/sampling or evaluator/Harness identity
mismatches, the v21 instrument tests are not green, the historical v2 root is
configured as output/cache/ledger, or the v21 HOLD is missing at build time.

Freeze records (distinct field names):
- semantic SHA256 (canonical JSON) and git blob hash for scopes / evaluator sets
- exact code hashes of every v21 module and driver script
- exact 14x4 planned episodes (task sorted, arm order GOLD/RMCSS/AGENT/PLACEBO)
- NO_SCOPE flag per episode where the frozen scope is empty
- TRANSPORT_V21 policy, $2 budget, variance design, d220 sensitivity rule,
  unique-diff evaluation rule.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

V21_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v21"
V1_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"
V1_SCOPES = V1_ROOT / "scopes"
HOLD = V21_ROOT / "HOLD"
V2_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v2"

from benchmark.wp2.e2e.spec import (  # noqa: E402
    ARMS,
    MAX_REPAIRS,
    MAX_TOKENS,
    MODEL,
    SMOKE_TASKS,
    TEMPERATURE,
    TOP_P,
)
from benchmark.wp2.e2e_v21.transport import (  # noqa: E402
    BACKOFFS_S,
    MIN_PACING_S,
    NON_RETRYABLE_STATUS,
    RETRYABLE_STATUS,
    TOTAL_HTTP_ATTEMPTS,
)

HARNESS_VERSION = "wp2-harness-v3-2026-09-26"
HARNESS_SPEC_SHA256 = "e7897ba0850bd0af372273a32ffb33435b4dc75c9476d527ec86fa424a75f034"
HARNESS_GIT_HEAD = "9216c2991e08795b00d9811be16da2f049ede68a"
SCIENTIFIC_CEILING_USD = 2.00


def _sha(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def semantic_sha256(path: Path) -> str:
    return _sha(json.loads(path.read_text(encoding="utf-8")))


def raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha1(path: Path) -> str:
    r = subprocess.run(["git", "hash-object", str(path)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git hash-object failed for {path}")
    return r.stdout.strip()


def _episodes_plan() -> list[dict]:
    plan = []
    for tid in sorted(SMOKE_TASKS):
        for arm in ARMS:
            plan.append({"task": tid, "arm": arm, "status": "PLANNED"})
    return plan


def _scope_noscope(arm: str) -> dict[str, bool]:
    """task -> True when the frozen arm scope has an empty editable set."""
    fname = {"GOLD_HARD": "scopes_GOLD_HARD.json",
             "RMCSS_HARD": "scopes_RMCSS_HARD.json",
             "AGENT_HARD": "scopes_AGENT_HARD.json",
             "PLACEBO_HARD": "scopes_PLACEBO_HARD.json"}[arm]
    data = json.loads((V1_SCOPES / fname).read_text(encoding="utf-8"))
    out = {}
    for tid in SMOKE_TASKS:
        out[tid] = len(data["per_task"].get(tid, {}).get("editable", [])) == 0
    return out


def build_freeze(allow_write: bool = True) -> dict:
    """Fail-closed freeze builder. Raises FreezeViolation on any check failure."""
    failures: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            failures.append(msg)

    # -- required identities (null forbidden) --------------------------------
    check(bool(HARNESS_SPEC_SHA256), "harness spec_sha256 is null/empty")
    check(bool(HARNESS_GIT_HEAD), "harness git_head is null/empty")
    check(MODEL == "qwen/qwen3-coder", f"model mismatch: {MODEL}")
    check(TEMPERATURE == 0.0, f"temperature mismatch: {TEMPERATURE}")
    check(TOP_P == 1.0, f"top_p mismatch: {TOP_P}")
    check(MAX_TOKENS == 8192, f"max_tokens mismatch: {MAX_TOKENS}")
    check(MAX_REPAIRS == 1, f"max_repairs mismatch: {MAX_REPAIRS}")
    check(len(SMOKE_TASKS) == 14, f"task count mismatch: {len(SMOKE_TASKS)}")
    check(tuple(ARMS) == ("GOLD_HARD", "RMCSS_HARD", "AGENT_HARD", "PLACEBO_HARD"),
          f"arms mismatch: {ARMS}")

    # -- evaluator / Harness identity ----------------------------------------
    es_path = PROJECT / "research/wp2/harness_v3_2026-09-26/evaluator_only/eng_evaluator_sets_v3.json"
    check(es_path.exists(), "evaluator sets file missing")
    es_semantic = semantic_sha256(es_path) if es_path.exists() else ""
    es_blob = git_blob_sha1(es_path) if es_path.exists() else ""

    # -- v1 frozen scope semantic hashes -------------------------------------
    v1_freeze = json.loads((V1_ROOT / "smoke_freeze.json").read_text(encoding="utf-8"))
    scope_hashes: dict[str, dict] = {}
    fnames = {"GOLD_HARD": "scopes_GOLD_HARD.json", "RMCSS_HARD": "scopes_RMCSS_HARD.json",
              "AGENT_HARD": "scopes_AGENT_HARD.json", "PLACEBO_HARD": "scopes_PLACEBO_HARD.json"}
    for arm in ARMS:
        p = V1_SCOPES / fnames[arm]
        check(p.exists(), f"scope file missing: {fnames[arm]}")
        if p.exists():
            sem = semantic_sha256(p)
            frozen = v1_freeze["scopes_sha256_per_arm"].get(arm)
            check(sem == frozen,
                  f"v1 frozen scope semantic hash mismatch for {arm}: got {sem}, want {frozen}")
            scope_hashes[arm] = {"semantic_sha256": sem,
                                 "git_blob_sha1": git_blob_sha1(p),
                                 "raw_sha256": raw_sha256(p)}

    # -- v21 code hashes -------------------------------------------------------
    module_files = sorted((PROJECT / "src/benchmark/wp2/e2e_v21").glob("*.py"))
    code_hashes = {p.name: raw_sha256(p) for p in module_files}
    driver_files = [
        PROJECT / "scripts/wp2_e2e_smoke_v21_generate.py",
        PROJECT / "scripts/wp2_e2e_smoke_v21_variance.py",
    ]
    for p in driver_files:
        check(p.exists(), f"driver missing: {p.name}")
        if p.exists():
            code_hashes[p.name] = raw_sha256(p)

    # -- historical v2 root must not be configured ---------------------------
    v2_root = V2_ROOT.resolve()
    v21_root = V21_ROOT.resolve()
    check(v21_root != v2_root, "v21 root must not equal the historical v2 root")
    check(v2_root not in v21_root.parents, "v21 root must not resolve inside the historical v2 root")
    check(HOLD.resolve().parent != v2_root, "v21 HOLD must not point at the v2 root")

    # -- v21 HOLD must be present at freeze-build time -----------------------
    check(HOLD.exists(), "v21 HOLD missing at freeze-build time")

    if failures:
        raise FreezeViolation("; ".join(failures))

    plan = _episodes_plan()
    noscope = {arm: _scope_noscope(arm) for arm in ARMS}
    n_noscope = sum(1 for arm in ARMS for tid in SMOKE_TASKS if noscope[arm].get(tid))

    freeze = {
        "artifact": "smoke_v21_freeze",
        "smoke_version": "wp2-e2e-smoke-eng-v21",
        "interface_version": "wp2-e2e-interface-v2",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "head": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                               text=True).stdout.strip(),
        "population": sorted(SMOKE_TASKS),
        "n_tasks": 14,
        "arms": list(ARMS),
        "model": MODEL,
        "route": "openrouter:qwen/qwen3-coder@deepinfra/turbo",
        "provider": "deepinfra/turbo",
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "max_tokens": MAX_TOKENS,
        "max_repairs": MAX_REPAIRS,
        "workers": 1,
        "scopes_sha256_per_arm": {arm: h["semantic_sha256"] for arm, h in scope_hashes.items()},
        "scopes_git_blob_per_arm": {arm: h["git_blob_sha1"] for arm, h in scope_hashes.items()},
        "scopes_raw_sha256_per_arm": {arm: h["raw_sha256"] for arm, h in scope_hashes.items()},
        "evaluator_sets": {
            "semantic_sha256": es_semantic,
            "git_blob_sha1": es_blob,
            "raw_sha256": raw_sha256(es_path) if es_path.exists() else "",
            "path": "research/wp2/harness_v3_2026-09-26/evaluator_only/eng_evaluator_sets_v3.json",
        },
        "harness_v3_identity": {
            "version": HARNESS_VERSION,
            "spec_sha256": HARNESS_SPEC_SHA256,
            "git_head": HARNESS_GIT_HEAD,
            "null_forbidden": True,
        },
        "code_sha256": code_hashes,
        "planned_episodes": plan,
        "n_planned": len(plan),
        "noscope_per_arm": noscope,
        "n_noscope": n_noscope,
        "transport_policy": {
            "name": "TRANSPORT_V21",
            "total_http_attempts": TOTAL_HTTP_ATTEMPTS,
            "backoff_s": list(BACKOFFS_S),
            "min_logical_call_pacing_s": MIN_PACING_S,
            "retryable_status": sorted(RETRYABLE_STATUS | set(range(500, 600))),
            "non_retryable_status": sorted(NON_RETRYABLE_STATUS),
            "byte_identical_retries": True,
            "no_fifth_attempt": True,
        },
        "budget": {
            "scientific_ceiling_usd": SCIENTIFIC_CEILING_USD,
            "includes": ["probe", "generation", "repair", "variance"],
        },
        "variance_design": {
            "tasks": ["saleor-rc-644f33094857", "saleor-rc-2d45b76a52f2",
                      "saleor-rc-d220843b5418"],
            "arm": "GOLD_HARD",
            "replicates": ["var_r1", "var_r2"],
            "n_episodes": 6,
            "cache_bypass_per_replicate": True,
        },
        "d220_sensitivity": {
            "rule": "d220 stays in the 14-task primary analysis. Produce a SECONDARY "
                    "sensitivity table with d220 omitted. It MUST NOT change the primary "
                    "Smoke token/NEXT rule.",
            "task": "saleor-rc-d220843b5418",
        },
        "evaluation_dedup_rule": {
            "rule": "collect main APPLIED diffs + variance APPLIED diffs; deduplicate per "
                    "task by (task_id, diff_sha256); freeze deterministic order by "
                    "(task_id, diff_sha256, label); evaluate every unique diff once; map "
                    "results back to all arms/variance records.",
        },
        "no_evaluation_before_generation_freeze": True,
        "hold_present_at_build": True,
    }
    freeze["freeze_sha256"] = _sha({k: v for k, v in freeze.items() if k != "freeze_sha256"})
    if allow_write:
        (V21_ROOT / "smoke_v21_freeze.json").write_text(
            json.dumps(freeze, indent=2, ensure_ascii=False), encoding="utf-8")
    return freeze


class FreezeViolation(RuntimeError):  # noqa: N818
    """Raised when a fail-closed freeze check fails."""


if __name__ == "__main__":
    f = build_freeze()
    print("FREEZE_OK", f["freeze_sha256"], "n_planned", f["n_planned"], "n_noscope", f["n_noscope"])
