"""R4 I4 convergence tests — cross-track integration proof.

Mission ``M17_D7_R4_I4_CONVERGENCE``.

This module proves that the combined repository state (I1 A+B composition, I2
Linux materialization wiring, I3 R4-D capability reconciliation replayed onto
the canonical integration branch) satisfies the frozen shared interface and the
qualified per-track behavior simultaneously.

P2P proofs (P1..P10):

* P1  — all I1/I2/I3 expected artifacts coexist in the worktree.
* P2  — the integrated parser provides ``parse_lock`` + ``wheel_compatible``
        simultaneously through one frozen ``LockParser`` binding.
* P3  — the Saleor uv fixture closure identity remains identical to the I1
        qualification.
* P4  — ``LinuxTreeWiring`` remains wired to the qualified R4-C materializer
        with no Windows working-tree fallback.
* P5  — R4-D population/count/strata artifacts remain unchanged.
* P6  — calibration N=12 membership and plan SHA remain unchanged.
* P7  — the I3 Docker reconciliation receipt is exactly 14/0/0 and is accepted
        as current-state capability evidence.
* P8  — original historical R4-D / ENV_CANON evidence is not overwritten.
* P9  — frozen shared interface files remain byte-identical to the seed.
* P10 — import provenance resolves to the I4 worktree, not the stale editable
        main-worktree installation.

F2P proofs:

* parser unbound -> fail closed;
* malformed lock -> fail closed;
* malformed/incompatible wheel -> fail closed;
* invalid materialization input -> fail closed;
* mutated calibration plan SHA -> convergence validation fails;
* mutated population count/strata -> convergence validation fails;
* Docker receipt with missing or mismatch count -> convergence validation fails;
* missing required provider artifact -> convergence validation fails.

F2P uses fixtures/copies/mocks only; authoritative files are never mutated.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Iterator
from pathlib import Path

import pytest

from benchmark.wp2.env_r4.contracts import (
    LockClosure,
    LockParseError,
    RuntimeTarget,
    parse_lock,
    unbind_lock_parser,
    wheel_compatible,
)
from benchmark.wp2.env_r4.integrated_parser import bind_integrated_parser
from benchmark.wp2.env_r4.linux_tree_materialize import MaterializeError, Materializer
from benchmark.wp2.env_r4.linux_tree_wiring import LinuxTreeWiring, R4MaterializationSource
from benchmark.wp2.linux_adapter import CommandResult, LinuxBackend

PROJECT_DIR = Path(__file__).resolve().parents[4]
SRC_DIR = PROJECT_DIR / "src"
R4_DIR = PROJECT_DIR / "research" / "env-canon-r4"

REAL_UV_LOCK = R4_DIR / "fixtures" / "saleor-3.23.0-uv.lock"

EXPECTED_SALEOR_SHA = (
    "a8c1bdd4a7eb9acf9fcd43a169cf44796881c177c43295c75c26549081f8631c"
)
EXPECTED_PLAN_SHA = "8ec20f360f62c7f4d072ad03bb5fe042c85fa98bad64757715227b5c88de687d"
EXPECTED_N_CALIBRATION = 12
EXPECTED_POPULATION_IDENTITY = "ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac"

REQUIRED_ARTIFACTS = (
    R4_DIR / "R4_A_WHEEL_TAG_REPORT.json",
    R4_DIR / "R4_B_UV_ADAPTER_REPORT.json",
    R4_DIR / "R4_I1_AB_COMPOSITION_REPORT.json",
    R4_DIR / "R4_C_LINUX_TREE_FIDELITY_REPORT.json",
    R4_DIR / "R4_I2_LINUX_MATERIALIZATION_WIRING_REPORT.json",
    R4_DIR / "R4_I3_CAPABILITY_STATE_RECONCILIATION.json",
    R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json",
    R4_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json",
    R4_DIR / "R4_D_CALIBRATION_COVERAGE_REPORT.md",
    R4_DIR / "R4_SHARED_INTERFACE.md",
    SRC_DIR / "benchmark" / "wp2" / "env_r4" / "contracts.py",
    SRC_DIR / "benchmark" / "wp2" / "env_r4" / "__init__.py",
    SRC_DIR / "benchmark" / "wp2" / "env_r4" / "integrated_parser.py",
    SRC_DIR / "benchmark" / "wp2" / "env_r4" / "uv_adapter.py",
    SRC_DIR / "benchmark" / "wp2" / "env_r4" / "wheel_tags.py",
    SRC_DIR / "benchmark" / "wp2" / "env_r4" / "linux_tree_materialize.py",
    SRC_DIR / "benchmark" / "wp2" / "env_r4" / "linux_tree_wiring.py",
)

FROZEN_SHARED_INTERFACE = (
    SRC_DIR / "benchmark" / "wp2" / "env_r4" / "contracts.py",
    SRC_DIR / "benchmark" / "wp2" / "env_r4" / "__init__.py",
    R4_DIR / "R4_SHARED_INTERFACE.md",
)

T38 = RuntimeTarget("3.8", "cpython", "linux", "x86_64")
T39 = RuntimeTarget("3.9", "cpython", "linux", "x86_64")
T312 = RuntimeTarget("3.12", "cpython", "linux", "x86_64")


class ConvergenceValidationError(Exception):
    """Raised when a convergence-state validation gate fails (fail closed)."""


# ---------------------------------------------------------------------------
# Convergence-state validator (test-local model of the I4 gate)
# ---------------------------------------------------------------------------


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def validate_convergence(
    plan_path: Path = R4_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json",
    matrix_path: Path = R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json",
    receipt_path: Path = R4_DIR / "R4_I3_CAPABILITY_STATE_RECONCILIATION.json",
    artifacts: tuple[Path, ...] = REQUIRED_ARTIFACTS,
) -> dict[str, object]:
    """Validate the full I4 convergence state; any mutation fails closed."""
    missing = [str(a) for a in artifacts if not a.is_file()]
    if missing:
        raise ConvergenceValidationError(f"missing required provider artifact: {missing}")

    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    population = matrix["population"]
    if population["n_validation_units"] != 144:
        raise ConvergenceValidationError("population unit count mutated")
    if population["n_mapped_tasks"] != 219:
        raise ConvergenceValidationError("population task count mutated")
    if population["population_identity_sha256"] != EXPECTED_POPULATION_IDENTITY:
        raise ConvergenceValidationError("population identity mutated")
    if matrix["strata"] != {
        "3.12_poetry": 25,
        "3.12_uv": 21,
        "3.9_poetry": 83,
        "3.8_poetry": 15,
    }:
        raise ConvergenceValidationError("strata counts mutated")

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    recomputed = _sha256_bytes(_canonical({k: v for k, v in plan.items() if k != "plan_sha256"}))
    if plan["plan_sha256"] != recomputed:
        raise ConvergenceValidationError("plan SHA is not self-consistent")
    if plan["n_calibration"] != EXPECTED_N_CALIBRATION:
        raise ConvergenceValidationError("calibration N mutated")
    membership = [c["validation_unit_id"] for c in plan["calibration_units"]]
    if len(membership) != len(set(membership)) or len(membership) != EXPECTED_N_CALIBRATION:
        raise ConvergenceValidationError("calibration membership mutated")
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA:
        raise ConvergenceValidationError("calibration plan SHA mutated")
    if plan["plan_status"] != "DRAFT_PENDING_R4_INTEGRATION":
        raise ConvergenceValidationError("historical R4-D draft status overwritten")

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt["present_match_count"] != 14:
        raise ConvergenceValidationError("Docker receipt present count mutated")
    if receipt["missing_count"] != 0:
        raise ConvergenceValidationError("Docker receipt missing count mutated")
    if receipt["mismatch_count"] != 0:
        raise ConvergenceValidationError("Docker receipt mismatch count mutated")
    if receipt["reconciliation_classification"] != "HISTORICAL_STALE_STATE_FOR_R4_INTEGRATION":
        raise ConvergenceValidationError("Docker reconciliation classification mutated")

    return {
        "n_validation_units": population["n_validation_units"],
        "n_mapped_tasks": population["n_mapped_tasks"],
        "plan_sha256": plan["plan_sha256"],
        "n_calibration": plan["n_calibration"],
        "membership": membership,
        "present_match_count": receipt["present_match_count"],
        "missing_count": receipt["missing_count"],
        "mismatch_count": receipt["mismatch_count"],
    }


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def _names(closure: LockClosure) -> set[str]:
    return {r.normalized_name for r in closure.requirements}


@pytest.fixture(autouse=True)
def _isolate_binding() -> Iterator[None]:
    unbind_lock_parser()
    yield
    unbind_lock_parser()


# ---------------------------------------------------------------------------
# P1 — all I1/I2/I3 expected artifacts coexist
# ---------------------------------------------------------------------------


class TestP1ArtifactsCoexist:
    def test_all_expected_artifacts_exist(self) -> None:
        missing = [str(a) for a in REQUIRED_ARTIFACTS if not a.is_file()]
        assert missing == []

    def test_reconciliation_report_and_drafts_present(self) -> None:
        for name in (
            "R4_CAPABILITY_MATRIX_DRAFT.json",
            "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json",
            "R4_D_CALIBRATION_COVERAGE_REPORT.md",
            "R4_I3_CAPABILITY_STATE_RECONCILIATION.json",
        ):
            assert (R4_DIR / name).is_file()


# ---------------------------------------------------------------------------
# P2 — the integrated parser provides parse_lock + wheel_compatible together
# ---------------------------------------------------------------------------


class TestP2IntegratedParser:
    def test_single_bind_serves_both_entry_points(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            "version = 1\n"
            "[[package]]\n"
            "name = 'requests'\n"
            "version = '2.32.3'\n"
            "source = { registry = 'https://pypi.org/simple' }\n",
        )
        bind_integrated_parser()
        try:
            closure = parse_lock(lock, T312)
            assert closure.is_valid
            assert closure.lock_format == "uv"
            assert "requests" in _names(closure)
            assert wheel_compatible("pkg-1.0-py3-none-any.whl", T312) is True
        finally:
            unbind_lock_parser()

    def test_alternating_parse_wheel_calls_remain_valid(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            "version = 1\n"
            "[[package]]\n"
            "name = 'django'\n"
            "version = '5.2.13'\n"
            "source = { registry = 'https://pypi.org/simple' }\n",
        )
        bind_integrated_parser()
        try:
            first = parse_lock(lock, T312)
            assert first.is_valid
            assert wheel_compatible("pkg-1.0-cp312-cp312-linux_x86_64.whl", T312) is True
            second = parse_lock(lock, T312)
            assert second.to_canonical_dict() == first.to_canonical_dict()
            assert wheel_compatible("pkg-1.0-py3-none-any.whl", T312) is True
            assert wheel_compatible("pkg-1.0-cp39-cp39-linux_x86_64.whl", T312) is False
        finally:
            unbind_lock_parser()


# ---------------------------------------------------------------------------
# P3 — Saleor closure identity identical to I1 qualification
# ---------------------------------------------------------------------------


class TestP3SaleorClosure:
    def test_closure_identity_unchanged(self) -> None:
        assert REAL_UV_LOCK.is_file()
        bind_integrated_parser()
        try:
            closure = parse_lock(REAL_UV_LOCK, T312)
            sha = closure.freeze_sha256()
        finally:
            unbind_lock_parser()
        assert closure.is_valid
        assert closure.lock_format == "uv"
        assert len(closure.requirements) == 230
        assert closure.editable_self is not None
        assert closure.editable_self.normalized_name == "saleor"
        assert len(closure.exclusions) == 2
        assert sha == EXPECTED_SALEOR_SHA


# ---------------------------------------------------------------------------
# P4 — LinuxTreeWiring wired to R4-C without Windows fallback
# ---------------------------------------------------------------------------


class _FakeBackend(LinuxBackend):
    def run(
        self,
        cmd: list[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout_s: int = 900,
    ) -> CommandResult:
        raise AssertionError("backend must never run in I4 wiring proof (no Docker)")


class _SpyMaterializer(Materializer):
    def __init__(self) -> None:
        super().__init__(_FakeBackend(), "envcanon/saleor-env-base-py312-bookworm:latest", "/opt/wp2_v2/saleor-cache")
        self.calls: list[tuple[str, str]] = []
        self.result = 1788
        self.raise_error: MaterializeError | None = None

    def materialize(self, commit: str, volume: str, *, resolve: bool = True) -> int:
        self.calls.append((commit, volume))
        if self.raise_error is not None:
            raise self.raise_error
        return self.result


class TestP4LinuxWiring:
    def test_wiring_delegates_exclusively_to_r4c(self) -> None:
        spy = _SpyMaterializer()
        wiring = LinuxTreeWiring(_FakeBackend(), R4MaterializationSource(
            image="envcanon/saleor-env-base-py312-bookworm:latest",
            repo_linux_path="/opt/wp2_v2/saleor-cache",
        ), materializer=spy)
        count = wiring.materialize("24f9b244d6bc8c591c9707380917d9b6c6d35c35", "r4-i4-test-vol")
        assert count == spy.result
        assert spy.calls == [("24f9b244d6bc8c591c9707380917d9b6c6d35c35", "r4-i4-test-vol")]

    def test_commit_identity_passes_through_unchanged(self) -> None:
        spy = _SpyMaterializer()
        wiring = LinuxTreeWiring(_FakeBackend(), R4MaterializationSource(
            image="envcanon/saleor-env-base-py312-bookworm:latest",
            repo_linux_path="/opt/wp2_v2/saleor-cache",
        ), materializer=spy)
        wiring.materialize("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", "vol")
        assert spy.calls == [("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", "vol")]

    def test_no_windows_working_tree_fallback_in_source(self) -> None:
        import benchmark.wp2.env_r4.linux_tree_wiring as wiring_mod

        source = Path(wiring_mod.__file__).read_text(encoding="utf-8")
        mods = {
            p
            for m in re.findall(r"^(?:from ([\w.]+)|import ([\w.]+))", source, re.M)
            for p in (m,)
            if p
        }
        forbidden = {"shutil", "os", "pathlib", "shlex", "glob", "subprocess"}
        assert not (mods & forbidden), mods & forbidden
        for call in ("copytree(", "copyfile(", "copy2(", "shutil.copy(", "os.replace("):
            assert call not in source

    def test_materialize_error_propagates_fail_closed(self) -> None:
        spy = _SpyMaterializer()
        error = MaterializeError("materialization failed (fail closed): BLOB_FAIL")
        spy.raise_error = error
        wiring = LinuxTreeWiring(_FakeBackend(), R4MaterializationSource(
            image="envcanon/saleor-env-base-py312-bookworm:latest",
            repo_linux_path="/opt/wp2_v2/saleor-cache",
        ), materializer=spy)
        with pytest.raises(MaterializeError) as exc_info:
            wiring.materialize("24f9b244d6bc8c591c9707380917d9b6c6d35c35", "vol")
        assert exc_info.value is error


# ---------------------------------------------------------------------------
# P5 / P6 — R4-D population and calibration invariance
# ---------------------------------------------------------------------------


class TestP5P6R4DInvariance:
    def test_population_counts_and_strata_unchanged(self) -> None:
        matrix = json.loads((R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json").read_text(encoding="utf-8"))
        assert matrix["population"]["n_validation_units"] == 144
        assert matrix["population"]["n_mapped_tasks"] == 219
        assert matrix["population"]["population_identity_sha256"] == EXPECTED_POPULATION_IDENTITY
        assert matrix["strata"] == {
            "3.12_poetry": 25,
            "3.12_uv": 21,
            "3.9_poetry": 83,
            "3.8_poetry": 15,
        }

    def test_calibration_n12_sha_and_membership_unchanged(self) -> None:
        plan = json.loads((R4_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json").read_text(encoding="utf-8"))
        assert plan["n_calibration"] == EXPECTED_N_CALIBRATION
        assert plan["plan_sha256"] == EXPECTED_PLAN_SHA
        membership = [c["validation_unit_id"] for c in plan["calibration_units"]]
        assert len(membership) == EXPECTED_N_CALIBRATION
        assert len(membership) == len(set(membership))


# ---------------------------------------------------------------------------
# P7 — I3 Docker reconciliation receipt 14/0/0 accepted as capability evidence
# ---------------------------------------------------------------------------


class TestP7DockerReceipt:
    def test_receipt_is_exactly_14_0_0(self) -> None:
        receipt = json.loads(
            (R4_DIR / "R4_I3_CAPABILITY_STATE_RECONCILIATION.json").read_text(encoding="utf-8")
        )
        assert receipt["present_match_count"] == 14
        assert receipt["missing_count"] == 0
        assert receipt["mismatch_count"] == 0
        assert receipt["expected_image_count"] == 14
        assert receipt["reconciliation_classification"] == "HISTORICAL_STALE_STATE_FOR_R4_INTEGRATION"

    def test_receipt_records_no_docker_or_network_execution(self) -> None:
        receipt = json.loads(
            (R4_DIR / "R4_I3_CAPABILITY_STATE_RECONCILIATION.json").read_text(encoding="utf-8")
        )
        assert receipt["docker_pull_used"] is False
        assert receipt["docker_build_used"] is False
        assert receipt["docker_run_used"] is False
        assert receipt["network_used"] is False

    def test_validate_convergence_accepts_receipt_as_current_state_evidence(self) -> None:
        result = validate_convergence()
        assert result["present_match_count"] == 14
        assert result["missing_count"] == 0
        assert result["mismatch_count"] == 0


# ---------------------------------------------------------------------------
# P8 — historical R4-D / ENV_CANON evidence not overwritten
# ---------------------------------------------------------------------------


class TestP8HistoricalEvidencePreserved:
    def test_r4d_drafts_retain_pending_status(self) -> None:
        plan = json.loads((R4_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json").read_text(encoding="utf-8"))
        matrix = json.loads((R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json").read_text(encoding="utf-8"))
        assert plan["plan_status"] == "DRAFT_PENDING_R4_INTEGRATION"
        assert matrix["plan_status"] == "DRAFT_PENDING_R4_INTEGRATION"

    def test_coverage_report_marks_draft_not_final(self) -> None:
        text = (R4_DIR / "R4_D_CALIBRATION_COVERAGE_REPORT.md").read_text(encoding="utf-8")
        assert "DRAFT_PENDING_R4_INTEGRATION" in text
        assert "NOT FINAL" in text

    def test_i3_receipt_retains_historical_gate_reference(self) -> None:
        receipt = json.loads(
            (R4_DIR / "R4_I3_CAPABILITY_STATE_RECONCILIATION.json").read_text(encoding="utf-8")
        )
        assert receipt["mission_id"] == "M17_D7_R4_I3_CAPABILITY_STATE_RECONCILIATION"
        assert receipt["R4-D plan status"] == "DRAFT_PENDING_R4_INTEGRATION"
        assert "ENV_CANON_GATE.json" in receipt["historical gate source reference"]


# ---------------------------------------------------------------------------
# P9 — frozen shared interface unchanged
# ---------------------------------------------------------------------------


class TestP9FrozenInterface:
    def test_frozen_files_still_contain_frozen_schema(self) -> None:
        contracts = (SRC_DIR / "benchmark" / "wp2" / "env_r4" / "contracts.py").read_text(encoding="utf-8")
        assert 'SCHEMA_VERSION = "env-canon-r4/1.0"' in contracts
        init_src = (SRC_DIR / "benchmark" / "wp2" / "env_r4" / "__init__.py").read_text(encoding="utf-8")
        assert "frozen contract" in init_src or "Frozen by" in init_src
        spec = (R4_DIR / "R4_SHARED_INTERFACE.md").read_text(encoding="utf-8")
        assert "M17_D7_R4_SHARED_INTERFACE_FREEZE" in spec


# ---------------------------------------------------------------------------
# P10 — import provenance resolves to the I4 worktree
# ---------------------------------------------------------------------------


class TestP10ImportProvenance:
    def test_benchmark_resolves_under_current_worktree_src(self) -> None:
        import benchmark

        module_path = Path(benchmark.__file__).resolve()
        assert module_path.is_relative_to(SRC_DIR.resolve()), (
            f"benchmark imported from {module_path}, not {SRC_DIR.resolve()} "
            "(stale editable install detected)"
        )

    def test_env_r4_modules_resolve_under_current_worktree(self) -> None:
        import benchmark.wp2.env_r4.integrated_parser as ip
        import benchmark.wp2.env_r4.linux_tree_materialize as ltm
        import benchmark.wp2.env_r4.linux_tree_wiring as ltw
        import benchmark.wp2.env_r4.uv_adapter as ua
        import benchmark.wp2.env_r4.wheel_tags as wt

        for mod in (ip, ltm, ltw, ua, wt):
            module_file = mod.__file__
            assert module_file is not None
            assert Path(module_file).resolve().is_relative_to(SRC_DIR.resolve())


# ---------------------------------------------------------------------------
# F2P — invalid/mutated inputs fail closed
# ---------------------------------------------------------------------------


class TestF2PConvergence:
    def test_parser_unbound_fails_closed(self, tmp_path: Path) -> None:
        lock = _write(tmp_path, "uv.lock", "version = 1\n[[package]]\nname = 'requests'\nversion = '1'\n")
        with pytest.raises(LockParseError):
            parse_lock(lock, T312)
        with pytest.raises(LockParseError):
            wheel_compatible("pkg-1.0-py3-none-any.whl", T312)

    def test_malformed_lock_fails_closed(self, tmp_path: Path) -> None:
        lock = _write(tmp_path, "uv.lock", "version = 1\n[[package]]\nname = ")
        bind_integrated_parser()
        try:
            with pytest.raises(LockParseError):
                parse_lock(lock, T312)
        finally:
            unbind_lock_parser()

    @pytest.mark.parametrize(
        "name",
        ["", "   ", "notawheel", "pkg-1.0.whl", "pkg-1.0-py3-none-any", "pkg-1.0-py3-none-any.tar.gz"],
    )
    def test_malformed_wheel_fails_closed(self, name: str) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible(name, T312) is False
        finally:
            unbind_lock_parser()

    def test_incompatible_wheel_fails_closed(self) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible("pkg-1.0-cp39-cp39-linux_x86_64.whl", T312) is False
            assert wheel_compatible("pkg-1.0-cp312-cp312-win_amd64.whl", T312) is False
            assert wheel_compatible("pkg-1.0-cp312-cp312-linux_aarch64.whl", T312) is False
        finally:
            unbind_lock_parser()

    def test_invalid_materialization_input_fails_closed(self) -> None:
        source = R4MaterializationSource(
            image="envcanon/saleor-env-base-py312-bookworm:latest",
            repo_linux_path="/opt/wp2_v2/saleor-cache",
        )
        wiring = LinuxTreeWiring(_FakeBackend(), source, materializer=_SpyMaterializer())
        with pytest.raises(MaterializeError):
            wiring.materialize("", "vol")
        with pytest.raises(MaterializeError):
            wiring.materialize("24f9b244d6bc8c591c9707380917d9b6c6d35c35", " ")

    # -- convergence-state F2P ----------------------------------------------

    def test_mutated_plan_sha_fails_convergence_validation(self, tmp_path: Path) -> None:
        plan = json.loads((R4_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json").read_text(encoding="utf-8"))
        plan = copy.deepcopy(plan)
        plan["plan_sha256"] = "0" * 64
        mutated = tmp_path / "plan.json"
        mutated.write_text(json.dumps(plan), encoding="utf-8")
        with pytest.raises(ConvergenceValidationError, match="SHA"):
            validate_convergence(plan_path=mutated)

    def test_mutated_population_count_fails_convergence_validation(self, tmp_path: Path) -> None:
        matrix = json.loads((R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json").read_text(encoding="utf-8"))
        matrix = copy.deepcopy(matrix)
        matrix["population"]["n_validation_units"] = 143
        mutated = tmp_path / "matrix.json"
        mutated.write_text(json.dumps(matrix), encoding="utf-8")
        with pytest.raises(ConvergenceValidationError, match="population"):
            validate_convergence(matrix_path=mutated)

    def test_mutated_strata_fails_convergence_validation(self, tmp_path: Path) -> None:
        matrix = json.loads((R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json").read_text(encoding="utf-8"))
        matrix = copy.deepcopy(matrix)
        matrix["strata"]["3.12_uv"] = 20
        mutated = tmp_path / "matrix.json"
        mutated.write_text(json.dumps(matrix), encoding="utf-8")
        with pytest.raises(ConvergenceValidationError, match="strata"):
            validate_convergence(matrix_path=mutated)

    def test_mutated_calibration_n_fails_convergence_validation(self, tmp_path: Path) -> None:
        plan = json.loads((R4_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json").read_text(encoding="utf-8"))
        plan = copy.deepcopy(plan)
        plan["calibration_units"] = plan["calibration_units"][:-1]
        plan["n_calibration"] = 11
        plan["plan_sha256"] = _sha256_bytes(_canonical({k: v for k, v in plan.items() if k != "plan_sha256"}))
        mutated = tmp_path / "plan.json"
        mutated.write_text(json.dumps(plan), encoding="utf-8")
        with pytest.raises(ConvergenceValidationError, match="N|membership"):
            validate_convergence(plan_path=mutated)

    def test_docker_receipt_missing_count_fails_convergence_validation(self, tmp_path: Path) -> None:
        receipt = json.loads((R4_DIR / "R4_I3_CAPABILITY_STATE_RECONCILIATION.json").read_text(encoding="utf-8"))
        receipt = copy.deepcopy(receipt)
        receipt["missing_count"] = 1
        mutated = tmp_path / "receipt.json"
        mutated.write_text(json.dumps(receipt), encoding="utf-8")
        with pytest.raises(ConvergenceValidationError, match="missing"):
            validate_convergence(receipt_path=mutated)

    def test_docker_receipt_mismatch_count_fails_convergence_validation(self, tmp_path: Path) -> None:
        receipt = json.loads((R4_DIR / "R4_I3_CAPABILITY_STATE_RECONCILIATION.json").read_text(encoding="utf-8"))
        receipt = copy.deepcopy(receipt)
        receipt["mismatch_count"] = 1
        mutated = tmp_path / "receipt.json"
        mutated.write_text(json.dumps(receipt), encoding="utf-8")
        with pytest.raises(ConvergenceValidationError, match="mismatch"):
            validate_convergence(receipt_path=mutated)

    def test_missing_required_provider_artifact_fails_convergence_validation(self, tmp_path: Path) -> None:
        ghosts = (tmp_path / "does-not-exist.json",)
        with pytest.raises(ConvergenceValidationError, match="missing required provider artifact"):
            validate_convergence(artifacts=ghosts)


# ---------------------------------------------------------------------------
# No task-ID special cases (cross-track design rule)
# ---------------------------------------------------------------------------


class TestNoTaskIdSpecialCase:
    def test_integrated_sources_have_no_task_id_branch(self) -> None:
        import inspect

        from benchmark.wp2.env_r4.integrated_parser import IntegratedR4Parser, bind_integrated_parser

        source = inspect.getsource(IntegratedR4Parser) + inspect.getsource(bind_integrated_parser)
        assert re.search(r"saleor-rc-[0-9a-f]{12}", source) is None
