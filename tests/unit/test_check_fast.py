"""Lightweight tests for check_fast.py pure path-mapping logic."""

import os
from pathlib import Path
from unittest.mock import patch


def _import_select_tests():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "check_fast",
        str(Path(__file__).resolve().parent.parent.parent
            / "scripts" / "check_fast.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.select_tests


select_tests = _import_select_tests()


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
S = os.sep


def test_seven_arm_maps_to_correct_paths():
    paths = select_tests(
        [PROJECT_ROOT / "seven_arm_benchmark.py"],
        PROJECT_ROOT,
    )
    expected = [
        str(PROJECT_ROOT / "tests" / "unit" / "test_cli.py"),
        str(PROJECT_ROOT / "tests" / "unit" / "execution"
            / "test_pipeline.py"),
        str(PROJECT_ROOT / "tests" / "unit" / "execution"
            / "test_runner.py"),
        str(PROJECT_ROOT / "tests" / "integration"
            / "test_su0010a_regeneration.py"),
        str(PROJECT_ROOT / "tests" / "integration"
            / "test_su0011_iterative_agent.py"),
    ]
    assert paths == sorted(expected)


def test_all_returned_paths_exist():
    paths = select_tests(
        [PROJECT_ROOT / "seven_arm_benchmark.py"],
        PROJECT_ROOT,
    )
    for p in paths:
        assert Path(p).exists(), f"Path does not exist: {p}"


def test_duplicates_removed():
    reqs = [
        PROJECT_ROOT / "seven_arm_benchmark.py",
        PROJECT_ROOT / "seven_arm_benchmark.py",
    ]
    paths = select_tests(reqs, PROJECT_ROOT)
    unique = set(paths)
    assert len(paths) == len(unique)


def test_no_python_changes_returns_empty():
    with patch("sys.exit"):
        paths = select_tests([PROJECT_ROOT / "README.md"], PROJECT_ROOT)
    assert paths == []


def test_execution_mapping():
    paths = select_tests(
        [PROJECT_ROOT / "src" / "benchmark" / "execution" / "runner.py"],
        PROJECT_ROOT,
    )
    assert any(f"tests{S}unit{S}execution" in p for p in paths)
    assert any("test_su0010a_regeneration" in p for p in paths)
    assert any("test_su0011_iterative_agent" in p for p in paths)


def test_strategies_mapping():
    paths = select_tests(
        [PROJECT_ROOT / "src" / "benchmark" / "strategies" / "strategy.py"],
        PROJECT_ROOT,
    )
    assert any(f"tests{S}unit{S}strategies" in p for p in paths)
    assert any("test_su0011_iterative_agent" in p for p in paths)


def test_checkpoint_mapping():
    paths = select_tests(
        [PROJECT_ROOT / "src" / "benchmark" / "checkpoint" / "state.py"],
        PROJECT_ROOT,
    )
    assert any("test_checkpoint.py" in p for p in paths)
    assert any("test_su0008" in p for p in paths)


def test_statistics_mapping():
    paths = select_tests(
        [PROJECT_ROOT / "src" / "benchmark" / "statistics" / "metrics.py"],
        PROJECT_ROOT,
    )
    assert any(f"tests{S}unit{S}statistics" in p for p in paths)


def test_graph_mapping():
    paths = select_tests(
        [PROJECT_ROOT / "src" / "benchmark" / "graph" / "builder.py"],
        PROJECT_ROOT,
    )
    assert any(f"tests{S}unit{S}graph" in p for p in paths)
    assert any(f"tests{S}unit{S}strategies" in p for p in paths)


def test_missing_configured_path_raises_error():
    with patch("sys.exit") as mock_exit:
        select_tests(
            [PROJECT_ROOT / "tests" / "NONEXISTENT_FILE_xyz.py"],
            PROJECT_ROOT,
        )
    mock_exit.assert_called_once_with(1)
