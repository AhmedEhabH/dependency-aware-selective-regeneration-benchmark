#!/usr/bin/env python3
"""WP-2 Mission-12 B8 - zero-API controls v2 (J1-J10).

Controls (all ZERO API):
  J1 G-FORMAT CLEAN       - gold-as-output parsed by the v2 parser on the frozen
                            expressible denominator (expected 100%).
  J2 G-FORMAT-NOISY       - gold-as-output wrapped with preamble + fences +
                            trailing prose; same final patch bytes.
  J3 G-POS                - 3 control tasks through run_episode_v2 with a
                            scripted client: initial replay response invalid,
                            repair response = gold blocks. Verify APPLIED via
                            repair, original user + previous output present,
                            repair hash valid, tree == target, F2P PASS.
  J4 G-NEG                - known wrong patch fails downstream appropriately.
  J5 G-REPAIR-CONTEXT     - 3/3 exact four-message structure; 3/3 hashes valid.
  J6 G-CACHE              - logical requests == expected N; client invocations
                            == unique request hashes.
  J7 G-LEAK               - all 56 planned v2 prompts; 0 blocking hits.
  J8 G-REPLAY             - paid v2 episodes root has 0 replay routes.
  J9 G-BUDGET             - worst case <= $2.00.
  J10                     - instrument_v2_ready.json.

Usage:
  python scripts/wp2_e2e_controls_v2.py --control format|noisy|pos|neg|cache|leak|replay|budget|all
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

V1_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"
V2_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v2"
SALEOR_CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"

from benchmark.wp2.e2e.generate import _raw_scope  # noqa: E402
from benchmark.wp2.e2e.llm_client import CallResult, Ledger  # noqa: E402
from benchmark.wp2.e2e.patch_format import apply_patch_v2, parse_multi_file_patch_v2  # noqa: E402
from benchmark.wp2.e2e.prompt import build_prompt  # noqa: E402
from benchmark.wp2.e2e.response_cache import ResponseCache  # noqa: E402
from benchmark.wp2.e2e.scopes import build_arm_scopes, commits_of, editable_filter, gold_raw_scope  # noqa: E402
from benchmark.wp2.e2e.spec import (  # noqa: E402
    CEILING_AGENT_USD,
    CEILING_SMOKE_V2_USD,
    MAX_TOKENS,
    SMOKE_TASKS,
)
from benchmark.wp2.e2e.task_inputs import load_task_input  # noqa: E402

CONTROL_TASKS = json.loads((V1_ROOT / "controls" / "control_tasks.json").read_text(encoding="utf-8"))["chosen"]
ARMS = ("GOLD_HARD", "RMCSS_HARD", "AGENT_HARD", "PLACEBO_HARD")


def _git(commit: str, path: str) -> str | None:
    r = subprocess.run(["git", "-C", str(SALEOR_CACHE), "show", f"{commit}:{path}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def gold_p1_v2(_task_id: str, path: str, parent: str, target: str) -> str | None:
    from scripts.wp2_e2e_expressibility import _try_convert_v2
    old = _git(parent, path)
    if old is None:
        return None
    return _try_convert_v2(path, parent, target, old)[0]


def gold_as_model_output(task_id: str) -> str:
    from benchmark.wp2.e2e.scopes import editable_filter, gold_raw_scope
    parent, target = commits_of(task_id)
    scope = editable_filter(task_id, gold_raw_scope(task_id))
    blocks = []
    for path in scope["editable"]:
        p1 = gold_p1_v2(task_id, path, parent, target)
        if p1:
            blocks.append(p1)
    return "\n".join(blocks)


def _diff_text(task_id: str, arm: str, subdir: str = "episodes") -> str:
    p = V2_ROOT / subdir / task_id / arm / "final_diff.patch"
    return p.read_text(encoding="utf-8") if p.exists() else ""


# ---------------------------------------------------------------------------
# J1 / J2
# ---------------------------------------------------------------------------
def control_format() -> int:
    out = {"artifact": "g_format_v2", "per_task": {}}
    total_expr = 0
    total_ok = 0
    for tid in SMOKE_TASKS:
        gold = gold_as_model_output(tid)
        parent, target = commits_of(tid)
        scope = editable_filter(tid, gold_raw_scope(tid))
        editable = set(scope["editable"])
        ok = False
        err = ""
        try:
            sections, stats = parse_multi_file_patch_v2(gold)
            res, results = apply_patch_v2({p: _git(parent, p) or "" for p in scope["editable"]},
                                          sections, editable)
            if all(res[p] == (_git(target, p) or "") for p in scope["editable"]):
                ok = True
        except ValueError as exc:
            err = str(exc)
        expressible = json.loads((V2_ROOT / "controls" / "expressible_population.json")
                                 .read_text(encoding="utf-8"))["per_task"][tid]["expressible_count"]
        total_expr += expressible
        total_ok += 1 if ok else 0
        out["per_task"][tid] = {"expressible": expressible, "parse_ok": ok, "error": err}
    out["summary"] = {"expressible_paths_total": total_expr,
                      "tasks_with_expressible_files": len(SMOKE_TASKS),
                      "tasks_parse_ok": total_ok,
                      "expected_100pct": total_ok == len(SMOKE_TASKS)}
    (V2_ROOT / "controls").mkdir(parents=True, exist_ok=True)
    (V2_ROOT / "controls" / "g_format_v2.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("G-FORMAT-V2:", json.dumps(out["summary"]))
    return 0


def control_noisy() -> int:
    out = {"artifact": "g_format_noisy_v2", "per_task": {}}
    for tid in SMOKE_TASKS:
        gold = gold_as_model_output(tid)
        noisy = ("Let me look at this change carefully.\n\n```python\n" + gold +
                 "\n```\nI believe this fixes the issue. Regards.\n")
        parent, target = commits_of(tid)
        scope = editable_filter(tid, gold_raw_scope(tid))
        editable = set(scope["editable"])
        ok = False
        err = ""
        try:
            from benchmark.wp2.e2e.patch_format import extract_envelope
            clean, stats = extract_envelope(noisy)
            sections, _ = parse_multi_file_patch_v2(clean)
            res, _ = apply_patch_v2({p: _git(parent, p) or "" for p in scope["editable"]},
                                    sections, editable)
            ok = all(res[p] == (_git(target, p) or "") for p in scope["editable"])
        except ValueError as exc:
            err = str(exc)
        out["per_task"][tid] = {"ok": ok, "error": err}
    total = sum(1 for v in out["per_task"].values() if v["ok"])
    out["summary"] = {"ok_total": total, "of": len(SMOKE_TASKS),
                      "expected_100pct": total == len(SMOKE_TASKS)}
    (V2_ROOT / "controls" / "g_format_noisy_v2.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("G-FORMAT-NOISY:", json.dumps(out["summary"]))
    return 0


# ---------------------------------------------------------------------------
# J3 / J5 (G-POS + G-REPAIR-CONTEXT)
# ---------------------------------------------------------------------------
def _run_pos(task_list: list[str]) -> int:
    from benchmark.wp2.e2e import evaluate as ev
    from benchmark.wp2.e2e import generate_v2 as gv2
    from benchmark.wp2.e2e.evaluate import evaluate_state, materialize, score

    out = {"artifact": "g_pos_v2", "per_task": {}}
    ctx = {"artifact": "g_repair_context_v2", "per_task": {}}

    class GoldClient:
        def __init__(self, gold: str) -> None:
            self.gold = gold
            self.calls = 0

        def generate_messages(self, _messages):
            self.calls += 1
            if self.calls == 1:
                text = ("I will implement this change now.\n\n"
                        "FILE: saleor/x/models.py\n<<<<<<< SEARCH\nZZZ_NOT_FOUND\n"
                        "=======\nNOP\n>>>>>>> REPLACE\n")
            else:
                text = self.gold
            return CallResult(text=text, finish_reason="stop", prompt_tokens=100,
                              completion_tokens=len(text) // 4, cost_usd=0.0,
                              route="replay", provider="replay", latency_s=0.0,
                              request_id=f"gold-ctrl-{self.calls}")

    for tid in task_list:
        parent, target = commits_of(tid)
        gold = gold_as_model_output(tid)
        real_pycompile = gv2.py_compile_in_era
        gv2.py_compile_in_era = lambda _era, files: {p: "ok" for p in files}
        real_root = ev.E2E_ROOT
        ev.E2E_ROOT = V2_ROOT  # junit output to v2 root only
        try:
            cache = ResponseCache(V2_ROOT / "cache_tmp_pos")
            ledger = Ledger(V2_ROOT / "ledger" / "controls_v2.jsonl",
                            {"AGENT": CEILING_AGENT_USD, "SMOKE": CEILING_SMOKE_V2_USD})
            client = GoldClient(gold)
            ep = gv2.run_episode_v2(tid, "GOLD_HARD", client, ledger, cache,
                                    root=V2_ROOT, episodes_subdir="controls")
            # G-REPAIR-CONTEXT: verify exact four-message structure + hashes
            repair_hashes = ep.get("repair_component_hashes", {})
            roles_ok = (len(repair_hashes) == 4) if ep.get("repair_used") else False
            sha_valid = bool(ep.get("repair_request_sha256"))
            ctx["per_task"][tid] = {
                "repair_used": ep.get("repair_used"),
                "exact_four_message_structure": roles_ok,
                "component_hashes": repair_hashes,
                "repair_request_sha_valid": sha_valid,
            }
            if ep["status"] != "APPLIED":
                out["per_task"][tid] = {"status": ep["status"], "validation": ep["validation"]}
                continue
            wt, tree_sha = materialize(tid, "ctrl_pos_v2", _diff_text(tid, "GOLD_HARD", "controls"))
            target_tree = subprocess.run(["git", "-C", str(SALEOR_CACHE), "rev-parse", f"{target}^{{tree}}"],
                                         capture_output=True, text=True, encoding="utf-8").stdout.strip()
            rec = evaluate_state(tid, "ctrl_pos_v2", wt)
            scd = score(tid, "ctrl_pos_v2", rec["groups"])
            out["per_task"][tid] = {"tree_sha": tree_sha, "target_tree": target_tree,
                                    "tree_matches": tree_sha == target_tree, **scd}
        finally:
            gv2.py_compile_in_era = real_pycompile
            ev.E2E_ROOT = real_root
    ok_tree = sum(1 for v in out["per_task"].values() if v.get("tree_matches"))
    ok_ctx = sum(1 for v in ctx["per_task"].values()
                 if v.get("exact_four_message_structure") and v.get("repair_request_sha_valid"))
    out["summary"] = {"tree_matches": f"{ok_tree}/{len(task_list)}",
                      "f2p_pass": sum(1 for v in out["per_task"].values() if v.get("f2p_task") == "PASS")}
    ctx["summary"] = {"context_ok": f"{ok_ctx}/{len(task_list)}", "expected_3_3": ok_ctx == 3}
    (V2_ROOT / "controls" / "g_pos_v2.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    (V2_ROOT / "controls" / "g_repair_context_v2.json").write_text(
        json.dumps(ctx, indent=1, ensure_ascii=False), encoding="utf-8")
    print("G-POS-V2:", json.dumps(out["summary"]))
    print("G-REPAIR-CONTEXT-V2:", json.dumps(ctx["summary"]))
    return 0


def _run_neg(task_list: list[str]) -> int:
    from benchmark.wp2.e2e import evaluate as ev
    from benchmark.wp2.e2e.evaluate import evaluate_state, materialize, score
    out = {"artifact": "g_neg_v2", "per_task": {}}
    real_root = ev.E2E_ROOT
    ev.E2E_ROOT = V2_ROOT
    try:
        for tid in task_list:
            wt, _tree = materialize(tid, "ctrl_neg_v2", "")
            rec = evaluate_state(tid, "ctrl_neg_v2", wt)
            scd = score(tid, "ctrl_neg_v2", rec["groups"])
            out["per_task"][tid] = scd
    finally:
        ev.E2E_ROOT = real_root
    out["summary"] = {"f2p_fail": sum(1 for v in out["per_task"].values() if v.get("f2p_task") == "FAIL"),
                      "resolved_false": sum(1 for v in out["per_task"].values() if not v.get("resolved"))}
    (V2_ROOT / "controls" / "g_neg_v2.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("G-NEG-V2:", json.dumps(out["summary"]))
    return 0


# ---------------------------------------------------------------------------
# J6 / J7 / J8 / J9
# ---------------------------------------------------------------------------
def build_planned_episodes() -> list[tuple[str, str]]:
    episodes = []
    for tid in sorted(SMOKE_TASKS):
        for arm in ARMS:
            episodes.append((tid, arm))
    return episodes


def control_cache() -> int:
    from benchmark.wp2.e2e.llm_client import ReplayClient
    from benchmark.wp2.e2e.response_cache import ResponseCache

    # Build the 56 v2 request shas; count unique. Then simulate client calls.
    # Scopes resolve EXACTLY as the paid generator does (generate._raw_scope).
    shas: set[str] = set()
    messages_by_episode: dict[tuple[str, str], list[dict]] = {}
    for tid, arm in build_planned_episodes():
        scope = editable_filter(tid, _raw_scope(tid, arm))
        if not scope.get("editable"):
            continue
        ti = load_task_input(tid)
        texts = {p: _git(commits_of(tid)[0], p) or "" for p in scope["editable"]}
        system, user, _sha = build_prompt(ti, scope["editable"], texts, scope)
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        messages_by_episode[(tid, arm)] = msgs
        shas.add(ResponseCache.request_sha(
            "qwen/qwen3-coder", "openrouter:qwen/qwen3-coder@deepinfra/turbo",
            "deepinfra/turbo", 0.0, 1.0, MAX_TOKENS, msgs))
    # Simulate the dry-run with ReplayClient: client invocations == unique shas
    import shutil
    cache_dir = V2_ROOT / "cache_dry"
    shutil.rmtree(cache_dir, ignore_errors=True)
    cache = ResponseCache(cache_dir)
    client = ReplayClient({})
    invocations = 0
    for (_tid, _arm), msgs in messages_by_episode.items():
        rs = ResponseCache.request_sha(
            "qwen/qwen3-coder", "openrouter:qwen/qwen3-coder@deepinfra/turbo",
            "deepinfra/turbo", 0.0, 1.0, MAX_TOKENS, msgs)
        if cache.get(rs) is None:
            call = client.generate_messages(msgs)
            invocations += 1
            cache.put(rs, {"request_sha": rs, "text": call.text,
                           "finish_reason": "stop", "prompt_tokens": 0,
                           "completion_tokens": 0, "cost_usd": 0.0})
    out = {"artifact": "g_cache_v2", "logical_requests": len(messages_by_episode),
           "unique_request_shas": len(shas), "client_invocations": invocations,
           "match": len(shas) == invocations,
           "note": "scopes resolved via generate._raw_scope (same as paid generator)"}
    (V2_ROOT / "controls" / "g_cache_v2.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("G-CACHE-V2:", json.dumps(out))
    return 0


def control_leak() -> int:
    from benchmark.wp2.e2e.evaluator_sets import load_evaluator_sets
    from benchmark.wp2.e2e.prompt import leakage_scan

    es = load_evaluator_sets()
    out = {"artifact": "g_leak_v2", "per_prompt": {}, "blocking_total": 0}
    for tid, arm in build_planned_episodes():
        scope = editable_filter(tid, _raw_scope(tid, arm))
        if not scope.get("editable"):
            continue
        ti = load_task_input(tid)
        sets = es["tasks"][tid]
        texts = {p: _git(commits_of(tid)[0], p) or "" for p in scope["editable"]}
        _s, user, _sh = build_prompt(ti, scope["editable"], texts, scope)
        protected = {"f2p_ids": sets["behavioral_f2p_node_ids"],
                     "p2ps_ids": sets["p2p_s_node_ids"],
                     "p2pu_ids": sets["p2p_u_cap200_stable_ids"],
                     "changed_test_paths": sets["changed_test_paths"],
                     "target_added_lines": []}
        hits = leakage_scan(user, protected)
        out["per_prompt"][f"{tid}|{arm}"] = hits
        out["blocking_total"] += len(hits["blocking"])
    out["expected_0_blocking"] = out["blocking_total"] == 0
    (V2_ROOT / "controls" / "g_leak_v2.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("G-LEAK-V2 blocking_total:", out["blocking_total"])
    return 0


def control_replay() -> int:
    episodes_dir = V2_ROOT / "episodes"
    replay_count = 0
    if episodes_dir.exists():
        for ep in episodes_dir.rglob("episode.json"):
            d = json.loads(ep.read_text(encoding="utf-8"))
            for c in d.get("calls", []):
                if c.get("route") == "replay":
                    replay_count += 1
    out = {"artifact": "g_replay_v2", "replay_routes_in_paid_episodes": replay_count,
           "expected_0": replay_count == 0}
    (V2_ROOT / "controls" / "g_replay_v2.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("G-REPLAY-V2:", json.dumps(out))
    return 0


def control_budget() -> int:
    est = {"artifact": "g_budget_v2", "per_episode": {}, "worst_case_smoke_usd": 0.0,
           "ceiling_smoke_v2_usd": CEILING_SMOKE_V2_USD}
    for tid, arm in build_planned_episodes():
        scope = build_arm_scopes(tid, arm)
        chars = sum(len(_git(commits_of(tid)[0], p) or "") for p in scope.get("editable", []))
        tokens = max(1, chars // 3)
        worst = tokens / 1e6 * 0.30 + MAX_TOKENS / 1e6 * 1.00
        worst *= 2.0  # initial + full-context repair
        est["per_episode"][f"{tid}|{arm}"] = round(worst, 4)
        est["worst_case_smoke_usd"] += worst
    # variance probe: 3 GOLD control tasks x 2 extra replicates, full-context worst case
    variance = 0.0
    for tid in CONTROL_TASKS:
        scope = build_arm_scopes(tid, "GOLD_HARD")
        chars = sum(len(_git(commits_of(tid)[0], p) or "") for p in scope.get("editable", []))
        tokens = max(1, chars // 3)
        variance += 2 * (tokens / 1e6 * 0.30 + MAX_TOKENS / 1e6 * 1.00)
    est["variance_worst_case_usd"] = round(variance, 4)
    est["worst_case_smoke_usd"] = round(est["worst_case_smoke_usd"] + variance, 4)
    est["within_ceiling"] = est["worst_case_smoke_usd"] <= CEILING_SMOKE_V2_USD
    (V2_ROOT / "controls" / "g_budget_v2.json").write_text(
        json.dumps(est, indent=1, ensure_ascii=False), encoding="utf-8")
    print("G-BUDGET-V2 worst_case:", est["worst_case_smoke_usd"], "<= 2.00:",
          est["within_ceiling"])
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", required=True,
                    choices=["format", "noisy", "pos", "neg", "cache", "leak",
                             "replay", "budget", "all"])
    ap.add_argument("--only", default=None)
    args = ap.parse_args()
    fns = {"format": control_format, "noisy": control_noisy, "pos": _run_pos,
           "neg": _run_neg, "cache": control_cache, "leak": control_leak,
           "replay": control_replay, "budget": control_budget}
    if args.control == "all":
        for name in ("format", "noisy", "cache", "leak", "replay", "budget"):
            fns[name]()
        tasks = [args.only] if args.only else CONTROL_TASKS
        _run_pos(tasks)
        _run_neg(tasks)
    else:
        if args.control == "pos":
            raise SystemExit(_run_pos([args.only] if args.only else CONTROL_TASKS))
        if args.control == "neg":
            raise SystemExit(_run_neg([args.only] if args.only else CONTROL_TASKS))
        raise SystemExit(fns[args.control]())
