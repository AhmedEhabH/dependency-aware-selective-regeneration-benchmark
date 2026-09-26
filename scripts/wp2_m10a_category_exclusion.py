#!/usr/bin/env python3
"""WP-2 Mission-10A Phase D: mechanical excluded-test-category analysis.

ZERO API. Defines test categories MECHANICALLY from static evidence BEFORE any
probe outcome, then measures whether V2 systematically excludes whole
categories for the SAME missing declared dependency.

Categories (mechanical, static):
  C1 benchmark-count-queries: node test-file path contains ``tests/benchmark``
     AND the target-commit test file marks/requests ``count_queries``.
  C2 mocker-fixture: node test file (target commit) requests the ``mocker``
     fixture (function argument / pytestmark / usefixtures).
Verification of fixture request is read from the target-commit source via the
saleor cache (grep of the test file text), NOT from probe outcomes.

For each category reports: nodes seen in C4/C2/P2P-U, tasks affected, files
affected, V2 outcomes, and the share failing for the same missing dependency.

Usage:
    python scripts/wp2_m10a_category_exclusion.py [--out DIR]
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.m10a_audit import node_requests_fixture  # noqa: E402
from benchmark.wp2.oracle_confirmation import parse_junit_with_failures  # noqa: E402

SALEOR_CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"
V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
ENG_ROOT = PROJECT / "research" / "wp2" / "p2p_u_v2_eng_2026-09-25"
OUT_ROOT = PROJECT / "research" / "wp2" / "mission10a_env_audit_2026-09-26"
C2_TAR = V2_ROOT / "c2_junit_rescue_2026-09-23.tar.gz"

# Task -> target commit resolution
def load_task_targets() -> dict[str, str]:
    out: dict[str, str] = {}
    dev = json.loads((V2_ROOT / "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
    for t in dev["tasks"]:
        out[t["task_id"]] = t["target_commit"]
    main = json.loads(
        (PROJECT / "research" / "wp2" / "wp2_saleor_main297_census_2026-09-22.json").read_text(encoding="utf-8")
    )
    for t in main.get("tasks", []):
        out.setdefault(t["task_id"], t.get("target_commit"))
    return out


def test_file_text(cache: Path, commit: str, rel_path: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(cache), "show", f"{commit}:{rel_path}"],
        capture_output=True, text=True, encoding="utf-8", timeout=120, check=False,
    )
    return r.stdout if r.returncode == 0 else ""


def build_categories() -> dict:
    task_targets = load_task_targets()
    return {
        "task_targets": task_targets,
    }


def analyze() -> dict:
    task_targets = load_task_targets()
    _text_cache: dict[tuple[str, str], str] = {}

    def cached_text(task: str, fpath: str) -> str:
        commit = task_targets.get(task)
        key = (task, fpath)
        if key not in _text_cache:
            _text_cache[key] = test_file_text(SALEOR_CACHE, commit, fpath) if commit else ""
        return _text_cache[key]

    out: dict = {
        "artifact": "category_exclusion_analysis",
        "schema_version": "mission10a-category-exclusion-v1",
        "created_utc": _now_utc(),
        "category_definitions": {
            "benchmark-count-queries": "node test-file path contains "
            "``tests/benchmark`` AND target-commit test file marks/requests "
            "``count_queries`` (static source evidence)",
            "mocker-fixture": "target-commit test file requests the ``mocker`` "
            "fixture (static source evidence)",
        },
        "datasets": {},
    }

    # ---------- C4 dataset ----------
    per_test = V2_ROOT / "per_test_dev_v2.jsonl"
    c4 = {"benchmark-count-queries": Counter(), "mocker-fixture": Counter()}
    c4_tasks: dict[str, set] = {"benchmark-count-queries": set(), "mocker-fixture": set()}
    c4_files: dict[str, set] = {"benchmark-count-queries": set(), "mocker-fixture": set()}
    c4_fixture_req: dict[str, Counter] = {"benchmark-count-queries": Counter(), "mocker-fixture": Counter()}
    for line in per_test.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["classification"] != "TARGET_ORACLE_INVALID":
            continue
        nid = r["node_id"]
        fpath = nid.split("::", 1)[0]
        task = r["task_id"]
        text = cached_text(task, fpath)
        tname = nid.split("::", 1)[1] if "::" in nid else ""
        if "/tests/benchmark/" in f"/{fpath}" and node_requests_fixture(text, tname, "count_queries"):
            c4["benchmark-count-queries"]["error"] += 1
            c4_tasks["benchmark-count-queries"].add(task)
            c4_files["benchmark-count-queries"].add(fpath)
            c4_fixture_req["benchmark-count-queries"]["count_queries"] += 1
        if node_requests_fixture(text, tname, "mocker"):
            c4["mocker-fixture"]["error"] += 1
            c4_tasks["mocker-fixture"].add(task)
            c4_files["mocker-fixture"].add(fpath)
            c4_fixture_req["mocker-fixture"]["mocker"] += 1
    out["datasets"]["C4"] = {
        "error_TOI_nodes_by_category": {
            k: {"count": sum(v.values()), "by_outcome": dict(v),
                "tasks_affected": sorted(c4_tasks[k]),
                "files_affected": len(c4_files[k]),
                "fixture_requests_verified": dict(c4_fixture_req[k])}
            for k, v in c4.items()
        },
    }

    # ---------- C2 dataset (rescue archive) ----------
    c2 = {"benchmark-count-queries": Counter(), "mocker-fixture": Counter()}
    c2_tasks: dict[str, set] = {"benchmark-count-queries": set(), "mocker-fixture": set()}
    c2_files: dict[str, set] = {"benchmark-count-queries": set(), "mocker-fixture": set()}
    c2_fixture_req: dict[str, Counter] = {"benchmark-count-queries": Counter(), "mocker-fixture": Counter()}
    seen_c2: set[tuple[str, str]] = set()
    if C2_TAR.exists():
        import tarfile

        with tarfile.open(C2_TAR, "r:gz") as tar:
            for member in tar.getmembers():
                if not member.isfile() or not member.name.endswith(".xml"):
                    continue
                name = member.name.rsplit("/", 1)[-1]
                parts = name.split("_")
                if len(parts) < 4:
                    continue
                tid12 = parts[0]
                try:
                    content = tar.extractfile(member).read().decode("utf-8", errors="replace")
                    outs, _ = parse_junit_with_failures(content)
                except Exception:
                    continue
                task = None
                for full in task_targets:
                    if full.split("-")[-1].startswith(tid12):
                        task = full
                        break
                if task is None:
                    task = f"saleor-rc-{tid12}"
                for nid, outcome in outs.items():
                    if outcome != "error":
                        continue
                    if (tid12, nid) in seen_c2:
                        continue
                    seen_c2.add((tid12, nid))
                    fpath = nid.split("::", 1)[0]
                    text = cached_text(task, fpath)
                    tname = nid.split("::", 1)[1] if "::" in nid else ""
                    if "/tests/benchmark/" in f"/{fpath}" and node_requests_fixture(text, tname, "count_queries"):
                        c2["benchmark-count-queries"]["error"] += 1
                        c2_tasks["benchmark-count-queries"].add(task)
                        c2_files["benchmark-count-queries"].add(fpath)
                        c2_fixture_req["benchmark-count-queries"]["count_queries"] += 1
                    if node_requests_fixture(text, tname, "mocker"):
                        c2["mocker-fixture"]["error"] += 1
                        c2_tasks["mocker-fixture"].add(task)
                        c2_files["mocker-fixture"].add(fpath)
                        c2_fixture_req["mocker-fixture"]["mocker"] += 1
    out["datasets"]["C2"] = {
        "error_nodes_by_category": {
            k: {"count": sum(v.values()), "by_outcome": dict(v),
                "tasks_affected": sorted(c2_tasks[k]),
                "files_affected": len(c2_files[k]),
                "fixture_requests_verified": dict(c2_fixture_req[k])}
            for k, v in c2.items()
        },
    }

    # ---------- P2P-U ENG dataset ----------
    eng = {"benchmark-count-queries": Counter(), "mocker-fixture": Counter()}
    eng_tasks: dict[str, set] = {"benchmark-count-queries": set(), "mocker-fixture": set()}
    eng_files: dict[str, set] = {"benchmark-count-queries": set(), "mocker-fixture": set()}
    eng_fixture_req: dict[str, Counter] = {"benchmark-count-queries": Counter(), "mocker-fixture": Counter()}
    eng_cap200_all: Counter = Counter()
    eng_cap200_error: Counter = Counter()
    eng_node_requesting: dict[str, Counter] = {"benchmark-count-queries": Counter(), "mocker-fixture": Counter()}
    for task_dir in sorted(ENG_ROOT.iterdir()):
        if not task_dir.is_dir() or not task_dir.name.startswith("saleor-rc-"):
            continue
        cap_dir = task_dir / "cap200"
        run = cap_dir / "A"
        nc = run / "node_classes.json"
        no = run / "node_outcomes.json"
        if not nc.exists() or not no.exists():
            continue
        classes = json.loads(nc.read_text(encoding="utf-8"))
        task = task_dir.name
        for nid, cls in classes.items():
            fpath = nid.split("::", 1)[0]
            text = cached_text(task, fpath)
            tname = nid.split("::", 1)[1] if "::" in nid else ""
            req_cq = node_requests_fixture(text, tname, "count_queries")
            req_mocker = node_requests_fixture(text, tname, "mocker")
            is_cq = "/tests/benchmark/" in f"/{fpath}" and req_cq
            is_mocker = req_mocker
            if is_cq:
                eng_cap200_all["benchmark-count-queries"] += 1
                if cls == "COLLECTION_ERROR":
                    eng_cap200_error["benchmark-count-queries"] += 1
                    eng_node_requesting["benchmark-count-queries"]["error"] += 1
                    eng["benchmark-count-queries"]["COLLECTION_ERROR"] += 1
                    eng_tasks["benchmark-count-queries"].add(task)
                    eng_files["benchmark-count-queries"].add(fpath)
                    eng_fixture_req["benchmark-count-queries"]["count_queries"] += 1
                else:
                    eng_node_requesting["benchmark-count-queries"]["valid"] += 1
            if is_mocker:
                eng_cap200_all["mocker-fixture"] += 1
                if cls == "COLLECTION_ERROR":
                    eng_cap200_error["mocker-fixture"] += 1
                    eng_node_requesting["mocker-fixture"]["error"] += 1
                    eng["mocker-fixture"]["COLLECTION_ERROR"] += 1
                    eng_tasks["mocker-fixture"].add(task)
                    eng_files["mocker-fixture"].add(fpath)
                    eng_fixture_req["mocker-fixture"]["mocker"] += 1
                else:
                    eng_node_requesting["mocker-fixture"]["valid"] += 1
    out["datasets"]["P2P_U_ENG_cap200"] = {
        "category_nodes_total": dict(eng_cap200_all),
        "category_error_nodes": dict(eng_cap200_error),
        "by_category": {
            k: {"count": sum(v.values()), "by_class": dict(v),
                "tasks_affected": sorted(eng_tasks[k]),
                "files_affected": len(eng_files[k]),
                "fixture_requests_verified": dict(eng_fixture_req[k]),
                "node_level_requesting_fixture": dict(eng_node_requesting[k]),
                "excluded_share_of_category": (
                    eng_cap200_error[k] / eng_cap200_all[k] if eng_cap200_all[k] else None
                )}
            for k, v in eng.items()
        },
        "systematic_exclusion_note": "A mechanically defined category is "
        "systematically excluded if every V2-observed node that requests the "
        "missing fixture (node-level static signature evidence) reaches the "
        "relevant pytest setup point and errors for the SAME missing declared "
        "dependency with no valid execution observed.",
    }
    (OUT_ROOT / "category_exclusion_analysis.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    print("wrote category_exclusion_analysis.json")
    print(json.dumps(out["datasets"]["P2P_U_ENG_cap200"]["by_category"], indent=1))
    return out


def _now_utc() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


if __name__ == "__main__":
    analyze()
