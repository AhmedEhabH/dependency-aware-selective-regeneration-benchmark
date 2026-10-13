"""M17_D7 R4-I5 zero-container N12 smoke P2P/F2P tests (mission-local).

Mission M17_D7_R4_I5_ZERO_CONTAINER_SMOKE_N12.

Covers:

P2P (P1..P12):
  P1  — exact frozen N12 plan loads in frozen order and SHA matches.
  P2  — all required R4-D strata/coverage represented by N12 remain unchanged.
  P3  — a selected Poetry unit resolves through integrated R4-B + R4-A.
  P4  — a selected uv unit resolves through integrated R4-B + R4-A.
  P5  — Python 3.8 target uses py38 compatibility semantics.
  P6  — Python 3.9 target uses py39 compatibility semantics.
  P7  — Python 3.12 target uses py312 compatibility semantics.
  P8  — both source-fidelity units resolve PyXB/authorizenet through SF R1.
  P9  — editable root/self is not treated as a third-party artifact.
  P10 — I3 receipt consumed without Docker re-query (14/0/0 structurally).
  P11 — all mapped member-task commit identities checked without materialization.
  P12 — repeated run yields deterministic canonical results.

F2P (F1..F16):
  F1  — mutated N12 membership fails closed.
  F2  — mutated N12 order fails closed.
  F3  — mutated plan SHA fails closed.
  F4  — unknown Python era fails closed.
  F5  — unknown lock type fails closed.
  F6  — unsupported/unknown required source semantics fails closed.
  F7  — missing unit metadata fails closed.
  F8  — missing member-task metadata fails closed.
  F9  — missing repository identity fails closed.
  F10 — missing commit object fails closed.
  F11 — malformed I3 Docker reconciliation receipt fails closed.
  F12 — wrong/missing integrated provider artifact fails closed.
  F13 — package-name near-match must NOT satisfy exact dependency identity.
  F14 — wrong version must NOT satisfy the requirement.
  F15 — wrong-era wheel must NOT be accepted.
  F16 — network fallback configuration/path fails closed / absent by construction.

F2P uses fixtures/copies/mocks only; authoritative evidence is never mutated.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
R4_DIR = ROOT / "research" / "env-canon-r4"
SF_R1_DIR = ROOT / "research" / "source-fidelity-r1"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

import r4_i5_zero_container_smoke as i5  # noqa: E402

from benchmark.wp2.env_r4.contracts import (  # noqa: E402
    NormalizedRequirement,
    RuntimeTarget,
    SourceType,
    unbind_lock_parser,
    wheel_compatible,
)
from benchmark.wp2.env_r4.integrated_parser import bind_integrated_parser  # noqa: E402

HAS_STORE = Path(r"D:\wp2_env_store\manifests").is_dir()
HAS_REPO = Path(
    r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor"
).is_dir()

PLAN_PATH = R4_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json"
MATRIX_PATH = R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json"
I3_RECEIPT_PATH = R4_DIR / "R4_I3_CAPABILITY_STATE_RECONCILIATION.json"
EXPECTED_PLAN_SHA = i5.EXPECTED_PLAN_SHA
FROZEN_ORDER = list(i5.FROZEN_UNIT_ORDER)
SF_UNITS = list(i5.SOURCE_FIDELITY_UNITS)
EXPECTED_STRATA = {"3.12_poetry": 25, "3.12_uv": 21, "3.9_poetry": 83, "3.8_poetry": 15}

T38 = RuntimeTarget("3.8", "cpython", "linux", "x86_64")
T39 = RuntimeTarget("3.9", "cpython", "linux", "x86_64")
T312 = RuntimeTarget("3.12", "cpython", "linux", "x86_64")


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


@pytest.fixture(autouse=True)
def _isolate_binding() -> None:
    unbind_lock_parser()
    yield
    unbind_lock_parser()


def _canonical_plan(path: Path) -> dict:
    plan = json.loads(path.read_text(encoding="utf-8"))
    plan["plan_sha256"] = i5._sha256_bytes(
        i5._canonical({k: v for k, v in plan.items() if k != "plan_sha256"})
    )
    return plan


# ---------------------------------------------------------------------------
# P1 — exact N12 plan loads in frozen order and SHA matches
# ---------------------------------------------------------------------------


class TestP1PlanIdentity:
    def test_n12_order_and_sha(self) -> None:
        plan = i5.load_plan()
        units = [c["validation_unit_id"] for c in plan["calibration_units"]]
        assert units == FROZEN_ORDER
        assert plan["plan_sha256"] == EXPECTED_PLAN_SHA

    def test_membership_uniqueness(self) -> None:
        plan = i5.load_plan()
        units = [c["validation_unit_id"] for c in plan["calibration_units"]]
        assert len(units) == len(set(units)) == 12

    def test_source_fidelity_units_present(self) -> None:
        plan = i5.load_plan()
        units = {c["validation_unit_id"] for c in plan["calibration_units"]}
        assert set(SF_UNITS) <= units


# ---------------------------------------------------------------------------
# P2 — R4-D strata / required coverage unchanged
# ---------------------------------------------------------------------------


class TestP2CoverageUnchanged:
    def test_strata_unchanged(self) -> None:
        matrix = i5.load_matrix()
        assert matrix["strata"] == EXPECTED_STRATA

    def test_plan_required_categories_all_uncovered_empty(self) -> None:
        plan = i5.load_plan()
        assert plan["uncovered_categories"] == []
        assert plan["n_calibration"] == 12

    def test_matrix_install_routes_are_frozen_labels(self) -> None:
        matrix = i5.load_matrix()
        routes = {u["install_route"] for u in matrix["units"]}
        assert routes == set(i5.INSTALL_ROUTES)


# ---------------------------------------------------------------------------
# P3 — Poetry unit resolves via integrated R4-B + R4-A
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestP3PoetryUnit:
    def test_poetry_unit_closes(self) -> None:
        store = Path(r"D:\wp2_env_store")
        plan = i5.load_plan()
        matrix = i5.load_matrix()
        identities = i5.build_unit_identity(plan, matrix, store)
        identity = identities["vu-e4998719ee01"]
        target = RuntimeTarget(
            "3.12", "cpython", "linux", "x86_64"
        )
        bind_integrated_parser()
        try:
            td = identity["member_tasks"][0]
            closure = i5._parse_lock_once(td, store, "poetry", target)
            assert wheel_compatible("django-4.2.20-py3-none-any.whl", T312) is True
        finally:
            unbind_lock_parser()
        assert closure.is_valid
        assert closure.lock_format == "poetry"


# ---------------------------------------------------------------------------
# P4 — uv unit resolves via integrated R4-B + R4-A
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestP4UvUnit:
    def test_uv_unit_editable_self_and_closure(self) -> None:
        store = Path(r"D:\wp2_env_store")
        plan = i5.load_plan()
        matrix = i5.load_matrix()
        identities = i5.build_unit_identity(plan, matrix, store)
        identity = identities["vu-13c1de1de71e"]
        target = RuntimeTarget("3.12", "cpython", "linux", "x86_64")
        bind_integrated_parser()
        try:
            td = identity["member_tasks"][0]
            closure = i5._parse_lock_once(td, store, "uv", target)
        finally:
            unbind_lock_parser()
        assert closure.is_valid
        assert closure.lock_format == "uv"
        assert closure.editable_self is not None
        assert closure.editable_self.normalized_name == "saleor"
        assert closure.editable_self.source_type == SourceType.EDITABLE_SELF


# ---------------------------------------------------------------------------
# P5/P6/P7 — era-aware compatibility semantics
# ---------------------------------------------------------------------------


class TestP567EraSemantics:
    def test_py38_semantics(self) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible("pkg-1.0-cp38-cp38-linux_x86_64.whl", T38) is True
            assert wheel_compatible("pkg-1.0-cp39-cp39-linux_x86_64.whl", T38) is False
        finally:
            unbind_lock_parser()

    def test_py39_semantics(self) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible("pkg-1.0-cp39-cp39-linux_x86_64.whl", T39) is True
            assert wheel_compatible("pkg-1.0-cp312-cp312-linux_x86_64.whl", T39) is False
        finally:
            unbind_lock_parser()

    def test_py312_semantics(self) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible("pkg-1.0-cp312-cp312-linux_x86_64.whl", T312) is True
            assert wheel_compatible("pkg-1.0-cp38-cp38-linux_x86_64.whl", T312) is False
        finally:
            unbind_lock_parser()


# ---------------------------------------------------------------------------
# P8 — source-fidelity units resolve PyXB / authorizenet through R1
# ---------------------------------------------------------------------------


class TestP8SourceFidelity:
    def test_pyxb_and_authorizenet_overlay(self) -> None:
        overlay = i5.SourceFidelityOverlay()
        pyxb = overlay.resolve("PyXB", "1.2.5")
        auth = overlay.resolve("authorizenet", "1.1.4")
        assert pyxb is not None
        assert auth is not None
        assert pyxb["source_type"] == "DIRECTORY"
        assert auth["source_type"] == "DIRECTORY"
        assert pyxb["output_filename"] == "pyxb-1.2.5-py3-none-any.whl"
        assert auth["output_filename"] == "authorizenet-1.1.4-py3-none-any.whl"

    def test_both_sf_units_in_plan(self) -> None:
        plan = i5.load_plan()
        units = {c["validation_unit_id"] for c in plan["calibration_units"]}
        assert set(SF_UNITS) <= units


# ---------------------------------------------------------------------------
# P9 — editable root/self is not a third-party artifact
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestP9EditableSelf:
    def test_editable_self_never_in_requirements(self) -> None:
        bind_integrated_parser()
        try:
            closure = i5._parse_lock_once(
                "saleor-rc-e0f2933d58b9",
                Path(r"D:\wp2_env_store"),
                "uv",
                T312,
            )
        finally:
            unbind_lock_parser()
        assert closure.editable_self is not None
        assert closure.editable_self.editable_self is True
        names = {r.normalized_name for r in closure.requirements}
        assert closure.editable_self.normalized_name not in names


# ---------------------------------------------------------------------------
# P10 — I3 receipt consumed without Docker re-query
# ---------------------------------------------------------------------------


class TestP10DockerReceipt:
    def test_receipt_14_0_0(self) -> None:
        receipt = i5.validate_i3_receipt()
        assert receipt["present_match_count"] == 14
        assert receipt["missing_count"] == 0
        assert receipt["mismatch_count"] == 0

    def test_driver_never_invokes_docker_cli(self) -> None:
        source = Path(i5.__file__).read_text(encoding="utf-8")
        # The driver consumes the I3 receipt structurally and must never invoke
        # any Docker CLI command.
        assert "docker image inspect" not in source
        assert "docker run" not in source
        assert "docker pull" not in source
        assert "docker build" not in source
        assert "docker create" not in source
        assert re.search(r"subprocess\.run\(\s*\[\s*[\"']docker", source) is None
        if "docker" in source.lower():
            # Docker may appear only as evidence/reporting field labels, never as
            # a command or module import.
            assert "import docker" not in source


# ---------------------------------------------------------------------------
# P11 — member-task commit identities checked without materialization
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_REPO, reason="repo unavailable")
class TestP11CommitReadiness:
    def test_commit_identity_bounded_check(self) -> None:
        repo = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor")
        plan = i5.load_plan()
        store = Path(r"D:\wp2_env_store")
        matrix = i5.load_matrix()
        identities = i5.build_unit_identity(plan, matrix, store)
        checked = 0
        for uid in FROZEN_ORDER:
            for _tid, trec in identities[uid]["task_identity"].items():
                commit = trec["target_commit"]
                assert i5._check_commit(repo, commit) is True
                checked += 1
        assert checked == 18


# ---------------------------------------------------------------------------
# P12 — deterministic canonical results
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not (HAS_STORE and HAS_REPO), reason="store/os env unavailable")
class TestP12Determinism:
    def test_repeated_run_canonical_equal(self) -> None:
        store = Path(r"D:\wp2_env_store")
        repo = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor")
        first = i5.run_smoke(store, repo, write=False, out_path=None)
        second = i5.run_smoke(store, repo, write=False, out_path=None)
        assert first["canonical_sha256"] == second["canonical_sha256"]

    def test_rerun_mismatch_fails_closed(self) -> None:
        store = Path(r"D:\wp2_env_store")
        repo = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor")
        with pytest.raises(i5.SmokeFailClosedError, match="deterministic rerun mismatch"):
            i5.run_smoke(
                store, repo, write=False, out_path=None, previous_canonical="0" * 64
            )


# ---------------------------------------------------------------------------
# F2P — invalid/mutated inputs fail closed
# ---------------------------------------------------------------------------


class TestF1F2F3PlanMutations:
    def test_f1_mutated_membership(self, tmp_path: Path) -> None:
        plan = _canonical_plan(PLAN_PATH)
        plan["calibration_units"] = plan["calibration_units"][1:]
        plan["n_calibration"] = len(plan["calibration_units"])
        plan["plan_sha256"] = i5._sha256_bytes(
            i5._canonical({k: v for k, v in plan.items() if k != "plan_sha256"})
        )
        path = _write(tmp_path, "plan.json", json.dumps(plan))
        with pytest.raises(i5.SmokeFailClosedError, match="N mutated|order|membership|SHA"):
            i5.load_plan(path)

    def test_f2_mutated_order(self, tmp_path: Path) -> None:
        plan = _canonical_plan(PLAN_PATH)
        cu = plan["calibration_units"]
        cu[0], cu[1] = cu[1], cu[0]
        plan["calibration_units"] = cu
        plan["plan_sha256"] = i5._sha256_bytes(
            i5._canonical({k: v for k, v in plan.items() if k != "plan_sha256"})
        )
        path = _write(tmp_path, "plan.json", json.dumps(plan))
        with pytest.raises(i5.SmokeFailClosedError, match="order|membership|SHA"):
            i5.load_plan(path)

    def test_f3_mutated_sha(self, tmp_path: Path) -> None:
        plan = _canonical_plan(PLAN_PATH)
        plan["plan_sha256"] = EXPECTED_PLAN_SHA  # leave self-consistent
        plan["calibration_units"][0]["python_version"] = "3.99"
        plan["plan_sha256"] = i5._sha256_bytes(
            i5._canonical({k: v for k, v in plan.items() if k != "plan_sha256"})
        )
        path = _write(tmp_path, "plan.json", json.dumps(plan))
        with pytest.raises(i5.SmokeFailClosedError):
            i5.load_plan(path)


class TestF4F5UnitTargetMutations:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_f4_unknown_python_era(self) -> None:
        store = Path(r"D:\wp2_env_store")
        plan = i5.load_plan()
        matrix = i5.load_matrix()
        identities = i5.build_unit_identity(plan, matrix, store)
        identity = identities["vu-13c1de1de71e"]
        mut = copy.deepcopy(identity)
        mut["matrix_record"]["python_version"] = "3.7"
        mut["matrix_record"]["wheelhouse_era"] = "py37"
        wheel_store = i5.LocalWheelStore(store, "py312")
        repo = Path(r"D:\wp2_env_store")
        with pytest.raises(i5.SmokeFailClosedError, match="python era|era"):
            i5.resolve_unit(
                "vu-13c1de1de71e", mut, store, repo, wheel_store, i5.SourceFidelityOverlay()
            )

    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_f5_unknown_lock_type(self) -> None:
        store = Path(r"D:\wp2_env_store")
        plan = i5.load_plan()
        matrix = i5.load_matrix()
        identities = i5.build_unit_identity(plan, matrix, store)
        identity = identities["vu-13c1de1de71e"]
        mut = copy.deepcopy(identity)
        mut["matrix_record"]["lock_type"] = "npm"
        wheel_store = i5.LocalWheelStore(store, "py312")
        repo = Path(r"D:\wp2_env_store")
        with pytest.raises(i5.SmokeFailClosedError, match="lock_type"):
            i5.resolve_unit(
                "vu-13c1de1de71e", mut, store, repo, wheel_store, i5.SourceFidelityOverlay()
            )


class TestF6SourceSemantics:
    def test_unsupported_source_semantics_fails_closed(self) -> None:
        sf = i5.SourceFidelityOverlay()
        ws = i5.LocalWheelStore if hasattr(i5, "LocalWheelStore") else None
        assert ws is not None
        # Non-SF unit requesting DIRECTORY source semantics is unsupported.
        # Exercise the classifier with a synthetic DIRECTORY requirement on a
        # non-source-fidelity unit.

        req = NormalizedRequirement(
            normalized_name="some-dir-pkg",
            version="1.0.0",
            source_type=SourceType.DIRECTORY,
            source_reference="some/path",
            marker=None,
            marker_applies=True,
            editable_self=False,
        )
        rec = {}
        # Use a temp wheel store so no real store dependency.
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            # build minimal wheelhouse manifest referencing no artifacts
            manif = tmp / "manifests"
            manif.mkdir()
            (manif / "WHEELHOUSE_HASHES_py312.json").write_text(
                json.dumps({"artifacts": []}), encoding="utf-8"
            )
            ws = i5.LocalWheelStore(tmp, "py312")
            cls = i5._classify_requirement(req, rec, "3.12", ws, sf, "vu-13c1de1de71e")
            assert cls == i5.UNSUPPORTED_SOURCE_SEMANTICS


class TestF7F8F9IdentityMutations:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_f7_missing_unit_metadata(self) -> None:
        plan = i5.load_plan()
        matrix = i5.load_matrix()
        matrix = copy.deepcopy(matrix)
        matrix["units"] = [u for u in matrix["units"] if u["validation_unit_id"] != "vu-13c1de1de71e"]
        with pytest.raises(i5.SmokeFailClosedError, match="missing"):
            i5.build_unit_identity(plan, matrix, Path(r"D:\wp2_env_store"))

    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_f8_missing_member_task_metadata(self, tmp_path: Path) -> None:
        store = tmp_path / "store"
        manif = store / "manifests"
        manif.mkdir(parents=True)
        src_unit = Path(r"D:\wp2_env_store\manifests\VALIDATION_UNIT_MATRIX.csv").read_text(encoding="utf-8")
        src_task = Path(r"D:\wp2_env_store\manifests\TASK_ENV_MATRIX.csv").read_text(encoding="utf-8")
        (manif / "VALIDATION_UNIT_MATRIX.csv").write_text(src_unit, encoding="utf-8")
        task_rows = [ln for ln in src_task.splitlines() if not ln.startswith("saleor-rc-e0f2933d58b9,")]
        (manif / "TASK_ENV_MATRIX.csv").write_text("\n".join(task_rows) + "\n", encoding="utf-8")
        plan = i5.load_plan()
        matrix = i5.load_matrix()
        with pytest.raises(i5.SmokeFailClosedError, match="missing from TASK_ENV"):
            i5.build_unit_identity(plan, matrix, store)

    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_f9_missing_repository_identity(self, tmp_path: Path) -> None:
        import csv

        store = tmp_path / "store"
        manif = store / "manifests"
        manif.mkdir(parents=True)
        src_unit = Path(r"D:\wp2_env_store\manifests\VALIDATION_UNIT_MATRIX.csv").read_text(encoding="utf-8")
        (manif / "VALIDATION_UNIT_MATRIX.csv").write_text(src_unit, encoding="utf-8")
        src_task = Path(r"D:\wp2_env_store\manifests\TASK_ENV_MATRIX.csv").read_text(encoding="utf-8")
        with open(manif / "TASK_ENV_MATRIX.csv", "w", encoding="utf-8", newline="") as fh:
            reader = list(csv.DictReader(src_task.splitlines()))
            writer = csv.DictWriter(fh, fieldnames=list(reader[0].keys()))
            writer.writeheader()
            for row in reader:
                if row["task_id"] == "saleor-rc-e0f2933d58b9":
                    row["target_commit"] = ""
                writer.writerow(row)
        plan = i5.load_plan()
        matrix = i5.load_matrix()
        with pytest.raises(i5.SmokeFailClosedError, match="commit identity|repository"):
            i5.build_unit_identity(plan, matrix, store)


class TestF10CommitObject:
    def test_missing_commit_object_fails_closed(self) -> None:
        # Bounded git-object check MUST fail for a bogus commit.
        repo = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor")
        if not repo.exists():
            pytest.skip("repo unavailable")
        assert i5._check_commit(repo, "0" * 40) is False


class TestF11MalformedReceipt:
    def test_malformed_i3_receipt(self, tmp_path: Path) -> None:
        receipts = copy.deepcopy(json.loads(I3_RECEIPT_PATH.read_text(encoding="utf-8")))
        receipts["present_match_count"] = 13
        path = _write(tmp_path, "i3.json", json.dumps(receipts))
        with pytest.raises(i5.SmokeFailClosedError, match="present|receipt"):
            i5.validate_i3_receipt(path)

    def test_missing_i3_receipt(self, tmp_path: Path) -> None:
        with pytest.raises(i5.SmokeFailClosedError, match="missing required artifact"):
            i5.validate_i3_receipt(tmp_path / "nope.json")


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestF12MissingProviderArtifact:
    def test_missing_wheelhouse_manifest(self, tmp_path: Path) -> None:
        store = tmp_path / "store"
        (store / "manifests").mkdir(parents=True)
        with pytest.raises(i5.SmokeFailClosedError, match="wheelhouse manifest"):
            i5.LocalWheelStore(store, "py312")


class TestF13F14F15ExactIdentity:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_f13_near_match_name(self) -> None:
        store = Path(r"D:\wp2_env_store")
        ws = i5.LocalWheelStore(store, "py312")
        # 'django' exists in the py312 wheelhouse; a near-match must not resolve.
        assert any(w["filename"].startswith("Django-") for w in ws.wheels_for("django"))

        req = NormalizedRequirement(
            normalized_name="django-not-a-real-pkg",
            version="1.0.0",
            source_type=SourceType.REGISTRY,
            source_reference=None,
            marker=None,
            marker_applies=True,
            editable_self=False,
        )
        rec = {}
        cls = i5._classify_requirement(req, rec, "3.12", ws, i5.SourceFidelityOverlay(), "vu-13c1de1de71e")
        assert cls == i5.MISSING_LOCAL_ARTIFACT_CANDIDATE

    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_f14_wrong_version(self) -> None:
        store = Path(r"D:\wp2_env_store")
        ws = i5.LocalWheelStore(store, "py312")

        req = NormalizedRequirement(
            normalized_name="django",
            version="9.9.9",
            source_type=SourceType.REGISTRY,
            source_reference=None,
            marker=None,
            marker_applies=True,
            editable_self=False,
        )
        rec = {}
        cls = i5._classify_requirement(req, rec, "3.12", ws, i5.SourceFidelityOverlay(), "vu-13c1de1de71e")
        assert cls == i5.MISSING_LOCAL_ARTIFACT_CANDIDATE

    def test_f15_wrong_era_wheel(self) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible("pkg-1.0-cp38-cp38-linux_x86_64.whl", T312) is False
        finally:
            unbind_lock_parser()


class TestF16NoNetworkFallback:
    def test_driver_has_no_network_fallback(self) -> None:
        source = Path(i5.__file__).read_text(encoding="utf-8")
        forbidden = (
            "urllib",
            "requests",
            "httpx",
            "aiohttp",
            "socket",
            "http.client",
            "urllib3",
            "pip install",
            "poetry add",
            "uv pip",
            "pythonhosted",
        )
        for token in forbidden:
            assert token not in source, f"network/online token present in driver: {token}"

    def test_driver_never_invokes_docker(self) -> None:
        source = Path(i5.__file__).read_text(encoding="utf-8")
        # Docker may appear as evidence/reporting field labels; the driver must
        # never invoke the Docker CLI or import the docker module.
        assert "import docker" not in source
        assert "docker image inspect" not in source
        assert "docker run" not in source
        assert "docker pull" not in source
        assert "docker build" not in source
        assert "docker create" not in source
        assert re.search(r"subprocess\.run\(\s*\[\s*[\"']docker", source) is None

    def test_driver_misses_no_silent_skip(self) -> None:
        source = Path(i5.__file__).read_text(encoding="utf-8")
        # every requirement is classified or explicitly excluded; no pass-through
        assert "for req in closure.requirements:" in source
        assert "rec[\"classification\"]" in source
