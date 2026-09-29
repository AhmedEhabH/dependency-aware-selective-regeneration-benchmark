#!/usr/bin/env python3
"""WP2 M13B — Pilot design/readiness freeze: atomic steps (brain-authored; hash-verified).

ZERO API. ZERO Docker/WSL. ZERO paid generation. Every subcommand is ONE atomic step:
it reads declared inputs, checks invariants, writes EXACTLY one declared artifact under
research/wp2/pilot_v1_design/ and prints one token line. Exit 0 = PASS, 1 = STOP.

  python scripts/wp2_m13.py guard      -> m13_guard.json
  python scripts/wp2_m13.py usage      -> smoke_v22_usage_accounting.json
  python scripts/wp2_m13.py forensics  -> smoke_v22_failure_taxonomy.json
  python scripts/wp2_m13.py pool       -> pool_census.json
  python scripts/wp2_m13.py select     -> pilot_selection.json
  python scripts/wp2_m13.py design     -> pilot_design_freeze_v1.json (+ .md)
  python scripts/wp2_m13.py map        -> task_map_validation.json (+ TASK_MAP_M13_M16.md)
  python scripts/wp2_m13.py freeze     -> m13_freeze.json (+ PILOT_A_HUMAN_AUTH_TEMPLATE.json)
  python scripts/wp2_m13.py verify     -> m13_verify.json (independent re-derivation)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parent.parent
V22 = PROJECT / "research/wp2/e2e_smoke_eng_v22"
OUT = PROJECT / "research/wp2/pilot_v1_design"
V2 = PROJECT / "research/wp2/oracle_confirmation_linux_v2_2026-09-23"
SPLIT = V2 / "dev_split_v2_2026-09-23.json"
PER_TASK = V2 / "per_task_dev_v2.jsonl"
OOF_A = PROJECT / "research/memory-rescue-v2/final_oof_predictions_A.json"
AGENT_DEV_ENG = PROJECT / "research/wp2/e2e_smoke_eng_v1/scopes/agent_scopes_dev_eng.json"
AGENT_MAIN297 = PROJECT / "research/wp1b/main-297-2026-09-22/wp1b_agent_predictions.json"
TASK_MAP = PROJECT / "controller/task_map_m13_m16_v1.json"
PLAN = PROJECT / "controller/plan_m13_pilot_prep_v1.json"

ARMS = ("GOLD_HARD", "RMCSS_HARD", "AGENT_HARD", "PLACEBO_HARD")
TERMINAL = ("NO_SCOPE", "INVALID_AFTER_REPAIR", "APPLIED")
SALT = "wp2-pilot-v1-assay-holdout-2026-09-29"
N_A = N_B = 12
MIN_TASKS_PER_PILOT = 10

# ---- Smoke v2.2 closure facts (audited from the final LIGHT, 2026-09-29) ----
GEN_FREEZE_SHA = "29a4e1f1c45238673e3c70ec6a8e47b150c7185e233ffe8b4d72a824d6311778"
SMOKE_FREEZE_SHA = "4c41fdfee05bb3cdff951b2b393a5a9c557b55776fea4572c9c5b156708eeb87"
SOURCE_GUARDS = {  # normalized (CRLF->LF) sha256
    "ledger/spend_ledger_v22.jsonl":
        "fceaa0489b50d3d5202910793d1b8533e29edfe41188c8e894b3746bb7b5b9ae",
    "transport/attempts.jsonl":
        "f91405bb5c00ec20f4ef88bdd404d0e1d103a1971246c157dae81ee0f7c6d210",
    "smoke_v22_summary.json":
        "61cd27bc0e290bc5a66a353b9a17cfce58d4ab177bf59c38582323a2f5b02d25",
    "generation_freeze_v22.json":
        "77aedff2ab50f1cd7df2e67da53ee64845eb76d6b4741d5766f60e2a55e23d21",
    "evaluation_instrument_amendment_v221.json":
        "f46fd60781abb40f6a5281708832d65339cd7d129d5834977e3610109a23fa19",
    "smoke_v22_freeze.json":
        "4f18a66308394201bef4f5e092c72385c6ec68ed5302fd456fa2b6bbf44533b2",
    "evaluations/plan.json":
        "f54330674e3f72ab197ccb20f936598ba5802f91b564f7628eb6cd28c0733ab7",
}
USAGE_EXPECTED = {
    "ledger_rows": 77, "transport_attempts": 77,
    "provider_reported_prompt_tokens": 865733, "provider_reported_completion_tokens": 83796,
    "provider_reported_tokens_total": 949529, "provider_reported_tokens_main": 756153,
    "provider_reported_tokens_variance": 193376, "main_logical_tokens": 777379,
    "main_cache_reuse_tokens": 21226, "provider_reported_cost_usd": 0.2769655,
}
POOL_EXPECTED = {"assay_members": 80, "eligible": 26}
EXPECTED_A = ["saleor-rc-b497f8d82426", "saleor-rc-b410358502a1", "saleor-rc-a91ea48a60a7",
              "saleor-rc-bbba01a02725", "saleor-rc-6f37bd256e12", "saleor-rc-5b0e5206c5fd",
              "saleor-rc-d3847fa5f518", "saleor-rc-6459dd2d9135", "saleor-rc-012472eb8482",
              "saleor-rc-44c7495ca9bf", "saleor-rc-b14def73518c", "saleor-rc-a3c478408852"]
EXPECTED_B = ["saleor-rc-436f52ee3d0c", "saleor-rc-34511f977388", "saleor-rc-0a39d039049d",
              "saleor-rc-aca84e6c4252", "saleor-rc-60c8722863c1", "saleor-rc-9bf2755c9bd0",
              "saleor-rc-05df3bec57e2", "saleor-rc-9aa434eeefe7", "saleor-rc-99d963aed3e5",
              "saleor-rc-eacffa70e721", "saleor-rc-ded69f9c7097", "saleor-rc-d7fe298a4752"]

# Smoke-derived design inputs (from the audited forensics; used for gate calibration)
SMOKE_GOLD_RESOLVED, SMOKE_GOLD_TRIALS = 4, 20      # 3/14 main + 1/6 variance
SMOKE_GOLD_APPLIED, SMOKE_GOLD_APPLIED_TRIALS = 16, 20  # 11/14 main + 5/6 variance
SMOKE_USD_PER_EPISODE = 0.2769655 / 62
SMOKE_EVAL_MIN_PER_IDENTITY = 182.65 / 44           # P10 wall ≈ 3h02m for 44 identities
AGENT_USD_PER_TASK_REF = 0.370939 / 16              # frozen protocol-v3 on 16 DEV tasks


class Stop(Exception):
    pass


# ------------------------------------------------------------------ helpers
def norm_sha(p: Path) -> str:
    d = p.read_bytes()
    if b"\x00" not in d[:8192]:
        d = d.replace(b"\r\n", b"\n")
    return hashlib.sha256(d).hexdigest()


def json_sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode("utf-8")).hexdigest()


def load(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def write_json(name: str, payload: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    body = {k: v for k, v in payload.items() if k != "artifact_sha256"}
    payload = dict(body, artifact_sha256=json_sha(body))
    p = OUT / name
    p.write_text(json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
                 encoding="utf-8")
    return p


def write_text(name: str, text: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    p.write_text(text, encoding="utf-8", newline="\n")
    return p


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise Stop(msg)


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=PROJECT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def binom_tail_ge(n: int, p: float, k: int) -> float:
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def binom_cdf_le(n: int, p: float, k: int) -> float:
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))


# ------------------------------------------------------------------ A: guard
def build_guard(check_git: bool = True) -> dict:
    sm = load(V22 / "smoke_v22_summary.json")
    require(sm.get("token") == "E2E_SMOKE_V22_PIPELINE_VALID", f"smoke token {sm.get('token')}")
    require(sm.get("next") == "PILOT_DESIGN", f"smoke next {sm.get('next')}")
    st = load(V22 / "controller_state.json")
    require(st.get("stop") is None, f"smoke controller has a stop: {st.get('stop')}")
    bad = {k: v.get("status") for k, v in st["phases"].items() if v.get("status") != "PASS"}
    require(not bad and len(st["phases"]) == 13, f"smoke phases not all PASS: {bad}")
    gen = load(V22 / "generation_freeze_v22.json")
    require(gen.get("generation_freeze_sha256") == GEN_FREEZE_SHA, "generation freeze sha")
    require(load(V22 / "smoke_v22_freeze.json").get("freeze_sha256") == SMOKE_FREEZE_SHA,
            "smoke freeze sha")
    guards = {}
    for rel, want in SOURCE_GUARDS.items():
        got = norm_sha(V22 / rel)
        require(got == want, f"source guard changed: {rel}")
        guards[rel] = got
    for p in (SPLIT, PER_TASK, OOF_A, AGENT_DEV_ENG, AGENT_MAIN297):
        require(p.exists(), f"input missing: {p.relative_to(PROJECT)}")
    info: dict[str, Any] = {}
    if check_git:
        tags = [t for t in git("tag", "--list", "wp2-e2e-smoke-eng-v22-result-*").stdout.split()]
        require(len(tags) >= 1, "smoke result tag missing")
        tag = sorted(tags)[-1]
        commit = git("rev-parse", f"{tag}^{{commit}}").stdout.strip()
        anc = git("merge-base", "--is-ancestor", commit, "HEAD").returncode == 0
        require(anc, "smoke result commit is not an ancestor of HEAD")
        info = {"smoke_result_tag": tag, "smoke_result_commit": commit}
    return {"artifact": "m13_guard", "smoke_token": sm["token"], "smoke_next": sm["next"],
            "smoke_spend_usd": sm.get("spend_usd"), "generation_freeze_sha256": GEN_FREEZE_SHA,
            "smoke_freeze_sha256": SMOKE_FREEZE_SHA, "source_guards": guards, **info,
            "zero_api": True}


# ------------------------------------------------------------------ A: usage
def _call_tokens(c: dict) -> int:
    return int(c.get("prompt_tokens", 0) or 0) + int(c.get("completion_tokens", 0) or 0)


def _episode_usage(subdir: str) -> dict:
    tot = {"logical": 0, "reused": 0, "fresh": 0, "fresh_cost": 0.0, "reused_cost": 0.0}
    by_arm: dict[str, dict] = defaultdict(lambda: {"logical_tokens": 0, "cache_reuse_tokens": 0,
                                                   "fresh_tokens": 0, "fresh_cost_usd": 0.0,
                                                   "cache_reuse_nominal_usd": 0.0,
                                                   "fresh_calls": 0, "reused_calls": 0})
    for p in sorted((V22 / subdir).glob("*/*/episode.json")):
        e = load(p)
        arm = e.get("arm", "UNKNOWN")
        for c in e.get("calls", []):
            n, cost = _call_tokens(c), float(c.get("cost_usd_actual", 0.0) or 0.0)
            a = by_arm[arm]
            a["logical_tokens"] += n
            tot["logical"] += n
            if "reused" in str(c.get("kind", "")):
                a["cache_reuse_tokens"] += n
                a["cache_reuse_nominal_usd"] += cost
                a["reused_calls"] += 1
                tot["reused"] += n
                tot["reused_cost"] += cost
            else:
                a["fresh_tokens"] += n
                a["fresh_cost_usd"] += cost
                a["fresh_calls"] += 1
                tot["fresh"] += n
                tot["fresh_cost"] += cost
    for a in by_arm.values():
        a["fresh_cost_usd"] = round(a["fresh_cost_usd"], 7)
        a["cache_reuse_nominal_usd"] = round(a["cache_reuse_nominal_usd"], 7)
    return {"totals": tot, "by_arm": {k: by_arm[k] for k in sorted(by_arm)}}


def build_usage() -> dict:
    ledger = load_jsonl(V22 / "ledger/spend_ledger_v22.jsonl")
    attempts = load_jsonl(V22 / "transport/attempts.jsonl")
    pt = sum(int(r.get("prompt_tokens", 0) or 0) for r in ledger)
    ct = sum(int(r.get("completion_tokens", 0) or 0) for r in ledger)
    cost = round(sum(float(r.get("cost_usd", 0.0) or 0.0) for r in ledger), 7)
    classes = Counter(f"{r.get('http_status')}|{r.get('class')}" for r in attempts)
    main, var = _episode_usage("episodes"), _episode_usage("variance")
    got = {"ledger_rows": len(ledger), "transport_attempts": len(attempts),
           "provider_reported_prompt_tokens": pt, "provider_reported_completion_tokens": ct,
           "provider_reported_tokens_total": pt + ct,
           "provider_reported_tokens_main": main["totals"]["fresh"],
           "provider_reported_tokens_variance": var["totals"]["fresh"],
           "main_logical_tokens": main["totals"]["logical"],
           "main_cache_reuse_tokens": main["totals"]["reused"],
           "provider_reported_cost_usd": cost}
    diff = {k: (got[k], v) for k, v in USAGE_EXPECTED.items()
            if (abs(got[k] - v) > 1e-9 if isinstance(v, float) else got[k] != v)}
    require(not diff, f"usage differs from audited values: {diff}")
    require(got["provider_reported_tokens_main"] + got["provider_reported_tokens_variance"]
            == got["provider_reported_tokens_total"], "ledger vs fresh-call tokens disagree")
    require(dict(classes) == {"200|SUCCESS": 77}, f"transport classes {dict(classes)}")
    return {
        "artifact": "smoke_v22_usage_accounting",
        "definitions": {
            "provider_reported_tokens": "prompt+completion tokens returned by the provider on "
                                        "fresh successful calls (durable spend ledger)",
            "logical_tokens": "tokens represented in episode call records, INCLUDING "
                              "identical-request cache reuse (not billed again)",
            "cache_reuse_tokens": "logical tokens served from the response cache; never billed",
            "hidden_provider_compute": "NOT_MEASURED (qwen3-coder reports no reasoning tokens)",
        },
        "authoritative": got, "transport_classes": dict(classes),
        "main_by_arm": main["by_arm"], "variance_by_arm": var["by_arm"],
        "erratum_smoke_v22_summary": {
            "field": "per_arm.billed_tokens / per_arm.usd",
            "issue": "copied logical tokens and nominal cached-call cost (v2.1 summarizer "
                     "behavior); AGENT_HARD includes 21,226 cache-reused tokens",
            "correct_source": "main_by_arm.fresh_tokens / fresh_cost_usd in this artifact",
            "historical_summary_modified": False,
        },
    }


# ------------------------------------------------------------------ A: forensics
def _err_type(s: Any) -> str:
    return str(s).split(":", 1)[0].split(" ", 1)[0]


def build_forensics() -> dict:
    ev = {}
    for p in (V22 / "evaluations/unique").glob("*/*/evaluation.json"):
        r = load(p)
        ev[(r["task_id"], r["diff_sha256"])] = r
    bc = {}
    for sub in ("episodes", "variance"):
        for p in (V22 / "evaluations" / sub).glob("*/*/evaluation.json"):
            r = load(p)
            bc[(sub, r["task_id"], r["label"])] = r
    per_arm = {}
    for arm in ARMS:
        status: Counter = Counter()
        errors: Counter = Counter()
        rec = {"invalid_tasks": [], "no_scope_tasks": [], "repair_used": 0, "resolved": 0,
               "f2p": 0, "p2p_s": 0, "p2p_u200": 0, "applied_without_evaluation": 0}
        for p in sorted((V22 / "episodes").glob(f"*/{arm}/episode.json")):
            e = load(p)
            tid, st = e["task_id"], e["status"]
            status[st] += 1
            rec["repair_used"] += int(bool(e.get("repair_used")))
            for ph in ("initial", "repair"):
                for er in e.get("validation", {}).get(ph, []) or []:
                    errors[_err_type(er)] += 1
            if st == "INVALID_AFTER_REPAIR":
                rec["invalid_tasks"].append(tid)
            if st == "NO_SCOPE":
                rec["no_scope_tasks"].append(tid)
            r = ev.get((tid, e.get("diff_sha256", ""))) if st == "APPLIED" \
                else bc.get(("episodes", tid, arm))
            if st == "APPLIED" and not r:
                rec["applied_without_evaluation"] += 1
            if r:
                rec["resolved"] += int(bool(r.get("resolved")))
                rec["f2p"] += int(r.get("f2p_task") == "PASS")
                rec["p2p_s"] += int(r.get("p2p_s_task") in ("PASS", "PASS_BY_CONSTRUCTION"))
                rec["p2p_u200"] += int(r.get("p2p_u200_task") in ("PASS", "PASS_BY_CONSTRUCTION"))
        per_arm[arm] = {"status": dict(status), "error_counts": dict(errors), **rec}
    variance = []
    for p in sorted((V22 / "variance").glob("*/*/episode.json")):
        e = load(p)
        tid, label = e["task_id"], p.parent.name
        m = load(V22 / "episodes" / tid / "GOLD_HARD" / "episode.json")
        r = ev.get((tid, e.get("diff_sha256", ""))) if e["status"] == "APPLIED" \
            else bc.get(("variance", tid, label), {})
        r = r or {}
        variance.append({"task_id": tid, "replicate": label, "main_status": m["status"],
                         "rep_status": e["status"], "same_status": m["status"] == e["status"],
                         "same_diff": bool(m.get("diff_sha256"))
                         and m.get("diff_sha256") == e.get("diff_sha256"),
                         "resolved": bool(r.get("resolved")), "f2p": r.get("f2p_task")})
    vs = {"n": len(variance),
          "applied": sum(x["rep_status"] == "APPLIED" for x in variance),
          "same_status": sum(x["same_status"] for x in variance),
          "same_diff": sum(x["same_diff"] for x in variance),
          "resolved": sum(x["resolved"] for x in variance)}
    g, rm = per_arm["GOLD_HARD"], per_arm["RMCSS_HARD"]
    require(g["status"] == {"APPLIED": 11, "INVALID_AFTER_REPAIR": 3}, f"GOLD {g['status']}")
    require(g["resolved"] == 3 and g["f2p"] == 4, "GOLD resolved/f2p")
    require(rm["status"] == {"APPLIED": 11, "INVALID_AFTER_REPAIR": 2, "NO_SCOPE": 1},
            f"RMCSS {rm['status']}")
    require(rm["resolved"] == 2, "RMCSS resolved")
    require(vs == {"n": 6, "applied": 5, "same_status": 1, "same_diff": 0, "resolved": 1},
            f"variance {vs}")
    require(all(a["applied_without_evaluation"] == 0 for a in per_arm.values()), "orphans")
    invalid_err = sum(v.get("SEARCH_ERROR", 0) for v in (a["error_counts"] for a in per_arm.values()))
    return {"artifact": "smoke_v22_failure_taxonomy", "per_arm": per_arm,
            "variance": dict(vs, records=variance),
            "search_error_total": invalid_err,
            "readings": [
                "INVALID_AFTER_REPAIR is a terminal outcome: the SEARCH block did not match the "
                "file text even after one repair (edit-interface failure, not environment).",
                "GOLD failures show the generator/interface is a bottleneck even with oracle scope.",
                "Variance probe: generation is highly stochastic (0/6 identical diffs).",
                "Smoke is DEV_TRAIN_ENG pipeline validation; no RM-CSS-vs-Agent claim."]}


# ------------------------------------------------------------------ A: pool census
def _agent_task_sets() -> dict[str, set[str]]:
    a = load(AGENT_DEV_ENG)
    b = load(AGENT_MAIN297)
    return {"agent_dev_eng": set(a.get("per_task", {})), "agent_main297": set(b.get("per_task", {}))}


def build_pool() -> dict:
    split = load(SPLIT)["membership"]
    assay, val, eng = (set(split["DEV_TRAIN_ASSAY_HOLDOUT"]), set(split["DEV_VALIDATION"]),
                       set(split["DEV_TRAIN_ENG"]))
    require(not (assay & val) and not (assay & eng), "split roles overlap")
    rows = {r["task_id"]: r for r in load_jsonl(PER_TASK)}
    oof = load(OOF_A)
    agents = _agent_task_sets()
    census = []
    for tid in sorted(assay):
        r = rows.get(tid)
        e = (r or {}).get("eligibility", {})
        eligible = bool(r) and e.get("PRIMARY_BEHAVIORAL_F2P_ELIGIBLE") is True \
            and e.get("environment_valid") is True
        census.append({"task_id": tid, "in_per_task": bool(r),
                       "classification": (r or {}).get("classification"),
                       "era_key": (r or {}).get("era_key", "UNKNOWN"),
                       "n_behavioral_f2p": int(e.get("n_behavioral_f2p", 0) or 0),
                       "eligible": eligible,
                       "rmcss_oof_nonempty": bool(oof.get(tid)),
                       "agent_selection_available": any(tid in s for s in agents.values())})
    elig = [c for c in census if c["eligible"]]
    require(len(assay) == POOL_EXPECTED["assay_members"], f"assay members {len(assay)}")
    require(len(elig) == POOL_EXPECTED["eligible"], f"eligible {len(elig)}")
    return {"artifact": "pool_census", "assay_members": len(assay),
            "in_per_task": sum(c["in_per_task"] for c in census), "eligible": len(elig),
            "eligible_era_counts": dict(Counter(c["era_key"] for c in elig)),
            "eligible_with_rmcss_oof": sum(c["rmcss_oof_nonempty"] for c in elig),
            "eligible_with_agent_selection": sum(c["agent_selection_available"] for c in elig),
            "finding_agent": "No frozen Agent selection exists for any eligible holdout task; "
                             "M15 must run the frozen protocol-v3 Agent localization (paid) "
                             "before Pilot-B generation.",
            "source_sha256": {"split": norm_sha(SPLIT), "per_task": norm_sha(PER_TASK),
                              "oof_a": norm_sha(OOF_A), "agent_dev_eng": norm_sha(AGENT_DEV_ENG),
                              "agent_main297": norm_sha(AGENT_MAIN297)},
            "tasks": census}


# ------------------------------------------------------------------ A: selection
def rank(tid: str) -> str:
    return hashlib.sha256(f"{SALT}|{tid}".encode()).hexdigest()


def largest_remainder_quota(counts: dict[str, int], total: int) -> dict[str, int]:
    n = sum(counts.values())
    if n < total:
        raise Stop(f"eligible={n} < requested={total}")
    exact = {k: total * v / n for k, v in counts.items()}
    q = {k: int(exact[k]) for k in counts}
    for k in sorted(counts, key=lambda k: (-(exact[k] - q[k]), k))[:total - sum(q.values())]:
        q[k] += 1
    return q


def select_from(eligible: list[dict]) -> dict:
    by_era = Counter(x["era_key"] for x in eligible)
    quota = largest_remainder_quota(dict(by_era), N_A + N_B)
    chosen, reserve = [], []
    for era in sorted(by_era):
        pool = sorted([x for x in eligible if x["era_key"] == era],
                      key=lambda x: (rank(x["task_id"]), x["task_id"]))
        chosen += pool[:quota[era]]
        reserve += pool[quota[era]:]
    chosen.sort(key=lambda x: (rank(x["task_id"]), x["task_id"]))
    reserve.sort(key=lambda x: (rank(x["task_id"]), x["task_id"]))
    a: list[dict] = []
    b: list[dict] = []
    ea: Counter = Counter()
    eb: Counter = Counter()
    for x in chosen:
        e = x["era_key"]
        if len(a) >= N_A:
            dest = b
        elif len(b) >= N_B:
            dest = a
        elif ea[e] < eb[e]:
            dest = a
        elif eb[e] < ea[e]:
            dest = b
        else:
            dest = a if len(a) <= len(b) else b
        dest.append(x)
        (ea if dest is a else eb)[e] += 1
    return {"quota": quota, "A": [x["task_id"] for x in a], "B": [x["task_id"] for x in b],
            "reserve": [x["task_id"] for x in reserve]}


def finalize_after_readiness(a0: list[str], b0: list[str], reserve: list[str],
                             ready: set[str]) -> dict:
    """Frozen replacement rule, applied in M14A.S0 BEFORE any paid generation.

    1. Drop not-ready tasks from A and B (order preserved).
    2. Fill from the ready reserve in reserve order; each reserve task goes to the
       smaller of A/B (A on a tie) while that list is < 12.
    3. If A and B are both 12 -> FULL. Otherwise n = min(|A|, |B|); both lists are
       truncated to their first n tasks (dropped tasks are recorded, never used).
       n >= 10 -> REDUCED_<n>; n < 10 -> POOL_INSUFFICIENT (human decision; no paid run).
    """
    a = [t for t in a0 if t in ready]
    b = [t for t in b0 if t in ready]
    used = []
    for t in reserve:
        if t not in ready or (len(a) >= N_A and len(b) >= N_B):
            continue
        dest = a if (len(a) <= len(b) and len(a) < N_A) or len(b) >= N_B else b
        dest.append(t)
        used.append(t)
    if len(a) == N_A and len(b) == N_B:
        return {"verdict": "FULL", "A": a, "B": b, "reserve_used": used, "dropped": []}
    n = min(len(a), len(b))
    dropped = a[n:] + b[n:]
    verdict = f"REDUCED_{n}" if n >= MIN_TASKS_PER_PILOT else "POOL_INSUFFICIENT"
    return {"verdict": verdict, "A": a[:n], "B": b[:n], "reserve_used": used, "dropped": dropped}


def build_selection() -> dict:
    pool = load(OUT / "pool_census.json")
    elig = [c for c in pool["tasks"] if c["eligible"]]
    s = select_from(elig)
    require(s["A"] == EXPECTED_A and s["B"] == EXPECTED_B,
            "selection differs from the audited deterministic selection")
    split = load(SPLIT)["membership"]
    assay = set(split["DEV_TRAIN_ASSAY_HOLDOUT"])
    protected = set(split["DEV_VALIDATION"]) | set(split["DEV_TRAIN_ENG"])
    ids = set(s["A"]) | set(s["B"]) | set(s["reserve"])
    require(not (set(s["A"]) & set(s["B"])), "A/B overlap")
    require(ids <= assay and not (ids & protected), "selection outside ASSAY_HOLDOUT")
    oof = load(OOF_A)
    require(all(oof.get(t) for t in s["B"]), "a Pilot-B task lacks an RM-CSS prediction")
    return {"artifact": "pilot_selection", "salt": SALT,
            "semantics": "pre-E2E, deterministic; ASSAY_HOLDOUT; primary behavioral F2P "
                         "eligible and environment_valid; era-stratified largest remainder; "
                         "SHA-256 rank",
            "selected_quota_by_era": s["quota"], "pilot_a_tasks": s["A"],
            "pilot_b_tasks": s["B"], "reserve_order": s["reserve"],
            "replacement_rule": finalize_after_readiness.__doc__.strip(),
            "replacement_rule_examples": {
                "all_ready": finalize_after_readiness(s["A"], s["B"], s["reserve"],
                                                      set(ids))["verdict"],
                "three_not_ready": finalize_after_readiness(
                    s["A"], s["B"], s["reserve"], set(ids) - set(s["A"][:3]))["verdict"],
            },
            "rmcss_oof_coverage": {
                "pilot_a": sum(bool(oof.get(t)) for t in s["A"]),
                "pilot_b": sum(bool(oof.get(t)) for t in s["B"]),
                "reserve": sum(bool(oof.get(t)) for t in s["reserve"]),
                "rule": "Pilot-A does not use RM-CSS. For Pilot-B an absent/empty RM-CSS "
                        "prediction is the method's own outcome (NO_SCOPE), never a stop"},
            "protected_assertions": {"DEV_VALIDATION_touched": False,
                                     "DEV_TRAIN_ENG_reused": False,
                                     "MAIN_touched": False, "pilot_a_b_disjoint": True},
            "pool_census_sha256": pool["artifact_sha256"]}


# ------------------------------------------------------------------ A: design
def gates_for(n_tasks: int) -> dict[str, int]:
    """Pilot-A thresholds for n_tasks x 2 replicates (24 episodes/arm at n=12)."""
    e = 2 * n_tasks
    return {"episodes_per_arm": e,
            "A2_gold_applied_min": math.ceil(14 * e / 24),
            "A3_gold_resolved_min": math.ceil(3 * e / 24),
            "A4_placebo_resolved_max": max(1, math.floor(1 * e / 24)),
            "A5_gold_minus_placebo_min": math.ceil(2 * e / 24)}


def gate_pass_probabilities(n_tasks: int = 12) -> dict[str, Any]:
    g = gates_for(n_tasks)
    e = g["episodes_per_arm"]
    out = {}
    for p in (0.15, 0.20, 0.25):
        out[f"P(A3 pass | gold_rate={p})"] = round(binom_tail_ge(e, p, g["A3_gold_resolved_min"]), 3)
    old = round(binom_tail_ge(24, 0.20, 4), 3)
    out["P(A2 pass | gold_applied_rate=0.80)"] = round(binom_tail_ge(e, 0.80, g["A2_gold_applied_min"]), 3)
    out["P(A4 pass | placebo_rate=0.03)"] = round(binom_cdf_le(e, 0.03, g["A4_placebo_resolved_max"]), 3)
    out["reference_old_gate_P(>=4/24 | 0.20)"] = old
    out["note"] = ("binomial, episodes treated as independent (optimistic: two replicates per "
                   "task are correlated); used only to avoid gates that fail by chance")
    return out


def build_design() -> dict:
    sel = load(OUT / "pilot_selection.json")
    use = load(OUT / "smoke_v22_usage_accounting.json")
    fx = load(OUT / "smoke_v22_failure_taxonomy.json")
    g12 = gates_for(12)
    eps_a, eps_b = 2 * 2 * 12, 3 * 2 * 12
    return {
        "artifact": "pilot_design_freeze_v1",
        "status": "DESIGN_FROZEN_ZERO_API_NOT_AUTHORIZED_FOR_PAID_EXECUTION",
        "selection_sha256": sel["artifact_sha256"],
        "pilot_a": {
            "id": "M14A", "purpose": "Gold-vs-Placebo assay sensitivity + generation variance "
                                     "calibration on the protected holdout; NOT a selector comparison",
            "tasks": sel["pilot_a_tasks"], "arms": ["GOLD_HARD", "PLACEBO_HARD"],
            "replicates": ["r1", "r2"], "planned_episodes": eps_a,
            "replicate_cache_policy": "one response cache per replicate label; no reuse across "
                                      "replicates or arms",
            "interface": "UNCHANGED from Smoke v2.2 (SEARCH/REPLACE, 1 repair, qwen/qwen3-coder "
                         "via deepinfra/turbo, allow_fallbacks=false, temperature 0, 8192 tokens)",
            "order": ["S0 zero-API V3.1 oracle readiness of ALL 26 eligible tasks (A, B and "
                      "reserve) + frozen replacement rule", "S1 freeze", "S2 generation (all 48)",
                      "S3 generation freeze + push", "S4 evaluation (task_id, full diff sha)",
                      "S5 summary + gates"],
            "gates_n12": g12,
            "gate_rule_for_reduced_n": "gates_for(n) in scripts/wp2_m13.py (scaled from 24)",
            "gates_text": {
                "A0_instrument": "evidence integrity; zero protected-pool violations; zero "
                                 "applied_without_evaluation; zero architecture-scope violations",
                "A1_completion": "100% planned episodes terminal (provider outages are pending, "
                                 "never terminal); evaluation complete",
                "A2": f"GOLD APPLIED >= {g12['A2_gold_applied_min']}/24",
                "A3": f"GOLD RESOLVED >= {g12['A3_gold_resolved_min']}/24",
                "A4": f"PLACEBO RESOLVED <= {g12['A4_placebo_resolved_max']}/24",
                "A5": f"GOLD - PLACEBO RESOLVED >= {g12['A5_gold_minus_placebo_min']} and "
                      "#tasks(gold>placebo) >= #tasks(placebo>gold)"},
            "gate_calibration": gate_pass_probabilities(12),
            "outcome_tokens": {
                "PILOT_A_PASS": "A0..A5 pass -> M15",
                "PILOT_A_INSTRUMENT_FIX": "A0 or A1 fail -> instrument repair on ENG/synthetic "
                                          "evidence; no new protected outcomes",
                "PILOT_A_PLACEBO_LEAK_REVIEW": "A4 fail -> HUMAN_DECISION",
                "PILOT_A_GENERATOR_FLOOR_HOLD": "A2/A3/A5 fail -> HUMAN_DECISION (options: M14R "
                                                "interface probe on DEV_TRAIN_ENG only; never "
                                                "consume Pilot-B tasks)"},
            "diagnostics_recorded": ["SEARCH_ERROR / PARSE_ERROR rates", "repair success rate",
                                     "replicate endpoint-tuple agreement", "diff agreement"],
            "budget": {"expected_generation_usd": round(eps_a * SMOKE_USD_PER_EPISODE, 3),
                       "ceiling_usd": 1.00,
                       "expected_evaluation_hours": round(eps_a * SMOKE_EVAL_MIN_PER_IDENTITY / 60, 1)},
        },
        "pilot_b": {
            "id": "M15", "purpose": "selector E2E behavior and run-to-run stability; NOT a "
                                    "final ranking and NOT a significance test",
            "tasks": sel["pilot_b_tasks"], "arms": ["RMCSS_HARD", "AGENT_HARD", "GOLD_HARD"],
            "gold_role": "within-block reference ceiling on the same tasks",
            "replicates": ["r1", "r2"], "planned_episodes": eps_b,
            "agent_localization": {
                "required": True,
                "reason": "no frozen Agent selection exists for any holdout task (pool census)",
                "protocol": "research/wp1b/wp1b_frozen_agent_protocol_v3.json (unchanged)",
                "runs": "one fresh Agent localization per task per replicate (r1, r2); "
                        "replicate r uses Agent run r (selector stochasticity is part of the "
                        "method)",
                "expected_usd": round(24 * AGENT_USD_PER_TASK_REF, 3),
                "order": "all Agent localizations frozen and pushed BEFORE any Pilot-B generation"},
            "rmcss_selection": {"source": "final_oof_predictions_A.json (deterministic; same "
                                          "scope for r1 and r2)",
                                "coverage_at_design": f"{sel['rmcss_oof_coverage']['pilot_b']}/12 "
                                                      "non-empty (reserve "
                                                      f"{sel['rmcss_oof_coverage']['reserve']}/2)",
                                "empty_prediction_rule": "NO_SCOPE outcome of the method; "
                                                         "never a stop"},
            "cost_boundary": {
                "headline": "selector + generation + repair, provider-reported (ledger)",
                "agent_selector_cost": "actual ledger of the M15 Agent localization runs",
                "rmcss_selector_cost": "per-task WP-1 records if present; otherwise the frozen "
                                       "MAIN_297 per-task mean, labeled IMPUTED_FROM_MAIN297",
                "decomposition": "generation-only and repair-only reported separately"},
            "budget": {"expected_generation_usd": round(eps_b * SMOKE_USD_PER_EPISODE, 3),
                       "expected_agent_usd": round(24 * AGENT_USD_PER_TASK_REF, 3),
                       "ceiling_usd": 2.50,
                       "expected_evaluation_hours": round(eps_b * SMOKE_EVAL_MIN_PER_IDENTITY / 60, 1)},
            "outputs": ["per-arm APPLIED/F2P/P2P-S/P2P-U200/RESOLVED per replicate",
                        "replicate endpoint-tuple agreement per arm",
                        "end-to-end cost per arm (headline) + decomposition"],
            "claim_rule": "descriptive only; no superiority/non-inferiority claim",
        },
        "research_replicate_rule_after_pilot_b": {
            "minimum": 2, "never_reduce_to_1": True,
            "escalate_to_3_if": "for RM-CSS or Agent: endpoint-tuple agreement across r1/r2 "
                                "< 0.75 OR |resolved_rate_r1 - resolved_rate_r2| > 0.10",
            "endpoint_tuple": ["terminal_status", "f2p_task", "p2p_s_task", "p2p_u200_task",
                               "resolved"]},
        "cost_accounting_contract": {
            "provider_reported_tokens": "fresh successful calls only (ledger)",
            "logical_tokens": "may include cache reuse; never reported as billed",
            "per_arm_summary": "must use fresh-call fields (fixes the Smoke v2.2 summary erratum)"},
        "smoke_inputs": {"provider_reported_tokens": use["authoritative"]["provider_reported_tokens_total"],
                         "provider_reported_cost_usd": use["authoritative"]["provider_reported_cost_usd"],
                         "gold": {k: fx["per_arm"]["GOLD_HARD"][k] for k in ("status", "resolved", "f2p")},
                         "variance": {k: v for k, v in fx["variance"].items() if k != "records"}},
        "forbidden": ["DEV_VALIDATION E2E outcomes", "DEV_TRAIN_ENG reuse as pilot evidence",
                      "MAIN generation", "task replacement after any E2E outcome",
                      "interface/model/provider change inside a pilot",
                      "target patch or target tests in the generator prompt"],
    }


def design_md(d: dict) -> str:
    a, b = d["pilot_a"], d["pilot_b"]
    g = a["gates_text"]
    lines = ["# WP2 Pilot Design Freeze V1 (M13B)", "",
             f"Status: **{d['status']}**", "",
             "## Pilot-A (M14A): Gold vs Placebo assay calibration", "",
             f"- Tasks (12, protected ASSAY_HOLDOUT): {', '.join(t[-12:] for t in a['tasks'])}",
             "- Arms: GOLD_HARD, PLACEBO_HARD; replicates r1, r2; 48 episodes.",
             f"- Interface: {a['interface']}.",
             "- S0: zero-API V3.1 oracle readiness of all 26 eligible tasks, then the frozen "
             "replacement rule, before any paid call.", "",
             "| Gate | Rule |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in g.items()]
    lines += ["", "Gate calibration (binomial): " + json.dumps(a["gate_calibration"]), "",
              "Outcome tokens:", ""]
    lines += [f"- `{k}`: {v}" for k, v in a["outcome_tokens"].items()]
    lines += ["", f"Budget: expected ${a['budget']['expected_generation_usd']}, ceiling "
              f"${a['budget']['ceiling_usd']}, evaluation ≈ {a['budget']['expected_evaluation_hours']} h.",
              "", "## Pilot-B (M15): selector behavior (descriptive)", "",
              f"- Tasks (12, disjoint): {', '.join(t[-12:] for t in b['tasks'])}",
              "- Arms: RMCSS_HARD, AGENT_HARD, GOLD_HARD (reference); r1, r2; 72 episodes.",
              f"- Agent localization REQUIRED first: {b['agent_localization']['runs']}; "
              f"expected ${b['agent_localization']['expected_usd']}.",
              f"- Cost boundary: {b['cost_boundary']['headline']}.",
              f"- Budget ceiling ${b['budget']['ceiling_usd']}; evaluation ≈ "
              f"{b['budget']['expected_evaluation_hours']} h.",
              "", "## Research replicate rule", "",
              f"- {d['research_replicate_rule_after_pilot_b']['escalate_to_3_if']}; never 1.", ""]
    return "\n".join(lines)


# ------------------------------------------------------------------ A: task map
MAP_REQUIRED = ("id", "title", "executor", "inputs", "outputs", "checks", "on_pass", "on_fail")


def validate_task_map(m: dict, plan: dict | None = None) -> list[str]:
    bad: list[str] = []
    ids: list[str] = []
    for t in m.get("tasks", []):
        for s in t.get("subtasks", []):
            for a in s.get("atomics", []):
                ids.append(a.get("id", ""))
                for f in MAP_REQUIRED:
                    if f not in a:
                        bad.append(f"{a.get('id')} missing {f}")
                of = a.get("on_fail", {})
                if not isinstance(of, dict) or "token" not in of or "reaction" not in of:
                    bad.append(f"{a.get('id')} on_fail needs token+reaction")
    if len(ids) != len(set(ids)):
        bad.append("duplicate atomic ids")
    known = set(ids) | {t["id"] for t in m.get("tasks", [])} | set(m.get("terminal_states", []))
    for t in m.get("tasks", []):
        for s in t.get("subtasks", []):
            for a in s.get("atomics", []):
                nxt = a.get("on_pass")
                if nxt not in known:
                    bad.append(f"{a.get('id')} on_pass -> unknown {nxt}")
    if plan is not None:
        m13 = [a["id"] for t in m["tasks"] if t["id"] == "M13"
               for s in t["subtasks"] for a in s["atomics"] if a["executor"] == "CONTROLLER"]
        phases = [p["id"] for p in plan["phases"]]
        if m13 != phases:
            bad.append(f"M13 controller atomics != plan phases: {m13} vs {phases}")
    return bad


def map_md(m: dict) -> str:
    lines = [f"# {m['title']}", "", m["transition_contract"], ""]
    for t in m["tasks"]:
        lines += [f"## {t['id']} — {t['title']}  ({t['status']})", "", t.get("goal", ""), ""]
        for s in t["subtasks"]:
            lines += [f"### {s['id']} — {s['title']}", "",
                      "| Atomic | Executor | Does | Output | On PASS | On FAIL |",
                      "|---|---|---|---|---|---|"]
            for a in s["atomics"]:
                of = a["on_fail"]
                lines.append(f"| {a['id']} | {a['executor']} | {a['title']} | "
                             f"{', '.join(a['outputs']) or '—'} | {a['on_pass']} | "
                             f"{of['token']} ({of['reaction']}) |")
            lines.append("")
    return "\n".join(lines)


def build_map() -> dict:
    m = load(TASK_MAP)
    plan = load(PLAN) if PLAN.exists() else None
    bad = validate_task_map(m, plan)
    require(not bad, f"task map invalid: {bad[:10]}")
    n = sum(len(s["atomics"]) for t in m["tasks"] for s in t["subtasks"])
    return {"artifact": "task_map_validation", "task_map_sha256": norm_sha(TASK_MAP),
            "plan_sha256": norm_sha(PLAN) if PLAN.exists() else None,
            "tasks": [t["id"] for t in m["tasks"]], "n_atomics": n, "valid": True}


# ------------------------------------------------------------------ A: freeze / verify
FROZEN_ARTIFACTS = ("m13_guard.json", "smoke_v22_usage_accounting.json",
                    "smoke_v22_failure_taxonomy.json", "pool_census.json",
                    "pilot_selection.json", "pilot_design_freeze_v1.json",
                    "PILOT_DESIGN_FREEZE_V1.md", "task_map_validation.json",
                    "TASK_MAP_M13_M16.md")


def build_freeze() -> tuple[dict, dict]:
    files = {}
    for name in FROZEN_ARTIFACTS:
        p = OUT / name
        require(p.exists(), f"artifact missing: {name}")
        files[f"research/wp2/pilot_v1_design/{name}"] = norm_sha(p)
    files["controller/task_map_m13_m16_v1.json"] = norm_sha(TASK_MAP)
    design = load(OUT / "pilot_design_freeze_v1.json")
    auth = {"artifact": "pilot_a_human_authorization_template", "authorized": False,
            "approval_token_required": "I_AUTHORIZE_WP2_PILOT_A_V1=YES",
            "authorized_by": "", "authorized_utc": "",
            "design_artifact_sha256": design["artifact_sha256"],
            "max_generation_spend_usd": design["pilot_a"]["budget"]["ceiling_usd"],
            "model": "qwen/qwen3-coder", "provider": "deepinfra/turbo",
            "allow_fallbacks": False,
            "note": "M14A kit refuses to start unless this file is filled by the human, "
                    "committed, and the design hash matches."}
    freeze = {"artifact": "m13_freeze", "files": files,
              "design_artifact_sha256": design["artifact_sha256"]}
    return freeze, auth


def build_verify() -> dict:
    checks = {}
    checks["guard"] = build_guard(check_git=False)["source_guards"] == SOURCE_GUARDS
    for name, fn in (("smoke_v22_usage_accounting.json", build_usage),
                     ("smoke_v22_failure_taxonomy.json", build_forensics),
                     ("pool_census.json", build_pool), ("pilot_selection.json", build_selection),
                     ("pilot_design_freeze_v1.json", build_design),
                     ("task_map_validation.json", build_map)):
        on_disk = load(OUT / name)
        body = {k: v for k, v in on_disk.items() if k != "artifact_sha256"}
        fresh = fn()
        checks[name] = json_sha(body) == on_disk["artifact_sha256"] and fresh == body
    fz = load(OUT / "m13_freeze.json")
    checks["freeze_hashes"] = all(norm_sha(PROJECT / rel) == h for rel, h in fz["files"].items())
    auth = load(OUT / "PILOT_A_HUMAN_AUTH_TEMPLATE.json")
    checks["auth_unfilled_and_bound"] = (auth["authorized"] is False and
                                         auth["design_artifact_sha256"] == fz["design_artifact_sha256"])
    require(all(checks.values()), f"verify failed: {[k for k, v in checks.items() if not v]}")
    return {"artifact": "m13_verify", "checks": checks, "zero_api": True,
            "next": "M14A_KIT_BUILD (brain) + human authorization"}


# ------------------------------------------------------------------ CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["guard", "usage", "forensics", "pool", "select", "design",
                                     "map", "freeze", "verify"])
    a = ap.parse_args(argv)
    try:
        if a.step == "guard":
            p = write_json("m13_guard.json", build_guard())
        elif a.step == "usage":
            p = write_json("smoke_v22_usage_accounting.json", build_usage())
        elif a.step == "forensics":
            p = write_json("smoke_v22_failure_taxonomy.json", build_forensics())
        elif a.step == "pool":
            p = write_json("pool_census.json", build_pool())
        elif a.step == "select":
            p = write_json("pilot_selection.json", build_selection())
        elif a.step == "design":
            p = write_json("pilot_design_freeze_v1.json", build_design())
            write_text("PILOT_DESIGN_FREEZE_V1.md", design_md(load(p)))
        elif a.step == "map":
            p = write_json("task_map_validation.json", build_map())
            write_text("TASK_MAP_M13_M16.md", map_md(load(TASK_MAP)))
        elif a.step == "freeze":
            freeze, auth = build_freeze()
            write_json("PILOT_A_HUMAN_AUTH_TEMPLATE.json", auth)
            freeze["files"]["research/wp2/pilot_v1_design/PILOT_A_HUMAN_AUTH_TEMPLATE.json"] = \
                norm_sha(OUT / "PILOT_A_HUMAN_AUTH_TEMPLATE.json")
            p = write_json("m13_freeze.json", freeze)
        else:
            p = write_json("m13_verify.json", build_verify())
    except Stop as exc:
        print(f"M13_STEP_STOP {a.step}: {exc}")
        return 1
    print(f"M13_STEP_PASS {a.step} {p.relative_to(PROJECT).as_posix()} "
          f"{load(p)['artifact_sha256'][:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
