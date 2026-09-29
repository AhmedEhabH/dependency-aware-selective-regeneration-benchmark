#!/usr/bin/env python3
"""WP2 M14A Pilot-A engine (brain-authored corrected kit).

Only `generate` may call the model API. `doctor-paid` uses read-only credit/pricing
metadata endpoints. Every other subcommand makes zero model/API calls.

Subcommands (one atomic step each):
  auth-check | doctor-offline | doctor-paid | canary | freeze | freeze-verify |
  generate | generation-complete | generation-freeze | generation-freeze-verify |
  eval-plan | evaluate | eval-complete | summary
Exit codes: 0 PASS/progress, 1 check-not-yet, 3 HOLD, 4 stop flag, 32 not authorized,
33 preflight fail, 75 provider outage, 76 request rejected, 77 budget, 78 invariant,
79 evaluation infrastructure error (resumable).
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
for _p in (PROJECT, PROJECT / "src", PROJECT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

ROOT = PROJECT / "research/wp2/pilot_a_v1"
DESIGN_ROOT = PROJECT / "research/wp2/pilot_v1_design"
DESIGN = DESIGN_ROOT / "pilot_design_freeze_v1.json"
SELECTION = DESIGN_ROOT / "pilot_selection.json"
AUTH_TEMPLATE = DESIGN_ROOT / "PILOT_A_HUMAN_AUTH_TEMPLATE.json"
M13_FREEZE = DESIGN_ROOT / "m13_freeze.json"
M13_VERIFY = DESIGN_ROOT / "m13_verify.json"
FINAL = ROOT / "pilot_final_membership.json"
EVAL_SETS = ROOT / "evaluator_only/pilot_a_evaluator_sets_v1.json"
ENG_SETS = PROJECT / "research/wp2/harness_v3_2026-09-26/evaluator_only/eng_evaluator_sets_v3.json"
AUTH = ROOT / "human_authorization.json"
FREEZE = ROOT / "pilot_a_freeze.json"
SCOPES = ROOT / "frozen_scopes.json"
GEN_PLAN = ROOT / "generation_plan.json"
GEN_FREEZE = ROOT / "generation_freeze.json"
EVAL_PLAN = ROOT / "evaluations/plan.json"
SUMMARY = ROOT / "pilot_a_summary.json"
REPORT = PROJECT / "docs/WP2_PILOT_A_V1_RESULT.md"
LEDGER = ROOT / "ledger/pilot_a_spend.jsonl"
STOP_FLAG = PROJECT / "logs/PILOT_A_STOP.flag"

MODEL, PROVIDER, MAX_USD, WORST_EPISODE_USD = "qwen/qwen3-coder", "deepinfra/turbo", 1.0, 0.08
APPROVAL_TOKEN = "I_AUTHORIZE_WP2_PILOT_A_V1=YES"
CANARY_TASK = "saleor-rc-2d45b76a52f2"      # proven DEV_TRAIN_ENG task; never a Pilot task
ARMS = ("GOLD_HARD", "PLACEBO_HARD")
REPLICATES = ("r1", "r2")
TERMINAL = {"NO_SCOPE", "INVALID_AFTER_REPAIR", "APPLIED"}
FORBIDDEN = {"GENERATION_FAIL"}
EXIT_HOLD, EXIT_STOP, EXIT_AUTH, EXIT_PREFLIGHT = 3, 4, 32, 33
EXIT_OUTAGE, EXIT_REJECTED, EXIT_BUDGET, EXIT_INVARIANT, EXIT_EVAL_INFRA = 75, 76, 77, 78, 79
BORROWED = ["src/benchmark/wp2/e2e_v22/transport.py", "src/benchmark/wp2/e2e_v22/circuit.py",
            "src/benchmark/wp2/e2e_v21/generate.py", "src/benchmark/wp2/e2e/generate.py",
            "src/benchmark/wp2/e2e/generate_v2.py", "src/benchmark/wp2/e2e/scopes.py",
            "src/benchmark/wp2/e2e/spec.py", "src/benchmark/wp2/e2e/prompt.py",
            "src/benchmark/wp2/e2e/response_cache.py", "src/benchmark/wp2/e2e/task_inputs.py",
            "src/benchmark/wp2/e2e/evaluate.py", "src/benchmark/wp2/e2e/evaluator_sets.py",
            "src/benchmark/wp2/e2e/patch_format.py", "src/benchmark/wp2/e2e/pycompile.py",
            "src/benchmark/wp2/harness_v3.py", "scripts/wp2_m13.py"]
KIT = ["scripts/wp2_ctl_v224.py", "scripts/wp2_m14a_readiness.py", "scripts/wp2_m14a_run.py",
       "scripts/wp2_m14a_evalcore.py", "scripts/wp2_m14a_authorize.py",
       "controller/plan_m14a_pilot_a_v1.json", "controller/light_profile_m14a.json",
       "controller/KIT_MANIFEST_M14A.json"]


class Stop(Exception):
    def __init__(self, msg: str, code: int = EXIT_INVARIANT) -> None:
        super().__init__(msg)
        self.code = code


# ------------------------------------------------------------------ helpers
def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def norm_sha(p: Path) -> str:
    d = p.read_bytes()
    if b"\x00" not in d[:8192]:
        d = d.replace(b"\r\n", b"\n")
    return hashlib.sha256(d).hexdigest()


def sha_obj(x: Any) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def write(p: Path, d: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                 encoding="utf-8", newline="\n")


def self_hash(d: dict, key: str = "artifact_sha256") -> dict:
    q = copy.deepcopy(d)
    q[key] = ""
    d[key] = sha_obj(q)
    return d


def hash_ok(d: dict, key: str = "artifact_sha256") -> bool:
    q = copy.deepcopy(d)
    got = q.get(key, "")
    q[key] = ""
    return bool(got) and sha_obj(q) == got


def require(c: bool, m: str, code: int = EXIT_INVARIANT) -> None:
    if not c:
        raise Stop(m, code)


def rel(p: Path) -> str:
    return p.relative_to(PROJECT).as_posix()


def git(*a: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *a], cwd=PROJECT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


# ------------------------------------------------------------------ authorization
def validate_auth() -> dict:
    require(AUTH.exists(), "human_authorization.json missing", EXIT_AUTH)
    a, d, m = load(AUTH), load(DESIGN), load(FINAL)
    require(hash_ok(a), "authorization self-hash mismatch", EXIT_AUTH)
    require(a.get("authorized") is True, "authorized != true", EXIT_AUTH)
    require(a.get("approval_token") == APPROVAL_TOKEN, "approval token mismatch", EXIT_AUTH)
    require(a.get("design_artifact_sha256") == d["artifact_sha256"], "design hash mismatch",
            EXIT_AUTH)
    require(a.get("membership_artifact_sha256") == m["artifact_sha256"],
            "membership hash mismatch", EXIT_AUTH)
    require(a.get("m13_auth_template_sha256") == load(AUTH_TEMPLATE)["artifact_sha256"],
            "not bound to the frozen M13B authorization template", EXIT_AUTH)
    require(a.get("model") == MODEL and a.get("provider") == PROVIDER
            and a.get("allow_fallbacks") is False, "route mismatch", EXIT_AUTH)
    cap = a.get("max_generation_spend_usd")
    require(isinstance(cap, (int, float)) and 0 < float(cap) <= MAX_USD,
            "max spend must be > 0 and <= 1.00", EXIT_AUTH)
    require(m.get("verdict") == "FULL" or str(m.get("verdict", "")).startswith("REDUCED_"),
            "membership not runnable", EXIT_AUTH)
    r = rel(AUTH)
    require(git("ls-files", "--error-unmatch", r).returncode == 0, "authorization not tracked",
            EXIT_AUTH)
    require(not git("status", "--porcelain", "--", r).stdout.strip(),
            "authorization has uncommitted changes", EXIT_AUTH)
    return a


def auth_check() -> int:
    a = validate_auth()
    write(ROOT / "auth_check.json", self_hash({
        "artifact": "pilot_a_auth_check", "artifact_sha256": "",
        "auth_artifact_sha256": a["artifact_sha256"], "authorized_by": a.get("authorized_by"),
        "max_generation_spend_usd": a["max_generation_spend_usd"]}))
    print("AUTH_CHECK_PASS " + json.dumps({"by": a.get("authorized_by"),
                                           "max_usd": a["max_generation_spend_usd"]}))
    return 0


# ------------------------------------------------------------------ doctor / canary
def doctor(mode: str) -> int:
    checks: dict[str, dict] = {}
    free = shutil.disk_usage(PROJECT).free / 2 ** 30
    checks["disk_free_gib"] = {"ok": free >= 20, "value": round(free, 1)}
    try:
        from benchmark.wp2.harness_v3 import clock_preflight, ensure_postgres_running
        ensure_postgres_running()
        clk = clock_preflight()
        checks["postgres_clock"] = {"ok": clk.get("verdict") != "CLOCK_BLOCKED",
                                    "value": clk.get("verdict")}
    except Exception as exc:
        checks["postgres_clock"] = {"ok": False, "value": str(exc)[:300]}
    try:
        from benchmark.wp2.e2e_v22.common import env_identity
        env = env_identity()
        checks["images"] = {"ok": not env.get("errors"), "value": env}
    except Exception as exc:
        checks["images"] = {"ok": False, "value": str(exc)[:300]}
    checks["evaluator_sets"] = {"ok": EVAL_SETS.exists()}
    if mode == "paid":
        checks["api_key"] = {"ok": bool(os.environ.get("OPENROUTER_API_KEY", "").strip())}
        out = ROOT / "doctor/key_usage.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            r = subprocess.run([sys.executable, "scripts/wp1b_openrouter_key_usage.py", "--out",
                                str(out)], cwd=PROJECT, capture_output=True, text=True,
                               timeout=180)
            u = load(out) if out.exists() else {}
            credit = u.get("remaining_usd_min_of_sources") or u.get("limit_remaining_usd")
            checks["credit_ge_5"] = {"ok": r.returncode == 0 and credit is not None
                                     and float(credit) >= 5, "value": credit}
        except Exception as exc:
            checks["credit_ge_5"] = {"ok": False, "value": str(exc)[:200]}
        try:
            from scripts.wp2_e2e_v22_doctor import live_pricing   # read-only endpoint metadata
            checks["pricing"] = live_pricing()
        except Exception as exc:
            checks["pricing"] = {"ok": False, "value": str(exc)[:200]}
    ok = all(v.get("ok") for v in checks.values())
    write(ROOT / f"doctor/doctor_{mode}.json", self_hash({
        "artifact": "pilot_a_doctor", "artifact_sha256": "", "mode": mode, "checks": checks,
        "pass": ok, "model_api_calls": 0, "utc": now()}))
    for k, v in checks.items():
        print(f"DOCTOR {'PASS' if v.get('ok') else 'FAIL'} {k} {str(v.get('value', ''))[:160]}")
    return 0 if ok else EXIT_PREFLIGHT


def canary() -> int:
    from scripts.wp2_m14a_evalcore import gold_empty_canary, point_evaluator
    ev = point_evaluator(ENG_SETS, ROOT)          # JUnit -> research/wp2/pilot_a_v1/junit/
    res = gold_empty_canary(ev, CANARY_TASK, "pa")
    write(ROOT / "canary.json", self_hash({
        "artifact": "pilot_a_canary", "artifact_sha256": "", "task_id": CANARY_TASK, **res,
        "protected_pilot_outcomes_consumed": False, "model_api_calls": 0}))
    print("PILOT_A_CANARY " + json.dumps({"pass": res["ok"]}))
    return 0 if res["ok"] else EXIT_PREFLIGHT


# ------------------------------------------------------------------ freeze
def generation_items(tasks: list[str] | None = None) -> list[dict]:
    tasks = load(FINAL)["A"] if tasks is None else tasks
    return [{"task_id": t, "arm": arm, "replicate": rep, "label": f"{arm}__{rep}"}
            for t in tasks for rep in REPLICATES for arm in ARMS]


def cache_dir(item: dict) -> Path:
    """Cache namespace = (task_id, arm, replicate): no reuse across tasks/arms/replicates;
    an interrupted episode reuses only its own already-paid request on resume."""
    return ROOT / "cache_namespaces" / item["task_id"] / item["label"]


def ep_path(item: dict) -> Path:
    return ROOT / "episodes" / item["task_id"] / item["label"] / "episode.json"


def ep_status(item: dict) -> str | None:
    p = ep_path(item)
    if not p.exists():
        return None
    try:
        return load(p).get("status")
    except (ValueError, OSError):
        return "UNREADABLE"


def build_freeze() -> dict:
    from benchmark.wp2.e2e.scopes import build_arm_scopes
    a = validate_auth()
    m = load(FINAL)
    scopes = {t: {arm: build_arm_scopes(t, arm) for arm in ARMS} for t in m["A"]}
    write(SCOPES, {"artifact": "pilot_a_frozen_scopes", "tasks": scopes, "sha256": sha_obj(scopes)})
    items = generation_items()
    write(GEN_PLAN, {"artifact": "pilot_a_generation_plan", "items": items,
                     "sha256": sha_obj(items)})
    arts = [DESIGN, SELECTION, M13_FREEZE, M13_VERIFY, FINAL, EVAL_SETS, AUTH,
            ROOT / "m14a_guard.json", ROOT / "doctor/doctor_offline.json",
            ROOT / "doctor/doctor_paid.json", ROOT / "canary.json", SCOPES, GEN_PLAN]
    intents = {}
    for t in m["A"]:
        p = PROJECT / f"benchmark_data/real_commit_impact_saleor/scientific/{t}/public/intent.json"
        require(p.exists(), f"public intent missing {t}")
        intents[rel(p)] = norm_sha(p)
    return self_hash({
        "artifact": "pilot_a_freeze", "artifact_sha256": "",
        "design_artifact_sha256": load(DESIGN)["artifact_sha256"],
        "membership_artifact_sha256": m["artifact_sha256"],
        "human_auth_artifact_sha256": a["artifact_sha256"],
        "max_generation_spend_usd": float(a["max_generation_spend_usd"]),
        "model": MODEL, "provider": PROVIDER, "allow_fallbacks": False, "temperature": 0.0,
        "max_tokens": 8192, "max_repairs": 1, "planned_episodes": len(items),
        "generation_plan_sha256": sha_obj(items), "frozen_scopes_sha256": sha_obj(scopes),
        "artifact_hashes": {rel(p): norm_sha(p) for p in arts},
        "source_hashes": {r: norm_sha(PROJECT / r) for r in BORROWED + KIT},
        "public_intent_hashes": intents})


def verify_freeze() -> list[str]:
    if not (FREEZE.exists() and GEN_PLAN.exists() and SCOPES.exists()):
        return ["freeze artifacts missing"]
    fr = load(FREEZE)
    bad = [] if hash_ok(fr) else ["freeze self-hash"]
    for key in ("artifact_hashes", "source_hashes", "public_intent_hashes"):
        for r, h in fr.get(key, {}).items():
            p = PROJECT / r
            if not p.exists() or norm_sha(p) != h:
                bad.append(f"drift {r}")
    gp, sc = load(GEN_PLAN), load(SCOPES)
    if sha_obj(gp["items"]) != fr["generation_plan_sha256"] or \
            sha_obj(sc["tasks"]) != fr["frozen_scopes_sha256"] or \
            len(gp["items"]) != fr["planned_episodes"]:
        bad.append("plan/scope drift")
    return bad


def freeze() -> int:
    write(FREEZE, build_freeze())
    bad = verify_freeze()
    require(not bad, f"freeze verify failed {bad[:5]}")
    fr = load(FREEZE)
    print("PILOT_A_FREEZE_PASS " + json.dumps({"sha": fr["artifact_sha256"][:16],
                                               "episodes": fr["planned_episodes"]}))
    return 0


def freeze_verify() -> int:
    bad = verify_freeze()
    print("PILOT_A_FREEZE_VERIFY_PASS" if not bad else "PILOT_A_FREEZE_VERIFY_FAIL " + str(bad[:5]))
    return 0 if not bad else 1


# ------------------------------------------------------------------ generation
class Ledger:
    """Durable spend ledger (fsync per record). Fresh provider calls only."""

    def __init__(self, path: Path, ceiling: float) -> None:
        self.path, self.ceiling, self.t = path, ceiling, 0.0
        if path.exists():
            for x in path.read_text(encoding="utf-8").splitlines():
                if x.strip():
                    self.t += float(json.loads(x).get("cost_usd", 0) or 0)

    def total(self) -> float:
        return self.t

    def can_spend(self, worst: float) -> bool:
        return self.t + worst <= self.ceiling + 1e-12

    def record(self, r: dict) -> None:
        r = dict(r, stage="PILOT_A")
        self.t += float(r.get("cost_usd", 0) or 0)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(r, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())


def drive(items: list[dict], client: Any, ledger: Any, breaker: Any,
          episode_fn: Callable[..., dict], cache_factory: Callable[[dict], Any],
          expected_editable: Callable[[dict], list[str]],
          current_editable: Callable[[dict], list[str]], max_new: int, max_seconds: float,
          clock: Callable[[], float] = time.monotonic,
          sleep: Callable[[float], None] = time.sleep,
          stop_flag: Path = STOP_FLAG) -> tuple[int, dict]:
    """v2.2 driver semantics for Pilot-A; provider failures never become outcomes."""
    from benchmark.wp2.e2e_v22.transport import HoldActiveV22, ProviderUnavailable, RequestRejected
    info: dict[str, Any] = {"new_terminal": 0, "planned": len(items)}
    for i in items:
        st = ep_status(i)
        if st in FORBIDDEN or st == "UNREADABLE":
            info["invariant"] = f"forbidden/unreadable episode {i['task_id']}/{i['label']}"
            return EXIT_INVARIANT, info
    breaker.on_start()
    t0 = clock()
    for i in items:
        if ep_status(i) in TERMINAL:
            continue
        if info["new_terminal"] >= max_new or clock() - t0 >= max_seconds:
            break
        if current_editable(i) != expected_editable(i):
            info["invariant"] = f"frozen scope drift {i['task_id']}/{i['arm']}"
            return EXIT_INVARIANT, info
        while True:
            if stop_flag.exists():
                return EXIT_STOP, info
            if not ledger.can_spend(WORST_EPISODE_USD):
                info["budget_total"] = ledger.total()
                return EXIT_BUDGET, info
            client.set_context(task_id=i["task_id"], arm=i["arm"], label=i["label"],
                               replicate=i["replicate"], mode="pilot_a")
            try:
                rec = episode_fn(i["task_id"], i["arm"], client, ledger, cache_factory(i), ROOT,
                                 subdir="episodes", label=i["label"])
            except HoldActiveV22 as exc:
                info["hold"] = str(exc)
                return EXIT_HOLD, info
            except ProviderUnavailable as exc:
                d = breaker.on_unavailable(str(exc))
                if d.action == "STOP":
                    write(ROOT / "transport/pending.json", {"item": i, "reason": d.reason,
                                                            "utc": now()})
                    info["outage"] = d.reason
                    return EXIT_OUTAGE, info
                waited = 0.0
                while waited < d.seconds:
                    if stop_flag.exists():
                        return EXIT_STOP, info
                    client.check_hold()
                    step = min(15.0, d.seconds - waited)
                    sleep(step)
                    waited += step
                continue
            except RequestRejected as exc:
                write(ROOT / "transport/rejected.json", {"item": i, "error": str(exc),
                                                         "attempts": exc.attempts, "utc": now()})
                return EXIT_REJECTED, info
            except Exception as exc:
                write(ROOT / "transport/instrument_error.json", {
                    "item": i, "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc()[-7000:], "utc": now()})
                info["instrument_error"] = str(exc)[:500]
                return EXIT_INVARIANT, info
            if rec.get("status") not in TERMINAL or \
                    rec.get("editable_set", []) != expected_editable(i):
                info["invariant"] = f"non-terminal or scope mismatch {i['task_id']}/{i['label']}"
                return EXIT_INVARIANT, info
            breaker.on_success()
            info["new_terminal"] += 1
            break
    info["terminal"] = sum(ep_status(i) in TERMINAL for i in items)
    return 0, info


def generate(max_new: int, max_seconds: float) -> int:
    bad = verify_freeze()
    require(not bad, f"freeze drift before generation {bad[:3]}")
    from benchmark.wp2.e2e.response_cache import ResponseCache
    from benchmark.wp2.e2e.scopes import build_arm_scopes
    from benchmark.wp2.e2e_v21.generate import run_episode_v21
    from benchmark.wp2.e2e_v22.circuit import CircuitBreaker
    from benchmark.wp2.e2e_v22.transport import AttemptLog, V22HttpClient
    a = validate_auth()
    ledger = Ledger(LEDGER, min(float(a["max_generation_spend_usd"]), MAX_USD))
    client = V22HttpClient([ROOT / "HOLD"], AttemptLog(ROOT / "transport/attempts.jsonl"))
    breaker = CircuitBreaker(ROOT / "transport/circuit.json")
    scopes = load(SCOPES)["tasks"]
    code, info = drive(load(GEN_PLAN)["items"], client, ledger, breaker, run_episode_v21,
                       lambda i: ResponseCache(cache_dir(i)),
                       lambda i: scopes[i["task_id"]][i["arm"]]["editable"],
                       lambda i: build_arm_scopes(i["task_id"], i["arm"])["editable"],
                       max_new, max_seconds)
    info.update({"exit": code, "spend_total_usd": round(ledger.total(), 7),
                 "network_attempts": client.network_attempts})
    print("PILOT_A_DRIVER_RESULT " + json.dumps(info, sort_keys=True, default=str))
    return code


def generation_complete() -> int:
    if not GEN_PLAN.exists():
        return 1
    items = load(GEN_PLAN)["items"]
    n = sum(ep_status(i) in TERMINAL for i in items)
    print(f"GENERATION_{'COMPLETE' if n == len(items) else 'INCOMPLETE'} {n}/{len(items)}")
    return 0 if n == len(items) else 1


def generation_freeze() -> int:
    require(generation_complete() == 0, "generation incomplete")
    require(not verify_freeze(), "freeze drift")
    files = {p.relative_to(ROOT).as_posix(): norm_sha(p)
             for p in sorted((ROOT / "episodes").rglob("*")) if p.is_file()}
    for r in ("ledger/pilot_a_spend.jsonl", "transport/attempts.jsonl"):
        if (ROOT / r).exists():
            files[r] = norm_sha(ROOT / r)
    for i in load(GEN_PLAN)["items"]:
        e = load(ep_path(i))
        require(e.get("status") in TERMINAL, "non-terminal episode")
        for c in e.get("calls", []):
            require(c.get("route") != "replay", "replay route in paid evidence")
    gf = self_hash({"artifact": "pilot_a_generation_freeze", "artifact_sha256": "",
                    "pilot_a_freeze_sha256": load(FREEZE)["artifact_sha256"],
                    "generation_plan_sha256": sha_obj(load(GEN_PLAN)["items"]),
                    "n_episodes": len(load(GEN_PLAN)["items"]), "files": files,
                    "spend_usd": round(Ledger(LEDGER, MAX_USD).total(), 7)})
    if GEN_FREEZE.exists():
        require(load(GEN_FREEZE)["artifact_sha256"] == gf["artifact_sha256"],
                "generation freeze exists and differs")
    write(GEN_FREEZE, gf)
    print("GENERATION_FROZEN " + json.dumps({"n": gf["n_episodes"], "spend_usd": gf["spend_usd"]}))
    return 0


def verify_generation_freeze() -> list[str]:
    if not GEN_FREEZE.exists():
        return ["generation freeze missing"]
    bad = verify_freeze()
    gf = load(GEN_FREEZE)
    if not hash_ok(gf):
        bad.append("generation freeze self-hash")
    for r, h in gf.get("files", {}).items():
        p = ROOT / r
        if not p.exists() or norm_sha(p) != h:
            bad.append(f"generation evidence drift {r}")
    return bad


def generation_freeze_verify() -> int:
    bad = verify_generation_freeze()
    print("GENERATION_FREEZE_VERIFY_PASS" if not bad else "GENERATION_FREEZE_VERIFY_FAIL "
          + str(bad[:5]))
    return 0 if not bad else 1


# ------------------------------------------------------------------ evaluation
def unique_path(task_id: str, diff_sha: str) -> Path:
    require(len(diff_sha) == 64, f"full diff sha required: {diff_sha!r}")
    return ROOT / "evaluations/unique" / task_id / diff_sha / "evaluation.json"


def bc_path(task_id: str, label: str) -> Path:
    return ROOT / "evaluations/episodes" / task_id / label / "evaluation.json"


def record_state(p: Path) -> str:
    """ABSENT | VALID | CORRUPT (a corrupt committed record is never silently replaced)."""
    if not p.exists():
        return "ABSENT"
    try:
        return "VALID" if hash_ok(load(p), "evaluation_sha256") else "CORRUPT"
    except (ValueError, OSError):
        return "CORRUPT"


def build_eval_plan() -> list[dict]:
    uniq: dict[tuple[str, str], dict] = {}
    for i in load(GEN_PLAN)["items"]:
        e = load(ep_path(i))
        if e.get("status") != "APPLIED" or not e.get("diff_sha256"):
            continue
        k = (i["task_id"], e["diff_sha256"])
        src = ep_path(i).relative_to(ROOT).as_posix()
        if k not in uniq:
            uniq[k] = {**i, "diff_sha256": e["diff_sha256"], "source": src,
                       "also_sources": [], "also_labels": []}
        else:
            uniq[k]["also_sources"].append(src)
            uniq[k]["also_labels"].append(i["label"])
    return sorted(uniq.values(), key=lambda x: (x["task_id"], x["diff_sha256"], x["label"]))


def eval_plan() -> int:
    bad = verify_generation_freeze()
    require(not bad, f"generation freeze drift {bad[:3]}")
    items = build_eval_plan()
    p = {"artifact": "pilot_a_evaluation_plan", "rule": "unique (task_id, full diff_sha256)",
         "items": items, "n_unique_identities": len(items), "plan_sha256": sha_obj(items)}
    if EVAL_PLAN.exists():
        require(load(EVAL_PLAN)["items"] == items, "existing evaluation plan differs")
    else:
        write(EVAL_PLAN, p)
    print("EVAL_PLAN " + json.dumps({"n_unique_identities": len(items)}))
    return 0


def by_construction() -> int:
    sets = load(EVAL_SETS)["tasks"]
    n = 0
    for i in load(GEN_PLAN)["items"]:
        e = load(ep_path(i))
        if e["status"] == "APPLIED":
            continue
        p = bc_path(i["task_id"], i["label"])
        stt = record_state(p)
        require(stt != "CORRUPT", f"corrupt by-construction record {p}")
        if stt == "VALID":
            continue
        t = sets[i["task_id"]]
        r = {"task_id": i["task_id"], "arm": i["arm"], "replicate": i["replicate"],
             "label": i["label"], "status": "BY_CONSTRUCTION", "source_status": e["status"],
             "diff_sha256": e.get("diff_sha256", ""),
             "f2p_task": "FAIL" if t["behavioral_f2p_node_ids"] else "UNDEFINED",
             "p2p_s_task": "PASS_BY_CONSTRUCTION" if t["p2p_s_defined"] else "UNDEFINED",
             "p2p_u200_task": "PASS_BY_CONSTRUCTION" if t["p2p_u_cap200_defined"] else "UNDEFINED",
             "resolved": False, "groups": {}, "evaluation_sha256": ""}
        write(p, self_hash(r, "evaluation_sha256"))
        n += 1
    return n


def evaluate(max_evals: int, evaluate_fn: Callable[..., dict] | None = None) -> int:
    bad = verify_generation_freeze()
    require(not bad, f"generation freeze drift {bad[:3]}")
    require(EVAL_PLAN.exists(), "evaluation plan missing")
    from scripts.wp2_m14a_evalcore import EvalInfraError, evaluate_state_safe, point_evaluator
    ev = point_evaluator(EVAL_SETS, ROOT)
    evaluate_fn = evaluate_fn or (lambda t, lab, wt: evaluate_state_safe(ev, t, lab, wt))
    done = 0
    for i in load(EVAL_PLAN)["items"]:
        if done >= max_evals:
            break
        p = unique_path(i["task_id"], i["diff_sha256"])
        stt = record_state(p)
        require(stt != "CORRUPT", f"corrupt evaluation record {p}")
        if stt == "VALID":
            continue
        txt = (ROOT / i["source"]).parent.joinpath("final_diff.patch").read_text(encoding="utf-8")
        lab = "u_" + i["diff_sha256"][:12]
        try:
            wt, tree = ev.materialize(i["task_id"], lab, txt)
            er = evaluate_fn(i["task_id"], lab, wt)
        except (EvalInfraError, RuntimeError, subprocess.TimeoutExpired) as exc:
            raise Stop(f"evaluation infrastructure error: {exc}", EXIT_EVAL_INFRA) from exc
        sc = ev.score(i["task_id"], lab, er["groups"])
        r = {"task_id": i["task_id"], "diff_sha256": i["diff_sha256"],
             "eval_identity": f"{i['task_id']}/{i['diff_sha256']}", "label": lab,
             "tree_sha": tree, "status": "DONE", "groups": er["groups"],
             **{k: sc[k] for k in ("f2p_task", "p2p_s_task", "p2p_u200_task", "resolved",
                                   "flaky_under_patch")},
             "sources": [i["source"]] + i["also_sources"],
             "labels": [i["label"]] + i["also_labels"], "evaluation_sha256": ""}
        write(p, self_hash(r, "evaluation_sha256"))
        done += 1
        print(f"[pilot-a-eval] {i['task_id']} {i['diff_sha256'][:12]} -> f2p={r['f2p_task']} "
              f"p2ps={r['p2p_s_task']} p2pu={r['p2p_u200_task']} resolved={r['resolved']}",
              flush=True)
    print(f"EVAL_CHUNK evaluated={done} by_construction_written={by_construction()}")
    return 0


def eval_complete() -> int:
    if not EVAL_PLAN.exists():
        return 1
    miss, corrupt = [], []
    targets = [unique_path(i["task_id"], i["diff_sha256"]) for i in load(EVAL_PLAN)["items"]]
    for i in load(GEN_PLAN)["items"]:
        if load(ep_path(i))["status"] != "APPLIED":
            targets.append(bc_path(i["task_id"], i["label"]))
    for p in targets:
        s = record_state(p)
        (corrupt if s == "CORRUPT" else miss if s == "ABSENT" else []).append(
            p.relative_to(ROOT).as_posix())
    for p in targets:
        if record_state(p) == "VALID":
            r = load(p)
            if r["task_id"] != p.parent.parent.name:
                corrupt.append(p.relative_to(ROOT).as_posix())
    if corrupt:
        print("EVAL_CORRUPT " + json.dumps(corrupt[:20]))
        return 1
    if miss:
        print("EVAL_INCOMPLETE " + json.dumps(miss[-20:]))
        return 1
    print(f"EVAL_COMPLETE n_unique={load(EVAL_PLAN)['n_unique_identities']}")
    return 0


# ------------------------------------------------------------------ summary
def evaluation_for(i: dict, e: dict) -> dict | None:
    p = unique_path(i["task_id"], e["diff_sha256"]) if e["status"] == "APPLIED" \
        else bc_path(i["task_id"], i["label"])
    return load(p) if record_state(p) == "VALID" else None


def compute_summary() -> dict:
    from scripts.wp2_m13 import gates_for      # M13B frozen thresholds
    items = load(GEN_PLAN)["items"]
    tasks = load(FINAL)["A"]
    ledger = [json.loads(x) for x in LEDGER.read_text(encoding="utf-8").splitlines()
              if x.strip()] if LEDGER.exists() else []
    per: dict[str, dict] = {}
    tup: dict[tuple[str, str, str], tuple] = {}
    arch = orphan = 0
    passish = ("PASS", "PASS_BY_CONSTRUCTION")
    for arm in ARMS:
        cnt: Counter = Counter()
        errs: Counter = Counter()
        logical = cache = repairs = 0
        evs = []
        for i in [x for x in items if x["arm"] == arm]:
            e = load(ep_path(i))
            cnt[e["status"]] += 1
            repairs += int(bool(e.get("repair_used")))
            for c in e.get("calls", []):
                n = int(c.get("prompt_tokens", 0) or 0) + int(c.get("completion_tokens", 0) or 0)
                logical += n
                cache += n if "reused" in str(c.get("kind", "")) else 0
            for ph in ("initial", "repair"):
                for er in e.get("validation", {}).get(ph, []) or []:
                    errs[str(er).split(":", 1)[0].split(" ", 1)[0]] += 1
            if e["status"] == "APPLIED" and not set(e.get("edited_files", [])) <= set(
                    e.get("editable_set", [])):
                arch += 1
            v = evaluation_for(i, e)
            if v is None:
                orphan += 1
            evs.append(v)
            tup[(i["task_id"], arm, i["replicate"])] = (
                e["status"], (v or {}).get("f2p_task"), (v or {}).get("p2p_s_task"),
                (v or {}).get("p2p_u200_task"), bool((v or {}).get("resolved")))
        rows = [r for r in ledger if r.get("arm") == arm]
        pt = sum(int(r.get("prompt_tokens", 0) or 0) for r in rows)
        ct = sum(int(r.get("completion_tokens", 0) or 0) for r in rows)
        per[arm] = {"planned": sum(cnt.values()), "status": dict(cnt), "applied": cnt["APPLIED"],
                    "resolved": sum(bool(v and v.get("resolved")) for v in evs),
                    "f2p": sum(bool(v and v.get("f2p_task") == "PASS") for v in evs),
                    "p2p_s": sum(bool(v and v.get("p2p_s_task") in passish) for v in evs),
                    "p2p_u200": sum(bool(v and v.get("p2p_u200_task") in passish) for v in evs),
                    "repair_used": repairs, "validation_error_counts": dict(errs),
                    "provider_reported_prompt_tokens": pt,
                    "provider_reported_completion_tokens": ct,
                    "provider_reported_tokens": pt + ct,
                    "provider_reported_cost_usd": round(sum(float(r.get("cost_usd", 0) or 0)
                                                            for r in rows), 7),
                    "logical_tokens": logical, "cache_reuse_tokens": cache}
    rep = {}
    for arm in ARMS:
        agree = sum(tup[(t, arm, "r1")] == tup[(t, arm, "r2")] for t in tasks)
        rep[arm] = {"n_tasks": len(tasks), "endpoint_tuple_agreement": agree / len(tasks),
                    "resolved_rate_r1": sum(tup[(t, arm, "r1")][4] for t in tasks) / len(tasks),
                    "resolved_rate_r2": sum(tup[(t, arm, "r2")][4] for t in tasks) / len(tasks)}
    g = gates_for(len(tasks))
    gd = sum(sum(tup[(t, "GOLD_HARD", r)][4] for r in REPLICATES)
             > sum(tup[(t, "PLACEBO_HARD", r)][4] for r in REPLICATES) for t in tasks)
    pd = sum(sum(tup[(t, "PLACEBO_HARD", r)][4] for r in REPLICATES)
             > sum(tup[(t, "GOLD_HARD", r)][4] for r in REPLICATES) for t in tasks)
    gold, plac = per["GOLD_HARD"], per["PLACEBO_HARD"]
    gates = {"A0_instrument": not verify_generation_freeze() and arch == 0 and orphan == 0,
             "A1_completion": all(ep_status(i) in TERMINAL for i in items) and eval_complete() == 0,
             "A2_gold_applied": gold["applied"] >= g["A2_gold_applied_min"],
             "A3_gold_resolved": gold["resolved"] >= g["A3_gold_resolved_min"],
             "A4_placebo_ceiling": plac["resolved"] <= g["A4_placebo_resolved_max"],
             "A5_separation": gold["resolved"] - plac["resolved"] >= g["A5_gold_minus_placebo_min"]
             and gd >= pd}
    if not (gates["A0_instrument"] and gates["A1_completion"]):
        token = "PILOT_A_INSTRUMENT_FIX"
    elif not gates["A4_placebo_ceiling"]:
        token = "PILOT_A_PLACEBO_LEAK_REVIEW"
    elif not (gates["A2_gold_applied"] and gates["A3_gold_resolved"] and gates["A5_separation"]):
        token = "PILOT_A_GENERATOR_FLOOR_HOLD"
    else:
        token = "PILOT_A_PASS"
    total_cost = round(sum(float(r.get("cost_usd", 0) or 0) for r in ledger), 7)
    return {"artifact": "pilot_a_summary", "token": token,
            "next": "M15_KIT_BUILD_BY_BRAIN" if token == "PILOT_A_PASS" else "HUMAN_DECISION",
            "auto_execution_of_M14R_or_M15": False, "n_tasks": len(tasks), "gates": gates,
            "thresholds": g, "per_arm": per, "replicate": rep,
            "task_direction": {"gold_gt_placebo": gd, "placebo_gt_gold": pd,
                               "ties": len(tasks) - gd - pd},
            "architecture_scope_violations": arch, "applied_without_evaluation": orphan,
            "provider_reported_total_cost_usd": total_cost,
            "provider_reported_total_tokens": sum(int(r.get("prompt_tokens", 0) or 0)
                                                  + int(r.get("completion_tokens", 0) or 0)
                                                  for r in ledger),
            "mandatory_wording": "Pilot-A is protected development-holdout assay/generator "
                                 "calibration (GOLD vs PLACEBO). It is not an RM-CSS-vs-Agent "
                                 "comparison and supports no selector ranking or claim."}


def summary() -> int:
    require(generation_complete() == 0, "generation incomplete")
    s = compute_summary()
    write(SUMMARY, self_hash(dict(s, artifact_sha256="")))
    lines = ["# WP2 Pilot-A V1 result", "", f"Token: **{s['token']}**. Next: **{s['next']}**.", "",
             f"Tasks: {s['n_tasks']}. Provider-reported spend: "
             f"${s['provider_reported_total_cost_usd']:.6f}.", "",
             "| Arm | APPLIED | RESOLVED | F2P | P2P-S | P2P-U200 | provider tokens | USD |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for arm in ARMS:
        a = s["per_arm"][arm]
        lines.append(f"| {arm} | {a['applied']} | {a['resolved']} | {a['f2p']} | {a['p2p_s']} | "
                     f"{a['p2p_u200']} | {a['provider_reported_tokens']} | "
                     f"{a['provider_reported_cost_usd']:.6f} |")
    lines += ["", "Gates: " + json.dumps(s["gates"], sort_keys=True), "", s["mandatory_wording"], ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("PILOT_A_SUMMARY " + json.dumps({"token": s["token"], "gates": s["gates"]}, sort_keys=True))
    return 0


# ------------------------------------------------------------------ CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for x in ("auth-check", "doctor-offline", "doctor-paid", "canary", "freeze", "freeze-verify",
              "generation-complete", "generation-freeze", "generation-freeze-verify", "eval-plan",
              "eval-complete", "summary"):
        sp.add_parser(x)
    q = sp.add_parser("generate")
    q.add_argument("--max-new", type=int, default=8)
    q.add_argument("--max-seconds", type=float, default=5400)
    q = sp.add_parser("evaluate")
    q.add_argument("--max-evals", type=int, default=4)
    a = ap.parse_args(argv)
    fns: dict[str, Callable[[], int]] = {
        "auth-check": auth_check, "doctor-offline": lambda: doctor("offline"),
        "doctor-paid": lambda: doctor("paid"), "canary": canary, "freeze": freeze,
        "freeze-verify": freeze_verify, "generation-complete": generation_complete,
        "generation-freeze": generation_freeze,
        "generation-freeze-verify": generation_freeze_verify, "eval-plan": eval_plan,
        "eval-complete": eval_complete, "summary": summary,
        "generate": lambda: generate(a.max_new, a.max_seconds),
        "evaluate": lambda: evaluate(a.max_evals)}
    try:
        return fns[a.cmd]()
    except Stop as exc:
        print(f"M14A_STOP {a.cmd} code={exc.code}: {exc}")
        return exc.code
    except Exception as exc:
        if type(exc).__name__ == "EvalInfraError":
            print(f"M14A_EVAL_INFRA {a.cmd}: {exc}")
            return EXIT_EVAL_INFRA
        print(f"M14A_STEP_ERROR {a.cmd} {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return EXIT_INVARIANT


if __name__ == "__main__":
    raise SystemExit(main())
