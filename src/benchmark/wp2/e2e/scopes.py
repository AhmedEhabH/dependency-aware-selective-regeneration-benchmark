"""WP-2 Mission-11 E2E Smoke - scope builders (B4).

GOLD_HARD  = target-changed non-test paths (D42).
RMCSS_HARD = RM-CSS out-of-fold realization-A DEV predictions (D43).
PLACEBO_HARD = deterministic sha256-ranked placebo of size |GOLD| (D45).
AGENT_HARD = frozen protocol-v3 Agent selected_paths (D44; from C2).

The editable-set filter (D35) is applied to every arm identically.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4]
E2E_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"
CENSUS = json.loads((PROJECT / "research/wp2/oracle_confirmation_linux_v2_2026-09-23" /
                     "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
SALEOR_CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"
OOF_A = json.loads((PROJECT / "research/memory-rescue-v2/final_oof_predictions_A.json").read_text(encoding="utf-8"))
OOF_A_SHA = hashlib.sha256(
    (PROJECT / "research/memory-rescue-v2/final_oof_predictions_A.json").read_bytes()).hexdigest()

from benchmark.wp2.e2e.spec import MAX_CONTEXT_CHARS, MAX_FILE_CHARS, PLACEBO_SALT  # noqa: E402
from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2  # noqa: E402


def _git_show(commit: str, path: str) -> str | None:
    r = subprocess.run(["git", "-C", str(SALEOR_CACHE), "show", f"{commit}:{path}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def _tracked_paths(commit: str) -> list[str]:
    r = subprocess.run(["git", "-C", str(SALEOR_CACHE), "ls-tree", "-r", "--name-only", commit],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def commits_of(task_id: str) -> tuple[str, str]:
    for c in CENSUS.get("tasks", []):
        if c["task_id"] == task_id:
            return c["parent_commit"], c["target_commit"]
    raise KeyError(task_id)


def gold_raw_scope(task_id: str) -> list[str]:
    parent, target = commits_of(task_id)
    r = subprocess.run(["git", "-C", str(SALEOR_CACHE), "diff", "--name-status", parent, target],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    out = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        st = parts[0]
        if st in ("M", "R", "D"):
            p = parts[-1] if st != "R" else parts[1]
            if not is_test_path_v2(p):
                out.append(p)
    return sorted(out)


def rmcss_raw_scope(task_id: str) -> list[str]:
    return sorted(OOF_A.get(task_id, []))


def placebo_raw_scope(task_id: str, k: int) -> list[str]:
    parent, _ = commits_of(task_id)
    universe = [
        p for p in _tracked_paths(parent)
        if p.startswith("saleor/") and p.endswith(".py")
        and not is_test_path_v2(p)
        and "/migrations/" not in p
        and not p.endswith("__init__.py")
    ]
    ranked = sorted(universe, key=lambda p: hashlib.sha256(
        f"{PLACEBO_SALT}|{task_id}|{p}".encode()).hexdigest())
    return ranked[:k]


def editable_filter(task_id: str, raw: list[str]) -> dict:
    """D35 filter: exists at parent, not test path, text, <=120k chars, sorted,
    total <=300k chars. Returns {editable, excluded_large, excluded_budget, raw}."""
    parent, _ = commits_of(task_id)
    texts: dict[str, str] = {}
    excluded_large: list[str] = []
    for p in raw:
        if is_test_path_v2(p):
            continue
        txt = _git_show(parent, p)
        if txt is None:
            continue
        if len(txt) > MAX_FILE_CHARS:
            excluded_large.append(p)
            continue
        try:
            txt.encode("utf-8")
        except UnicodeEncodeError:
            continue
        texts[p] = txt
    ordered = sorted(texts)
    editable: list[str] = []
    excluded_budget: list[str] = []
    budget = 0
    for p in ordered:
        if budget + len(texts[p]) > MAX_CONTEXT_CHARS:
            excluded_budget.append(p)
            continue
        budget += len(texts[p])
        editable.append(p)
    return {"editable": editable, "excluded_large": sorted(excluded_large),
            "excluded_budget": sorted(excluded_budget), "raw": sorted(raw)}


def build_arm_scopes(task_id: str, arm: str, placeholder_k: int | None = None) -> dict:
    if arm == "GOLD_HARD":
        raw = gold_raw_scope(task_id)
    elif arm == "RMCSS_HARD":
        raw = rmcss_raw_scope(task_id)
    elif arm == "PLACEBO_HARD":
        k = placeholder_k if placeholder_k is not None else len(gold_raw_scope(task_id))
        raw = placebo_raw_scope(task_id, k)
    elif arm == "AGENT_HARD":
        agent = E2E_ROOT / "scopes" / "agent_scopes_dev_eng.json"
        if agent.exists():
            d = json.loads(agent.read_text(encoding="utf-8"))
            raw = sorted(d.get(task_id, {}).get("selected_paths", []))
        else:
            return {"task_id": task_id, "arm": arm, "status": "AGENT_SCOPE_PENDING",
                    "raw": [], "editable": [], "excluded_large": [], "excluded_budget": []}
    else:
        raise ValueError(arm)
    filt = editable_filter(task_id, raw)
    filt["arm"] = arm
    filt["task_id"] = task_id
    filt["status"] = "DONE"
    return filt
