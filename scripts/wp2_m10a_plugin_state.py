#!/usr/bin/env python3
"""WP-2 Mission-10A: frozen V2 installed state + pytest plugin-layer proof.

ZERO API. ENV introspection only (Mission-10A sections 12, 17). For the two
suspect packages (pytest-django-queries, pytest-mock) prove all four layers in
a NON-FROZEN scratch container that replicates the frozen V2 install exactly:

  Layer 1 PACKAGE      - distribution installed? exact version?
  Layer 2 ENTRY POINT  - pytest11 entry point registered?
  Layer 3 PYTEST LOAD  - plugin actually loaded (pytest --trace-config)?
  Layer 4 FIXTURE      - expected fixture visible (pytest --fixtures)?

Also records the V2 install commands verbatim (deps_install_cmd +
TOOLING_INSTALL) and the installed package diff. Writes
frozen_v2_installed_state.json + pytest_plugin_state.json.

Usage:
    python scripts/wp2_m10a_plugin_state.py --era py312 --task saleor-rc-...
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from scripts.wp2_linux_dryrun import (  # noqa: E402
    TOOLING_INSTALL,
    WSL_WT,
    deps_install_cmd,
    ensure_cache,
    ensure_era_images,
    wsl,
    wsl_docker,
)

OUT_ROOT = PROJECT / "research" / "wp2" / "mission10a_env_audit_2026-09-26"
ERA_KEY = "py312"

# Target commit for task saleor-rc-74538ea00ce9 (py312, declares the dev group)
TARGET_COMMIT = "74538ea00ce938489bcd36b180e3b9b31f265e40"
TARGET_COMMITS = {
    "py312": "74538ea00ce938489bcd36b180e3b9b31f265e40",
    "py39": "e03ee76d2b895c707dbd9ee7fe8ff4b1c3cee026",
}

SUSPECT_PACKAGES = ("pytest-django-queries", "pytest-mock")
EXPECTED_FIXTURES = {"pytest-django-queries": "count_queries", "pytest-mock": "mocker"}


def wsl_script(script: str, timeout_s: int = 1800) -> str:
    r = wsl(script, timeout_s=timeout_s)
    if r.returncode != 0:
        return f"__RC_{r.returncode}__\n" + r.stdout[-3000:] + "\n" + r.stderr[-3000:]
    return r.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--era", default=ERA_KEY)
    ap.add_argument("--task", default="saleor-rc-74538ea00ce9")
    args = ap.parse_args()
    era_key = args.era
    out_root = OUT_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    ensure_cache()
    ensure_era_images()

    # Build a scratch worktree for the task's target commit so deps_install_cmd
    # has a real workspace (V2 install semantics require a checkout).
    tid_short = args.task.split("-")[-1][:12]
    wt = f"{WSL_WT}/{tid_short}_m10a_introspect"
    wsl(f"git -C /opt/wp2_v2/saleor-cache worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    r = wsl(f"git -C /opt/wp2_v2/saleor-cache worktree add --detach {wt} {TARGET_COMMITS[era_key]}")
    if r.returncode != 0:
        print("worktree add FAILED:", r.stderr[-1200:])
        return 2

    base_in_container = f"/workspace/{wt.rsplit('/', 1)[-1]}"
    deps_cmd = deps_install_cmd(wt, era_key)
    script = (
        "set -e; "
        "uv venv /opt/venv >/dev/null 2>&1 || true; "
        f"{deps_cmd} "
        ">/tmp/install.log 2>&1 "
        f"|| {{ echo INSTALL_DEP_FAIL; tail -30 /tmp/install.log; exit 3; }}; "
        f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 || {{ echo INSTALL_TOOL_FAIL; exit 4; }}; "
        "FIXED_PATH=" + base_in_container + "/m10a_introspect_results.txt; "
        "rm -f " + base_in_container + "/m10a_introspect_results.txt; "
        "{ echo '=== PIP_FREEZE ==='; uv pip list --python /opt/venv/bin/python 2>/dev/null | sort; "
        "echo '=== ENTRYPOINTS ==='; /opt/venv/bin/python -c \"import importlib.metadata as md; "
        "[print(ep.group + '|' + ep.name + '|' + ep.value) for d in md.distributions() for ep in d.entry_points if ep.group=='pytest11']\" | sort; "  # noqa: E501
        "echo '=== TRACE_CONFIG ==='; "
        "cd /tmp && /opt/venv/bin/python -m pytest --trace-config -p no:cacheprovider -o addopts= 2>&1 | grep -iE 'plugin.*(pytest-django-queries|pytest_mock|django_queries|pytest-mock)' | head -20; "  # noqa: E501
        "echo '=== FIXTURES ==='; "
        "cd /tmp && /opt/venv/bin/python -m pytest --fixtures -p no:cacheprovider -o addopts= 2>&1 | grep -E 'count_queries|mocker' | head -20; "  # noqa: E501
        "echo '=== INSTALL_TAIL ==='; tail -5 /tmp/install.log; "
        "} > " + base_in_container + "/m10a_introspect_results.txt 2>&1; "
        "echo RESULTS_FILE_WRITTEN"
    )
    container_name = f"wp2-m10a-introspect-{era_key}"
    wsl_docker(["rm", "-f", container_name], timeout_s=60)
    r = wsl_docker(
        [
            "run", "--rm", "--network", "host",
            "--name", container_name,
            "-e", "DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/m10a_introspect",
            "-e", "CACHE_URL=locmem://",
            "-v", f"{wt}:/workspace/{wt.rsplit('/',1)[-1]}",
            "-v", "wp2-uv-cache:/root/.cache/uv",
            f"wp2-era-{era_key}",
            "bash", "-lc", script,
        ],
        timeout_s=3600,
    )
    stdout = r.stdout
    if r.returncode != 0 and "INSTALL" in stdout:
        print("install failed:", stdout[-2000:].encode("ascii", "replace").decode())
        wsl(f"git -C /opt/wp2_v2/saleor-cache worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
        return 3

    # Read the results file written inside the container (avoids stdout truncation).
    rf = wsl(f"cat {wt}/m10a_introspect_results.txt 2>/dev/null || echo __NO_RESULTS__")
    if "__NO_RESULTS__" in rf.stdout[:20]:
        print("results file missing; stdout tail:", stdout[-1000:].encode("ascii", "replace").decode())
        wsl(f"git -C /opt/wp2_v2/saleor-cache worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
        return 4
    results_text = rf.stdout

    def section(name: str) -> str:
        for line in results_text.splitlines():
            if line.strip() == name:
                return name
        return ""

    def between(start: str, end: str | None = None) -> str:
        lines = results_text.splitlines()
        out: list[str] = []
        in_sec = False
        for line in lines:
            if line.strip() == start:
                in_sec = True
                continue
            if in_sec and end and line.strip() == end:
                break
            if in_sec:
                out.append(line)
        return "\n".join(out)

    pip_freeze = between("=== PIP_FREEZE ===", "=== ENTRYPOINTS ===")
    entrypoints = between("=== ENTRYPOINTS ===", "=== TRACE_CONFIG ===")
    trace_config = between("=== TRACE_CONFIG ===", "=== FIXTURES ===")
    fixtures = between("=== FIXTURES ===", "=== INSTALL_TAIL ===")

    freeze_pkgs: dict[str, str] = {}
    for line in pip_freeze.splitlines():
        parts = line.split()
        if len(parts) >= 2 and "Package" not in parts[0] and "Version" not in parts[0]:
            freeze_pkgs[parts[0].strip()] = parts[1].strip()

    plugin_state: dict[str, dict] = {}
    installed_state: dict[str, dict] = {}
    for pkg in SUSPECT_PACKAGES:
        layer1 = pkg in freeze_pkgs
        version = freeze_pkgs.get(pkg, "")
        layer2 = pkg.replace("-", "_") in entrypoints or pkg in entrypoints
        layer3 = pkg.replace("-", "_") in trace_config or pkg in trace_config
        fixture = EXPECTED_FIXTURES.get(pkg, "")
        layer4 = fixture in fixtures
        plugin_state[pkg] = {
            "PACKAGE_INSTALLED": layer1,
            "version": version,
            "ENTRY_POINT_REGISTERED": layer2,
            "PLUGIN_LOADED": layer3,
            "FIXTURE_VISIBLE": layer4,
            "expected_fixture": fixture,
            "fixtures_grep": fixtures.strip(),
            "trace_config_grep": trace_config.strip(),
            "layer": "1:PACKAGE 2:ENTRYPOINT 3:LOAD 4:FIXTURE",
        }
        installed_state[pkg] = {
            "installed": layer1,
            "version": version,
        }

    base_image = wsl_docker(["image", "inspect", f"wp2-era-{era_key}", "--format", "{{.Id}}"]).stdout.strip()

    out = {
        "artifact": "frozen_v2_installed_state",
        "schema_version": "mission10a-installed-state-v1",
        "created_utc": _now_utc(),
        "task_id": args.task,
        "eras": {
            era_key: {
                "era_key": era_key,
                "task_id": args.task,
                "target_commit": TARGET_COMMITS[era_key],
                "base_image_id": base_image,
                "container": container_name,
                "v2_install_commands": {
                    "deps_install_cmd": deps_cmd,
                    "tooling_install": TOOLING_INSTALL,
                },
                "installed": installed_state,
                "n_installed_packages": len(freeze_pkgs),
                "pip_freeze_head": "\n".join(sorted(freeze_pkgs)[:60]),
            }
        },
    }
    # accumulate across eras (each run adds one era)
    state_path = out_root / "frozen_v2_installed_state.json"
    if state_path.exists():
        prev = json.loads(state_path.read_text(encoding="utf-8"))
        if isinstance(prev.get("eras"), dict):
            prev["eras"].update(out["eras"])
            prev["created_utc"] = out["created_utc"]
            out = prev
    state_path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    plugin_out = {
        "artifact": "pytest_plugin_state",
        "schema_version": "mission10a-plugin-state-v1",
        "created_utc": _now_utc(),
        "task_id": args.task,
        "eras": {
            era_key: {
                "era_key": era_key,
                "task_id": args.task,
                "target_commit": TARGET_COMMITS[era_key],
                "base_image_id": base_image,
                "plugin_state": plugin_state,
                "entrypoints_raw": entrypoints.strip(),
                "trace_config_raw": trace_config.strip(),
                "fixtures_raw": fixtures.strip(),
            }
        },
        "layer_model": {
            "Layer1": "PACKAGE distribution installed",
            "Layer2": "PYTEST ENTRY POINT (pytest11) registered",
            "Layer3": "PYTEST LOAD (--trace-config) proves plugin loaded",
            "Layer4": "FIXTURE visible via --fixtures",
        },
    }
    p_path = out_root / "pytest_plugin_state.json"
    if p_path.exists():
        prev = json.loads(p_path.read_text(encoding="utf-8"))
        if isinstance(prev.get("eras"), dict):
            prev["eras"].update(plugin_out["eras"])
            prev["created_utc"] = plugin_out["created_utc"]
            plugin_out = prev
    p_path.write_text(json.dumps(plugin_out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in plugin_state.items()}, indent=1))
    print("installed:", installed_state)
    print("n_installed_packages:", len(freeze_pkgs))
    print("wrote frozen_v2_installed_state.json + pytest_plugin_state.json")

    wsl(f"rm -f {wt}/m10a_introspect_results.txt")
    wsl(f"git -C /opt/wp2_v2/saleor-cache worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    return 0


def _now_utc() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
