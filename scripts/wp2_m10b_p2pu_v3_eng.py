#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 5B: P2P-U V3 ENG rediscovery + execution (20) - ZERO API.

TRUE candidate rediscovery under Harness V3 (not frozen V2 membership reuse):

For each V3 oracle-valid ENG task:
1. Re-run unchanged-test candidate discovery (pytest --collect-only at the
   TARGET state inside the V3 era container, nofile=65536, lock-exact install)
   over the frozen associated unchanged-test files -- SAME scientific rule as
   P2P-U V2 (same candidate pool source, UNKNOWN handling, proximal/distal,
   salt, hashing, round-robin, 3P:1D, cap200/cap400, first200 subset first400).
2. Freeze the NEW V3 raw candidate pool BEFORE outcome execution.
3. Derive V3 cap200/cap400 memberships from the V3-discovered pool.
4. Report true V2->V3 membership diff (raw candidates, files, first200,
   first400, intersection, additions, removals, reason categories).
5. Execute V3 cap200 and cap400 INDEPENDENTLY, workers=1, 3 parent + 3 target
   reps, nofile=65536, fresh DB policy, frozen classify_p2p_node taxonomy.

The V2 membership is a comparison baseline only, never the V3 population.

Mission-11 A2 hardening (engineering only; NO scientific change):
- H1  persist raw JUnit per (task, cap, state, rep) + SHA-256.
- H2  install/tooling failure -> ENV_FAIL_P2PU (never classified), retry once.
- H3  parse errors -> INTEGRITY_FAIL (never swallowed), retry once, then stop.
- H4  monotonic wall clock + clock pre/post post-check.
- H5  evidence_sha256 + verified resume (verify_unit).
- H6  collection-session abort flag (D18).
- H7  --max-units chunking + P2PU_STOP.flag + progress file.
- H8  complete unit manifest.

Usage:
    python scripts/wp2_m10b_p2pu_v3_eng.py --all-tasks --max-units 0
    python scripts/wp2_m10b_p2pu_v3_eng.py --all-tasks --max-units 4
    python scripts/wp2_m10b_p2pu_v3_eng.py --task saleor-rc-... [--cap 200|400]
    python scripts/wp2_m10b_p2pu_v3_eng.py --all-tasks [--cap 200|400]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.harness_v3 import (  # noqa: E402
    HARNESS_V3_VERSION,
    NOFILE_HARD,
    NOFILE_SOFT,
    TOOLING_INSTALL,
    base_image_id,
    clock_preflight,
    drop_db,
    ensure_fresh_db,
    ensure_postgres_running,
    ensure_worktrees_v3,
    fresh_db_name,
    git_linux,
    lock_install_script,
    locked_dev_install,
    lockfile_sha256,
    remove_worktrees_v3,
    target_manifests,
    wsl,
    wsl_docker,
)
from benchmark.wp2.p2p_inventory_dev_v1 import classify_p2p_node  # noqa: E402
from benchmark.wp2.p2p_u_v2 import build_task_selection  # noqa: E402

V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
MEMBERSHIP = json.loads((PROJECT / "research" / "wp2" /
                         "wp2_p2p_u_v2_membership_2026-09-25.json").read_text(encoding="utf-8"))
INVENTORY = json.loads((PROJECT / "research" / "wp2" /
                        "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json").read_text(encoding="utf-8"))
WSL_CACHE = "/opt/wp2_v2/saleor-cache"
WSL_WT = "/opt/wp2_v2/worktrees"
WSL_DISTRO = "Ubuntu-24.04"
REPS = 3
P2PU_V3_VERSION = "p2p-u-v3-eng-2026-09-26"
PYTEST_FLAGS = "--ds=saleor.tests.settings --disable-socket --reuse-db"
INSTALL_FAIL_MARKERS = ("INSTALL_DEV_FAIL", "INSTALL_MAIN_FAIL", "TOOLING_FAIL", "INSTALL_FAIL")


class P2PUIntegrityError(RuntimeError):
    """Second INTEGRITY_FAIL for a unit -> P2PU_INTEGRITY_STOP (D17)."""


def _now_utc() -> str:
    import datetime
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


RUNNER_SHA256 = _file_sha256(__file__)


def _harness_spec_sha256() -> str:
    spec = json.loads((OUT_ROOT / "harness_v3_spec.json").read_text(encoding="utf-8"))
    return spec["freeze_hashes"]["v3_spec_sha256"]


HARNESS_SPEC_SHA256 = _harness_spec_sha256()


def load_v3_oracle_valid_eng() -> list[str]:
    """P2P-U V3 population = oracle_valid_union from the corrected
    ENG_V3_ORACLE_READY artifact (single source of truth; addendum B)."""
    eng_ready = json.loads((OUT_ROOT / "eng_v3_oracle_ready.json").read_text(encoding="utf-8"))
    return sorted(eng_ready["oracle_valid_union_task_ids"])


def inventory_row(task_id: str) -> dict:
    for r in INVENTORY["tasks"]:
        if r["task_id"] == task_id:
            return r
    raise RuntimeError(f"{task_id} not in unchanged-test inventory")


def task_commits(task_id: str) -> tuple[str, str]:
    census = json.loads((V2_ROOT / "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
    for t in census.get("tasks", []):
        if t["task_id"] == task_id:
            return t["parent_commit"], t["target_commit"]
    raise RuntimeError(f"{task_id} not in census")


def v2_membership_for(task_id: str, cap: int) -> list[str]:
    t = MEMBERSHIP.get("tasks", {}).get(task_id)
    if not t:
        return []
    key = "cap200_node_ids" if cap == 200 else "cap400_node_ids"
    return list(t.get(key, []))


def _proximity_equivalence(task_id: str, v3_sel: dict, v2_mem: dict) -> dict:
    """Addendum E: assert the V3 touched-production derivation equals the V2
    frozen values on shared evidence."""
    v2_unknown = set(v2_mem.get("unknown_touched_paths", []))
    v3_unknown = set(v3_sel.get("unknown_touched_paths", []))
    v2_prox = v2_mem.get("proximity_by_file", {})
    v3_prox = v3_sel.get("proximity_by_file", {})
    shared = sorted(set(v2_prox) & set(v3_prox))
    prox_diffs = {f: (v2_prox[f], v3_prox.get(f)) for f in shared
                  if v2_prox[f] != v3_prox.get(f)}
    unknown_ok = v2_unknown == v3_unknown
    known_ok = v2_mem.get("n_known_touched_paths") == v3_sel.get("n_known_touched_paths")
    prox_ok = len(prox_diffs) == 0
    return {
        "task_id": task_id,
        "ok": unknown_ok and known_ok and prox_ok,
        "unknown_touched_equal": unknown_ok,
        "n_known_touched_equal": known_ok,
        "shared_files": len(shared),
        "proximity_diffs": prox_diffs,
        "v2_n_known": v2_mem.get("n_known_touched_paths"),
        "v3_n_known": v3_sel.get("n_known_touched_paths"),
        "v2_unknown": sorted(v2_unknown),
        "v3_unknown": sorted(v3_unknown),
    }


# ---------------------------------------------------------------------------
# V3 rediscovery (20 step 1)
# ---------------------------------------------------------------------------
def rediscover_v3(task_id: str) -> dict:
    """pytest --collect-only at TARGET under V3 environment (nofile, lock-exact)."""
    t_start = time.monotonic()
    row = inventory_row(task_id)
    parent, target = task_commits(task_id)
    era_key = row["era_key"]
    all_associated = row.get("associated_unchanged_test_files", [])
    collect_files = [
        f for f in all_associated
        if f.endswith(".py") and "[" not in f and "]" not in f
        and not f.endswith("__init__.py") and not f.endswith("conftest.py")
    ]
    tid = task_id.split("-")[-1][:12]
    wt = f"{WSL_WT}/{tid}_v3_p2pu_t"
    wsl(f"mkdir -p {WSL_WT}")
    wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    r = git_linux(WSL_CACHE, "worktree", "add", "--detach", wt, target)
    if r.returncode != 0:
        raise RuntimeError(f"[wt] target add FAILED: {r.stderr[-1200:]}")
    wt_name = wt.rsplit("/", 1)[-1]

    manifests = target_manifests(target)
    install_frag, install_mode, _ = lock_install_script(wt, manifests)
    locked_dev = locked_dev_install(task_id)

    subprocess.run(["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
                    f"cat > {wt}/.wp2_disc_files.txt"],
                   input=("\n".join(collect_files) + "\n").encode("utf-8"),
                   capture_output=True, timeout=180, check=True)
    script = (
        "#!/usr/bin/env bash\nset -e\n"
        "uv venv /opt/venv >/dev/null 2>&1 || true\n"
        f"{install_frag} >/tmp/install.log 2>&1 || "
        "{ echo INSTALL_FAIL; tail -120 /tmp/install.log; exit 2; }\n"
        f"{locked_dev} >>/tmp/install.log 2>&1 || "
        "{ echo INSTALL_DEV_FAIL; tail -80 /tmp/install.log; exit 2; }\n"
        f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 || "
        "{ echo TOOLING_FAIL; tail -80 /tmp/install.log; exit 2; }\n"
        f"cd /workspace/{wt_name}\n"
        f"mapfile -t FILES < /workspace/{wt_name}/.wp2_disc_files.txt\n"
        "rc=0\n"
        "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
        "--ds=saleor.tests.settings --collect-only -q "
        '"${FILES[@]}" >/tmp/collect.log 2>&1 || rc=$?\n'
        "grep -E '::' /tmp/collect.log | grep -v '^=' | sort -u > "
        f"/workspace/{wt_name}/.wp2_disc_nodes.txt\n"
        "echo COLLECT_RC=$rc\n"
    )
    subprocess.run(["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
                    f"cat > {wt}/.wp2_discover.sh"],
                   input=script.encode("utf-8"), capture_output=True, timeout=180, check=True)
    r = wsl_docker(
        ["run", "--rm", "--network", "host",
         "--ulimit", f"nofile={NOFILE_SOFT}:{NOFILE_HARD}",
         "-e", "DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/saleor",
         "-e", "CACHE_URL=locmem://",
         "-v", f"{wt}:/workspace/{wt_name}",
         "-v", "wp2-uv-cache:/root/.cache/uv",
         f"wp2-era-{era_key}", "bash", f"/workspace/{wt_name}/.wp2_discover.sh"],
        timeout_s=7200,
    )
    nodes_txt = wsl(f"cat {wt}/.wp2_disc_nodes.txt 2>/dev/null || echo __NO_FILE__")
    nodes = []
    if "__NO_FILE__" not in nodes_txt.stdout[:20]:
        nodes = sorted(line.strip() for line in nodes_txt.stdout.splitlines() if line.strip())
    wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    wsl(f"git -C {WSL_CACHE} worktree prune 2>/dev/null || true")
    return {
        "task_id": task_id,
        "era_key": era_key,
        "target_commit": target,
        "rediscovery_version": "p2p-u-v3-eng-rediscovery-2026-09-26",
        "install_mode": install_mode,
        "collect_rc": r.returncode,
        "n_associated_files": len(all_associated),
        "n_collect_files": len(collect_files),
        "candidate_node_ids": nodes,
        "wall_s": round(time.monotonic() - t_start, 1),
    }


def derive_v3_selection(discovery: dict) -> dict:
    """Derive V3 cap200/cap400 from the V3-discovered pool (SAME rule/salt).

    Uses the EXACT frozen touched-production derivation (changed_paths_linux
    with is_test_path_v2) that produced the V2 membership - never a heuristic."""
    from scripts.wp2_linux_dryrun import changed_paths_linux

    census = json.loads((V2_ROOT / "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
    parent = target = None
    for c in census.get("tasks", []):
        if c["task_id"] == discovery["task_id"]:
            parent, target = c["parent_commit"], c["target_commit"]
            break
    if parent is None or target is None:
        raise RuntimeError(f"{discovery['task_id']} not in census")
    cp = changed_paths_linux(parent, target)
    sel = build_task_selection(
        task_id=discovery["task_id"],
        candidate_node_ids=discovery["candidate_node_ids"],
        touched_production_files=cp["prod_files"],
    )
    return sel


def ensure_discovery(task_id: str) -> dict:
    """Return the frozen V3 rediscovery record, rediscovering only if absent."""
    discovery_file = OUT_ROOT / f"p2pu_v3_rediscovery_{task_id}.json"
    if discovery_file.exists():
        return json.loads(discovery_file.read_text(encoding="utf-8"))
    print(f"  {task_id}: rediscovering candidates under V3 ...", flush=True)
    discovery = rediscover_v3(task_id)
    sel = derive_v3_selection(discovery)
    v2_200 = set(v2_membership_for(task_id, 200))
    v2_400 = set(v2_membership_for(task_id, 400))
    v3_200 = set(sel.get("cap200_node_ids", []))
    v3_400 = set(sel.get("cap400_node_ids", []))
    discovery["rediscovery_sha256"] = _sha256({
        "task_id": task_id,
        "candidate_node_ids": discovery["candidate_node_ids"],
    })
    discovery["v3_selection"] = {
        "cap200_node_ids": sel.get("cap200_node_ids", []),
        "cap400_node_ids": sel.get("cap400_node_ids", []),
        "proximal_nodes": sel.get("proximal_nodes", []),
        "distal_nodes": sel.get("distal_nodes", []),
        "composition_cap200": sel.get("composition_cap200"),
        "composition_cap400": sel.get("composition_cap400"),
        "proximity_by_file": sel.get("proximity_by_file", {}),
        "unknown_touched_paths": sel.get("unknown_touched_paths", []),
        "n_known_touched_paths": sel.get("n_known_touched_paths"),
    }
    # Addendum E: assert V3 derivation == V2 frozen derivation on shared
    # evidence (for tasks with a frozen V2 membership).
    v2_mem = MEMBERSHIP.get("tasks", {}).get(task_id)
    if v2_mem:
        eq = _proximity_equivalence(task_id, sel, v2_mem)
        discovery["proximity_equivalence_v2"] = eq
        if not eq["ok"]:
            raise RuntimeError(
                f"[P2PU-V3] proximity equivalence FAILED for {task_id}: {eq}")
    discovery["membership_diff"] = {
        "v2_cap200": sorted(v2_200),
        "v3_cap200": sorted(v3_200),
        "v2_cap400": sorted(v2_400),
        "v3_cap400": sorted(v3_400),
        "cap200_intersection": sorted(v2_200 & v3_200),
        "cap200_additions": sorted(v3_200 - v2_200),
        "cap200_removals": sorted(v2_200 - v3_200),
        "cap400_intersection": sorted(v2_400 & v3_400),
        "cap400_additions": sorted(v3_400 - v2_400),
        "cap400_removals": sorted(v2_400 - v3_400),
    }
    discovery_file.write_text(json.dumps(discovery, indent=1, ensure_ascii=False),
                              encoding="utf-8")
    print(f"  -> rediscovered {len(discovery['candidate_node_ids'])} nodes; "
          f"cap200={len(v3_200)} cap400={len(v3_400)}")
    return discovery


def selection_nodes_from_discovery(discovery: dict, cap: int) -> list[str]:
    sel = discovery.get("v3_selection", {})
    key = "cap200_node_ids" if cap == 200 else "cap400_node_ids"
    return list(sel.get(key, []))


def selection_node_count(task_id: str, cap: int) -> int:
    discovery_file = OUT_ROOT / f"p2pu_v3_rediscovery_{task_id}.json"
    if not discovery_file.exists():
        return -1
    discovery = json.loads(discovery_file.read_text(encoding="utf-8"))
    return len(selection_nodes_from_discovery(discovery, cap))


# ---------------------------------------------------------------------------
# H6 - collection-session abort (D18)
# ---------------------------------------------------------------------------
def _is_collection_abort(xml_text: str) -> bool:
    """True when a rep JUnit signals a collection failure: 0 testcases OR a
    testcase whose failure/error mentions 'collection'."""
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return False
    cases = list(root.iter("testcase"))
    if len(cases) == 0:
        return True
    for tc in cases:
        for tag in ("failure", "error"):
            el = tc.find(tag)
            if el is None:
                continue
            msg = (el.get("message") or "") + (el.text or "")
            if "collection" in msg.lower():
                return True
    return False


# ---------------------------------------------------------------------------
# V3 execution (20 step 5) - hardened
# ---------------------------------------------------------------------------
def run_p2pu_state(*, task_id: str, era_key: str, worktree_linux: str, tid: str,
                   state: str, cap: int, node_ids: list[str], install_fragment: str,
                   locked_dev_fragment: str, timeout_s: int) -> dict:
    """One (task, state) V3 container; returns a structured result dict.

    ok=True  -> outcomes / failures / junit_files / collection_session_abort
    ok=False -> error: ENV_FAIL_P2PU (reason) or INTEGRITY_FAIL (parse_error)
    """
    wt_name = worktree_linux.rsplit("/", 1)[-1]
    mount = f"{worktree_linux}:/workspace/{wt_name}"
    db_name = fresh_db_name(f"saleor-rc-{tid}", state)
    t0 = time.monotonic()
    ensure_postgres_running()
    ensure_fresh_db(db_name)
    subprocess.run(["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
                    f"cat > {worktree_linux}/.p2pu_nodes.txt"],
                   input=("\n".join(node_ids) + "\n").encode("utf-8"),
                   capture_output=True, timeout=180, check=True)
    runs_script_lines = []
    for rep in range(REPS):
        logf = f"/workspace/{wt_name}/logs/run_{rep}.log"
        runs_script_lines.append(
            f"( mapfile -t NODES < /workspace/{wt_name}/.p2pu_nodes.txt && "
            "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
            f"{PYTEST_FLAGS} "
            f"--junitxml /workspace/{wt_name}/{tid}_{state}_c{cap}_r{rep}.xml -q "
            f'\"${{NODES[@]}}\" >{logf} 2>&1; echo RUN_{rep}_RC=$? >>{logf} )'
        )
    runs_script = " ; ".join(runs_script_lines)
    subprocess.run(["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
                    f"mkdir -p {worktree_linux}/logs; cat > {worktree_linux}/.p2pu_runs.sh"],
                   input=runs_script.encode("utf-8"), capture_output=True, timeout=180, check=True)
    script = (
        "set -e; "
        "uv venv /opt/venv >/dev/null 2>&1 || true; "
        f"{install_fragment}; "
        f"{locked_dev_fragment} >>/tmp/install.log 2>&1 "
        "|| { echo INSTALL_DEV_FAIL; tail -80 /tmp/install.log; exit 2; }; "
        f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 || {{ echo TOOLING_FAIL; "
        "tail -80 /tmp/install.log; exit 2; }; "
        f"cd /workspace/{wt_name} && bash /workspace/{wt_name}/.p2pu_runs.sh; "
        "echo ALL_RUNS_DONE"
    )
    try:
        r = wsl_docker(
            ["run", "--rm", "--network", "host",
             "--ulimit", f"nofile={NOFILE_SOFT}:{NOFILE_HARD}",
             "-e", f"DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/{db_name}",
             "-e", "CACHE_URL=locmem://",
             "-v", mount, "-v", "wp2-uv-cache:/root/.cache/uv",
             f"wp2-era-{era_key}", "bash", "-lc", script],
            timeout_s=timeout_s,
        )
    except subprocess.TimeoutExpired:
        drop_db(db_name)
        return {"ok": False, "error": "ENV_FAIL_P2PU", "reason": "TIMEOUT",
                "db_name": db_name, "stdout_tail": "",
                "wall_s": round(time.monotonic() - t0, 1)}
    stdout = r.stdout or ""

    # H1: persist raw JUnit (read via wsl cat, write on Windows) + SHA-256
    from benchmark.wp2.oracle_confirmation import parse_junit_with_failures
    junit_files: dict[str, str] = {}
    xml_per_rep: dict[int, str | None] = {}
    missing_all = True
    for rep in range(REPS):
        src_name = f"{tid}_{state}_c{cap}_r{rep}.xml"
        rr = wsl(f"cat {worktree_linux}/{src_name} 2>/dev/null || echo __NO_FILE__")
        if "__NO_FILE__" in rr.stdout[:20]:
            junit_files[f"{state}_r{rep}.xml"] = "MISSING"
            xml_per_rep[rep] = None
            continue
        missing_all = False
        junit_dir = OUT_ROOT / "p2pu_v3_junit" / task_id / f"cap{cap}"
        junit_dir.mkdir(parents=True, exist_ok=True)
        out_name = f"{state}_r{rep}.xml"
        # newline="" keeps the raw bytes byte-identical for hash verification.
        (junit_dir / out_name).write_text(rr.stdout, encoding="utf-8",
                                          errors="replace", newline="")
        junit_files[out_name] = _sha256_bytes(rr.stdout.encode("utf-8"))
        xml_per_rep[rep] = rr.stdout

    # H2: install/tooling failure OR all-3-XMLs-missing -> ENV_FAIL_P2PU
    if any(m in stdout for m in INSTALL_FAIL_MARKERS) or missing_all:
        drop_db(db_name)
        reason = "MISSING_XML" if missing_all else "INSTALL"
        return {"ok": False, "error": "ENV_FAIL_P2PU", "reason": reason,
                "db_name": db_name, "stdout_tail": stdout[-4000:],
                "wall_s": round(time.monotonic() - t0, 1)}

    # H3: never swallow parse errors -> INTEGRITY_FAIL
    outcomes: dict[str, list[str]] = {}
    failures: dict[str, str] = {}
    per_rep_missing: dict[int, int] = {}
    parse_error: str | None = None
    for rep in range(REPS):
        xml = xml_per_rep.get(rep)
        if xml is None:
            for n in node_ids:
                outcomes.setdefault(n, []).append("missing")
            per_rep_missing[rep] = len(node_ids)
            continue
        try:
            outs, fails = parse_junit_with_failures(xml)
        except Exception as exc:
            parse_error = f"{type(exc).__name__}: {exc}"
            break
        miss = 0
        for n in node_ids:
            v = outs.get(n, "missing")
            outcomes.setdefault(n, []).append(v)
            if v == "missing":
                miss += 1
            if n in fails:
                failures[n] = fails[n]
        per_rep_missing[rep] = miss
    if parse_error is not None:
        drop_db(db_name)
        return {"ok": False, "error": "INTEGRITY_FAIL", "parse_error": parse_error,
                "db_name": db_name, "stdout_tail": stdout[-3000:],
                "wall_s": round(time.monotonic() - t0, 1)}

    # H6: collection-session abort (D18)
    abort_reps: list[int] = []
    for rep in range(REPS):
        xml = xml_per_rep.get(rep)
        if xml is None or len(node_ids) == 0:
            continue
        if _is_collection_abort(xml) and per_rep_missing.get(rep, 0) / len(node_ids) >= 0.5:
            abort_reps.append(rep)

    drop_db(db_name)
    return {"ok": True, "outcomes": outcomes, "failures": failures,
            "junit_files": junit_files, "collection_session_abort": abort_reps,
            "db_name": db_name, "stdout_tail": stdout[-3000:],
            "wall_s": round(time.monotonic() - t0, 1)}


def _attempt_unit(*, task_id: str, cap: int, node_ids: list[str], era_key: str,
                  parent: str, target: str) -> dict:
    """Run both states once; ok=True with all evidence, or a failure dict."""
    manifests = target_manifests(target)
    wts = ensure_worktrees_v3(task_id, parent, target)
    tid = task_id.split("-")[-1][:12]
    install_t, install_mode, install_evidence = lock_install_script(wts["t"], manifests)
    install_p, _, _ = lock_install_script(wts["p"], manifests)
    locked_dev = locked_dev_install(task_id)
    img_id = base_image_id(era_key)
    lock_sha = lockfile_sha256(manifests)

    t_res = run_p2pu_state(
        task_id=task_id, era_key=era_key, worktree_linux=wts["t"], tid=tid, state="t",
        cap=cap, node_ids=node_ids, install_fragment=install_t,
        locked_dev_fragment=locked_dev, timeout_s=28800)
    p_res = run_p2pu_state(
        task_id=task_id, era_key=era_key, worktree_linux=wts["p"], tid=tid, state="p",
        cap=cap, node_ids=node_ids, install_fragment=install_p,
        locked_dev_fragment=locked_dev, timeout_s=28800)

    for state, res in (("t", t_res), ("p", p_res)):
        if not res.get("ok"):
            remove_worktrees_v3(task_id)
            return {"ok": False, "error": res["error"], "state": state,
                    "detail": {k: v for k, v in res.items() if k != "ok"}}

    return {
        "ok": True,
        "outcomes_t": t_res["outcomes"],
        "outcomes_p": p_res["outcomes"],
        "failures_t": t_res["failures"],
        "failures_p": p_res["failures"],
        "junit_t": t_res["junit_files"],
        "junit_p": p_res["junit_files"],
        "abort_t": t_res["collection_session_abort"],
        "abort_p": t_res["collection_session_abort"],
        "wall_t": t_res["wall_s"],
        "wall_p": t_res["wall_s"],
        "db_t": t_res["db_name"],
        "db_p": p_res["db_name"],
        "install_mode": install_mode,
        "install_evidence": install_evidence,
        "img_id": img_id,
        "lockfile_sha256": lock_sha,
    }


def execute_cap(task_id: str, cap: int, node_ids: list[str], discovery: dict) -> dict:
    """Execute one (task, cap) unit with H1-H8 (retried once on D16/D17)."""
    t0 = time.monotonic()
    parent, target = task_commits(task_id)
    row = inventory_row(task_id)
    era_key = row["era_key"]
    print(f"[P2PU-V3] {task_id} cap={cap} nodes={len(node_ids)} era={era_key}", flush=True)

    clock = clock_preflight()
    if clock["verdict"] == "CLOCK_BLOCKED":
        return {"task_id": task_id, "cap": cap, "status": "CLOCK_BLOCKED"}

    attempt_result = None
    for attempt in (1, 2):
        try:
            attempt_result = _attempt_unit(task_id=task_id, cap=cap, node_ids=node_ids,
                                           era_key=era_key, parent=parent, target=target)
        except Exception as exc:
            remove_worktrees_v3(task_id)
            attempt_result = {"ok": False, "error": "ENV_FAIL_P2PU", "state": "unit",
                              "detail": {"exception": f"{type(exc).__name__}: {exc}"}}
        if attempt_result["ok"]:
            break
        print(f"  {task_id} cap{cap} attempt {attempt} -> {attempt_result['error']} "
              f"(state={attempt_result.get('state')})", flush=True)
        if attempt == 1:
            continue

    clock_after = clock_preflight()
    clock_pre_post = {
        "pre": {"median_skew_s": clock["pre"]["median_skew_s"], "verdict": clock["pre"]["verdict"]},
        "post": {"median_skew_s": clock_after["pre"]["median_skew_s"], "verdict": clock_after["pre"]["verdict"]},
    }

    if not attempt_result["ok"]:
        status = attempt_result["error"]  # ENV_FAIL_P2PU or INTEGRITY_FAIL
        result = {
            "task_id": task_id,
            "cap": cap,
            "status": status,
            "era_key": era_key,
            "rediscovery_sha256": discovery.get("rediscovery_sha256", ""),
            "n_selected": len(node_ids),
            "class_counts": {},
            "n_stable_p2p": 0,
            "node_classes": {},
            "wall_s": round(time.monotonic() - t0, 1),
            "junit_files": {},
            "manifest": {
                "task_id": task_id, "era": era_key, "cap": cap,
                "harness_v3_version": HARNESS_V3_VERSION,
                "harness_v3_spec_sha256": HARNESS_SPEC_SHA256,
                "runner_sha256": RUNNER_SHA256,
                "rediscovery_sha256": discovery.get("rediscovery_sha256", ""),
                "selection_sha256": _sha256(node_ids),
                "pytest_flags": PYTEST_FLAGS,
                "reps": REPS,
                "junit_dir": f"p2pu_v3_junit/{task_id}/cap{cap}",
                "clock_pre_post": clock_pre_post,
                "collection_session_abort": {"t": [], "p": []},
                "workers": 1,
                "failure_detail": attempt_result["detail"],
            },
        }
        result["evidence_sha256"] = _sha256(
            {k: v for k, v in result.items() if k != "evidence_sha256"})
        _write_unit_result(result)
        if status == "INTEGRITY_FAIL":
            raise P2PUIntegrityError(
                f"{task_id} cap{cap} second INTEGRITY_FAIL -> P2PU_INTEGRITY_STOP; "
                f"detail={json.dumps(attempt_result['detail'], ensure_ascii=False)[:800]}")
        return result

    class_counts = {"STABLE_P2P": 0, "TARGET_BROKEN": 0, "PARENT_BROKEN": 0,
                    "BOTH_FAIL": 0, "FLAKY": 0, "COLLECTION_ERROR": 0}
    node_classes = {}
    for nid in node_ids:
        t = attempt_result["outcomes_t"].get(nid, ["missing"] * 3)
        p = attempt_result["outcomes_p"].get(nid, ["missing"] * 3)
        t_list = t if isinstance(t, list) else [t] * 3
        p_list = p if isinstance(p, list) else [p] * 3
        cls = classify_p2p_node(list(p_list), list(t_list))
        class_counts[cls] = class_counts.get(cls, 0) + 1
        node_classes[nid] = cls

    result = {
        "task_id": task_id,
        "cap": cap,
        "status": "DONE",
        "era_key": era_key,
        "rediscovery_sha256": discovery.get("rediscovery_sha256", ""),
        "n_selected": len(node_ids),
        "class_counts": class_counts,
        "n_stable_p2p": class_counts.get("STABLE_P2P", 0),
        "node_classes": node_classes,
        "wall_s": round(time.monotonic() - t0, 1),
        "wall_t_s": attempt_result["wall_t"],
        "wall_p_s": attempt_result["wall_p"],
        "junit_files": {**attempt_result["junit_t"], **attempt_result["junit_p"]},
        "manifest": {
            "task_id": task_id, "era": era_key, "cap": cap,
            "harness_v3_version": HARNESS_V3_VERSION,
            "harness_v3_spec_sha256": HARNESS_SPEC_SHA256,
            "runner_sha256": RUNNER_SHA256,
            "rediscovery_sha256": discovery.get("rediscovery_sha256", ""),
            "selection_sha256": _sha256(node_ids),
            "frozen_base_image_id": attempt_result["img_id"],
            "install_mode": attempt_result["install_mode"],
            "lockfile_sha256": attempt_result["lockfile_sha256"],
            "nofile_soft": NOFILE_SOFT,
            "nofile_hard": NOFILE_HARD,
            "pytest_flags": PYTEST_FLAGS,
            "reps": REPS,
            "db_names": {"t": attempt_result["db_t"], "p": attempt_result["db_p"]},
            "junit_dir": f"p2pu_v3_junit/{task_id}/cap{cap}",
            "clock_pre_post": clock_pre_post,
            "collection_session_abort": {"t": attempt_result["abort_t"],
                                         "p": attempt_result["abort_p"]},
            "workers": 1,
        },
    }
    result["evidence_sha256"] = _sha256(
        {k: v for k, v in result.items() if k != "evidence_sha256"})
    remove_worktrees_v3(task_id)
    _write_unit_result(result)
    print(f"  -> {class_counts}", flush=True)
    return result


# ---------------------------------------------------------------------------
# Evidence + resume (H5), progress (H7), helpers
# ---------------------------------------------------------------------------
def _write_unit_result(result: dict) -> dict:
    (OUT_ROOT / f"p2pu_v3_eng_{result['task_id']}_cap{result['cap']}.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    return result


def _delete_unit_evidence(task_id: str, cap: int) -> None:
    (OUT_ROOT / f"p2pu_v3_eng_{task_id}_cap{cap}.json").unlink(missing_ok=True)
    junit_dir = OUT_ROOT / "p2pu_v3_junit" / task_id / f"cap{cap}"
    if junit_dir.exists():
        import shutil
        shutil.rmtree(junit_dir, ignore_errors=True)


def verify_unit(task_id: str, cap: int) -> tuple[bool, str]:
    """Verified-resume gate (H5): ok only when the result + its JUnit hashes hold."""
    path = OUT_ROOT / f"p2pu_v3_eng_{task_id}_cap{cap}.json"
    if not path.exists():
        return False, "MISSING_RESULT"
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"JSON_LOAD_FAIL: {exc}"
    if "evidence_sha256" not in result:
        return False, "NO_EVIDENCE_SHA"
    recomputed = _sha256({k: v for k, v in result.items() if k != "evidence_sha256"})
    if recomputed != result["evidence_sha256"]:
        return False, "EVIDENCE_HASH_MISMATCH"
    if result.get("status") not in ("DONE", "UNDEFINED", "ENV_FAIL_P2PU"):
        return False, f"BAD_STATUS:{result.get('status')}"
    if result.get("status") == "DONE":
        junit_files = result.get("junit_files", {})
        for name, expected in junit_files.items():
            jpath = OUT_ROOT / "p2pu_v3_junit" / task_id / f"cap{cap}" / name
            if expected == "MISSING" or not jpath.exists():
                return False, f"JUNIT_NOT_ON_DISK:{name}"
            if _file_sha256(jpath) != expected:
                return False, f"JUNIT_HASH_MISMATCH:{name}"
        if len(result.get("node_classes", {})) != result.get("n_selected"):
            return False, "NODE_COUNT_MISMATCH"
    return True, "OK"


def _stop_flag_present() -> bool:
    return (PROJECT / "logs" / "P2PU_STOP.flag").exists()


def load_progress(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def update_progress(path: Path, unit_id: str, status: str, evidence_sha256: str) -> None:
    prog = load_progress(path)
    prog["version"] = "p2p-u-v3-progress-2026-09-26"
    prog.setdefault("units", {})
    prog["units"][unit_id] = {
        "status": status,
        "evidence_sha256": evidence_sha256,
        "finished_utc": _now_utc(),
    }
    path.write_text(json.dumps(prog, indent=1, ensure_ascii=False), encoding="utf-8")


def build_undefined_result(task_id: str, cap: int, discovery: dict) -> dict:
    row = inventory_row(task_id)
    result = {
        "task_id": task_id,
        "cap": cap,
        "status": "UNDEFINED",
        "era_key": row["era_key"],
        "rediscovery_sha256": discovery.get("rediscovery_sha256", ""),
        "n_selected": 0,
        "class_counts": {},
        "n_stable_p2p": 0,
        "node_classes": {},
        "wall_s": 0.0,
        "junit_files": {},
        "manifest": {
            "task_id": task_id, "era": row["era_key"], "cap": cap,
            "harness_v3_version": HARNESS_V3_VERSION,
            "harness_v3_spec_sha256": HARNESS_SPEC_SHA256,
            "runner_sha256": RUNNER_SHA256,
            "rediscovery_sha256": discovery.get("rediscovery_sha256", ""),
            "selection_sha256": _sha256([]),
            "pytest_flags": PYTEST_FLAGS,
            "reps": REPS,
            "junit_dir": f"p2pu_v3_junit/{task_id}/cap{cap}",
            "workers": 1,
        },
    }
    result["evidence_sha256"] = _sha256(
        {k: v for k, v in result.items() if k != "evidence_sha256"})
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default=None)
    ap.add_argument("--cap", type=int, default=None, choices=(200, 400))
    ap.add_argument("--all-tasks", action="store_true")
    ap.add_argument("--discovery-only", action="store_true")
    ap.add_argument("--max-units", type=int, default=None,
                    help="process at most N EXECUTED units per invocation "
                         "(0 = list the plan only and exit)")
    ap.add_argument("--progress-file", default=None)
    args = ap.parse_args()
    tasks = [args.task] if args.task else (load_v3_oracle_valid_eng() if args.all_tasks else [])
    caps = [args.cap] if args.cap else [200, 400]
    if not tasks:
        print("no tasks selected; use --task or --all-tasks")
        return 2

    # D12 plan: sorted task_id; within a task cap200 then cap400.
    plan = [(tid, cap) for tid in sorted(tasks) for cap in caps]
    print(f"[P2PU-V3] plan: {len(plan)} units "
          f"(D12 order: sorted task_id, cap200 then cap400)", flush=True)

    if args.max_units is not None and args.max_units == 0:
        n_undef = 0
        for i, (tid, cap) in enumerate(plan, 1):
            n = selection_node_count(tid, cap)
            undefined = n == 0
            n_undef += int(undefined)
            tag = "UNDEFINED" if undefined else (f"{n} nodes" if n > 0 else "rediscovery-pending")
            print(f"  {i:2d}. {tid} cap{cap} -> {tag}", flush=True)
        print(f"[P2PU-V3] plan: {len(plan)} units; {n_undef} UNDEFINED; "
              f"{len(plan) - n_undef} planned for execution", flush=True)
        return 0

    progress_path = Path(args.progress_file) if args.progress_file else OUT_ROOT / "p2pu_v3_progress.json"
    executed = 0
    for i, (tid, cap) in enumerate(plan, 1):
        if _stop_flag_present():
            print("[P2PU-V3] P2PU_STOP.flag present; stopping cleanly (D08)", flush=True)
            break
        unit_id = f"{tid}_cap{cap}"
        result_file = OUT_ROOT / f"p2pu_v3_eng_{tid}_cap{cap}.json"
        if result_file.exists():
            ok, reason = verify_unit(tid, cap)
            if ok:
                print(f"  {i:2d}. {unit_id} verified; skip (resume)", flush=True)
                continue
            print(f"  {i:2d}. {unit_id} verify FAILED ({reason}); "
                  "C09 delete partial evidence and rerun", flush=True)
            _delete_unit_evidence(tid, cap)
        discovery = ensure_discovery(tid)
        if args.discovery_only:
            continue
        node_ids = selection_nodes_from_discovery(discovery, cap)
        if not node_ids:
            print(f"  {i:2d}. {tid} cap{cap} UNDEFINED (zero nodes)", flush=True)
            res = build_undefined_result(tid, cap, discovery)
            _write_unit_result(res)
            update_progress(progress_path, unit_id, res["status"],
                            res.get("evidence_sha256", ""))
            continue
        if args.max_units is not None and executed >= args.max_units:
            print(f"[P2PU-V3] reached --max-units {args.max_units}; stopping invocation", flush=True)
            break
        res = execute_cap(tid, cap, node_ids, discovery)
        update_progress(progress_path, unit_id, res["status"],
                        res.get("evidence_sha256", ""))
        executed += 1
    print(f"[P2PU-V3] complete (executed units this invocation: {executed})", flush=True)
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except P2PUIntegrityError as exc:
        print(f"[P2PU-V3] {exc}", flush=True)
        print("P2PU_INTEGRITY_STOP", flush=True)
        rc = 3
    raise SystemExit(rc)
