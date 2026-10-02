#!/usr/bin/env python3
"""WP2 M16 conditional S3 storage maintenance helper (human-run only). ZERO model API.

Never run by a controller. Used ONLY when the frozen resource gate says S3_REQUIRED.

  probe       read-only capability probe of this Windows/WSL/Docker host; writes the
              probe record and machine-specific human compaction instructions (nothing is run)
  inventory   read-only Docker volume inventory; freezes the explicit deletion allow-list
              (anonymous 64-hex name AND referenced by no container AND not protected)
  delete      deletes ONLY the frozen allow-list, one `docker volume rm <name>` at a time,
              after re-checking each volume right before deletion; requires --inventory-sha
  measure     storage snapshot (before/after compaction)
  post-check  Docker/WSL health + era images + protected volumes + frozen-hash health
It never calls `docker volume prune`, `docker system prune`, or any compaction command.
Protected forever: wp2-uv-cache, wp2-pg and its volumes, every named (non-hex) volume, every
volume referenced by any container (running or stopped).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
for _p in (PROJECT, PROJECT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m16_resource as resource  # noqa: E402
from scripts.wp2_m16_run import hash_ok, load, now, self_hash, write  # noqa: E402

MAINT = PROJECT / "research/wp2/m16_v1/maintenance"
PROBE = MAINT / "capability_probe.json"
INSTR = MAINT / "COMPACTION_INSTRUCTIONS.md"
INVENTORY = MAINT / "volume_inventory.json"
DELETIONS = MAINT / "deletions.jsonl"
PROTECTED_NAMES = ("wp2-uv-cache",)
PROTECTED_CONTAINERS = ("wp2-pg",)
ANON_RE = re.compile(r"^[0-9a-f]{64}$")


def run(cmd: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    def dec(b: bytes) -> str:
        if b.count(b"\x00") > len(b) // 4:            # wsl.exe prints UTF-16LE
            return b.decode("utf-16-le", "replace")
        return b.decode("utf-8", "replace")
    return subprocess.CompletedProcess(cmd, r.returncode, dec(r.stdout or b""), dec(r.stderr or b""))


def wsl(script: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return run(["wsl", "-d", resource.DISTRO, "--", "bash", "-lc", script], timeout)


# ------------------------------------------------------------------ classification (pure)
def classify_volume(name: str, referenced_by: list[str], protected_container_volumes: set[str]) -> dict:
    """Pure (unit-tested). delete_allowed only for anonymous, unreferenced, unprotected volumes."""
    reasons = []
    if name in PROTECTED_NAMES:
        reasons.append("PROTECTED_NAME")
    if name in protected_container_volumes:
        reasons.append("USED_BY_PROTECTED_CONTAINER")
    if not ANON_RE.match(name):
        reasons.append("NAMED_VOLUME")
    if referenced_by:
        reasons.append("REFERENCED_BY_CONTAINER")
    allowed = not reasons
    protected = any(r in reasons for r in ("PROTECTED_NAME", "USED_BY_PROTECTED_CONTAINER", "NAMED_VOLUME"))
    return {"name": name, "referenced_by": referenced_by, "protected": protected,
            "classification": "REBUILDABLE_CACHE" if allowed else "KEEP", "delete_allowed": allowed,
            "reasons": reasons or ["ANONYMOUS_UNREFERENCED"]}


def volume_refs(name: str) -> list[str]:
    r = wsl(f"docker ps -a --filter volume={name} --format '{{{{.Names}}}}'", 120)
    if r.returncode:
        raise SystemExit(f"cannot list references for {name}: {r.stderr[-300:]}")
    return sorted(x for x in r.stdout.split() if x)


def protected_container_volumes() -> set[str]:
    out = set()
    for c in PROTECTED_CONTAINERS:
        r = wsl(f"docker inspect {c} --format '{{{{range .Mounts}}}}{{{{.Name}}}} {{{{end}}}}'", 120)
        if r.returncode:                                   # fail closed: unknown mounts -> no deletion
            raise SystemExit(f"cannot inspect protected container {c}: {(r.stderr or '')[-300:]}")
        out |= {x for x in r.stdout.split() if x}
    return out


def volume_sizes() -> dict[str, int | None]:
    r = wsl("docker system df -v --format '{{json .Volumes}}'", 900)
    sizes: dict[str, int | None] = {}
    try:
        for v in json.loads(r.stdout.strip() or "[]"):
            sizes[v.get("Name")] = _bytes(v.get("Size"))
    except ValueError:
        pass
    return sizes


def _bytes(s: object) -> int | None:
    if not isinstance(s, str):
        return None
    m = re.match(r"^\s*([\d.]+)\s*([kKMGT]?B)\s*$", s)
    if not m:
        return None
    mult = {"B": 1, "kB": 1e3, "KB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12}[m.group(2)]
    return int(float(m.group(1)) * mult)


# ------------------------------------------------------------------ commands
def probe() -> int:
    h = run(["wsl", "--help"])
    v = run(["wsl", "--version"])
    ps = run(["powershell", "-NoProfile", "-Command",
              "if (Get-Command Optimize-VHD -ErrorAction SilentlyContinue) {'YES'} else {'NO'}"])
    dp = run(["where", "diskpart"])
    vh = resource.vhdx_path()
    d = {"artifact": "m16_s3_capability_probe", "artifact_sha256": "", "utc": now(),
         "wsl_version_text": v.stdout.strip()[:2000], "wsl_supports_manage": "--manage" in h.stdout,
         "wsl_supports_set_sparse": "--set-sparse" in h.stdout,
         "optimize_vhd_available": ps.stdout.strip().endswith("YES"),
         "diskpart_available": dp.returncode == 0, "vhdx_path": vh,
         "vhdx": resource.file_size_info(vh), "c_free_gib": round(resource.c_free_gib(), 3),
         "docker_info_ok": wsl("docker info >/dev/null 2>&1 && echo OK").stdout.strip() == "OK",
         "commands_executed": "read-only probes only"}
    write(PROBE, self_hash(d))
    lines = ["# M16 S3 - vhdx compaction instructions for THIS machine (generated, not executed)", "",
             f"VHDX: `{vh}`", "", "Run only after `delete` finished and with every controller stopped.", "",
             "1. Measure: `python scripts/wp2_m16_maint.py measure --label pre_compaction`",
             "2. Stop WSL (admin PowerShell): `wsl --shutdown`; wait until `wsl --list --running` "
             "lists nothing."]
    if d["optimize_vhd_available"]:
        lines += [f"3. Compact (admin PowerShell): `Optimize-VHD -Path \"{vh}\" -Mode Full`"]
    elif d["diskpart_available"]:
        lines += ["3. Compact with diskpart (admin): run `diskpart`, then type:",
                  f"   `select vdisk file=\"{vh}\"`", "   `attach vdisk readonly`", "   `compact vdisk`",
                  "   `detach vdisk`", "   `exit`"]
    else:
        lines += ["3. No supported compaction tool was found on this machine: STOP and send the probe "
                  "record to the brain."]
    if d["wsl_supports_set_sparse"]:
        lines += ["   (Optional, only if the brain approves: the installed WSL supports "
                  "`wsl --manage <distro> --set-sparse true`; it is NOT part of this procedure.)"]
    lines += ["4. Start WSL again: `wsl -d Ubuntu-24.04 -- echo ok`",
              "5. Measure: `python scripts/wp2_m16_maint.py measure --label post_compaction`",
              "6. Health: `python scripts/wp2_m16_maint.py post-check`", ""]
    INSTR.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"M16_S3_PROBE optimize_vhd={d['optimize_vhd_available']} diskpart={d['diskpart_available']} "
          f"vhdx={vh}")
    return 0


def inventory() -> int:
    r = wsl("docker volume ls --format '{{.Name}}'", 300)
    if r.returncode:
        raise SystemExit(f"docker volume ls failed: {r.stderr[-300:]}")
    names = sorted(x for x in r.stdout.split() if x)
    pcv = protected_container_volumes()
    sizes = volume_sizes()
    vols = []
    for n in names:
        c = classify_volume(n, volume_refs(n), pcv)
        c["size_bytes"] = sizes.get(n)
        vols.append(c)
    allow = sorted(v["name"] for v in vols if v["delete_allowed"])
    for p in PROTECTED_NAMES:
        if p in allow:
            raise SystemExit(f"invariant: protected volume {p} in allow-list")
    d = {"artifact": "m16_s3_volume_inventory", "artifact_sha256": "", "utc": now(), "volumes": vols,
         "protected_names": list(PROTECTED_NAMES), "protected_container_volumes": sorted(pcv),
         "allow_list": allow, "allow_list_bytes": sum(v["size_bytes"] or 0 for v in vols if v["delete_allowed"]),
         "rule": "delete_allowed iff anonymous 64-hex name AND referenced by no container AND not "
                 "protected; never prune"}
    write(INVENTORY, self_hash(d))
    print(f"M16_S3_INVENTORY volumes={len(vols)} allow_list={len(allow)} "
          f"bytes={d['allow_list_bytes']} sha={d['artifact_sha256']}")
    return 0


def delete(inventory_sha: str) -> int:
    inv = load(INVENTORY)
    if not (hash_ok(inv) and inv["artifact_sha256"] == inventory_sha):
        raise SystemExit("inventory hash mismatch: re-run `inventory` and pass its sha")
    pcv = protected_container_volumes()
    for n in inv["allow_list"]:
        c = classify_volume(n, volume_refs(n), pcv)          # re-check right before deletion
        if not c["delete_allowed"]:
            row = {"utc": now(), "volume": n, "action": "SKIPPED", "reasons": c["reasons"]}
        else:
            r = wsl(f"docker volume rm {n}", 300)
            row = {"utc": now(), "volume": n, "action": "REMOVED" if r.returncode == 0 else "FAILED",
                   "stderr": r.stderr[-300:]}
        DELETIONS.parent.mkdir(parents=True, exist_ok=True)
        with open(DELETIONS, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
        print(f"[s3] {n} {row['action']}")
    for p in PROTECTED_NAMES:
        if wsl(f"docker volume inspect {p} >/dev/null 2>&1 && echo OK").stdout.strip() != "OK":
            raise SystemExit(f"PROTECTED VOLUME MISSING: {p}")
    print("M16_S3_DELETE_DONE")
    return 0


def measure(label: str) -> int:
    s = resource.snapshot(label, heavy=False)
    write(MAINT / f"measure_{label}.json", self_hash({"artifact": "m16_s3_measure", "artifact_sha256": "",
                                                      **s, "utc": now()}))
    print(f"M16_S3_MEASURE {label} c_free={s['c_free_gib']} vhdx={s['vhdx']}")
    return 0


def post_check() -> int:
    checks = {}
    checks["docker_info"] = wsl("docker info >/dev/null 2>&1 && echo OK").stdout.strip() == "OK"
    wsl("docker start wp2-pg >/dev/null 2>&1 || true")
    checks["wp2_pg_ready"] = "accepting" in wsl("sleep 3; docker exec wp2-pg pg_isready -U saleor").stdout
    checks["wp2_uv_cache_present"] = wsl("docker volume inspect wp2-uv-cache >/dev/null 2>&1 && echo OK"
                                         ).stdout.strip() == "OK"
    imgs = {}
    for era in ("py38", "py39", "py312"):
        imgs[era] = wsl(f"docker image inspect wp2-era-{era} --format '{{{{.Id}}}}'").stdout.strip()
    checks["era_images_present"] = all(imgs.values())
    py = sys.executable
    hv = subprocess.run([py, "scripts/wp2_m16_run.py", "historical-verify"], cwd=PROJECT,
                        capture_output=True, text=True)
    kv = subprocess.run([py, "scripts/wp2_ctl_v224.py", "verify-kit", "--plan", "controller/plan_m16_v1.json"],
                        cwd=PROJECT, capture_output=True, text=True)
    checks["historical_unchanged"] = hv.returncode == 0
    checks["kit_ok"] = kv.returncode == 0
    ok = all(checks.values())
    write(MAINT / "post_check.json", self_hash({"artifact": "m16_s3_post_check", "artifact_sha256": "",
                                                "checks": checks, "era_image_ids": imgs, "ok": ok,
                                                "storage": resource.snapshot("post_check", heavy=False),
                                                "utc": now()}))
    print(f"M16_S3_POST_CHECK {'PASS' if ok else 'FAIL'} {checks}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("probe")
    sp.add_parser("inventory")
    sp.add_parser("delete").add_argument("--inventory-sha", required=True)
    sp.add_parser("measure").add_argument("--label", required=True)
    sp.add_parser("post-check")
    a = ap.parse_args(argv)
    return {"probe": probe, "inventory": inventory, "post-check": post_check,
            "delete": lambda: delete(a.inventory_sha), "measure": lambda: measure(a.label)}[a.cmd]()


if __name__ == "__main__":
    raise SystemExit(main())
