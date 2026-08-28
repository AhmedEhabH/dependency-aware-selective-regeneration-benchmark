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
import subprocess
import sys
import time as _time
from pathlib import Path
from typing import Any

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"
CANONICAL_NOTEBOOK = PROJECT_DIR / "notebooks" / "pilot_exec_01.ipynb"
EXPECTED_FROZEN_SOURCE_TAG = "v0.9.22-pilot-exec-ready"

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


def _assigned_list_elements(source: str, target: str) -> list[ast.expr]:
    tree = ast.parse(source)
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(name, ast.Name) and name.id == target for name in node.targets)
    ]
    assert len(assignments) == 1, f"expected one assignment to {target}"
    value = assignments[0].value
    assert isinstance(value, ast.List), f"{target} must be a list"
    return list(value.elts)


def _assert_string(node: ast.expr, expected: str) -> None:
    assert isinstance(node, ast.Constant) and node.value == expected


def _assert_prefixed_name(node: ast.expr, prefix: str, name: str) -> None:
    assert isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
    _assert_string(node.left, prefix)
    assert isinstance(node.right, ast.Name) and node.right.id == name


def _assert_validation_argv_contract(nb: dict[str, Any]) -> None:
    cells = _cells_by_id(nb)
    for cell_id, target in (
        ("pilot-launch-cell", "exec_cmd"),
        ("pilot-resume-cell", "resume_cmd"),
    ):
        elements = _assigned_list_elements(_src(cells[cell_id]), target)
        validation_indices = [
            index
            for index, node in enumerate(elements)
            if isinstance(node, ast.Constant) and node.value == "--validation-python"
        ]
        assert len(validation_indices) == 3, cell_id
        for index, expected in zip(
            validation_indices,
            (
                ("todo=", "TODO_PYTHON"),
                ("djangocms=", "DJANGO_PYTHON"),
                ("saleor=", "SALEOR_PYTHON"),
            ),
            strict=True,
        ):
            _assert_prefixed_name(elements[index + 1], *expected)
        timeout_indices = [
            index
            for index, node in enumerate(elements)
            if isinstance(node, ast.Constant) and node.value == "--validation-timeout"
        ]
        assert len(timeout_indices) == 1, cell_id
        _assert_string(elements[timeout_indices[0] + 1], "1800")
        hf_indices = [
            index
            for index, node in enumerate(elements)
            if isinstance(node, ast.Constant) and node.value == "--hf-repo-id"
        ]
        assert len(hf_indices) == 1, cell_id
        assert timeout_indices[0] < hf_indices[0], cell_id
        scientific_timeout_indices = [
            index
            for index, node in enumerate(elements)
            if isinstance(node, ast.Constant) and node.value == "--timeout"
        ]
        assert len(scientific_timeout_indices) == 1, cell_id
        _assert_string(elements[scientific_timeout_indices[0] + 1], "600")


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

    def test_list_backed_code_cell_sources_preserve_newlines(self) -> None:
        for cell in _code_cells(_nb()):
            source = cell["source"]
            if not isinstance(source, list):
                continue
            for index, element in enumerate(source[:-1]):
                assert element.endswith("\n"), (
                    f"code cell {cell.get('id')} source element {index} lacks a newline"
                )


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

    def test_pgdg_no_shell_string_construction(self) -> None:
        """PGDG-CONTRACT: PGDG path must use no bash -c / sh -c / gpg pipeline."""
        src = self._src("service-bootstrap-cell")
        full_pgdg = src[src.index("_ensure_pgdg_prerequisites"):src.index("def _psql")]
        code_lines = [
            ln for ln in full_pgdg.splitlines()
            if ln.strip() and not ln.strip().startswith("#") and not ln.strip().startswith('"""')
        ]
        code_text = "\n".join(code_lines)
        assert '"bash", "-c"' not in code_text
        assert '"sh", "-c"' not in code_text
        assert "gpg --dearmor" not in code_text
        assert "echo 'deb" not in code_text

    def test_pgdg_uses_deb822_sources_format(self) -> None:
        """PGDG-CONTRACT: PGDG path uses Deb822 .sources, not legacy .list."""
        src = self._src("service-bootstrap-cell")
        assert "pgdg.sources" in src
        assert "Types: deb" in src
        assert "Signed-By:" in src
        assert "Path.write_text" in src

    def test_pgdg_uses_official_https_repo_url(self) -> None:
        """PGDG-CONTRACT: official HTTPS PGDG repo URL."""
        src = self._src("service-bootstrap-cell")
        assert "https://apt.postgresql.org/pub/repos/apt" in src
        assert "https://www.postgresql.org/media/keys/ACCC4CF8.asc" in src

    def test_pgdg_codename_safety(self) -> None:
        """PGDG-CONTRACT: no silent jammy fallback; fail on missing/unsafe."""
        src = self._src("service-bootstrap-cell")
        assert "VERSION_CODENAME not found" in src
        assert "unsafe characters" in src
        assert "OS_RELEASE_PATH" in src


class TestRepoPreflight:
    def test_all_three_repos_preflight_no_model_call(self) -> None:
        preflight = _src(_cells_by_id(_nb())["pilot-repo-preflight-cell"])
        for repo in ("todo", "djangocms", "saleor"):
            assert repo in preflight
        assert "no model call" in preflight or "no model" in preflight

    def test_preflight_wires_baseline_flake_profile_fail_closed(self) -> None:
        """v0.9.20 Task F: the preflight cell must arm the bundled exact-nodeid
        baseline-flake profile when the bundle carries it and stay strictly
        fail-closed when it does not (both modes fail closed; the profile only
        widens tolerance to exactly the evidenced nodeid set)."""
        preflight = _src(_cells_by_id(_nb())["pilot-repo-preflight-cell"])
        assert 'BASELINE_PROFILE_PATH = CODE_DIR / "reports" / ' in preflight
        assert '"pilot_saleor_baseline_flaky_profile.json"' in preflight
        assert "if BASELINE_PROFILE_PATH.is_file():" in preflight
        assert 'preflight_cmd += ["--baseline-profile", str(BASELINE_PROFILE_PATH)]' in preflight
        # The no-profile branch must be explicit, not an accidental fall-through.
        assert "else:" in preflight
        assert "strict fail-closed validation" in preflight

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

    def test_model_preflight_gated_on_repo_preflight_evidence(self) -> None:
        repo_preflight = _src(_cells_by_id(_nb())["pilot-repo-preflight-cell"])
        model_preflight = _src(_cells_by_id(_nb())["model-preflight-cell"])
        assert "PREFLIGHT_JSON" in repo_preflight
        assert "repo_preflight_json_path=str(PREFLIGHT_JSON)" in model_preflight, (
            "the model preflight must consume the repo-preflight evidence file so "
            "a FAILED repo preflight can never be followed by a model load"
        )


class TestRepoPreflightCellExecutable:
    """PILOT-EXEC-01 D3/D4: the repo-preflight cell must be a GENUINE
    executable gate, not an accidental no-op.

    The historical defect serialized cell 8's source as a list with ZERO
    newlines, so ``"".join(source)`` produced a single line starting with ``#``
    (a comment) and the whole GQA microprobe + repository preflight was skipped.
    These tests prove (1) the canonical source re-joins to executable Python and
    (2) the AST contains real executable microprobe / fail-closed / ``_run_tee``
    nodes — string/comment-only matches are explicitly insufficient because
    comments never appear as AST nodes.
    """

    def _preflight_src(self) -> str:
        return _src(_cells_by_id(_nb())["pilot-repo-preflight-cell"])

    def test_canonical_cell8_source_joins_and_compiles(self) -> None:
        src = self._preflight_src()
        assert "\n" in src, "cell 8 source must be newline-preserving"
        # compile("".join(source)) must succeed (raises SyntaxError on failure).
        compile("".join(_cells_by_id(_nb())["pilot-repo-preflight-cell"]["source"]),
                "<pilot-repo-preflight-cell>", "exec")

    def test_ast_has_executable_microprobe_call(self) -> None:
        tree = ast.parse(self._preflight_src())
        microprobe_calls = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and (
                (isinstance(n.func, ast.Attribute)
                 and n.func.attr == "probe_sdpa_gqa_kernel_compatibility")
                or (isinstance(n.func, ast.Name)
                    and n.func.id == "probe_sdpa_gqa_kernel_compatibility")
            )
        ]
        # A real call site is REQUIRED; a comment mentioning the name does not
        # produce an AST Call node, so this cannot be satisfied accidentally.
        assert microprobe_calls, "no executable probe_sdpa_gqa_kernel_compatibility() call"

    def test_ast_has_fail_closed_raise_branch(self) -> None:
        tree = ast.parse(self._preflight_src())

        def _contains_raise_with(node: Any, needles: tuple[str, ...]) -> bool:
            if isinstance(node, ast.Raise):
                assert node.exc is not None
                src = ast.get_source_segment(self._preflight_src(), node.exc) or ""
                return any(nd in src for nd in needles)
            return any(
                _contains_raise_with(child, needles)
                for child in ast.iter_child_nodes(node)
            )

        assert _contains_raise_with(tree, ("MICROPROBE FAILED", "all_passed")), (
            "missing executable fail-closed raise gated on the microprobe"
        )
        assert _contains_raise_with(tree, ("PILOT REPO PREFLIGHT FAILED",)), (
            "missing executable fail-closed raise for the repo preflight"
        )

    def test_ast_has_executable_run_tee_call(self) -> None:
        tree = ast.parse(self._preflight_src())
        run_tee_calls = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "_run_tee"
        ]
        assert run_tee_calls, "no executable _run_tee(...) call"

    def test_run_tee_enforces_deadline_while_running(self) -> None:
        """D4: the _run_tee body must enforce the deadline while the child is
        running (not only after EOF), and terminate/kill on timeout."""
        src = self._preflight_src()
        # The deadline is computed from a monotonic clock and the reader loop
        # checks it while the process is still alive.
        assert "_time.monotonic()" in src
        assert "deadline" in src
        assert "proc.terminate()" in src
        assert "proc.kill()" in src
        assert "timed out" in src


class TestNoEncodingMojibake:
    """PILOT-EXEC-01 D5: reject the em-dash mojibake ``â€"`` in canonical and
    bundled notebook sources. The branch corrupted valid em dashes (U+2014) into
    the mojibake sequence U+00E2 U+20AC U+201D in several cells; these must be
    absent and proper em dashes present."""

    MOJIBAKE = "\u00e2\u20ac\u201d"
    EM_DASH = "\u2014"

    def _walk_strings(self, obj: Any) -> list[str]:
        out: list[str] = []
        if isinstance(obj, dict):
            for v in obj.values():
                out.extend(self._walk_strings(v))
        elif isinstance(obj, list):
            for x in obj:
                out.extend(self._walk_strings(x))
        elif isinstance(obj, str):
            out.append(obj)
        return out

    def test_canonical_notebook_has_no_mojibake(self) -> None:
        nb = _nb()
        strings = self._walk_strings(nb)
        assert not any(self.MOJIBAKE in s for s in strings), (
            "canonical notebook contains em-dash mojibake"
        )
        # The restored em dashes must be present (they are real, not deleted).
        assert any(self.EM_DASH in s for s in strings), (
            "expected restored em dashes in the canonical notebook"
        )

    def test_canonical_code_cells_contain_no_mojibake(self) -> None:
        for cell in _code_cells(_nb()):
            assert self.MOJIBAKE not in _src(cell), (
                f"code cell {cell.get('id')} contains em-dash mojibake"
            )

    def test_bundled_notebook_contains_no_mojibake(self, tmp_path: Path) -> None:
        spec = importlib.util.spec_from_file_location(
            "build_pilot_upload_bundle_no_mojibake",
            str(SCRIPTS_DIR / "build_pilot_upload_bundle.py"),
        )
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        output_root = tmp_path / "bundle-no-mojibake"
        archive = tmp_path / "bundle-no-mojibake.zip"
        mod.build_pilot_bundle(
            output_root=output_root,
            archive_path=archive,
            source_commit="a" * 40,
            source_tag="v0.9.3-pilot-exec-ready",
            created_utc="2026-08-10T00:00:00+00:00",
            validate_notebook_trust=False,
        )
        bundled = output_root / "notebooks" / "pilot_exec_01.ipynb"
        bundled_nb = json.loads(bundled.read_text(encoding="utf-8"))
        strings = self._walk_strings(bundled_nb)
        assert not any(self.MOJIBAKE in s for s in strings), (
            "bundled notebook contains em-dash mojibake"
        )


def _load_run_tee() -> Any:
    """Extract the canonical cell-8 ``_run_tee`` function and load it as a real
    callable against real stdlib subprocess/threading, so its timeout and
    fail-closed behavior can be exercised with genuine child processes."""
    src = _src(_cells_by_id(_nb())["pilot-repo-preflight-cell"])
    tree = ast.parse(src)
    func_node = next(
        (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_run_tee"),
        None,
    )
    assert func_node is not None, "_run_tee not defined in the repo-preflight cell"
    func_src = ast.get_source_segment(src, func_node) or ""
    ns: dict[str, Any] = {
        "subprocess": __import__("subprocess"),
        "sys": __import__("sys"),
    }
    exec(compile(func_src, "<pilot-run-tee>", "exec"), ns)
    return ns["_run_tee"]


class TestRunTeeSubprocessBehavior:
    """D4: the cell-8 ``_run_tee`` must enforce its deadline WHILE the child is
    still running and fail-closed (terminate -> kill -> reap, close the console
    handle, raise with the command and a bounded tail). These run against real
    subprocesses, not a fake runner, so a regression that only enforced the
    timeout after EOF would fail."""

    def test_returns_captured_output_on_success(self, tmp_path: Path) -> None:
        run_tee = _load_run_tee()
        console = tmp_path / "console.log"
        result = run_tee(
            [sys.executable, "-c", "print('hello-from-child')"],
            timeout=30,
            console_path=str(console),
        )
        assert result.stdout.strip() == "hello-from-child"
        assert result.returncode == 0
        assert "hello-from-child" in console.read_text(encoding="utf-8", errors="replace")

    def test_raises_on_nonzero_exit(self) -> None:
        run_tee = _load_run_tee()
        with pytest.raises(RuntimeError, match="command failed \\(exit="):
            run_tee([sys.executable, "-c", "import sys; sys.exit(3)"], timeout=30)

    def test_enforces_deadline_while_child_still_running(self) -> None:
        """A child that sleeps 60s with a 1s timeout must raise after ~1s, far
        before the child could complete naturally — proving the deadline is
        checked while the process is alive, not only after EOF."""
        run_tee = _load_run_tee()
        started = _time.monotonic()
        with pytest.raises(RuntimeError, match="timed out") as excinfo:
            run_tee(
                [sys.executable, "-c", "import time; time.sleep(60)"],
                timeout=1,
            )
        elapsed = _time.monotonic() - started
        assert elapsed < 10, f"deadline not enforced while running (elapsed={elapsed:.1f}s)"
        msg = str(excinfo.value)
        assert "timed out after 1s" in msg
        assert "import time; time.sleep(60)" in msg or "sleep(60)" in msg

    def test_timeout_message_contains_bounded_tail(self) -> None:
        run_tee = _load_run_tee()
        with pytest.raises(RuntimeError) as excinfo:
            run_tee(
                [sys.executable, "-c", "import time; print('START'); time.sleep(60)"],
                timeout=1,
            )
        msg = str(excinfo.value)
        # The child's output must appear in the message but the message stays
        # bounded to a tail window (never an unbounded full capture).
        assert "START" in msg
        assert len(msg) < 10_000


class TestRepoPreflightTimeoutAndOrdering:
    """D4/D3: the repo-preflight cell keeps its preflight-before-anything-scary
    ordering and the shared fail-closed runner."""

    def test_repo_preflight_present_and_before_gpu_verify(self) -> None:
        def _index(cell_id: str) -> int:
            return [c.get("id", "") for c in _nb()["cells"]].index(cell_id)

        assert _index("pilot-repo-preflight-cell") < _index("gpu-verify-cell")


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

        bundled_nb = json.loads(bundled.read_text(encoding="utf-8"))
        for cell in _code_cells(bundled_nb):
            source = cell["source"]
            if not isinstance(source, list):
                continue
            for index, element in enumerate(source[:-1]):
                assert element.endswith("\n"), (
                    f"bundled code cell {cell.get('id')} source element {index} lacks a newline"
                )
        _assert_validation_argv_contract(bundled_nb)


def _load_bundle_builder() -> Any:
    spec = importlib.util.spec_from_file_location(
        "build_pilot_upload_bundle_d8",
        str(SCRIPTS_DIR / "build_pilot_upload_bundle.py"),
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _get_call_literals(tree: ast.AST) -> list[str]:
    """First-argument string literals of every method call in the AST."""
    out: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        args = node.args
        if not args or not isinstance(args[0], ast.Constant):
            continue
        if isinstance(args[0].value, str):
            out.append(args[0].value)
    return out


class TestPilotDryrunCellSchema:
    """PILOT-EXEC-01 D8.2/D8.6: the dryrun-cell MUST delegate verification to
    the canonical ``benchmark.execution.preflight.validate_pilot_dryrun_evidence``
    and MUST NOT read the fabricated top-level ``total_tokens`` key (the
    pre-D8 false-green shape). Proof is AST-driven: a comment mentioning the
    name produces no Import/Call node."""

    def _src(self) -> str:
        return _src(_cells_by_id(_nb())["dryrun-cell"])

    def _tree(self) -> ast.Module:
        return ast.parse(self._src())

    def test_imports_canonical_validator(self) -> None:
        tree = self._tree()
        imports = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.ImportFrom)
            and n.module in ("benchmark.execution.preflight",)
            and any(
                alias.name == "validate_pilot_dryrun_evidence"
                for alias in n.names
            )
        ]
        assert imports, (
            "dryrun-cell must import validate_pilot_dryrun_evidence from "
            "benchmark.execution.preflight"
        )

    def test_calls_canonical_validator(self) -> None:
        tree = self._tree()
        calls = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and (
                (isinstance(n.func, ast.Name)
                 and n.func.id == "validate_pilot_dryrun_evidence")
                or (isinstance(n.func, ast.Attribute)
                    and n.func.attr == "validate_pilot_dryrun_evidence")
            )
        ]
        assert calls, "no executable validate_pilot_dryrun_evidence(...) call"

    def test_never_reads_top_level_total_tokens(self) -> None:
        """The cell must never read a per-record top-level ``total_tokens`` key.
        The ONLY ``['total_tokens']`` subscripts allowed are the canonical
        validator's summary aggregate (``dryrun_summary['total_tokens']``),
        printed for truthful evidence display."""
        src = self._src()
        tree = self._tree()
        get_literals = _get_call_literals(tree)
        assert "total_tokens" not in get_literals, (
            "dryrun-cell still reads top-level total_tokens via .get() "
            "(pre-D8 false-green shape)"
        )
        subscripts = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Subscript)
            and isinstance(n.slice, ast.Constant)
            and n.slice.value == "total_tokens"
        ]
        for node in subscripts:
            receiver = ast.get_source_segment(src, node.value) or ""
            assert receiver in ("dryrun_summary", "summary"), (
                f"top-level total_tokens must only be read from the validator "
                f"summary, got receiver {receiver!r}"
            )

    def test_prints_truthful_summary_after_validation(self) -> None:
        """The cell must print the validated summary (counts + zero tokens +
        source identity), never a hand-rolled verdict."""
        src = self._src()
        assert "validate_pilot_dryrun_evidence(" in src
        for needle in ("record_count", "unique_run_ids", "repo_counts",
                       "strategy_counts", "rep_counts", "model_calls",
                       "total_tokens", "total_workflow_tokens",
                       "source_commit", "deployed_build_id"):
            assert needle in src, f"truthful summary must print {needle!r}"

    def test_bundled_dryrun_cell_matches_canonical(self, tmp_path: Path) -> None:
        mod = _load_bundle_builder()
        output_root = tmp_path / "bundle-dryrun-schema"
        archive = tmp_path / "bundle-dryrun-schema.zip"
        mod.build_pilot_bundle(
            output_root=output_root,
            archive_path=archive,
            source_commit="a" * 40,
            source_tag="v0.9.3-pilot-exec-ready",
            created_utc="2026-08-10T00:00:00+00:00",
            validate_notebook_trust=False,
        )
        bundled = output_root / "notebooks" / "pilot_exec_01.ipynb"
        bundled_nb = json.loads(bundled.read_text(encoding="utf-8"))
        bundled_src = _src(_cells_by_id(bundled_nb)["dryrun-cell"])
        tree = ast.parse(bundled_src)
        assert any(
            isinstance(n, ast.ImportFrom)
            and n.module == "benchmark.execution.preflight"
            and any(a.name == "validate_pilot_dryrun_evidence" for a in n.names)
            for n in ast.walk(tree)
        ), "bundled dryrun-cell lost the canonical validator import"
        assert any(
            isinstance(n, ast.Call)
            and (
                (isinstance(n.func, ast.Name)
                 and n.func.id == "validate_pilot_dryrun_evidence")
                or (isinstance(n.func, ast.Attribute)
                    and n.func.attr == "validate_pilot_dryrun_evidence")
            )
            for n in ast.walk(tree)
        ), "bundled dryrun-cell lost the canonical validator call"
        assert "total_tokens" not in _get_call_literals(tree), (
            "bundled dryrun-cell still reads top-level total_tokens"
        )


class TestGqaPerDeviceEvidenceDisplay:
    """PILOT-EXEC-01 D8.3/D8.6: the repo-preflight cell must display the SDPA
    GQA microprobe per visible device using the REAL per-device evidence
    (``passed``/``gpu_name``/``compute_capability``/``before_heads``/
    ``after_heads``/``q_device``/``k_device``/``v_device``/``output_device``/
    ``output_shape``/``error``), NOT the fabricated ``available`` key."""

    REQUIRED_DEVICE_FIELDS = (
        "device_index", "device", "passed", "gpu_name", "compute_capability",
        "before_heads", "after_heads", "q_device", "k_device", "v_device",
        "output_device", "output_shape", "error",
    )

    def _preflight_src(self) -> str:
        return _src(_cells_by_id(_nb())["pilot-repo-preflight-cell"])

    def test_per_device_display_reads_real_fields(self) -> None:
        tree = ast.parse(self._preflight_src())
        get_literals = _get_call_literals(tree)
        for field in self.REQUIRED_DEVICE_FIELDS:
            assert field in get_literals, (
                f"GQA per-device display must read {field!r}"
            )
        assert "available" not in get_literals, (
            "GQA per-device display must NOT read the fabricated 'available' key"
        )

    def test_per_device_loop_shape(self) -> None:
        """The per-device loop must iterate ``gqa_probe.get('devices', [])`` and
        print a per-device line (device index/name + passed)."""
        src = self._preflight_src()
        assert ".get(\"devices\", [])" in src or ".get('devices', [])" in src
        assert "device_index" in src
        assert "passed=" in src
        assert "output_shape" in src

    def test_bundled_gqa_display_matches_canonical(self, tmp_path: Path) -> None:
        mod = _load_bundle_builder()
        output_root = tmp_path / "bundle-gqa-display"
        archive = tmp_path / "bundle-gqa-display.zip"
        mod.build_pilot_bundle(
            output_root=output_root,
            archive_path=archive,
            source_commit="a" * 40,
            source_tag="v0.9.3-pilot-exec-ready",
            created_utc="2026-08-10T00:00:00+00:00",
            validate_notebook_trust=False,
        )
        bundled = output_root / "notebooks" / "pilot_exec_01.ipynb"
        bundled_nb = json.loads(bundled.read_text(encoding="utf-8"))
        bundled_src = _src(_cells_by_id(bundled_nb)["pilot-repo-preflight-cell"])
        get_literals = _get_call_literals(ast.parse(bundled_src))
        for field in self.REQUIRED_DEVICE_FIELDS:
            assert field in get_literals, (
                f"bundled GQA per-device display must read {field!r}"
            )
        assert "available" not in get_literals


class TestPilotDryrunEvidenceValidatorIntegration:
    """PILOT-EXEC-01 D8.5: run the REAL CLI dry-run and require the canonical
    dry-run evidence validator to pass on the real artifact (never a fixture),
    proving 48/48 cells, exact source identity, and zero model calls/tokens."""

    SOURCE_COMMIT = "3ebc75dad2f47c8985ce045bcdc8907ce2d52f3c"
    SOURCE_TAG = "v0.9.22-pilot-exec-ready"
    BUILT_ID = "d8-validator-integration"

    def _run_cli(self, script: Path, dryrun_dir: Path, data_dir: Path) -> None:
        result = subprocess.run(
            [
                sys.executable, "-u", str(script),
                "--dry-run",
                "--profile", "pilot",
                "--protocol-version", "1.0",
                "--max-attempts", "3",
                "--max-completion-tokens-per-call", "4096",
                "--max-total-workflow-tokens", "0",
                "--timeout", "600",
                "--source-commit", self.SOURCE_COMMIT,
                "--source-tag", self.SOURCE_TAG,
                "--deployed-build-id", self.BUILT_ID,
                "--data-dir", str(data_dir),
                "--qwen-quantization", "bnb-nf4",
                "--output-dir", str(dryrun_dir),
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_DIR),
            errors="replace",
        )
        assert result.returncode == 0, (
            f"CLI dry-run failed:\nSTDOUT:\n{result.stdout[-2000:]}\n"
            f"STDERR:\n{result.stderr[-2000:]}"
        )

    def _assert_validator_pass(self, dryrun_dir: Path) -> None:
        from benchmark.execution.preflight import validate_pilot_dryrun_evidence
        summary = validate_pilot_dryrun_evidence(
            dryrun_dir=dryrun_dir,
            expected_source_commit=self.SOURCE_COMMIT,
            expected_source_tag=self.SOURCE_TAG,
            expected_deployed_build_id=self.BUILT_ID,
            expected_model_identity="dry-run:mock",
        )
        assert summary["passed"] is True
        assert summary["record_count"] == 48
        assert summary["unique_run_ids"] == 48
        assert summary["repo_counts"] == {"todo": 16, "djangocms": 16, "saleor": 16}
        assert summary["strategy_counts"] == {
            "iterative_repository_agent": 24,
            "selective": 24,
        }
        assert summary["rep_counts"] == {1: 24, 2: 24}
        assert summary["model_calls"] == 0
        assert summary["prompt_tokens"] == 0
        assert summary["completion_tokens"] == 0
        assert summary["total_tokens"] == 0
        assert summary["total_workflow_model_calls"] == 0
        assert summary["total_workflow_tokens"] == 0
        assert summary["source_commit"] == self.SOURCE_COMMIT
        assert summary["source_tag"] == self.SOURCE_TAG
        assert summary["deployed_build_id"] == self.BUILT_ID
        assert summary["model_identity"] == "dry-run:mock"

    def test_real_cli_dryrun_passes_canonical_validator(self, tmp_path: Path) -> None:
        dryrun_dir = tmp_path / "dryrun"
        self._run_cli(
            PROJECT_DIR / "seven_arm_benchmark.py",
            dryrun_dir,
            PROJECT_DIR / "benchmark_data",
        )
        self._assert_validator_pass(dryrun_dir)

    def test_bundled_cli_dryrun_passes_canonical_validator(self, tmp_path: Path) -> None:
        mod = _load_bundle_builder()
        output_root = tmp_path / "bundle-validator"
        archive = tmp_path / "bundle-validator.zip"
        mod.build_pilot_bundle(
            output_root=output_root,
            archive_path=archive,
            source_commit="a" * 40,
            source_tag="v0.9.3-pilot-exec-ready",
            created_utc="2026-08-10T00:00:00+00:00",
            validate_notebook_trust=False,
        )
        script = output_root / "code" / "seven_arm_benchmark.py"
        data_dir = output_root / "data"
        dryrun_dir = tmp_path / "bundled-dryrun"
        self._run_cli(script, dryrun_dir, data_dir)
        self._assert_validator_pass(dryrun_dir)
