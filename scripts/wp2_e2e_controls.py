#!/usr/bin/env python3
"""WP-2 Mission-11 B11 - zero-API E2E instrument controls.

G-FORMAT / G-POS / G-NEG / G-LEAK / G-BUDGET. Usage:
    python scripts/wp2_e2e_controls.py --control format|leak|budget|choose|pos|neg
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

E2E_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
SALEOR_CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"

from benchmark.wp2.e2e.scopes import editable_filter, gold_raw_scope  # noqa: E402
from benchmark.wp2.e2e.spec import SMOKE_TASKS  # noqa: E402
from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2  # noqa: E402


def _git(commit: str, path: str) -> str | None:
    r = subprocess.run(["git", "-C", str(SALEOR_CACHE), "show", f"{commit}:{path}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def commits_of(task_id: str) -> tuple[str, str]:
    census = json.loads((PROJECT / "research/wp2/oracle_confirmation_linux_v2_2026-09-23" /
                         "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
    for c in census.get("tasks", []):
        if c["task_id"] == task_id:
            return c["parent_commit"], c["target_commit"]
    raise KeyError(task_id)


def control_format() -> int:
    from benchmark.wp2.e2e.patch_format import apply_patch, parse_multi_file_patch

    out = {"artifact": "g_format", "per_task": {}}
    for tid in SMOKE_TASKS:
        parent, target = commits_of(tid)
        r = subprocess.run(["git", "-C", str(SALEOR_CACHE), "diff", "--name-status", parent, target],
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
        scope = editable_filter(tid, gold_raw_scope(tid))
        editable = set(scope["editable"])
        non_expressible: list[str] = []
        checked = 0
        for line in r.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            st, path = parts[0], parts[-1]
            if st not in ("M",):
                continue
            if is_test_path_v2(path):
                continue
            if path not in editable:
                non_expressible.append(f"{path}:not-in-editable")
                continue
            old = _git(parent, path)
            new = _git(target, path)
            if old is None or new is None:
                non_expressible.append(f"{path}:missing-at-parent-or-target")
                continue
            p1, err = _try_convert(path, parent, target, old)
            checked += 1
            if p1 is None:
                non_expressible.append(f"{path}:{err}")
        out["per_task"][tid] = {"checked": checked, "non_expressible": non_expressible}
    (E2E_ROOT / "controls").mkdir(parents=True, exist_ok=True)
    (E2E_ROOT / "controls" / "g_format.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("G-FORMAT:", json.dumps(out, indent=1)[:1500])
    return 0


def _diff_to_p1(diff_text: str, path: str) -> str:
    """Convert a unified diff into P1 SEARCH/REPLACE blocks (context+old->new)."""
    hunks: list[tuple[list[str], list[str]]] = []
    old_lines: list[str] = []
    new_lines: list[str] = []
    in_hunk = False
    for line in diff_text.splitlines(keepends=True):
        if line.startswith("@@"):
            if in_hunk and (old_lines or new_lines):
                hunks.append((old_lines, new_lines))
            old_lines, new_lines = [], []
            in_hunk = True
            continue
        if not in_hunk or line.startswith(("diff ", "index ", "---", "+++")):
            continue
        if line.startswith("-"):
            old_lines.append(line[1:])
        elif line.startswith("+"):
            new_lines.append(line[1:])
        else:
            old_lines.append(line[1:])
            new_lines.append(line[1:])
    if in_hunk and (old_lines or new_lines):
        hunks.append((old_lines, new_lines))
    blocks: list[str] = []
    for old, new in hunks:
        blocks.append("<<<<<<< SEARCH\n" + "".join(old) + "=======\n" + "".join(new) + ">>>>>>> REPLACE\n")
    return "FILE: " + path + "\n" + "\n".join(blocks)


def _try_convert(path: str, parent: str, target: str, old: str) -> tuple[str | None, str]:
    """Build P1 with increasing context; returns (p1, error-or-empty)."""
    from benchmark.wp2.e2e.patch_format import apply_patch, parse_multi_file_patch
    for context in (3, 10, 40, 120, 400):
        ud = subprocess.run(["git", "-C", str(SALEOR_CACHE), "diff", f"--unified={context}",
                             parent, target, "--", path],
                            capture_output=True, text=True, encoding="utf-8", timeout=60).stdout
        p1 = _diff_to_p1(ud, path)
        try:
            sections = parse_multi_file_patch(p1)
            applied = apply_patch({path: old}, sections, {path})
            if applied[path] == _git(target, path):
                return p1, ""
        except ValueError:
            pass
    return None, "FORMAT_NOT_EXPRESSIBLE"


def control_choose() -> int:
    out = {"artifact": "control_tasks", "per_era": {}}
    eras = {"py38": [], "py39": [], "py312": []}
    for tid in SMOKE_TASKS:
        parent, target = commits_of(tid)
        era = next((i["era_key"] for i in json.loads((PROJECT / "research/wp2/" /
                      "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json").read_text(encoding="utf-8"))["tasks"]
                    if i["task_id"] == tid), "?")
        r = subprocess.run(["git", "-C", str(SALEOR_CACHE), "diff", "--name-status", parent, target],
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
        statuses = [ln.split("\t")[0] for ln in r.stdout.splitlines() if ln.strip()]
        gold = gold_raw_scope(tid)
        if not gold:
            continue
        scope = editable_filter(tid, gold)
        all_m = all(s == "M" for s in statuses)
        zero_excl = not scope["excluded_large"] and not scope["excluded_budget"]
        if all_m and zero_excl:
            eras.setdefault(era, []).append(tid)
    chosen = []
    for era in ("py38", "py39", "py312"):
        if eras.get(era):
            chosen.append(eras[era][0])
    out["chosen"] = chosen
    (E2E_ROOT / "controls").mkdir(parents=True, exist_ok=True)
    (E2E_ROOT / "controls" / "control_tasks.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("CONTROL_TASKS:", chosen)
    return 0


def control_leak() -> int:
    from benchmark.wp2.e2e.evaluator_sets import load_evaluator_sets
    from benchmark.wp2.e2e.prompt import build_prompt, leakage_scan
    from benchmark.wp2.e2e.scopes import build_arm_scopes
    from benchmark.wp2.e2e.task_inputs import load_task_input

    es = load_evaluator_sets()
    out = {"artifact": "g_leak", "per_prompt": {}, "blocking_total": 0}
    for tid in SMOKE_TASKS:
        ti = load_task_input(tid)
        sets = es["tasks"][tid]
        for arm in ("GOLD_HARD", "RMCSS_HARD", "PLACEBO_HARD", "AGENT_HARD"):
            scope = build_arm_scopes(tid, arm)
            if not scope.get("editable"):
                continue
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
    (E2E_ROOT / "controls").mkdir(parents=True, exist_ok=True)
    (E2E_ROOT / "controls" / "g_leak.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("G-LEAK blocking_total:", out["blocking_total"])
    return 0


def control_budget() -> int:
    from benchmark.wp2.e2e.scopes import build_arm_scopes
    est = {"artifact": "g_budget", "per_episode": {}, "worst_case_smoke_usd": 0.0,
           "ceiling_smoke_usd": 4.50}
    for tid in SMOKE_TASKS:
        for arm in ("GOLD_HARD", "RMCSS_HARD", "PLACEBO_HARD", "AGENT_HARD"):
            scope = build_arm_scopes(tid, arm)
            chars = sum(len(_git(commits_of(tid)[0], p) or "") for p in scope.get("editable", []))
            tokens = max(1, chars // 3)
            worst = tokens / 1e6 * 0.30 + 8192 / 1e6 * 1.00
            worst *= 2.0  # possible repair
            est["per_episode"][f"{tid}|{arm}"] = round(worst, 4)
            est["worst_case_smoke_usd"] += worst
    est["worst_case_smoke_usd"] = round(est["worst_case_smoke_usd"], 4)
    (E2E_ROOT / "controls").mkdir(parents=True, exist_ok=True)
    (E2E_ROOT / "controls" / "g_budget.json").write_text(
        json.dumps(est, indent=1, ensure_ascii=False), encoding="utf-8")
    print("G-BUDGET worst_case_smoke_usd:", est["worst_case_smoke_usd"],
          "<= 4.50:", est["worst_case_smoke_usd"] <= est["ceiling_smoke_usd"])
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", required=True,
                    choices=["format", "choose", "leak", "budget"])
    args = ap.parse_args()
    fn = {"format": control_format, "choose": control_choose,
          "leak": control_leak, "budget": control_budget}[args.control]
    raise SystemExit(fn())
