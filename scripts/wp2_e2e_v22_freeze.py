#!/usr/bin/env python3
"""WP-2 E2E Smoke v2.2 freeze / verification gates (brain-authored kit; hash-verified).

Subcommands (each exits 0 = PASS, 1 = FAIL with reasons printed as FREEZE_FAIL lines):
  --close-v21          classify the v2.1 run TRANSPORT_ABORTED_DIAGNOSTIC_RUN (HOLD + closure JSON)
  --build              write smoke_v22_freeze.json (code, scopes, evaluator, env identity, policy)
  --verify             recompute and compare with the freeze (code drift / env drift)
  --generation-freeze  check generation invariants and write generation_freeze_v22.json
  --eval-complete      PASS only when every planned unique diff and every non-APPLIED
                       episode has an evaluation record
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.e2e_v22 import circuit as circuit_mod  # noqa: E402
from benchmark.wp2.e2e_v22 import transport as transport_mod  # noqa: E402
from benchmark.wp2.e2e_v22.common import (  # noqa: E402
    EVALUATOR_SETS,
    FORBIDDEN_STATUS,
    SCIENTIFIC_CEILING_USD,
    SMOKE_VERSION_V22,
    TERMINAL,
    V1_ROOT,
    V21_ROOT,
    V22_ROOT,
    VARIANCE_ARM,
    VARIANCE_LABELS,
    VARIANCE_TASKS,
    env_identity,
    episode_path,
    json_sha256,
    norm_sha256,
    planned_main,
    planned_variance,
    read_status,
)

FREEZE_FILE = V22_ROOT / "smoke_v22_freeze.json"
GEN_FREEZE_FILE = V22_ROOT / "generation_freeze_v22.json"

CODE_GLOBS = (
    "src/benchmark/wp2/e2e/*.py",
    "src/benchmark/wp2/e2e_v21/*.py",
    "src/benchmark/wp2/e2e_v22/*.py",
    "scripts/wp2_e2e_v22_*.py",
    "scripts/wp2_ctl.py",
    "scripts/wp2_export_light.py",
    "scripts/wp2_e2e_smoke_v21_evaluate.py",
    "scripts/wp2_e2e_smoke_v21_summary.py",
    "scripts/wp2_linux_dryrun.py",
    "src/benchmark/wp2/harness_v3.py",
    "src/benchmark/wp2/oracle_semantics_v2.py",
    "controller/*.json",
)
SCOPE_FILES = {"GOLD_HARD": "scopes_GOLD_HARD.json", "RMCSS_HARD": "scopes_RMCSS_HARD.json",
               "AGENT_HARD": "scopes_AGENT_HARD.json", "PLACEBO_HARD": "scopes_PLACEBO_HARD.json"}
EXCLUDED_FROM_CODE_HASH = {"controller/controller_state.json"}


def _fail(reasons: list[str]) -> int:
    for r in reasons:
        print(f"FREEZE_FAIL {r}")
    return 1 if reasons else 0


def code_hashes(project: Path = PROJECT) -> dict[str, str]:
    out: dict[str, str] = {}
    for pattern in CODE_GLOBS:
        for p in sorted(project.glob(pattern)):
            rel = p.relative_to(project).as_posix()
            if rel in EXCLUDED_FROM_CODE_HASH or not p.is_file():
                continue
            out[rel] = norm_sha256(p)
    return out


def scope_hashes() -> tuple[dict[str, str], list[str]]:
    reasons: list[str] = []
    v1_freeze = json.loads((V1_ROOT / "smoke_freeze.json").read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for arm, fname in SCOPE_FILES.items():
        p = V1_ROOT / "scopes" / fname
        if not p.exists():
            reasons.append(f"scope file missing: {fname}")
            continue
        sem = json_sha256(json.loads(p.read_text(encoding="utf-8")))
        out[arm] = sem
        if sem != v1_freeze["scopes_sha256_per_arm"].get(arm):
            reasons.append(f"scope semantic hash differs from v1 freeze: {arm}")
    return out, reasons


def policy() -> dict[str, Any]:
    from benchmark.wp2.e2e.spec import ARMS, MAX_REPAIRS, MAX_TOKENS, MODEL, SMOKE_TASKS, TEMPERATURE, TOP_P
    return {
        "model": MODEL, "provider": transport_mod.PROVIDER, "allow_fallbacks": False,
        "temperature": TEMPERATURE, "top_p": TOP_P, "max_tokens": MAX_TOKENS,
        "max_repairs": MAX_REPAIRS, "workers": 1,
        "population": sorted(SMOKE_TASKS), "arms": list(ARMS),
        "variance": {"tasks": list(VARIANCE_TASKS), "arm": VARIANCE_ARM,
                     "labels": list(VARIANCE_LABELS)},
        "transport": {"max_attempts": transport_mod.MAX_ATTEMPTS,
                      "baseline_backoffs_s": list(transport_mod.BASELINE_BACKOFFS_S),
                      "retry_after_cap_s": transport_mod.RETRY_AFTER_CAP_S,
                      "min_pacing_s": transport_mod.MIN_PACING_S},
        "circuit": {"cooldown_s": circuit_mod.COOLDOWN_S,
                    "max_cooldowns": circuit_mod.MAX_COOLDOWNS,
                    "max_outage_s": circuit_mod.MAX_OUTAGE_S},
        "ceiling_usd": SCIENTIFIC_CEILING_USD,
        "terminal_statuses": sorted(TERMINAL),
        "provider_failures_are_scientific_outcomes": False,
    }


def close_v21() -> int:
    hold = V21_ROOT / "HOLD"
    if not hold.exists():
        hold.write_text("CLOSED: TRANSPORT_ABORTED_DIAGNOSTIC_RUN. Do not resume.\n",
                        encoding="utf-8")
    counts: dict[str, int] = {}
    for p in (V21_ROOT / "episodes").rglob("episode.json") if (V21_ROOT / "episodes").exists() else []:
        s = read_status(p) or "MISSING"
        counts[s] = counts.get(s, 0) + 1
    closure = {"artifact": "v21_closure", "classification": "TRANSPORT_ABORTED_DIAGNOSTIC_RUN",
               "resume": False, "scored": False, "episode_status_counts": counts,
               "reason": "provider HTTP 429 exhaustion was recorded as terminal GENERATION_FAIL; "
                         "v2.2 treats provider failures as pending infrastructure, so the v2.1 "
                         "run is closed as diagnostic evidence and a fresh v2.2 run starts at 0/56",
               "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (V21_ROOT / "V21_CLOSURE.json").write_text(json.dumps(closure, indent=1), encoding="utf-8")
    print("V21_CLOSED " + json.dumps(counts, sort_keys=True))
    return 0


def build(runner: Any = None) -> int:
    reasons: list[str] = []
    if FREEZE_FILE.exists():
        return _fail(["freeze already exists; a freeze is immutable (use --verify)"])
    for sub in ("episodes", "variance"):
        d = V22_ROOT / sub
        if d.exists() and any(d.rglob("episode.json")):
            reasons.append(f"v22 {sub} already contains episodes; freeze must precede generation")
    if not (V21_ROOT / "HOLD").exists():
        reasons.append("v21 HOLD missing: run --close-v21 first")
    scopes, r2 = scope_hashes()
    reasons += r2
    if not EVALUATOR_SETS.exists():
        reasons.append("evaluator sets missing")
    env = env_identity(runner) if runner else env_identity()
    if env["errors"]:
        reasons += [f"env: {e}" for e in env["errors"]]
    if reasons:
        return _fail(reasons)
    freeze = {
        "artifact": "smoke_v22_freeze", "smoke_version": SMOKE_VERSION_V22,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "policy": policy(), "population": policy()["population"],
        "scopes_semantic_sha256": scopes,
        "evaluator_sets_sha256": norm_sha256(EVALUATOR_SETS),
        "code_sha256": code_hashes(),
        "env_identity": env,
        "planned_main": [list(x) for x in planned_main()],
        "planned_variance": [list(x) for x in planned_variance()],
        "reproducibility_note": "Fresh API generation is a replication, not a bit-exact "
                                "reproduction; exact reproducibility is defined as replaying "
                                "the frozen raw responses/diffs through the frozen evaluator.",
    }
    freeze["freeze_sha256"] = json_sha256({k: v for k, v in freeze.items()
                                           if k not in ("created_utc", "freeze_sha256")})
    V22_ROOT.mkdir(parents=True, exist_ok=True)
    FREEZE_FILE.write_text(json.dumps(freeze, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"FREEZE_BUILT {freeze['freeze_sha256']}")
    return 0


def verify(runner: Any = None) -> int:
    if not FREEZE_FILE.exists():
        return _fail(["freeze missing"])
    freeze = json.loads(FREEZE_FILE.read_text(encoding="utf-8"))
    reasons: list[str] = []
    now = code_hashes()
    for rel, h in freeze["code_sha256"].items():
        if now.get(rel) != h:
            reasons.append(f"CODE_DRIFT {rel}")
    for rel in sorted(set(now) - set(freeze["code_sha256"])):
        reasons.append(f"CODE_ADDED_AFTER_FREEZE {rel}")
    scopes, r2 = scope_hashes()
    reasons += r2
    if scopes != freeze["scopes_semantic_sha256"]:
        reasons.append("SCOPE_DRIFT")
    if norm_sha256(EVALUATOR_SETS) != freeze["evaluator_sets_sha256"]:
        reasons.append("EVALUATOR_SETS_DRIFT")
    if policy() != freeze["policy"]:
        reasons.append("POLICY_DRIFT")
    env = env_identity(runner) if runner else env_identity()
    if env["errors"]:
        reasons += [f"ENV_UNAVAILABLE {e}" for e in env["errors"]]
    elif env["era_images"] != freeze["env_identity"]["era_images"]:
        reasons.append("ENV_DRIFT era images")
    elif env["postgres"].get("image_id") != freeze["env_identity"]["postgres"].get("image_id"):
        reasons.append("ENV_DRIFT postgres image")
    if not reasons:
        print("FREEZE_VERIFY_PASS")
    return _fail(reasons)


def _episode_dir_calls_ok(ep_file: Path, rec: dict[str, Any]) -> list[str]:
    bad: list[str] = []
    for c in rec.get("calls", []):
        if c.get("route") == "replay":
            bad.append(f"replay route in {ep_file}")
        idx, kind = c.get("index", 0), c.get("kind", "")
        if idx and c.get("raw_sha256") and kind in ("initial", "repair"):
            raw = ep_file.parent / "calls" / f"{idx}_{kind}.txt"
            if not raw.exists():
                bad.append(f"raw response missing {raw}")
            elif hashlib.sha256(raw.read_bytes()).hexdigest() != c["raw_sha256"]:
                bad.append(f"raw response hash mismatch {raw}")
    return bad


def generation_freeze() -> int:
    reasons: list[str] = []
    entries: dict[str, Any] = {}
    for subdir, plan in (("episodes", planned_main()), ("variance", planned_variance())):
        for task_id, _arm, label in plan:
            p = episode_path(V22_ROOT, subdir, task_id, label)
            status = read_status(p)
            if status not in TERMINAL:
                reasons.append(f"not terminal: {subdir}/{task_id}/{label} status={status}")
                continue
            rec = json.loads(p.read_text(encoding="utf-8"))
            reasons += _episode_dir_calls_ok(p, rec)
            entries[p.relative_to(V22_ROOT).as_posix()] = {
                "status": status, "diff_sha256": rec.get("diff_sha256", ""),
                "episode_file_sha256": norm_sha256(p)}
    for sub in ("episodes", "variance"):
        d = V22_ROOT / sub
        for p in (d.rglob("episode.json") if d.exists() else []):
            if read_status(p) in FORBIDDEN_STATUS:
                reasons.append(f"forbidden status in {p}")
    from benchmark.wp2.e2e_v21.ledger import LedgerV21
    ledger = LedgerV21(V22_ROOT / "ledger" / "spend_ledger_v22.jsonl",
                       {"SMOKE": SCIENTIFIC_CEILING_USD})
    if ledger.total() > SCIENTIFIC_CEILING_USD:
        reasons.append(f"spend {ledger.total():.6f} > ceiling")
    if reasons:
        return _fail(reasons)
    payload = {"artifact": "generation_freeze_v22", "n_episodes": len(entries),
               "episodes": entries, "spend_usd": round(ledger.total(), 6)}
    payload["generation_freeze_sha256"] = json_sha256(payload)
    if GEN_FREEZE_FILE.exists():
        old = json.loads(GEN_FREEZE_FILE.read_text(encoding="utf-8"))
        if old.get("generation_freeze_sha256") != payload["generation_freeze_sha256"]:
            return _fail(["generation freeze exists and differs (evidence changed after freeze)"])
    GEN_FREEZE_FILE.write_text(json.dumps(payload, indent=1, ensure_ascii=False),
                               encoding="utf-8")
    counts: dict[str, int] = {}
    for e in entries.values():
        counts[e["status"]] = counts.get(e["status"], 0) + 1
    print("GENERATION_FROZEN " + json.dumps({"n": len(entries), "status": counts,
                                             "spend_usd": payload["spend_usd"]}, sort_keys=True))
    return 0


def eval_complete() -> int:
    plan_path = V22_ROOT / "evaluations" / "plan.json"
    if not plan_path.exists():
        return _fail(["evaluation plan missing"])
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    reasons: list[str] = []
    for item in plan["items"]:
        label = f"unique_{item['diff_sha256'][:8]}"
        if not (V22_ROOT / "evaluations" / "unique" / label / "evaluation.json").exists():
            reasons.append(f"missing unique evaluation {label}")
    for subdir, plan_items in (("episodes", planned_main()), ("variance", planned_variance())):
        for task_id, _arm, label in plan_items:
            p = episode_path(V22_ROOT, subdir, task_id, label)
            if read_status(p) != "APPLIED":
                rec_path = V22_ROOT / "evaluations" / subdir / task_id / label / "evaluation.json"
                if not rec_path.exists():
                    reasons.append(f"missing by-construction record {subdir}/{label}")
    if not reasons:
        print(f"EVAL_COMPLETE n_unique={plan['n_unique_diffs']}")
    return _fail(sorted(set(reasons))[:40])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    for flag in ("--close-v21", "--build", "--verify", "--generation-freeze", "--eval-complete"):
        g.add_argument(flag, action="store_true")
    a = ap.parse_args(argv)
    if a.close_v21:
        return close_v21()
    if a.build:
        return build()
    if a.verify:
        return verify()
    if a.generation_freeze:
        return generation_freeze()
    return eval_complete()


if __name__ == "__main__":
    raise SystemExit(main())
