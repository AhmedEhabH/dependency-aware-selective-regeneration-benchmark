"""PILOT-EXEC-01: release source-provenance closure (v0.9.11 defect regression).

The v0.9.11 release tag peeled to commit ``8801304``, but the deployed notebook
(sha256 ``85edbd33...``) was re-frozen AFTER the tag at commit ``b87aa49``, so
the tag's notebook (``d15d8683...``) differed from the artifact Kaggle actually
ran. The embedded notebook trust could be made internally self-consistent
(identity derived from the bundled notebook's own frozen anchors passes), yet
the release was not a truthful snapshot of its declared source commit.

These tests lock in the fail-closed ``source_commit`` Git-tree provenance gate
added to ``build_pilot_upload_bundle.py``: the bundled Pilot notebook AND every
``code_manifest.json`` entry must equal the normalized tracked Git blob at the
declared source commit. No skip flag exists; the only way to pass is to be
source-faithful.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"
CANONICAL_NOTEBOOK = PROJECT_DIR / "notebooks" / "pilot_exec_01.ipynb"
TARGET_RELEASE_TAG = "v0.9.22-d13r1-candidate"

V0911_TAG_PEEL_COMMIT = "8801304d855fe29c694f2a3c0500f661685b0d72"
V0911_DEPLOYED_COMMIT = "b87aa49e766a7881e0f5d55c85ceb5594657db60"
V0911_TAG_NOTEBOOK_SHA = "d15d86831bf805e7bcc9e811eb87158b2e4f56732082d1e6326ee9d94ccb81ec"
V0911_DEPLOYED_NOTEBOOK_SHA = (
    "85edbd33e81bb05065c66a1630f75a02043df9fbd0a8f8091b3bff9712181ed0"
)

LOCK_FILES = ("requirements-pilot-kaggle.lock", "requirements-smoke-kaggle.lock")


def _load_module(module_name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_pilot_builder() -> Any:
    return _load_module(
        "build_pilot_upload_bundle_provenance_test",
        SCRIPTS_DIR / "build_pilot_upload_bundle.py",
    )


def _load_test_module(name: str) -> Any:
    return _load_module(
        f"{name}_release_provenance_import",
        PROJECT_DIR / "tests" / "integration" / f"{name}.py",
    )


def _git_text(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {args} failed: {result.stderr.strip()}")
    return result.stdout


def _git_bytes(args: list[str]) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {args} failed: {result.stderr.decode('utf-8', 'replace').strip()}")
    return result.stdout


def _head_sha() -> str:
    return _git_text(["rev-parse", "HEAD"]).strip()


def _blob_bytes(commit: str, rel_path: str) -> bytes:
    return _git_bytes(["show", f"{commit}:{rel_path}"])


def _ls_tree(commit: str, rel_path: str) -> list[tuple[str, str, str, str]]:
    out = _git_text(["ls-tree", "-r", commit, "--", rel_path])
    entries: list[tuple[str, str, str, str]] = []
    for line in out.splitlines():
        mode, typ, sha, name = line.split(None, 3)
        if typ == "blob":
            entries.append((mode, typ, sha, name))
    return entries


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def _code_manifest_from_commit(commit: str) -> dict[str, str]:
    """Reconstruct the LF-faithful bundle code manifest from a git tree.

    Mirrors the exact file set the Pilot bundle builder archives (historical
    CANONICAL_CODE_SOURCES plus the Pilot-specific lock and scripts) and hashes
    every tracked blob LF-normalized, matching the builder's text policy. This
    is the source-side expectation the provenance gate enforces.
    """
    hb = _load_module("build_upload_bundle_release_provenance", SCRIPTS_DIR / "build_upload_bundle.py")
    pilot_files = [
        PROJECT_DIR / "requirements-pilot-kaggle.lock",
        PROJECT_DIR / "scripts" / "pilot_repo_snapshot.py",
        PROJECT_DIR / "scripts" / "pilot_kaggle_repo_envs.py",
    ]
    manifest: dict[str, str] = {}
    for src in [*hb.CANONICAL_CODE_SOURCES, *pilot_files]:
        rel = src.resolve().relative_to(hb.PROJECT_ROOT.resolve()).as_posix()
        if src.resolve().is_dir():
            for _mode, _typ, _blob_sha, name in _ls_tree(commit, rel):
                if hb.should_exclude(Path(name).name):
                    continue
                manifest[name] = _sha256(_lf(_blob_bytes(commit, name)))
        else:
            entries = _ls_tree(commit, rel)
            assert len(entries) == 1, f"expected exactly one tracked blob for {rel}"
            manifest[rel] = _sha256(_lf(_blob_bytes(commit, rel)))
    return manifest


def _minimal_notebook(source_tag: str) -> bytes:
    source = (
        f'FROZEN_SOURCE_TAG = "{source_tag}"\n'
        "FROZEN_DEPLOYMENT = {\n"
        '    "task": "PILOT-EXEC-01",\n'
        "    \"expected_cells\": 48,\n"
        "}\n"
        "FROZEN_MANIFEST_HASHES = {\n"
        '    "code_manifest_sha256": "%s",\n'
        '    "data_manifest_sha256": "%s",\n'
        '    "repository_snapshot_manifest_sha256": "%s",\n'
        '    "kaggle_transport_path_map_sha256": "%s",\n'
        "}\n" % ("a" * 64, "b" * 64, "c" * 64, "d" * 64)
    )
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "id": "setup-cell",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": source.splitlines(keepends=True),
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(notebook).encode("utf-8")


def _write_bundle(
    tmp_path: Path,
    notebook_bytes: bytes,
    code_manifest: dict[str, str],
) -> Path:
    bundled_root = tmp_path / "bundle"
    notebooks_dir = bundled_root / "notebooks"
    notebooks_dir.mkdir(parents=True, exist_ok=True)
    (notebooks_dir / "pilot_exec_01.ipynb").write_bytes(notebook_bytes)
    (bundled_root / "code_manifest.json").write_text(
        json.dumps(code_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return bundled_root


def _load_finalizer() -> Any:
    return _load_module(
        "finalize_pilot_notebook_trust_release_provenance",
        SCRIPTS_DIR / "finalize_pilot_notebook_trust.py",
    )


def _hermetic_frozen_notebook(tmp_path: Path) -> Path:
    """Freeze a hermetic copy of the canonical notebook via the finalizer bridge.

    Under the hermetic repo-materialization stub the bundled repository snapshot
    differs from the real pinned trees, so the canonical anchors do not match a
    hermetic build. Freezing a copy first makes it self-consistent (the exact
    pattern the deployment-bundle Gate 4 tests use) and yields a notebook whose
    bytes legitimately differ from the tracked canonical blob - the v0.9.11
    defect class the acceptance gate must reject.
    """
    notebook = tmp_path / "bridge" / "pilot_exec_01.ipynb"
    notebook.parent.mkdir(parents=True, exist_ok=True)
    notebook.write_bytes(CANONICAL_NOTEBOOK.read_bytes())
    _load_finalizer().freeze(
        notebook_path=notebook,
        output_root=tmp_path / "bridge" / "pilot-kaggle-upload",
        archive_path=tmp_path / "bridge" / "pilot-kaggle-upload.zip",
        source_commit="a" * 40,
        source_tag=TARGET_RELEASE_TAG,
        created_utc="2026-08-16T12:00:00+00:00",
        repo_cache=None,
        allow_acquire=False,
        report_path=tmp_path / "bridge" / "report.json",
    )
    return notebook


class TestGate1ExactV0911ForensicRegression:
    """Gate 1: the exact v0.9.11 defect class must fail the provenance gate.

    Identity built from the bundled (deployed) notebook's own frozen anchors
    passes the embedded trust check, while the source-provenance gate must still
    reject the artifact because the tag's notebook differs.
    """

    def test_real_history_reproduces_the_defect(self, tmp_path: Path) -> None:
        tag_notebook = _blob_bytes(V0911_TAG_PEEL_COMMIT, "notebooks/pilot_exec_01.ipynb")
        deployed_notebook = _blob_bytes(V0911_DEPLOYED_COMMIT, "notebooks/pilot_exec_01.ipynb")
        assert _sha256(_lf(tag_notebook)) == V0911_TAG_NOTEBOOK_SHA
        assert _sha256(_lf(deployed_notebook)) == V0911_DEPLOYED_NOTEBOOK_SHA

        bundled_root = _write_bundle(
            tmp_path,
            deployed_notebook,
            _code_manifest_from_commit(V0911_TAG_PEEL_COMMIT),
        )
        builder = _load_pilot_builder()
        bundled_nb = bundled_root / "notebooks" / "pilot_exec_01.ipynb"

        frozen = builder.read_frozen_values(bundled_nb)
        identity = {
            "source_tag": frozen["FROZEN_SOURCE_TAG"],
            **frozen["FROZEN_DEPLOYMENT"],
            **frozen["FROZEN_MANIFEST_HASHES"],
        }
        assert builder.validate_bundled_notebook_trust(identity, bundled_nb) == []

        mismatches = builder.validate_source_commit_provenance(
            source_commit=V0911_TAG_PEEL_COMMIT,
            bundled_root=bundled_root,
        )
        assert mismatches, "source-provenance gate must fail for the exact v0.9.11 defect"
        assert any("notebook" in m for m in mismatches)
        assert all("code_manifest entry mismatch" not in m for m in mismatches)

    def test_synthetic_defect_class(self, tmp_path: Path) -> None:
        bundled_root = _write_bundle(
            tmp_path,
            _minimal_notebook("v0.9.11-pilot-exec-ready"),
            {},
        )
        builder = _load_pilot_builder()
        bundled_nb = bundled_root / "notebooks" / "pilot_exec_01.ipynb"

        frozen = builder.read_frozen_values(bundled_nb)
        identity = {
            "source_tag": frozen["FROZEN_SOURCE_TAG"],
            **frozen["FROZEN_DEPLOYMENT"],
            **frozen["FROZEN_MANIFEST_HASHES"],
        }
        assert builder.validate_bundled_notebook_trust(identity, bundled_nb) == []

        stale_source = _minimal_notebook("v0.9.10-pilot-exec-ready")

        def reader(_commit: str, _rel_path: str) -> bytes:
            return stale_source

        mismatches = builder.validate_source_commit_provenance(
            source_commit="a" * 40,
            bundled_root=bundled_root,
            git_reader=reader,
        )
        assert any("notebook" in m for m in mismatches)


class TestGate2NotebookSourceParity:
    """Gate 2: the bundled notebook must equal the normalized tracked blob."""

    def test_crlf_checkout_still_matches_lf_blob(self, tmp_path: Path) -> None:
        head = _head_sha()
        source = _blob_bytes(head, "notebooks/pilot_exec_01.ipynb")
        crlf_copy = source.replace(b"\n", b"\r\n")
        bundled_root = _write_bundle(tmp_path, crlf_copy, {})
        mismatches = _load_pilot_builder().validate_source_commit_provenance(
            source_commit=head,
            bundled_root=bundled_root,
        )
        assert mismatches == []

    def test_missing_bundled_notebook_fails(self, tmp_path: Path) -> None:
        bundled_root = tmp_path / "bundle"
        bundled_root.mkdir()
        (bundled_root / "code_manifest.json").write_text("{}\n", encoding="utf-8")
        mismatches = _load_pilot_builder().validate_source_commit_provenance(
            source_commit=_head_sha(),
            bundled_root=bundled_root,
        )
        assert any("notebook" in m for m in mismatches)


class TestGate3CodeManifestSourceParity:
    """Gate 3: every code_manifest.json entry must equal its source blob."""

    def test_all_matching_entries_pass(self, tmp_path: Path) -> None:
        head = _head_sha()
        bundled_root = _write_bundle(
            tmp_path,
            _blob_bytes(head, "notebooks/pilot_exec_01.ipynb"),
            _code_manifest_from_commit(head),
        )
        assert len(_code_manifest_from_commit(head)) >= 90
        mismatches = _load_pilot_builder().validate_source_commit_provenance(
            source_commit=head,
            bundled_root=bundled_root,
        )
        assert mismatches == []

    def test_modified_source_blob_fails_naming_the_path(self, tmp_path: Path) -> None:
        head = _head_sha()
        manifest = _code_manifest_from_commit(head)
        changed = sorted(manifest)[0]
        manifest[changed] = "0" * 64
        bundled_root = _write_bundle(
            tmp_path,
            _blob_bytes(head, "notebooks/pilot_exec_01.ipynb"),
            manifest,
        )
        mismatches = _load_pilot_builder().validate_source_commit_provenance(
            source_commit=head,
            bundled_root=bundled_root,
        )
        assert any(changed in m and "code_manifest entry mismatch" in m for m in mismatches)

    def test_missing_tracked_source_fails_naming_the_path(self, tmp_path: Path) -> None:
        head = _head_sha()
        manifest = _code_manifest_from_commit(head)
        missing = sorted(manifest)[0]
        bundled_root = _write_bundle(
            tmp_path,
            _blob_bytes(head, "notebooks/pilot_exec_01.ipynb"),
            manifest,
        )
        real = _blob_bytes

        def reader(commit: str, rel_path: str) -> bytes:
            if rel_path == missing:
                raise RuntimeError(f"fatal: path {rel_path!r} is not in the tree")
            return real(commit, rel_path)

        mismatches = _load_pilot_builder().validate_source_commit_provenance(
            source_commit=head,
            bundled_root=bundled_root,
            git_reader=reader,
        )
        assert any(missing in m and "not found in source tree" in m for m in mismatches)

    def test_lock_files_must_be_lf_faithful(self, tmp_path: Path) -> None:
        head = _head_sha()
        manifest = _code_manifest_from_commit(head)
        for rel in LOCK_FILES:
            assert rel in manifest
        lf_bundle = _write_bundle(
            tmp_path / "lf",
            _blob_bytes(head, "notebooks/pilot_exec_01.ipynb"),
            manifest,
        )
        assert _load_pilot_builder().validate_source_commit_provenance(
            source_commit=head,
            bundled_root=lf_bundle,
        ) == []

        crlf_manifest = dict(manifest)
        for rel in LOCK_FILES:
            crlf_manifest[rel] = _sha256(_blob_bytes(head, rel).replace(b"\n", b"\r\n"))
        crlf_bundle = _write_bundle(
            tmp_path / "crlf",
            _blob_bytes(head, "notebooks/pilot_exec_01.ipynb"),
            crlf_manifest,
        )
        mismatches = _load_pilot_builder().validate_source_commit_provenance(
            source_commit=head,
            bundled_root=crlf_bundle,
        )
        assert any(
            "code_manifest entry mismatch" in m and "requirements-pilot-kaggle.lock" in m
            for m in mismatches
        )

    def test_missing_code_manifest_fails(self, tmp_path: Path) -> None:
        bundled_root = tmp_path / "bundle"
        notebooks_dir = bundled_root / "notebooks"
        notebooks_dir.mkdir(parents=True)
        (notebooks_dir / "pilot_exec_01.ipynb").write_bytes(_minimal_notebook("v0.9.12-pilot-exec-ready"))
        mismatches = _load_pilot_builder().validate_source_commit_provenance(
            source_commit=_head_sha(),
            bundled_root=bundled_root,
        )
        assert any("code_manifest.json" in m for m in mismatches)


class TestGate4FailClosedSourceCommitValidation:
    """Gate 4: malformed or unavailable source commits fail without exceptions."""

    @pytest.mark.parametrize("bad", ["", "abc", "v0.9.12-pilot-exec-ready", "A" * 40])
    def test_invalid_source_commit_format_fails(self, tmp_path: Path, bad: str) -> None:
        bundled_root = _write_bundle(tmp_path, _minimal_notebook("v0.9.12-pilot-exec-ready"), {})
        mismatches = _load_pilot_builder().validate_source_commit_provenance(
            source_commit=bad,
            bundled_root=bundled_root,
        )
        assert mismatches, "well-formed check must fail closed for invalid source_commit"
        assert any("source_commit" in m and "SHA" in m for m in mismatches)

    def test_unknown_commit_fails_closed(self, tmp_path: Path) -> None:
        bundled_root = _write_bundle(
            tmp_path,
            _minimal_notebook("v0.9.12-pilot-exec-ready"),
            {"requirements-pilot-kaggle.lock": "0" * 64},
        )
        mismatches = _load_pilot_builder().validate_source_commit_provenance(
            source_commit="f" * 40,
            bundled_root=bundled_root,
        )
        assert mismatches, "unknown commit must fail closed via the git reader"
        assert any("notebook blob unavailable" in m for m in mismatches)

    def test_non_string_manifest_entry_fails(self, tmp_path: Path) -> None:
        bundled_root = _write_bundle(
            tmp_path,
            _minimal_notebook("v0.9.12-pilot-exec-ready"),
            {"requirements-pilot-kaggle.lock": 123},
        )
        mismatches = _load_pilot_builder().validate_source_commit_provenance(
            source_commit=_head_sha(),
            bundled_root=bundled_root,
        )
        assert any("must be a sha256 string" in m for m in mismatches)


class TestGate5ReleaseTagSequencingContract:
    """Gate 5: every frozen release constant names the same v0.9.14 target."""

    def test_all_release_constants_aligned(self) -> None:
        builder = _load_pilot_builder()
        frozen = builder.read_frozen_values(CANONICAL_NOTEBOOK)
        assert frozen["FROZEN_SOURCE_TAG"] == TARGET_RELEASE_TAG

        deployment = _load_test_module("test_pilot_deployment_bundle")
        contract = _load_test_module("test_pilot_notebook_contract")
        provisioning = _load_test_module("test_pilot_repo_env_provisioning")
        assert deployment.PILOT_SOURCE_TAG == TARGET_RELEASE_TAG
        assert contract.EXPECTED_FROZEN_SOURCE_TAG == TARGET_RELEASE_TAG
        assert provisioning.SOURCE_TAG == TARGET_RELEASE_TAG


class TestReleaseBuildProvenanceWiring:
    """Gate 6 (release acceptance wiring): the source-provenance gate must be
    enforced by validated release builds and by the finalizer's explicit
    acceptance flag, while the finalizer's internal validation rebuild stays a
    bridge self-check (fresh anchors predate any commit).

    ``build_pilot_bundle(validate_notebook_trust=True)`` defaults to verifying
    source provenance; the only way out is the explicit
    ``verify_source_provenance=False`` used by the finalizer's internal rebuild.
    """

    def _build(
        self,
        tmp_path: Path,
        label: str,
        notebook: Path,
        source_commit: str,
        *,
        verify_source_provenance: bool = True,
    ) -> dict[str, Any]:
        return _load_pilot_builder().build_pilot_bundle(
            output_root=tmp_path / f"bundle-{label}",
            archive_path=tmp_path / f"bundle-{label}.zip",
            source_commit=source_commit,
            source_tag=TARGET_RELEASE_TAG,
            created_utc="2026-08-16T12:00:00+00:00",
            repo_cache=None,
            allow_acquire=False,
            notebook=notebook,
            validate_notebook_trust=True,
            verify_source_provenance=verify_source_provenance,
        )

    def test_validated_build_rejects_refrozen_notebook_at_head(
        self, tmp_path: Path, hermetic_pilot_repo_materialize: Any
    ) -> None:
        """Exact v0.9.11 defect class: the deployed notebook differs from the
        tracked blob at the declared source commit -> the provenance gate must
        abort the release build even though embedded trust passes."""
        notebook = _hermetic_frozen_notebook(tmp_path)
        with pytest.raises(RuntimeError) as exc:
            self._build(tmp_path, "refrozen", notebook, _head_sha())
        assert "PILOT SOURCE-PROVENANCE GATE FAILED" in str(exc.value)

    def test_verify_source_provenance_false_disables_the_gate(
        self, tmp_path: Path, hermetic_pilot_repo_materialize: Any
    ) -> None:
        notebook = _hermetic_frozen_notebook(tmp_path)
        identity = self._build(
            tmp_path,
            "bridge-only",
            notebook,
            _head_sha(),
            verify_source_provenance=False,
        )
        assert identity["source_commit"] == _head_sha()

    def test_finalizer_acceptance_gate_fails_on_divergent_commit(
        self, tmp_path: Path, hermetic_pilot_repo_materialize: Any
    ) -> None:
        notebook = tmp_path / "acceptance-fail" / "pilot_exec_01.ipynb"
        notebook.parent.mkdir(parents=True, exist_ok=True)
        notebook.write_bytes(CANONICAL_NOTEBOOK.read_bytes())
        with pytest.raises(RuntimeError) as exc:
            _load_finalizer().freeze(
                notebook_path=notebook,
                output_root=tmp_path / "acceptance-fail" / "pilot-kaggle-upload",
                archive_path=tmp_path / "acceptance-fail" / "pilot-kaggle-upload.zip",
                source_commit=V0911_TAG_PEEL_COMMIT,
                source_tag=TARGET_RELEASE_TAG,
                created_utc="2026-08-16T12:00:00+00:00",
                repo_cache=None,
                allow_acquire=False,
                report_path=tmp_path / "acceptance-fail" / "report.json",
                verify_source_provenance=True,
            )
        assert "PILOT SOURCE-PROVENANCE GATE FAILED" in str(exc.value)

    def test_finalizer_acceptance_gate_runs_only_on_validation_rebuild(
        self, tmp_path: Path, hermetic_pilot_repo_materialize: Any, monkeypatch: Any
    ) -> None:
        builder = _load_finalizer().load_pilot_builder()
        calls: list[str] = []
        monkeypatch.setattr(
            builder,
            "validate_source_commit_provenance",
            lambda source_commit, bundled_root, **kwargs: (
                calls.append(str(source_commit)) or []
            ),
        )
        notebook = tmp_path / "acceptance-pass" / "pilot_exec_01.ipynb"
        notebook.parent.mkdir(parents=True, exist_ok=True)
        notebook.write_bytes(CANONICAL_NOTEBOOK.read_bytes())
        report = _load_finalizer().freeze(
            notebook_path=notebook,
            output_root=tmp_path / "acceptance-pass" / "pilot-kaggle-upload",
            archive_path=tmp_path / "acceptance-pass" / "pilot-kaggle-upload.zip",
            source_commit="a" * 40,
            source_tag=TARGET_RELEASE_TAG,
            created_utc="2026-08-16T12:00:00+00:00",
            repo_cache=None,
            allow_acquire=False,
            report_path=tmp_path / "acceptance-pass" / "report.json",
            verify_source_provenance=True,
        )
        assert report["status"] == "FROZEN"
        assert calls == ["a" * 40], (
            "source provenance must run exactly once: on the validation-enabled "
            "rebuild, never on the discovery pass and never twice"
        )

    def test_finalizer_cli_exposes_verify_source_provenance_flag(
        self, monkeypatch: Any
    ) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "finalize_pilot_notebook_trust",
                "--notebook", str(CANONICAL_NOTEBOOK),
                "--output-root", "out",
                "--archive-path", "out.zip",
                "--source-commit", "a" * 40,
                "--source-tag", TARGET_RELEASE_TAG,
                "--created-utc", "2026-08-16T12:00:00+00:00",
                "--report", "report.json",
                "--verify-source-provenance",
            ],
        )
        args = _load_finalizer().parse_args()
        assert args.verify_source_provenance is True
