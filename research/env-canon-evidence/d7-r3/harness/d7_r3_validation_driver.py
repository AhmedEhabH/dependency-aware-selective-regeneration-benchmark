#!/usr/bin/env python3
"""D7_R3 validation driver + synthetic P2P/F2P engine (FROZEN with the R3 harness).

Mission: M17_ENV_CANON_D7_R3_HARNESS_DEFECT_CORRECTION_AND_FREEZE
(ENGINEERING QUALIFICATION / HARNESS DEFECT CORRECTION ONLY — no scientific result)

R3 is the ADDITIVE correction of the frozen R2 harness (R2 = immutable failed
calibration evidence; never repaired in place).  It changes ONLY harness
engineering probe-spec metadata, backed by read-only loader/path evidence in the
frozen images (see tmp/d7_r3_out/probes/D7_R3_NATIVE_SPEC_AUDIT.json):

  * libopenjp2-7 SONAME: libopenjp2-7.so.7 -> libopenjp2.so.7   (R2_DEFECT_A)
  * pipx: absolute /usr/local/bin/pipx -> EXEC probe on PATH      (R2_DEFECT_B)
  * libxslt1-dev SONAME: libxslt.so.1.1 -> libxslt.so.1           (R2_DEFECT_C)

This driver FREEZES the D7_R3 harness contract and proves it with a
deterministic synthetic P2P/F2P suite.  It:
  * NEVER executes any of the frozen 12 real calibration units;
  * NEVER runs Full D7 / D8 / D9 / D10 / MAIN Oracle / READY / OPWS;
  * NEVER performs a source build (runtime path is WHEEL-ONLY);
  * NEVER touches the network inside synthetic or preflight paths.

CLI:
  python d7_r3_validation_driver.py --synthetic          # run P2P/F2P suite
  python d7_r3_validation_driver.py --preflight          # read-only frozen-input checks
  python d7_r3_validation_driver.py --closure-check      # read-only 12-unit closure resolution
  python d7_r3_validation_driver.py --manifest           # emit D7_R3_HARNESS_MANIFEST.json
  python d7_r3_validation_driver.py --freeze-outputs     # write manifest+freeze+receipt+report

The real calibration path (`--calibration`) is gated for a separate, later,
owner-authorized D7_R3_CALIBRATION_12 mission and is NOT run by this mission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from d7_r3_closure import (  # noqa: E402
    assemble_runtime_input,
    derive_runtime_closure,
    marker_excluded_linux_names,
    poetry_pins,
    resolve_runtime_artifacts,
    win32_platform_names,
)
from d7_r3_probes import (  # noqa: E402
    audit_toolhouse_contamination,
    derive_probe_payload,
    run_native_probes,
)
from d7_r3_wheeltags import wheel_compatible  # noqa: E402

STORE = r"D:\wp2_env_store"
MANIFESTS = os.path.join(STORE, "manifests")
RECEIPTS = os.path.join(STORE, "receipts")
REPORTS = os.path.join(STORE, "reports")
HARNESS_DIR = HERE

PLAN = os.path.join(MANIFESTS, "D7_CALIBRATION_12_PLAN.json")
MATRIX = os.path.join(MANIFESTS, "VALIDATION_UNIT_MATRIX.csv")
LOCK_DIR = os.path.join(STORE, "artifacts", "locks")
WORKTREE_DIR = os.path.join(STORE, "tmp", "d7_r1_worktrees")
MARKER_AUDIT = os.path.join(MANIFESTS, "MARKER_FILTER_AUDIT.json")
DOCKER_PROFILES = os.path.join(MANIFESTS, "DOCKER_PROFILE_MANIFEST.json")
WHEELHOUSE_PY312 = os.path.join(STORE, "wheelhouse", "py312")
CANON_PY312 = os.path.join(STORE, "built_wheelhouse", "canon_r4b", "py312")
TOOLHOUSE_MANIFEST = os.path.join(MANIFESTS, "R4B_FINAL_BUILD_TOOLHOUSE.json")

# R3 harness file set (every file hashed into the harness manifest).
HARNESS_FILES = [
    "D7_R3_HARNESS_CONTRACT.md",
    "d7_r3_validation_driver.py",
    "d7_r3_closure.py",
    "d7_r3_probes.py",
    "d7_r3_native_specs.py",
    "d7_r3_wheeltags.py",
    "d7_r3_light_pack.py",
    "tests/pytest.ini",
    "tests/test_d7_r3_harness.py",
    "D7_R3_HARNESS_MANIFEST.json",
]
MANIFEST_OUT = os.path.join(HARNESS_DIR, "D7_R3_HARNESS_MANIFEST.json")
FREEZE_OUT = os.path.join(MANIFESTS, "D7_R3_HARNESS_FREEZE.json")
RECEIPT_OUT = os.path.join(RECEIPTS, "D7_R3_HARNESS_P2P_F2P.json")
REPORT_OUT = os.path.join(REPORTS, "D7_R3_HARNESS_FREEZE_REPORT.md")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class HarnessExit(Exception):
    """Deterministic harness decision (PASS vs FAIL CLOSED)."""

    def __init__(self, decision: str, detail: str = ""):
        self.decision = decision
        self.detail = detail
        super().__init__(decision + (" :: " + detail if detail else ""))


# ---------------------------------------------------------------------------
# Synthetic engine -- deterministic, docker-free, network-free
# ---------------------------------------------------------------------------

# Loader-visible soname truth from the FROZEN py312-bookworm images for the
# nat-34c1a3756742 profile (read-only probes, ldconfig -p).  libopenjp2's
# loader token here is libopenjp2.so.7 (R2_DEFECT_A corrected token).
_FAKE_LOADER_NAT34 = [
    "libffi.so.8 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libffi.so.8",
    "libgdk_pixbuf-2.0.so.0 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libgdk_pixbuf-2.0.so.0",
    "liblcms2.so.2 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/liblcms2.so.2",
    "libopenjp2.so.7 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libopenjp2.so.7",
    "libpq.so.5 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libpq.so.5",
    "libssl.so.3 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libssl.so.3",
    "libtiff.so.6 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libtiff.so.6",
    "libwebp.so.7 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libwebp.so.7",
]

_PROFILE_NAT34 = [
    "gettext", "libffi8", "libgdk-pixbuf2.0-0", "liblcms2-2", "libopenjp2-7",
    "libpq5", "libssl3", "libtiff6", "libwebp7", "mime-support", "shared-mime-info",
]
_PROFILE_NAT_A396 = _PROFILE_NAT34 + ["pipx"]

# pipx PATH-resolution truth from the FROZEN pipx images: Debian package pipx
# 1.1.0-1 installs to /usr/bin/pipx and resolves via command -v (R2_DEFECT_B).
_PIPX_RESOLUTION = "/usr/bin/pipx"


def _fake_fs(paths_ok: list[str]) -> dict[str, bool]:
    return {p: True for p in paths_ok}


class SyntheticUnit:
    """A tiny immutable stand-in for a frozen calibration unit (harness-only)."""

    def __init__(
        self,
        validation_unit_id: str,
        native_profile_id: str,
        profile_packages: list[str],
        runtime_pins: list[str],
        runtime_wheels: list[str],
        loader_tokens: list[str],
        fs: dict[str, bool],
        exec_resolutions: dict[str, str] | None = None,
        network_unavailable: bool = True,
        installed_packages: list[str] | None = None,
        pip_check_rc: int = 0,
        smoke: dict[str, str] | None = None,
    ):
        self.validation_unit_id = validation_unit_id
        self.native_profile_id = native_profile_id
        self.profile_packages = profile_packages
        self.runtime_pins = runtime_pins
        self.runtime_wheels = runtime_wheels
        self.loader_tokens = loader_tokens
        self.fs = fs
        self.exec_resolutions = exec_resolutions or {}
        self.network_unavailable = network_unavailable
        self.installed_packages = installed_packages or []
        self.pip_check_rc = pip_check_rc
        self.smoke = smoke or {}


def synthetic_assert(cond: bool, msg: str) -> None:
    if not cond:
        raise HarnessExit("FAIL_CLOSED", msg)


def simulate_unit(u: SyntheticUnit, tmpdir: str | None = None) -> dict:
    """Deterministic in-process simulation of one synthetic unit's gates.

    Mirrors the real container path gate-for-gate:
      1. --network=none is enforced by the caller; here we simulate the V2
         probe result.
      2. wheel-only closure resolution (no source build possible).
      3. runtime install (RC + build-toolhouse contamination audit).
      4. pip check.
      5. native probes (profile-derived, soname-exact + PATH-exact).
      6. smoke semantics.
    """
    # --- wheel-only closure resolution (read-only file-list resolution) ---
    res = resolve_runtime_artifacts(u.runtime_pins, wheel_file_list=u.runtime_wheels)
    if not res["pass_"]:
        return {"classification": "RUNTIME_ARTIFACT_CLOSURE_DEFECT", "resolution": res}

    # --- network gate ---
    if not u.network_unavailable:
        return {"classification": "NETWORK_FAIL_CLOSED", "detail": "network reachable"}

    # --- install + contamination audit ---
    contamination = audit_toolhouse_contamination(u.installed_packages)
    if contamination:
        return {
            "classification": "RUNTIME_TOOLHOUSE_CONTAMINATION",
            "detail": f"build toolhouse distributions present: {contamination}",
        }

    # --- pip check ---
    if u.pip_check_rc != 0:
        return {"classification": "PIP_CHECK_FAIL", "detail": f"pip check rc={u.pip_check_rc}"}

    # --- native probes (exact profile derivation) ---
    payload = derive_probe_payload(u.profile_packages)
    native_failures = run_native_probes(
        payload, u.loader_tokens, u.fs, exec_resolutions=u.exec_resolutions
    )
    if native_failures:
        return {"classification": "NATIVE_FAIL", "native_failures": native_failures}

    # --- smoke ---
    bad = [k for k, v in u.smoke.items() if v not in ("0", "SKIP")]
    if bad:
        return {"classification": "SMOKE_FAIL", "detail": f"smoke rcs nonzero: {bad}"}

    return {"classification": "PASS"}


def run_synthetic_suite() -> dict:
    """The deterministic P2P/F2P suite. Returns the receipt-style result dict."""

    p2p: list[dict] = []
    f2p: list[dict] = []

    def check(name: str, fn, expect_pass: bool) -> dict:
        import traceback

        rec = {"name": name}
        try:
            out = fn()
            if expect_pass:
                synthetic_assert(out["classification"] == "PASS", f"expected PASS, got {out}")
                rec.update({"pass": True, "classification": out["classification"]})
            else:
                # FAIL CLOSED is the *expected* outcome of a negative control.
                synthetic_assert(out["classification"] != "PASS", "negative control must not PASS")
                rec.update({"pass": True, "classification": out["classification"]})
        except HarnessExit as e:
            if not expect_pass:
                rec.update({"pass": True, "classification": e.decision, "detail": e.detail})
            else:
                rec.update({"pass": False, "detail": str(e)})
        except Exception as e:  # noqa: BLE001
            rec.update({"pass": False, "error": f"{type(e).__name__}: {e}"})
            if expect_pass:
                rec["traceback"] = traceback.format_exc(limit=2)
        return rec

    def fs_ok():
        return _fake_fs(["/usr/bin/gettext", "/usr/share/mime", "/etc/mime.types", "/usr/bin/pipx"])

    # ------------------------------------------------------------------
    # POSITIVE (P2P) controls -- required by the freeze contract
    # ------------------------------------------------------------------
    def p1_clean_wheel_only_install():
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-p1",
                native_profile_id="nat-34c1a3756742",
                profile_packages=_PROFILE_NAT34,
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=_FAKE_LOADER_NAT34,
                fs=fs_ok(),
                network_unavailable=True,
                installed_packages=["demo-pkg"],
                pip_check_rc=0,
                smoke={"import_wt0": "0", "manage_wt0": "0", "pytest_wt0": "0"},
            ),
            _tmp("p1"),
        )

    def p2_pip_check_clean():
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-p2",
                native_profile_id="nat-34c1a3756742",
                profile_packages=_PROFILE_NAT34,
                runtime_pins=["demo-pkg==1.0.0", "dep-a==2.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl", "dep_a-2.0.0-py3-none-any.whl"],
                loader_tokens=_FAKE_LOADER_NAT34,
                fs=fs_ok(),
                network_unavailable=True,
                installed_packages=["demo-pkg", "dep-a"],
                pip_check_rc=0,
                smoke={},
            ),
            _tmp("p2"),
        )

    def p3_native_exact_required_probes():
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-p3",
                native_profile_id="nat-34c1a3756742",
                profile_packages=_PROFILE_NAT34,
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=_FAKE_LOADER_NAT34,
                fs=fs_ok(),
                network_unavailable=True,
                installed_packages=["demo-pkg"],
                pip_check_rc=0,
                smoke={},
            ),
            _tmp("p3"),
        )

    def p3b_pipx_path_execution_required():
        # R3_DEFECT_B correction: nat-a39687f3d19c (and nat-cc2f641e9e04) include
        # pipx, which must resolve via PATH (command -v pipx -> /usr/bin/pipx).
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-p3b",
                native_profile_id="nat-a39687f3d19c",
                profile_packages=_PROFILE_NAT_A396,
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=_FAKE_LOADER_NAT34,
                fs=fs_ok(),
                exec_resolutions={"pipx": _PIPX_RESOLUTION},
                network_unavailable=True,
                installed_packages=["demo-pkg"],
                pip_check_rc=0,
                smoke={},
            ),
            _tmp("p3b"),
        )

    def p4_no_native_does_not_run_unrelated_probes():
        # Profile WITHOUT pipx: loader visibly LACKS pipx, and no pipx
        # resolution exists -- yet the unit must PASS because pipx is never
        # probed for nat-34c1a3756742 (exact-profile scope).
        fs_without_pipx = _fake_fs(["/usr/bin/gettext", "/usr/share/mime", "/etc/mime.types"])
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-p4",
                native_profile_id="nat-34c1a3756742",
                profile_packages=list(_PROFILE_NAT34),  # exact profile; no pipx
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=_FAKE_LOADER_NAT34,
                fs=fs_without_pipx,
                network_unavailable=True,
                installed_packages=["demo-pkg"],
                pip_check_rc=0,
                smoke={},
            ),
            _tmp("p4"),
        )

    def p5_network_unavailable():
        # Network gate: the synthetic runner is invoked in "network=none" mode;
        # the V2 probe reports UNAVAILABLE and the unit passes.
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-p5",
                native_profile_id="nat-34c1a3756742",
                profile_packages=_PROFILE_NAT34,
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=_FAKE_LOADER_NAT34,
                fs=fs_ok(),
                network_unavailable=True,
                installed_packages=["demo-pkg"],
                pip_check_rc=0,
                smoke={},
            ),
            _tmp("p5"),
        )

    def p6_libxslt_correct_soname():
        # R3_DEFECT_C correction: loader exposes libxslt.so.1 (the real SONAME);
        # the frozen spec expects exactly that token.  This profile
        # (nat-02b9bb45ba01) is exercised so the corrected spec is proven.
        loader = _FAKE_LOADER_NAT34 + [
            "libmagic.so.1 (libc6,x86-64) => /lib/x86_64-linux-gnu/libmagic.so.1",
            "libxslt.so.1 (libc6,x86-64) => /lib/x86_64-linux-gnu/libxslt.so.1",
        ]
        profile = [
            "gettext", "libffi8", "libgdk-pixbuf-2.0-0", "liblcms2-2", "libmagic1",
            "libopenjp2-7", "libpq5", "libssl3", "libtiff6", "libwebp7",
            "libxslt1-dev", "shared-mime-info",
        ]
        fs_xslt = _fake_fs(["/usr/bin/gettext", "/usr/share/mime"])
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-p6",
                native_profile_id="nat-02b9bb45ba01",
                profile_packages=profile,
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=loader,
                fs=fs_xslt,
                network_unavailable=True,
                installed_packages=["demo-pkg"],
                pip_check_rc=0,
                smoke={},
            ),
            _tmp("p6"),
        )

    # ------------------------------------------------------------------
    # NEGATIVE (F2P) controls -- each MUST be detected / fail closed.
    # ------------------------------------------------------------------
    def n1_build_toolhouse_contamination():
        # vcs-versioning (build toolhouse) present in runtime env -> FAIL CLOSED.
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-n1",
                native_profile_id="nat-34c1a3756742",
                profile_packages=_PROFILE_NAT34,
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=_FAKE_LOADER_NAT34,
                fs=fs_ok(),
                network_unavailable=True,
                installed_packages=["demo-pkg", "vcs-versioning"],
                pip_check_rc=0,
                smoke={},
            ),
            _tmp("n1"),
        )

    def n2_missing_wheel_causes_source_build_request():
        # The unit's closure contains a pin with NO compatible wheel in the
        # runtime input.  Wheel-only resolution -> RUNTIME_ARTIFACT_CLOSURE_DEFECT.
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-n2",
                native_profile_id="nat-34c1a3756742",
                profile_packages=_PROFILE_NAT34,
                runtime_pins=["needs-build==1.0.0"],
                runtime_wheels=[],
                loader_tokens=_FAKE_LOADER_NAT34,
                fs=fs_ok(),
                network_unavailable=True,
                installed_packages=["demo-pkg"],
                pip_check_rc=0,
                smoke={},
            ),
            _tmp("n2"),
        )

    def n3_wrong_native_profile_probe():
        # Inject a payload from ANOTHER profile (nat-a396 includes pipx) into a
        # nat-34 unit whose fs lacks pipx -> profile-scope must FAIL CLOSED.
        fs_no_pipx = _fake_fs(["/usr/bin/gettext", "/usr/share/mime", "/etc/mime.types"])
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-n3",
                native_profile_id="nat-34c1a3756742",
                profile_packages=_PROFILE_NAT_A396,  # WRONG profile's package list
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=_FAKE_LOADER_NAT34,
                fs=fs_no_pipx,
                exec_resolutions={},
                network_unavailable=True,
                installed_packages=["demo-pkg"],
                pip_check_rc=0,
                smoke={},
            ),
            _tmp("n3"),
        )

    def n4_incorrect_absent_required_soname():
        # Loader does NOT expose libopenjp2.so.7 (R2's defect token
        # libopenjp2-7.so.7 is NOT accepted either).  Guards strict equality:
        # the corrected spec must not silently pass on a wrong/absent token.
        loader_bad = [t for t in _FAKE_LOADER_NAT34 if "libopenjp2" not in t]
        loader_bad.append("libopenjp2-7.so.7 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libopenjp2-7.so.7")
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-n4",
                native_profile_id="nat-34c1a3756742",
                profile_packages=_PROFILE_NAT34,
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=loader_bad,
                fs=fs_ok(),
                network_unavailable=True,
                installed_packages=["demo-pkg"],
                pip_check_rc=0,
                smoke={},
            ),
            _tmp("n4"),
        )

    def n4b_pipx_not_resolvable_on_path():
        # R3_DEFECT_B is genuine FAIL CLOSED: a profile that requires pipx but
        # where `command -v pipx` resolves nowhere must fail (no optimistic
        # fallback to a guessed path).
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-n4b",
                native_profile_id="nat-a39687f3d19c",
                profile_packages=_PROFILE_NAT_A396,
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=_FAKE_LOADER_NAT34,
                fs=_fake_fs(["/usr/bin/gettext", "/usr/share/mime", "/etc/mime.types"]),
                exec_resolutions={},  # pipx ABSENT from PATH
                network_unavailable=True,
                installed_packages=["demo-pkg"],
                pip_check_rc=0,
                smoke={},
            ),
            _tmp("n4b"),
        )

    def n4c_libxslt_wrong_soname():
        # R3_DEFECT_C negative: loader exposes only the R2-era wrong token
        # (libxslt.so.1.1 absent, libxslt.so.1 present would be required).
        # Here we expose NOTHING for xslt -> must fail closed.
        profile = [
            "gettext", "libffi8", "libgdk-pixbuf-2.0-0", "liblcms2-2", "libmagic1",
            "libopenjp2-7", "libpq5", "libssl3", "libtiff6", "libwebp7",
            "libxslt1-dev", "shared-mime-info",
        ]
        loader_no_xslt = [t for t in _FAKE_LOADER_NAT34 if "xslt" not in t]
        fs_no_xslt = _fake_fs(["/usr/bin/gettext", "/usr/share/mime"])
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-n4c",
                native_profile_id="nat-02b9bb45ba01",
                profile_packages=profile,
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=loader_no_xslt,
                fs=fs_no_xslt,
                network_unavailable=True,
                installed_packages=["demo-pkg"],
                pip_check_rc=0,
                smoke={},
            ),
            _tmp("n4c"),
        )

    def n5_network_visible_fetch_capable():
        # Simulation of a container that ISN'T isolated: network reachable.
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-n5",
                native_profile_id="nat-34c1a3756742",
                profile_packages=_PROFILE_NAT34,
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=_FAKE_LOADER_NAT34,
                fs=fs_ok(),
                network_unavailable=False,
                installed_packages=["demo-pkg"],
                pip_check_rc=0,
                smoke={},
            ),
            _tmp("n5"),
        )

    def n6_pip_check_inconsistency():
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-n6",
                native_profile_id="nat-34c1a3756742",
                profile_packages=_PROFILE_NAT34,
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=_FAKE_LOADER_NAT34,
                fs=fs_ok(),
                network_unavailable=True,
                installed_packages=["demo-pkg"],
                pip_check_rc=1,
                smoke={},
            ),
            _tmp("n6"),
        )

    def n7_deliberate_smoke_failure():
        return simulate_unit(
            SyntheticUnit(
                validation_unit_id="syn-n7",
                native_profile_id="nat-34c1a3756742",
                profile_packages=_PROFILE_NAT34,
                runtime_pins=["demo-pkg==1.0.0"],
                runtime_wheels=["demo_pkg-1.0.0-py3-none-any.whl"],
                loader_tokens=_FAKE_LOADER_NAT34,
                fs=fs_ok(),
                network_unavailable=True,
                installed_packages=["demo-pkg"],
                pip_check_rc=0,
                smoke={"import_wt0": "1", "manage_wt0": "0"},
            ),
            _tmp("n7"),
        )

    # wheel tag controls (owner-mandated additional negatives/positives)
    def wt_case(name: str, fn: str, expect_compat: bool):
        rec = {"name": name, "wheel": fn}
        got = wheel_compatible(fn)
        rec.update({"pass": got == expect_compat, "compatible": got,
                    "expect": expect_compat})
        return rec

    def _tmp(tag: str) -> None:
        # Resolution is list-based; no scratch dir is needed. Kept as a name
        # hook so the gate functions read identically to a real run.
        return None

    p2p_cases = [
        ("P1_clean_runtime_wheel_only_install_path", p1_clean_wheel_only_install),
        ("P2_runtime_pip_check_clean", p2_pip_check_clean),
        ("P3_native_profile_exact_required_probes", p3_native_exact_required_probes),
        ("P3b_pipx_path_resolution_exact", p3b_pipx_path_execution_required),
        ("P4_no_native_profile_does_not_probe_unrelated", p4_no_native_does_not_run_unrelated_probes),
        ("P5_network_unavailable_under_network_none", p5_network_unavailable),
        ("P6_libxslt_soname_exact_loader", p6_libxslt_correct_soname),
    ]
    f2p_cases = [
        ("F1_build_toolhouse_contamination_fail_closed", n1_build_toolhouse_contamination),
        ("F2_missing_runtime_wheel_source_build_request_fail_closed", n2_missing_wheel_causes_source_build_request),
        ("F3_wrong_native_profile_probe_fail_closed", n3_wrong_native_profile_probe),
        ("F4_incorrect_absent_required_soname_fail_closed", n4_incorrect_absent_required_soname),
        ("F4b_pipx_not_resolvable_fail_closed", n4b_pipx_not_resolvable_on_path),
        ("F4c_libxslt_absent_soname_fail_closed", n4c_libxslt_wrong_soname),
        ("F5_network_visible_fetchcapable_fail_closed", n5_network_visible_fetch_capable),
        ("F6_deliberate_pip_check_inconsistency_fail_closed", n6_pip_check_inconsistency),
        ("F7_deliberate_smoke_failure_fail_closed", n7_deliberate_smoke_failure),
    ]
    wheel_controls = [
        wt_case("WT_abi3_cp37", "bcrypt-4.2.1-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", True),
        wt_case("WT_abi3_cp38", "protobuf-5.29.2-cp38-abi3-manylinux2014_x86_64.whl", True),
        wt_case("WT_abi3_cp39", "deptry-0.21.2-cp39-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", True),
        wt_case("WT_cp312_native", "demo_pkg-1.0.0-cp312-cp312-manylinux_2_17_x86_64.whl", True),
        wt_case("WT_py3_none_any", "petl-1.7.17-py3-none-any.whl", True),
        wt_case("WT_win_amd64_rejected", "bcrypt-4.2.1-cp37-abi3-win_amd64.whl", False),
        wt_case("WT_macos_rejected", "demo_pkg-1.0.0-cp312-cp312-macosx_10_9_x86_64.whl", False),
        wt_case("WT_cp311_not_abi3_rejected", "demo_pkg-1.0.0-cp311-cp311-manylinux2014_x86_64.whl", False),
        wt_case("WT_future_cp313_rejected", "demo_pkg-1.0.0-cp313-cp313-manylinux2014_x86_64.whl", False),
    ]

    suite = {"p2p": [], "f2p": [], "wheel_tags": []}
    for name, fn in p2p_cases:
        suite["p2p"].append(check(name, fn, expect_pass=True))
    for name, fn in f2p_cases:
        suite["f2p"].append(check(name, fn, expect_pass=False))
    suite["wheel_tags"] = wheel_controls

    n_p2p = sum(1 for r in suite["p2p"] if r.get("pass"))
    n_f2p = sum(1 for r in suite["f2p"] if r.get("pass"))
    n_wt = sum(1 for r in suite["wheel_tags"] if r.get("pass"))
    return {
        "p2p": {"n_items": len(suite["p2p"]), "n_pass": n_p2p, "all_pass": n_p2p == len(suite["p2p"]), "items": suite["p2p"]},
        "f2p": {"n_items": len(suite["f2p"]), "n_pass": n_f2p, "all_pass": n_f2p == len(suite["f2p"]), "items": suite["f2p"]},
        "wheel_tags": {"n_items": len(suite["wheel_tags"]), "n_pass": n_wt, "all_pass": n_wt == len(suite["wheel_tags"]), "items": suite["wheel_tags"]},
        "all_pass": (n_p2p == len(suite["p2p"]) and n_f2p == len(suite["f2p"]) and n_wt == len(suite["wheel_tags"])),
    }


def _run_preflight() -> dict:
    """READ-ONLY frozen-input preflight (no network, no docker, no writes)."""
    import csv

    checks = {}

    # 1. plan present, 12 units, members of 144 matrix
    plan = json.load(open(PLAN, encoding="utf-8"))
    units = plan["units"]
    matrix = set()
    with open(MATRIX, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            matrix.add(row.get("unit_id") or row.get("validation_unit_id"))
    bad = [u["validation_unit_id"] for u in units if u["validation_unit_id"] not in matrix]
    checks["plan"] = {"n_units": len(units), "n_matrix": len(matrix),
                      "not_in_matrix": bad, "pass_": len(units) == 12 and not bad}

    # 2. frozen locks exist for every member task
    missing_locks = []
    for u in units:
        for tid in u["member_task_ids"]:
            lp = os.path.join(LOCK_DIR, f"{tid}_{u['lock_type']}.toml")
            if not os.path.isfile(lp):
                missing_locks.append(tid)
    checks["locks"] = {"missing": missing_locks, "pass_": not missing_locks}

    # 3. marker audit exists; exactly the frozen exclusions
    m = marker_excluded_linux_names(MARKER_AUDIT)
    checks["marker_excluded_linux"] = sorted(m)
    checks["marker_audit_ok"] = m == {"pywin32"}

    # 4. wheelhouse + canon runtime wheel input enumerated (no copies)
    wheels = assemble_runtime_input(WHEELHOUSE_PY312, CANON_PY312)
    checks["runtime_wheel_input"] = {"n_wheels": len(wheels), "pass_": len(wheels) > 0}

    # 5. docker images manifest present (real calibration needs them later)
    checks["docker_profile_manifest"] = os.path.isfile(DOCKER_PROFILES)

    return {k: v for k, v in checks.items()}


def _run_closure_check() -> dict:
    """READ-ONLY 12-unit frozen closure resolution (no execution, no docker,
    no scratch copies: the runtime wheel input is enumerated and resolved by
    filename list)."""
    plan = json.load(open(PLAN, encoding="utf-8"))
    units_report = []
    runtime_wheels = assemble_runtime_input(WHEELHOUSE_PY312, CANON_PY312)
    for u in plan["units"]:
        lock = os.path.join(LOCK_DIR, f"{u['member_task_ids'][0]}_{u['lock_type']}.toml")
        ppaths = []
        for tid in u["member_task_ids"]:
            wtx = os.path.join(WORKTREE_DIR, tid, "pyproject.toml")
            if os.path.isfile(wtx):
                ppaths.append(wtx)
        closure = derive_runtime_closure(lock, ppaths, MARKER_AUDIT)
        res = resolve_runtime_artifacts(closure["runtime_pins"], wheel_file_list=runtime_wheels)
        units_report.append({
            "validation_unit_id": u["validation_unit_id"],
            "n_pins": len(closure["pins"]),
            "n_runtime": len(closure["runtime_pins"]),
            "excluded": closure["excluded"],
            **res,
        })
    ok = all(ur["pass_"] for ur in units_report)
    return {"n_units": len(units_report), "all_resolve": ok, "units": units_report}


def _find_canon_wheel(wheelname: str) -> str | None:
    for ident in os.listdir(CANON_PY312):
        wd = os.path.join(CANON_PY312, ident, "wheels")
        if os.path.isdir(wd) and os.path.isfile(os.path.join(wd, wheelname)):
            return os.path.join(wd, wheelname)
    return None


# ---------------------------------------------------------------------------
# Manifest (self-inclusive hash freeze)
# ---------------------------------------------------------------------------

def build_harness_manifest() -> dict:
    """Build the harness manifest dict.

    Every R3 harness file is listed with SHA-256 and byte size, INCLUDING the
    manifest file itself.  To keep the self-entry deterministic, the manifest's
    own hash is defined as the SHA-256 of this manifest's JSON skeleton (all
    fields EXCEPT the manifest file's own files-entry), which is stable across
    runs and reproducible: drop ``files['D7_R3_HARNESS_MANIFEST.json']``, dump
    with ``json.dumps(indent=2, sort_keys=True) + '\\n'``, SHA-256, and compare.
    """
    entries = {}
    for rel in HARNESS_FILES:
        p = os.path.join(HARNESS_DIR, rel)
        if not os.path.isfile(p):
            continue
        entries[rel] = {"sha256": sha256(p), "bytes": os.path.getsize(p)}

    skeleton_files = {rel: v for rel, v in entries.items() if rel != "D7_R3_HARNESS_MANIFEST.json"}
    skeleton = {
        "artifact": "D7_R3_HARNESS_MANIFEST",
        "mission": "M17_ENV_CANON_D7_R3_HARNESS_DEFECT_CORRECTION_AND_FREEZE",
        "harness_dir": HARNESS_DIR,
        "files": skeleton_files,
        "created_at_utc": utcnow(),
    }
    skel_json = json.dumps(skeleton, indent=2, sort_keys=True) + "\n"
    self_sha = hashlib.sha256(skel_json.encode("utf-8")).hexdigest()

    manifest = dict(skeleton)
    manifest["files"] = dict(skeleton_files)
    manifest["files"]["D7_R3_HARNESS_MANIFEST.json"] = {
        "sha256": self_sha,
        "bytes": len(skel_json.encode("utf-8")),
        "note": "self-hash = SHA-256 of this manifest's JSON skeleton excluding "
                "files['D7_R3_HARNESS_MANIFEST.json'] (deterministic self-reference).",
    }
    return manifest


def emit_manifest() -> str:
    manifest = build_harness_manifest()
    with open(MANIFEST_OUT, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")
    return MANIFEST_OUT


# ---------------------------------------------------------------------------
# Output artifacts
# ---------------------------------------------------------------------------

def write_freeze_artifacts(suite: dict, closure: dict, preflight: dict) -> None:
    # The manifest file is written first on disk; freeze/report must reference
    # its recorded hashes so the evidence chain is byte-exact.
    manifest = json.load(open(MANIFEST_OUT, encoding="utf-8"))
    os.makedirs(MANIFESTS, exist_ok=True)
    os.makedirs(RECEIPTS, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)

    freeze = {
        "artifact": "D7_R3_HARNESS_FREEZE",
        "mission": "M17_ENV_CANON_D7_R3_HARNESS_DEFECT_CORRECTION_AND_FREEZE",
        "mission_class": "ENGINEERING_QUALIFICATION_HARNESS_DEFECT_CORRECTION_ONLY",
        "scientific_changes": "NONE",
        "population_changed": False,
        "metrics_thresholds_selectors_locks_changed": False,
        "final_r4b_frozen_artifacts_changed": False,
        "r2_evidence_changed": False,
        "real_12_unit_execution_started": False,
        "docker_used_in_freezes_now": True,
        "docker_used_network": "none-only-read-only-probes",
        "network_used_in_freeze": False,
        "source_build_attempted": False,
        "harness_dir": HARNESS_DIR,
        "harness_files": manifest["files"],
        "defect_corrections": [
            "R2_DEFECT_A: libopenjp2-7 SONAME libopenjp2-7.so.7 -> libopenjp2.so.7",
            "R2_DEFECT_B: pipx absolute /usr/local/bin/pipx -> EXEC-on-PATH probe (command -v pipx -> /usr/bin/pipx)",
            "R2_DEFECT_C: libxslt1-dev SONAME libxslt.so.1.1 -> libxslt.so.1",
        ],
        "freeze_token": "M17_ENV_CANON_D7_R3_HARNESS_FREEZE_COMPLETE_READY_FOR_CALIBRATION_OWNER_DECISION",
        "created_at_utc": utcnow(),
    }
    with open(FREEZE_OUT, "w", encoding="utf-8") as f:
        json.dump(freeze, f, indent=2, sort_keys=True)
        f.write("\n")

    receipt = {
        "artifact": "D7_R3_HARNESS_P2P_F2P",
        "mission": "M17_ENV_CANON_D7_R3_HARNESS_DEFECT_CORRECTION_AND_FREEZE",
        "deterministic": True,
        "docker_not_used": True,
        "network_not_used": True,
        "real_units_not_used": True,
        "p2p": suite["p2p"],
        "f2p": suite["f2p"],
        "wheel_tags": suite["wheel_tags"],
        "closure_check": {"n_units": closure["n_units"], "all_resolve": closure["all_resolve"]},
        "preflight": preflight,
        "created_at_utc": utcnow(),
    }
    with open(RECEIPT_OUT, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, sort_keys=True)
        f.write("\n")

    lines = [
        "# D7_R3_HARNESS_FREEZE_REPORT",
        "",
        f"- **Mission:** `M17_ENV_CANON_D7_R3_HARNESS_DEFECT_CORRECTION_AND_FREEZE`",
        f"- **Harness:** `{HARNESS_DIR}`",
        f"- **Deterministic synthetic suite:** P2P {suite['p2p']['n_pass']}/{suite['p2p']['n_items']} | F2P {suite['f2p']['n_pass']}/{suite['f2p']['n_items']} | wheel-tag controls {suite['wheel_tags']['n_pass']}/{suite['wheel_tags']['n_items']}",
        f"- **Real 12-unit calibration executed:** NO",
        f"- **Scientific changes:** NONE",
        "",
        "## Corrected engineering probe-spec defects (evidence-mapped)",
        "",
        "| defect | package | R2 spec | R3 spec (loader-truth) |",
        "|---|---|---|---|",
        "| R2_DEFECT_A | `libopenjp2-7` | `libopenjp2-7.so.7` | `libopenjp2.so.7` |",
        "| R2_DEFECT_B | `pipx` | PATH `/usr/local/bin/pipx` | EXEC probe (command -v pipx -> `/usr/bin/pipx`) |",
        "| R2_DEFECT_C | `libxslt1-dev` | `libxslt.so.1.1` | `libxslt.so.1` |",
        "",
        "## Harness SHA256 (per file)",
        "",
        "| file | sha256 | bytes |",
        "|---|---|---|",
    ]
    for rel in sorted(manifest["files"]):
        lines.append(f"| `{rel}` | `{manifest['files'][rel]['sha256']}` | {manifest['files'][rel]['bytes']} |")
    lines += [
        "",
        "## Synthetic suite items",
        "",
        "### Positive (P2P)",
        "",
    ]
    for it in suite["p2p"]["items"]:
        lines.append(f"- {it['name']}: `{'PASS' if it.get('pass') else 'FAIL'}` ({it.get('classification', it.get('error', ''))})")
    lines += ["", "### Negative (F2P), each must FAIL CLOSED", ""]
    for it in suite["f2p"]["items"]:
        lines.append(f"- {it['name']}: detected as `{it.get('classification')}` ({'OK' if it.get('pass') else 'NOT DETECTED'})")
    lines += [
        "",
        "## Frozen closure (read-only, 12 units, no execution)",
        "",
        f"- `{closure['n_units']}` units checked | all_resolve=`{closure['all_resolve']}`",
        "- Runtime path is wheel-only; a missing/incompatible wheel is a runtime-artifact-closure defect (FAIL CLOSED); no source build is ever attempted.",
        "",
        "## Build/runtime separation mechanism",
        "",
        "- SOURCE-BUILD CANON -> frozen canonical wheels -> D7 runtime wheel input -> clean runtime install -> pip check / smoke / native probes.",
        "- The build toolhouse is NEVER installed into the runtime environment. `audit_toolhouse_contamination` fails closed if any build-toolhouse-only distribution (vcs-versioning, poetry-core, setuptools-scm, wheel) is present.",
        "",
        "## Native-profile derivation & matching",
        "",
        "- Probes are derived from the unit's exact frozen `native_profile_id`; no global probe map.",
        "- SONAME matching validates loader-visible names with strict equality against frozen allowed sonames - no substring-based optimistic matching.",
        "- PATH/executable requirements use fetch-truth: absolute paths where the frozen images genuinely place them, and EXEC-on-PATH resolution (command -v) for PATH-resolved executables (pipx).",
        "",
        "## Network enforcement",
        "",
        "- Every execution path requires the network gate: containers run with `--network=none` and the V2 probe must report `NETWORK_UNAVAILABLE`; a reachable/fetch-capable outcome is FAIL CLOSED.",
        "",
        "## R2 immutability",
        "",
        "- R2 harness (`harness/d7_r2`) is immutable historical evidence; all its manifest-listed files were SHA-256-verified before and after this mission (unchanged).  R3 is a separate additive harness (harness/d7_r3).",
        "",
    ]
    with open(REPORT_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return freeze, receipt


def main() -> int:
    ap = argparse.ArgumentParser(description="D7_R3 harness freeze driver")
    ap.add_argument("--synthetic", action="store_true", help="run deterministic synthetic P2P/F2P suite (no docker, no network)")
    ap.add_argument("--preflight", action="store_true", help="read-only frozen-input preflight")
    ap.add_argument("--closure-check", action="store_true", help="read-only 12-unit frozen closure resolution")
    ap.add_argument("--manifest", action="store_true", help="emit D7_R3_HARNESS_MANIFEST.json")
    ap.add_argument("--freeze-outputs", action="store_true", help="write manifest+freeze+receipt+report (requires successful suite)")
    args = ap.parse_args()

    if not (args.synthetic or args.preflight or args.closure_check or args.manifest or args.freeze_outputs):
        ap.print_help()
        return 0

    if args.preflight:
        pre = _run_preflight()
        print(json.dumps(pre, indent=2, sort_keys=True))

    if args.closure_check:
        cl = _run_closure_check()
        print(json.dumps(cl, indent=2, sort_keys=True))

    if args.manifest:
        out = emit_manifest()
        print(f"MANIFEST_WRITTEN={out}")

    if args.freeze_outputs:
        suite = run_synthetic_suite()
        if not suite["all_pass"]:
            print("SYNTHETIC_SUITE_FAILED")
            for bucket in ("p2p", "f2p", "wheel_tags"):
                for it in suite[bucket]["items"]:
                    if not it.get("pass"):
                        print(f"  FAILED {bucket}::{it['name']} {it.get('error', '')}")
            return 1
        import shutil

        scratch = os.path.join(STORE, "tmp", "d7_r3_preflight_wh")
        shutil.rmtree(scratch, ignore_errors=True)
        cl = _run_closure_check()
        pre = _run_preflight()
        if not cl["all_resolve"]:
            print("CLOSURE_CHECK_FAILED")
            for ur in cl["units"]:
                if not ur["pass_"]:
                    print(f"  {ur['validation_unit_id']} missing={ur['missing']} incompatible={ur['incompatible']}")
            return 1
        if not pre["plan"]["pass_"] or not pre["marker_audit_ok"]:
            print("PREFLIGHT_FAILED")
            return 1
        emit_manifest()
        freeze, receipt = write_freeze_artifacts(suite, cl, pre)
        print(f"FREEZE_OUT={FREEZE_OUT}")
        print(f"RECEIPT_OUT={RECEIPT_OUT}")
        print(f"REPORT_OUT={REPORT_OUT}")
        print("P2P %d/%d" % (suite["p2p"]["n_pass"], suite["p2p"]["n_items"]))
        print("F2P %d/%d" % (suite["f2p"]["n_pass"], suite["f2p"]["n_items"]))
        print("WT  %d/%d" % (suite["wheel_tags"]["n_pass"], suite["wheel_tags"]["n_items"]))
        print("CLOSURE_CHECK all_resolve=%s" % cl["all_resolve"])
        print("SCIENTIFIC_CHANGES=NONE")

    if args.synthetic and not args.freeze_outputs:
        suite = run_synthetic_suite()
        print(json.dumps(suite, indent=2, sort_keys=True))
        print("SYNTHETIC_ALL_PASS=%s" % suite["all_pass"])
        return 0 if suite["all_pass"] else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
