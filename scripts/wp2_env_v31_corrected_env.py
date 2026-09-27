#!/usr/bin/env python3
"""WP-2 Env Closure V3.1 E5 - build + prove CORRECTED V3 environments.

For each task: EXISTING V3 MAIN recipe (unchanged) + rule-based exact historical
DEV/TEST closure (compiler-derived) + frozen tooling, then preflight:
- pip check (E5.4)
- plugin trace + markers (E5.5)
- collection preflight (E5.6)
- fixture-resolution preflight, zero test-body execution (E5.7)
- VCR provider audit (E5.8/E5.9)
Persists research/wp2/harness_v3_2026-09-26/env_closure_v31_corrected_env/<task_id>/.

Usage:
    python scripts/wp2_env_v31_corrected_env.py --all [--max-tasks N] [--task ID]
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

OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
CENSUS = json.loads((PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" /
                     "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
INVENTORY = json.loads((PROJECT / "research" / "wp2/" /
                        "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json").read_text(encoding="utf-8"))
WSL_CACHE = "/opt/wp2_v2/saleor-cache"
WSL_WT = "/opt/wp2_v2/worktrees"
DISTRO = "Ubuntu-24.04"

from benchmark.wp2.harness_v3 import (  # noqa: E402
    NOFILE_HARD,
    NOFILE_SOFT,
    TOOLING_INSTALL,
    lock_install_script,
    locked_dev_install,
    target_manifests,
    v31_dev_closure,
)

NEW_ROOT = OUT_ROOT / "env_closure_v31_corrected_env"

FIXTURE_PLUGIN = r'''
"""v31 fixture-resolution preflight plugin (zero test-body execution)."""
import json
from pathlib import Path

BUILTIN = {
    "request", "pytestconfig", "record_property", "record_xml_attribute",
    "record_testsuite_property", "capsys", "capfd", "capsysbinary", "capfdbinary",
    "caplog", "monkeypatch", "tmp_path", "tmp_path_factory", "tmpdir",
    "tmpdir_factory", "cache", "doctest_namespace", "recwarn", "pytester",
    "pytester_example_path",
}


def pytest_collection_modifyitems(session, config, items):
    unresolved = {}
    checked = {}
    for item in items:
        fi = getattr(item, "_fixtureinfo", None)
        if fi is None:
            continue
        n2f = getattr(fi, "name2fixturedefs", {}) or {}
        names = list(getattr(fi, "argnames", None) or [])
        miss = []
        for fname in names:
            if fname in BUILTIN:
                continue
            defs = n2f.get(fname)
            if not defs:
                miss.append(fname)
        checked[item.nodeid] = sorted(names)
        if miss:
            unresolved[item.nodeid] = miss
    out = {"unresolved": unresolved, "checked": len(items), "checked_nodes": checked}
    out_path = Path.cwd() / "fixture_preflight.json"
    out_path.write_text(json.dumps(out), encoding="utf-8")
'''


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def task_commits(task_id: str) -> tuple[str, str]:
    for t in CENSUS.get("tasks", []):
        if t["task_id"] == task_id:
            return t["parent_commit"], t["target_commit"]
    raise KeyError(task_id)


def era_of(task_id: str) -> str:
    for r in INVENTORY["tasks"]:
        if r["task_id"] == task_id:
            return r["era_key"]
    return ""


def collect_files(task_id: str) -> list[str]:
    for r in INVENTORY["tasks"]:
        if r["task_id"] == task_id:
            all_associated = r.get("associated_unchanged_test_files", [])
            return sorted(
                f for f in all_associated
                if f.endswith(".py") and "[" not in f and "]" not in f
                and not f.endswith("__init__.py") and not f.endswith("conftest.py"))
    return []


def wsl(script: str, timeout_s: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["wsl", "-d", DISTRO, "--", "bash", "-lc", script],
                          capture_output=True, text=True, encoding="utf-8", timeout=timeout_s)


def build_corrected(task_id: str) -> dict:
    parent, target = task_commits(task_id)
    era = era_of(task_id)
    tid = task_id.split("-")[-1][:12]
    wt = f"{WSL_WT}/{tid}_v31_new_t"
    wt_name = wt.rsplit("/", 1)[-1]
    t0 = time.monotonic()

    manifests = target_manifests(target)
    install_frag, install_mode, _ = lock_install_script(wt, manifests)
    dev_frag = locked_dev_install(task_id)
    closure = v31_dev_closure(task_id)
    cfiles = collect_files(task_id)

    wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    r = wsl(f"git -C {WSL_CACHE} worktree add --detach {wt} {target}", timeout_s=180)
    if r.returncode != 0:
        return {"task_id": task_id, "status": "WORKTREE_FAIL", "error": r.stderr[-800:]}

    # write fixture preflight plugin + collect files
    subprocess.run(["wsl", "-d", DISTRO, "--", "bash", "-lc",
                    f"cat > {wt}/v31_fixture_preflight.py"],
                   input=FIXTURE_PLUGIN.encode("utf-8"), capture_output=True, timeout=120)
    subprocess.run(["wsl", "-d", DISTRO, "--", "bash", "-lc",
                    f"cat > {wt}/.v31_collect_files.txt"],
                   input=("\n".join(cfiles) + "\n").encode("utf-8"), capture_output=True, timeout=120)

    script = (
        "set -e; "
        "uv venv /opt/venv >/dev/null 2>&1 || true; "
        f"{install_frag}; "
        f"{dev_frag} >>/tmp/install.log 2>&1 "
        "|| { echo INSTALL_DEV_FAIL; tail -60 /tmp/install.log; exit 2; }; "
        f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 "
        "|| { echo TOOLING_FAIL; tail -80 /tmp/install.log; exit 2; }; "
        f"cd /workspace/{wt_name} && "
        "set +e; "
        "uv pip check --python /opt/venv/bin/python > /workspace/" + wt_name + "/pipcheck.txt 2>&1; "
        "echo PIPCHECK_RC=$? >> /workspace/" + wt_name + "/pipcheck.txt; "
        "uv pip freeze --python /opt/venv/bin/python > /workspace/" + wt_name + "/freeze.txt; "
        "/opt/venv/bin/python -V > /workspace/" + wt_name + "/pyversion.txt 2>&1; "
        "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
        "--ds=saleor.tests.settings --version > /workspace/" + wt_name + "/pytestversion.txt 2>&1; "
        "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
        "--ds=saleor.tests.settings --trace-config 2>&1 | head -2000 > /workspace/" + wt_name + "/traceconfig.txt; "
        "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
        "--ds=saleor.tests.settings --markers > /workspace/" + wt_name + "/markers.txt 2>&1; "
        "mapfile -t FILES < /workspace/" + wt_name + "/.v31_collect_files.txt; "
        "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
        "--ds=saleor.tests.settings --collect-only -q \"${FILES[@]}\" "
        "> /workspace/" + wt_name + "/collect.txt 2>&1; echo COLLECT_RC=$? >> /workspace/" + wt_name + "/collect.txt; "
        "PYTHONPATH=/workspace/" + wt_name + " /opt/venv/bin/python -m pytest "
        "-p no:cacheprovider -o addopts= -p v31_fixture_preflight "
        "--ds=saleor.tests.settings --collect-only -q \"${FILES[@]}\" "
        "> /workspace/" + wt_name + "/fixture_collect.txt 2>&1; "
        "echo FIXTURE_RC=$? >> /workspace/" + wt_name + "/fixture_collect.txt; "
        "cp /tmp/install.log /workspace/" + wt_name + "/install.log; "
        "echo CORRECTED_ENV_DONE"
    )
    rc = subprocess.run(
        ["wsl", "-d", DISTRO, "--", "bash", "-lc", "cat > " + wt + "/.v31_new.sh"],
        input=script.encode("utf-8"), capture_output=True, timeout=120)
    if rc.returncode != 0:
        return {"task_id": task_id, "status": "SCRIPT_WRITE_FAIL", "error": rc.stderr[-500:]}

    r = subprocess.run(
        ["wsl", "-d", DISTRO, "--", "docker", "run", "--rm", "--network", "host",
         "--ulimit", f"nofile={NOFILE_SOFT}:{NOFILE_HARD}",
         "-v", f"{wt}:/workspace/{wt_name}",
         "-v", "wp2-uv-cache:/root/.cache/uv",
         f"wp2-era-{era}", "bash", f"/workspace/{wt_name}/.v31_new.sh"],
        capture_output=True, text=True, encoding="utf-8", timeout=3600)
    container_rc = r.returncode
    stdout = r.stdout or ""
    stderr = r.stderr or ""

    def read_back(name: str) -> tuple[str, str | None]:
        rr = wsl(f"cat {wt}/{name} 2>/dev/null || echo __NO_FILE__")
        if "__NO_FILE__" in rr.stdout[:20]:
            return "", None
        return rr.stdout, _sha(rr.stdout)

    names = ("freeze.txt", "pyversion.txt", "pytestversion.txt", "traceconfig.txt",
             "markers.txt", "pipcheck.txt", "collect.txt", "fixture_collect.txt",
             "fixture_preflight.json", "install.log")
    files = {}
    for name in names:
        text, sha = read_back(name)
        files[name] = {"sha256": sha, "lines": len(text.splitlines()) if text else 0}
    install_text, _ = read_back("install.log")
    dev_pins_unavailable = _extract_unavailable(install_text)

    task_dir = NEW_ROOT / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        text, _ = read_back(name)
        (task_dir / name).write_text(text, encoding="utf-8", errors="replace", newline="")

    freeze_text, _ = read_back("freeze.txt")
    pipcheck_text, _ = read_back("pipcheck.txt")
    collect_text, _ = read_back("collect.txt")
    fixture_text, _ = read_back("fixture_preflight.json")
    trace_text, _ = read_back("traceconfig.txt")

    pip_rc = _rc_from(pipcheck_text)
    collect_rc = _rc_from(collect_text)
    collect_ok = collect_rc == 0
    fixture_data = None
    try:
        fixture_data = json.loads(fixture_text) if fixture_text else None
    except Exception:
        fixture_data = None
    unresolved_fixtures = (fixture_data or {}).get("unresolved", {})
    fixture_ok = collect_ok and not unresolved_fixtures

    # VCR provider audit (E5.8): historically declared VCR family must be loaded.
    vcr_family = closure.get("vcr_family_present", [])
    trace_loaded = [ln for ln in trace_text.splitlines() if "PLUGIN registered" in ln]
    loaded_plugins = [ln.split("'")[1] if "'" in ln else "" for ln in trace_loaded]
    loaded_names = " ".join(loaded_plugins)
    vcr_unresolved = []
    for provider in vcr_family:
        pkg = {"pytest-vcr": "pytest_vcr", "pytest-recording": "pytest_recording",
               "vcrpy": "vcr", "pytest-socket": "pytest_socket"}.get(provider, provider)
        if pkg not in loaded_names and provider != "vcrpy":
            vcr_unresolved.append(provider)

    rec = {
        "task_id": task_id,
        "era_key": era,
        "target_commit": target,
        "install_mode": install_mode,
        "install_fragment": install_frag,
        "dev_pins": closure.get("pins", []),
        "dev_all_locked_n": len((closure.get("all_locked_pins") or {}).get("pins", [])),
        "dev_pins_unavailable": dev_pins_unavailable,
        "dev_test_closure": {
            "mechanism": closure.get("mechanism"),
            "n_pins": len(closure.get("pins", [])),
            "pins_sha256": closure.get("pins_sha256"),
            "unsupported": closure.get("unsupported", []),
            "vcr_family_present": vcr_family,
        },
        "container_rc": container_rc,
        "pip_check": {"rc": pip_rc, "ok": pip_rc == 0, "text_tail": pipcheck_text[-2000:]},
        "collect": {"rc": collect_rc, "ok": collect_ok, "text_tail": collect_text[-2000:]},
        "fixture_preflight": {"ok": fixture_ok, "n_checked": (fixture_data or {}).get("checked", 0),
                              "n_unresolved": len(unresolved_fixtures),
                              "unresolved": {k: v for k, v in list(unresolved_fixtures.items())[:20]}},
        "vcr_preflight": {"unresolved": vcr_unresolved},
        "files": files,
        "freeze_sha256": files["freeze.txt"]["sha256"],
        "freeze_packages": len(freeze_text.splitlines()) if freeze_text else 0,
        "wall_s": round(time.monotonic() - t0, 1),
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-1000:],
    }
    (task_dir / "record.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    wsl(f"git -C {WSL_CACHE} worktree prune 2>/dev/null || true")
    print(f"  {task_id} corrected mode={install_mode} pins={len(closure.get('pins', []))} "
          f"pip_rc={pip_rc} collect_rc={collect_rc} fixture_ok={fixture_ok} "
          f"vcr_unresolved={vcr_unresolved} pkgs={rec['freeze_packages']} wall={rec['wall_s']}s")
    return rec


def _rc_from(text: str) -> int | None:
    for line in text.splitlines():
        if line.startswith(("PIPCHECK_RC=", "COLLECT_RC=", "FIXTURE_RC=")):
            try:
                return int(line.split("=")[1].strip())
            except Exception:
                return None
    return None


def _extract_unavailable(install_log: str) -> list[str]:
    import re
    out: list[str] = []
    for pat in (r"no version of ([A-Za-z0-9_.-]+==[^ ]+)",
                r"([A-Za-z0-9_.-]+==[^ ]+) has no wheels"):
        for m in re.finditer(pat, install_log):
            pin = m.group(1)
            if pin not in out:
                out.append(pin)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--max-tasks", type=int, default=9999)
    args = ap.parse_args()
    if args.task:
        tasks = [args.task]
    else:
        eng = json.loads((OUT_ROOT / "eng_v3_oracle_ready.json").read_text(encoding="utf-8"))
        tasks = sorted(eng["oracle_valid_union_task_ids"])
    done = 0
    for tid in tasks:
        if done >= args.max_tasks:
            break
        rec_path = NEW_ROOT / tid / "record.json"
        if rec_path.exists():
            print(f"  {tid} already built; skip")
            continue
        build_corrected(tid)
        done += 1
    print(f"[E5] corrected-env build complete (done this invocation: {done})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
