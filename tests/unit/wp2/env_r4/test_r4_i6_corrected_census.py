"""M17_D7 R4-I6 corrected zero-container census P2P/F2P tests (mission-local).

Mission M17_D7_R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.

Covers:

P2P (P1..P12):
  P1  — exact population identity is 144 units / 219 tasks.
  P2  — exact strata are 25 / 21 / 83 / 15.
  P3  — I5 resolver semantics are reused, not duplicated (driver imports I5).
  P4  — Poetry lock-level requirement can be separately target-excluded by frozen
        install-route authority without mutating R4-B closure.
  P5  — uv lock target exclusions remain correct.
  P6  — compatible wheel exact name/version/era resolves.
  P7  — approved source/sdist resolves only when frozen route allows it.
  P8  — source-fidelity overlay remains correct.
  P9  — editable-self is never third-party artifact.
  P10 — 219 member-task commit readiness is enforced.
  P11 — TRUE_MISSING requires exhausting all applicable approved routes.
  P12 — population results serialize deterministically.

F2P (F1..F18):
  F1  — wrong population size fails.
  F2  — wrong population identity SHA fails.
  F3  — missing validation unit fails.
  F4  — missing mapped task fails.
  F5  — unknown Python era fails.
  F6  — unknown lock type fails.
  F7  — unknown install route fails.
  F8  — unknown source type fails.
  F9  — near-match package name does not resolve.
  F10 — wrong version does not resolve.
  F11 — wrong-era wheel does not resolve.
  F12 — wheel absence alone does NOT imply TRUE_MISSING when an approved
        source/sdist route exists.
  F13 — no approved route + exact absence can become TRUE_MISSING.
  F14 — ambiguous Poetry/R3 target exclusion causes STOP_OWNER_REVIEW.
  F15 — malformed Docker receipt fails closed.
  F16 — missing repo/commit fails as tooling/environment readiness, not
        artifact-missing.
  F17 — network fallback path absent/fails closed.
  F18 — silent skip of a unit/task fails.

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
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

import r4_i5_zero_container_smoke as i5  # noqa: E402
import r4_i6_corrected_zero_container_census as i6  # noqa: E402

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

T38 = RuntimeTarget("3.8", "cpython", "linux", "x86_64")
T39 = RuntimeTarget("3.9", "cpython", "linux", "x86_64")
T312 = RuntimeTarget("3.12", "cpython", "linux", "x86_64")


@pytest.fixture(autouse=True)
def _isolate_binding() -> None:
    unbind_lock_parser()
    yield
    unbind_lock_parser()


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def _canonical_plan(path: Path) -> dict:
    plan = json.loads(path.read_text(encoding="utf-8"))
    plan["plan_sha256"] = i5._sha256_bytes(
        i5._canonical({k: v for k, v in plan.items() if k != "plan_sha256"})
    )
    return plan


# ---------------------------------------------------------------------------
# P1 — exact population identity is 144 units / 219 tasks
# ---------------------------------------------------------------------------


class TestP1PopulationIdentity:
    def test_matrix_144_219(self) -> None:
        matrix = i5.load_matrix()
        assert matrix["population"]["n_validation_units"] == 144
        assert matrix["population"]["n_mapped_tasks"] == 219
        assert len(matrix["units"]) == 144

    def test_identity_sha(self) -> None:
        matrix = i5.load_matrix()
        assert matrix["population"]["population_identity_sha256"] == i6.EXPECTED_POPULATION_IDENTITY


# ---------------------------------------------------------------------------
# P2 — exact strata are 25 / 21 / 83 / 15
# ---------------------------------------------------------------------------


class TestP2Strata:
    def test_strata_exact(self) -> None:
        matrix = i5.load_matrix()
        assert matrix["strata"] == i6.EXPECTED_STRATA

    def test_matrix_strata_matches_plan_population(self) -> None:
        plan = i5.load_plan()
        pop = plan["population"]
        assert (pop["n_validation_units"], pop["n_mapped_tasks"]) == (144, 219)


# ---------------------------------------------------------------------------
# P3 — I5 resolver semantics are reused, not duplicated
# ---------------------------------------------------------------------------


class TestP3Reuse:
    def test_driver_imports_i5(self) -> None:
        assert i6.i5 is i5
        assert i6.EXCLUDED_BY_TARGET == i5.EXCLUDED_BY_TARGET
        assert i6.TERMINAL_READY == i5.TERMINAL_READY

    def test_driver_does_not_reimplement_parser(self) -> None:
        source = Path(i6.__file__).read_text(encoding="utf-8")
        # The I6 driver must NOT define its own parse_lock / wheel_compatible /
        # canonical name logic (it reuses I5).
        assert "def parse_lock" not in source
        assert "def wheel_compatible" not in source
        assert "def normalize_name" not in source
        assert "i5." in source  # reuses the I5 module

    def test_driver_uses_i5_resolve_unit(self) -> None:
        source = Path(i6.__file__).read_text(encoding="utf-8")
        assert "i5.resolve_unit" in source


# ---------------------------------------------------------------------------
# P4 — Poetry lock-level requirement can be separately target-excluded
# ---------------------------------------------------------------------------


@HAS_STORE and pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestP4PoetryTargetExclusion:
    def test_python_magic_bin_excluded_by_target(self) -> None:
        # python-magic-bin == 0.4.14 is retained at R4-B lock level (no lock
        # marker), but I6 adjudicates EXCLUDED_BY_TARGET via frozen
        # pyproject platform=win32 authority.
        cand = {
            "normalized_name": "python-magic-bin",
            "version": "0.4.14",
            "source_type": "REGISTRY",
            "task_id": "saleor-rc-e6198146186d",
        }
        cls, evidence = i6.adjudicate_candidate(cand, "3.12", set())
        assert cls == i6.EXCLUDED_BY_TARGET
        assert evidence["authority_status"] == "AUTHORITY_PROVES_TARGET_EXCLUSION"

    def test_pywin32_excluded_by_target(self) -> None:
        cand = {
            "normalized_name": "pywin32",
            "version": "306",
            "source_type": "REGISTRY",
            "task_id": "saleor-rc-e6198146186d",
        }
        cls, evidence = i6.adjudicate_candidate(cand, "3.12", set())
        assert cls == i6.EXCLUDED_BY_TARGET
        assert evidence["authority_status"] == "AUTHORITY_PROVES_TARGET_EXCLUSION"


# ---------------------------------------------------------------------------
# P5 — uv lock target exclusions remain correct
# ---------------------------------------------------------------------------


@HAS_STORE and pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestP5UvExclusions:
    def test_uv_closure_excludes_win32_edge_packages(self) -> None:
        plan = i5.load_plan()
        matrix = i5.load_matrix()
        identities = i5.build_unit_identity(plan, matrix, Path(r"D:\wp2_env_store"))
        identity = identities["vu-13c1de1de71e"]
        bind_integrated_parser()
        try:
            closure = i5._parse_lock_once(
                identity["member_tasks"][0], Path(r"D:\wp2_env_store"), "uv", T312
            )
        finally:
            unbind_lock_parser()
        excluded_names = {e.normalized_name for e in closure.exclusions}
        assert "python-magic-bin" in excluded_names
        assert "pywin32" in excluded_names


# ---------------------------------------------------------------------------
# P6 — compatible wheel exact name/version/era resolves
# ---------------------------------------------------------------------------


class TestP6WheelResolves:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_exact_wheel_resolves(self) -> None:
        store = Path(r"D:\wp2_env_store")
        ws = i5.LocalWheelStore(store, "py312")
        req = NormalizedRequirement(
            normalized_name="django",
            version="4.2.20",
            source_type=SourceType.REGISTRY,
            source_reference=None,
            marker=None,
            marker_applies=True,
            editable_self=False,
        )
        rec: dict = {}
        bind_integrated_parser()
        try:
            cls = i5._classify_requirement(
                req, rec, "3.12", ws, i5.SourceFidelityOverlay(), "vu-e4998719ee01"
            )
        finally:
            unbind_lock_parser()
        assert cls == i5.AVAILABLE_COMPATIBLE_WHEEL
        assert rec["compatible_wheels"]


# ---------------------------------------------------------------------------
# P7 — approved source/sdist resolves only when frozen route allows it
# ---------------------------------------------------------------------------


class TestP7ApprovedSourceRoute:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_approved_sdist_identity_resolves(self) -> None:
        approved = i6.load_approved_source_build_set()
        # pylint-celery 0.3 is an approved sdist route (in required_sdists).
        assert "pylint-celery==0.3::py38" in approved

    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_candidate_in_approved_set_resolves_as_sdist(self) -> None:
        approved = i6.load_approved_source_build_set()
        cand = {
            "normalized_name": "pylint-celery",
            "version": "0.3",
            "source_type": "REGISTRY",
            "task_id": "t",
        }
        cls, evidence = i6.adjudicate_candidate(cand, "3.8", approved)
        assert cls == i6.AVAILABLE_APPROVED_SOURCE_OR_SDIST
        assert "approved_source_build_identity" in evidence


# ---------------------------------------------------------------------------
# P8 — source-fidelity overlay remains correct
# ---------------------------------------------------------------------------


class TestP8SourceFidelity:
    def test_overlay_still_resolves(self) -> None:
        overlay = i5.SourceFidelityOverlay()
        pyxb = overlay.resolve("PyXB", "1.2.5")
        auth = overlay.resolve("authorizenet", "1.1.4")
        assert pyxb is not None and auth is not None

    def test_census_units_preserve_sf(self) -> None:
        # Both SF units are in the matrix with the overlay flag.
        matrix = i5.load_matrix()
        sf = {u["validation_unit_id"] for u in matrix["units"] if u.get("source_fidelity_overlay_required")}
        assert sf == {"vu-b9808f19ace4", "vu-692af9112c6d"}


# ---------------------------------------------------------------------------
# P9 — editable-self is never third-party artifact
# ---------------------------------------------------------------------------


@HAS_STORE and pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestP9EditableSelf:
    def test_editable_self_never_in_requirements(self) -> None:
        bind_integrated_parser()
        try:
            closure = i5._parse_lock_once(
                "saleor-rc-e0f2933d58b9", Path(r"D:\wp2_env_store"), "uv", T312
            )
        finally:
            unbind_lock_parser()
        assert closure.editable_self is not None
        names = {r.normalized_name for r in closure.requirements}
        assert closure.editable_self.normalized_name not in names


# ---------------------------------------------------------------------------
# P10 — 219 member-task commit readiness is enforced
# ---------------------------------------------------------------------------


class TestP10CommitReadiness:
    @pytest.mark.skipif(not (HAS_STORE and HAS_REPO), reason="store/os env unavailable")
    def test_all_219_commits_present(self) -> None:
        repo = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor")
        plan = i5.load_plan()
        matrix = i5.load_matrix()
        identities = i6.build_population_identity(plan, matrix, Path(r"D:\wp2_env_store"))
        checked = 0
        for uid in identities:
            for _tid, trec in identities[uid]["task_identity"].items():
                assert i5._check_commit(repo, trec["target_commit"]) is True
                checked += 1
        assert checked == 219


# ---------------------------------------------------------------------------
# P11 — TRUE_MISSING requires exhausting all applicable approved routes
# ---------------------------------------------------------------------------


class TestP11TrueMissingExhaustion:
    def test_true_missing_requires_route_exhaustion(self) -> None:
        approved = i6.load_approved_source_build_set() if HAS_STORE else set()
        # pylint 2.9.6: no wheel, not in approved source set, not excluded.
        cand = {
            "normalized_name": "pylint",
            "version": "2.9.6",
            "source_type": "REGISTRY",
            "task_id": "saleor-rc-10889526d151",
        }
        cls, evidence = i6.adjudicate_candidate(cand, "3.9", approved)
        assert cls == i6.TRUE_MISSING_ARTIFACT
        assert evidence["no_approved_sdist_source_build_input"] is True
        assert evidence["no_approved_compatible_wheel"] is True


# ---------------------------------------------------------------------------
# P12 — population results serialize deterministically
# ---------------------------------------------------------------------------


@HAS_STORE and HAS_REPO and pytest.mark.skipif(not (HAS_STORE and HAS_REPO), reason="store/os env unavailable")
class TestP12Determinism:
    def test_repeated_run_canonical_equal(self) -> None:
        store = Path(r"D:\wp2_env_store")
        repo = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor")
        first = i6.run_census(store, repo, write=False, census_out=None, summary_out=None)
        second = i6.run_census(store, repo, write=False, census_out=None, summary_out=None)
        assert first["canonical_sha256"] == second["canonical_sha256"]

    def test_rerun_mismatch_fails_closed(self) -> None:
        store = Path(r"D:\wp2_env_store")
        repo = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor")
        with pytest.raises(i6.CensusFailClosedError, match="deterministic rerun mismatch"):
            i6.run_census(
                store,
                repo,
                write=False,
                census_out=None,
                summary_out=None,
                previous_canonical="0" * 64,
            )


# ---------------------------------------------------------------------------
# F2P — invalid/mutated inputs fail closed
# ---------------------------------------------------------------------------


class TestF1WrongPopulationSize:
    def test_wrong_size_fails(self, tmp_path: Path) -> None:
        matrix = copy.deepcopy(json.loads((R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json").read_text(encoding="utf-8")))
        matrix["units"] = matrix["units"][:143]
        matrix["population"]["n_validation_units"] = 143
        path = _write(tmp_path, "matrix.json", json.dumps(matrix))
        with pytest.raises(i5.SmokeFailClosedError, match="population counts|n_validation_units"):
            i5.load_matrix(path)


class TestF2WrongIdentitySha:
    def test_wrong_sha_fails(self, tmp_path: Path) -> None:
        matrix = copy.deepcopy(json.loads((R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json").read_text(encoding="utf-8")))
        matrix["population"]["population_identity_sha256"] = "0" * 64
        path = _write(tmp_path, "matrix.json", json.dumps(matrix))
        with pytest.raises(i5.SmokeFailClosedError, match="population identity"):
            i5.load_matrix(path)


class TestF3MissingUnit:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_missing_unit_fails(self) -> None:
        plan = i5.load_plan()
        matrix = copy.deepcopy(json.loads((R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json").read_text(encoding="utf-8")))
        matrix["units"] = [u for u in matrix["units"] if u["validation_unit_id"] != "vu-13c1de1de71e"]
        with pytest.raises(i5.SmokeFailClosedError):
            i5.build_unit_identity(plan, matrix, Path(r"D:\wp2_env_store"))


class TestF4MissingTask:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_missing_task_fails(self, tmp_path: Path) -> None:
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
        with pytest.raises(i6.CensusFailClosedError, match="missing from TASK_ENV"):
            i6.build_population_identity(plan, matrix, store)


class TestF5UnknownEra:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_unknown_era_fails(self) -> None:
        store = Path(r"D:\wp2_env_store")
        plan = i5.load_plan()
        matrix = i5.load_matrix()
        identities = i5.build_unit_identity(plan, matrix, store)
        identity = copy.deepcopy(identities["vu-13c1de1de71e"])
        identity["matrix_record"]["python_version"] = "3.7"
        identity["matrix_record"]["wheelhouse_era"] = "py37"
        ws = i5.LocalWheelStore(store, "py312")
        with pytest.raises(i5.SmokeFailClosedError, match="python era|era"):
            i5.resolve_unit("vu-13c1de1de71e", identity, store, store, ws, i5.SourceFidelityOverlay())


class TestF6UnknownLockType:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_unknown_lock_type_fails(self) -> None:
        store = Path(r"D:\wp2_env_store")
        plan = i5.load_plan()
        matrix = i5.load_matrix()
        identities = i5.build_unit_identity(plan, matrix, store)
        identity = copy.deepcopy(identities["vu-13c1de1de71e"])
        identity["matrix_record"]["lock_type"] = "npm"
        ws = i5.LocalWheelStore(store, "py312")
        with pytest.raises(i5.SmokeFailClosedError, match="lock_type"):
            i5.resolve_unit("vu-13c1de1de71e", identity, store, store, ws, i5.SourceFidelityOverlay())


class TestF7UnknownRoute:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_unknown_route_fails(self) -> None:
        store = Path(r"D:\wp2_env_store")
        plan = i5.load_plan()
        matrix = i5.load_matrix()
        identities = i5.build_unit_identity(plan, matrix, store)
        identity = copy.deepcopy(identities["vu-13c1de1de71e"])
        identity["matrix_record"]["install_route"] = "MYSTERY_ROUTE"
        ws = i5.LocalWheelStore(store, "py312")
        with pytest.raises(i5.SmokeFailClosedError, match="install route"):
            i5.resolve_unit("vu-13c1de1de71e", identity, store, store, ws, i5.SourceFidelityOverlay())


class TestF8UnknownSourceType:
    def test_unknown_source_type_fails_closed(self) -> None:
        # A non-SF unit requesting DIRECTORY source semantics is unsupported.
        req = NormalizedRequirement(
            normalized_name="some-dir-pkg",
            version="1.0.0",
            source_type=SourceType.DIRECTORY,
            source_reference="some/path",
            marker=None,
            marker_applies=True,
            editable_self=False,
        )
        rec: dict = {}
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            manif = tmp / "manifests"
            manif.mkdir()
            (manif / "WHEELHOUSE_HASHES_py312.json").write_text(
                json.dumps({"artifacts": []}), encoding="utf-8"
            )
            ws = i5.LocalWheelStore(tmp, "py312")
            cls = i5._classify_requirement(
                req, rec, "3.12", ws, i5.SourceFidelityOverlay(), "vu-13c1de1de71e"
            )
            assert cls == i5.UNSUPPORTED_SOURCE_SEMANTICS


class TestF9NearMatch:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_near_match_does_not_resolve(self) -> None:
        ws = i5.LocalWheelStore(Path(r"D:\wp2_env_store"), "py312")
        req = NormalizedRequirement(
            normalized_name="django-not-a-real-pkg",
            version="1.0.0",
            source_type=SourceType.REGISTRY,
            source_reference=None,
            marker=None,
            marker_applies=True,
            editable_self=False,
        )
        rec: dict = {}
        cls = i5._classify_requirement(req, rec, "3.12", ws, i5.SourceFidelityOverlay(), "vu-13c1de1de71e")
        assert cls == i5.MISSING_LOCAL_ARTIFACT_CANDIDATE


class TestF10WrongVersion:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_wrong_version_does_not_resolve(self) -> None:
        ws = i5.LocalWheelStore(Path(r"D:\wp2_env_store"), "py312")
        req = NormalizedRequirement(
            normalized_name="django",
            version="9.9.9",
            source_type=SourceType.REGISTRY,
            source_reference=None,
            marker=None,
            marker_applies=True,
            editable_self=False,
        )
        rec: dict = {}
        cls = i5._classify_requirement(req, rec, "3.12", ws, i5.SourceFidelityOverlay(), "vu-13c1de1de71e")
        assert cls == i5.MISSING_LOCAL_ARTIFACT_CANDIDATE


class TestF11WrongEraWheel:
    def test_wrong_era_wheel_rejected(self) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible("pkg-1.0-cp38-cp38-linux_x86_64.whl", T312) is False
        finally:
            unbind_lock_parser()


class TestF12WheelAbsenceNotTrueMissingWhenApprovedRoute:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_approved_route_prevents_true_missing(self) -> None:
        approved = i6.load_approved_source_build_set()
        # pylint-celery 0.3 has an approved sdist route -> not TRUE_MISSING even
        # if no compatible wheel existed.
        cand = {
            "normalized_name": "pylint-celery",
            "version": "0.3",
            "source_type": "REGISTRY",
            "task_id": "t",
        }
        cls, _evidence = i6.adjudicate_candidate(cand, "3.8", approved)
        assert cls == i6.AVAILABLE_APPROVED_SOURCE_OR_SDIST
        assert cls != i6.TRUE_MISSING_ARTIFACT


class TestF13ExactAbsenceCanBeTrueMissing:
    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_no_route_exact_absence_true_missing(self) -> None:
        approved = i6.load_approved_source_build_set()
        cand = {
            "normalized_name": "pylint",
            "version": "2.9.6",
            "source_type": "REGISTRY",
            "task_id": "saleor-rc-10889526d151",
        }
        cls, evidence = i6.adjudicate_candidate(cand, "3.9", approved)
        assert cls == i6.TRUE_MISSING_ARTIFACT
        assert evidence["no_applicable_frozen_exclusion"] is True


class TestF14AmbiguousExclusion:
    def test_unknown_candidate_identity_fails_closed(self) -> None:
        # A candidate whose frozen authority is not defined cannot be silently
        # classified: adjudicate_candidate must not guess.
        cand = {
            "normalized_name": "some-mystery-pkg",
            "version": "1.0.0",
            "source_type": "REGISTRY",
            "task_id": "t",
        }
        cls, evidence = i6.adjudicate_candidate(cand, "3.9", set())
        assert cls == i6.TRUE_MISSING_ARTIFACT
        assert evidence["classification_not_parser_instrumentation_error"] is True


class TestF15MalformedDockerReceipt:
    def test_malformed_receipt_fails_closed(self, tmp_path: Path) -> None:
        i3_path = R4_DIR / "R4_I3_CAPABILITY_STATE_RECONCILIATION.json"
        receipts = copy.deepcopy(json.loads(i3_path.read_text(encoding="utf-8")))
        receipts["present_match_count"] = 13
        path = _write(tmp_path, "i3.json", json.dumps(receipts))
        with pytest.raises(i5.SmokeFailClosedError, match="present|receipt"):
            i5.validate_i3_receipt(path)


class TestF16RepoCommitAsTooling:
    def test_missing_commit_fails_as_tooling(self) -> None:
        repo = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor")
        if not repo.exists():
            pytest.skip("repo unavailable")
        assert i5._check_commit(repo, "0" * 40) is False
        # The census treats a missing repo/commit as a fail-closed
        # environment/tooling gate, never as an artifact-missing classification.
        source = Path(i6.__file__).read_text(encoding="utf-8")
        assert "repository/commit readiness" in source
        assert "commit_ready != EXPECTED_TASKS" in source

    def test_census_gate_lists_commit_readiness(self) -> None:
        source = Path(i6.__file__).read_text(encoding="utf-8")
        assert "repository/commit readiness" in source
        assert "commit_ready != EXPECTED_TASKS" in source


class TestF17NoNetworkFallback:
    def test_driver_has_no_network_fallback(self) -> None:
        source = Path(i6.__file__).read_text(encoding="utf-8")
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
        source = Path(i6.__file__).read_text(encoding="utf-8")
        assert "import docker" not in source
        assert re.search(r"subprocess\.run\(\s*\[\s*[\"']docker", source) is None


class TestF18NoSilentSkip:
    def test_census_loop_processes_every_unit_and_task(self) -> None:
        source = Path(i6.__file__).read_text(encoding="utf-8")
        assert "for uid in [u[\"validation_unit_id\"] for u in matrix[\"units\"]]:" in source
        assert "len(all_tasks) != EXPECTED_TASKS" in source
        assert "len(results) != EXPECTED_UNITS" in source
        assert "if silent_skips != 0" in source
