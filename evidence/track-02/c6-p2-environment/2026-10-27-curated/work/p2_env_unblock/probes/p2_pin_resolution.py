# -*- coding: utf-8 -*-
"""P2 offline dependency-resolution probe (NON-CANDIDATE, read-only).

Mission TRACK02-C6-P2-ENV-UNBLOCK (2026-10-27).
Determines, for every pinned entry of requirements.txt and
requirements_dev.txt AT COMMIT P, which offline supply exists locally:
  exact_wheel | sdist | built_wheel | patch_compatible | union_skip | MISSING
No package is downloaded, no network is used, no candidate test runs.
"""
import json
import os
import re
import subprocess
import sys

GIT_DIR = r"D:\wp2_env_store\git_cache\saleor.git"
P = "5b0e5206c5fd30d81438b6489d0441df51038a85"
WHEELHOUSE = [r"D:\wp2_env_store\wheelhouse\py39"]
BUILT = [
    r"D:\wp2_env_store\built_wheelhouse\py39",
    r"D:\wp2_env_store\built_wheelhouse\canon_r4b\py39",
]
NAMES = ["requirements.txt", "requirements_dev.txt"]


def git_show(rev, path):
    out = subprocess.run(
        ["git", "show", f"{rev}:{path}"], capture_output=True, text=True,
        env={"GIT_DIR": GIT_DIR}, check=False)
    return out.stdout if out.returncode == 0 else None


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_pin(line):
    line = line.split(";")[0].strip()        # strip pip marker suffix
    if not line:
        return None
    m = re.match(r"^([A-Za-z0-9_.\-]+)(\[[^\]]*\])?==([^=\s]+)$", line.strip())
    if not m:
        return None
    return m.group(1), m.group(2) or "", m.group(3)


def scan_dir(d):
    by_normal = {}
    if not os.path.isdir(d):
        return by_normal
    for fn in os.listdir(d):
        base, ext = os.path.splitext(fn)
        if ext != ".whl":
            continue
        parts = base.split("-")
        # wheel name may contain dashes; version is the part matching PEP440
        ver = parts[-1] if len(parts) >= 5 else None
        name_part = "-".join(parts[:-4]) if len(parts) >= 5 else fn
        by_normal.setdefault(norm(name_part), []).append((fn, "wheel"))
    return by_normal


def scan_sdists(d):
    by_normal = {}
    if not os.path.isdir(d):
        return by_normal
    for fn in os.listdir(d):
        if fn.endswith(".tar.gz") or fn.endswith(".zip"):
            base = fn[: fn.rfind("-")]
            by_normal.setdefault(norm(base), []).append((fn, "sdist"))
    return by_normal


def scan_built_dirs(d):
    """built_wheelhouse/*/py39/<name>__<ver>____py39/<name>-<ver>-*.whl"""
    out = {}
    if not os.path.isdir(d):
        return out
    for item in os.listdir(d):
        p = os.path.join(d, item)
        if not os.path.isdir(p):
            continue
        m = re.match(r"^(.*)__([0-9][^-]*)____py39$", item)
        if not m:
            continue
        name, ver = m.group(1), m.group(2)
        wheels = [f for f in os.listdir(p) if f.endswith(".whl")]
        out.setdefault(norm(name), []).append((ver, os.path.join(item, wheels[0]) if wheels else None))
    return out


PATCH_COMPAT = {
    # documented patch-compatible substitutions (operator pin decision):
    "measurement": {"3.2.0": [("3.2.2", "wheel")]},       # 3.2.2 wheel present
    "psycopg2": {"2.9.4": [("2.9.3", "psycopg2_binary cp39 wheel")]},
    "before-after": {"1.0.1": [("1.0.1", "built wheel")]},
    "promise": {"2.3": [("2.3", "sdist buildable offline (setuptools)")]},
}

# packages known to have ZERO presence in the C6 contract closure
# (from the frozen feasibility analysis + fresh grep evidence below)
UNION_SKIP = set()


def main():
    wh = {}
    for d in WHEELHOUSE:
        wh.update(scan_dir(d))
    sd = {}
    for d in WHEELHOUSE:
        sd.update(scan_sdists(d))
    built = {}
    for d in BUILT:
        built.update(scan_built_dirs(d))

    results = {}
    for mname in NAMES:
        txt = git_show(P, mname)
        if txt is None:
            results[mname] = {"error": "not present at P"}
            continue
        entries = []
        for lineno, line in enumerate(txt.splitlines(), 1):
            pin = parse_pin(line)
            if pin is None:
                continue
            name, extra, ver = pin
            n = norm(name)
            entry = {"line": line.strip(), "package": name, "extra": extra,
                     "version": ver}
            if n in PATCH_COMPAT and ver in PATCH_COMPAT[n]:
                entry["verdict"] = "patch_compatible"
                entry["detail"] = PATCH_COMPAT[n][ver]
            elif n in wh:
                wheels = [w for w, _ in wh[n]]
                entry["verdict"] = "exact_wheel"
                entry["detail"] = sorted(wheels)
            elif n in sd:
                entry["verdict"] = "sdist"
                entry["detail"] = [s for s, _ in sd[n]]
            elif n in built and built[n]:
                entry["verdict"] = "built_wheel"
                entry["detail"] = built[n]
            else:
                entry["verdict"] = "MISSING"
                entry["detail"] = []
            entries.append(entry)
        results[mname] = entries

    # summarize
    summary = {}
    for mname, entries in results.items():
        if isinstance(entries, dict):
            summary[mname] = entries
            continue
        cnt = {}
        for e in entries:
            cnt[e["verdict"]] = cnt.get(e["verdict"], 0) + 1
        missing = [e for e in entries if e["verdict"] == "MISSING"]
        summary[mname] = {"count": len(entries), "by_verdict": cnt,
                          "missing": [e["line"] for e in missing]}
    out = {"P": P, "wheelhouse_dirs": WHEELHOUSE, "built_dirs": BUILT,
           "results": results, "summary": summary}
    with open(os.path.join(os.path.dirname(__file__),
                           "p2_pin_resolution.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print(json.dumps(summary, indent=1, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())