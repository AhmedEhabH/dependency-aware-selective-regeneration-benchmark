#!/usr/bin/env python3
"""D7_R3 native probe spec table (FROZEN with the R3 harness).

Mission: M17_ENV_CANON_D7_R3_HARNESS_DEFECT_CORRECTION_AND_FREEZE
(ENGINEERING QUALIFICATION / HARNESS DEFECT CORRECTION ONLY — no scientific change)

R3 is created ADDITIVELY from the frozen R2 harness.  It corrects ONLY the
engineering probe-spec metadata that the real D7_R2_CALIBRATION_12 mission
proved wrong, per the loader/path evidence reproduced in
`tmp/d7_r3_out/probes/D7_R3_NATIVE_SPEC_AUDIT.json` (read-only probes under
--network=none against the FROZEN images):

  R2_DEFECT_A (libopenjp2-7):
    R2 expected loader-visible soname token "libopenjp2-7.so.7".
    Loader reality on ALL frozen images that install libopenjp2-7 (9/10 native
    profiles) is "libopenjp2.so.7" (ldconfig -p + readelf -d SONAME of
    /usr/lib/x86_64-linux-gnu/libopenjp2.so.2.5.0).  "libopenjp2-7.so.7" is the
    Debian package-name morphology (libopenjp2-7) masquerading as a SONAME; no
    file or loader token with that name exists in any frozen image.  R3 encodes
    the loader-visible SONAME.

  R2_DEFECT_B (pipx):
    R2 expected an absolute PATH probe "/usr/local/bin/pipx".
    Loader/path reality on both pipx images (nat-a39687f3d19c, nat-cc2f641e9e04)
    is: pipx is the Debian package `pipx 1.1.0-1` installed to /usr/bin/pipx,
    resolved via `command -v pipx` -> /usr/bin/pipx.  /usr/local/bin/pipx does
    NOT exist.  The requirement semantics is "pipx is resolvable on PATH"
    (executable presence), not a frozen absolute path under /usr/local/bin.  R3
    encodes an EXEC probe resolving the executable via PATH.

  R2_DEFECT_C (libxslt1-dev):
    R2 expected loader-visible soname token "libxslt.so.1.1".
    Loader reality (nat-02b9bb45ba01, 7 units in the 144 population) is
    "libxslt.so.1" (ldconfig -p token; readelf -d of the real object).  The file
    /usr/lib/x86_64-linux-gnu/libxslt.so.1.1.35 is the versioned FILENAME
    (full version 1.1.35), NOT a loader token; "libxslt.so.1.1" exists nowhere
    in the loader cache.  R3 encodes the loader-visible SONAME.

Every corrected entry in this table is backed by strict-readelf/ldconfig/command-v
evidence inside the exact frozen images.  No environment artifact, population,
threshold, selector, lock, or protocol changed.

R1-fixed semantics retained unchanged:
- Probes are derived from the unit's EXACT frozen native_profile_id (never a
  global map), so packages belonging to another profile are never probed.
- Soname matching is strict EQUALITY of a permitted candidate against a
  loader-visible token; no substring-based optimistic matching.

Spec provenance: Debian bookworm base manifest + scripts/env_canon_phase_b_native.py
NATIVE_SONAME_MAP (the frozen Phase-B authority) — which already encoded
libopenjp2-7 -> libopenjp2.so.7, libxslt1-dev -> libxslt.so.1, and pipx as an
executable.  The R3 table restores consistency with that authority.  The harness
FAILS CLOSED if a profile contains a package with no spec entry, and every spec
is loader-confirmed during the calibration mission itself.
"""
from __future__ import annotations

# Canonical dist names that exist ONLY to perform source builds.  These are
# recorded in ``manifests/R4B_FINAL_BUILD_TOOLHOUSE.json``.  Presence of ANY of
# these in the final runtime environment is RUNTIME_TOOLHOUSE_CONTAMINATION
# (FAIL CLOSED).  Base-image tooling (pip/setuptools ship in python:3.12-
# bookworm) is out of scope for this marker set; the four names below are
# exactly the R1 post-install-removal set, promoted to a design-level audit.
BUILD_TOOLHOUSE_ONLY_DISTS = frozenset(
    {
        "vcs-versioning",
        "poetry-core",
        "setuptools-scm",
        "wheel",
    }
)

# Probe kinds
PATH_PROBE = "PATH"
SONAME_PROBE = "SONAME"
EXEC_PROBE = "EXEC"

# name -> spec
#   PATH  : {"kind": "PATH",  "path": <absolute path (file or dir)>}
#   SONAME: {"kind": "SONAME", "allowed_sonames": (loader-visible name tokens)}
#   EXEC  : {"kind": "EXEC", "executable": <PATH-resolvable executable name>}
NATIVE_PROBE_SPECS = {
    "gettext": {"kind": PATH_PROBE, "path": "/usr/bin/gettext"},
    "libffi8": {"kind": SONAME_PROBE, "allowed_sonames": ("libffi.so.8",)},
    "libgdk-pixbuf-2.0-0": {
        "kind": SONAME_PROBE,
        "allowed_sonames": ("libgdk_pixbuf-2.0.so.0",),
    },
    "libgdk-pixbuf2.0-0": {
        "kind": SONAME_PROBE,
        "allowed_sonames": ("libgdk_pixbuf-2.0.so.0",),
    },
    "liblcms2-2": {"kind": SONAME_PROBE, "allowed_sonames": ("liblcms2.so.2",)},
    "libmagic1": {"kind": SONAME_PROBE, "allowed_sonames": ("libmagic.so.1",)},
    "libopenjp2-7": {"kind": SONAME_PROBE, "allowed_sonames": ("libopenjp2.so.7",)},
    "libpq5": {"kind": SONAME_PROBE, "allowed_sonames": ("libpq.so.5",)},
    "libssl3": {"kind": SONAME_PROBE, "allowed_sonames": ("libssl.so.3",)},
    "libtiff6": {"kind": SONAME_PROBE, "allowed_sonames": ("libtiff.so.6",)},
    "libwebp7": {"kind": SONAME_PROBE, "allowed_sonames": ("libwebp.so.7",)},
    "libcairo2": {"kind": SONAME_PROBE, "allowed_sonames": ("libcairo.so.2",)},
    "libpango-1.0-0": {"kind": SONAME_PROBE, "allowed_sonames": ("libpango-1.0.so.0",)},
    "libpangocairo-1.0-0": {
        "kind": SONAME_PROBE,
        "allowed_sonames": ("libpangocairo-1.0.so.0",),
    },
    "libssl1.1": {"kind": SONAME_PROBE, "allowed_sonames": ("libssl.so.1.1", "libssl.so.1.1")},
    "libxml2": {"kind": SONAME_PROBE, "allowed_sonames": ("libxml2.so.2",)},
    "libtiff5": {"kind": SONAME_PROBE, "allowed_sonames": ("libtiff.so.5",)},  # bullseye era
    "libwebp6": {"kind": SONAME_PROBE, "allowed_sonames": ("libwebp.so.6",)},  # bullseye era
    "libxslt1-dev": {"kind": SONAME_PROBE, "allowed_sonames": ("libxslt.so.1",)},
    "shared-mime-info": {"kind": PATH_PROBE, "path": "/usr/share/mime"},
    "mime-support": {"kind": PATH_PROBE, "path": "/etc/mime.types"},
    "pipx": {"kind": EXEC_PROBE, "executable": "pipx"},
}


def spec_for(package: str) -> dict | None:
    return NATIVE_PROBE_SPECS.get(package)
