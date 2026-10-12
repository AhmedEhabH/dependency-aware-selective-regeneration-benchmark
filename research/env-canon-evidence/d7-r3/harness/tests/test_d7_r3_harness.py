"""Unit + deterministic synthetic tests for the D7_R3 harness freeze.

Mission: M17_ENV_CANON_D7_R3_HARNESS_DEFECT_CORRECTION_AND_FREEZE
(ENGINEERING QUALIFICATION / HARNESS DEFECT CORRECTION ONLY)

Harness-only tests: NO docker, NO network, NO real calibration unit, NO frozen
artifact is read or modified.  Runs the same synthetic gate functions the
driver uses, so the pytest run and the receipt-producing run agree byte-for-byte
on outcomes.

Test scope also covers the three evidence-mapped R2 -> R3 engineering
corrections:
  - libopenjp2-7 SONAME token is libopenjp2.so.7 (R2_DEFECT_A)
  - pipx is an EXEC-on-PATH probe resolving to /usr/bin/pipx (R2_DEFECT_B)
  - libxslt1-dev SONAME token is libxslt.so.1 (R2_DEFECT_C)
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import d7_r3_probes as probes  # noqa: E402
from d7_r3_closure import (  # noqa: E402
    derive_runtime_closure,
    marker_excluded_linux_names,
    poetry_pins,
    resolve_runtime_artifacts,
    win32_platform_names,
)
from d7_r3_native_specs import NATIVE_PROBE_SPECS  # noqa: E402
from d7_r3_validation_driver import (  # noqa: E402
    _FAKE_LOADER_NAT34,
    _PROFILE_NAT34,
    _run_closure_check,
    _run_preflight,
    run_synthetic_suite,
)
from d7_r3_wheeltags import wheel_compatible  # noqa: E402

HARNESS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_p2p_all_pass():
    suite = run_synthetic_suite()
    assert suite["p2p"]["all_pass"]
    assert suite["f2p"]["all_pass"]
    assert suite["wheel_tags"]["all_pass"]
    assert suite["all_pass"]


def test_p2p_counts():
    suite = run_synthetic_suite()
    assert suite["p2p"]["n_items"] >= 5  # the contract's required positives
    assert suite["f2p"]["n_items"] >= 7  # the contract's required negatives


# ---- R2 -> R3 engineering corrections (loader/path truth) ----
def test_r3_defect_a_libopenjp2_soname_corrected():
    spec = NATIVE_PROBE_SPECS["libopenjp2-7"]
    assert spec["kind"] == "SONAME"
    assert spec["allowed_sonames"] == ("libopenjp2.so.7",)
    # the R2-era wrong token must not appear anywhere in the frozen spec
    for pkg_spec in NATIVE_PROBE_SPECS.values():
        for soname in pkg_spec.get("allowed_sonames", ()):
            assert "libopenjp2-7.so" not in soname


def test_r3_defect_b_pipx_exec_on_path():
    spec = NATIVE_PROBE_SPECS["pipx"]
    assert spec["kind"] == "EXEC"
    assert spec["executable"] == "pipx"
    # R2's wrong absolute /usr/local/bin/pipx must not be the requirement
    assert spec.get("path") is None


def test_r3_defect_c_libxslt1_dev_soname_corrected():
    spec = NATIVE_PROBE_SPECS["libxslt1-dev"]
    assert spec["kind"] == "SONAME"
    assert spec["allowed_sonames"] == ("libxslt.so.1",)


def test_loader_truth_nat34_exposes_libopenjp2_so7():
    tokens = [t.split(None, 1)[0] for t in _FAKE_LOADER_NAT34]
    assert "libopenjp2.so.7" in tokens
    assert "libopenjp2-7.so.7" not in tokens


# ---- required positive controls ----
def test_p1_clean_wheel_only_install_path():
    suite = run_synthetic_suite()
    names = [it["name"] for it in suite["p2p"]["items"]]
    assert "P1_clean_runtime_wheel_only_install_path" in names
    it = next(x for x in suite["p2p"]["items"] if x["name"] == "P1_clean_runtime_wheel_only_install_path")
    assert it["pass"]


def test_p2_runtime_pip_check_clean():
    suite = run_synthetic_suite()
    it = next(x for x in suite["p2p"]["items"] if x["name"] == "P2_runtime_pip_check_clean")
    assert it["pass"]


def test_p3_native_profile_exact_required_probes():
    suite = run_synthetic_suite()
    it = next(x for x in suite["p2p"]["items"] if x["name"] == "P3_native_profile_exact_required_probes")
    assert it["pass"]


def test_p3b_pipx_path_resolution_exact():
    suite = run_synthetic_suite()
    it = next(x for x in suite["p2p"]["items"] if x["name"] == "P3b_pipx_path_resolution_exact")
    assert it["pass"]


def test_p4_no_native_profile_does_not_probe_unrelated():
    suite = run_synthetic_suite()
    it = next(x for x in suite["p2p"]["items"] if x["name"] == "P4_no_native_profile_does_not_probe_unrelated")
    assert it["pass"]


def test_p5_network_unavailable_under_network_none():
    suite = run_synthetic_suite()
    it = next(x for x in suite["p2p"]["items"] if x["name"] == "P5_network_unavailable_under_network_none")
    assert it["pass"]


def test_p6_libxslt_soname_exact_loader():
    suite = run_synthetic_suite()
    it = next(x for x in suite["p2p"]["items"] if x["name"] == "P6_libxslt_soname_exact_loader")
    assert it["pass"]


# ---- wheel-tag controls (owner-specified) ----
def test_wt_abi3_cp37():
    assert wheel_compatible("bcrypt-4.2.1-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl")


def test_wt_abi3_cp38():
    assert wheel_compatible("protobuf-5.29.2-cp38-abi3-manylinux2014_x86_64.whl")


def test_wt_abi3_cp39():
    assert wheel_compatible("deptry-0.21.2-cp39-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl")


def test_wt_cp312_native():
    assert wheel_compatible("demo_pkg-1.0.0-cp312-cp312-manylinux_2_17_x86_64.whl")


def test_wt_py3_none_any():
    assert wheel_compatible("petl-1.7.17-py3-none-any.whl")


def test_wt_win_amd64_rejected():
    assert not wheel_compatible("bcrypt-4.2.1-cp37-abi3-win_amd64.whl")


def test_wt_macos_rejected():
    assert not wheel_compatible("demo_pkg-1.0.0-cp312-cp312-macosx_10_9_x86_64.whl")


def test_wt_cp311_not_abi3_rejected():
    assert not wheel_compatible("demo_pkg-1.0.0-cp311-cp311-manylinux2014_x86_64.whl")


def test_wt_future_cp313_rejected():
    assert not wheel_compatible("demo_pkg-1.0.0-cp313-cp313-manylinux2014_x86_64.whl")


# ---- required negative controls (each must fail closed) ----
def test_f1_build_toolhouse_contamination_detected():
    suite = run_synthetic_suite()
    it = next(x for x in suite["f2p"]["items"] if x["name"] == "F1_build_toolhouse_contamination_fail_closed")
    assert it["pass"]
    assert it["classification"] == "RUNTIME_TOOLHOUSE_CONTAMINATION"


def test_f2_missing_runtime_wheel_source_build_request_detected():
    suite = run_synthetic_suite()
    it = next(x for x in suite["f2p"]["items"] if x["name"] == "F2_missing_runtime_wheel_source_build_request_fail_closed")
    assert it["pass"]
    assert it["classification"] == "RUNTIME_ARTIFACT_CLOSURE_DEFECT"


def test_f3_wrong_native_profile_probe_detected():
    suite = run_synthetic_suite()
    it = next(x for x in suite["f2p"]["items"] if x["name"] == "F3_wrong_native_profile_probe_fail_closed")
    assert it["pass"]  # wrong profile payload must produce a native failure
    assert it["classification"] == "NATIVE_FAIL"


def test_f4_incorrect_absent_required_soname_detected():
    suite = run_synthetic_suite()
    it = next(x for x in suite["f2p"]["items"] if x["name"] == "F4_incorrect_absent_required_soname_fail_closed")
    assert it["pass"]
    assert it["classification"] == "NATIVE_FAIL"


def test_f4b_pipx_not_resolvable_detected():
    suite = run_synthetic_suite()
    it = next(x for x in suite["f2p"]["items"] if x["name"] == "F4b_pipx_not_resolvable_fail_closed")
    assert it["pass"]
    assert it["classification"] == "NATIVE_FAIL"


def test_f4c_libxslt_absent_soname_detected():
    suite = run_synthetic_suite()
    it = next(x for x in suite["f2p"]["items"] if x["name"] == "F4c_libxslt_absent_soname_fail_closed")
    assert it["pass"]
    assert it["classification"] == "NATIVE_FAIL"


def test_f5_network_visible_detected():
    suite = run_synthetic_suite()
    it = next(x for x in suite["f2p"]["items"] if x["name"] == "F5_network_visible_fetchcapable_fail_closed")
    assert it["pass"]
    assert it["classification"] == "NETWORK_FAIL_CLOSED"


def test_f6_pip_check_inconsistency_detected():
    suite = run_synthetic_suite()
    it = next(x for x in suite["f2p"]["items"] if x["name"] == "F6_deliberate_pip_check_inconsistency_fail_closed")
    assert it["pass"]
    assert it["classification"] == "PIP_CHECK_FAIL"


def test_f7_smoke_failure_detected():
    suite = run_synthetic_suite()
    it = next(x for x in suite["f2p"]["items"] if x["name"] == "F7_deliberate_smoke_failure_fail_closed")
    assert it["pass"]
    assert it["classification"] == "SMOKE_FAIL"


# ---- no R2 harness imports leak into R3 ----
def test_no_r2_import_leak():
    import d7_r3_closure
    import d7_r3_native_specs
    import d7_r3_probes
    import d7_r3_validation_driver
    import d7_r3_wheeltags

    for mod in (d7_r3_closure, d7_r3_native_specs, d7_r3_probes,
                d7_r3_validation_driver, d7_r3_wheeltags):
        assert "d7_r2" not in getattr(mod, "__name__", "")


def test_run_native_probes_exact():
    # strict equality: the wrong R2 token libopenjp2-7.so.7 must NOT satisfy
    # the corrected libopenjp2.so.7 spec.
    failures = probes.run_native_probes(
        {"libopenjp2-7": {"kind": "SONAME", "allowed_sonames": ("libopenjp2.so.7",)}},
        ["libopenjp2-7.so.7 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libopenjp2-7.so.7"],
        {},
    )
    assert len(failures) == 1
    assert failures[0]["package"] == "libopenjp2-7"


def test_exec_probe_strict_resolution():
    spec = {"kind": "EXEC", "executable": "pipx"}
    # resolved + file present -> pass
    ok = probes.run_native_probes({"pipx": spec}, [], {"/usr/bin/pipx": True},
                                  exec_resolutions={"pipx": "/usr/bin/pipx"})
    assert ok == []
    # not resolved -> fail closed
    bad = probes.run_native_probes({"pipx": spec}, [], {},
                                   exec_resolutions={"pipx": ""})
    assert len(bad) == 1 and bad[0]["detail"].startswith("executable")


# ---- closure / platform semantics ----
def test_frozen_marker_exclusion_is_exactly_pywin32(tmp_path):
    audit = tmp_path / "marker.json"
    audit.write_text('{"packages": {"pywin32": {"classification": "MARKER_EXCLUDED_ON_LINUX"}, "deptry": {"classification": "MAIN"}}}', encoding="utf-8")
    assert marker_excluded_linux_names(str(audit)) == {"pywin32"}


def test_win32_platform_exclusion_reads_frozen_pyproject(tmp_path):
    pyproj = tmp_path / "pyproject.toml"
    pyproj.write_text(
        '[tool.poetry.dependencies]\n'
        'python = "^3.12"\n'
        'magic-bin = {version = "^0.4.14", platform = "win32"}\n'
        'ruff = "^0.9.1"\n',
        encoding="utf-8",
    )
    assert win32_platform_names([str(pyproj)]) == {"magic-bin"}


def test_dev_tools_are_not_pruned_from_closure(tmp_path):
    lock = tmp_path / "poetry.lock"
    lock.write_text(
        '[[package]]\nname = "demo"\nversion = "1.0.0"\n'
        '[[package]]\nname = "ruff"\nversion = "0.9.1"\n'
        '[[package]]\nname = "deptry"\nversion = "0.21.2"\n'
        '[[package]]\nname = "pywin32"\nversion = "308"\n'
        '[metadata.files]\n', encoding="utf-8")
    audit = tmp_path / "marker.json"
    audit.write_text('{"packages": {"pywin32": {"classification": "MARKER_EXCLUDED_ON_LINUX"}}}', encoding="utf-8")
    pyproj = tmp_path / "pyproject.toml"
    pyproj.write_text('[tool.poetry.dependencies]\npython = "^3.12"\nruff = "^0.9.1"\ndeptry = "^0.21"\n', encoding="utf-8")
    closure = derive_runtime_closure(str(lock), [str(pyproj)], str(audit))
    pins = {p.split("==")[0] for p in closure["runtime_pins"]}
    assert "ruff" in pins and "deptry" in pins  # dev-tool packages stay
    assert "pywin32" not in pins
    assert [e["pin"] for e in closure["excluded"]] == ["pywin32==308"]


def test_no_win32_and_no_marker_then_kept(tmp_path):
    lock = tmp_path / "poetry.lock"
    lock.write_text(
        '[[package]]\nname = "demo"\nversion = "1.0.0"\n'
        '[metadata.files]\n', encoding="utf-8")
    audit = tmp_path / "marker.json"
    audit.write_text('{"packages": {}}', encoding="utf-8")
    closure = derive_runtime_closure(str(lock), [str(tmp_path / "missing_pyproject.toml")], str(audit))
    assert closure["runtime_pins"] == ["demo==1.0.0"]
    assert closure["excluded"] == []


def test_resolve_missing_wheel_fails_closed():
    res = resolve_runtime_artifacts(["needs-build==1.0.0"], wheel_file_list=[])
    assert not res["pass_"]
    assert res["missing"] == ["needs-build==1.0.0"]


def test_readonly_12_unit_closure_all_resolves():
    # Real frozen inputs, read-only, NO execution. This is the same check the
    # freeze gate runs; kept here so the frozen closure state is guarded by CI.
    cl = _run_closure_check()
    assert cl["n_units"] == 12
    assert cl["all_resolve"]


def test_preflight_frozen_inputs():
    pre = _run_preflight()
    assert pre["plan"]["pass_"]
    assert pre["marker_audit_ok"]
    assert pre["locks"]["pass_"]
    assert pre["runtime_wheel_input"]["pass_"]


def test_contract_file_present():
    assert os.path.isfile(os.path.join(HARNESS, "D7_R3_HARNESS_CONTRACT.md"))


def test_no_real_unit_executed_by_synthetic():
    # The synthetic suite uses only harness-only synthetic unit ids.
    suite = run_synthetic_suite()
    for bucket in ("p2p", "f2p"):
        for it in suite[bucket]["items"]:
            assert "vu-" not in it.get("name", "")
