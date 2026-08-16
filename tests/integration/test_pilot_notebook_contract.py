"""PILOT-EXEC-01: Pilot notebook contract (04_PILOT_NOTEBOOK_CONTRACT.md).

Validates the canonical ``notebooks/pilot_exec_01.ipynb``:

- valid nbformat JSON and required cell order;
- every code cell compiles;
- exact Pilot profile / model / quantization identity;
- no forbidden executable Smoke launch (scientific-smoke-v2, Full-9, bnb-int8,
  7B, --max-runs, --strategy);
- the three-repo preflight runs before the model preflight, and both run before
  the real launch; the mock dry-run runs before the model run; the secrets cell
  never prints the token;
- the bundled notebook byte-equals the canonical notebook (via the Pilot
  deployment bundle builder);
- the Kaggle transport restore cell runs immediately after extraction, verifies
  the hashed path map against the deployment identity, restores exact original
  paths BEFORE manifest/snapshot verification, keeps fail-closed traversal
  guards, and leaves scientific cell ordering unchanged.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"
CANONICAL_NOTEBOOK = PROJECT_DIR / "notebooks" / "pilot_exec_01.ipynb"
EXPECTED_FROZEN_SOURCE_TAG = "v0.9.12-pilot-exec-ready"

# The bundled-notebook parity test builds a full Pilot bundle; the hermetic
# fixture keeps that build deterministic without developer-local repo caches.
pytestmark = pytest.mark.usefixtures("hermetic_pilot_repo_materialize")

REQUIRED_CELL_ORDER = (
    "setup-cell",
    "pilot-archive-verify-cell",
    "transport-restore-cell",
    "pilot-identity-verify-cell",
    "install-lock-cell",
    "pilot-snapshot-verify-cell",
    "service-bootstrap-cell",
    "pilot-repo-preflight-cell",
    "gpu-verify-cell",
    "model-preflight-cell",
    "dryrun-cell",
    "secrets-cell",
    "pilot-launch-cell",
    "pilot-resume-cell",
    "pilot-verify-cell",
    "pilot-export-cell",
)

FORBIDDEN_CODE_FRAGMENTS = (
    "--profile scientific-smoke-v2",
    "scientific-smoke-v2",
    "bnb-int8",
    "--max-runs",
    "--strategy",
    "full9_scientific_smoke",
    "qwen14b_bnb_nf4_full9",
    "max-runs 2",
)


def _nb() -> dict[str, Any]:
    return json.loads(CANONICAL_NOTEBOOK.read_text(encoding="utf-8"))


def _src(cell: dict[str, Any]) -> str:
    src = cell["source"]
    return src if isinstance(src, str) else "".join(src)


def _code_cells(nb: dict[str, Any]) -> list[dict[str, Any]]:
    return [c for c in nb["cells"] if c.get("cell_type") == "code"]


def _code_text(nb: dict[str, Any]) -> str:
    return "\n".join(_src(c) for c in _code_cells(nb))


def _cells_by_id(nb: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c.get("id", ""): c for c in nb["cells"]}


class TestNotebookStructure:
    def test_valid_nbformat(self) -> None:
        nb = _nb()
        assert nb["nbformat"] == 4
        assert nb["nbformat_minor"] == 5

    def test_required_cell_order(self) -> None:
        nb = _nb()
        ids = [c.get("id", "") for c in nb["cells"]]
        index = {cell_id: idx for idx, cell_id in enumerate(ids)}
        for idx, cell_id in enumerate(REQUIRED_CELL_ORDER):
            assert cell_id in index, f"missing required cell: {cell_id}"
            assert index[cell_id] == idx + 1, (
                f"cell '{cell_id}' at position {index[cell_id]}, expected {idx + 1}"
            )

    def test_title_identifies_pilot_non_publication(self) -> None:
        nb = _nb()
        title = _src(nb["cells"][0])
        assert "PILOT-EXEC-01" in title
        assert "48" in title
        assert "bnb-nf4" in title


class TestCodeCellsCompile:
    def test_all_code_cells_compile(self) -> None:
        nb = _nb()
        for cell in _code_cells(nb):
            ast.parse(_src(cell))  # raises SyntaxError on failure


class TestFrozenIdentity:
    def test_profile_model_quantization_identity(self) -> None:
        cells = _cells_by_id(_nb())
        setup = _src(cells["setup-cell"])
        assert 'EXPECTED_PROFILE = "pilot"' in setup
        assert 'EXPECTED_MODEL_IDENTITY = "qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25"' in setup
        assert 'QWEN_QUANTIZATION = "bnb-nf4"' in setup
        assert 'EXPECTED_PROTOCOL_VERSION = "1.0"' in setup

    def test_identity_cell_reads_bundled_identity(self) -> None:
        cells = _cells_by_id(_nb())
        identity_src = _src(cells["pilot-identity-verify-cell"])
        setup_src = _src(cells["setup-cell"])
        assert "pilot_deployment_identity.json" in identity_src
        # Frozen deployment identity now lives once in the setup cell and is
        # referenced by the verify cell for both input modes.
        assert "FROZEN_DEPLOYMENT" in identity_src
        assert '"task": "PILOT-EXEC-01"' in setup_src
        assert '"expected_cells": 48' in setup_src

    def test_identity_cell_anchors_source_tag(self) -> None:
        identity_src = _src(_cells_by_id(_nb())["pilot-identity-verify-cell"])
        assert "FROZEN_SOURCE_COMMIT" not in identity_src
        assert "FROZEN_SOURCE_TAG" in identity_src
        assert "SOURCE TAG MISMATCH" in identity_src


class TestForbiddenContent:
    def test_no_forbidden_smoke_launch_in_code(self) -> None:
        text = _code_text(_nb())
        for fragment in FORBIDDEN_CODE_FRAGMENTS:
            assert fragment not in text, f"forbidden code fragment present: {fragment!r}"


class TestExecutionOrdering:
    def _index(self, cell_id: str) -> int:
        return [c.get("id", "") for c in _nb()["cells"]].index(cell_id)

    def test_repo_preflight_before_model_preflight_before_launch(self) -> None:
        assert self._index("pilot-repo-preflight-cell") < self._index("model-preflight-cell")
        assert self._index("model-preflight-cell") < self._index("pilot-launch-cell")

    def test_dryrun_before_model_run(self) -> None:
        assert self._index("dryrun-cell") < self._index("pilot-launch-cell")

    def test_secrets_before_launch_and_never_printed(self) -> None:
        assert self._index("secrets-cell") < self._index("pilot-launch-cell")
        secrets = _src(_cells_by_id(_nb())["secrets-cell"])
        assert "get_secret" in secrets
        assert "print(hf_token" not in secrets
        assert "print(hf_tok" not in secrets

    @staticmethod
    def _cmd_list_tokens(cell_src: str, target: str) -> list[str]:
        """Extract the string tokens of ``target = [...]`` from a code cell."""
        module = ast.parse(cell_src)
        for node in module.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == target for t in node.targets
            ):
                assert isinstance(node.value, (ast.List, ast.Tuple))
                return [
                    elt.value
                    for elt in node.value.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                ]
        raise AssertionError(f"no assignment to {target} found in cell")

    def test_launch_frozen_flags(self) -> None:
        launch = _src(_cells_by_id(_nb())["pilot-launch-cell"])
        for fragment in (
            "--backend",
            "kaggle-qwen",
            "--profile",
            "pilot",
            "--qwen-quantization",
            "QWEN_QUANTIZATION",
            "--max-attempts",
            "3",
            "--protocol-version",
            "1.0",
            "--timeout",
            "600",
            "--hf-sync",
            "--new-experiment",
        ):
            assert fragment in launch, f"missing launch fragment: {fragment!r}"
        tokens = self._cmd_list_tokens(launch, "exec_cmd")
        assert "--new-experiment" in tokens
        assert "bnb-nf4" not in tokens  # value frozen via QWEN_QUANTIZATION in setup

    def test_resume_never_creates_new_experiment(self) -> None:
        resume = _src(_cells_by_id(_nb())["pilot-resume-cell"])
        tokens = self._cmd_list_tokens(resume, "resume_cmd")
        assert "--resume-from-hf" in tokens
        assert "--new-experiment" not in tokens


class TestServiceBootstrap:
    def _index(self, cell_id: str) -> int:
        return [c.get("id", "") for c in _nb()["cells"]].index(cell_id)

    def _src(self, cell_id: str) -> str:
        return _src(_cells_by_id(_nb())[cell_id])

    def test_cell_exists(self) -> None:
        assert "service-bootstrap-cell" in _cells_by_id(_nb())

    def test_after_snapshot_before_repo_preflight(self) -> None:
        assert self._index("pilot-snapshot-verify-cell") < self._index(
            "service-bootstrap-cell"
        )
        assert self._index("service-bootstrap-cell") < self._index(
            "pilot-repo-preflight-cell"
        )
        assert self._index("service-bootstrap-cell") < self._index("model-preflight-cell")

    def test_topology_matches_frozen_manifest(self) -> None:
        src = self._src("service-bootstrap-cell")
        assert "127.0.0.1" in src
        assert "5433" in src
        assert "6379" in src
        assert "saleor" in src
        assert "postgres://saleor:saleor@127.0.0.1:5433/saleor" in src
        assert "redis://127.0.0.1:6379/0" in src
        assert "valkey-server" in src
        assert "redis-server" in src

    def test_fail_closed_and_idempotent(self) -> None:
        src = self._src("service-bootstrap-cell")
        assert "raise RuntimeError" in src
        assert "already listening" in src or "already open" in src
        assert "SALEOR VALIDATION SERVICE BOOTSTRAP: PASSED" in src
        assert "model load" in src

    def test_root_safe_unprivileged_postgres_lifecycle(self) -> None:
        """Kaggle runs the notebook as root; initdb/pg_ctl must run unprivileged."""
        src = self._src("service-bootstrap-cell")
        assert "geteuid" in src
        assert "pwd.getpwnam" in src
        assert '"postgres"' in src
        assert "user=pg_user" in src
        assert "user=None" in src
        assert "shell=True" not in src
        assert "runuser" not in src

    def test_never_prints_unknown_secrets(self) -> None:
        src = self._src("service-bootstrap-cell")
        assert "HF_TOKEN" not in src
        assert "get_secret" not in src

    def test_redis_package_fallback_contract(self) -> None:
        """KAGGLE-REDIS-PACKAGE-FALLBACK: never install alternative packages in
        one apt transaction; probe and install exactly one candidate at a time.
        """
        src = self._src("service-bootstrap-cell")
        assert '"valkey-server redis-server"' not in src
        assert "REDIS_CANDIDATE_PACKAGES" in src
        assert "_apt_update_once" in src
        assert "_apt_install_one" in src
        assert "_apt_package_available" in src
        assert "_provision_redis_server" in src
        assert '"apt-cache", "policy"' in src
        assert "no pip" in src
        assert "in-process fake server" in src
        assert "shell=True" not in src


class TestRepoPreflight:
    def test_all_three_repos_preflight_no_model_call(self) -> None:
        preflight = _src(_cells_by_id(_nb())["pilot-repo-preflight-cell"])
        for repo in ("todo", "djangocms", "saleor"):
            assert repo in preflight
        assert "no model call" in preflight or "no model" in preflight

    def test_snapshot_verify_checks_three_repos(self) -> None:
        snapshot = _src(_cells_by_id(_nb())["pilot-snapshot-verify-cell"])
        assert "repository_snapshot_manifest.json" in snapshot
        assert "PILOT_REPOSITORIES" in snapshot
        assert "requested_sha" in snapshot
        assert "content_hash" in snapshot
        # The frozen repo list lives in the setup cell; the verify cell must
        # iterate over it rather than hard-coding a single repository.
        setup = _src(_cells_by_id(_nb())["setup-cell"])
        assert 'PILOT_REPOSITORIES = ("todo", "djangocms", "saleor")' in setup

    def test_preflight_is_a_thin_provisioning_helper_adapter(self) -> None:
        preflight = _src(_cells_by_id(_nb())["pilot-repo-preflight-cell"])
        assert "pilot_kaggle_repo_envs.py" in preflight
        assert "importlib.util.spec_from_file_location" in preflight
        assert "provision_repository_envs(" in preflight
        assert "host_python=sys.executable" in preflight
        assert "source_tag=SOURCE_TAG" in preflight
        assert 'log_path=PREFLIGHT_DIR / "environment_provisioning.log"' in preflight
        assert 'envs_evidence["djangocms"]["python"]' in preflight
        assert 'envs_evidence["saleor"]["python"]' in preflight
        assert "def _assert_service_port(host, port, label):" in preflight
        assert "SALEOR_PG_PORT" in preflight and "SALEOR_REDIS_PORT" in preflight
        assert '"-m", "venv"' not in preflight
        assert "ensurepip" not in preflight
        assert "--strategy" not in preflight and "--max-runs" not in preflight


class TestKaggleTransportRestore:
    """PILOT-EXEC-01 KAGGLE-FILENAME-TRANSPORT notebook contract.

    The transport restore must run immediately AFTER archive extraction and
    BEFORE any code/data/notebook manifest or repository snapshot verification,
    must verify the hashed path map against the deployment identity, and must
    fail closed on any traversal/escaping destination. Scientific cell ordering
    is otherwise unchanged.
    """

    def _index(self, cell_id: str) -> int:
        return [c.get("id", "") for c in _nb()["cells"]].index(cell_id)

    def _src(self, cell_id: str) -> str:
        return _src(_cells_by_id(_nb())[cell_id])

    def test_cell_present(self) -> None:
        assert "transport-restore-cell" in _cells_by_id(_nb())

    def test_restore_after_extraction(self) -> None:
        assert self._index("transport-restore-cell") > self._index("pilot-archive-verify-cell")

    def test_restore_before_manifest_verification(self) -> None:
        assert self._index("transport-restore-cell") < self._index("pilot-identity-verify-cell")
        assert self._index("transport-restore-cell") < self._index("pilot-snapshot-verify-cell")

    def test_transport_map_hash_verified_against_identity(self) -> None:
        src = self._src("transport-restore-cell")
        assert "kaggle_transport_path_map_sha256" in src
        assert "pilot_deployment_identity.json" in src
        assert "_sha256_bytes(TRANSPORT_MAP_PATH.read_bytes())" in src
        assert "SHA VERIFICATION FAILED" in src

    def test_fail_closed_path_traversal_guards_exist(self) -> None:
        src = self._src("transport-restore-cell")
        assert '".." in _dest_rel.split("/")' in src
        assert "is_relative_to(EXTRACT_ROOT.resolve())" in src
        assert "escape" in src.lower()
        assert "destination collision" in src
        assert "transport blob missing" in src
        assert "kaggle_transport" in src
        assert "__kaggle_transport__" not in src

    def test_restore_requires_nonempty_map(self) -> None:
        src = self._src("transport-restore-cell")
        assert "must be a non-empty JSON object" in src

    def test_restore_verifies_no_mapped_blob_remains(self) -> None:
        src = self._src("transport-restore-cell")
        assert "unmapped transport members remain" in src

    def test_scientific_cell_ordering_unchanged(self) -> None:
        order = list(REQUIRED_CELL_ORDER)
        code_ids = [
            c.get("id", "") for c in _nb()["cells"] if c.get("cell_type") == "code"
        ]
        for cell_id in order:
            assert cell_id in code_ids, f"missing cell: {cell_id}"
        assert code_ids == order


class TestKaggleAutoExpandedMount:
    """PILOT-EXEC-01 KAGGLE-AUTO-EXPANDED-MOUNT notebook contract.

    The notebook must support exactly two fail-closed input modes: (A) the
    original frozen archive and (B) the Kaggle auto-expanded directory mounted
    as ``<dataset>/pilot-kaggle-upload/`` with a sibling ``.sha256`` sidecar.
    Mode B is trusted only against the notebook-frozen anchors that are
    INDEPENDENT of the notebook bytes (source tag, deployment identity, the
    four stable manifest/map SHA values); the archive SHA and notebook-manifest
    SHA are verified self-consistently at runtime (sidecar vs actual ZIP SHA,
    manifest file vs identity field, manifest notebook entry vs the bundled
    notebook bytes). The expanded tree is copied to the writable working root -
    /kaggle/input is never mutated. Either mode converges on the same
    EXTRACT_ROOT provisioning before the unchanged transport-restore +
    identity-verify cells.
    """

    def _index(self, cell_id: str) -> int:
        return [c.get("id", "") for c in _nb()["cells"]].index(cell_id)

    def _src(self, cell_id: str) -> str:
        return _src(_cells_by_id(_nb())[cell_id])

    def test_dual_mode_discovery_present(self) -> None:
        setup = self._src("setup-cell")
        assert 'PILOT_ARCHIVE_NAME = "pilot-kaggle-upload.zip"' in setup
        assert 'EXPANDED_BUNDLE_DIR_NAME = "pilot-kaggle-upload"' in setup
        assert "PILOT_ARCHIVE_SIDECAR_NAME" in setup
        assert "_discover_expanded_bundle" in setup
        assert "_is_pilot_expanded_root" in setup

    def test_expanded_root_signature_members(self) -> None:
        setup = self._src("setup-cell")
        for member in (
            "pilot_deployment_identity.json",
            "code_manifest.json",
            "data_manifest.json",
            "notebook_manifest.json",
            "repository_snapshot_manifest.json",
            "kaggle_transport_path_map.json",
            "code",
            "data",
            "notebooks",
            "kaggle_transport",
        ):
            assert member in setup, f"expanded-root member missing: {member}"

    def test_exactly_one_input_shape_selected(self) -> None:
        setup = self._src("setup-cell")
        assert 'PILOT_INPUT_MODE = "archive"' in setup
        assert 'PILOT_INPUT_MODE = "expanded"' in setup
        assert "PILOT_BUNDLE_INPUT" in setup
        assert "Ambiguous Pilot bundle input mounts" in setup
        assert "BOTH an original archive" in setup
        assert "len(_pilot_archives) > 1 or len(_pilot_expanded) > 1" in setup
        # The single-shape archive discovery variable must no longer exist.
        assert "PILOT_ARCHIVE =" not in setup

    def test_sidecar_required_in_both_modes(self) -> None:
        setup = self._src("setup-cell")
        assert "missing SHA-256 sidecar for Pilot bundle input" in setup
        assert "PILOT_ARCHIVE_SHA" in setup

    def test_frozen_trust_anchors_present(self) -> None:
        setup = self._src("setup-cell")
        assert f'FROZEN_SOURCE_TAG = "{EXPECTED_FROZEN_SOURCE_TAG}"' in setup
        assert "FROZEN_DEPLOYMENT" in setup
        assert "FROZEN_MANIFEST_HASHES" in setup

    def test_frozen_anchor_shapes(self) -> None:
        setup = self._src("setup-cell")
        # Anchors that hash content containing the notebook bytes must NOT be
        # embedded (they cannot equal their own hash).
        assert not re.search(r'FROZEN_ARCHIVE_SHA = "', setup)
        assert not re.search(r'FROZEN_SOURCE_COMMIT = "', setup)
        for key in (
            "code_manifest_sha256",
            "data_manifest_sha256",
            "repository_snapshot_manifest_sha256",
            "kaggle_transport_path_map_sha256",
        ):
            m = re.search(rf'"{key}": "([0-9a-fA-F]+)"', setup)
            assert m is not None, f"missing frozen hash: {key}"
            assert len(m.group(1)) == 64, f"frozen hash not 64 hex: {key}"
        assert not re.search(r'"notebook_manifest_sha256": "', setup)

    def test_frozen_deployment_identity_values(self) -> None:
        setup = self._src("setup-cell")
        for fragment in (
            '"task": "PILOT-EXEC-01"',
            '"protocol_version": "1.0"',
            '"model_name": "Qwen/Qwen2.5-Coder-14B-Instruct"',
            '"quantization": "bnb-nf4"',
            '"timeout_seconds": 600',
            '"max_attempts": 3',
            '"max_completion_tokens_per_call": 4096',
            '"max_total_workflow_tokens": 0',
            '"scenario_count": 12',
            '"strategy_count": 2',
            '"repetitions": 2',
            '"expected_cells": 48',
        ):
            assert fragment in setup, f"frozen deployment field missing: {fragment}"

    def test_verify_cell_checks_sidecar_against_zip(self) -> None:
        verify = self._src("pilot-archive-verify-cell")
        assert "FROZEN_ARCHIVE_SHA" not in verify
        assert "PILOT_ARCHIVE_SHA.read_text" in verify
        assert "SIDECAR MALFORMED" in verify
        assert "PILOT ARCHIVE SHA VERIFICATION FAILED" in verify
        assert "_sha256_bytes(PILOT_BUNDLE_INPUT.read_bytes())" in verify
        assert "provenance only" in verify

    def test_verify_cell_frozen_tree_trust_in_both_modes(self) -> None:
        verify = self._src("pilot-archive-verify-cell")
        assert "SOURCE TAG MISMATCH" in verify
        assert "DEPLOYMENT IDENTITY MISMATCH" in verify
        assert "MANIFEST/MAP SHA MISMATCH" in verify
        assert "FROZEN_MANIFEST_HASHES" in verify
        assert "SOURCE COMMIT MISMATCH" not in verify
        assert "refusing to proceed" in verify
        assert "refusing to copy" not in verify
        # notebook_manifest must be verified self-consistently, not against a
        # frozen equality anchor.
        assert "identity field does not match manifest file hash" in verify
        assert "entry does not match the bundled notebook bytes" in verify
        assert "_tree = PILOT_BUNDLE_INPUT if PILOT_INPUT_MODE" in verify

    def test_expanded_mode_copies_to_working_root(self) -> None:
        verify = self._src("pilot-archive-verify-cell")
        assert "NEVER mutate /kaggle/input" in verify
        assert "shutil.copytree(PILOT_BUNDLE_INPUT, EXTRACT_ROOT" in verify
        assert "PILOT BUNDLE PROVISIONING: PASSED (auto-expanded copy)" in verify
        assert "EXTRACT_ROOT" in verify

    def test_verify_cell_never_mutates_input(self) -> None:
        verify = self._src("pilot-archive-verify-cell")
        for fragment in ("rmtree", ".unlink(", ".rename(", "remove("):
            assert fragment not in verify, f"mutating fragment present: {fragment!r}"

    def test_both_modes_converge_on_same_provisioning(self) -> None:
        verify = self._src("pilot-archive-verify-cell")
        assert 'CODE_DIR = EXTRACT_ROOT / "code"' in verify
        assert 'DATA_DIR = EXTRACT_ROOT / "data"' in verify
        # The unchanged transport-restore cell must only ever touch the working
        # copy, never the /kaggle/input bundle path.
        restore = self._src("transport-restore-cell")
        assert "PILOT_BUNDLE_INPUT" not in restore
        assert "PILOT_ARCHIVE" not in restore
        assert "EXTRACT_ROOT" in restore
        assert self._index("pilot-archive-verify-cell") < self._index(
            "transport-restore-cell"
        )


class TestBundledNotebookParity:
    def test_bundled_notebook_byte_equals_canonical(self, tmp_path: Path) -> None:
        spec = importlib.util.spec_from_file_location(
            "build_pilot_upload_bundle_parity_test",
            str(SCRIPTS_DIR / "build_pilot_upload_bundle.py"),
        )
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        output_root = tmp_path / "pilot-upload-parity"
        archive = tmp_path / "pilot-upload-parity.zip"
        mod.build_pilot_bundle(
            output_root=output_root,
            archive_path=archive,
            source_commit="a" * 40,
            source_tag="v0.9.3-pilot-exec-ready",
            created_utc="2026-08-10T00:00:00+00:00",
            validate_notebook_trust=False,
        )
        bundled = output_root / "notebooks" / "pilot_exec_01.ipynb"
        assert bundled.is_file()
        canonical_bytes = CANONICAL_NOTEBOOK.read_bytes().replace(b"\r\n", b"\n")
        bundled_bytes = bundled.read_bytes().replace(b"\r\n", b"\n")
        assert bundled_bytes == canonical_bytes, "bundled notebook differs from canonical"
