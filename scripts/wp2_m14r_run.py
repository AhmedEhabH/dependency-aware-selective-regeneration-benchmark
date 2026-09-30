#!/usr/bin/env python3
"""WP2 M14R engine: generator/interface probe on DEV_TRAIN_ENG only (brain-authored).

Frozen design: research/wp2/m14r_v1/m14r_design_freeze_v1.json (sha pinned below).
Only `generate` and `static` may call the model API; `doctor-paid` reads provider
metadata only. Every other subcommand makes zero model/API calls. No Pilot-A or Pilot-B
(protected) task is ever generated or evaluated here.

Subcommands (one atomic step each):
  guard | pilot-a-taxonomy | readiness | readiness-check | membership | auth-check |
  doctor-offline | doctor-paid | freeze | freeze-verify | generate | generation-complete |
  static | static-complete | generation-freeze | generation-freeze-verify | eval-plan |
  evaluate | eval-complete | summary
Exit codes: 0 PASS/progress, 1 check-not-yet, 3 HOLD, 4 stop flag, 31 pool insufficient,
32 not authorized, 33 environment/preflight fail (resumable), 75 provider outage,
76 request rejected, 77 budget, 78 invariant, 79 evaluation infrastructure error.
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
for _p in (PROJECT, PROJECT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m14r_core as core  # noqa: E402

ROOT = PROJECT / "research/wp2/m14r_v1"
DESIGN = ROOT / "m14r_design_freeze_v1.json"
DESIGN_SHA = "4d3e73fac6f4095622f448ff85cc4e53aa7cf493ded14c698447b477943bc68f"
PILOT_A = PROJECT / "research/wp2/pilot_a_v1"
ENG_SETS = PROJECT / "research/wp2/harness_v3_2026-09-26/evaluator_only/eng_evaluator_sets_v3.json"
GUARD = ROOT / "m14r_guard.json"
TAXO = ROOT / "analysis/pilot_a_taxonomy.json"
TAXO_MD = PROJECT / "docs/WP2_M14R_PILOT_A_TAXONOMY.md"
READY = ROOT / "readiness"
MEMBERSHIP = ROOT / "m14r_membership.json"
AUTH = ROOT / "human_authorization.json"
FREEZE = ROOT / "m14r_freeze.json"
SCOPES = ROOT / "frozen_scopes.json"
CTX_DIR = ROOT / "readonly_context"
GEN_PLAN = ROOT / "generation_plan.json"
STATIC_PLAN = ROOT / "static_plan.json"
GEN_FREEZE = ROOT / "generation_freeze.json"
EVAL_PLAN = ROOT / "evaluations/plan.json"
SUMMARY = ROOT / "m14r_summary.json"
REPORT = PROJECT / "docs/WP2_M14R_V1_RESULT.md"
LEDGER = ROOT / "ledger/m14r_spend.jsonl"
STOP_FLAG = PROJECT / "logs/M14R_STOP.flag"

APPROVAL_TOKEN = "I_AUTHORIZE_WP2_M14R_V1=YES"
MODEL, PROVIDER = "qwen/qwen3-coder", "deepinfra/turbo"
MAX_USD, WORST_EPISODE_USD = 3.0, 0.12
MIN_MEMBERS = 10
ARMS = ("GOLD_HARD", "PLACEBO_HARD")
GOLD_REPS = ("r1", "r2", "r3")
PLACEBO_REPS = ("r1",)
EMPTY_DIFF_SHA = "16ec795185b645d8d57bd90786f83612f045ee5efe642dd1520f3496ef3b03d3"
TERMINAL = {"NO_SCOPE", "INVALID_AFTER_REPAIR", "APPLIED"}
EXIT_HOLD, EXIT_STOP, EXIT_POOL, EXIT_AUTH, EXIT_PREFLIGHT = 3, 4, 31, 32, 33
EXIT_OUTAGE, EXIT_REJECTED, EXIT_BUDGET, EXIT_INVARIANT, EXIT_EVAL_INFRA = 75, 76, 77, 78, 79
BORROWED = ["src/benchmark/wp2/e2e_v22/transport.py", "src/benchmark/wp2/e2e_v22/circuit.py",
            "src/benchmark/wp2/e2e_v21/generate.py", "src/benchmark/wp2/e2e/generate.py",
            "src/benchmark/wp2/e2e/generate_v2.py", "src/benchmark/wp2/e2e/scopes.py",
            "src/benchmark/wp2/e2e/spec.py", "src/benchmark/wp2/e2e/prompt.py",
            "src/benchmark/wp2/e2e/response_cache.py", "src/benchmark/wp2/e2e/task_inputs.py",
            "src/benchmark/wp2/e2e/evaluate.py", "src/benchmark/wp2/e2e/evaluator_sets.py",
            "src/benchmark/wp2/e2e/patch_format.py", "src/benchmark/wp2/e2e/pycompile.py",
            "src/benchmark/wp2/harness_v3.py", "scripts/wp2_m14a_run.py",
            "scripts/wp2_m14a_evalcore.py", "scripts/wp2_m14a_evalcore_e1.py"]
KIT = ["scripts/wp2_ctl_v224.py", "scripts/wp2_m14r_core.py", "scripts/wp2_m14r_run.py",
       "scripts/wp2_m14r_authorize.py", "controller/plan_m14r_v1.json",
       "controller/light_profile_m14r.json", "controller/KIT_MANIFEST_M14R.json"]


class Stop(Exception):
    def __init__(self, msg: str, code: int = EXIT_INVARIANT) -> None:
        super().__init__(msg)
        self.code = code


# ------------------------------------------------------------------ helpers
def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load(p: Path) -> Any:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def norm_sha(p: Path) -> str:
    d = Path(p).read_bytes()
    if b"\x00" not in d[:8192]:
        d = d.replace(b"\r\n", b"\n")
    return hashlib.sha256(d).hexdigest()


sha_obj = core.sha_obj


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
    return Path(p).relative_to(PROJECT).as_posix()


def git(*a: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *a], cwd=PROJECT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def record_state(p: Path, key: str = "artifact_sha256") -> str:
    if not p.exists():
        return "ABSENT"
    try:
        return "VALID" if hash_ok(load(p), key) else "CORRUPT"
    except (ValueError, OSError):
        return "CORRUPT"


def eng_sets() -> dict:
    d = load(ENG_SETS)
    c = copy.deepcopy(d)
    c.setdefault("hashes", {})["artifact_sha256"] = ""
    got = hashlib.sha256(json.dumps(c, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    require(got == d.get("hashes", {}).get("artifact_sha256") ==
            load(DESIGN)["inputs"]["eng_evaluator_sets_artifact_sha256"], "ENG evaluator sets drift")
    return d["tasks"]


def design() -> dict:
    d = load(DESIGN)
    require(hash_ok(d) and d["artifact_sha256"] == DESIGN_SHA, "design freeze drift")
    require(d["core_constants_sha256"] == sha_obj(core.design_constants()),
            "core constants differ from the frozen design")
    return d


def members() -> list[str]:
    m = load(MEMBERSHIP)
    require(hash_ok(m) and m["verdict"] == "OK", "membership missing or not OK")
    return list(m["members"])


# ------------------------------------------------------------------ guard / taxonomy
def protected_tasks() -> set[str]:
    sel = load(PROJECT / "research/wp2/pilot_v1_design/pilot_selection.json")
    out = set(sel["pilot_a_tasks"]) | set(sel["pilot_b_tasks"]) | set(sel.get("reserve_order", []))
    if (PILOT_A / "readiness").exists():
        out |= {p.name for p in (PILOT_A / "readiness").iterdir() if p.is_dir()}
    return out


def guard() -> int:
    d = design()
    import scripts.wp2_m14a_run as m14a
    bad = m14a.verify_generation_freeze()
    require(not bad, f"Pilot-A frozen evidence drift {bad[:3]}")
    pin = d["inputs"]
    s = load(PILOT_A / "pilot_a_summary.json")
    require(s["artifact_sha256"] == pin["pilot_a_summary_artifact_sha256"]
            and s["token"] == "PILOT_A_GENERATOR_FLOOR_HOLD", "Pilot-A summary differs")
    require(load(PILOT_A / "m14a_e1_amendment.json")["artifact_sha256"]
            == pin["m14a_e1_amendment_artifact_sha256"], "E1 amendment differs")
    require(load(PILOT_A / "generation_freeze.json")["artifact_sha256"]
            == pin["pilot_a_generation_freeze_artifact_sha256"], "Pilot-A generation freeze differs")
    cands = d["population"]["candidate_tasks"]
    overlap = sorted(set(cands) & protected_tasks())
    require(not overlap, f"protected task in M14R population {overlap}")
    sets = eng_sets()
    for t in cands:
        require(t in sets and sets[t]["behavioral_f2p_node_ids"], f"no ENG F2P set for {t}")
    for r in d["inputs"]["required_files"]:
        require((PROJECT / r).exists(), f"required file missing {r}")
    write(GUARD, self_hash({"artifact": "m14r_guard", "artifact_sha256": "", "design": DESIGN_SHA,
                            "candidates": cands, "protected_overlap": [], "model_api_calls": 0,
                            "utc": now()}))
    print("M14R_GUARD_PASS " + json.dumps({"candidates": len(cands)}))
    return 0


def pilot_a_taxonomy() -> int:
    design()
    gp = load(PILOT_A / "generation_plan.json")["items"]
    sets = load(PILOT_A / "evaluator_only/pilot_a_evaluator_sets_v1.json")["tasks"]
    diag: dict[tuple[str, str], str] = {}
    for f in sorted((PILOT_A / "evaluations/diagnostics").glob("*/*/e1_diagnostics.json")):
        x = load(f)
        diag[(x["task_id"], x["label"])] = x["decision"]
    rows = []
    for i in gp:
        e = load(PILOT_A / "episodes" / i["task_id"] / i["label"] / "episode.json")
        t = sets[i["task_id"]]
        if e["status"] == "APPLIED":
            ev = load(PILOT_A / "evaluations/unique" / i["task_id"] / e["diff_sha256"] /
                      "evaluation.json")
            st = core.score_strict(t, ev["groups"])
            require((st["f2p_task"], st["p2p_s_task"], st["p2p_u200_task"], st["resolved"]) ==
                    (ev["f2p_task"], ev["p2p_s_task"], ev["p2p_u200_task"], ev["resolved"]),
                    f"strict re-score differs {i}")
            c = core.classify_episode("APPLIED", e["diff_sha256"] == EMPTY_DIFF_SHA,
                                      diag.get((i["task_id"], "u_" + e["diff_sha256"][:12])),
                                      t, ev["groups"], st)
            rb = core.score_robust(t, ev["groups"])
            nr = core.node_report(t, ev["groups"])
        else:
            c = core.classify_episode(e["status"], False, None, None, None, None)
            st = rb = nr = None
        rows.append({"task_id": i["task_id"], "arm": i["arm"], "replicate": i["replicate"],
                     "status": e["status"], **c, "strict": st, "robust": rb, "nodes": nr,
                     "diff12": e.get("diff_sha256", "")[:12]})
    agg = {a: dict(Counter(r["label"] for r in rows if r["arm"] == a)) for a in ARMS}
    robust = {a: sum(bool(r["robust"] and r["robust"]["resolved"]) for r in rows if r["arm"] == a)
              for a in ARMS}
    exp = design()["pilot_a_expected"]
    require(agg == exp["taxonomy"] and robust == exp["robust_resolved"],
            f"Pilot-A taxonomy differs from the brain's derivation {agg} {robust}")
    out = self_hash({"artifact": "m14r_pilot_a_taxonomy", "artifact_sha256": "",
                     "descriptive_only": True, "changes_no_gate": True,
                     "precedence": list(core.TAXONOMY_PRECEDENCE), "rows": rows,
                     "aggregate": agg, "robust_resolved_descriptive": robust})
    write(TAXO, out)
    lines = ["# Pilot-A failure taxonomy (descriptive; changes no Pilot-A gate)", "",
             "Precedence: " + " > ".join(core.TAXONOMY_PRECEDENCE), "",
             "| Task | Arm | Rep | Label | Detail | F2P nodes 3/3 | S det/int | U det/int |",
             "|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["arm"], r["task_id"], r["replicate"])):
        n = r["nodes"]
        f2 = "-" if not n else f"{n['f2p_pass3']}/{n['f2p_total']}"
        sd = "-" if not n else f"{n['s_deterministic'] + n['s_missing']}/{n['s_intermittent']}"
        ud = "-" if not n else f"{n['u_deterministic'] + n['u_missing']}/{n['u_intermittent']}"
        lines.append(f"| {r['task_id']} | {r['arm']} | {r['replicate']} | {r['label']} | "
                     f"{r['detail']} | {f2} | {sd} | {ud} |")
    lines += ["", f"Aggregate: {json.dumps(agg, sort_keys=True)}",
              f"Descriptive robust-preservation RESOLVED: {json.dumps(robust, sort_keys=True)}", ""]
    TAXO_MD.parent.mkdir(parents=True, exist_ok=True)
    TAXO_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("M14R_PILOT_A_TAXONOMY " + json.dumps(agg, sort_keys=True))
    return 0


# ------------------------------------------------------------------ readiness (zero API)
def _ev():
    from scripts.wp2_m14a_evalcore import point_evaluator
    return point_evaluator(ENG_SETS, ROOT)


def scoped_gold_diff(task_id: str, editable: list[str]) -> str:
    from benchmark.wp2.e2e.scopes import commits_of
    from scripts.wp2_linux_dryrun import WSL_CACHE, wsl
    parent, target = commits_of(task_id)
    if not editable:
        return ""
    quoted = " ".join(f"'{p}'" for p in editable)
    r = wsl(f"git -C {WSL_CACHE} diff {parent} {target} -- {quoted}")
    if r.returncode != 0:
        from scripts.wp2_m14a_evalcore import EvalInfraError
        raise EvalInfraError(f"git diff failed for {task_id}")
    return r.stdout


def readiness_task(task_id: str, ev: Any = None) -> dict:
    from benchmark.wp2.e2e.scopes import build_arm_scopes
    from scripts.wp2_m14a_evalcore import evaluate_state_safe
    from scripts.wp2_m14a_evalcore_e1 import evaluate_state_e1
    ev = ev or _ev()
    t = eng_sets()[task_id]
    wt, tree = ev.materialize(task_id, "rneg", "")
    neg = evaluate_state_safe(ev, task_id, "rneg", wt)
    nst, nrb = core.score_strict(t, neg["groups"]), core.score_robust(t, neg["groups"])
    rec: dict[str, Any] = {"task_id": task_id, "negative": {
        "tree_sha": tree, "strict": nst, "robust": nrb,
        "nodes": core.node_report(t, neg["groups"])}}
    write(READY / task_id / "negative_groups.json",
          self_hash({"task_id": task_id, "groups": neg["groups"], "tree_sha": tree,
                     "junit_files": neg["junit_files"], "artifact_sha256": ""}))
    gold = build_arm_scopes(task_id, "GOLD_HARD")
    diff = scoped_gold_diff(task_id, gold["editable"])
    rec["positive"] = {"editable": gold["editable"], "excluded_large": gold["excluded_large"],
                       "excluded_budget": gold["excluded_budget"],
                       "scoped_diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest()}
    reason = ""
    if nst["f2p_task"] != "FAIL" or nrb["p2p_s_task"] not in core.PASSISH or \
            nrb["p2p_u200_task"] not in core.PASSISH:
        reason = "NEGATIVE_CONTROL_INVALID"
    elif not diff.strip():
        reason = "EMPTY_SCOPED_GOLD"
    else:
        try:
            wt2, tree2 = ev.materialize(task_id, "rpos", diff)
        except ValueError as exc:
            reason = "SCOPED_GOLD_DOES_NOT_APPLY"
            rec["positive"]["error"] = str(exc)[:300]
        else:
            pos = evaluate_state_e1(ev, task_id, "rpos", wt2, diff_text=diff,
                                    diag_path=READY / task_id / "positive_e1_diagnostics.json",
                                    parent_starts_ok=True)
            pst, prb = core.score_strict(t, pos["groups"]), core.score_robust(t, pos["groups"])
            rec["positive"].update({"tree_sha": tree2, "strict": pst, "robust": prb,
                                    "e1_decision": pos["e1_decision"],
                                    "nodes": core.node_report(t, pos["groups"])})
            if not prb["resolved"]:
                reason = "SCOPED_GOLD_NOT_RESOLVED"
    rec["decision"] = "READY" if not reason else "NOT_READY_" + reason
    return rec


def readiness(max_new: int, task_fn: Callable[[str], dict] | None = None) -> int:
    design()
    require(GUARD.exists() and hash_ok(load(GUARD)), "guard missing")
    task_fn = task_fn or readiness_task
    done = 0
    for t in design()["population"]["candidate_tasks"]:
        p = READY / t / "record.json"
        st = record_state(p)
        require(st != "CORRUPT", f"corrupt readiness record {t}")
        if st == "VALID":
            continue
        if done >= max_new:
            break
        try:
            rec = task_fn(t)
        except Exception as exc:
            if type(exc).__name__ in ("EvalInfraError", "RuntimeError", "TimeoutExpired"):
                raise Stop(f"readiness environment failure {t}: {exc}", EXIT_PREFLIGHT) from exc
            raise
        write(p, self_hash(dict(rec, artifact="m14r_readiness_task", artifact_sha256="",
                                model_api_calls=0, utc=now())))
        done += 1
        print(f"[m14r-readiness] {t} -> {rec['decision']}", flush=True)
    print(f"READINESS_CHUNK new={done}")
    return 0


def readiness_check() -> int:
    c = design()["population"]["candidate_tasks"]
    n = sum(record_state(READY / t / "record.json") == "VALID" for t in c)
    print(f"READINESS_{'COMPLETE' if n == len(c) else 'INCOMPLETE'} {n}/{len(c)}")
    return 0 if n == len(c) else 1


def membership() -> int:
    require(readiness_check() == 0, "readiness incomplete")
    c = design()["population"]["candidate_tasks"]
    recs = {t: load(READY / t / "record.json") for t in c}
    mem = sorted(t for t in c if recs[t]["decision"] == "READY")
    verdict = "OK" if len(mem) >= MIN_MEMBERS else "POOL_INSUFFICIENT"
    write(MEMBERSHIP, self_hash({"artifact": "m14r_membership", "artifact_sha256": "",
                                 "verdict": verdict, "members": mem, "min_members": MIN_MEMBERS,
                                 "excluded": {t: recs[t]["decision"] for t in c if t not in mem},
                                 "readiness_record_sha256": {t: recs[t]["artifact_sha256"]
                                                             for t in c}}))
    print("M14R_MEMBERSHIP " + json.dumps({"verdict": verdict, "n": len(mem)}))
    return 0 if verdict == "OK" else EXIT_POOL


# ------------------------------------------------------------------ authorization / doctor
def validate_auth() -> dict:
    require(AUTH.exists(), "human_authorization.json missing", EXIT_AUTH)
    a = load(AUTH)
    require(hash_ok(a), "authorization self-hash mismatch", EXIT_AUTH)
    require(a.get("authorized") is True and a.get("approval_token") == APPROVAL_TOKEN,
            "authorization token", EXIT_AUTH)
    require(a.get("design_artifact_sha256") == DESIGN_SHA, "design hash mismatch", EXIT_AUTH)
    require(a.get("membership_artifact_sha256") == load(MEMBERSHIP)["artifact_sha256"],
            "membership hash mismatch", EXIT_AUTH)
    require(a.get("model") == MODEL and a.get("provider") == PROVIDER
            and a.get("allow_fallbacks") is False, "route mismatch", EXIT_AUTH)
    cap = a.get("max_generation_spend_usd")
    require(isinstance(cap, (int, float)) and 0 < float(cap) <= MAX_USD,
            f"max spend must be > 0 and <= {MAX_USD}", EXIT_AUTH)
    r = rel(AUTH)
    require(git("ls-files", "--error-unmatch", r).returncode == 0, "authorization not tracked",
            EXIT_AUTH)
    require(not git("status", "--porcelain", "--", r).stdout.strip(),
            "authorization has uncommitted changes", EXIT_AUTH)
    return a


def auth_check() -> int:
    a = validate_auth()
    write(ROOT / "auth_check.json", self_hash({
        "artifact": "m14r_auth_check", "artifact_sha256": "", "auth_artifact_sha256":
        a["artifact_sha256"], "authorized_by": a.get("authorized_by"),
        "max_generation_spend_usd": a["max_generation_spend_usd"]}))
    print("AUTH_CHECK_PASS " + json.dumps({"by": a.get("authorized_by"),
                                           "max_usd": a["max_generation_spend_usd"]}))
    return 0


def pyflakes_identity() -> dict:
    import pyflakes
    import pyflakes.checker as pc
    return {"version": pyflakes.__version__, "checker_sha256": norm_sha(Path(pc.__file__)),
            "host_python": sys.version.split()[0]}


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
    try:
        checks["pyflakes"] = {"ok": True, "value": pyflakes_identity()}
    except Exception as exc:
        checks["pyflakes"] = {"ok": False, "value": f"{exc}; install with: "
                              "python -m pip install pyflakes"}
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
            from scripts.wp2_e2e_v22_doctor import live_pricing
            checks["pricing"] = live_pricing()
        except Exception as exc:
            checks["pricing"] = {"ok": False, "value": str(exc)[:200]}
    ok = all(v.get("ok") for v in checks.values())
    write(ROOT / f"doctor/doctor_{mode}.json", self_hash({
        "artifact": "m14r_doctor", "artifact_sha256": "", "mode": mode, "checks": checks,
        "pass": ok, "model_api_calls": 0, "utc": now()}))
    for k, v in checks.items():
        print(f"DOCTOR {'PASS' if v.get('ok') else 'FAIL'} {k} {str(v.get('value', ''))[:160]}")
    return 0 if ok else EXIT_PREFLIGHT


# ------------------------------------------------------------------ plans / freeze
def base_items(tasks: list[str]) -> list[dict]:
    out = []
    for rep in GOLD_REPS:
        for t in tasks:
            for ctx in core.CONTEXTS:
                out.append({"task_id": t, "arm": "GOLD_HARD", "context": ctx, "replicate": rep,
                            "label": f"GOLD_HARD__{ctx}__{rep}"})
        if rep in PLACEBO_REPS:
            for t in tasks:
                for ctx in core.CONTEXTS:
                    out.append({"task_id": t, "arm": "PLACEBO_HARD", "context": ctx,
                                "replicate": rep, "label": f"PLACEBO_HARD__{ctx}__{rep}"})
    return out


def static_items(tasks: list[str]) -> list[dict]:
    return [{**i, "context": i["context"], "static": True, "base_label": i["label"],
             "label": f"{i['arm']}__{i['context']}S__{i['replicate']}"} for i in base_items(tasks)]


def variant_of(label: str) -> str:
    ctx = label.split("__")[1]
    return {"C0": "G0", "C0S": "G1", "C2": "G2", "C2S": "G3"}[ctx]


def ctx_path(task_id: str, arm: str) -> Path:
    return CTX_DIR / task_id / f"{arm}.txt"


def host_parent_reader(task_id: str) -> tuple[Callable[[str], str | None], set[str]]:
    from benchmark.wp2.e2e.scopes import _git_show, _tracked_paths, commits_of
    parent, _ = commits_of(task_id)
    cache: dict[str, str | None] = {}

    def show(p: str) -> str | None:
        if p not in cache:
            cache[p] = _git_show(parent, p)
        return cache[p]
    return show, set(_tracked_paths(parent))


def leakage_scan(task_id: str, text: str, sets_t: dict) -> list[str]:
    """Evaluator-side audit of a read-only context (never shown to the model)."""
    from benchmark.wp2.e2e.scopes import SALEOR_CACHE, commits_of
    from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2
    parent, target = commits_of(task_id)
    r = subprocess.run(["git", "-C", str(SALEOR_CACHE), "diff", "--name-only", parent, target],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    tests = [p for p in r.stdout.split() if is_test_path_v2(p)]
    hits = [f"test_path:{p}" for p in tests if p in text]
    for n in (sets_t["behavioral_f2p_node_ids"] + sets_t["p2p_s_node_ids"]
              + sets_t["p2p_u_cap200_stable_ids"]):
        if n in text:
            hits.append(f"node:{n[:100]}")
    return hits


def build_contexts(tasks: list[str], scopes: dict) -> dict:
    from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2
    sets = eng_sets()
    meta: dict[str, dict] = {}
    for t in tasks:
        show, tracked = host_parent_reader(t)
        for arm in ARMS:
            ctx = core.build_readonly_context(scopes[t][arm]["editable"], show, tracked,
                                              is_test_path_v2)
            bad = core.verbatim_audit(ctx["text"], show)
            require(not bad, f"read-only context not parent-verbatim {t}/{arm}: {bad[:2]}")
            hits = leakage_scan(t, ctx["text"], sets[t])
            require(not hits, f"LEAKAGE_BLOCK {t}/{arm}: {hits[:3]}")
            p = ctx_path(t, arm)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(ctx["text"], encoding="utf-8", newline="\n")
            meta[f"{t}/{arm}"] = {"sha256": ctx["sha256"], "chars": ctx["chars"],
                                  "modules": ctx["modules"], "leakage_hits": 0,
                                  "verbatim_violations": 0}
    return meta


def build_freeze() -> dict:
    from benchmark.wp2.e2e.scopes import build_arm_scopes
    d = design()
    a = validate_auth()
    tasks = members()
    scopes = {t: {arm: build_arm_scopes(t, arm) for arm in ARMS} for t in tasks}
    for t in tasks:
        require(load(READY / t / "record.json")["positive"]["editable"]
                == scopes[t]["GOLD_HARD"]["editable"],
                f"GOLD scope differs from the readiness positive control {t}")
    write(SCOPES, {"artifact": "m14r_frozen_scopes", "tasks": scopes, "sha256": sha_obj(scopes)})
    ctx_meta = build_contexts(tasks, scopes)
    write(ROOT / "readonly_context/context_meta.json", {"artifact": "m14r_context_meta",
                                                       "contexts": ctx_meta})
    bi, si = base_items(tasks), static_items(tasks)
    write(GEN_PLAN, {"artifact": "m14r_generation_plan", "items": bi, "sha256": sha_obj(bi)})
    write(STATIC_PLAN, {"artifact": "m14r_static_plan", "items": si, "sha256": sha_obj(si)})
    intents = {}
    for t in tasks:
        p = PROJECT / f"benchmark_data/real_commit_impact_saleor/scientific/{t}/public/intent.json"
        require(p.exists(), f"public intent missing {t}")
        intents[rel(p)] = norm_sha(p)
    arts = [DESIGN, GUARD, MEMBERSHIP, AUTH, ROOT / "doctor/doctor_offline.json",
            ROOT / "doctor/doctor_paid.json", SCOPES, GEN_PLAN, STATIC_PLAN,
            ROOT / "readonly_context/context_meta.json"]
    arts += [ctx_path(t, arm) for t in tasks for arm in ARMS]
    arts += [READY / t / "record.json" for t in d["population"]["candidate_tasks"]]
    return self_hash({
        "artifact": "m14r_freeze", "artifact_sha256": "", "design_artifact_sha256": DESIGN_SHA,
        "membership_artifact_sha256": load(MEMBERSHIP)["artifact_sha256"],
        "human_auth_artifact_sha256": a["artifact_sha256"],
        "max_generation_spend_usd": float(a["max_generation_spend_usd"]),
        "model": MODEL, "provider": PROVIDER, "allow_fallbacks": False, "temperature": 0.0,
        "max_tokens": 8192, "max_format_repairs": 1, "max_static_repairs": 1,
        "pyflakes": pyflakes_identity(), "planned_base_episodes": len(bi),
        "planned_static_episodes": len(si), "generation_plan_sha256": sha_obj(bi),
        "static_plan_sha256": sha_obj(si), "frozen_scopes_sha256": sha_obj(scopes),
        "artifact_hashes": {rel(p): norm_sha(p) for p in arts},
        "source_hashes": {r: norm_sha(PROJECT / r) for r in BORROWED + KIT},
        "public_intent_hashes": intents})


def verify_freeze() -> list[str]:
    if not (FREEZE.exists() and GEN_PLAN.exists() and SCOPES.exists() and STATIC_PLAN.exists()):
        return ["freeze artifacts missing"]
    fr = load(FREEZE)
    bad = [] if hash_ok(fr) else ["freeze self-hash"]
    for key in ("artifact_hashes", "source_hashes", "public_intent_hashes"):
        for r, h in fr.get(key, {}).items():
            p = PROJECT / r
            if not p.exists() or norm_sha(p) != h:
                bad.append(f"drift {r}")
    if sha_obj(load(GEN_PLAN)["items"]) != fr["generation_plan_sha256"] or \
            sha_obj(load(STATIC_PLAN)["items"]) != fr["static_plan_sha256"] or \
            sha_obj(load(SCOPES)["tasks"]) != fr["frozen_scopes_sha256"]:
        bad.append("plan/scope drift")
    return bad


def freeze() -> int:
    require(not FREEZE.exists() or not (ROOT / "episodes").exists(),
            "freeze exists and paid evidence exists")
    write(FREEZE, build_freeze())
    bad = verify_freeze()
    require(not bad, f"freeze verify failed {bad[:5]}")
    print("M14R_FREEZE_PASS " + json.dumps({"sha": load(FREEZE)["artifact_sha256"][:16],
                                            "base": load(FREEZE)["planned_base_episodes"]}))
    return 0


def freeze_verify() -> int:
    bad = verify_freeze()
    print("M14R_FREEZE_VERIFY_PASS" if not bad else "M14R_FREEZE_VERIFY_FAIL " + str(bad[:5]))
    return 0 if not bad else 1


# ------------------------------------------------------------------ generation
class Ledger:
    """Durable spend ledger (fsync per record). Fresh provider calls only."""

    def __init__(self, path: Path, ceiling: float) -> None:
        self.path, self.ceiling, self.t, self.context = path, ceiling, 0.0, {}
        if path.exists():
            for x in path.read_text(encoding="utf-8").splitlines():
                if x.strip():
                    self.t += float(json.loads(x).get("cost_usd", 0) or 0)

    def total(self) -> float:
        return self.t

    def can_spend(self, worst: float) -> bool:
        return self.t + worst <= self.ceiling + 1e-12

    def record(self, r: dict) -> None:
        r = dict(r, stage="M14R", **self.context)
        self.t += float(r.get("cost_usd", 0) or 0)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(r, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())


def ep_dir(item: dict) -> Path:
    return ROOT / "episodes" / item["task_id"] / item["label"]


def ep_status(item: dict) -> str | None:
    p = ep_dir(item) / "episode.json"
    if not p.exists():
        return None
    try:
        return load(p).get("status")
    except (ValueError, OSError):
        return "UNREADABLE"


def system_for(ctx: str) -> str:
    from benchmark.wp2.e2e.prompt import SYSTEM_PROMPT
    if ctx == "C0":
        return SYSTEM_PROMPT
    anchor = "Implement the described change by editing ONLY those files."
    require(anchor in SYSTEM_PROMPT, "frozen system prompt anchor missing")
    return SYSTEM_PROMPT.replace(anchor, core.SYSTEM_PROMPT_C2_INSERT + anchor)


def context_text(item: dict) -> str:
    if item["context"] == "C0":
        return ""
    txt = ctx_path(item["task_id"], item["arm"]).read_text(encoding="utf-8")
    key = f"{item['task_id']}/{item['arm']}"
    meta = load(ROOT / "readonly_context/context_meta.json")["contexts"][key]
    require(hashlib.sha256(txt.encode("utf-8")).hexdigest() == meta["sha256"],
            f"read-only context drift {key}")
    return txt


def messages_for(item: dict, ti: Any, editable: list[str], parent_texts: dict[str, str],
                 scope: dict) -> tuple[list[dict], str]:
    from benchmark.wp2.e2e.prompt import build_prompt
    _system, user, prompt_sha = build_prompt(ti, editable, parent_texts, scope)
    ctx = context_text(item)
    if ctx:
        user = user + "\n\n" + ctx
        prompt_sha = hashlib.sha256(user.encode("utf-8")).hexdigest()
    return ([{"role": "system", "content": system_for(item["context"])},
             {"role": "user", "content": user}], prompt_sha)


def _call(client: Any, ledger: Any, cache: Any, request: dict, messages: list[dict],
          task_id: str, arm: str, label: str, idx: int, kind: str) -> dict:
    from benchmark.wp2.e2e.generate import _record_ledger
    from benchmark.wp2.e2e.generate_v2 import _cache_entry_from_call, _persist_raw
    from benchmark.wp2.e2e.response_cache import ResponseCache
    from benchmark.wp2.e2e_v21.generate import _call_entry_v21
    rsha = ResponseCache.request_sha(**request)
    entry = cache.get(rsha)
    if entry is None:
        call = client.generate_messages(messages)
        raw_path, raw_sha = _persist_raw(ROOT, task_id, label, idx, kind, call.text)
        entry = _cache_entry_from_call(call, request, rsha, True, str(raw_path))
        entry["raw_sha256"] = raw_sha
        cache.put(rsha, entry)
        _record_ledger(ledger, call, task_id, arm, kind)
        return {"entry": entry, "call": _call_entry_v21(entry, kind, idx), "sha": rsha}
    return {"entry": entry, "call": _call_entry_v21(entry, kind + "_reused", 0), "sha": rsha}


def run_base_episode(item: dict, client: Any, ledger: Any, cache: Any) -> dict:
    """Frozen run_episode_v21 semantics (G0) with an optional read-only context (C2)."""
    from benchmark.wp2.e2e.generate import _parent_texts, _raw_scope
    from benchmark.wp2.e2e.generate_v2 import _component_hashes, _validate_v2
    from benchmark.wp2.e2e.patch_format import unified_diff
    from benchmark.wp2.e2e.prompt import build_repair_messages
    from benchmark.wp2.e2e.scopes import editable_filter
    from benchmark.wp2.e2e.spec import INTERFACE_VERSION, MAX_REPAIRS, spec_sha256
    from benchmark.wp2.e2e.task_inputs import load_task_input
    from benchmark.wp2.e2e_v21.generate import _build_request
    task_id, arm, label = item["task_id"], item["arm"], item["label"]
    scope = editable_filter(task_id, _raw_scope(task_id, arm))
    base = {"smoke_version": "wp2-m14r-v1", "interface_version": INTERFACE_VERSION,
            "task_id": task_id, "arm": arm, "label": label, "variant": variant_of(label),
            "context": item["context"], "replicate": item["replicate"],
            "spec_sha256": spec_sha256(), "created_utc": now()}
    if not scope["editable"]:
        rec = dict(base, status="NO_SCOPE", editable_set=[], excluded=scope, calls=[],
                   validation={}, repair_used=False, edited_files=[], diff_sha256="",
                   context_sha256="")
        return persist_episode(item, rec, "", {})
    ti = load_task_input(task_id)
    parent_texts = _parent_texts(task_id, scope["editable"])
    messages, prompt_sha = messages_for(item, ti, scope["editable"], parent_texts, scope)
    request = _build_request(messages)
    calls: list[dict] = []
    r1 = _call(client, ledger, cache, request, messages, task_id, arm, label, 1, "initial")
    calls.append(r1["call"])
    text = r1["entry"]["text"]
    errors, final, _br, _st = _validate_v2(text, scope["editable"], parent_texts,
                                           r1["entry"]["finish_reason"], ti.era_key)
    initial_errors = list(errors)
    repair_used, errors2, repair_sha, comp = False, [], "", {}
    produced_by = "initial"
    if errors and MAX_REPAIRS >= 1:
        hint = any("SEARCH_ELLIPSIS" in e or "SEARCH_ERROR" in e for e in errors)
        rmsg = build_repair_messages(messages[0]["content"], messages[1]["content"], text,
                                     errors, hint)
        rreq = _build_request(rmsg)
        r2 = _call(client, ledger, cache, rreq, rmsg, task_id, arm, label, 2, "repair")
        calls.append(r2["call"])
        repair_used, repair_sha, comp = True, r2["sha"], _component_hashes(rmsg)
        errors2, final2, _b2, _s2 = _validate_v2(r2["entry"]["text"], scope["editable"],
                                                 parent_texts, r2["entry"]["finish_reason"],
                                                 ti.era_key)
        if not errors2:
            errors, final, produced_by = errors2, final2, "repair"
    status = "APPLIED" if not errors else "INVALID_AFTER_REPAIR"
    diff = unified_diff(parent_texts, final) if (final and status == "APPLIED") else ""
    rec = dict(base, status=status, editable_set=scope["editable"], excluded=scope,
               prompt_sha256=prompt_sha, request_sha_initial=r1["sha"],
               request_sha_repair=repair_sha, repair_component_hashes=comp,
               context_sha256=hashlib.sha256(context_text(item).encode("utf-8")).hexdigest(),
               calls=calls, validation={"initial": initial_errors, "repair": errors2},
               repair_used=repair_used, produced_by=produced_by if status == "APPLIED" else "",
               edited_files=sorted(final.keys()) if status == "APPLIED" else [],
               diff_sha256=core_diff_sha(diff) if status == "APPLIED" else "")
    return persist_episode(item, rec, diff, final if status == "APPLIED" else {})


def core_diff_sha(diff: str) -> str:
    """Frozen v21 identity: sha256(json.dumps([diff]))."""
    return hashlib.sha256(json.dumps([diff], sort_keys=True, ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def persist_episode(item: dict, rec: dict, diff: str, final: dict[str, str]) -> dict:
    rec["episode_sha256"] = ""
    rec["episode_sha256"] = sha_obj(rec)
    d = ep_dir(item)
    d.mkdir(parents=True, exist_ok=True)
    if rec["status"] == "APPLIED":
        (d / "final_diff.patch").write_text(diff, encoding="utf-8", newline="")
        for path, text in final.items():
            p = d / "final_files" / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8", newline="")
    (d / "episode.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False),
                                    encoding="utf-8")
    return rec


def run_static_episode(item: dict, client: Any, ledger: Any, cache: Any) -> dict:
    """STATIC_UNDEFINED_V1 on top of the frozen base episode (paired design)."""
    from benchmark.wp2.e2e.generate import _parent_texts
    from benchmark.wp2.e2e.generate_v2 import _validate_v2
    from benchmark.wp2.e2e.patch_format import unified_diff
    from benchmark.wp2.e2e.task_inputs import load_task_input
    from benchmark.wp2.e2e_v21.generate import _build_request
    bitem = {**item, "label": item["base_label"]}
    bdir = ep_dir(bitem)
    b = load(bdir / "episode.json")
    require(b.get("status") in TERMINAL, f"base episode not terminal {bitem}")
    require(b["episode_sha256"] == sha_obj(dict(b, episode_sha256="")),
            f"base episode hash {bitem}")
    rec = {k: v for k, v in b.items() if k != "episode_sha256"}
    rec.update({"label": item["label"], "variant": variant_of(item["label"]),
                "base_label": item["base_label"], "base_episode_sha256": b["episode_sha256"],
                "created_utc": now(), "calls": [dict(c, inherited_from_base=True)
                                                for c in b.get("calls", [])]})
    if b["status"] != "APPLIED":
        rec["static"] = {"triggered": False, "reason": "BASE_NOT_APPLIED"}
        return persist_episode(item, rec, "", {})
    editable = b["editable_set"]
    parent = _parent_texts(item["task_id"], editable)
    final = dict(parent)
    for p in b["edited_files"]:
        final[p] = (bdir / "final_files" / p).read_text(encoding="utf-8")
    base_diff = (bdir / "final_diff.patch").read_text(encoding="utf-8")
    require(core_diff_sha(base_diff) == b["diff_sha256"], f"base diff drift {bitem}")
    found = core.new_static_findings(parent, final, b["edited_files"])
    if not found["new"]:
        rec["static"] = {"triggered": False, "reason": "CLEAN",
                         "parse_skipped": found["parse_skipped"]}
        return persist_episode(item, rec, base_diff,
                               {p: final[p] for p in b["edited_files"]})
    ti = load_task_input(item["task_id"])
    messages, prompt_sha = messages_for(bitem, ti, editable, parent, b["excluded"])
    require(prompt_sha == b["prompt_sha256"], f"base prompt not reproducible {bitem}")
    cand_idx, cand_kind = (1, "initial") if b.get("produced_by") == "initial" else (2, "repair")
    cand = bdir / "calls" / f"{cand_idx}_{cand_kind}.txt"
    cand_text = cand.read_text(encoding="utf-8")
    want = [c for c in b["calls"] if c.get("kind", "").startswith(cand_kind)]
    require(bool(want) and hashlib.sha256(cand_text.encode("utf-8")).hexdigest()
            == want[0].get("response_sha256"), f"candidate response drift {bitem}")
    smsg = messages + [{"role": "assistant", "content": cand_text},
                       {"role": "user", "content": core.static_repair_text(found["new"])}]
    sreq = _build_request(smsg)
    r3 = _call(client, ledger, cache, sreq, smsg, item["task_id"], item["arm"], item["label"],
               3, "static_repair")
    rec["calls"].append(r3["call"])
    errs, final2, _b, _s = _validate_v2(r3["entry"]["text"], editable, parent,
                                        r3["entry"]["finish_reason"], ti.era_key)
    if errs:
        rec["static"] = {"triggered": True, "findings": found["new"], "repair_status":
                         "INVALID_KEPT_BASE", "repair_errors": errs, "request_sha": r3["sha"]}
        return persist_episode(item, rec, base_diff, {p: final[p] for p in b["edited_files"]})
    diff2 = unified_diff(parent, final2)
    remaining = core.new_static_findings(parent, {**parent, **final2}, sorted(final2))["new"]
    rec.update({"edited_files": sorted(final2), "diff_sha256": core_diff_sha(diff2)})
    rec["static"] = {"triggered": True, "findings": found["new"], "repair_status": "ADOPTED",
                     "remaining_new_findings": len(remaining), "request_sha": r3["sha"]}
    return persist_episode(item, rec, diff2, final2)


def drive(items: list[dict], runner: Callable[[dict], dict], client: Any, ledger: Any,
          breaker: Any, expected_editable: Callable[[dict], list[str]], max_new: int,
          max_seconds: float, clock: Callable[[], float] = time.monotonic,
          sleep: Callable[[float], None] = time.sleep, stop_flag: Path | None = None) -> tuple[int, dict]:
    """M14A v2.2 driver semantics; provider failures never become outcomes."""
    from benchmark.wp2.e2e_v22.transport import HoldActiveV22, ProviderUnavailable, RequestRejected
    stop_flag = stop_flag or STOP_FLAG
    info: dict[str, Any] = {"new_terminal": 0, "planned": len(items)}
    for i in items:
        if ep_status(i) == "UNREADABLE":
            info["invariant"] = f"unreadable episode {i['task_id']}/{i['label']}"
            return EXIT_INVARIANT, info
    breaker.on_start()
    t0 = clock()
    for i in items:
        if ep_status(i) in TERMINAL:
            continue
        if info["new_terminal"] >= max_new or clock() - t0 >= max_seconds:
            break
        while True:
            if stop_flag.exists():
                return EXIT_STOP, info
            if not ledger.can_spend(WORST_EPISODE_USD):
                info["budget_total"] = ledger.total()
                return EXIT_BUDGET, info
            client.set_context(task_id=i["task_id"], arm=i["arm"], label=i["label"],
                               replicate=i["replicate"], mode="m14r")
            ledger.context = {"label": i["label"], "variant": variant_of(i["label"])}
            try:
                rec = runner(i)
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
            except Stop:
                raise
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


def _paid_setup():
    from benchmark.wp2.e2e_v22.circuit import CircuitBreaker
    from benchmark.wp2.e2e_v22.transport import AttemptLog, V22HttpClient
    a = validate_auth()
    ledger = Ledger(LEDGER, min(float(a["max_generation_spend_usd"]), MAX_USD))
    client = V22HttpClient([ROOT / "HOLD"], AttemptLog(ROOT / "transport/attempts.jsonl"))
    breaker = CircuitBreaker(ROOT / "transport/circuit.json")
    return ledger, client, breaker


def cache_for(item: dict):
    from benchmark.wp2.e2e.response_cache import ResponseCache
    return ResponseCache(ROOT / "cache_namespaces" / item["task_id"] / item["label"])


def generate(max_new: int, max_seconds: float) -> int:
    bad = verify_freeze()
    require(not bad, f"freeze drift before generation {bad[:3]}")
    ledger, client, breaker = _paid_setup()
    scopes = load(SCOPES)["tasks"]
    code, info = drive(load(GEN_PLAN)["items"],
                       lambda i: run_base_episode(i, client, ledger, cache_for(i)),
                       client, ledger, breaker,
                       lambda i: scopes[i["task_id"]][i["arm"]]["editable"], max_new, max_seconds)
    info.update({"exit": code, "spend_total_usd": round(ledger.total(), 7),
                 "network_attempts": client.network_attempts})
    print("M14R_DRIVER_RESULT " + json.dumps(info, sort_keys=True, default=str))
    return code


def _complete(plan: Path, tag: str) -> int:
    if not plan.exists():
        return 1
    items = load(plan)["items"]
    n = sum(ep_status(i) in TERMINAL for i in items)
    print(f"{tag}_{'COMPLETE' if n == len(items) else 'INCOMPLETE'} {n}/{len(items)}")
    return 0 if n == len(items) else 1


def generation_complete() -> int:
    return _complete(GEN_PLAN, "GENERATION")


def static(max_new: int, max_seconds: float) -> int:
    bad = verify_freeze()
    require(not bad, f"freeze drift before static stage {bad[:3]}")
    require(generation_complete() == 0, "base generation incomplete")
    ledger, client, breaker = _paid_setup()
    scopes = load(SCOPES)["tasks"]
    code, info = drive(load(STATIC_PLAN)["items"],
                       lambda i: run_static_episode(i, client, ledger, cache_for(i)),
                       client, ledger, breaker,
                       lambda i: scopes[i["task_id"]][i["arm"]]["editable"], max_new, max_seconds)
    info.update({"exit": code, "spend_total_usd": round(ledger.total(), 7),
                 "network_attempts": client.network_attempts})
    print("M14R_STATIC_RESULT " + json.dumps(info, sort_keys=True, default=str))
    return code


def static_complete() -> int:
    return _complete(STATIC_PLAN, "STATIC")


def all_items() -> list[dict]:
    return load(GEN_PLAN)["items"] + load(STATIC_PLAN)["items"]


def generation_freeze() -> int:
    require(generation_complete() == 0 and static_complete() == 0, "generation incomplete")
    require(not verify_freeze(), "freeze drift")
    files = {p.relative_to(ROOT).as_posix(): norm_sha(p)
             for p in sorted((ROOT / "episodes").rglob("*")) if p.is_file()}
    for r in ("ledger/m14r_spend.jsonl", "transport/attempts.jsonl"):
        if (ROOT / r).exists():
            files[r] = norm_sha(ROOT / r)
    for i in all_items():
        e = load(ep_dir(i) / "episode.json")
        require(e.get("status") in TERMINAL, "non-terminal episode")
        require(e["episode_sha256"] == sha_obj(dict(e, episode_sha256="")), f"episode hash {i}")
        for c in e.get("calls", []):
            require(c.get("route") != "replay", "replay route in paid evidence")
    gf = self_hash({"artifact": "m14r_generation_freeze", "artifact_sha256": "",
                    "m14r_freeze_sha256": load(FREEZE)["artifact_sha256"],
                    "n_episodes": len(all_items()), "files": files,
                    "spend_usd": round(Ledger(LEDGER, MAX_USD).total(), 7)})
    if GEN_FREEZE.exists():
        require(load(GEN_FREEZE)["artifact_sha256"] == gf["artifact_sha256"],
                "generation freeze exists and differs")
    write(GEN_FREEZE, gf)
    print("M14R_GENERATION_FROZEN " + json.dumps({"n": gf["n_episodes"], "usd": gf["spend_usd"]}))
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
    print("M14R_GENERATION_FREEZE_VERIFY_PASS" if not bad else
          "M14R_GENERATION_FREEZE_VERIFY_FAIL " + str(bad[:5]))
    return 0 if not bad else 1


# ------------------------------------------------------------------ evaluation (zero API)
def unique_path(task_id: str, diff_sha: str) -> Path:
    require(len(diff_sha) == 64, f"full diff sha required: {diff_sha!r}")
    return ROOT / "evaluations/unique" / task_id / diff_sha / "evaluation.json"


def build_eval_plan() -> list[dict]:
    uniq: dict[tuple[str, str], dict] = {}
    for i in all_items():
        e = load(ep_dir(i) / "episode.json")
        if e.get("status") != "APPLIED" or not e.get("diff_sha256"):
            continue
        k = (i["task_id"], e["diff_sha256"])
        src = (ep_dir(i) / "episode.json").relative_to(ROOT).as_posix()
        if k not in uniq:
            uniq[k] = {"task_id": i["task_id"], "diff_sha256": e["diff_sha256"], "source": src,
                       "labels": [i["label"]], "sources": [src]}
        else:
            uniq[k]["labels"].append(i["label"])
            uniq[k]["sources"].append(src)
    return sorted(uniq.values(), key=lambda x: (x["task_id"], x["diff_sha256"]))


def eval_plan() -> int:
    bad = verify_generation_freeze()
    require(not bad, f"generation freeze drift {bad[:3]}")
    items = build_eval_plan()
    p = {"artifact": "m14r_evaluation_plan", "items": items, "n_unique_identities": len(items),
         "sha256": sha_obj(items)}
    if EVAL_PLAN.exists():
        require(load(EVAL_PLAN)["items"] == items, "existing evaluation plan differs")
    else:
        write(EVAL_PLAN, p)
    print("M14R_EVAL_PLAN " + json.dumps({"n_unique_identities": len(items)}))
    return 0


def readiness_ok(task_id: str) -> bool:
    p = READY / task_id / "record.json"
    return record_state(p) == "VALID" and load(p)["decision"] == "READY"


def evaluation_record(i: dict, groups: dict, t: dict, tree: str, e1_decision: str,
                      source: str) -> dict:
    st, rb = core.score_strict(t, groups), core.score_robust(t, groups)
    return self_hash({"task_id": i["task_id"], "diff_sha256": i["diff_sha256"],
                      "eval_identity": f"{i['task_id']}/{i['diff_sha256']}",
                      "label": "u_" + i["diff_sha256"][:12], "tree_sha": tree, "status": "DONE",
                      "groups": groups, "strict": st, "robust": rb,
                      "nodes": core.node_report(t, groups), "e1_decision": e1_decision,
                      "evaluation_source": source, "labels": i["labels"],
                      "sources": i["sources"], "evaluation_sha256": ""}, "evaluation_sha256")


def evaluate(max_evals: int, evaluate_fn: Callable[..., dict] | None = None,
             materialize_fn: Callable[..., tuple[str, str]] | None = None) -> int:
    bad = verify_generation_freeze()
    require(not bad, f"generation freeze drift {bad[:3]}")
    require(EVAL_PLAN.exists(), "evaluation plan missing")
    from scripts.wp2_m14a_evalcore import EvalInfraError
    from scripts.wp2_m14a_evalcore_e1 import evaluate_state_e1
    sets = eng_sets()
    ev = None
    done = 0
    for i in load(EVAL_PLAN)["items"]:
        if done >= max_evals:
            break
        p = unique_path(i["task_id"], i["diff_sha256"])
        stt = record_state(p, "evaluation_sha256")
        require(stt != "CORRUPT", f"corrupt evaluation record {p}")
        if stt == "VALID":
            continue
        t = sets[i["task_id"]]
        require(readiness_ok(i["task_id"]), f"task not ready {i['task_id']}")
        if i["diff_sha256"] == EMPTY_DIFF_SHA:
            ng = load(READY / i["task_id"] / "negative_groups.json")
            require(hash_ok(ng), "negative control record hash")
            rec = evaluation_record(i, ng["groups"], t, ng["tree_sha"], "ALL_JUNIT_PRESENT",
                                    "READINESS_NEGATIVE_CONTROL")
        else:
            if ev is None and (evaluate_fn is None or materialize_fn is None):
                ev = _ev()
            txt = (ROOT / i["source"]).parent.joinpath("final_diff.patch").read_text(
                encoding="utf-8")
            lab = "u_" + i["diff_sha256"][:12]
            mat = materialize_fn or ev.materialize
            efn = evaluate_fn or (lambda tk, lb, wt, diff, _ev=ev: evaluate_state_e1(
                _ev, tk, lb, wt, diff_text=diff,
                diag_path=ROOT / "evaluations/diagnostics" / tk / lb / "e1_diagnostics.json",
                parent_starts_ok=readiness_ok(tk)))
            try:
                wt, tree = mat(i["task_id"], lab, txt)
            except ValueError as exc:
                raise Stop(f"frozen APPLIED diff does not apply at evaluation: {exc}") from exc
            except (RuntimeError, subprocess.TimeoutExpired) as exc:
                raise Stop(f"evaluation infrastructure error: {exc}", EXIT_EVAL_INFRA) from exc
            try:
                er = efn(i["task_id"], lab, wt, txt)
            except (EvalInfraError, RuntimeError, subprocess.TimeoutExpired) as exc:
                raise Stop(f"evaluation infrastructure error: {exc}", EXIT_EVAL_INFRA) from exc
            rec = evaluation_record(i, er["groups"], t, tree, er.get("e1_decision", ""),
                                    "EVALUATED")
        write(p, rec)
        done += 1
        print(f"[m14r-eval] {i['task_id']} {i['diff_sha256'][:12]} -> strict="
              f"{rec['strict']['resolved']} robust={rec['robust']['resolved']} "
              f"f2p={rec['strict']['f2p_task']}", flush=True)
    print(f"EVAL_CHUNK evaluated={done}")
    return 0


def eval_complete() -> int:
    if not EVAL_PLAN.exists():
        return 1
    miss, corrupt = [], []
    for i in load(EVAL_PLAN)["items"]:
        s = record_state(unique_path(i["task_id"], i["diff_sha256"]), "evaluation_sha256")
        (corrupt if s == "CORRUPT" else miss if s == "ABSENT" else []).append(
            f"{i['task_id']}/{i['diff_sha256'][:12]}")
    if corrupt:
        print("EVAL_CORRUPT " + json.dumps(corrupt[:20]))
        return 1
    if miss:
        print("EVAL_INCOMPLETE " + json.dumps(miss[:20]))
        return 1
    print(f"EVAL_COMPLETE n_unique={load(EVAL_PLAN)['n_unique_identities']}")
    return 0


# ------------------------------------------------------------------ summary
def episode_tokens(e: dict) -> int:
    return sum(int(c.get("prompt_tokens", 0) or 0) + int(c.get("completion_tokens", 0) or 0)
               for c in e.get("calls", []))


def compute_summary() -> dict:
    sets = eng_sets()
    tasks = members()
    rows = []
    arch = orphan = 0
    for i in all_items():
        e = load(ep_dir(i) / "episode.json")
        t = sets[i["task_id"]]
        v = None
        if e["status"] == "APPLIED":
            p = unique_path(i["task_id"], e["diff_sha256"])
            v = load(p) if record_state(p, "evaluation_sha256") == "VALID" else None
            orphan += v is None
            if not set(e.get("edited_files", [])) <= set(e.get("editable_set", [])):
                arch += 1
        if e["status"] == "APPLIED" and v is None:
            lab = {"label": "UNEVALUATED", "detail": ""}
        else:
            lab = core.classify_episode(e["status"], e.get("diff_sha256") == EMPTY_DIFF_SHA,
                                        (v or {}).get("e1_decision"), t,
                                        (v or {}).get("groups"), (v or {}).get("strict"))
        rows.append({"task_id": i["task_id"], "arm": i["arm"], "variant": variant_of(i["label"]),
                     "replicate": i["replicate"], "label": i["label"], "status": e["status"],
                     "taxonomy": lab, "strict_resolved": bool(v and v["strict"]["resolved"]),
                     "robust_resolved": bool(v and v["robust"]["resolved"]),
                     "f2p_pass": bool(v and v["strict"]["f2p_task"] == "PASS"),
                     "tokens": episode_tokens(e),
                     "cost_usd": round(sum(float(c.get("cost_usd_actual", 0) or 0)
                                           for c in e.get("calls", [])), 7),
                     "static": e.get("static", {}).get("repair_status",
                                                       e.get("static", {}).get("reason", ""))})
    per: dict[str, dict] = {}
    per_task: dict[str, dict[str, int]] = {}
    for v in core.VARIANT_ORDER:
        g = [r for r in rows if r["variant"] == v and r["arm"] == "GOLD_HARD"]
        pl = [r for r in rows if r["variant"] == v and r["arm"] == "PLACEBO_HARD"]
        per_task[v] = {t: sum(r["robust_resolved"] for r in g if r["task_id"] == t) for t in tasks}
        per[v] = {"gold_n": len(g), "gold_applied": sum(r["status"] == "APPLIED" for r in g),
                  "gold_invalid": sum(r["status"] == "INVALID_AFTER_REPAIR" for r in g),
                  "gold_robust": sum(r["robust_resolved"] for r in g),
                  "gold_strict": sum(r["strict_resolved"] for r in g),
                  "gold_f2p": sum(r["f2p_pass"] for r in g),
                  "gold_mean_tokens": round(sum(r["tokens"] for r in g) / max(1, len(g)), 1),
                  "gold_cost_usd": round(sum(r["cost_usd"] for r in g), 7),
                  "tasks_any": sum(per_task[v][t] > 0 for t in tasks),
                  "placebo_n": len(pl), "placebo_robust": sum(r["robust_resolved"] for r in pl),
                  "placebo_strict": sum(r["strict_resolved"] for r in pl),
                  "taxonomy_gold": dict(Counter(r["taxonomy"]["label"] for r in g)),
                  "taxonomy_placebo": dict(Counter(r["taxonomy"]["label"] for r in pl)),
                  "static_outcomes_gold": dict(Counter(r["static"] for r in g))}
    instrument_ok = (not verify_generation_freeze() and eval_complete() == 0 and arch == 0
                     and orphan == 0)
    dec = core.decide(per, per_task, len(tasks), instrument_ok)
    strict_view = {v: dict(per[v], gold_robust=per[v]["gold_strict"],
                           placebo_robust=per[v]["placebo_strict"]) for v in per}
    strict_task = {v: {t: sum(r["strict_resolved"] for r in rows if r["variant"] == v and
                              r["arm"] == "GOLD_HARD" and r["task_id"] == t) for t in tasks}
                   for v in per}
    dec_strict = core.decide(strict_view, strict_task, len(tasks), instrument_ok)
    ledger = [json.loads(x) for x in LEDGER.read_text(encoding="utf-8").splitlines()
              if x.strip()] if LEDGER.exists() else []
    return {"artifact": "m14r_summary", "design_artifact_sha256": DESIGN_SHA,
            "token": dec["token"], "winner": dec["winner"], "decision": dec,
            "strict_endpoint_sensitivity": {"token": dec_strict["token"],
                                            "winner": dec_strict["winner"]},
            "n_tasks": len(tasks), "members": tasks, "per_variant": per,
            "per_task_gold_robust": per_task, "architecture_scope_violations": arch,
            "applied_without_evaluation": orphan, "rows": rows,
            "provider_reported_total_cost_usd": round(sum(float(r.get("cost_usd", 0) or 0)
                                                          for r in ledger), 7),
            "provider_reported_total_tokens": sum(int(r.get("prompt_tokens", 0) or 0)
                                                  + int(r.get("completion_tokens", 0) or 0)
                                                  for r in ledger),
            "auto_execution_of_M15": False,
            "mandatory_wording": ("M14R is a development probe on DEV_TRAIN_ENG only. It selects "
                                  "a generator variant for a future, separately frozen M15; it is "
                                  "not an RM-CSS-vs-Agent comparison and supports no selector "
                                  "claim. Pilot-A remains PILOT_A_GENERATOR_FLOOR_HOLD.")}


def summary() -> int:
    require(eval_complete() == 0, "evaluation incomplete")
    s = compute_summary()
    write(SUMMARY, self_hash(dict(s, artifact_sha256="")))
    lines = ["# WP2 M14R V1 result (DEV_TRAIN_ENG only)", "",
             f"Token: **{s['token']}**. Winner: **{s['winner']}**. Next: **{s['decision']['next']}**.",
             f"Strict-endpoint sensitivity: {s['strict_endpoint_sensitivity']}.", "",
             f"Member tasks: {s['n_tasks']}. Provider-reported spend: "
             f"${s['provider_reported_total_cost_usd']:.6f}.", "",
             "| Variant | GOLD n | APPLIED | INVALID | F2P | RESOLVED strict | RESOLVED robust | tasks>=1 | "
             "mean tokens | PLACEBO robust |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for v in core.VARIANT_ORDER:
        a = s["per_variant"][v]
        lines.append(f"| {v} | {a['gold_n']} | {a['gold_applied']} | {a['gold_invalid']} | "
                     f"{a['gold_f2p']} | {a['gold_strict']} | {a['gold_robust']} | "
                     f"{a['tasks_any']} | {a['gold_mean_tokens']} | {a['placebo_robust']} |")
    lines += ["", "Decision: " + json.dumps({k: s["decision"][k] for k in
                                             ("eligible", "checks", "thresholds")}, sort_keys=True),
              "", s["mandatory_wording"], ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("M14R_SUMMARY " + json.dumps({"token": s["token"], "winner": s["winner"]}))
    return 0


# ------------------------------------------------------------------ CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for x in ("guard", "pilot-a-taxonomy", "readiness-check", "membership", "auth-check",
              "doctor-offline", "doctor-paid", "freeze", "freeze-verify", "generation-complete",
              "static-complete", "generation-freeze", "generation-freeze-verify", "eval-plan",
              "eval-complete", "summary"):
        sp.add_parser(x)
    q = sp.add_parser("readiness")
    q.add_argument("--max-new", type=int, default=1)
    for x in ("generate", "static"):
        q = sp.add_parser(x)
        q.add_argument("--max-new", type=int, default=8)
        q.add_argument("--max-seconds", type=float, default=5400)
    q = sp.add_parser("evaluate")
    q.add_argument("--max-evals", type=int, default=4)
    a = ap.parse_args(argv)
    fns: dict[str, Callable[[], int]] = {
        "guard": guard, "pilot-a-taxonomy": pilot_a_taxonomy,
        "readiness": lambda: readiness(a.max_new), "readiness-check": readiness_check,
        "membership": membership, "auth-check": auth_check,
        "doctor-offline": lambda: doctor("offline"), "doctor-paid": lambda: doctor("paid"),
        "freeze": freeze, "freeze-verify": freeze_verify,
        "generate": lambda: generate(a.max_new, a.max_seconds),
        "generation-complete": generation_complete,
        "static": lambda: static(a.max_new, a.max_seconds), "static-complete": static_complete,
        "generation-freeze": generation_freeze,
        "generation-freeze-verify": generation_freeze_verify, "eval-plan": eval_plan,
        "evaluate": lambda: evaluate(a.max_evals), "eval-complete": eval_complete,
        "summary": summary}
    try:
        return fns[a.cmd]()
    except Stop as exc:
        print(f"M14R_STOP {a.cmd} code={exc.code}: {exc}")
        return exc.code
    except Exception as exc:
        if type(exc).__name__ == "EvalInfraError":
            print(f"M14R_EVAL_INFRA {a.cmd}: {exc}")
            return EXIT_EVAL_INFRA
        print(f"M14R_STEP_ERROR {a.cmd} {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return EXIT_INVARIANT


if __name__ == "__main__":
    raise SystemExit(main())
