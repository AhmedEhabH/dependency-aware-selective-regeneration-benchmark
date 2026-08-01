"""R6 deterministic builder tests.

No network, no Git, no Django. All tests use tmp_path fixtures and
monkeypatched module roots / canonical source lists.
"""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def _load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_upload_bundle_under_test",
        str(
            Path(__file__).resolve().parent.parent.parent
            / "scripts"
            / "build_upload_bundle.py"
        ),
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


builder = _load_builder()

EVALUATOR_ASSET_RELATIVE_PATHS = (
    "tests/evaluator_assets/todo_smoke_001_checks.py",
    "tests/evaluator_assets/todo_smoke_001_checks.py.sha256",
    "tests/evaluator_assets/todo_smoke_002_checks.py",
    "tests/evaluator_assets/todo_smoke_002_checks.py.sha256",
    "tests/evaluator_assets/todo_smoke_003_checks.py",
    "tests/evaluator_assets/todo_smoke_003_checks.py.sha256",
)


def _write_text(path: Path, content: str, crlf: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = content
    if crlf:
        data = content.replace("\n", "\r\n")
    path.write_bytes(data.encode("utf-8"))


def _patch_builder(monkeypatch, project: Path, kaggle: Path) -> None:
    monkeypatch.setattr(builder, "PROJECT_ROOT", project)
    monkeypatch.setattr(builder, "KAGGLE_UPLOAD", kaggle)
    monkeypatch.setattr(builder, "KAGGLE_CODE", kaggle / "code")
    monkeypatch.setattr(builder, "KAGGLE_DATA", kaggle / "data")
    monkeypatch.setattr(builder, "KAGGLE_NOTEBOOKS", kaggle / "notebooks")
    monkeypatch.setattr(
        builder,
        "CANONICAL_CODE_SOURCES",
        [
            project / "seven_arm_benchmark.py",
            project / "src" / "benchmark",
            project / "configs",
            project / "requirements-kaggle.txt",
            project / "requirements-smoke-kaggle.lock",
            project / "pyproject.toml",
            *(project / rel for rel in EVALUATOR_ASSET_RELATIVE_PATHS),
        ],
    )
    monkeypatch.setattr(
        builder,
        "CANONICAL_DATA_SOURCES",
        [
            project / "benchmark_data" / "manifests",
            project / "benchmark_data" / "repository_profiles",
            project / "benchmark_data" / "repositories",
            project / "benchmark_data" / "scenarios",
        ],
    )
    monkeypatch.setattr(
        builder,
        "CANONICAL_NOTEBOOK_SOURCES",
        [project / "notebooks" / "seven_arm_benchmark.ipynb"],
    )


def _install(tmp_path, monkeypatch):
    project = tmp_path / "project"
    for i, rel in enumerate(EVALUATOR_ASSET_RELATIVE_PATHS):
        p = project / rel
        if rel.endswith(".py"):
            _write_text(p, f"EVALUATOR_{i}\n", crlf=(i % 2 == 0))
        else:
            _write_text(p, f"fingerprint_{i}\n", crlf=True)

    _write_text(project / "seven_arm_benchmark.py", "print('main')\n", crlf=True)
    _write_text(project / "requirements-kaggle.txt", "numpy\n", crlf=True)
    _write_text(project / "requirements-smoke-kaggle.lock", "Django==5.2.16\n", crlf=True)
    _write_text(project / "pyproject.toml", "[project]\n", crlf=False)
    _write_text(project / "configs/smoke.yaml", "profile: v2\n", crlf=True)
    _write_text(project / "src/benchmark/core.py", "VALUE = 1\n", crlf=True)
    _write_text(project / "src/benchmark/models.py", "class M:\n    pass\n", crlf=False)
    pycache = project / "src/benchmark/__pycache__"
    pycache.mkdir(parents=True)
    (pycache / "core.cpython-311.pyc").write_bytes(b"\x00\x0d\x0a\xff")
    _write_text(project / "configs/.env", "SECRET=value\n", crlf=False)

    _write_text(project / "benchmark_data/manifests/repositories.yaml", "repos:\n", crlf=True)
    _write_text(project / "benchmark_data/repository_profiles/todo.yaml", "profile:\n", crlf=True)
    _write_text(project / "benchmark_data/scenarios/todo-smoke-001.yaml", "scenario:\n", crlf=True)
    _write_text(
        project / "benchmark_data/repositories/todo/todo/models.py",
        "from django.db import models\n",
        crlf=True,
    )
    _write_text(
        project / "benchmark_data/repositories/todo/todo/tests/test_example.py",
        "def test_x():\n    pass\n",
        crlf=True,
    )
    _write_text(
        project / "benchmark_data/repositories/todo/db.sqlite3",
        "SQLITE_DB_PLACEHOLDER\n",
    )
    _write_text(
        project / "notebooks/seven_arm_benchmark.ipynb",
        '{"cells": [], "metadata": {}}\n',
        crlf=True,
    )
    _write_text(
        project / "tests/support/scripted_llm_backend.py",
        "PROHIBITED = True\n",
        crlf=False,
    )

    kaggle = tmp_path / "kaggle_upload"
    _patch_builder(monkeypatch, project, kaggle)
    return project, kaggle


def _snapshot(directory: Path) -> dict[str, bytes]:
    return {
        p.relative_to(directory).as_posix(): p.read_bytes()
        for p in sorted(directory.rglob("*"))
        if p.is_file()
    }


def test_r6_text_suffix_contract():
    expected = frozenset(
        {
            ".py",
            ".pyw",
            ".toml",
            ".txt",
            ".yaml",
            ".yml",
            ".md",
            ".cfg",
            ".ini",
            ".ipynb",
            ".sha256",
        }
    )
    assert expected == builder.TEXT_SUFFIXES
    assert ".json" not in builder.TEXT_SUFFIXES
    assert ".sqlite3" not in builder.TEXT_SUFFIXES


def test_r6_normalize_text_converts_all_supported_text_to_lf(tmp_path):
    for suffix in builder.TEXT_SUFFIXES:
        p = tmp_path / f"sample{suffix}"
        p.write_bytes(b"line1\r\nline2\r\n")
        builder.normalize_text(p)
        assert p.read_bytes() == b"line1\nline2\n", suffix


def test_r6_normalize_text_preserves_binary_bytes(tmp_path):
    p = tmp_path / "sample.bin"
    payload = b"\x00\x0d\x0a\xff\r\nX\x00\x0d"
    p.write_bytes(payload)
    builder.normalize_text(p)
    assert p.read_bytes() == payload


def test_r6_manifest_keys_are_posix(tmp_path, monkeypatch):
    _project, kaggle = _install(tmp_path, monkeypatch)
    err = builder.build_bundle()
    assert err == 0
    for name in ("code_manifest.json", "data_manifest.json", "notebook_manifest.json"):
        manifest = json.loads((kaggle / name).read_text(encoding="utf-8"))
        assert manifest, name
        for key in manifest:
            assert "\\" not in key, name


def test_r6_nested_repository_tests_are_preserved(tmp_path, monkeypatch):
    _project, kaggle = _install(tmp_path, monkeypatch)
    err = builder.build_bundle()
    assert err == 0
    bundled = (
        kaggle / "data" / "repositories" / "todo" / "todo" / "tests" / "test_example.py"
    )
    assert bundled.is_file()


def test_r6_evaluator_allowlist_is_exact(tmp_path, monkeypatch):
    assert builder.EVALUATOR_ASSET_RELATIVE_PATHS == EVALUATOR_ASSET_RELATIVE_PATHS
    assert len(builder.EVALUATOR_ASSET_RELATIVE_PATHS) == 6
    _project, kaggle = _install(tmp_path, monkeypatch)
    err = builder.build_bundle()
    assert err == 0
    for rel in EVALUATOR_ASSET_RELATIVE_PATHS:
        assert (kaggle / "code" / rel).is_file(), rel


def test_r6_project_test_support_is_not_deployed(tmp_path, monkeypatch):
    _project, kaggle = _install(tmp_path, monkeypatch)
    err = builder.build_bundle()
    assert err == 0
    assert not (kaggle / "code" / "tests" / "support").exists()


def test_r6_manifests_match_raw_emitted_bytes(tmp_path, monkeypatch):
    _project, kaggle = _install(tmp_path, monkeypatch)
    err = builder.build_bundle()
    assert err == 0
    for name in ("code_manifest.json", "data_manifest.json", "notebook_manifest.json"):
        manifest = json.loads((kaggle / name).read_text(encoding="utf-8"))
        category = {"code_manifest.json": "code", "data_manifest.json": "data"}.get(name, "notebooks")
        for rel, digest in manifest.items():
            emitted = kaggle / category / rel
            assert emitted.is_file(), (name, rel)
            assert hashlib.sha256(emitted.read_bytes()).hexdigest() == digest, (name, rel)


def test_r6_second_build_is_byte_identical(tmp_path, monkeypatch):
    _project, kaggle = _install(tmp_path, monkeypatch)
    assert builder.build_bundle() == 0
    first = _snapshot(kaggle)
    assert builder.build_bundle() == 0
    second = _snapshot(kaggle)
    assert first == second


def test_r6_forbidden_artifacts_are_excluded(tmp_path, monkeypatch):
    _project, kaggle = _install(tmp_path, monkeypatch)
    err = builder.build_bundle()
    assert err == 0
    forbidden_rels = (
        "code/src/benchmark/__pycache__",
        "code/configs/.env",
        "data/repositories/todo/db.sqlite3",
    )
    for rel in forbidden_rels:
        assert not (kaggle / rel).exists(), rel


def test_r7c_smoke_kaggle_lock_is_bundled(tmp_path, monkeypatch):
    _project, kaggle = _install(tmp_path, monkeypatch)
    err = builder.build_bundle()
    assert err == 0
    bundled = kaggle / "code" / "requirements-smoke-kaggle.lock"
    assert bundled.is_file()
    assert "Django==5.2.16" in bundled.read_text(encoding="utf-8")
