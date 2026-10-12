#!/usr/bin/env python3
"""D7_R3 frozen runtime closure derivation (FROZEN with the R3 harness).

Mission: M17_ENV_CANON_D7_R3_HARNESS_DEFECT_CORRECTION_AND_FREEZE
(ENGINEERING QUALIFICATION / HARNESS DEFECT CORRECTION ONLY)

R3 is the additive correction of the frozen R2 harness.  Closure semantics are
byte-identical to R2: this module is unchanged except the internal module
prefix (d7_r2_* -> d7_r3_*), so R3 never imports R2 harness code.

Restores the EXACT frozen Linux/amd64 closure semantics of the D7 plan:

  * the runtime closure is the unit's frozen lock fragment, FULLY (both
    LOCK_FRAGMENT_MAIN_PLUS_DEV and V2_EDITABLE_PLUS_LOCK_DEV include the
    complete main+dev dependency set recorded in the frozen lock);
  * NO dependency is pruned merely because it looks dev-only.  Tools such as
    ruff, semgrep, deptry are members of the frozen closure and stay in it;
  * exactly two platform exclusions are applied (both frozen evidence, no new
    rule, no outcome-tuning):
        pywin32           -> MARKER_EXCLUDED_ON_LINUX  (MARKER_FILTER_AUDIT.json)
        python-magic-bin  -> platform = "win32"        (frozen pyproject.toml)

Anything that has no compatible artifact after those two exclusions is a
genuine runtime-artifact-closure defect (FAIL CLOSED).  The driver NEVER falls
back to a source build.
"""
from __future__ import annotations

import os
import tomllib

from d7_r3_wheeltags import parse_wheel, wheel_compatible


def load_toml(path: str) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def poetry_pins(lock_path: str, pyver: str = "3.12") -> tuple[list[str], list[str]]:
    """Return (pins, excluded_by_python_versions) from a frozen Poetry lock.

    Identical pinning semantics to the R1 frozen closure: every package entry,
    honouring python-versions marker filtering for the target version.
    """
    from packaging.specifiers import SpecifierSet
    from packaging.utils import canonicalize_name  # noqa: F401

    data = load_toml(lock_path)
    pins: list[str] = []
    excluded: list[str] = []
    for p in data.get("package", []):
        name = p["name"]
        ver = p.get("version", "UNKNOWN")
        pv = p.get("python-versions", "")
        if pv and pv != "*":
            try:
                if not SpecifierSet(pv).contains(pyver):
                    excluded.append(f"{name}=={ver}")
                    continue
            except Exception:
                excluded.append(f"{name}=={ver}")
                continue
        pins.append(f"{name}=={ver}")
    return sorted(set(pins)), sorted(set(excluded))


def marker_excluded_linux_names(marker_audit_path: str) -> set[str]:
    """Packages classified MARKER_EXCLUDED_ON_LINUX (frozen audit)."""
    import json

    with open(marker_audit_path, "r", encoding="utf-8") as f:
        audit = json.load(f)
    out = set()
    for name, info in (audit.get("packages") or {}).items():
        if isinstance(info, dict) and info.get("classification") == "MARKER_EXCLUDED_ON_LINUX":
            out.add(name.lower().replace("_", "-"))
    return out


def win32_platform_names(pyproject_paths: list[str]) -> set[str]:
    """Packages declared platform = \"win32\" in the FROZEN pyproject files.

    Same function the R1 final harness used (pyproject_platform_win32), applied
    to every frozen member-task pyproject of the unit.  Missing files are
    ignored exactly as R1 ignored them (no exclusion is invented).
    """
    out = set()
    for pp in pyproject_paths:
        if not os.path.isfile(pp):
            continue
        data = load_toml(pp)
        tables = []
        for key in ("tool.poetry.dependencies", "tool.poetry.group.dev.dependencies"):
            node = data
            for part in key.split("."):
                node = node.get(part, {})
                if not isinstance(node, dict):
                    node = {}
                    break
            tables.append(node)
        for table in tables:
            for name, spec in table.items():
                if not isinstance(spec, dict):
                    continue
                norm = str(name).lower().replace("_", "-")
                plat = str(spec.get("platform", ""))
                if "win32" in plat and "!=" not in plat:
                    out.add(norm)
    return out


def derive_runtime_closure(
    lock_path: str,
    pyproject_paths: list[str],
    marker_audit_path: str,
    pyver: str = "3.12",
) -> dict:
    """Compute the frozen Linux runtime closure for one unit.

    Returns:
        pins: sorted pin list (== frozen closure, no pruning)
        excluded: [(pin, reason)] for the exactly-two platform exclusions
        runtime_pins: pins to install (pins minus excluded)
    """
    pins, _ = poetry_pins(lock_path, pyver)
    marker_excl = marker_excluded_linux_names(marker_audit_path)
    win32_excl = win32_platform_names(pyproject_paths)

    excluded: list[dict] = []
    runtime_pins: list[str] = []
    for pin in pins:
        name = pin.split("==", 1)[0].lower().replace("_", "-")
        if name in marker_excl:
            excluded.append({"pin": pin, "reason": "MARKER_EXCLUDED_ON_LINUX"})
        elif name in win32_excl:
            excluded.append({"pin": pin, "reason": "PLATFORM_WIN32"})
        else:
            runtime_pins.append(pin)
    return {
        "pins": pins,
        "excluded": excluded,
        "runtime_pins": runtime_pins,
    }


def resolve_runtime_artifacts(
    runtime_pins: list[str],
    runtime_dir: str | None = None,
    wheel_file_list: list[str] | None = None,
) -> dict:
    """Resolve every runtime pin against the wheel-only runtime input set.

    The R2 runtime path is WHEEL-ONLY (build tools are never installed;
    ``--only-binary=:all:`` is enforced at install time).  Missing/incompatible
    pins are FAIL CLOSED as runtime-artifact-closure defects.

    ``runtime_dir``: a directory (the driver enumerates it).
    ``wheel_file_list``: an explicit READ-ONLY list of wheel filenames (used by
    the read-only closure check so no scratch copies are made).

    This resolver never consults the network.
    """
    artifacts: dict[tuple[str, str], list[str]] = {}
    filenames = list(wheel_file_list or [])
    if runtime_dir is not None and runtime_dir and os.path.isdir(runtime_dir):
        filenames.extend(os.listdir(runtime_dir))
    for fn in sorted(set(filenames)):
        if not fn.endswith(".whl"):
            continue
        parsed = parse_wheel(fn)
        if parsed is None:
            continue
        name, version, _tags = parsed
        artifacts.setdefault((str(name), str(version)), []).append(fn)

    missing: list[str] = []
    incompatible: list[dict] = []
    for pin in runtime_pins:
        if pin.startswith("-") or "==" not in pin:
            continue
        pname, pver = pin.split("==", 1)
        key = (pname.lower().replace("_", "-"), pver.lower().replace("_", "-"))
        cands = artifacts.get(key, [])
        if not cands:
            missing.append(pin)
            continue
        ok = [fn for fn in cands if wheel_compatible(fn)]
        if not ok:
            incompatible.append({"pin": pin, "candidates": cands})
    return {
        "n_runtime_pins": len(runtime_pins),
        "missing": sorted(set(missing)),
        "incompatible": incompatible,
        "pass_": (not missing and not incompatible),
    }


def assemble_runtime_input(
    wheelhouse_dir: str,
    canon_wheels_dir: str,
    dest_dir: str | None = None,
) -> list[str]:
    """Build the D7 runtime wheel input set.

    SOURCE-BUILD CANON -> frozen canonical wheels -> D7 runtime wheel input.

    Returns the deterministic sorted list of wheel filenames that constitute
    the runtime input: frozen wheelhouse wheels PLUS Final-R4B canonical wheels
    (canon wins on filename collision, which is expected and intended for e.g.
    petl==1.7.15 where the canon wheel replaces the 1.7.17 wheelhouse wheel).
    With ``dest_dir`` None, this is a pure enumeration over the frozen stores
    (no copies, no network).  When ``dest_dir`` is supplied, the merged set is
    materialised there (used by the real calibration driver).
    """
    merged: dict[str, str] = {}
    if os.path.isdir(wheelhouse_dir):
        for fn in sorted(os.listdir(wheelhouse_dir)):
            if fn.endswith(".whl"):
                merged[fn] = os.path.join(wheelhouse_dir, fn)
    if os.path.isdir(canon_wheels_dir):
        for identity in sorted(os.listdir(canon_wheels_dir)):
            wd = os.path.join(canon_wheels_dir, identity, "wheels")
            if not os.path.isdir(wd):
                continue
            for fn in sorted(os.listdir(wd)):
                if fn.endswith(".whl"):
                    merged[fn] = os.path.join(wd, fn)
    if dest_dir:
        import shutil

        os.makedirs(dest_dir, exist_ok=True)
        for fn in merged:
            shutil.copy2(merged[fn], os.path.join(dest_dir, fn))
    return sorted(merged)