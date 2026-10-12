#!/usr/bin/env python3
"""D7_R3 native probe derivation + soname matching (FROZEN with the R3 harness).

Mission: M17_ENV_CANON_D7_R3_HARNESS_DEFECT_CORRECTION_AND_FREEZE
(ENGINEERING QUALIFICATION / HARNESS DEFECT CORRECTION ONLY)

R3 is the additive correction of the frozen R2 harness.  It retains the two R1
defect fixes (exact-profile probe scope + strict soname equality) and adds the
probe semantics corrections demonstrated by the real D7_R2_CALIBRATION_12 run:

  HARNESS_DEFECT_1 (R1, retained): probe scope derived from the unit's EXACT
    frozen native_profile_id (DOCKER_PROFILE_MANIFEST.json).  A profile never
    probes packages that belong to another profile, and any profile package
    without a frozen spec is a FAIL CLOSED probe-spec gap.

  HARNESS_DEFECT_2 (R1, retained): soname matching against ACTUAL loader-visible
    names with EXACT equality on the soname stem; no substring-based optimistic
    matching.

  R3_DEFECT_A (libopenjp2-7 SONAME token): the expected token is now
    "libopenjp2.so.7" (loader-visible SONAME proven by readelf -d + ldconfig -p
    in the frozen images), replacing the wrong "libopenjp2-7.so.7".

  R3_DEFECT_B (pipx PATH semantics): pipx is now an EXEC probe resolving the
    executable via PATH (command -v pipx -> /usr/bin/pipx in the frozen images),
    replacing the wrong absolute PATH "/usr/local/bin/pipx".

  R3_DEFECT_C (libxslt1-dev SONAME token): the expected token is now
    "libxslt.so.1" (loader-visible SONAME), replacing the wrong
    "libxslt.so.1.1" (the versioned filename libxslt.so.1.1.35 is NOT a SONAME).
"""
from __future__ import annotations

import os

from d7_r3_native_specs import (
    BUILD_TOOLHOUSE_ONLY_DISTS,
    NATIVE_PROBE_SPECS,
    EXEC_PROBE,
    PATH_PROBE,
    SONAME_PROBE,
)


def derive_probe_payload(profile_packages: list[str]) -> dict:
    """Map a frozen profile's package list to the exact probe payload.

    Raises:
        KeyError: if any profile package lacks a frozen spec (FAIL CLOSED).
    """
    payload = {}
    for pkg in profile_packages:
        spec = NATIVE_PROBE_SPECS.get(pkg)
        if spec is None:
            raise KeyError(
                f"RUNTIME_NATIVE_SPEC_GAP: profile package {pkg!r} has no frozen "
                "probe spec. FAIL CLOSED (never silently skipped)."
            )
        payload[pkg] = spec
    return payload


def loader_token_equals(loader_tokens: list[str], candidate: str) -> bool:
    """Exact equality between a loader-visible name token and a frozen soname.

    Loader tokens come from ``ldconfig -p`` output lines, e.g.
    ``libopenjp2.so.7 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libopenjp2.so.7``.
    The harness compares the *soname part* (everything up to the first space /
    '(' or the '=>' separator).
    """
    for tok in loader_tokens:
        t = tok.strip()
        if not t:
            continue
        # token = "name (info) => path"  -> take the first whitespace-delimited word
        name_part = t.split(None, 1)[0]
        if name_part.endswith("=>"):
            name_part = name_part[:-2].strip()
        if name_part == candidate:
            return True
    return False


def run_native_probes(
    probe_payload: dict,
    loader_tokens: list[str],
    fs: dict[str, bool],
    exec_resolutions: dict[str, str] | None = None,
) -> list[dict]:
    """Run all probes for the payload.

    Args:
        probe_payload: {pkg: spec} exactly as derived for the unit's profile.
        loader_tokens: loader-visible shared-library names (ldconfig -p scan).
        fs: {absolute path: exists} filesystem view (for PATH probes).
        exec_resolutions: {executable name: resolved absolute path} for EXEC
            probes (from ``command -v`` inside the container).

    Returns:
        list of failed probes [{package, kind, expected, detail}] ([] => PASS).
    """
    exec_resolutions = exec_resolutions or {}
    failures: list[dict] = []
    for pkg, spec in probe_payload.items():
        kind = spec["kind"]
        if kind == PATH_PROBE:
            path = spec["path"]
            if not fs.get(path, False):
                failures.append(
                    {"package": pkg, "kind": kind, "expected": path, "detail": "path not present"}
                )
        elif kind == EXEC_PROBE:
            exe = spec["executable"]
            resolved = exec_resolutions.get(exe, "")
            # A strict PATH-resolution check: the executable must resolve to a
            # real filesystem entry inside the container.
            if not resolved or not fs.get(resolved, False):
                failures.append(
                    {
                        "package": pkg,
                        "kind": kind,
                        "expected": exe,
                        "detail": f"executable {exe!r} not resolvable on PATH",
                    }
                )
        elif kind == SONAME_PROBE:
            allowed = spec["allowed_sonames"]
            found = any(loader_token_equals(loader_tokens, cand) for cand in allowed)
            if not found:
                failures.append(
                    {
                        "package": pkg,
                        "kind": kind,
                        "expected": list(allowed),
                        "detail": "no allowed soname among loader-visible names",
                    }
                )
        else:  # unknown spec kind -> FAIL CLOSED (spec defect, not env defect)
            failures.append(
                {"package": pkg, "kind": str(kind), "expected": "frozen-spec", "detail": "unknown probe kind"}
            )
    return failures


def audit_toolhouse_contamination(installed_packages: list[str]) -> list[str]:
    """Detect build-toolhouse-only distributions in the runtime environment.

    R1 Defect #3 root cause: build tools (vcs-versioning, poetry-core,
    setuptools-scm, wheel) installed into the runtime env caused a
    pip-check conflict (vcs-versioning 2.6.0 -> packaging>=26.2 vs the runtime
    closure's packaging==24.2).  In R2/R3 the build toolhouse is NEVER installed
    into the runtime environment; this audit fails closed if any
    build-toolhouse-only distribution is present.

    Returns the offending distribution names ([] => clean).
    """
    present = {p.lower().replace("_", "-") for p in installed_packages}
    return sorted(present & BUILD_TOOLHOUSE_ONLY_DISTS)
